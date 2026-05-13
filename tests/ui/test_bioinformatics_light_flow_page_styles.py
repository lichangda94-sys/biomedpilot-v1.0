from __future__ import annotations

import pytest

QtWidgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = QtWidgets.QApplication
QFrame = QtWidgets.QFrame
QLabel = QtWidgets.QLabel
QPushButton = QtWidgets.QPushButton

from app.bioinformatics.pages.differential_expression_page import DifferentialExpressionPage
from app.bioinformatics.pages.geo_asset_detection_page import GeoAssetDetectionPage
from app.bioinformatics.pages.geo_cleaning_page import GeoCleaningPage
from app.bioinformatics.pages.geo_download_page import GeoDownloadPage
from app.shared.ui import BioMedPilotColors, page_title_qss


@pytest.fixture
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def _button_with_text(page, text: str) -> QPushButton:
    for button in page.findChildren(QPushButton):
        if button.text() == text:
            return button
    raise AssertionError(f"button not found: {text}")


@pytest.mark.parametrize(
    ("page_cls", "primary_text", "secondary_text", "next_text"),
    [
        (GeoDownloadPage, "生成下载计划", "选择 GEO 查询计划", "下一步：数据资产识别"),
        (GeoAssetDetectionPage, "识别本地数据资产", "选择 GEO 下载计划", "下一步：数据清洗"),
        (GeoCleaningPage, "生成清洗计划", "选择资产识别结果", "下一步：样本分组"),
        (DifferentialExpressionPage, "运行差异分析预检", "选择样本分组计划", "下一步：富集分析"),
    ],
)
def test_light_flow_pages_use_shared_ui_styles(qt_app, page_cls, primary_text: str, secondary_text: str, next_text: str) -> None:
    page = page_cls()

    title_label = next(label for label in page.findChildren(QLabel) if label.text() == page._state.title)
    assert title_label.styleSheet() == page_title_qss()

    feature_status = next(label for label in page.findChildren(QLabel) if label.text().startswith("功能状态："))
    assert BioMedPilotColors.PRIMARY_NAVY in feature_status.styleSheet()

    assert BioMedPilotColors.PRIMARY_NAVY in _button_with_text(page, primary_text).styleSheet()
    assert BioMedPilotColors.BIO_SOFT in _button_with_text(page, secondary_text).styleSheet()
    assert BioMedPilotColors.PRIMARY_NAVY in _button_with_text(page, next_text).styleSheet()

    assert BioMedPilotColors.BORDER_MEDIUM in "".join(frame.styleSheet() for frame in page.findChildren(QFrame))
    assert BioMedPilotColors.STATUS_ERROR in page._error_label.styleSheet()
    assert BioMedPilotColors.SURFACE_MUTED in page._status_label.styleSheet()
