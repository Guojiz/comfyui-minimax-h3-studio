#!/usr/bin/env python3
"""Render a Remotion composition into a project version directory.

Remotion is a programmatic video toolkit (React-based) suited to motion
graphics, data visualization, titles, and overlay compositions. This script
only orchestrates a render with deterministic version protection; it does not
install Remotion or write the composition source. Dependencies missing produce
an actionable error (exit 2) instead of an automatic install.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_DEPENDENCY = 2
EXIT_INPUT = 3
EXIT_RENDER = 4

REMOTION_PACKAGE_DIR = "node_modules/remotion"


class UsageError(Exception):
    pass


class DependencyError(Exception):
    pass


class InputError(Exception):
    pass


class RenderError(Exception):
    pass


def build_parser():
    parser = argparse.ArgumentParser(
        prog="remotion-render.py",
        description="把 Remotion composition 渲染为视频，保存到 "
        "<project>/remotion/<output-name>/vNN/，版本自动递增、绝不覆盖。",
        epilog=(
            "退出码：0 成功；1 用法错误；2 缺少 node/Remotion 依赖；"
            "3 入口或项目路径错误；4 渲染失败。\n"
            "脚本不自动安装 Remotion，也不会替你写 composition 源码。\n"
            "示例：python3 scripts/remotion-render.py --entry src/Index.tsx "
            "--output-name title-card --project <项目> --json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project", default=".", help="项目目录（默认当前目录）")
    parser.add_argument("--entry", required=True, help="Remotion 入口文件（如 src/Index.tsx）")
    parser.add_argument("--composition", default=None, help="composition id（默认由 Remotion 决定）")
    parser.add_argument("--output-name", default=None, help="输出目录名（默认取入口文件名）")
    parser.add_argument("--width", type=int, default=None, help="目标宽度（可选）")
    parser.add_argument("--height", type=int, default=None, help="目标高度（可选）")
    parser.add_argument("--fps", type=int, default=None, help="目标帧率（可选）")
    parser.add_argument("--node-dir", default=None, help="node/npx 所在目录（默认 PATH）")
    parser.add_argument("--timeout", type=int, default=1800, help="渲染总超时秒数（默认 1800）")
    parser.add_argument("--json", action="store_true", help="stdout 只输出最终 JSON 结果")
    parser.add_argument("--dry-run", action="store_true", help="只校验并打印计划，不渲染")
    return parser


def emit_final(args, result):
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("message"):
            print(result["message"])
        for line in result.get("detail_lines", []):
            print(line)


def find_node(node_dir):
    if node_dir:
        base = Path(node_dir).expanduser()
        node = base / "node"
        npx = base / "npx"
        if node.is_file() and npx.is_file():
            return str(node), str(npx)
        raise DependencyError(f"--node-dir 内未找到 node/npx: {node_dir}")
    node = shutil.which("node")
    npx = shutil.which("npx")
    if not node or not npx:
        raise DependencyError(
            "未找到 node/npx。请先安装 Node.js 20+（例如 brew install node），"
            "或设置 --node-dir 指向包含 node 与 npx 的目录"
        )
    return node, npx


def ensure_remotion_installed(project):
    package = Path(project).expanduser() / REMOTION_PACKAGE_DIR
    if (package / "package.json").is_file():
        return
    raise DependencyError(
        f"项目未安装 Remotion 依赖（{package} 不存在）。请在本机项目内执行：\n"
        "  npm install remotion @remotion/cli\n"
        "并保留 package.json / node_modules（两者都不应提交到公开仓库）"
    )


def render(argv, timeout):
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout if isinstance(error.stdout, str) else ""
        stderr = error.stderr if isinstance(error.stderr, str) else ""
        stderr += f"\nERROR: remotion render timed out after {timeout}s"
        return subprocess.CompletedProcess(argv, 124, stdout, stderr)


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.timeout < 1:
        print("错误: --timeout 必须 >= 1", file=sys.stderr)
        return EXIT_USAGE
    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": EXIT_INPUT,
                "status": "input_error",
                "error": f"项目目录不存在: {project}",
            },
        )
        return EXIT_INPUT
    entry = Path(args.entry).expanduser()
    if not entry.is_file():
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": EXIT_INPUT,
                "status": "input_error",
                "error": f"Remotion 入口不存在: {entry}",
            },
        )
        return EXIT_INPUT
    try:
        node, npx = find_node(args.node_dir)
        ensure_remotion_installed(project)
    except DependencyError as error:
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": EXIT_DEPENDENCY,
                "status": "dependency_missing",
                "error": str(error),
                "message": "缺少依赖，未执行渲染",
            },
        )
        return EXIT_DEPENDENCY

    output_name = args.output_name or entry.stem
    out_root = project / "remotion" / output_name
    versions = []
    if out_root.is_dir():
        for child in out_root.iterdir():
            if child.is_dir() and child.name.startswith("v"):
                try:
                    versions.append(int(child.name[1:]))
                except ValueError:
                    pass
    next_version = max(versions, default=0) + 1
    version_dir = out_root / f"v{next_version:02d}"
    if args.dry_run:
        emit_final(
            args,
            {
                "ok": True,
                "exit_code": EXIT_OK,
                "dry_run": True,
                "status": "prepared",
                "version_dir": str(version_dir),
                "command": [
                    npx,
                    "remotion",
                    "render",
                    str(entry),
                ],
                "message": "dry-run: 校验通过，未渲染、未写文件",
                "detail_lines": [f"将输出到: {version_dir}"],
            },
        )
        return EXIT_OK

    version_dir.mkdir(parents=True, exist_ok=False)
    output_file = version_dir / "out.mp4"
    cmd = [
        npx,
        "remotion",
        "render",
        str(entry),
        str(output_file),
        "--codec",
        "h264",
    ]
    if args.composition:
        cmd += ["--composition", args.composition]
    if args.width:
        cmd += ["--width", str(args.width)]
    if args.height:
        cmd += ["--height", str(args.height)]
    if args.fps:
        cmd += ["--fps", str(args.fps)]
    result = render(cmd, args.timeout)
    if result.returncode != 0:
        for path in (version_dir, out_root):
            try:
                path.rmdir()
            except OSError:
                break
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": EXIT_RENDER,
                "status": "render_failed",
                "error": (result.stderr or result.stdout or "remotion render failed")[:2000],
                "message": "渲染失败，已清理未完成版本目录",
            },
        )
        return EXIT_RENDER
    if not output_file.is_file() or output_file.stat().st_size == 0:
        for path in (version_dir, out_root):
            try:
                path.rmdir()
            except OSError:
                break
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": EXIT_RENDER,
                "status": "render_failed",
                "error": "渲染结束但输出文件缺失或为空",
                "message": "渲染失败，已清理未完成版本目录",
            },
        )
        return EXIT_RENDER
    version_info = {
        "schema_version": 1,
        "output_name": output_name,
        "version": f"v{next_version:02d}",
        "entry": str(entry),
        "composition": args.composition,
        "target": {
            "width": args.width,
            "height": args.height,
            "fps": args.fps,
        },
        "output_file": str(output_file),
        "rendered_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "node": node,
    }
    (version_dir / "version.json").write_text(
        json.dumps(version_info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    emit_final(
        args,
        {
            "ok": True,
            "exit_code": EXIT_OK,
            "status": "rendered",
            "version_dir": str(version_dir),
            "output_file": str(output_file),
            "version_info": version_info,
            "message": f"渲染完成: {output_file}",
            "detail_lines": [f"记录: {version_dir / 'version.json'}"],
        },
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
