from __future__ import annotations

import json
from pathlib import Path

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report


ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_PATH = ROOT / "data" / "medical_terms" / "reference_checklists" / "endocrine_metabolic_core_checklist.json"


def _lookup_text(term: str, *, target_context: str = "bioinformatics") -> str:
    result = lookup_medical_terms(term, target_context=target_context)
    return " ".join(
        [
            *result.disease_terms_en,
            *result.exposure_terms,
            *result.synonyms_en,
            *result.abbreviations,
            *result.mesh_terms,
            *result.tissue_terms,
            *result.tcga_project_candidates,
            *result.gtex_tissue_candidates,
        ]
    )


def test_endocrine_metabolic_checklist_has_systematic_scope() -> None:
    payload = json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))
    subcategories = {item["subcategory"] for item in payload["items"]}
    ambiguity_terms = {item["term"] for item in payload["ambiguity_terms"]}

    assert payload["coverage_type"] == "endocrine_metabolic_core"
    assert len(payload["items"]) >= 70
    assert {
        "glucose_metabolism",
        "obesity_weight",
        "lipid_disorder",
        "metabolic_syndrome_fatty_liver",
        "thyroid_disease",
        "parathyroid_calcium",
        "pituitary_disease",
        "adrenal_disease",
        "reproductive_endocrine",
        "biomarker",
    } <= subcategories
    assert {"T1D", "T2D", "PCOS", "TSH", "T3", "T4", "PTH", "BMI", "HDL", "LDL", "NAFLD", "NASH", "MASLD"} <= ambiguity_terms


def test_endocrine_metabolic_coverage_audit_is_complete() -> None:
    report = build_coverage_audit_report()
    section = report["sections"]["endocrine_metabolic_core"]
    gates = {gate["gate_id"]: gate for gate in report["quality_gates"]["gates"]}

    assert section["total_checklist_items"] >= 70
    assert section["covered"] == section["total_checklist_items"]
    assert section["missing"] == 0
    assert section["coverage_rate"] == 1.0
    assert section["missing_terms"] == []
    assert gates["endocrine_metabolic_core_coverage"]["status"] == "pass"
    assert gates["endocrine_metabolic_missing_terms"]["observed"] == 0


def test_metabolic_and_endocrine_disease_positive_lookup() -> None:
    cases = [
        ("1型糖尿病", "type 1 diabetes mellitus", "T1D", "Pancreas"),
        ("2型糖尿病", "type 2 diabetes mellitus", "T2D", "Pancreas"),
        ("妊娠期糖尿病", "gestational diabetes mellitus", "GDM", "Pancreas"),
        ("多囊卵巢综合征", "polycystic ovary syndrome", "PCOS", "Ovary"),
        ("原发性醛固酮增多症", "primary aldosteronism", "PA", "Adrenal Gland"),
        ("垂体腺瘤", "pituitary adenoma", "", "Pituitary"),
    ]

    for term, disease, abbreviation, gtex in cases:
        result = lookup_medical_terms(term)
        text = _lookup_text(term).lower()

        assert disease in text
        if abbreviation:
            assert abbreviation in result.abbreviations
        assert gtex in result.gtex_tissue_candidates


def test_biomarkers_are_not_disease_concepts() -> None:
    cases = [
        ("脂联素", "adiponectin", "Adipose Tissue"),
        ("瘦素", "leptin", "Adipose Tissue"),
        ("糖化血红蛋白", "hemoglobin A1c", "Whole Blood"),
        ("TSH", "thyroid-stimulating hormone", "Pituitary"),
        ("BMI", "body mass index", ""),
        ("甲状旁腺激素", "parathyroid hormone", "Whole Blood"),
    ]

    for term, biomarker, gtex in cases:
        result = lookup_medical_terms(term)
        text = " ".join([*result.exposure_terms, *result.abbreviations, *result.mesh_terms]).lower()

        assert biomarker.lower() in text
        assert result.disease_terms_en == []
        if gtex:
            assert gtex in result.gtex_tissue_candidates


def test_endocrine_metabolic_context_outputs_are_isolated() -> None:
    bio = build_search_translation_draft(
        "2型糖尿病 RNA-seq",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "2型糖尿病 HbA1c Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert bio.pubmed_query_candidates == []
    assert bio.geo_query_candidates
    assert "Pancreas" in bio.audit.get("gtex_tissue_candidates", [])
    assert meta.geo_query_candidates == []
    assert meta.pubmed_query_candidates
    assert not meta.audit.get("tcga_project_candidates")
    assert not meta.audit.get("gtex_tissue_candidates")
    assert "hemoglobin a1c" in " ".join(meta.exposure_terms_en).lower()


def test_negative_disease_expansion_boundaries() -> None:
    prediabetes = _lookup_text("prediabetes").lower()
    t1d = _lookup_text("type 1 diabetes").lower()
    insulin_resistance = lookup_medical_terms("胰岛素抵抗")
    obesity = _lookup_text("肥胖").lower()

    assert "type 2 diabetes mellitus" not in prediabetes
    assert "type 2 diabetes mellitus" not in t1d
    assert insulin_resistance.disease_terms_en == []
    assert "diabetes mellitus" not in " ".join(insulin_resistance.disease_terms_en).lower()
    assert "metabolic syndrome" not in obesity


def test_thyroid_and_fatty_liver_do_not_leak_to_oncology() -> None:
    thyroid_nodule = _lookup_text("甲状腺结节").lower()
    hashimoto = _lookup_text("桥本甲状腺炎").lower()
    graves = _lookup_text("Graves病").lower()

    for text in (thyroid_nodule, hashimoto, graves):
        assert "thyroid cancer" not in text
        assert "papillary thyroid carcinoma" not in text
        assert "ptc" not in text
        assert "tcga-thca" not in text
    assert "hypothyroidism" not in hashimoto
    assert "hyperthyroidism" not in graves

    for term in ("NAFLD", "MASLD", "NASH"):
        text = _lookup_text(term).lower()
        assert "hepatocellular carcinoma" not in text
        assert "hcc" not in text
        assert "tcga-lihc" not in text


def test_short_tokens_require_exact_boundary() -> None:
    t3 = lookup_medical_terms("T3")
    stat3 = lookup_medical_terms("STAT3")
    t4 = lookup_medical_terms("T4")
    cd4 = lookup_medical_terms("CD4 T cell")
    tsh = lookup_medical_terms("TSH")
    hdl = lookup_medical_terms("HDL")
    ldl = lookup_medical_terms("LDL")

    assert "triiodothyronine" in " ".join(t3.exposure_terms).lower()
    assert stat3.exposure_terms == []
    assert "thyroxine" in " ".join(t4.exposure_terms).lower()
    assert cd4.exposure_terms == []
    assert "thyroid-stimulating hormone" in " ".join(tsh.exposure_terms)
    assert hdl.disease_terms_en == []
    assert ldl.disease_terms_en == []
