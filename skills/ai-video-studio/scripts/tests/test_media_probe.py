import argparse
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_PROBE_PATH = Path(__file__).resolve().parents[1] / "media-probe.py"
_PROBE_SPEC = importlib.util.spec_from_file_location("media_probe_under_test", _PROBE_PATH)
media_probe = importlib.util.module_from_spec(_PROBE_SPEC)
_PROBE_SPEC.loader.exec_module(media_probe)


PROBE_JSON = {
    "format": {"duration": "12.500"},
    "streams": [
        {
            "codec_type": "video",
            "width": 1920,
            "height": 1080,
            "avg_frame_rate": "30000/1001",
            "r_frame_rate": "30/1",
        },
        {"codec_type": "audio", "codec_name": "aac"},
    ],
}


def make_args(**overrides):
    args = argparse.Namespace(files=[], ffmpeg_dir=None, json=True, timeout=30)
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


def make_executable(path):
    path.touch()
    os.chmod(path, 0o755)
    return path


def fake_ffprobe(returncode=0, stdout=json.dumps(PROBE_JSON), stderr=""):
    return mock.patch.object(
        media_probe.subprocess,
        "run",
        return_value=mock.Mock(returncode=returncode, stdout=stdout, stderr=stderr),
    )


class FindToolTests(unittest.TestCase):
    def test_ffmpeg_dir_env_is_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            tool = make_executable(Path(tmp) / "ffprobe")
            with mock.patch.dict(os.environ, {"FFMPEG_DIR": tmp}, clear=False), mock.patch.object(
                media_probe.shutil, "which", return_value=None
            ):
                found = media_probe.find_tool("ffprobe")
            self.assertEqual(found, tool)

    def test_ffmpeg_dir_flag_beats_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_dir = Path(tmp) / "env"
            flag_dir = Path(tmp) / "flag"
            env_dir.mkdir()
            flag_dir.mkdir()
            env_tool = make_executable(env_dir / "ffprobe")
            flag_tool = make_executable(flag_dir / "ffprobe")
            with mock.patch.dict(os.environ, {"FFMPEG_DIR": str(env_dir)}, clear=False), mock.patch.object(
                media_probe.shutil, "which", return_value=None
            ):
                found = media_probe.find_tool("ffprobe", ffmpeg_dir=str(flag_dir))
            self.assertEqual(found, flag_tool)
            self.assertNotEqual(found, env_tool)

    def test_path_is_used_after_explicit_locations(self):
        with mock.patch.object(media_probe.shutil, "which", return_value="/usr/local/bin/ffprobe"):
            found = media_probe.find_tool("ffprobe")
        self.assertEqual(found, Path("/usr/local/bin/ffprobe"))

    def test_common_dirs_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            common_dir = Path(tmp) / "common"
            common_dir.mkdir()
            tool = make_executable(common_dir / "ffprobe")
            with mock.patch.object(media_probe.shutil, "which", return_value=None), mock.patch.dict(
                os.environ, {}, clear=True
            ), mock.patch.object(media_probe, "COMMON_BIN_DIRS", [common_dir]):
                found = media_probe.find_tool("ffprobe")
            self.assertEqual(found, tool)

    def test_missing_tool_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            common_dir = Path(tmp) / "common"
            common_dir.mkdir()
            with mock.patch.object(media_probe.shutil, "which", return_value=None), mock.patch.dict(
                os.environ, {}, clear=True
            ), mock.patch.object(media_probe, "COMMON_BIN_DIRS", [common_dir]):
                found = media_probe.find_tool("ffprobe")
            self.assertIsNone(found)


class ParseTests(unittest.TestCase):
    def test_parse_fps_rational(self):
        fps, raw = media_probe.parse_fps({"avg_frame_rate": "30000/1001"})
        self.assertEqual(fps, 29.97)
        self.assertEqual(raw, "30000/1001")

    def test_parse_fps_zero_denominator(self):
        self.assertEqual(media_probe.parse_fps({"avg_frame_rate": "0/0"}), (None, None))

    def test_parse_probe_fields(self):
        result = media_probe.parse_probe(PROBE_JSON, "x.mp4")
        self.assertEqual(result["duration"], 12.5)
        self.assertEqual(result["width"], 1920)
        self.assertEqual(result["height"], 1080)
        self.assertEqual(result["fps"], 29.97)
        self.assertEqual(result["video_streams"], 1)
        self.assertEqual(result["audio_streams"], 1)

    def test_parse_probe_audio_only(self):
        data = {
            "format": {"duration": "5.000"},
            "streams": [{"codec_type": "audio", "codec_name": "aac"}],
        }
        result = media_probe.parse_probe(data, "x.mp4")
        self.assertEqual(result["duration"], 5.0)
        self.assertIsNone(result["width"])
        self.assertIsNone(result["height"])
        self.assertIsNone(result["fps"])
        self.assertEqual(result["audio_streams"], 1)
        self.assertEqual(result["video_streams"], 0)


class RunTests(unittest.TestCase):
    def test_run_emits_only_final_json_on_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "clip.mp4"
            media.write_bytes(b"not-a-real-video")
            with mock.patch.object(media_probe, "find_tool", return_value=Path("/fake/ffprobe")), fake_ffprobe(), redirect_stdout(
                io.StringIO()
            ) as stdout:
                code = media_probe.run(make_args(files=[str(media)]))
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["exit_code"], 0)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["tools"]["ffprobe"], "/fake/ffprobe")
            self.assertEqual(payload["files"][0]["width"], 1920)
            self.assertEqual(payload["files"][0]["duration"], 12.5)

    def test_missing_file_exit_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.mp4"
            with mock.patch.object(media_probe, "find_tool", return_value=Path("/fake/ffprobe")), fake_ffprobe(), redirect_stdout(
                io.StringIO()
            ) as stdout:
                code = media_probe.run(make_args(files=[str(missing)]))
            self.assertEqual(code, 3)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "file_error")
            self.assertFalse(payload["files"][0]["ok"])

    def test_unreadable_file_exit_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "clip.mp4"
            media.write_bytes(b"data")
            with mock.patch.object(media_probe, "find_tool", return_value=Path("/fake/ffprobe")), mock.patch.object(
                media_probe.os, "access", return_value=False
            ), fake_ffprobe(), redirect_stdout(io.StringIO()) as stdout:
                code = media_probe.run(make_args(files=[str(media)]))
            self.assertEqual(code, 3)
            payload = json.loads(stdout.getvalue())
            self.assertIn("不可读", payload["files"][0]["error"])

    def test_ffprobe_failure_exit_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "clip.mp4"
            media.write_bytes(b"data")
            with mock.patch.object(media_probe, "find_tool", return_value=Path("/fake/ffprobe")), fake_ffprobe(
                returncode=1, stdout="", stderr="invalid data"
            ), redirect_stdout(io.StringIO()) as stdout:
                code = media_probe.run(make_args(files=[str(media)]))
            self.assertEqual(code, 3)
            payload = json.loads(stdout.getvalue())
            self.assertIn("invalid data", payload["files"][0]["error"])

    def test_main_missing_tool_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "clip.mp4"
            media.write_bytes(b"data")
            with mock.patch.object(media_probe, "find_tool", return_value=None), redirect_stdout(
                io.StringIO()
            ) as stdout:
                code = media_probe.main([str(media), "--json"])
            self.assertEqual(code, 2)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "missing_tool")
            self.assertIn("ffprobe", payload["error"])

    def test_main_usage_error_exit_1(self):
        self.assertEqual(media_probe.main([]), 1)

    def test_non_json_mode_is_human_readable(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "clip.mp4"
            media.write_bytes(b"data")
            with mock.patch.object(media_probe, "find_tool", return_value=Path("/fake/ffprobe")), fake_ffprobe(), redirect_stdout(
                io.StringIO()
            ) as stdout:
                code = media_probe.run(make_args(files=[str(media)], json=False))
            self.assertEqual(code, 0)
            text = stdout.getvalue()
            self.assertIn("1920x1080", text)
            self.assertIn("29.97 fps", text)


if __name__ == "__main__":
    unittest.main()
