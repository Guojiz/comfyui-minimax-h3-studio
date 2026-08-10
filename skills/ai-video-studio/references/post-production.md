# 后期制作

何时读取：拿到候选片段之后、需要剪辑/抽帧/技术 QC、正式交付客户之前。

## 定位与原则

后期是**确定性工作**：字幕、响度、转场、封装、裁剪、拼接等能用 FFmpeg/剪辑工具可靠完成的问题，
一律用确定性工具解决，不重新调用生成模型、不浪费生成额度。后期流程按需触发，不是固定流水线：
先做成本最低、最能让客户判断方向的那一步，再根据结果继续。

**Agent 是剪辑决策者，工具是执行面。** Agent（与客户）决定哪些片段进入粗剪、接缝是否需要补镜、
节奏是否成立、哪些版本 approved、交付哪些文件；`rough-cut.py`、`deliver.py` 只按命令执行并保留
版本与来源事实。工具不会替 Agent 判断好坏，Agent 也不要把剪辑决定丢给脚本参数。

硬性约束：

- 绝不覆盖已有输出；粗剪自动生成新版本目录（`v01`、`v02` …）。
- 交付绝不移动原始文件，只复制或硬链接；只处理清单中列出的文件。
- 依赖缺失时报错并给出可操作指引，**绝不自动安装** ffmpeg，也绝不联网下载。
- `--json` 时 stdout 只输出一个结构化 JSON 结果对象，人类可读信息走 stderr。

## 工具与依赖

Phase 4 提供三个确定性脚本（位于 `scripts/`，均为新增文件，未改动任何既有脚本）：

| 脚本 | 用途 | 退出码 |
| --- | --- | --- |
| `scripts/media-probe.py` | 定位 ffprobe/ffmpeg 并探测时长、宽高、帧率、音轨数 | 0 成功；1 用法；2 缺依赖；3 文件缺失/不可读 |
| `scripts/rough-cut.py` | 统一目标规格后规范化并拼接 | 0 成功；1 用法/规格不一致；2 缺依赖；3 输入缺失/不可读；4 ffmpeg 失败 |
| `scripts/deliver.py` | approved-only 交付，生成 delivery.json | 0 成功；1 清单/用法；3 清单文件缺失/不可读/为空；4 写入/校验失败 |

工具定位顺序（两个脚本一致）：`--ffmpeg-dir` → `FFMPEG_DIR` 环境变量 → `PATH` → 常见安装目录。
找不到时返回退出码 2，错误信息包含修复指引（例如 `brew install ffmpeg`，或设置 `FFMPEG_DIR`
指向包含 `ffmpeg`/`ffprobe` 的目录）。

示例：

```bash
python3 scripts/media-probe.py shot-01.mp4 shot-02.mp4 --json
python3 scripts/rough-cut.py shot-01.mp4 shot-02.mp4 --project <项目> --json --dry-run
python3 scripts/deliver.py <项目>/delivery-manifest.json --project <项目> --json
```

## 流程总览

```text
edit plan / EDL
→ 抽帧与技术 QC（media-probe + 静帧检查）
→ 粗剪（rough-cut，先 dry-run 看计划）
→ 规范化（统一 width/height/fps、编码与音频参数）
→ 字幕 / 音频 / 转场（按需）
→ approved-only 交付（deliver + delivery.json）
```

每一环节都保留来源关系，成片可回溯到片段、参考资产、workflow 与客户决定。

## Edit plan / EDL

有多个镜头或需要节奏评审时，先写简短 edit plan：镜头 ID、来源资产（workflow/run 关系）、
入点/出点（或整段）、顺序、转场、字幕/音频备注。EDL 只要字段稳定即可，推荐 JSON，放项目目录，
并登记到 `assets.md`。edit plan 是工作文档，不是交付物；只有客户确认的成片组合才是交付依据。

## 抽帧与技术 QC

拿到候选后先做技术 QC，再谈内容。用 `media-probe.py` 批量确认时长、分辨率、帧率、音轨数；
需要看画面时抽静帧（帧抽取命令属于标准 FFmpeg 用法，本机未做真实执行验证，见“验证状态”）：

```bash
ffmpeg -ss 00:00:01 -i shot-01.mp4 -frames:v 1 -q:v 2 frame-01.png
```

对照 `references/quality-control.md`：时长与请求一致、分辨率/画幅正确、24 FPS、文件完整非空、
画面无黑帧/形变/乱码、音轨存在且音量正常、无白名单外声音。技术项不过就返工对应片段，
不进入粗剪。

## 粗剪

`rough-cut.py` 按输入顺序拼接，行为确定性：

- 显式给出 `--width/--height/--fps` 时以此为准；否则要求所有输入规格完全一致。
- 规格不一致且未给显式目标时直接报错，JSON 错误里列出每个输入的实际规格，绝不静默损坏。
- 音频策略 `--audio keep`（默认，保留各输入音轨并统一转码，无音轨输入补静音）或 `drop`（无音轨）。
- 输出写入 `<project>/rough-cut/<output-name>/vNN/`，`vNN` 自动递增，已有版本绝不覆盖；
  同目录内保存 `version.json`（输入清单 + 目标规格 + 输出）与规范化后的 `segments/`，便于回溯。
- 失败时清理本次未完成的版本目录，不留半成品版本。
- 正式执行前建议先 `--dry-run`：只校验并输出计划，不写任何文件。

规范化参数固定：`scale` 等比缩放后 `pad` 到目标画布、`fps` 对齐、`libx264`/`yuv420p`、
音频 `aac 192k 48kHz 立体声`，最后 concat demuxer `-c copy` 拼接。目标宽高必须是正偶数。

## 规范化

规范化的目标是让所有片段共享同一技术基线，后续拼接/交付不再出现流参数冲突：

- 视频：目标 `width × height`、目标 `fps`、`h264`、`yuv420p`。
- 音频：`aac`、48 kHz、立体声；无音轨片段按策略补静音或丢弃。
- 内容：等比缩放 + 黑边填充，不做拉伸变形。

`rough-cut.py` 的规范化段即按上述参数执行；单独需要规范化单文件时，按同样的参数手写 FFmpeg
命令（本机未验证，见“验证状态”）。

## 字幕、音频与转场

这些环节按需触发，优先确定性工具：

- 字幕：以 SRT/ASS 文件为源，成品字幕烧录或外挂均由 FFmpeg 字幕滤镜/容器支持完成；
  字幕原文与时间轴属于文案工作，按 `quality-control.md` 的台词预算核对。
- 音频：对白/BGM/环境音分轨、响度统一（例如 EBU R128 `loudnorm` 目标）属于确定性混音；
  不要在混音阶段重新调用生成模型。
- 转场：简单转场（淡入淡出、交叉溶解等）用 FFmpeg `xfade` 或剪辑工具；复杂镜头关系回到生成阶段补镜头。

以上命令属于标准工具用法，当前机器未做真实执行验证（见“验证状态”）；正式使用前先在样片上验证。

## Approved-only 交付

只有客户确认（或正式下游采用）的资产才允许交付。`approved` 语义由 Agent 依据客户反馈更新
（见 `references/asset-management.md`），脚本本身不判断资产是否 approved——交付清单由 Agent
根据已 approved 资产编写，脚本只负责确定性的存在性、完整性校验与复制。

交付清单 JSON 示例：

```json
{
  "schema_version": 1,
  "run": "run-20260810-120000-abc123",
  "workflow": "mzsj-video",
  "instance": "mzsj-remote",
  "decision": "2026-08-10 客户确认交付版本",
  "files": [
    {"path": "shots/final-rough-cut/final.mp4", "role": "video"},
    {"path": "subtitles/zh.srt", "role": "subtitle", "language": "zh"}
  ]
}
```

`deliver.py` 行为：

- 逐个校验存在、可读、非空，计算 sha256；任一文件不过，整体失败（退出码 3），不开始复制。
- 复制（默认）或硬链接（`--link`）到 `<project>/dist/`（或 `--dist` 指定目录）；
  绝不移动原始文件，绝不复制清单外文件。
- 生成 `delivery.json`：每文件 `path/role/sha256/source/size`，
  并把清单顶层字段（`run`、`workflow`、`instance`、`decision` 等）透传；
  条目级字段覆盖顶层。
- 已有 `delivery.json` 的 dist 目录受保护，报错并要求 `--dist` 新目录，绝不覆盖旧交付。
- 复制后再次校验目标 sha256 与源一致；失败即退出码 4。
- 相对路径以清单文件所在目录为基准解析；建议先 `--dry-run` 看校验与计划。

## 验证状态

当前机器的真实情况与能力验证状态如下，能力声明以实际证据为准：

| 能力 | 验证状态 |
| --- | --- |
| `media-probe.py` 工具定位与 JSON 解析 | 单元测试通过（mock subprocess）；真实 ffprobe 执行未在本机验证 |
| `rough-cut.py` 版本化与命令行生成 | 单元测试通过（mock subprocess）；真实 ffmpeg 规范化/拼接未在本机验证 |
| `deliver.py` 复制/校验/透传 | 单元测试通过（真实文件 IO，无 ffmpeg 依赖） |
| FFmpeg 字幕/音频/转场命令 | 标准用法记录，本机未执行验证 |
| 长视频多段生产 | `long-video: design documented, execution unverified` |

`long-video: design documented, execution unverified`：长视频多段生成、连续性接缝修复与
最终合成目前只有设计与流程文档，没有真实 fixture 验证证据。除非以后在装有 ffmpeg 的机器上
用真实样片完成端到端验证并留下证据，否则不得把该能力描述为已验证。

## 与现有文档的关系

- `references/quality-control.md`：抽帧、技术 QC 与内容 QC 的具体检查项。
- `references/long-video.md`：多镜头/长视频的粗剪与最终合成设计。
- `references/asset-management.md`：`candidate`/`approved` 资产语义与来源登记。
- `references/rework.md`：局部返工与版本比较，后期脚本配合版本目录使用。
