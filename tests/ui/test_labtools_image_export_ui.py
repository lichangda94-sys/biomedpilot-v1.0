from __future__ import annotations

import os
from pathlib import Path

import pytest
from PIL import Image

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _fluorescence_result(tmp_path):
    from app.labtools.image_analysis.fluorescence import (
        FluorescenceAnalysisParameters,
        FluorescenceROI,
        analyze_fluorescence_roi,
    )

    image_path = tmp_path / "fluorescence-ui.png"
    image = Image.new("L", (6, 3))
    image.putdata([20, 20, 20, 2, 2, 2, 20, 20, 20, 2, 2, 2, 20, 20, 20, 2, 2, 2])
    image.save(image_path)
    return analyze_fluorescence_roi(
        FluorescenceAnalysisParameters(
            image_path=str(image_path),
            signal_roi=FluorescenceROI("signal", 0, 0, 3, 3, "signal"),
            background_roi=FluorescenceROI("background", 3, 0, 3, 3, "background"),
        ),
        task_id="ui-export",
    )


@pytest.fixture()
def image_widget():
    try:
        from PySide6.QtWidgets import QApplication

        from app.labtools.ui.image_analysis_widgets import LabToolsImageAnalysisWidget
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    app = QApplication.instance() or QApplication([])
    widget = LabToolsImageAnalysisWidget()
    assert app is not None
    return widget


def test_image_export_button_disabled_until_result_exists(image_widget, tmp_path) -> None:
    result = _fluorescence_result(tmp_path)

    assert image_widget._export_button.isEnabled() is False
    assert image_widget.has_exportable_result() is False

    image_widget.set_export_result_for_testing("fluorescence_intensity", result)

    assert image_widget.has_exportable_result() is True
    assert image_widget._export_button.isEnabled() is True


def test_image_export_cancel_does_not_write_or_show_success(image_widget, tmp_path, monkeypatch) -> None:
    result = _fluorescence_result(tmp_path)
    export_dir = tmp_path / "exports"
    image_widget.set_export_result_for_testing("fluorescence_intensity", result)
    monkeypatch.setattr(image_widget, "_select_export_directory", lambda: "")

    image_widget._handle_export_current_result()

    text = image_widget._task_summary.toPlainText()
    assert "已取消导出" in text
    assert "ROI 结果导出完成" not in text
    assert not export_dir.exists()


def test_image_export_failure_surfaces_error_and_keeps_result(image_widget, tmp_path, monkeypatch) -> None:
    from app.labtools.image_analysis.image_models import ImageAnalysisError

    result = _fluorescence_result(tmp_path)
    image_widget.set_export_result_for_testing("fluorescence_intensity", result)
    monkeypatch.setattr(image_widget, "_select_export_directory", lambda: str(tmp_path / "exports"))
    monkeypatch.setattr(
        image_widget,
        "_perform_export_to_directory",
        lambda _directory: (_ for _ in ()).throw(ImageAnalysisError("模拟导出失败")),
    )

    image_widget._handle_export_current_result()

    text = image_widget._task_summary.toPlainText()
    assert "导出需要调整" in text
    assert "模拟导出失败" in text
    assert "当前分析结果保留如下" in text
    assert "ROI 结果导出完成" not in text


def test_image_export_success_shows_four_file_roles(image_widget, tmp_path, monkeypatch) -> None:
    result = _fluorescence_result(tmp_path)
    export_dir = tmp_path / "exports"
    image_widget.set_export_result_for_testing("fluorescence_intensity", result)
    monkeypatch.setattr(image_widget, "_select_export_directory", lambda: str(export_dir))

    image_widget._handle_export_current_result()

    text = image_widget._task_summary.toPlainText()
    assert "ROI 结果导出完成" in text
    assert "JSON manifest" in text
    assert "CSV summary" in text
    assert "Markdown 片段" in text
    assert "ROI overlay PNG" in text
    assert "manual-review / semi-quantitative 辅助结果" in text
    assert len(list(Path(export_dir).iterdir())) == 4
