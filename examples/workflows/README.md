# Curated Workflow Library / 精选工作流库

A hand-picked set of 16 **API-format** ComfyUI workflows that form the technical workflow canvas of the AI Video Studio Agent Skill. The Agent handles planning, the Skill supplies process and prompt discipline, Assets provide reusable inputs, and these workflows execute. All files are `/prompt`-ready JSON: suitable for scripting, batch runs, agent-driven automation, and manual loading in the ComfyUI UI.

中文：精选的 16 个 **API 格式** ComfyUI 工作流，是 AI Video Studio Agent Skill 的技术工作流画布——Agent 负责编排，Skill 提供流程与提示词纪律，资产提供可复用输入，这些 workflow 负责执行。全部为可直接走 `/prompt` 接口的 JSON，适合脚本化、批量、agent 自动化，也可在 ComfyUI UI 中手动加载。

## Categories / 分类

### video/ — Video generation & motion / 视频生成与动作迁移

| Workflow | Purpose |
| --- | --- |
| `Wan2.2极速文生视频KJ版本（已确保跑通）.json` | Fast text-to-video, verified runnable |
| `wan2.2文生视频(14B)GGUF适合16G以下显存.json` | Text-to-video for GPUs with ≤16 GB VRAM (GGUF) |
| `wan2.1 vace首尾帧视频.json` | First-&-last-frame video (pairs well with our first-frame stage) |
| `视频动作迁移WAN2.1-VACE-14B.json` | Motion transfer from a reference video |
| `万相MotionLoRA - 镜头推进.json` | Camera push-in motion via MotionLoRA |

### first-frame/ — Image generation for first frames / 首帧与文生图

| Workflow | Purpose |
| --- | --- |
| `FLUX 文生图 + ControlNet + 支持中文输入.json` | Text-to-image with structure control, Chinese prompts supported |
| `万相2.2文生图-图生图-fp8量化版-Magic-Wan-Image.json` | Text/image-to-image, fp8 quantized |
| `qwen—image万物迁移合集.json` | Subject/style transfer collection |

### upscale/ — Upscaling & restoration / 高清放大与修复

| Workflow | Purpose |
| --- | --- |
| `Kontext 绝对无损放大.json` | Lossless-style upscaling |
| `最强高清放大还原.json` | Aggressive upscale + detail restoration |
| `商业级高清放大工作流.json` | Commercial-grade upscaling |
| `Flux kontext 高清放大.json` | Flux/Kontext-based upscaling |

### product/ — Character consistency & product shots / 人物一致性与产品电商

| Workflow | Purpose |
| --- | --- |
| `Kontext人物换姿势【解决一致性】.json` | Change pose while keeping character identity |
| `模特一键换衣-电商.json` | One-click outfit swap for e-commerce |
| `FLUX-产品生成背景.json` | AI background generation for product cutouts |
| `kontext电商产品打光_渲染.json` | Product relighting & rendering |

## How to use / 使用方式

1. 用 ComfyUI Manager 安装 workflow 中缺失的自定义节点，并按需准备对应模型权重。
2. 将 `LoadImage` / `LoadVideo` 节点的占位输入替换为你自己的素材。
3. 提交执行，三选一：
   - 通用脚本：`python3 skills/ai-video-studio/scripts/run-workflow.py <file>.json --project <project-dir> --set '1.inputs.prompt="..."' --dry-run`；去掉 `--dry-run` 即真实提交并轮询，run 记录在 `<project-dir>/runs/`
   - 一键快速路径：`make-video.sh` 仍用于三段式一句话出片（见插件根 README）
   - 直接 `POST /prompt`，或在 ComfyUI UI 中加载
4. 详细依赖与 API 调用说明可参考上游仓库的 `docs/`。

English:

1. Install missing custom nodes with ComfyUI Manager and prepare the required model weights.
2. Replace the placeholder inputs in `LoadImage` / `LoadVideo` nodes with your own material.
3. Submit any of these ways:
   - Generic script: `python3 skills/ai-video-studio/scripts/run-workflow.py <file>.json --project <project-dir> --set '1.inputs.prompt="..."' --dry-run`; drop `--dry-run` to submit and poll, with the run recorded under `<project-dir>/runs/`
   - One-line quick path: `make-video.sh` remains available for the three-stage one-shot flow (see plugin root README)
   - POST `/prompt` directly, or load the JSON in the ComfyUI UI
4. For detailed dependencies and API notes, see the upstream repository's `docs/`.

## Attribution & license / 来源与许可

These workflow JSON files are curated from [Lesilva/comfyui-workflows](https://github.com/Lesilva/comfyui-workflows), a public sharing repository intended for learning, modification, and reuse. The upstream repository carries no formal license file; the original author's sharing terms apply to these JSON files. Please credit the upstream repository when redistributing. Curation, organization, and documentation in this directory are provided under this project's MIT license.

中文：以上 workflow 精选自公开分享仓库 [Lesilva/comfyui-workflows](https://github.com/Lesilva/comfyui-workflows)。上游仓库未附正式 license 文件，JSON 文件遵循原作者的分享条款，再分发时请注明来源。本目录的精选、整理与文档部分按本项目的 MIT 许可提供。
