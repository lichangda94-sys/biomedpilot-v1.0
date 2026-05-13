from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.literature_import_page import (
    import_diagnostics_visual_summary,
    literature_import_state_from_result,
)
from app.meta_analysis.services.literature_import_service import ImportResult


def test_import_diagnostics_visual_summary_reads_core_quality_counts(tmp_path: Path) -> None:
    diagnostics_path = tmp_path / "batch-1_import_diagnostics.json"
    warnings_path = tmp_path / "batch-1_import_warnings.csv"
    diagnostics_path.write_text(
        json.dumps(
            {
                "warning_count": 9,
                "missing_title_count": 1,
                "missing_author_count": 2,
                "missing_year_count": 3,
                "missing_doi_count": 4,
                "missing_pmid_count": 5,
                "empty_abstract_count": 6,
                "invalid_doi_count": 7,
                "invalid_year_count": 8,
                "failed_record_count": 1,
                "failed_record_examples": ["record 2 missing title"],
                "parse_warning_examples": ["record 3 missing DOI"],
            }
        ),
        encoding="utf-8",
    )
    warnings_path.write_text("record_id,warning\nrec-3,missing_doi\n", encoding="utf-8")

    summary = import_diagnostics_visual_summary(str(diagnostics_path), warnings_path=str(warnings_path))
    card_values = {card.key: card.value for card in summary.summary_cards}

    assert summary.missing_diagnostics is False
    assert summary.total_warning_count == 9
    assert card_values["missing_title_count"] == 1
    assert card_values["missing_author_count"] == 2
    assert card_values["missing_year_count"] == 3
    assert card_values["missing_doi_count"] == 4
    assert card_values["missing_pmid_count"] == 5
    assert card_values["empty_abstract_count"] == 6
    assert card_values["invalid_doi_count"] == 7
    assert card_values["invalid_year_count"] == 8
    assert summary.failed_record_examples == ("record 2 missing title",)
    assert summary.warning_examples == ("record 3 missing DOI",)
    assert summary.warnings_csv_path == str(warnings_path)


def test_import_diagnostics_visual_summary_handles_missing_file_without_crashing(tmp_path: Path) -> None:
    diagnostics_path = tmp_path / "missing_import_diagnostics.json"

    summary = import_diagnostics_visual_summary(str(diagnostics_path))

    assert summary.missing_diagnostics is True
    assert summary.total_warning_count == 0
    assert all(card.value == 0 for card in summary.summary_cards)
    assert summary.warning_rows == ()
    assert summary.failed_record_examples == ()
    assert summary.warnings_csv_path.endswith("missing_import_warnings.csv")


def test_import_diagnostics_visual_summary_defaults_missing_fields_to_zero(tmp_path: Path) -> None:
    diagnostics_path = tmp_path / "batch-2_import_diagnostics.json"
    diagnostics_path.write_text(json.dumps({"missing_title_count": 2}), encoding="utf-8")

    summary = import_diagnostics_visual_summary(str(diagnostics_path))
    card_values = {card.key: card.value for card in summary.summary_cards}

    assert card_values["missing_title_count"] == 2
    assert card_values["missing_author_count"] == 0
    assert card_values["missing_year_count"] == 0
    assert card_values["missing_doi_count"] == 0
    assert card_values["missing_pmid_count"] == 0
    assert card_values["empty_abstract_count"] == 0
    assert card_values["invalid_doi_count"] == 0
    assert card_values["invalid_year_count"] == 0
    assert summary.total_warning_count == 2


def test_import_diagnostics_visual_summary_builds_warning_table_for_nonzero_counts(tmp_path: Path) -> None:
    diagnostics_path = tmp_path / "batch-3_import_diagnostics.json"
    diagnostics_path.write_text(
        json.dumps(
            {
                "missing_doi_count": 2,
                "missing_pmid_count": 3,
                "duplicate_identifier_count": 1,
                "failed_record_count": 1,
            }
        ),
        encoding="utf-8",
    )

    summary = import_diagnostics_visual_summary(str(diagnostics_path))
    warning_counts = {row.key: row.count for row in summary.warning_rows}

    assert warning_counts == {
        "missing_doi_count": 2,
        "missing_pmid_count": 3,
        "duplicate_identifier_count": 1,
        "failed_record_count": 1,
    }
    assert all(row.message for row in summary.warning_rows)


def test_literature_import_page_state_exposes_visual_diagnostics_summary(tmp_path: Path) -> None:
    diagnostics_path = tmp_path / "batch-4_import_diagnostics.json"
    warnings_path = tmp_path / "batch-4_import_warnings.csv"
    diagnostics_path.write_text(
        json.dumps(
            {
                "warning_count": 4,
                "missing_title_count": 1,
                "missing_author_count": 1,
                "invalid_year_count": 1,
                "failed_record_count": 1,
                "failed_record_examples": ["row 5 missing title"],
            }
        ),
        encoding="utf-8",
    )
    warnings_path.write_text("record_id,warning\nrec-5,missing_title\n", encoding="utf-8")
    result = ImportResult(
        success=True,
        source_path=str(tmp_path / "source.csv"),
        source_type="csv",
        total_records=5,
        imported_records=4,
        skipped_records=1,
        error_count=1,
        output_path=str(tmp_path / "literature_records.json"),
        message="Imported",
        details={"diagnostics_path": str(diagnostics_path), "warnings_path": str(warnings_path)},
    )

    state = literature_import_state_from_result(result)
    card_values = {card.key: card.value for card in state.diagnostics_cards}
    warning_counts = {row.key: row.count for row in state.warning_table}

    assert state.status_label == "测试中"
    assert state.total_warning_count == 4
    assert card_values["missing_title_count"] == 1
    assert card_values["missing_author_count"] == 1
    assert card_values["invalid_year_count"] == 1
    assert warning_counts["failed_record_count"] == 1
    assert state.failed_records_preview == ("row 5 missing title",)
    assert state.warnings_export_path == str(warnings_path)
