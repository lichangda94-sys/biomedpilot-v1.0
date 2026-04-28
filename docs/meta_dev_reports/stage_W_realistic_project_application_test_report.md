# Stage W Realistic Project Application Test Report

## Goal

Run Meta Analysis with PubMed-derived realistic literature metadata instead of relying only on mock literature records.

## Scenario

- Topic: hydroxychloroquine COVID-19 randomized trial binary treatment-effect OR validation.
- Source fixture: `examples/meta_analysis_realistic_project/inputs/pubmed_hydroxychloroquine_trials.csv`.
- Source provenance: read-only PubMed E-utilities metadata retrieval, no API key, no private-data upload.
- Long abstracts are omitted from committed fixtures.
- Binary 2x2 extraction values are manual validation seeds and are not asserted as published trial data.

## Chain Result

The realistic fixture can run through:

- Import
- Deduplication
- Screening decisions
- Full-text status
- ExtractionRecord save
- Quality assessment
- Analysis-ready dataset
- Random-effects OR meta-analysis
- Forest plot
- Funnel plot
- PRISMA summary
- Formal Markdown report
- HTML/DOCX testing exports
- Supplementary exports
- Project snapshot
- Reproducibility package

## Manual Bypasses

- Full-text review is seeded as available/include for included records.
- Extraction 2x2 values are manually seeded validation data.
- Quality assessment judgements are manually seeded.

## Artifacts Generated In Test Temp Project

- Root manifests: `project.json`, `data_manifest.json`, `artifact_manifest.json`, `task_manifest.json`, `lineage_manifest.json`.
- Report manifest: `reports/report_manifest.json`.
- Literature, screening, full-text, extraction, quality, analysis, figure, report, export, snapshot, and reproducibility artifacts.

## Findings

- Realistic metadata import works with CSV source input.
- The report is readable enough for internal beta but still clearly says Developer Preview / testing.
- Manifests and reproducibility package are complete enough for internal beta validation.
- Extraction remains the most manual step and needs real user feedback before broader beta.

## User Trial Blockers

- Users must not interpret manually seeded extraction values as true published data.
- Full-text workflow remains testing and partly seeded.
- Formal PDF is not implemented.
- Network meta remains not implemented.

## Validation

- `python -m compileall -q .`: not available in local shell (`python` command missing).
- `pytest -q`: not available in local shell (`pytest` command missing).
- `/Users/changdali/Documents/model9/.venv/bin/python -m compileall -q .`: passed.
- `/Users/changdali/Documents/model9/.venv/bin/python -m pytest -q`: 279 passed.
- `/Users/changdali/Documents/model9/.venv/bin/python scripts/run_tests.py`: 279 passed.
- `python3 -m app.main --smoke-test`: passed.
- `python3 scripts/package_app.py --smoke-test`: passed.
