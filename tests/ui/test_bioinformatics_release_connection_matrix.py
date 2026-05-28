from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton, QTableWidget

    from app.bioinformatics.analysis_connection_matrix import CONNECTION_ROWS
    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.workflow_pages import BioinformaticsAnalysisTaskCenterWidget
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
def bio_project(tmp_path: Path):
    return create_bioinformatics_project("Release Bioinformatics Wiring", tmp_path)


def test_release_connection_matrix_lists_ui_backend_branch_and_test(qt_app, bio_project) -> None:
    widget = BioinformaticsAnalysisTaskCenterWidget()
    widget.refresh_project(bio_project)

    table = widget.findChild(QTableWidget, "bioinformaticsReleaseConnectionMatrixTable")
    assert table is not None
    assert table.rowCount() == len(CONNECTION_ROWS)
    assert table.property("schemaVersion") == "biomedpilot.bioinformatics_release_connection_matrix.v1"

    text = _table_text(table)
    for row in CONNECTION_ROWS:
        assert row.ui_page in text
        assert row.backend_capability in text
        assert row.branch_source in text
        assert row.expected_test in text

    matrix_path = bio_project.project_root / "manifests" / "bioinformatics_release_connection_matrix.json"
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix["schema_version"] == "biomedpilot.bioinformatics_release_connection_matrix.v1"
    assert {item["action_id"] for item in matrix["rows"]} == {row.action_id for row in CONNECTION_ROWS}


def test_release_connection_buttons_call_services_and_write_artifacts(qt_app, bio_project) -> None:
    widget = BioinformaticsAnalysisTaskCenterWidget()
    widget.refresh_project(bio_project)

    buttons = widget.findChildren(QPushButton, "bioinformaticsReleaseActionButton")
    by_action = {str(button.property("actionId")): button for button in buttons}
    assert set(by_action) == {row.action_id for row in CONNECTION_ROWS}

    for row in CONNECTION_ROWS:
        button = by_action[row.action_id]
        assert button.isEnabled() is True
        assert button.property("expectedTest") == row.expected_test
        assert button.property("branchSource") == row.branch_source

        button.click()
        QApplication.processEvents()

        latest_path = bio_project.project_root / "analysis" / "connection_runs" / f"{row.action_id}_latest.json"
        assert latest_path.is_file()
        payload = json.loads(latest_path.read_text(encoding="utf-8"))
        assert payload["schema_version"] == "biomedpilot.bioinformatics_release_action_result.v1"
        assert payload["action_id"] == row.action_id
        assert payload["services_called"]
        if row.action_id == "formal_deg_gate_run_review_report":
            assert "build_formal_deg_r_backend_capability" in payload["services_called"]
            assert payload["backend_results"]["r_backend_capability"]["install_action"] == "none_detect_first_only"
        if row.action_id in {"ora_gate_run_review_report", "gsea_gate_run_review_report"}:
            assert "detect_enrichment_r_backend_capability" in payload["services_called"]
            assert payload["backend_results"]["r_backend_capability"]["packaging_policy"] == "external_r_runtime_not_bundled"
        assert payload["status"] in {"passed", "blocked"}
        if payload["status"] == "passed":
            assert payload["artifact_paths"] or payload["action_artifact_path"]
        else:
            assert payload["disabled_reason"]
        assert row.action_id in widget.status_message()


def _table_text(table: QTableWidget) -> str:
    return " ".join(
        table.item(row, column).text()
        for row in range(table.rowCount())
        for column in range(table.columnCount())
        if table.item(row, column) is not None
    )
