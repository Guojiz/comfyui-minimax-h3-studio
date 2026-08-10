"""Instance catalog, normalization, health checks and project locks.

The catalog lives on the local machine (ignored or Codex MCP config), never in
the session.  Project selection is persisted in project files by the Agent;
this module only parses instances and reads/writes the machine-readable lock.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_SERVER = "http://127.0.0.1:8188"
SERVER_ENV = "COMFY_SERVER"
INSTANCES_ENV = "COMFY_INSTANCES"
DEFAULT_CATALOG = "~/.config/ai-video-studio/instances.json"
HEALTH_TIMEOUT = 8


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


def default_catalog_path():
    return Path(os.environ.get(INSTANCES_ENV) or DEFAULT_CATALOG).expanduser()


def load_catalog(catalog_path=None):
    path = Path(catalog_path) if catalog_path else default_catalog_path()
    if not path.exists():
        return {"version": 1, "instances": [], "path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"instance catalog cannot be read {path}: {error}")
    raw_instances = data.get("instances") if isinstance(data, dict) else None
    if not isinstance(raw_instances, list):
        raise ValueError(f"instance catalog {path} must contain an instances list")
    instances = []
    for entry in raw_instances:
        if not isinstance(entry, dict):
            raise ValueError(f"instance catalog {path} contains a non-object entry")
        instance_id = entry.get("instance_id")
        if not isinstance(instance_id, str) or not instance_id.strip():
            raise ValueError(f"instance catalog {path} entry needs a non-empty instance_id")
        instances.append(
            {
                "instance_id": instance_id.strip(),
                "name": str(entry.get("name") or instance_id.strip()),
                "server": normalize_server_url(entry.get("server")),
                "auth_env": entry.get("auth_env"),
                "notes": str(entry.get("notes") or ""),
            }
        )
    return {"version": data.get("version", 1), "instances": instances, "path": str(path)}


def find_instance(instance_id, catalog_path=None):
    catalog = load_catalog(catalog_path)
    for entry in catalog["instances"]:
        if entry["instance_id"] == instance_id:
            return entry
    return None


def check_instance(instance_id=None, server=None, catalog_path=None, timeout=HEALTH_TIMEOUT):
    try:
        record, _ = resolve_instance(instance_id, server, catalog_path=catalog_path)
        server_url = record["server"]
        with urllib.request.urlopen(
            server_url + "/system_stats", timeout=timeout
        ) as response:
            status_code = response.status
            body = response.read().decode("utf-8", errors="replace")
            payload = json.loads(body) if body.strip() else {}
        return {
            "ok": True,
            "instance_id": record["instance_id"],
            "server": server_url,
            "endpoint": "/system_stats",
            "status_code": status_code,
            "system": payload,
        }
    except Exception as error:  # reachability must be a result, not a crash
        return {
            "ok": False,
            "instance_id": record["instance_id"] if "record" in locals() else instance_id,
            "server": record["server"] if "record" in locals() else server,
            "endpoint": "/system_stats",
            "error": str(error),
        }


def resolve_instance(
    instance_id=None,
    server=None,
    project=None,
    catalog_path=None,
):
    """Resolve a single target instance; without one, no prompt may be submitted."""
    if instance_id:
        entry = find_instance(instance_id, catalog_path)
        if entry is None:
            raise LookupError(f"instance_id {instance_id!r} not found in catalog")
        return entry, f"catalog:{instance_id}"
    if server:
        return {
            "instance_id": "explicit-server",
            "name": "Explicit server",
            "server": normalize_server_url(server),
            "auth_env": None,
            "notes": "resolved from explicit server argument",
        }, "explicit-server"
    if project:
        lock = read_project_lock(project)
        if lock:
            entry = find_instance(lock["instance_id"], catalog_path)
            if entry is None:
                raise LookupError(
                    f"project lock references unknown instance {lock['instance_id']!r}"
                )
            return entry, f"project-lock:{lock['instance_id']}"
    catalog = load_catalog(catalog_path)
    if len(catalog["instances"]) == 1:
        return catalog["instances"][0], "auto-single"
    raise LookupError(
        "no unique target instance: pass instance_id, an explicit server, a project "
        "lock, or configure exactly one instance in the catalog"
    )


def _project_state_dir(project):
    path = Path(project).expanduser() / ".ai-video-studio"
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_project_lock(project):
    path = Path(project).expanduser() / ".ai-video-studio" / "instance.lock.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_project_lock(project, instance, note=None):
    lock = {
        "instance_id": instance["instance_id"],
        "server": instance["server"],
        "selected_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "note": note or "",
    }
    path = _project_state_dir(project) / "instance.lock.json"
    path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return lock


def decision_line(instance, source):
    return (
        f"- {datetime.now(timezone.utc).astimezone().strftime('%Y-%m-%d')} — "
        f"锁定 ComfyUI 实例 {instance['instance_id']}（{instance['server']}，"
        f"来源 {source}）— 后续 run 均须使用该实例"
    )
