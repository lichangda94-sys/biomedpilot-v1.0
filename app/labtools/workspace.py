from __future__ import annotations

from collections.abc import Callable

from app.shared.feature_status import FeatureItem, FeatureStatus


def labtools_features() -> list[FeatureItem]:
    return [
        FeatureItem(
            "labtools",
            "图像能力边界",
            FeatureStatus.TESTING,
            "消费 shared ImageJ/Fiji 本机引擎检测；manual-review 准备为 testing，未启用 WB/gel、agarose、自动 ROI、细胞计数或生产级真实图像算法。",
        )
    ]


try:
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

    from app.labtools.ui.image_analysis_widgets import LabToolsImageAnalysisWidget
    from app.ui_style_tokens import COLORS, FONT_SIZE, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsWorkspace")
            self._on_back = on_back
            self._build_ui()

        def page_keys(self) -> tuple[str, ...]:
            return ("image_analysis",)

        def current_page_key(self) -> str:
            return "image_analysis"

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)

            header = QFrame()
            header.setObjectName("labToolsWorkspaceHeader")
            header.setStyleSheet(
                f"QFrame#labToolsWorkspaceHeader {{ background: {COLORS['surface']}; border-bottom: 1px solid {COLORS['border']}; }}"
            )
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(SPACING["xl"], SPACING["md"], SPACING["xl"], SPACING["md"])
            title = QLabel("LabTools / 实验工具")
            title.setStyleSheet(f"color: {COLORS['bio']}; font-size: {FONT_SIZE['page_title']}px; font-weight: 760;")
            header_layout.addWidget(title)
            header_layout.addStretch(1)
            if self._on_back is not None:
                back = QPushButton("返回模块首页")
                back.clicked.connect(self._on_back)
                header_layout.addWidget(back)
            root.addWidget(header)
            root.addWidget(LabToolsImageAnalysisWidget(), 1)

else:  # pragma: no cover

    class LabToolsWorkspaceWidget:  # type: ignore[no-redef]
        def page_keys(self) -> tuple[str, ...]:
            return ("image_analysis",)

        def current_page_key(self) -> str:
            return "image_analysis"
