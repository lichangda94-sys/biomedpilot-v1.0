# UI-C1d Meta Analysis Mockup Sample Data

This file contains non-production, mockup-only sample data for high-fidelity Meta Analysis interface planning. It must not be treated as real evidence, real analysis output, or a report-ready dataset.

## 1. Mock Topic

Primary mock topic:

- Chinese working question: 甲状腺癌患者中 adiponectin 表达或水平是否与预后或临床病理特征相关？
- English working question: Is adiponectin expression or circulating adiponectin level associated with prognosis or clinicopathological features in thyroid cancer?
- Suggested Meta type: biomarker_expression_difference_meta or prognostic_factor_meta
- Processing boundary: Chinese UI is allowed, but search/extraction processing is English-first and reviewer-confirmed.

Generic fallback topic:

- English topic: Oncology biomarker association with disease prognosis
- Suggested Meta type: prognostic_factor_meta

## 2. PICO / PECO Draft

| field | mock value | boundary |
|---|---|---|
| Population | Adults with thyroid cancer | reviewer must confirm |
| Exposure / Index marker | Adiponectin expression or circulating adiponectin level | candidate term only |
| Comparator | Low vs high adiponectin; tumor vs adjacent normal tissue | depends on included studies |
| Outcome | Overall survival, recurrence, lymph node metastasis, tumor stage | not final |
| Study design | Observational cohort or case-control studies | reviewer confirmed only |
| Meta type | Prognostic factor Meta / biomarker expression difference Meta | workflow control item |

## 3. English Search Query Example

Mock PubMed query draft:

```text
("thyroid cancer"[Title/Abstract] OR "thyroid carcinoma"[Title/Abstract] OR "thyroid neoplasm"[Title/Abstract])
AND
("adiponectin"[Title/Abstract] OR "ADIPOQ"[Title/Abstract])
AND
("prognosis"[Title/Abstract] OR "survival"[Title/Abstract] OR "recurrence"[Title/Abstract] OR "clinicopathological"[Title/Abstract])
```

Search boundary:

- This is a draft query, not an executed search.
- Chinese input may help generate English terms.
- Do not show CNKI / WanFang / VIP direct search execution.
- PubMed execution, if later supported, must be explicit and reviewer-confirmed.

## 4. Reference Table Example

| ref_id | title | year | source | DOI/PMID | screening_status | dedup_status |
|---|---|---:|---|---|---|---|
| REF-001 | Serum adiponectin and clinicopathological features in thyroid carcinoma | 2018 | PubMed mock | PMID-MOCK-001 | not_started | unique |
| REF-002 | ADIPOQ expression and survival outcomes in differentiated thyroid cancer | 2020 | RIS mock | DOI-MOCK-002 | not_started | possible_duplicate |
| REF-003 | Adiponectin signaling in thyroid neoplasm progression | 2021 | CSV mock | DOI-MOCK-003 | not_started | possible_duplicate |
| REF-004 | Circulating adipokines and thyroid cancer risk | 2017 | PubMed mock | PMID-MOCK-004 | not_started | unique |

## 5. Deduplication Example

| group_id | risk | records | suggested_action | boundary |
|---|---|---|---|---|
| DUP-001 | yellow | REF-002, REF-003 | reviewer compare title, DOI, year | no automatic merge |

## 6. Screening Decisions Example

| ref_id | title_abstract_decision | reason | ai_suggestion | final_decision_boundary |
|---|---|---|---|---|
| REF-001 | include_draft | biomarker association in target population | likely_include, confidence 0.72 | reviewer decides |
| REF-002 | uncertain | survival endpoint unclear | needs_review, confidence 0.61 | reviewer decides |
| REF-004 | exclude_draft | risk study, not prognosis | likely_exclude, confidence 0.68 | reviewer decides |

AI boundary:

- AI suggestion is advisory only.
- AI does not apply final include/exclude decisions.
- Exclusion reasons require reviewer confirmation.

## 7. Full-text / Extraction Fields

Type-specific extraction fields for biomarker/prognostic Meta:

| section | field | example value | required | boundary |
|---|---|---|---|---|
| Study identity | first_author | Zhang | yes | mock only |
| Study identity | year | 2020 | yes | mock only |
| Population | cancer_type | thyroid carcinoma | yes | reviewer confirmed |
| Biomarker | marker_name | adiponectin / ADIPOQ | yes | normalize later |
| Effect | effect_measure | HR | yes | depends on reported study |
| Effect | effect_value | 1.48 | yes | non-production example |
| Effect | ci_lower | 1.05 | yes | non-production example |
| Effect | ci_upper | 2.10 | yes | non-production example |
| Adjustment | adjusted_model | multivariable | optional | needs notes |
| Outcome | outcome_name | overall survival | yes | reviewer confirmed |

## 8. Risk of Bias Domains

| tool | domain | mock state | boundary |
|---|---|---|---|
| Newcastle-Ottawa Scale | Selection | incomplete | reviewer required |
| Newcastle-Ottawa Scale | Comparability | incomplete | reviewer required |
| Newcastle-Ottawa Scale | Outcome | incomplete | reviewer required |
| ROBINS-I | Confounding | not_started | tool suggestion only |
| QUADAS-2 | Patient selection | not_applicable_for_current_type | depends on diagnostic type |

## 9. Pairwise Input Table Example

| study_id | effect_type | effect_value | ci_lower | ci_upper | weight_status | readiness |
|---|---|---:|---:|---:|---|---|
| STUDY-001 | HR | 1.48 | 1.05 | 2.10 | not_calculated | preflight_only |
| STUDY-002 | HR | 1.21 | 0.88 | 1.67 | not_calculated | warning_missing_adjustment |
| STUDY-003 | OR | 1.76 | 1.10 | 2.82 | incompatible_effect_type | blocked |

Boundary:

- This table is for preflight/mockup only.
- Do not show a pooled estimate.
- Do not show heterogeneity, forest plot, or publication bias statistics as computed.

## 10. Result Review Gate State

| gate | state | reason |
|---|---|---|
| result_semantic | result.semantic.testing_summary_only | no formal pooled effect |
| report_status | report.status.draft | no report-ready package |
| export_gate | disabled_empty_result | no formal result and export adapter not connected |
| forest_plot | disabled_boundary | do not fake plot |
| report_ready | blocked | manual review and formal analysis missing |

## 11. Disabled Export Formats

| format | state |
|---|---|
| DOCX | disabled |
| HTML | disabled |
| PDF | disabled / future |
| CSV | disabled unless formal result exists |
| XLSX | disabled unless formal result exists |
| ZIP reproducibility package | disabled |
