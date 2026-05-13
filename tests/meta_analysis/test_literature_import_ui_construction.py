from __future__ import annotations

from app.meta_analysis.pages.literature_import_page import (
    ImportDiagnosticsCard,
    ImportDiagnosticsWarningRow,
    LiteratureImportPageState,
    _RESULT_CARD_STYLE,
    _RESULT_TEXT_STYLE,
    _RESULT_TITLE_STYLE,
    _diagnostics_cards_text,
    _failed_preview_text,
    _recent_batches_text,
    _warning_rows_text,
    initial_literature_import_state,
    literature_import_ui_panel_state,
)
from app.ui_style_tokens import COLORS


def test_literature_import_ui_panel_state_exposes_desktop_sections() -> None:
    state = literature_import_ui_panel_state()

    assert state.status_label == "测试中"
    assert "file_picker" in state.sections
    assert "diagnostics_summary_cards" in state.sections
    assert "warning_table" in state.sections
    assert "recent_import_batches" in state.sections
    assert "missing_title_count" in state.diagnostics_fields
    assert "duplicate_candidate_count" in state.recent_batch_fields
    assert state.next_action == "Review duplicates"


def test_literature_import_diagnostics_panel_text_is_readable() -> None:
    base = initial_literature_import_state()
    state = LiteratureImportPageState(
        **{
            **base.__dict__,
            "diagnostics_cards": (
                ImportDiagnosticsCard("missing_title_count", "Missing title", 1),
                ImportDiagnosticsCard("missing_doi_count", "Missing DOI", 2),
            ),
            "warning_table": (
                ImportDiagnosticsWarningRow("missing_title_count", "Missing title", 1, "Title is required.", "blocker"),
            ),
            "failed_records_preview": ("row 2 missing title",),
            "warning_list": ("row 3 missing DOI",),
            "diagnostics_export_path": "/tmp/import_diagnostics.json",
            "warnings_export_path": "/tmp/import_warnings.csv",
            "total_warning_count": 3,
            "warning_severity_counts": {"blocker": 1, "major": 2},
        }
    )

    diagnostics_text = _diagnostics_cards_text(state)
    warning_text = _warning_rows_text(state)
    failed_text = _failed_preview_text(state)

    assert "Total warnings: 3" in diagnostics_text
    assert "Missing title: 1" in diagnostics_text
    assert "Diagnostics path: /tmp/import_diagnostics.json" in diagnostics_text
    assert "[blocker] Missing title: 1" in warning_text
    assert "Severity counts: blocker=1, major=2" in warning_text
    assert "row 2 missing title" in failed_text
    assert "row 3 missing DOI" in failed_text


def test_literature_import_recent_batches_text_handles_empty_and_populated() -> None:
    empty = _recent_batches_text()
    base = initial_literature_import_state()
    state = LiteratureImportPageState(
        **{
            **base.__dict__,
            "recent_import_batches": (
                {
                    "batch_id": "batch-1",
                    "source_database": "PubMed",
                    "source_format": "nbib",
                    "raw_record_count": 3,
                    "parsed_record_count": 3,
                    "normalized_record_count": 2,
                    "failed_record_count": 1,
                    "warning_count": 4,
                    "duplicate_candidate_count": 1,
                },
            ),
        }
    )

    populated = _recent_batches_text(state)

    assert "No recent import batches" in empty
    assert "batch=batch-1" in populated
    assert "source=PubMed" in populated
    assert "duplicates=1" in populated


def test_literature_import_result_cards_use_readable_contrast_styles() -> None:
    assert f"background: {COLORS['light_gray']}" in _RESULT_CARD_STYLE
    assert f"color: {COLORS['text']}" in _RESULT_TEXT_STYLE
    assert f"color: {COLORS['deep_navy']}" in _RESULT_TITLE_STYLE
