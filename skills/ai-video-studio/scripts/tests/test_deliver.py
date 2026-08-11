import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_DELIVER_PATH = Path(__file__).resolve().parents[1] / "deliver.py"
_DELIVER_SPEC = importlib.util.spec_from_file_location("deliver_under_test", _DELIVER_PATH)
deliver = importlib.util.module_from_spec(_DELIVER_SPEC)
_DELIVER_SPEC.loader.exec_module(deliver)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def make_project(tmp, contents=None):
    root = Path(tmp)
    media = root / "media"
    media.mkdir()
    files = {}
    for name, data in (contents or {"a.mp4": b"aaa", "sub.srt": b"bbb"}).items():
        path = media / name
        path.write_bytes(data)
        files[name] = path
    return root, media, files


def write_manifest(root, entries, extra=None):
    manifest = root / "manifest.json"
    payload = {"files": entries}
    if extra:
        payload.update(extra)
    manifest.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return manifest


class DeliveryTests(unittest.TestCase):
    def test_copies_files_and_records_hashes_with_passthrough(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, media, files = make_project(tmp)
            manifest = write_manifest(
                root,
                [
                    {"path": "media/a.mp4", "role": "video"},
                    {"path": "media/sub.srt", "role": "subtitle", "language": "zh"},
                ],
                extra={
                    "run": "run-1",
                    "workflow": "video-wf-1",
                    "instance": "local-comfy",
                    "decision": "2026-08-10 approved",
                },
            )
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "delivered")
            dist = Path(payload["dist_dir"])
            self.assertTrue((dist / "a.mp4").is_file())
            self.assertTrue((dist / "sub.srt").is_file())
            self.assertTrue((dist / "delivery.json").is_file())
            delivery_json = json.loads((dist / "delivery.json").read_text(encoding="utf-8"))
            self.assertEqual(delivery_json["schema_version"], 1)
            self.assertEqual(delivery_json["link"], False)
            self.assertEqual(delivery_json["meta"]["run"], "run-1")
            by_role = {item["role"]: item for item in delivery_json["files"]}
            self.assertEqual(by_role["video"]["sha256"], sha256(b"aaa"))
            self.assertEqual(by_role["video"]["source"], str(files["a.mp4"].resolve()))
            self.assertEqual(by_role["video"]["run"], "run-1")
            self.assertEqual(by_role["video"]["workflow"], "video-wf-1")
            self.assertEqual(by_role["video"]["instance"], "local-comfy")
            self.assertEqual(by_role["video"]["decision"], "2026-08-10 approved")
            self.assertEqual(by_role["subtitle"]["language"], "zh")
            self.assertEqual(by_role["subtitle"]["sha256"], sha256(b"bbb"))
            self.assertTrue(files["a.mp4"].is_file(), "原始文件不得被移动")
            self.assertEqual((dist / "a.mp4").read_bytes(), b"aaa")

    def test_missing_file_fails_before_any_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, _ = make_project(tmp)
            manifest = write_manifest(
                root, [{"path": "media/ghost.mp4", "role": "video"}]
            )
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 3)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "missing_file")
            self.assertIn("ghost.mp4", payload["error"])
            self.assertFalse(Path(root, "dist").exists())

    def test_empty_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, _ = make_project(tmp, {"empty.mp4": b""})
            manifest = write_manifest(
                root, [{"path": "media/empty.mp4", "role": "video"}]
            )
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 3)
            payload = json.loads(stdout.getvalue())
            self.assertIn("为空", payload["error"])

    def test_link_creates_hardlink_not_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, media, files = make_project(tmp)
            manifest = write_manifest(
                root, [{"path": "media/a.mp4", "role": "video"}]
            )
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main(
                    [str(manifest), "--project", str(root), "--json", "--link"]
                )
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            dist = Path(payload["dist_dir"])
            self.assertEqual((dist / "a.mp4").stat().st_ino, files["a.mp4"].stat().st_ino)
            delivery_json = json.loads((dist / "delivery.json").read_text(encoding="utf-8"))
            self.assertTrue(delivery_json["link"])

    def test_existing_delivery_is_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, _ = make_project(tmp)
            manifest = write_manifest(
                root, [{"path": "media/a.mp4", "role": "video"}]
            )
            dist = Path(root, "dist")
            dist.mkdir()
            (dist / "delivery.json").write_text("{}", encoding="utf-8")
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 1)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "usage_error")
            self.assertIn("受保护", payload["error"])

    def test_only_manifest_files_are_copied(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, _ = make_project(tmp)
            (root / "outside.mp4").write_bytes(b"secret")
            manifest = write_manifest(
                root,
                [
                    {"path": "media/a.mp4", "role": "video"},
                    {"path": "media/sub.srt", "role": "subtitle"},
                ],
            )
            with redirect_stdout(io.StringIO()):
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 0)
            dist_files = {p.name for p in Path(root, "dist").iterdir()}
            self.assertEqual(dist_files, {"a.mp4", "sub.srt", "delivery.json"})
            self.assertNotIn("outside.mp4", dist_files)

    def test_relative_paths_resolve_from_manifest_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest_dir = root / "manifests"
            media = manifest_dir / "media"
            media.mkdir(parents=True)
            source = media / "a.mp4"
            source.write_bytes(b"aaa")
            manifest = manifest_dir / "delivery.json"
            manifest.write_text(
                json.dumps({"files": [{"path": "media/a.mp4", "role": "video"}]}),
                encoding="utf-8",
            )
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["files"][0]["source"], str(source.resolve()))

    def test_malformed_manifest_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "bad.json"
            manifest.write_text("{not json", encoding="utf-8")
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main([str(manifest), "--project", tmp, "--json"])
            self.assertEqual(code, 1)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "usage_error")

    def test_entry_without_role_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, _ = make_project(tmp)
            manifest = write_manifest(root, [{"path": "media/a.mp4"}])
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 1)
            payload = json.loads(stdout.getvalue())
            self.assertIn("role", payload["error"])

    def test_dry_run_validates_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, files = make_project(tmp)
            manifest = write_manifest(
                root, [{"path": "media/a.mp4", "role": "video"}]
            )
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main(
                    [str(manifest), "--project", str(root), "--json", "--dry-run"]
                )
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "prepared")
            self.assertEqual(payload["files"][0]["sha256"], sha256(b"aaa"))
            self.assertFalse(Path(root, "dist").exists())
            self.assertTrue(files["a.mp4"].is_file())

    def test_filename_collision_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            one = root / "one"
            two = root / "two"
            one.mkdir()
            two.mkdir()
            (one / "a.mp4").write_bytes(b"1")
            (two / "a.mp4").write_bytes(b"2")
            manifest = write_manifest(
                root,
                [
                    {"path": "one/a.mp4", "role": "video"},
                    {"path": "two/a.mp4", "role": "video"},
                ],
            )
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 1)
            payload = json.loads(stdout.getvalue())
            self.assertIn("冲突", payload["error"])

    def test_existing_dest_refused_exit_4(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, _ = make_project(tmp)
            manifest = write_manifest(
                root, [{"path": "media/a.mp4", "role": "video"}]
            )
            dist = Path(root, "dist")
            dist.mkdir()
            (dist / "a.mp4").write_bytes(b"older")
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 4)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "delivery_error")
            self.assertIn("不会覆盖", payload["error"])
            self.assertEqual((dist / "a.mp4").read_bytes(), b"older")

    def test_missing_manifest_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            with redirect_stdout(io.StringIO()) as stdout:
                code = deliver.main(
                    [str(Path(tmp) / "nope.json"), "--project", tmp, "--json"]
                )
            self.assertEqual(code, 1)
            payload = json.loads(stdout.getvalue())
            self.assertIn("无法读取交付清单", payload["error"])

    def test_absolute_path_in_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, media, files = make_project(tmp)
            manifest = write_manifest(
                root, [{"path": str(files["a.mp4"]), "role": "video"}]
            )
            with redirect_stdout(io.StringIO()):
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 1)

    def test_tilde_and_traversal_paths_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, media, _ = make_project(tmp)
            for bad in ("~/secret.txt", "media/../../outside.mp4"):
                manifest = write_manifest(
                    root, [{"path": bad, "role": "video"}]
                )
                with redirect_stdout(io.StringIO()):
                    code = deliver.main([str(manifest), "--project", str(root), "--json"])
                self.assertEqual(code, 1, bad)

    def test_path_escaping_project_root_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = Path(tmp).parent / "outside" / "secret.mp4"
            outside.parent.mkdir(exist_ok=True)
            outside.write_bytes(b"zzz")
            manifest = write_manifest(root, [{"path": "../outside/secret.mp4", "role": "video"}])
            with redirect_stdout(io.StringIO()):
                code = deliver.main([str(manifest), "--project", str(root), "--json"])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
