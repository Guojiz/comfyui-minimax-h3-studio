import json
import os
import sys
import tempfile
import urllib.request
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import comfyui_mcp as bridge


SAMPLE_WORKFLOW = {
    "1": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "model.safetensors"},
    }
}


def make_catalog(tmp, instances=None):
    catalog = Path(tmp) / "instances.json"
    catalog.write_text(
        json.dumps(
            {
                "version": 1,
                "instances": instances
                or [
                    {
                        "instance_id": "local-a",
                        "name": "Local A",
                        "server": "http://127.0.0.1:8188",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return str(catalog)


class SubmitAndStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.registry = self.root / "registry"
        self.registry.mkdir()
        (self.registry / "video.json").write_text(
            json.dumps(SAMPLE_WORKFLOW), encoding="utf-8"
        )
        self.catalog = make_catalog(self.tmp.name)
        self.project = str(self.root / "project")

    def test_submit_returns_ids_without_polling(self):
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json", return_value={"prompt_id": "p-1"}
        ) as post:
            result = bridge.tool_submit_workflow(
                "video",
                str(self.registry),
                instance_id="local-a",
                catalog_path=self.catalog,
                project=self.project,
                sets=['1.inputs.prompt="hello"'],
                run_name="r1",
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["prompt_id"], "p-1")
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(result["run_id"], "r1")
        post.assert_called_once()
        meta = json.loads(
            (Path(self.project) / "runs" / "r1" / "run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["instance_id"], "local-a")
        self.assertEqual(meta["prompt_id"], "p-1")
        self.assertEqual(meta["idempotency_key"], bridge.run_mgmt_mod.idempotency_key(
            "local-a", SAMPLE_WORKFLOW, ['1.inputs.prompt="hello"'], None, "default"
        ))

    def test_submit_duplicate_returns_existing_run(self):
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json", return_value={"prompt_id": "p-1"}
        ):
            first = bridge.tool_submit_workflow(
                "video",
                str(self.registry),
                instance_id="local-a",
                catalog_path=self.catalog,
                project=self.project,
                sets=['1.inputs.prompt="hello"'],
                run_name="r1",
            )
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json", return_value={"prompt_id": "p-2"}
        ) as post:
            second = bridge.tool_submit_workflow(
                "video",
                str(self.registry),
                instance_id="local-a",
                catalog_path=self.catalog,
                project=self.project,
                sets=['1.inputs.prompt="hello"'],
                run_name="r1",
            )
        self.assertTrue(second["duplicate"])
        self.assertEqual(second["prompt_id"], "p-1")
        self.assertNotEqual(second["prompt_id"], "p-2")
        post.assert_not_called()

    def test_submit_unreachable_does_not_claim_generation_failed(self):
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json", side_effect=RuntimeError("connection refused")
        ):
            result = bridge.tool_submit_workflow(
                "video",
                str(self.registry),
                instance_id="local-a",
                catalog_path=self.catalog,
                project=self.project,
                run_name="r2",
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "instance_unreachable")
        meta = json.loads(
            (Path(self.project) / "runs" / "r2" / "run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["status"], "instance_unreachable")

    def test_status_never_submits_and_maps_terminal_states(self):
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json", return_value={"prompt_id": "p-1"}
        ):
            bridge.tool_submit_workflow(
                "video",
                str(self.registry),
                instance_id="local-a",
                catalog_path=self.catalog,
                project=self.project,
                run_name="r3",
            )
        history = {
            "p-1": {"status": {"status_str": "success", "completed": True}, "outputs": {}}
        }
        with mock.patch.object(
            bridge.run_mgmt_mod,
            "http_json",
            side_effect=[
                {"queue_running": [["1", "p-1"]], "queue_pending": []},
                history,
            ],
        ) as query:
            result = bridge.tool_get_run_status("r3", self.project, instance_id="local-a", catalog_path=self.catalog)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(query.call_count, 2)
        meta = json.loads(
            (Path(self.project) / "runs" / "r3" / "run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["last_known_status"], "completed")
        self.assertIn("last_checked_at", meta)

    def test_status_unreachable_is_not_terminal(self):
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json", return_value={"prompt_id": "p-1"}
        ):
            bridge.tool_submit_workflow(
                "video",
                str(self.registry),
                instance_id="local-a",
                catalog_path=self.catalog,
                project=self.project,
                run_name="r4",
            )
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json", side_effect=RuntimeError("down")
        ):
            result = bridge.tool_get_run_status(
                "r4", self.project, instance_id="local-a", catalog_path=self.catalog
            )
        self.assertEqual(result["status"], "instance_unreachable")
        self.assertFalse(result["ok"])


class QueueAndCancelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog = make_catalog(self.tmp.name)

    def test_list_queue_parses_running_and_pending(self):
        with mock.patch.object(
            bridge.run_mgmt_mod,
            "http_json",
            return_value={
                "queue_running": [["1", "a"], ["2", "b"]],
                "queue_pending": [["3", "c"]],
            },
        ):
            result = bridge.tool_list_queue(instance_id="local-a", catalog_path=self.catalog)
        self.assertEqual(result["queue_running"], ["a", "b"])
        self.assertEqual(result["queue_pending"], ["c"])

    def test_cancel_queued_run(self):
        with mock.patch.object(
            bridge.run_mgmt_mod,
            "http_json",
            return_value={"queue_running": [], "queue_pending": [["1", "p-1"]]},
        ), mock.patch.object(
            bridge.run_mgmt_mod,
            "http_json",
            return_value={},
        ) as http, mock.patch.object(
            bridge.run_mgmt_mod.urllib.request,
            "urlopen",
            return_value=mock.MagicMock(),
        ):
            # http_json patched twice: queue read, then delete write
            result = bridge.run_mgmt_mod.cancel_run(
                "http://127.0.0.1:8188", "p-1",
                {"queue_running": [], "queue_pending": [["1", "p-1"]]},
            )
        self.assertTrue(result["ok"])
        self.assertTrue(result["cancelled"])

    def test_cancel_running_reports_unsupported(self):
        result = bridge.run_mgmt_mod.cancel_run(
            "http://127.0.0.1:8188",
            "p-1",
            {"queue_running": [["1", "p-1"]], "queue_pending": []},
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["unsupported"])


class UploadAndDownloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog = make_catalog(self.tmp.name)
        self.registry = Path(self.tmp.name) / "registry"
        self.registry.mkdir()
        (self.registry / "video.json").write_text(
            json.dumps(SAMPLE_WORKFLOW), encoding="utf-8"
        )
        self.project = str(Path(self.tmp.name) / "project")

    def test_upload_requires_authorization(self):
        image = Path(self.tmp.name) / "ref.png"
        image.write_bytes(b"fake-png")
        with self.assertRaises(ValueError):
            bridge.tool_upload_asset(
                str(image), instance_id="local-a", catalog_path=self.catalog
            )

    def test_upload_returns_server_name_and_hash(self):
        image = Path(self.tmp.name) / "ref.png"
        image.write_bytes(b"fake-png")
        fake_response = mock.MagicMock()
        fake_response.read.return_value = b'{"name": "ref.png"}'
        fake_response.__enter__.return_value = fake_response
        with mock.patch.object(
            bridge.run_mgmt_mod.urllib.request, "urlopen", return_value=fake_response
        ):
            result = bridge.tool_upload_asset(
                str(image),
                instance_id="local-a",
                catalog_path=self.catalog,
                authorized=True,
            )
        self.assertTrue(result["ok"])
        self.assertEqual(result["remote_name"], "ref.png")
        self.assertEqual(len(result["sha256"]), 64)

    def test_download_records_hash_and_source(self):
        root = Path(self.tmp.name)
        project = root / "project"
        run_dir = project / "runs" / "r1"
        run_dir.mkdir(parents=True)
        meta = {
            "status": "completed",
            "prompt_id": "p-1",
            "artifacts": [
                {
                    "node": "7",
                    "kind": "video",
                    "filename": "out.mp4",
                    "type": "video",
                    "subfolder": "",
                    "view_url": "http://127.0.0.1:8188/view?filename=out.mp4&type=output",
                }
            ],
        }
        (run_dir / "run.json").write_text(json.dumps(meta), encoding="utf-8")
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json_byte", return_value=b"video-bytes"
        ):
            result = bridge.tool_download_artifacts(
                "r1", str(project), instance_id="local-a", catalog_path=self.catalog
            )
        self.assertTrue(result["ok"])
        downloaded = result["downloaded"][0]
        self.assertEqual(downloaded["filename"], "out.mp4")
        self.assertEqual(len(downloaded["sha256"]), 64)
        self.assertEqual(downloaded["instance_id"], "local-a")
        manifest = json.loads(
            (root / "project" / "artifacts" / "download-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["downloaded"][0]["sha256"], downloaded["sha256"])

    def test_semantic_binding_sets_from_manifest(self):
        manifest = {
            "bindings": {
                "reference_image": "137.inputs.image",
                "prompt": "138.inputs.value",
            }
        }
        specs = bridge.run_mgmt_mod.semantic_binding_sets(
            manifest,
            {"reference_image": "ref.png", "prompt": "一只猫"},
        )
        self.assertIn('137.inputs.image="ref.png"', specs)
        self.assertIn('138.inputs.value="一只猫"', specs)

    def test_local_video_source_path_outside_allowed_roots_is_rejected(self):
        root = Path(self.tmp.name)
        project = root / "project"
        run_dir = project / "runs" / "r1"
        run_dir.mkdir(parents=True)
        secret = root / "secret.txt"
        secret.write_text("secret", encoding="utf-8")
        meta = {
            "status": "completed",
            "prompt_id": "p-1",
            "artifacts": [
                {
                    "node": "7",
                    "kind": "video",
                    "filename": "leak.mp4",
                    "type": "local-video",
                    "source_path": str(secret),
                    "view_url": None,
                }
            ],
        }
        (run_dir / "run.json").write_text(json.dumps(meta), encoding="utf-8")
        result = bridge.tool_download_artifacts(
            "r1", str(project), instance_id="local-a", catalog_path=self.catalog
        )
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["downloaded"]), 0)
        self.assertEqual(len(result["failures"]), 1)
        self.assertIn("rejected", result["failures"][0]["error"])

    def test_local_video_source_path_inside_allowed_root_is_read(self):
        root = Path(self.tmp.name)
        project = root / "project"
        run_dir = project / "runs" / "r1"
        run_dir.mkdir(parents=True)
        output_root = root / "comfy-output"
        output_root.mkdir(parents=True)
        video = output_root / "generated_task.mp4"
        video.write_bytes(b"video-bytes")
        meta = {
            "status": "completed",
            "prompt_id": "p-1",
            "artifacts": [
                {
                    "node": "7",
                    "kind": "video",
                    "filename": "generated_task.mp4",
                    "type": "local-video",
                    "source_path": str(video),
                    "view_url": None,
                }
            ],
        }
        (run_dir / "run.json").write_text(json.dumps(meta), encoding="utf-8")
        instance = {
            "instance_id": "local-a",
            "server": "http://127.0.0.1:8188",
            "output_dir": str(output_root),
        }
        result = bridge.run_mgmt_mod.download_artifacts(
            str(project), "r1", instance, "http://127.0.0.1:8188"
        )
        self.assertTrue(result["ok"])
        self.assertEqual(result["downloaded"][0]["filename"], "generated_task.mp4")

    def test_legacy_local_artifact_type_is_still_accepted(self):
        root = Path(self.tmp.name)
        project = root / "project"
        run_dir = project / "runs" / "r1"
        run_dir.mkdir(parents=True)
        output_root = root / "comfy-output"
        output_root.mkdir(parents=True)
        video = output_root / "old.mp4"
        video.write_bytes(b"old-video")
        meta = {
            "status": "completed",
            "prompt_id": "p-1",
            "artifacts": [
                {
                    "node": "7",
                    "kind": "video",
                    "filename": "old.mp4",
                    "type": "local-video",
                    "source_path": str(video),
                    "view_url": None,
                }
            ],
        }
        (run_dir / "run.json").write_text(json.dumps(meta), encoding="utf-8")
        instance = {
            "instance_id": "local-a",
            "server": "http://127.0.0.1:8188",
            "output_dir": str(output_root),
        }
        result = bridge.run_mgmt_mod.download_artifacts(
            str(project), "r1", instance, "http://127.0.0.1:8188"
        )
        self.assertTrue(result["ok"])

    def test_same_host_redirect_handler_blocks_other_host(self):
        handler = bridge.run_mgmt_mod.SameHostRedirectHandler("comfy.example")
        request = urllib.request.Request("http://comfy.example/view?x=1")
        with self.assertRaises(RuntimeError):
            handler.redirect_request(
                request,
                mock.MagicMock(),
                302,
                "Found",
                {"Location": "http://evil.example/x"},
                "http://evil.example/x",
            )

    def test_same_host_redirect_handler_allows_same_host(self):
        handler = bridge.run_mgmt_mod.SameHostRedirectHandler("comfy.example")
        request = urllib.request.Request("http://comfy.example/view?x=1")
        new_request = handler.redirect_request(
            request,
            mock.MagicMock(),
            302,
            "Found",
            {"Location": "http://comfy.example/other"},
            "http://comfy.example/other",
        )
        self.assertIsNotNone(new_request)
        self.assertEqual(new_request.full_url, "http://comfy.example/other")

    def test_sanitize_remote_name_strips_injection_chars(self):
        name = bridge.run_mgmt_mod._sanitize_remote_name('a"b\r\nc/../d')
        self.assertNotIn('"', name)
        self.assertNotIn("\r", name)
        self.assertNotIn("\n", name)
        self.assertNotIn("/", name)
        self.assertNotIn("..", name)

    def test_run_name_traversal_rejected(self):
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json", return_value={"prompt_id": "p-1"}
        ):
            with self.assertRaises(ValueError):
                bridge.tool_submit_workflow(
                    "video",
                    str(self.registry),
                    instance_id="local-a",
                    catalog_path=self.catalog,
                    project=self.project,
                    run_name="../../escape",
                )

    def test_read_run_dir_rejects_escape(self):
        project = Path(self.tmp.name) / "project"
        project.mkdir()
        with self.assertRaises(LookupError):
            bridge.run_mgmt_mod.read_run_dir(str(project), "../../etc")

    def test_external_task_id_derived_from_ui(self):
        entry = {
            "outputs": {
                "7": {
                    "ui": {
                        "task_ids": ["task-42"],
                        "video_paths": ["/output/local/x.mp4"],
                    }
                }
            }
        }
        task_id = bridge.run_mgmt_mod.derive_external_task_id(entry)
        self.assertEqual(task_id, "task-42")

    def test_completed_status_merges_local_video_artifacts_into_run(self):
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json", return_value={"prompt_id": "p-1"}
        ):
            bridge.tool_submit_workflow(
                "video",
                str(self.registry),
                instance_id="local-a",
                catalog_path=self.catalog,
                project=self.project,
                run_name="r5",
            )
        history = {
            "p-1": {
                "status": {"status_str": "success", "completed": True},
                "outputs": {
                    "7": {
                        "ui": {
                            "video_paths": ["/output/local/x.mp4"],
                            "video_filenames": ["x.mp4"],
                            "task_ids": ["task-9"],
                        }
                    }
                },
            }
        }
        with mock.patch.object(
            bridge.run_mgmt_mod,
            "http_json",
            side_effect=[{"queue_running": [], "queue_pending": []}, history],
        ):
            result = bridge.tool_get_run_status(
                "r5", self.project, instance_id="local-a", catalog_path=self.catalog
            )
        self.assertEqual(result["status"], "completed")
        meta = json.loads(
            (Path(self.project) / "runs" / "r5" / "run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(meta["artifacts"][0]["type"], "local-video")
        self.assertEqual(meta["external_task_id"], "task-9")

    def test_completed_status_merges_generic_images_with_view_url(self):
        with mock.patch.object(
            bridge.run_mgmt_mod, "http_json", return_value={"prompt_id": "p-1"}
        ):
            bridge.tool_submit_workflow(
                "video",
                str(self.registry),
                instance_id="local-a",
                catalog_path=self.catalog,
                project=self.project,
                run_name="r6",
            )
        history = {
            "p-1": {
                "status": {"status_str": "success", "completed": True},
                "outputs": {
                    "3": {
                        "images": [
                            {
                                "filename": "smoke_00001_.png",
                                "subfolder": "",
                                "type": "output",
                            }
                        ]
                    }
                },
            }
        }
        with mock.patch.object(
            bridge.run_mgmt_mod,
            "http_json",
            side_effect=[{"queue_running": [], "queue_pending": []}, history],
        ):
            result = bridge.tool_get_run_status(
                "r6", self.project, instance_id="local-a", catalog_path=self.catalog
            )
        self.assertEqual(result["status"], "completed")
        meta = json.loads(
            (Path(self.project) / "runs" / "r6" / "run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(meta["artifacts"]), 1)
        self.assertEqual(meta["artifacts"][0]["filename"], "smoke_00001_.png")
        self.assertIn("/view?", meta["artifacts"][0]["view_url"])


if __name__ == "__main__":
    unittest.main()
