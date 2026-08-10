# ComfyUI 工作流

何时加载：任何一次生成执行前、需要改工作流结构、单步执行、批量提交或排查执行故障时加载本篇。

## 一、定位

ComfyUI 是本技能的**操作面/执行面/技术工作流画布**：

- 节点承载能力：自定义节点实现提示词增强、首帧生图、视频生成。
- workflow JSON 承载结构：节点、连线、参数一起序列化，可脚本化提交。
- API 承载执行：提交与轮询都走本地 HTTP 接口。

服务地址：`http://127.0.0.1:8188`（本机 ComfyUI）。

## 二、能力边界

默认打包节点（快速路径）能力：

| 能力 | 节点 | 说明 |
|---|---|---|
| 提示词增强 | DeepSeekPromptEnhance | 用 LLM 把一句话扩成 H3 规范提示词 |
| 首帧生图 | HuoshenImageGenerate | 生成首帧图片（默认 1536x1024） |
| 文生/图生视频 | MzsjVideoGenerate | 文生视频；当前网关用 HTTPS 首帧、尾帧或参考图 URL |

默认打包节点未暴露（不是整个 Studio 不支持）：

- 素材上传
- 视频/音频多模态参考与多张参考图
- 视频/音频精准编辑（替换、局部修改、背景替换、台词替换等）
- 单次生成长视频

说明：当前 `/v1/videos` 网关要求 HTTPS 图片地址，使用 `first_frame_url`、`last_frame_url`、
`reference_image_urls`；本地 IMAGE/data URL 仅供 `api_mode=legacy` 的旧网关。公开临时图片前
先确认授权，并对首尾帧路径做一次小任务验证后再批量使用。

Studio 层：本机 ComfyUI 可加载任意已安装节点与工作流；首尾帧、参考素材、
精准编辑等可由其他 Comfy workflow 或扩展节点实现，本 Skill 不限制实例能力。
提交前用 `object_info` 确认实际加载的节点，不要把默认打包节点边界扩大成产品边界。

上游 MiniMax H3 模型宣称具备多模态参考与精准编辑能力，但默认打包节点未实现，
只能作为未来能力方向或提示词创作参考，绝不能写成默认打包节点支持。

## 三、工作流形态

两种格式分工：

| 形态 | 用途 | 提交方式 |
|---|---|---|
| API 格式 JSON | 脚本化、批量、agent 自动化 | `POST /prompt` |
| UI 画布格式 | 人工实验、调结构、看中间结果 | ComfyUI UI 加载 |

本技能自带文生快速模板 `assets/workflow_api_mzsj_video_text.json`（提示词导演 → 文生视频）。
旧 `workflow_api_mzsj_video.json` 保留作兼容参考，但其本地 IMAGE/data URL 路径不适用于当前网关。

`examples/workflows/` 是精选 API 格式工作流库，四类用途：

| 分类 | 用途 | 示例 |
|---|---|---|
| video/ | 文生视频、首尾帧、动作迁移、MotionLoRA | Wan 系列、VACE |
| first-frame/ | FLUX、万相、qwen 图像迁移等生图 | 文生图+ControlNet、图生图 |
| upscale/ | Kontext 等放大修复 | 无损放大、高清还原 |
| product/ | 人物一致性、换衣、产品打光/背景 | 换姿势、一键换衣、电商打光 |

这些是可移植参考，不代表本机已装好依赖。使用前先运行 `scripts/workflow-doctor.py`，再按
`examples/workflows/README.md` 准备缺失节点、模型和输入素材。

## 四、执行方式优先级

### 0. 运行前体检：workflow-doctor.py

```bash
python3 scripts/workflow-doctor.py <workflow.json>
```

退出码：`0` 结构/实例检查通过；`1` JSON 结构错误；`2` ComfyUI 不可达；`3` 缺节点或模型/枚举资源。
`--offline` 只检查 API JSON 结构。体检通过仍不等于显存、输入素材和外部 API 已验证。

### 1. 任意 API 工作流：run-workflow.py

正式项目优先使用通用 runner：它校验节点字段、提交、轮询，并把真实执行记录写入项目。

```bash
python3 scripts/run-workflow.py \
  assets/workflow_api_mzsj_video.json \
  --project <项目目录> \
  --set '1.inputs.prompt="雨夜霓虹街道"' \
  --set '3.inputs.duration=5' \
  --dry-run
```

`--set` 的值必须是 JSON；字符串需要双引号。先保留 `--dry-run` 检查，确认后去掉。
脚本把实际提交的 workflow、history 响应、状态与产物清单保存到
`<项目目录>/runs/<run-name>/`，不依赖共享输出目录前后差集。

### 2. 一句话出片：make-video.sh

```bash
bash scripts/make-video.sh "雨夜霓虹街道，赛博朋克" --duration 5 --resolution 720p
```

流程：健康检查 → 注入参数 → 文生视频提交 → 轮询 → 打开产物。

参数：

| 参数 | 说明 |
|---|---|
| `--duration` | 时长（秒），上游约束 4–15 |
| `--resolution` | `720p` / `1080p` 等 |
| `--size` | 首帧尺寸，默认 `1536x1024` |
| `--no-open` | 不自动打开产物 |
| `--dry-run` | 只输出注入后的 workflow JSON；不检查/拉起 ComfyUI，不提交 |

退出码：`0` 成功；`2` 拉起 ComfyUI 失败；`3` 执行错误；`4` 超时。真实提交时服务未启动会自动拉起，日志在 `~/Library/Logs/comfyui-headless.log`。需要指定项目目录、修改任意节点字段或保留 run 记录时使用 `run-workflow.py`。

### 3. 改结构/单步执行：直接 POST /prompt

最小步骤：
1. 编辑 API JSON 中节点的 `inputs`（改提示词、时长、分辨率）。
2. `POST /prompt` 提交，拿 `prompt_id`。
3. 轮询 `GET /history/<prompt_id>` 直到 `completed` 或 `error`。
4. 出错读 `status.messages` 里的 `execution_error`（`node_type` + `exception_message`）。

```bash
curl -s http://127.0.0.1:8188/prompt -H "Content-Type: application/json" -d @workflow.json
# 响应示例：{"prompt_id": "xxxx"}
curl -s http://127.0.0.1:8188/history/<prompt_id>
```

### 4. comfy run CLI

适合在命令行做受控单次运行：

```bash
comfy --workspace <项目路径> run --workflow <api.json> --host 127.0.0.1 --port 8188 --timeout 600
```

### 5. 人工实验：ComfyUI UI 画布

需要调节点连线、看中间图、验证新 workflow 时，在 UI 加载 JSON 后手动执行；跑通后再导出 API 格式复用。

## 五、API 操作细节

- 提交：`POST /prompt`，body 为 `{"prompt": <workflow JSON>}`，返回 `prompt_id`。
- 轮询状态机：`pending/running → completed`；异常时 `status_str: error`。
- 错误解析：`history[<prompt_id>].status.messages` 中找 `execution_error`，读节点类型与异常信息，修复对应节点后再提交。
- 超时：`run-workflow.py` 与 `comfy run` 用 `--timeout` 控制；make-video.sh 内置 900 秒上限。
- dry-run：先跑 `--dry-run` 检查注入后的 JSON，再真实提交，避免参数错误浪费调用。

## 六、健康检查与故障

健康检查命令：

```bash
curl -s -m 5 http://127.0.0.1:8188/object_info | grep -o "MzsjVideoGenerate"
```

故障排查：

| 现象 | 处理 |
|---|---|
| `object_info` 无节点 | 检查 custom_nodes 是否安装、config.json 是否配好 |
| 连接超时 | 确认本机 ComfyUI 已启动；脚本会自动拉起，看日志 |
| DNS 解析到 `198.18.x.x` | 代理（Clash 类）掉线，先恢复代理再重试，不要盲目重发 |
| 同一参数失败 ≥3 次 | 停手，改策略：检查节点/提示词/费用，而不是重复提交 |

## 七、批量与复用

批量纪律：
- 批量循环提交前先算成本：三段式快速路径每次 = 1 次提示词增强 + 1 次生图 + 1 次视频；其他 workflow 按实际节点计算。
- 同类资源一次生成完再进入下一步（先全部首帧，再全部视频），失败样本单独处理。
- 单条失败不盲目重试；记录失败的 `prompt_id` 与参数后再重试。

复用规则：
- 跑通的自定义 workflow 保存为可复用资产：命名 `作者-用途-版本.json`，在 `_meta` 注释输入输出，放回 `examples/workflows/` 对应分类。
- 放回前遵循 `examples/workflows/README.md` 的来源与许可说明。
- 只有验证跑通、注释清楚的 workflow 才入库。

## 八、安全与成本

- `config.json` 含真实 key：不外传、不入库；仓库只保留 `config.json.example`。
- 文生快速路径固定 1 次增强 + 1 次视频；旧三段式另含 1 次生图。其他 workflow 按实际节点计费。
- 按“方向 + shot 表 + 总预算”一次授权；范围内不逐镜头重复确认。

## 九、自查清单

- [ ] 服务地址 `127.0.0.1:8188` 可达，`object_info` 含所需节点
- [ ] 已确认默认模板与所选 workflow 的能力边界；首尾帧/单参考图路径已做小任务验证
- [ ] 用模板或 examples 工作流，参数在合法范围（时长 4–15、分辨率/尺寸匹配）
- [ ] 先 `--dry-run` 或检查 JSON，再真实提交
- [ ] 提交后记录 `prompt_id`，轮询到 completed/error
- [ ] 错误按 `execution_error` 修复；同一参数失败 ≥3 次已停手
- [ ] 批量前确认成本；跑通的自定义 workflow 已注释并入库

## 交叉引用

- references/prompt-craft.md：提示词怎么写、踩坑表
- references/prompt-templates.md：可直接套用的完整模板
- references/quality-control.md：提交前与结果验收
- references/asset-management.md：workflow 作为可复用资产的命名与入库
- references/production-workflow.md：端到端生产流程
- references/long-video.md：长片拆段策略（当前单次生成不支持长视频）
