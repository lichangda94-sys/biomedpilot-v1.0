# B8.6 Report-ready Gate and Export Package

## 旧实现审计与迁入判断

| 范围 | 判断 | 可复用内容 | 不直接迁入原因 | 本阶段处理 | 测试 |
| --- | --- | --- | --- | --- | --- |
| `reports/project_report_builder.py` | 最小迁入 | Markdown 草稿生成 | 草稿缺 gate，不能称 formal report | manifest 新增 `draft_only` 和 gate snapshot | report tests |
| `results/*` | 直接保留 | v2 result registry | report-ready 只消费 result index | gate 基于 result registry | gate tests |
| `plots/*` | 直接保留 | plot artifact schema | figures 必须注册 | gate 检查 plot entries | export tests |
| old report builder / result summary | 不迁入，仅记录 | markdown package 思路 | 缺 semantics/provenance/dependency snapshot | 新 export package 重新组装 | export tests |
| PDF/DOCX 脚本 | 不迁入 | 无 | 新依赖和打包风险 | 默认 Markdown + artifacts package | 文档记录 |

## Report-ready Gate

新增 `reports/readiness.py`，检查 result index、semantics、testing/imported/exploratory、input package provenance、parameters、dependency snapshot、validation status、plot artifact、warnings、limitations、no clinical advice。

Report status：`draft_only`、`blocked`、`eligible_for_internal_report`、`report_ready_package_created`、`test_report_only`。

## Export Package

新增 `reports/export_package.py`，生成：

```text
report_package/
  report.md
  tables/
  plots/
  manifests/
    result_index_snapshot.json
    input_package_manifests/
    parameters_manifests/
    dependency_snapshot.json
    validation_report.json
    warnings.json
  logs/
  README_limitations.md
```

## UI 变化

现有“刷新报告草稿”仍保留，报告 manifest 明确 `report_status=draft_only`。Report-ready export 仅当 gate pass 时应启用。

## 未实现边界

不生成临床建议，不承诺投稿级结论，不默认纳入 testing-level，未新增 PDF/DOCX 依赖。

## B8.7 建议

Survival/clinical outputs 必须先完成 preflight 和 backend decision，不能直接进入 report-ready。
