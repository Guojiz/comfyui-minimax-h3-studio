#!/usr/bin/env python3
"""Thin Codex-ComfyUI STDIO MCP bridge backed by ai-video-studio runner scripts."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_REGISTRY = SKILL_DIR / "assets"
RUN_WORKFLOW = SKILL_DIR / "scripts" / "run-workflow.py"
WORKFLOW_DOCTOR = SKILL_DIR / "scripts" / "workflow-doctor.py"
DEFAULT_SERVER = "http://127.0.0.1:8188"
HEALTH_TIMEOUT = 8
SUBPROCESS_TIMEOUT_GRACE = 30
MAX_OUTPUT_CHARS = 250_000
WORKFLOW_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SERVER_ENV = "COMFY_SERVER"
REGISTRY_ENV = "COMFY_WORKFLOW_REGISTRY"


class _Result:
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _load_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"file not found: {path}"
    except OSError as error:
        return None, f"cannot read {path}: {error}"
    except json.JSONDecodeError as error:
        return None, f"invalid JSON: {error}"
    return data, None


def _positive_int(value, name):
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{name} must be an integer >= 1")
    return value


def _snippet(text, limit=MAX_OUTPUT_CHARS):
    if not text:
        return ""
    text = str(text)
    if len(text) <= limit:
        return text
    head_len = int(limit * 0.6)
    marker = "\n...[truncated output]...\n"
    tail_len = max(0, limit - head_len - len(marker))
    return text[:head_len] + marker + text[-tail_len:]


def normalize_server_url(value):
    if value is None:
        value = os.environ.get(SERVER_ENV) or DEFAULT_SERVER
    if not isinstance(value, str) or not value.strip():
        raise ValueError("ComfyUI server URL must not be empty")
    parts = urllib.parse.urlsplit(value.strip())
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        raise ValueError(f"ComfyUI server URL must use http/https: {value!r}")
    if not parts.netloc:
        raise ValueError(f"ComfyUI server URL is missing a host: {value!r}")
    if parts.username or parts.password:
        raise ValueError(
            "ComfyUI server URL must not embed credentials; configure auth outside this bridge"
        )
    # Query and fragment are stripped so cached URLs cannot carry stale auth params.
    path = parts.path.rstrip("/")
    return urllib.parse.urlunsplit((scheme, parts.netloc, path, "", ""))


def normalize_registry_dir(value):
    if value is None:
        value = os.environ.get(REGISTRY_ENV) or DEFAULT_REGISTRY
    path = Path(value).expanduser()
    if not path.is_dir():
        raise ValueError(f"workflow registry is not a directory: {path}")
    return str(path.resolve())


def load_registry(registry_dir=None):
    root = Path(normalize_registry_dir(registry_dir))
    entries = []
    for workflow_file in sorted(root.glob("*.json")):
        if workflow_file.name.endswith(".manifest.json"):
            continue
        workflow, workflow_error = _load_json(workflow_file)
        manifest_path = workflow_file.with_name(f"{workflow_file.stem}.manifest.json")
        manifest = None
        manifest_error = None
        if manifest_path.exists():
            manifest, manifest_error = _load_json(manifest_path)
            if manifest_error is None and not isinstance(manifest, dict):
                manifest_error = "companion manifest must be a JSON object"
                manifest = None

        errors = []
        if workflow_error:
            errors.append(f"workflow: {workflow_error}")
        elif not isinstance(workflow, dict) or not workflow:
            errors.append("workflow JSON must be a non-empty object")

        manifest_id = None
        if manifest and isinstance(manifest.get("id"), str) and manifest["id"].strip():
            manifest_id = manifest["id"].strip()
        workflow_id = manifest_id or workflow_file.stem
        if workflow_id in (".", "..") or not WORKFLOW_ID_RE.fullmatch(workflow_id):
            errors.append(f"invalid workflow id {workflow_id!r}")
        if manifest_error:
            errors.append(f"manifest: {manifest_error}")

        node_count = None
        node_types = []
        if isinstance(workflow, dict) and workflow:
            node_count = len(workflow)
            node_types = sorted(
                {
                    node.get("class_type")
                    for node in workflow.values()
                    if isinstance(node, dict)
                    and isinstance(node.get("class_type"), str)
                }
            )

        meta = manifest if isinstance(manifest, dict) else {}
        entries.append(
            {
                "id": workflow_id,
                "file": str(workflow_file),
                "manifest_file": str(manifest_path) if manifest_path.exists() else None,
                "name": meta.get("name") or workflow_id,
                "description": meta.get("purpose") or "",
                "provider": meta.get("provider"),
                "license": meta.get("license"),
                "source": meta.get("source"),
                "distribution": meta.get("distribution"),
                "inputs": meta.get("inputs"),
                "outputs": meta.get("outputs"),
                "required_nodes": meta.get("required_nodes"),
                "verified": meta.get("verified"),
                "node_count": node_count,
                "node_types": node_types,
                "ok": not errors,
                "errors": errors,
            }
        )
    return {"registry": str(root), "count": len(entries), "workflows": entries}


def resolve_workflow(workflow_id, registry_dir=None):
    if not isinstance(workflow_id, str) or not workflow_id.strip():
        raise ValueError("workflow id must not be empty")
    workflow_id = workflow_id.strip()
    if workflow_id in (".", "..") or not WORKFLOW_ID_RE.fullmatch(workflow_id):
        raise ValueError(
            f"workflow id {workflow_id!r} contains unsafe characters; "
            "use alphanumerics plus . _ -"
        )
    registry = load_registry(registry_dir)
    match = next(
        (entry for entry in registry["workflows"] if entry["id"] == workflow_id),
        None,
    )
    if match is None:
        available = ", ".join(entry["id"] for entry in registry["workflows"])
        raise LookupError(
            f"workflow id {workflow_id!r} not found in registry "
            f"{registry['registry']} (available: {available or 'none'})"
        )
    if not match["ok"]:
        raise ValueError(
            f"workflow {workflow_id!r} is not usable: " + "; ".join(match["errors"])
        )
    root = Path(registry["registry"]).resolve()
    workflow_path = Path(match["file"]).resolve()
    if not workflow_path.is_relative_to(root):
        raise ValueError(f"workflow path escapes registry root: {workflow_path}")
    return workflow_path


def tool_health(server=None):
    server = normalize_server_url(server)
    url = server + "/system_stats"
    try:
        with urllib.request.urlopen(url, timeout=HEALTH_TIMEOUT) as response:
            status_code = response.status
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body) if body.strip() else {}
        return {
            "ok": True,
            "server": server,
            "endpoint": "/system_stats",
            "status_code": status_code,
            "system": payload,
        }
    except Exception as error:  # reachability must be a result, not an MCP crash
        return {
            "ok": False,
            "server": server,
            "endpoint": "/system_stats",
            "error": str(error),
        }


def tool_list_workflows(registry_dir=None):
    return load_registry(registry_dir)


def tool_inspect_workflow(workflow_id, registry_dir=None):
    workflow_path = resolve_workflow(workflow_id, registry_dir)
    workflow, error = _load_json(workflow_path)
    if error:
        raise ValueError(f"cannot inspect {workflow_id}: {error}")
    if not isinstance(workflow, dict) or not workflow:
        raise ValueError(f"workflow {workflow_id} must be a non-empty JSON object")
    manifest_path = workflow_path.with_name(f"{workflow_path.stem}.manifest.json")
    manifest = None
    if manifest_path.exists():
        manifest, error = _load_json(manifest_path)
        if error:
            raise ValueError(f"cannot inspect manifest for {workflow_id}: {error}")
        if not isinstance(manifest, dict):
            raise ValueError(f"companion manifest for {workflow_id} must be a JSON object")
    return {
        "id": workflow_id,
        "file": str(workflow_path),
        "node_count": len(workflow),
        "node_types": sorted(
            {
                node.get("class_type")
                for node in workflow.values()
                if isinstance(node, dict) and isinstance(node.get("class_type"), str)
            }
        ),
        "manifest": manifest,
        "workflow": workflow,
    }


def build_doctor_argv(workflow_path, server, offline, timeout):
    argv = [str(workflow_path), "--server", normalize_server_url(server)]
    if offline:
        argv.append("--offline")
    argv += ["--timeout", str(timeout)]
    return argv


def build_run_argv(
    workflow_path,
    server,
    sets,
    dry_run,
    project,
    run_name,
    shot,
    iteration,
    timeout,
    poll_interval,
    json_output=False,
):
    argv = [
        str(workflow_path),
        "--server",
        normalize_server_url(server),
        "--project",
        project,
    ]
    if dry_run:
        argv.append("--dry-run")
    if run_name:
        argv += ["--run-name", run_name]
    if shot:
        argv += ["--shot", shot]
    if iteration:
        argv += ["--iteration", iteration]
    argv += ["--timeout", str(timeout), "--poll-interval", str(poll_interval)]
    if json_output:
        argv.append("--json")
    for spec in sets or []:
        argv += ["--set", spec]
    return argv


def _run_script(script, argv, timeout):
    try:
        result = subprocess.run(
            [sys.executable, str(script), *argv],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return _Result(result.returncode, result.stdout or "", result.stderr or "")
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout if isinstance(error.stdout, str) else ""
        stderr = error.stderr if isinstance(error.stderr, str) else ""
        stderr += f"\nERROR: script timed out after {timeout}s"
        return _Result(124, stdout, stderr)


def tool_doctor(workflow_id, registry_dir=None, server=None, offline=False, timeout=8):
    timeout = _positive_int(timeout, "timeout")
    workflow_path = resolve_workflow(workflow_id, registry_dir)
    argv = build_doctor_argv(workflow_path, server, bool(offline), timeout)
    result = _run_script(WORKFLOW_DOCTOR, argv, timeout=timeout + SUBPROCESS_TIMEOUT_GRACE)
    return {
        "ok": result.returncode == 0,
        "exit_code": result.returncode,
        "workflow_id": workflow_id,
        "offline": bool(offline),
        "stdout": _snippet(result.stdout),
        "stderr": _snippet(result.stderr),
    }


def tool_run_workflow(
    workflow_id,
    registry_dir=None,
    server=None,
    sets=None,
    dry_run=True,
    project=".",
    run_name=None,
    shot=None,
    iteration=None,
    timeout=900,
    poll_interval=5,
):
    if sets is None:
        sets = []
    if not isinstance(sets, list) or not all(
        isinstance(spec, str) and spec for spec in sets
    ):
        raise ValueError("sets must be a list of NODE.FIELD=JSON_VALUE strings")
    timeout = _positive_int(timeout, "timeout")
    poll_interval = _positive_int(poll_interval, "poll_interval")
    workflow_path = resolve_workflow(workflow_id, registry_dir)
    argv = build_run_argv(
        workflow_path,
        server,
        sets,
        dry_run,
        project,
        run_name,
        shot,
        iteration,
        timeout,
        poll_interval,
        json_output=True,
    )
    result = _run_script(RUN_WORKFLOW, argv, timeout=timeout + SUBPROCESS_TIMEOUT_GRACE)
    outcome = {
        "ok": result.returncode == 0,
        "exit_code": result.returncode,
        "workflow_id": workflow_id,
        "dry_run": dry_run,
        "stdout": _snippet(result.stdout),
        "stderr": _snippet(result.stderr),
    }
    parsed = None
    if result.stdout.strip():
        try:
            parsed = json.loads(result.stdout)
        except json.JSONDecodeError:
            parsed = None
    if isinstance(parsed, dict):
        for key in (
            "run_id",
            "run_name",
            "run_dir",
            "prompt_id",
            "status",
            "server",
            "artifacts",
            "errors",
            "error",
            "message",
        ):
            if key in parsed:
                outcome[key] = parsed[key]
        outcome["run_facts"] = parsed
    return outcome


def _tool_error(message):
    try:
        from mcp.server.fastmcp import ToolError
    except ImportError:
        try:
            from mcp.server.fastmcp.exceptions import ToolError
        except ImportError:
            return RuntimeError(message)
    return ToolError(message)


def _register_tool(mcp, fn, name, description, *, is_readonly):
    from mcp.types import ToolAnnotations

    annotations = ToolAnnotations(
        readOnlyHint=is_readonly,
        destructiveHint=False,
        idempotentHint=is_readonly,
    )
    mcp.tool(name=name, description=description, annotations=annotations)(fn)


def create_server(server=None, registry_dir=None):
    from mcp.server.fastmcp import FastMCP

    server_url = normalize_server_url(server)
    registry = normalize_registry_dir(registry_dir)
    mcp = FastMCP("ai-video-studio-comfyui")

    def health() -> dict:
        return tool_health(server_url)

    def list_workflows() -> dict:
        return tool_list_workflows(registry)

    def inspect_workflow(workflow_id: str) -> dict:
        try:
            return tool_inspect_workflow(workflow_id, registry)
        except (ValueError, LookupError) as error:
            raise _tool_error(str(error)) from error

    def doctor(
        workflow_id: str, offline: bool = False, timeout: int = 8
    ) -> dict:
        try:
            return tool_doctor(workflow_id, registry, server_url, offline, timeout)
        except (ValueError, LookupError) as error:
            raise _tool_error(str(error)) from error

    def run_workflow(
        workflow_id: str,
        sets: list[str] | None = None,
        dry_run: bool = True,
        project: str = ".",
        run_name: str | None = None,
        shot: str | None = None,
        iteration: str | None = None,
        timeout: int = 900,
        poll_interval: int = 5,
    ) -> dict:
        try:
            return tool_run_workflow(
                workflow_id,
                registry,
                server_url,
                sets,
                dry_run,
                project,
                run_name,
                shot,
                iteration,
                timeout,
                poll_interval,
            )
        except (ValueError, LookupError) as error:
            raise _tool_error(str(error)) from error

    _register_tool(
        mcp,
        health,
        "health",
        "Read-only ComfyUI health check. Returns /system_stats when the server "
        "is reachable and a structured error result otherwise.",
        is_readonly=True,
    )
    _register_tool(
        mcp,
        list_workflows,
        "list_workflows",
        "Read-only list of registered workflows: JSON files in the registry "
        "directory plus companion *.manifest.json metadata.",
        is_readonly=True,
    )
    _register_tool(
        mcp,
        inspect_workflow,
        "inspect_workflow",
        "Read-only inspect of one registered workflow by id: full JSON, "
        "companion manifest and node summary.",
        is_readonly=True,
    )
    _register_tool(
        mcp,
        doctor,
        "doctor",
        "Read-only preflight via scripts/workflow-doctor.py. offline=true checks "
        "JSON structure without contacting the server.",
        is_readonly=True,
    )
    _register_tool(
        mcp,
        run_workflow,
        "run_workflow",
        "Validate and, unless dry_run=true (the default), submit a registered "
        "workflow via scripts/run-workflow.py. Non-read-only when dry_run=false "
        "because it submits and writes run records.",
        is_readonly=False,
    )
    return mcp


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="comfyui_mcp.py",
        description="Run the ai-video-studio ComfyUI bridge as an MCP STDIO server.",
    )
    parser.add_argument(
        "--server",
        default=None,
        help=f"ComfyUI URL (default: env {SERVER_ENV} or {DEFAULT_SERVER})",
    )
    parser.add_argument(
        "--registry",
        default=None,
        help=(
            f"workflow registry directory (default: env {REGISTRY_ENV} "
            f"or {DEFAULT_REGISTRY})"
        ),
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=("stdio",),
        help="MCP transport (default: stdio)",
    )
    args = parser.parse_args(argv)
    try:
        mcp = create_server(args.server, args.registry)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    mcp.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    sys.exit(main())
