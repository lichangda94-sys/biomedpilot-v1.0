# UI-C2a Bioinformatics Executor Carry-Over Audit

## 1. Audit Question

This audit answers whether UIShell currently contains formal Bioinformatics executors and whether it should carry over formal DEG, ORA, GSEA, survival, or Cox from the local `dev/bioinformatics` worktree.

## 2. Current UIShell Executor Inventory

| Capability | Current UIShell evidence | Current classification | UI-C2a decision |
| --- | --- | --- | --- |
| DEG preflight | `app/bioinformatics/deg_executor_preflight.py`; `app/bioinformatics/pages/differential_expression_page.py` states no p-values/FDR/limma/DESeq2/edgeR | `preflight_only` | Can be shown as preflight/testing only |
| GEO differential expression runner | `app/bioinformatics/services/geo_differential_expression_runner.py`; test asserts `formal_deg_executed=True` | legacy/testing runner outside target gate stack | Do not expose as normal formal executor |
| TCGA DEG runner | `app/bioinformatics/tcga/deg_runner.py` and focused tests | testing/data-specific runner, not target UI formal DEG gate | Do not expose as normal formal executor |
| DEG task plan | `app/bioinformatics/deg_task_plan.py`; tests expect `DESeq2` status `planned_placeholder` | planned/preflight contract | Show as planning/preflight only |
| ORA/enrichment runner | `app/bioinformatics/services/enrichment_runner.py`; local GMT ORA test asserts execution true | small local/testing runner without full product gate stack | Keep disabled or developer/testing only |
| GSEA | configs and task cards mention GSEA; no formal GSEA executor identified in UIShell | planned/preflight only | Keep hidden/disabled |
| Survival service | `app/bioinformatics/services/survival_service.py`; tests assert `survival_analysis_executed=False` | preflight only | Keep preflight only |
| Cox | config mentions Cox; no UIShell formal Cox executor identified | absent/formal not wired | Keep disabled |
| Report service | `app/bioinformatics/services/bio_report_service.py`; tests assert `formal_report_executed=False` | testing summary/draft | Keep draft/testing only |
| Result/report/export shell | shared result/report/export shell has `resultSemanticKey`, `reportStatusKey`, and `exportGate` tests | shell/gated | Reuse shell semantics |

## 3. `dev/bioinformatics` Branch Inventory

Read-only comparison against `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics` on `dev/bioinformatics` shows:

| Capability | Branch evidence | Carry-over risk |
| --- | --- | --- |
| Analysis UI state/action gates | `app/bioinformatics/analysis_ui/state.py`, `action_rules.py`, `labels.py`; tests `test_analysis_ui_state.py`, `test_analysis_ui_action_rules.py` | Low to medium; should be first scoped carry-over target |
| Formal controlled DEG | `app/bioinformatics/deg_engine/formal_runner.py`, parameter gates, dependency gates, result schema, confirmation, result review, report-ready gate tests | Medium to high; only safe after gate contracts land |
| Formal GSEA | `analysis_ui/action_rules.py` marks `formal_gsea` as `hidden_until_ready`; no formal GSEA executor found | High; do not carry executor as active |
| ORA | Existing enrichment runner remains local/testing-style; no branch-level formal ORA action gate comparable to formal DEG was found | Medium; keep as testing/developer until product gates exist |
| KM/log-rank | `app/bioinformatics/survival_clinical/km_executor.py`, parameter/confirmation/result schema/review tests | High due clinical interpretation; carry only after state/result gates |
| Cox univariate | `app/bioinformatics/survival_clinical/cox_executor.py`, confirmation, result schema, review, e2e tests | High due clinical interpretation; carry only after survival gate audit |
| Cox multivariate/risk score | Action rules explicitly disabled/hidden | Must not carry as active |
| Result registry | `app/bioinformatics/results/registry.py`, models, validation, migration, semantic tests | Low to medium; important for safe UI |
| Report/export gates | `app/bioinformatics/reports/readiness.py`, `formal_deg.py`, `export_package.py`; report-ready tests | Medium; carry gate evaluation before export UI activation |
| Plot artifacts | `app/bioinformatics/plots/**`; formal DEG/KM/Cox plot tests | Medium to high; do not render as runtime formal plots until result semantics are wired |

## 4. Branch Diff Summary

`dev/bioinformatics` adds or changes a large surface under `app/bioinformatics/**`, including:

- `analysis_ui/**`
- `deg_engine/**`
- `deg_ready/**`
- `results/**`
- `reports/**`
- `plots/**`
- `survival_clinical/**`
- clinical analysis preflight and TCGA/GTEx source executors

It also removes or supersedes some UIShell-era preflight files. A direct wholesale merge into UIShell would be too broad for UI-C2a and risks changing runtime behavior before the UI gates are in place.

## 5. Carry-Over Decision

| Candidate | Decision | Reason |
| --- | --- | --- |
| `analysis_ui` state/action/labels | Carry over next, scoped | Needed to render mockup buttons safely and keep normal-user visibility correct |
| Result semantic models/registry/validation | Carry over next, scoped with tests | Required before result/report/export UI can distinguish imported/testing/formal results |
| Report-ready gate evaluation | Carry over after result registry | Required before export buttons can be truthfully gated |
| Formal DEG executor | Do not carry in UI-C2a; plan C2d scoped carry-over after gates | It writes formal result artifacts and requires dependency, parameter, confirmation, and result schema gates |
| ORA runner | Do not carry as formal executor | Existing runner lacks the same product gate stack; show preflight/testing only |
| Formal GSEA executor | Do not carry | Branch action rules say formal GSEA is hidden until ready |
| KM/log-rank executor | Do not carry in UI-C2a; plan later clinical/survival audit | Clinical interpretation risk and formal result write path |
| Cox executor | Do not carry in UI-C2a; plan later clinical/survival audit | Clinical interpretation risk and formal result write path |
| Cox multivariate/risk score | Do not carry as active | Branch action rules explicitly keep these hidden/disabled |

## 6. Recommended Carry-Over Order

1. `Bioinformatics UI-C2b State/Action Gate Carry-Over Audit`
   - Carry `analysis_ui/state.py`, `analysis_ui/action_rules.py`, labels, and focused tests.
   - Do not carry formal executors yet.
2. `Bioinformatics UI-C2c Result Semantics And Report Gate Carry-Over`
   - Carry result models, registry, validation, report readiness gate, and tests.
   - Keep export disabled until package gate is separately approved.
3. `Bioinformatics UI-C2d Formal DEG Scoped Carry-Over`
   - Carry formal DEG only if UI has disabled-by-default gate rendering and all formal DEG tests are in scope.
4. `Bioinformatics UI-C2e Survival/Cox Scoped Carry-Over Audit`
   - Audit KM/log-rank and Cox separately. Keep clinical conclusion, multivariate Cox, risk score, and nomogram disabled.

## 7. Executor Boundary For UI-C2 Implementation

Until carry-over stages complete, the Bioinformatics target shell should use these labels:

- DEG: `preflight_only` or `blocked_until_gate`
- ORA/GSEA: `planned` or `hidden_until_ready`
- KM/log-rank: `blocked_until_carryover`
- Cox: `blocked_until_carryover`
- Clinical audit: `preflight_only`
- Result/report: `testing_summary` or `draft`
- Export: `disabled_missing_report_ready`

## 8. Commands Run

| Command | Result |
| --- | --- |
| `git -C .../Bioinformatics ls-tree -r --name-only HEAD app/bioinformatics tests/bioinformatics config/bioinformatics docs/bioinformatics ...` | Identified analysis UI, formal DEG, KM/Cox, result registry, report gates in `dev/bioinformatics` |
| `git diff --name-status dev/ui-shell..dev/bioinformatics -- app/bioinformatics tests/bioinformatics config/bioinformatics docs/bioinformatics ...` | Confirmed carry-over surface is broad and should be scoped |
| `git -C .../Bioinformatics show HEAD:app/bioinformatics/analysis_ui/state.py` | Confirmed branch builds central UI state from resolver, gates, results, dependencies, and reports |
| `git -C .../Bioinformatics show HEAD:app/bioinformatics/analysis_ui/action_rules.py` | Confirmed formal GSEA and multivariate/risk-score actions are hidden/disabled; formal DEG requires gates |
| `git -C .../Bioinformatics show HEAD:app/bioinformatics/deg_engine/formal_runner.py` | Confirmed formal DEG writes result table/log and registers `formal_computed_result` |
| `git -C .../Bioinformatics show HEAD:app/bioinformatics/survival_clinical/km_executor.py` | Confirmed KM/log-rank executor writes result tables and registers formal result entries |
| `git -C .../Bioinformatics show HEAD:app/bioinformatics/survival_clinical/cox_executor.py` | Confirmed Cox executor writes result table/log and registers formal result entries |

## 9. Final Recommendation

Do not carry formal DEG, ORA, GSEA, survival, or Cox executors directly as part of UI-C2a. The next actionable step is a scoped state/action/result/report gate carry-over. After that, formal DEG can be considered first because it has the clearest audited gate stack. ORA/GSEA should remain planned/hidden. KM/log-rank and Cox require a separate clinical/survival carry-over audit before any active UI action is allowed.
