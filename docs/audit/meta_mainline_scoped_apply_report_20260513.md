# Meta MainLine Scoped Apply Report

日期：2026-05-13

## 1. 本阶段目标

本阶段在用户确认后，于 MainLine worktree 执行 Meta active runtime 的 path-limited scoped apply。目标是将 Integration `f66be3d` 已验证通过的 Meta active runtime、Meta tests、Meta UI tests 和必要报告文档引入 MainLine，同时保留 MainLine 当前 shared UI 架构和 Bioinformatics 边界。

本阶段未执行整分支 merge，未修改 `CODEX.md`，未引入 `app/meta_analysis/legacy/**`，未修改 Bioinformatics 业务代码，未 push，未打包发布。

## 2. 当前分支 / worktree / git head

| Worktree | 分支 | Git head |
| --- | --- | --- |
| MainLine | `stable/mainline` | scoped apply 前：`040cc46fac8e59f8c794e5e57c27dc5ecceea1aa` |
| Integration | `dev/integration` | `f66be3d140e8398ae889ffbf3ed0aa8f22c5c2d3` |
| Meta | `dev/meta-analysis` | `76f9a0ee6017ba47519c969d5a987698691d68a1` |

前置提交：

- `76f9a0e`：Meta active runtime legacy bridge 退休。
- `dbf4323`：Integration staged Meta active runtime apply。
- `f66be3d`：Integration full validation 通过。
- `11d6454`：MainLine Meta merge preparation audit。
- `97f5972`：MainLine AI Gateway Ollama audit 文档恢复。

## 3. 实际引入文件范围

从 Integration path-limited 引入：

- `app/meta_analysis/**` active runtime。
- `tests/meta_analysis/**`。
- `tests/ui/test_meta_analysis_workflow_pages.py`。
- `tests/ui/test_meta_search_stage_m2.py`。
- `tests/ui/test_meta_stage_m3_dedup_workflow.py`。
- Meta audit reports:
  - `docs/audit/meta_mainline_merge_readiness_audit_20260513.md`
  - `docs/audit/meta_ui_theme_unification_report_20260513.md`
  - `docs/audit/meta_active_runtime_legacy_bridge_retirement_report_20260513.md`
- Integration reports:
  - `docs/integration/meta_integration_merge_validation_20260513.md`
  - `docs/integration/meta_staged_integration_report_20260513.md`
  - `docs/integration/meta_staged_integration_apply_report_20260513.md`
  - `docs/integration/meta_integration_full_validation_20260513.md`
- `docs/meta_dev_reports/ui_construction_preparation_report.md`，用于满足当前 Meta UI construction test contract。

手工适配：

- `app/shared/ui/theme.py`
  - 将 legacy bridge `COLORS` 映射中的 Meta token 收敛到 `PRIMARY_NAVY` / `ACCENT_TEAL` / `BACKGROUND_LIGHT`。
  - 移除 active token map 中的 old Meta purple 使用路径。
- `app/ui_style_tokens.py`
  - 在 MainLine 当前 shared UI bridge 上新增 `meta_workspace_stylesheet()`、`meta_card_stylesheet()`、`meta_error_text_style()`、`meta_text_style()`、`meta_title_style()`。
  - 未覆盖 MainLine 当前 `app.shared.ui.theme` bridge。
- `tests/ui/test_module_selection.py`
  - 仅更新 Meta active workflow 前四个 page key 断言。

## 4. 明确未引入文件范围

明确未引入：

- `CODEX.md`。
- `app/bioinformatics/**`。
- `tests/bioinformatics/**`。
- `app/meta_analysis/legacy/**`。
- `app/shared/ui/**` 删除差异。
- `docs/architecture/**` 删除差异。
- `docs/handoff/**` 删除差异。
- `docs/ui/**` 删除差异。
- `docs/archive/legacy_handoff_20260513/**` 向顶层 docs 的大规模历史迁移差异。
- Vocabulary / packaging / AI Gateway / schema 非 Meta scoped 差异。

## 5. shared UI token 处理

未使用 Integration 的旧版 `app/ui_style_tokens.py` 覆盖 MainLine。

MainLine 当前 shared UI 架构继续保留：

- `app/shared/ui/theme.py`
- `app/shared/ui/__init__.py`
- `app/ui_style_tokens.py` 的 `as_legacy_*_dict()` bridge。

Meta active UI 需要的 helper 已在现有 bridge 上补齐，避免回退 `button_qss()`、`surface_card_qss()`、`page_title_qss()` 等 MainLine shared UI helper。

## 6. legacy / Bioinformatics 边界检查

检查结果：

- `app/meta_analysis/legacy/` 不存在于 MainLine active tree。
- active runtime 未发现 `_legacy_path` / `LEGACY_ROOT` / `app.meta_analysis.legacy` bridge；命中仅为 guard tests 的 forbidden-token 字面量。
- active Meta runtime 未发现 `app.bioinformatics` import；命中仅为防护断言。
- 未修改 `app/bioinformatics/**` 或 `tests/bioinformatics/**`。

## 7. UI / module selection 处理

`tests/ui/test_module_selection.py` 仅将 Meta workspace page key 断言从旧 shell contract 更新为 active workflow 前四个 key：

- `workflow_home`
- `pico_workspace`
- `search_strategy`
- `literature_import`

未修改 UI shell 结构，未覆盖 MainLine `app/shell/main_window.py`，未回退 shared UI helper。

## 8. 测试结果

| 命令 | 结果 |
| --- | --- |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q` | `465 passed in 7.11s` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | `170 passed in 11.95s` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q` | `225 passed in 25.60s` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q` | `264 passed in 4.98s` |
| `python3 -m app.main --smoke-test` | passed；`workspace_entries=2`，`meta_analysis_features=7` |
| `python3 scripts/run_tests.py` | `1147 passed in 53.59s` |
| `git diff --check` | passed |

## 9. 剩余风险

Medium:

1. 本阶段仍是 path-limited scoped apply，不代表 `dev/integration` 或 `dev/meta-analysis` 可以整分支 merge。
2. `app/meta_analysis/legacy/**` 仍未进入 MainLine；如未来需要历史归档，应另开隔离 / archive 阶段处理。
3. Meta active runtime 已进入 MainLine，但仍是 Developer Preview / testing-level research assistance，不得描述为 clinical-grade、production-ready 或 submission-grade。

Low:

1. docs 中保留历史报告文字，可能提及 GEO / TCGA / GTEx / Bioinformatics；这些不是 active runtime。
2. Meta import parser / normalizer 已通过当前 tests，但更多供应商导出格式仍属于后续 Meta 扩展风险。

## 10. 是否建议继续准备主线合并

本阶段已经在 MainLine 完成 scoped apply，因此不再需要“把 Meta 合并进 MainLine”的分支合并动作。

建议下一步在用户确认后进入 MainLine 后续发布准备审计或 ReleaseBuild 同步准备，而不是继续 merge 分支。任何 ReleaseBuild / 打包 / 发布前动作仍需单独确认。
