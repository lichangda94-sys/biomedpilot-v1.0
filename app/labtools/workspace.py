from __future__ import annotations

from collections.abc import Callable

from app.labtools.labtools_tool_registry import LabToolsTool, labtools_tool_registry
from app.shared.feature_status import FeatureItem, FeatureStatus


def labtools_features() -> list[FeatureItem]:
    return [
        FeatureItem(
            "labtools",
            tool.chinese_name,
            FeatureStatus.TESTING if tool.is_available else FeatureStatus.UNAVAILABLE,
            f"{tool.description} {tool.boundary_statement}",
        )
        for tool in labtools_tool_registry()
    ]


try:
    from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QStackedWidget, QTabWidget, QVBoxLayout, QWidget

    from app.labtools.labtools_home import LabToolsHomeWidget
    from app.labtools.ui.calculator_widgets import LabToolsCalculatorWidget
    from app.labtools.ui.cell_experiment_widgets import LabToolsCellExperimentPage as CellExperimentPageWidget
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

            title = QLabel("ImageJ 本地引擎配置")
            title.setObjectName("labToolsImageJConfigTitle")
            description = QLabel("用于图像 workflow 的本地 ImageJ 检测、路径配置和验证状态查看；可选保留 Fiji 增强路径。BioMedPilot 不会自动下载、联网安装或上传图片。")
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

    class LabToolsPlannedToolDetailPage(QWidget):
        def __init__(self, tool: LabToolsTool) -> None:
            super().__init__()
            self._tool = tool
            self.setObjectName("labToolsPlannedToolDetailPage")
            self.setStyleSheet(self._stylesheet())

            root = QVBoxLayout(self)
            root.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            root.setSpacing(SPACING["lg"])

            title = QLabel(tool.chinese_name)
            title.setObjectName("labToolsPlannedToolTitle")
            subtitle = QLabel(f"{tool.english_name} / {tool.category}")
            subtitle.setObjectName("labToolsPlannedToolSubtitle")
            status = QLabel(f"当前状态：{tool.status}")
            status.setObjectName("labToolsPlannedToolStatus")
            description = QLabel(tool.description)
            description.setObjectName("labToolsPlannedToolDescription")
            description.setWordWrap(True)
            boundary = QLabel(f"边界声明：{tool.boundary_statement}")
            boundary.setObjectName("labToolsPlannedToolBoundary")
            boundary.setWordWrap(True)

            root.addWidget(title)
            root.addWidget(subtitle)
            root.addWidget(status)
            root.addWidget(description)
            root.addWidget(self._section("可做内容：未来将支持什么", tool.future_capabilities))
            root.addWidget(self._section("当前不可做内容", tool.unavailable_capabilities))
            root.addWidget(boundary)
            logic_card = QLabel("后续开发前需要 Tool Logic Card：需先明确输入、输出、公式/算法来源、人工复核点、失败状态、测试夹具和 UI 边界。")
            logic_card.setObjectName("labToolsPlannedToolLogicCard")
            logic_card.setWordWrap(True)
            root.addWidget(logic_card)
            if tool.requires_imagej_fiji:
                imagej_note = QLabel("本工具后续图像 workflow 可能读取 ImageJ 本地引擎状态；Fiji 仅用于后续插件型 macro。当前不会运行真实图像分析。")
                imagej_note.setObjectName("labToolsPlannedToolImageJNote")
                imagej_note.setWordWrap(True)
                root.addWidget(imagej_note)
            root.addStretch(1)

        def _section(self, title: str, rows: tuple[str, ...]) -> QFrame:
            frame = QFrame()
            frame.setObjectName("labToolsPlannedToolSection")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])
            heading = QLabel(title)
            heading.setObjectName("labToolsPlannedToolSectionTitle")
            body = QLabel("\n".join(f"- {row}" for row in rows) if rows else "- 暂未登记")
            body.setObjectName("labToolsPlannedToolSectionBody")
            body.setWordWrap(True)
            layout.addWidget(heading)
            layout.addWidget(body)
            return frame

        def _stylesheet(self) -> str:
            return f"""
            QWidget#labToolsPlannedToolDetailPage {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QLabel#labToolsPlannedToolTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 760;
            }}
            QLabel#labToolsPlannedToolSubtitle, QLabel#labToolsPlannedToolDescription {{
                color: {COLORS["muted"]};
            }}
            QLabel#labToolsPlannedToolStatus {{
                color: #0E6F66;
                background: #E7F7F5;
                border: 1px solid #BCE7E2;
                border-radius: {RADIUS["sm"]}px;
                padding: 6px 10px;
                font-weight: 700;
            }}
            QFrame#labToolsPlannedToolSection {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
            }}
            QLabel#labToolsPlannedToolSectionTitle {{
                color: {COLORS["bio"]};
                font-weight: 760;
            }}
            QLabel#labToolsPlannedToolSectionBody {{
                color: {COLORS["text"]};
            }}
            QLabel#labToolsPlannedToolBoundary {{
                color: {COLORS["text"]};
                background: #FFF4F2;
                border: 1px solid #F3B4AA;
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            QLabel#labToolsPlannedToolLogicCard, QLabel#labToolsPlannedToolImageJNote {{
                color: {COLORS["text"]};
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 10px;
            }}
            """

    class LabToolsCellExperimentPage(CellExperimentPageWidget):
        pass

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
            self._annotate_disabled_buttons()

        def page_keys(self) -> tuple[str, ...]:
            return tuple(self._page_keys)

        def _annotate_disabled_buttons(self) -> None:
            for button in self.findChildren(QPushButton):
                if button.isEnabled() or button.property("disabledReason") or button.toolTip():
                    continue
                text = button.text().lower()
                reason = "labtools_action_disabled_until_required_input_or_result_exists"
                if "export" in text or "导出" in text:
                    reason = "labtools_export_disabled_until_result_artifact_exists"
                elif "save" in text or "保存" in text:
                    reason = "labtools_save_disabled_until_project_storage_and_result_exist"
                elif "copy" in text or "复制" in text:
                    reason = "labtools_copy_disabled_until_calculation_result_exists"
                button.setProperty("disabledReason", reason)
                button.setToolTip(reason)
                button.setAccessibleDescription(reason)

        def current_page_key(self) -> str:
            current = self._stack.currentWidget()
            for key, page in self._route_pages.items():
                if current is page:
                    return key
            return "unknown"

        def show_home(self) -> None:
            self._show_page("home")

        def show_general_calculators(self) -> None:
            self._show_page("general_calculators")

        def show_imagej_fiji(self) -> None:
            self._show_page("imagej_fiji")

        def show_reagent_records(self) -> None:
            self._show_page("reagent_records")

        def show_cell_experiments(self) -> None:
            self._show_page("cell_experiments")

        def show_western_blot(self) -> None:
            self._show_page("western_blot")

        def show_pcr_qpcr(self) -> None:
            self._show_page("pcr_qpcr")

        def show_elisa_absorbance(self) -> None:
            self._show_page("elisa_absorbance")

        def show_tool(self, tool_id: str) -> None:
            for tool in labtools_tool_registry():
                if tool.tool_id == tool_id:
                    self._show_page(tool.entry_page)
                    return
            raise KeyError(f"Unknown LabTools tool_id: {tool_id}")

        def _show_page(self, key: str) -> None:
            self._stack.setCurrentWidget(self._route_pages[key])
            self.setProperty("pageKey", key)
            self.setProperty("semanticKey", self._semantic_key_for_route(key))

        def _semantic_key_for_route(self, key: str) -> str:
            from app.shared.semantic_keys import PageKey

            semantic_by_route = {
                "home": PageKey.LABTOOLS_HOME.value,
                "general_calculators": PageKey.LABTOOLS_GENERAL_CALCULATORS.value,
                "imagej_fiji": "labtools.page.imagej_fiji",
                "reagent_records": PageKey.LABTOOLS_REAGENT_PREPARATION.value,
                "cell_experiments": PageKey.LABTOOLS_CELL_EXPERIMENTS.value,
                "western_blot": PageKey.LABTOOLS_PROTEIN_EXPERIMENTS.value,
                "pcr_qpcr": PageKey.LABTOOLS_NUCLEIC_ACID_EXPERIMENTS.value,
                "elisa_absorbance": PageKey.LABTOOLS_IMMUNO_ABSORBANCE.value,
            }
            return semantic_by_route.get(key, PageKey.LABTOOLS_HOME.value)

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
            engine_settings = QPushButton("外部引擎设置")
            engine_settings.setObjectName("labToolsExternalEngineSettingsButton")
            engine_settings.clicked.connect(self.show_imagej_fiji)
            header_layout.addWidget(engine_settings)
            if self._on_back is not None:
                back = QPushButton("返回模块首页")
                back.clicked.connect(self._on_back)
                header_layout.addWidget(back)
            root.addWidget(header)

            self._stack = QStackedWidget()
            self._home_page = LabToolsHomeWidget()
            self._home_page.tool_requested.connect(self.show_tool)
            self._home_page.general_calculators_requested.connect(self.show_general_calculators)
            self._home_page.reagent_records_requested.connect(self.show_reagent_records)
            self._home_page.imagej_fiji_requested.connect(self.show_imagej_fiji)
            self._home_page.cell_experiments_requested.connect(self.show_cell_experiments)
            self._home_page.western_blot_requested.connect(self.show_western_blot)
            self._home_page.pcr_qpcr_requested.connect(self.show_pcr_qpcr)
            self._home_page.elisa_absorbance_requested.connect(self.show_elisa_absorbance)
            self._general_calculator_page = LabToolsCalculatorWidget()
            self._imagej_fiji_page = LabToolsImageJConfigPage()
            self._planned_tool_pages = {
                tool.entry_page: LabToolsPlannedToolDetailPage(tool)
                for tool in labtools_tool_registry()
                if tool.is_planned_only
            }
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
            self._cell_experiments_page = LabToolsCellExperimentPage()
            self._western_blot_page = LabToolsWesternBlotWidget()
            self._pcr_qpcr_page = self._planned_tool_pages["pcr_qpcr"]
            self._elisa_absorbance_page = self._planned_tool_pages["elisa_absorbance"]
            self._route_pages = {
                "home": self._home_page,
                "general_calculators": self._general_calculator_page,
                "imagej_fiji": self._imagej_fiji_page,
                "reagent_records": self._reagent_records_page,
                "cell_experiments": self._cell_experiments_page,
                "western_blot": self._western_blot_page,
                "pcr_qpcr": self._pcr_qpcr_page,
                "elisa_absorbance": self._elisa_absorbance_page,
            }
            for key, page in self._route_pages.items():
                self._page_keys.append(key)
                self._stack.addWidget(page)
            self._stack.setCurrentWidget(self._home_page)
            root.addWidget(self._stack, 1)

else:  # pragma: no cover

    class LabToolsWorkspaceWidget:  # type: ignore[no-redef]
        def page_keys(self) -> tuple[str, ...]:
            return ("home", "general_calculators", "imagej_fiji", "reagent_records", "cell_experiments", "western_blot", "pcr_qpcr", "elisa_absorbance")
