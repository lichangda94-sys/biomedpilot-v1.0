# Integration Package Readiness Audit - 2026-05-13

## 1. Scope

本报告由 `Integration` worktree 生成，用于判断 BioMedPilot v1.0 各模块当前开发成果是否适合进入第一次 Integration Preview 桌面测试包。

本阶段仅做审计和报告：

- 未进入 ReleaseBuild 打包。
- 未覆盖 `/Users/changdali/Desktop/BioMedPilot Dev.app`。
- 未覆盖旧正式 `BioMedPilot.app`。
- 未修改 MainLine、Bioinformatics、Meta、LabTools、UIShell 或 ReleaseBuild 工作树。
- 未执行 wholesale merge。
- 未 push remote。
- 未提交任何业务代码。

审计基准：

- MainLine 稳定入口基线：`stable/mainline` at `fd0b9a0`
- Integration 当前工作树：`dev/integration` at `f66be3d`
- 当前日期：2026-05-13

判定标签：

- `YES`：可进入候选集成，但仍需 scoped integration，不允许整分支合并。
- `YES-DOCS-ONLY`：仅文档、报告、审计结论可进入；runtime 功能不得作为正式能力开放。
- `NO-BLOCKED`：存在启动、测试、边界或语义阻塞，不能进入。
- `NEEDS-SCOPED-FIX`：需要先做最小 scoped fix 或 scoped integration validation 后再进入。

## 2. Inputs Checked

| Object | Checked evidence |
| --- | --- |
| MainLine stable baseline | `git status --short --branch`; `git rev-parse --short HEAD`; `git log --oneline`; latest MainLine docs and commit stats |
| Bioinformatics dev branch | current branch/head/status; `stable/mainline...dev/bioinformatics`; latest handoff; B5 report; commit stats |
| Meta dev branch | current branch/head/status; `stable/mainline...dev/meta-analysis`; handoff; M9 audit; M10 report; commit stats |
| LabTools dev branch | current branch/head/status; `stable/mainline...dev/labtools`; current handoff; L6A.1 report; commit stats |
| UIShell dev branch | current branch/head/status; `stable/mainline...dev/ui-shell`; handoff; smoke and targeted UI test rerun |
| ReleaseBuild | current branch/head/status at `d2bc191`; handoff and package metadata audit; used only as packaging capability reference |
| Project control docs | `01_ProjectControl/current_handoff_20260513.md`; `01_ProjectControl/Global_Development_Manual.md` |

## 3. Current Branch / HEAD / Dirty Status

| Worktree | Branch | HEAD | Dirty status | Audit note |
| --- | --- | ---: | --- | --- |
| MainLine | `stable/mainline` | `fd0b9a0` | clean | Current stable desktop baseline; includes `Fix desktop Bioinformatics recognition readiness gate`. |
| Integration | `dev/integration` | `f66be3d` | clean before this report | Current Integration baseline has staged Meta validation, but is now behind current MainLine. |
| Bioinformatics | `dev/bioinformatics` | `6745d7c` | dirty: untracked `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md` | HEAD advanced beyond handoff to a standardization readiness gate fix. |
| Meta | `dev/meta-analysis` | `24f43c7` | dirty: untracked `app/meta_analysis/models/effect_size_normalization.py`; untracked `docs/meta_dev_reports/Meta_handoff_report_20260513.md` | Untracked runtime code is a release/integration blocker for that file; M9/M10 committed evidence remains usable for docs/status. |
| LabTools | `dev/labtools` | `63e7b5e` | clean | L6A.1 ROI export hardening committed and tested. |
| UIShell | `dev/ui-shell` | `391c882` | dirty: untracked `docs/UIShell_handoff_report_20260513.md` | Current branch is stale relative to MainLine and MainWindow targeted tests fail. |
| ReleaseBuild | `dev/release-internal-test` | `d2bc191` | dirty: untracked `docs/release/ReleaseBuild_handoff_report_20260513.md` | Packaging capability reference only; not a business maturity source. |

## 4. Ahead / Behind And Difference Summary

Counts are from `git rev-list --left-right --count stable/mainline...<branch>`. The first number is MainLine commits not in the module branch; the second number is module commits not in MainLine.

| Target branch | MainLine-only | Branch-only | Difference summary versus current MainLine |
| --- | ---: | ---: | --- |
| `dev/integration` | 30 | 6 | Integration contains staged Meta validation reports and scoped integration commits, but lacks current MainLine commits including `fd0b9a0`. Do not package directly from current Integration without refresh. |
| `dev/bioinformatics` | 88 | 13 | Large divergence: 678 changed files; includes B2/B3/B5 result/report loop work, but also legacy Meta material and broad historical differences. Whole-branch merge is not acceptable. |
| `dev/meta-analysis` | 46 | 21 | Large divergence: 665 changed files; contains active Meta M4-M10 work and legacy-isolated material. Whole-branch merge is not acceptable; runtime stats remain testing-level. |
| `dev/labtools` | 30 | 16 | Large divergence: 555 changed files; LabTools additions are coherent, but branch also differs from MainLine across Meta/shared areas. Needs scoped apply of LabTools-only surface. |
| `dev/ui-shell` | 30 | 1 | Functionally stale branch: only one branch-only commit, but misses 30 MainLine commits and deletes many current MainLine Meta/shared assets. Not a valid integration source. |
| `dev/release-internal-test` | 30 | 7 | Small source diff against MainLine: 10 files changed, mostly packaging metadata/tests and ReleaseBuild-local docs. Packaging capable, but not business maturity evidence. |

## 5. Module Readiness Decisions

| Module | Latest report evidence | Decision | Integration Preview suitability |
| --- | --- | --- | --- |
| MainLine baseline | `MainLine` HEAD `fd0b9a0`; MainLine docs and logs | `YES` as baseline | Use as stable source baseline for Integration Preview scoped work. Do not back-merge broad module branches into it. |
| Bioinformatics | `Bioinformatics/docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`; `Bioinformatics/docs/bioinformatics/stage_B5_result_report_loop_stabilization_20260513.md` | `NEEDS-SCOPED-FIX` | Result/report loop can enter only through scoped integration after minimal compatibility validation. Do not whole-branch merge. |
| Meta | `Meta/docs/meta_dev_reports/Meta_handoff_report_20260513.md`; `Meta/docs/meta_dev_reports/Meta_M9_statistical_executor_preintegration_audit_20260513.md`; `Meta/docs/meta_dev_reports/Meta_M10_statistical_result_state_gating_report_20260513.md` | `YES-DOCS-ONLY` | M9/M10 audit/status can enter docs. Runtime statistical executor or formal analysis output must not be exposed as formal capability. |
| LabTools | `LabTools/docs/labtools_current_handoff.md`; `LabTools/docs/stage_labtools_l6a1_image_roi_export_hardening_report.md` | `YES` | Best first scoped module candidate, limited to LabTools L6A.1 calculators/recipe/image ROI export surfaces. Must be scoped into MainLine/Integration, not merged wholesale. |
| UIShell | `UIShell/docs/UIShell_handoff_report_20260513.md`; targeted test rerun in this audit | `NO-BLOCKED` | Not suitable as source. MainWindow cannot instantiate in targeted tests; branch is stale and missing current MainLine UI/shared/Meta assets. |
| ReleaseBuild | `ReleaseBuild/docs/release/ReleaseBuild_handoff_report_20260513.md`; `ReleaseBuild/docs/release/Integration_readiness_audit_mainline_ui_package_20260513.md`; HEAD `d2bc191` | packaging-ready reference only | Do not use for business maturity judgment. ReleaseBuild may package only after Integration-approved source passes audit. |

## 6. Blockers And Required Scoped Work

### Bioinformatics - `NEEDS-SCOPED-FIX`

Current usable scope:

- B5 result/report loop stabilization.
- Imported DEG browsing and report candidate handling.
- Report wording hardening for `preflight-only`, `imported result`, `testing-level`, `dry-run/configured-not-run`, and current absence of real computed result.
- Current HEAD `6745d7c` adds Bioinformatics standardization readiness gate fix.

Blockers:

- Branch has 88 MainLine-only / 13 branch-only divergence and broad historical changes; whole-branch merge would reintroduce unrelated or legacy surfaces.
- No real DEG executor exists; B2/B5 are preflight/import/report-loop work only.
- Result index remains a mixed compatibility index; formal executor schema still needs a separate audit.
- Current handoff is untracked and older than HEAD; Integration must record current HEAD facts directly.

Required scoped work before Preview inclusion:

1. Create a Bioinformatics scoped integration plan limited to B5 result/report loop and `6745d7c` readiness gate behavior.
2. Apply only the minimal files needed for result/report loop and readiness compatibility.
3. Preserve MainLine current desktop shell and Meta active runtime.
4. Re-run Bioinformatics and UI tests listed below before package approval.

### Meta - `YES-DOCS-ONLY`

Current usable scope:

- M9 statistical executor pre-integration audit.
- M10 statistical result-state gating report and committed guard code, as evidence of current testing-level boundaries.
- Existing MainLine active Meta runtime remains the runtime baseline; Meta dev branch itself is not a package source.

Blockers:

- Untracked runtime file exists: `app/meta_analysis/models/effect_size_normalization.py`. It is not integration-approved and must not silently enter a package.
- M9 explicitly did not implement a real statistical executor.
- M10 adds state gating but still does not upgrade any output to production, clinical, submission-grade, publication-ready, or formal evidence status.
- Existing testing helpers, forest/funnel output, draft reports, PubMed candidate preview, full-text parsing, AI suggestions, and statistical runs remain Developer Preview / testing-level.
- Whole-branch merge would bring broad divergence and legacy-isolated material.

Allowed for Preview:

- Documentation and user-facing limitation notes.
- Testing-level status labels and guard language.

Not allowed for Preview:

- Formal statistical executor claim.
- Formal pooled effect / heterogeneity / p-value / report-ready output.
- Any automatic screening, extraction, AI decision, or final report claim.

### LabTools - `YES`

Current usable scope:

- L6A.1 image ROI export hardening.
- Calculators, local recipe library, manual source drafts, manual ROI fluorescence and wound threshold estimation.
- Export package schema: `labtools_roi_export_manifest.v1`.

Strengths:

- Worktree clean.
- L6A.1 report records `tests/labtools` 130 passed, `tests/ui` 139 passed, focused shell tests 18 passed, source smoke passed, `compileall app/labtools` passed, and `git diff --check` passed.
- Semantics are correctly constrained to manual-review, testing-level measurement assistance.

Blockers / constraints:

- Still requires scoped integration because the branch differs from MainLine across non-LabTools areas.
- Must not pull LabTools branch deletions/differences in Meta/shared/Bioinformatics.
- Must not enable network, AI Gateway, ImageJ/Fiji, OpenCV/scikit-image, automatic ROI, automatic cell counting, WB/gel densitometry, or batch analysis.

Required scoped work before package:

1. Apply only `app/labtools/**`, LabTools UI entry wiring, LabTools tests, and LabTools docs needed for L6A.1.
2. Keep generated export files user-confirmed only; no automatic write of user images or experiment data.
3. Preserve MainLine Bioinformatics and Meta behavior.

### UIShell - `NO-BLOCKED`

Current evidence:

- `python3 -m app.main --smoke-test` passed at `git_head=391c882`.
- Targeted rerun `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_sidebar.py tests/ui/test_module_selection.py -q` produced `3 failed, 11 passed`.

Blocking failures:

- `MainWindow()` fails at `app/shell/main_window.py:51`.
- Error: `TypeError: BioinformaticsWorkspaceWidget() takes no arguments`.
- The handoff explains the root issue: `app.bioinformatics.workflow_pages` import misses `app.bioinformatics.deg_executor_preflight`, causing fallback workspace class usage.

Additional blockers:

- `dev/ui-shell` is 30 commits behind MainLine and only 1 commit ahead.
- Diff versus MainLine deletes many current Meta/shared vocabulary/shared UI assets.
- It is not a valid Integration Preview source until rebased or rebuilt on current MainLine and UI tests pass.

### ReleaseBuild - Packaging Reference Only

Current evidence:

- ReleaseBuild HEAD `d2bc191` aligns dev package build metadata.
- Packaging metadata tests were updated in ReleaseBuild.
- Existing release audit records package command and packaged smoke capability from a previous stage.

Boundary:

- ReleaseBuild may package only Integration-approved source or MainLine stable source.
- ReleaseBuild must not decide whether Bioinformatics, Meta, LabTools, or UIShell are mature enough.
- In this audit stage, no packaging command was run and no desktop app was overwritten.

## 7. Recommended First Integration Preview Contents

Recommended content after scoped integration validation, not immediately from the current Integration HEAD:

1. MainLine `stable/mainline` at `fd0b9a0` as the desktop shell and stable baseline.
2. LabTools L6A.1 scoped integration: calculators, recipe MVP, manual ROI fluorescence/wound analysis, and user-confirmed ROI export package.
3. Bioinformatics B5 result/report loop only after scoped fix/integration: imported DEG browsing, safe report semantics, standardization readiness gate, and no real DEG executor claim.
4. Meta documentation/status layer only: M9/M10 limitations and testing-level result-state wording. Keep current MainLine active Meta runtime as testing-level; do not expose formal statistics.
5. ReleaseBuild packaging metadata capability after Integration source passes checks.

Not recommended for the first Integration Preview:

- UIShell `dev/ui-shell` branch.
- Whole Bioinformatics branch merge.
- Whole Meta branch merge.
- Whole LabTools branch merge.
- Meta untracked `effect_size_normalization.py`.
- Any real Bioinformatics DEG executor.
- Any formal Meta statistical executor.
- Any production-ready, clinical-grade, submission-grade, or publication-ready claim.
- Any package generated directly from a single module branch.

## 8. Required Next-Stage Tests Before Packaging

For the next scoped integration stage, run these before allowing ReleaseBuild to package:

| Scope | Required commands |
| --- | --- |
| Integration baseline | `git diff --check`; `python3 -m app.main --smoke-test` |
| Bioinformatics scoped result/report loop | `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/bioinformatics -q`; `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q`; targeted report builder/imported DEG tests |
| LabTools scoped apply | `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/labtools -q`; `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_labtools_image_export_ui.py -q`; `python3 -m compileall app/labtools` |
| Shell/module entry after scoped apply | `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_module_selection.py tests/ui/test_sidebar.py tests/test_unified_entry.py -q` |
| Meta boundary guard if Meta docs/status wording changes | `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/meta_analysis -q`; `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_meta_analysis_workflow_pages.py -q` |
| Package-source final gate | `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q`; relevant `tests/shared` and `tests/test_package_app.py` only after Integration source is approved |

Full `pytest` was not run in this audit stage because this stage only adds a documentation report and the user explicitly did not request full business-test execution.

## 9. Packaging Recommendation

Do not generate `BioMedPilot Integration Preview.app` immediately from current `dev/integration`.

Recommended next step:

1. Perform scoped integration for LabTools L6A.1 first.
2. Separately perform Bioinformatics B5 result/report loop scoped integration or scoped fix.
3. Keep Meta M9/M10 as docs/status evidence only unless a later task explicitly authorizes runtime scoped apply.
4. Exclude UIShell `dev/ui-shell` until MainWindow/tests are fixed on a current MainLine base.
5. After the scoped Integration audit passes, then authorize ReleaseBuild to package the Integration-approved source.

ReleaseBuild next step is therefore gated: it may package only after Integration audit and scoped validation pass.

## 10. Verification In This Audit Stage

Commands run for this report stage:

```bash
git diff --check
```

Result before and after creating this report: passed.

```bash
python3 -m app.main --smoke-test
```

Run in `UIShell`: passed, but smoke does not instantiate `MainWindow`.

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_sidebar.py tests/ui/test_module_selection.py -q
```

Run in `UIShell`: failed with `3 failed, 11 passed`; all failures are `MainWindow()` instantiation failures caused by `BioinformaticsWorkspaceWidget() takes no arguments`.

Packaging was not run.
