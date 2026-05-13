from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.literature_import_page import literature_import_state_from_batch_summary
from app.meta_analysis.services.literature_batch_import_service import (
    LiteratureBatchImportRequest,
    LiteratureBatchImportService,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "literature"


def test_literature_batch_import_executes_active_batch_service_and_returns_summary(tmp_path: Path) -> None:
    service = LiteratureBatchImportService(storage_root=tmp_path)

    summary = service.execute_import(
        LiteratureBatchImportRequest(
            project_id="meta-panel",
            source_path=str(FIXTURES / "zotero_export.ris"),
            import_format="auto",
            source_database="Zotero",
            search_date="2026-04-29",
            search_strategy="tea therapy randomized trial",
            dedup_mode="detect_only",
        )
    )

    assert summary.success
    assert summary.status == "completed"
    assert summary.import_format == "ris"
    assert summary.source_database == "Zotero"
    assert summary.search_date == "2026-04-29"
    assert summary.search_strategy == "tea therapy randomized trial"
    assert summary.dedup_mode == "detect_only"
    assert summary.raw_record_count == 1
    assert summary.parsed_record_count == 1
    assert summary.normalized_record_count == 1
    assert summary.failed_record_count == 0
    assert summary.diagnostics_path.endswith("_import_diagnostics.json")
    assert summary.warnings_path.endswith("_import_warnings.csv")
    assert Path(summary.diagnostics_path).exists()
    assert Path(summary.warnings_path).exists()
    batch_payload = json.loads((tmp_path / "projects" / "meta-panel" / "meta_analysis" / "literature" / "import_batches.json").read_text(encoding="utf-8"))
    assert batch_payload[0]["metadata"]["source_database"] == "Zotero"
    assert batch_payload[0]["metadata"]["search_date"] == "2026-04-29"
    assert batch_payload[0]["metadata"]["search_strategy"] == "tea therapy randomized trial"
    assert batch_payload[0]["metadata"]["dedup_mode"] == "detect_only"


def test_literature_batch_import_failure_returns_readable_error_without_crashing(tmp_path: Path) -> None:
    service = LiteratureBatchImportService(storage_root=tmp_path)

    summary = service.execute_import(
        LiteratureBatchImportRequest(
            project_id="meta-panel",
            source_path=str(tmp_path / "missing.ris"),
            import_format="auto",
            source_database="Zotero",
        )
    )

    assert not summary.success
    assert "文件不存在" in summary.message
    assert summary.error_message == summary.message
    assert summary.batch_id == ""
    assert summary.status == ""


def test_literature_batch_import_rejects_unknown_format_before_active_execution(tmp_path: Path) -> None:
    source = tmp_path / "records.txt"
    source.write_text("not a supported literature file", encoding="utf-8")
    service = LiteratureBatchImportService(storage_root=tmp_path)

    summary = service.execute_import(
        LiteratureBatchImportRequest(
            project_id="meta-panel",
            source_path=str(source),
            import_format="auto",
            dedup_mode="detect_only",
        )
    )

    assert not summary.success
    assert "无法识别导入格式" in summary.message
    assert not (tmp_path / "projects" / "meta-panel" / "meta_analysis" / "literature" / "import_batches.json").exists()


def test_literature_import_page_state_from_batch_summary_displays_batch_and_diagnostics(tmp_path: Path) -> None:
    service = LiteratureBatchImportService(storage_root=tmp_path)
    summary = service.execute_import(
        LiteratureBatchImportRequest(
            project_id="meta-panel",
            source_path=str(FIXTURES / "pubmed_export.nbib"),
            import_format="nbib",
            source_database="PubMed",
            search_date="2026-04-29",
            search_strategy="randomized placebo treatment trial",
            dedup_mode="manual_review",
        )
    )

    state = literature_import_state_from_batch_summary(summary)
    diagnostics = state.diagnostics_summary or {}

    assert state.status_label == "测试中"
    assert state.next_step == "下一步：Review duplicates。"
    assert state.last_batch_summary == summary
    assert state.source_database == "PubMed"
    assert state.search_date == "2026-04-29"
    assert state.search_strategy == "randomized placebo treatment trial"
    assert state.dedup_mode == "manual_review"
    assert diagnostics["duplicate_identifier_count"] == 1
    assert state.total_warning_count >= 1
    assert state.diagnostics_export_path == summary.diagnostics_path
    assert state.warnings_export_path == summary.warnings_path
    assert any(row.key == "duplicate_identifier_count" for row in state.warning_table)
