# Meta Staged Integration Report

日期：2026-05-13

## 1. 本阶段目标

本阶段目标是在 `Integration` worktree 中采用 staged、可审计、可回退的方式评估并尝试引入 Meta active runtime、Meta tests、Meta docs 和必要 shared UI token 变更，避免整分支 merge `dev/meta-analysis` 带入 Bioinformatics、UI shell、`CODEX.md` 或 legacy 历史差异。

本阶段不是 MainLine 合并准备，不直接修改 MainLine，不修改 Bioinformatics，不 push，不打包发布，不删除 legacy。

## 2. MainLine / Meta / Integration 分支和 git head

| Worktree | 分支 | Git head | 状态 |
| --- | --- | --- | --- |
| `/Users/changdali/Developer/biomedpilot v1.0/MainLine` | `stable/mainline` | `8fa20acd3202c7da2d34ac143e4f335b924a46ee` | clean |
| `/Users/changdali/Developer/biomedpilot v1.0/Meta` | `dev/meta-analysis` | `00765f49a8e37573ccf5fb18198ac36a2f105dea` | clean |
| `/Users/changdali/Developer/biomedpilot v1.0/Integration` | `dev/integration` | `80351d49f1adab0aabde52c62ba7c487e6d997dc` | 起始 clean；本阶段仅新增本报告 |

前置已读：

- `/Users/changdali/Developer/biomedpilot v1.0/README_总说明.md`
- `/Users/changdali/Developer/biomedpilot v1.0/01_ProjectControl/Global_Development_Manual.md`
- `MainLine/docs/architecture/BioMedPilot_v1_overall_architecture_20260513.md`
- `MainLine/docs/architecture/BioMedPilot_v1_code_structure_20260513.md`
- `Integration/docs/integration/meta_integration_merge_validation_20260513.md`
- Meta 审计报告和 Meta UI 主题统一报告

## 3. 为什么不能整分支 merge

上一阶段已验证整分支 merge 失败：

```bash
git merge --no-ff --no-commit dev/meta-analysis
```

失败原因包括：

- `CODEX.md` add/add 冲突。
- `app/meta_analysis/workspace.py`、`app/meta_analysis/project_workspace.py` content conflict。
- 多处 Meta page / service / test modify/delete 冲突。
- `tests/ui/test_module_selection.py` content conflict，属于 UI shell / module selection 语义。
- `dev/integration..dev/meta-analysis` 之间存在 Bioinformatics 文件差异，不能让 Meta 集成阶段改写 Bioinformatics。

本阶段进一步确认，整分支 diff 还会大量新增 `app/meta_analysis/legacy/` 历史内容，包括旧 UI、demo、GEO/TCGA/GTEx/Bioinformatics readiness 文件，因此不能无差别合入。

## 4. 差异分类结果

基于：

```bash
git diff --name-status HEAD dev/meta-analysis
```

分类如下：

### A. 可引入候选：Meta active runtime 文件

候选包括排除 `app/meta_analysis/legacy/**` 后的 `app/meta_analysis/` active 文件，例如：

- `app/meta_analysis/workspace.py`
- `app/meta_analysis/project_workspace.py`
- `app/meta_analysis/pages/**`
- `app/meta_analysis/services/**`
- `app/meta_analysis/models/**`
- `app/meta_analysis/search/**`
- `app/meta_analysis/stats/**`
- `app/meta_analysis/reports/**`
- `app/meta_analysis/extraction/**`
- `app/meta_analysis/quality/**`
- `app/meta_analysis/adapters/**`

统计结果：`app/meta_analysis` 非 legacy 差异约 121 个文件。

本阶段未引入这些文件，因为 active runtime legacy 依赖检查触发停止条件。

### B. 可引入候选：Meta tests

候选包括 `tests/meta_analysis/**` 和 Meta 专属 UI tests：

- `tests/meta_analysis/**`
- `tests/ui/test_meta_analysis_workflow_pages.py`
- `tests/ui/test_meta_search_stage_m2.py`
- `tests/ui/test_meta_stage_m3_dedup_workflow.py`

统计结果：Meta 分支当前 `tests/meta_analysis` 约 97 个文件。

本阶段未引入这些测试，因为部分测试明确依赖 legacy bridge，例如 `tests/meta_analysis/test_stage_6_literature_import_panel.py::test_literature_batch_import_executes_legacy_batch_service_and_returns_summary`。

### C. 可引入候选：Meta docs / reports

候选包括：

- `docs/audit/meta_mainline_merge_readiness_audit_20260513.md`
- `docs/audit/meta_ui_theme_unification_report_20260513.md`

本阶段未复制 Meta docs，以避免在阻塞状态下制造“已完成 staged integration”的误读；只新增本 Integration 阻塞报告。

### D. 需谨慎：shared UI token

`app/ui_style_tokens.py` 在 Meta 分支包含本阶段主题统一所需 token/helper：

- `COLORS["deep_navy"] = "#12324A"`
- `COLORS["teal"] = "#1BAE9F"`
- `COLORS["light_gray"] = "#F5F7F9"`
- `COLORS["white"] = "#FFFFFF"`
- `meta_workspace_stylesheet()`
- `meta_card_stylesheet()`
- `meta_error_text_style()`
- `meta_text_style()`
- `meta_title_style()`

本阶段未移植这些 shared token/helper，因为 active runtime 未被允许引入。下一阶段如获授权，应只移植 Meta UI helper，不覆盖 Integration / MainLine 当前 shell 和 Bioinformatics token 行为。

### E. 需单独审计：`tests/ui/test_module_selection.py`

该文件在 Meta 分支有差异，上一阶段整分支 merge 发生 content conflict。它属于 UI shell / module selection 语义，本阶段未修改。

下一阶段若继续 staged integration，应先审计：

- Integration 当前 module selection 逻辑。
- Meta 分支测试新增断言是否只是 Meta 入口可见性。
- 是否需要 shell 层最小适配，还是只需保留 Integration 当前基线。

### F. 禁止引入：Bioinformatics 文件

确认 `dev/integration..dev/meta-analysis` 存在 Bioinformatics 差异，包括：

- `app/bioinformatics/**`
- `tests/bioinformatics/**`

这些差异属于模块分支历史分叉，不允许由 Meta staged integration 改写。本阶段未修改 Bioinformatics。

### G. 禁止引入：`CODEX.md` 或总控文件差异

`CODEX.md` 在 Meta 分支有差异，上一阶段整分支 merge 发生 add/add 冲突。本阶段保持 Integration 侧 `CODEX.md` 不变。

### H. 暂缓：legacy 大规模历史内容、demo/mock runner、旧 UI

`app/meta_analysis/legacy/**` 在 diff 中约 334 个文件，包含旧桌面 UI、standalone Meta UI、demo projects、GEO/TCGA/GTEx/Bioinformatics readiness、旧 task runner 和旧 assets。

本阶段未引入 legacy 目录。

## 5. 哪些文件被引入

本阶段只新增：

- `docs/integration/meta_staged_integration_report_20260513.md`

未引入任何 Meta active runtime、Meta tests、shared token、Bioinformatics、UI shell 或 `CODEX.md` 改动。

## 6. 哪些文件明确没有引入

明确没有引入：

- `app/bioinformatics/**`
- `tests/bioinformatics/**`
- `CODEX.md`
- `app/shell/**`
- `tests/ui/test_module_selection.py`
- `app/ui_style_tokens.py`
- `app/meta_analysis/legacy/**`
- `app/meta_analysis/**` active runtime
- `tests/meta_analysis/**`
- `tests/ui/test_meta_analysis_workflow_pages.py`
- `tests/ui/test_meta_search_stage_m2.py`
- `tests/ui/test_meta_stage_m3_dedup_workflow.py`

## 7. Bioinformatics 是否保持不变

是。未修改 Bioinformatics 代码或测试。

已确认整分支 diff 中存在 Bioinformatics 差异，因此下一阶段仍必须显式保留 Integration 侧 Bioinformatics，不能使用整分支 merge 或整目录覆盖。

## 8. CODEX.md 是否保持不变

是。Integration 侧 `CODEX.md` 保持不变。

## 9. `tests/ui/test_module_selection.py` 如何处理

本阶段未处理。

原因：该文件是 UI shell / module selection 语义测试，上一阶段已出现 content conflict。当前任务要求该冲突必须单独审计，不能盲目解决。

建议下一阶段先做只读对比：

```bash
git diff HEAD dev/meta-analysis -- tests/ui/test_module_selection.py
```

如果 Meta 分支只是新增 Meta 入口断言，可在 Integration 当前 shell 基线上做最小测试合并；如果涉及 shell 结构分歧，应停止并请求 UI shell 方向确认。

## 10. Meta workspace / project_workspace 冲突如何处理

本阶段未处理 `app/meta_analysis/workspace.py` 或 `app/meta_analysis/project_workspace.py`。

原因：

- 上一阶段这两个文件与 Integration 当前版本发生 content conflict。
- 它们是 active Meta runtime 的入口文件。
- 继续引入前必须先解决 active runtime 对 legacy bridge 的依赖边界。

## 11. shared UI token 如何处理

本阶段未修改 `app/ui_style_tokens.py`。

Meta 分支中 UI token 修复方向本身符合主视觉，但它依赖 active Meta UI helper 的落地。由于 active runtime 本阶段未引入，shared token 暂不移植，避免产生未使用或与 Integration shell 行为未验证的 shared 改动。

## 12. legacy 是否影响 active runtime

是。检查 Meta worktree active runtime 时发现，非 legacy active 文件仍存在 transitional legacy bridge：

- `app/meta_analysis/adapters/literature_import_adapter.py` 通过 `LEGACY_ROOT = ... / "legacy"` 和 `_legacy_path()` 加载 legacy literature parser。
- `app/meta_analysis/adapters/duplicate_review_adapter.py` 通过 `_legacy_path()` 使用 legacy dedup。
- `app/meta_analysis/adapters/extraction_adapter.py` 通过 `_legacy_path()` 使用 legacy extraction。
- `app/meta_analysis/adapters/prepare_screening_adapter.py` 通过 `_legacy_path()` 使用 legacy screening。
- `app/meta_analysis/adapters/screening_adapter.py` 通过 `_legacy_path()` 使用 legacy screening。
- `app/meta_analysis/adapters/analysis_adapter.py` 通过 `_legacy_path()` 使用 legacy analysis。
- `app/meta_analysis/services/literature_batch_import_service.py` import `_legacy_path()`，并在 batch import 中调用 legacy literature batch service。
- `app/meta_analysis/services/literature_import_service.py` import `LiteratureImportAdapter, _legacy_path`，并记录 transitional bridge 元数据。

测试层也明确覆盖 legacy bridge：

- `tests/meta_analysis/test_stage_6_literature_import_panel.py::test_literature_batch_import_executes_legacy_batch_service_and_returns_summary`

这触发了本阶段用户指令中的停止条件：如果 active runtime 依赖 legacy，则停止并报告。故本阶段没有继续 staged 文件引入。

## 13. Meta UI 主题 token 是否仍符合统一主色

Meta worktree 最新提交 `00765f49a8e37573ccf5fb18198ac36a2f105dea` 中，active Meta UI token 已符合：

- deep navy：`#12324A`
- teal：`#1BAE9F`
- light gray：`#F5F7F9`
- white：`#FFFFFF`

但由于本阶段未引入 `app/ui_style_tokens.py` 和 active Meta UI，Integration 运行态尚未完成主题统一验证。

## 14. 测试结果

本阶段没有引入 runtime 或 tests，因此未运行合并后业务测试矩阵。

已运行：

| 命令 | 结果 |
| --- | --- |
| `git --git-dir="_repo.git" worktree list` | passed |
| MainLine / Meta / Integration `pwd`、`git status --short`、branch、head 检查 | passed |
| `git diff --name-status HEAD dev/meta-analysis` | passed，已分类 |
| active Meta legacy dependency scan | blocked：发现 active runtime transitional legacy bridge |
| `git diff --check` | passed |

未运行：

- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q`
- `python3 -m app.main --smoke-test`
- `python3 scripts/run_tests.py`

未运行原因：本阶段在代码引入前触发 stop-and-report 条件，继续运行合并后测试没有意义，且会给出当前 Integration 基线结果而非 staged Meta 集成结果。

## 15. 剩余风险

High:

1. Meta active runtime 仍依赖 legacy bridge，当前 staged integration 指令要求停止。
2. `app/meta_analysis/legacy/**` 体量大且包含旧 UI、demo、GEO/TCGA/GTEx/Bioinformatics readiness，不能无差别接入。
3. `dev/integration..dev/meta-analysis` 仍存在 Bioinformatics 文件差异风险。
4. `tests/ui/test_module_selection.py` 仍需 UI shell / module selection 语义审计。

Medium:

1. Meta active runtime 文件和 Integration 当前 Meta minimal surface 差异较大，`workspace.py` / `project_workspace.py` 需要专门冲突处理。
2. shared UI token 修复未进入 Integration，主题统一尚未在 Integration 运行态验证。
3. Meta tests 中已有 legacy bridge 覆盖，后续如果不引入 legacy，则需要先替换 active parser/dedup/extraction/screening/analysis 实现或明确授权过渡例外。

Low:

1. Meta worktree 自身 UI 主题修复测试已通过，但不能替代 Integration 测试。
2. 本阶段仅新增报告，没有改变 runtime 行为。

## 16. 是否建议再次进行 Integration 验证

建议先进入一个更窄的前置修复阶段，而不是马上再次做 staged integration：

`refactor(meta): retire transitional legacy bridge before integration`

可选替代方案是由人工明确批准“允许 transitional legacy literature/extraction/screening/analysis bridge 作为临时例外进入 Integration”，并同时要求 import guard 禁止 legacy UI、demo/mock runner、GEO readiness 被 active shell 调用。

## 17. 是否建议进入 MainLine 合并准备

不建议。

当前 Integration 未成功引入 Meta active runtime，且发现 active runtime legacy bridge 阻塞。应先解决或明确批准 legacy bridge 例外，再重新执行 staged Integration。
