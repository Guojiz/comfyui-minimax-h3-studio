# 资产清单

只登记当前工作会用到的资产。目录和文件在需要时再创建；状态变化时修改本表，不移动文件。

状态：`temporary`（可丢弃） / `candidate`（值得查看） / `approved`（已接受或被正式采用）。

| id | path | status | type | derived_from | workflow / run_id | authorization | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| _asset-001_ | _relative/or/absolute/path_ | _temporary_ | _image/video/audio/document/workflow_ |  |  | _owned/licensed/reference-only/unknown_ |  |

只有 `id`、`path`、`status` 必填，其余有可靠事实时再写。runner 只能补充客观执行信息；
`candidate/approved` 必须由 Agent 根据客户反馈判断。
