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
        warning_summary="missing full text、failed access 或 excluded after full-text review 必须记录可读 exclusion reason；本页不下载 PDF、不做 OCR。",
        candidate_count=0,
        candidates=(),
        status_options=FULLTEXT_ELIGIBILITY_STATUSES,
        exclusion_reason_options=FULLTEXT_EXCLUSION_REASONS,
        decision_counts={},
        output_paths=_output_paths(project_dir) if project_dir is not None else {},
        criteria_summary_path=str(project_dir / "criteria" / "criteria_summary.md") if project_dir is not None else "",
        criteria_hints=(),
        warnings=(),
        testing_limitations=(
            "不自动下载 PDF、不做 OCR、不做机构代理登录或版权受限全文访问。",
            "Full-text eligibility 是人工 workflow；不会自动删除文献。",
            "Developer Preview：final included studies 用于后续 extraction 测试链路，不代表投稿级最终纳入清单。",
        ),
    )


def fulltext_eligibility_state_from_project(
    project_dir: Path,
    *,
    service: FullTextEligibilityService | None = None,
    criteria_service: CriteriaBuilderService | None = None,
) -> FullTextEligibilityPageState:
    project_dir = project_dir.expanduser().resolve()
    service = service or FullTextEligibilityService()
    criteria_service = criteria_service or CriteriaBuilderService()
    base = initial_fulltext_eligibility_state(project_dir)
    candidates = service.build_candidates_from_screening(project_dir)
    decision_counts = _decision_counts(candidates)
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
        output_paths=_output_paths(project_dir),
        criteria_summary_path=str(project_dir / "criteria" / "criteria_summary.md"),
        criteria_hints=criteria_service.criteria_hints(project_dir, stage="full_text"),
        warnings=tuple(warnings),
        testing_limitations=base.testing_limitations,
    )


def _output_paths(project_dir: Path | None) -> dict[str, str]:
    if project_dir is None:
        return {}
    return {
        "fulltext_eligibility_decisions": str(project_dir / "fulltext" / "fulltext_eligibility_decisions.json"),
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
            title = QLabel(self._state.title)
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label}"))
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
