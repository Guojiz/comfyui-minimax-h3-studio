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

    def test_filename_id_without_manifest(self):
        write_json(self.registry / "plain.json", SAMPLE_WORKFLOW)
        entry = bridge.load_registry(str(self.registry))["workflows"][0]
        self.assertEqual(entry["id"], "plain")
        self.assertTrue(entry["ok"], entry["errors"])

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

    def test_registers_five_tools_with_tool_annotations(self):
        with self.install_fake_mcp():
            server = bridge.create_server(
                server="http://127.0.0.1:8188", registry_dir=str(self.registry)
            )
        names = [entry[0] for entry in server.registered]
        self.assertEqual(
            names, ["health", "list_workflows", "inspect_workflow", "doctor", "run_workflow"]
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
                "list_workflows": (True, False, True),
                "inspect_workflow": (True, False, True),
                "doctor": (True, False, True),
                "run_workflow": (False, False, False),
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
