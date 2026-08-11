---
name: ai-video-studio
description: >
  教 Agent 使用 Skill、项目资产与 ComfyUI 制作视频，并在需要时选择、修改或运行
  workflow。用于生成视频、制作广告/短片/MV/长视频、从已有素材逐步创作、管理中间
  产物与版本、检查和局部返工、把成功方法沉淀为新 Skill。用户常说：做条视频、生成
  片子、先给我看效果、继续做下一镜、打开 ComfyUI、跑这个 workflow、保存这个流程。
---

# AI Video Studio

## 定位

把当前宿主 Agent（默认 Codex）作为操作主体，把客户作为利用主体和最终裁决者。
不要在本插件内重新实现 Agent、编排器、状态机、App、CLI 产品或独立画布。

四个核心各司其职：

| 核心 | 职责 |
| --- | --- |
| Agent | 理解客户、选择下一步、操作工具、检查结果、整理和交付 |
| Skill | 教 Agent 怎样做好一类视频任务，保存方法、判断标准和纠错经验 |
| 资产 | 保存输入、可见产物、来源关系、版本和客户决定 |
| ComfyUI | workflow-as-code 的操作面、执行面和技术调试器 |

Plugin 只是把 Skill、节点、workflow、配置示例和必要适配脚本打包。客户入口始终是对话，
不是脚本命令。ComfyUI 必要但不垄断执行；直接 API、FFmpeg 或其他工具能更可靠完成时可以使用。

## 默认行为：渐进创作

不要先把整部作品固化成完整流水线，也不要把一句话直接赌成最终电影。循环执行：

1. 读取客户要求、选中文件及项目中的 `project.md`、`assets.md`、`decisions.md`。
2. 判断任务可以直接完成，还是需要逐步创作。
3. 选择当前**成本最低、最能帮助客户判断方向**的下一项可见产物。
4. 生成并直接展示产物，简要说明它来自什么、解决什么、下一步可以是什么。
5. 根据客户反应继续、修改、换方向或停止；只重做受影响部分。
6. 每次执行后更新资产来源和状态；稳定决定写入 `decisions.md`。
7. 达到交付目标后做 QC、整理最终文件，并在有意义的里程碑记录版本。

“下一项产物”可以是方向卡、效果图、角色/场景参考、文本分镜、单个测试镜头、视频片段或粗剪；
由任务与客户节奏决定。镜头表、批量生成和完整制作计划都是可选工具，不是所有项目的前置门。

## 客户交互

- 已明确的要求直接执行，不重复确认。
- 可逆、低成本且不改变核心方向的工作自动完成并报告。
- 中等风险先做小样或低成本预览，让客户看见后再决定。
- 高成本、授权/公开上传、不可逆动作或核心方向分叉必须先确认。
- 客户想逐步看时，每个重要可见产物后停下；客户要求少打扰时，推进到下一个重要里程碑。
- 技术细节默认隐藏。客户要求查看、接管或调试时才打开 ComfyUI，并解释语义输入输出。

不要把“一次确认完整 shot 表和总预算后批量生成”写成默认生产制度。预算授权只能覆盖客户已经
理解的范围；新方向、新公开上传或明显扩大的费用需要重新确认。

## 项目事实与资产

需要持续、多产物或可回退的任务时，初始化最小四件套：

```bash
bash scripts/init-project.sh <项目目录> [--name "项目名称"] [--git]
```

只预建：

- `project.md`：当前目标、锁定约束、进度和下一最小步骤；
- `assets.md`：产物、来源、版本、workflow/run 关系；
- `decisions.md`：客户确认、否决和替代的稳定决定；
- `workflows/`：本项目实际选择或修改的 workflow JSON。

其他目录在真正产生相应内容时再创建。资产状态只写在 `assets.md`，不因状态变化搬文件：

- `temporary`：试验或失败输出，可以清理；
- `candidate`：值得客户查看或比较；
- `approved`：客户接受或已被正式下游采用。

只有 Agent 能依据客户反馈更新资产语义。runner 只记录客观执行事实，不能自动决定 `approved`。
完整规则见 `references/asset-management.md`。

## ComfyUI：workflow as code

把 workflow 当代码处理：读取现有 JSON，根据任务选择或修改，复制到项目 `workflows/`，先体检/
dry-run，再执行并读取 history。不要让预设 `mode` 或节点编号成为产品抽象。

```bash
python3 scripts/workflow-doctor.py <workflow.json>
python3 scripts/run-workflow.py <workflow.json> \
  --project <项目目录> \
  --set '节点ID.inputs.字段=JSON值' --dry-run
```

去掉 `--dry-run` 才会提交。`run-workflow.py` 是 Agent 内部的确定性适配工具，不是用户产品入口。
它保存实际 workflow、history、run 状态和输出；需要关联镜头时可选用 `--shot`、`--iteration`。

Codex 配置了随 Skill 提供的 `mcp/comfyui_mcp.py` 时，优先通过 MCP 的 `list_workflows`、
`inspect_workflow`、`doctor` 和 `run_workflow` 使用这些相同工具。MCP 只是 ComfyUI HTTP API 与现有
脚本的薄适配层，不负责创意规划、资产审批或状态机。先用 `dry_run=true`；只有客户已明确要求生成时
才允许实际提交。每次执行前先确认当前工具清单里是否已有 `mcp__comfyui__*`；MCP 存在时使用 MCP，
不能因一次工具调用失败就宣称 MCP 未安装。正式提交必须绑定一个显式实例（项目锁定的 MCP 实例、
`--server` 或 `COMFY_SERVER`），任何回退都要写入 run 记录并说明原因，禁止静默落到
`127.0.0.1:8188`。已有同名 `runs/<run-name>` 记录受保护，不允许覆盖。

实例与任务流程：

1. 项目开始时用 `list_instances` 查看 catalog；只有一个实例时自动选择但必须报告，多个实例时
   用 `select_instance` 让客户选择并锁定到项目，选择结果写入 `decisions.md`。
2. 正式生成用 `submit_workflow`（立即返回 `run_id`/`prompt_id`/`status`），不要用同步阻塞工具。
3. 用 `get_run_status` 按已有 `prompt_id` 查询，禁止重复提交；`instance_unreachable` 与
   `monitoring_timeout` 不是失败，接口恢复后按同一 ID 补查。
4. 完成后用 `download_artifacts` 把产物带哈希与来源保存进项目；`approved` 仍由 Agent 依据客户
   反馈判断并写入 `assets.md`。
5. 需要取消时用 `cancel_run`；运行中任务若后端只能全局 interrupt，必须如实报告 unsupported，
   不得冒充精确取消。
6. H3 参考图用 `upload_asset(..., authorized=true, workflow_id=..., semantic_input="reference_image")`
   上传并按 manifest `bindings` 注入，不猜测节点编号；未获得授权不得上传敏感/肖像/版权素材。

正式提交前按 `references/creative-gates.md` 做参考图、节奏/时长与提示词检查。多片段、粗剪、
FFmpeg 后期与 approved-only 交付按 `references/post-production.md` 执行；当前在得到 fixture
验证前保持 `long-video: design documented, execution unverified`。

正式库中的每个 workflow 必须声明用途、输入输出、依赖、部署配置、来源、许可和验证状态。
项目修改版放项目 `workflows/`；许可或验证不明的外部 workflow 只能作为本地研究材料，不能冒充正式能力。
详情见 `references/comfyui-workflows.md`。

## 配置分层

始终区分：

```text
模型能力 != 实例部署配置 != 外部服务契约
```

- 模型/创作知识放提示词 reference；
- 实例部署配置描述当前 ComfyUI 实例的默认模型、尺寸、限制和实测观察；
- 外部服务契约只有在用户明确选择某个服务时才描述其接口、状态和下载规则；
- API Key 只保存在本机忽略文件中，不进入对话、workflow 或 Git。

只有实例配置限制影响当前请求时才向客户简要说明。本 Skill 只绑定 ComfyUI，不内置、不默认
任何模型或 API 服务；使用任何外部服务前必须先向客户确认服务、配置与费用授权。

## 质量、返工与长视频

- 结果拿到后检查技术完整性、内容符合度、连续性和声音；无法可靠视觉判断时使用多模态工具或请客户看候选。
- 一次只改变一个主要变量，保留旧候选；局部失败只重做受影响资产及下游。
- 同一策略连续失败 3 次、预算耗尽、目标漂移或需要新授权时停止并请求决策。
- 长视频按需要逐段推进：先验证角色/场景/风格锚点和关键镜头，再继续其他片段；不要把 `duration` 调长当成长片方案。
- 字幕、响度、转场、封装等确定性问题优先使用 FFmpeg/剪辑工具，不浪费生成额度。

后期脚本（`scripts/media-probe.py`、`scripts/rough-cut.py`、`scripts/deliver.py`）只在
需要抽帧 QC、粗剪或交付时按需调用；本机无 FFmpeg 时它们给出可操作错误而不是自动安装。
粗剪自动版本化，交付只处理 approved 清单并生成 `delivery.json`。当前长视频为
`long-video: design documented, execution unverified`，不得冒充已验证能力。

### 剪辑是 Agent 指导的工作

长视频的真正难点是剪辑决定，不是单段生成。工具只执行，不替 Agent 决定：

- Agent 决定拆段粒度、每段的起点/落点、转场与声音策略，并把这些写进 edit plan/EDL。
- 拿到候选先做接缝验收：相邻两段的末状态与起点是否连续，主体/场景/光照锚点是否成立；
  接不上时只重做接缝附近，不整片重抽。
- Agent 先做粗剪判断节奏（钩子、推进、转折、收尾），再决定补镜、返工或修改计划；
  `rough-cut.py` 只负责规范化与拼接，版本化保护旧粗剪。
- `approved` 只由 Agent 依据客户反馈认定，写入 `assets.md`；`deliver.py` 只复制清单内
  approved 文件，绝不替 Agent 判断最终候选。
- 每段生成都关联 run、workflow、实例与参考资产；成片必须可回溯到这些事实。

按需读取 `references/quality-control.md`、`references/rework.md` 和 `references/long-video.md`。
创作质量门见 `references/creative-gates.md`；确定性后期与交付见 `references/post-production.md`。

## Skill 演进

客户明确要求保存流程、同类任务重复出现或相同纠错反复发生时，生成 Skill 草稿。安装、覆盖或大幅
修改正式 Skill 前告知客户；具体创建与验证交给宿主的 `skill-creator`，不要在本 Skill 重复实现。

## 文档地图

| 文档 | 何时读取 |
| --- | --- |
| `references/production-workflow.md` | 正式制作或需要判断下一步 |
| `references/comfyui-workflows.md` | 选择、修改、体检、执行或调试 workflow |
| `references/asset-management.md` | 登记产物、来源、状态、授权和 Git 版本 |
| `references/prompt-craft.md` | 编写或修正视频提示词 |
| `references/prompt-templates.md` | 需要提示词模板 |
| `references/quality-control.md` | 检查候选、交付或决定返工 |
| `references/rework.md` | 局部修改、版本比较和回滚 |
| `references/long-video.md` | 多镜头或长视频 |
| `references/creative-gates.md` | 正式提交前的参考图、节奏/时长、提示词检查 |
| `references/post-production.md` | 抽帧 QC、粗剪、规范化、字幕/音频/交付 |
| `references/skill-evolution.md` | 从实践生成或更新 Skill |
| `references/codex.md` | Codex 宿主的工具映射 |
| `references/qoder.md` | Qoder 兼容安装与路径 |
