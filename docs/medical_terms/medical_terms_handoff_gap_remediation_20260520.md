# Medical Terms Handoff Gap Remediation

Date: 2026-05-20

## Purpose

This stage closes governance gaps exposed by `medical_terms_phase_final_handoff_20260520.md`. It is report-only and policy-only: no vocabulary expansion, no shared-core cleanup execution, no loader changes, no online retrieval, and no PDF extraction work.

## Task Responses

- Task 1 Vocabulary Consumer Adoption Audit: `complete`. 73 findings; 13 current manual review items; previous `needs_scope_loader_migration` resolved to `0`.
- Task 2 Shared Core Strategy A Execution Plan: `complete`. Plan only; no shared core fields written.
- Task 3 gene expression profiling Routing Decision: `complete`. Decision recorded for Bioinformatics scoped routing; no runtime write.
- Task 4 Documentation Source-of-Truth Cleanup: `complete`. Index generated; old docs not deleted or edited.
- Task 5 Meta Seed Expansion Governance: `complete`. Curated-only rules recorded.
- Task 6 Emtree Mapping Review Plan: `complete`. No Emtree terms guessed.
- Task 7 Bioinformatics GEO Long-tail Candidate Intake Policy: `complete`. Candidate queue policy recorded.
- Task 8 Medical Terms Candidate Archive Policy: `complete`. Lifecycle states recorded.

## New Files

- `scripts/audit_vocabulary_consumers.py`
- `docs/medical_terms/vocabulary_consumer_adoption_audit_20260520.md`
- `data/medical_terms/review_reports/vocabulary_consumer_adoption_audit.json`
- `docs/medical_terms/shared_core_strategy_a_execution_plan_20260520.md`
- `data/medical_terms/review_reports/shared_core_strategy_a_execution_plan.json`
- `docs/medical_terms/gene_expression_profiling_routing_decision_20260520.md`
- `data/medical_terms/review_reports/gene_expression_profiling_routing_decision.json`
- `docs/medical_terms/medical_terms_source_of_truth_index_20260520.md`
- `data/medical_terms/review_reports/medical_terms_document_status_index.json`
- `docs/medical_terms/meta_seed_expansion_governance_20260520.md`
- `data/medical_terms/review_reports/meta_seed_expansion_governance.json`
- `docs/medical_terms/emtree_mapping_review_plan_20260520.md`
- `data/medical_terms/review_reports/emtree_mapping_review_plan.json`
- `docs/medical_terms/bioinformatics_geo_long_tail_intake_policy_20260520.md`
- `data/medical_terms/review_reports/bioinformatics_geo_long_tail_intake_policy.json`
- `docs/medical_terms/medical_terms_candidate_archive_policy_20260520.md`
- `data/medical_terms/review_reports/medical_terms_candidate_archive_policy.json`
- `docs/medical_terms/medical_terms_handoff_gap_remediation_20260520.md`
- `data/medical_terms/review_reports/medical_terms_handoff_gap_remediation.json`
- `tests/shared/test_medical_terms_handoff_gap_remediation.py`

## Still Not Executed

- No Meta seed expansion.
- No Bioinformatics term expansion.
- No mini_medical_terms_index.json modification.
- No zh_term_overrides.json modification.
- No shared core deprecated marking.
- No physical shared core deletion.
- No online retrieval.
- No PDF extraction UI or extraction workflow.
- No automatic screening or included studies.

## Requires User Confirmation

- Execute Shared Core Strategy A deprecation fields.
- Promote gene expression profiling into Bioinformatics scoped runtime file.
- Start Emtree manual review batch.
- Archive closed candidate batches.

## Unchanged Boundaries

- `mini_medical_terms_index_modified`: `false`
- `zh_term_overrides_modified`: `false`
- `meta_seed_expanded`: `false`
- `bioinformatics_terms_expanded`: `false`
- `online_search_enabled`: `false`
- `pdf_extraction_enabled`: `false`
- `loader_modified`: `false`

## Manual Review Required

- Consumer adoption audit manual review findings: `13`
- Strategy A execution: required before any shared-core deprecation write.
- `gene expression profiling` runtime promotion: required before writing Bioinformatics vocabulary.
- Emtree mapping: required before Embase query support.

## Follow-Up Recommendations

- Keep consumer adoption audit current when adding new vocabulary scripts or tests.
- Ask for explicit approval before Strategy A shared-core deprecation.
- Route gene expression profiling to Bioinformatics only after a dedicated vocabulary patch.
- Keep Meta seed expansion curated and capped at 50-100 terms per batch.
- Do not implement Embase retrieval until Emtree mappings are manually reviewed for high-priority seeds.

## Test Results

```bash
git diff --check
# passed
python3 -m pytest tests/shared/test_medical_terms_handoff_gap_remediation.py -q
# 8 passed
python3 -m pytest tests/shared/test_medical_terms_scope_routing.py -q
# 6 passed
python3 -m pytest tests/shared/test_medical_terms_integration_audit.py -q
# 5 passed
python3 -m pytest tests/shared/test_meta_seed_terms.py -q
# 9 passed
python3 -m pytest tests/shared/test_query_intelligence_service.py -q
# 21 passed
python3 -m pytest tests/meta_analysis -q
# 17 passed
python3 -m pytest tests/bioinformatics -q
# 238 passed
python3 -m app.main --smoke-test
# passed
```
