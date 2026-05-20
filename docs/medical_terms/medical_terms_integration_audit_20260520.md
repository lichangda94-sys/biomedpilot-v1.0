# Medical Terms Integration Audit

Date: 2026-05-20

## 1. Audit Purpose

This audit verifies the integration boundaries across shared medical terms, Bioinformatics vocabulary, Meta seed terms, query intelligence, Meta search draft review, and PubMed preflight planning.

This stage is audit-focused. It does not expand seed vocabularies and does not enable real retrieval.

## 2. Current Vocabulary Architecture

The current vocabulary system has three practical layers:

- Shared core: `data/medical_terms/mini_medical_terms_index.json` and `data/medical_terms/zh_term_overrides.json`.
- Bioinformatics scoped vocabularies: `data/medical_terms/bioinformatics/`, including species, GTEx tissues, GEO data types, grouping terms, dataset registry terms, scoped stop terms, and coverage audits.
- Meta scoped vocabularies and helpers: `data/medical_terms/meta_analysis/` plus `app/shared/query_intelligence/meta_seed_terms/`, providing curated Meta seeds, MeSH/PubMed free-text mappings, PICO/intent matching, query guard, and extraction-oriented helper functions.

Meta search workflow currently remains local and staged:

`Chinese question -> seed matching -> PICO/PECO draft -> PubMed query draft -> user review gate -> confirmed_search_plan.json -> PubMed preflight -> search_execution_plan.json`

## 3. Shared Core Audit Result

Shared core is not clean enough to satisfy the target boundary as written.

Observed issue:

- `mini_medical_terms_index.json` currently contains Meta-specific outcome/effect/study-design terms, including `overall survival`, `progression-free survival`, `hazard ratio`, `odds ratio`, `cohort study`, and `randomized controlled trial`.
- This is recorded in `data/medical_terms/review_reports/medical_terms_integration_audit.json` as `shared_core_contains_meta_scope_terms`.
- This stage explicitly forbids modifying `mini_medical_terms_index.json`, so the issue is reported but not fixed here.

Confirmed clean boundaries:

- Bioinformatics GEO technical terms such as `GSE`, `GSM`, `TPM`, `FPKM`, `series matrix`, and `sample metadata` are not present as shared core term entries in the checked shared fields.
- `zh_term_overrides.json` does not contain GEO technical mappings for `GSE`, `GSM`, `GPL`, `series matrix`, or `sample metadata`.
- Meta exposure concepts such as `meta_exposure:obesity` and `meta_exposure:prediabetes` were not auto-promoted into shared core.
- Shared promotion candidates remain review artifacts rather than automatic merges.

## 4. Bioinformatics Calling Path Audit

Bioinformatics scoped files are present and loadable:

- Species: `Homo sapiens`, `Mus musculus`, `Rattus norvegicus`.
- Species synonyms: `human`, `mouse`, `rat`.
- GTEx tissue mappings: parent tissues and concrete subtypes including `Muscle - Skeletal` and `Nerve - Tibial`.
- GEO data types: `TPM`, `FPKM`, `raw counts`, `count matrix`.
- GEO grouping terms: `adjacent normal`, `knockdown`, `overexpression`.
- Dataset registry: `platform annotation`.
- Scoped stop terms: `dataset`, `sample`, `series`.

Boundary checks:

- `mouse` is a synonym of `Mus musculus`, not an independent species concept.
- `TPM` and `FPKM` are `normalized_expression`, not raw counts.
- `dataset`, `sample`, and `series` are scoped stop terms and are not global stop words.
- Bioinformatics scoped vocabularies do not contain Meta terms such as `overall survival`, `progression-free survival`, `hazard ratio`, `cohort study`, `risk factor`, `ROB2`, or `PRISMA`.

## 5. Meta Analysis Calling Path Audit

Meta seed helper behavior is available:

- Chinese question to seed concept matching.
- PICO/PECO draft generation.
- PubMed query block generation from curated MeSH/free-text mappings.
- Query guard visibility.
- English evidence regex helper remains helper-level and has no PDF extraction UI.

Validated Chinese examples:

- `糖尿病前期与甲状腺癌风险的关系`
- `二甲双胍治疗2型糖尿病的疗效`
- `放射性碘治疗甲状腺癌复发的影响`
- `肥胖与乳腺癌风险的Meta分析`

Guard checks:

- `research_intent` does not enter PubMed topic expansion.
- `effect_measure` does not enter PubMed topic expansion.
- `study_design` is `filter_only`.
- `outcome` remains conditional and requires disease/population pairing.

## 6. Scope Isolation Audit

Bioinformatics-to-Meta isolation:

- Meta helper no longer matches short Latin effect tokens inside Bioinformatics identifiers.
- Boundary fix: `SE` no longer matches inside `GSE`.
- Bioinformatics identifiers such as `GSE`, `GSM`, `GPL`, `TPM`, `FPKM`, `raw counts`, `probe ID`, `series matrix`, `sample metadata`, `TCGA barcode`, and `GTEx tissue` do not become Meta PICO concepts in the integration test.

Meta-to-Bioinformatics isolation:

- Bioinformatics scoped term files do not load Meta outcome/effect/study-design/research-intent terms.

Residual issue:

- Shared core contains older Meta-scope concepts. This is a shared-layer issue, not a Bioinformatics scoped-file issue.

## 7. Meta Search Draft / Review Gate / Preflight Audit

Draft and review gate behavior:

- `draft_only` does not generate `confirmed_search_plan.json`.
- `needs_edit` remains user-edited but not executable until confirmed.
- `rejected` does not enter preflight.
- Only `user_confirmed` can generate `confirmed_search_plan.json`.
- Guard override warnings must be explicitly confirmed before PubMed preflight.

Preflight behavior:

- `search_execution_plan.json` is generated only from confirmed plans.
- `plan_status=draft_execution_plan`.
- `search_execution_status=not_executed`.
- `online_retrieval_executed=false`.
- PubMed is not queried and no records are downloaded.

Boundary fix applied:

- PubMed preflight `plan_status` was renamed from `preflight_ready` to `draft_execution_plan` to make the non-executing boundary explicit.

## 8. Unimplemented Boundary Confirmation

The following remain intentionally unimplemented:

- PubMed online search.
- Embase, Web of Science, and Cochrane retrieval.
- Chinese database retrieval.
- Chinese PDF extraction.
- English PDF extraction UI.
- Automatic literature screening.
- Automatic included studies.
- Meta statistical analysis progression.
- Shared core automatic promotion.

These are current scope boundaries, not defects.

## 9. Test Commands And Results

Validation completed:

```bash
git diff --check
# pass
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
# pass
```

## 10. Issues Found

Issue:

- `shared_core_contains_meta_scope_terms`

Details:

- `mini_medical_terms_index.json` contains Meta-specific outcome/effect/study-design terms.
- This violates the target shared-core cleanliness boundary.
- The current stage forbids editing `mini_medical_terms_index.json`, so the issue is reported in the machine-readable audit JSON and left for a dedicated shared-core cleanup stage.

## 11. Fixes Applied

Fixes:

- `meta_matcher_short_latin_token_boundary_fix`: Meta matcher now applies Latin token boundaries, preventing `SE` from matching inside `GSE`.
- `preflight_plan_status_boundary_fix`: PubMed preflight plan status is now `draft_execution_plan`.

These are boundary fixes, not business workflow expansion.

## 12. Follow-Up Recommendations

Recommended next stages:

- Plan a dedicated shared-core cleanup or migration for Meta-specific concepts currently present in `mini_medical_terms_index.json`.
- Keep Meta outcome/effect/study-design/research-intent concepts in Meta scoped seed/runtime files.
- Keep Bioinformatics GEO/TCGA/GTEx technical terms outside Meta PICO/query expansion.
- Do not enable online retrieval until execution logging, rate-limit handling, and user-confirmed database selection are designed.
