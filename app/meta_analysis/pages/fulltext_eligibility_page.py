from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.models.systematic_review import FULLTEXT_EXCLUSION_REASONS
from app.meta_analysis.services.criteria_service import CriteriaBuilderService
from app.meta_analysis.services.fulltext_eligibility_service import (
    FULLTEXT_ELIGIBILITY_STATUSES,
    FullTextEligibilityCandidate,
    FullTextEligibilityService,
)
from app.meta_analysis.services.fulltext_management_service import (
    FULLTEXT_MANAGEMENT_REGISTRY_SCHEMA_VERSION,
    FULLTEXT_MANAGEMENT_STATUSES,
    FullTextManagementService,
)
from app.meta_analysis.services.fulltext_parsing_service import (
    FULLTEXT_PARSE_MANIFEST_SCHEMA_VERSION,
    FullTextParsingService,
)
from app.meta_analysis.ui_text import (
    DEVELOPER_INFO_TITLE_ZH,
    FULLTEXT_ELIGIBILITY_DESCRIPTION_ZH,
    FULLTEXT_ELIGIBILITY_TITLE_ZH,
    FULLTEXT_STATUS_ZH,
    INTERNAL_BETA_STATUS_ZH,
)
from app.version import APP_VERSION


@dataclass(frozen=True)
class FullTextEligibilityPageState:
    title: str
    description: str
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    warning_summary: str
    candidate_count: int
    candidates: tuple[FullTextEligibilityCandidate, ...]
    status_options: tuple[str, ...]
    exclusion_reason_options: tuple[str, ...]
    decision_counts: dict[str, int]
    output_paths: dict[str, str]
    criteria_summary_path: str
    criteria_hints: tuple[str, ...]
    warnings: tuple[str, ...]
    testing_limitations: tuple[str, ...]
    fulltext_management_record_count: int = 0
    fulltext_management_status_counts: dict[str, int] | None = None
    fulltext_management_registry_path: str = ""
    fulltext_management_schema_version: str = FULLTEXT_MANAGEMENT_REGISTRY_SCHEMA_VERSION
    fulltext_parse_manifest_path: str = ""
    fulltext_parse_schema_version: str = FULLTEXT_PARSE_MANIFEST_SCHEMA_VERSION
    fulltext_parse_counts: dict[str, int] | None = None
    title_zh: str = FULLTEXT_ELIGIBILITY_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = FULLTEXT_ELIGIBILITY_DESCRIPTION_ZH
    input_summary_zh: str = "输入：标题摘要筛选 include / maybe 记录、附件登记和全文状态。"
    output_summary_zh: str = "输出：全文筛选决策、全文排除报告和最终纳入研究。"
    next_step_zh: str = "下一步：included_for_extraction 记录进入数据提取。"
    empty_state_zh: str = "没有全文候选记录。请先完成标题摘要筛选。"
    warning_summary_zh: str = "缺失全文、访问失败或全文后排除必须记录可读原因。"
    status_option_labels_zh: tuple[str, ...] = ()
    decision_count_labels_zh: dict[str, str] | None = None
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


def initial_fulltext_eligibility_state(project_dir: Path | None = None) -> FullTextEligibilityPageState:
    project_dir = project_dir.expanduser().resolve() if project_dir is not None else None
    return FullTextEligibilityPageState(
        title="Full-text Eligibility Screening",
        description="Developer Preview / testing 全文资格筛选页：从 title/abstract included 或 maybe 记录生成全文候选清单，支持手动记录 PDF availability、全文排除原因和 final included studies。",
        status_label="Testing / Developer Preview",
        input_summary="输入：screening/title_abstract_decisions.json 或 screening/screening_decisions.json；可选 attachment/fulltext registry。",
        output_summary="输出：fulltext_eligibility_decisions.json、fulltext_exclusion_report.csv、final_included_studies.json，并保留旧 fulltext_screening_decisions.json 兼容。",
        next_step="下一步：Extraction。只有 included_for_extraction 或已绑定本地 PDF 的记录应进入提取。",
        empty_state="没有 full-text 候选记录。请先完成 title/abstract screening，并将记录标记为 included 或 maybe。",
        warning_summary="missing full text、failed access 或 excluded after full-text review 必须记录可读 exclusion reason；本页不下载 PDF，OCR 仅用于用户触发的本地全文文本获取。",
        candidate_count=0,
        candidates=(),
        status_options=FULLTEXT_ELIGIBILITY_STATUSES,
        exclusion_reason_options=FULLTEXT_EXCLUSION_REASONS,
        decision_counts={},
        fulltext_management_record_count=0,
        fulltext_management_status_counts={},
        fulltext_management_registry_path=str(project_dir / "fulltext" / "fulltext_management_registry_v1.json") if project_dir is not None else "",
        fulltext_parse_manifest_path=str(project_dir / "fulltext" / "fulltext_parse_manifest_v1.json") if project_dir is not None else "",
        fulltext_parse_counts={},
        output_paths=_output_paths(project_dir) if project_dir is not None else {},
        criteria_summary_path=str(project_dir / "criteria" / "criteria_summary.md") if project_dir is not None else "",
        criteria_hints=(),
        warnings=(),
        testing_limitations=(
            "不自动下载 PDF；OCR 仅用于用户触发的本地全文文本获取，不自动提取、不自动筛选。",
            "Full-text eligibility 是人工 workflow；不会自动删除文献。",
            "Developer Preview：final included studies 用于后续 extraction 测试链路，不代表投稿级最终纳入清单。",
        ),
        title_zh=FULLTEXT_ELIGIBILITY_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=FULLTEXT_ELIGIBILITY_DESCRIPTION_ZH,
        status_option_labels_zh=tuple(FULLTEXT_STATUS_ZH.get(item, item) for item in FULLTEXT_ELIGIBILITY_STATUSES),
        decision_count_labels_zh={"total": "总数"},
    )


def fulltext_eligibility_state_from_project(
    project_dir: Path,
    *,
    service: FullTextEligibilityService | None = None,
    fulltext_management_service: FullTextManagementService | None = None,
    fulltext_parsing_service: FullTextParsingService | None = None,
    criteria_service: CriteriaBuilderService | None = None,
) -> FullTextEligibilityPageState:
    project_dir = project_dir.expanduser().resolve()
    service = service or FullTextEligibilityService()
    fulltext_management_service = fulltext_management_service or FullTextManagementService()
    fulltext_parsing_service = fulltext_parsing_service or FullTextParsingService(fulltext_management=fulltext_management_service)
    criteria_service = criteria_service or CriteriaBuilderService()
    base = initial_fulltext_eligibility_state(project_dir)
    candidates = service.build_candidates_from_screening(project_dir)
    management_records = fulltext_management_service.list_records(project_dir)
    decision_counts = _decision_counts(candidates)
    management_counts = _management_counts(management_records)
    parse_counts = _parse_counts(fulltext_parsing_service.manifest_path(project_dir))
    warnings: list[str] = []
    if not candidates:
        warnings.append("empty_fulltext_candidate_list")
    if not (project_dir / "screening" / "title_abstract_decisions.json").exists() and not (project_dir / "screening" / "screening_decisions.json").exists():
        warnings.append("missing_screening_decisions")
    missing_pdf = len([candidate for candidate in candidates if candidate.pdf_status == "no_local_pdf"])
    if missing_pdf:
        warnings.append(f"missing_local_pdf_count:{missing_pdf}")
    return FullTextEligibilityPageState(
        title=base.title,
        description=base.description,
        status_label=base.status_label,
        input_summary=base.input_summary,
        output_summary=base.output_summary,
        next_step=base.next_step,
        empty_state=base.empty_state,
        warning_summary=base.warning_summary,
        candidate_count=len(candidates),
        candidates=candidates,
        status_options=base.status_options,
        exclusion_reason_options=base.exclusion_reason_options,
        decision_counts=decision_counts,
        fulltext_management_record_count=len(management_records),
        fulltext_management_status_counts=management_counts,
        fulltext_management_registry_path=str(fulltext_management_service.registry_path(project_dir)),
        fulltext_management_schema_version=FULLTEXT_MANAGEMENT_REGISTRY_SCHEMA_VERSION,
        fulltext_parse_manifest_path=str(fulltext_parsing_service.manifest_path(project_dir)),
        fulltext_parse_schema_version=FULLTEXT_PARSE_MANIFEST_SCHEMA_VERSION,
        fulltext_parse_counts=parse_counts,
        output_paths=_output_paths(project_dir),
        criteria_summary_path=str(project_dir / "criteria" / "criteria_summary.md"),
        criteria_hints=criteria_service.criteria_hints(project_dir, stage="full_text"),
        warnings=tuple(warnings),
        testing_limitations=base.testing_limitations,
        title_zh=FULLTEXT_ELIGIBILITY_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=FULLTEXT_ELIGIBILITY_DESCRIPTION_ZH,
        status_option_labels_zh=tuple(FULLTEXT_STATUS_ZH.get(item, item) for item in base.status_options),
        decision_count_labels_zh={key: FULLTEXT_STATUS_ZH.get(key, "总数" if key == "total" else key) for key in decision_counts},
    )


def _output_paths(project_dir: Path | None) -> dict[str, str]:
    if project_dir is None:
        return {}
    return {
            "fulltext_eligibility_decisions": str(project_dir / "fulltext" / "fulltext_eligibility_decisions.json"),
        "fulltext_management_registry": str(project_dir / "fulltext" / "fulltext_management_registry_v1.json"),
        "fulltext_parse_manifest": str(project_dir / "fulltext" / "fulltext_parse_manifest_v1.json"),
        "fulltext_exclusion_report": str(project_dir / "fulltext" / "fulltext_exclusion_report.csv"),
        "compatibility_exclusion_report": str(project_dir / "reports" / "full_text_exclusion_report.csv"),
        "final_included_studies": str(project_dir / "fulltext" / "final_included_studies.json"),
        "compatibility_fulltext_decisions": str(project_dir / "fulltext" / "fulltext_screening_decisions.json"),
    }


def _decision_counts(candidates: tuple[FullTextEligibilityCandidate, ...]) -> dict[str, int]:
    counts: dict[str, int] = {"total": len(candidates)}
    for candidate in candidates:
        counts[candidate.fulltext_status] = counts.get(candidate.fulltext_status, 0) + 1
    return counts


def _management_counts(records: tuple[object, ...]) -> dict[str, int]:
    counts = {"total": len(records)}
    for record in records:
        status = getattr(record, "fulltext_status", "needs_manual_retrieval")
        counts[status] = counts.get(status, 0) + 1
    for status in FULLTEXT_MANAGEMENT_STATUSES:
        counts.setdefault(status, 0)
    return counts


def _parse_counts(manifest_path: Path) -> dict[str, int]:
    if not manifest_path.exists():
        return {"total": 0, "parsed": 0, "parse_failed": 0}
    try:
        import json

        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {"total": 0, "parsed": 0, "parse_failed": 0}
    return {
        "total": int(payload.get("record_count", 0) or 0),
        "parsed": int(payload.get("parsed_count", 0) or 0),
        "parse_failed": int(payload.get("parse_failed_count", 0) or 0),
    }


try:
    from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFrame = QLabel = QVBoxLayout = QWidget = None


if QWidget is not None:

    class FullTextEligibilityPage(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._state = initial_fulltext_eligibility_state()
            root = QVBoxLayout(self)
            title = QLabel(f"{self._state.title_zh} · {self._state.status_label_zh}")
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description_zh)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label_zh} / {self._state.status_label}"))
            help_text = QLabel(
                "\n".join(
                    [
                        self._state.input_summary,
                        self._state.output_summary,
                        self._state.next_step,
                        self._state.warning_summary,
                    ]
                )
            )
            help_text.setWordWrap(True)
            root.addWidget(help_text)

else:

    class FullTextEligibilityPage:  # type: ignore[no-redef]
        pass
