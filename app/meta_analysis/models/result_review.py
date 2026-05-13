from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


RESULT_REVIEW_SCHEMA_VERSION = "meta_statistical_result_review.m13"

REVIEW_STATE_NOT_REVIEWED = "not_reviewed"
REVIEW_STATE_IN_REVIEW = "in_review"
REVIEW_STATE_ACCEPTED_FOR_REPORT = "accepted_for_report"
REVIEW_STATE_NEEDS_REVISION = "needs_revision"
REVIEW_STATE_REJECTED_FOR_REPORT = "rejected_for_report"

RESULT_REVIEW_STATES = (
    REVIEW_STATE_NOT_REVIEWED,
    REVIEW_STATE_IN_REVIEW,
    REVIEW_STATE_ACCEPTED_FOR_REPORT,
    REVIEW_STATE_NEEDS_REVISION,
    REVIEW_STATE_REJECTED_FOR_REPORT,
)

RESULT_REVIEW_LABELS_ZH = {
    REVIEW_STATE_NOT_REVIEWED: "尚未审核",
    REVIEW_STATE_IN_REVIEW: "审核中",
    REVIEW_STATE_ACCEPTED_FOR_REPORT: "接受进入报告草稿",
    REVIEW_STATE_NEEDS_REVISION: "需要修订",
    REVIEW_STATE_REJECTED_FOR_REPORT: "不纳入报告",
}

RESULT_REVIEW_PANEL_LABELS_ZH = (
    "统计结果审核",
    "尚未审核",
    "审核中",
    "接受进入报告草稿",
    "需要修订",
    "不纳入报告",
    "已确认查看警告",
    "申请报告就绪",
    "报告就绪",
    "阻止进入报告的原因",
)


@dataclass(frozen=True)
class StatisticalResultReview:
    schema_version: str = RESULT_REVIEW_SCHEMA_VERSION
    result_ref: str = "latest_pairwise_result"
    result_state: str = ""
    review_state: str = REVIEW_STATE_NOT_REVIEWED
    reviewer_role: str = "reviewer"
    reviewed_at: str = ""
    review_decision: str = ""
    review_notes: str = ""
    review_warnings_acknowledged: bool = False
    report_ready_requested: bool = False
    report_ready_granted: bool = False
    report_ready_blockers: list[str] = field(default_factory=list)
    audit_summary: dict[str, Any] = field(default_factory=dict)
    warnings_visible: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResultReviewTransition:
    success: bool
    review: StatisticalResultReview
    result_payload: dict[str, Any] = field(default_factory=dict)
    blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "review": self.review.to_dict(),
            "result_payload": dict(self.result_payload),
            "blockers": list(self.blockers),
        }


def validate_review_state(state: str) -> str:
    value = str(state or "").strip()
    if value not in RESULT_REVIEW_STATES:
        raise ValueError(f"invalid_result_review_state:{state}")
    return value


def result_review_label_zh(state: str) -> str:
    value = str(state or "").strip()
    return RESULT_REVIEW_LABELS_ZH.get(value, "未知审核状态")
