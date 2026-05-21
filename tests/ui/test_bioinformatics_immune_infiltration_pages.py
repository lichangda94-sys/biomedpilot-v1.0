from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QPushButton

    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.workflow_pages import BioinformaticsAnalysisTaskCenterWidget, BioinformaticsImmuneInfiltrationWidget
    from app.bioinformatics.workspace import BioinformaticsWorkspaceWidget
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


def test_analysis_task_center_has_immune_scoring_entry(qt_app, tmp_path: Path) -> None:
    summary = create_bioinformatics_project("B7 UI", tmp_path)
    _write_registry(summary.project_root, _write_matrix(summary.project_root / "expr.tsv"))
    opened: list[Path] = []
    widget = BioinformaticsAnalysisTaskCenterWidget(on_configure_immune_scoring=lambda root: opened.append(root))
    widget.refresh_project(summary)
    assert any("免疫浸润 / TME评分" in button.text() for button in widget.findChildren(QPushButton))
    widget.open_immune_scoring()
    assert opened == [summary.project_root]
    assert "探索性" in widget.status_message()


def test_immune_scoring_page_runs_and_previews_result(qt_app, tmp_path: Path) -> None:
    summary = create_bioinformatics_project("B7 UI Run", tmp_path)
    matrix = _write_matrix(summary.project_root / "expr.tsv")
    _write_registry(summary.project_root, matrix)
    widget = BioinformaticsImmuneInfiltrationWidget()
    widget.refresh_project(summary)
    assert widget.findChild(QPushButton, "immuneRunButton").isEnabled()
    result = widget.run_scoring()
    assert result is not None
    assert Path(result.score_matrix_path).is_file()
    assert "已完成" in widget.status_message()


def test_workspace_can_open_immune_scoring_page(qt_app, tmp_path: Path) -> None:
    summary = create_bioinformatics_project("B7 Workspace", tmp_path)
    workspace = BioinformaticsWorkspaceWidget()
    workspace.show_analysis_tasks(summary)
    workspace.show_immune_scoring(summary)
    assert workspace.current_page_object_name() == "bioinformaticsImmuneInfiltrationPage"


def _write_matrix(path: Path) -> Path:
    path.write_text(
        "gene_id\tS1\tS2\tS3\n"
        "CD3D\t10\t3\t4\n"
        "CD8A\t12\t2\t3\n"
        "GZMB\t15\t1\t2\n"
        "PRF1\t14\t2\t1\n"
        "PDCD1\t5\t0\t1\n"
        "NKG7\t11\t1\t2\n"
        "ACTB\t50\t51\t52\n"
        "GAPDH\t30\t31\t29\n"
        "HLA-DRA\t9\t9\t8\n"
        "MS4A1\t0\t7\t8\n",
        encoding="utf-8",
    )
    return path


def _write_registry(root: Path, matrix_path: Path) -> None:
    path = root / "manifests" / "standardized_assets_registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.standardized_assets_registry.v2",
                "assets": [
                    {
                        "asset_id": "expr",
                        "label_zh": "UI TPM expression",
                        "asset_type": "normalized_expression_matrix",
                        "file_path": str(matrix_path),
                        "expression_value_type": "TPM",
                        "gene_id_type": "symbol",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
