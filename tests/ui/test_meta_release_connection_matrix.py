from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton, QTableWidget

    from app.meta_analysis.connection_matrix import ACTION_RESULT_SCHEMA_VERSION, CONNECTION_ROWS, MATRIX_SCHEMA_VERSION
    from app.meta_analysis.project_workspace import create_meta_analysis_project
    from app.meta_analysis.workspace import MetaAnalysisWorkspaceWidget
except Exception as exc:  # pragma: no cover - optional GUI runtime.
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def meta_project(tmp_path: Path):
    return create_meta_analysis_project("Release Meta Wiring", tmp_path, research_topic="Release Meta wiring")


def test_meta_release_connection_matrix_lists_ui_backend_branch_and_test(qt_app, meta_project) -> None:
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(meta_project.project_root)

    table = widget.findChild(QTableWidget, "metaReleaseConnectionMatrixTable")
    assert table is not None
    assert table.rowCount() == len(CONNECTION_ROWS)
    assert table.property("schemaVersion") == MATRIX_SCHEMA_VERSION

    text = _table_text(table)
    for row in CONNECTION_ROWS:
        assert row.ui_page in text
        assert row.backend_capability in text
        assert row.branch_source in text
        assert row.expected_test in text

    matrix_path = meta_project.project_root / "manifests" / "meta_release_connection_matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix["schema_version"] == MATRIX_SCHEMA_VERSION
    assert {item["action_id"] for item in matrix["rows"]} == {row.action_id for row in CONNECTION_ROWS}


def test_meta_release_connection_buttons_call_services_and_write_artifacts(qt_app, meta_project) -> None:
    widget = MetaAnalysisWorkspaceWidget()
    widget.set_project_dir(meta_project.project_root)

    buttons = widget.findChildren(QPushButton, "metaReleaseActionButton")
    by_action = {str(button.property("actionId")): button for button in buttons}
    assert set(by_action) == {row.action_id for row in CONNECTION_ROWS}

    for row in CONNECTION_ROWS:
        button = by_action[row.action_id]
        assert button.isEnabled() is True
        assert button.property("expectedTest") == row.expected_test
        assert button.property("branchSource") == row.branch_source

        button.click()
        QApplication.processEvents()

        latest_path = meta_project.project_root / "meta_analysis" / "connection_runs" / f"{row.action_id}_latest.json"
        assert latest_path.is_file()
        payload = json.loads(latest_path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == ACTION_RESULT_SCHEMA_VERSION
        assert payload["action_id"] == row.action_id
        assert payload["services_called"]
        assert payload["ui_page"] == row.ui_page
        assert payload["backend_capability"] == row.backend_capability
        assert payload["branch_source"] == row.branch_source
        assert payload["expected_test"] == row.expected_test
        assert payload["status"] in {"passed", "blocked"}
        if payload["status"] == "passed":
            assert payload["artifact_paths"] or payload["action_artifact_path"]
        else:
            assert payload["disabled_reason"]
            assert payload["artifact_paths"] or payload["backend_results"]
        assert row.action_id in widget.status_message()

    library = meta_project.project_root / "literature" / "literature_records.json"
    screening = meta_project.project_root / "screening" / "title_abstract_queue_v2.json"
    report_manifest = meta_project.project_root / "reports" / "report_manifest.json"
    assert library.is_file()
    assert screening.is_file()
    assert report_manifest.is_file()


def _table_text(table: QTableWidget) -> str:
    return " ".join(
        table.item(row, column).text()
        for row in range(table.rowCount())
        for column in range(table.columnCount())
        if table.item(row, column) is not None
    )
