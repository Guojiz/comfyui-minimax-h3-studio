# Skill 演进与维护

> 何时加载：用户要求创建/修改/保存 Skill，或同一流程重复出现、想把经验固化为 Skill 时加载本文档。

## Skill 是什么

Skill 是给 Agent 的可复用工作说明书，固化技艺/流程/审美/纠错知识，不是产品能力本身。

- Agent 不加载 Skill 也能工作；Skill 负责稳定复现
- 同样的输入走同样的步骤、同样的确认点、同样的纠错规则
- 不把产品能力或模型能力写进 Skill；能力边界始终以节点实际实现为准

## 什么值得存成 Skill

至少满足两条才建议保存：

| 条件 | 判断 |
| --- | --- |
| 复杂度 | ≥3 步或有分支逻辑 |
| 可复用 | 用户可能用不同输入重复做同样的事 |
| 隐性知识 | 含不显而易见的技巧、参数、失败应对 |
| 纠错历史 | 用户修正过流程，修正适用于未来 |

一次性简单操作（如“生成一张图”）不值得存，直接描述即可。

## 目录结构

提炼 skill-creator 指南与本仓库实际布局：

```
skill-name/
├── SKILL.md            # name + description + 触发词 + 运行时指令
├── agents/openai.yaml  # Codex 等宿主的可选界面元数据
├── references/         # 按需加载的大文档
├── scripts/            # 可执行脚本
└── assets/             # 插件/节点等静态资源（本仓库实际布局）
```

- 正文 ≤500 行，超出放 `references/`，可执行模式提取到 `scripts/`
- SKILL.md 保持精简，只保留运行时必需字段
- description 描述用户意图与触发词，不写实现步骤
- `SKILL.md` 是唯一通用必需文件；`agents/openai.yaml`、`meta.yaml` 或插件 manifest
  按目标宿主选用，不要把某个平台的展示字段误写成通用要求
- 本仓库即示例：`SKILL.md` + `agents/openai.yaml` + `references/` + `scripts/`；
  插件根目录另有 `.qoder-plugin/plugin.json` 与共享 `assets/`

## 创建路径

- 从对话提取已有流程：把已完成的工作流固化为 Skill
- 从零问答：没有现成流程时，先问输入/输出/步骤/约束/易错点
- 修改现有 Skill：读现有文件，只改需要改的部分
- 上传资料生成：把经验文档、笔记交给 Agent 提炼

从对话提取时至少记录：

- 发生了什么：使用了哪些能力、什么顺序
- 媒体流转：输入 → 中间产物 → 最终输出
- 创意目的：核心意图
- 关键决策：风格方向、参数调整、确认点
- 纠错点：失败、重试、参数变更，这是最有价值的知识
- 用户没改动的默认值：说明这些参数可以保持灵活

写作原则：

- 编码用户纠错与决策，不只写成功路径
- 不写死单次内容（不要写具体文件名、具体台词）
- 描述任务而非路由（不写“调用某 agent 某模型”，除非用户明确指定）
- 高成本操作前加确认点，不要每个小步骤都确认
- 同类资源批量处理，不逐个交替
- 解释约束背后的原因，不只给命令

## 五步流程

1. 捕捉意图：理解工作流、输入输出、关键决策、纠错点
2. 编写：按目录结构写 SKILL.md、`references/` 与 `scripts/`
3. 审查：向用户展示，收集调整
4. 验证：触发测试 + 工作流走查
5. 保存加载：写入目标目录并触发重新加载

### 验证清单

触发测试：

- 3 个应触发查询，3 个不应触发查询
- 只看 name + description 判断“会触发吗”

工作流走查（用一个新假设场景逐步走）：

- 完整性：每步输出是下一步输入吗
- 通用性：是否绑定了原始对话的具体内容
- 确认点：高成本操作前有确认吗
- 失败路径：失败时有指导吗
- 批量策略：同类资源批量处理吗

## 迭代信号

| 信号 | 含义 | 修复 |
| --- | --- | --- |
| 没触发 | description 缺用户说法 | 补触发词 |
| 不该触发却触发 | description 太宽 | 收窄边界 |
| 触发了但执行差 | 指令不清晰 | 澄清步骤，加示例 |
| 每次都写类似脚本 | 重复工作未打包 | 抽到 `scripts/` |
| 用户总改同一步 | 约束不够 | 加明确约束与原因 |
| 做了多余的事 | 指令导致无效工作 | 删减简化 |

迭代前收集 2–3 次使用证据，诊断是触发问题、执行问题还是缺资源，只修有问题的部分。

## 版本与维护

- 行为变化升版本：内容修复升 patch，新能力升 minor，大重构升 major（按平台版本规则）
- SKILL.md 保持精简，新增知识先沉淀到 `references/` 再链接
- 每次迭代记录证据：什么输入、什么失败、改了什么、验证结果
- 修改后重新做验证清单，并触发 Skill 重新加载

保存与引用完整性检查：

```bash
# 目标目录
TARGET_DIR=skills/ai-video-studio

# 通用必需文件
test -f "$TARGET_DIR/SKILL.md"

# 引用的 references/scripts 都必须存在
grep -oE '(references|scripts)/[^`" ]+' "$TARGET_DIR/SKILL.md" \
  | while read f; do
      [ -f "$TARGET_DIR/$f" ] || echo "MISSING: $f"
    done
```

提交示例：

```bash
git add work/ai-video-studio/skills/ai-video-studio
git commit -m "docs(ai-video-studio): 更新 Skill 流程与 references"
```

## 本技能的演进示例

本技能从“三段式唯一流程”重构为“Agent / Skill / 资产 / ComfyUI 四核心”：

- 旧版：提示词增强 → 首帧生图 → 视频生成，作为唯一流程
- 新版：Agent 负责创意编排与决策，Skill 固化知识，资产中心跨项目复用，ComfyUI 作为操作面/执行面；三段式降级为快速路径
- 重构效果：流程可复用（同类片子直接走生产工作流）、可扩展（长视频、参考能力未来可在 ComfyUI 层扩展，Skill 文档结构不用推倒重来）

这次演进本身也是迭代信号的应用：原流程过度绑定“一段式生成”，用户需要完整生产流程与长视频时无法复用，因此把结构从单一流水线升级为四核心加阶段式生产路径。

## 能力边界

Skill 只固化知识与流程，不改变默认打包节点能力，也不限制 ComfyUI 实例能力：

- 默认三段式模板未封装素材上传、首 + 尾帧和单参考图；打包视频节点虽有尾帧和
  单参考图输入，仍需接入 IMAGE 上游并实测。视频/音频多模态参考、精准编辑、单次长视频
  目前未由默认路径实现；
  这些不是整个 Studio 的能力边界，可由扩展节点或工作流实现
- Skill 文档不得把未验证能力写成“当前支持”，也不得把快速路径边界写成产品边界
- 上游模型宣称的能力只作为未来方向或提示词创作参考

## 交叉引用

- `references/production-workflow.md`
- `references/long-video.md`
- `references/prompt-craft.md`
- `references/prompt-templates.md`
- `references/asset-management.md`
- `references/comfyui-workflows.md`
- `references/quality-control.md`
