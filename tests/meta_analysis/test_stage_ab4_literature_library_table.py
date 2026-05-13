from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.literature_library_page import (
    DUPLICATE_RISK_HIGH,
    DUPLICATE_RISK_NONE,
    DUPLICATE_RISK_PROBABLE,
    initial_literature_library_state,
    literature_library_state_from_project,
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_ab4_literature_library_empty_state_no_crash(tmp_path: Path) -> None:
    project_dir = tmp_path / "empty-project"

    initial = initial_literature_library_state(project_dir)
    state = literature_library_state_from_project(project_dir)

    assert initial.status_label == "Testing / Developer Preview"
    assert state.total_records == 0
    assert "missing_literature_records" in state.warnings
    assert "Literature Import Wizard" in state.empty_state
    assert "duplicate_risk" in state.table_columns


def test_ab4_literature_library_reads_records_and_workflow_statuses(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    write_json(
        project_dir / "literature" / "literature_records.json",
        {
            "records": [
                {
                    "record_id": "rec-1",
                    "title": "Trial A",
                    "creators": [
                        {"full_name": "John Smith", "creator_type": "author", "order": 1},
                        {"full_name": "Mei Wang", "creator_type": "corresponding_author", "order": 2},
                    ],
                    "year": "2024",
                    "date": "2024-01-01",
                    "journal": "Journal A",
                    "doi": "10.1000/a",
                    "pmid": "111",
                    "publication_type": "randomized_trial",
                    "abstract": "Abstract",
                    "source_database": "PubMed",
                    "source_file": "records.nbib",
                    "import_batch_id": "batch-1",
                },
                {
                    "record_id": "rec-2",
                    "title": "Trial B",
                    "authors_text": "Lee K",
                    "year": "2023",
                    "publication_title": "Journal B",
                    "abstract": "",
                    "source_database": "Zotero",
                    "import_batch_id": "batch-1",
                },
            ]
        },
    )
    write_json(project_dir / "screening" / "screening_decisions.json", {"records": [{"record_id": "rec-1", "decision": "include"}]})
    write_json(project_dir / "fulltext" / "fulltext_registry.json", {"fulltext_files": [{"record_id": "rec-1", "availability_status": "available"}]})
    write_json(project_dir / "extraction" / "extraction_records.json", {"records": [{"record_id": "rec-1", "validation_status": "valid"}]})

    state = literature_library_state_from_project(project_dir)
    by_id = {row.record_id: row for row in state.rows}

    assert state.total_records == 2
    assert by_id["rec-1"].first_author == "John Smith"
    assert by_id["rec-1"].corresponding_author == "Mei Wang"
    assert by_id["rec-1"].abstract_available is True
    assert by_id["rec-1"].screening_status == "include"
    assert by_id["rec-1"].fulltext_status == "available"
    assert by_id["rec-1"].extraction_status == "valid"
    assert by_id["rec-2"].journal == "Journal B"
    assert by_id["rec-2"].abstract_available is False


def test_ab4_duplicate_risk_tags_and_colors_are_read_only(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    write_json(
        project_dir / "literature" / "literature_records.json",
        {
            "records": [
                {"record_id": "rec-1", "title": "A", "authors_text": "Smith", "year": "2024"},
                {"record_id": "rec-2", "title": "A duplicate", "authors_text": "Smith", "year": "2024"},
                {"record_id": "rec-3", "title": "B", "authors_text": "Wang", "year": "2023"},
            ]
        },
    )
    write_json(
        project_dir / "deduplication" / "duplicate_candidate_groups.json",
        {
            "duplicate_groups": [
                {"group_id": "dup-exact", "record_ids": ["rec-1", "rec-2"], "reason": "pmid_exact", "confidence": 0.99},
                {"group_id": "dup-suspected", "record_ids": ["rec-3"], "reason": "title_author_year_journal_suspected", "confidence": 0.82},
            ]
        },
    )

    state = literature_library_state_from_project(project_dir)
    by_id = {row.record_id: row for row in state.rows}

    assert by_id["rec-1"].duplicate_risk == DUPLICATE_RISK_HIGH
    assert by_id["rec-1"].row_status_color == "red"
    assert by_id["rec-3"].duplicate_risk == DUPLICATE_RISK_PROBABLE
    assert by_id["rec-3"].row_status_color == "yellow"
    assert state.high_duplicate_risk_count == 2
    assert state.probable_duplicate_count == 1
    assert "high_duplicate_risk_records:2" in state.warnings
    assert "auto" not in state.output_summary.lower()


def test_ab4_no_obvious_duplicate_risk_label_is_not_trusted_claim(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    write_json(project_dir / "literature" / "literature_records.json", {"records": [{"record_id": "rec-1", "title": "Only record"}]})

    state = literature_library_state_from_project(project_dir)
    row = state.rows[0]

    assert row.duplicate_risk == DUPLICATE_RISK_NONE
    assert row.row_status_color == "green"
    assert row.duplicate_risk_label == "No obvious duplicate risk"
    assert "trusted" not in row.duplicate_risk_label.lower()
    assert "可信" not in row.duplicate_risk_label
    assert "不代表文献质量" in " ".join(state.testing_limitations)


def test_ab4_reads_legacy_import_records_shape(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    write_json(
        project_dir / "literature_import" / "batch-1_records.json",
        {
            "records": [
                {
                    "record_id": "legacy-1",
                    "title": "Legacy imported record",
                    "authors": ["Smith J", "Lee K"],
                    "journal": "Legacy Journal",
                    "batch_id": "batch-1",
                    "source": "ris",
                }
            ]
        },
    )

    state = literature_library_state_from_project(project_dir)
    row = state.rows[0]

    assert state.total_records == 1
    assert row.record_id == "legacy-1"
    assert row.authors_text == "Smith J; Lee K"
    assert row.import_batch_id == "batch-1"
    assert row.source_database == "ris"
