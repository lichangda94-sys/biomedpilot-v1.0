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
    assert {"human", "humans", "人", "人类"} <= set(by_id["bio_species:homo_sapiens"]["synonyms"])
    assert {"mouse", "mice", "小鼠"} <= set(by_id["bio_species:mus_musculus"]["synonyms"])
    assert {"rat", "rats", "大鼠"} <= set(by_id["bio_species:rattus_norvegicus"]["synonyms"])
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

    assert by_label["count matrix"]["concept_type"] == "expression_matrix"
    assert set(by_label["count matrix"]["differential_expression_candidate_tools"]) == {"DESeq2", "edgeR"}
    assert by_label["raw counts"]["concept_type"] == "raw_count_matrix"
    assert by_label["raw counts"]["data_category"] == "raw_counts"
    assert by_label["raw counts"]["is_raw_counts"] is True
    assert set(by_label["raw counts"]["differential_expression_candidate_tools"]) == {"DESeq2", "edgeR"}
    for label in ["TPM", "FPKM", "RPKM", "CPM"]:
        assert by_label[label]["concept_type"] == "normalized_expression"
        assert by_label[label]["data_category"] == "normalized_expression"
        assert by_label[label]["is_raw_counts"] is False
        assert "raw counts" not in by_label[label].get("synonyms", [])
    assert by_label["gene symbol"]["concept_type"] == "gene_identifier"
    assert by_label["Ensembl ID"]["concept_type"] == "gene_identifier"
    assert by_label["probe ID"]["concept_type"] == "platform_identifier"
    assert by_label["series matrix"]["concept_type"] == "geo_file_type"
    assert by_label["series matrix"]["is_expression_matrix"] is False
    assert by_label["sample metadata"]["concept_type"] == "geo_metadata"
    assert by_label["sample metadata"]["is_expression_matrix"] is False
    assert all(term["shared_core_allowed"] is False for term in terms)
    assert all(term["meta_scope_allowed"] is False for term in terms)


def test_geo_core_dataset_registry_and_stop_terms_are_scoped() -> None:
    registry = _terms("bioinformatics_dataset_registry_terms.json")
    stop_terms = _terms("bioinformatics_stop_terms.json")

    assert {term["preferred_label"] for term in registry} == {"platform annotation"}
    assert {term["term"] for term in stop_terms} == {"dataset", "sample", "series"}
    assert all(term["term_type"] == "scoped_stop_term" for term in stop_terms)
    assert all(term["stop_scope"] == "free_topic_expansion" for term in stop_terms)
    assert all(term["global_stop_word"] is False for term in stop_terms)
    for term in stop_terms:
        assert {"sample_metadata_detection", "geo_record_type_detection", "file_type_detection"} <= set(term["does_not_block"])
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
    assert by_term["mouse"]["source_file"] == "data/medical_terms/bioinformatics/bioinformatics_species_terms.json"
    for term in ["TPM", "FPKM", "RPKM", "CPM", "dataset", "sample", "series"]:
        assert by_term[term]["status"] == "approved-with-note"
    for term in ["TPM", "FPKM", "RPKM", "CPM"]:
        assert by_term[term]["concept_type"] == "normalized_expression"
        assert by_term[term]["is_raw_counts"] is False
    for term in ["dataset", "sample", "series"]:
        assert by_term[term]["term_role"] == "scoped_stop_term"
        assert by_term[term]["stop_scope"] == "free_topic_expansion"
        assert by_term[term]["global_stop_word"] is False
        assert {"sample_metadata_detection", "geo_record_type_detection", "file_type_detection"} <= set(by_term[term]["does_not_block"])
    assert all(item["covered"] is True for item in audit["items"])  # type: ignore[index]
    assert all(item["shared_core_allowed"] is False for item in audit["items"])  # type: ignore[index]
    assert all(item["meta_scope_allowed"] is False for item in audit["items"])  # type: ignore[index]


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
