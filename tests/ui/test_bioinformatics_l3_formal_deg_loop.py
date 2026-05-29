from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    from app.bioinformatics.project_workspace import create_bioinformatics_project
    from app.bioinformatics.results.registry import load_registry
    from app.bioinformatics.workflow_pages import BioinformaticsAnalysisTaskCenterWidget, BioinformaticsResultsBrowserWidget
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_bioinformatics_l3_formal_deg_current_ui_loop(qt_app, tmp_path: Path) -> None:
    """Prove the current Bioinformatics UI can drive one real formal DEG loop."""
    project = create_bioinformatics_project("Bioinformatics L3 Formal DEG", tmp_path)
    _write_standardized_deg_inputs(project.project_root)

    task_center = BioinformaticsAnalysisTaskCenterWidget()
    task_center.refresh_project(project)

    confirm_button = _button(task_center, "确认 formal DEG 参数")
    assert confirm_button.isEnabled(), task_center.status_message()
    confirm_button.click()
    assert "已确认 formal DEG 参数" in task_center.status_message()

    run_button = _button(task_center, "运行两组 controlled DEG")
    assert run_button.isEnabled(), run_button.toolTip()
    run_button.click()
    assert "已完成两组 controlled DEG MVP" in task_center.status_message()

    registry = load_registry(project.project_root)
    formal_results = [entry for entry in registry.get("results", []) if entry.get("result_semantics") == "formal_computed_result"]
    assert len(formal_results) == 1
    entry = formal_results[0]
    result_id = str(entry["result_id"])
    table_path = project.project_root / entry["output_artifacts"][0]["path"]
    log_path = project.project_root / entry["log_artifacts"][0]["path"]
    assert table_path.is_file()
    assert log_path.is_file()
    table_text = table_path.read_text(encoding="utf-8")
    assert "p_value" in table_text
    assert "adjusted_p_value" in table_text
    assert entry["report_ready_eligible"] is False
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []

    results = BioinformaticsResultsBrowserWidget()
    results.refresh_project(project)
    summary = results.findChild(QLabel, "formalDegReviewSummary")
    assert summary is not None
    assert "genes=3" in summary.text()
    assert "method=welch_t_test" in summary.text()

    exported = results.export_formal_deg_review_csv()
    assert exported is not None
    assert exported["status"] == "passed"
    assert Path(str(exported["export_path"])).is_file()
    assert exported["report_ready_eligible"] is False

    plot = results.generate_formal_deg_plot_artifact()
    assert plot is not None
    assert plot["status"] == "passed"
    assert plot["plot_artifact"]["source_result_id"] == result_id
    assert plot["plot_artifact"]["source_result_semantics"] == "formal_computed_result"
    image_artifacts = plot["plot_artifact"]["image_artifacts"]
    assert image_artifacts
    assert (project.project_root / image_artifacts[0]["path"]).is_file()
    assert plot["report_ready_eligible"] is False

    results.refresh_results()
    report_button = _wait_for_enabled_button(results, "生成 formal DEG report-ready package")
    assert report_button.isEnabled()
    report = results.generate_formal_deg_report_ready_package()
    assert report is not None
    assert report["status"] == "formal_deg_report_ready_package_created"
    assert report["section_scope"] == "formal_deg_only"
    assert report["gsea_enabled"] is False
    assert report["survival_enabled"] is False
    package_path = Path(str(report["user_visible_package_path"]))
    assert package_path.is_dir()
    assert (package_path / "formal_deg_report.md").is_file()
    assert (package_path / "tables").is_dir()
    assert (package_path / "plots").is_dir()
    assert (package_path / "manifests" / "formal_deg_parameter_confirmation.json").is_file()
    assert "仅包含 formal DEG section" in results.status_message()


def _button(widget, text: str) -> QPushButton:
    for button in widget.findChildren(QPushButton):
        if button.text() == text:
            return button
    raise AssertionError(f"button not found: {text}")


def _wait_for_enabled_button(widget, text: str) -> QPushButton:
    button = _button(widget, text)
    for _ in range(5):
        if button.isEnabled():
            return button
        if hasattr(widget, "refresh_results"):
            widget.refresh_results()
        QApplication.processEvents()
    return button


def _write_standardized_deg_inputs(root: Path) -> None:
    matrix = root / "input" / "deg_l3_count_matrix.tsv"
    matrix.parent.mkdir(parents=True, exist_ok=True)
    matrix.write_text(
        "gene\tcase1\tcase2\tcase3\tctrl1\tctrl2\tctrl3\n"
        "TP53\t30\t32\t31\t8\t9\t7\n"
        "EGFR\t4\t5\t4\t20\t21\t19\n"
        "BAX\t16\t15\t17\t14\t13\t14\n",
        encoding="utf-8",
    )
    sample = root / "input" / "deg_l3_sample_metadata.tsv"
    sample.write_text(
        "sample_id\tgroup\n"
        "case1\tcase\ncase2\tcase\ncase3\tcase\n"
        "ctrl1\tcontrol\nctrl2\tcontrol\nctrl3\tcontrol\n",
        encoding="utf-8",
    )
    group = root / "input" / "deg_l3_group_design.json"
    group.write_text(
        json.dumps(
            {
                "comparison_id": "case_vs_control",
                "case_group": "case",
                "control_group": "control",
                "group_design": {
                    "sample_group_assignments": {
                        "case1": "case",
                        "case2": "case",
                        "case3": "case",
                        "ctrl1": "control",
                        "ctrl2": "control",
                        "ctrl3": "control",
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    assets = [
        _asset("deg-l3-expression", "raw_count_matrix", "expression_repository", matrix, value_type="count", gene_id_type="symbol"),
        _asset("deg-l3-sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("deg-l3-group", "group_design", "group_design_repository", group),
    ]
    selection = {"expression": {"asset_id": "deg-l3-expression", "selection_state": "user_confirmed"}}
    repository = {"schema_version": "biomedpilot.repository_manifest.v1", "assets": assets, "default_asset_selection": selection}
    registry = {"schema_version": "biomedpilot.standardized_assets_registry.v2", "assets": assets, "default_asset_selection": selection}
    repo_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.write_text(json.dumps(repository, ensure_ascii=False, indent=2), encoding="utf-8")
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


def _asset(asset_id: str, asset_type: str, repository: str, path: Path, *, value_type: str = "", gene_id_type: str = "symbol") -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_role": "expression_matrix" if "expression" in asset_type or "count" in asset_type else asset_type,
        "repository": repository,
        "path": str(path),
        "file_path": str(path),
        "validation_status": "passed",
        "analysis_ready": True,
        "expression_value_type": value_type,
        "gene_id_type": gene_id_type,
    }
