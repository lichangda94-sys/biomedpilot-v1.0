from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.shared.feature_availability import FeatureAvailability, FeatureAvailabilityStatus, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.version import APP_VERSION

from app.meta_analysis.project_workspace import MetaProjectSummary, open_meta_analysis_project
from app.meta_analysis.version import META_ANALYSIS_MAINLINE_CONTRACT_VERSION
from app.shared.ui import (
    BioMedPilotColors,
    BioMedPilotSpacing,
    button_qss,
    card_title_qss,
    diagnostic_card_qss,
    helper_text_qss,
    page_title_qss,
    section_card_qss,
    status_badge_qss,
)

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
except Exception:  # pragma: no cover
    QWidget = None  # type: ignore[assignment]


def meta_analysis_features() -> list[FeatureItem]:
    return [feature_item_from_availability(feature) for feature in meta_analysis_step_features()]


def meta_analysis_step_features() -> list[FeatureAvailability]:
    features = list_features("meta_analysis")
    if features:
        return features
    return [
        FeatureAvailability(
            "meta_analysis",
            "meta-mainline-shell",
            "Meta 分析入口",
            FeatureAvailabilityStatus.TESTING,
            "主线保留 Meta 模块入口、项目绑定和占位工作台；完整流程在 Meta 开发线验收后接入。",
            "在 Meta 开发线完成验收后再合入具体功能。",
            "app/meta_analysis/workspace.py",
        )
    ]


@dataclass(frozen=True)
class MetaWorkspaceNavigationItem:
    step_id: str
    label: str
    description: str
    page_key: str
    status_label: str = "Mainline shell"
    status_label_zh: str = "主线壳"


@dataclass(frozen=True)
class MetaWorkspaceLayoutState:
    title: str
    status_label: str
    description: str
    navigation_items: tuple[MetaWorkspaceNavigationItem, ...]
    default_page_key: str
    testing_notice: str
    version_status_label: str = ""
    entry_title: str = "Meta 分析模块"
    developer_info_label: str = "开发者信息"


def meta_workspace_layout_state() -> MetaWorkspaceLayoutState:
    version_status = f"{APP_VERSION} · {META_ANALYSIS_MAINLINE_CONTRACT_VERSION}"
    return MetaWorkspaceLayoutState(
        title="Meta 分析模块",
        status_label=version_status,
        description="主线保留 Meta 入口和项目壳；具体 PICO、检索、筛选、提取、统计和报告功能在 Meta 开发线验收后接入。",
        navigation_items=(
            MetaWorkspaceNavigationItem("project_home", "Meta 项目首页", "项目绑定、状态摘要和分支边界说明。", "workflow_home"),
            MetaWorkspaceNavigationItem("project_contract", "项目契约", "创建和打开 Meta 项目的最小项目结构契约。", "project_contract"),
            MetaWorkspaceNavigationItem("dev_branch", "功能开发线", "完整 Meta workflow 在独立开发线验收后接入。", "dev_branch"),
        ),
        default_page_key="workflow_home",
        testing_notice="当前主线只保留 Meta 模块入口和接口；完整功能需在独立开发线完成验收后接入。",
        version_status_label=version_status,
    )


def _meta_status_family(status: str) -> str:
    normalized = status.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized in {"active", "ready", "opened"}:
        return "ready"
    if normalized in {"confirmed", "completed"}:
        return normalized
    if normalized in {"error", "invalid", "blocked"}:
        return "error"
    return "draft"


def _meta_status_text(status: str) -> str:
    normalized = status.strip().lower().replace("-", "_").replace(" ", "_")
    return {
        "active": "已就绪",
        "ready": "已就绪",
        "opened": "已就绪",
        "confirmed": "已确认",
        "completed": "已完成",
        "error": "错误",
        "invalid": "错误",
        "blocked": "受阻",
        "created": "草稿",
        "draft": "草稿",
    }.get(normalized, "草稿")


if QWidget is not None:

    class MetaAnalysisWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("metaAnalysisWorkspace")
            self._on_back = on_back
            self._current_project_dir: Path | None = None
            self._current_meta_project: MetaProjectSummary | None = None
            self._layout_state = meta_workspace_layout_state()
            self._page_keys: list[str] = []
            self._build_ui()

        def page_keys(self) -> tuple[str, ...]:
            return tuple(self._page_keys)

        def current_page_key(self) -> str:
            row = self._navigation_list.currentRow()
            if row < 0 or row >= len(self._page_keys):
                return ""
            return self._page_keys[row]

        def current_project_dir(self) -> Path | None:
            return self._current_project_dir

        def set_project_record(self, record) -> None:
            self.set_project_dir(Path(record.project_dir))

        def set_project_dir(self, path: str | Path | None) -> None:
            self._current_project_dir = Path(path).expanduser().resolve() if path else None
            self._current_meta_project = None
            if self._current_project_dir is not None:
                validation = open_meta_analysis_project(self._current_project_dir)
                if validation.is_valid and validation.summary is not None:
                    self._current_meta_project = validation.summary
            self._refresh_summary()

        def open_meta_project_folder(self, path: str | Path) -> bool:
            validation = open_meta_analysis_project(path)
            if not validation.is_valid or validation.summary is None:
                self._status_label.setText("该文件夹不是有效 Meta 项目。")
                self._status_label.setStyleSheet(status_badge_qss("warning"))
                self._diagnostic_text.setText(
                    "\n".join(
                        [
                            f"selected_dir: {Path(path).expanduser().resolve()}",
                            "errors:",
                            *validation.errors,
                        ]
                    )
                )
                return False
            self._current_project_dir = validation.summary.project_root
            self._current_meta_project = validation.summary
            self._refresh_summary()
            return True

        def show_step(self, page_key: str) -> None:
            if page_key in self._page_keys:
                self._navigation_list.setCurrentRow(self._page_keys.index(page_key))

        def meta_workspace_layout_state(self) -> dict[str, object]:
            return {
                "workflow_nav": self._navigation_list.objectName(),
                "current_step_workspace": self._page_stack.objectName(),
                "page_keys": self.page_keys(),
                "current_page_key": self.current_page_key(),
                "project_dir": str(self._current_project_dir or ""),
                "contract_version": META_ANALYSIS_MAINLINE_CONTRACT_VERSION,
            }

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(18, 18, 18, 18)
            root.setSpacing(12)

            header = QFrame()
            header.setObjectName("metaMainlineHeader")
            header.setStyleSheet(section_card_qss("QFrame#metaMainlineHeader"))
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(16, 14, 16, 14)
            title_col = QVBoxLayout()
            title = QLabel("Meta 分析模块")
            title.setObjectName("metaWorkspaceTitle")
            title.setStyleSheet(page_title_qss())
            subtitle = QLabel("主线入口与项目壳；完整功能需在独立开发线完成验收后接入。")
            subtitle.setObjectName("metaWorkspaceSubtitle")
            subtitle.setStyleSheet(helper_text_qss())
            title_col.addWidget(title)
            title_col.addWidget(subtitle)
            header_layout.addLayout(title_col, 1)
            if self._on_back is not None:
                back = QPushButton("返回模块首页")
                back.setObjectName("metaBackButton")
                back.setProperty("buttonRole", "navigation_back")
                back.setStyleSheet(button_qss("navigation_back"))
                back.clicked.connect(self._on_back)
                header_layout.addWidget(back)
            root.addWidget(header)

            self._status_label = QLabel("")
            self._status_label.setObjectName("metaProjectStatus")
            root.addWidget(self._status_label)
            self._diagnostic_toggle_button = QPushButton("展开开发者诊断")
            self._diagnostic_toggle_button.setObjectName("metaDeveloperDiagnosticsToggle")
            self._diagnostic_toggle_button.setProperty("buttonRole", "secondary")
            self._diagnostic_toggle_button.setStyleSheet(button_qss("secondary"))
            self._diagnostic_toggle_button.clicked.connect(self._toggle_developer_diagnostics)
            root.addWidget(self._diagnostic_toggle_button)

            self._diagnostic_card = QFrame()
            self._diagnostic_card.setObjectName("metaDeveloperDiagnosticsCard")
            self._diagnostic_card.setStyleSheet(diagnostic_card_qss("QFrame#metaDeveloperDiagnosticsCard"))
            diagnostic_layout = QVBoxLayout(self._diagnostic_card)
            diagnostic_layout.setContentsMargins(14, 12, 14, 12)
            diagnostic_title = QLabel("开发者诊断")
            diagnostic_title.setObjectName("metaDeveloperDiagnosticsTitle")
            diagnostic_title.setStyleSheet(card_title_qss())
            self._diagnostic_text = QLabel("")
            self._diagnostic_text.setObjectName("metaDeveloperDiagnosticsText")
            self._diagnostic_text.setWordWrap(True)
            self._diagnostic_text.setTextInteractionFlags(self._diagnostic_text.textInteractionFlags() | Qt.TextSelectableByMouse)
            self._diagnostic_text.setStyleSheet(helper_text_qss())
            diagnostic_layout.addWidget(diagnostic_title)
            diagnostic_layout.addWidget(self._diagnostic_text)
            self._diagnostic_card.setVisible(False)
            root.addWidget(self._diagnostic_card)

            body = QHBoxLayout()
            self._navigation_list = QListWidget()
            self._navigation_list.setObjectName("metaWorkflowStepList")
            self._navigation_list.setMaximumWidth(260)
            self._navigation_list.setStyleSheet(
                "QListWidget { "
                f"background: {BioMedPilotColors.SURFACE_WHITE}; "
                f"border: 1px solid {BioMedPilotColors.BORDER_MEDIUM}; "
                "border-radius: 8px; "
                "}"
                "QListWidget::item { "
                f"padding: {BioMedPilotSpacing.SM}px; "
                f"color: {BioMedPilotColors.TEXT_PRIMARY}; "
                "}"
                "QListWidget::item:selected { "
                f"background: {BioMedPilotColors.BIO_SOFT}; "
                f"color: {BioMedPilotColors.PRIMARY_NAVY}; "
                "}"
            )
            self._page_stack = QStackedWidget()
            self._page_stack.setObjectName("metaCurrentStepWorkspace")
            body.addWidget(self._navigation_list)
            body.addWidget(self._page_stack, 1)
            root.addLayout(body, 1)

            self._navigation_list.currentRowChanged.connect(self._page_stack.setCurrentIndex)
            self._build_pages()
            self._refresh_summary()

        def _build_pages(self) -> None:
            for item in self._layout_state.navigation_items:
                self._navigation_list.addItem(QListWidgetItem(f"{item.label}\n{item.status_label_zh}"))
                self._page_stack.addWidget(self._page(item))
                self._page_keys.append(item.page_key)
            self._navigation_list.setCurrentRow(0)

        def _page(self, item: MetaWorkspaceNavigationItem) -> QFrame:
            frame = QFrame()
            frame.setObjectName(f"metaMainlinePage_{item.page_key}")
            frame.setStyleSheet(section_card_qss(f"QFrame#metaMainlinePage_{item.page_key}"))
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(16, 14, 16, 14)
            layout.setSpacing(10)
            heading = QLabel(item.label)
            heading.setObjectName("metaMainlinePageTitle")
            heading.setStyleSheet(card_title_qss())
            body = QLabel(item.description)
            body.setWordWrap(True)
            body.setStyleSheet(helper_text_qss())
            note = QLabel(self._layout_state.testing_notice)
            note.setObjectName("metaMainlineBoundaryNotice")
            note.setWordWrap(True)
            note.setStyleSheet(status_badge_qss("testing"))
            layout.addWidget(heading)
            layout.addWidget(body)
            layout.addWidget(note)
            layout.addStretch(1)
            return frame

        def _refresh_summary(self) -> None:
            if self._current_meta_project is not None:
                summary = self._current_meta_project
                self._status_label.setText(f"当前 Meta 项目：{summary.project_name} · {_meta_status_text(summary.status)}")
                self._status_label.setStyleSheet(status_badge_qss(_meta_status_family(summary.status)))
                self._diagnostic_text.setText(
                    "\n".join(
                        [
                            f"project_root: {summary.project_root}",
                            f"manifest_path: {summary.manifest_path}",
                            f"config_path: {summary.config_path}",
                            f"workflow_stage: {summary.workflow_stage}",
                            f"status: {summary.status}",
                            "development_line: dev/meta-analysis",
                            f"contract_version: {META_ANALYSIS_MAINLINE_CONTRACT_VERSION}",
                        ]
                    )
                )
            elif self._current_project_dir is not None:
                self._status_label.setText("当前目录未绑定有效 Meta 项目。")
                self._status_label.setStyleSheet(status_badge_qss("warning"))
                self._diagnostic_text.setText(
                    "\n".join(
                        [
                            f"selected_dir: {self._current_project_dir}",
                            "manifest: 未读取到有效 meta_project_manifest.json",
                            "development_line: dev/meta-analysis",
                            f"contract_version: {META_ANALYSIS_MAINLINE_CONTRACT_VERSION}",
                        ]
                    )
                )
            else:
                self._status_label.setText("当前未绑定 Meta 项目。")
                self._status_label.setStyleSheet(status_badge_qss("not_ready"))
                self._diagnostic_text.setText(
                    "\n".join(
                        [
                            "selected_dir: 未选择",
                            "development_line: dev/meta-analysis",
                            f"contract_version: {META_ANALYSIS_MAINLINE_CONTRACT_VERSION}",
                        ]
                    )
                )

        def _toggle_developer_diagnostics(self) -> None:
            should_show = self._diagnostic_card.isHidden()
            self._diagnostic_card.setVisible(should_show)
            self._diagnostic_toggle_button.setText(
                "收起开发者诊断" if should_show else "展开开发者诊断"
            )

else:  # pragma: no cover

    class MetaAnalysisWorkspaceWidget:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            self._current_project_dir = None

        def page_keys(self) -> tuple[str, ...]:
            return tuple(item.page_key for item in meta_workspace_layout_state().navigation_items)

        def current_project_dir(self) -> Path | None:
            return self._current_project_dir

        def set_project_record(self, record) -> None:
            self._current_project_dir = Path(record.project_dir).expanduser().resolve()
