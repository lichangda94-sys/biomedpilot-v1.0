# Medical Terms Phase Final Handoff

Date: 2026-05-20

## Scope

This handoff summarizes the completed medical terms work across Bioinformatics scoped vocabulary, Meta seed vocabulary, scope-aware routing, and shared-core cleanup decision reporting.

This document is a summary artifact only. It does not modify runtime behavior, shared core, Bioinformatics vocabulary, Meta seed files, loader routing, search execution, or PDF extraction.

## Current Branch State

Relevant phase commits:

- `61f02a6` `feat(medical-terms): complete bioinformatics geo core terms`
- `5287f00` `feat(medical-terms): resolve bioinformatics gtex tissue mappings`
- `e55867b` `feat(medical-terms): refine bioinformatics geo core mappings`
- `9caf33a` `feat(medical-terms): add meta seed mapping extraction mvp`
- `f44db92` `feat(medical-terms): expand meta curated seed batch 2`
- `f983252` `docs(medical-terms): audit meta seed MVP`
- `50f3b56` `test(medical-terms): audit vocabulary integration boundaries`
- `f8da814` `test(medical-terms): inventory shared core vocabulary pollution`
- `e5f9e17` `docs(medical-terms): add scope usage annotation schema`
- `c52438b` `feat(medical-terms): mirror meta scoped terms from shared core`
- `7f6e711` `fix(medical-terms): route migrated terms by scope`
- `927f998` `docs(medical-terms): record shared core cleanup decision`

## Bioinformatics Handoff

Source directories:

- `data/medical_terms/bioinformatics/`
- `data/medical_terms/bioinformatics/audits/`
- `tests/shared/test_bioinformatics_geo_core_terms.py`
- `tests/shared/test_bioinformatics_gtex_tissue_terms.py`
- `tests/bioinformatics/`

Implemented vocabulary files:

- `bioinformatics_species_terms.json`
- `bioinformatics_grouping_terms.json`
- `bioinformatics_data_type_terms.json`
- `bioinformatics_dataset_registry_terms.json`
- `bioinformatics_stop_terms.json`
- `bioinformatics_tissue_terms.json`

GEO status:

- GEO audit source of truth: `data/medical_terms/bioinformatics/audits/geo_core_terms_coverage_audit.json`
- Final summary: total `54`, complete `46`, missing `0`, needs_review `0`, approved_with_note `8`.
- `mouse` is a synonym of `Mus musculus`, not a standalone species concept.
- `TPM`, `FPKM`, `RPKM`, and `CPM` are normalized expression terms, not raw-count terms.
- `raw counts` and `count matrix` remain DESeq2/edgeR candidates.
- `series matrix` and `sample metadata` are GEO file or metadata types, not expression matrices.
- `dataset`, `sample`, and `series` are scoped stop terms for free topic expansion only; they do not block GEO structure/file/sample metadata detection.
- All GEO scoped terms are Bioinformatics-only with `shared_core_allowed=false` and `meta_scope_allowed=false`.

GTEx status:

- GTEx audit source of truth: `data/medical_terms/bioinformatics/audits/gtex_terms_coverage_audit.json`
- Final summary: total `23`, complete `18`, missing `0`, needs_review `0`, approved_with_subtype_mapping `3`, complete_with_note `2`.
- `Skin`, `Heart`, and `Artery` are parent terms requiring subtype mapping.
- `Muscle` maps to `Muscle - Skeletal` with Chinese preferred term `骨骼肌`.
- `Nerve` maps to `Nerve - Tibial` with Chinese preferred term `胫神经`.
- Broad Chinese entries such as `皮肤`, `心脏`, `肌肉`, `动脉`, and `神经` remain low-weight entry terms and do not override concrete GTEx subtypes.

Bioinformatics boundary:

- Bioinformatics loads its scoped vocabulary and shared core through scope-aware routing.
- Bioinformatics does not load Meta migrated mirror terms.
- Bioinformatics does not activate legacy Meta compatibility mappings.
- Bioinformatics scoped vocabulary remains separate from Meta PICO/query-expansion vocabulary.

## Meta Seed Handoff

Source directories:

- `data/medical_terms/meta_analysis/`
- `app/shared/query_intelligence/meta_seed_terms/`
- `tests/shared/test_meta_seed_terms.py`
- `tests/shared/test_query_intelligence_service.py`
- `tests/meta_analysis/`

Current seed layer:

- `meta_seed_terms.json`: `190` curated seed concepts.
- `meta_seed_terms_schema.json`: schema for curated seed entries.
- `mesh_mappings.json`: `152` disease/exposure/intervention/outcome mapping rows.
- `pubmed_free_text_mappings.json`: `152` disease/exposure/intervention/outcome mapping rows.
- `emtree_mappings.json`: `190` placeholder rows, with unknown Emtree values kept as `emtree_review_status=needs_review`.

Seed distribution:

- disease / population: `50`
- exposure: `35`
- intervention: `30`
- outcome: `37`
- effect / statistical term: `14`
- study design: `12`
- research intent: `12`

Meta helper capabilities:

- Curated seed loading and validation.
- PubMed query block generation from manual MeSH/free-text mappings.
- Chinese question matching to seed concepts.
- PICO/PECO draft generation.
- Deterministic research-intent classification.
- English text cleanup, section detection, References exclusion, regex evidence candidates, and outcome/effect pending-review binding.

Query guard status:

- Effect/statistical terms do not enter PubMed topic expansion.
- Research-intent terms do not enter PubMed topic expansion.
- Study-design terms are filter-only.
- Outcome terms are conditional and require disease/population pairing.
- English extraction emits `pending_review` rows only and does not write formal extraction records.

Validated Chinese examples:

- `糖尿病前期与甲状腺癌风险的关系`
- `二甲双胍治疗2型糖尿病的疗效`
- `放射性碘治疗甲状腺癌复发的影响`
- `肥胖与乳腺癌风险的Meta分析`

Meta workflow status:

- Meta search config can produce local PICO/PECO and PubMed query drafts.
- Search draft review gate supports `draft_only`, `needs_edit`, `user_confirmed`, and `rejected`.
- PubMed preflight can generate `search_execution_plan.json` from confirmed plans.
- Online retrieval is not executed.

Explicit unsupported behavior:

- No Chinese database retrieval.
- No Chinese PDF extraction.
- No English PDF extraction UI.
- No automatic literature screening.
- No automatic included-study decisions.
- No automatic formal extraction-table writes.
- No Meta statistical analysis execution from this vocabulary phase.

## Scope Routing Handoff

Source files:

- `app/shared/query_intelligence/medical_terms/scope_loader.py`
- `app/shared/query_intelligence/medical_terms/__init__.py`
- `tests/shared/test_medical_terms_scope_routing.py`
- `docs/medical_terms/loader_routing_compatibility_20260520.md`

Implemented API:

- `load_terms(scope="shared_core")`
- `load_terms(scope="meta_analysis")`
- `load_terms(scope="bioinformatics")`
- `find_terms(query, scope=...)`
- `resolve_legacy_concept_id(concept_id, scope=...)`

Routing behavior:

- `shared_core` loads shared-core data only.
- `meta_analysis` loads shared core, Meta seed terms, `meta_migrated_from_shared_terms.json`, and `legacy_meta_compatibility_map.json`.
- `bioinformatics` loads shared core and Bioinformatics scoped vocabularies.
- Bioinformatics scope does not load `meta_migrated_from_shared_terms.json`.
- Bioinformatics scope does not load `legacy_meta_compatibility_map.json`.

Compatibility examples:

- `mini:meta_outcomes_core` resolves to `meta_outcome:overall_survival` in Meta scope.
- `mini:meta_analysis_overall_survival` resolves to `meta_outcome:overall_survival` in Meta scope.
- `mini:study_design_core` resolves to `meta_study_design:randomized_controlled_trial` in Meta scope.
- `mini:meta_analysis_quadas_2` resolves to `meta_quality_tool:quadas_2` in Meta scope.
- `survival data` resolves as `meta_data_context:survival_data`, not as an `overall survival` synonym.
- `gene expression profiling` does not enter Meta migrated compatibility.

Scope isolation:

- Meta can resolve `overall survival`, `hazard ratio`, `randomized controlled trial`, and `QUADAS-2`.
- Bioinformatics does not treat those Meta migrated concepts as active Bioinformatics scoped terms.
- Bioinformatics still loads `TPM`, `FPKM`, `raw counts`, GTEx/GEO terms, and scoped stop terms.
- Meta does not treat `TPM`, `FPKM`, `GSE`, `GSM`, or `series matrix` as PICO main terms.

## Shared Core Cleanup Decision Handoff

Source files:

- `data/medical_terms/review_reports/shared_core_pollution_inventory.json`
- `data/medical_terms/review_reports/shared_core_pollution_manual_review.jsonl`
- `data/medical_terms/meta_analysis/meta_migrated_from_shared_terms.json`
- `data/medical_terms/meta_analysis/legacy_meta_compatibility_map.json`
- `data/medical_terms/review_reports/meta_scoped_mirror_conflicts.jsonl`
- `data/medical_terms/review_reports/shared_core_cleanup_decision.json`
- `docs/medical_terms/shared_core_cleanup_decision_20260520.md`

S1-S5 status:

- Suspected shared-core pollution count: `177`.
- Manual review count: `50`.
- Mirrored Meta scoped count: `48`.
- Compatibility mapping count: `48`.
- Excluded from Meta mirror: `1`.
- Routing status: `passed`.

Meta mirror status:

- Confirmed Meta-scope shared rows were mirrored into `meta_migrated_from_shared_terms.json`.
- Legacy IDs are mapped through `legacy_meta_compatibility_map.json`.
- `overall survival` is represented once as `meta_outcome:overall_survival`, with both legacy IDs mapped to the canonical concept.
- `survival data` is a context/extraction concept, not an `overall survival` synonym.
- All mirrored terms are Meta-only with `shared_core_allowed=false`, `bioinformatics_allowed=false`, and `meta_analysis_allowed=true`.

Non-Meta routing item:

- `gene expression profiling` remains `bioinformatics_candidate_migration_required`.
- It was not mirrored into Meta scoped vocabulary.
- Future work should decide whether it belongs in Bioinformatics scoped vocabulary or remains a manual routing item.

Cleanup decision:

- Recommended default strategy: Strategy A, mark deprecated or `active_in_shared=false` in a future phase.
- Strategy B, moving rows to `archive/shared_core_deprecated_terms.json`, is deferred until Strategy A and consumer audits are proven safe.
- Strategy C, physical deletion, is not recommended as default.
- No cleanup action was executed in S5.
- Any cleanup action requires explicit user confirmation.

Protected files not modified by S5:

- `data/medical_terms/mini_medical_terms_index.json`
- `data/medical_terms/zh_term_overrides.json`
- loader routing files
- Meta seed files
- Bioinformatics vocabulary files

## Validation Snapshot

Most recent full validation across the scope-routing and cleanup decision phase:

```bash
git diff --check
# passed
python3 -m pytest tests/shared/test_medical_terms_scope_routing.py -q
# 6 passed
python3 -m pytest tests/shared/test_meta_scoped_mirror_from_shared.py -q
# 7 passed
python3 -m pytest tests/shared/test_medical_terms_integration_audit.py -q
# 5 passed
python3 -m pytest tests/meta_analysis -q
# 17 passed
python3 -m pytest tests/bioinformatics -q
# 238 passed
python3 -m app.main --smoke-test
# passed
```

Current handoff validation:

```bash
git diff --check
# passed
python3 -m pytest tests/shared/test_medical_terms_scope_routing.py tests/shared/test_meta_scoped_mirror_from_shared.py tests/shared/test_meta_seed_terms.py tests/shared/test_query_intelligence_service.py -q
# 43 passed
python3 -m app.main --smoke-test
# passed
```

## Source Of Truth Notes

Use these machine-readable files for current status:

- GEO current audit: `data/medical_terms/bioinformatics/audits/geo_core_terms_coverage_audit.json`
- GTEx current audit: `data/medical_terms/bioinformatics/audits/gtex_terms_coverage_audit.json`
- Meta seed current list: `data/medical_terms/meta_analysis/meta_seed_terms.json`
- Meta mapping files: `mesh_mappings.json`, `pubmed_free_text_mappings.json`, `emtree_mappings.json`
- Scope mirror: `data/medical_terms/meta_analysis/meta_migrated_from_shared_terms.json`
- Legacy compatibility: `data/medical_terms/meta_analysis/legacy_meta_compatibility_map.json`
- Shared cleanup decision: `data/medical_terms/review_reports/shared_core_cleanup_decision.json`

Some older human-readable coverage summaries under `docs/medical_terms/` may describe pre-fix states. For final operational status, prefer the machine-readable audit JSON files and the stage-specific tests listed above.

## Recommended Next Steps

1. Review and explicitly approve or reject Strategy A before any shared-core deprecation fields are written.
2. Decide the routing target for `gene expression profiling`.
3. Keep Meta seed expansion curated and separate from external Chinese corpus candidates.
4. Do not enable online retrieval until execution logging, database selection, rate-limit handling, and result persistence are designed.
5. Keep Bioinformatics GEO/GTEx/TCGA technical terms out of Meta PICO/query expansion.
6. Keep Meta outcome/effect/study-design/research-intent vocabulary out of Bioinformatics scoped loading.
