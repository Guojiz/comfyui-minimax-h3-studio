# Qoder 兼容映射

Qoder 通过 `.qoder-plugin/plugin.json` 安装整个插件，或从 `.qoder/skills/ai-video-studio/` 读取 Skill。
它仍把当前宿主 Agent 作为操作主体；不要假设插件内存在独立编排器。

运行时资产随 Skill 位于 `assets/`，内部脚本从 Skill 自身目录解析模板。其他宿主可以复制完整
`skills/ai-video-studio/` 并将语义动作映射到自身的文件、终端、浏览器和多模态能力。
