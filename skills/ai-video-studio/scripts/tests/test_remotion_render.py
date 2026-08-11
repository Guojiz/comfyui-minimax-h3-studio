import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys_path = str(Path(__file__).resolve().parents[1])

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "remotion-render.py"
_SPEC = importlib.util.spec_from_file_location("remotion_render_under_test", _SCRIPT_PATH)
rr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rr)


def make_project(tmp):
    root = Path(tmp)
    src = root / "remotion-src"
    src.mkdir(parents=True)
    (src / "Index.tsx").write_text("// composition", encoding="utf-8")
    node_modules = root / "node_modules" / "remotion"
    node_modules.mkdir(parents=True)
    (node_modules / "package.json").write_text("{}", encoding="utf-8")
    return root, src


def fake_render_success(argv, **kwargs):
    # argv: [npx, remotion, render, entry, output_file, --codec, h264, ...]
    output = Path(argv[4])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"fake-mp4")
    return mock.Mock(returncode=0, stdout="rendered", stderr="")


class RemotionRenderTests(unittest.TestCase):
    def test_missing_node_returns_dependency_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, src = make_project(tmp)
            with mock.patch.object(rr.shutil, "which", return_value=None):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = rr.main(
                        [
                            "--project",
                            str(root),
                            "--entry",
                            str(src / "Index.tsx"),
                            "--json",
                        ]
                    )
            self.assertEqual(code, rr.EXIT_DEPENDENCY)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "dependency_missing")

    def test_missing_remotion_package_returns_dependency_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "remotion-src"
            src.mkdir(parents=True)
            (src / "Index.tsx").write_text("// composition", encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = rr.main(
                    [
                        "--project",
                        str(root),
                        "--entry",
                        str(src / "Index.tsx"),
                        "--json",
                    ]
                )
            self.assertEqual(code, rr.EXIT_DEPENDENCY)
            payload = json.loads(stdout.getvalue())
            self.assertIn("npm install remotion", payload["error"])

    def test_dry_run_emits_plan_without_rendering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, src = make_project(tmp)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = rr.main(
                    [
                        "--project",
                        str(root),
                        "--entry",
                        str(src / "Index.tsx"),
                        "--output-name",
                        "title-card",
                        "--json",
                        "--dry-run",
                    ]
                )
            self.assertEqual(code, rr.EXIT_OK)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["status"], "prepared")
            self.assertIn("title-card", payload["version_dir"])
            self.assertFalse((root / "remotion").exists())

    def test_successful_render_versions_output_and_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, src = make_project(tmp)
            with mock.patch.object(rr.subprocess, "run", side_effect=fake_render_success):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = rr.main(
                        [
                            "--project",
                            str(root),
                            "--entry",
                            str(src / "Index.tsx"),
                            "--output-name",
                            "title-card",
                            "--json",
                        ]
                    )
                self.assertEqual(code, rr.EXIT_OK)
                payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "rendered")
            output = Path(payload["output_file"])
            self.assertTrue(output.is_file())
            self.assertEqual(output.read_bytes(), b"fake-mp4")
            version_info = json.loads(
                (output.parent / "version.json").read_text(encoding="utf-8")
            )
            self.assertEqual(version_info["version"], "v01")
            self.assertEqual(version_info["output_name"], "title-card")

    def test_second_render_uses_v02(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, src = make_project(tmp)
            with mock.patch.object(rr.subprocess, "run", side_effect=fake_render_success):
                rr.main(
                    [
                        "--project",
                        str(root),
                        "--entry",
                        str(src / "Index.tsx"),
                        "--output-name",
                        "title-card",
                        "--json",
                    ]
                )
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    rr.main(
                        [
                            "--project",
                            str(root),
                            "--entry",
                            str(src / "Index.tsx"),
                            "--output-name",
                            "title-card",
                            "--json",
                        ]
                    )
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["version_info"]["version"], "v02")
            self.assertEqual((root / "remotion" / "title-card" / "v01").is_dir(), True)
            self.assertEqual((root / "remotion" / "title-card" / "v02").is_dir(), True)

    def test_failed_render_cleans_partial_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, src = make_project(tmp)
            with mock.patch.object(
                rr.subprocess,
                "run",
                return_value=mock.Mock(returncode=1, stdout="", stderr="boom"),
            ):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = rr.main(
                        [
                            "--project",
                            str(root),
                            "--entry",
                            str(src / "Index.tsx"),
                            "--output-name",
                            "title-card",
                            "--json",
                        ]
                    )
            self.assertEqual(code, rr.EXIT_RENDER)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "render_failed")
            self.assertFalse((root / "remotion" / "title-card" / "v01").exists())
            self.assertFalse((root / "remotion" / "title-card").exists())

    def test_missing_entry_returns_input_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = make_project(tmp)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = rr.main(
                    [
                        "--project",
                        str(root),
                        "--entry",
                        str(root / "nope.tsx"),
                        "--json",
                    ]
                )
            self.assertEqual(code, rr.EXIT_INPUT)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "input_error")


if __name__ == "__main__":
    unittest.main()
