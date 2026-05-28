# Bioinformatics UI-C3a Formal DEG Carry-over Readiness Audit

Date: 2026-05-24

## 1. Scope

This audit evaluates whether Bioinformatics can safely move from the current gated UI shell toward formal DEG carry-over.

This stage is audit-only. It does not modify `app/**`, `tests/**`, `assets/**`, `scripts/**`, `dist/**`, packaged app artifacts, App icon, Finder icon, Info.plist, or LaunchServices. It does not enable any executor.

Reviewed inputs:

- `docs/ui/UI_C2a_bioinformatics_executor_carryover_audit_20260522.md`
- `docs/ui/UI_C2a_bioinformatics_state_action_gate_contract_20260522.md`
- `docs/ui/UI_C2g_bioinformatics_gated_ui_closure_audit_20260522.md`
- `docs/ui/UI_C2g_bioinformatics_runtime_status_matrix_20260522.csv`
- `app/bioinformatics/analysis_ui/action_rules.py`
- `app/bioinformatics/analysis_ui/state.py`
- `app/bioinformatics/deg_task_plan.py`
- `app/bioinformatics/deg_executor_preflight.py`
- `tests/ui/test_bioinformatics_analysis_tasks_gated_page.py`
- `tests/ui/test_bioinformatics_gate_shell.py`
- `tests/ui/test_bioinformatics_workflow_pages.py`

## 2. Decision

Decision: `not_ready_to_enable_formal_deg`.

Recommended next action: `plan_scoped_formal_deg_carryover`, not runtime activation.

Rationale:

- The current UI gate shell is stable and correctly blocks ordinary formal actions.
- DEG task plan and executor preflight exist, but they intentionally stop at `configured_not_run`, `skipped_dry_run`, and `preflight_only`.
- Current normal UI still treats formal DEG as `blocked_until_carryover`.
- Formal result registry, result schema gate, report-ready gate, plot gate, and export gate are not yet connected as a single product-safe execution chain.
- Existing legacy/testing GEO DEG runner and TCGA runner are not equivalent to the target formal DEG executor.

## 3. Current Readiness Inventory

| Capability | Current evidence | Readiness |
| --- | --- | --- |
| 7-step gated UI | C2g closure and focused tests | ready |
| action gate shell | `analysis_ui/action_rules.py` | ready for disabled state |
| page state summary | `analysis_ui/state.py` | ready for preview |
| DEG task plan | `deg_task_plan.py`, status `configured_not_run` | preflight-ready only |
| DEG executor preflight | `deg_executor_preflight.py`, status `preflight_only` | preflight-ready only |
| legacy GEO DEG runner | `geo_differential_expression_runner.py` and workflow tests | legacy/testing only |
| TCGA DEG runner | `tcga/deg_runner.py` | data-specific/testing only |
| formal DEG executor | no target `deg_engine/formal_runner.py` in active UIShell runtime | not present |
| formal result schema/registry | result gate preview exists; no formal DEG result production chain | not ready |
| volcano/heatmap | no formal plot production allowed | disabled |
| report-ready package | C2f gate blocked | disabled |
| export | C2f export gate disabled | disabled |

## 4. Gate Requirements Before Formal DEG Activation

Formal DEG must remain disabled until all of these are implemented and tested together:

1. Project context and storage path are valid.
2. Standardized count matrix is selected and immutable for the run.
3. Sample metadata and group design are confirmed.
4. Comparison selection is explicit.
5. Method policy is explicit and matches available executor.
6. Dependency gate validates required runtime packages.
7. Parameter gate validates thresholds, normalization policy, and filters.
8. User confirmation gate records that formal computation is intended.
9. Formal executor writes a result artifact only under approved project storage.
10. Result registry records `formal_computed_result`.
11. Result schema validation passes.
12. Result review page displays formal output without fake plot/table fallback.
13. Report-ready gate stays blocked until formal result review requirements pass.
14. Export stays disabled until report-ready and file-picker/export adapter gates pass.

## 5. Current Blockers

Blocking items:

- no active UIShell formal DEG executor module comparable to the audited `dev/bioinformatics` formal runner
- no connected formal DEG result registry write path in ordinary UI
- no connected formal DEG result schema gate
- no formal result review acceptance workflow
- no report-ready package gate from formal DEG results
- no export adapter gate for DEG result export

High-risk legacy surfaces:

- `run_geo_differential_expression_task()` exists in workflow tests, but it is legacy/testing and outside the C2 target gate stack.
- imported/testing DEG result display must not be treated as formal computation.
- `deg_executor_preflight` writes preflight inputs and manifests, but it explicitly sets `not_run=True`.

## 6. Carry-over Recommendation

Recommended scoped stages:

1. `Bioinformatics UI-C3b Formal DEG Contract Planning`
   - define formal DEG state/action/result schema contract
   - define exact executor source and dependency gate
   - define result registry and report-ready interactions
2. `Bioinformatics UI-C3c Formal DEG Disabled-by-default Runtime Wiring`
   - wire buttons and gate details, still disabled
   - expose only readiness diagnostics
3. `Bioinformatics UI-C3d Formal DEG Executor Pilot`
   - run only on explicit fixture/project storage
   - generate formal result only after confirmation gate
4. `Bioinformatics UI-C3e Formal DEG Result Review / Report Gate`
   - keep report/export disabled until result review is accepted

Do not combine ORA/GSEA, survival/KM, Cox, report generation, or export with the first formal DEG pilot.

## 7. Non-goals

This audit does not approve:

- ORA/GSEA execution
- survival/KM/log-rank execution
- Cox execution
- fake DEG table or fake plots
- volcano/heatmap generation
- report-ready package generation
- DOCX / HTML / PDF / CSV / XLSX export
- packaged app or UI-B10 work

## 8. Verification

Verification commands for this audit:

- `python3 -m pytest -q tests/ui/test_bioinformatics_gate_shell.py tests/ui/test_bioinformatics_analysis_tasks_gated_page.py tests/ui/test_bioinformatics_result_report_export_split_pages.py`
- `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_bioinformatics_workflow_pages.py`
- CSV structure check for `docs/ui/UI_C3a_bioinformatics_formal_deg_readiness_matrix_20260524.csv`
- `python3 -m app.main --smoke-test`

Results are recorded after the verification run.

Verification results:

| Command | Result |
| --- | --- |
| `python3 -m pytest -q tests/ui/test_bioinformatics_gate_shell.py tests/ui/test_bioinformatics_analysis_tasks_gated_page.py tests/ui/test_bioinformatics_result_report_export_split_pages.py` | passed, 13 tests |
| `python3 -m pytest -q tests/ui/test_bioinformatics_ia_shell.py tests/ui/test_bioinformatics_workflow_pages.py` | passed, 97 tests |
| CSV structure check for `docs/ui/UI_C3a_bioinformatics_formal_deg_readiness_matrix_20260524.csv` | passed, 18 rows |

## 9. Conclusion

Bioinformatics is ready for a scoped formal DEG planning stage. It is not ready to enable formal DEG execution in the ordinary UI.

The current safe state remains:

- `formal_deg.enabled=false`
- `resultSemanticKey != formal_computed_result` for preflight/testing/imported outputs
- `reportStatusKey != report_ready`
- `exportGate=disabled`
