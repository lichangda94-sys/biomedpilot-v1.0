from __future__ import annotations

import json
from pathlib import Path

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report


ROOT = Path(__file__).resolve().parents[2]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"
CHECKLIST = MEDICAL_TERMS / "reference_checklists" / "cardiovascular_core_checklist.json"


def _mini() -> list[dict[str, object]]:
    return json.loads((MEDICAL_TERMS / "mini_medical_terms_index.json").read_text(encoding="utf-8"))


def _joined(values: list[str]) -> str:
    return " ".join(values).lower()


def test_cardiovascular_core_checklist_is_systematic_and_covered() -> None:
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    report = build_coverage_audit_report()
    section = report["sections"]["cardiovascular_core"]

    assert checklist["coverage_type"] == "cardiovascular_core"
    assert len(checklist["items"]) >= 75
    assert len(checklist["ambiguity_terms"]) >= 10
    assert section["total_checklist_items"] == len(checklist["items"])
    assert section["covered"] == len(checklist["items"])
    assert section["missing"] == 0
    assert section["coverage_rate"] == 1.0
    assert section["subcategory_coverage"]["cardiovascular_biomarker"]["covered"] >= 10
    assert report["core_checklist_summary"]["cardiovascular_core"]["quality_gate_status"] == "pass"


def test_cardiovascular_disease_and_chinese_aliases_match() -> None:
    pulmonary = lookup_medical_terms("肺动脉高压", target_context="bioinformatics")
    mi = lookup_medical_terms("心肌梗死 RNA-seq", target_context="bioinformatics")
    af = lookup_medical_terms("房颤", target_context="bioinformatics")

    assert "pulmonary hypertension" in _joined(pulmonary.disease_terms_en)
    assert "PH" in pulmonary.abbreviations
    assert "Lung" in pulmonary.gtex_tissue_candidates

    assert "myocardial infarction" in _joined(mi.disease_terms_en)
    assert "MI" in mi.abbreviations
    assert "Heart - Left Ventricle" in mi.gtex_tissue_candidates
    assert "RNA-seq" in mi.data_modality_terms

    assert "atrial fibrillation" in _joined(af.disease_terms_en)
    assert "AF" in af.abbreviations


def test_cardiovascular_abbreviations_and_biomarkers_are_not_diseases() -> None:
    for token, expected in {
        "BNP": "B-type natriuretic peptide",
        "CRP": "C-reactive protein",
        "LDL": "LDL cholesterol",
        "HDL": "HDL cholesterol",
        "EF": "ejection fraction",
    }.items():
        result = lookup_medical_terms(token, target_context="bioinformatics")

        assert result.disease_terms_en == []
        assert expected.lower() in _joined(result.exposure_terms)
        assert token in result.abbreviations
        assert any("高歧义心血管缩写" in warning for warning in result.warnings)

    concepts = {item["concept_id"]: item for item in _mini()}
    assert concepts["mini:cardiovascular_b_type_natriuretic_peptide"]["concept_type"] == "biomarker"
    assert concepts["mini:cardiovascular_c_reactive_protein"]["concept_type"] == "biomarker"
    assert concepts["mini:cardiovascular_ejection_fraction"]["concept_type"] == "phenotype"


def test_cardiovascular_context_isolation_between_bioinformatics_and_meta() -> None:
    bio = build_search_translation_draft(
        "心力衰竭 BNP HR RNA-seq 数据集",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "心力衰竭 BNP HR cohort study",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert bio.geo_query_candidates
    assert bio.pubmed_query_candidates == []
    assert "effect_measures" not in bio.audit["term_lookup"]
    assert "hazard ratio" not in _joined(bio.effect_measures)
    assert "RNA-seq" in bio.data_type_terms_en

    assert meta.geo_query_candidates == []
    assert not meta.audit.get("gtex_tissue_candidates")
    assert "heart failure" in _joined(meta.disease_terms_en)
    assert "hazard ratio" in _joined(meta.effect_measures)
    assert "cohort study" in _joined(meta.audit["term_lookup"]["study_design_terms"])


def test_cardiovascular_negative_expansion_guards() -> None:
    forbidden = {
        "hypertension": ["pulmonary hypertension"],
        "pulmonary hypertension": ["essential hypertension"],
        "myocardial infarction": ["stroke", "cerebral infarction"],
        "ischemic stroke": ["myocardial infarction"],
        "heart failure": ["cardiomyopathy"],
        "atrial fibrillation": ["arrhythmia"],
        "atherosclerosis": ["coronary artery disease"],
        "heart": ["heart failure", "cardiovascular disease"],
        "artery": ["atherosclerosis", "coronary artery disease"],
    }

    for query, blocked_terms in forbidden.items():
        result = lookup_medical_terms(query, target_context="bioinformatics")
        text = _joined([*result.disease_terms_en, *result.exposure_terms])

        for blocked in blocked_terms:
            assert blocked not in text


def test_cardiovascular_short_token_guard_and_cross_core_concepts() -> None:
    for query in ("xLDLx", "CRP1", "BNPx", "EFX"):
        result = lookup_medical_terms(query, target_context="bioinformatics")

        assert not any("cardiovascular" in concept_id for concept_id in result.concept_ids)
        assert result.exposure_terms == []
        assert result.disease_terms_en == []

    mini = _mini()
    concept_ids = [item["concept_id"] for item in mini]
    by_id = {item["concept_id"]: item for item in mini}

    assert concept_ids.count("mini:diabetes_mellitus") == 1
    assert concept_ids.count("mini:obesity") == 1
    assert concept_ids.count("mini:dyslipidemia") == 1
    assert by_id["mini:diabetes_mellitus"]["category"] == "endocrine_metabolic"
    assert by_id["mini:obesity"]["category"] == "endocrine_metabolic"
    assert by_id["mini:dyslipidemia"]["category"] == "endocrine_metabolic"
