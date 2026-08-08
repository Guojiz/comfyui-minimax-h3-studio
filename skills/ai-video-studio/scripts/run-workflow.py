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
        default=os.environ.get("COMFY_SERVER", DEFAULT_SERVER),
        help="ComfyUI 地址（默认 %s，可用 COMFY_SERVER 覆盖）" % DEFAULT_SERVER,
    )
    parser.add_argument("--timeout", type=int, default=900, help="轮询总超时秒数（默认 900）")
    parser.add_argument("--poll-interval", type=int, default=5, help="轮询间隔秒数（默认 5）")
    parser.add_argument(
        "--project",
        default=".",
        help="项目目录，run 保存到 <project>/runs/（默认当前目录）",
    )
    parser.add_argument("--run-name", default=None, help="run 目录名（默认自动生成）")
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


def normalize_run_name(name):
    if name in ("", ".", ".."):
        raise UsageError("--run-name 不能为空、. 或 ..")
    if "/" in name or "\\" in name:
        raise UsageError("--run-name 不能包含路径分隔符")
    return name


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


def view_url(server, artifact):
    query = urllib.parse.urlencode(
        {
            "filename": artifact["filename"],
            "subfolder": artifact["subfolder"],
            "type": artifact["type"],
        }
    )
    return f"{server}/view?{query}"


def run(args):
    workflow = load_workflow(args.workflow)
    apply_sets(workflow, args.set)
    run_name = normalize_run_name(
        args.run_name
        or f"run-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    )
    run_dir = Path(args.project).expanduser() / "runs" / run_name
    if args.dry_run:
        print("dry-run: 校验通过，未提交、未写文件")
        print(f"将保存到: {run_dir}")
        print("提交的 workflow:")
        print(json.dumps(workflow, ensure_ascii=False, indent=2))
        return 0

    run_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "schema_version": 1,
        "run_name": run_name,
        "server": args.server,
        "workflow_file": args.workflow,
        "sets": list(args.set),
        "submitted_at": now_iso(),
        "status": "pending",
    }
    save_json(run_dir / "workflow.json", workflow)
    save_json(run_dir / "run.json", meta)

    server = args.server.rstrip("/")
    print(f"提交任务到 {server}/prompt")
    try:
        response = http_json(f"{server}/prompt", method="POST", payload={"prompt": workflow}, timeout=SUBMIT_TIMEOUT)
    except ServerError as error:
        meta["status"] = "submit_error"
        meta["error"] = str(error)
        save_json(run_dir / "run.json", meta)
        print(f"错误: 提交失败: {error}", file=sys.stderr)
        return 2
    prompt_id = response.get("prompt_id") if isinstance(response, dict) else None
    if not prompt_id:
        meta["status"] = "submit_error"
        meta["error"] = f"提交响应缺少 prompt_id: {json.dumps(response, ensure_ascii=False)[:500]}"
        save_json(run_dir / "run.json", meta)
        print(f"错误: {meta['error']}", file=sys.stderr)
        return 2

    meta["prompt_id"] = prompt_id
    save_json(run_dir / "run.json", meta)
    print(f"任务 ID: {prompt_id}")

    try:
        outcome = poll_history(server, prompt_id, args.timeout, args.poll_interval)
    except ServerError as error:
        meta["status"] = "poll_error"
        meta["error"] = str(error)
        save_json(run_dir / "run.json", meta)
        print(f"错误: 轮询失败: {error}", file=sys.stderr)
        return 2
    except PollTimeout as error:
        meta["status"] = "timeout"
        meta["error"] = str(error)
        save_json(run_dir / "run.json", meta)
        print(f"错误: {error}", file=sys.stderr)
        return 4

    save_json(run_dir / "history.json", outcome["history"])
    meta["finished_at"] = now_iso()
    meta["elapsed_seconds"] = round(outcome["elapsed"], 1)
    meta["status"] = "success" if outcome["state"] == "success" else "error"
    if outcome["state"] == "error":
        errors = execution_errors(outcome["status"]) or ["ComfyUI 报告执行错误"]
        meta["error"] = errors
        save_json(run_dir / "run.json", meta)
        for line in errors:
            print(f"错误: {line}", file=sys.stderr)
        print(f"记录: {run_dir}", file=sys.stderr)
        return 3

    outputs = outcome["entry"].get("outputs") if isinstance(outcome["entry"], dict) else {}
    artifacts = extract_artifacts(outputs)
    meta["artifacts"] = artifacts
    save_json(run_dir / "run.json", meta)
    print(f"完成（{outcome['elapsed']:.0f}s）")
    if artifacts:
        for artifact in artifacts:
            where = (
                f"{artifact['subfolder']}/{artifact['filename']}"
                if artifact["subfolder"]
                else artifact["filename"]
            )
            print(f"产物 {artifact['kind']} {artifact['type']}: {where}")
            print(f"  查看: {view_url(server, artifact)}")
    else:
        print("提示: history 输出中没有可识别的 images/gifs/videos/audio 产物")
    for line in collect_ui(outputs):
        print(line)
    print(f"记录: {run_dir}")
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
        print(f"错误: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
