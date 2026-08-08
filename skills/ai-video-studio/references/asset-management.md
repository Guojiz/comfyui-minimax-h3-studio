# 资产管理

何时加载：准备或检索素材、整理项目文件、决定哪些文件入库、把已验证素材跨项目复用时加载本篇。

## 一、资产是什么

资产 = 可复用的素材，而不是一次性草稿。常见类型：

| 类型 | 示例 | 入库价值 |
|---|---|---|
| 角色 | 林晚-v1 参考图 | 高：跨镜头、跨项目锁脸 |
| 场景 | 竹林庭院氛围图 | 高：重复使用环境 |
| 风格包 | 胶片/赛博朋克风格参考 | 高：统一视觉 |
| 道具 | 产品瓶身图 | 高：品牌一致性 |
| 参考素材 | 调研收集的构图/光影图 | 中：看授权与体积 |
| 成片 | 已交付 mp4 | 中：归档而不是入库 |

来源可以是：本流水线生成产物（`huoshen_*.png`、`output/mzsj/*.mp4`）、用户提供的文件、调研收集物。

判定规则：会在第二次及以后使用才入库；一次性草稿放项目临时目录，不进资产目录。

## 二、本地目录与命名约定

建议目录（放在项目根，与插件 `assets/` 区分）：

```text
<项目>/
  characters/   # 角色
  scenes/       # 场景
  styles/       # 风格包
  props/        # 道具
  references/   # 调研/参考素材
  final/        # 成片
```

文件名模板：`类别-名称-版本-用途.ext`，示例：

```text
characters/林晚-v1-锁脸.png
characters/林晚-v1-锁脸.md     # sidecar 元数据
styles/胶片-v1-风格参考.png
```

命名规则：
- 类别目录用英文小写；文件名允许中文，但不要用空格，用 `-` 或 `_` 连接，避免 shell 与脚本转义问题。
- 版本用 `v1`、`v2` 递增，同一资产新版本不覆盖旧版本。
- 用途词与 `prompt-craft.md` 的用途词一致：人物参考（锁脸）/物体参考/场景参考/关键帧/风格参考/构图参考等。

## 三、sidecar 元数据（必须）

每个入库素材配一个同名 `.md`，至少记录五项：

| 字段 | 必填内容 |
|---|---|
| 用途词 | 人物参考（锁脸）/物体参考/场景参考/关键帧/风格参考/构图参考… |
| 来源 | 本项目生成 / 用户提供 / 调研收集（附出处） |
| 授权/敏感 | 可商用/仅个人/未确认；肖像是否已授权；敏感内容标记 |
| 规格 | 尺寸/格式/大小（如 1536x1024 PNG，2.4MB） |
| 提示词引用编号 | 最近一次生成中的 `@图片1` 等编号与任务记录 |

模板：

```markdown
# 林晚-v1
- 用途词：人物参考（锁脸）
- 来源：本项目生成（2026-08-05）
- 授权：可商用；肖像：已获用户授权
- 规格：1536x1024 PNG，2.4MB
- 提示词引用编号：@图片1（任务 <prompt_id> 使用）
- 复用记录：已用于 2 条短片，脸部一致 OK
```

## 四、入库前格式校验

上游输入约束（作为校验标准）：

| 素材 | 允许格式 | 单文件上限 |
|---|---|---|
| 视频 | H.264/H.265（内嵌 AAC/MP3） | 50MB |
| 图片 | JPG/JPEG/PNG/WEBP/HEIC/HEIF | 30MB |
| 音频 | WAV/MP3 | 15MB |

入库前检查：

```bash
ffprobe -v error -show_entries format=duration,size,format_name -of default=nw=1 林晚-v1.png
ffprobe -v error -show_entries stream=codec_name,width,height -of default=nw=1 demo.mp4
```

不合格时先转码再入库（示例）：

```bash
ffmpeg -i input.webm -c:v libx264 -c:a aac output.mp4
```

默认打包节点未实现素材上传，但校验仍要做：这些资产未来由扩展节点或直调参考 API 时会直接复用。

## 五、提示词引用编号规则

- `@图片1`、`@视频1`、`@音频1` 按本次生成的上传顺序编号，不是按文件在磁盘上的顺序。
- 每次提交前记录映射，避免串号：

```markdown
生成日期：2026-08-08 项目A 镜头02
@图片1 -> characters/林晚-v1-锁脸.png（人物参考（锁脸））
@图片2 -> scenes/竹林-v1-场景参考.png（场景参考）
```

- 同一个文件在不同任务中编号可能不同，提交时以本次上传顺序重新编号。
- 能力边界：默认打包节点未实现素材上传；若本机 ComfyUI 已加载支持上传的扩展节点，
  按该工作流实际能力执行。上述规则用于参考 API 直调与未来能力方向；
  默认快速路径提交时按 `prompt-craft.md` 跳过参考素材段。

## 六、资产中心式跨项目复用

把厂商"资产中心"概念落到本地实现：已验证好用的角色/风格/场景沉淀为资产，新项目直接调用，不要每次重新生成。

做法：
1. 跑通并验收后，把素材 + sidecar 存入对应的 `characters/`、`scenes/`、`styles/`、`props/` 或 `references/`。
2. 新项目直接引用共享资产目录（或复制到项目对应目录），并在元数据中保留原始出处。
3. 复用后把效果写回 sidecar 的"复用记录"，持续积累哪些资产可靠。

这比每次都重新生成成本低，也能保证跨项目一致性。

## 七、Git 选择性版本管理

原则：真实 key、输出产物、大体积临时文件不入库；源码、配置示例、workflow JSON、文档、精选示例素材入库。

分类表：

| 类别 | 处理 | 示例 |
|---|---|---|
| 入库 | 源码、脚本、文档 | `scripts/`、`references/` |
| 入库 | 配置示例、workflow JSON | `config.json.example`、`assets/workflow_api_mzsj_video.json` |
| 入库 | 已授权、小体积的精选素材 | `examples/` 下的示例图 |
| 不入库 | 真实 key | `config.json`、`*.key` |
| 不入库 | 输出产物、临时文件 | `output/`、`__pycache__/` |
| 不入库 | 敏感/未授权素材 | 用户肖像、版权存疑的参考图 |
| 看情况 | 参考素材 | 授权清楚且体积小时可入库；否则归档在外 |
| 看情况 | 成片 | 一般归档到项目外或对象存储，git 只存清单 |

仓库已有 `.gitignore`，下面是模板片段，不是强制覆盖：

```gitignore
# 真实凭据
config.json
*.key
.env
.env.*

# 本地运行时产物
output/
input/
__pycache__/
*.pyc
.DS_Store
```

选择性 add 与自查：

```bash
git status                       # 1. 先看全部变更
git add -f characters/林晚-v1-锁脸.png characters/林晚-v1-锁脸.md
git check-ignore -v config.json  # 2. 验证敏感文件确实被忽略
git diff --cached --stat         # 3. 复查暂存内容
git commit -m "assets(character): add 林晚-v1 参考图"
```

严禁 `git add .` 盲提；提交信息风格：`assets(类别): 动词 内容`。

大文件处理：成片/大素材放项目外归档目录或对象存储，git 只存清单/索引：

```csv
date,type,name,path,size,usage
2026-08-08,finals,brand-02-v1.mp4,/Volumes/Archive/brand/finals/brand-02-v1.mp4,48MB,@视频1
```

## 八、失败模式与自查清单

| 失败模式 | 规避 |
|---|---|
| 文件名含空格/中文 | 中文 OK；空格统一改 `-`；脚本中引用时加引号 |
| 未校验格式直接上传 | 入库前用 ffprobe 查格式/大小，不合格先转码 |
| 提示词编号串号 | 每次提交前写映射；同一文件按本次顺序重排 |
| 把 key 提交 | `config.json` 永不 add；提交前 `git status` + `git check-ignore -v` |
| 未确认授权就入库 | 肖像/版权素材先记录授权，未确认不入库 |
| 草稿混入资产 | 一次性草稿放临时目录，验收后再入库 |

自查清单（入库前逐项打勾）：
- [ ] 文件名符合 `类别-名称-版本-用途`
- [ ] sidecar 五项元数据齐全
- [ ] 格式与大小通过上游约束校验
- [ ] 授权/敏感字段已填写
- [ ] `git status` 只包含计划提交的路径
- [ ] `git check-ignore -v` 确认敏感文件被忽略

## 交叉引用

- references/prompt-craft.md：用途词表、素材编号与参考素材段写法
- references/prompt-templates.md：含参考素材的提示词模板
- references/comfyui-workflows.md：执行面、产物路径与提交方式
- references/quality-control.md：素材校验与结果验收
- references/production-workflow.md：项目文件组织与交付流程
