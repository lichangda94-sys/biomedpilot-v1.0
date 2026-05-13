# Meta Analysis Legacy Migration Audit

## Audit Conclusion

`app/meta_analysis/legacy/` is a historical snapshot and reference area. It is not the current BioMedPilot Meta Analysis runtime boundary. Active Meta feature work must not directly depend on legacy modules, must not introduce new active imports from legacy, and must not copy legacy directories into active code.

Current exception: the active literature import and duplicate review path still contains a transitional adapter bridge that loads legacy `literature` parser and dedup components through `app/meta_analysis/adapters/literature_import_adapter.py`, `app/meta_analysis/adapters/duplicate_review_adapter.py`, and `app/meta_analysis/services/literature_batch_import_service.py`. This bridge is existing behavior only. It should be treated as technical debt to retire through focused tests and active replacements, not as permission to add more legacy dependencies.

## Migration Candidates / Whitelist For Future Review

These legacy ideas may be reviewed later, but only after an active Meta service gap is demonstrated:

- Artifact preview / result detail viewer ideas.
- Task execution log / lifecycle design ideas.
- Literature import / dedup edge-case handling.
- Analysis profile / rule config structure ideas.

Any future migration must be test-driven, file-whitelisted, and incremental. Do not copy a whole directory. Do not import legacy as a shortcut. Each migrated behavior should have an active Meta test that proves the missing behavior before the active implementation is added.

## Defer

These items are intentionally deferred:

- Manual runner.
- Retry foundation.
- Materialization UI.
- Packaging / local readiness scripts.

Reason: current Meta Analysis remains `Developer Preview / testing`. It has not yet entered a long-running task queue, scheduler, or production packaging hardening phase, so these legacy designs would add surface area before the active workflow needs them.

## Do Not Migrate / Blacklist

These items must not be migrated into active Meta Analysis:

- `app/meta_analysis/legacy/geo_readiness/`.
- GSE33630 / GPL570 / DEG-ready matrix logic.
- TCGA / GTEx / GEO submission readiness logic.
- Legacy app shell / main window.
- Scheduler / automatic task scanning / production downloader.
- Any Bioinformatics, GEO, TCGA, GDC, or GTEx dataset-analysis code.

Reason: these belong to Bioinformatics or to an old desktop shell. Current Meta Analysis owns literature evidence synthesis, not dataset-source retrieval, GEO readiness, TCGA/GDC project retrieval, GTEx tissue retrieval, DEG readiness, or data-analysis runners.

## Current Boundary State

- Active Meta search path: `app/meta_analysis/search/`.
- PubMed execution service: `app/meta_analysis/search/pubmed_search_service.py`.
- No `app/shared/literature_search/` package has been added.
- Shared language intelligence should provide general translation, medical vocabulary, disease guard, and `build_search_translation_draft(target_context="meta_analysis")` style behavior only. Shared code should not execute PubMed, GEO, TCGA, GDC, GTEx, WOS, Embase, or CNKI retrieval.
- Meta search must filter GEO, GSE, TCGA, and GTEx from concept blocks and rendered query drafts.
- Bioinformatics UI should not present PubMed, Web of Science, Embase, or CNKI as literature-search targets.
- Meta Analysis UI should not present GEO, GSE, TCGA, GDC, or GTEx as search targets.
- `app/meta_analysis/legacy/geo_readiness/` remains quarantined and must not be imported by active Meta code.

## Current Active Literature Import / Dedup Files

Active Meta literature import and dedup code currently includes:

- `app/meta_analysis/services/literature_import_service.py`: single-file NBIB/RIS/CSV import path, output registration, diagnostics generation, and audit events.
- `app/meta_analysis/services/literature_batch_import_service.py`: batch import wrapper for RIS/NBIB/CSV, source metadata, dedup mode, diagnostics path, warning path, and next-step summary.
- `app/meta_analysis/adapters/literature_import_adapter.py`: transitional adapter bridge from active Meta service to legacy parser output shape.
- `app/meta_analysis/services/duplicate_review_service.py`: duplicate candidate review task, duplicate group output, Data Center registration, and audit events.
- `app/meta_analysis/services/dedup_decision_service.py`: duplicate group loading, merge preview, duplicate review queue export, and interactive reviewer decisions.
- `app/meta_analysis/adapters/duplicate_review_adapter.py`: transitional adapter bridge from active Meta duplicate review to legacy duplicate detection.
- `app/meta_analysis/pages/literature_import_page.py`: Developer Preview UI state and page for RIS/NBIB/CSV import, diagnostics cards, warnings, failed examples, and duplicate-review handoff.
- `app/meta_analysis/pages/duplicate_review_page.py`: Developer Preview UI state and page for duplicate candidates, match reasons, merge preview, queue export, and reviewer decision options.

Current active capabilities:

- RIS, NBIB, and CSV file import.
- Import diagnostics JSON and warnings CSV.
- Missing title/author/year/DOI/PMID and invalid DOI/year warning summaries.
- Duplicate identifier counts in import diagnostics.
- Detect-only, manual-review, and skip dedup modes in the batch import request surface.
- Duplicate candidate group generation from normalized records.
- Manual duplicate review decisions, merge preview, duplicate review queue export, and reviewer-facing warnings.

## Legacy Literature Import / Dedup Files Reviewed

Legacy literature files with possible relevance:

- `app/meta_analysis/legacy/literature/adapters.py`: RIS, NBIB, CSV, and manual parser behavior, DOI extraction, CSV header aliases, publication type mapping, and clinical trial id extraction.
- `app/meta_analysis/legacy/literature/import_diagnostics.py`: import diagnostics counters, warning examples, duplicate identifier counts, and diagnostics/warnings writers.
- `app/meta_analysis/legacy/literature/normalize.py`: title, DOI, PMID, author, journal, year, publication type, creator, and normalized record construction.
- `app/meta_analysis/legacy/literature/dedup.py`: DOI/PMID exact matching, title/author matching, similar-title matching with year and journal checks, completeness-based primary record suggestion.
- `app/meta_analysis/legacy/literature/merge_service.py`: merged record construction, field-source tracing, and re-normalization after merge.
- `app/meta_analysis/legacy/literature/field_sanitizer.py`: system-field and unsupported-field filtering.
- `app/meta_analysis/legacy/literature/import_options.py`: UI, execution, and save option separation.
- `app/meta_analysis/legacy/literature/store.py`: JSON stores for import records, batches, normalized records, duplicate groups, merge results, and screening records.

Possible legacy edge capabilities to review later:

- More complete CSV header alias handling.
- Publication type and clinical trial id extraction.
- Field sanitization rules for imported payloads.
- Completeness-based primary record selection.
- Field-source tracing during merge preview or final merge.
- Similar-title duplicate matching thresholds that combine title, year, journal, and author signals.

Migration recommendation:

- Do not migrate legacy literature code now.
- First add active Meta tests that capture a concrete missing edge case, such as a specific CSV alias, DOI cleanup case, similar-title duplicate pair, or field-source merge trace.
- Then implement the behavior inside active Meta services or a new active Meta helper module.
- Keep the write scope narrow and avoid importing from `app/meta_analysis/legacy/`.
- After active replacements exist, retire the transitional adapter bridge in a separate compatibility stage.

## Boundary Guard Coverage

Existing boundary tests:

- `tests/architecture/test_module_retrieval_boundaries.py::test_shared_runtime_does_not_depend_on_product_modules` checks that active shared runtime code does not import Bioinformatics or Meta Analysis product modules.
- `tests/architecture/test_module_retrieval_boundaries.py::test_bioinformatics_runtime_does_not_call_literature_retrieval_services` checks that active Bioinformatics runtime code does not call literature retrieval services such as PubMed, WOS, Embase, CNKI, NBIB, RIS, Zotero, or EndNote service names.
- `tests/architecture/test_module_retrieval_boundaries.py::test_meta_runtime_does_not_call_bioinformatics_retrieval_services` checks that active Meta runtime code does not import Bioinformatics or call GEO/TCGA/GTEx retrieval services.
- `tests/architecture/test_module_retrieval_boundaries.py::test_legacy_literature_and_geo_readiness_modules_are_not_imported_by_mainline` checks that active mainline code does not import `app.meta_analysis.legacy.geo_readiness`.
- `tests/architecture/test_module_retrieval_boundaries.py::test_search_context_database_boundaries` checks that Bioinformatics and Meta SearchContext database allow/deny lists stay separated.
- `tests/ui/test_meta_analysis_workflow_pages.py::test_meta_protocol_search_strategy_payload_does_not_show_dataset_sources` and `test_meta_page_does_not_show_geo_tcga_gtex` check that Meta search draft output does not show GEO, GSE, TCGA, or GTEx.
- `tests/ui/test_bioinformatics_workflow_pages.py` includes UI coverage that Bioinformatics Chinese dataset search does not surface PubMed, PICO, literature search, or Meta Analysis wording in the dataset-search presentation.

No new boundary test was added in this audit stage because the requested guards are already covered at architecture and UI levels, except for the known transitional literature adapter bridge documented above. Adding a full "no active legacy literature import" test now would fail against existing active import/dedup behavior and should be deferred until the bridge is intentionally retired.
