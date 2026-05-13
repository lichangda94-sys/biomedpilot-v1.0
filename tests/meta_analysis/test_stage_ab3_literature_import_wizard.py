from __future__ import annotations

from pathlib import Path

from app.meta_analysis.pages.literature_import_page import (
    execute_literature_import_wizard,
    initial_literature_import_wizard_state,
    preview_literature_import_files,
)
from app.meta_analysis.services.literature_batch_import_service import LiteratureBatchImportService


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "literature"


def test_ab3_import_wizard_initial_state_is_file_picker_first() -> None:
    state = initial_literature_import_wizard_state()

    assert state.title == "Literature Import Wizard"
    assert state.status_label == "测试中"
    assert state.current_step == "source_selection"
    assert state.file_picker_first is True
    assert state.multi_file_ready is True
    assert "auto" in state.format_options
    assert "manual_review" in state.dedup_mode_options
    assert "Review duplicates" in state.next_step
    assert "Developer Preview" in " ".join(state.testing_limitations)


def test_ab3_import_wizard_empty_input_returns_readable_error() -> None:
    result = execute_literature_import_wizard(project_id="meta-wizard", source_paths=())

    assert result.success is False
    assert result.summaries == ()
    assert result.state.current_step == "file_selection"
    assert result.state.warnings == ("no_files_selected",)
    assert "请选择至少一个" in result.message


def test_ab3_import_wizard_rejects_unsupported_file_before_execution(tmp_path: Path) -> None:
    unsupported = tmp_path / "records.txt"
    unsupported.write_text("not supported", encoding="utf-8")

    state = preview_literature_import_files([str(unsupported)])

    assert state.current_step == "file_selection"
    assert state.previews[0].detected_format == "unknown"
    assert state.previews[0].supported is False
    assert "无法识别导入格式" in state.warnings[0]


def test_ab3_import_wizard_preview_detects_supported_formats() -> None:
    state = preview_literature_import_files(
        [
            str(FIXTURES / "zotero_export.ris"),
            str(FIXTURES / "pubmed_export.nbib"),
            str(FIXTURES / "sample.csv"),
        ]
    )
    by_name = {preview.file_name: preview for preview in state.previews}

    assert state.current_step == "import_preview"
    assert by_name["zotero_export.ris"].detected_format == "ris"
    assert by_name["pubmed_export.nbib"].detected_format == "nbib"
    assert by_name["sample.csv"].detected_format == "csv"
    assert all(preview.supported for preview in state.previews)
    assert by_name["sample.csv"].record_count_preview is not None


def test_ab3_import_wizard_executes_single_file_and_exposes_diagnostics(tmp_path: Path) -> None:
    service = LiteratureBatchImportService(storage_root=tmp_path)

    result = execute_literature_import_wizard(
        project_id="meta-wizard",
        source_paths=[str(FIXTURES / "pubmed_export.nbib")],
        import_format="auto",
        source_database="PubMed",
        search_date="2026-04-29",
        search_strategy="randomized placebo treatment trial",
        dedup_mode="manual_review",
        service=service,
    )

    assert result.success is True
    assert result.state.current_step == "duplicate_review_handoff"
    assert result.summaries[0].import_format == "nbib"
    assert result.summaries[0].source_database == "PubMed"
    assert result.state.diagnostics_export_paths[0].endswith("_import_diagnostics.json")
    assert result.state.warnings_export_paths[0].endswith("_import_warnings.csv")
    assert any(row.key == "duplicate_identifier_count" for row in result.state.warning_table)
    assert result.state.next_step == "Review duplicates"


def test_ab3_import_wizard_multi_file_execution_is_deterministic_and_registers_batches(tmp_path: Path) -> None:
    service = LiteratureBatchImportService(storage_root=tmp_path)

    result = execute_literature_import_wizard(
        project_id="meta-wizard",
        source_paths=[
            str(FIXTURES / "zotero_export.ris"),
            str(FIXTURES / "sample.csv"),
        ],
        import_format="auto",
        source_database="Local exports",
        search_date="2026-04-29",
        search_strategy="validation batch",
        dedup_mode="detect_only",
        service=service,
    )

    assert result.success is True
    assert [preview.file_name for preview in result.state.previews] == sorted(["zotero_export.ris", "sample.csv"])
    assert len(result.summaries) == 2
    assert all(summary.batch_id for summary in result.summaries)
    assert len({summary.batch_id for summary in result.summaries}) == 2
    assert (tmp_path / "projects" / "meta-wizard" / "meta_analysis" / "literature" / "import_batches.json").exists()
