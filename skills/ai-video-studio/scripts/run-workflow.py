#!/usr/bin/env python3
"""Submit and poll an API-format ComfyUI workflow, saving the run under a project."""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SERVER = "http://127.0.0.1:8188"
SUBMIT_TIMEOUT = 30


class UsageError(Exception):
    """User-facing validation or usage error (exit code 1)."""


class ServerError(Exception):
    """Server or network failure (exit code 2)."""


class PollTimeout(Exception):
    """Polling did not reach a terminal state (exit code 4)."""


def build_parser():
    parser = argparse.ArgumentParser(
        prog="run-workflow.py",
        description="校验、提交并轮询 API 格式 ComfyUI 工作流；"
        "把实际提交、history 响应和产物清单保存到 <project>/runs/<run-name>/。",
        epilog=(
            "退出码：0 成功；1 工作流校验错误；2 命令行或服务器/网络错误；"
            "3 工作流执行错误；4 轮询超时。\n"
            "正式提交必须显式指定实例（--server 或 COMFY_SERVER），不会静默回退 localhost；"
            "已有同名 run 目录不会覆盖。\n"
            "--set 示例：--set '1.inputs.prompt=\"雨夜街道\"' --set '3.inputs.duration=5'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "workflow",
        metavar="WORKFLOW.json",
        help="API 格式工作流 JSON 文件，- 表示从 stdin 读取",
    )
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="NODE.FIELD=JSON_VALUE",
        help="修改节点字段，可重复；值必须是 JSON，字符串需带引号",
    )
    parser.add_argument(
        "--server",
        default=None,
        help=(
            "ComfyUI 地址；真实提交必须显式提供（CLI、COMFY_SERVER 或项目锁定的 "
            "localhost 实例），不允许静默回退到默认地址"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="stdout 只输出一个结构化 JSON 结果对象，人类可读信息走 stderr",
    )
    parser.add_argument("--timeout", type=int, default=900, help="轮询总超时秒数（默认 900）")
    parser.add_argument("--poll-interval", type=int, default=5, help="轮询间隔秒数（默认 5）")
    parser.add_argument(
        "--project",
        default=".",
        help="项目目录，run 保存到 <project>/runs/（默认当前目录）",
    )
    parser.add_argument("--run-name", default=None, help="run 目录名（默认自动生成）")
    parser.add_argument("--shot", default=None, help="关联的镜头 ID，例如 s03")
    parser.add_argument("--iteration", default=None, help="镜头迭代版本，例如 v1")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只校验并打印，不提交、不写文件",
    )
    return parser


def load_workflow(path):
    if path == "-":
        raw = sys.stdin.read()
    else:
        try:
            raw = Path(path).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise UsageError(f"找不到工作流文件: {path}")
        except OSError as error:
            raise UsageError(f"无法读取工作流文件 {path}: {error}")
    try:
        workflow = json.loads(raw)
    except json.JSONDecodeError as error:
        raise UsageError(f"工作流 JSON 解析失败: {error}")
    if not isinstance(workflow, dict) or not workflow:
        raise UsageError("工作流必须是包含节点的 JSON 对象")
    for node_id, node in workflow.items():
        if not isinstance(node, dict):
            raise UsageError(f"节点 {node_id} 必须是对象")
        if not isinstance(node.get("class_type"), str) or not node.get("class_type"):
            raise UsageError(f"节点 {node_id} 缺少 class_type")
        if not isinstance(node.get("inputs"), dict):
            raise UsageError(f"节点 {node_id} 缺少 inputs 对象")
    return workflow


def apply_sets(workflow, specs):
    for spec in specs:
        if "=" not in spec:
            raise UsageError(f"--set 必须是 NODE.FIELD=JSON_VALUE: {spec}")
        location, raw_value = spec.split("=", 1)
        parts = location.split(".")
        if len(parts) < 2:
            raise UsageError(f"--set 必须是 NODE.FIELD=JSON_VALUE: {spec}")
        node_id = parts[0]
        field_parts = parts[1:]
        if node_id not in workflow:
            available = ", ".join(sorted(workflow))
            raise UsageError(f"--set 指向不存在的节点 {node_id}（可用节点: {available}）")
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            raise UsageError(f"--set 的值不是合法 JSON: {raw_value!r}（字符串示例: '\"文本\"'）")
        cursor = workflow[node_id]
        for part in field_parts[:-1]:
            if not isinstance(cursor, dict) or part not in cursor:
                raise UsageError(f"节点 {node_id} 缺少字段路径 {'.'.join(field_parts)}")
            cursor = cursor[part]
        last = field_parts[-1]
        if not isinstance(cursor, dict) or last not in cursor:
            raise UsageError(f"节点 {node_id} 缺少字段 {'.'.join(field_parts)}")
        cursor[last] = value


def http_json(url, method="GET", payload=None, timeout=10):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            if not raw.strip():
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError as error:
                raise ServerError(f"响应不是 JSON: {url}: {error}（{raw[:200]}）")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")[:800]
        raise ServerError(f"HTTP {error.code}: {url} {body}".strip())
    except urllib.error.URLError as error:
        raise ServerError(f"无法连接 {url}: {error.reason}")
    except (TimeoutError, OSError) as error:
        raise ServerError(f"请求失败 {url}: {error}")


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def emit(args, **fields):
    """Write progress facts; stdout carries only the final JSON object in --json mode."""
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


def normalize_server_url(value):
    if not isinstance(value, str) or not value.strip():
        raise UsageError("ComfyUI server URL must not be empty")
    parts = urllib.parse.urlsplit(value.strip())
    if parts.scheme.lower() not in ("http", "https"):
        raise UsageError("ComfyUI server URL must use http/https")
    if not parts.netloc:
        raise UsageError("ComfyUI server URL is missing a host")
    if parts.username or parts.password:
        raise UsageError("ComfyUI server URL must not embed credentials")
    path = parts.path.rstrip("/")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def resolve_server(args):
    """Explicit server wins; env COMFY_SERVER is explicit configuration, never a silent default."""
    if args.server:
        return normalize_server_url(args.server)
    env_server = os.environ.get("COMFY_SERVER")
    if env_server:
        return normalize_server_url(env_server)
    return None


def require_submit_server(args, server):
    """Real submissions need an explicit instance; localhost must never be an implicit fallback."""
    if server:
        return server
    raise UsageError(
        "正式提交必须显式指定 ComfyUI 实例（--server 或 COMFY_SERVER 或项目锁定的 "
        "localhost 实例）；当前没有显式实例，已停止，未向默认地址提交"
    )


def normalize_run_name(name):
    if name in ("", ".", ".."):
        raise UsageError("--run-name 不能为空、. 或 ..")
    if "/" in name or "\\" in name:
        raise UsageError("--run-name 不能包含路径分隔符")
    return name


def normalize_label(value, option):
    if value is None:
        return None
    value = value.strip()
    if not value or value in (".", ".."):
        raise UsageError(f"{option} 不能为空、. 或 ..")
    if "/" in value or "\\" in value:
        raise UsageError(f"{option} 不能包含路径分隔符")
    return value


def poll_history(server, prompt_id, timeout, interval):
    start = time.monotonic()
    url = f"{server}/history/{urllib.parse.quote(prompt_id, safe='')}"
    while True:
        elapsed = time.monotonic() - start
        if elapsed >= timeout:
            raise PollTimeout(f"超过 {timeout}s 未等到工作流终态")
        history = http_json(url, timeout=max(interval * 2, 10))
        if isinstance(history, dict) and prompt_id in history:
            entry = history[prompt_id]
            if isinstance(entry, dict):
                status = entry.get("status") or {}
                if isinstance(status, dict):
                    if status.get("status_str") == "error":
                        return {
                            "state": "error",
                            "entry": entry,
                            "history": history,
                            "status": status,
                            "elapsed": time.monotonic() - start,
                        }
                    if status.get("completed") or status.get("status_str") == "success":
                        return {
                            "state": "success",
                            "entry": entry,
                            "history": history,
                            "status": status,
                            "elapsed": time.monotonic() - start,
                        }
        print(f"等待中 {elapsed:.0f}s ...")
        time.sleep(interval)


def execution_errors(status):
    errors = []
    for msg in status.get("messages", []):
        if not (isinstance(msg, list) and len(msg) >= 2):
            continue
        event, data = msg[0], msg[1]
        if event in ("execution_error", "execution_interrupted") and isinstance(data, dict):
            node_id = data.get("node_id", "")
            node_type = data.get("node_type", "")
            detail = data.get("exception_message") or data.get("exception_type") or data.get("error") or ""
            errors.append(f"节点 {node_id} ({node_type}): {str(detail)[:500]}")
        elif event == "execution_error" and isinstance(data, str):
            errors.append(data[:500])
    if not errors and status.get("status_str") == "error":
        errors.append("ComfyUI 报告执行错误")
    return errors


def extract_artifacts(outputs):
    artifacts = []
    seen = set()

    def walk(obj, node_id, hint):
        if isinstance(obj, dict):
            if isinstance(obj.get("filename"), str) and ("type" in obj or "subfolder" in obj):
                key = (obj.get("type", ""), obj.get("subfolder", ""), obj.get("filename", ""))
                if key not in seen:
                    seen.add(key)
                    artifacts.append(
                        {
                            "node": node_id,
                            "kind": hint or obj.get("type", "file"),
                            "filename": obj.get("filename", ""),
                            "subfolder": obj.get("subfolder", "") or "",
                            "type": obj.get("type", ""),
                        }
                    )
                return
            for key, value in obj.items():
                walk(value, node_id, key if isinstance(value, (dict, list)) else hint)
        elif isinstance(obj, list):
            for value in obj:
                walk(value, node_id, hint)

    for node_id, out in outputs.items():
        walk(out, node_id, None)
    return artifacts


def extract_local_video_artifacts(outputs):
    """Nodes may publish videos as ui.video_paths/video_filenames; turn them into artifacts."""
    artifacts = []
    seen = set()
    for node_id, out in outputs.items():
        if not isinstance(out, dict):
            continue
        ui = out.get("ui")
        if not isinstance(ui, dict):
            continue
        paths = ui.get("video_paths")
        names = ui.get("video_filenames")
        if not isinstance(paths, list) or not isinstance(names, list):
            continue
        for path, name in zip(paths, names):
            if not isinstance(path, str) or not isinstance(name, str):
                continue
            key = (path, name)
            if key in seen:
                continue
            seen.add(key)
            artifacts.append(
                {
                    "node": node_id,
                    "kind": "video",
                    "filename": name,
                    "subfolder": "",
                    "type": "local-video",
                    "source_path": path,
                    "view_url": None,
                }
            )
    return artifacts


def collect_ui(outputs):
    lines = []
    skipped = {"images", "gifs", "videos", "audio"}
    for node_id, out in outputs.items():
        if not isinstance(out, dict):
            continue
        ui = out.get("ui")
        if not isinstance(ui, dict):
            continue
        for key, values in ui.items():
            if key in skipped or not isinstance(values, list):
                continue
            texts = [v for v in values if isinstance(v, (str, int, float))]
            if texts:
                lines.append(f"节点 {node_id} {key}: " + ", ".join(str(v)[:200] for v in texts[:5]))
    return lines


def run(args):
    workflow = load_workflow(args.workflow)
    apply_sets(workflow, args.set)
    shot_id = normalize_label(args.shot, "--shot")
    iteration = normalize_label(args.iteration, "--iteration")
    default_prefix = "-".join(part for part in (shot_id, iteration) if part)
    if default_prefix:
        default_prefix += "-"
    run_name = normalize_run_name(
        args.run_name
        or f"{default_prefix}run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    )
    run_dir = Path(args.project).expanduser() / "runs" / run_name
    if args.dry_run:
        emit_final(
            args,
            {
                "ok": True,
                "exit_code": 0,
                "dry_run": True,
                "run_id": None,
                "run_name": run_name,
                "run_dir": str(run_dir),
                "prompt_id": None,
                "status": "prepared",
                "server": resolve_server(args),
                "workflow_id": Path(args.workflow).stem,
                "message": "dry-run: 校验通过，未提交、未写文件",
                "detail_lines": [
                    f"将保存到: {run_dir}",
                    "提交的 workflow:",
                    json.dumps(workflow, ensure_ascii=False, indent=2),
                ],
            },
        )
        return 0

    if run_dir.exists():
        raise UsageError(
            f"run 目录已存在: {run_dir}；旧 run 记录受保护，请使用新的 run-name"
        )
    server = require_submit_server(args, resolve_server(args))

    run_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema_version": 2,
        "run_name": run_name,
        "shot_id": shot_id,
        "iteration": iteration,
        "server": server,
        "server_source": (
            "cli"
            if args.server
            else "env:COMFY_SERVER"
            if os.environ.get("COMFY_SERVER")
            else "unknown"
        ),
        "workflow_file": args.workflow,
        "sets": list(args.set),
        "submitted_at": now_iso(),
        "status": "prepared",
    }
    save_json(run_dir / "workflow.json", workflow)
    save_json(run_dir / "run.json", meta)

    emit(args, event="submitting", server=server, message=f"提交任务到 {server}/prompt")
    try:
        response = http_json(f"{server}/prompt", method="POST", payload={"prompt": workflow}, timeout=SUBMIT_TIMEOUT)
    except ServerError as error:
        meta["status"] = "submit_error"
        meta["error"] = str(error)
        save_json(run_dir / "run.json", meta)
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": 2,
                "dry_run": False,
                "run_id": run_name,
                "run_name": run_name,
                "run_dir": str(run_dir),
                "prompt_id": None,
                "status": "submit_error",
                "error": str(error),
                "message": f"提交失败: {error}",
            },
        )
        return 2
    prompt_id = response.get("prompt_id") if isinstance(response, dict) else None
    if not prompt_id:
        meta["status"] = "submit_error"
        meta["error"] = f"提交响应缺少 prompt_id: {json.dumps(response, ensure_ascii=False)[:500]}"
        save_json(run_dir / "run.json", meta)
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": 2,
                "dry_run": False,
                "run_id": run_name,
                "run_name": run_name,
                "run_dir": str(run_dir),
                "prompt_id": None,
                "status": "submit_error",
                "error": meta["error"],
                "message": meta["error"],
            },
        )
        return 2

    meta["prompt_id"] = prompt_id
    meta["status"] = "submitted"
    save_json(run_dir / "run.json", meta)
    emit(args, event="submitted", prompt_id=prompt_id, message=f"任务 ID: {prompt_id}")

    try:
        outcome = poll_history(server, prompt_id, args.timeout, args.poll_interval)
    except ServerError as error:
        meta["status"] = "instance_unreachable"
        meta["error"] = str(error)
        save_json(run_dir / "run.json", meta)
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": 2,
                "dry_run": False,
                "run_id": run_name,
                "run_name": run_name,
                "run_dir": str(run_dir),
                "prompt_id": prompt_id,
                "status": "instance_unreachable",
                "error": str(error),
                "message": f"实例不可达: {error}",
            },
        )
        return 2
    except PollTimeout as error:
        meta["status"] = "monitoring_timeout"
        meta["error"] = str(error)
        save_json(run_dir / "run.json", meta)
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": 4,
                "dry_run": False,
                "run_id": run_name,
                "run_name": run_name,
                "run_dir": str(run_dir),
                "prompt_id": prompt_id,
                "status": "monitoring_timeout",
                "error": str(error),
                "message": f"监控超时: {error}",
            },
        )
        return 4

    save_json(run_dir / "history.json", outcome["history"])
    meta["finished_at"] = now_iso()
    meta["elapsed_seconds"] = round(outcome["elapsed"], 1)
    meta["status"] = "success" if outcome["state"] == "success" else "error"
    if outcome["state"] == "error":
        errors = execution_errors(outcome["status"]) or ["ComfyUI 报告执行错误"]
        meta["error"] = errors
        save_json(run_dir / "run.json", meta)
        emit_final(
            args,
            {
                "ok": False,
                "exit_code": 3,
                "dry_run": False,
                "run_id": run_name,
                "run_name": run_name,
                "run_dir": str(run_dir),
                "prompt_id": prompt_id,
                "status": "generation_failed",
                "errors": errors,
                "message": "工作流执行错误",
                "detail_lines": [f"错误: {line}" for line in errors] + [f"记录: {run_dir}"],
            },
        )
        return 3

    outputs = outcome["entry"].get("outputs") if isinstance(outcome["entry"], dict) else {}
    artifacts = extract_artifacts(outputs) + extract_local_video_artifacts(outputs)
    for artifact in artifacts:
        if artifact["type"] != "local-video" and artifact.get("view_url") is None:
            query = urllib.parse.urlencode(
                {
                    "filename": artifact["filename"],
                    "subfolder": artifact["subfolder"],
                    "type": artifact["type"],
                }
            )
            artifact["view_url"] = f"{server}/view?{query}"
    meta["artifacts"] = artifacts
    meta["status"] = "completed"
    save_json(run_dir / "run.json", meta)
    detail_lines = [f"完成（{outcome['elapsed']:.0f}s）"]
    if artifacts:
        for artifact in artifacts:
            where = (
                f"{artifact['subfolder']}/{artifact['filename']}"
                if artifact["subfolder"]
                else artifact["filename"]
            )
            detail_lines.append(f"产物 {artifact['kind']} {artifact['type']}: {where}")
            if artifact.get("view_url"):
                detail_lines.append(f"  查看: {artifact['view_url']}")
            elif artifact.get("source_path"):
                detail_lines.append(f"  路径: {artifact['source_path']}")
    else:
        detail_lines.append("提示: history 输出中没有可识别的 images/gifs/videos/audio 产物")
    for line in collect_ui(outputs):
        detail_lines.append(line)
    detail_lines.append(f"记录: {run_dir}")
    emit_final(
        args,
        {
            "ok": True,
            "exit_code": 0,
            "dry_run": False,
            "run_id": run_name,
            "run_name": run_name,
            "run_dir": str(run_dir),
            "prompt_id": prompt_id,
            "status": "completed",
            "server": server,
            "workflow_id": Path(args.workflow).stem,
            "artifacts": artifacts,
            "message": f"完成（{outcome['elapsed']:.0f}s）",
            "detail_lines": detail_lines,
        },
    )
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.timeout < 1:
        print("错误: --timeout 必须 >= 1", file=sys.stderr)
        return 1
    if args.poll_interval < 1:
        print("错误: --poll-interval 必须 >= 1", file=sys.stderr)
        return 1
    try:
        return run(args)
    except UsageError as error:
        if args.json:
            emit_final(
                args,
                {
                    "ok": False,
                    "exit_code": 1,
                    "dry_run": bool(args.dry_run),
                    "run_id": None,
                    "run_name": args.run_name,
                    "run_dir": None,
                    "prompt_id": None,
                    "status": "usage_error",
                    "error": str(error),
                    "message": str(error),
                },
            )
        else:
            print(f"错误: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
