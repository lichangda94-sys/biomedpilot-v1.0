from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton

    from app.meta_analysis.project_workspace import create_meta_analysis_project
    from app.meta_analysis.services.dedup_review_v2_service import DedupReviewV2Service
    from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _stage_m3_project(tmp_path: Path) -> Path:
    summary = create_meta_analysis_project("Stage M3", tmp_path)
    project_dir = summary.project_root
    LiteratureLibraryService().import_records(
        project_dir,
        project_id="stage-m3-ui",
        source_type="pubmed_confirmed_candidates",
        source_name="PubMed",
        raw_records=[
            {
                "record_id": "lit-ui-a",
                "title": "Obesity and thyroid cancer risk",
                "abstract": "Candidate abstract.",
                "authors": ["Alice Adams"],
                "journal": "Journal A",
                "year": "2024",
                "pmid": "111",
                "doi": "10.1000/a",
            },
            {
                "record_id": "lit-ui-b",
                "title": "Obesity and thyroid cancer risk",
                "abstract": "Duplicate candidate.",
                "authors": ["Alice Adams"],
                "journal": "Journal A",
                "year": "2024",
                "pmid": "111",
                "doi": "10.1000/a",
            },
        ],
    )
    return project_dir


def test_stage_m3_dedup_service_remains_available_as_old_capability_source(tmp_path: Path) -> None:
    project_dir = _stage_m3_project(tmp_path)

    result = DedupReviewV2Service().build_review_queue(project_dir, project_id="stage-m3-ui")

    assert result.output_path
    assert Path(result.output_path).exists()
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["group_count"] >= 1


def test_stage_m3_ui_uses_import_dedup_gate_not_old_page(qt_app, tmp_path: Path) -> None:
    project_dir = _stage_m3_project(tmp_path)
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(project_dir)
    widget.show_target_ia_page("import_dedup")

    assert widget.current_target_page_key() == "import_dedup"
    import_buttons = [button for button in widget.findChildren(QPushButton) if button.text().startswith("Import - adapter needed")]
    assert import_buttons
    assert all(not button.isEnabled() for button in import_buttons)
    assert all(button.property("disabledReason") for button in import_buttons)
    assert widget.findChild(QPushButton, "metaImportSourceButton") is not None
