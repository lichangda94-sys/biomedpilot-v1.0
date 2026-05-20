# B8.4 Result Index and Result Browser Foundation

## 旧实现审计与迁入判断

| 范围 | 判断 | 可复用内容 | 不直接迁入原因 | 本阶段处理 | 测试 |
| --- | --- | --- | --- | --- | --- |
| `results/project_results.py` | 最小迁入 | load/write 路径和旧 index 兼容 | v1 字段不足，semantics 不统一 | 加 migration 到 v2 entry | `test_result_registry.py` |
| `reports/project_report_builder.py` | 最小迁入 | 报告草稿已从 result index 读取 | 缺 report-ready gate | B8.6 接 gate | report tests |
| `immune_infiltration/*` | 直接保留 | B7 exploratory 语义 | 不应升级为 formal | registry semantics 保守处理 | semantics tests |
| `enrichment_runner.py` / `correlation_runner.py` | 不迁入，仅记录 | 旧 runner 输出思路 | 缺 input_package_id / dependency snapshot | 后续需注册 result index 后消费 | 文档记录 |
| Integration / ReleaseBuild result/report | 不迁入，仅记录 | result summary 概念 | schema/path 不兼容 | 不删除旧结果，migration 保守 | migration tests |

## Result Schema

新增 `results/models.py`、`registry.py`、`migration.py`、`validation.py`。最小字段包括 result id、task run、semantics、input package、source manifest、parameters、engine/version、dependencies、artifacts、validation、warnings/blockers、logs、report-ready eligibility、migration status。

## Result Semantics

统一 `preflight_only`、`testing_level`、`exploratory`、`formal_computed_result`、`imported_external_result`、`configured_not_run`、`failed`、`blocked`。Unknown legacy 默认不升 formal。

## Migration

不删除旧结果。能识别则迁移；不能识别则 `legacy_unverified`，保守标记为 `testing_level` 或 `imported_external_result`。

## UI 变化

现有 result browser 可继续读 `project_results.load_result_index`，该函数现在自动迁移 entries。后续 UI 可基于 `result_semantics` 做筛选和标签。

## 未实现边界

未新增 GSEA/survival/plot/report-ready 执行器，未升级旧结果，未隐藏 warnings/blockers。

## B8.5 建议

Plot artifact 必须引用 result index entry，并继承 source result semantics。
