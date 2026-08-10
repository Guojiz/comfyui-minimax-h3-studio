"""Submit/status/artifact lifecycle for ComfyUI runs.

Kept separate from comfyui_mcp.py so the bridge stays a thin deterministic
adapter: submit returns ids immediately, status never re-submits, downloads
never change a generation's terminal state, and old runs are never overwritten.
"""

from __future__ import annotations

import json
import hashlib
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {path}: {error}")
    return data


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_run_meta(run_dir):
    path = Path(run_dir) / "run.json"
    if not path.exists():
        raise LookupError(f"no run record at {path}")
    meta = _load_json(path)
    if not isinstance(meta, dict):
        raise ValueError(f"run record {path} must be a JSON object")
    return meta


def read_run_dir(project, run_id):
    project_root = Path(project).expanduser().resolve()
    run_dir = (project_root / "runs" / run_id).resolve()
    runs_root = (project_root / "runs").resolve()
    if not run_dir.is_relative_to(runs_root):
        raise LookupError(f"run id {run_id!r} escapes the project runs directory")
    if not run_dir.is_dir():
        raise LookupError(f"run {run_id!r} not found under {project}/runs")
    return run_dir


def workflow_hash(workflow, sets=None):
    payload = json.dumps(
        workflow, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    if sets:
        payload += "\n" + json.dumps(sets, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def idempotency_key(instance_id, workflow, sets, seed, intended_run):
    parts = [instance_id, workflow_hash(workflow, sets)]
    if seed:
        parts.append(f"seed={seed}")
    parts.append(f"intent={intended_run}")
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]


def http_json(url, method="GET", payload=None, timeout=10, headers=None, max_bytes=None):
    data = None
    request_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    limit = max_bytes if max_bytes is not None else 128 * 1024 * 1024
    expected = _expected_netloc(url)
    opener = urllib.request.build_opener(SameHostRedirectHandler(expected))
    try:
        with opener.open(request, timeout=timeout) as response:
            raw_bytes = response.read(limit + 1)
            if len(raw_bytes) > limit:
                raise RuntimeError(f"response exceeds {limit} byte cap from {url}")
            raw = raw_bytes.decode("utf-8", errors="replace")
            if not raw.strip():
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError as error:
                raise RuntimeError(f"response is not JSON: {url}: {error}")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"HTTP {error.code}: {url} {body}".strip())
    except urllib.error.URLError as error:
        raise RuntimeError(f"cannot connect {url}: {error.reason}")
    except (TimeoutError, OSError) as error:
        raise RuntimeError(f"request failed {url}: {error}")


class SameHostRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Block redirects that leave the expected origin host."""

    def __init__(self, expected_host):
        super().__init__()
        self.expected_host = expected_host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_request = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_request is None:
            return None
        host = urllib.parse.urlsplit(new_request.full_url).netloc
        if host != self.expected_host:
            raise RuntimeError(
                f"redirect blocked to a different host ({new_request.full_url}); "
                "artifact downloads must stay on the selected instance"
            )
        return new_request


def _expected_netloc(url):
    parts = urllib.parse.urlsplit(url)
    return parts.netloc


def http_json_byte(url, timeout=60, max_bytes=None):
    """Fetch raw bytes with same-host redirects and an optional size cap."""
    limit = max_bytes if max_bytes is not None else 1024 * 1024 * 1024
    expected = _expected_netloc(url)
    opener = urllib.request.build_opener(SameHostRedirectHandler(expected))
    try:
        with opener.open(url, timeout=timeout) as response:
            chunks = []
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    raise RuntimeError(
                        f"download exceeds {limit} byte cap from {url}"
                    )
                chunks.append(chunk)
            return b"".join(chunks)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"HTTP {error.code}: {url} {body}".strip())
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RuntimeError(f"download failed {url}: {error}")


def _safe_local_source_path(source_path, allowed_roots):
    """Resolve a server-reported local path only when it stays inside allowed roots."""
    candidate = Path(source_path).expanduser().resolve()
    if not allowed_roots:
        raise RuntimeError(
            "mzsj local source path rejected: no allowed local output roots configured"
        )
    for root in allowed_roots:
        root_path = Path(root).expanduser().resolve()
        if candidate.is_relative_to(root_path):
            return candidate
    raise RuntimeError(
        f"mzsj local source path rejected (outside allowed roots): {source_path}"
    )


def _sanitize_remote_name(name):
    """Keep printable multipart filename content, strip header-injection characters."""
    cleaned = []
    for char in str(name):
        if char in ('"', "\\", "/", "\r", "\n", ":", "*", "?", "<", ">", "|"):
            cleaned.append("_")
        elif ord(char) < 32 or ord(char) == 127:
            continue
        else:
            cleaned.append(char)
    result = "".join(cleaned).strip(" .")
    result = result.replace("..", ".")
    return result or "upload"


def derive_provider_task_id(entry):
    """MZSJ provider task ids live inside node internals, not ComfyUI history status."""
    outputs = entry.get("outputs") if isinstance(entry, dict) else None
    if not isinstance(outputs, dict):
        return None
    for node_id, out in outputs.items():
        if not isinstance(out, dict):
            continue
        ui = out.get("ui")
        if not isinstance(ui, dict):
            continue
        for key in ("task_ids", "provider_task_ids"):
            values = ui.get(key)
            if isinstance(values, list) and values:
                return str(values[0])
    return None


def extract_mzsj_artifacts(outputs):
    """MZSJ nodes publish videos as ui.video_paths/video_filenames."""
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
                    "type": "mzsj",
                    "source_path": path,
                    "view_url": None,
                }
            )
    return artifacts


def extract_generic_artifacts(outputs):
    """Generic ComfyUI file outputs (images/gifs/videos/audio) from history."""
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
                            "source_path": None,
                            "view_url": None,
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


def merge_artifacts_into_meta(meta, entry, server=None):
    """Merge structured artifacts from a completed history entry into run meta."""
    if not isinstance(entry, dict):
        return meta
    outputs = entry.get("outputs") if isinstance(entry, dict) else None
    if not isinstance(outputs, dict):
        return meta
    artifacts = extract_mzsj_artifacts(outputs) + extract_generic_artifacts(outputs)
    if server:
        for artifact in artifacts:
            if artifact.get("view_url") is None and artifact.get("type") != "mzsj":
                query = urllib.parse.urlencode(
                    {
                        "filename": artifact["filename"],
                        "subfolder": artifact["subfolder"],
                        "type": artifact["type"],
                    }
                )
                artifact["view_url"] = server + "/view?" + query
    if artifacts:
        meta["artifacts"] = artifacts
        provider_task_id = derive_provider_task_id(entry)
        if provider_task_id:
            meta["provider_task_id"] = provider_task_id
    return meta


def parse_queue_response(payload):
    """ComfyUI /queue returns {queue_running, queue_pending}; map to statuses."""
    if not isinstance(payload, dict):
        return None
    running = payload.get("queue_running")
    pending = payload.get("queue_pending")
    if not isinstance(running, list) or not isinstance(pending, list):
        return None
    running_ids = {
        item[1] for item in running if isinstance(item, (list, tuple)) and len(item) > 1
    }
    pending_ids = {
        item[1] for item in pending if isinstance(item, (list, tuple)) and len(item) > 1
    }
    return running_ids, pending_ids


def list_queue(instance_id, server):
    payload = http_json(server + "/queue", timeout=10)
    parsed = parse_queue_response(payload)
    if parsed is None:
        return {
            "ok": False,
            "instance_id": instance_id,
            "server": server,
            "error": "server /queue response is not recognized; cannot report queue",
        }
    running, pending = parsed
    return {
        "ok": True,
        "instance_id": instance_id,
        "server": server,
        "queue_running": sorted(running),
        "queue_pending": sorted(pending),
    }


def infer_status(history_entry, queue_state, server_unreachable=False):
    """Only backend-confirmed terminal states become terminal; otherwise unknown/last-known."""
    if server_unreachable:
        return "instance_unreachable"
    if not isinstance(history_entry, dict):
        return "unknown"
    status = history_entry.get("status") or {}
    if not isinstance(status, dict):
        return "unknown"
    if status.get("status_str") == "error":
        return "generation_failed"
    if status.get("completed") or status.get("status_str") == "success":
        return "completed"
    if queue_state == "running":
        return "running"
    if queue_state == "queued":
        return "queued"
    return "unknown"


def status_for_prompt_id(server, prompt_id):
    """Query /queue + /history; never submits a new task."""
    queue_payload = http_json(server + "/queue", timeout=10)
    parsed = parse_queue_response(queue_payload)
    state = None
    if parsed is not None:
        running, pending = parsed
        if prompt_id in running:
            state = "running"
        elif prompt_id in pending:
            state = "queued"
    history_payload = http_json(
        server + "/history/" + urllib.parse.quote(prompt_id, safe=""), timeout=10
    )
    entry = (
        history_payload.get(prompt_id)
        if isinstance(history_payload, dict)
        else None
    )
    status = infer_status(entry, state)
    return {
        "status": status,
        "entry": entry if isinstance(entry, dict) else None,
        "queue_state": state,
        "history": history_payload if isinstance(history_payload, dict) else None,
    }


def cancel_run(server, prompt_id, queue_payload):
    """Delete from pending queue; ComfyUI has no precise running interrupt."""
    parsed = parse_queue_response(queue_payload)
    if parsed is None:
        return {
            "ok": False,
            "prompt_id": prompt_id,
            "cancelled": False,
            "error": "cannot parse /queue; cancellation unsupported right now",
        }
    running, pending = parsed
    if prompt_id in running:
        return {
            "ok": False,
            "prompt_id": prompt_id,
            "cancelled": False,
            "error": (
                "ComfyUI has no precise running interrupt; a global interrupt "
                "would affect other tasks on this instance"
            ),
            "unsupported": True,
        }
    if prompt_id not in pending:
        return {
            "ok": True,
            "prompt_id": prompt_id,
            "cancelled": False,
            "already_terminal": True,
        }
    delete_url = server + "/queue"
    data = json.dumps({"delete": [prompt_id]}).encode("utf-8")
    request = urllib.request.Request(
        delete_url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=10):
            return {
                "ok": True,
                "prompt_id": prompt_id,
                "cancelled": True,
            }
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return {
            "ok": False,
            "prompt_id": prompt_id,
            "cancelled": False,
            "error": str(error),
        }


def status_update_meta(meta, status, server, extra=None):
    meta["status"] = status
    meta["last_checked_at"] = now_iso()
    meta["last_known_status"] = status
    meta["server"] = server
    if extra:
        meta.update(extra)
    return meta


def write_status(project, run_id, status, server, extra=None, meta=None):
    if meta is None:
        meta = read_run_meta(read_run_dir(project, run_id))
    status_update_meta(meta, status, server, extra)
    save_json(Path(project).expanduser() / "runs" / run_id / "run.json", meta)
    return meta


def safe_filename(name):
    cleaned = "".join(ch for ch in name if ch.isalnum() or ch in "._-").strip(".")
    return cleaned or "asset"


def semantic_binding_sets(manifest, values):
    """Turn semantic input values into --set specs using the manifest bindings.

    Example manifest binding: {"reference_image": "137.inputs.image"}; callers
    then never need to guess node ids like 137.
    """
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    bindings = manifest.get("bindings")
    if not isinstance(bindings, dict):
        raise ValueError("manifest has no bindings map for semantic inputs")
    if not isinstance(values, dict):
        raise ValueError("values must be a dict of semantic input -> value")
    specs = []
    for name, value in values.items():
        field_path = bindings.get(name)
        if not isinstance(field_path, str) or not field_path:
            raise ValueError(f"manifest has no binding for semantic input {name!r}")
        parts = field_path.split(".")
        if len(parts) < 2:
            raise ValueError(f"invalid binding for {name!r}: {field_path!r}")
        specs.append(f"{field_path}={json.dumps(value, ensure_ascii=False)}")
    return specs


def download_artifacts(
    project,
    run_id,
    instance,
    server,
    target_dir=None,
    overwrite=False,
    allowed_source_roots=None,
):
    """Download artifacts for a completed run into the project; never moves originals."""
    run_dir = read_run_dir(project, run_id)
    meta = read_run_meta(run_dir)
    artifacts = meta.get("artifacts")
    if not isinstance(artifacts, list):
        return {
            "ok": False,
            "run_id": run_id,
            "artifacts": [],
            "downloaded": [],
            "error": "run has no structured artifacts to download",
        }
    target = Path(target_dir or (Path(project).expanduser() / "artifacts")).expanduser()
    allowed_roots = allowed_source_roots or []
    if instance and isinstance(instance, dict):
        output_dir = instance.get("output_dir")
        if output_dir:
            allowed_roots = [*allowed_roots, output_dir]
    downloaded = []
    failures = []
    for artifact in artifacts:
        filename = artifact.get("filename")
        source_path = artifact.get("source_path")
        view_url = artifact.get("view_url")
        if not filename:
            failures.append({"artifact": artifact, "error": "artifact has no filename"})
            continue
        local_name = safe_filename(filename)
        destination = target / local_name
        if destination.exists() and not overwrite:
            failures.append(
                {
                    "artifact": artifact,
                    "error": f"target exists (use overwrite=true): {destination}",
                }
            )
            continue
        try:
            if source_path and artifact.get("type") == "mzsj":
                resolved = _safe_local_source_path(source_path, allowed_roots)
                if not resolved.exists():
                    raise RuntimeError(f"mzsj source file not found: {resolved}")
                data = resolved.read_bytes()
                source_record = {
                    "kind": "local",
                    "source_path": str(resolved),
                }
            else:
                if not view_url:
                    raise RuntimeError("artifact has no view_url to download")
                data = http_json_byte(view_url, timeout=60)
                source_record = {
                    "kind": "url",
                    "url": view_url,
                    "node": artifact.get("node"),
                }
            if not data:
                raise RuntimeError("downloaded artifact is empty")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            digest = hashlib.sha256(data).hexdigest()
            downloaded.append(
                {
                    "filename": local_name,
                    "path": str(destination),
                    "sha256": digest,
                    "size": len(data),
                    "source": source_record,
                    "run_id": run_id,
                    "instance_id": instance.get("instance_id") if instance else None,
                    "server": server,
                    "workflow_id": meta.get("workflow_id") or meta.get("workflow_file"),
                }
            )
        except (OSError, RuntimeError) as error:
            failures.append({"artifact": artifact, "error": str(error)})
    if failures:
        result = {
            "ok": False,
            "run_id": run_id,
            "artifacts": artifacts,
            "downloaded": downloaded,
            "failures": failures,
        }
    else:
        result = {
            "ok": True,
            "run_id": run_id,
            "artifacts": artifacts,
            "downloaded": downloaded,
            "failures": [],
        }
    manifest_path = target / "download-manifest.json"
    save_json(manifest_path, result)
    return result


def upload_image(server, local_path, remote_name=None):
    """Upload one local image to ComfyUI /upload/image; returns server filename."""
    path = Path(local_path).expanduser()
    if not path.is_file():
        raise ValueError(f"image file not found: {path}")
    content = path.read_bytes()
    if not content:
        raise ValueError(f"image file is empty: {path}")
    remote_name = _sanitize_remote_name(remote_name or path.name)
    boundary = "----ai-video-studio" + hashlib.sha256(content).hexdigest()[:12]
    filename_field = remote_name
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        f'Content-Disposition: form-data; name="image"; filename="{filename_field}"\r\n'.encode()
    )
    body.extend(b"Content-Type: application/octet-stream\r\n\r\n")
    body.extend(content)
    body.extend(f"\r\n--{boundary}--\r\n".encode())
    request = urllib.request.Request(
        server + "/upload/image",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"upload failed HTTP {error.code}: {error.read().decode('utf-8', 'replace')[:500]}")
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise RuntimeError(f"upload failed {server}/upload/image: {error}")
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    stored_name = payload.get("name") if isinstance(payload, dict) else None
    if not stored_name:
        stored_name = remote_name
    return {
        "ok": True,
        "remote_name": stored_name,
        "local_file": str(path.resolve()),
        "sha256": hashlib.sha256(content).hexdigest(),
        "server": server,
    }
