import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_ROUGH_PATH = Path(__file__).resolve().parents[1] / "rough-cut.py"
_ROUGH_SPEC = importlib.util.spec_from_file_location("rough_cut_under_test", _ROUGH_PATH)
rough = importlib.util.module_from_spec(_ROUGH_SPEC)
_ROUGH_SPEC.loader.exec_module(rough)


VIDEO_SPEC = {
    "format": {"duration": "10.000"},
    "streams": [
        {
            "codec_type": "video",
            "width": 1280,
            "height": 720,
            "avg_frame_rate": "24/1",
            "r_frame_rate": "24/1",
        },
        {"codec_type": "audio", "codec_name": "aac"},
    ],
}

VIDEO_SPEC_NO_AUDIO = {
    "format": {"duration": "8.000"},
    "streams": [
        {
            "codec_type": "video",
            "width": 1280,
            "height": 720,
            "avg_frame_rate": "24/1",
            "r_frame_rate": "24/1",
        }
    ],
}


def patch_tools():
    def fake_find(name, ffmpeg_dir=None):
        return Path("/fake/bin") / name

    return mock.patch.object(rough, "find_tool", side_effect=fake_find)


def build_fake_run():
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[0].endswith("ffprobe"):
            stdout = VIDEO_SPEC_NO_AUDIO if "noaudio" in command[-1] else VIDEO_SPEC
            return mock.Mock(returncode=0, stdout=json.dumps(stdout), stderr="")
        output = Path(command[-1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"fake-video-bytes")
        return mock.Mock(returncode=0, stdout="", stderr="")

    return fake_run, calls


def make_inputs(tmp, names=("clip-a.mp4", "clip-b.mp4")):
    paths = []
    for name in names:
        path = Path(tmp) / name
        path.write_bytes(b"media")
        paths.append(str(path))
    return paths


class ResolveTargetTests(unittest.TestCase):
    def test_mismatch_without_explicit_target_raises_actionable(self):
        probed = [
            {"path": "a.mp4", "width": 1280, "height": 720, "fps": 24.0},
            {"path": "b.mp4", "width": 1920, "height": 1080, "fps": 24.0},
        ]
        with self.assertRaises(rough.UsageError) as ctx:
            rough.resolve_target(probed, {"width": None, "height": None, "fps": None})
        message = str(ctx.exception)
        self.assertIn("--width", message)
        self.assertIn("a.mp4", message)
        self.assertIn("b.mp4", message)

    def test_explicit_target_overrides_mismatch(self):
        probed = [
            {"path": "a.mp4", "width": 1280, "height": 720, "fps": 24.0},
            {"path": "b.mp4", "width": 1920, "height": 1080, "fps": 30.0},
        ]
        target = rough.resolve_target(
            probed, {"width": 1080, "height": 1920, "fps": 25}
        )
        self.assertEqual(target["width"], 1080)
        self.assertEqual(target["height"], 1920)
        self.assertEqual(target["fps"], 25)
        self.assertFalse(target["derived"])

    def test_target_derived_when_inputs_agree(self):
        probed = [
            {"path": "a.mp4", "width": 1280, "height": 720, "fps": 24.0},
            {"path": "b.mp4", "width": 1280, "height": 720, "fps": 24.0},
        ]
        target = rough.resolve_target(probed, {"width": None, "height": None, "fps": None})
        self.assertEqual(target["width"], 1280)
        self.assertEqual(target["height"], 720)
        self.assertEqual(target["fps"], 24.0)
        self.assertTrue(target["derived"])


class RunTests(unittest.TestCase):
    def test_locate_tools_raises_when_missing(self):
        with mock.patch.object(rough, "find_tool", return_value=None):
            with self.assertRaises(rough.MissingToolError):
                rough.locate_tools(None)

    def test_main_missing_tool_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs = make_inputs(tmp)
            with mock.patch.object(rough, "find_tool", return_value=None), redirect_stdout(
                io.StringIO()
            ) as stdout:
                code = rough.main(inputs + ["--json", "--project", tmp])
            self.assertEqual(code, 2)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "missing_tool")

    def test_main_creates_versioned_output_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs = make_inputs(tmp)
            fake_run, _ = build_fake_run()
            with patch_tools(), mock.patch.object(rough.subprocess, "run", side_effect=fake_run), redirect_stdout(
                io.StringIO()
            ) as stdout:
                code = rough.main(inputs + ["--json", "--project", tmp, "--output-name", "edit"])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "completed")
            self.assertEqual(payload["version"], "v01")
            version_dir = Path(payload["version_dir"])
            self.assertTrue(version_dir.is_dir())
            self.assertTrue((version_dir / "final.mp4").is_file())
            self.assertTrue((version_dir / "version.json").is_file())
            self.assertEqual(len(payload["segments"]), 2)
            self.assertEqual(len(payload["inputs"]), 2)
            self.assertEqual(payload["target"]["width"], 1280)
            version_json = json.loads((version_dir / "version.json").read_text(encoding="utf-8"))
            self.assertEqual(version_json["schema_version"], 1)
            self.assertEqual(len(version_json["inputs"]), 2)

    def test_second_run_auto_versions_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs = make_inputs(tmp)
            first = Path(tmp) / "rough-cut" / "edit" / "v01"
            first.mkdir(parents=True)
            fake_run, _ = build_fake_run()
            with patch_tools(), mock.patch.object(rough.subprocess, "run", side_effect=fake_run), redirect_stdout(
                io.StringIO()
            ) as stdout:
                code = rough.main(inputs + ["--json", "--project", tmp, "--output-name", "edit"])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["version"], "v02")
            self.assertNotIn("v01", payload["output"])

    def test_dry_run_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs = make_inputs(tmp)
            fake_run, calls = build_fake_run()
            with patch_tools(), mock.patch.object(rough.subprocess, "run", side_effect=fake_run), redirect_stdout(
                io.StringIO()
            ) as stdout:
                code = rough.main(
                    inputs + ["--json", "--project", tmp, "--output-name", "edit", "--dry-run"]
                )
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "prepared")
            self.assertTrue(payload["dry_run"])
            self.assertFalse(Path(tmp, "rough-cut").exists())
            ffmpeg_calls = [c for c in calls if not c[0].endswith("ffprobe")]
            self.assertEqual(ffmpeg_calls, [])

    def test_main_missing_input_exit_3(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch_tools(), redirect_stdout(io.StringIO()) as stdout:
                code = rough.main(
                    [str(Path(tmp) / "missing.mp4"), "--json", "--project", tmp]
                )
            self.assertEqual(code, 3)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "input_error")
            self.assertIn("不存在", payload["error"])

    def test_ffmpeg_failure_exit_4_and_cleans_up(self):
        def failing_run(command, **kwargs):
            if command[0].endswith("ffprobe"):
                return mock.Mock(returncode=0, stdout=json.dumps(VIDEO_SPEC), stderr="")
            return mock.Mock(returncode=1, stdout="", stderr="boom: encode failed")

        with tempfile.TemporaryDirectory() as tmp:
            inputs = make_inputs(tmp)
            with patch_tools(), mock.patch.object(rough.subprocess, "run", side_effect=failing_run), redirect_stdout(
                io.StringIO()
            ) as stdout:
                code = rough.main(inputs + ["--json", "--project", tmp, "--output-name", "edit"])
            self.assertEqual(code, 4)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "ffmpeg_error")
            self.assertIn("boom", payload["error"])
            self.assertFalse(Path(tmp, "rough-cut", "edit", "v01").exists())

    def test_odd_target_width_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs = make_inputs(tmp)
            fake_run, _ = build_fake_run()
            with patch_tools(), mock.patch.object(rough.subprocess, "run", side_effect=fake_run), redirect_stdout(
                io.StringIO()
            ) as stdout:
                code = rough.main(
                    inputs + ["--json", "--project", tmp, "--width", "641", "--height", "360", "--fps", "24"]
                )
            self.assertEqual(code, 1)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "usage_error")
            self.assertIn("正偶数", payload["error"])


class CommandTests(unittest.TestCase):
    def test_drop_policy_adds_an_to_ffmpeg_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs = make_inputs(tmp)
            fake_run, calls = build_fake_run()
            with patch_tools(), mock.patch.object(rough.subprocess, "run", side_effect=fake_run), redirect_stdout(
                io.StringIO()
            ):
                rough.main(inputs + ["--json", "--project", tmp, "--audio", "drop"])
        ffmpeg_calls = [c for c in calls if not c[0].endswith("ffprobe")]
        self.assertTrue(ffmpeg_calls)
        self.assertTrue(any("-an" in part for c in ffmpeg_calls for part in c))

    def test_keep_policy_adds_silence_for_audio_missing_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs = make_inputs(tmp, names=("clip-a.mp4", "noaudio-clip.mp4"))
            fake_run, calls = build_fake_run()
            with patch_tools(), mock.patch.object(rough.subprocess, "run", side_effect=fake_run), redirect_stdout(
                io.StringIO()
            ):
                rough.main(inputs + ["--json", "--project", tmp])
        ffmpeg_calls = [c for c in calls if not c[0].endswith("ffprobe")]
        self.assertTrue(any("anullsrc" in part for c in ffmpeg_calls for part in c))

    def test_normalize_and_concat_commands_are_built(self):
        target = {"width": 1280, "height": 720, "fps": 24.0, "derived": False}
        normalize = rough.build_normalize_command(
            Path("/fake/ffmpeg"), "a.mp4", target, "keep", True, Path("/tmp/seg-01.mp4")
        )
        normalize_text = " ".join(normalize)
        self.assertIn("scale=1280:720", normalize_text)
        self.assertIn("fps=24.0", normalize_text)
        self.assertIn("yuv420p", normalize_text)
        self.assertIn("-shortest", normalize_text)
        self.assertNotIn("anullsrc", normalize_text)
        concat = rough.build_concat_command(
            Path("/fake/ffmpeg"), Path("/tmp/segments.txt"), "drop", Path("/tmp/final.mp4")
        )
        concat_text = " ".join(concat)
        self.assertIn("concat", concat_text)
        self.assertIn("-an", concat_text)


if __name__ == "__main__":
    unittest.main()
