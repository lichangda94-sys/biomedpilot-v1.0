# B48 Risk Score / Survival Integrated Report UX Audit

Date: 2026-05-27

## Scope

B48 audits and hardens the Results Browser UX around survival / clinical section packages and the optional risk score validation section in full integrated report packaging.

This stage does not add clinical interpretation, risk groups, cutoff selection, treatment advice, or automatic risk score inclusion.

## UX Changes

- Survival / clinical section package panel now shows KM, Cox, and risk score validation report-ready gates.
- Risk score validation has its own section package button and table-only checkbox.
- Full integrated report preview has an explicit checkbox: include risk score validation section.
- Full integrated preview and package generation pass `risk_score_validation` only when the checkbox is selected.
- The preview plan displays optional section policy and whether risk score validation is included.
- Status copy says risk score validation is optional and does not create clinical diagnosis, prognosis, risk group, or treatment recommendation.

## Gate Behavior

Default full integrated report generation still uses only:

- formal DEG
- ORA enrichment
- preranked GSEA
- KM/log-rank survival
- Cox clinical association

When the risk score checkbox is selected, UI calls the full integrated gate with:

- `include_sections=[formal_deg, ora_enrichment, gsea_preranked, survival_km_logrank, cox, risk_score_validation]`
- `section_result_ids={"risk_score_validation": <selected risk score result>}` when a selected risk score result exists

If the B46 risk score validation section package is missing, the integrated gate remains blocked and surfaces the package prerequisite blocker.

## Boundaries Preserved

- No automatic risk score inclusion in full integrated report.
- No clinical conclusion, prognosis label, treatment recommendation, risk group, or cutoff generation.
- Rendered DOCX/PDF exports remain package artifacts only.
- No result index write from renderer exports.
- Imported/testing/exploratory/preflight results are not upgraded.

## Verification

- `python3 -m py_compile app/bioinformatics/workflow_pages.py`
- `QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests/ui/test_bioinformatics_workflow_pages.py -k "full_integrated or survival_clinical_section_report"`
