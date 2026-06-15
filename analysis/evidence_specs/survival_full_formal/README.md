# Survival Full/Formal Evidence Specification

This directory contains templates and rules for future survival full/formal migration evidence.

It is not a full evidence bundle. It must not be used to mark survival as migrated, full-ready, or production-ready.

Required future acceptance data:

- `clinical_survival.tsv`
- `expression_or_signature.tsv`
- `input.json`
- `expected_result_manifest.json`
- `README.md`

Required future output package:

- `result.json`
- `provenance.json`
- `tables/survival_summary.tsv`
- `tables/km_logrank.tsv`
- `tables/cox_univariate.tsv`
- `tables/cox_multivariate.tsv`
- `plots/km_curve.svg`
- `plots/km_curve.png`
- `plots/cox_forest.svg`
- `reports/report.html`
- `logs/stdout.log`
- `logs/stderr.log`
- `logs/worker_invocation.json`
- `logs/r_session_info.txt`

Forbidden evidence sources are listed in `forbidden_sources.json`.
