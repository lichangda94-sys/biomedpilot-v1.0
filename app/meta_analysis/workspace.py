from __future__ import annotations

from collections.abc import Callable

from app.shared.feature_availability import FeatureAvailability, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability


def meta_analysis_features() -> list[FeatureItem]:
    return [feature_item_from_availability(feature) for feature in meta_analysis_step_features()]


def meta_analysis_step_features() -> list[FeatureAvailability]:
    step_ids = {
        "meta-literature-import",
        "meta-dedup-prep",
        "meta-duplicate-review",
        "meta-screening",
        "meta-extraction",
        "meta-analysis",
        "meta-reporting",
    }
    return [feature for feature in list_features("meta_analysis") if feature.feature_id in step_ids]


try:
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFrame = QHBoxLayout = QLabel = QPushButton = QScrollArea = QVBoxLayout = QWidget = None


if QWidget is not None:
    from app.meta_analysis.pages.literature_import_page import LiteratureImportPage
    from app.meta_analysis.pages.prepare_screening_page import PrepareScreeningPage
    from app.meta_analysis.pages.duplicate_review_page import DuplicateReviewPage
    from app.meta_analysis.pages.screening_page import ScreeningPage
    from app.meta_analysis.pages.extraction_page import ExtractionPage
    from app.meta_analysis.pages.analysis_page import AnalysisPage
    from app.meta_analysis.pages.reporting_page import ReportingPage

    class MetaAnalysisWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            root = QVBoxLayout(self)
            header = QHBoxLayout()
            title = QLabel("Meta Analysis / 医学 Meta 分析工作台")
            title.setStyleSheet("font-size: 24px; font-weight: 700;")
            header.addWidget(title)
            header.addStretch(1)
            back = QPushButton("返回首页")
            if on_back:
                back.clicked.connect(on_back)
            header.addWidget(back)
            root.addLayout(header)

            note = QLabel("业务代码边界：Meta legacy 项目保留在 app/meta_analysis/legacy/。当前页面提供步骤入口、状态说明和下一步提示。")
            note.setWordWrap(True)
            root.addWidget(note)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.addWidget(LiteratureImportPage())
            content_layout.addWidget(PrepareScreeningPage())
            content_layout.addWidget(DuplicateReviewPage())
            content_layout.addWidget(ScreeningPage())
            content_layout.addWidget(ExtractionPage())
            content_layout.addWidget(AnalysisPage())
            content_layout.addWidget(ReportingPage())
            for feature in meta_analysis_step_features():
                if feature.feature_id in {"meta-literature-import", "meta-dedup-prep", "meta-duplicate-review", "meta-screening", "meta-extraction", "meta-analysis", "meta-reporting"}:
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

    class MetaAnalysisWorkspaceWidget:  # type: ignore[no-redef]
        pass
