from __future__ import annotations

import json
from pathlib import Path

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report


ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_PATH = ROOT / "data" / "medical_terms" / "reference_checklists" / "meta_analysis_terms_core_checklist.json"


def test_meta_analysis_terms_checklist_has_systematic_scope() -> None:
    payload = json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))
    subcategories = {item["subcategory"] for item in payload["items"]}
    ambiguity_terms = {item["term"] for item in payload["ambiguity_terms"]}

    assert payload["coverage_type"] == "meta_analysis_terms_core"
    assert len(payload["items"]) >= 100
    assert {
        "pico_framework",
        "study_design",
        "effect_measure",
        "survival_oncology_outcome",
        "general_clinical_outcome",
        "diagnostic_accuracy",
        "heterogeneity_statistics",
        "publication_type",
        "exclusion_type",
        "quality_assessment",
    } <= subcategories
    assert {"OS", "HR", "OR", "RR", "CI", "MD", "SMD", "PR", "SD", "PD"} <= ambiguity_terms


def test_meta_analysis_terms_coverage_audit_is_complete() -> None:
    report = build_coverage_audit_report()
    section = report["sections"]["meta_analysis_terms_core"]
    gates = {gate["gate_id"]: gate for gate in report["quality_gates"]["gates"]}

    assert section["total_checklist_items"] >= 100
    assert section["covered"] == section["total_checklist_items"]
    assert section["missing"] == 0
    assert section["coverage_rate"] == 1.0
    assert section["missing_terms"] == []
    assert all(bucket["coverage_rate"] == 1.0 for bucket in section["subcategory_coverage"].values())
    assert gates["meta_analysis_terms_core_coverage"]["status"] == "pass"
    assert gates["meta_analysis_terms_missing_terms"]["observed"] == 0


def test_pico_and_chinese_aliases_positive_lookup() -> None:
    cases = [
        ("研究人群", "population", "pico_terms"),
        ("干预措施", "intervention", "pico_terms"),
        ("暴露因素", "exposure", "pico_terms"),
        ("对照组", "comparator", "pico_terms"),
        ("随访时间", "follow-up", "pico_terms"),
        ("亚组分析人群", "subgroup", "pico_terms"),
    ]

    for query, expected, field in cases:
        result = lookup_medical_terms(query, target_context="meta_analysis")
        values = getattr(result, field)

        assert expected in " ".join(values).lower()
        assert result.disease_terms_en == []


def test_effect_measures_and_outcomes_are_separate() -> None:
    effect_cases = {
        "HR": "hazard ratio",
        "OR": "odds ratio",
        "RR": "risk ratio",
        "MD": "mean difference",
        "SMD": "standardized mean difference",
        "置信区间": "confidence interval",
    }
    outcome_cases = {
        "OS": "overall survival",
        "PFS": "progression-free survival",
        "DFS": "disease-free survival",
        "RFS": "recurrence-free survival",
        "客观缓解率": "objective response rate",
    }

    for query, expected in effect_cases.items():
        result = lookup_medical_terms(query, target_context="meta_analysis")

        assert expected in " ".join(result.effect_measures).lower()
        assert result.outcome_terms == []
        assert result.disease_terms_en == []

    for query, expected in outcome_cases.items():
        result = lookup_medical_terms(query, target_context="meta_analysis")

        assert expected in " ".join(result.outcome_terms).lower()
        assert result.effect_measures == []
        assert result.disease_terms_en == []


def test_study_design_publication_exclusion_and_quality_terms() -> None:
    rct = lookup_medical_terms("RCT", target_context="meta_analysis")
    cohort = lookup_medical_terms("队列研究", target_context="meta_analysis")
    review = lookup_medical_terms("case report", target_context="meta_analysis")
    animal = lookup_medical_terms("animal study", target_context="meta_analysis")
    rob = lookup_medical_terms("RoB 2", target_context="meta_analysis")
    nos = lookup_medical_terms("NOS量表", target_context="meta_analysis")

    assert "randomized controlled trial" in " ".join(rct.study_design_terms).lower()
    assert "cohort study" in " ".join(cohort.study_design_terms).lower()
    assert "case report" in " ".join(review.publication_type_terms).lower()
    assert "case report" in " ".join(review.exclusion_type_terms).lower()
    assert "animal study" in " ".join(animal.exclusion_type_terms).lower()
    assert "cochrane risk of bias" in " ".join(rob.quality_assessment_terms).lower()
    assert "newcastle-ottawa scale" in " ".join(nos.quality_assessment_terms).lower()
    assert rct.disease_terms_en == []


def test_diagnostic_accuracy_terms_are_separate_from_general_outcomes() -> None:
    auc = lookup_medical_terms("AUC", target_context="meta_analysis")
    sensitivity = lookup_medical_terms("敏感性", target_context="meta_analysis")
    incidence = lookup_medical_terms("发病率", target_context="meta_analysis")

    assert "area under the curve" in " ".join(auc.diagnostic_accuracy_terms).lower()
    assert "sensitivity" in " ".join(sensitivity.diagnostic_accuracy_terms).lower()
    assert sensitivity.outcome_terms == []
    assert "incidence" in " ".join(incidence.outcome_terms).lower()
    assert incidence.diagnostic_accuracy_terms == []


def test_short_token_boundaries_and_bioinformatics_isolation() -> None:
    lowercase_or = lookup_medical_terms("treatment or control", target_context="meta_analysis")
    clinical = lookup_medical_terms("clinical cohort", target_context="meta_analysis")
    os_meta = lookup_medical_terms("OS", target_context="meta_analysis")
    os_bio = lookup_medical_terms("OS", target_context="bioinformatics")
    hr_meta = lookup_medical_terms("HR", target_context="meta_analysis")
    hr_bio = lookup_medical_terms("HR", target_context="bioinformatics")
    pr = lookup_medical_terms("PR", target_context="meta_analysis")
    sd = lookup_medical_terms("SD", target_context="meta_analysis")
    pd = lookup_medical_terms("PD", target_context="meta_analysis")

    assert "odds ratio" not in " ".join(lowercase_or.effect_measures).lower()
    assert "confidence interval" not in " ".join(clinical.effect_measures).lower()
    assert "overall survival" in " ".join(os_meta.outcome_terms).lower()
    assert os_bio.outcome_terms == []
    assert os_bio.effect_measures == []
    assert os_bio.data_modality_terms == []
    assert "hazard ratio" in " ".join(hr_meta.effect_measures).lower()
    assert hr_bio.effect_measures == []
    assert "partial response" in " ".join(pr.outcome_terms).lower()
    assert "stable disease" in " ".join(sd.outcome_terms).lower()
    assert "progressive disease" in " ".join(pd.outcome_terms).lower()
    assert pr.warnings and sd.warnings and pd.warnings


def test_context_output_policy_for_meta_terms() -> None:
    meta = build_search_translation_draft(
        "肺腺癌 OS HR Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )
    bio = build_search_translation_draft(
        "肺腺癌 OS RNA-seq 数据集",
        target_context="bioinformatics",
        target_database="geo",
    )

    assert "overall survival" in " ".join(meta.outcome_terms_en).lower()
    assert "hazard ratio" in " ".join(meta.effect_measures).lower()
    assert "effect_measures" in meta.audit["term_lookup"]
    assert meta.geo_query_candidates == []
    assert not meta.audit.get("tcga_project_candidates")
    assert bio.pubmed_query_candidates == []
    assert "effect_measures" not in bio.audit["term_lookup"]
    assert bio.effect_measures == []
    assert bio.outcome_terms_en == []
