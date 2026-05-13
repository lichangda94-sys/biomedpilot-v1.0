from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


def _run_builder(tmp_path: Path) -> tuple[Path, Path]:
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
    return index_path, report_path


def test_can_build_sqlite_index_from_mini_vocabulary(tmp_path: Path) -> None:
    index_path, report_path = _run_builder(tmp_path)

    assert index_path.exists()
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["build_status"] == "success"
    assert report["schema_version"] == "biomedpilot.medical_terms.sqlite.v6"
    assert report["fallback_mode"] == "mini_vocabulary_only"
    assert report["index_kind"] == "mini-derived sqlite index"
    assert report["terms_count"] > 0
    assert report["synonyms_count"] > 0
    assert "No local ontology source files were parsed" in " ".join(report["warnings"])


def test_sqlite_schema_and_counts_are_present(tmp_path: Path) -> None:
    index_path, report_path = _run_builder(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    with sqlite3.connect(index_path) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        metadata = conn.execute("SELECT schema_version, fallback_mode FROM ontology_build_metadata").fetchone()
        terms_count = conn.execute("SELECT COUNT(*) FROM ontology_terms").fetchone()[0]
        synonyms_count = conn.execute("SELECT COUNT(*) FROM ontology_synonyms").fetchone()[0]
        crossrefs_count = conn.execute("SELECT COUNT(*) FROM ontology_crossrefs").fetchone()[0]

    assert {"ontology_terms", "ontology_synonyms", "ontology_crossrefs", "ontology_search_index", "ontology_build_metadata"} <= tables
    assert metadata == ("biomedpilot.medical_terms.sqlite.v6", "mini_vocabulary_only")
    assert terms_count == report["terms_count"]
    assert synonyms_count == report["synonyms_count"]
    assert crossrefs_count == report["crossrefs_count"]


def test_repeated_build_replaces_index_without_error(tmp_path: Path) -> None:
    first_index, first_report = _run_builder(tmp_path)
    second_index, second_report = _run_builder(tmp_path)

    assert first_index == second_index
    assert first_report == second_report
    first = json.loads(first_report.read_text(encoding="utf-8"))
    second = json.loads(second_report.read_text(encoding="utf-8"))
    assert first["terms_count"] == second["terms_count"]
    assert first["synonyms_count"] == second["synonyms_count"]
