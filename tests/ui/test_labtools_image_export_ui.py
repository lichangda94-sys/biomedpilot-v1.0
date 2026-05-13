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


def _wound_result(tmp_path):
    from app.labtools.image_analysis.wound_healing import (
        WoundHealingParameters,
        WoundHealingROI,
        analyze_wound_healing_area,
    )

    image_path = tmp_path / "wound-ui.png"
    image = Image.new("L", (10, 10))
    image.putdata([250] * 25 + [20] * 75)
    image.save(image_path)
    return analyze_wound_healing_area(
        WoundHealingParameters(str(image_path), WoundHealingROI("analysis ROI", 0, 0, 10, 10), 200, "bright"),
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
    from PySide6.QtWidgets import QLabel, QPushButton

    result = _fluorescence_result(tmp_path)
    buttons = [button.text() for button in image_widget.findChildren(QPushButton)]
    labels = "\n".join(label.text() for label in image_widget.findChildren(QLabel))

    assert "导出当前 ROI 结果" in buttons
    assert "仅在用户选择目录后写入 JSON manifest、CSV summary、Markdown 片段和 ROI overlay PNG" in labels
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
    assert "当前分析结果仍保留" in text
    assert image_widget.has_exportable_result() is True
    assert image_widget._export_button.isEnabled() is True
    assert "导出成功" not in text
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
        lambda _directory: (_ for _ in ()).throw(ImageAnalysisError("模拟导出失败\nTraceback: hidden")),
    )

    image_widget._handle_export_current_result()

    text = image_widget._task_summary.toPlainText()
    assert "导出需要调整" in text
    assert "模拟导出失败" in text
    assert "Traceback" not in text
    assert "当前分析结果保留如下" in text
    assert image_widget.has_exportable_result() is True
    assert image_widget._export_button.isEnabled() is True
    assert "导出成功" not in text
    assert "ROI 结果导出完成" not in text


def test_image_export_success_shows_four_file_roles(image_widget, tmp_path, monkeypatch) -> None:
    result = _fluorescence_result(tmp_path)
    export_dir = tmp_path / "exports"
    image_widget.set_export_result_for_testing("fluorescence_intensity", result)
    monkeypatch.setattr(image_widget, "_select_export_directory", lambda: str(export_dir))

    image_widget._handle_export_current_result()

    text = image_widget._task_summary.toPlainText()
    assert "导出成功" in text
    assert "ROI 结果导出完成" in text
    assert "导出目录" in text
    assert "JSON manifest" in text
    assert "CSV summary" in text
    assert "Markdown fragment" in text
    assert "ROI overlay PNG" in text
    assert "人工复核提示" in text
    assert "Developer Preview / testing" in text
    assert "manual ROI auxiliary analysis" in text
    assert "manual-review / semi-quantitative 辅助结果" in text
    for forbidden in ("正式报告", "正式结论", "临床诊断", "无需人工复核", "production-grade"):
        assert forbidden not in text
    assert len(list(Path(export_dir).iterdir())) == 4


def test_image_export_wound_success_keeps_manual_review_semantics(image_widget, tmp_path, monkeypatch) -> None:
    result = _wound_result(tmp_path)
    export_dir = tmp_path / "wound-exports"
    image_widget.set_export_result_for_testing("wound_healing", result)
    monkeypatch.setattr(image_widget, "_select_export_directory", lambda: str(export_dir))

    image_widget._handle_export_current_result()

    text = image_widget._task_summary.toPlainText()
    assert "导出成功" in text
    assert "ROI 结果导出完成" in text
    assert "分析类型：wound_healing" in text
    assert "JSON manifest" in text
    assert "CSV summary" in text
    assert "Markdown fragment" in text
    assert "ROI overlay PNG" in text
    assert "人工复核提示" in text
    assert "Developer Preview / testing" in text
    assert "manual ROI auxiliary analysis" in text
    assert "manual-review / semi-quantitative 辅助结果" in text
    assert "实验 SOP" in text
    for forbidden in ("正式报告", "正式结论", "临床诊断", "无需人工复核", "production-grade"):
        assert forbidden not in text
    assert len(list(Path(export_dir).iterdir())) == 4


def test_image_export_same_directory_twice_does_not_overwrite(image_widget, tmp_path, monkeypatch) -> None:
    result = _fluorescence_result(tmp_path)
    export_dir = tmp_path / "exports"
    image_widget.set_export_result_for_testing("fluorescence_intensity", result)
    monkeypatch.setattr(image_widget, "_select_export_directory", lambda: str(export_dir))

    image_widget._handle_export_current_result()
    first_files = sorted(path.name for path in export_dir.iterdir())
    first_manifest = next(path for path in export_dir.glob("*_manifest.json"))
    first_manifest_text = first_manifest.read_text(encoding="utf-8")

    image_widget._handle_export_current_result()

    all_files = sorted(path.name for path in export_dir.iterdir())
    manifests = sorted(path.name for path in export_dir.glob("*_manifest.json"))
    assert len(first_files) == 4
    assert len(all_files) == 8
    assert len(manifests) == 2
    assert manifests[0] != manifests[1]
    assert first_manifest.exists()
    assert first_manifest.read_text(encoding="utf-8") == first_manifest_text
    assert image_widget.has_exportable_result() is True
    assert image_widget._export_button.isEnabled() is True
