from __future__ import annotations

from collections.abc import Callable

from app.shared.feature_status import FeatureItem, FeatureStatus


def labtools_features() -> list[FeatureItem]:
    return [
        FeatureItem("labtools", "通用试剂计算器", FeatureStatus.TESTING, "用于浓度、质量、体积、摩尔量、稀释等基础实验计算；不长期承载全部实验特异性计算。"),
        FeatureItem("labtools", "ImageJ/Fiji 本地引擎", FeatureStatus.TESTING, "用于图像 workflow 的本地 ImageJ/Fiji 检测与路径配置；不启用真实图像分析算法。"),
        FeatureItem("labtools", "试剂与实验记录", FeatureStatus.TESTING, "用于本地 recipe 草稿、实验记录草稿、模板保存和 JSON 导入导出；不等同于完整 ELN。"),
        FeatureItem(
            "labtools",
            "细胞实验",
            FeatureStatus.UNAVAILABLE,
            "用于细胞接种、活率、Transwell、wound healing、增殖率、台盼蓝、Alamar Blue 等；规划中，待确认使用逻辑。",
        ),
        FeatureItem(
            "labtools",
            "Western Blot",
            FeatureStatus.UNAVAILABLE,
            "用于 WB 上样计算、条带定量 workflow 占位；planned / 规划中 / 未启用，不启用 WB/gel 真实分析。",
        ),
        FeatureItem(
            "labtools",
            "PCR / qPCR",
            FeatureStatus.UNAVAILABLE,
            "用于 PCR/qPCR 体系计算、运行参数、plate layout、Ct / ΔCt / ΔΔCt 结果分析；规划中，待确认使用逻辑。",
        ),
        FeatureItem(
            "labtools",
            "ELISA / 吸光度与标准曲线",
            FeatureStatus.UNAVAILABLE,
            "用于 OD 值、标准曲线、BCA、Bradford、NanoDrop、ELISA 样本浓度反推等；规划中，待确认使用逻辑。",
        ),
    ]


try:
    from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

    from app.labtools.labtools_home import LabToolsHomeWidget
    from app.labtools.ui.calculator_widgets import LabToolsCalculatorWidget
    from app.labtools.ui.imagej_bridge_widgets import LabToolsImageJFijiStatusPanel
    from app.labtools.ui.western_blot_widgets import LabToolsWesternBlotWidget
    from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


if QWidget is not None:

    class LabToolsModulePlaceholderPage(QWidget):
        def __init__(
            self,
            title: str,
            description: str,
            planned_items: tuple[str, ...],
            current_mapping: tuple[str, ...] = (),
            status_text: str = "规划中 / 待确认使用逻辑 / 暂未开放",
        ) -> None:
            super().__init__()
            self.setObjectName("labToolsModulePlaceholderPage")
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["md"])

            title_label = QLabel(title)
            title_label.setObjectName("labToolsModuleTitle")
            title_label.setStyleSheet(f"color: {COLORS['bio']}; font-size: {FONT_SIZE['page_title']}px; font-weight: 760;")
            description_label = QLabel(description)
            description_label.setObjectName("labToolsModuleDescription")
            description_label.setWordWrap(True)
            status_label = QLabel(status_text)
            status_label.setObjectName("labToolsModulePlaceholderStatus")
            status_label.setWordWrap(True)
            status_label.setStyleSheet(
                f"color: {COLORS['text']}; background: {COLORS['surface']}; border: 1px solid {COLORS['border']}; border-radius: {RADIUS['sm']}px; padding: 8px 10px;"
            )

            root.addWidget(title_label)
            root.addWidget(description_label)
            root.addWidget(status_label)
            if current_mapping:
                mapping = QLabel("当前归类说明\n" + "\n".join(f"- {item}" for item in current_mapping))
                mapping.setObjectName("labToolsModuleMapping")
                mapping.setWordWrap(True)
                root.addWidget(mapping)
            planned = QLabel("后续候选能力\n" + "\n".join(f"- {item}" for item in planned_items))
            planned.setObjectName("labToolsModulePlannedItems")
            planned.setWordWrap(True)
            root.addWidget(planned)
            note = QLabel("本阶段只建立模块入口和占位语义，不新增算法、公式、图像处理、schema 或导出格式。")
            note.setObjectName("labToolsModuleBoundaryNote")
            note.setWordWrap(True)
            root.addWidget(note)
            root.addStretch(1)

    class LabToolsImageJConfigPage(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsImageJConfigPage")
            self.setStyleSheet(self._stylesheet())
            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["lg"])

            title = QLabel("ImageJ/Fiji 本地引擎配置")
            title.setObjectName("labToolsImageJConfigTitle")
            description = QLabel("用于图像 workflow 的本地 ImageJ/Fiji 检测、路径配置和验证状态查看。BioMedPilot 不会自动下载、联网安装或上传图片。")
            description.setObjectName("labToolsImageJConfigDescription")
            description.setWordWrap(True)
            boundary = QLabel("检测失败时可继续 manual-review workflow 准备；当前不启用 WB/gel 真实分析、自动 ROI、细胞计数、条带识别或生产级图像算法。")
            boundary.setObjectName("labToolsImageJConfigBoundary")
            boundary.setWordWrap(True)

            root.addWidget(title)
            root.addWidget(description)
            root.addWidget(boundary)
            root.addWidget(
                LabToolsImageJFijiStatusPanel(
                    workflow_name="LabTools 图像 workflow 配置中心",
                    can_continue_without_engine=True,
                )
            )
            root.addStretch(1)

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsImageJConfigPage {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QLabel#labToolsImageJConfigTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 760;
            }}
            QLabel#labToolsImageJConfigDescription {{
                color: {COLORS["muted"]};
            }}
            QLabel#labToolsImageJConfigBoundary {{
                color: {COLORS["text"]};
                background: #FFF4F2;
                border: 1px solid #F3B4AA;
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            """

    class LabToolsWesternBlotScaffoldPage(QWidget):
        SECTION_STATUS = "待确认使用逻辑 / 规划中 / 暂未开放"

        def __init__(self) -> None:
            super().__init__()
            self.setObjectName("labToolsWesternBlotScaffoldPage")
            root = QVBoxLayout(self)
            root.setContentsMargins(0, 0, 0, 0)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setObjectName("labToolsWesternBlotScroll")
            content = QWidget()
            content.setObjectName("labToolsWesternBlotContent")
            content.setStyleSheet(self._stylesheet())
            layout = QVBoxLayout(content)
            layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            layout.setSpacing(SPACING["lg"])

            title = QLabel("Western Blot")
            title.setObjectName("labToolsWesternBlotTitle")
            description = QLabel("用于蛋白样品准备、蛋白浓度测定入口、上样体系、SDS-PAGE 配胶、电泳/转膜参数、抗体孵育流程和后续灰度分析。")
            description.setObjectName("labToolsWesternBlotDescription")
            description.setWordWrap(True)
            boundary = QLabel("本阶段只建立 Western Blot 模块入口和占位分区；不新增算法、公式、图像处理、schema 或导出格式。")
            boundary.setObjectName("labToolsWesternBlotBoundary")
            boundary.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(description)
            layout.addWidget(boundary)

            grid = QGridLayout()
            grid.setSpacing(SPACING["md"])
            sections = (
                (
                    "蛋白样品准备",
                    "用于记录蛋白提取、裂解液/抑制剂草稿、样本分组和实验室自定义流程。当前为流程模板入口，不自动生成唯一实验方案。",
                    (),
                ),
                (
                    "蛋白浓度测定",
                    "提供 BCA、Bradford、NanoDrop 等蛋白浓度测定入口；底层逻辑后续与吸光度/标准曲线能力复用。",
                    (),
                ),
                (
                    "上样与胶",
                    "用于蛋白上样体系计算、loading buffer、还原剂、SDS-PAGE 配胶模板和批量配制计算。",
                    ("蛋白上样体系计算", "SDS-PAGE 配胶模板与批量配制"),
                ),
                (
                    "电泳 / 转膜 / 抗体孵育流程",
                    "用于记录电泳参数、电转参数、封闭、一抗、二抗和洗膜步骤模板。用户可录入试剂盒说明书或实验室成熟流程。",
                    (),
                ),
                (
                    "结果与灰度分析",
                    "用于后续 WB/gel grayscale、条带 ROI、背景扣除、target/loading control ratio 和结果导出。开发前需单独确认图像分析逻辑。",
                    (),
                ),
            )
            for index, (section_title, section_description, planned_entries) in enumerate(sections):
                grid.addWidget(
                    self._section_card(section_title, section_description, planned_entries),
                    index // 2,
                    index % 2,
                )
            layout.addLayout(grid)
            layout.addStretch(1)
            scroll.setWidget(content)
            root.addWidget(scroll)

        def _section_card(self, title: str, description: str, planned_entries: tuple[str, ...]) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsWesternBlotSectionCard")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])

            status = QLabel(self.SECTION_STATUS)
            status.setObjectName("labToolsWesternBlotSectionStatus")
            section_title = QLabel(title)
            section_title.setObjectName("labToolsWesternBlotSectionTitle")
            section_description = QLabel(description)
            section_description.setObjectName("labToolsWesternBlotSectionDescription")
            section_description.setWordWrap(True)
            layout.addWidget(status)
            layout.addWidget(section_title)
            layout.addWidget(section_description)
            if planned_entries:
                planned_label = QLabel("planned 子入口\n" + "\n".join(f"- {entry}: {self.SECTION_STATUS}" for entry in planned_entries))
                planned_label.setObjectName("labToolsWesternBlotPlannedEntries")
                planned_label.setWordWrap(True)
                layout.addWidget(planned_label)
            layout.addStretch(1)
            return frame

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsWesternBlotContent {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
            }}
            QScrollArea#labToolsWesternBlotScroll {{
                border: 0;
                background: {COLORS["background"]};
            }}
            QLabel#labToolsWesternBlotTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 780;
            }}
            QLabel#labToolsWesternBlotDescription {{
                color: {COLORS["muted"]};
            }}
            QLabel#labToolsWesternBlotBoundary {{
                color: {COLORS["text"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            QFrame#labToolsWesternBlotSectionCard {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["md"]}px;
                min-height: 190px;
            }}
            QLabel#labToolsWesternBlotSectionStatus {{
                color: #0E6F66;
                background: #E7F7F5;
                border: 1px solid #BCE7E2;
                border-radius: {RADIUS["sm"]}px;
                padding: 4px 8px;
                font-weight: 700;
            }}
            QLabel#labToolsWesternBlotSectionTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["card_title"]}px;
                font-weight: 760;
            }}
            QLabel#labToolsWesternBlotSectionDescription, QLabel#labToolsWesternBlotPlannedEntries {{
                color: {COLORS["muted"]};
            }}
            """

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
            if current is self._general_calculator_page:
                return "general_calculators"
            if current is self._imagej_fiji_page:
                return "imagej_fiji"
            if current is self._reagent_records_page:
                return "reagent_records"
            if current is self._cell_experiments_page:
                return "cell_experiments"
            if current is self._western_blot_page:
                return "western_blot"
            if current is self._pcr_qpcr_page:
                return "pcr_qpcr"
            if current is self._elisa_absorbance_page:
                return "elisa_absorbance"
            return "unknown"

        def show_home(self) -> None:
            self._stack.setCurrentWidget(self._home_page)

        def show_general_calculators(self) -> None:
            self._stack.setCurrentWidget(self._general_calculator_page)

        def show_imagej_fiji(self) -> None:
            self._stack.setCurrentWidget(self._imagej_fiji_page)

        def show_reagent_records(self) -> None:
            self._stack.setCurrentWidget(self._reagent_records_page)

        def show_cell_experiments(self) -> None:
            self._stack.setCurrentWidget(self._cell_experiments_page)

        def show_western_blot(self) -> None:
            self._stack.setCurrentWidget(self._western_blot_page)

        def show_pcr_qpcr(self) -> None:
            self._stack.setCurrentWidget(self._pcr_qpcr_page)

        def show_elisa_absorbance(self) -> None:
            self._stack.setCurrentWidget(self._elisa_absorbance_page)

        # Backward-compatible route names for existing internal callers.
        def show_calculators(self) -> None:
            self.show_general_calculators()

        def show_recipes(self) -> None:
            self.show_reagent_records()

        def show_image_analysis(self) -> None:
            self.show_imagej_fiji()

        def show_templates(self) -> None:
            self.show_reagent_records()

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
            self._home_page.general_calculators_requested.connect(self.show_general_calculators)
            self._home_page.reagent_records_requested.connect(self.show_reagent_records)
            self._home_page.imagej_fiji_requested.connect(self.show_imagej_fiji)
            self._home_page.cell_experiments_requested.connect(self.show_cell_experiments)
            self._home_page.western_blot_requested.connect(self.show_western_blot)
            self._home_page.pcr_qpcr_requested.connect(self.show_pcr_qpcr)
            self._home_page.elisa_absorbance_requested.connect(self.show_elisa_absorbance)
            self._general_calculator_page = LabToolsCalculatorWidget()
            self._imagej_fiji_page = LabToolsImageJConfigPage()
            self._reagent_records_page = LabToolsModulePlaceholderPage(
                "试剂与实验记录",
                "用于本地 recipe 草稿、实验记录草稿、模板保存和 JSON 导入导出；不等同于完整 ELN。",
                (
                    "recipe draft store 与 recipe import/export 现有能力后续归入本模块。",
                    "experiment template draft 与 experiment record draft JSON persistence 后续归入本模块。",
                    "完整 ELN、权限、签名、审计合规仍为未开放能力。",
                ),
                (
                    "recipe draft、experiment record draft 当前仍保留在既有实现中；本阶段只调整顶层入口语义。",
                ),
                status_text="已开放能力待重新归类 / 待确认使用逻辑",
            )
            self._cell_experiments_page = LabToolsModulePlaceholderPage(
                "细胞实验",
                "用于细胞接种、活率、Transwell、wound healing、增殖率、台盼蓝、Alamar Blue 等细胞实验工具。",
                (
                    "cell seeding 现有计算器未来归入本模块。",
                    "wound manual ROI + threshold 未来归入本模块，当前仍是 manual-review 辅助估算。",
                    "活率、Transwell、增殖率、台盼蓝、Alamar Blue 均待确认使用逻辑。",
                ),
            )
            self._western_blot_page = LabToolsWesternBlotWidget()
            self._pcr_qpcr_page = LabToolsModulePlaceholderPage(
                "PCR / qPCR",
                "用于 PCR/qPCR 体系计算、运行参数、plate layout、Ct / ΔCt / ΔΔCt 结果分析。",
                (
                    "qPCR mix 现有计算器未来归入本模块。",
                    "PCR/qPCR 运行参数、plate layout、Ct / ΔCt / ΔΔCt 分析待确认使用逻辑。",
                    "Delta Delta Ct 结果分析暂未开放。",
                ),
            )
            self._elisa_absorbance_page = LabToolsModulePlaceholderPage(
                "ELISA / 吸光度与标准曲线",
                "用于 OD 值、标准曲线、BCA、Bradford、NanoDrop、ELISA 样本浓度反推等。",
                (
                    "OD 值、标准曲线、BCA、Bradford、NanoDrop、ELISA 样本浓度反推均为 planned tools。",
                    "本模块暂未开放，必须先做 Tool Logic Card。",
                ),
            )
            for key, page in (
                ("home", self._home_page),
                ("general_calculators", self._general_calculator_page),
                ("imagej_fiji", self._imagej_fiji_page),
                ("reagent_records", self._reagent_records_page),
                ("cell_experiments", self._cell_experiments_page),
                ("western_blot", self._western_blot_page),
                ("pcr_qpcr", self._pcr_qpcr_page),
                ("elisa_absorbance", self._elisa_absorbance_page),
            ):
                self._page_keys.append(key)
                self._stack.addWidget(page)
            self._stack.setCurrentWidget(self._home_page)
            root.addWidget(self._stack, 1)

else:  # pragma: no cover

    class LabToolsWorkspaceWidget:  # type: ignore[no-redef]
        def page_keys(self) -> tuple[str, ...]:
            return ("home", "general_calculators", "imagej_fiji", "reagent_records", "cell_experiments", "western_blot", "pcr_qpcr", "elisa_absorbance")
