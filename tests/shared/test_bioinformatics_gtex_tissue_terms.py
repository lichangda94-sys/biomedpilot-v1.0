from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"
BIO_DIR = MEDICAL_TERMS / "bioinformatics"


def _json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _tissue_terms_for_scope(target_context: str) -> list[dict[str, object]]:
    payload = _json(BIO_DIR / "bioinformatics_tissue_terms.json")
    assert payload["shared_core_allowed"] is False  # type: ignore[index]
    assert payload["meta_scope_allowed"] is False  # type: ignore[index]
    if target_context not in payload["target_contexts"]:  # type: ignore[index]
        return []
    return payload["terms"]  # type: ignore[index]


def test_gtex_tissue_terms_are_bioinformatics_only() -> None:
    bio_terms = _tissue_terms_for_scope("bioinformatics")
    meta_terms = _tissue_terms_for_scope("meta_analysis")

    assert bio_terms
    assert meta_terms == []
    assert all(term["shared_core_allowed"] is False for term in bio_terms)
    assert all(term["meta_scope_allowed"] is False for term in bio_terms)


def test_muscle_and_nerve_use_specific_gtex_mappings() -> None:
    by_id = {term["concept_id"]: term for term in _tissue_terms_for_scope("bioinformatics")}
    muscle = by_id["bio_gtex_tissue:muscle_skeletal"]
    nerve = by_id["bio_gtex_tissue:nerve_tibial"]

    assert muscle["preferred_label"] == "Muscle - Skeletal"
    assert muscle["preferred_zh"] == "骨骼肌"
    assert muscle["gtex_tissue"] == "Muscle - Skeletal"
    assert {"term": "肌肉", "weight": "low", "entry_type": "broad_entry"} in muscle["zh_entry_terms"]

    assert nerve["preferred_label"] == "Nerve - Tibial"
    assert nerve["preferred_zh"] == "胫神经"
    assert nerve["gtex_tissue"] == "Nerve - Tibial"
    assert {"term": "神经", "weight": "low", "entry_type": "broad_entry"} in nerve["zh_entry_terms"]


def test_parent_terms_require_subtype_mapping_and_do_not_override_subtypes() -> None:
    by_id = {term["concept_id"]: term for term in _tissue_terms_for_scope("bioinformatics")}
    skin = by_id["bio_gtex_tissue:skin_parent"]
    heart = by_id["bio_gtex_tissue:heart_parent"]
    artery = by_id["bio_gtex_tissue:artery_parent"]

    for term in [skin, heart, artery]:
        assert term["term_type"] == "gtex_parent_tissue"
        assert term["requires_subtype_mapping"] is True
        assert term["standalone_search_allowed"] is False
        assert all(entry["weight"] == "low" for entry in term["zh_entry_terms"])

    artery_subtypes = {item["gtex_tissue"] for item in artery["gtex_subtype_mappings"]}
    assert artery_subtypes == {"Artery - Aorta", "Artery - Coronary", "Artery - Tibial"}
    assert "Artery" not in artery_subtypes
    assert artery.get("gtex_tissue") is None


def test_gtex_audit_resolves_previous_needs_review_items() -> None:
    audit = _json(BIO_DIR / "audits" / "gtex_terms_coverage_audit.json")

    assert audit["summary"]["needs_review"] == 0  # type: ignore[index]
    assert audit["summary"]["approved_with_subtype_mapping"] == 3  # type: ignore[index]
    assert audit["summary"]["complete_with_note"] == 2  # type: ignore[index]
    by_term = {item["gtex_tissue"]: item for item in audit["items"]}  # type: ignore[index]
    for term in ["Skin", "Heart", "Artery"]:
        assert by_term[term]["status"] == "approved_with_subtype_mapping"
        assert by_term[term]["requires_subtype_mapping"] is True
        assert by_term[term]["source_file"] == "data/medical_terms/bioinformatics/bioinformatics_tissue_terms.json"
    assert by_term["Muscle"]["standard_gtex_tissue"] == "Muscle - Skeletal"
    assert by_term["Muscle"]["zh_term"] == "骨骼肌"
    assert by_term["Nerve"]["standard_gtex_tissue"] == "Nerve - Tibial"
    assert by_term["Nerve"]["zh_term"] == "胫神经"
