# AI Video Studio

一个让现有 Agent 更好地制作视频的开放 Skill/Plugin。它不实现新的 App、CLI 产品、Agent Runtime
或通用编排器：Codex 等宿主 Agent 已经负责理解客户、调用工具和交付作品。

## 核心定位

- **Agent**：操作主体，理解目标、选择下一步、检查和交付；
- **Skill**：视频制作方法、判断标准和纠错经验；
- **资产**：输入、可见产物、来源、版本和客户决定；
- **ComfyUI**：workflow-as-code 操作面、执行面和技术调试器。

客户通过对话描述想要什么。Agent 默认逐步产生最有判断价值的可见结果，例如效果图、关键帧或一个
测试镜头；客户想看技术细节时再打开 ComfyUI。workflow 是工具，不是产品菜单。

## 包含内容

```text
skills/ai-video-studio/
  SKILL.md                  平台中立的生产方法
  references/              按需加载的制作、资产、QC、ComfyUI 和宿主说明
  scripts/init-project.sh  创建轻量项目事实
  scripts/run-workflow.py  通用 API workflow 提交与客观 run 留痕
  scripts/workflow-doctor.py 运行前节点/资源体检
  mcp/                     Codex 到 ComfyUI HTTP API 的可选薄桥接器
  assets/                   正式模板、部署配置和项目模板
assets/comfyui-nodes/       ComfyUI 自定义节点
examples/workflows/         第三方研究目录说明，不分发许可不明 JSON
```

## 使用

安装后直接对 Agent 说：

> 使用 `$ai-video-studio`，根据这些素材先做一个能判断风格的可见结果，再听我的意见继续。

持续项目可由 Agent 初始化：

```bash
bash skills/ai-video-studio/scripts/init-project.sh ./my-video --name "My Video" --git
```

只创建 `project.md`、`assets.md`、`decisions.md`、`workflows/` 和 `.gitignore`；其他目录用到时再建。

Agent 内部执行任意 ComfyUI API workflow：

```bash
python3 skills/ai-video-studio/scripts/workflow-doctor.py workflow.json
python3 skills/ai-video-studio/scripts/run-workflow.py workflow.json \
  --project ./my-video --set '1.inputs.prompt="雨夜街道"' --dry-run
```

去掉 `--dry-run` 才提交。命令是内部确定性工具，不是客户入口。

Codex 可通过 `skills/ai-video-studio/mcp/comfyui_mcp.py` 把同一套 registry、doctor 和 runner
暴露为 STDIO MCP 工具。安装与安全配置见 `skills/ai-video-studio/mcp/README.md`；MCP 不替代 Agent，
实际生成工具保持写操作审批。

## 配置与能力

项目明确区分模型能力、实例部署和外部服务契约。正式 workflow 配 manifest；真实 API Key
只保存在本机 `config.json`，仓库仅发布示例。

**本 Skill 只绑定 ComfyUI，不内置、不默认任何模型或 API 服务。** 公开仓库不随包分发外部服务
配置、服务自定义节点或第三方 workflow 模板。使用任何外部服务（API 节点、远程 GPU 平台、
第三方 API）都必须由客户显式选择并授权：Agent 先问清用哪个服务、是否已有配置、是否接受费用，
不得默认假设任何服务。
legacy data URL 模式必须显式配置，不能混为同一契约。

选择 workflow 时以当前 `object_info`、部署配置、许可和验证状态为准。外部 JSON 只有在许可
明确、依赖清楚并达到声明验证级别后才能进入公开正式库。

## 验证范围

当前已验证：Skill 结构、Shell/Python/JSON、项目初始化、runner dry-run/模拟路径、workflow doctor，
以及当前文生模板在本机 ComfyUI 的节点/枚举资源体检。`/v1/videos` 适配按用户提供的当前契约完成
payload/download 模拟验证，但没有通过本次正式模板执行新的付费生成，因此其 manifest 标记为
`dry-run`，不冒充端到端 `live-tested`。

## 安装

- Codex：复制完整 `skills/ai-video-studio/` 到可发现的 Skills 目录；
- Qoder：可安装整个目录的 `.qoder-plugin/plugin.json`，或复制 Skill；
- 其他支持 `SKILL.md` 的 Agent：复制 Skill，并按自身工具映射文件、终端和多模态能力。

Qoder manifest 仅用于兼容，不代表项目内实现了独立 Agent。
