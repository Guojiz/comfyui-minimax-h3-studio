# 资产、来源与版本

> 产生、比较、批准、复用或归档图片、视频、音频、文档和 workflow 时读取。

## 原则

资产不是独立数据库，而是项目中可继续使用的真实文件及其轻量来源记录。ComfyUI workflow/history
能说明一次运行；`assets.md` 补充跨运行、跨工具和客户选择后的关系。

不要预建一整套资产目录。真正产生某类文件时再创建合适目录；状态只写元数据，不搬文件、不破坏
workflow 引用。

## 三种状态

| 状态 | 含义 | 处理 |
| --- | --- | --- |
| `temporary` | 试验、失败或尚未判断 | 可以清理，不默认进入版本记录 |
| `candidate` | Agent 判断值得客户查看或比较 | 保留并展示，不能冒充已批准 |
| `approved` | 客户明确接受或已被正式下游采用 | 默认进入资产清单和有意义的版本里程碑 |

runner 只记录 workflow、参数、run ID、history 和输出路径等客观事实。只有 Agent 能根据客户反应
更新 `candidate/approved`；脚本不能自动判断创意价值。

## `assets.md` 最小记录

只有 `id`、`path`、`status` 必填，其余有事实时再写：

```yaml
assets:
  - id: shot-01-v2
    path: outputs/shot-01-v2.mp4
    status: candidate
    type: video
    derived_from: [character-main-v1, scene-night-v1]
    workflow: workflows/h3-ref2va.json
    run_id: task_xxx
    model: minimax/minimax-h3-ref2va
    content_hash: sha256:...
    authorization: owned
    note: 等客户比较 v1/v2
```

规则：

- 新版本永不覆盖旧文件；使用稳定 `id` 与递增版本。
- `derived_from` 记录“什么产生什么”，不要保存完整聊天或内部思考。
- 有肖像、版权、公开上传或第三方素材时记录授权状态。
- 客户否决的方向写 `decisions.md`，相应产物保留为 temporary 或按客户要求清理。
- workflow 修改版也作为资产登记，并保存来源、许可和验证状态。

## 复用与项目关系

复用前检查：用途是否匹配、来源是否可信、授权是否覆盖本项目、文件是否仍与哈希一致、历史表现
是否可靠。角色、场景、风格和产品参考应保持稳定 ID；新版本通过 `derived_from` 或备注关联旧版本。

ComfyUI UI 可以展示一次 workflow 的节点和中间结果，但跨运行的批准关系仍以项目文件为准。客户
想看技术细节时打开 ComfyUI；平时由 Agent 在对话中展示真实产物并解释来源。

## 格式和安全

提交前用 `ffprobe` 或适合的媒体工具检查格式、尺寸、时长、编码和文件完整性。真实 API Key、临时
公网 URL、未授权素材和内部模型路径不得进入可发布的资产记录。

参考格式限制必须属于相应 provider/profile，不要在本文件把某个供应商当前限制写成全局规则。

## Git 选择性版本管理

Git 管 Skill、workflow、提示词、项目事实、资产清单、决策、配置示例及精选小资产；大型媒体默认
保存在项目资产目录或外部存储，Git 记录路径、哈希和谱系。确实需要跨设备复现时再选择 Git LFS。

在有意义的里程碑提交，例如：客户锁定方向、批准关键资产、跑通 workflow、完成交付、正式更新
Skill。项目已采用 Git 时可自动完成低风险本地提交并告知；推送远端必须单独授权。

提交前检查：

```bash
git status --short
git diff --cached --stat
git check-ignore -v config.json
```

不要盲目 `git add .`。大媒体、缓存、失败草稿、真实 key 和未授权素材不应意外进入仓库。
