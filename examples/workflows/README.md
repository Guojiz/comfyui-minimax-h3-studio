# Workflow research catalog / Workflow 研究目录

This public package intentionally does not redistribute third-party workflow JSON files whose upstream repository has no
formal license. The former 16-file collection came from `Lesilva/comfyui-workflows`; keep any local copies under the
Git-ignored `.local-sources/research-workflows/` directory for study and adaptation.

本公开包不再分发上游没有正式许可证的第三方 workflow JSON。此前 16 个参考文件来自
`Lesilva/comfyui-workflows`；本地研究副本应保存在 Git 忽略的 `.local-sources/research-workflows/`，
供 Agent 阅读、体检和改造，但不能作为本项目 MIT 许可下的正式能力发布。

## Promotion rule / 晋升规则

A workflow may enter the distributable Skill assets only when all of these are known:

- purpose and semantic inputs/outputs;
- required nodes, models and deployment configuration;
- source and redistribution license;
- verification status: `untested`, `dry-run` or `live-tested`, with date and scope;
- no private paths, credentials or unlicensed media.

满足用途、语义输入输出、依赖、部署配置、来源、再分发许可、验证级别和隐私检查后，才能把
本地研究 workflow 晋升到可发布正式库。项目修改版始终先复制到 `<project>/workflows/`。

Use `skills/ai-video-studio/scripts/workflow-doctor.py` before execution and the generic
`run-workflow.py --dry-run` path before any real submission. A filename or upstream claim is not local verification.
