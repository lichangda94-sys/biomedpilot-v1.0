from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTextEdit

    from app.labtools.workspace import LabToolsWorkspaceWidget
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


def test_labtools_workspace_instantiates_as_scoped_imagej_consumer(qt_app) -> None:
    widget = LabToolsWorkspaceWidget()

    labels = "\n".join(label.text() for label in widget.findChildren(QLabel))
    notes = "\n".join(note.toPlainText() for note in widget.findChildren(QTextEdit))
    buttons = [button.text() for button in widget.findChildren(QPushButton)]

    assert widget.page_keys() == ("image_analysis",)
    assert widget.current_page_key() == "image_analysis"
    assert "ImageJ/Fiji 本机引擎" in labels
    assert "LabTools 图像定量 workflow" in labels
    assert "不内置 WB/gel 真实分析、agarose gel、自动 ROI、细胞计数" in labels
    assert "不会上传图片，不联网，不调用模型服务" in notes
    assert "检测 ImageJ/Fiji" in buttons
