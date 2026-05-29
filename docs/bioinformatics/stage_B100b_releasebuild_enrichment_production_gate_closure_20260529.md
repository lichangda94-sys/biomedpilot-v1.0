# B100b ReleaseBuild Enrichment Production Gate Closure

## Scope

B100b validates ReleaseBuild after B100 preflight, B100a scoped convergence, and the external R enrichment dependency refresh.

This stage checks whether the ReleaseBuild enrichment production hardening layer can remain in the internal-test candidate after `ReactomePA` and `msigdbr` were added to the local external R environment.

B100b does not publish ReleaseBuild, does not notarize, does not install R packages from BioMedPilot, does not download MSigDB, and does not enable clinical or biological interpretation.

## Current ReleaseBuild State

- Worktree: `/Users/changdali/Developer/biomedpilot v1.0/ReleaseBuild`
- Branch: `dev/release-internal-test`
- Validation HEAD: `f5d1c35`
- Existing uncommitted DEG input-adaptation work remains present and is out of scope for this closure:
  - `app/bioinformatics/analysis_ui/state.py`
  - `app/bioinformatics/deg_engine/__init__.py`
  - `tests/bioinformatics/test_analysis_ui_state.py`
  - `app/bioinformatics/deg_engine/input_adaptation.py`
  - `tests/bioinformatics/test_deg_input_adaptation_gate.py`
- Existing generated/untracked handoff outputs remain excluded:
  - `docs/release/ReleaseBuild_handoff_report_20260513.md`
  - `project_storage/external_engines/`
  - `external_engines/`

## B100 / B100a Closure Table

| Area | B100 status | B100a status | B100b result |
| --- | --- | --- | --- |
| Direct Bioinformatics B92-B99 copy | Blocked | Avoided | Passed; ReleaseBuild-native convergence preserved |
| ReleaseBuild ORA/GSEA schema compatibility | Required adapter | Implemented via `production_hardening.py` | Passed |
| Resource lock metadata | Missing checksum/file size for imported GMT | Added to `import_gmt_file` | Passed |
| Background / identifier gate | Required | Implemented for ORA and preranked GSEA | Passed |
| Statistical policy | Required | Implemented for ORA/GSEA parameter manifests | Passed |
| Formal-only production result schema gate | Required | Implemented | Passed |
| Production audit package primitive | Required | Implemented; explicit function only | Passed |
| Analysis UI preview | Not connected | Connected as review-only action | Passed |
| ReactomePA/msigdbr runtime blocker | Previously external-environment dependent | Detector supported them | Cleared |
| Package/open-W/codesign | Required after convergence | Passed on B100a | Re-run for B100b |

## External R Enrichment Runtime

Current real detection:

- Rscript: `/usr/local/bin/Rscript`
- R version: `R version 4.4.2 (2024-10-31)`
- architecture: `arm64`
- `clusterProfiler`: 4.14.6, available/importable
- `fgsea`: 1.32.4, available/importable
- `DOSE`: 4.0.1, available/importable
- `enrichplot`: 1.26.6, available/importable
- `ggplot2`: 3.5.2, available/importable
- `AnnotationDbi`: 1.68.0, available/importable
- `org.Hs.eg.db`: 3.20.0, available/importable
- `ReactomePA`: 1.50.0, available/importable
- `msigdbr`: 26.1.0, available/importable

Detector result:

- `status=passed`
- `blockers=[]`
- warning: `optional_r_package_missing:pathview:package_not_installed_or_not_on_libpaths:pathview`

The optional `pathview` warning is not a B100b blocker because ReleaseBuild does not enable pathview pathway diagram rendering in this stage.

## R Fixture Evidence

The external dependency registry fixture was executed through real Rscript:

- ORA fixture: generated TSV with `pvalue`, `p.adjust`, and `qvalue`.
- GSEA fixture: generated TSV with `NES`, `pval`, `padj`, and `leadingEdge`.
- Plot smoke: ORA dotplot, ORA barplot, and GSEA curve returned ggplot/enrichplot objects.

This validates runtime availability. It does not by itself bypass ORA/GSEA input gates, parameter confirmation, result schema gates, or report-ready gates.

## Production Gate Check

ReleaseBuild `app/bioinformatics/enrichment/production_hardening.py` remains the accepted production hardening surface:

- `build_enrichment_resource_lock(...)`
- `build_enrichment_background_identifier_gate(...)`
- `build_enrichment_statistical_policy(...)`
- `build_enrichment_production_result_schema_gate(...)`
- `build_enrichment_production_preview(...)`
- `create_enrichment_production_audit_package(...)`

Formal-only rule:

- `formal_computed_result` ORA/GSEA can enter the production schema/audit package gate.
- `imported_external_result`, `testing_level`, `exploratory`, and `preflight_only` remain blocked from formal production audit packages.

Report boundary:

- Enrichment production audit package creation does not set `report_ready_eligible=True`.
- ORA/GSEA section report-ready remains controlled by existing ORA/GSEA report gates.
- Full integrated report remains controlled by the full integrated report gate.

## UI Gate Closure

Analysis Center exposes:

- `enrichment_production_gate_rows`
- `developer_diagnostics.enrichment_production_preview`
- action row `enrichment_production_preview`

The UI action remains review-only:

- `button_behavior=enabled_review_only_no_package_write` only when all preview gates pass.
- blocked state uses `blocked_enrichment_production_gate` and explicit disabled reasons.
- UI state construction does not write audit packages.
- UI preview does not upgrade report-ready eligibility.

B100b also fixed a ReleaseBuild UI gate-shell compatibility regression found during full UI testing. The compatibility layer restores legacy read-only fields and action aliases used by the ReleaseBuild UI shell tests:

- `result_gate.fake_result_allowed`
- `result_gate.fake_plot_allowed`
- result semantic counts
- `report_gate.report_ready_package_allowed`
- `export_gate.export_enabled`
- aliases for `formal_ora`, `km_logrank`, `report_ready_package`, and `export_package`

These compatibility fields are read-only presentation fields and do not enable formal execution.

## Tests And Commands

Commands run:

```bash
git diff --check
python3 -m pytest tests/shared/test_external_dependency_registry.py -q
python3 -m pytest tests/bioinformatics/test_enrichment_production_hardening.py tests/bioinformatics/test_analysis_ui_state.py tests/bioinformatics/test_analysis_ui_action_rules.py -q
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_gate_shell.py tests/ui/test_bioinformatics_analysis_tasks_gated_page.py tests/ui/test_bioinformatics_data_check_group_design_gated_pages.py tests/ui/test_bioinformatics_result_report_export_split_pages.py -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

Observed results before final packaging rerun:

- `git diff --check`: passed.
- external dependency registry tests: 11 passed.
- enrichment / Analysis UI focused tests: 31 passed.
- bioinformatics full tests: 775 passed, 1 warning.
- UI gate-shell focused regression tests: 17 passed after the compatibility fix.
- UI full tests: 450 passed, 115 skipped.
- source smoke: passed, `git_head=f5d1c35`.

Final package/open-W/codesign results must be read from the B100b handoff response because package build metadata changes after the B100b commit is created.

## Blockers / Major / Minor

Blockers:

- None for ReleaseBuild enrichment production hardening internal-test closure.

Major:

- None found after the UI compatibility fix.

Minor:

- Optional `pathview` remains missing. It is not required for controlled ORA/GSEA, Reactome ORA detection, msigdbr metadata detection, or current SVG/enrichplot smoke.
- Production audit package export is still not exposed as a normal UI write action. It should remain an explicit future task because UI state construction must stay side-effect free.
- Existing out-of-scope DEG input-adaptation dirty files should be resolved in their own DEG stage before broader release-candidate cleanup.

## Boundaries Preserved

B100b does not:

- auto-install R/Bioconductor packages;
- bundle R packages into `BioMedPilot.app`;
- download MSigDB;
- enable phenotype-permutation GSEA;
- claim pathway activation or clinical interpretation;
- turn imported/testing/preflight enrichment outputs into formal results;
- make enrichment production preview a report-ready action;
- replace ReleaseBuild ORA/GSEA schemas with Bioinformatics B92-B99 standalone schemas.

## Conclusion

Conclusion label: `passed_internal_releasebuild_enrichment_candidate`.

ReleaseBuild can retain the scoped enrichment production-hardening convergence with the refreshed R enrichment backend. `ReactomePA` and `msigdbr` are no longer blockers in the current local environment.

## Recommendation

Proceed to the next scoped stage only if the next task is explicit. Reasonable next options:

1. Add an explicit user-triggered enrichment production audit package export UI action.
2. Run a ReleaseBuild candidate cleanup that resolves the out-of-scope DEG input-adaptation dirty files.
3. Start the next analysis-line production hardening stage after preserving the current ReleaseBuild candidate snapshot.
