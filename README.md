# AI Video Studio (`ai-video-studio`)

**One sentence → finished video.** A Qoder plugin + Agent Skill that drives your local
ComfyUI through a pure-API pipeline:

```
prompt enhancement (LLM)
   → first-frame image generation
      → video generation
```

**Bring your own API keys. No local models, no GPU required** — runs fine on a MacBook.

> [中文文档](README.zh-CN.md)

## Demo

First frame image generated first, then animated into video (~4 min end-to-end):

![Sample first frame](examples/sample-first-frame.png)

▶ Watch: [`examples/sample-video.mp4`](examples/sample-video.mp4)

## Why this project

Existing community projects either run **open weights locally**
(requires a high-end GPU) or only build prompts. This project is different:

- **BYO API key, pure cloud pipeline** — works on any machine
- **Agent Skill wrapper** — say "make a video about X" and the agent handles the rest
- **Self-healing script** — auto-starts your ComfyUI backend if it's down
- **Official prompt engineering baked in** — the vendor's official user manual ships in
  `references/h3-manual.md`, with its prompt formula and pitfall checklist distilled into
  `references/prompt-craft.md`, plus ready-to-use complete prompt templates in
  `references/prompt-templates.md`

## Three ways to use it

| You are… | How to use |
|---|---|
| Qoder user | Install this whole directory as a plugin (`.qoder-plugin/plugin.json`) |
| Claude Code / Cursor / Codex / other agent user | Copy `skills/ai-video-studio/` into your platform's skills directory (SKILL.md open standard) |
| ComfyUI-only user | Copy the two node packs from `assets/comfyui-nodes/` into your `custom_nodes/`, fill in keys, done |

## Quick start

1. **ComfyUI** running on `http://127.0.0.1:8188` (Comfy Desktop or headless)
2. **Install nodes**: copy `assets/comfyui-nodes/comfyui-mzsj-api` and
   `comfyui-huoshen-image` into ComfyUI's `custom_nodes/`
3. **Configure keys**: in each node directory, copy `config.json.example` → `config.json`
   and fill in your keys (see [CONNECTORS.md](CONNECTORS.md))
4. **Make a video**:

```bash
bash skills/ai-video-studio/scripts/make-video.sh "rainy neon street, cyberpunk" \
  --duration 5 --resolution 720p
```

The script health-checks ComfyUI, **auto-starts it if down**, injects parameters,
submits, polls, and opens the result.

Optional env overrides: `COMFY_SERVER`, `COMFY_WORKFLOW_TPL`, `COMFY_PYTHON`,
`COMFY_OUTPUT_DIR`, `COMFY_ROOT`.

## Contents

| Path | What |
|---|---|
| `skills/ai-video-studio/SKILL.md` | The Agent Skill: execution modes, prompt rules, cost discipline |
| `skills/.../references/prompt-craft.md` | Prompt engineering handbook (official formula + pitfall checklist) |
| `skills/.../references/h3-manual.md` | Official vendor user manual (source document, shipped as-is) |
| `skills/.../references/prompt-templates.md` | Complete ready-to-use prompt templates + worked examples |
| `skills/.../scripts/make-video.sh` | One-line video production script (self-healing) |
| `assets/workflow_api_mzsj_video.json` | Three-stage API-format workflow template |
| `examples/workflows/` | Curated library: 16 API-format workflows for video / first-frame / upscaling / product shots — see its [README](examples/workflows/README.md) |
| `assets/comfyui-nodes/` | Two custom node packs (source) + `config.json.example` |
| `.qoder-plugin/plugin.json` | Qoder plugin manifest |
| `CONNECTORS.md` | Which API keys you need and where to put them |

## Limitations & roadmap

- **macOS only for now** (the script uses `open` and Mac paths); Linux support is on the roadmap
- Reference mode (lock a face from a reference image), first/last frame, and
  multi-shot are **not yet** supported — the node layer needs asset-upload capability first
- Video and image generation run on third-party API platforms; their pricing and terms
  are governed by their official sites. This project only provides technical integration.

## Related ecosystem

This project believes the real value of agent tooling is a stock of high-quality, ready-to-use workflows and skills:

- **Workflows**: see `examples/workflows/` — 16 curated API-format workflows, credited to [Lesilva/comfyui-workflows](https://github.com/Lesilva/comfyui-workflows)
- **Skills**: the open SKILL.md standard works across Claude Code / Codex / Gemini CLI / Cursor / Qoder and more. Good starting points: [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) (1000+ curated skills) and [awesome-claude-code-skills](https://github.com/helloianneo/awesome-claude-code-skills) (scene-based picks)

## License

MIT (see [LICENSE](LICENSE)).
