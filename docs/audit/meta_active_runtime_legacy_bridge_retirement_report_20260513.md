# Meta active runtime legacy bridge 退休前置修复报告

## 1. 修复目标

本阶段目标是在 Meta worktree 内退休 active Meta runtime 对 `app/meta_analysis/legacy` 的 transitional legacy bridge 依赖。legacy 目录继续保留为历史隔离区，但 active services、active adapters、active UI 状态与 active tests 不再通过 `_legacy_path()`、legacy service loader、legacy parser/normalizer 或 legacy batch service 运行。

本阶段未进入 Integration / MainLine 合并准备，未修改 Bioinformatics，未删除 legacy 文件，未修改 AI Gateway、shared vocabulary 或数据 schema。

## 2. 当前分支 / worktree / git head

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/Meta`
- Branch: `dev/meta-analysis`
- 修复前 HEAD: `00765f49a8e37573ccf5fb18198ac36a2f105dea`
- 本报告生成时间: `2026-05-13`

## 3. legacy bridge 审计结果

修复前 active runtime 仍存在以下 bridge：

- `app/meta_analysis/adapters/literature_import_adapter.py`: 暴露 `_legacy_path()` 并通过 legacy parser 解析 RIS / NBIB / CSV。
- `app/meta_analysis/adapters/duplicate_review_adapter.py`: 通过 legacy dedup service 生成 duplicate groups。
- `app/meta_analysis/adapters/prepare_screening_adapter.py`: 通过 legacy normalizer 生成 screening-ready records。
- `app/meta_analysis/adapters/screening_adapter.py`: 通过 legacy screening service 生成 title/abstract queue。
- `app/meta_analysis/adapters/extraction_adapter.py`: 通过 legacy extraction service 生成 extraction pool。
- `app/meta_analysis/adapters/analysis_adapter.py`: 通过 legacy `OutcomeType` 读取 supported outcome types。
- `app/meta_analysis/services/literature_batch_import_service.py`: 直接调用 legacy `ImportBatchService`。
- `app/meta_analysis/services/literature_import_service.py`: 通过 `_legacy_path()` 调用 legacy sanitizer 和 diagnostics。
- `tests/meta_analysis/test_stage_6_literature_import_panel.py`: 测试命名和覆盖目标仍指向 legacy batch service。
- `tests/meta_analysis/test_literature_contract_hardening.py`: 直接 import `_legacy_path()` 并覆盖 legacy sanitizer / normalizer contract。

## 4. 移除或替换的 active runtime legacy 依赖

已移除 active runtime 中的 `_legacy_path()`、`LEGACY_ROOT`、legacy service loader 和 `sys.path` 注入。

新增 active helper：

- `app/meta_analysis/literature_import_core.py`

该 helper 承担 active runtime 所需的最小文献导入能力：

- RIS / NBIB / CSV 本地解析。
- DOI / PMID / title / author / publication type 标准化。
- import payload sanitizer。
- import diagnostics JSON 和 warnings CSV 生成。
- import batch manifest append。
- duplicate group identifier detection。

Adapters 已改为 active implementation：

- `literature_import_adapter.py`: 使用 `parse_literature_file()`。
- `prepare_screening_adapter.py`: 使用 `normalize_record_payload()`。
- `duplicate_review_adapter.py`: 使用 `duplicate_groups_for_records()`。
- `screening_adapter.py`: 在 active adapter 内生成 title/abstract screening queue。
- `extraction_adapter.py`: 在 active adapter 内生成 extraction pool。
- `analysis_adapter.py`: 在 active adapter 内维护 supported outcome type set。

## 5. literature batch import service 如何从 legacy 解耦

`app/meta_analysis/services/literature_batch_import_service.py` 不再调用 legacy `ImportBatchService`、`LiteratureStore`、`ImportFormatHint` 或 `ImportSourceKind`。

现在执行流程为：

1. 校验本地文件路径和导入格式。
2. 使用 active parser 解析 RIS / NBIB / CSV。
3. 使用 active normalizer 生成 records。
4. 使用 active diagnostics 生成 JSON / warnings CSV。
5. 写入 active import batch manifest。
6. 返回 `LiteratureBatchImportSummary`，保持 UI panel 需要的 status、counts、diagnostics path 和 warnings path。

不联网，不生成假结果，不新增 GEO / TCGA / GTEx 行为。

## 6. `test_stage_6_literature_import_panel.py` 如何调整

该测试已从 legacy batch service 语义改为 active batch service 语义：

- `test_literature_batch_import_executes_legacy_batch_service_and_returns_summary` 改为 `test_literature_batch_import_executes_active_batch_service_and_returns_summary`。
- `test_literature_batch_import_rejects_unknown_format_before_legacy_execution` 改为 `test_literature_batch_import_rejects_unknown_format_before_active_execution`。

测试仍覆盖：

- RIS / NBIB / CSV 导入路径。
- diagnostics JSON / warnings CSV 输出。
- metadata 中 source database、search date、search strategy、dedup mode。
- unknown format 在执行前被阻止。
- UI state 从 batch summary 读取 diagnostics。

## 7. 新增 guard test 说明

新增：

- `tests/meta_analysis/test_active_runtime_legacy_bridge_retirement.py`

Guard 覆盖：

- active app targets 不包含 `_legacy_path`。
- active app targets 不包含 `LEGACY_ROOT`。
- active app targets 不 import `app.meta_analysis.legacy`。
- active app targets 不使用 `app/meta_analysis/legacy` 路径。
- active app targets 不再从 legacy top-level `literature.*`、`extraction.models`、`analysis.*` import。
- active literature tests 不依赖 legacy batch service。

允许 docs 和 `app/meta_analysis/legacy/` 内部继续出现 legacy 字符串。

## 8. legacy 目录当前隔离状态

`app/meta_analysis/legacy/` 未删除、未重构、未迁移。该目录仍保留历史 UI、旧 literature/dedup、旧 GEO/TCGA/GTEx/Bioinformatics readiness、旧 demo/mock runner 和历史测试材料。

当前隔离结论：

- active runtime 不再通过 `_legacy_path()` 调用 legacy。
- active runtime 不再导入 `app.meta_analysis.legacy`。
- legacy 目录内部自引用和历史内容允许保留，但不作为 MainLine active runtime 合并标准。

## 9. 是否仍有 active runtime 调用 legacy

截至本次修复后检查：未发现 active runtime 调用 `app/meta_analysis/legacy`。

剩余 legacy 字符串主要位于：

- `app/meta_analysis/legacy/` 历史隔离区。
- docs / audit / historical reports。
- 少量兼容性字段名称，例如 screening decision 中的 `legacy_decision`，该字段用于旧数据兼容，不是 legacy runtime 调用。

## 10. 测试结果

已执行：

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`
  结果：`462 passed in 4.25s`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
  结果：`154 passed in 9.62s`
- `python3 -m app.main --smoke-test`
  结果：通过，`git_head=00765f4`，`meta_analysis_features=7`
- `git diff --check`
  结果：通过
- active runtime legacy bridge focused rg check
  结果：未发现 active runtime bridge；命中仅位于本报告、既有 audit 文档或 guard test 的 forbidden-token 字面量。

## 11. 剩余风险

Medium:

- 新 active parser/normalizer 是 legacy bridge 的最小替代实现，已覆盖现有 RIS / NBIB / CSV fixture 和 diagnostics contract，但尚未覆盖更多供应商导出边界，例如复杂 EndNote / Zotero / WOS / CNKI alias。
- `legacy_decision` 等兼容字段仍存在于 active screening 数据结构中。它不是 runtime bridge，但后续进入 MainLine 前需要决定字段命名是否继续保留。

Low:

- docs 和 historical reports 中仍大量记录 legacy、GEO、TCGA、GTEx、Bioinformatics 历史内容。当前允许保留，但 Integration staged integration 需要继续只引入必要 docs。
- `app/meta_analysis/legacy/` 目录体量较大，仍会在整分支 merge 中制造审计噪声。

## 12. 是否建议回到 Integration staged integration

建议回到 Integration staged integration，但仍不建议整分支 merge `dev/meta-analysis`。

推荐下一步：

1. 在 Integration worktree 重新采用 staged integration。
2. 优先引入 active runtime 文件、active tests、报告文档和必要 shared UI token。
3. 继续排除 Bioinformatics、CODEX.md、MainLine UI shell 非必要差异和 legacy 大规模历史内容。
4. 在 Integration 中重新运行 `tests/meta_analysis`、`tests/ui`、`tests/shared`、smoke test 和 diff check。
