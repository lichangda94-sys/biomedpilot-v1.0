from __future__ import annotations

from collections.abc import Callable

from app.labtools.labtools_tool_registry import labtools_primary_entries
from app.shared.feature_status import FeatureItem, FeatureStatus


def labtools_features() -> list[FeatureItem]:
    legacy_image_boundary = FeatureItem(
        "labtools",
        "图像能力边界",
        FeatureStatus.TESTING,
        "消费 shared ImageJ/Fiji 本机引擎检测；manual-review 准备为 testing，未启用 WB/gel、agarose、自动 ROI、细胞计数或生产级真实图像算法。",
    )
    c1_module_entries = [
        FeatureItem(
            "labtools",
            entry.title,
            FeatureStatus.TESTING if entry.tool_id == "experiment_modules" else FeatureStatus.UNAVAILABLE,
            f"{entry.description} {' / '.join(entry.details)}",
        )
        for entry in labtools_primary_entries()
    ]
    return [legacy_image_boundary, *c1_module_entries]


try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

    from app.app_identity import load_labtools_pixmap
    from app.labtools.labtools_home import LabToolsHomeWidget
    from app.labtools.labtools_tool_registry import (
        LabToolsPrimaryEntry,
        LabToolsSecondaryEntry,
        get_labtools_primary_entry,
        get_labtools_secondary_by_page,
        get_labtools_secondary_entry,
        labtools_secondary_entries,
    )
    from app.labtools.ui.calculator_widgets import LabToolsCalculatorWidget, ReagentPreparationWorkflowWidget
    from app.labtools.ui.cell_experiment_widgets import LabToolsCellExperimentPage
    from app.labtools.ui.western_blot_widgets import LabToolsWesternBlotWidget
    from app.ui_style_tokens import COLORS, FONT_SIZE, RADIUS, SPACING, button_stylesheet, status_chip_stylesheet
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
            for key, page in self._route_pages.items():
                if current is page:
                    return key
            return "unknown"

        def current_page_widget(self) -> QWidget:
            return self._stack.currentWidget()

        def show_home(self) -> None:
            self._show_page("home")

        def show_primary(self, tool_id: str) -> None:
            entry = get_labtools_primary_entry(tool_id)
            self._show_page(entry.page_key)

        def show_secondary(self, tool_id: str) -> None:
            entry = get_labtools_secondary_entry(tool_id)
            self._show_page(entry.page_key)

        def show_general_calculator(self) -> None:
            self._show_page("general_calculators")

        def show_general_calculators(self) -> None:
            self.show_general_calculator()

        def show_reagent_preparation(self) -> None:
            self._show_page("reagent_preparation")

        def show_experiment_modules(self) -> None:
            self._show_page("experiment_modules")

        def show_western_blot(self) -> None:
            self._show_page("protein_experiments")

        def show_protein_experiments(self) -> None:
            self._show_page("protein_experiments")

        def show_cell_info(self) -> None:
            self._show_page("cell_experiments")

        def show_cell_experiments(self) -> None:
            self._show_page("cell_experiments")

        def _show_page(self, key: str) -> None:
            self._stack.setCurrentWidget(self._route_pages[key])
            self.setProperty("pageKey", key)
            page = self._route_pages[key]
            self.setProperty("semanticKey", page.property("semanticKey"))

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
            home.setObjectName("labToolsHomeButton")
            home.setStyleSheet(button_stylesheet("secondary"))
            home.clicked.connect(self.show_home)
            header_layout.addWidget(home)
            if self._on_back is not None:
                back = QPushButton("返回模块首页")
                back.setObjectName("labToolsBackToDashboardButton")
                back.setStyleSheet(button_stylesheet("secondary"))
                back.clicked.connect(self._on_back)
                header_layout.addWidget(back)
            root.addWidget(header)

            self._stack = QStackedWidget()
            self._home_page = LabToolsHomeWidget()
            self._home_page.primary_requested.connect(self.show_primary)
            self._route_pages = {
                "home": self._home_page,
                "general_calculators": self._connected_page(
                    get_labtools_primary_entry("general_calculators"),
                    LabToolsCalculatorWidget(),
                ),
                "reagent_preparation": self._connected_page(
                    get_labtools_primary_entry("reagent_preparation"),
                    ReagentPreparationWorkflowWidget(),
                ),
                "experiment_modules": self._experiment_modules_page(),
                "cell_experiments": self._connected_page(
                    get_labtools_secondary_by_page("cell_experiments"),
                    LabToolsCellExperimentPage(),
                ),
                "protein_experiments": self._connected_page(
                    get_labtools_secondary_by_page("protein_experiments"),
                    LabToolsWesternBlotWidget(),
                ),
                "nucleic_acid_experiments": self._secondary_placeholder_page(
                    get_labtools_secondary_by_page("nucleic_acid_experiments")
                ),
                "immuno_absorbance": self._secondary_placeholder_page(get_labtools_secondary_by_page("immuno_absorbance")),
                "ihc": self._secondary_placeholder_page(get_labtools_secondary_by_page("ihc")),
            }
            for page in self._route_pages.values():
                self._annotate_button_contracts(page)
            for key, page in self._route_pages.items():
                self._page_keys.append(key)
                self._stack.addWidget(page)
            self._stack.setCurrentWidget(self._home_page)
            self.setProperty("pageKey", "home")
            self.setProperty("semanticKey", self._home_page.property("semanticKey"))
            root.addWidget(self._stack, 1)

        def _primary_placeholder_page(self, entry: LabToolsPrimaryEntry) -> QWidget:
            page = QWidget()
            page.setObjectName("labToolsC1PlaceholderPage")
            page.setProperty("pageKey", entry.page_key)
            page.setProperty("semanticKey", entry.semantic_key)
            page.setProperty("toolId", entry.tool_id)
            page.setStyleSheet(self._placeholder_stylesheet())

            layout = QVBoxLayout(page)
            layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            layout.setSpacing(SPACING["md"])

            status = QLabel(entry.status)
            status.setObjectName("uiStatusChip")
            status.setProperty("statusKey", entry.status_key)
            status.setStyleSheet(status_chip_stylesheet(entry.status_key))
            title = QLabel(entry.title)
            title.setObjectName("labToolsC1Title")
            subtitle = QLabel(entry.english_title)
            subtitle.setObjectName("labToolsC1Subtitle")
            description = QLabel(entry.description)
            description.setObjectName("labToolsC1Description")
            description.setWordWrap(True)
            details = QLabel("\n".join(f"- {item}" for item in entry.details))
            details.setObjectName("labToolsC1Description")
            details.setWordWrap(True)
            provenance = QLabel("恢复来源：" + " / ".join(entry.source_commits))
            provenance.setObjectName("labToolsC1Provenance")

            layout.addWidget(status, alignment=Qt.AlignLeft)
            layout.addWidget(title)
            layout.addWidget(subtitle)
            layout.addWidget(description)
            layout.addWidget(details)
            layout.addWidget(provenance)
            layout.addStretch(1)
            return page

        def _connected_page(self, entry: LabToolsPrimaryEntry | LabToolsSecondaryEntry, widget: QWidget) -> QWidget:
            widget.setProperty("pageKey", entry.page_key)
            widget.setProperty("semanticKey", entry.semantic_key)
            widget.setProperty("toolId", entry.tool_id)
            widget.setProperty("sourceCommits", " / ".join(entry.source_commits))
            widget.setProperty("connectionStatus", "connected")
            return widget

        def _experiment_modules_page(self) -> QWidget:
            page = QWidget()
            page.setObjectName("labToolsExperimentModulesPage")
            page.setProperty("pageKey", "experiment_modules")
            page.setProperty("semanticKey", "labtools.page.experiment_modules")
            page.setStyleSheet(self._placeholder_stylesheet())

            layout = QVBoxLayout(page)
            layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            layout.setSpacing(SPACING["lg"])
            title = QLabel("实验模块 / Experiment Modules")
            title.setObjectName("labToolsC1Title")
            description = QLabel("按 Figma 分类恢复二级实验模块：细胞实验、蛋白实验、核酸实验、免疫与吸光度实验、免疫组化。")
            description.setObjectName("labToolsC1Description")
            description.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(description)

            grid = QGridLayout()
            grid.setSpacing(SPACING["md"])
            for index, entry in enumerate(labtools_secondary_entries()):
                grid.addWidget(self._secondary_card(entry), index // 3, index % 3)
            layout.addLayout(grid)
            layout.addStretch(1)
            return page

        def _secondary_card(self, entry: LabToolsSecondaryEntry) -> QFrame:
            frame = QFrame()
            frame.setObjectName(entry.object_name)
            frame.setProperty("pageKey", entry.page_key)
            frame.setProperty("semanticKey", entry.semantic_key)
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
            layout.setSpacing(SPACING["sm"])
            chip = QLabel(entry.status)
            chip.setObjectName("uiStatusChip")
            chip.setProperty("statusKey", entry.status_key)
            chip.setStyleSheet(status_chip_stylesheet(entry.status_key))
            title = QLabel(entry.title)
            title.setObjectName("labtoolsSecondaryEntryTitle")
            title.setProperty("pageKey", entry.page_key)
            title.setProperty("semanticKey", entry.semantic_key)
            description = QLabel(entry.description)
            description.setObjectName("labtoolsSecondaryEntryDetail")
            description.setWordWrap(True)
            button = QPushButton(entry.button_text)
            button.setObjectName("labtoolsSecondaryEntryButton")
            button.setProperty("pageKey", entry.page_key)
            button.setProperty("semanticKey", entry.semantic_key)
            button.setProperty("disabledReason", entry.disabled_reason)
            button.setStyleSheet(button_stylesheet("secondary"))
            button.clicked.connect(lambda _checked=False, item=entry: self.show_secondary(item.tool_id))
            icon = QLabel()
            icon.setObjectName("labtoolsSecondaryEntryIcon")
            pixmap = load_labtools_pixmap(entry.semantic_key, 36)
            if not pixmap.isNull():
                icon.setPixmap(pixmap)
                icon.setFixedSize(40, 40)
            layout.addWidget(icon, alignment=Qt.AlignLeft)
            layout.addWidget(chip, alignment=Qt.AlignLeft)
            layout.addWidget(title)
            layout.addWidget(description)
            layout.addStretch(1)
            layout.addWidget(button)
            return frame

        def _secondary_placeholder_page(self, entry: LabToolsSecondaryEntry) -> QWidget:
            page = QWidget()
            page.setObjectName("labToolsC1PlaceholderPage")
            page.setProperty("pageKey", entry.page_key)
            page.setProperty("semanticKey", entry.semantic_key)
            page.setProperty("toolId", entry.tool_id)
            page.setProperty("disabledReason", entry.disabled_reason)
            page.setStyleSheet(self._placeholder_stylesheet())

            layout = QVBoxLayout(page)
            layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
            layout.setSpacing(SPACING["md"])

            status = QLabel(entry.status)
            status.setObjectName("labToolsC1Status")
            status.setProperty("statusKey", entry.status_key)
            status.setStyleSheet(status_chip_stylesheet(entry.status_key))
            title = QLabel(entry.title)
            title.setObjectName("labToolsC1Title")
            subtitle = QLabel(entry.english_title)
            subtitle.setObjectName("labToolsC1Subtitle")
            description = QLabel(entry.description)
            description.setObjectName("labToolsC1Description")
            description.setWordWrap(True)
            reason = QLabel(f"Disabled reason: {entry.disabled_reason}")
            reason.setObjectName("labToolsC1DisabledReason")
            reason.setWordWrap(True)
            provenance = QLabel("恢复来源：" + " / ".join(entry.source_commits))
            provenance.setObjectName("labToolsC1Provenance")
            provenance.setWordWrap(True)
            disabled_action = QPushButton("C2 接入后启用")
            disabled_action.setObjectName("labToolsC1DisabledActionButton")
            disabled_action.setEnabled(False)
            disabled_action.setProperty("disabledReason", entry.disabled_reason)
            disabled_action.setToolTip(entry.disabled_reason)
            disabled_action.setAccessibleDescription(entry.disabled_reason)

            layout.addWidget(status, alignment=Qt.AlignLeft)
            layout.addWidget(title)
            layout.addWidget(subtitle)
            layout.addWidget(description)
            layout.addWidget(reason)
            layout.addWidget(provenance)
            layout.addWidget(disabled_action)
            layout.addStretch(1)
            return page

        def _placeholder_stylesheet(self) -> str:
            return f"""
            QWidget#labToolsC1PlaceholderPage, QWidget#labToolsExperimentModulesPage {{
                background: {COLORS["background"]};
                color: {COLORS["text"]};
                font-size: {FONT_SIZE["body"]}px;
            }}
            QFrame#labToolsCellExperimentsSecondaryEntry,
            QFrame#labToolsProteinExperimentsSecondaryEntry,
            QFrame#labToolsNucleicAcidExperimentsSecondaryEntry,
            QFrame#labToolsImmunoAbsorbanceSecondaryEntry,
            QFrame#labToolsIhcSecondaryEntry {{
                background: {COLORS["surface"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["md"]}px;
                min-height: 180px;
            }}
            QLabel#labToolsC1Title {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["page_title"]}px;
                font-weight: 780;
            }}
            QLabel#labToolsC1Subtitle,
            QLabel#labToolsC1Description,
            QLabel#labToolsC1Provenance,
            QLabel#labtoolsSecondaryEntryDetail {{
                color: {COLORS["muted"]};
            }}
            QLabel#labtoolsSecondaryEntryTitle {{
                color: {COLORS["bio"]};
                font-size: {FONT_SIZE["card_title"]}px;
                font-weight: 760;
            }}
            QLabel#labToolsC1DisabledReason {{
                color: {COLORS["text_secondary"]};
                background: {COLORS["warning_soft"]};
                border: 1px solid {COLORS["warning_border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 9px 11px;
            }}
            QPushButton#labToolsC1DisabledActionButton:disabled {{
                color: {COLORS["muted"]};
                background: {COLORS["surface_muted"]};
                border: 1px solid {COLORS["border"]};
                border-radius: {RADIUS["sm"]}px;
                padding: 8px 12px;
            }}
            """

        def _annotate_button_contracts(self, page: QWidget) -> None:
            for button in page.findChildren(QPushButton):
                if button.property("buttonBehavior") is None:
                    button.setProperty("buttonBehavior", self._button_behavior(button))
                if not button.isEnabled() and button.property("disabledReason") is None:
                    reason = self._button_disabled_reason(button)
                    button.setProperty("disabledReason", reason)
                    button.setToolTip(reason)
                    button.setAccessibleDescription(reason)

        def _button_behavior(self, button: QPushButton) -> str:
            name = button.objectName()
            text = button.text()
            page_key = str(button.property("pageKey") or "")
            if name == "labtoolsEntryButton":
                return f"navigates_to_labtools_primary_{page_key}"
            if name == "labtoolsSecondaryEntryButton":
                return f"navigates_to_labtools_secondary_{page_key}"
            if name == "quickAccessButton":
                return "disabled_labtools_quick_access_placeholder"
            if name == "labToolsC1DisabledActionButton":
                return "disabled_labtools_secondary_backend_not_connected"
            if name.startswith("cellExperimentDisabledRecordButton_"):
                return "disabled_figma_summary_record_card_uses_backend_record_tabs"
            if name == "cellExperimentSeedingHelperButton":
                return "scrolls_to_cell_seeding_backend_calculator"
            if name == "cellExperimentCreateFromLastDisabledButton":
                return "disabled_requires_saved_cell_record_history"
            if name == "cellExperimentSettingsRouteDisabledButton":
                return "disabled_settings_route_available_from_shell_sidebar"
            if name == "cellExperimentRunImageAnalysisDisabledButton":
                return "disabled_image_engine_execution_gated_creates_run_request_only"
            if name.startswith("wbRecordSaveButton_"):
                return "saves_western_blot_workflow_record"
            if name.startswith("wbRecordSaveSopTemplateButton_"):
                return "saves_western_blot_sop_template"
            if name.startswith("wbRecordLoadLastButton_"):
                return "loads_latest_western_blot_workflow_record"
            if name.startswith("wbRecordExportTextButton_"):
                return "exports_western_blot_workflow_record_text"
            if name.startswith("wbWorkflowStepButton_"):
                return "navigates_western_blot_workflow_step"
            explicit_by_name = {
                "refreshBlankLaneLayoutButton": "generates_blank_sds_page_lane_layout",
                "importLoadingLaneLayoutButton": "imports_wb_loading_lane_layout",
                "sdsPageTemplateJsonExportButton": "exports_sds_page_template_json_when_available",
                "sdsPageTemplateJsonImportButton": "imports_sds_page_template_json",
                "sdsPageXlsxExportButton": "exports_sds_page_calculation_xlsx_when_available",
                "proteinLoadingAddSampleRowButton": "adds_protein_loading_sample_row",
                "proteinLoadingCalculateButton": "calculates_protein_loading_plan",
                "proteinLoadingCopyResultButton": "copies_protein_loading_markdown_when_available",
                "wbLoadingSaveRecordButton": "saves_wb_loading_record_when_calculation_exists",
                "wbLoadingCopyMarkdownButton": "copies_wb_loading_markdown_when_available",
                "wbLoadingExportMarkdownButton": "exports_wb_loading_markdown_when_available",
                "wbLoadingExportCsvButton": "exports_wb_loading_csv_when_available",
                "wbLoadingViewRecordButton": "loads_selected_wb_loading_record",
                "wbLoadingDeleteRecordButton": "deletes_selected_wb_loading_record",
                "wbLoadingRefreshRecordHistoryButton": "refreshes_wb_loading_record_history",
                "bcaParseOdMatrixButton": "parses_bca_od_matrix",
                "bcaApplyBatchAnnotationButton": "applies_bca_batch_well_annotation",
                "bcaApplySelectedAnnotationButton": "applies_bca_selected_well_annotation",
                "bcaSetBlankButton": "sets_bca_selected_wells_blank",
                "bcaSetStandardButton": "sets_bca_selected_wells_standard",
                "bcaSetSampleButton": "sets_bca_selected_wells_sample",
                "bcaSetUnusedButton": "sets_bca_selected_wells_unused",
                "bcaCalculateButton": "calculates_bca_standard_curve_and_samples",
                "bcaCopyResultButton": "copies_bca_result_when_available",
                "openBcaAssayToolButton": "navigates_to_bca_assay_tool",
                "openProteinLoadingToolButton": "navigates_to_protein_loading_tool",
                "openSdsPageGelToolButton": "navigates_to_sds_page_gel_tool",
            }
            if name in explicit_by_name:
                return explicit_by_name[name]
            explicit_by_text = {
                "计算配制用量": "calls_solution_preparation_calculator",
                "计算稀释体积": "calls_dilution_calculator",
                "换算浓度": "calls_concentration_unit_conversion",
                "计算摩尔浓度": "calls_molar_concentration_calculator",
                "计算称量质量": "calls_molar_mass_weighing_calculator",
                "复制结果": "copies_latest_calculation_result_when_available",
                "计算批量用量": "calls_sds_page_gel_batch_calculator",
            }
            return explicit_by_text.get(text, f"labtools_connected_action_{name}")

        def _button_disabled_reason(self, button: QPushButton) -> str:
            name = button.objectName()
            text = button.text()
            if name == "quickAccessButton":
                return "LabTools quick access center is planned for UI-SHELL-CENTERS-C1."
            if name.startswith("cellExperimentDisabledRecordButton_"):
                return "This visual Figma summary card is not the write path; use the Cell Experiment Record tabs below for connected save/export actions."
            if name == "cellExperimentCreateFromLastDisabledButton":
                return "Requires saved cell experiment history; connected from-last actions are available in backend record tabs once records exist."
            if name == "cellExperimentSettingsRouteDisabledButton":
                return "Settings is reachable from the shell sidebar; this LabTools summary-card shortcut is intentionally not wired."
            if name == "cellExperimentRunImageAnalysisDisabledButton":
                return "Cell image analysis execution is gated; current workbenches generate run request artifacts but do not run ImageJ/Fiji macros."
            if text == "复制结果":
                return "Requires a successful calculation result on the current calculator tab."
            if name in {
                "sdsPageTemplateJsonExportButton",
                "sdsPageXlsxExportButton",
                "proteinLoadingCopyResultButton",
                "wbLoadingSaveRecordButton",
                "wbLoadingCopyMarkdownButton",
                "wbLoadingExportMarkdownButton",
                "wbLoadingExportCsvButton",
                "bcaCopyResultButton",
            }:
                return "Requires a generated calculation or analysis result before export/copy/save is enabled."
            return "This LabTools action is intentionally disabled until the required upstream state exists."

else:  # pragma: no cover

    class LabToolsWorkspaceWidget:  # type: ignore[no-redef]
        def page_keys(self) -> tuple[str, ...]:
            return (
                "home",
                "general_calculators",
                "reagent_preparation",
                "experiment_modules",
                "cell_experiments",
                "protein_experiments",
                "nucleic_acid_experiments",
                "immuno_absorbance",
                "ihc",
            )

        def current_page_key(self) -> str:
            return "home"
