from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QScrollArea

    from app.shell.main_window import MainWindow
    from app.shared.semantic_keys import PageKey
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    MainWindow = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


@pytest.fixture
def labtools_window(qt_app):
    window = MainWindow()
    window._welcome_page.enter_workspace()
    window.show_labtools()
    yield window
    window.close()
    window.deleteLater()
    qt_app.processEvents()


def _content(window: MainWindow):
    return window.findChild(QScrollArea, "labtoolsShellPage").widget()


def _labels(window: MainWindow) -> str:
    return "\n".join(label.text() for label in _content(window).findChildren(QLabel))


def _open_experiment_page(window: MainWindow, page_key: str) -> None:
    window._show_labtools_home()
    primary = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsEntryButton")
        if item.property("semanticKey") == PageKey.LABTOOLS_EXPERIMENT_MODULES.value
    )
    primary.click()
    secondary = next(
        item
        for item in window.findChildren(QPushButton, "labtoolsSecondaryEntryButton")
        if item.property("pageKey") == page_key
    )
    secondary.click()


def _boundary_actions(window: MainWindow) -> list[QPushButton]:
    return _content(window).findChildren(QPushButton, "labtoolsBoundaryActionButton")


def test_sds_page_boundary_renders_adapter_needed_layout(labtools_window) -> None:
    _open_experiment_page(labtools_window, "sds_page")
    content = _content(labtools_window)
    labels = _labels(labtools_window)
    actions = _boundary_actions(labtools_window)

    assert content.property("pageKey") == "sds_page"
    assert content.findChild(QLabel, "labtoolsBoundaryPanelTitle") is not None
    assert "SDS-PAGE 属于 Protein Experiment 后续 subpage" in labels
    assert "Resolving gel section" in labels
    assert "Stacking gel section" in labels
    assert "导出 XLSX 需文件选择器适配" in labels
    assert actions and all(not action.isEnabled() for action in actions)
    assert any(action.property("disabledState") == "disabled_missing_file_picker" for action in actions)


def test_bca_od_boundary_shows_matrix_without_elisa_or_formal_report(labtools_window) -> None:
    _open_experiment_page(labtools_window, "bca_od_mvp")
    content = _content(labtools_window)
    labels = _labels(labtools_window)
    wells = content.findChildren(QLabel, "labtoolsBcaWellCell")
    actions = _boundary_actions(labtools_window)

    assert content.property("pageKey") == "bca_od_mvp"
    assert len(wells) == 96
    assert "Linear-fit summary：testing / MVP preview" in labels
    assert "low R2 warning" in labels
    assert "High CV warning" in labels
    assert "Negative corrected OD warning" in labels
    assert "Out-of-range warning" in labels
    assert "ELISA" not in labels
    assert "4PL" not in labels
    assert "formal report" not in labels
    assert "临床级定量" in labels
    assert actions and all(not action.isEnabled() for action in actions)


def test_cell_experiment_workspace_has_three_main_areas_without_elisa(labtools_window) -> None:
    _open_experiment_page(labtools_window, "cell_experiment_workspace")
    content = _content(labtools_window)
    labels = _labels(labtools_window)
    actions = _boundary_actions(labtools_window)
    settings_link = content.findChild(QPushButton, "labtoolsSettingsLinkButton")

    assert content.property("pageKey") == "cell_experiment_workspace"
    assert content.findChild(QLabel, "labtoolsBoundaryPanelTitle") is not None
    assert "细胞信息 / Cell Profile & Dynamic State" in labels
    assert "细胞实验记录 / Experiment Record Templates" in labels
    assert "细胞结果处理工具 / Result Processing" in labels
    assert "A549" in labels
    assert "传代、复苏、冻存、接种、给药 / 处理、转染" in labels
    assert "接种：计算辅助可用；保存记录 disabled" in labels
    assert "ELISA" not in labels
    assert "假保存记录" in labels
    assert settings_link is not None and settings_link.isEnabled()
    assert actions and all(not action.isEnabled() for action in actions)


def test_elisa_boundary_blocks_run_save_and_export(labtools_window) -> None:
    _open_experiment_page(labtools_window, "elisa_boundary")
    content = _content(labtools_window)
    labels = _labels(labtools_window)
    actions = _boundary_actions(labtools_window)

    assert content.property("pageKey") == "elisa_boundary"
    assert "blocked_until_backend" in labels
    assert "标准曲线模型尚未固化" in labels
    assert "运行 ELISA 分析 - 后端未完成" in [action.text() for action in actions]
    assert "保存记录 - 后端未完成" in [action.text() for action in actions]
    assert "导出报告 - 后端未完成" in [action.text() for action in actions]
    assert all(not action.isEnabled() for action in actions)
    assert all(action.property("disabledState") == "disabled_backend_missing" for action in actions)


def test_image_processing_boundary_keeps_external_engine_and_no_macro_surface(labtools_window) -> None:
    _open_experiment_page(labtools_window, "image_processing_boundary")
    content = _content(labtools_window)
    labels = _labels(labtools_window)
    actions = _boundary_actions(labtools_window)
    settings_link = content.findChild(QPushButton, "labtoolsSettingsLinkButton")

    assert content.property("pageKey") == "image_processing_boundary"
    assert "图像列表" in labels
    assert "中央图像预览" in labels
    assert "Scratch：planned" in labels
    assert "Transwell：planned" in labels
    assert "WB band ROI：planned" in labels
    assert "IHC / staining：planned" in labels
    assert "ImageJ/Fiji：外部能力配置" in labels
    assert "macro" not in labels.lower()
    assert settings_link is not None and settings_link.isEnabled()
    assert actions and all(not action.isEnabled() for action in actions)


def test_imagej_fiji_is_not_labtools_primary_entry(labtools_window) -> None:
    labtools_window._show_labtools_home()
    content = _content(labtools_window)
    titles = "\n".join(label.text() for label in content.findChildren(QLabel, "labtoolsPrimaryEntryTitle"))

    assert "通用计算器" in titles
    assert "试剂制备" in titles
    assert "实验模块" in titles
    assert "ImageJ" not in titles
    assert "Fiji" not in titles


def test_boundary_pages_do_not_create_labtools_storage(qt_app, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    window = MainWindow()
    try:
        window._welcome_page.enter_workspace()
        window.show_labtools()
        for page_key in ("sds_page", "bca_od_mvp", "cell_experiment_workspace", "elisa_boundary", "image_processing_boundary"):
            _open_experiment_page(window, page_key)
            assert all(not action.isEnabled() for action in _boundary_actions(window))

        assert not (Path(tmp_path) / ".labtools").exists()
        assert list(Path(tmp_path).iterdir()) == []
    finally:
        window.close()
        window.deleteLater()
        qt_app.processEvents()
