# Meta Staged Integration Apply Report

日期：2026-05-13

## 1. 本阶段目标

本阶段在 `Integration` worktree 中重新执行 Meta staged Integration。目标是不用整分支 merge 的方式，只引入当前 Meta active runtime、Meta tests、Meta docs 和必要 shared UI token 变更，验证 Meta 是否已解除 legacy bridge 阻塞，并为后续 Integration full validation 做准备。

本阶段不是 MainLine 合并准备；未 push，未打包发布，未删除 legacy。

## 2. MainLine / Meta / Integration 分支和 git head

| Worktree | 分支 | Git head | 起始状态 |
| --- | --- | --- | --- |
| `/Users/changdali/Developer/biomedpilot v1.0/MainLine` | `stable/mainline` | `1dceec0ded869489f42a988f3ce9547af3b713fa` | clean |
| `/Users/changdali/Developer/biomedpilot v1.0/Meta` | `dev/meta-analysis` | `76f9a0ee6017ba47519c969d5a987698691d68a1` | clean |
| `/Users/changdali/Developer/biomedpilot v1.0/Integration` | `dev/integration` | `ba41dca1c2b3664312af3f93bacdbac27f3d72fa` | clean |

## 3. 为什么仍不使用整分支 merge

仍不使用 `git merge dev/meta-analysis`，原因与前两次 Integration 报告一致：

- 整分支 diff 仍包含 `CODEX.md`、Bioinformatics、Vocabulary、packaging、shared vocabulary docs 和 UI shell 历史差异。
- `app/meta_analysis/legacy/**` 仍约 334 个历史文件，包含旧 UI、demo/mock runner、GEO/TCGA/GTEx/Bioinformatics readiness 历史内容。
- `tests/ui/test_module_selection.py` 属于 UI shell / module selection 边界，不能用 Meta 分支版本覆盖 Integration 当前基线。
- 本阶段目标是 staged、可审计、可回退地引入 active Meta runtime，而不是解决所有分支历史差异。

## 4. Integration 工作区开始时是否干净

开始时 Integration 为 clean。

未发现上一次报告提到的 Vocabulary / packaging 既有 staged 或 unstaged 变更。因此本阶段没有需要绕开的已有 dirty files。

## 5. 差异分类结果

基于 `git diff --name-status HEAD dev/meta-analysis` 分类：

- A 可引入：`app/meta_analysis/**` 中排除 `legacy/**` 的 active runtime，约 122 个文件。
- B 可引入：`tests/meta_analysis/**` 中新增或修改的 active Meta tests，约 99 个文件；保留 Integration 原有 `tests/meta_analysis/test_mainline_meta_contract.py` 并更新其 active workspace 合同断言。
- C 可引入：Meta docs / audit reports 三份。
- D 谨慎引入：`app/ui_style_tokens.py`，仅手工移植 Meta active UI 所需 token/helper，未覆盖 Bioinformatics button-role 样式。
- E 单独审计：`tests/ui/test_module_selection.py`，仅更新 Meta page key 断言，保留 Integration 的 window dispose / Qt lifecycle 基线。
- F 禁止引入：`app/bioinformatics/**`、`tests/bioinformatics/**`。
- G 禁止引入：`CODEX.md`、总控文件差异。
- H 暂缓引入：`app/meta_analysis/legacy/**`、demo/mock runner、旧 UI。
- I 停止条件检查：未发现 active runtime 重新出现 `_legacy_path()` / `LEGACY_ROOT` / legacy service loader。

## 6. 实际引入文件清单

本阶段 staged 文件总数：230。

实际引入 / 修改：

- `app/meta_analysis/**` active runtime：122 个文件。
  - 重点包括 `workspace.py`、`project_workspace.py`、`workflow_pages.py`。
  - 新增 `app/meta_analysis/literature_import_core.py`。
  - 新增 active `adapters/`、`services/`、`pages/`、`models/`、`search/`、`stats/`、`quality/`、`extraction/`。
- `tests/meta_analysis/**`：99 个文件。
  - 新增 legacy bridge guard：`tests/meta_analysis/test_active_runtime_legacy_bridge_retirement.py`。
  - 新增 / 引入 Meta UI theme guard、literature import、workflow、dedup、screening、statistics、reporting 等 active tests。
  - 更新 Integration 原有 `tests/meta_analysis/test_mainline_meta_contract.py`，使其验证 active 8 步 Meta workspace，而非旧 3 页占位入口。
- `tests/ui/`：4 个文件。
  - 新增 `tests/ui/test_meta_analysis_workflow_pages.py`。
  - 新增 `tests/ui/test_meta_search_stage_m2.py`。
  - 新增 `tests/ui/test_meta_stage_m3_dedup_workflow.py`。
  - 更新 `tests/ui/test_module_selection.py` 的 Meta page key 断言。
- `app/ui_style_tokens.py`：手工移植 Meta unified token/helper。
- `app/shell/main_window.py`：最小 Integration 兼容修复。当前 Integration 的 Bioinformatics workspace fallback 可能不是 QWidget；MainWindow 现在在该情况下创建 shell 占位 QWidget，保证 shell navigation tests 可运行。未修改 Bioinformatics 业务代码。
- `docs/audit/meta_mainline_merge_readiness_audit_20260513.md`
- `docs/audit/meta_ui_theme_unification_report_20260513.md`
- `docs/audit/meta_active_runtime_legacy_bridge_retirement_report_20260513.md`
- 本报告：`docs/integration/meta_staged_integration_apply_report_20260513.md`

## 7. 明确未引入文件清单

明确未引入：

- `app/bioinformatics/**`
- `tests/bioinformatics/**`
- `CODEX.md`
- `app/meta_analysis/legacy/**`
- `app/main.py`
- `app/shared/query_intelligence/**`
- `data/medical_terms/**`
- `data/package_manifest.json`
- `scripts/package_app.py`
- `tests/shared/**` 的 Vocabulary 删除/修改差异
- `tests/test_package_app.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`
- Meta 分支对 `tests/ui/test_module_selection.py` 中删除 `_dispose_window()` 的改动

## 8. `tests/ui/test_module_selection.py` 如何处理

该文件未用 Meta 分支版本覆盖。

实际处理：

- 保留 Integration 当前 `qt_app`、`_dispose_window()` 和窗口清理模式。
- 只将 Meta workspace page key 断言从旧占位三页更新为 active workflow 的前四个关键页面：
  - `workflow_home`
  - `pico_workspace`
  - `search_strategy`
  - `literature_import`

未修改 UI shell 结构或模块选择流程。

## 9. `app/ui_style_tokens.py` / shared UI token 如何处理

未 checkout Meta 分支的完整 `app/ui_style_tokens.py`。

实际处理：

- 新增统一主色别名：
  - `deep_navy = #12324A`
  - `teal = #1BAE9F`
  - `light_gray = #F5F7F9`
  - `white = #FFFFFF`
- 将 active Meta token 收敛为：
  - `meta = #12324A`
  - `meta_accent = #1BAE9F`
  - `meta_soft = #F5F7F9`
- 新增 Meta UI helper：
  - `meta_workspace_stylesheet()`
  - `meta_card_stylesheet()`
  - `meta_error_text_style()`
  - `meta_text_style()`
  - `meta_title_style()`
- 保留 Integration 当前 Bioinformatics / shell button-role 样式，未引入 Meta 分支中删除这些样式的差异。

## 10. Meta active runtime 是否仍不依赖 legacy

是。

检查命令：

```bash
rg -n --hidden --glob '!**/.git/**' --glob '!**/__pycache__/**' "_legacy_path|LEGACY_ROOT|app/meta_analysis/legacy|meta_analysis\.legacy|legacy service loader|legacy parser|legacy normalizer" app/meta_analysis tests/meta_analysis || true
```

结果：未发现 active runtime bridge。命中仅位于 guard tests 的 forbidden-token 字面量。

`app/meta_analysis/legacy/` 未引入 Integration。

## 11. Meta UI 主题 token 是否仍统一

是。active Meta UI 使用统一主色：

- `#12324A`
- `#1BAE9F`
- `#F5F7F9`
- `#FFFFFF`

retired colors 未出现在 active Meta UI 代码中。扫描命中仅来自历史 audit 报告或 guard test 字面量。

未恢复：

- `#6B4FD8`
- `#F0EDFF`
- `#0F766E`
- `#E6FFFB`
- `#99F6E4`
- `#D8DEE9`
- `#111827`
- `#B42318`

## 12. Bioinformatics 是否保持不变

是。未修改 `app/bioinformatics/**` 或 `tests/bioinformatics/**`。

本阶段唯一与 Bioinformatics 相关的处理是 shell 兼容：`app/shell/main_window.py` 在当前 Integration Bioinformatics workspace fallback 不是 QWidget 时显示占位 QWidget，以便 shell 测试能执行。该处理不修改 Bioinformatics 业务流程，不新增 PubMed，不新增 GEO/TCGA/GTEx 行为。

## 13. 测试结果

已执行：

| 命令 | 结果 |
| --- | --- |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q` | `465 passed in 7.60s` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` | `72 passed, 87 skipped in 7.28s` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/shared -q` | `225 passed in 27.37s` |
| `python3 -m app.main --smoke-test` | passed；`git_head=ba41dca` |
| `python3 scripts/run_tests.py` | `1049 passed, 87 skipped in 48.01s` |
| `git diff --check` / `git diff --cached --check` | passed after EOF formatting cleanup |

## 14. 剩余风险

Medium:

- 本阶段是 staged apply，不是整分支 merge；仍需下一步 Integration full validation 对 MainLine 候选面进行复核。
- `app/meta_analysis/legacy/**` 未引入，MainLine 前仍需决定是否完全排除、单独归档，或以后以独立历史包方式处理。
- `app/shell/main_window.py` 的 Bioinformatics fallback QWidget 是 Integration 兼容补丁；后续应由 Bioinformatics / UI shell 阶段修复根因，即当前 `app.bioinformatics.workflow_pages` import 缺少 `app.bioinformatics.deg_executor_preflight` 时 workspace fallback 不是 QWidget。
- active Meta parser/normalizer 是 legacy bridge 退休后的最小实现，已通过当前 tests，但更多供应商导出 alias 仍是后续扩展风险。

Low:

- docs 中仍存在大量历史 GEO/TCGA/GTEx/Bioinformatics 文字；这些是历史报告，不是 active runtime。
- `legacy_decision` 等兼容字段仍在 active screening 数据结构中，但不是 runtime legacy bridge。

## 15. 是否建议进入下一步 Integration full validation

建议进入下一步 Integration full validation。

理由：

- Meta active runtime 已成功 staged 引入。
- Meta tests、UI tests、shared tests、smoke test 和 `scripts/run_tests.py` 均通过。
- Bioinformatics、CODEX、legacy、Vocabulary / packaging 历史差异未混入。
- active runtime legacy bridge 未回归。
- Meta UI theme token 仍符合统一主色。

## 16. 是否仍不建议直接进入 MainLine 合并准备

仍不建议直接进入 MainLine 合并准备。

建议先执行一次独立的 Integration full validation / MainLine merge readiness audit，重点确认：

- 当前 Integration commit 与 MainLine 的差异面。
- `app/shell/main_window.py` fallback 兼容补丁是否应保留、迁移或由 Bioinformatics/UI shell 阶段替代。
- legacy 完全排除策略。
- MainLine 合并前是否需要补充 release / packaging 侧验证。
