from __future__ import annotations

from collections.abc import Callable

from app.shared.feature_availability import FeatureAvailability, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability


def bioinformatics_features() -> list[FeatureItem]:
    return [feature_item_from_availability(feature) for feature in bioinformatics_step_features()]


def bioinformatics_step_features() -> list[FeatureAvailability]:
    step_ids = {
        "bio-data-import",
        "bio-download",
        "bio-asset-detection",
        "bio-cleaning",
        "bio-sample-groups",
        "bio-deg",
        "bio-enrichment",
    }
    return [feature for feature in list_features("bioinformatics") if feature.feature_id in step_ids]


try:
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
except Exception:  # pragma: no cover - non-GUI environments import feature registry only.
    QFrame = QHBoxLayout = QLabel = QPushButton = QScrollArea = QVBoxLayout = QWidget = None


if QWidget is not None:
    from app.bioinformatics.pages.geo_import_page import GeoImportPage
    from app.bioinformatics.pages.geo_download_page import GeoDownloadPage
    from app.bioinformatics.pages.geo_asset_detection_page import GeoAssetDetectionPage
    from app.bioinformatics.pages.geo_cleaning_page import GeoCleaningPage
    from app.bioinformatics.pages.sample_grouping_page import SampleGroupingPage
    from app.bioinformatics.pages.differential_expression_page import DifferentialExpressionPage
    from app.bioinformatics.pages.enrichment_page import EnrichmentPage

    class BioinformaticsWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            root = QVBoxLayout(self)
            header = QHBoxLayout()
            title = QLabel("Bioinformatics Analysis / 生信分析工作台")
            title.setStyleSheet("font-size: 24px; font-weight: 700;")
            header.addWidget(title)
            header.addStretch(1)
            back = QPushButton("返回首页")
            if on_back:
                back.clicked.connect(on_back)
            header.addWidget(back)
            root.addLayout(header)

            note = QLabel("业务代码边界：生信 legacy 项目保留在 app/bioinformatics/legacy/。当前页面提供步骤入口、状态说明和下一步提示。")
            note.setWordWrap(True)
            root.addWidget(note)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.addWidget(GeoImportPage())
            content_layout.addWidget(GeoDownloadPage())
            content_layout.addWidget(GeoAssetDetectionPage())
            content_layout.addWidget(GeoCleaningPage())
            content_layout.addWidget(SampleGroupingPage())
            content_layout.addWidget(DifferentialExpressionPage())
            content_layout.addWidget(EnrichmentPage())
            for feature in bioinformatics_step_features():
                if feature.feature_id in {
                    "bio-data-import",
                    "bio-download",
                    "bio-asset-detection",
                    "bio-cleaning",
                    "bio-sample-groups",
                    "bio-deg",
                    "bio-enrichment",
                }:
                    continue
                content_layout.addWidget(_feature_row(feature))
            content_layout.addStretch(1)
            scroll.setWidget(content)
            root.addWidget(scroll, 1)


    def _feature_row(feature: FeatureAvailability) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
        layout = QVBoxLayout(frame)
        title = QLabel(feature.display_label())
        title.setStyleSheet("font-weight: 700;")
        detail = QLabel(feature.description)
        detail.setWordWrap(True)
        source = QLabel(f"legacy 来源：{feature.legacy_source or '统一壳子占位'}")
        source.setWordWrap(True)
        next_step = QLabel(f"下一步：{feature.next_step}")
        next_step.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(detail)
        layout.addWidget(source)
        layout.addWidget(next_step)
        return frame

else:

    class BioinformaticsWorkspaceWidget:  # type: ignore[no-redef]
        pass
