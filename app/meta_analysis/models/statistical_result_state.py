from __future__ import annotations

from dataclasses import dataclass, field, is_dataclass, asdict
from typing import Any


STATISTICAL_RESULT_STATE_NOT_RUN = "not_run"
STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN = "configured_not_run"
STATISTICAL_RESULT_STATE_TESTING_LEVEL = "testing_level"
STATISTICAL_RESULT_STATE_FAILED_VALIDATION = "failed_validation"
STATISTICAL_RESULT_STATE_COMPUTED = "computed"
STATISTICAL_RESULT_STATE_USER_REVIEWED = "user_reviewed"
STATISTICAL_RESULT_STATE_REPORT_READY = "report_ready"

STATISTICAL_RESULT_STATES = (
    STATISTICAL_RESULT_STATE_NOT_RUN,
    STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN,
    STATISTICAL_RESULT_STATE_TESTING_LEVEL,
    STATISTICAL_RESULT_STATE_FAILED_VALIDATION,
    STATISTICAL_RESULT_STATE_COMPUTED,
    STATISTICAL_RESULT_STATE_USER_REVIEWED,
    STATISTICAL_RESULT_STATE_REPORT_READY,
)

STATISTICAL_RESULT_STATE_LABELS_ZH = {
    STATISTICAL_RESULT_STATE_NOT_RUN: "尚未运行正式统计分析",
    STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN: "已配置但尚未运行正式统计分析",
    STATISTICAL_RESULT_STATE_TESTING_LEVEL: "测试级结果",
    STATISTICAL_RESULT_STATE_FAILED_VALIDATION: "输入校验失败",
    STATISTICAL_RESULT_STATE_COMPUTED: "已计算，待用户复核",
    STATISTICAL_RESULT_STATE_USER_REVIEWED: "用户已复核",
    STATISTICAL_RESULT_STATE_REPORT_READY: "可进入报告",
}

NON_RESULT_STATES = {
    STATISTICAL_RESULT_STATE_NOT_RUN,
    STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN,
}

FORMAL_COMPUTED_STATES = {
    STATISTICAL_RESULT_STATE_COMPUTED,
    STATISTICAL_RESULT_STATE_USER_REVIEWED,
    STATISTICAL_RESULT_STATE_REPORT_READY,
}

M10_COMPUTED_REQUIREMENTS = (
    "confirmed_analysis_plan",
    "confirmed_extraction_rows",
    "effect_measure_consistent",
    "numeric_fields_valid",
    "enough_included_studies",
    "reproducibility_metadata_present",
)


@dataclass(frozen=True)
class StatisticalResultGateResult:
    allowed: bool
    target_state: str
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    state_label_zh: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "target_state": self.target_state,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "state_label_zh": self.state_label_zh or statistical_result_state_label_zh(self.target_state),
        }


def validate_statistical_result_state(state: str) -> str:
    normalized = str(state or "").strip().lower()
    if normalized not in STATISTICAL_RESULT_STATES:
        raise ValueError(f"invalid_statistical_result_state:{state}")
    return normalized


def statistical_result_state_label_zh(state: str) -> str:
    normalized = normalize_statistical_result_state(state)
    return STATISTICAL_RESULT_STATE_LABELS_ZH.get(normalized, "未知状态")


def normalize_statistical_result_state(state: str | None, *, default: str = STATISTICAL_RESULT_STATE_TESTING_LEVEL) -> str:
    value = str(state or default).strip().lower()
    return value if value in STATISTICAL_RESULT_STATES else default


def result_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return dict(result)
    if is_dataclass(result):
        return asdict(result)
    payload: dict[str, Any] = {}
    for name in (
        "result_state",
        "testing_level",
        "production_grade",
        "formal_computed",
        "user_reviewed",
        "report_ready",
        "warnings",
        "validation_errors",
        "result_state_warnings",
    ):
        if hasattr(result, name):
            payload[name] = getattr(result, name)
    return payload


def get_statistical_result_state(result: Any) -> str:
    payload = result_payload(result)
    return normalize_statistical_result_state(str(payload.get("result_state") or ""))


def is_result_output_state(state: str) -> bool:
    return validate_statistical_result_state(state) not in NON_RESULT_STATES


def is_formal_computed_result(result: Any) -> bool:
    payload = result_payload(result)
    state = get_statistical_result_state(payload)
    if state not in FORMAL_COMPUTED_STATES:
        return False
    if bool(payload.get("testing_level", False)):
        return False
    return bool(payload.get("formal_computed", state in FORMAL_COMPUTED_STATES)) and not bool(payload.get("testing_level", False))


def requires_user_review(result: Any) -> bool:
    payload = result_payload(result)
    state = get_statistical_result_state(payload)
    return state == STATISTICAL_RESULT_STATE_COMPUTED and not bool(payload.get("user_reviewed", False))


def can_enter_report_ready_state(result: Any) -> StatisticalResultGateResult:
    payload = result_payload(result)
    state = get_statistical_result_state(payload)
    errors: list[str] = []
    if bool(payload.get("testing_level", False)):
        errors.append("testing_level_result_cannot_enter_report_ready")
    if state not in FORMAL_COMPUTED_STATES:
        errors.append("computed_result_required")
    if not (bool(payload.get("user_reviewed", False)) or state in {STATISTICAL_RESULT_STATE_USER_REVIEWED, STATISTICAL_RESULT_STATE_REPORT_READY}):
        errors.append("user_review_required")
    return StatisticalResultGateResult(
        allowed=not errors,
        target_state=STATISTICAL_RESULT_STATE_REPORT_READY,
        errors=tuple(errors),
        state_label_zh=statistical_result_state_label_zh(STATISTICAL_RESULT_STATE_REPORT_READY),
    )


def is_report_ready_result(result: Any) -> bool:
    payload = result_payload(result)
    return get_statistical_result_state(payload) == STATISTICAL_RESULT_STATE_REPORT_READY and can_enter_report_ready_state(payload).allowed


def blocks_formal_report_claim(result: Any) -> bool:
    return not is_report_ready_result(result)


def can_enter_computed_state(requirements: dict[str, Any] | None = None, *, warnings: list[str] | None = None) -> StatisticalResultGateResult:
    values = dict(requirements or {})
    errors = [f"{key}_required_for_computed_state" for key in M10_COMPUTED_REQUIREMENTS if not bool(values.get(key))]
    return StatisticalResultGateResult(
        allowed=not errors,
        target_state=STATISTICAL_RESULT_STATE_COMPUTED if not errors else STATISTICAL_RESULT_STATE_FAILED_VALIDATION,
        errors=tuple(errors),
        warnings=tuple(warnings or []),
        state_label_zh=statistical_result_state_label_zh(STATISTICAL_RESULT_STATE_COMPUTED if not errors else STATISTICAL_RESULT_STATE_FAILED_VALIDATION),
    )


def failed_validation_result_metadata(errors: list[str], warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "result_state": STATISTICAL_RESULT_STATE_FAILED_VALIDATION,
        "testing_level": False,
        "formal_computed": False,
        "user_reviewed": False,
        "report_ready": False,
        "validation_errors": list(errors),
        "result_state_warnings": list(warnings or []),
        "medical_conclusion_status": "not_generated",
    }


def testing_level_result_metadata(warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "result_state": STATISTICAL_RESULT_STATE_TESTING_LEVEL,
        "testing_level": True,
        "production_grade": False,
        "formal_computed": False,
        "user_reviewed": False,
        "report_ready": False,
        "medical_conclusion_status": "not_generated",
        "testing_level_notice": "Developer Preview / testing-level statistical output; not a formal computed result.",
        "result_state_warnings": list(warnings or ["testing_level_result_blocks_formal_report_claim"]),
    }
