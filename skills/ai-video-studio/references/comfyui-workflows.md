# ComfyUI workflow-as-code

> 选择、修改、体检、执行、复用或调试 ComfyUI workflow 时读取。

## 定位

ComfyUI 是必要的技术生产环境：节点连接模型与工具，JSON 保存可复现执行图，UI 用于查看输入输出、
调整节点和人工接管。Agent 默认把 workflow 当代码操作；客户想看、接管或调试时再打开 UI。

ComfyUI 不决定创意流程，也不是唯一执行工具。Skill 规定怎么做好视频，Agent 决定当前要解决什么，
资产记录输入输出和采用关系。

## 三层配置

不要混淆：

- **模型能力**：模型理论上能做什么；
- **provider**：提交、轮询、下载和认证契约；
- **profile**：当前实例的默认模型、尺寸、时长、限额和实测观察。

正式模板的 manifest 必须引用 provider/profile。真实 key 留在本机 `config.json`，不写进 manifest、
workflow、对话或 Git。当前打包示例见：

- `assets/providers/mzsj-videos.json`
- `assets/profiles/mzsj-current.example.json`
- `assets/workflow_api_mzsj_video_text.manifest.json`

当前 `/v1/videos` provider 接受 HTTPS 图片 URL；本地 IMAGE/data URL 只属于明确配置的 legacy
契约。公开临时图片前必须获得授权。当前 profile 的限制只在影响本次需求时告诉客户。

## Workflow 库

每个可正式使用的 workflow 至少声明：

```json
{
  "id": "mzsj-video-text",
  "purpose": "text to video",
  "workflow": "workflow_api_mzsj_video_text.json",
  "provider": "mzsj-videos",
  "profile": "mzsj-current",
  "inputs": ["prompt", "seconds", "size"],
  "outputs": ["video"],
  "required_nodes": ["DeepSeekPromptEnhance", "MzsjVideoGenerate"],
  "verified": {"status": "live-tested", "date": "2026-08-08"},
  "source": "project",
  "license": "MIT"
}
```

验证状态只能是 `untested`、`dry-run` 或 `live-tested`，并保留日期和证据范围。结构通过不等于
本机节点、模型、显存、输入素材和外部服务均可用。

库分工：

- **正式库**：许可明确、依赖清楚并达到声明验证级别，可随插件分发；
- **本地研究库**：许可或验证不明，只供 Agent 阅读和改造，不随插件发布；
- **项目 `workflows/`**：为本次任务复制、修改并实际执行的版本。

Agent 默认根据客户指定、当前已配置能力、输入匹配、实测成功率、成本、耗时和 profile 限制选择；
客户可以要求列出、打开、替换或指定 workflow。

## 运行协议

### 1. 体检

```bash
python3 scripts/workflow-doctor.py <workflow.json>
```

退出码：`0` 结构/实例检查通过；`1` JSON 错误；`2` ComfyUI 不可达；`3` 缺节点或枚举资源。
`--offline` 只检查 API JSON 结构。体检通过不是付费端到端证明。

执行实例必须是显式决策：MCP 已配置实例时优先用 MCP；MCP 不可用时必须显式传入同一
锁定实例地址。正式提交必须显式指定 `--server` 或 `COMFY_SERVER`，不会静默回退
`127.0.0.1:8188`。已有同名 run 目录受保护，重复 `--run-name` 会报错而不是覆盖旧记录。

### 2. 复制到项目并 dry-run

先把正式模板复制到项目 `workflows/`，再按项目修改。不要直接破坏公共模板。

```bash
python3 scripts/run-workflow.py <project>/workflows/example.json \
  --project <project> \
  --set '节点ID.inputs.字段=JSON值' \
  --dry-run
```

`--set` 的值必须是 JSON；字符串需要双引号。dry-run 不启动服务、不提交、不写 run。确认后去掉
`--dry-run`，脚本通过 `/prompt` 提交、轮询 `/history/<prompt_id>`，并保存实际 workflow、history、
run 状态和产物清单。镜头标识和版本需要时使用 `--shot`、`--iteration`，不是所有任务必填。

### 3. 查看或人工接管

需要调连接、看中间结果或让客户接管时，在 ComfyUI UI 加载项目 JSON。跑通后保存回项目，不要让
UI 中未保存的状态成为唯一事实。

## 失败与安全

| 现象 | 处理 |
| --- | --- |
| `object_info` 缺节点 | 换已安装 workflow 或补依赖；不要在付费窗口盲试 |
| provider 字段错误 | 修 provider 适配，不改通用 Skill |
| profile 限制不匹配 | 告诉客户实际影响，选择降规格、换 provider 或等待 |
| DNS 为 `198.18.x.x` 且超时 | 先恢复代理或路由，不重复提交 |
| 同一策略连续失败 3 次 | 停止，换方法或请求客户决定 |
| 找不到产物 | 以 history/run 记录为准，不用共享目录“最新文件”猜测 |

真实配置只报告 `SET/UNSET`；不要读取或显示密钥。外部上传、肖像和版权素材在公开前确认授权。

## 复用纪律

跑通后把项目 workflow、manifest、provider/profile 引用、验证证据和来源登记到 `assets.md`。只有
许可明确且达到所声明验证级别的模板才能晋升正式库。不要因为文件名写“已跑通”就声称本机验证。
