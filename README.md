# AI Video Studio

An open Skill/Plugin that teaches an existing agent how to make videos. It does not implement another app, CLI product,
agent runtime, or general orchestrator: the host agent (Codex by default) already understands the customer, invokes tools,
and delivers the work.

<p align="center">
  <a href="https://guojiz.github.io/"><img alt="Website" src="https://img.shields.io/badge/website-guojiz.github.io-111111?style=flat-square"></a>
  <a href="https://github.com/Guojiz/Sponsors"><img alt="Sponsor" src="https://img.shields.io/badge/sponsor-support-111111?style=flat-square"></a>
</p>

<p align="center">
  <a href="https://guojiz.github.io/"><strong>Author website</strong></a>
  · <a href="https://x.com/guojizh">X</a>
  · <a href="https://space.bilibili.com/3493114115263006">Bilibili</a>
  · <a href="https://youtube.com/@guojizh">YouTube</a>
  · <a href="https://github.com/Guojiz/Sponsors">Sponsor</a>
</p>


## Core model

- **Agent** — operator: understand the goal, choose the next step, inspect, revise, and deliver.
- **Skill** — reusable production methods, judgment criteria, and corrections.
- **Assets** — inputs, visible outputs, lineage, versions, and customer decisions.
- **ComfyUI** — the workflow-as-code workbench, execution surface, and technical debugger.

The customer talks to the agent. The agent normally creates the lowest-cost visible artifact that resolves the current
uncertainty—a direction image, key frame, or test clip—then continues from customer feedback. ComfyUI opens when the
customer wants technical detail or manual control. A workflow is a tool, not the product menu.

## Contents

```text
skills/ai-video-studio/
  SKILL.md                    platform-neutral production method
  references/                production, assets, QC, ComfyUI, and host mappings
  scripts/init-project.sh    minimal durable project facts
  scripts/run-workflow.py    generic API workflow execution and factual run records
  scripts/workflow-doctor.py preflight node/resource checks
  mcp/                       optional thin Codex-to-ComfyUI HTTP bridge
  assets/                     distributable templates, deployment config, project template
assets/comfyui-nodes/         ComfyUI custom nodes
examples/workflows/           research policy; no unlicensed third-party JSON redistribution
```

## Use

After installation, tell the agent:

> Use `$ai-video-studio`. Start with one visible result that lets me judge the direction, then continue from my feedback.

For a durable project, the agent may initialize:

```bash
bash skills/ai-video-studio/scripts/init-project.sh ./my-video --name "My Video" --git
```

This creates only `project.md`, `assets.md`, `decisions.md`, `workflows/`, and `.gitignore`. Other directories appear
only when work produces them.

The agent can execute any ComfyUI API workflow internally:

```bash
python3 skills/ai-video-studio/scripts/workflow-doctor.py workflow.json
python3 skills/ai-video-studio/scripts/run-workflow.py workflow.json \
  --project ./my-video --set '1.inputs.prompt="rainy street"' --dry-run
```

Removing `--dry-run` submits the workflow. These commands are deterministic internal tools, not the customer interface.

Codex can expose the same registry, doctor, and runner through the optional STDIO bridge at
`skills/ai-video-studio/mcp/comfyui_mcp.py`. See its `README.md` for installation and safety configuration. The bridge
does not replace the agent, and live generation remains a write-approved tool action.

## Configuration and capability

The project separates model capability, instance deployment, and external-service contract. A distributable workflow has a
manifest. Real API keys stay in local `config.json`; only examples are published.

**The skill binds only to ComfyUI.** No model or API service is bundled, assumed, or configured by default. Any use
of an external service (API-backed custom nodes, remote GPU platforms, third-party services) is a local, explicitly
chosen configuration: the agent must ask the customer which service to use, confirm authorization and cost before
generating, and never fall back to a default service.

Workflow selection depends on current `object_info`, deployment configuration, license, and verification status. External JSON
enters the public verified library only after its redistribution license, dependencies, and evidence are known.

## Verification scope

Validated by automated tests: Skill structure, Shell/Python/JSON, minimal project initialization, runner dry-run/mock
paths, workflow doctor, and the MCP lifecycle (instance resolution/locking, submit/status, idempotency, queue/cancel,
download with sha256, upload with manifest bindings). The zero-model smoke workflow was **live-tested** end-to-end on a
real ComfyUI (upload → submit → status → download) and is kept as a repeatable fixture.

Real production evidence provided by the operator: the remote GPU instance has successfully generated many videos
through this stack, so video-model workflows are in routine use even though Codex itself did not re-run a paid
generation during this work. Keep that distinction explicit in release notes.

Long-video support is an **agent-guided editing workflow**: segment planning, continuity facts, QC, rough cuts, and
approved-only delivery are decisions the agent makes with the customer, executed by deterministic scripts
(`media-probe.py`, `rough-cut.py`, `deliver.py`) and FFmpeg. The scripts are unit-tested with mocks; the full
multi-segment fixture acceptance has not been run, so long-video stays
`design documented, execution unverified` until that evidence exists.

## Install

- Codex: copy the full `skills/ai-video-studio/` directory into a discoverable Skills directory.
- Qoder: install the repository through `.qoder-plugin/plugin.json`, or copy the Skill.
- Other `SKILL.md` hosts: copy the Skill and map semantic actions to their own file, terminal, and multimodal tools.

The Qoder manifest is compatibility packaging; it is not a second agent runtime.

## Website and other links

No separate product site is required for this repository. The public face of the work is the author website, this GitHub repo, and the projects below.

| | |
| --- | --- |
| **Project page** | https://guojiz.github.io/ai-video-studio/ |
| **Author website** | https://guojiz.github.io/ |
| **X** | https://x.com/guojizh |
| **Bilibili** | https://space.bilibili.com/3493114115263006 |
| **YouTube** | https://youtube.com/@guojizh |
| **Sponsor** | https://github.com/Guojiz/Sponsors |

### Other open-source projects

- [GitLearnOS](https://guojiz.github.io/gitlearnos/) — learner-owned Git memory
- [Word Snap](https://guojiz.github.io/word-snap/) — bilingual vocabulary matching
- [AI Subtitle Extractor](https://github.com/Guojiz/ai-subtitle-extractor)
- [Design Master](https://github.com/Guojiz/design-master)
- [AI Video Studio](https://github.com/Guojiz/comfyui-minimax-h3-studio)
- [llm-provider-compat](https://github.com/Guojiz/llm-provider-compat)
- [Claude Desktop Tweak Models](https://github.com/Guojiz/claude-desktop-tweak-models)
- All projects: [github.com/Guojiz](https://github.com/Guojiz)
