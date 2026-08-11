# ComfyUI MCP Bridge

A thin STDIO MCP server that lets Codex inspect and drive the ai-video-studio
ComfyUI scripts without reimplementing their validation or execution logic.

## Install

```bash
python3 -m pip install -r skills/ai-video-studio/mcp/requirements.txt
```

## Run

```bash
python3 skills/ai-video-studio/mcp/comfyui_mcp.py \
  --server http://127.0.0.1:8188 \
  --registry skills/ai-video-studio/assets
```

The same values can come from environment variables:

```bash
export COMFY_SERVER=http://127.0.0.1:8188
export COMFY_WORKFLOW_REGISTRY=/path/to/workflow/registry
python3 skills/ai-video-studio/mcp/comfyui_mcp.py
```

CLI arguments override environment variables; both override the built-in
defaults (`http://127.0.0.1:8188` and the skill `assets/` directory).

## Tools

| Tool | Read-only | Behavior |
| --- | --- | --- |
| `health` | yes | GET `/system_stats`; returns a structured result when unreachable |
| `list_instances` | yes | Lists the local instance catalog (`instance_id`, name, normalized server, auth_env) |
| `check_instance(instance_id?, server?, timeout=8)` | yes | Health check for one catalog instance or an explicit server |
| `select_instance(instance_id, project, decision_note?)` | no | Writes the project instance lock and returns a `decisions.md` line; Agent persists it |
| `get_active_instance(project=".")` | yes | Reports the project's locked instance, if any |
| `list_workflows` | yes | Lists registry JSON files plus companion manifest metadata |
| `inspect_workflow(workflow_id)` | yes | Returns full workflow JSON, manifest, and node summary |
| `doctor(workflow_id, offline=false, timeout=8)` | yes | Runs `scripts/workflow-doctor.py` |
| `run_workflow(workflow_id, sets=[], dry_run=true, ...)` | no when `dry_run=false` | Runs `scripts/run-workflow.py`; default is dry-run validation only |
| `submit_workflow(workflow_id, project, instance_id?, sets=[], ...)` | no | Submits and returns `run_id`/`prompt_id`/`status` immediately; never blocks polling; idempotent for active runs |
| `get_run_status(run_id, project, instance_id?)` | yes | Queries `/queue` + `/history` for an existing run; never submits a new task |
| `list_queue(instance_id?)` | yes | Snapshot of queue running/pending prompt ids |
| `cancel_run(run_id, project, instance_id?)` | no | Deletes a queued run; reports `unsupported` for running tasks that would need a global interrupt |
| `download_artifacts(run_id, project, instance_id?, target_dir?, overwrite=false)` | no | Saves completed-run artifacts with sha256 + source records into the project; never changes generation status |
| `upload_asset(local_path, authorized=false, workflow_id?, semantic_input?, ...)` | no | Uploads one local image to `/upload/image`; requires explicit `authorized=true`; can return the manifest-bound `--set` spec |

`run_workflow` is registered as non-read-only because `dry_run=false` submits to
ComfyUI and writes run records under `<project>/runs/`.

When `dry_run=false`, `run_workflow` returns structured run facts instead of raw
stdout, including `run_id`, `run_name`, `run_dir`, `prompt_id`, `status`,
`server`, `artifacts`, and a full `run_facts` object. The underlying runner is
invoked with `--json` so the bridge never requires parsing human-readable
output. Statuses follow the run contract: `prepared`, `submitted`,
`completed`, `generation_failed`, `instance_unreachable`, `monitoring_timeout`,
and `usage_error`; only backend-confirmed terminal states count as
`completed`/`generation_failed`.

Two safety rules are enforced by the runner and therefore by this bridge:

- A real submission (not dry-run) must have an explicit instance via `--server`
  or `COMFY_SERVER`; there is no silent fallback to `127.0.0.1:8188`. The bridge
  always passes its configured server explicitly.
- An existing `<project>/runs/<run-name>` directory is never overwritten; the
  runner fails with a `usage_error` and the caller must choose a new run name.
- Without a resolved unique instance (catalog id, explicit server, or project
  lock), `submit_workflow` refuses to POST `/prompt`; there is no silent target.
- `get_run_status` never re-submits. `instance_unreachable` and
  `monitoring_timeout` are non-terminal; only backend-confirmed states become
  `completed`/`generation_failed`/`cancelled`.

Nodes that publish `ui.video_paths`/`ui.video_filenames` are recognized and
returned as `type: "local-video"` artifacts with their source path. External
task ids published as `ui.task_ids` are written into the run record as soon as
status is observed. The bridge itself binds only to ComfyUI; no model or API
service is assumed, bundled, or configured by default.

## Instance catalog

The catalog is a local JSON file, never the session:

```json
{
  "version": 1,
  "instances": [
    {"instance_id": "local-a", "name": "Local A", "server": "http://127.0.0.1:8188"},
    {"instance_id": "remote-b", "name": "Remote B", "server": "https://comfy.example:8443"}
  ]
}
```

Default location: `~/.config/ai-video-studio/instances.json` (override with
`COMFY_INSTANCES` or `--catalog`). Server URLs are normalized and must not embed
credentials; auth stays in local env/ignored files. A single catalog instance is
auto-selected but always reported; multiple instances require an explicit
project selection via `select_instance`, persisted in
`.ai-video-studio/instance.lock.json` plus a `decisions.md` line.

## Semantic input bindings

Manifests can declare a `bindings` map from semantic inputs to node fields, so
the Agent never has to guess node ids:

```json
{"bindings": {"reference_image": "137.inputs.image", "prompt": "138.inputs.value"}}
```

`upload_asset(..., workflow_id=..., semantic_input="reference_image")` returns
the exact `--set` spec to inject the uploaded server filename into the workflow.
`list_workflows` surfaces `bindings` for every registered workflow.

## Registry format

Every `*.json` file directly inside the registry directory is a workflow.
Optional companion manifests are named `<workflow>.manifest.json` and provide
metadata such as `id`, `purpose`, `inputs`, `outputs`,
`required_nodes`, `verified`, `license`, `source`, and `distribution`. The
manifest filename must match the workflow filename stem exactly (for example
`minimax-h3-r2v-0.7mp.json` pairs with `minimax-h3-r2v-0.7mp.manifest.json`);
a mismatched name leaves `manifest_file: null` and drops the metadata. The
manifest `id` is used as the workflow id when present; otherwise the filename
stem is used.

Workflow ids are restricted to alphanumeric characters plus `.`, `_`, and `-`,
and resolved paths are checked to stay inside the registry directory.

## Security notes

- No API keys are embedded or printed. Server URLs must not contain embedded
  credentials, and query/fragment parts are stripped.
- Workflow ids cannot contain path separators, `.`/`..`, or absolute paths.
- Do not pass secret-bearing values through `run_workflow` sets; the bridge
  returns captured script output and does not filter arbitrary values.

## Tests

```bash
python3 -m unittest discover -s skills/ai-video-studio/mcp/tests
```

Tests are offline and do not require the `mcp` package.
