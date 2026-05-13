from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.services.criteria_service import CriteriaBuilderService
from app.meta_analysis.services.exclusion_criteria_library_service import ExclusionCriteriaLibraryService
from app.meta_analysis.services.screening_service import ScreeningQueueResult, ScreeningService
from app.meta_analysis.services.title_abstract_screening_v2_service import (
    DECISION_EXCLUDE,
    DECISION_INCLUDE,
    DECISION_NEEDS_REVIEW,
    DECISION_NOT_SCREENED,
    DECISION_UNCERTAIN,
    DEFAULT_EXCLUSION_REASONS,
    TITLE_ABSTRACT_SCREENING_QUEUE_SCHEMA_VERSION,
    TitleAbstractScreeningV2Service,
)
from app.meta_analysis.ui_text import (
    DEVELOPER_INFO_TITLE_ZH,
    INTERNAL_BETA_STATUS_ZH,
    SCREENING_DECISION_ZH,
    SCREENING_DESCRIPTION_ZH,
    SCREENING_FILTER_ZH,
    SCREENING_PROGRESS_ZH,
    SCREENING_TITLE_ZH,
)
from app.shared.feature_availability import get_feature
from app.ui_style_tokens import meta_card_stylesheet, meta_error_text_style, meta_title_style
from app.version import APP_VERSION


@dataclass(frozen=True)
class ScreeningPageState:
    title: str
    description: str
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    warning_summary: str
    last_result: ScreeningQueueResult | None = None
    criteria_summary_path: str = ""
    criteria_hints: tuple[str, ...] = ()
    title_zh: str = SCREENING_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = SCREENING_DESCRIPTION_ZH
    input_summary_zh: str = "输入：去重后的文献、筛选队列和纳入/排除标准。"
    output_summary_zh: str = "输出：标题摘要筛选决策、进度摘要和排除原因。"
    next_step_zh: str = "下一步：对纳入或可能纳入的文献进行全文筛选。"
    empty_state_zh: str = "没有筛选来源时无法生成队列；请先完成文献导入和去重审核。"
    warning_summary_zh: str = "排除记录必须填写排除原因；maybe 和 needs review 需要 reviewer 复核。"
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


@dataclass(frozen=True)
class TitleAbstractScreeningRecordView:
    screening_record_id: str
    record_id: str
    title: str
    abstract: str
    authors: str
    journal: str
    year: str
    doi: str
    pmid: str
    source_links: tuple[str, ...]
    source_link_labels_zh: tuple[str, ...]
    decision: str
    decision_zh: str
    exclusion_reason_text: str
    notes: str


@dataclass(frozen=True)
class TitleAbstractScreeningUXState:
    title: str
    status_label: str
    queue_path: str
    current_index: int
    current_record: TitleAbstractScreeningRecordView | None
    previous_record_id: str
    next_record_id: str
    records: tuple[TitleAbstractScreeningRecordView, ...]
    decision_options: tuple[str, ...]
    exclusion_reason_options: tuple[str, ...]
    criteria_hints: tuple[str, ...]
    progress_summary: dict[str, int]
    filter_views: tuple[str, ...]
    decision_option_labels_zh: tuple[str, ...]
    filter_view_labels_zh: tuple[str, ...]
    progress_labels_zh: dict[str, str]
    output_paths: dict[str, str]
    warnings: tuple[str, ...]
    empty_state: str
    testing_limitations: tuple[str, ...]
    title_zh: str = SCREENING_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = SCREENING_DESCRIPTION_ZH
    input_summary_zh: str = "输入：screening queue、纳入/排除标准和文献来源链接。"
    output_summary_zh: str = "输出：title_abstract_decisions.json/csv 和 screening_summary.json。"
    next_step_zh: str = "下一步：筛选 include / maybe 记录进入全文筛选。"
    empty_state_zh: str = "没有可筛选记录。请先生成 screening queue。"
    warning_summary_zh: str = "缺少 queue、空 queue 或排除原因缺失时需要人工处理。"
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


@dataclass(frozen=True)
class TitleAbstractScreeningV2PageState:
    title: str
    status_label: str
    queue_path: str
    decisions_path: str
    compatible_decisions_path: str
    schema_version: str
    source_type: str
    total_records: int
    queue_records: tuple[TitleAbstractScreeningRecordView, ...]
    decision_counts: dict[str, int]
    decision_options: tuple[str, ...]
    decision_option_labels_zh: tuple[str, ...]
    exclusion_reason_options: tuple[str, ...]
    warnings: tuple[str, ...]
    next_step: str
    testing_limitations: tuple[str, ...]
    output_summary: str
    empty_state: str
    title_zh: str = "标题摘要初筛 v2"
    status_label_zh: str = "Developer Preview / 需要人工确认"


def initial_screening_state() -> ScreeningPageState:
    feature = get_feature("meta-screening")
    return ScreeningPageState(
        title="Screening / 标题摘要筛选",
        description="读取 Prepare for Screening 或 Duplicate Review 输出，生成待人工判读的标题摘要筛选队列。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        input_summary="输入：screening_ready_records 或 duplicate_candidate_groups JSON。",
        output_summary="输出：screening_queue / screening_decisions 数据资产和 screening task。",
        next_step="下一步：Extraction；也可继续 full-text status 和质量评价 testing 子流程。",
        empty_state="没有筛选来源时无法生成队列；没有候选记录时页面应显示空队列摘要。",
        warning_summary="excluded 决策必须填写排除原因；错误提示为用户可读 message。",
        title_zh=SCREENING_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=SCREENING_DESCRIPTION_ZH,
    )


def screening_state_with_criteria(project_dir: Path, *, criteria_service: CriteriaBuilderService | None = None) -> ScreeningPageState:
    base = initial_screening_state()
    criteria_service = criteria_service or CriteriaBuilderService()
    project_dir = project_dir.expanduser().resolve()
    criteria_summary = project_dir / "criteria" / "criteria_summary.md"
    hints = criteria_service.criteria_hints(project_dir, stage="title_abstract")
    return ScreeningPageState(
        **{
            **base.__dict__,
            "criteria_summary_path": str(criteria_summary),
            "criteria_hints": hints,
            "warning_summary": base.warning_summary
            + (" Criteria hints loaded from criteria_summary.md." if hints else " Criteria Builder 尚未生成；筛选仍可运行，但排除标准需人工记录。"),
        }
    )


def title_abstract_screening_state_from_queue(
    queue_path: Path,
    *,
    project_dir: Path | None = None,
    current_index: int = 0,
    criteria_service: CriteriaBuilderService | None = None,
) -> TitleAbstractScreeningUXState:
    queue_path = queue_path.expanduser().resolve()
    project_dir = (project_dir or queue_path.parents[1] if len(queue_path.parents) > 1 else queue_path.parent).expanduser().resolve()
    criteria_service = criteria_service or CriteriaBuilderService()
    payload = _load_json(queue_path)
    records = tuple(_record_view(item) for item in payload.get("screening_records", []) if isinstance(item, dict)) if isinstance(payload, dict) else ()
    safe_index = max(0, min(current_index, len(records) - 1)) if records else 0
    current = records[safe_index] if records else None
    progress = _progress_summary(records)
    warnings: list[str] = []
    if not queue_path.exists():
        warnings.append("missing_screening_queue")
    if not records:
        warnings.append("empty_screening_queue")
    return TitleAbstractScreeningUXState(
        title="Title / Abstract Screening",
        status_label="Testing / Developer Preview",
        queue_path=str(queue_path),
        current_index=safe_index,
        current_record=current,
        previous_record_id=records[safe_index - 1].screening_record_id if records and safe_index > 0 else "",
        next_record_id=records[safe_index + 1].screening_record_id if records and safe_index + 1 < len(records) else "",
        records=records,
        decision_options=("included", "excluded", "maybe", "needs_review", "pending"),
        exclusion_reason_options=_exclusion_options(criteria_service.criteria_hints(project_dir, stage="title_abstract")),
        criteria_hints=criteria_service.criteria_hints(project_dir, stage="title_abstract"),
        progress_summary=progress,
        filter_views=("all", "pending", "included", "excluded", "maybe", "needs_review"),
        decision_option_labels_zh=tuple(SCREENING_DECISION_ZH[item] for item in ("included", "excluded", "maybe", "needs_review", "pending")),
        filter_view_labels_zh=tuple(SCREENING_FILTER_ZH[item] for item in ("all", "pending", "included", "excluded", "maybe", "needs_review")),
        progress_labels_zh={key: SCREENING_PROGRESS_ZH[key] for key in progress},
        output_paths={
            "title_abstract_decisions_json": str(project_dir / "screening" / "title_abstract_decisions.json"),
            "title_abstract_decisions_csv": str(project_dir / "screening" / "title_abstract_decisions.csv"),
            "screening_summary_json": str(project_dir / "screening" / "screening_summary.json"),
        },
        warnings=tuple(warnings),
        empty_state="没有可筛选记录。请先生成 screening queue。" if not records else "",
        testing_limitations=(
            "needs_review 是 UI 视图标签；当前保存服务仍使用 pending/included/excluded/maybe 兼容旧格式。",
            "本页面不删除文献；只辅助 reviewer 保存明确 screening decision。",
        ),
        title_zh=SCREENING_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=SCREENING_DESCRIPTION_ZH,
        empty_state_zh="没有可筛选记录。请先生成 screening queue。" if not records else "",
    )


def title_abstract_screening_v2_state_from_project(
    project_dir: Path,
    *,
    service: TitleAbstractScreeningV2Service | None = None,
    exclusion_library_service: ExclusionCriteriaLibraryService | None = None,
) -> TitleAbstractScreeningV2PageState:
    project_dir = project_dir.expanduser().resolve()
    service = service or TitleAbstractScreeningV2Service()
    exclusion_library_service = exclusion_library_service or ExclusionCriteriaLibraryService()
    queue_payload = service.load_queue(project_dir)
    records = tuple(_v2_record_view(item) for item in queue_payload.get("queue_records", []) if isinstance(item, dict))
    decisions_payload = _load_json(Path(service.decisions_path(project_dir)))
    decisions = [dict(item) for item in decisions_payload.get("screening_records", []) if isinstance(item, dict)]
    counts = {
        "include": 0,
        "exclude": 0,
        "uncertain": 0,
        "needs_review": 0,
        "not_screened": max(len(records) - len(decisions), 0),
        "total": len(records),
    }
    for item in decisions:
        decision = str(item.get("decision") or "needs_review")
        counts[decision] = counts.get(decision, 0) + 1
    warnings = list(str(item) for item in queue_payload.get("warnings", []) if str(item))
    if not records:
        warnings.append("empty_title_abstract_screening_queue_v2")
    exclusion_options = tuple(
        reason.english_label
        for reason in exclusion_library_service.list_reasons(project_dir, stage="title_abstract", enabled_only=True)
    ) or DEFAULT_EXCLUSION_REASONS
    return TitleAbstractScreeningV2PageState(
        title="Title / Abstract Screening v2",
        status_label="Developer Preview / reviewer decisions required",
        queue_path=str(service.queue_path(project_dir)),
        decisions_path=str(service.decisions_path(project_dir)),
        compatible_decisions_path=str(service.compatible_decisions_path(project_dir)),
        schema_version=str(queue_payload.get("schema_version") or TITLE_ABSTRACT_SCREENING_QUEUE_SCHEMA_VERSION),
        source_type=str(queue_payload.get("source_type") or ""),
        total_records=len(records),
        queue_records=records,
        decision_counts=counts,
        decision_options=(DECISION_INCLUDE, DECISION_EXCLUDE, DECISION_UNCERTAIN, DECISION_NEEDS_REVIEW),
        decision_option_labels_zh=("纳入", "排除", "不确定", "需要复核"),
        exclusion_reason_options=exclusion_options,
        warnings=tuple(dict.fromkeys(warnings)),
        next_step="下一步：仅 reviewer 决策为 include / uncertain 的记录可进入全文候选。",
        testing_limitations=(
            "生成队列不是筛选决定，不会自动纳入或排除文献。",
            "AI/model 输出只能作为 suggestion，不能直接写最终筛选结果。",
            "PRISMA screened / excluded 数字只应来自 reviewer 保存的真实决策记录。",
        ),
        output_summary="输出：title_abstract_queue_v2.json、title_abstract_decisions_v2.json 和兼容 screening_decisions.json。",
        empty_state="没有可筛选记录。请先完成文献导入和去重复核。" if not records else "",
    )


def export_title_abstract_screening_artifacts(queue_path: Path, project_dir: Path) -> dict[str, str]:
    state = title_abstract_screening_state_from_queue(queue_path, project_dir=project_dir)
    project_dir = project_dir.expanduser().resolve()
    output_dir = project_dir / "screening"
    output_dir.mkdir(parents=True, exist_ok=True)
    decisions_json = output_dir / "title_abstract_decisions.json"
    decisions_csv = output_dir / "title_abstract_decisions.csv"
    summary_json = output_dir / "screening_summary.json"
    records_payload = [record.__dict__ for record in state.records]
    decisions_json.write_text(json.dumps({"records": records_payload, "decision_counts": state.progress_summary}, ensure_ascii=False, indent=2), encoding="utf-8")
    with decisions_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["screening_record_id", "record_id", "decision", "exclusion_reason_text", "notes", "title"])
        writer.writeheader()
        for record in state.records:
            writer.writerow(
                {
                    "screening_record_id": record.screening_record_id,
                    "record_id": record.record_id,
                    "decision": record.decision,
                    "exclusion_reason_text": record.exclusion_reason_text,
                    "notes": record.notes,
                    "title": record.title,
                }
            )
    summary_json.write_text(json.dumps({"stage": "title_abstract_screening", "progress_summary": state.progress_summary, "warnings": list(state.warnings)}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "title_abstract_decisions_json": str(decisions_json),
        "title_abstract_decisions_csv": str(decisions_csv),
        "screening_summary_json": str(summary_json),
    }


def _record_view(item: dict[str, object]) -> TitleAbstractScreeningRecordView:
    doi = str(item.get("doi") or item.get("doi_normalized") or "")
    pmid = str(item.get("pmid") or item.get("pmid_normalized") or "")
    return TitleAbstractScreeningRecordView(
        screening_record_id=str(item.get("screening_record_id", "")),
        record_id=str(item.get("normalized_record_id") or item.get("record_id") or item.get("source_record_id") or ""),
        title=str(item.get("title", "")),
        abstract=str(item.get("abstract", "")),
        authors=_join_text(item.get("authors") or item.get("authors_normalized") or item.get("authors_text")),
        journal=str(item.get("journal") or item.get("journal_normalized") or ""),
        year=str(item.get("year") or item.get("year_normalized") or ""),
        doi=doi,
        pmid=pmid,
        source_links=tuple(link for link in (_doi_link(doi), _pmid_link(pmid)) if link),
        source_link_labels_zh=tuple(label for label, link in (("打开 DOI", _doi_link(doi)), ("打开 PubMed", _pmid_link(pmid))) if link),
        decision=str(item.get("decision") or "pending"),
        decision_zh=SCREENING_DECISION_ZH.get(str(item.get("decision") or "pending"), str(item.get("decision") or "pending")),
        exclusion_reason_text=str(item.get("exclusion_reason_text") or ""),
        notes=str(item.get("notes") or ""),
    )


def _v2_record_view(item: dict[str, object]) -> TitleAbstractScreeningRecordView:
    doi = str(item.get("doi") or "")
    pmid = str(item.get("pmid") or "")
    decision = str(item.get("decision") or DECISION_NOT_SCREENED)
    decision_zh = {
        DECISION_INCLUDE: "纳入",
        DECISION_EXCLUDE: "排除",
        DECISION_UNCERTAIN: "不确定",
        DECISION_NEEDS_REVIEW: "需要复核",
        DECISION_NOT_SCREENED: "未筛选",
    }.get(decision, decision)
    return TitleAbstractScreeningRecordView(
        screening_record_id=str(item.get("record_id", "")),
        record_id=str(item.get("record_id", "")),
        title=str(item.get("title", "")),
        abstract=str(item.get("abstract", "")),
        authors=_join_text(item.get("authors") or item.get("authors_text")),
        journal=str(item.get("journal") or ""),
        year=str(item.get("year") or ""),
        doi=doi,
        pmid=pmid,
        source_links=tuple(link for link in (_doi_link(doi), _pmid_link(pmid)) if link),
        source_link_labels_zh=tuple(label for label, link in (("打开 DOI", _doi_link(doi)), ("打开 PubMed", _pmid_link(pmid))) if link),
        decision=decision,
        decision_zh=decision_zh,
        exclusion_reason_text=str(item.get("exclusion_reason_text") or ""),
        notes=str(item.get("notes") or ""),
    )


def _progress_summary(records: tuple[TitleAbstractScreeningRecordView, ...]) -> dict[str, int]:
    output = {"total": len(records), "pending": 0, "included": 0, "excluded": 0, "maybe": 0, "needs_review": 0, "screened": 0}
    for record in records:
        decision = record.decision if record.decision in output else "pending"
        output[decision] += 1
        if decision != "pending":
            output["screened"] += 1
    output["needs_review"] += output["maybe"]
    return output


def _exclusion_options(criteria_hints: tuple[str, ...]) -> tuple[str, ...]:
    options = [hint.removeprefix("Exclude if: ").strip() for hint in criteria_hints if hint.startswith("Exclude if: ")]
    defaults = ("wrong population", "wrong intervention or exposure", "wrong comparator", "wrong outcome", "insufficient data", "full text unavailable")
    return tuple(dict.fromkeys([*options, *defaults]))


def _doi_link(doi: str) -> str:
    return f"https://doi.org/{doi}" if doi else ""


def _pmid_link(pmid: str) -> str:
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""


def _join_text(value: object) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value or "")


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class ScreeningPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: ScreeningService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or ScreeningService()
            self._state = initial_screening_state()

            root = QVBoxLayout(self)
            title = QLabel(f"{self._state.title_zh} · {self._state.status_label_zh}")
            title.setStyleSheet(meta_title_style())
            root.addWidget(title)
            description = QLabel(self._state.description_zh)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label_zh} / {self._state.status_label}"))

            row = QHBoxLayout()
            self._path_input = QLineEdit()
            self._path_input.setPlaceholderText("选择或粘贴 Prepare / Duplicate Review 输出 JSON 文件路径")
            choose_button = QPushButton("选择筛选来源")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("生成标题摘要筛选队列")
            run_button.clicked.connect(self._create_queue)
            root.addWidget(run_button)

            decision_card = QFrame()
            decision_card.setStyleSheet(meta_card_stylesheet())
            decision_layout = QVBoxLayout(decision_card)
            decision_title = QLabel("最小人工判读")
            decision_title.setStyleSheet("font-weight: 700;")
            decision_layout.addWidget(decision_title)
            self._record_id_input = QLineEdit()
            self._record_id_input.setPlaceholderText("screening_record_id，例如 screen-xxxx")
            self._decision_input = QLineEdit()
            self._decision_input.setPlaceholderText("decision: included / excluded / maybe / pending")
            self._reason_input = QLineEdit()
            self._reason_input.setPlaceholderText("excluded 时填写排除原因")
            self._notes_input = QLineEdit()
            self._notes_input.setPlaceholderText("可选 notes")
            decision_layout.addWidget(self._record_id_input)
            decision_layout.addWidget(self._decision_input)
            decision_layout.addWidget(self._reason_input)
            decision_layout.addWidget(self._notes_input)
            save_decision_button = QPushButton("保存筛选决策")
            save_decision_button.clicked.connect(self._save_decision)
            decision_layout.addWidget(save_decision_button)
            root.addWidget(decision_card)

            self._status_label = QLabel("筛选状态：等待筛选来源")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet(meta_card_stylesheet())
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("筛选队列摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet(meta_error_text_style())
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：Extraction")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择筛选来源", "", "Screening source (*.json)")
            if path:
                self._path_input.setText(path)

        def _create_queue(self) -> None:
            result = self._service.create_queue(project_id=self._project_id, source_path=self._path_input.text())
            if result.success:
                self._status_label.setText("筛选状态：队列已生成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"总记录：{result.total_records}\n"
                    f"待筛选：{result.queued_records}\n"
                    f"Pending：{result.decision_counts.get('pending', 0)}\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("筛选状态：失败")
                self._summary_label.setText("没有生成筛选队列。")
                self._error_label.setText(result.message)

        def _save_decision(self) -> None:
            result = self._service.update_decision(
                project_id=self._project_id,
                queue_path=self._path_input.text(),
                screening_record_id=self._record_id_input.text(),
                decision=self._decision_input.text(),
                exclusion_reason_text=self._reason_input.text(),
                notes=self._notes_input.text(),
            )
            if result.success:
                self._status_label.setText("筛选状态：决策已保存")
                self._summary_label.setText(
                    f"队列：{result.queue_path}\n"
                    f"记录：{result.screening_record_id}\n"
                    f"决策：{result.decision}\n"
                    f"Included：{result.decision_counts.get('included', 0)}\n"
                    f"Excluded：{result.decision_counts.get('excluded', 0)}\n"
                    f"Maybe：{result.decision_counts.get('maybe', 0)}\n"
                    f"Pending：{result.decision_counts.get('pending', 0)}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("筛选状态：决策保存失败")
                self._error_label.setText(result.message)

else:

    class ScreeningPage:  # type: ignore[no-redef]
        pass
