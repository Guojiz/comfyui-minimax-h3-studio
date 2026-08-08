---
name: ai-video-studio
version: 1.2.0
description: >
  AI 视频创作全流程技能。适用场景：用户要求生成视频、制作短片/广告/种草视频、
  生成视频首帧图、增强视频提示词、运行 ComfyUI 工作流出片。
  触发表述：生成视频、做一条片子、出个视频、文生视频、图生视频、跑工作流、
  video generation、make a clip。
  不适用：纯文生图（直接用生图 API）、剪辑成片（引导用户用剪映/DaVinci）、
  本地模型推理（本环境为纯 API 路线）。
---

# AI Video Studio — 纯 API 视频创作技能

本技能驱动用户本机的 ComfyUI（localhost:8188）三段式纯 API 流水线：
DeepSeek v4-flash 提示词增强 → 火神 gpt-image-2 生图 → mzsjai MiniMax H3 视频生成。
不加载任何本地模型，全部走用户自有 API key。

## 环境事实（已验证）

- ComfyUI 服务：http://127.0.0.1:8188（由 Comfy Desktop 或手动启动）
- 自定义节点包：
  - `comfyui-mzsj-api`：DeepSeekPromptEnhance / MzsjVideoGenerate
  - `comfyui-huoshen-image`：HuoshenImageGenerate
- 工作流文件（UI 格式）：`~/ComfyUI-Installs/ComfyUI/ComfyUI/user/default/workflows/workflow_api_mzsj_video.json`
- 工作流文件（API 格式）：工作区 `mzsj-node/workflow_api_mzsj_video.json`
- 产物目录：`~/ComfyUI-Installs/ComfyUI/ComfyUI/output/`（图片）与 `output/mzsj/`（视频）
- API key 配置：各节点目录下 `config.json`（勿外传、勿写入 git）

## 执行方式（按优先级）

1. **首选：改 prompt 后提交 API 格式工作流**
   - 编辑 API 格式 JSON 中节点 "1" 的 `prompt` 为用户诉求
   - POST http://127.0.0.1:8188/prompt，body `{"prompt": <workflow>}`
   - 轮询 GET /history/<prompt_id> 直到 status 终态；错误读 `execution_error` 消息
   - 完成后 `open` 产物文件给用户预览
2. **备选：comfy run**（`comfy --workspace <path> run --workflow <api.json> --host 127.0.0.1 --port 8188 --timeout 600`）
3. **备选：一键脚本**：`scripts/make-video.sh`（见下方工具脚本节）
4. **单步能力**：只生图 → 直接 POST /prompt 仅含节点 1+2；只要提示词增强 → 仅节点 1

## 工具脚本

**scripts/make-video.sh**：一句话出片（健康检查 → 参数注入 → 提交 → 轮询 → 自动打开产物）。**执行**它，不要读取改写：

```bash
bash .qoder/skills/ai-video-studio/scripts/make-video.sh "雨夜霓虹街道，赛博朋克" \
  [--duration 5] [--resolution 720p] [--size 1536x1024] [--no-open] [--dry-run]
```

- 退出码：0 成功；2 自动拉起失败；3 执行错误（已打印节点与异常）；4 超时
- 服务未启动时脚本会自动后台拉起 ComfyUI 并等待就绪（无需人工打开桌面端），日志在 ~/Library/Logs/comfyui-headless.log
- 用户只说"生成视频"且参数齐全时优先用此脚本；需要改工作流结构时走方式 1

## 提示词工程（生成前必须应用）

详细方法论见 `references/prompt-craft.md`（已融合官方《H3 使用手册》）。
官方公式：`完整提示词 = 参考素材说明 + 核心创意 + 画面过程说明`。核心铁律：

1. **素材引用**：有参考素材时用 `@图片N/@视频N` 编号并逐个写清用途（人物参考/动作参考/运镜参考/首帧尾帧…）；无素材时跳过该段
2. **核心创意四要素**：主体（具体可见名词）+ 地点 + 事件 + 题材风格；默认会切镜，一镜到底需明说
3. **画面过程按 shot 分段**：每 shot 写景别+内容+运镜+动作+台词+音效；台词长度与 shot 时长对齐（中文 3–4 字/秒）
4. **正向描述**：禁止负向词（"不要 X"会激活 X），改写为目标可见状态；少比喻、写看得见的画面
5. **声音控制**：不要配乐必须显式写 `非叙事性音乐：N/A`
6. **文字必给原文**：画面要出现的具体文字/Logo/标语写出原文；乱码时改传图片参考
7. **每条 prompt 末尾锁 Medium**：防介质漂移（如 `Medium: photoreal live-action footage`）
8. **提交前过官方踩坑表**（prompt-craft.md 第三节）逐条自检

## 服务健康检查（操作前）

- `curl -s http://127.0.0.1:8188/object_info | grep MzsjVideoGenerate` 无结果 → 服务未启动或节点未加载，提示用户在 Comfy Desktop 重启实例
- mzsjai.com 超时且 DNS 为 198.18.x.x → 用户代理软件掉线，提醒开代理，勿反复重试
- 同一参数失败 ≥3 次必须停下换策略或询问用户（anti-loop 纪律）

## 成本纪律

每次完整流水线消耗 1 次 DeepSeek + 1 次生图 + 1 次视频额度。
调试节点逻辑用最小任务；用户未确认前不重复提交相同任务。
