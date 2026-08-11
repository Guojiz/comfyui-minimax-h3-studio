# Remotion 动效与可视化合成

> 需要程序化动效、数据可视化、标题/字幕动画、片头片尾或叠加层时读取。

## 定位

Remotion 是用 React/TypeScript 以代码方式生成视频的工具。它在**动效与可视化合成**上很强：
文字动画、图表/数据可视化、HUD 叠加、片头片尾、节奏精确的图形变化，都适合用 Remotion 做。

它**不适合替代长视频粗剪**：Remotion 是“生成一段画面”，不是剪辑器。真正的拼接、转场、
规范化、混音、封装仍由 `rough-cut.py` + FFmpeg 负责。Remotion 渲染出的片段只是素材流里的
一段（和其他生成片段地位相同），仍然按 `candidate → approved` 管理，并进入粗剪输入清单。

## 与视频模型的分工

| 场景 | 优先工具 |
| --- | --- |
| 真实感画面、人物、场景、镜头运动 | 视频模型（通过 ComfyUI workflow） |
| 文字、图形、图表、HUD、精确节奏的动效 | Remotion（程序化、可精确复现、可迭代） |
| 拼接、转场、字幕烧录、混音、封装 | FFmpeg / rough-cut / deliver |

Agent 决定用视频模型还是 Remotion 时，向客户说明取舍：视频模型出“真实画面”但每次有随机性；
Remotion 出“确定画面”但需要写代码。两者产出的片段都进入同一资产流。

## 流程位置

```text
edit plan / EDL
→ 确定哪些视觉元素用 Remotion（动效/文字/数据）
→ remotion-render.py 渲染动效片段（版本化输出）
→ media-probe.py 技术 QC（时长/分辨率/帧率/非空）
→ 登记 assets.md（candidate，客户确认后 approved）
→ rough-cut.py 拼接（动效片段作为一段输入）
→ deliver.py approved-only 交付
```

## 使用方式

`scripts/remotion-render.py` 只负责编排渲染与版本保护，不写 composition 源码：

```bash
python3 scripts/remotion-render.py \
  --entry <项目>/remotion-src/src/Index.tsx \
  --output-name title-card \
  --project <项目> --json --dry-run
```

去掉 `--dry-run` 才渲染。输出写入 `<project>/remotion/<output-name>/vNN/out.mp4`，
版本自动递增、已有版本绝不覆盖；同目录保存 `version.json`（入口、composition、目标规格、
渲染时间、node 路径）。渲染失败会清理未完成的版本目录。

依赖与安全约束：

- 需要 Node.js 20+（node/npx 可从 `--node-dir`、`REMOTION_NODE_DIR` 或 PATH 定位）；
- 项目内需要安装 `remotion` 与 `@remotion/cli`。缺失时脚本返回退出码 2 并给出安装指引，
  **绝不自动安装**；`node_modules/` 与 `package.json` 属于用户本地，不提交公开仓库；
- `--json` 时 stdout 只输出最终 JSON，人类信息走 stderr；
- 脚本是 Agent 内部工具，不负责创意判断；composition 内容由 Agent 依据客户需求编写或修改。

## 许可注意

Remotion 不是宽松 MIT 库，其许可证对使用组织的规模/收入有门槛。公开仓库只提供方法与编排脚本，
不内置 Remotion 依赖、不改写其许可、也不代用户判断合规。使用前由客户确认自己的使用场景符合
Remotion 许可条款。

## 与现有文档的关系

- `references/post-production.md`：动效片段进入粗剪/交付的流程总览。
- `references/asset-management.md`：动效片段与其他素材一样登记来源与 approved 状态。
- `references/quality-control.md`：对渲染出的动效片段做同样技术 QC。
