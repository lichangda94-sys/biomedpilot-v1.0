# Bioinformatics B11.4 DEG / ORA / GSEA Enrichment Layer Closure Audit

Date: 2026-05-21

Baseline HEAD before this audit: `c6d0deaa94e3f7e48dc7b6bfd07d863980c10f0b` (`add Bioinformatics GSEA plot and report gates`)

Final audit status: **完全通过**

## 1. Audit Scope

This audit closes the current enrichment layer boundary across formal DEG, imported DEG review, controlled ORA, controlled preranked GSEA, plot artifact specs, section-only report-ready packages, Analysis Center gates, dependency detection, provenance, and E2E audit helpers.

Inspected surfaces:

- `app/bioinformatics/deg_engine/*`
- `app/bioinformatics/deg_ready/*`
- `app/bioinformatics/results/*`
- `app/bioinformatics/plots/*`
- `app/bioinformatics/reports/*`
- `app/bioinformatics/enrichment/*`
- `app/bioinformatics/gsea/*`
- `app/bioinformatics/analysis_inputs/*`
- `app/bioinformatics/analysis_task_runs.py`
- `app/bioinformatics/analysis_ui/*`
- `app/bioinformatics/workflow_pages.py`
- `config/bioinformatics/enrichment_defaults.yaml`
- `config/bioinformatics/package_requirements.yaml`
- B9/B10/B11 DEG/ORA/GSEA/result/plot/report/E2E/UI tests

Implementation added in this audit:

- `app/bioinformatics/enrichment/closure_audit.py`
- `tests/bioinformatics/test_enrichment_layer_closure_audit.py`

The helper is read-only: it audits existing `result_index.json`, plot artifacts, report package manifests, gene set registry, dependency snapshots, Analysis Center action rows, and E2E helper status. It does not execute DEG, ORA, GSEA, survival, plot rendering, or report generation.

## 2. Capability Matrix

| Capability | Current status | Allowed input | result_semantics | Plot status | Report-ready status | UI state in repo-root audit | Unsupported boundary |
|---|---|---|---|---|---|---|---|
| Formal DEG | implemented_and_gated | standardized DEG-ready package | formal_computed_result | formal DEG plot artifact/spec | formal DEG report package | blocked_missing_backend | no survival/clinical/full integrated report/pathway activation conclusions |
| Imported DEG review | implemented_review_only | imported DEG table | imported_external_result | imported plot path only | not formal report-ready | blocked_missing_input_package | no survival/clinical/full integrated report/pathway activation conclusions |
| Controlled ORA from formal DEG | implemented_and_gated | formal DEG result index | formal_computed_result | ORA plot artifact/spec | ORA report package | blocked_controlled_ora_gate | no survival/clinical/full integrated report/pathway activation conclusions |
| Controlled ORA from imported DEG | implemented_imported_derived | imported DEG result index | imported_external_result / imported_source_derived_result policy | imported-derived ORA plot/package | imported-derived ORA package | blocked_controlled_ora_gate | no survival/clinical/full integrated report/pathway activation conclusions |
| Controlled preranked GSEA from formal DEG | implemented_and_gated | formal DEG result index/rank metric | formal_computed_result | GSEA plot artifact/spec | GSEA report package | disabled_gsea_gate_not_passed | no survival/clinical/full integrated report/pathway activation conclusions |
| Controlled preranked GSEA from imported DEG | implemented_imported_derived | imported DEG result index/rank metric | imported_external_result / imported_source_derived_result policy | imported-derived GSEA plot/package | imported-derived GSEA package | disabled_gsea_gate_not_passed | no survival/clinical/full integrated report/pathway activation conclusions |
| ORA plot artifact/spec | implemented_spec_only | ORA result table | inherits source | spec-only; no PNG/SVG/PDF renderer | does not auto report-ready | blocked_ora_plot_gate | no survival/clinical/full integrated report/pathway activation conclusions |
| GSEA plot artifact/spec | implemented_spec_only | GSEA result table | inherits source | spec-only; no PNG/SVG/PDF renderer | does not auto report-ready | blocked_gsea_plot_gate | no survival/clinical/full integrated report/pathway activation conclusions |
| DEG report-ready package | implemented_section_only | formal DEG result | formal_computed_result | optional formal DEG plot/table-only | DEG section only | blocked_report_ready_gate | no survival/clinical/full integrated report/pathway activation conclusions |
| ORA report-ready package | implemented_section_only | ORA result | formal_computed_result / imported_external_result | ORA plot/table-only | ORA section only | blocked_ora_report_ready_gate | no survival/clinical/full integrated report/pathway activation conclusions |
| GSEA report-ready package | implemented_section_only | GSEA result | formal_computed_result / imported_external_result | GSEA plot/table-only | GSEA section only | blocked_gsea_report_ready_gate | no survival/clinical/full integrated report/pathway activation conclusions |
| Full integrated report | disabled_not_implemented | not supported | not applicable | not supported | disabled/not implemented | blocked_report_ready_gate | not implemented |
| Survival / KM / Cox | disabled_not_implemented | not supported | not applicable | KM plot disabled | disabled/not implemented | hidden_until_ready | not implemented |
| Clinical association statistics | disabled_not_implemented | not supported | not applicable | not supported | disabled/not implemented | hidden_until_ready | not implemented |

Note: repo-root UI states are disabled because the repository root is not a populated user analysis project. Fixture tests verify the enabled path for valid formal ORA/GSEA plot and section-only report packages.

## 3. Result Semantics Audit

Passed.

- Formal DEG remains `task_type=deg`, `result_semantics=formal_computed_result`.
- Imported DEG review remains `imported_external_result`.
- Formal DEG-derived ORA remains `task_type=ora_enrichment`, `source_result_semantics=formal_computed_result`.
- Imported-derived ORA is allowed only with imported source semantics and imported-derived warnings; it does not set `report_ready_eligible=True`.
- Formal DEG-derived GSEA remains `task_type=gsea_preranked`, `source_result_semantics=formal_computed_result`.
- Imported-derived GSEA is allowed only with imported source semantics and imported-derived warnings; it does not set `report_ready_eligible=True`.
- `testing_level`, `exploratory`, and `preflight_only` are blocked from report-ready artifacts.

Added regression coverage:

- raw expression source to ORA/GSEA is blocked.
- preflight ORA marked report-ready is blocked.
- imported-derived ORA/GSEA package remains non-formal.

## 4. Input Chain Audit

Passed.

Allowed chain:

- DEG: standardized repository / registry / analysis input repository -> DEG-ready -> confirmation -> formal DEG.
- ORA: formal/imported DEG result index -> ORA input gate -> gene set gate -> parameter gate -> controlled ORA.
- GSEA: formal/imported DEG result index -> GSEA input gate -> rank metric gate -> gene set gate -> parameter gate -> controlled preranked GSEA.

Blocked boundaries:

- ORA/GSEA from raw expression matrix.
- ORA/GSEA using `recognition_report.json` as formal input.
- ORA/GSEA generated from plot artifact or report package.
- GSEA from ORA result.
- ORA pretending to be GSEA ranked analysis.

## 5. Gene Set Resource Audit

Passed.

The closure audit now checks:

- `gene_set_resource_id` exists on ORA/GSEA result entries.
- parameter manifest includes the same `gene_set_resource_id`.
- project gene set registry contains the referenced resource.
- source/species/gene_id_type are visible in audit rows.
- external-source warning policy is enforced for audited external resources.

No automatic MSigDB/KEGG/GO/Reactome download path was added.

## 6. Dependency Audit

Passed.

- DEG dependency policy remains numpy/pandas/scipy/statsmodels for formal DEG.
- ORA dependency snapshot requires passed status and records scipy/statsmodels.
- GSEA dependency snapshot requires passed status and records numpy/pandas/scipy/statsmodels.
- Settings/Analysis Center dependency rows are detect-first and carry “no install action” text.
- Missing dependency snapshots block closure audit for ORA/GSEA formal paths.

## 7. Plot Artifact Audit

Passed.

- ORA plot artifact is spec-only and must be sourced from an ORA result.
- GSEA plot artifact is spec-only and must be sourced from a GSEA result.
- Plot artifacts inherit source result semantics.
- Plot artifacts do not render PNG/SVG/PDF in this stage.
- Plot artifacts do not enable report-ready on their own.
- Preflight/testing/exploratory sources cannot produce formal plot artifacts.

## 8. Report-Ready Package Audit

Passed.

- DEG package remains `formal_deg_only`.
- ORA package remains `formal_ora_only` or `imported_derived_ora_only`.
- GSEA package remains `formal_gsea_only` or `imported_derived_gsea_only`.
- Package manifests must declare `survival_enabled=false` and `clinical_conclusion_enabled=false`.
- Full integrated report artifacts are blocked.
- Imported-derived report packages are explicitly labeled and cannot upgrade to formal recomputed results.

## 9. E2E Helper Audit

Passed.

Existing helpers are present and callable:

- `audit_formal_deg_e2e_acceptance`
- `audit_ora_e2e_acceptance`
- `audit_gsea_e2e_acceptance`

The B11.4 closure helper summarizes these without executing new algorithms. Imported-derived ORA/GSEA package review is treated as imported-derived package integrity review, not as formal recomputation.

## 10. UI Boundary Audit

Passed.

- Analysis Center action rows expose ORA/GSEA readiness, run, plot, and report-ready disabled reasons.
- Survival formal and KM/Cox/log-rank remain hidden/disabled.
- Dependency rows are detect-only; no install action is exposed.
- ORA/GSEA plot/report buttons remain gate-driven.
- Current repo-root audit shows disabled states because no populated project inputs are present; fixture tests cover valid enabled gate paths.

## 11. Blocker / Major / Minor

Blockers: none.

Major issues: none.

Minor issues: none.

Small fix made during audit:

- Avoided circular import by lazily loading `build_analysis_center_state` inside the closure audit function.
- Added closure-level guardrails for result semantics, lineage, gene set registry, dependency snapshots, plot/report artifact ownership, section-only report manifests, UI dependency install wording, and completeness checks.

## 12. Verification Commands

Required commands:

```text
git diff --check
```

Result: passed.

```text
python3 -m pytest tests/bioinformatics -q -k "formal_deg or ora or gsea or enrichment or result_semantics or plot or report or e2e or analysis_ui"
```

Result: `182 passed, 343 deselected`.

```text
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "analysis_task or results_browser or report"
```

Result: `15 passed, 96 deselected`.

```text
python3 -m pytest tests/bioinformatics -q
```

Result: `525 passed`.

```text
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
```

Result: `268 passed`.

```text
python3 -m app.main --smoke-test
```

Result: passed.

Additional focused command:

```text
python3 -m pytest tests/bioinformatics/test_enrichment_layer_closure_audit.py -q
```

Result: `4 passed`.

Package preflight was not run because this audit did not modify packaging, runtime dependency, launcher, or codesign surfaces.

## 13. Final Conclusion

**完全通过.**

The DEG / ORA / GSEA enrichment layer is closed for the current MVP scope:

- formal DEG: two-group controlled DEG only;
- ORA: controlled ORA from formal or imported DEG result index entries;
- GSEA: controlled preranked GSEA from formal or imported DEG result index entries;
- plot: spec-only ORA/GSEA artifacts;
- report-ready: section-only DEG/ORA/GSEA packages.

Still not implemented and intentionally blocked:

- full integrated multi-section scientific report;
- survival / KM / Cox / log-rank / HR;
- clinical association statistics;
- clinical conclusion, diagnosis, treatment recommendation;
- pathway activation/inhibition conclusion;
- GSEA phenotype permutation;
- rendered volcano/heatmap/ORA/GSEA image output in this closure stage.

## 14. Recommendation

Recommendation: proceed only to a scoped carry-over or release-readiness step for the closed B9/B10/B11 MVP. Do not start survival, clinical statistics, or integrated report work until a separate task file defines gates and result semantics for those features.
