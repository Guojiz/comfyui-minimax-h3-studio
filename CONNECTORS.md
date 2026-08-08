# 连接器说明（Connectors）

本插件不含任何真实凭据。使用前需要三组自有 API key，填入对应节点包的 `config.json`
（可复制同目录 `config.json.example` 改名 `config.json` 后填写）。

## 1. DeepSeek（提示词增强）

- 用途：把一句话描述扩写为符合官方公式的视频提示词
- 获取：<https://platform.deepseek.com/>
- 配置位置：`custom_nodes/comfyui-mzsj-api/config.json` → `deepseek.api_key`
- 端点：`/v1/chat/completions`（OpenAI 兼容），模型 `deepseek-v4-flash`

## 2. mzsjai（MiniMax H3 视频生成）

- 用途：文生视频 / 图生视频（首帧）
- 配置位置：`custom_nodes/comfyui-mzsj-api/config.json` → `mzsj.api_key`
- 端点：POST `/v1/video/generations` 提交，GET 轮询（响应在 `data` 包装内，
  状态为大写 `SUCCESS`，视频地址为 `result_url`）
- 模型：`minimax/minimax-h3-fl2va`（文生/首帧）、`minimax/minimax-h3-ref2va`（参考）

## 3. huoshenai（gpt-image-2 首帧生图）

- 用途：生成视频首帧图（1536x1024 默认）
- 配置位置：`custom_nodes/comfyui-huoshen-image/config.json` → `huoshen.api_key`
- 端点：必须用 `/v1/images/generations`（chat/completions 端点不支持生图模型）

## 网络注意

mzsjai 与 huoshenai 域名可能需要代理。若 DNS 解析到 `198.18.x.x`（fake-IP）且连接超时，
说明代理软件（Clash 类）未运行，先恢复代理而不是重试。
