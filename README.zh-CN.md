# AI 视频工作室（ai-video-studio）

一个面向本地 ComfyUI 的视频生产 **Agent Skill** 包，围绕四个可复用核心组织：

| 核心 | 在本包中的角色 |
|---|---|
| Agent | 创作编排：解析简报、锁定方向、规划分镜、协调执行、验收结果 |
| Skill | 可复用流程与知识：`SKILL.md`、`references/`、`scripts/` |
| 资产 | 跨项目复用的角色、场景、风格与参考素材 |
| ComfyUI | 操作面/执行面/技术工作流画布：节点、API 格式 workflow JSON、`/prompt` API |

ComfyUI 是执行画布，不是全部流程。「提示词增强 → 首帧生图 → 视频生成」三段式仅保留为**快速路径**，适合先快速出一版；正式生产走 `skills/ai-video-studio/references/production-workflow.md` 的 Agent 完整流程。

> [English](README.md)

## 能力

- **Agent 生产流程**：简报 → 调研 → 创意 → 剧本/分镜 → 执行 → 验收 → 沉淀（细节见 `references/`）
- **可复用资产**：角色/场景/风格 + sidecar 元数据，新项目优先复用
- **ComfyUI 工作流画布**：可交付、选择或修改 API 格式 workflow JSON，脚本或 UI 均可执行
- **用户自有 key**：API key 只放本机节点 `config.json`，不内置任何凭据
- **快速路径**：需要粗剪样张时，一句话即可出短片

## 快速开始

1. 本机 ComfyUI 监听 `http://127.0.0.1:8188`（Comfy Desktop 或 headless）
2. 安装节点：把 `assets/comfyui-nodes/comfyui-mzsj-api` 和 `comfyui-huoshen-image` 复制到 ComfyUI 的 `custom_nodes/`
3. 配置 key：把各节点 `config.json.example` 复制为 `config.json` 并填写（见 [CONNECTORS.md](CONNECTORS.md)）
4. 初始化项目：

```bash
bash skills/ai-video-studio/scripts/init-project.sh <项目目录>
```

生成 `project.md`、`shots/index.md`、`.gitignore` 以及素材、分镜、workflow、音频、成片和运行记录目录。

运行任何 workflow 前先做实例体检，避免在模型额度窗口内才发现缺节点或模型：

```bash
python3 skills/ai-video-studio/scripts/workflow-doctor.py <workflow.json>
```

5. 运行指定 API 格式工作流：

```bash
python3 skills/ai-video-studio/scripts/run-workflow.py \
  assets/workflow_api_mzsj_video_text.json \
  --project <项目目录> \
  --set '1.inputs.prompt="..."' \
  --dry-run
```

`--dry-run` 只校验并打印，不提交。去掉它后脚本会提交到 ComfyUI `/prompt`、轮询到终态，并把 `workflow.json`、`history.json`、`run.json` 记录到 `<项目目录>/runs/<run-name>/`。其他 workflow 的可调节点与字段以其 JSON 为准。

6. 一键文生快速路径：

```bash
bash skills/ai-video-studio/scripts/make-video.sh "雨夜霓虹街道，赛博朋克" \
  --duration 5 --resolution 720p
```

脚本会健康检查、服务未启动时自动拉起、注入参数、文生视频提交、轮询并打开产物。

可选环境变量：`COMFY_SERVER`、`COMFY_WORKFLOW_TPL`、`COMFY_PYTHON`、`COMFY_OUTPUT_DIR`、`COMFY_ROOT`。

## 包含内容

| 文件 | 说明 |
|---|---|
| `skills/ai-video-studio/SKILL.md` | Agent Skill 主入口：能力、默认生产路径、快速路径、成本纪律 |
| `skills/ai-video-studio/agents/openai.yaml` | Codex 等宿主使用的 Skill 界面元数据 |
| `skills/.../references/` | 生产流程、提示词方法论/模板、ComfyUI 操作、资产管理、长视频、QC、Skill 演进 |
| `skills/.../scripts/init-project.sh` | 项目骨架生成脚本 |
| `skills/.../scripts/make-video.sh` | 一句话文生视频快速路径脚本（自愈） |
| `skills/.../scripts/run-workflow.py` | 通用 API 工作流提交 + 轮询，run 记录到 `<项目>/runs/` |
| `skills/.../scripts/workflow-doctor.py` | 提交前检查 workflow 格式、节点和模型/枚举资源 |
| `skills/.../assets/` | 随独立 Skill 分发的快速路径 workflow 与项目模板 |
| `assets/workflow_api_mzsj_video_text.json` | 当前文生视频快速路径模板 |
| `assets/workflow_api_mzsj_video.json` | 旧三段式兼容模板；当前 HTTPS 图片网关不接受其本地 IMAGE/data URL |
| `assets/project-template/` | 插件根中的项目模板镜像 |
| `examples/workflows/` | 精选 API 格式参考库；真实运行前必须体检节点、模型和素材 |
| `assets/comfyui-nodes/` | 两个自定义节点包源码 + `config.json.example`（不含真实 key） |
| `.qoder-plugin/plugin.json` | Qoder 插件 manifest |
| `CONNECTORS.md` | 需要配置哪些 API key、放在哪里 |

## 安装方式

- **Qoder**：整个目录作为插件安装（`.qoder-plugin/plugin.json`）
- **其他 agent 平台**（Claude Code / Cursor / Codex 等）：把 `skills/ai-video-studio/` 复制到平台 skills 目录（SKILL.md 开放格式）
- **只用 ComfyUI**：把 `assets/comfyui-nodes/` 两个节点包复制到 `custom_nodes/`，配好 key 即可

## 已知限制

- `make-video.sh` 的自动拉起/自动打开按 macOS 实现（`open` 与默认安装路径）；一键路径的 Linux 支持在路线图中
- 默认三段式模板只连接自动生成的首帧；打包视频节点另有尾帧和单参考图输入，但需要自行连接 IMAGE 上游并实测服务兼容性。视频/音频多模态参考和精准编辑需要其他节点或 workflow
- 生成发生在第三方 API 平台，价格与条款以其官方为准；本包只提供技术集成

## 出处

- 技能与节点在本机 Mac（ComfyUI v0.30.2 / Comfy Desktop 1.0.37）开发并端到端验证
- Prompt 方法论提炼自官方手册与官方 app 内置知识体系；原文版权归原厂商，不随仓库分发
- Logo 为本地生成的 SVG

## 生态推荐

agent 工具的真正价值在于拥有一定量现成、高质量的 workflow 与 skill：

- **Workflow**：见 `examples/workflows/` ——精选 16 个 API 格式参考工作流；收录不代表本机可运行，来源 [Lesilva/comfyui-workflows](https://github.com/Lesilva/comfyui-workflows)
- **Skill**：SKILL.md 开放标准已被 Claude Code / Codex / Gemini CLI / Cursor / Qoder 等 20+ 平台支持。推荐入口：[VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills)（1000+ 精选）、[awesome-claude-code-skills](https://github.com/helloianneo/awesome-claude-code-skills)（按场景精选）

## License

MIT（见 [LICENSE](LICENSE)）。上游 API 平台的费率与条款以各官方为准。
