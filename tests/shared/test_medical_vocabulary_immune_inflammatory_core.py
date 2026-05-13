from __future__ import annotations

import json
from pathlib import Path

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report


ROOT = Path(__file__).resolve().parents[2]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"
CHECKLIST = MEDICAL_TERMS / "reference_checklists" / "immune_inflammatory_core_checklist.json"


def _mini() -> list[dict[str, object]]:
    return json.loads((MEDICAL_TERMS / "mini_medical_terms_index.json").read_text(encoding="utf-8"))


def _joined(values: list[str]) -> str:
    return " ".join(values).lower()


def test_immune_inflammatory_core_checklist_is_systematic_and_covered() -> None:
    checklist = json.loads(CHECKLIST.read_text(encoding="utf-8"))
    report = build_coverage_audit_report()
    section = report["sections"]["immune_inflammatory_core"]

    assert checklist["coverage_type"] == "immune_inflammatory_core"
    assert len(checklist["items"]) >= 65
    assert len(checklist["ambiguity_terms"]) >= 30
    assert section["total_checklist_items"] == len(checklist["items"])
    assert section["covered"] == len(checklist["items"])
    assert section["missing"] == 0
    assert section["coverage_rate"] == 1.0
    assert section["subcategory_coverage"]["immune_cell"]["covered"] >= 10
    assert section["subcategory_coverage"]["immune_biomarker"]["covered"] >= 6
    assert report["core_checklist_summary"]["immune_inflammatory_core"]["quality_gate_status"] == "pass"


def test_immune_disease_and_chinese_aliases_match() -> None:
    sle = lookup_medical_terms("系统性红斑狼疮 RNA-seq", target_context="bioinformatics")
    ra = lookup_medical_terms("类风湿关节炎 单细胞", target_context="bioinformatics")
    crohn = lookup_medical_terms("克罗恩病", target_context="bioinformatics")

    assert "systemic lupus erythematosus" in _joined(sle.disease_terms_en)
    assert "SLE" in sle.abbreviations
    assert "Skin" in sle.gtex_tissue_candidates
    assert "RNA-seq" in sle.data_modality_terms

    assert "rheumatoid arthritis" in _joined(ra.disease_terms_en)
    assert "RA" in ra.abbreviations
    assert any(term in _joined(ra.data_modality_terms) for term in ["single-cell", "scrna-seq"])

    assert "crohn disease" in _joined(crohn.disease_terms_en)
    assert "ulcerative colitis" not in _joined(crohn.disease_terms_en)


def test_immune_cells_and_biomarkers_are_not_diseases() -> None:
    t_cell = lookup_medical_terms("T cell", target_context="bioinformatics")
    treg = lookup_medical_terms("Treg", target_context="bioinformatics")
    macrophage = lookup_medical_terms("巨噬细胞", target_context="bioinformatics")
    il6 = lookup_medical_terms("IL-6", target_context="bioinformatics")
    ana = lookup_medical_terms("ANA", target_context="meta_analysis")

    assert "T cell" in t_cell.immune_cell_terms
    assert "regulatory t cell" in _joined(treg.immune_cell_terms)
    assert "macrophage" in _joined(macrophage.immune_cell_terms)
    assert t_cell.disease_terms_en == []
    assert macrophage.disease_terms_en == []

    assert "interleukin-6" in _joined(il6.biomarker_terms)
    assert "antinuclear antibody" in _joined(ana.biomarker_terms)
    assert il6.disease_terms_en == []
    assert ana.disease_terms_en == []
    assert any("免疫炎症缩写" in warning for warning in il6.warnings)

    concepts = {item["concept_id"]: item for item in _mini()}
    assert concepts["mini:immune_inflammatory_t_cell"]["concept_type"] == "immune_cell"
    assert concepts["mini:immune_inflammatory_interleukin_6"]["concept_type"] == "biomarker"
    assert concepts["mini:cardiovascular_c_reactive_protein"]["concept_type"] == "biomarker"


def test_immune_context_isolation_between_bioinformatics_and_meta() -> None:
    bio = build_search_translation_draft(
        "系统性红斑狼疮 IL-6 RNA-seq 数据集",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "系统性红斑狼疮 IL-6 cohort study",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert bio.geo_query_candidates
    assert bio.pubmed_query_candidates == []
    assert "effect_measures" not in bio.audit["term_lookup"]
    assert "RNA-seq" in bio.data_type_terms_en
    assert "interleukin-6" in _joined(bio.audit["term_lookup"]["biomarker_terms"])

    assert meta.geo_query_candidates == []
    assert not meta.audit.get("gtex_tissue_candidates")
    assert "systemic lupus erythematosus" in _joined(meta.disease_terms_en)
    assert "cohort study" in _joined(meta.audit["term_lookup"]["study_design_terms"])
    assert "interleukin-6" in _joined(meta.audit["term_lookup"]["biomarker_terms"])


def test_immune_negative_expansion_guards() -> None:
    forbidden = {
        "IBD": ["crohn disease", "ulcerative colitis"],
        "Crohn disease": ["ulcerative colitis"],
        "ulcerative colitis": ["crohn disease"],
        "asthma": ["chronic obstructive pulmonary disease", "COPD"],
        "COPD": ["asthma"],
        "psoriasis": ["psoriatic arthritis"],
        "psoriatic arthritis": ["psoriasis vulgaris"],
        "SLE": ["lupus nephritis"],
        "ANCA": ["ANCA-associated vasculitis"],
        "Hashimoto thyroiditis": ["thyroid cancer", "PTC", "TCGA-THCA"],
        "Graves disease": ["thyroid cancer", "PTC", "TCGA-THCA"],
        "CRP": ["cardiovascular disease"],
    }

    for query, blocked_terms in forbidden.items():
        result = lookup_medical_terms(query, target_context="bioinformatics")
        text = _joined([*result.disease_terms_en, *result.biomarker_terms, *result.abbreviations, *result.tcga_project_candidates])
        for blocked in blocked_terms:
            assert blocked.lower() not in text


def test_immune_short_token_guard_and_cross_core_uniqueness() -> None:
    for query in ("xRAx", "IL-67", "TNFAKE", "ANCA1", "IgEX"):
        result = lookup_medical_terms(query, target_context="bioinformatics")

        assert not any("immune_inflammatory" in concept_id for concept_id in result.concept_ids)
        assert result.disease_terms_en == []
        assert result.immune_cell_terms == []
        assert result.biomarker_terms == []

    mini = _mini()
    concept_ids = [item["concept_id"] for item in mini]
    by_id = {item["concept_id"]: item for item in mini}

    assert concept_ids.count("mini:hashimoto_thyroiditis") == 1
    assert concept_ids.count("mini:graves_disease") == 1
    assert concept_ids.count("mini:cardiovascular_c_reactive_protein") == 1
    assert by_id["mini:hashimoto_thyroiditis"]["category"] == "endocrine_metabolic"
    assert by_id["mini:graves_disease"]["category"] == "endocrine_metabolic"
    assert by_id["mini:cardiovascular_c_reactive_protein"]["category"] == "cardiovascular"
