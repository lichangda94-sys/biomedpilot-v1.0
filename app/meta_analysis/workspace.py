from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.shared.feature_availability import FeatureAvailability, FeatureAvailabilityStatus, list_features
from app.shared.feature_status import FeatureItem, feature_item_from_availability
from app.version import APP_VERSION

from app.meta_analysis.project_workspace import MetaProjectSummary, open_meta_analysis_project
from app.meta_analysis.search_config_draft import (
    MetaSeedConceptGuard,
    MetaSeedSearchConfigDraft,
    build_user_edited_search_plan,
    build_meta_seed_search_config_draft,
    save_confirmed_search_plan,
    save_meta_seed_search_config_draft,
    save_rejected_search_config_draft,
)
from app.meta_analysis.version import META_ANALYSIS_MAINLINE_CONTRACT_VERSION

try:
    from PySide6.QtWidgets import (
        QFrame,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPlainTextEdit,
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
            "mainline 保留 Meta 模块入口、项目绑定和占位工作台；完整流程在 dev/meta-analysis 开发。",
            "在 dev/meta-analysis 完成验收后再合入具体功能。",
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
        description="主线保留 Meta 入口、项目壳和 seed 检索配置草稿；正式检索、筛选、提取、统计和报告功能仍在 dev/meta-analysis 开发。",
        navigation_items=(
            MetaWorkspaceNavigationItem("project_home", "Meta 项目首页", "项目绑定、状态摘要和分支边界说明。", "workflow_home"),
            MetaWorkspaceNavigationItem("project_contract", "项目契约", "创建和打开 Meta 项目的最小 manifest contract。", "project_contract"),
            MetaWorkspaceNavigationItem(
                "search_config_draft",
                "Seed 检索草稿",
                "中文研究问题映射到 PICO/PECO 草稿、英文 PubMed query draft 和 query guard。",
                "search_config_draft",
                "Draft only",
                "仅草稿",
            ),
            MetaWorkspaceNavigationItem("dev_branch", "功能开发线", "完整 Meta workflow 位于 dev/meta-analysis。", "dev_branch"),
        ),
        default_page_key="workflow_home",
        testing_notice="当前 mainline 只生成和保存 seed 检索配置草稿；不会执行 PubMed/Embase/WOS/中文数据库检索，也不会标记正式检索完成。",
        version_status_label=version_status,
    )


if QWidget is not None:

    class MetaAnalysisWorkspaceWidget(QWidget):
        def __init__(self, on_back: Callable[[], None] | None = None) -> None:
            super().__init__()
            self.setObjectName("metaAnalysisWorkspace")
            self._on_back = on_back
            self._current_project_dir: Path | None = None
            self._current_meta_project: MetaProjectSummary | None = None
            self._current_search_config_draft: MetaSeedSearchConfigDraft | None = None
            self._current_user_edited_search_plan = None
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
                self._status_label.setText("；".join(validation.errors) or "该文件夹不是有效 Meta 项目。")
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
                "search_config_draft_available": "search_config_draft" in self._page_keys,
            }

        def generate_seed_search_config_preview(self, question: str) -> dict[str, object]:
            draft = build_meta_seed_search_config_draft(question)
            self._current_search_config_draft = draft
            self._render_seed_search_config_draft(draft)
            return draft.to_dict()

        def save_seed_search_config_preview(self) -> Path:
            if self._current_project_dir is None:
                raise ValueError("请先绑定 Meta 项目，再保存检索配置草稿。")
            if self._current_search_config_draft is None:
                question = self._search_question_input.toPlainText() if hasattr(self, "_search_question_input") else ""
                if not question.strip():
                    raise ValueError("请先输入中文研究问题并生成草稿。")
                self._current_search_config_draft = build_meta_seed_search_config_draft(question)
            edited = self._build_user_edited_search_plan_from_ui()
            self._current_user_edited_search_plan = edited
            path = save_meta_seed_search_config_draft(self._current_project_dir, self._current_search_config_draft, edited)
            self._search_config_status_label.setText(f"已保存草稿：{path}；状态为 {edited.review_status}/not_executed。")
            return path

        def confirm_seed_search_config_plan(self) -> Path:
            if self._current_project_dir is None:
                raise ValueError("请先绑定 Meta 项目，再确认检索计划。")
            if self._current_search_config_draft is None:
                raise ValueError("请先生成检索配置草稿。")
            edited = self._build_user_edited_search_plan_from_ui()
            self._current_user_edited_search_plan = edited
            path = save_confirmed_search_plan(
                self._current_project_dir,
                self._current_search_config_draft,
                edited,
                user_confirmed=True,
            )
            self._search_config_status_label.setText(f"已确认检索计划：{path}；仍未执行在线检索。")
            return path

        def reject_seed_search_config_draft(self) -> Path:
            if self._current_project_dir is None:
                raise ValueError("请先绑定 Meta 项目，再拒绝检索草稿。")
            if self._current_search_config_draft is None:
                raise ValueError("请先生成检索配置草稿。")
            path = save_rejected_search_config_draft(
                self._current_project_dir,
                self._current_search_config_draft,
                user_notes=self._search_user_notes_input.toPlainText() if hasattr(self, "_search_user_notes_input") else "",
            )
            self._search_config_status_label.setText(f"已拒绝草稿：{path}；不会进入后续 workflow。")
            return path

        def _build_ui(self) -> None:
            root = QVBoxLayout(self)
            root.setContentsMargins(18, 18, 18, 18)
            root.setSpacing(12)

            header = QFrame()
            header.setObjectName("metaMainlineHeader")
            header_layout = QHBoxLayout(header)
            title_col = QVBoxLayout()
            title = QLabel("Meta 分析模块")
            title.setObjectName("metaWorkspaceTitle")
            title.setStyleSheet("font-size: 22px; font-weight: 700;")
            subtitle = QLabel("mainline 入口与项目壳；完整功能开发保留在 dev/meta-analysis。")
            subtitle.setObjectName("metaWorkspaceSubtitle")
            title_col.addWidget(title)
            title_col.addWidget(subtitle)
            header_layout.addLayout(title_col, 1)
            if self._on_back is not None:
                back = QPushButton("返回模块首页")
                back.setObjectName("metaBackButton")
                back.clicked.connect(self._on_back)
                header_layout.addWidget(back)
            root.addWidget(header)

            self._status_label = QLabel("")
            self._status_label.setObjectName("metaProjectStatus")
            root.addWidget(self._status_label)

            body = QHBoxLayout()
            self._navigation_list = QListWidget()
            self._navigation_list.setObjectName("metaWorkflowStepList")
            self._navigation_list.setMaximumWidth(260)
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
            if item.page_key == "search_config_draft":
                return self._search_config_draft_page(item)
            frame = QFrame()
            frame.setObjectName(f"metaMainlinePage_{item.page_key}")
            layout = QVBoxLayout(frame)
            heading = QLabel(item.label)
            heading.setStyleSheet("font-size: 18px; font-weight: 700;")
            body = QLabel(item.description)
            body.setWordWrap(True)
            note = QLabel(self._layout_state.testing_notice)
            note.setObjectName("metaMainlineBoundaryNotice")
            note.setWordWrap(True)
            layout.addWidget(heading)
            layout.addWidget(body)
            layout.addWidget(note)
            layout.addStretch(1)
            return frame

        def _search_config_draft_page(self, item: MetaWorkspaceNavigationItem) -> QFrame:
            frame = QFrame()
            frame.setObjectName(f"metaMainlinePage_{item.page_key}")
            layout = QVBoxLayout(frame)
            heading = QLabel(item.label)
            heading.setStyleSheet("font-size: 18px; font-weight: 700;")
            body = QLabel("输入中文研究问题后，本地 seed helper 会生成 PICO/PECO 草稿、英文 PubMed query draft 和 query guard。")
            body.setWordWrap(True)
            notice = QLabel("Draft only：需要用户确认；不执行在线检索；保存后不标记正式检索完成。")
            notice.setObjectName("metaSearchConfigDraftNotice")
            notice.setWordWrap(True)
            self._search_question_input = QPlainTextEdit()
            self._search_question_input.setObjectName("metaSearchQuestionInput")
            self._search_question_input.setPlaceholderText("例如：肥胖与乳腺癌风险的Meta分析")
            self._search_question_input.setMaximumHeight(90)
            button_row = QHBoxLayout()
            generate_button = QPushButton("生成检索配置草稿")
            generate_button.setObjectName("metaGenerateSearchConfigDraftButton")
            save_button = QPushButton("保存草稿")
            save_button.setObjectName("metaSaveSearchConfigDraftButton")
            confirm_button = QPushButton("确认为检索计划")
            confirm_button.setObjectName("metaConfirmSearchPlanButton")
            reject_button = QPushButton("拒绝草稿")
            reject_button.setObjectName("metaRejectSearchDraftButton")
            generate_button.clicked.connect(
                lambda: self.generate_seed_search_config_preview(self._search_question_input.toPlainText())
            )
            save_button.clicked.connect(self.save_seed_search_config_preview)
            confirm_button.clicked.connect(self.confirm_seed_search_config_plan)
            reject_button.clicked.connect(self.reject_seed_search_config_draft)
            button_row.addWidget(generate_button)
            button_row.addWidget(save_button)
            button_row.addWidget(confirm_button)
            button_row.addWidget(reject_button)
            button_row.addStretch(1)
            self._search_config_status_label = QLabel("尚未生成检索配置草稿。")
            self._search_config_status_label.setObjectName("metaSearchConfigDraftStatus")
            self._search_config_status_label.setWordWrap(True)
            self._search_config_summary_label = QLabel("")
            self._search_config_summary_label.setObjectName("metaSearchConfigDraftSummary")
            self._search_config_summary_label.setWordWrap(True)
            self._search_query_edit = QPlainTextEdit()
            self._search_query_edit.setObjectName("metaSearchQueryDraftEdit")
            self._search_query_edit.setPlaceholderText("生成后可编辑 PubMed query block；确认前不会执行检索。")
            self._search_query_edit.setMaximumHeight(120)
            self._search_user_notes_input = QPlainTextEdit()
            self._search_user_notes_input.setObjectName("metaSearchUserNotes")
            self._search_user_notes_input.setPlaceholderText("用户 notes / selected terms / included blocks 说明")
            self._search_user_notes_input.setMaximumHeight(80)
            self._search_config_guard_label = QLabel("")
            self._search_config_guard_label.setObjectName("metaSearchConfigDraftGuards")
            self._search_config_guard_label.setWordWrap(True)
            layout.addWidget(heading)
            layout.addWidget(body)
            layout.addWidget(notice)
            layout.addWidget(self._search_question_input)
            layout.addLayout(button_row)
            layout.addWidget(self._search_config_status_label)
            layout.addWidget(self._search_config_summary_label)
            layout.addWidget(self._search_query_edit)
            layout.addWidget(self._search_user_notes_input)
            layout.addWidget(self._search_config_guard_label)
            layout.addStretch(1)
            return frame

        def _render_seed_search_config_draft(self, draft: MetaSeedSearchConfigDraft) -> None:
            if not hasattr(self, "_search_config_summary_label"):
                return
            self._search_config_status_label.setText("已生成 draft；需要用户确认，尚未执行任何在线检索。")
            summary = [
                f"Population: {_labels(draft.population)}",
                f"Exposure/Intervention: {_labels(draft.exposure_or_intervention)}",
                f"Outcome: {_labels(draft.outcome)}",
                f"Intent: {draft.detected_intent}",
                f"PubMed query draft: {draft.pubmed_query_draft or '未生成'}",
                f"Search status: {draft.search_execution_status}; formal completed: {draft.formal_search_completed}",
            ]
            guards = [
                f"{guard.preferred_label_en}: expansion={guard.query_expansion_allowed}, "
                f"standalone={guard.standalone_search_allowed}, filter_only={guard.filter_only}, "
                f"in_query={guard.included_in_pubmed_topic_query}"
                for guard in draft.detected_concepts
            ]
            self._search_config_summary_label.setText("\n".join(summary))
            self._search_query_edit.setPlainText(draft.pubmed_query_draft)
            self._search_config_guard_label.setText("Query guard:\n" + ("\n".join(guards) if guards else "未检测到 seed term。"))

        def _build_user_edited_search_plan_from_ui(self):
            if self._current_search_config_draft is None:
                raise ValueError("请先生成检索配置草稿。")
            edited_query = self._search_query_edit.toPlainText() if hasattr(self, "_search_query_edit") else None
            notes = self._search_user_notes_input.toPlainText() if hasattr(self, "_search_user_notes_input") else ""
            return build_user_edited_search_plan(
                self._current_search_config_draft,
                edited_pubmed_query_draft=edited_query,
                user_notes=notes,
            )

        def _refresh_summary(self) -> None:
            if self._current_meta_project is not None:
                summary = self._current_meta_project
                self._status_label.setText(
                    f"当前 Meta 项目：{summary.project_name} · {summary.status} · {summary.project_root}"
                )
            elif self._current_project_dir is not None:
                self._status_label.setText(f"当前目录：{self._current_project_dir}；尚未读取到有效 Meta 项目 manifest。")
            else:
                self._status_label.setText("当前未绑定 Meta 项目。")

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


def _labels(guards: tuple[MetaSeedConceptGuard, ...]) -> str:
    return ", ".join(guard.preferred_label_en for guard in guards) or "未识别"
