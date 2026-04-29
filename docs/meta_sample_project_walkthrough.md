# Meta Analysis Sample Project Walkthrough

The committed sample project contains source inputs only:

- `examples/meta_analysis_e2e_project/inputs/mock_literature.csv`
- `examples/meta_analysis_e2e_project/inputs/mock_literature.ris`
- `examples/meta_analysis_realistic_project/inputs/pubmed_hydroxychloroquine_trials.csv`
- `examples/meta_analysis_realistic_project/inputs/pubmed_hydroxychloroquine_trials.ris`
- `examples/meta_analysis_realistic_project/inputs/pubmed_retrieval_history_fixture.json`
- `examples/meta_analysis_internal_beta_samples/treatment_effect_binary_or/inputs/literature.csv`
- `examples/meta_analysis_internal_beta_samples/biomarker_prevalence_correlation/inputs/literature.csv`

The Stage W realistic sample is PubMed-derived metadata for hydroxychloroquine COVID-19 randomized trial validation. Its committed fixture omits long abstracts, and software tests use manually seeded binary extraction values for internal beta chain validation.

The AB13 internal beta sample pack adds:

- `treatment_effect_binary_or`: expected 3 imports, 1 duplicate, 2 included studies, binary OR seeded extraction.
- `biomarker_prevalence_correlation`: expected 3 imports, no duplicates, prevalence and correlation seeded extraction.

Each sample includes an `expected_manifest.json` with expected counts, seeded extraction notes, expected analysis behavior, and known limitations.

Generated outputs are intentionally produced in temporary test projects and are not committed.

Expected internal beta artifacts:

- root project manifests
- literature records
- screening decisions
- extraction records
- quality assessments
- analysis-ready datasets
- analysis results
- forest and funnel plots
- report manifest
- formal Markdown/HTML/DOCX testing report
- supplementary exports
- reproducibility package

Missing artifacts should be shown as warnings or `missing / not generated`, not as crashes.
