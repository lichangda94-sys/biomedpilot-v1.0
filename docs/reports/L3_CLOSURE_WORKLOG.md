# L3 Closure Worklog

Date: 2026-05-29

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

## Scope

This worklog initially covered Phase 0 and Phase 1. It now also records the Phase 2 Bioinformatics single-point L3 proof.

1. Freeze and record current UI baseline.
2. Map current UI pages, buttons, handlers, services, output status, and L3 blockers.

No Meta result-contract implementation was performed.

## Files Created

```text
docs/reports/UI_BASELINE_STATUS.md
docs/reports/UI_FEATURE_ENTRY_MAP.md
docs/reports/L3_CLOSURE_WORKLOG.md
docs/reports/BIOINFORMATICS_L3_UI_PATH_MAP.md
docs/reports/BIOINFORMATICS_L3_COMPLETION_REPORT.md
tests/ui/test_bioinformatics_l3_formal_deg_loop.py
```

## Files Modified In Phase 2

```text
app/bioinformatics/deg_engine/formal_runner.py
docs/reports/BIOINFORMATICS_L3_UI_PATH_MAP.md
docs/reports/BIOINFORMATICS_L3_COMPLETION_REPORT.md
docs/reports/L3_CLOSURE_WORKLOG.md
tests/bioinformatics/test_formal_controlled_deg_runner.py
tests/ui/test_bioinformatics_l3_formal_deg_loop.py
```

`formal_runner.py` changed only to preserve the user-confirmed parameter manifest in the result index after the confirmation gate passes.

## Files Intentionally Not Modified

```text
app/meta_analysis/**
app/shared/**
docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
project_storage/bioinformatics/
```

## Commands Run

| Command | Result | Use |
| --- | --- | --- |
| `sed -n '1,260p' /Users/changdali/Desktop/SOFTWARE_REMEDIATION_PLAN_UI_AND_ANALYSIS_L3.md` | Passed | Read remediation plan. |
| `sed -n '261,620p' /Users/changdali/Desktop/SOFTWARE_REMEDIATION_PLAN_UI_AND_ANALYSIS_L3.md` | Passed | Read remediation plan. |
| `sed -n '621,980p' /Users/changdali/Desktop/SOFTWARE_REMEDIATION_PLAN_UI_AND_ANALYSIS_L3.md` | Passed | Read remediation plan. |
| `git status --short && git branch --show-current && git rev-parse HEAD` | Passed | Baseline repository state. |
| `python3 -m app.main --smoke-test` | Passed | UI/app source smoke baseline. |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py tests/ui/test_meta_analysis_workflow_pages.py -q` | Passed, `131 passed` | Current Bio/Meta UI workflow baseline. |
| `rg ... app/bioinformatics/workflow_pages.py app/bioinformatics/pages app/meta_analysis/pages app/meta_analysis/workflow_pages.py` | Passed | UI page/button/handler discovery. |
| `rg ... app/bioinformatics/... app/meta_analysis/...` | Passed | Service/output chain discovery. |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_l3_formal_deg_loop.py -q` | Passed, `1 passed` | Bioinformatics controlled formal DEG single-point L3 proof. |
| repeated `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_l3_formal_deg_loop.py -q` | Passed three consecutive runs after the provenance fix | Flake guard for the report-ready gate. |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q` | Passed, `110 passed` | Existing Bioinformatics UI regression. |
| `python3 -m pytest tests/bioinformatics/test_formal_controlled_deg_runner.py tests/bioinformatics/test_formal_deg_plot_artifact.py tests/bioinformatics/test_formal_deg_report_ready.py -q` | Passed, `16 passed` | Formal DEG backend/plot/report regression. |
| `python3 -m app.main --smoke-test` | Passed | Source smoke check. |
| `git diff --check` | Passed | Whitespace/conflict marker check. |

## Discovery Notes

| Area | Finding |
| --- | --- |
| Current UI mainline | Bioinformatics and Meta UI source/tests are active and passing. |
| Bioinformatics L3 candidate | Controlled Formal DEG is the closest candidate because result index, runtime validation, review, plot artifact, and report gate exist. |
| Bioinformatics single-point proof | Controlled Formal DEG is now proven through current UI widgets from standardized project data to parameter confirmation, run, result table, CSV export, SVG plot artifact, and formal DEG section package. |
| Meta L3 candidate | Meta v2 statistics engine is the right statistics source, but figure/report services must read a canonical contract from the same run. |
| Meta blocker | Current result paths/contracts are split between `analysis/results/{run_id}_result.json` and `analysis/analysis_results.json`. |
| Legacy handling | Legacy folders were read only as context and were not promoted or merged. |

## Stage Acceptance

| Phase | Acceptance item | Status |
| --- | --- | --- |
| Phase 0 | Current branch and HEAD recorded | Passed |
| Phase 0 | UI smoke run | Passed |
| Phase 0 | Current UI files identified as protected baseline | Passed |
| Phase 0 | No old branch merge or UI replacement | Passed |
| Phase 1 | Bioinformatics UI entries mapped | Passed |
| Phase 1 | Meta Analysis UI entries mapped | Passed |
| Phase 1 | Key buttons classified by current state and L3 risk | Passed |
| Phase 1 | L3 blockers identified | Passed |
| Phase 2 | Only Bioinformatics was touched | Passed |
| Phase 2 | Controlled formal DEG current UI path was tested | Passed |
| Phase 2 | Real DEG table with p-value/FDR was generated by runner | Passed |
| Phase 2 | Result review CSV was exported from same result | Passed |
| Phase 2 | Real SVG plot artifact was generated from same result | Passed |
| Phase 2 | Formal DEG section package was generated from same result | Passed |
| Phase 2 | GSEA/survival/clinical conclusions remained disabled | Passed |

## Stop Point

This worklog stops after the Bioinformatics controlled formal DEG single-point proof. It does not proceed into Meta Analysis.

The minimum blocker remains factual and narrow:

```text
Bioinformatics controlled formal DEG has a current UI single-point L3 proof.
Bioinformatics full module should not be claimed complete.
Meta should not be claimed complete until one canonical result contract feeds statistics, forest plot, table, and report/export from the same run.
```

## Phase 3: Meta Result Contract Unification

Date: 2026-05-29

### Scope

This phase touched only the Meta Analysis result contract layer. Bioinformatics was not modified.

### Files Changed

```text
app/meta_analysis/services/meta_result_contract_adapter.py
app/meta_analysis/pages/analysis_page.py
tests/meta_analysis/test_meta_result_contract_adapter.py
docs/reports/META_RESULT_CONTRACT_MAP.md
docs/reports/META_RESULT_CONTRACT_UNIFICATION_REPORT.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Result

Meta statistics v2 now has a narrow canonical contract bridge. One real `MetaStatisticsEngineService.run_statistics()` result can drive:

- a canonical contract manifest,
- a result table artifact,
- a real forest plot PNG artifact,
- a testing-level markdown report/export artifact.

All derived artifacts preserve the same `analysis_run_id` and `source_statistics_result_hash`.

### UI Discovery

`meta_statistics_engine_state_from_project()` now exposes the canonical contract path, source statistics hash, artifact count, and artifact list for the latest v2 run. This is discovery only; it does not redesign the Meta UI and does not claim Meta L3.

### Commands Run

| Command | Result |
| --- | --- |
| `python3 -m pytest tests/meta_analysis/test_meta_result_contract_adapter.py -q` | Passed, `2 passed` |
| `python3 -m pytest tests/meta_analysis/test_meta_statistics_engine_v2.py -q` | Passed, `6 passed` |
| `python3 -m pytest tests/meta_analysis/test_analysis_core_mvp.py tests/meta_analysis/test_figure_result_table_mvp.py tests/meta_analysis/test_publication_export_reproducibility.py -q` | Passed, `15 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_meta_analysis_workflow_pages.py -q` | Passed, `21 passed` |
| `python3 -m app.main --smoke-test` | Passed, `git_head=8036e50` |
| `git diff --check` | Passed |

### Stop Point

Phase 3 stops here. Meta Analysis is not claimed L3. Phase 4 is still required to prove the current Meta UI loop end to end.

## Phase 2.5: Branch Inventory and Migration Candidate Audit

Date: 2026-05-29

### Scope

This phase was audit-only. No branch was checked out, merged, or cherry-picked. No UI code, analysis algorithm, or legacy runtime path was modified.

### Reports Added

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
```

### Findings

The local branch set contains substantial historical Bioinformatics and Meta Analysis material, but no branch is safe to merge wholesale.

Highest-value Bioinformatics sources:

- `dev/release-internal-test`
- `codex/releasebuild-formal-deg-carryover`
- `codex/mainline-survival-clinical-carryover`
- `stable/mainline`

Highest-value Meta Analysis sources:

- current `dev/bioinformatics` Meta services/pages
- `dev/meta-analysis` for OCR/fulltext/package history only
- `codex/meta-workflow-ui` and `codex/meta-analysis-refresh` as UI references only

Legacy directories remain quarantined:

- `app/bioinformatics/legacy/**`
- `app/meta_analysis/legacy/**`

### Decision

Old branches and legacy directories are material libraries only. Candidate features require a current UI entry, current contract mapping, current tests, and real output evidence before they can be marked usable.

### Commands Run

| Command | Result |
| --- | --- |
| `git status --short && git branch --show-current && git rev-parse HEAD` | Passed |
| `git branch --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname` | Passed |
| `git branch -r --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname` | Passed; no remote branches listed |
| `git diff --name-status HEAD..<branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics scripts` | Passed for sampled relevant branches |
| `git log --oneline --max-count=8 <branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs scripts` | Passed for sampled relevant branches |
| `rg --files app \| rg '(^\|/)legacy(/\|_)|legacy'` | Passed |
| `find app/bioinformatics/legacy app/meta_analysis/legacy -maxdepth 2 -type d` | Passed |

### Stop Point

Stop after audit documents. No migration execution should begin until the next explicit instruction selects one candidate and one current UI path.

## Phase 2.5 Refresh: Full Branch Inventory and Migration Candidate Audit

Date: 2026-06-05

### Scope

This refresh was audit-only. It followed `../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` and `../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md`.

No old branch was checked out, merged, or cherry-picked. No current UI, analysis algorithm, result runner, report/export path, or legacy runtime path was modified. The current UI remains the only mainline, and old branches plus `legacy/` directories remain material libraries only.

### Baseline

```text
workspace: /Users/changdali/Developer/biomedpilot v1.0/Bioinformatics
branch: dev/bioinformatics
HEAD: e3157fb2fb91b03174975c5774234c03970dd4aa
subject: show standard input manifests in results browser
```

The worktree already had unrelated non-report modifications before this refresh:

```text
 M app/analysis_runtime/package_catalog.py
 M app/bioinformatics/workflow_pages.py
 M docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md
 M docs/R_ANALYSIS_REMEDIATION_PLAN.md
 M tests/test_analysis_runtime_task_bridge.py
 M tests/ui/test_bioinformatics_workflow_pages.py
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

Those files were preserved and were not treated as Phase 2.5 outputs.

### Reports Refreshed

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,220p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,220p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short --branch` | Passed |
| `git branch --show-current` | Passed, `dev/bioinformatics` |
| `git rev-parse HEAD` | Passed, `e3157fb2fb91b03174975c5774234c03970dd4aa` |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' refs/heads refs/remotes` | Passed |
| `find app/bioinformatics app/meta_analysis archive/legacy_sources -path '*legacy*' -type f \| wc -l` | Passed, 924 files |
| `find app/bioinformatics app/meta_analysis archive/legacy_sources -path '*legacy*' -type d` | Passed |
| `git diff --shortstat HEAD..<branch> -- ...` | Passed for sampled high-relevance branches |
| `git ls-tree -r --name-only <branch> -- ...` | Passed for `dev/release-internal-test` and `dev/meta-analysis` |
| `rg --files ...` and `rg -n ... app/bioinformatics app/meta_analysis tests/ui` | Passed; used for current UI/service/test inventory |

No functional tests were run because this was a read-only branch/legacy inventory. Running current tests would not prove old branch runtime availability.

### Findings

The current branch set still contains rich historical Bioinformatics, Meta Analysis, UI shell, plot, report/export, testing, and helper material. Whole-branch migration remains unsafe because high-relevance branches diverge by hundreds to thousands of files.

`app/bioinformatics/legacy/**`, `app/meta_analysis/legacy/**`, and `archive/legacy_sources/**` together contain 924 legacy/archive files. These include old standalone apps, old task runners, old analysis/profile stores, static UI assets, docs, tests, scripts, and archived mirrors. None are current functionality solely by being present.

Current implementation evidence is strongest for current Bioinformatics controlled DEG/standard package surfaces and current Meta v2 testing-level contract/artifact paths. Enrichment, survival/Cox, report/export, OCR/fulltext, risk/nomogram, and UI shell material remain gated candidates unless a later phase proves one selected current UI path with real output evidence.

### Stop Point

Stop after this audit refresh. Do not begin migration, development, branch merge, cherry-pick, UI replacement, legacy code adaptation, or analysis algorithm changes until the next explicit instruction selects one candidate and one current UI path.

## Phase 2.5 Refresh: Full Branch Inventory and Migration Candidate Audit

Date: 2026-06-04

### Scope

This refresh repeated the Phase 2.5 inventory against the current `dev/bioinformatics` branch at `b77805c242d4f1a47a4cca20fcf21fb3ac4c6e15`.

This was audit-only:

- No branch was checked out.
- No branch was merged.
- No cherry-pick was performed.
- No UI code was changed.
- No analysis algorithm was changed.
- No legacy code was migrated.

### Pre-existing Dirty Worktree

The following pre-existing files were preserved and excluded from Phase 2.5 completion claims:

```text
 M analysis/modules/univariate/module.json
 M analysis/registry/analysis_modules.json
 M analysis/runners/run_module.R
 M docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md
 M docs/R_ANALYSIS_ARCHITECTURE.md
 M tests/test_analysis_runtime_task_bridge.py
 M tests/test_r_analysis_architecture_contract.py
?? analysis/fixtures/inputs/univariate/lite_clinical.tsv
?? analysis/fixtures/inputs/univariate/module_input_lite.json
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Commands Run

| Command | Result |
| --- | --- |
| `git status --short` | Passed; pre-existing dirty files recorded |
| `git branch --all --verbose --no-abbrev` | Passed; local branch inventory refreshed |
| `git rev-parse HEAD` | Passed; current HEAD `b77805c242d4f1a47a4cca20fcf21fb3ac4c6e15` |
| `find .. -name 'CODEX_UI_BRANCH_MIGRATION_GUIDE.md' -o -name 'CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md' ...` | Passed; required governance docs found |
| `sed -n '1,260p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed; migration rules read |
| `sed -n '1,260p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed; real-loop rules read |
| `git ls-tree -r --name-only <branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs scripts` | Passed via read-only branch inventory script |
| `git diff --name-status HEAD..<branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/bioinformatics docs/reports scripts` | Passed for sampled high-relevance branches |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive -maxdepth 4 -type f` | Passed; legacy inventory refreshed |
| `rg -n "QPushButton\|setText\|plot\|report\|DEG\|ORA\|GSEA\|survival\|Cox\|Meta" app/bioinformatics app/meta_analysis -g '*.py'` | Passed; current and legacy UI/action surfaces sampled |

### Finding Refresh

The earlier Phase 2.5 conclusion still holds: old branches and legacy directories are material libraries only. The current refresh adds one important boundary:

```text
Current standard analysis runtime mock/lite worker scaffold is current code,
but it is not full Bio/Meta L3 completion and must not be used to claim
real production R/Bioc analysis until a selected module proves that full loop.
```

### Stop Point

Stop after audit documents. The next phase must select one candidate feature and one current UI path before any migration or implementation begins.

## Phase 4: Meta Analysis Current UI Single-Point L3 Proof

Date: 2026-05-29

### Scope

This phase proves one current Meta Analysis UI L3 loop from confirmed analysis plan to v2 statistics run, canonical contract, result table, real forest plot, and testing-level report/export artifact.

No Bioinformatics code was modified. No generic Analysis Runner was created. No Meta statistics rewrite, Meta UI redesign, branch merge, cherry-pick, legacy workbench migration, OCR migration, or fulltext migration was performed.

### Files Changed

```text
app/meta_analysis/pages/analysis_page.py
tests/meta_analysis/test_meta_statistics_engine_v2.py
tests/ui/test_meta_analysis_l3_loop.py
docs/reports/META_L3_UI_PATH_MAP.md
docs/reports/META_L3_COMPLETION_REPORT.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Result

The current Meta Analysis UI now has a focused Phase 4 L3 proof:

- `生成分析计划草稿` creates the analysis plan draft from current Meta services.
- `确认分析计划` writes a locked confirmed analysis plan.
- `运行统计分析` triggers a real v2 statistics run from the confirmed plan.
- `生成 canonical result artifacts` generates the canonical contract, result table CSV, real forest plot PNG, and testing-level markdown report/export from the same v2 run.

All canonical artifacts preserve the same `analysis_run_id` and `source_statistics_result_hash`.

The report/export artifact remains Developer Preview / testing-level and explicitly does not generate medical, clinical, diagnostic, treatment, or production-grade conclusions.

### Commands Run

| Command | Result |
| --- | --- |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_meta_analysis_l3_loop.py -q` | Passed, `1 passed` |
| `python3 -m pytest tests/meta_analysis/test_meta_statistics_engine_v2.py::test_statistics_page_state_exposes_confirmed_plan_guardrails tests/meta_analysis/test_meta_result_contract_adapter.py -q` | Passed, `3 passed` |
| `python3 -m app.main --smoke-test` | Passed, `git_head=7cd526a` |
| `git diff --check` | Passed |
| `python3 -m pytest tests/meta_analysis/test_meta_result_contract_adapter.py -q` | Passed, `2 passed` |
| `python3 -m pytest tests/meta_analysis/test_meta_statistics_engine_v2.py -q` | Passed, `6 passed` |
| `python3 -m pytest tests/meta_analysis/test_analysis_core_mvp.py tests/meta_analysis/test_figure_result_table_mvp.py tests/meta_analysis/test_publication_export_reproducibility.py -q` | Passed, `15 passed` |
| `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_meta_analysis_workflow_pages.py tests/ui/test_meta_analysis_l3_loop.py -q` | Passed, `22 passed` |

### Stop Point

Phase 4 stops after the current Meta Analysis UI single-point L3 proof. It does not start old feature migration, OCR/fulltext work, full module completion, or production/clinical claims.

## Phase 2.5 Refresh: Full Branch Inventory and Migration Candidate Audit

Date: 2026-06-04

### Scope

This refresh is audit-only. No branch was checked out, merged, or cherry-picked. No UI code, analysis algorithm, legacy runtime path, or current analysis task implementation was changed.

### Current Baseline

```text
branch: dev/bioinformatics
HEAD: 4e699cf961e97306e7ab3c4628c3fc9d05d54967
subject: add analysis runtime mock task bridge
```

The worktree already contained unrelated changes before this Phase 2.5 refresh:

```text
 M analysis/registry/analysis_modules.json
?? analysis/modules/
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

These files were preserved and were not treated as Phase 2.5 migration work.

### Reports Refreshed

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Findings

The branch inventory now includes the newer current-line commits through the analysis runtime mock bridge and the newer UI/integration branches. The highest-value historical sources remain candidate libraries only:

- `dev/release-internal-test`
- `codex/releasebuild-formal-deg-carryover`
- `codex/mainline-survival-clinical-carryover`
- `dev/meta-analysis`
- `dev/ui-shell` and related `integration/*ui*` branches for design material only

Legacy directories remain quarantined:

- `app/bioinformatics/legacy/**`
- `app/meta_analysis/legacy/**`
- `archive/legacy_sources/**`

### Decision

No old branch is safe to merge wholesale. Any future migration must select one candidate feature and one current UI path, then use `adapter` or `rewrite` against the current contracts. Mock, placeholder, no-op, fake preflight, testing-level export, and branch-only artifacts remain excluded from current completion claims.

### Commands Run

| Command | Result |
| --- | --- |
| `git status --short && git branch --show-current && git rev-parse HEAD` | Passed |
| `git branch --all --format='%(refname:short)'` | Passed |
| `git branch --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname` | Passed |
| `git log --oneline --decorate --max-count=30 -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts app/analysis_runtime analysis` | Passed |
| `git ls-tree -r --name-only <branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs scripts` | Passed for sampled high-relevance branches |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive archive/legacy_sources -maxdepth 3 -type f` | Passed |
| `find app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui -path '*/__pycache__' -prune -o -type f -print` | Passed |
| `rg -n "QPushButton\|report\|plot\|DEG\|ORA\|GSEA\|survival\|Cox\|Meta" app/bioinformatics app/meta_analysis -g '*.py'` | Passed |

### Stop Point

Stop after audit documents. Do not begin migration, branch convergence, UI replacement, or algorithm work until the next explicit instruction selects a candidate.

## Phase 2.5 Refresh: Full Branch Inventory and Migration Candidate Audit

Date: 2026-06-04

### Scope

This refresh updated the branch/legacy inventory against current `dev/bioinformatics` at `0aa6793f460f79a78036c352f918a5acfc7a522b`.

This was audit-only:

- No branch was checked out.
- No branch was merged.
- No cherry-pick was performed.
- No UI code was changed.
- No analysis algorithm was changed.
- No legacy code was migrated.
- No mock, placeholder, or testing-level output was promoted to completed functionality.

### Current Baseline

```text
branch: dev/bioinformatics
HEAD: 0aa6793f460f79a78036c352f918a5acfc7a522b
subject: add enrichment standard result package sidecar
```

Pre-existing unrelated untracked files were preserved:

```text
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

### Reports Refreshed

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Findings

The current line has advanced since the previous Phase 2.5 refresh. It now includes a standard analysis runtime scaffold, lite workers for enrichment/survival/univariate/multivariate/immune infiltration, and an enrichment standard result package sidecar. These are current-branch materials, not old-branch migrations.

The boundary remains unchanged:

```text
Old branches and legacy directories are material libraries only.
Current UI is the only mainline.
No branch-only or legacy-only feature is current-available without a current UI path,
current contract mapping, current tests, and real output evidence.
```

Highest-value candidate libraries remain:

- `dev/release-internal-test`
- `codex/releasebuild-formal-deg-carryover`
- `codex/mainline-survival-clinical-carryover`
- `dev/meta-analysis`
- `dev/ui-shell` and integration UI shell branches as design references only

Quarantined legacy directories remain:

- `app/bioinformatics/legacy/**`
- `app/meta_analysis/legacy/**`
- `archive/legacy_sources/**`

### Commands Run

| Command | Result |
| --- | --- |
| `git status --short` | Passed; only pre-existing untracked handoff/project_storage items present |
| `git branch --all --verbose --no-abbrev` | Passed |
| `git for-each-ref --format='%(refname:short)\|%(objectname)\|%(committerdate:short)\|%(subject)' refs/heads refs/remotes` | Passed |
| `git rev-parse HEAD` | Passed; `0aa6793f460f79a78036c352f918a5acfc7a522b` |
| `git log --oneline --decorate --max-count=40 -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts app/analysis_runtime analysis` | Passed |
| `find analysis -maxdepth 4 -type f` | Passed |
| `find app/analysis_runtime -maxdepth 3 -type f` | Passed |
| `find app/bioinformatics -maxdepth 3 -type f ...` | Passed |
| `find app/meta_analysis -maxdepth 3 -type f ...` | Passed |
| `git diff --name-status HEAD..<branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/bioinformatics docs/reports docs/ui scripts analysis app/analysis_runtime` | Passed for sampled high-relevance branches |
| `rg --files \| rg '(^\|/)(legacy\|Legacy\|old\|archive\|deprecated)(/\|$)'` | Passed |

No tests were run because this phase was audit-only and made documentation changes only.

### Stop Point

Stop after audit documents. Do not begin migration, branch convergence, UI replacement, or algorithm work until the next explicit instruction selects one candidate feature and one current UI path.

## Phase 2.5 Refresh: Full Branch Inventory and Migration Candidate Audit

Date: 2026-06-04

### Scope

This refresh updated the Phase 2.5 branch inventory against the current `dev/bioinformatics` HEAD:

```text
3509f627a343c0e4290b0e1d86b0a5287462c7f3
```

The task was audit-only. No old branch was checked out, merged, cherry-picked, or used to modify current UI or analysis algorithms. Legacy directories and old branches remain material libraries only.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Preserved Pre-existing Worktree State

The audit observed existing unrelated worktree changes and left them untouched:

```text
 M app/bioinformatics/deg_engine/multifactor_r_runner.py
 M tests/bioinformatics/test_multifactor_deg_deseq2_runner.py
 M tests/bioinformatics/test_multifactor_deg_edger_runner.py
 M tests/bioinformatics/test_multifactor_deg_limma_runner.py
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

### Commands Run

| Command | Result |
| --- | --- |
| `git status --short --branch` | Passed; confirmed current branch and unrelated dirty files |
| `git branch --all --verbose --no-abbrev` | Passed; enumerated local branch refs and linked worktree markers |
| `git rev-parse HEAD` | Passed; current HEAD `3509f627a343c0e4290b0e1d86b0a5287462c7f3` |
| `rg --files docs/reports app tests \| sort` | Passed; inventoried current report/code/test surfaces |
| `sed -n ... docs/reports/*.md` | Passed; reviewed existing Phase 2.5 reports |
| `find app/bioinformatics/legacy app/meta_analysis/legacy -maxdepth 3 -type f \| sort` | Passed; inventoried legacy Bio/Meta files |
| `git log --oneline --decorate --max-count=35 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed; reviewed current-line feature history |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' refs/heads --sort=refname` | Passed; recorded branch tips |
| `git diff --name-status HEAD..<branch> -- ...` | Passed for selected high-relevance branches; no checkout or merge was performed |

### Findings

Current Bioinformatics and Meta Analysis already contain substantial non-legacy implementations and tests. Historical branches still contain useful material for UI design, enrichment/R adapters, report/rendering policy, survival/risk candidates, OCR/fulltext, and older shell work. None of that branch-only material is current availability evidence.

Legacy directories remain quarantined:

```text
app/bioinformatics/legacy/**
app/meta_analysis/legacy/**
```

### Decision

No migration candidate is approved for direct carry-over. Future work must select one candidate and one current UI entry, then adapt or rewrite against current contracts with real output proof. Mock, placeholder, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

### Stop Point

Stop after the Phase 2.5 audit refresh. Do not proceed into development, branch merge, UI replacement, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `9436f03`

Date: 2026-06-04

### Scope

This refresh updated the branch inventory reports against the current `dev/bioinformatics` HEAD:

```text
9436f03aa0ea3d926f44e3aceef5320bfb0e2781
```

The task remained audit-only. No old branch was checked out, merged, cherry-picked, or used to modify the current UI or analysis algorithms. Legacy directories and old branches remain material libraries only.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Current Worktree State

The refresh observed and preserved unrelated pre-existing untracked files:

```text
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

### Commands Run

| Command | Result |
| --- | --- |
| `git status --short --branch` | Passed; confirmed current branch and unrelated untracked files |
| `git branch --all --verbose --no-abbrev` | Passed; enumerated local branch refs and linked worktree markers |
| `git rev-parse HEAD` | Passed; current HEAD `9436f03aa0ea3d926f44e3aceef5320bfb0e2781` |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' refs/heads --sort=refname` | Passed; recorded branch tips |
| `git log --oneline --decorate --max-count=60 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed; reviewed current-line feature history |
| `find analysis -maxdepth 4 -type f \| sort` | Passed; inventoried standard analysis runtime files |
| `find app/analysis_runtime -maxdepth 3 -type f \| sort` | Passed; inventoried analysis runtime bridge files |
| `find app/bioinformatics app/meta_analysis -maxdepth 3 -type f \| sort` | Passed; inventoried current Bio/Meta feature files |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive -maxdepth 4 -type f \| sort` | Passed; inventoried legacy/archive material |
| `rg --files tests/bioinformatics tests/meta_analysis tests/ui \| sort` | Passed; inventoried test surfaces |
| `git diff --name-status HEAD..<branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/bioinformatics docs/reports docs/ui scripts analysis app/analysis_runtime` | Passed for selected high-relevance branches; no checkout or merge was performed |

No functional tests were run for this refresh because it was documentation-only and audit-only. `git diff --check` was run after editing.

### Findings

Current Bioinformatics and Meta Analysis contain substantial non-legacy implementations and tests. Since the previous inventory baseline, current `dev/bioinformatics` added standard analysis runtime material:

- DEG standard module contract and DEG lite worker fixture.
- Multi-factor DEG standard result package sidecar.
- Standard R worker provenance hardening with separate input and parameter hashes.

These are current-line scaffolds and sidecars, not old-branch migrations and not production availability claims. Mock/lite/testing-level output remains excluded from completed-feature claims.

Legacy directories remain quarantined:

```text
app/bioinformatics/legacy/**
app/meta_analysis/legacy/**
archive/legacy_sources/**
```

### Decision

No migration candidate is approved for direct carry-over. Future work must select one candidate and one current UI entry, then adapt or rewrite against current contracts with real output proof. Current UI remains the only mainline.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, UI replacement, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `8c34c37`

Date: 2026-06-04

### Scope

This refresh updated the Phase 2.5 branch, legacy, migration-candidate, deprecated-register, and current-UI coverage reports against the current `dev/bioinformatics` HEAD:

```text
8c34c377f28302128161c23384ca79f40ded4e2d
```

The task remained audit-only:

- No old branch was checked out.
- No branch was merged.
- No cherry-pick was performed.
- No current UI code was changed.
- No analysis algorithm was changed.
- No legacy code was migrated.
- No mock, placeholder, testing-level, branch-only, or legacy-only output was promoted to completed functionality.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Current Worktree State

The refresh observed and preserved non-Phase-2.5 working changes:

```text
 M analysis/runners/run_module.R
 M analysis/schemas/output/worker_invocation.schema.json
 M app/analysis_runtime/standard_package.py
 M docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md
 M docs/R_ANALYSIS_ARCHITECTURE.md
 M docs/R_ANALYSIS_REMEDIATION_PLAN.md
 M tests/test_r_analysis_architecture_contract.py
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

These files were not treated as Phase 2.5 migration outputs.

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,260p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,260p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short --branch` | Passed, current branch `dev/bioinformatics` |
| `git branch --all --verbose --no-abbrev` | Passed |
| `git for-each-ref --format='%(refname:short) %(objectname:short) %(committerdate:short) %(subject)' --sort=refname refs/heads refs/remotes` | Passed |
| `git rev-parse HEAD` | Passed, `8c34c377f28302128161c23384ca79f40ded4e2d` |
| `git log --oneline --decorate --max-count=80 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Passed for selected high-relevance branches |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -maxdepth 4 -type f` | Passed |
| `find app/meta_analysis tests/meta_analysis tests/ui -maxdepth 4 -type f` | Passed |
| `rg -n "QPushButton\|setText\|plot\|report\|export\|DEG\|ORA\|GSEA\|survival\|Cox\|forest\|funnel\|Meta\|run" app/bioinformatics app/meta_analysis tests/ui -g '*.py'` | Passed |

No functional tests were run for this refresh because the task was audit-only and documentation-only. Functional tests would validate the current checkout but would not prove old-branch runtime availability.

### Findings

The current line now includes standard analysis runtime scaffolding, external R command boundary material, standard package sidecars for selected Bioinformatics results, and full-mode environment blocker snapshots. These are current-code governance and packaging-contract materials, not proof that every old branch analysis or every full-mode scientific workflow is production-ready.

Additional legacy inventory was recorded for:

- Meta bias/profile/readiness helpers.
- Meta GEO/local dataset readiness utilities.
- Meta legacy packaging scripts.
- Full-mode analysis environment blocker snapshots as current governance scaffold.

Selected high-relevance branch deltas remain large:

- `dev/release-internal-test`: 2118 audited-path files.
- `codex/releasebuild-formal-deg-carryover`: 1093 files.
- `codex/mainline-survival-clinical-carryover`: 732 files.
- `stable/mainline`: 790 files.
- `feature/meta-l3-ui-loop`: 149 files.
- `dev/meta-analysis`: 607 files.
- `dev/ui-shell`: 2118 files.
- `integration/release-ui-shell-scoped-migration`: 793 files.
- `integration/release-labtools-c1-module-nav`: 809 files.
- `codex/bio-geo-real-download-test`: 567 files.
- `codex/stage-3.6-deg-preflight`: 1078 files.
- `codex/meta-workflow-ui`: 505 files.
- `codex/meta-search-ui-main`: 590 files.
- `integration/phase4-meta-l3-scoped-pick`: 930 files.
- `mainline/phase4-meta-l3-scoped-pick`: 790 files.

### Decision

No migration candidate is approved for direct carry-over. Future work must choose one candidate feature, one current UI entry, one contract bridge, and one focused proof plan. Old branches and legacy directories remain material libraries only.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, UI replacement, analysis algorithm modification, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `fca3a01`

Date: 2026-06-04

### Scope

This refresh updated the full branch inventory and migration-candidate reports against the current `dev/bioinformatics` HEAD:

```text
fca3a012342d2fa6168107835bdcb196df43d3a1
```

The task remained audit-only:

- No old branch was checked out.
- No branch was merged.
- No cherry-pick was performed.
- No UI code was changed.
- No analysis algorithm was changed.
- No legacy code was migrated.
- No mock, placeholder, testing-level, branch-only, or legacy-only output was promoted to completed functionality.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Current Worktree State

The refresh intentionally modified only the Phase 2.5 report files above. These unrelated untracked paths were observed and preserved:

```text
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

### Commands Run

| Command | Result |
| --- | --- |
| `rg -n "Meta analysis\|BioMedPilot\|LabTools\|legacy\|L3" /Users/changdali/.codex/memories/MEMORY.md` | Passed |
| `git status --short --branch` | Passed |
| `git branch --all --verbose --no-abbrev` | Passed |
| `rg --files docs/reports app tests` | Passed |
| `sed -n '1,260p' docs/reports/BRANCH_INVENTORY.md` | Passed |
| `sed -n '1,260p' docs/reports/LEGACY_FEATURE_CATALOG.md` | Passed |
| `sed -n '1,260p' docs/reports/MIGRATION_CANDIDATE_LEDGER.md` | Passed |
| `sed -n '1,260p' docs/reports/DEPRECATED_LEGACY_REGISTER.md` | Passed |
| `sed -n '1,260p' docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md` | Passed |
| `sed -n '1,220p' docs/reports/L3_CLOSURE_WORKLOG.md` | Passed |
| `sed -n '1,220p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,220p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git rev-parse HEAD` | Passed, `fca3a012342d2fa6168107835bdcb196df43d3a1` |
| `git log --oneline --decorate --max-count=80 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -maxdepth 4 -type f` | Passed |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads` | Passed |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Passed for selected high-relevance branches |
| `rg -n "risk_score\|nomogram\|calibration\|decision curve\|DCA\|forest\|funnel\|OCR\|fulltext\|DESeq2\|edgeR\|limma\|ORA\|GSEA\|survival\|Cox\|report_ready\|standard_result_package\|source_statistics_result_hash" app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui -g '*.py' -g '*.json'` | Passed |
| `git diff --stat -- docs/reports/BRANCH_INVENTORY.md docs/reports/LEGACY_FEATURE_CATALOG.md docs/reports/MIGRATION_CANDIDATE_LEDGER.md docs/reports/DEPRECATED_LEGACY_REGISTER.md docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md docs/reports/L3_CLOSURE_WORKLOG.md` | Passed |
| `git diff -- docs/reports/BRANCH_INVENTORY.md` | Passed |
| `git diff -- docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md docs/reports/DEPRECATED_LEGACY_REGISTER.md docs/reports/LEGACY_FEATURE_CATALOG.md docs/reports/MIGRATION_CANDIDATE_LEDGER.md` | Passed |
| `tail -n 140 docs/reports/L3_CLOSURE_WORKLOG.md` | Passed |
| `git diff -- docs/reports/L3_CLOSURE_WORKLOG.md` | Passed |

No functional tests were run for this refresh because it was documentation-only and audit-only. Functional tests would validate the current checkout, not prove old-branch runtime availability.

### Findings

The current line has advanced beyond the previous Phase 2.5 reports and now includes formal DEG, survival/Cox, immune infiltration, and expression correlation standard result package sidecars, plus standard analysis runtime/package catalog scaffolds. These are current-code contract/package materials, not proof that every old branch, legacy directory, Bioinformatics candidate, or Meta Analysis candidate is current available.

High-relevance branch deltas remain large:

| Branch | Audited-path file delta vs current |
| --- | ---: |
| `dev/release-internal-test` | 2118 |
| `codex/releasebuild-formal-deg-carryover` | 1093 |
| `codex/mainline-survival-clinical-carryover` | 732 |
| `stable/mainline` | 790 |
| `feature/meta-l3-ui-loop` | 149 |
| `dev/meta-analysis` | 607 |
| `dev/ui-shell` | 2118 |
| `integration/release-ui-shell-scoped-migration` | 793 |
| `integration/release-labtools-c1-module-nav` | 809 |
| `codex/bio-geo-real-download-test` | 567 |
| `codex/stage-3.6-deg-preflight` | 1078 |
| `codex/meta-workflow-ui` | 505 |
| `codex/meta-search-ui-main` | 590 |
| `integration/phase4-meta-l3-scoped-pick` | 930 |
| `mainline/phase4-meta-l3-scoped-pick` | 790 |

No old branch is safe to merge wholesale. Legacy directories and `archive/legacy_sources/**` remain quarantined material libraries only.

### Decision

No migration candidate is approved for direct carry-over. Future work must select one candidate feature, one current UI entry, one current contract bridge, and one focused proof plan. Mock, placeholder, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, UI replacement, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `05d3afc`

Date: 2026-06-04

### Scope

This refresh updated the full branch inventory and migration-candidate reports against the current `dev/bioinformatics` HEAD:

```text
05d3afcff4782d037405dd618db32661cb338fd4
```

The task remained audit-only:

- No old branch was checked out.
- No branch was merged.
- No cherry-pick was performed.
- No UI code was changed.
- No analysis algorithm was changed.
- No legacy code was migrated.
- No mock, placeholder, testing-level, branch-only, or legacy-only output was promoted to completed functionality.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Current Worktree State

The refresh observed and preserved pre-existing non-Phase-2.5 changes:

```text
 M app/bioinformatics/deg_engine/formal_runner.py
 M docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md
 M docs/R_ANALYSIS_ARCHITECTURE.md
 M docs/R_ANALYSIS_REMEDIATION_PLAN.md
 M tests/bioinformatics/test_formal_controlled_deg_runner.py
?? app/bioinformatics/deg_engine/standard_package.py
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

These files were not treated as Phase 2.5 migration outputs.

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,260p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,260p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short` | Passed |
| `git branch --all --verbose --no-abbrev` | Passed |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads` | Passed |
| `git rev-parse HEAD` | Passed, `05d3afcff4782d037405dd618db32661cb338fd4` |
| `git log --oneline --decorate --max-count=80 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Passed for selected high-relevance branches |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -maxdepth 3 -type f` | Passed |
| `rg --files app tests docs` | Passed |

No functional tests were run for this refresh because it was documentation-only and audit-only. Functional tests would validate the current checkout, not prove old-branch runtime availability.

### Findings

The current line has advanced beyond the previous Phase 2.5 reports and now includes standard package artifact manifests, worker invocation manifest validation, and controlled survival/Cox standard package sidecars. These are current-code contract/package materials, not proof that every old branch, legacy directory, Bioinformatics candidate, or Meta Analysis candidate is current available.

High-relevance branch deltas remain large:

| Branch | Audited-path file delta vs current |
| --- | ---: |
| `dev/release-internal-test` | 2111 |
| `codex/releasebuild-formal-deg-carryover` | 1086 |
| `codex/mainline-survival-clinical-carryover` | 725 |
| `stable/mainline` | 783 |
| `dev/meta-analysis` | 602 |
| `dev/ui-shell` | 2115 |
| `integration/phase4-meta-l3-scoped-pick` | 923 |

No old branch is safe to merge wholesale. Legacy directories and `archive/legacy_sources/**` remain quarantined material libraries only.

### Decision

No migration candidate is approved for direct carry-over. Future work must select one candidate feature, one current UI entry, one current contract bridge, and one focused proof plan. Mock, placeholder, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, UI replacement, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `db5bef1`

Date: 2026-06-04

### Scope

This refresh updated the Phase 2.5 branch and legacy inventory reports against the current `dev/bioinformatics` HEAD:

```text
db5bef1a224a8a6983c011da9260658364c25c7f
```

The task remained audit-only. No old branch was checked out, merged, cherry-picked, or used to modify the current UI or analysis algorithms. The current UI remains the only mainline, and old branches remain material libraries only.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Current Worktree State

The refresh observed and preserved pre-existing non-Phase-2.5 changes:

```text
 M app/analysis_runtime/standard_package.py
 M docs/R_ANALYSIS_ARCHITECTURE.md
 M tests/test_analysis_runtime_task_bridge.py
 M tests/test_r_analysis_architecture_contract.py
?? analysis/schemas/output/worker_invocation.schema.json
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

The Phase 2.5 report updates were the only intentional changes made in this refresh.

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,260p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,260p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short --branch` | Passed |
| `git branch --show-current` | Passed, `dev/bioinformatics` |
| `git rev-parse HEAD` | Passed, `db5bef1a224a8a6983c011da9260658364c25c7f` |
| `git branch --all --format='%(refname:short)'` | Passed |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads` | Passed |
| `git log --oneline --decorate --max-count=40 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Passed for selected high-relevance branches |
| `find . -maxdepth 4 -type d \( -name legacy -o -name '*legacy*' -o -name Legacy -o -name ReleaseBuild -o -name MainLine -o -name Integration \)` | Passed |
| `find app tests docs scripts analysis -maxdepth 4 -type f` | Passed |
| `grep -R "ccf7967609\|a471a25\|2097\|1072\|711\|2103\|dee35e5" -n docs/reports/...` | Passed; remaining old commit references are historical recent-history entries only |

No functional tests were run because the task was documentation-only and audit-only. Functional tests would validate the current checkout, not prove old-branch runtime availability.

### Findings

The current line has advanced beyond the previous Phase 2.5 reports and now includes R worker invocation manifest diagnostics in the package catalog. This is current scaffold/contract material, not proof that every Bioinformatics or Meta Analysis candidate has production-grade analysis output.

High-relevance branch deltas remain large:

| Branch | Audited-path file delta vs current |
| --- | ---: |
| `dev/release-internal-test` | 2105 |
| `codex/releasebuild-formal-deg-carryover` | 1080 |
| `codex/mainline-survival-clinical-carryover` | 719 |
| `stable/mainline` | 781 |
| `dev/meta-analysis` | 600 |
| `dev/ui-shell` | 2111 |

No old branch is safe to merge wholesale. Legacy directories and `archive/legacy_sources/**` remain quarantined material libraries only.

### Decision

No migration candidate is approved for direct carry-over. Future work must select one candidate feature, one current UI entry, one current contract bridge, and one focused proof plan. Mock, placeholder, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, UI replacement, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `ccf7967`

Date: 2026-06-04

### Scope

This refresh updated the branch inventory reports against the current `dev/bioinformatics` HEAD:

```text
ccf7967609a283cddfbb83bdf6d68ceb7bc12b63
```

The task remained audit-only:

- No old branch was checked out.
- No branch was merged.
- No cherry-pick was performed.
- No UI code was changed.
- No analysis algorithm was changed.
- No legacy code was migrated.
- No mock, placeholder, testing-level, branch-only, or legacy-only output was promoted to completed functionality.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Current Worktree State

The refresh observed and preserved pre-existing unrelated changes:

```text
 M analysis/modules/molecular_dynamics/module.json
 M analysis/registry/analysis_modules.json
 M analysis/runners/run_module.R
 M tests/test_analysis_runtime_task_bridge.py
 M tests/test_r_analysis_architecture_contract.py
?? analysis/fixtures/inputs/molecular_dynamics/lite_coordinates.gro
?? analysis/fixtures/inputs/molecular_dynamics/lite_mdp.mdp
?? analysis/fixtures/inputs/molecular_dynamics/lite_topology.top
?? analysis/fixtures/inputs/molecular_dynamics/module_input_lite.json
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

These files were not treated as Phase 2.5 migration outputs.

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,260p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,260p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short` | Passed |
| `git branch --show-current` | Passed, `dev/bioinformatics` |
| `git rev-parse HEAD` | Passed, `ccf7967609a283cddfbb83bdf6d68ceb7bc12b63` |
| `git branch --all --verbose --no-abbrev` | Passed |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads` | Passed |
| `git log --oneline --decorate --max-count=60 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Passed for selected high-relevance branches |
| `git diff --name-status HEAD..<branch> -- ...` | Passed for selected high-relevance branches |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -maxdepth 4 -type f` | Passed |
| `find app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui -maxdepth 3 -type f` | Passed |
| `rg -n "QPushButton\|setText\|plot\|report\|DEG\|ORA\|GSEA\|survival\|Cox\|Meta" app/bioinformatics app/meta_analysis -g '*.py'` | Passed |

No functional tests were run for this refresh because it was documentation-only and audit-only. Functional tests would not prove old-branch runtime availability.

### Findings

The current line now includes standard analysis runtime scaffolding, an external R command boundary, and docking lite command-manifest contract material. These are current-code scaffolds, not evidence that every analysis module has a full production real loop.

High-relevance branch deltas remain large:

- `dev/release-internal-test`: 2097 files in audited paths.
- `codex/releasebuild-formal-deg-carryover`: 1072 files.
- `codex/mainline-survival-clinical-carryover`: 711 files.
- `dev/meta-analysis`: 592 files.
- `dev/ui-shell`: 2103 files, with rename-detection warning.

No old branch is safe to merge wholesale. Legacy directories and `archive/legacy_sources/**` remain quarantined material libraries only.

### Decision

No migration candidate is approved for direct carry-over. Future work must select one candidate feature and one current UI entry, then adapt or rewrite against current contracts with real output proof.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, UI replacement, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `a471a25`

Date: 2026-06-04

### Scope

This refresh updated the branch inventory reports against the current `dev/bioinformatics` HEAD:

```text
a471a25a9153b23c224ea7a96e425c44de92ee5e
```

The task remained audit-only. No old branch was checked out, merged, cherry-picked, or used to modify the current UI or analysis algorithms. Legacy directories and old branches remain material libraries only.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Current Worktree State

The refresh observed and preserved pre-existing unrelated changes:

```text
 M app/analysis_runtime/__init__.py
 M app/analysis_runtime/r_worker.py
 M app/bioinformatics/deg_engine/multifactor_r_runner.py
 M app/bioinformatics/enrichment_r_adapter.py
 M docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md
 M docs/R_ANALYSIS_ARCHITECTURE.md
 M docs/R_ANALYSIS_REMEDIATION_PLAN.md
 M tests/test_analysis_runtime_task_bridge.py
 M tests/test_r_analysis_architecture_contract.py
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,260p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,260p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short --branch` | Passed |
| `git branch --all --verbose --no-abbrev` | Passed |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads refs/remotes` | Passed |
| `git rev-parse HEAD` | Passed, `a471a25a9153b23c224ea7a96e425c44de92ee5e` |
| `git log --oneline --decorate --max-count=45 -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts app/analysis_runtime analysis` | Passed |
| `git diff --name-status HEAD..<branch> -- app/bioinformatics app/meta_analysis tests/bioinformatics tests/meta_analysis tests/ui docs/bioinformatics docs/reports docs/ui scripts app/analysis_runtime analysis` | Passed for selected high-relevance branches |
| `find app/bioinformatics/legacy app/meta_analysis/legacy -maxdepth 4 -type f` | Passed |
| `find app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui -maxdepth 4 -type f` | Passed |
| `rg -n "QPushButton\|run\|export\|plot\|report\|DEG\|GSEA\|ORA\|survival\|Cox\|forest\|funnel" app/bioinformatics app/meta_analysis tests/ui` | Passed |

No functional tests were run for this refresh because it was documentation-only and audit-only. The audit did not claim branch-only runtime availability.

### Findings

Current Bioinformatics and Meta Analysis contain substantial non-legacy implementations and tests. Old branches contain useful material for DEG, enrichment, survival/Cox, risk/report/renderers, OCR/fulltext, UI shell design, and search workflows, but no old branch is safe to merge wholesale. High-relevance branch deltas ranged from `122` to `2099` files in audited paths.

Legacy directories remain quarantined:

```text
app/bioinformatics/legacy/**
app/meta_analysis/legacy/**
```

### Decision

No migration candidate is approved for direct carry-over. Future work must select one candidate and one current UI entry, then adapt or rewrite against current contracts with real output proof. Mock, placeholder, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, UI replacement, or legacy code migration without the next explicit instruction.

## Current Latest Phase 2.5 Snapshot

Date: 2026-06-04

Latest refreshed audit baseline: `dev/bioinformatics` at `25e179d238b762fc63a69b802f4f231f01effdbe`.

The detailed current refresh entry is recorded below as `Phase 2.5 Refresh: Full Branch Inventory at 25e179d`. It supersedes older Phase 2.5 entries for current-state reporting while preserving them as historical worklog records.

Current decision remains unchanged: no old branch, legacy directory, archive source, mock output, placeholder output, testing-level output, or branch-only implementation is approved for direct carry-over. The current UI remains the only mainline, and old branches remain material libraries only.

## Phase 2.5 Refresh: Full Branch Inventory at `25e179d`

Date: 2026-06-04

This refresh updated the Phase 2.5 branch inventory, legacy catalog, migration ledger, deprecated register, and current UI coverage matrix against the current `dev/bioinformatics` HEAD:

```text
25e179d238b762fc63a69b802f4f231f01effdbe
block runtime gene set resource downloads
```

The task remained audit-only. No old branch was checked out, merged, cherry-picked, or used to modify the current UI or analysis algorithms. Legacy directories, archive sources, and old branches remain material libraries only.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Worktree Boundaries

The refresh intentionally modified only Phase 2.5 report files. These unrelated untracked paths were observed and preserved:

```text
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

They were not treated as Phase 2.5 migration outputs.

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,240p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,240p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short --branch` | Passed |
| `git branch --all --verbose --no-abbrev` | Passed |
| `git rev-parse HEAD` | Passed, `25e179d238b762fc63a69b802f4f231f01effdbe` |
| `git for-each-ref '--format=%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads refs/remotes` | Passed |
| `git log --oneline --decorate --max-count=60 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Passed for selected high-relevance branches |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -maxdepth 4 -type f` | Passed; current inventory size is 827 files |
| `find app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui -maxdepth 3 -type f` | Passed |
| `rg -n "QPushButton\|setText\|run\|export\|plot\|report\|DEG\|GSEA\|ORA\|survival\|Cox\|forest\|funnel\|meta" app/bioinformatics app/meta_analysis tests/ui -g '*.py'` | Passed |

No functional tests were run because this phase was documentation-only and audit-only. The audit does not claim branch-only or legacy-only runtime availability.

### Updated Findings

Current `dev/bioinformatics` has advanced beyond the previous `f8590cc` snapshot and now includes a resource-governance hardening commit that blocks runtime gene-set downloads by default. This affects enrichment resource migration candidates: old branch code that silently downloads Reactome, GO, KEGG, or related resources must remain quarantined unless adapted to explicit import or prelocked resource contracts.

High-relevance branch deltas remain large. Selected audited branches ranged from `154` to `2120` changed files in audited paths, so whole-branch carry-over remains unsafe.

### Decision

No migration candidate is approved for direct carry-over. Future work must select one current UI entry and one candidate, then adapt or rewrite it against the current contracts with current tests and real output evidence.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, cherry-pick, UI replacement, analysis algorithm modification, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `8eb18b01`

Date: 2026-06-05

### Scope

This refresh updated the Phase 2.5 branch inventory, legacy feature catalog, migration candidate ledger, deprecated legacy register, and branch-to-current-UI coverage matrix against the current `dev/bioinformatics` HEAD:

```text
8eb18b01a7d3cfc29d3d788feb82e48aec6f2cfb
block full analysis without restored environment locks
```

The task remained audit-only. No old branch was checked out, merged, cherry-picked, or used to modify the current UI or analysis algorithms. Legacy directories, archive sources, and old branches remain material libraries only.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Worktree Boundaries

The refresh intentionally modified only Phase 2.5 report files. These unrelated dirty or untracked paths were observed and preserved:

```text
 M app/analysis_runtime/__init__.py
 M app/analysis_runtime/resources.py
 M docs/ARCHITECTURE_AUDIT_R_ANALYSIS.md
 M docs/R_ANALYSIS_ARCHITECTURE.md
 M tests/test_r_analysis_architecture_contract.py
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

They were not treated as Phase 2.5 migration outputs.

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,240p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,240p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short --branch` | Passed |
| `git branch --all --verbose --no-abbrev` | Passed |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads` | Passed |
| `git rev-parse HEAD` | Passed, `8eb18b01a7d3cfc29d3d788feb82e48aec6f2cfb` |
| `git show -s --format='%h%n%H%n%ci%n%s' HEAD` | Passed |
| `find app/bioinformatics app/meta_analysis archive/legacy_sources -path '*legacy*' -type f` | Passed; current boundary count remains 924 files |
| `git diff --shortstat HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Passed for selected high-relevance branches |
| `git ls-tree -r --name-only <branch> -- ...` | Passed for selected high-relevance branches |
| `rg -n "standard package\|package_manifest\|environment_lock_status\|full_mode\|mock\|lite\|result_package\|worker\|invocation\|resource" app/analysis_runtime analysis tests/test_r_analysis_architecture_contract.py tests/test_analysis_runtime_task_bridge.py docs/reports -g '*.py' -g '*.R' -g '*.md'` | Passed |
| `git diff --check -- docs/reports/BRANCH_INVENTORY.md docs/reports/LEGACY_FEATURE_CATALOG.md docs/reports/MIGRATION_CANDIDATE_LEDGER.md docs/reports/DEPRECATED_LEGACY_REGISTER.md docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md docs/reports/L3_CLOSURE_WORKLOG.md` | Passed |

No functional tests were run because this phase was documentation-only and audit-only. Functional tests would validate the current checkout, not prove old-branch runtime availability.

### Findings

Current `dev/bioinformatics` now includes standard package/input manifest surfacing and full-mode environment-lock blockers on top of previous standard package worker and sidecar governance. These are current contract and blocker-surfacing facts; they do not prove full scientific production analysis and do not authorize migration from old branches.

High-relevance branch deltas remain large:

- `dev/release-internal-test`: 2130 files changed, 135505 insertions, 86177 deletions.
- `codex/releasebuild-formal-deg-carryover`: 1104 files changed, 91914 insertions, 79141 deletions.
- `codex/mainline-survival-clinical-carryover`: 744 files changed, 15914 insertions, 70433 deletions.
- `stable/mainline`: 801 files changed, 14358 insertions, 81312 deletions.
- `dev/meta-analysis`: 617 files changed, 20794 insertions, 78968 deletions.

Legacy directories remain quarantined:

```text
app/bioinformatics/legacy/**
app/meta_analysis/legacy/**
archive/legacy_sources/**
```

### Decision

No migration candidate is approved for direct carry-over. Future work must select one current UI entry and one candidate, then adapt or rewrite it against current contracts with current tests and real output evidence. Mock, placeholder, dry-run, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, cherry-pick, UI replacement, analysis algorithm modification, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `81225c3`

Date: 2026-06-05

### Scope

This refresh updated the Phase 2.5 branch inventory, legacy feature catalog, migration candidate ledger, deprecated legacy register, and branch-to-current-UI coverage matrix against the current `dev/bioinformatics` HEAD:

```text
81225c3625022d180447b4a3fe4b2d0f7882360f
surface standard package gates in analysis center
```

The task remained audit-only. No old branch was checked out, merged, cherry-picked, or used to modify the current UI or analysis algorithms. Legacy directories, archive sources, and old branches remain material libraries only.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Worktree Boundaries

The refresh intentionally modified only Phase 2.5 report files. These unrelated dirty or untracked paths were observed and preserved:

```text
 M app/bioinformatics/analysis_ui/state.py
 M tests/bioinformatics/test_analysis_ui_state.py
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

They were not treated as Phase 2.5 migration outputs and were not used as evidence for old-branch runtime availability.

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,260p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,260p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short --branch` | Passed |
| `git branch --show-current` | Passed, `dev/bioinformatics` |
| `git rev-parse HEAD` | Passed, `81225c3625022d180447b4a3fe4b2d0f7882360f` |
| `git branch --all --verbose --no-abbrev` | Passed |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads refs/remotes` | Passed |
| `git log --oneline --decorate --max-count=100 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Passed for selected high-relevance branches; `dev/ui-shell` produced a rename-detection warning due to size |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -maxdepth 4 -type f` | Passed |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -maxdepth 4 -type f \| wc -l` | Passed, 827 files |
| `rg -n "QPushButton\|setText\|run\|export\|plot\|report\|DEG\|GSEA\|ORA\|survival\|Cox\|forest\|funnel\|meta\|Meta\|Bioinformatics" app/bioinformatics app/meta_analysis tests/ui -g '*.py'` | Passed |

No functional tests were run because this phase was documentation-only and audit-only. Functional tests would validate the current checkout, not prove old-branch runtime availability.

### Findings

Current `dev/bioinformatics` has advanced beyond the previous `25e179d` inventory and now includes:

```text
d2ed1ed harden R adapter subprocess boundary
8632907 harden standard package artifact validation
81225c3 surface standard package gates in analysis center
```

These are current contract and UI-gate facts, not approval to migrate any old branch or treat old implementations as current available features.

High-relevance branch deltas remain large:

- `dev/release-internal-test`: 2120 files in audited paths.
- `codex/releasebuild-formal-deg-carryover`: 1094 files.
- `codex/mainline-survival-clinical-carryover`: 734 files.
- `stable/mainline`: 791 files.
- `feature/meta-l3-ui-loop`: 154 files.
- `dev/meta-analysis`: 607 files.
- `dev/ui-shell`: 2118 files.
- `integration/release-ui-shell-scoped-migration`: 794 files.
- `integration/release-labtools-c1-module-nav`: 810 files.
- `codex/bio-geo-real-download-test`: 567 files.
- `codex/stage-3.6-deg-preflight`: 1078 files.
- `codex/meta-workflow-ui`: 505 files.
- `codex/meta-search-ui-main`: 590 files.
- `integration/phase4-meta-l3-scoped-pick`: 931 files.
- `mainline/phase4-meta-l3-scoped-pick`: 791 files.
- `integration/release-bio-c1-ui-shell`: 1071 files.

Legacy directories remain quarantined:

```text
app/bioinformatics/legacy/**
app/meta_analysis/legacy/**
archive/legacy_sources/**
```

### Decision

No migration candidate is approved for direct carry-over. Future work must select one current UI entry and one candidate, then adapt or rewrite it against the current contracts with current tests and real output evidence. Mock, placeholder, dry-run, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, cherry-pick, UI replacement, analysis algorithm modification, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `cdae468`

Date: 2026-06-04

This refresh updated the Phase 2.5 branch inventory, legacy catalog, migration ledger, deprecated register, and current UI coverage matrix against the current `dev/bioinformatics` HEAD:

```text
cdae46876aaf383ecca218d5d6dd57a3449983aa
validate indexed worker invocation artifacts
```

The task remained audit-only. No old branch was checked out, merged, cherry-picked, or used to modify the current UI or analysis algorithms. Legacy directories, archive sources, and old branches remain material libraries only.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Worktree Boundaries

The refresh intentionally modified only Phase 2.5 report files. These unrelated untracked paths were observed and preserved:

```text
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

They were not treated as Phase 2.5 migration outputs.

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,220p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,220p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short --branch` | Passed |
| `git branch --all --no-color` | Passed |
| `git branch --all --verbose --no-abbrev` | Passed |
| `git rev-parse HEAD` | Passed, `cdae46876aaf383ecca218d5d6dd57a3449983aa` |
| `git for-each-ref '--format=%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads refs/remotes` | Passed |
| `git log --oneline --decorate --max-count=80 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Passed for selected high-relevance branches |
| `find app/bioinformatics/legacy app/meta_analysis/legacy archive/legacy_sources -maxdepth 4 -type f` | Passed |
| `find app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui -maxdepth 3 -type f` | Passed |
| `rg -n "QPushButton\|setText\|run\|export\|plot\|report\|DEG\|GSEA\|ORA\|survival\|Cox\|forest\|funnel\|meta" app/bioinformatics app/meta_analysis tests/ui -g '*.py'` | Passed |

No functional tests were run because this phase was documentation-only and audit-only. The audit does not claim branch-only or legacy-only runtime availability.

### Updated Findings

Current `dev/bioinformatics` has advanced beyond the previous `8c34c37` snapshot and now includes direct and legacy-sidecar worker invocation validation, including indexed worker invocation log validation. These are current contract/runtime diagnostics, not approval to migrate any old branch or to treat old implementations as current available features.

High-relevance branch deltas remain large. Selected audited branches ranged from `149` to `2118` changed files in audited paths, so whole-branch carry-over remains unsafe.

### Decision

No migration candidate is approved for direct carry-over. Future work must select one current UI entry and one candidate, then adapt or rewrite it against the current contracts with current tests and real output evidence.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, cherry-pick, UI replacement, analysis algorithm modification, or legacy code migration without the next explicit instruction.

## Phase 2.5 Refresh: Full Branch Inventory at `f8590cc`

Date: 2026-06-04

### Scope

This refresh updated the Phase 2.5 branch inventory, legacy catalog, migration candidate ledger, deprecated legacy register, and branch-to-current-UI coverage matrix against the current `dev/bioinformatics` HEAD:

```text
f8590cc458317656aee600430e911d57cecbb32f
harden standard package module mapping
```

The task remained audit-only. No old branch was checked out, merged, cherry-picked, or used to modify the current UI or analysis algorithms. Legacy directories, archive sources, and old branches remain material libraries only.

### Reports Updated

```text
docs/reports/BRANCH_INVENTORY.md
docs/reports/LEGACY_FEATURE_CATALOG.md
docs/reports/MIGRATION_CANDIDATE_LEDGER.md
docs/reports/DEPRECATED_LEGACY_REGISTER.md
docs/reports/BRANCH_TO_CURRENT_UI_COVERAGE_MATRIX.md
docs/reports/L3_CLOSURE_WORKLOG.md
```

### Worktree Boundaries

The refresh intentionally modified only Phase 2.5 report files. These unrelated dirty or untracked paths were observed and preserved:

```text
 M app/bioinformatics/gene_set_resources.py
 M tests/bioinformatics/test_gene_set_resources.py
?? docs/bioinformatics/Bioinformatics_handoff_report_20260513.md
?? project_storage/bioinformatics/
```

They were not treated as Phase 2.5 migration outputs and were not committed as part of this audit.

### Commands Run

| Command | Result |
| --- | --- |
| `sed -n '1,240p' ../CODEX_UI_BRANCH_MIGRATION_GUIDE.md` | Passed |
| `sed -n '1,240p' ../CODEX_MINIMAL_REAL_LOOP_SELF_CHECK.md` | Passed |
| `git status --short --branch` | Passed |
| `git branch --all --verbose --no-abbrev` | Passed |
| `git for-each-ref --format='%(refname:short)\|%(objectname:short)\|%(committerdate:short)\|%(subject)' --sort=refname refs/heads refs/remotes` | Passed |
| `git rev-parse HEAD` | Passed, `f8590cc458317656aee600430e911d57cecbb32f` |
| `git log --oneline --decorate --max-count=90 -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports scripts` | Passed |
| `git diff --name-only HEAD..<branch> -- app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui docs/reports docs/bioinformatics docs/ui scripts` | Passed for selected high-relevance branches |
| `git diff --name-status HEAD..<branch> -- ...` | Passed for selected high-relevance branches |
| `find app/bioinformatics/legacy app/meta_analysis/legacy -maxdepth 4 -type f` | Passed |
| `find archive -maxdepth 4 -type f` | Passed |
| `find app/bioinformatics app/meta_analysis app/analysis_runtime analysis tests/bioinformatics tests/meta_analysis tests/ui -maxdepth 3 -type f` | Passed |
| `rg -n "QPushButton\|setText\|run\|export\|plot\|report\|DEG\|GSEA\|ORA\|survival\|Cox\|forest\|funnel\|meta" app/bioinformatics app/meta_analysis tests/ui -g '*.py'` | Passed |

No functional tests were run because this phase was documentation-only and audit-only. Functional tests would validate the current checkout, not prove old-branch runtime availability.

### Findings

Current `dev/bioinformatics` now includes standard package module mapping on top of prior worker invocation manifest, sidecar standard package, and Bio/Meta L3 proof history. This strengthens current contract inventory, but it does not approve any old branch for direct migration.

High-relevance branch deltas remain large:

- `dev/release-internal-test`: 2118 files in audited paths.
- `codex/releasebuild-formal-deg-carryover`: 1093 files.
- `codex/mainline-survival-clinical-carryover`: 732 files.
- `dev/meta-analysis`: 607 files.
- `dev/ui-shell`: 2118 files.

Legacy directories remain quarantined:

```text
app/bioinformatics/legacy/**
app/meta_analysis/legacy/**
archive/legacy_sources/**
```

### Decision

No migration candidate is approved for direct carry-over. Future work must select one current UI entry and one candidate, then adapt or rewrite it against current contracts with current tests and real output evidence. Mock, placeholder, dry-run, testing-level, branch-only, and legacy-only outputs remain excluded from completed-feature claims.

### Stop Point

Stop after this Phase 2.5 audit refresh. Do not proceed into development, branch merge, cherry-pick, UI replacement, analysis algorithm modification, or legacy code migration without the next explicit instruction.
