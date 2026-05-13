from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QPushButton

    from app.meta_analysis.pages.analysis_page import AnalysisPage
except Exception as exc:  # pragma: no cover
    QApplication = None  # type: ignore[assignment]
    QCheckBox = QLabel = QPushButton = None  # type: ignore[assignment]
    AnalysisPage = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def test_m13_statistics_review_panel_instantiates_with_chinese_labels(qt_app) -> None:
    widget = AnalysisPage(project_id="m13-ui-test")
    rendered = "\n".join(
        [
            *[label.text() for label in widget.findChildren(QLabel)],
            *[button.text() for button in widget.findChildren(QPushButton)],
            *[checkbox.text() for checkbox in widget.findChildren(QCheckBox)],
        ]
    )

    assert "统计结果审核" in rendered
    assert "尚未审核" in rendered
    assert "已确认查看警告" in rendered
    assert "接受进入报告草稿" in rendered
    assert "标记需要修订" in rendered
    assert "不纳入报告" in rendered
    assert "申请报告就绪" in rendered
    assert "报告就绪" in rendered
    assert "raw JSON" not in rendered
    assert "pairwise-result-" not in rendered
