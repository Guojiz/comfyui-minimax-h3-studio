#!/usr/bin/env python3
"""Approved-only delivery: copy or hardlink manifest files into a dist dir and record hashes."""

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

EXIT_OK = 0
EXIT_USAGE = 1
EXIT_MISSING_FILE = 3
EXIT_DELIVERY_ERROR = 4

ENTRY_RESERVED = {"path", "role", "sha256", "source", "size"}
META_RESERVED = {"files", "schema_version"}


class UsageError(Exception):
    """清单或用法错误（退出码 1）。"""


class MissingFileError(Exception):
    """清单列出的文件缺失、不可读或为空（退出码 3）。"""


class DeliveryError(Exception):
    """交付写入或校验失败（退出码 4）。"""


def build_parser():
    parser = argparse.ArgumentParser(
        prog="deliver.py",
        description="approved-only 交付：读取交付清单 JSON，校验文件后复制（或硬链接）到 dist 并生成 delivery.json。",
        epilog=(
            "退出码：0 成功；1 清单或用法错误；3 清单列出的文件缺失、不可读或为空；"
            "4 交付写入/校验失败。\n"
            "只处理清单中列出的文件，绝不移动原始文件，绝不额外复制未列出的文件。\n"
            "清单相对路径相对于清单文件所在目录解析；其余顶层字段（run/workflow/instance/"
            "decision 等）透传到 delivery.json，条目级字段覆盖顶层。\n"
            "已有 delivery.json 的 dist 目录受保护，不会覆盖。\n"
            "--json 时 stdout 只输出一个结构化 JSON 结果对象，人类可读信息走 stderr。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("manifest", metavar="MANIFEST.json", help="交付清单 JSON 文件")
    parser.add_argument(
        "--project", default=".", help="项目目录，dist 默认放 <project>/dist（默认当前目录）"
    )
    parser.add_argument("--dist", default=None, help="交付目录（默认 <project>/dist）")
    parser.add_argument(
        "--link", action="store_true", help="用硬链接代替复制（要求与 dist 在同一文件系统）"
    )
    parser.add_argument("--json", action="store_true", help="stdout 只输出一个 JSON 结果对象")
    parser.add_argument("--dry-run", action="store_true", help="只校验并打印计划，不写入任何文件")
    return parser


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path):
    path = Path(path).expanduser()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise UsageError(f"无法读取交付清单 {path}: {error}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise UsageError(f"交付清单 JSON 解析失败: {error}")
    if isinstance(data, list):
        return data, {}
    if isinstance(data, dict):
        files = data.get("files")
        if not isinstance(files, list):
            raise UsageError("交付清单对象必须包含 files 列表（或直接是条目列表）")
        meta = {key: value for key, value in data.items() if key not in META_RESERVED}
        return files, meta
    raise UsageError("交付清单必须是 JSON 对象（含 files 列表）或条目列表")


def parse_entries(files, manifest_path, project_root=None):
    base = Path(manifest_path).expanduser().resolve().parent
    if project_root is None:
        project_root = base
    root = Path(project_root).expanduser().resolve()
    entries = []
    for index, item in enumerate(files, start=1):
        if not isinstance(item, dict):
            raise UsageError(f"清单第 {index} 项必须是对象")
        raw_path = item.get("path")
        role = item.get("role")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise UsageError(f"清单第 {index} 项缺少 path 字符串")
        if not isinstance(role, str) or not role.strip():
            raise UsageError(f"清单第 {index} 项（{raw_path}）缺少 role 字符串")
        if raw_path.startswith("~"):
            raise UsageError(f"清单第 {index} 项 path 不允许使用 ~ 展开: {raw_path}")
        source = Path(raw_path)
        if source.is_absolute():
            raise UsageError(f"清单第 {index} 项 path 必须是项目内相对路径: {raw_path}")
        if any(part in ("..", ".") or not part for part in source.parts):
            raise UsageError(f"清单第 {index} 项 path 含非法路径段: {raw_path}")
        if not source.is_absolute():
            source = base / source
        resolved = source.resolve()
        if not resolved.is_relative_to(root):
            raise UsageError(
                f"清单第 {index} 项 path 越出项目根目录: {raw_path}（根: {root}）"
            )
        entries.append({"index": index, "role": role.strip(), "source": resolved, "raw": item})
    return entries


def validate_sources(entries):
    problems = []
    for entry in entries:
        source = entry["source"]
        if not source.is_file():
            problems.append(f"文件不存在或不是普通文件: {source}")
            continue
        if not os.access(source, os.R_OK):
            problems.append(f"文件不可读: {source}")
            continue
        try:
            entry["size"] = source.stat().st_size
        except OSError as error:
            problems.append(f"无法读取文件信息 {source}: {error}")
            continue
        if entry["size"] == 0:
            problems.append(f"文件为空: {source}")
            continue
        entry["sha256"] = sha256_file(source)
    if problems:
        raise MissingFileError("存在不可交付的文件:\n" + "\n".join(problems))
    return entries


def check_filenames(entries):
    seen = {}
    for entry in entries:
        name = entry["source"].name
        if name in seen:
            raise UsageError(
                f"清单内文件名冲突: {name}（{seen[name]} 与 {entry['source']}），"
                "请先改名或拆分清单"
            )
        seen[name] = str(entry["source"])
    return seen


def record(entry, meta):
    passthrough = {
        key: value for key, value in entry["raw"].items() if key not in ENTRY_RESERVED
    }
    result = {
        "path": entry["source"].name,
        "role": entry["role"],
        "source": str(entry["source"]),
        "sha256": entry.get("sha256"),
        "size": entry.get("size"),
    }
    result.update({**meta, **passthrough})
    return result


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
    manifest_path = Path(args.manifest).expanduser()
    files, meta = load_manifest(manifest_path)
    entries = parse_entries(files, manifest_path, project_root=args.project)
    if not entries:
        raise UsageError("清单中没有任何文件")
    validate_sources(entries)
    check_filenames(entries)
    project = Path(args.project).expanduser()
    dist = Path(args.dist).expanduser() if args.dist else project / "dist"
    if not dist.is_absolute():
        dist = project / dist
    delivery_file = dist / "delivery.json"
    if args.dry_run:
        emit_final(
            args,
            {
                "ok": True,
                "exit_code": EXIT_OK,
                "dry_run": True,
                "status": "prepared",
                "dist_dir": str(dist),
                "delivery_file": str(delivery_file),
                "link": args.link,
                "meta": meta,
                "files": [record(entry, meta) for entry in entries],
                "message": "dry-run: 校验通过，未写入任何文件",
                "detail_lines": [f"将交付到: {dist}", f"共 {len(entries)} 个文件"],
            },
        )
        return EXIT_OK
    if delivery_file.exists():
        raise UsageError(
            f"交付记录已存在: {delivery_file}；旧交付受保护，不会覆盖。"
            "请使用 --dist 指定新的交付目录。"
        )
    try:
        dist.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise DeliveryError(f"无法创建交付目录 {dist}: {error}")
    records = []
    for entry in entries:
        source = entry["source"]
        dest = dist / source.name
        if dest.exists():
            raise DeliveryError(f"交付目标已存在，不会覆盖: {dest}")
        try:
            if args.link:
                os.link(source, dest)
            else:
                shutil.copy2(source, dest)
        except OSError as error:
            raise DeliveryError(f"无法交付 {source} -> {dest}: {error}")
        dest_sha = sha256_file(dest)
        if dest_sha != entry["sha256"]:
            raise DeliveryError(f"交付校验失败: {dest} sha256 与源文件不一致")
        records.append(record(entry, meta))
        records[-1]["sha256"] = dest_sha
        records[-1]["size"] = entry["size"]
    payload = {
        "schema_version": 1,
        "created_at": now_iso(),
        "source_manifest": str(manifest_path),
        "dist_dir": str(dist),
        "link": args.link,
        "meta": meta,
        "files": records,
    }
    try:
        delivery_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except OSError as error:
        raise DeliveryError(f"无法写入交付记录 {delivery_file}: {error}")
    emit_final(
        args,
        {
            "ok": True,
            "exit_code": EXIT_OK,
            "dry_run": False,
            "status": "delivered",
            "dist_dir": str(dist),
            "delivery_file": str(delivery_file),
            "link": args.link,
            "files": records,
            "message": f"交付完成：{len(records)} 个文件",
            "detail_lines": [f"交付目录: {dist}", f"交付记录: {delivery_file}"]
            + [f"{item['role']}: {item['path']} ({item['sha256'][:12]}...)" for item in records],
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
    try:
        return run(args)
    except UsageError as error:
        emit_error(args, error, EXIT_USAGE, "usage_error")
        return EXIT_USAGE
    except MissingFileError as error:
        emit_error(args, error, EXIT_MISSING_FILE, "missing_file")
        return EXIT_MISSING_FILE
    except DeliveryError as error:
        emit_error(args, error, EXIT_DELIVERY_ERROR, "delivery_error")
        return EXIT_DELIVERY_ERROR


if __name__ == "__main__":
    sys.exit(main())
