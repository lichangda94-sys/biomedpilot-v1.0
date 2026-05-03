from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import app.shared.query_intelligence.medical_terms.term_lookup as term_lookup
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from app.shared.query_intelligence.medical_terms.term_index_loader import load_full_term_index
from app.shared.query_intelligence.medical_terms.term_index_models import TermConcept


def _write_full_index(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE term_concepts (
                concept_id TEXT PRIMARY KEY,
                source_vocabulary TEXT,
                source_id TEXT,
                preferred_label_en TEXT,
                synonyms_en TEXT,
                exact_synonyms_en TEXT,
                related_synonyms_en TEXT,
                abbreviations TEXT,
                mesh_terms TEXT,
                disease_group TEXT,
                concept_type TEXT,
                parent_terms TEXT,
                cross_refs TEXT,
                license TEXT,
                version TEXT,
                normalized_terms TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO term_concepts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "full:test_disease",
                "MONDO",
                "MONDO:TEST",
                "full index test disease",
                json.dumps(["full index synonym"]),
                json.dumps(["full index exact"]),
                json.dumps([]),
                json.dumps(["FITD"]),
                json.dumps(["Full Index Test Disease"]),
                "",
                "disease",
                json.dumps([]),
                json.dumps({"tcga": ["TCGA-FULL"], "gtex": ["FullTissue"]}),
                "CC BY 4.0",
                "test",
                json.dumps(["测试病", "full index test disease"]),
            ),
        )
        conn.commit()


def test_full_index_exists_is_preferred(monkeypatch, tmp_path: Path) -> None:
    index_path = tmp_path / "medical_terms_index.sqlite"
    _write_full_index(index_path)
    load_full_term_index.cache_clear()
    monkeypatch.setattr(term_lookup, "load_full_term_index", lambda: load_full_term_index(str(index_path)))
    monkeypatch.setattr(term_lookup, "load_zh_overrides", lambda: ())

    result = lookup_medical_terms("测试病")

    assert "medical_terms_index.sqlite" in result.term_sources
    assert "full index test disease" in result.disease_terms_en
    assert "TCGA-FULL" in result.tcga_project_candidates


def test_full_index_missing_reads_mini_index(monkeypatch) -> None:
    mini = (
        TermConcept(
            concept_id="mini:test_mini",
            source_vocabulary="mini",
            source_id="test_mini",
            preferred_label_en="mini index disease",
            concept_type="disease",
            normalized_terms=["迷你病"],
        ),
    )
    monkeypatch.setattr(term_lookup, "load_full_term_index", lambda: ())
    monkeypatch.setattr(term_lookup, "load_mini_term_index", lambda: mini)
    monkeypatch.setattr(term_lookup, "load_zh_overrides", lambda: ())

    result = lookup_medical_terms("迷你病")

    assert "mini_medical_terms_index" in result.term_sources
    assert "mini index disease" in result.disease_terms_en


def test_mini_index_missing_falls_back_to_registry(monkeypatch) -> None:
    monkeypatch.setattr(term_lookup, "load_full_term_index", lambda: ())
    monkeypatch.setattr(term_lookup, "load_mini_term_index", lambda: ())
    monkeypatch.setattr(term_lookup, "load_zh_overrides", lambda: ())

    result = lookup_medical_terms("甲状腺癌")

    assert "biomedical_term_registry" in result.term_sources
    assert "thyroid cancer" in result.disease_terms_en


def test_missing_term_files_do_not_crash(monkeypatch) -> None:
    monkeypatch.setattr(term_lookup, "load_full_term_index", lambda: ())
    monkeypatch.setattr(term_lookup, "load_mini_term_index", lambda: ())
    monkeypatch.setattr(term_lookup, "load_zh_overrides", lambda: ())

    result = lookup_medical_terms("完全未知词", target_context="meta_analysis")

    assert result.matched is False
    assert result.warnings


def test_source_metadata_and_license_attribution_exist() -> None:
    root = Path("data/medical_terms")
    metadata = json.loads((root / "source_metadata.json").read_text(encoding="utf-8"))
    attribution = (root / "license_attribution.md").read_text(encoding="utf-8")

    vocabularies = {item["vocabulary_name"]: item for item in metadata["vocabularies"]}
    for name in ("MONDO", "DOID", "NCIt", "MeSH", "EFO"):
        assert name in vocabularies
        assert "source_url" in vocabularies[name]
        assert "license" in vocabularies[name]
        assert "downloaded_at" in vocabularies[name]
        assert "processed_at" in vocabularies[name]
        assert "included_in_package" in vocabularies[name]
    assert "MONDO" in attribution and "CC BY 4.0" in attribution
    assert "DOID" in attribution and "CC0 1.0" in attribution
    assert "NCIt" in attribution and "CC BY 4.0" in attribution
    assert "MeSH" in attribution and "does not imply endorsement" in attribution
    assert "EFO" in attribution and "Apache License 2.0" in attribution


def test_package_manifest_records_shared_medical_term_index() -> None:
    manifest = json.loads(Path("data/package_manifest.json").read_text(encoding="utf-8"))
    medical = manifest["medical_terms_index"]

    assert medical["scope"] == "BioMedPilot shared medical vocabulary"
    assert medical["not_bioinformatics_specific"] is True
    assert "data/medical_terms/mini_medical_terms_index.json" in medical["included_in_default_package"]
    assert medical["optional_enhancement"] == "data/medical_terms/medical_terms_index.sqlite"
