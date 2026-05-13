# Stage 2.5 Medical Vocabulary Coverage Audit Gap Fix

## Goal

Stage 2.5 closes the remaining partial or approximate findings from
`data/medical_terms/coverage_audit_report.json` using small, auditable mini
vocabulary updates.

## Modified Scope

- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- `data/medical_terms/reference_checklists/gtex_tissues_checklist.json`
- `data/medical_terms/source_metadata.json`
- `scripts/audit_medical_vocabulary_coverage.py`
- shared vocabulary tests under `tests/shared/`
- coverage audit outputs and this stage document

## Explicitly Not Done

- Did not enable the optional full ontology sqlite index.
- Did not modify Bioinformatics business code.
- Did not modify Meta Analysis business code.
- Did not change the shared query intelligence runtime path.
- Did not change the mini vocabulary JSON as the current stable primary path.

## Fixed Gaps

| Gap | Before | Fix |
| --- | --- | --- |
| cardiovascular | partial | Added a curated broad cardiovascular concept covering cardiovascular disease, heart disease, coronary artery disease, atherosclerosis, hypertension, and myocardial infarction. |
| neurodegenerative | partial | Added a curated broad neurodegenerative disease concept covering neurodegeneration, Alzheimer disease, Parkinson disease, and dementia. |
| autoimmune | partial | Added a curated broad autoimmune disease concept covering autoimmunity, rheumatoid arthritis, systemic lupus erythematosus, and inflammatory bowel disease. |
| GTEx Kidney | approximate | Expanded kidney tissue synonyms and marked the mini kidney tissue candidate as exact for the current shared vocabulary checklist. |
| GTEx Bladder | approximate | Expanded bladder tissue synonyms and marked the mini bladder tissue candidate as exact for the current shared vocabulary checklist. |

## Audit Before/After

Before Stage 2.5:

- Overall: 83 covered, 5 partial, 0 missing
- Coverage rate: 0.943
- Weighted coverage rate: 0.972
- P1 partial: cardiovascular, neurodegenerative, autoimmune, GTEx Kidney
- P2 partial: GTEx Bladder

After Stage 2.5:

- Overall: 88 covered, 0 partial, 0 missing
- Coverage rate: 1.000
- Weighted coverage rate: 1.000
- P0/P1/P2 gaps: none

## Tests

Validated with:

- `python3 scripts/audit_medical_vocabulary_coverage.py`
- `python3 -m pytest tests/shared/test_medical_vocabulary_reference_audit.py tests/shared/test_medical_vocabulary_coverage.py tests/shared/test_medical_vocabulary_systematic_coverage.py tests/shared/test_medical_term_lookup.py tests/shared/test_medical_term_index_runtime_strategy.py tests/shared/test_query_intelligence_service.py`
- `python3 -m compileall app/shared/query_intelligence scripts tests/shared`
- `QT_QPA_PLATFORM=offscreen python3 -m app.main --smoke-test`

## Follow-Up

V6 full ontology index remains a separate optional enhancement. Do not combine
that work with Stage 2.5 gap fixes.
