# AI 视频工作室（ai-video-studio）

一个 Qoder 插件，把「一句话 → 成片」的纯 API 视频流水线封装成 Agent Skill：
**DeepSeek 提示词增强 → gpt-image-2 首帧生图 → MiniMax H3 视频生成**。
全部走用户自有 API key，不加载任何本地模型（无 GPU 也能跑，Mac/轻薄本友好）。

> [English](README.md)

## 效果展示

首帧由 gpt-image-2 生成，再由 MiniMax H3 动效化（端到端约 4 分钟）：

![样例首帧](examples/sample-first-frame.png)

▶ 观看：[`examples/sample-video.mp4`](examples/sample-video.mp4)

> **与已有方案的差异**：社区现有 MiniMax H3 项目多为本地开源权重路线（需高端 GPU）
> 或仅做提示词构建；本项目是 **BYO API key 纯云端流水线 + Agent Skill 封装**，
> 并把官方《H3 使用手册》的提示词公式与踩坑表固化进了知识库。

## 三种用法

| 你是谁 | 怎么用 |
|---|---|
| Qoder 用户 | 整个目录作为插件安装（`.qoder-plugin/plugin.json`） |
| Claude Code / Cursor / Codex 等其他 agent 用户 | 把 `skills/ai-video-studio/` 拷到对应平台的 skills 目录（SKILL.md 开放标准） |
| 只用 ComfyUI | 把 `assets/comfyui-nodes/` 下两个节点包拷入 `custom_nodes/`，填 key 即用 |

## 包含内容

| 文件 | 说明 |
|---|---|
| `skills/ai-video-studio/SKILL.md` | 主技能：执行方式、提示词铁律、健康检查、成本纪律 |
| `skills/ai-video-studio/references/prompt-craft.md` | 视频 Prompt 工程手册（已融合官方《MiniMax H3 使用手册》三段公式与踩坑表） |
| `skills/ai-video-studio/scripts/make-video.sh` | 一句话出片脚本（健康检查→参数注入→提交→轮询→自动打开产物） |
| `assets/workflow_api_mzsj_video.json` | 三段式 API 格式工作流模板（脚本自带，自包含） |
| `assets/comfyui-nodes/` | 两个自定义节点包源码 + config.json.example（不含真实 key） |
| `CONNECTORS.md` | 需要配置的三组 API key 说明（本插件不内置任何凭据） |

## 前置条件（Setup）

1. **本机 ComfyUI**：服务监听 `http://127.0.0.1:8188`（Comfy Desktop 或 headless 均可）
2. **安装自定义节点**：把 `assets/comfyui-nodes/` 下两个目录复制到 ComfyUI 的 `custom_nodes/`：
   - `comfyui-mzsj-api`：`DeepSeekPromptEnhance` + `MzsjVideoGenerate`
   - `comfyui-huoshen-image`：`HuoshenImageGenerate`
3. **API key**：复制各节点包内 `config.json.example` 为 `config.json`，按 `CONNECTORS.md` 填入
4. **环境变量（可选）**：`COMFY_SERVER` / `COMFY_WORKFLOW_TPL` / `COMFY_PYTHON` / `COMFY_OUTPUT_DIR` 覆盖脚本默认值

## 出处与来源（Provenance）

- 技能与节点由作者在本地 Mac（ComfyUI v0.30.2 / Comfy Desktop 1.0.37）上开发并端到端验证
- Prompt 方法论来源：官方《MiniMax H3 模型 - 使用手册》《MiniMax Design - 新手指南》
  （飞书文档导出）+ MiniMax Design app 内置 agent-profiles 知识体系
- Logo：本地生成的 SVG（无第三方素材）

## 已知限制 / 省略内容

- mzsj 视频 API 单条约 220 秒，720p/5s；代理软件（Clash 类）掉线时 DNS 会返回
  198.18.x.x fake-IP 导致超时，属环境问题而非节点 bug
- 工作流的 UI 格式版本（画布用）未打包，分发场景只需 API 格式模板
- 源工程中的 `config.json`（含真实 key）一律不打包

## 验证

- 官方离线验证器：`validate_qoder_plugin.py <本目录>` 通过
- 脚本 dry-run 实测：健康检查、参数注入、模板加载均正常
- 服务自愈实测：停掉后端后脚本自动拉起并继续执行

## License

MIT（见 [LICENSE](LICENSE)）。API 服务（DeepSeek / mzsjai / huoshenai）的费率与条款以各官方为准。
