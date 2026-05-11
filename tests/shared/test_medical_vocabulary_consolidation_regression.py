from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report


ROOT = Path(__file__).resolve().parents[2]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"
CORE_CHECKLISTS = {
    "oncology_core": "oncology_core_checklist.json",
    "endocrine_metabolic_core": "endocrine_metabolic_core_checklist.json",
    "anatomy_tissue_core": "anatomy_tissue_core_checklist.json",
    "bioinformatics_modality_core": "bioinformatics_modality_core_checklist.json",
    "meta_analysis_terms_core": "meta_analysis_terms_core_checklist.json",
    "cardiovascular_core": "cardiovascular_core_checklist.json",
}
CORE_TERM_SOURCES = {
    "project_curated_endocrine_metabolic_core_v1",
    "project_curated_anatomy_tissue_core_v1",
    "project_curated_bioinformatics_modality_core_v1",
    "project_curated_meta_analysis_terms_core_v1",
    "project_curated_cardiovascular_core_v1",
}


def _mini() -> list[dict[str, object]]:
    return json.loads((MEDICAL_TERMS / "mini_medical_terms_index.json").read_text(encoding="utf-8"))


def _zh_overrides() -> list[dict[str, object]]:
    return json.loads((MEDICAL_TERMS / "zh_term_overrides.json").read_text(encoding="utf-8"))


def _joined(values: list[str]) -> str:
    return " ".join(values).lower()


def test_all_core_checklists_are_covered_and_summarized() -> None:
    report = build_coverage_audit_report()

    assert set(CORE_CHECKLISTS) <= set(report["sections"])
    assert set(CORE_CHECKLISTS) <= set(report["core_checklist_summary"])
    for checklist_id in CORE_CHECKLISTS:
        section = report["sections"][checklist_id]
        summary = report["core_checklist_summary"][checklist_id]

        assert section["missing"] == 0
        assert section["coverage_rate"] == 1.0
        assert summary["total"] == section["total_checklist_items"]
        assert summary["covered"] == section["covered"]
        assert summary["missing"] == 0
        assert summary["quality_gate_status"] == "pass"
        assert summary["high_risk_ambiguity_terms"]

    assert report["overall"]["quality_gate_status"] == "pass"
    assert report["overall"]["core_missing"] == 0
    assert report["overall"]["core_coverage_rate"] == 1.0
    assert report["overall"]["total_runtime_concepts"] == len(_mini())
    assert report["overall"]["total_zh_overrides"] == len(_zh_overrides())
    assert report["overall"]["total_high_risk_ambiguity_terms"] >= 60


def test_runtime_concept_structure_is_consistent_for_curated_cores() -> None:
    mini = _mini()
    concept_ids = [str(item.get("concept_id") or "") for item in mini]
    curated = [item for item in mini if item.get("term_source") in CORE_TERM_SOURCES]

    assert not [concept_id for concept_id, count in Counter(concept_ids).items() if count > 1]
    assert curated
    for item in curated:
        assert item.get("concept_id")
        assert item.get("preferred_label_en")
        assert item.get("preferred_en")
        assert item.get("preferred_zh")
        assert isinstance(item.get("zh_synonyms"), list)
        assert isinstance(item.get("en_synonyms"), list)
        assert isinstance(item.get("abbreviations"), list)
        assert item.get("category")
        assert item.get("subcategory")
        assert item.get("contexts")
        assert item.get("confidence")
        assert item.get("sources")

    for item in curated:
        category = item.get("category")
        concept_type = item.get("concept_type")
        if category == "data_modality":
            assert concept_type == "data_modality"
            assert not item.get("disease_terms_en")
        if category == "anatomy_or_tissue":
            assert concept_type == "tissue"
        if category == "meta_analysis_term":
            assert concept_type != "disease"
            assert item.get("contexts") == ["meta_analysis"]
        if concept_type in {"biomarker", "hormone", "laboratory_marker"}:
            assert not item.get("disease_terms_en")


def test_zh_overrides_for_curated_cores_have_mappable_audit_fields() -> None:
    concept_ids = {str(item["concept_id"]) for item in _mini()}
    overrides = [item for item in _zh_overrides() if item.get("term_source") in CORE_TERM_SOURCES]

    assert overrides
    for item in overrides:
        mapped_ids = item.get("mapped_concept_ids")
        assert item.get("zh_term")
        assert mapped_ids
        assert set(mapped_ids) <= concept_ids
        assert item.get("confidence")
        assert item.get("source")
        assert item.get("preferred_label_en")


def test_sqlite_index_is_consistent_with_json_runtime_vocabulary() -> None:
    mini = _mini()
    with sqlite3.connect(MEDICAL_TERMS / "medical_terms_index.sqlite") as conn:
        sqlite_count = conn.execute("SELECT COUNT(*) FROM ontology_terms").fetchone()[0]
        sqlite_ids = {row[0] for row in conn.execute("SELECT concept_id FROM ontology_terms")}
        meta_payload = conn.execute(
            "SELECT payload_json FROM ontology_terms WHERE concept_id = ?",
            ("mini:meta_analysis_overall_survival",),
        ).fetchone()[0]

    assert sqlite_count == len(mini)
    assert sqlite_ids == {item["concept_id"] for item in mini}
    payload = json.loads(meta_payload)
    assert payload["outcome_terms"]
    assert payload["contexts"] == ["meta_analysis"]


def test_bioinformatics_and_meta_context_outputs_remain_isolated() -> None:
    bio = build_search_translation_draft(
        "肺腺癌 OS HR RNA-seq 数据集",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "肺腺癌 OS HR Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert bio.pubmed_query_candidates == []
    assert bio.geo_query_candidates
    assert "effect_measures" not in bio.audit["term_lookup"]
    assert "pico_terms" not in bio.audit["term_lookup"]
    assert "publication_type_terms" not in bio.audit["term_lookup"]
    assert bio.effect_measures == []
    assert bio.outcome_terms_en == []
    assert "RNA-seq" in bio.data_type_terms_en

    assert meta.geo_query_candidates == []
    assert not meta.audit.get("tcga_project_candidates")
    assert not meta.audit.get("gtex_tissue_candidates")
    assert not meta.audit.get("platform_candidates")
    assert "overall survival" in _joined(meta.outcome_terms_en)
    assert "hazard ratio" in _joined(meta.effect_measures)


def test_short_token_guards_across_contexts() -> None:
    for token in ("OS", "HR", "OR", "RR", "CI"):
        result = lookup_medical_terms(token, target_context="bioinformatics")

        assert result.disease_terms_en == []
        assert result.outcome_terms == []
        assert result.effect_measures == []

    assert lookup_medical_terms("or", target_context="meta_analysis").effect_measures == []
    assert lookup_medical_terms("clinical", target_context="meta_analysis").effect_measures == []
    assert "progressive disease" in _joined(lookup_medical_terms("PD", target_context="meta_analysis").outcome_terms)
    assert lookup_medical_terms("PD", target_context="meta_analysis").disease_terms_en == []
    assert lookup_medical_terms("STATAC1", target_context="bioinformatics").concept_ids == []


def test_cross_domain_negative_leakage_guards() -> None:
    cases = {
        "ESCC": ["thyroid", "PTC", "THCA"],
        "PTC": ["esophageal", "ESCC"],
        "LUAD": ["lung squamous cell carcinoma", "LUSC"],
        "LUSC": ["lung adenocarcinoma", "LUAD"],
        "HCC": ["cholangiocarcinoma"],
        "GBM": ["brain tumor"],
        "SCC": ["lung squamous", "cervical", "head and neck"],
        "thyroid": ["thyroid cancer", "PTC", "THCA"],
        "liver": ["hepatocellular carcinoma", "HCC", "LIHC"],
        "lung": ["lung adenocarcinoma", "LUAD", "LUSC"],
        "bone marrow": ["leukemia"],
        "lymph node": ["lymphoma"],
        "adipose tissue": ["obesity"],
        "NAFLD": ["hepatocellular carcinoma", "HCC", "LIHC"],
        "thyroid nodule": ["thyroid cancer", "PTC", "THCA"],
    }

    for query, forbidden_terms in cases.items():
        result = lookup_medical_terms(query, target_context="bioinformatics")
        text = _joined(
            [
                *result.disease_terms_en,
                *result.abbreviations,
                *result.tcga_project_candidates,
                *result.tissue_terms,
            ]
        )

        for forbidden in forbidden_terms:
            assert forbidden.lower() not in text


def test_modality_boundaries_and_category_separation() -> None:
    scrna = lookup_medical_terms("scRNA-seq", target_context="bioinformatics")
    atac = lookup_medical_terms("ATAC-seq", target_context="bioinformatics")
    wgs = lookup_medical_terms("WGS", target_context="bioinformatics")
    proteomics = lookup_medical_terms("proteomics", target_context="bioinformatics")
    adiponectin = lookup_medical_terms("adiponectin", target_context="meta_analysis")
    os_result = lookup_medical_terms("OS", target_context="meta_analysis")
    hr_result = lookup_medical_terms("HR", target_context="meta_analysis")

    assert "bulk RNA-seq" not in scrna.data_modality_terms
    assert "ChIP-seq" not in atac.data_modality_terms
    assert "whole exome sequencing" not in _joined(wgs.data_modality_terms)
    assert "metabolomics" not in proteomics.data_modality_terms
    assert adiponectin.disease_terms_en == []
    assert adiponectin.exposure_terms
    assert os_result.disease_terms_en == []
    assert os_result.outcome_terms
    assert hr_result.outcome_terms == []
    assert hr_result.effect_measures
