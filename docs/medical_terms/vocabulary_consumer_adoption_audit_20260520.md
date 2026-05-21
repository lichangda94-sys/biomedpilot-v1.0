# Vocabulary Consumer Adoption Audit

Date: 2026-05-20

## Scope

This audit scans code and test paths for direct references to medical vocabulary source files. It reports potential bypasses of the scope-aware loader but does not refactor runtime code.

Scanned roots: `app/`, `scripts/`, `tests/`.

## Summary

- Findings: `73`
- Manual review required: `13`
- Runtime refactor executed: `false`
- Loader behavior modified: `false`

Classification counts:

- `approved_loader_internal`: 6
- `bioinformatics_scoped_allowed`: 3
- `legacy_meta_compatibility_allowed`: 2
- `manual_review_required`: 13
- `safe_test_fixture`: 49

## Findings

- `app/shared/query_intelligence/medical_terms/scope_loader.py:45` references `meta_migrated_from_shared_terms.json`; classification=`legacy_meta_compatibility_allowed`; risk=`low`; recommendation=Already part of the approved loader layer..
- `app/shared/query_intelligence/medical_terms/scope_loader.py:46` references `legacy_meta_compatibility_map.json`; classification=`legacy_meta_compatibility_allowed`; risk=`low`; recommendation=Already part of the approved loader layer..
- `app/shared/query_intelligence/medical_terms/scope_loader.py:47` references `meta_seed_terms.json`; classification=`approved_loader_internal`; risk=`low`; recommendation=Already part of the approved loader layer..
- `app/shared/query_intelligence/medical_terms/term_index_loader.py:14` references `mini_medical_terms_index.json`; classification=`approved_loader_internal`; risk=`low`; recommendation=Already part of the approved loader layer..
- `app/shared/query_intelligence/medical_terms/term_index_loader.py:70` references `zh_term_overrides.json`; classification=`approved_loader_internal`; risk=`low`; recommendation=Already part of the approved loader layer..
- `app/shared/query_intelligence/medical_terms/term_index_loader.py:72` references `mini_medical_terms_index.json`; classification=`approved_loader_internal`; risk=`low`; recommendation=Already part of the approved loader layer..
- `app/shared/query_intelligence/medical_terms/zh_overrides_loader.py:11` references `zh_term_overrides.json`; classification=`approved_loader_internal`; risk=`low`; recommendation=Already part of the approved loader layer..
- `app/shared/query_intelligence/meta_seed_terms/loader.py:11` references `meta_seed_terms.json`; classification=`approved_loader_internal`; risk=`low`; recommendation=Already part of the approved loader layer..
- `scripts/audit_medical_terms_scope_isolation.py:16` references `mini_medical_terms_index.json`; classification=`manual_review_required`; risk=`medium`; recommendation=load_terms(scope='<shared_core|meta_analysis|bioinformatics>') based on caller context.
- `scripts/audit_medical_terms_scope_isolation.py:16` references `zh_term_overrides.json`; classification=`manual_review_required`; risk=`medium`; recommendation=Use approved zh override loader or load_terms(scope=...) based on caller context.
- `scripts/audit_medical_terms_scope_isolation.py:20` references `mini_medical_terms_index.json`; classification=`manual_review_required`; risk=`medium`; recommendation=load_terms(scope='<shared_core|meta_analysis|bioinformatics>') based on caller context.
- `scripts/audit_medical_terms_scope_isolation.py:20` references `zh_term_overrides.json`; classification=`manual_review_required`; risk=`medium`; recommendation=Use approved zh override loader or load_terms(scope=...) based on caller context.
- `scripts/audit_medical_vocabulary_coverage.py:14` references `mini_medical_terms_index.json`; classification=`manual_review_required`; risk=`medium`; recommendation=load_terms(scope='<shared_core|meta_analysis|bioinformatics>') based on caller context.
- `scripts/audit_medical_vocabulary_coverage.py:15` references `zh_term_overrides.json`; classification=`manual_review_required`; risk=`medium`; recommendation=Use approved zh override loader or load_terms(scope=...) based on caller context.
- `scripts/inventory_shared_core_pollution.py:10` references `mini_medical_terms_index.json`; classification=`manual_review_required`; risk=`medium`; recommendation=load_terms(scope='<shared_core|meta_analysis|bioinformatics>') based on caller context.
- `scripts/inventory_shared_core_pollution.py:11` references `meta_seed_terms.json`; classification=`manual_review_required`; risk=`medium`; recommendation=load_terms(scope='meta_analysis').
- `scripts/inventory_shared_core_pollution.py:164` references `mini_medical_terms_index.json`; classification=`manual_review_required`; risk=`medium`; recommendation=load_terms(scope='<shared_core|meta_analysis|bioinformatics>') based on caller context.
- `scripts/inventory_shared_core_pollution.py:190` references `meta_migrated_from_shared_terms.json`; classification=`manual_review_required`; risk=`medium`; recommendation=load_terms(scope='meta_analysis').
- `scripts/prepare_medical_terms_review_batches.py:192` references `bioinformatics_data_type_terms.json`; classification=`bioinformatics_scoped_allowed`; risk=`low`; recommendation=load_terms(scope='bioinformatics').
- `scripts/prepare_medical_terms_review_batches.py:193` references `bioinformatics_data_type_terms.json`; classification=`bioinformatics_scoped_allowed`; risk=`low`; recommendation=load_terms(scope='bioinformatics').
- `scripts/prepare_medical_terms_review_batches.py:199` references `bioinformatics_species_terms.json`; classification=`bioinformatics_scoped_allowed`; risk=`low`; recommendation=load_terms(scope='bioinformatics').
- `scripts/update_medical_term_index.py:19` references `mini_medical_terms_index.json`; classification=`manual_review_required`; risk=`medium`; recommendation=load_terms(scope='<shared_core|meta_analysis|bioinformatics>') based on caller context.
- `scripts/update_medical_term_index.py:639` references `mini_medical_terms_index.json`; classification=`manual_review_required`; risk=`medium`; recommendation=load_terms(scope='<shared_core|meta_analysis|bioinformatics>') based on caller context.
- `scripts/update_medical_term_index.py:639` references `zh_term_overrides.json`; classification=`manual_review_required`; risk=`medium`; recommendation=Use approved zh override loader or load_terms(scope=...) based on caller context.
- `tests/shared/test_bioinformatics_geo_core_terms.py:32` references `bioinformatics_species_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_bioinformatics_geo_core_terms.py:56` references `bioinformatics_data_type_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_bioinformatics_geo_core_terms.py:82` references `bioinformatics_data_type_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_bioinformatics_geo_core_terms.py:124` references `bioinformatics_species_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_bioinformatics_geo_core_terms.py:142` references `bioinformatics_species_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_bioinformatics_geo_core_terms.py:144` references `bioinformatics_data_type_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_bioinformatics_gtex_tissue_terms.py:17` references `bioinformatics_tissue_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_bioinformatics_gtex_tissue_terms.py:79` references `bioinformatics_tissue_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_term_index_runtime_strategy.py:241` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_handoff_gap_remediation.py:67` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_handoff_gap_remediation.py:132` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_handoff_gap_remediation.py:133` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_handoff_gap_remediation.py:134` references `meta_seed_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_integration_audit.py:31` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_integration_audit.py:32` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_integration_audit.py:64` references `bioinformatics_species_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_integration_audit.py:65` references `bioinformatics_tissue_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_integration_audit.py:66` references `bioinformatics_data_type_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_review_batches.py:26` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_review_batches.py:27` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_terms_scope_routing.py:76` references `bioinformatics_data_type_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_vocabulary_cardiovascular_core.py:17` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_vocabulary_consolidation_regression.py:35` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_vocabulary_consolidation_regression.py:39` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_vocabulary_governance_release.py:13` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_vocabulary_governance_release.py:14` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_medical_vocabulary_immune_inflammatory_core.py:17` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_meta_scoped_mirror_from_shared.py:14` references `meta_migrated_from_shared_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_meta_scoped_mirror_from_shared.py:15` references `legacy_meta_compatibility_map.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_meta_scoped_mirror_from_shared.py:24` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_meta_scoped_mirror_from_shared.py:25` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_meta_scoped_mirror_from_shared.py:125` references `meta_migrated_from_shared_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_meta_scoped_mirror_from_shared.py:126` references `legacy_meta_compatibility_map.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_meta_scoped_mirror_from_shared.py:178` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_meta_scoped_mirror_from_shared.py:179` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_meta_scoped_mirror_from_shared.py:186` references `meta_migrated_from_shared_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_meta_scoped_mirror_from_shared.py:190` references `legacy_meta_compatibility_map.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_shared_core_pollution_inventory.py:20` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_shared_core_pollution_inventory.py:24` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_shared_core_pollution_inventory.py:25` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_shared_core_pollution_inventory.py:26` references `meta_migrated_from_shared_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_shared_core_pollution_inventory.py:27` references `legacy_meta_compatibility_map.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_vocabulary_consumer_manual_review.py:46` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_vocabulary_consumer_manual_review.py:47` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_vocabulary_consumer_manual_review.py:63` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_vocabulary_consumer_manual_review.py:64` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_vocabulary_consumer_manual_review.py:65` references `meta_seed_terms.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_vocabulary_stage_v0_1_merge_readiness.py:29` references `mini_medical_terms_index.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..
- `tests/shared/test_vocabulary_stage_v0_1_merge_readiness.py:30` references `zh_term_overrides.json`; classification=`safe_test_fixture`; risk=`low`; recommendation=No migration required for tests; use load_terms(scope=...) in new runtime-facing tests..

## Remediation Guidance

- Approved loader internals may continue direct file reads.
- Tests may continue direct reads when asserting file-level boundaries.
- Audit/build scripts may keep direct reads as reporting inputs, but must not become runtime lookup paths.
- Any runtime-adjacent direct consumer should migrate to `load_terms(scope=...)` in a separate implementation phase.
