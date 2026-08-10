#!/usr/bin/env python3
"""Deterministic rough cut: normalize inputs to one target spec with ffmpeg, then concatenate."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_MISSING_TOOL = 2
EXIT_INPUT_ERROR = 3
EXIT_FFMPEG_ERROR = 4

COMMON_BIN_DIRS = [
    Path("/usr/local/bin"),
    Path("/opt/homebrew/bin"),
    Path("/opt/local/bin"),
    Path("/usr/bin"),
    Path("/bin"),
]


class UsageError(Exception):
    """用法或输入规格错误（退出码 1）。"""


class MissingToolError(Exception):
    """缺少 ffmpeg/ffprobe 依赖（退出码 2）。"""


class InputError(Exception):
    """输入文件缺失或不可读（退出码 3）。"""


class FfmpegError(Exception):
    """ffmpeg 执行失败（退出码 4）。"""


def build_parser():
    parser = argparse.ArgumentParser(
        prog="rough-cut.py",
        description="确定性粗剪：先用 ffmpeg 把输入规范化为统一 width/height/fps 与音频策略，再按顺序拼接。",
        epilog=(
            "退出码：0 成功；1 用法或输入规格错误；2 缺少 ffmpeg/ffprobe 依赖；"
            "3 输入文件缺失或不可读；4 ffmpeg 执行失败。\n"
            "输入规格不一致且未给显式 --width/--height/--fps 时直接报错并列出各输入规格，"
            "绝不静默损坏。\n"
            "输出写入 <project>/rough-cut/<output-name>/vNN/，vNN 自动递增，绝不覆盖已有版本。\n"
            "--json 时 stdout 只输出一个结构化 JSON 结果对象，人类可读信息走 stderr。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("inputs", nargs="+", metavar="INPUT", help="要拼接的媒体文件，至少一个，按给定顺序拼接")
    parser.add_argument("--width", type=int, default=None, help="显式输出宽度（不提供时要求所有输入一致）")
    parser.add_argument("--height", type=int, default=None, help="显式输出高度（不提供时要求所有输入一致）")
    parser.add_argument("--fps", type=float, default=None, help="显式输出帧率（不提供时要求所有输入一致）")
    parser.add_argument(
        "--audio",
        choices=("keep", "drop"),
        default="keep",
        help="音频策略：keep 保留各输入音轨并统一转码，无音轨输入补静音；drop 输出无音轨（默认 keep）",
    )
    parser.add_argument(
        "--ffmpeg-dir",
        default=None,
        help="显式指定 ffmpeg/ffprobe 所在目录（优先级最高，替代 FFMPEG_DIR）",
    )
    parser.add_argument("--project", default=".", help="项目目录，输出在 <project>/rough-cut/ 下（默认当前目录）")
    parser.add_argument("--output-name", default=None, help="输出名称，默认取第一个输入文件名加 -rough-cut")
    parser.add_argument("--json", action="store_true", help="stdout 只输出一个 JSON 结果对象")
    parser.add_argument("--dry-run", action="store_true", help="只校验并打印计划，不写入任何文件")
    parser.add_argument(
        "--timeout", type=float, default=600, help="每次 ffmpeg/ffprobe 调用的超时秒数（默认 600）"
    )
    return parser


def find_tool(name, ffmpeg_dir=None):
    """Search order: --ffmpeg-dir, FFMPEG_DIR, PATH, then common install dirs."""
    candidates = []
    for raw in (ffmpeg_dir, os.environ.get("FFMPEG_DIR")):
        if raw:
            candidates.append(Path(raw).expanduser() / name)
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    which = shutil.which(name)
    if which:
        return Path(which)
    for directory in COMMON_BIN_DIRS:
        candidate = directory / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def locate_tools(ffmpeg_dir):
    ffmpeg = find_tool("ffmpeg", ffmpeg_dir)
    ffprobe = find_tool("ffprobe", ffmpeg_dir)
    missing = [name for name, tool in (("ffmpeg", ffmpeg), ("ffprobe", ffprobe)) if tool is None]
    if missing:
        raise MissingToolError(
            "找不到 " + "、".join(missing) + "：粗剪依赖它们。已按顺序检查 --ffmpeg-dir、"
            "FFMPEG_DIR、PATH 与常见安装目录。请先安装 ffmpeg（例如 brew install ffmpeg），"
            "或设置 FFMPEG_DIR 指向包含 ffmpeg/ffprobe 的目录后重试；本脚本不会自动安装。"
        )
    return ffmpeg, ffprobe


def run_capture(command, timeout):
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise FfmpegError(f"命令超时（>{timeout:.0f}s）: {' '.join(command)[:300]}")
    except OSError as error:
        raise FfmpegError(f"无法启动 {command[0]}: {error}")


def check_success(command, timeout):
    completed = run_capture(command, timeout)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[-800:]
        raise FfmpegError(
            f"命令失败（退出码 {completed.returncode}）: {' '.join(command)[:200]}\n{detail}"
        )
    return completed


def probe_input(path, ffprobe, timeout):
    path = Path(path).expanduser()
    if not path.is_file():
        raise InputError(f"输入文件不存在或不是普通文件: {path}")
    if not os.access(path, os.R_OK):
        raise InputError(f"输入文件不可读: {path}")
    command = [
        str(ffprobe),
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    completed = run_capture(command, timeout)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[:300]
        raise InputError(f"ffprobe 无法读取 {path}: {detail}")
    try:
        data = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as error:
        raise InputError(f"ffprobe 输出不是 JSON: {path}: {error}")
    streams = data.get("streams", []) if isinstance(data, dict) else []
    video = next(
        (s for s in streams if isinstance(s, dict) and s.get("codec_type") == "video"),
        None,
    )
    audio_count = sum(1 for s in streams if isinstance(s, dict) and s.get("codec_type") == "audio")
    fmt = data.get("format", {}) or {}
    duration_raw = fmt.get("duration")
    if duration_raw in (None, "", "N/A") and video is not None:
        duration_raw = video.get("duration")
    try:
        duration = round(float(duration_raw), 3) if duration_raw not in (None, "", "N/A") else None
    except (TypeError, ValueError):
        duration = None
    spec = {"width": None, "height": None, "fps": None}
    if video is not None:
        try:
            spec["width"] = int(video["width"]) if video.get("width") not in (None, "") else None
            spec["height"] = int(video["height"]) if video.get("height") not in (None, "") else None
        except (TypeError, ValueError):
            pass
        raw_fps = video.get("avg_frame_rate") or video.get("r_frame_rate")
        if raw_fps and raw_fps not in ("0/0", "N/A"):
            try:
                numerator, denominator = raw_fps.split("/", 1)
                fps = float(numerator) / float(denominator)
                spec["fps"] = round(fps, 3) if fps > 0 else None
            except (ValueError, ZeroDivisionError):
                spec["fps"] = None
    return {"path": str(path), "duration": duration, "audio_streams": audio_count, **spec}


def resolve_target(probed, explicit):
    target = {}
    derived = {}
    for field in ("width", "height", "fps"):
        if explicit.get(field) is not None:
            target[field] = explicit[field]
            continue
        values = {item[field] for item in probed}
        if len(values) != 1 or None in values:
            mismatch = {
                item["path"]: {key: item[key] for key in ("width", "height", "fps")}
                for item in probed
            }
            raise UsageError(
                "输入规格不一致且未给显式目标（--width/--height/--fps），已停止而不是静默损坏:\n"
                + json.dumps(mismatch, ensure_ascii=False, indent=2)
            )
        target[field] = values.pop()
        derived[field] = True
    target["derived"] = bool(derived)
    return target


def validate_target(target):
    if target["width"] is None or target["height"] is None:
        raise UsageError("必须得到明确的输出宽高（显式 --width/--height，或所有输入一致）")
    if target["fps"] is None:
        raise UsageError("必须得到明确的输出帧率（显式 --fps，或所有输入一致）")
    for field in ("width", "height"):
        if target[field] < 1 or target[field] % 2 != 0:
            raise UsageError(f"{field} 必须为正偶数（libx264/yuv420p 要求），当前: {target[field]}")
    if target["fps"] < 1:
        raise UsageError(f"输出帧率必须 >= 1，当前: {target['fps']}")


def normalize_name(value, option):
    value = value.strip()
    if not value or value in (".", ".."):
        raise UsageError(f"{option} 不能为空、. 或 ..")
    if "/" in value or "\\" in value:
        raise UsageError(f"{option} 不能包含路径分隔符")
    return value


def next_version_dir(base):
    existing = []
    if base.is_dir():
        for child in base.iterdir():
            if not child.is_dir() or not child.name.startswith("v"):
                continue
            try:
                existing.append(int(child.name[1:]))
            except ValueError:
                continue
    number = max(existing, default=0) + 1
    return base / f"v{number:02d}", f"v{number:02d}"


def build_normalize_command(ffmpeg, source, target, audio_policy, has_audio, output):
    command = [str(ffmpeg), "-y", "-i", str(source)]
    if audio_policy == "keep" and not has_audio:
        command += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
    command += [
        "-vf",
        (
            f"scale={target['width']}:{target['height']}:force_original_aspect_ratio=decrease,"
            f"pad={target['width']}:{target['height']}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"fps={target['fps']}"
        ),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "veryfast",
        "-movflags", "+faststart",
    ]
    if audio_policy == "keep":
        command += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest"]
    else:
        command += ["-an"]
    command.append(str(output))
    return command


def build_concat_command(ffmpeg, list_file, audio_policy, output):
    command = [
        str(ffmpeg),
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-fflags", "+genpts",
        "-c", "copy",
        "-movflags", "+faststart",
    ]
    if audio_policy == "drop":
        command.append("-an")
    command.append(str(output))
    return command


def emit_progress(args, **fields):
    if args.json:
        print(json.dumps(fields, ensure_ascii=False), file=sys.stderr)
    else:
        text = fields.get("message")
        if text:
            print(text, file=sys.stderr)


def emit_final(args, result):
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        text = result.get("message")
        if text:
            print(text)
        for line in result.get("detail_lines", []):
            print(line)


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def run(args):
    ffmpeg, ffprobe = locate_tools(args.ffmpeg_dir)
    explicit = {"width": args.width, "height": args.height, "fps": args.fps}
    probed = [probe_input(raw, ffprobe, args.timeout) for raw in args.inputs]
    target = resolve_target(probed, explicit)
    validate_target(target)
    output_name = normalize_name(
        args.output_name or f"{Path(args.inputs[0]).stem}-rough-cut", "--output-name"
    )
    project = Path(args.project).expanduser()
    base = project / "rough-cut" / output_name
    version_dir, version = next_version_dir(base)
    if args.dry_run:
        emit_final(
            args,
            {
                "ok": True,
                "exit_code": EXIT_OK,
                "dry_run": True,
                "status": "prepared",
                "project": str(project),
                "output_name": output_name,
                "version": version,
                "version_dir": str(version_dir),
                "target": target,
                "audio_policy": args.audio,
                "inputs": probed,
                "message": "dry-run: 校验通过，未写入任何文件",
                "detail_lines": [
                    f"将写入: {version_dir}",
                    "目标规格: " + json.dumps(target, ensure_ascii=False),
                    f"音频策略: {args.audio}",
                ],
            },
        )
        return EXIT_OK
    try:
        version_dir.mkdir(parents=True)
        segments_dir = version_dir / "segments"
        segments_dir.mkdir()
        segments = []
        for index, info in enumerate(probed, start=1):
            segment = segments_dir / f"seg-{index:02d}.mp4"
            emit_progress(
                args,
                event="normalize",
                index=index,
                message=f"规范化 {index}/{len(probed)}: {info['path']}",
            )
            command = build_normalize_command(
                ffmpeg,
                info["path"],
                target,
                args.audio,
                info["audio_streams"] > 0,
                segment,
            )
            check_success(command, args.timeout)
            segments.append(str(segment))
        list_file = version_dir / "segments.txt"
        list_file.write_text(
            "".join(f"file '{seg.replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'\n" for seg in segments),
            encoding="utf-8",
        )
        output = version_dir / "final.mp4"
        emit_progress(args, event="concat", message="拼接中")
        check_success(build_concat_command(ffmpeg, list_file, args.audio, output), args.timeout)
        if not output.is_file() or output.stat().st_size == 0:
            raise FfmpegError(f"拼接未产生有效输出: {output}")
        version_json = {
            "schema_version": 1,
            "version": version,
            "created_at": now_iso(),
            "target": target,
            "audio_policy": args.audio,
            "inputs": probed,
            "output": str(output),
            "segments": segments,
        }
        (version_dir / "version.json").write_text(
            json.dumps(version_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except Exception as error:
        if version_dir.exists():
            shutil.rmtree(version_dir, ignore_errors=True)
        raise
    emit_final(
        args,
        {
            "ok": True,
            "exit_code": EXIT_OK,
            "dry_run": False,
            "status": "completed",
            "version": version,
            "version_dir": str(version_dir),
            "output": str(output),
            "target": target,
            "audio_policy": args.audio,
            "inputs": probed,
            "segments": segments,
            "message": f"粗剪完成: {output}",
            "detail_lines": [
                f"版本: {version}",
                f"输出: {output}",
                f"输入: {len(probed)} 段",
                f"目标: {target['width']}x{target['height']}@{target['fps']}fps, 音频策略 {args.audio}",
            ],
        },
    )
    return EXIT_OK


def emit_error(args, error, code, status):
    if args.json:
        print(
            json.dumps(
                {
                    "ok": False,
                    "exit_code": code,
                    "status": status,
                    "error": str(error),
                    "message": str(error),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"错误: {error}", file=sys.stderr)


def main(argv=None):
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as error:
        return 0 if error.code in (None, 0) else EXIT_USAGE
    if args.timeout <= 0:
        print("错误: --timeout 必须 > 0", file=sys.stderr)
        return EXIT_USAGE
    try:
        return run(args)
    except UsageError as error:
        emit_error(args, error, EXIT_USAGE, "usage_error")
        return EXIT_USAGE
    except MissingToolError as error:
        emit_error(args, error, EXIT_MISSING_TOOL, "missing_tool")
        return EXIT_MISSING_TOOL
    except InputError as error:
        emit_error(args, error, EXIT_INPUT_ERROR, "input_error")
        return EXIT_INPUT_ERROR
    except FfmpegError as error:
        emit_error(args, error, EXIT_FFMPEG_ERROR, "ffmpeg_error")
        return EXIT_FFMPEG_ERROR


if __name__ == "__main__":
    sys.exit(main())
