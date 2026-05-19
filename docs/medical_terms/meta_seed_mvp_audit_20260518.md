# Meta Seed MVP Audit 20260518

Generated: 2026-05-19

Scope: audit of the additive Meta seed / mapping / extraction MVP after curated seed batch 2. This report verifies seed quality, query guards, Chinese input mapping, English evidence extraction, and module boundaries. It does not add seed terms, does not change retrieval workflows, and does not claim production PDF extraction.

## Seed Distribution

Source: `data/medical_terms/meta_analysis/meta_seed_terms.json`

Total seeds: 190

| category | count | notes |
| --- | ---: | --- |
| disease / population | 50 | Disease concepts usable as population/disease terms. |
| exposure | 35 | Risk factor, biomarker, lifestyle, environmental, socioeconomic, or exposure concepts. |
| intervention | 30 | Treatment, drug, procedure, screening, rehabilitation, diet, or exercise intervention concepts. |
| outcome | 37 | Outcome terms; all require context guard. |
| effect / statistical term | 14 | Effect measures and statistical tokens for extraction/planning, not topic expansion. |
| study design | 12 | Meta-analysis/systematic review and study design filters. |
| research intent | 12 | Intent classifiers, not retrieval topics. |

Mapping files:

- `data/medical_terms/meta_analysis/mesh_mappings.json`: 152 disease/exposure/intervention/outcome mapping rows.
- `data/medical_terms/meta_analysis/pubmed_free_text_mappings.json`: 152 disease/exposure/intervention/outcome mapping rows.
- `data/medical_terms/meta_analysis/emtree_mappings.json`: 190 rows, all present as placeholders with `emtree_review_status=needs_review`.

## Query Guard Audit

Source: `app/shared/query_intelligence/meta_seed_terms/query_builder.py`

| guard | result |
| --- | --- |
| effect measure not in topic search | Pass. All 14 effect/statistical terms have `query_expansion_allowed=false`; PubMed topic block generation for `meta_effect:hazard_ratio` returns no block. |
| research intent not in topic search | Pass. All 12 research-intent terms have `query_expansion_allowed=false`; PubMed topic block generation for `meta_research_intent:risk_factor` returns no block. |
| outcome conditional | Pass. All 37 outcome terms have `query_expansion_allowed=conditional`, `standalone_search_allowed=false`, and `requires_pairing_with=["population_or_disease"]`. |
| study design filter-only | Pass. All 12 study-design terms have `filter_only=true`, `query_expansion_allowed=false`, and `standalone_search_allowed=false`. |

Observed negative-control query block:

```text
build_pubmed_query_blocks(["meta_effect:hazard_ratio", "meta_research_intent:risk_factor"]) -> []
build_pubmed_query_blocks(["meta_study_design:meta_analysis"]) -> []
```

Observed positive-control query block:

```text
build_pubmed_query_blocks(["meta_disease:thyroid_cancer"])
-> ("Thyroid Neoplasms"[MeSH Terms] OR "thyroid cancer"[Title/Abstract])
```

Batch 2 positive controls:

```text
meta_disease:heart_failure -> "Heart Failure"[MeSH Terms]
meta_exposure:mediterranean_diet -> "Mediterranean diet"[Title/Abstract]
meta_intervention:sglt2_inhibitor -> "SGLT2 inhibitor"[Title/Abstract]
meta_outcome:objective_response_rate -> "objective response rate"[Title/Abstract]
```

## Chinese Input Tests

Source: `app/shared/query_intelligence/meta_seed_terms/matcher.py`

| Chinese question | detected intent | matched seed concepts |
| --- | --- | --- |
| 糖尿病前期与甲状腺癌风险的关系 | `exposure_disease_risk_meta` | `meta_disease:thyroid_cancer`, `meta_exposure:prediabetes` |
| 二甲双胍治疗2型糖尿病的疗效 | `treatment_effect_meta` | `meta_disease:type_2_diabetes_mellitus`, `meta_intervention:metformin`, `meta_outcome:treatment_response` |
| 放射性碘治疗甲状腺癌复发的影响 | `association_meta` | `meta_disease:thyroid_cancer`, `meta_intervention:radioactive_iodine_therapy`, `meta_outcome:recurrence` |
| 肥胖与乳腺癌风险的Meta分析 | `exposure_disease_risk_meta` | `meta_disease:breast_cancer`, `meta_exposure:obesity`, `meta_study_design:meta_analysis` |

Research-intent rules covered:

- `危险因素` -> `exposure_disease_risk_meta`
- `预后价值` -> `prognostic_factor_meta`
- `诊断价值` -> `diagnostic_accuracy_meta`
- `疗效` -> `treatment_effect_meta`
- `安全性` -> `safety_outcome_meta`

Batch 2 smoke:

```text
SGLT2抑制剂治疗心力衰竭的安全性
-> intent=safety_outcome_meta
-> concepts=meta_disease:heart_failure, meta_intervention:sglt2_inhibitor
```

## English Extraction Tests

Source: `app/shared/query_intelligence/meta_seed_terms/extraction.py`

Test text included `Abstract`, `Results`, and `References` sections. References were excluded before extraction.

Detected sections:

```text
["abstract", "results"]
```

Detected evidence candidates:

| evidence type | examples |
| --- | --- |
| HR / OR / RR | `HR=0.80`, `OR=1.42`, `RR=0.75` |
| 95% CI | `95% CI 0.66-0.98`, `95% CI 1.10-1.91`, `95% CI 0.61-0.92` |
| P value | `P=0.03`, `P=0.02`, `P=0.01` |
| sample size | `120 patients` |
| follow-up | `follow-up was 24 months` |

Reference-section negative control:

- `OS HR=9.99 P=0.99` in `References` was not included in extracted candidates.

## Outcome / Effect Binding Audit

MVP binding is proximity-based and intentionally conservative. It emits `pending_review` candidates only.

Observed outcome labels:

- `OS`
- `PFS`
- `DFS`
- `RFS`

Binding policy:

- `review_status=pending_review`
- `final_extraction_allowed=false`
- no write to a formal extraction table
- local human review is required before any candidate becomes structured evidence

This satisfies M4.2 because the MVP creates an evidence review queue, not final extracted results.

## Boundary Checks

No diff was observed for these protected areas during this audit:

- shared core: `data/medical_terms/mini_medical_terms_index.json`
- Chinese shared overrides: `data/medical_terms/zh_term_overrides.json`
- Bioinformatics vocabulary/runtime area: `data/medical_terms/bioinformatics/`, `app/bioinformatics/`
- old Meta runtime JSON:
  - `data/medical_terms/meta_analysis/meta_en_effect_measure_terms.json`
  - `data/medical_terms/meta_analysis/meta_en_outcome_terms.json`
  - `data/medical_terms/meta_analysis/meta_en_pdf_extraction_terms.json`
  - `data/medical_terms/meta_analysis/meta_en_pico_terms.json`
  - `data/medical_terms/meta_analysis/meta_en_study_design_terms.json`
  - `data/medical_terms/meta_analysis/meta_research_intent_terms.json`
  - `data/medical_terms/meta_analysis/meta_stop_terms.json`
  - `data/medical_terms/meta_analysis/meta_zh_to_en_concept_terms.json`

Explicit unsupported behavior:

- Chinese database retrieval is not supported by this MVP.
- Chinese PDF extraction is not supported by this MVP.
- English extraction candidates do not automatically write to a formal extraction table.
- Emtree mappings are placeholders only; no unreliable Emtree terms were guessed.

## Verification Commands

```bash
git diff --check
python3 -m pytest tests/shared/test_meta_seed_terms.py -q
python3 -m pytest tests/shared/test_query_intelligence_service.py -q
python3 -m app.main --smoke-test
```
