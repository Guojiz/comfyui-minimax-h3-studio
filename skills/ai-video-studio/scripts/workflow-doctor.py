#!/usr/bin/env python3
"""Check whether an API-format ComfyUI workflow is runnable on a server."""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"无法读取 {path}: {error}")


def validate_workflow(workflow):
    if not isinstance(workflow, dict) or not workflow:
        raise ValueError("工作流必须是非空 JSON 对象")
    for node_id, node in workflow.items():
        if not isinstance(node, dict) or not isinstance(node.get("class_type"), str):
            raise ValueError(f"节点 {node_id} 缺少 class_type")
        if not isinstance(node.get("inputs"), dict):
            raise ValueError(f"节点 {node_id} 缺少 inputs")


def fetch_object_info(server, timeout):
    url = server.rstrip("/") + "/object_info"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"无法读取 {url}: {error}")


def allowed_values(node_info, field):
    inputs = node_info.get("input", {}) if isinstance(node_info, dict) else {}
    for group in ("required", "optional"):
        spec = inputs.get(group, {}).get(field) if isinstance(inputs.get(group), dict) else None
        if isinstance(spec, list) and spec and isinstance(spec[0], list):
            return spec[0]
    return None


def diagnose(workflow, object_info):
    missing_nodes = []
    missing_resources = []
    for node_id, node in workflow.items():
        class_type = node["class_type"]
        info = object_info.get(class_type)
        if not isinstance(info, dict):
            missing_nodes.append((node_id, class_type))
            continue
        for field, value in node["inputs"].items():
            choices = allowed_values(info, field)
            if choices is not None and isinstance(value, str) and value not in choices:
                missing_resources.append((node_id, class_type, field, value))
    return missing_nodes, missing_resources


def main(argv=None):
    parser = argparse.ArgumentParser(description="检查 API workflow 的节点与模型/资源是否在 ComfyUI 中可用")
    parser.add_argument("workflow")
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--offline", action="store_true", help="只检查 JSON 结构")
    args = parser.parse_args(argv)
    try:
        workflow = load_json(args.workflow)
        validate_workflow(workflow)
    except ValueError as error:
        print(f"错误: {error}", file=sys.stderr)
        return 1
    classes = sorted({node["class_type"] for node in workflow.values()})
    print(f"结构通过: {len(workflow)} 个节点，{len(classes)} 种节点类型")
    if args.offline:
        return 0
    try:
        object_info = fetch_object_info(args.server, args.timeout)
    except RuntimeError as error:
        print(f"错误: {error}", file=sys.stderr)
        return 2
    missing_nodes, missing_resources = diagnose(workflow, object_info)
    if missing_nodes:
        print("缺少节点:")
        for node_id, class_type in missing_nodes:
            print(f"  {node_id}: {class_type}")
    if missing_resources:
        print("缺少模型或枚举资源:")
        for node_id, class_type, field, value in missing_resources:
            print(f"  {node_id} {class_type}.{field}: {value}")
    if missing_nodes or missing_resources:
        print("结论: 当前实例不可运行此 workflow")
        return 3
    print("结论: 节点与枚举资源检查通过；仍需确认输入素材、显存与外部服务")
    return 0


if __name__ == "__main__":
    sys.exit(main())
