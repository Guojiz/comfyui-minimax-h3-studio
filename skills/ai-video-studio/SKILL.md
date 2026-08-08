---
name: ai-video-studio
description: >
  AI 视频生产技能，以 Agent、Skill、资产、ComfyUI 四个核心组织视频制作：
  Agent 负责理解需求与创意编排，Skill 沉淀可复用流程与审美，资产实现角色/场景/风格
  跨项目复用，ComfyUI 是本技能的画布与技术执行面。适用：生成视频、做短片/广告/
  种草视频、生成首帧图、长视频分段制作、复用角色资产、运行 ComfyUI 工作流出片。
  触发表述：生成视频、做一条片子、出个视频、文生视频、图生视频、跑工作流、
  视频 production、video generation、make a clip、保存这个流程为 skill。
  可驱动本机 ComfyUI 的本地模型、第三方 API 与任意已安装节点；能力以实际加载为准。
---

# AI Video Studio — 视频生产 Skill

> 版本：2.0.0（四核心重构：Agent / Skill / 资产 / ComfyUI，三段式降为快速路径）

本技能把“拍一条片”拆成四个可复用核心：

| 核心 | 在本技能中的角色 | 主文档 |
| --- | --- | --- |
| Agent | 创作大脑：解析简报、调研、定方向、调度执行、验收、沉淀经验 | `references/production-workflow.md` |
| Skill | 可复用知识与流程：本文件 + references + scripts | `references/skill-evolution.md` |
| 资产 | 角色/场景/风格/道具等可复用素材，跨项目调用，选择性入库 | `references/asset-management.md` |
| ComfyUI | 操作面/执行面/技术工作流画布：节点 + workflow JSON + API | `references/comfyui-workflows.md` |

ComfyUI 是执行入口，不是唯一流程。三段式“提示词增强 → 首帧生图 → 视频生成”
保留为**快速路径**：适合一句话出片；正式生产走 `references/production-workflow.md`。

## 环境事实（已验证）

- ComfyUI 服务：`http://127.0.0.1:8188`（Comfy Desktop 或 headless）
- 自定义节点包：
  - `comfyui-mzsj-api`：`DeepSeekPromptEnhance` / `MzsjVideoGenerate`
  - `comfyui-huoshen-image`：`HuoshenImageGenerate`
- API key 配置：各节点目录 `config.json`（仓库只带 `config.json.example`；真实 key 勿外传、勿入库）
- 三段式模板：Skill 内 `assets/workflow_api_mzsj_video.json`（插件根另有镜像）
- 精选工作流库：插件根 `examples/workflows/`（video / first-frame / upscale / product 四类）
- 产物目录：`~/ComfyUI-Installs/ComfyUI/ComfyUI/output/`（图片 `huoshen_*.png`）与 `output/mzsj/`（视频）

## 能力边界（快速路径与 Studio 分层）

**默认三段式快速路径当前直接暴露：**

- 提示词增强（DeepSeek 兼容接口）
- 首帧生图（`HuoshenImageGenerate`）
- 文生视频 / 自动生成单张首帧后的图生视频（`MzsjVideoGenerate`）

打包的 `MzsjVideoGenerate` 节点还定义了 `last_frame` 与单张 `reference_image`
可选输入；接入能输出 `IMAGE` 的上游节点后可以组成相应 workflow，但现成模板和脚本尚未
把它们封装成开箱即用路径，真实服务兼容性需在提交前验证。

**打包节点当前未实现，或默认快速路径未封装（不是整个 Studio 不支持）：**

- 素材上传与图/视频/音频多模态参考（锁脸/锁动作/运镜参考等）
- 视频/音频精准编辑（替换、局部修改、背景替换、台词替换）
- 单次生成长视频（单条 4–15 秒）

本机 ComfyUI 可加载**任意已安装节点与工作流**；首尾帧、参考素材、精准编辑等若由
其他工作流或扩展节点提供，按该工作流实际能力执行，本 Skill 不限制实例能力。
提交前用 `object_info` 确认实际加载的节点，不要把默认打包节点的边界扩大成产品边界，
也不要声称默认打包节点支持未验证的能力。

上游模型能力说明只作为提示词创作参考，不代表默认打包节点已实现。

## 默认生产路径（正式流程）

1. **简报**：受众、平台/画幅、时长、用途、风格、必须出现/禁止出现、素材与授权
2. **调研与创意**：按需求做调研，收集本地参考证据
3. **方向锁定**：一句话核心创意（主体+地点+事件+题材风格）+ 风格卡，与用户确认
4. **资产准备**：按资产纪律收集/复用/登记素材
5. **剧本与分镜**：shot 列表（景别+内容+运镜+动作+台词+音效）；>15 秒走长视频规划
6. **提示词构建**：三段公式 + 模板（见下节），提交前过踩坑表
7. **执行**：在 ComfyUI 选择/提交工作流；高成本提交前确认
8. **验收**：两层 QC 通过后交付；记录产物与失败经验
9. **沉淀**：把可复用素材存为资产、把纠错经验写回 Skill

每步细节见 `references/production-workflow.md`。第 7 步若只需快速一版，可走下方快速路径。

新项目先初始化资产目录（已有内容不会被覆盖）：

```bash
bash scripts/init-project.sh <项目目录> [--name "项目名称"] [--git]
```

## 快速路径：三段式（一句话出片）

仅当用户要“快速出一版”、参数齐全时使用；需要改工作流结构或正式生产时走默认路径。

固定三段式直接执行 `scripts/make-video.sh`，不要复制脚本另造同类实现（Qoder 安装后路径
`.qoder/skills/ai-video-studio/scripts/make-video.sh`）：

```bash
bash scripts/make-video.sh "雨夜霓虹街道，赛博朋克" \
  [--duration 5] [--resolution 720p] [--size 1536x1024] [--no-open] [--dry-run]
```

- 退出码：0 成功；2 自动拉起失败；3 执行错误（已打印节点与异常）；4 超时
- 服务未启动时脚本会自动拉起 ComfyUI 并等待就绪，日志 `~/Library/Logs/comfyui-headless.log`
- 需要指定项目目录、保留 run 记录、修改任意节点字段或做无副作用 `--dry-run` 时，改用 `scripts/run-workflow.py`
- 单步能力：只生图/只增强提示词 → 按 `references/comfyui-workflows.md` 直接提交对应 API JSON

## ComfyUI 操作要点

- 健康检查：`curl -s http://127.0.0.1:8188/object_info | grep MzsjVideoGenerate` 无结果 → 服务未启动或节点未加载
- 任意 API 格式 workflow：用 `scripts/run-workflow.py` 校验、注入节点字段、提交、轮询，并把实际 workflow/history/run 记录保存到项目 `runs/`
- 提交流程：POST `/prompt` 得 `prompt_id`，轮询 `/history/<prompt_id>` 到终态；错误读 `execution_error`
- DNS 解析到 `198.18.x.x` 且超时 → 用户代理软件掉线，提醒恢复代理，勿反复重试
- 同一参数失败 ≥3 次必须停下换策略或询问用户（anti-loop）
- 工作流形态、批量、复用与故障排查见 `references/comfyui-workflows.md`

## 提示词铁律（提交前必过）

详细方法论与完整模板见 `references/prompt-craft.md` 与 `references/prompt-templates.md`。
官方公式：`完整提示词 = 参考素材说明 + 核心创意 + 画面过程说明`。铁律：

1. **素材引用**：有素材时用 `@图片N/@视频N` 编号并逐个写用途；默认快速路径无素材上传时跳过该段
2. **核心创意四要素**：主体 + 地点 + 事件 + 题材风格；默认会切镜，一镜到底需明说
3. **画面过程按 shot 分段**：景别+内容+运镜+动作+台词+音效；台词长度对齐（中文 3–4 字/秒）
4. **正向描述**：负向词会激活被禁对象，改写为目标可见状态
5. **声音控制**：不要配乐必须显式写 `非叙事性音乐：N/A`
6. **文字必给原文**：具体文字/Logo/标语写出原文
7. **锁介质**：每条 prompt 末尾写 `Medium: <one primary medium>`
8. **提交前过踩坑表**：prompt-craft.md 第三节逐条自检

## 资产纪律（摘要）

- 真实 key、输出产物、临时文件不入库；源码、配置示例、workflow JSON、文档、精选示例素材入库
- 资产命名 `类别-名称-版本`，配元数据文件记录用途/来源/授权/规格
- 新项目优先复用已登记资产，不重复生成
- Git 选择性版本管理与完整目录规范见 `references/asset-management.md`

## 长视频

- 单条生成 4–15 秒；>15 秒 = 规划 → 分段生成 → 连续性锚定 → Agent 用 FFmpeg/剪辑工具拼接
  （工具可用性以本机环境为准）
- 分段规划、连续性锚点、台词预算、失败修复见 `references/long-video.md`

## 质量控制

- 提交前 QC（提示词）与结果 QC（技术+内容）都要做；验收前与用户确认“完成”定义
- 一次只改一个变量；失败 ≥3 次停下询问；记录失败样例作为迭代证据
- 完整清单见 `references/quality-control.md`

## Skill 演进

- 同一流程重复 ≥3 次、用户每次做相同修正、流程含隐性知识时，提议保存为 Skill
- 新知识先沉淀到 references 再链接进 SKILL.md，保持本文件精简
- 创建/修改/验证/迭代流程见 `references/skill-evolution.md`

## 成本纪律

- 每次完整三段式快速路径消耗 1 次提示词增强 + 1 次生图 + 1 次视频额度；其他 workflow 按实际节点计算
- 高成本操作（视频生成、批量、长视频多段）前向用户确认
- 调试用最小任务；用户未确认前不重复提交相同任务

## 文档地图

| 文档 | 何时加载 |
| --- | --- |
| `references/production-workflow.md` | 正式做一条片、用户要求按流程执行 |
| `references/prompt-craft.md` | 写/改提示词、失败排查 |
| `references/prompt-templates.md` | 需要空白模板或完整范例 |
| `references/comfyui-workflows.md` | 任何一次执行、改工作流、批量、故障排查 |
| `references/asset-management.md` | 准备/检索/登记素材、决定入库内容 |
| `references/long-video.md` | 目标超过 15 秒或多镜头叙事 |
| `references/quality-control.md` | 提交前、拿到结果后、重试前、交付前 |
| `references/skill-evolution.md` | 创建/修改/保存 Skill、沉淀经验 |
