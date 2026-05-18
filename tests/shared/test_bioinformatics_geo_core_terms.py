from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"
BIO_DIR = MEDICAL_TERMS / "bioinformatics"


def _json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _terms(filename: str) -> list[dict[str, object]]:
    payload = _json(BIO_DIR / filename)
    assert payload["target_contexts"] == ["bioinformatics"]  # type: ignore[index]
    assert payload["shared_core_allowed"] is False  # type: ignore[index]
    assert payload["meta_scope_allowed"] is False  # type: ignore[index]
    return payload["terms"]  # type: ignore[index]


def _terms_for_scope(filename: str, target_context: str) -> list[dict[str, object]]:
    payload = _json(BIO_DIR / filename)
    if target_context not in payload["target_contexts"]:  # type: ignore[index]
        return []
    return payload["terms"]  # type: ignore[index]


def test_geo_core_species_terms_are_bioinformatics_only() -> None:
    terms = _terms("bioinformatics_species_terms.json")
    by_id = {term["concept_id"]: term for term in terms}
    all_ids = {term["concept_id"] for term in terms}

    assert {"bio_species:homo_sapiens", "bio_species:mus_musculus", "bio_species:rattus_norvegicus"} <= all_ids
    assert "mouse" in by_id["bio_species:mus_musculus"]["synonyms"]
    assert all(term["concept_id"] != "bio_species:mouse" for term in terms)
    assert all(term["shared_core_allowed"] is False for term in terms)
    assert all(term["meta_scope_allowed"] is False for term in terms)


def test_geo_core_grouping_terms_are_not_standalone_search_terms() -> None:
    terms = _terms("bioinformatics_grouping_terms.json")
    labels = {term["preferred_label"] for term in terms}

    assert {"adjacent normal", "untreated", "vehicle", "sham", "resistant", "wild type", "mutant", "knockdown", "overexpression"} <= labels
    assert all(term["standalone_search_allowed"] is False for term in terms)
    assert all(term["shared_core_allowed"] is False for term in terms)
    assert all(term["meta_scope_allowed"] is False for term in terms)


def test_geo_core_data_type_terms_separate_normalized_expression_from_raw_counts() -> None:
    terms = _terms("bioinformatics_data_type_terms.json")
    by_label = {term["preferred_label"]: term for term in terms}

    assert by_label["raw counts"]["data_category"] == "raw_counts"
    for label in ["TPM", "FPKM", "RPKM", "CPM"]:
        assert by_label[label]["data_category"] == "normalized_expression"
        assert by_label[label]["is_raw_counts"] is False
        assert "raw counts" not in by_label[label].get("synonyms", [])
    assert all(term["shared_core_allowed"] is False for term in terms)
    assert all(term["meta_scope_allowed"] is False for term in terms)


def test_geo_core_dataset_registry_and_stop_terms_are_scoped() -> None:
    registry = _terms("bioinformatics_dataset_registry_terms.json")
    stop_terms = _terms("bioinformatics_stop_terms.json")

    assert {term["preferred_label"] for term in registry} == {"platform annotation"}
    assert {term["term"] for term in stop_terms} == {"dataset", "sample", "series"}
    assert all(term["term_type"] == "scoped_stop_term" for term in stop_terms)
    assert all(term["standalone_search_allowed"] is False for term in stop_terms)
    assert all(term["shared_core_allowed"] is False for term in stop_terms)
    assert all(term["meta_scope_allowed"] is False for term in stop_terms)


def test_geo_core_audit_has_no_missing_terms_after_bioinformatics_fix() -> None:
    audit = _json(BIO_DIR / "audits" / "geo_core_terms_coverage_audit.json")

    assert audit["summary"]["missing"] == 0  # type: ignore[index]
    assert audit["summary"]["approved_with_note"] == 8  # type: ignore[index]
    assert not audit["future_candidates"]  # type: ignore[index]
    by_term = {item["term"]: item for item in audit["items"]}  # type: ignore[index]
    assert by_term["mouse"]["status"] == "approved-with-note"
    for term in ["TPM", "FPKM", "RPKM", "CPM", "dataset", "sample", "series"]:
        assert by_term[term]["status"] == "approved-with-note"
    assert all(item["covered"] is True for item in audit["items"])  # type: ignore[index]


def test_geo_core_terms_are_loadable_only_for_bioinformatics_scope() -> None:
    filenames = [
        "bioinformatics_species_terms.json",
        "bioinformatics_grouping_terms.json",
        "bioinformatics_data_type_terms.json",
        "bioinformatics_dataset_registry_terms.json",
        "bioinformatics_stop_terms.json",
    ]

    bio_terms = [term for filename in filenames for term in _terms_for_scope(filename, "bioinformatics")]
    meta_terms = [term for filename in filenames for term in _terms_for_scope(filename, "meta_analysis")]

    assert bio_terms
    assert meta_terms == []
