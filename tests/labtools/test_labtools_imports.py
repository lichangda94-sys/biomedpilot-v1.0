from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_labtools_module_exports_features() -> None:
    from app.labtools.workspace import labtools_features

    features = labtools_features()

    assert [feature.name for feature in features] == ["实验计算器", "试剂与配方", "图像定量", "实验模板"]
    assert features[0].status.value == "测试中"
    assert all(feature.module == "labtools" for feature in features)


def test_labtools_workspace_instantiates_when_qt_available() -> None:
    try:
        from PySide6.QtWidgets import QApplication, QPushButton

        from app.labtools.workspace import LabToolsWorkspaceWidget
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    app = QApplication.instance() or QApplication([])
    widget = LabToolsWorkspaceWidget()

    assert app is not None
    assert widget.objectName() == "labToolsWorkspace"
    assert widget.page_keys() == ("home", "calculators", "pending")
    assert widget.current_page_key() == "home"
    assert widget.findChild(QPushButton, "primaryButton") is not None
