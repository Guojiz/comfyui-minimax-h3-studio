# AI Video Studio (`ai-video-studio`)

A video production **Agent Skill** package for working with a local ComfyUI. It organizes production around four reusable cores:

| Core | Role |
|---|---|
| Agent | Creative brain: parses the brief, locks direction, plans shots, coordinates execution, reviews results |
| Skill | Reusable process and knowledge: `SKILL.md`, `references/`, and `scripts/` |
| Assets | Reusable characters, scenes, styles, and references across projects |
| ComfyUI | Operation/execution/technical workflow canvas: nodes, API-format workflow JSON, and the `/prompt` API |

ComfyUI is the execution canvas, not the whole workflow. The three-stage path `prompt enhancement → first-frame image → video generation` remains as a **quick path** for one-shot first versions; formal production follows the Agent-driven workflow in `skills/ai-video-studio/references/production-workflow.md`.

> [中文文档](README.zh-CN.md)

## Capabilities

- **Agent-driven production**: brief → research → creative direction → script/storyboard → execution → QC → skill evolution (documented under `references/`)
- **Reusable assets**: characters/scenes/styles with sidecar metadata, reuse-first across projects
- **ComfyUI workflow canvas**: ship, select, or edit API-format workflow JSON; run any workflow via script or UI
- **Your own keys**: API keys live in local node `config.json` files; no credentials are bundled
- **Quick path**: one sentence in, a short first version out, for rough cuts

## Quick start

1. ComfyUI running on `http://127.0.0.1:8188` (Comfy Desktop or headless)
2. Install nodes: copy `assets/comfyui-nodes/comfyui-mzsj-api` and `comfyui-huoshen-image` into ComfyUI's `custom_nodes/`
3. Configure keys: copy each node's `config.json.example` to `config.json` and fill in keys (see [CONNECTORS.md](CONNECTORS.md))
4. Initialize a project:

```bash
bash skills/ai-video-studio/scripts/init-project.sh <project-dir>
```

This creates `project.md`, a `.gitignore`, and directories for source material, reusable assets, storyboards, workflows, shots, audio, finals, and run records.

5. Run a specific API-format workflow:

```bash
python3 skills/ai-video-studio/scripts/run-workflow.py \
  assets/workflow_api_mzsj_video.json \
  --project <project-dir> \
  --set '1.inputs.prompt="..."' \
  --dry-run
```

`--dry-run` validates and prints the workflow without submitting. Remove it to submit via ComfyUI `/prompt`, poll to completion, and record `workflow.json`, `history.json`, and `run.json` under `<project-dir>/runs/<run-name>/`. For other workflows, inspect their JSON to identify adjustable node fields.

6. Quick path with the compatible one-line script:

```bash
bash skills/ai-video-studio/scripts/make-video.sh "rainy neon street, cyberpunk" \
  --duration 5 --resolution 720p
```

The script health-checks ComfyUI, auto-starts it if down, injects parameters, submits, polls, and opens the result.

Optional env overrides: `COMFY_SERVER`, `COMFY_WORKFLOW_TPL`, `COMFY_PYTHON`, `COMFY_OUTPUT_DIR`, `COMFY_ROOT`.

## Contents

| Path | What |
|---|---|
| `skills/ai-video-studio/SKILL.md` | Agent Skill entry: capabilities, default production path, quick path, cost discipline |
| `skills/ai-video-studio/agents/openai.yaml` | Skill UI metadata for Codex-compatible hosts |
| `skills/.../references/` | Production workflow, prompt craft/templates, ComfyUI operations, asset management, long video, QC, skill evolution |
| `skills/.../scripts/init-project.sh` | Project skeleton generator |
| `skills/.../scripts/make-video.sh` | One-line three-stage quick path (self-healing) |
| `skills/.../scripts/run-workflow.py` | Generic API workflow submit + poll, records runs under `<project>/runs/` |
| `skills/.../assets/` | Standalone Skill copies of the quick-path workflow and project template |
| `assets/workflow_api_mzsj_video.json` | Three-stage API-format quick-path template |
| `assets/project-template/` | Plugin-level mirror of the project template |
| `examples/workflows/` | Curated API-format workflow library — see its [README](examples/workflows/README.md) |
| `assets/comfyui-nodes/` | Two custom node packs (source) + `config.json.example` |
| `.qoder-plugin/plugin.json` | Qoder plugin manifest |
| `CONNECTORS.md` | Which API keys are needed and where to put them |

## Installation

- **Qoder**: install the whole directory as a plugin (`.qoder-plugin/plugin.json`)
- **Other agent platforms** (Claude Code / Cursor / Codex / ...): copy `skills/ai-video-studio/` into the platform's skills directory (open SKILL.md format)
- **ComfyUI only**: copy the two node packs from `assets/comfyui-nodes/` into `custom_nodes/`, configure keys, done

## Limitations

- `make-video.sh` auto-start/open behavior targets macOS (`open` and default install paths); Linux support for the one-line path is on the roadmap
- The default three-stage template only connects an automatically generated first frame. The bundled video node also exposes last-frame and single-reference-image inputs, but they require an IMAGE-producing upstream node and a small compatibility test. Video/audio multimodal reference and precise editing require another node or workflow
- Generation runs on third-party API platforms; their pricing and terms apply. This package only provides technical integration.

## Provenance

- Skills and nodes were developed and verified end-to-end on a local Mac (ComfyUI v0.30.2 / Comfy Desktop 1.0.37)
- Prompt methodology is a distilled summary of vendor manuals and the vendor app's built-in agent knowledge; original text remains copyrighted by its owners and is not redistributed here
- Logo is a locally generated SVG

## Related ecosystem

This project believes the real value of agent tooling is a stock of high-quality, ready-to-use workflows and skills:

- **Workflows**: see `examples/workflows/` — 16 curated API-format workflows, credited to [Lesilva/comfyui-workflows](https://github.com/Lesilva/comfyui-workflows)
- **Skills**: the open SKILL.md standard works across Claude Code / Codex / Gemini CLI / Cursor / Qoder and more. Good starting points: [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) (1000+ curated skills) and [awesome-claude-code-skills](https://github.com/helloianneo/awesome-claude-code-skills) (scene-based picks)

## License

MIT (see [LICENSE](LICENSE)).
