#!/usr/bin/env python3
"""Locate ffprobe/ffmpeg and report deterministic media facts (duration, size, fps, audio)."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_MISSING_TOOL = 2
EXIT_FILE_ERROR = 3

COMMON_BIN_DIRS = [
    Path("/usr/local/bin"),
    Path("/opt/homebrew/bin"),
    Path("/opt/local/bin"),
    Path("/usr/bin"),
    Path("/bin"),
]


class UsageError(Exception):
    """用法或参数错误（退出码 1）。"""


class MissingToolError(Exception):
    """缺少 ffmpeg/ffprobe 依赖（退出码 2）。"""


class FileError(Exception):
    """媒体文件缺失、不可读或无法探测（退出码 3）。"""


def build_parser():
    parser = argparse.ArgumentParser(
        prog="media-probe.py",
        description="可验证地定位 ffprobe/ffmpeg，并探测媒体文件的时长、宽高、帧率、音轨数。",
        epilog=(
            "退出码：0 成功；1 用法错误；2 缺少 ffmpeg/ffprobe 依赖；3 文件缺失或不可读。\n"
            "工具定位顺序：--ffmpeg-dir → FFMPEG_DIR 环境变量 → PATH → 常见安装目录。\n"
            "找不到工具时不安装、不联网，直接返回退出码 2 与修复指引。\n"
            "--json 时 stdout 只输出一个结构化 JSON 结果对象，人类可读信息走 stderr。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="+", metavar="MEDIA", help="要探测的媒体文件，至少一个")
    parser.add_argument(
        "--ffmpeg-dir",
        default=None,
        help="显式指定 ffmpeg/ffprobe 所在目录（优先级最高，替代 FFMPEG_DIR）",
    )
    parser.add_argument("--json", action="store_true", help="stdout 只输出一个 JSON 结果对象")
    parser.add_argument(
        "--timeout", type=float, default=30, help="每次 ffprobe 调用的超时秒数（默认 30）"
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
    ffprobe = find_tool("ffprobe", ffmpeg_dir)
    ffmpeg = find_tool("ffmpeg", ffmpeg_dir)
    if ffprobe is None:
        raise MissingToolError(
            "找不到 ffprobe：探测媒体依赖它。已按顺序检查 --ffmpeg-dir、FFMPEG_DIR、"
            "PATH 与常见安装目录。请先安装 ffmpeg（例如 brew install ffmpeg），或设置 "
            "FFMPEG_DIR 指向包含 ffmpeg/ffprobe 的目录后重试；本脚本不会自动安装。"
        )
    return ffprobe, ffmpeg


def run_capture(command, timeout):
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise FileError(f"ffprobe 超时（>{timeout:.0f}s）: {' '.join(command)}")
    except OSError as error:
        raise FileError(f"无法启动 ffprobe: {error}")


def probe_file(path, ffprobe, timeout):
    path = Path(path).expanduser()
    if not path.is_file():
        raise FileError(f"文件不存在或不是普通文件: {path}")
    if not os.access(path, os.R_OK):
        raise FileError(f"文件不可读: {path}")
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
        detail = (completed.stderr or completed.stdout or "").strip()[:500]
        raise FileError(f"ffprobe 无法读取 {path}: {detail}")
    try:
        data = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as error:
        raise FileError(f"ffprobe 输出不是 JSON: {path}: {error}")
    if not isinstance(data, dict):
        raise FileError(f"ffprobe 输出结构异常: {path}")
    return data


def parse_fps(stream):
    raw = stream.get("avg_frame_rate") or stream.get("r_frame_rate")
    if not raw or raw in ("0/0", "N/A"):
        return None, None
    try:
        numerator, denominator = raw.split("/", 1)
        value = float(numerator) / float(denominator)
    except (ValueError, ZeroDivisionError):
        return None, raw
    if value <= 0:
        return None, raw
    return round(value, 3), raw


def parse_probe(data, path):
    streams = data.get("streams", [])
    video = next(
        (s for s in streams if isinstance(s, dict) and s.get("codec_type") == "video"),
        None,
    )
    video_count = sum(1 for s in streams if isinstance(s, dict) and s.get("codec_type") == "video")
    audio_count = sum(1 for s in streams if isinstance(s, dict) and s.get("codec_type") == "audio")
    fmt = data.get("format", {}) or {}
    duration_raw = fmt.get("duration")
    if duration_raw in (None, "", "N/A") and video is not None:
        duration_raw = video.get("duration")
    try:
        duration = round(float(duration_raw), 3) if duration_raw not in (None, "", "N/A") else None
    except (TypeError, ValueError):
        duration = None
    width = None
    height = None
    if video is not None:
        try:
            width = int(video["width"]) if video.get("width") not in (None, "") else None
            height = int(video["height"]) if video.get("height") not in (None, "") else None
        except (TypeError, ValueError):
            pass
    fps, fps_raw = parse_fps(video) if video is not None else (None, None)
    return {
        "duration": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "fps_raw": fps_raw,
        "video_streams": video_count,
        "audio_streams": audio_count,
    }


def emit_final(args, result):
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for line in result.get("detail_lines", []):
            print(line)


def run(args):
    ffprobe, ffmpeg = locate_tools(args.ffmpeg_dir)
    results = []
    for raw in args.files:
        path = Path(raw).expanduser()
        try:
            data = probe_file(path, ffprobe, args.timeout)
            results.append({"file": str(path), "ok": True, **parse_probe(data, path)})
        except FileError as error:
            results.append({"file": str(path), "ok": False, "error": str(error)})
    failed = [result for result in results if not result["ok"]]
    detail_lines = []
    for result in results:
        if result["ok"]:
            fps_text = f"{result['fps']} fps" if result["fps"] is not None else "未知帧率"
            dims = f"{result['width']}x{result['height']}" if result["width"] is not None else "无视频流"
            detail_lines.append(
                f"{result['file']}: 时长 {result['duration']}s, {dims}, {fps_text}, "
                f"音轨 {result['audio_streams']}"
            )
        else:
            detail_lines.append(f"{result['file']}: 失败 - {result['error']}")
    tool_lines = [
        f"ffprobe: {ffprobe}",
        f"ffmpeg: {ffmpeg if ffmpeg else '未找到（探测不依赖它）'}",
    ]
    common = {
        "tools": {"ffprobe": str(ffprobe), "ffmpeg": str(ffmpeg) if ffmpeg else None},
        "files": results,
        "detail_lines": detail_lines + tool_lines,
    }
    if failed:
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": EXIT_FILE_ERROR,
                "status": "file_error",
                "error": f"{len(failed)} 个文件无法探测",
                "message": "存在无法探测的文件",
                **common,
            },
        )
        return EXIT_FILE_ERROR
    emit_final(
        args,
        {
            "ok": True,
            "exit_code": EXIT_OK,
            "status": "ok",
            "message": f"探测完成：{len(results)} 个文件",
            **common,
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
    except FileError as error:
        emit_error(args, error, EXIT_FILE_ERROR, "file_error")
        return EXIT_FILE_ERROR


if __name__ == "__main__":
    sys.exit(main())
