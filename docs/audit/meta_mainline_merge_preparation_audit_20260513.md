# Meta MainLine Merge Preparation Audit

日期：2026-05-13

## 1. 审计目标

本阶段在 MainLine worktree 中审计 Integration full validation 后的 Meta active runtime 是否具备进入 MainLine scoped apply 的准备条件。

本阶段只做审计和报告，不合并 MainLine，不执行整分支 merge，不修改业务代码，不修改 Bioinformatics，不引入 `app/meta_analysis/legacy/**`，不修改 `CODEX.md`，不 push，不打包发布。

## 2. 当前分支 / worktree / git head

| Worktree | 分支 | Git head | 状态 |
| --- | --- | --- | --- |
| `/Users/changdali/Developer/biomedpilot v1.0/MainLine` | `stable/mainline` | `8045864e116d98dd92793624be5b72dec0d9770b` | clean |
| `/Users/changdali/Developer/biomedpilot v1.0/Integration` | `dev/integration` | `f66be3d140e8398ae889ffbf3ed0aa8f22c5c2d3` | clean |
| `/Users/changdali/Developer/biomedpilot v1.0/Meta` | `dev/meta-analysis` | `76f9a0ee6017ba47519c969d5a987698691d68a1` | clean |

关键前置提交：

- `76f9a0e`：Meta active runtime legacy bridge 退休。
- `dbf4323`：Integration staged Meta active runtime apply。
- `f66be3d`：Integration full validation 通过。
- `8045864`：MainLine 当前 shared UI helper 阶段提交。

## 3. 检查方法

已阅读 / 复核：

- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `Integration/docs/integration/meta_integration_full_validation_20260513.md`
- `01_ProjectControl/current_handoff_20260513.md`

执行的审计命令包括：

```bash
git --git-dir="_repo.git" worktree list
git status --short
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git log --oneline -5
git diff --name-status HEAD dev/integration
git diff --name-status HEAD dev/integration -- app/meta_analysis tests/meta_analysis tests/ui/test_meta_analysis_workflow_pages.py tests/ui/test_meta_search_stage_m2.py tests/ui/test_meta_stage_m3_dedup_workflow.py tests/ui/test_module_selection.py docs/audit docs/integration app/ui_style_tokens.py app/shell/main_window.py
git diff HEAD dev/integration -- app/ui_style_tokens.py
git diff HEAD dev/integration -- app/shell/main_window.py tests/ui/test_module_selection.py
rg -n --hidden --glob '!**/.git/**' --glob '!**/__pycache__/**' "meta_.*style|Meta.*style|#12324A|#1BAE9F|#F5F7F9|#FFFFFF|#6B4FD8|#F0EDFF|#0F766E|#E6FFFB|#99F6E4|#D8DEE9|#111827|#B42318|_legacy_path|LEGACY_ROOT|app/meta_analysis/legacy|meta_analysis\\.legacy|app\\.bioinformatics|Bioinformatics readiness|GEO|TCGA|GTEx" app/meta_analysis app/ui_style_tokens.py app/shared/ui tests/meta_analysis tests/ui/test_module_selection.py
```

## 4. 直接 merge 风险结论

不建议、也不允许将 `dev/integration` 整分支 merge 到 `stable/mainline`。

`git diff --name-status HEAD dev/integration` 显示直接分支差异包含：

- `CODEX.md` 从 MainLine 说明变为 Integration 说明。
- `app/bioinformatics/**` 共有 9 个删除 / 修改差异，包括删除 `app/bioinformatics/deg_executor_preflight.py`。
- `app/shared/ui/__init__.py` 和 `app/shared/ui/theme.py` 将被删除。
- 多个 MainLine architecture / handoff / UI governance 文档将被删除。
- `tests/ui/test_shared_ui_theme.py` 和 `tests/ui/test_bioinformatics_light_flow_page_styles.py` 将被删除。
- 大量历史 docs 从 `docs/archive/legacy_handoff_20260513/**` 迁移回顶层 docs。

这些差异明显超出 Meta active runtime scoped apply 范围，并会破坏 MainLine 当前 shared UI 和文档治理基线。

## 5. 可 scoped apply 的 Meta 候选面

`git diff --name-status HEAD dev/integration -- app/meta_analysis ':!app/meta_analysis/legacy'` 显示 Meta active runtime 候选约 122 个文件。

主要候选：

- `app/meta_analysis/workspace.py`
- `app/meta_analysis/project_workspace.py`
- `app/meta_analysis/literature_import_core.py`
- `app/meta_analysis/adapters/**`
- `app/meta_analysis/pages/**`
- `app/meta_analysis/models/**`
- `app/meta_analysis/search/**`
- `app/meta_analysis/services/**`
- `app/meta_analysis/stats/**`
- `app/meta_analysis/quality/**`
- `app/meta_analysis/extraction/**`
- `app/meta_analysis/workflow_pages.py`

测试候选：

- `tests/meta_analysis/**`，约 99 个文件。
- `tests/ui/test_meta_analysis_workflow_pages.py`
- `tests/ui/test_meta_search_stage_m2.py`
- `tests/ui/test_meta_stage_m3_dedup_workflow.py`
- `tests/ui/test_module_selection.py` 中 Meta page key 断言的小范围更新。

文档候选：

- `docs/audit/meta_mainline_merge_readiness_audit_20260513.md`
- `docs/audit/meta_ui_theme_unification_report_20260513.md`
- `docs/audit/meta_active_runtime_legacy_bridge_retirement_report_20260513.md`
- `docs/integration/meta_integration_merge_validation_20260513.md`
- `docs/integration/meta_staged_integration_report_20260513.md`
- `docs/integration/meta_staged_integration_apply_report_20260513.md`
- `docs/integration/meta_integration_full_validation_20260513.md`

## 6. 明确不得引入的差异

明确不得从 Integration 整体带入：

- `CODEX.md`
- `app/bioinformatics/**`
- `tests/bioinformatics/**`
- `app/shared/ui/**` 删除差异
- `docs/architecture/**` 删除差异
- `docs/handoff/**` 删除差异
- `docs/ui/**` 删除差异
- `tests/ui/test_shared_ui_theme.py` 删除差异
- `tests/ui/test_bioinformatics_light_flow_page_styles.py` 删除差异
- `docs/archive/legacy_handoff_20260513/**` 向顶层 docs 的历史迁移差异
- 任何 Vocabulary / packaging / AI Gateway / schema 非 Meta scoped 差异

`app/meta_analysis/legacy/**` 当前在 MainLine 与 Integration 中均未出现；后续仍不得在 Meta MainLine scoped apply 中引入。

## 7. shared UI token / style helper 审计

当前 MainLine 已有新的 shared UI 架构：

- `app/shared/ui/theme.py`
- `app/shared/ui/__init__.py`
- `app/ui_style_tokens.py` 通过 `as_legacy_*_dict()` 读取 shared UI token。

Integration 中 `app/ui_style_tokens.py` 是较旧的手工 token 字典版本。直接 checkout Integration 的 `app/ui_style_tokens.py` 会：

- 删除 MainLine 对 `app.shared.ui.theme` 的桥接。
- 回退 `app/shared/ui` 阶段成果。
- 破坏 `app/shell/main_window.py` 当前对 `button_qss`、`surface_card_qss`、`page_title_qss` 等 shared UI helper 的使用。

结论：下一阶段不能直接覆盖 `app/ui_style_tokens.py`。应在 MainLine 当前 shared UI 架构上手工移植 Meta active UI 需要的 helper，例如：

- `meta_workspace_stylesheet()`
- `meta_card_stylesheet()`
- `meta_error_text_style()`
- `meta_text_style()`
- `meta_title_style()`

同时应移除或隔离 `app/shared/ui/theme.py` 中 `META_LEGACY = "#6B4FD8"` 和 `META_LEGACY_SOFT = "#F0EDFF"` 作为 active Meta token 的误用风险；如果保留为历史常量，必须保证 active Meta helper 不引用它们，并用 tests guard 防止回归。

## 8. UI shell / module selection 审计

Integration 对 `tests/ui/test_module_selection.py` 的差异仅为 7 行：

- 将 Meta page key 断言从旧 MainLine shell contract：
  - `workflow_home`
  - `project_contract`
  - `dev_branch`
- 改为 active workflow 前四个 key：
  - `workflow_home`
  - `pico_workspace`
  - `search_strategy`
  - `literature_import`

该测试意图可接受，但只能在 MainLine 已引入 active Meta workspace 后同步更新。

`app/shell/main_window.py` 差异需谨慎。Integration 版本包含 Bioinformatics fallback QWidget，但同时会回退 MainLine 当前 shared UI helper 使用，把 `surface_card_qss()` / `page_title_qss()` / `card_title_qss()` 改回硬编码 QSS。下一阶段不能直接覆盖该文件；如确需保留 Bioinformatics fallback，应在 MainLine 当前 helper 架构内做最小补丁。

## 9. Bioinformatics 隔离审计

直接 diff 显示 `dev/integration` 与 MainLine 之间存在 9 个 Bioinformatics 文件差异：

- `D app/bioinformatics/deg_executor_preflight.py`
- `M app/bioinformatics/pages/differential_expression_page.py`
- `M app/bioinformatics/pages/geo_asset_detection_page.py`
- `M app/bioinformatics/pages/geo_cleaning_page.py`
- `M app/bioinformatics/pages/geo_download_page.py`
- `M app/bioinformatics/pages/geo_import_page.py`
- `M app/bioinformatics/pages/local_expression_import_page.py`
- `M app/bioinformatics/reports/project_report_builder.py`
- `M app/bioinformatics/workflow_pages.py`

这些差异不得进入 Meta MainLine scoped apply。Bioinformatics 专项测试当前通过：`264 passed in 3.27s`。

## 10. legacy / cross-module boundary 审计

MainLine 当前没有 `app/meta_analysis/legacy/`，Integration 也没有引入该目录。

MainLine 当前 active Meta 是 minimal shell contract，仅有：

- `app/meta_analysis/__init__.py`
- `app/meta_analysis/project_workspace.py`
- `app/meta_analysis/version.py`
- `app/meta_analysis/workspace.py`

扫描结果：

- MainLine active Meta 未发现 `_legacy_path` / `LEGACY_ROOT` / `app.meta_analysis.legacy` runtime bridge。
- MainLine active Meta 未发现 `app.bioinformatics` import。
- MainLine active Meta 当前不包含 GEO / TCGA / GTEx readiness runtime。

## 11. 当前 MainLine 测试结果

| 命令 | 结果 |
| --- | --- |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q` | `4 passed in 0.28s` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | `144 passed in 9.02s` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q` | `2 failed, 223 passed in 25.31s` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q` | `264 passed in 3.27s` |
| `python3 -m app.main --smoke-test` | passed；`git_head=8045864`，`workspace_entries=2` |
| `git diff --check` | passed |

`tests/shared` 失败原因：

- `tests/shared/test_ai_gateway_ollama_migration_audit.py` 读取 `docs/ai_gateway_ollama_existing_call_audit.md`。
- MainLine 当前缺少该文档，导致两个 `FileNotFoundError` 失败。

该失败不是 Meta active runtime diff 自身引入，但它是 MainLine 当前测试健康阻塞。进入实际 MainLine scoped apply 前应先恢复 / 移植 / 修正该 AI Gateway audit 文档测试的基线，或由对应 AI / docs 阶段明确处理。

## 12. 风险清单

### High

1. 直接 merge `dev/integration` 到 MainLine 会带入 `CODEX.md`、Bioinformatics、shared UI 删除、架构/交接/UI 文档删除和历史 docs 迁移，不能执行。
2. MainLine 当前 `tests/shared` 已有 2 个失败，原因是 AI Gateway audit 文档缺失；这会阻塞 MainLine 合并准备的全量健康结论。
3. 直接覆盖 `app/ui_style_tokens.py` 会回退 MainLine 当前 `app/shared/ui` 架构。
4. 直接覆盖 `app/shell/main_window.py` 会回退 MainLine 当前 shared UI helper 使用，并重新引入硬编码 shell QSS。

### Medium

1. Meta scoped apply 文件面较大，约 122 个 active runtime 文件和 99 个 Meta tests，需要 path-limited、可审计引入。
2. MainLine 当前 minimal Meta shell contract 将被 active 8-step workflow 替换，`tests/meta_analysis/test_mainline_meta_contract.py` 和 `tests/ui/test_module_selection.py` 必须同步调整。
3. `app/shared/ui/theme.py` 仍含 `META_LEGACY` purple constants；如保留，应确保 active Meta helper 不引用并有 guard tests。
4. Integration full validation 通过的是 Integration runtime；MainLine scoped apply 后仍必须重新运行 MainLine 测试矩阵。

### Low

1. Integration full validation 已证明 staged Meta active runtime 不依赖 legacy，并且 Meta tests / UI / shared / Bioinformatics / smoke / full run 通过。
2. MainLine 当前 smoke、UI、Bioinformatics 和 minimal Meta tests 通过。

## 13. 是否建议进入 MainLine scoped apply

不建议现在直接进入 MainLine scoped apply。

建议先处理或明确 MainLine `tests/shared` 的 AI Gateway audit 文档缺失问题。该问题不是 Meta 功能问题，但它会导致 MainLine 基线不健康，后续 scoped apply 后难以判断失败归因。

在上述问题处理后，建议进入一个严格 path-limited 的 MainLine scoped apply 阶段，而不是整分支 merge：

1. 引入 `app/meta_analysis/**` active runtime，继续排除 `app/meta_analysis/legacy/**`。
2. 手工移植 Meta UI helper 到 MainLine 当前 `app/shared/ui` / `app/ui_style_tokens.py` 架构，禁止覆盖 shared UI。
3. 更新 Meta tests 和 3 个 Meta UI tests。
4. 小范围更新 `tests/ui/test_module_selection.py` 的 Meta page key 断言。
5. 如需要 `app/shell/main_window.py` Bioinformatics fallback，只在 MainLine 当前 shared UI helper 结构中做最小补丁。
6. 不修改 Bioinformatics、`CODEX.md`、AI Gateway、Vocabulary、packaging 或 docs archive / handoff / UI governance 文件。

## 14. 下一阶段建议

建议下一阶段拆为两步：

1. 先修复 / 恢复 MainLine AI Gateway audit 文档测试基线：
   - 目标是让 `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q` 在 MainLine 当前 HEAD 通过。
   - 不应混入 Meta scoped apply。
2. 再执行 MainLine Meta scoped apply：
   - 以 Integration `f66be3d` 为候选来源。
   - 严格 path-limited 引入 Meta active runtime / tests / docs。
   - 完成后运行 `tests/meta_analysis`、`tests/ui`、`tests/shared`、`tests/bioinformatics`、smoke test、`git diff --check`，必要时运行 `python3 scripts/run_tests.py`。
