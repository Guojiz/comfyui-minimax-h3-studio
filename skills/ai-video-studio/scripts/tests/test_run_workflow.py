import argparse
import io
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_RUNNER_PATH = Path(__file__).resolve().parents[1] / "run-workflow.py"
_RUNNER_SPEC = importlib.util.spec_from_file_location("runner_under_test", _RUNNER_PATH)
runner = importlib.util.module_from_spec(_RUNNER_SPEC)
_RUNNER_SPEC.loader.exec_module(runner)


SAMPLE_WORKFLOW = {
    "1": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "model.safetensors"},
    }
}


def make_args(**overrides):
    args = argparse.Namespace(
        workflow="/tmp/workflow.json",
        set=[],
        server=None,
        json=True,
        timeout=60,
        poll_interval=1,
        project="/tmp/project",
        run_name=None,
        shot=None,
        iteration=None,
        dry_run=True,
    )
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


class ServerGatingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.workflow = Path(self.tmp.name) / "workflow.json"
        self.workflow.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")

    def test_real_submit_requires_explicit_server(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(runner.UsageError):
                runner.run(make_args(workflow=str(self.workflow), dry_run=False))

    def test_env_server_is_explicit_configuration(self):
        with mock.patch.dict(os.environ, {"COMFY_SERVER": "http://comfy.example:8188"}):
            with mock.patch.object(
                runner,
                "http_json",
                return_value={"prompt_id": "p1"},
            ), mock.patch.object(
                runner,
                "poll_history",
                return_value={
                    "state": "success",
                    "entry": {"outputs": {}},
                    "history": {"p1": {}},
                    "status": {"status_str": "success", "completed": True},
                    "elapsed": 1.0,
                },
            ):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = runner.run(
                        make_args(
                            workflow=str(self.workflow),
                            dry_run=False,
                            project=str(Path(self.tmp.name) / "project"),
                        )
                    )
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["prompt_id"], "p1")
        self.assertEqual(payload["server"], "http://comfy.example:8188")
        run_json = json.loads(
            (Path(payload["run_dir"]) / "run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(run_json["server"], "http://comfy.example:8188")


class RunNameProtectionTests(unittest.TestCase):
    def test_existing_run_name_is_rejected(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        workflow = root / "workflow.json"
        workflow.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")
        run_dir = root / "runs" / "existing"
        run_dir.mkdir(parents=True)
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(runner.UsageError):
                runner.run(
                    make_args(
                        workflow=str(workflow),
                        dry_run=False,
                        project=str(root),
                        run_name="existing",
                        server="http://127.0.0.1:8188",
                    )
                )

class DryRunJsonTests(unittest.TestCase):
    def test_dry_run_emits_structured_json(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        workflow = Path(tmp.name) / "workflow.json"
        workflow.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")
        stdout = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True):
            with redirect_stdout(stdout):
                code = runner.run(make_args(workflow=str(workflow), dry_run=True))
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["dry_run"])
        self.assertEqual(payload["status"], "prepared")
        self.assertIsNone(payload["prompt_id"])
        self.assertIsNone(payload["server"])

    def test_cli_dry_run_emits_json_on_stdout(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        workflow = Path(tmp.name) / "workflow.json"
        workflow.write_text(json.dumps(SAMPLE_WORKFLOW), encoding="utf-8")
        stdout = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True):
            with redirect_stdout(stdout):
                code = runner.main(
                    [
                        str(workflow),
                        "--dry-run",
                        "--json",
                        "--project",
                        str(Path(tmp.name) / "project"),
                    ]
                )
        self.assertEqual(code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "prepared")


class LocalVideoArtifactTests(unittest.TestCase):
    def test_extracts_local_video_paths(self):
        outputs = {
            "7": {
                "ui": {
                    "video_paths": ["/output/local/generated_task_123.mp4"],
                    "video_filenames": ["generated_task_123.mp4"],
                }
            }
        }
        artifacts = runner.extract_local_video_artifacts(outputs)
        self.assertEqual(len(artifacts), 1)
        self.assertEqual(artifacts[0]["kind"], "video")
        self.assertEqual(artifacts[0]["type"], "local-video")
        self.assertEqual(artifacts[0]["filename"], "generated_task_123.mp4")
        self.assertEqual(artifacts[0]["source_path"], "/output/local/generated_task_123.mp4")


if __name__ == "__main__":
    unittest.main()
