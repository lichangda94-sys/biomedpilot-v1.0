# Bioinformatics B23 Full Integrated Report Gate and Export Package Planning Task

Date: 2026-05-22

## Objective

Define the B23 implementation plan for a full integrated Bioinformatics report gate and export package.

B23 must not treat existing section-only report packages as a full integrated report. It must introduce an explicit full-report gate that can combine DEG, ORA, GSEA, KM/log-rank, Cox, plot artifacts, provenance, dependency snapshots, warnings, and limitations only when every required section is eligible.

This planning task does not enable full integrated report export.

## Current Capability Baseline

Available and audited:

- Formal DEG controlled two-group MVP with result index v2, plot artifact, and formal DEG section-only report-ready package.
- ORA controlled MVP with ORA section-only report-ready package.
- Preranked GSEA controlled MVP with GSEA section-only report-ready package.
- KM/log-rank controlled MVP with formal result semantics and `report_ready_eligible=False`.
- Cox univariate controlled MVP with formal result semantics and `report_ready_eligible=False`.
- Cox multivariate gated execution with formal result semantics and `report_ready_eligible=False`.
- B22 real SVG plot artifacts for formal KM/Cox results, still with survival report-ready disabled.
- Analysis UI capability map marks full integrated report as planned, not completed.

Not yet available:

- Survival/clinical report-ready package.
- Clinical association formal report-ready section.
- Full integrated report gate.
- Full integrated report export manifest/package.
- PDF/DOCX full report rendering.
- Any clinical diagnosis, prognosis, treatment advice, or automatic clinical conclusion.

## Hard Boundaries

B23 implementation must preserve:

- Section-only DEG/ORA/GSEA packages remain section-only.
- Full integrated report must be a separate `section_scope=full_integrated_report` package.
- Imported, testing, exploratory, and preflight outputs cannot be included as formal integrated sections.
- Legacy acquisition/standardization outputs cannot bypass B8 resolver or result semantics gates.
- KM/Cox plot artifacts do not make survival/clinical report-ready by themselves.
- No GSEA, survival, Cox, DEG, ORA, plot, or report artifact may upgrade source result semantics.
- No clinical diagnosis, prognosis conclusion, treatment recommendation, or validated risk score wording.
- No automatic dependency installation.

## B23 Gate Requirements

Add a dedicated full integrated report gate, suggested module:

- `app/bioinformatics/reports/integrated.py`
- tests: `tests/bioinformatics/test_integrated_report_gate.py`

Gate input:

- `project_root`
- optional explicit `section_result_ids`
- optional `include_sections`
- optional `allow_markdown_only`
- optional `allow_missing_optional_sections` default `False`

Required section classes for a full integrated report:

- `formal_deg`
- `ora_enrichment`
- `gsea_preranked`
- `survival_km_logrank`
- `cox_univariate` or `cox_multivariate`

Each included section must pass:

- result exists in result index v2.
- `result_semantics=formal_computed_result`.
- `task_type` matches the expected section.
- `input_package_id` exists.
- `parameters_manifest` exists.
- `dependency_snapshot.status=passed`, or dependency snapshot includes a section-specific passed policy.
- `validation_status` is `passed` or `warning`.
- no blockers.
- task-run log exists.
- warnings and limitations are available for export.
- source table artifacts exist and are readable.
- plot artifacts are either eligible real/spec artifacts for the section or table-only mode is explicitly allowed for that section.
- section-specific report-ready gate is passed where implemented.

Current planned blocker:

- Full integrated report must remain blocked while survival/clinical report-ready is not implemented. KM/Cox formal results and real plot artifacts are not enough to satisfy survival/clinical report-ready.

Suggested blocker IDs:

- `full_integrated_report_gate_not_implemented`
- `missing_required_section:<section>`
- `section_result_missing:<section>`
- `section_result_not_formal:<section>:<result_id>`
- `section_report_ready_gate_missing:<section>`
- `section_report_ready_not_passed:<section>:<result_id>`
- `section_source_table_missing:<section>:<artifact_type>`
- `section_plot_artifact_missing:<section>`
- `survival_clinical_report_ready_not_implemented`
- `non_formal_result_forbidden_in_full_integrated_report:<result_id>`
- `legacy_result_forbidden_in_full_integrated_report:<result_id>`
- `clinical_conclusion_forbidden`

## B23 Export Package Requirements

Suggested package path:

- `report_package/integrated/<timestamp>_<safe_project_name>/`

Required directories:

- `sections/`
- `tables/`
- `plots/`
- `manifests/`
- `logs/`
- `provenance/`

Required files:

- `integrated_report.md`
- `README_limitations.md`
- `integrated_report_package_manifest.json`
- `manifests/full_integrated_gate_snapshot.json`
- `manifests/result_index_snapshot.json`
- `manifests/section_manifest.json`
- `manifests/dependency_snapshot.json`
- `manifests/warnings_limitations.json`
- `manifests/package_inventory.json`

Section subfiles:

- `sections/formal_deg.md`
- `sections/ora.md`
- `sections/gsea.md`
- `sections/survival_km.md`
- `sections/cox.md`

Artifact copy policy:

- Copy source tables into `tables/`.
- Copy only registered plot artifacts into `plots/`.
- Copy task-run logs into `logs/`.
- Copy parameter confirmations and dependency snapshots into `manifests/`.
- Do not copy runner temp files.
- Do not copy preflight-only, testing-level, exploratory, imported-derived, or legacy-only outputs as formal sections.

Overwrite policy:

- Always create a new timestamped package directory.
- Never overwrite existing package output.
- Return `user_visible_package_path`.
- Return explicit failure reason if package creation fails.

## Renderer Policy

Markdown can be the first implemented export format.

PDF/DOCX must be gated by an external renderer capability snapshot, such as:

- `renderer.pandoc.available`
- `renderer.quarto.available`
- `renderer.latex.available`
- `renderer.wkhtmltopdf.available`

Renderer missing behavior:

- Markdown package may be created only after full integrated gate passes.
- PDF/DOCX must be blocked gracefully with renderer disabled reason.
- Missing renderer must not traceback.
- No auto-install action.

## UI Requirements

Analysis Center:

- Keep `full_integrated_report` as not completed until the B23 gate passes and a package is exported.
- Add a full integrated report gate row showing section coverage.
- Show disabled reason when survival/clinical report-ready is missing.
- Show included sections, result IDs, semantics, validation status, dependency status, plot status, and section report-ready status.
- Keep section-only report buttons separate from full integrated report export.

Results Browser:

- Add full integrated report preview only after gate passes.
- Show package output path.
- Show package inventory and gate snapshot.
- Show limitations and "statistical research report only" boundary.

Settings:

- Show renderer capability status detect-first.
- No install buttons.

## Testing Plan

Add focused tests:

- `tests/bioinformatics/test_integrated_report_gate.py`
- `tests/bioinformatics/test_integrated_report_package.py`
- UI focused tests in `tests/ui/test_bioinformatics_workflow_pages.py`

Required assertions:

- Full integrated report gate blocks when survival/clinical report-ready is missing.
- Full integrated report gate blocks if any required section result is missing.
- Full integrated report gate blocks imported/testing/exploratory/preflight sources.
- Section-only DEG/ORA/GSEA report packages are not labeled as full integrated report.
- Real KM/Cox plot artifact alone does not enable survival report-ready.
- Missing plot artifact cannot be claimed as included figure.
- Markdown package includes all required manifests only after the full gate passes.
- PDF/DOCX export is disabled when renderer capability is missing.
- Package path is timestamped and non-overwriting.
- Package content can be independently audited from `result_index_snapshot.json`, section manifests, dependency snapshots, logs, warnings, and limitations.
- No clinical conclusion, diagnosis, prognosis, treatment recommendation, or risk score interpretation appears in full integrated report text.

Suggested validation commands:

```bash
git diff --check
python3 -m pytest tests/bioinformatics/test_integrated_report_gate.py tests/bioinformatics/test_integrated_report_package.py -q
python3 -m pytest tests/bioinformatics -q -k "report or integrated or formal_deg or ora or gsea or survival or cox or plot"
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/test_bioinformatics_workflow_pages.py -q -k "report or results_browser or analysis_task"
python3 -m pytest tests/bioinformatics -q
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q
python3 -m app.main --smoke-test
python3 scripts/package_app.py --smoke-test
open -W -n dist/BioMedPilot.app --args --smoke-test
codesign --verify --deep --strict --verbose=2 dist/BioMedPilot.app
```

## Implementation Sequence

### B23.1 Full Integrated Report Gate

- Add `evaluate_full_integrated_report_gate`.
- Select and validate section source results.
- Preserve blocked status while survival/clinical report-ready is missing.
- Expose gate snapshot in Analysis Center diagnostics.

### B23.2 Full Integrated Report Package Skeleton

- Add package manifest schema.
- Create timestamped output directory.
- Write `integrated_report.md`, `README_limitations.md`, section manifests, result index snapshot, dependency snapshot, logs, and inventory.
- Keep package creation blocked unless B23.1 gate passes.

### B23.3 UI Preview and Disabled Reasons

- Add Analysis Center full integrated gate row.
- Add Results Browser full integrated report preview/export control.
- Ensure section-only package buttons remain separate.

### B23.4 Renderer Format Gate

- Keep Markdown as the first supported format.
- Add PDF/DOCX disabled states from external renderer capability snapshot.

### B23.5 End-to-End Acceptance Audit

- Build a controlled fixture with DEG, ORA, GSEA, KM, Cox, and plot artifacts.
- Verify full gate status, package inventory, source result traceability, and no clinical conclusion wording.

## Current Recommendation

Proceed to B23.1 only if the goal is to add a blocked full integrated gate and UI visibility first.

Do not claim full integrated report completion until survival/clinical report-ready is implemented and the full integrated gate passes.
