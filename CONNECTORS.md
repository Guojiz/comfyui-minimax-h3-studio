# 连接器说明（Connectors）

本插件不含任何真实凭据。使用前需要三组自有 API key，填入对应节点包的 `config.json`
（可复制同目录 `config.json.example` 改名 `config.json` 后填写）。

| # | 用途 | 配置位置（key 字段） | 获取 key 的平台 | 技术参数 |
|---|---|---|---|---|
| 1 | 提示词增强 | `custom_nodes/comfyui-mzsj-api/config.json` → `deepseek.api_key` | platform.deepseek.com | POST `/v1/chat/completions`（OpenAI 兼容）；模型 `deepseek-v4-flash` |
| 2 | 视频生成 | `custom_nodes/comfyui-mzsj-api/config.json` → `mzsj.api_key` | mzsjai.com | POST `/v1/video/generations` 提交 + GET 轮询；响应在 `data` 包装内、状态为大写 `SUCCESS`、视频地址为 `result_url`；模型 `minimax/minimax-h3-fl2va`（文生/首帧）、`minimax/minimax-h3-ref2va`（参考） |
| 3 | 首帧生图（1536x1024 默认） | `custom_nodes/comfyui-huoshen-image/config.json` → `huoshen.api_key` | huoshenai.net | 必须用 `/v1/images/generations`（chat/completions 端点不支持生图模型） |

> 说明：上表中的平台名只用于获取 key，模型 ID 是 API 请求的必要参数；除此之外本仓库
> 不绑定任何品牌。三组 key 均由用户自备，本插件不内置、不存储任何凭据。

## 网络注意

上游平台域名可能需要代理。若 DNS 解析到 `198.18.x.x`（fake-IP）且连接超时，
说明代理软件（Clash 类）未运行，先恢复代理而不是重试。
