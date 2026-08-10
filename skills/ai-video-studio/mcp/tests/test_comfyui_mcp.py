import json
import os
import sys
import tempfile
import types
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


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


class ServerUrlTests(unittest.TestCase):
    def test_strips_query_fragment_and_trailing_slash(self):
        url = bridge.normalize_server_url(
            "https://comfy.example:8188/run/?token=abc#fragment"
        )
        self.assertEqual(url, "https://comfy.example:8188/run")

    def test_default_when_unset(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(bridge.normalize_server_url(None), bridge.DEFAULT_SERVER)

    def test_rejects_embedded_credentials(self):
        with self.assertRaises(ValueError):
            bridge.normalize_server_url("http://user:secret@127.0.0.1:8188")

    def test_rejects_non_http_scheme(self):
        with self.assertRaises(ValueError):
            bridge.normalize_server_url("ftp://127.0.0.1:8188")


class InstanceToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog = Path(self.tmp.name) / "instances.json"
        self.catalog.write_text(
            json.dumps(
                {
                    "version": 1,
                    "instances": [
                        {
                            "instance_id": "local-a",
                            "name": "Local A",
                            "server": "http://127.0.0.1:8188",
                        },
                        {
                            "instance_id": "remote-b",
                            "name": "Remote B",
                            "server": "https://comfy.example:8443",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_list_instances(self):
        result = bridge.tool_list_instances(str(self.catalog))
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["instances"][1]["instance_id"], "remote-b")

    def test_select_and_get_active_instance(self):
        project = Path(self.tmp.name) / "proj"
        selected = bridge.tool_select_instance("local-a", str(project), str(self.catalog))
        self.assertTrue(selected["ok"])
        active = bridge.tool_get_active_instance(str(project), str(self.catalog))
        self.assertEqual(active["instance_id"], "local-a")
        self.assertEqual(active["server"], "http://127.0.0.1:8188")
        lock = json.loads(
            (project / ".ai-video-studio" / "instance.lock.json").read_text(encoding="utf-8")
        )
        self.assertEqual(lock["instance_id"], "local-a")

    def test_get_active_instance_without_lock(self):
        result = bridge.tool_get_active_instance(str(Path(self.tmp.name) / "none"), str(self.catalog))
        self.assertFalse(result["ok"])


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registry = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_manifest_id_and_metadata(self):
        write_json(self.registry / "workflow.json", SAMPLE_WORKFLOW)
        write_json(
            self.registry / "workflow.manifest.json",
            {
                "id": "my-workflow",
                "purpose": "test workflow",
                "inputs": ["prompt"],
                "outputs": ["image"],
                "provider": "local",
            },
        )
        listing = bridge.load_registry(str(self.registry))
        self.assertEqual(listing["count"], 1)
        entry = listing["workflows"][0]
        self.assertTrue(entry["ok"], entry["errors"])
        self.assertEqual(entry["id"], "my-workflow")
        self.assertEqual(entry["node_count"], 1)
        self.assertEqual(entry["node_types"], ["CheckpointLoaderSimple"])
        self.assertEqual(entry["description"], "test workflow")
        self.assertEqual(entry["provider"], "local")
        self.assertEqual(entry["inputs"], ["prompt"])

    def test_manifest_license_and_source_metadata(self):
        write_json(self.registry / "workflow.json", SAMPLE_WORKFLOW)
        write_json(
            self.registry / "workflow.manifest.json",
            {
                "id": "my-workflow",
                "license": "redistribution-not-confirmed",
                "source": "user-provided",
                "distribution": "local-only",
            },
        )
        entry = bridge.load_registry(str(self.registry))["workflows"][0]
        self.assertEqual(entry["license"], "redistribution-not-confirmed")
        self.assertEqual(entry["source"], "user-provided")
        self.assertEqual(entry["distribution"], "local-only")

    def test_filename_id_without_manifest(self):
        write_json(self.registry / "plain.json", SAMPLE_WORKFLOW)
        entry = bridge.load_registry(str(self.registry))["workflows"][0]
        self.assertEqual(entry["id"], "plain")
        self.assertTrue(entry["ok"], entry["errors"])

    def test_manifest_must_pair_with_workflow_stem(self):
        write_json(self.registry / "video-v1.json", SAMPLE_WORKFLOW)
        write_json(
            self.registry / "video.manifest.json",
            {"id": "video-v1", "purpose": "metadata"},
        )
        entry = bridge.load_registry(str(self.registry))["workflows"][0]
        self.assertEqual(entry["id"], "video-v1")
        self.assertEqual(entry["manifest_file"], None)
        self.assertEqual(entry["description"], "")
        write_json(
            self.registry / "video-v1.manifest.json",
            {"id": "video-v1", "purpose": "metadata"},
        )
        entry = bridge.load_registry(str(self.registry))["workflows"][0]
        self.assertTrue(entry["manifest_file"].endswith("video-v1.manifest.json"))
        self.assertEqual(entry["description"], "metadata")

    def test_invalid_json_is_reported(self):
        (self.registry / "broken.json").write_text("{nope", encoding="utf-8")
        entry = bridge.load_registry(str(self.registry))["workflows"][0]
        self.assertFalse(entry["ok"])
        self.assertTrue(any("invalid JSON" in error for error in entry["errors"]))

    def test_resolve_rejects_path_injection(self):
        for bad in ["../secret", "a/b", "a\\b", "/etc/passwd", "..", ".", ""]:
            with self.assertRaises(ValueError, msg=bad):
                bridge.resolve_workflow(bad, str(self.registry))

    def test_resolve_missing_id(self):
        with self.assertRaises(LookupError):
            bridge.resolve_workflow("missing", str(self.registry))

    def test_resolve_uses_manifest_id(self):
        write_json(self.registry / "workflow.json", SAMPLE_WORKFLOW)
        write_json(self.registry / "workflow.manifest.json", {"id": "alias-id"})
        path = bridge.resolve_workflow("alias-id", str(self.registry))
        self.assertEqual(path.name, "workflow.json")

    def test_inspect_workflow(self):
        write_json(self.registry / "video.json", SAMPLE_WORKFLOW)
        inspected = bridge.tool_inspect_workflow("video", str(self.registry))
        self.assertEqual(inspected["node_count"], 1)
        self.assertEqual(
            inspected["workflow"]["1"]["class_type"], "CheckpointLoaderSimple"
        )


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registry = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        write_json(self.registry / "video.json", SAMPLE_WORKFLOW)

    def test_run_workflow_defaults_to_dry_run(self):
        result = mock.Mock(returncode=0, stdout="dry-run: ok\n", stderr="")
        with mock.patch.object(bridge.subprocess, "run", return_value=result) as run:
            outcome = bridge.tool_run_workflow(
                "video", str(self.registry), server="http://127.0.0.1:8188"
            )
        argv = run.call_args.args[0]
        self.assertIn("--dry-run", argv)
        self.assertTrue(Path(argv[2]).name == "video.json", argv)
        self.assertTrue(outcome["ok"])
        self.assertTrue(outcome["dry_run"])

    def test_run_workflow_submit_arguments(self):
        result = mock.Mock(returncode=0, stdout="ok", stderr="")
        with mock.patch.object(bridge.subprocess, "run", return_value=result) as run:
            bridge.tool_run_workflow(
                "video",
                str(self.registry),
                server="http://localhost:8188",
                sets=['1.inputs.prompt="hello"'],
                dry_run=False,
                project="/tmp/project",
                run_name="r1",
                shot="s01",
                iteration="v2",
                timeout=120,
                poll_interval=3,
            )
        argv = run.call_args.args[0]
        self.assertNotIn("--dry-run", argv)
        self.assertIn("--set", argv)
        self.assertIn('1.inputs.prompt="hello"', argv)
        self.assertIn("--run-name", argv)
        self.assertIn("r1", argv)
        self.assertIn("--shot", argv)
        self.assertIn("--iteration", argv)

    def test_run_workflow_uses_json_output_and_returns_run_facts(self):
        facts = {
            "ok": True,
            "exit_code": 0,
            "dry_run": False,
            "run_id": "r1",
            "run_name": "r1",
            "run_dir": "/tmp/project/runs/r1",
            "prompt_id": "abc-123",
            "status": "completed",
            "server": "http://127.0.0.1:8188",
            "artifacts": [
                {
                    "node": "7",
                    "kind": "video",
                    "filename": "out.mp4",
                    "subfolder": "",
                    "type": "mzsj",
                    "source_path": "/tmp/out.mp4",
                    "view_url": None,
                }
            ],
        }
        result = mock.Mock(returncode=0, stdout=json.dumps(facts), stderr="")
        with mock.patch.object(bridge.subprocess, "run", return_value=result) as run:
            outcome = bridge.tool_run_workflow(
                "video",
                str(self.registry),
                server="http://127.0.0.1:8188",
                dry_run=False,
                project="/tmp/project",
                run_name="r1",
                timeout=120,
                poll_interval=3,
            )
        argv = run.call_args.args[0]
        self.assertIn("--json", argv)
        self.assertTrue(outcome["ok"])
        self.assertEqual(outcome["run_id"], "r1")
        self.assertEqual(outcome["prompt_id"], "abc-123")
        self.assertEqual(outcome["status"], "completed")
        self.assertEqual(outcome["run_dir"], "/tmp/project/runs/r1")
        self.assertEqual(outcome["artifacts"][0]["type"], "mzsj")
        self.assertEqual(outcome["run_facts"]["run_id"], "r1")

    def test_run_workflow_falls_back_when_stdout_is_not_json(self):
        result = mock.Mock(returncode=3, stdout="错误: 节点缺失\n", stderr="")
        with mock.patch.object(bridge.subprocess, "run", return_value=result):
            outcome = bridge.tool_run_workflow(
                "video",
                str(self.registry),
                server="http://127.0.0.1:8188",
                dry_run=False,
                timeout=60,
            )
        self.assertFalse(outcome["ok"])
        self.assertEqual(outcome["exit_code"], 3)
        self.assertNotIn("run_facts", outcome)

    def test_doctor_offline_arguments(self):
        result = mock.Mock(returncode=0, stdout="structure ok", stderr="")
        with mock.patch.object(bridge.subprocess, "run", return_value=result) as run:
            outcome = bridge.tool_doctor(
                "video", str(self.registry), server="http://127.0.0.1:8188", offline=True
            )
        argv = run.call_args.args[0]
        self.assertIn("--offline", argv)
        self.assertTrue(outcome["ok"])

    def test_snippet_truncates_middle(self):
        text = "x" * 1000
        snippet = bridge._snippet(text, limit=100)
        self.assertLessEqual(len(snippet), 100)
        self.assertIn("truncated", snippet)


class FakeToolAnnotations:
    """Mirror of mcp.types.ToolAnnotations for offline registration tests."""

    def __init__(
        self,
        title=None,
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ):
        self.title = title
        self.readOnlyHint = readOnlyHint
        self.destructiveHint = destructiveHint
        self.idempotentHint = idempotentHint
        self.openWorldHint = openWorldHint


class ServerRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.registry = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        write_json(self.registry / "video.json", SAMPLE_WORKFLOW)

    @staticmethod
    def install_fake_mcp(with_annotations=True):
        fake_package = types.ModuleType("mcp")
        server_package = types.ModuleType("mcp.server")
        fastmcp = types.ModuleType("mcp.server.fastmcp")
        types_package = types.ModuleType("mcp.types")
        types_package.ToolAnnotations = FakeToolAnnotations

        class FakeFastMCP:
            def __init__(self, name):
                self.name = name
                self.registered = []

            def tool(self, name=None, description=None, annotations=None):
                if not with_annotations and annotations is not None:
                    raise TypeError("annotations unsupported for test")

                def decorator(fn):
                    self.registered.append((name, description, annotations, fn))
                    return fn

                return decorator

        fastmcp.FastMCP = FakeFastMCP
        server_package.fastmcp = fastmcp
        fake_package.server = server_package
        fake_package.types = types_package
        modules = {
            "mcp": fake_package,
            "mcp.server": server_package,
            "mcp.server.fastmcp": fastmcp,
            "mcp.types": types_package,
        }
        return mock.patch.dict(sys.modules, modules)

    def test_registers_all_tools_with_tool_annotations(self):
        with self.install_fake_mcp():
            server = bridge.create_server(
                server="http://127.0.0.1:8188", registry_dir=str(self.registry)
            )
        names = [entry[0] for entry in server.registered]
        self.assertEqual(
            names,
            [
                "health",
                "list_instances",
                "check_instance",
                "select_instance",
                "get_active_instance",
                "list_workflows",
                "inspect_workflow",
                "doctor",
                "run_workflow",
                "submit_workflow",
                "get_run_status",
                "list_queue",
                "cancel_run",
                "download_artifacts",
                "upload_asset",
            ],
        )
        for name, _, annotations, _ in server.registered:
            self.assertIsInstance(annotations, FakeToolAnnotations)
        flags = {
            entry[0]: (
                entry[2].readOnlyHint,
                entry[2].destructiveHint,
                entry[2].idempotentHint,
            )
            for entry in server.registered
        }
        self.assertEqual(
            flags,
            {
                "health": (True, False, True),
                "list_instances": (True, False, True),
                "check_instance": (True, False, True),
                "select_instance": (False, False, False),
                "get_active_instance": (True, False, True),
                "list_workflows": (True, False, True),
                "inspect_workflow": (True, False, True),
                "doctor": (True, False, True),
                "run_workflow": (False, False, False),
                "submit_workflow": (False, False, False),
                "get_run_status": (True, False, True),
                "list_queue": (True, False, True),
                "cancel_run": (False, False, False),
                "download_artifacts": (False, False, False),
                "upload_asset": (False, False, False),
            },
        )

    def test_registration_requires_annotations_support(self):
        with self.install_fake_mcp(with_annotations=False):
            with self.assertRaises(TypeError):
                bridge.create_server(
                    server="http://127.0.0.1:8188",
                    registry_dir=str(self.registry),
                )


if __name__ == "__main__":
    unittest.main()
