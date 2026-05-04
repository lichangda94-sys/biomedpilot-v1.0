from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import app.shared.query_intelligence.medical_terms.term_lookup as term_lookup
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from app.shared.query_intelligence.medical_terms.term_index_loader import SQLITE_SCHEMA_VERSION, load_full_term_index
from app.shared.query_intelligence.medical_terms.term_index_models import TermConcept


def _write_full_index(path: Path, *, schema_version: str = SQLITE_SCHEMA_VERSION) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE ontology_terms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id TEXT UNIQUE NOT NULL,
                ontology_source TEXT NOT NULL,
                ontology_id TEXT,
                canonical_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                term_type TEXT NOT NULL,
                definition TEXT,
                source_reference TEXT,
                payload_json TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE ontology_build_metadata (
                build_id TEXT PRIMARY KEY,
                build_time TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                source_versions TEXT NOT NULL,
                source_files TEXT NOT NULL,
                entry_counts TEXT NOT NULL,
                warnings TEXT NOT NULL,
                fallback_mode TEXT NOT NULL,
                index_kind TEXT NOT NULL
            )
            """
        )
        payload = {
            "concept_id": "full:test_disease",
            "source_vocabulary": "MONDO",
            "source_id": "MONDO:TEST",
            "preferred_label_en": "full index test disease",
            "synonyms_en": ["full index synonym"],
            "exact_synonyms_en": ["full index exact"],
            "related_synonyms_en": [],
            "abbreviations": ["FITD"],
            "mesh_terms": ["Full Index Test Disease"],
            "disease_group": "",
            "concept_type": "disease",
            "parent_terms": [],
            "cross_refs": {"tcga": ["TCGA-FULL"], "gtex": ["FullTissue"]},
            "license": "CC BY 4.0",
            "version": "test",
            "normalized_terms": ["测试病", "full index test disease"],
        }
        conn.execute(
            """
            INSERT INTO ontology_terms (
                concept_id, ontology_source, ontology_id, canonical_name,
                normalized_name, term_type, definition, source_reference,
                payload_json, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                payload["concept_id"],
                "MONDO",
                "MONDO:TEST",
                "full index test disease",
                "full index test disease",
                "disease",
                "",
                "test-fixture",
                json.dumps(payload, ensure_ascii=False),
                "2026-05-05T00:00:00+00:00",
            ),
        )
        conn.execute(
            "INSERT INTO ontology_build_metadata VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "test-build",
                "2026-05-05T00:00:00+00:00",
                schema_version,
                "{}",
                "[]",
                "{}",
                "[]",
                "test",
                "test",
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


def test_full_index_corrupt_falls_back_to_json(monkeypatch, tmp_path: Path) -> None:
    index_path = tmp_path / "broken.sqlite"
    index_path.write_text("not sqlite", encoding="utf-8")
    load_full_term_index.cache_clear()
    monkeypatch.setattr(term_lookup, "load_full_term_index", lambda: load_full_term_index(str(index_path)))

    result = lookup_medical_terms("脑胶质瘤")

    assert "medical_terms_index.sqlite" not in result.term_sources
    assert "glioma" in result.disease_terms_en
    assert "zh_term_overrides" in result.term_sources


def test_full_index_schema_mismatch_falls_back_to_json(monkeypatch, tmp_path: Path) -> None:
    index_path = tmp_path / "old-schema.sqlite"
    _write_full_index(index_path, schema_version="old.schema")
    load_full_term_index.cache_clear()
    monkeypatch.setattr(term_lookup, "load_full_term_index", lambda: load_full_term_index(str(index_path)))

    result = lookup_medical_terms("心血管疾病")

    assert "medical_terms_index.sqlite" not in result.term_sources
    assert "cardiovascular disease" in result.disease_terms_en
    assert "zh_term_overrides" in result.term_sources


def test_built_sqlite_index_can_be_loaded_first(monkeypatch, tmp_path: Path) -> None:
    index_path = tmp_path / "medical_terms_index.sqlite"
    report_path = tmp_path / "medical_terms_index_build_report.json"
    metadata_path = tmp_path / "source_metadata.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/update_medical_term_index.py",
            "--output",
            str(index_path),
            "--build-report-output",
            str(report_path),
            "--metadata-output",
            str(metadata_path),
        ],
        check=True,
    )
    load_full_term_index.cache_clear()
    monkeypatch.setattr(term_lookup, "load_full_term_index", lambda: load_full_term_index(str(index_path)))

    result = lookup_medical_terms("膀胱")

    assert "medical_terms_index.sqlite" in result.term_sources
    assert "Bladder" in result.gtex_tissue_candidates


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
