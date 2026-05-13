from __future__ import annotations

from collections.abc import Callable

from app.shared.feature_status import FeatureItem, FeatureStatus


def labtools_features() -> list[FeatureItem]:
    return [
        FeatureItem("labtools", "实验计算器", FeatureStatus.TESTING, "本地辅助计算草稿：浓度、稀释、溶液配制、细胞接种、qPCR 配液与 WB/SDS-PAGE 上样计算；使用前需人工核对。"),
        FeatureItem("labtools", "试剂与配方", FeatureStatus.TESTING, "本地常用配方库、体积缩放、stock-to-working 稀释和用户配方草稿；不替代 SOP/SDS 人工核对。"),
        FeatureItem(
            "labtools",
            "图像定量",
            FeatureStatus.TESTING,
            "荧光 manual ROI grayscale 指标和 scratch/wound manual ROI + threshold 面积估算为 manual-review MVP；细胞计数、灰度/墨值仍为占位。",
        ),
        FeatureItem("labtools", "实验模板", FeatureStatus.TESTING, "qPCR、WB、细胞接种、scratch assay 和免疫荧光图像记录结构化草稿；不是完整 ELN。"),
    ]


try:
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

    from app.labtools.labtools_home import LabToolsHomeWidget
    from app.labtools.ui.calculator_widgets import LabToolsCalculatorWidget
    from app.labtools.ui.image_analysis_widgets import LabToolsImageAnalysisWidget
    from app.labtools.ui.recipe_widgets import LabToolsRecipeWidget
    from app.labtools.ui.template_widgets import LabToolsTemplateWidget
    from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("labToolsWorkspace")
            self._on_back = on_back
            self._page_keys: list[str] = []
            self._build_ui()

        def page_keys(self) -> tuple[str, ...]:
            return tuple(self._page_keys)

        def current_page_key(self) -> str:
            current = self._stack.currentWidget()
            if current is self._home_page:
                return "home"
            if current is self._calculator_page:
                return "calculators"
            if current is self._recipe_page:
                return "recipes"
            if current is self._image_analysis_page:
                return "image_analysis"
            if current is self._template_page:
                return "templates"
            return "unknown"

        def show_home(self) -> None:
            self._stack.setCurrentWidget(self._home_page)

        def show_calculators(self) -> None:
            self._stack.setCurrentWidget(self._calculator_page)

        def show_recipes(self) -> None:
            self._stack.setCurrentWidget(self._recipe_page)

        def show_image_analysis(self) -> None:
            self._stack.setCurrentWidget(self._image_analysis_page)

        def show_templates(self) -> None:
            self._stack.setCurrentWidget(self._template_page)

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
            home = QPushButton("工具首页")
            home.clicked.connect(self.show_home)
            header_layout.addWidget(home)
            if self._on_back is not None:
                back = QPushButton("返回模块首页")
                back.clicked.connect(self._on_back)
                header_layout.addWidget(back)
            root.addWidget(header)

            self._stack = QStackedWidget()
            self._home_page = LabToolsHomeWidget()
            self._home_page.calculators_requested.connect(self.show_calculators)
            self._home_page.reagents_requested.connect(self.show_recipes)
            self._home_page.image_quant_requested.connect(self.show_image_analysis)
            self._home_page.templates_requested.connect(self.show_templates)
            self._calculator_page = LabToolsCalculatorWidget()
            self._recipe_page = LabToolsRecipeWidget()
            self._image_analysis_page = LabToolsImageAnalysisWidget()
            self._template_page = LabToolsTemplateWidget()
            for key, page in (
                ("home", self._home_page),
                ("calculators", self._calculator_page),
                ("recipes", self._recipe_page),
                ("image_analysis", self._image_analysis_page),
                ("templates", self._template_page),
            ):
                self._page_keys.append(key)
                self._stack.addWidget(page)
            self._stack.setCurrentWidget(self._home_page)
            root.addWidget(self._stack, 1)

else:  # pragma: no cover

    class LabToolsWorkspaceWidget:  # type: ignore[no-redef]
        def page_keys(self) -> tuple[str, ...]:
            return ("home", "calculators", "recipes", "image_analysis", "templates")
