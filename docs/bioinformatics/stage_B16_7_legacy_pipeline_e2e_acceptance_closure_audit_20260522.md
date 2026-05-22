# Bioinformatics B16.7 Legacy Pipeline E2E Acceptance / Closure Audit

Date: 2026-05-22

Workspace: `/Users/changdali/Developer/biomedpilot v1.0/Bioinformatics`

Branch: `dev/bioinformatics`

Baseline: `59c7f06 wire Bioinformatics legacy asset pipeline UI operations`

## Audit Scope

B16.7 audits the closed B16 legacy absorption pipeline:

- B16 legacy acquisition adapter manifests.
- B16.1 standardized asset candidate bridge.
- B16.2 candidate materialization gate.
- B16.3 repository manifest merge gate.
- B16.4 user-confirmed asset selection gate.
- B16.5 Analysis Center read-only pipeline exposure.
- B16.6 Analysis Center controlled pipeline operations.

The audit validates that legacy-derived assets can travel from adapter manifest to standardized repository default selection, while still remaining behind B8 resolver and downstream analysis gates.

Out of scope:

- formal DEG activation beyond existing controlled MVP gates.
- ORA/GSEA execution changes.
- KM/Cox/survival/clinical feature changes.
- formal plot/report-ready changes.
- automatic normalization, probe mapping, group design inference, or dependency installation.

Untracked files intentionally excluded:

- `docs/bioinformatics/Bioinformatics_handoff_report_20260513.md`
- `project_storage/bioinformatics/`

## Stage Acceptance Table

| Stage | Result | Evidence |
| --- | --- | --- |
| B16 adapter contract | Pass | Adapter manifests are written under `acquisition/legacy_adapter_manifests`; contract forbids formal result index, plot and report-ready outputs. |
| B16.1 candidate bridge | Pass | Candidate bundle writes `standardized_data/asset_candidates/legacy_acquisition_asset_candidates.json` and records `writes_analysis_input_repository=False`, `writes_result_index=False`. |
| B16.2 materialization | Pass | Materialization writes isolated repository files plus manifest/lineage only; tests assert no `analysis_input_repository` and no `result_index`. |
| B16.3 repository merge | Pass | Merge writes `repository_manifest.json`, validation report and lineage; assets remain `analysis_ready=False`, `formal_analysis_ready=False`, `result_semantics=not_a_result`. |
| B16.4 selection gate | Pass | User confirmation updates `default_asset_selection`; downstream blockers remain visible and formal analysis is not enabled. |
| B16.5 UI exposure | Pass | Analysis Center shows legacy pipeline rows and formal boundary state without calling mutation functions. |
| B16.6 UI operations | Pass | Analysis Center buttons call only B16 standardization-layer gates and preserve no-result side effects. |

## E2E Path Check

Accepted user path:

1. Legacy adapter manifest exists.
2. User builds legacy candidates.
3. User materializes candidates.
4. User merges materialized assets into standardized repository manifest.
5. User confirms default asset selection.
6. B8 resolver can inspect the standardized repository state.
7. Downstream DEG/ORA/GSEA/KM/Cox/report/plot gates still decide eligibility.

The path is accepted only as acquisition/standardization convergence. It does not create or imply formal analysis readiness.

## Boundary Checks

| Boundary | Result | Evidence |
| --- | --- | --- |
| No direct formal analysis runner | Pass | B16 UI operations call only candidate, materialization, repository merge and selection functions. |
| No `analysis_input_repository` write | Pass | E2E UI test asserts `standardized_data/repositories/analysis_input_repository` is absent after the full B16 UI chain. |
| No `result_index` write | Pass | E2E UI test asserts `results/summaries/result_index.json` is absent after the full B16 UI chain. |
| No formal result semantics | Pass | Candidate, materialized, merged and selected assets use `result_semantics=not_a_result`; validators block formalish assets. |
| No report-ready | Pass | B16 manifests keep `report_ready_eligible=False`; no report package function is called. |
| No plot artifact | Pass | B16 functions do not call plot registries or renderers. |
| GTEx normal-control boundary | Pass | GTEx selection records downstream blockers and resolver keeps GTEx normal-control/survival blockers. |
| UI does not mislead | Pass | UI copy says legacy pipeline is acquisition/standardization only and action rows use `controlled_standardization_artifact_write_no_formal_execution`. |

## Resolver / Downstream Gate Check

After B16.4/B16.6 selection, B8 resolver can use the repository default selection to remove multiple-expression ambiguity. That is intentionally not the same as formal execution readiness.

Formal DEG still requires:

- resolver package with no blockers.
- DEG-ready matrix gate.
- dependency gate.
- parameter manifest gate.
- user confirmation.
- result schema gate.

ORA/GSEA still require their enrichment-specific input/resource/result gates.

KM/Cox/survival/clinical still require B12-B14 gates and remain separated from legacy asset selection.

## UI Acceptance

Analysis Center now exposes:

- pipeline status rows for adapter, candidates, materialization, merge and selection.
- operation buttons gated by previous artifact presence.
- action matrix entries for review and controlled standardization operations.
- disabled/blocked reasons for missing previous artifacts.

The UI does not expose:

- legacy formal DEG execution.
- legacy GSEA/survival/clinical execution.
- legacy formal plot/report-ready execution.

## Tests And Validation

Commands run:

- `git diff --check` -> passed.
- `python3 -m pytest tests/bioinformatics/test_legacy_recognition_adapter.py tests/bioinformatics/test_geo_acquisition_adapter.py tests/bioinformatics/test_tcga_gtex_adapter_contract.py tests/bioinformatics/test_legacy_standardized_asset_bridge.py tests/bioinformatics/test_legacy_candidate_materialization_gate.py tests/bioinformatics/test_legacy_repository_manifest_merge_gate.py tests/bioinformatics/test_legacy_asset_selection_gate.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q` -> 38 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "legacy_pipeline_operations or userized_main_surface"` -> 2 passed, 108 deselected.
- `python3 -m pytest tests/bioinformatics -q -k "legacy or adapter or geo or tcga or gtex or recognition or standardization or resolver or analysis_ui"` -> 244 passed, 189 deselected.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or legacy or bioinformatics"` -> 110 passed.
- `python3 -m pytest tests/bioinformatics -q` -> 433 passed.
- `QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q` -> 177 passed.
- `python3 -m app.main --smoke-test` -> passed, `git_head=59c7f06`, `pyside6_available=True`.
- `python3 scripts/package_app.py --smoke-test` -> passed, `git_head=59c7f06`, `signing_status=ad_hoc_signed`.
- `open -W -n dist/BioMedPilot.app --args --smoke-test` -> passed.
- `codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app` -> passed.

## Issues

Blocker: none.

Major: none.

Minor:

- Legacy asset selection currently auto-confirms only when there is a single matching asset per role. Ambiguous multi-expression or multi-sample cases remain blocked until a future manual selection UI is added.
- B16 does not infer group design, normalize expression values, align samples, or resolve probe mappings. These are intentionally left to B8/downstream gates.

## Final Conclusion

完全通过.

B16 legacy absorption is closed for the current boundary. Legacy-derived GEO/TCGA/GTEx candidates can be reviewed and advanced into standardized repository/default-selection state, but they cannot bypass B8 resolver, DEG-ready, enrichment, survival/clinical, plot, or report-ready gates.

## Recommendation

Proceed to MainLine carry-over planning for B16 only after confirming the target branch already contains the B8-B14 gate baseline. ReleaseBuild should receive B16 through a scoped carry-over from MainLine, not by direct source tree replacement.
