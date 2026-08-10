# AI Video Studio

An open Skill/Plugin that teaches an existing agent how to make videos. It does not implement another app, CLI product,
agent runtime, or general orchestrator: the host agent (Codex by default) already understands the customer, invokes tools,
and delivers the work.

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
  assets/                     distributable templates, provider/profile, project template
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

The project separates model capability, provider API contract, and deployment profile. A distributable workflow has a
manifest. Real API keys stay in local `config.json`; only examples are published. The current MZSJ `/v1/videos` adapter
accepts HTTPS image URLs. Legacy data-URL behavior must be selected explicitly and is a different contract.

Workflow selection depends on current `object_info`, provider/profile, license, and verification status. External JSON
enters the public verified library only after its redistribution license, dependencies, and evidence are known.

## Verification scope

Validated: Skill structure, Shell/Python/JSON, minimal project initialization, runner dry-run/mock paths, workflow doctor,
and live ComfyUI node/enum preflight for the bundled text template. The `/v1/videos` adapter payload/download behavior
was mock-validated against the current contract supplied by the user, but no new paid generation ran through this exact
template, so its manifest says `dry-run`, not end-to-end `live-tested`.

## Install

- Codex: copy the full `skills/ai-video-studio/` directory into a discoverable Skills directory.
- Qoder: install the repository through `.qoder-plugin/plugin.json`, or copy the Skill.
- Other `SKILL.md` hosts: copy the Skill and map semantic actions to their own file, terminal, and multimodal tools.

The Qoder manifest is compatibility packaging; it is not a second agent runtime.
