from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.meta_analysis.models.pairwise_meta_executor import PairwiseMetaExecutorResult
from app.meta_analysis.models.result_review import (
    REVIEW_STATE_ACCEPTED_FOR_REPORT,
    REVIEW_STATE_IN_REVIEW,
    REVIEW_STATE_NEEDS_REVISION,
    REVIEW_STATE_NOT_REVIEWED,
    REVIEW_STATE_REJECTED_FOR_REPORT,
    ResultReviewTransition,
    StatisticalResultReview,
)
from app.meta_analysis.models.statistical_result_state import (
    STATISTICAL_RESULT_STATE_COMPUTED,
    STATISTICAL_RESULT_STATE_REPORT_READY,
    STATISTICAL_RESULT_STATE_USER_REVIEWED,
    can_enter_report_ready_state,
)
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.pairwise_meta_executor_service import PairwiseMetaExecutorService


class StatisticalResultReviewService:
    def __init__(
        self,
        *,
        pairwise_executor: PairwiseMetaExecutorService | None = None,
        audit_log: MetaAuditLogService | None = None,
    ) -> None:
        self._pairwise_executor = pairwise_executor or PairwiseMetaExecutorService()
        self._audit_log = audit_log or MetaAuditLogService()

    def review_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "pairwise_executor" / "latest_pairwise_meta_result_review.json"

    def load_review(self, project_dir: Path) -> StatisticalResultReview:
        path = self.review_path(project_dir)
        if not path.exists():
            latest = self._pairwise_executor.load_latest_result(project_dir)
            return self.default_review(latest)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return StatisticalResultReview()
        return StatisticalResultReview(**_known_review_fields(payload if isinstance(payload, dict) else {}))

    def default_review(self, result: PairwiseMetaExecutorResult | dict[str, Any] | None) -> StatisticalResultReview:
        payload = _result_payload(result)
        return StatisticalResultReview(
            result_ref=_safe_result_ref(payload),
            result_state=str(payload.get("result_state", "")),
            review_state=str(payload.get("review_state") or REVIEW_STATE_NOT_REVIEWED),
            reviewer_role=str(payload.get("reviewer_role") or "reviewer"),
            reviewed_at=str(payload.get("reviewed_at") or ""),
            review_decision=str(payload.get("review_decision") or ""),
            review_notes=str(payload.get("review_notes") or ""),
            review_warnings_acknowledged=bool(payload.get("review_warnings_acknowledged", False)),
            report_ready_requested=bool(payload.get("report_ready_requested", False)),
            report_ready_granted=bool(payload.get("report_ready_granted", False)),
            report_ready_blockers=list(payload.get("report_ready_blockers", [])) if isinstance(payload.get("report_ready_blockers"), list) else [],
            audit_summary=dict(payload.get("audit_summary", {})) if isinstance(payload.get("audit_summary"), dict) else {},
            warnings_visible=_visible_warnings(payload),
        )

    def start_review(
        self,
        project_dir: Path,
        result: PairwiseMetaExecutorResult | dict[str, Any] | None = None,
        *,
        reviewer_role: str = "reviewer",
        review_notes: str = "",
    ) -> ResultReviewTransition:
        payload = _result_payload(result or self._pairwise_executor.load_latest_result(project_dir))
        review = self._build_review(
            payload,
            review_state=REVIEW_STATE_IN_REVIEW,
            reviewer_role=reviewer_role,
            review_decision=REVIEW_STATE_IN_REVIEW,
            review_notes=review_notes,
            warnings_acknowledged=False,
            report_ready_requested=False,
            report_ready_granted=False,
            blockers=[],
            action="start_review",
        )
        self._persist(project_dir, review, payload=payload, actor=reviewer_role, action="start_review")
        return ResultReviewTransition(True, review, _safe_result_payload(payload), ())

    def accept_for_report(
        self,
        project_dir: Path,
        result: PairwiseMetaExecutorResult | dict[str, Any] | None = None,
        *,
        reviewer_role: str = "reviewer",
        review_notes: str = "",
        warnings_acknowledged: bool = False,
        report_ready_requested: bool = False,
    ) -> ResultReviewTransition:
        payload = _result_payload(result or self._pairwise_executor.load_latest_result(project_dir))
        blockers = _computed_review_blockers(payload, warnings_acknowledged=warnings_acknowledged)
        if blockers:
            review = self._build_review(
                payload,
                review_state=REVIEW_STATE_IN_REVIEW,
                reviewer_role=reviewer_role,
                review_decision=REVIEW_STATE_ACCEPTED_FOR_REPORT,
                review_notes=review_notes,
                warnings_acknowledged=warnings_acknowledged,
                report_ready_requested=report_ready_requested,
                report_ready_granted=False,
                blockers=blockers,
                action="accept_for_report_blocked",
            )
            self._persist(project_dir, review, payload=payload, actor=reviewer_role, action="accept_for_report_blocked")
            return ResultReviewTransition(False, review, _safe_result_payload(payload), tuple(blockers))
        updated = dict(payload)
        updated.update(
            {
                "result_state": STATISTICAL_RESULT_STATE_USER_REVIEWED,
                "user_reviewed": True,
                "report_ready": False,
                "review_state": REVIEW_STATE_ACCEPTED_FOR_REPORT,
                "reviewer_role": reviewer_role,
                "reviewed_at": _now(),
                "review_decision": REVIEW_STATE_ACCEPTED_FOR_REPORT,
                "review_notes": review_notes,
                "review_warnings_acknowledged": warnings_acknowledged,
                "report_ready_requested": report_ready_requested,
                "report_ready_granted": False,
                "report_ready_blockers": [],
                "audit_summary": _audit_summary("accept_for_report", payload, STATISTICAL_RESULT_STATE_USER_REVIEWED, warnings_acknowledged, []),
            }
        )
        review = self._review_from_payload(updated, action="accept_for_report")
        self._pairwise_executor.save_result(project_dir, PairwiseMetaExecutorResult(**_known_result_fields(updated)))
        self._persist(project_dir, review, payload=updated, actor=reviewer_role, action="accept_for_report")
        return ResultReviewTransition(True, review, _safe_result_payload(updated), ())

    def mark_needs_revision(
        self,
        project_dir: Path,
        result: PairwiseMetaExecutorResult | dict[str, Any] | None = None,
        *,
        reviewer_role: str = "reviewer",
        review_notes: str = "",
    ) -> ResultReviewTransition:
        return self._mark_non_report_decision(project_dir, result, reviewer_role=reviewer_role, review_notes=review_notes, review_state=REVIEW_STATE_NEEDS_REVISION, action="needs_revision")

    def reject_for_report(
        self,
        project_dir: Path,
        result: PairwiseMetaExecutorResult | dict[str, Any] | None = None,
        *,
        reviewer_role: str = "reviewer",
        review_notes: str = "",
    ) -> ResultReviewTransition:
        return self._mark_non_report_decision(project_dir, result, reviewer_role=reviewer_role, review_notes=review_notes, review_state=REVIEW_STATE_REJECTED_FOR_REPORT, action="rejected_for_report")

    def request_report_ready(
        self,
        project_dir: Path,
        result: PairwiseMetaExecutorResult | dict[str, Any] | None = None,
        *,
        reviewer_role: str = "reviewer",
    ) -> ResultReviewTransition:
        payload = _result_payload(result or self._pairwise_executor.load_latest_result(project_dir))
        review = self.load_review(project_dir)
        blockers = _report_ready_blockers(payload, review=review, requested=True)
        updated = dict(payload)
        updated.update(
            {
                "report_ready_requested": True,
                "report_ready_granted": False,
                "report_ready_blockers": blockers,
                "audit_summary": _audit_summary("request_report_ready", payload, str(payload.get("result_state", "")), review.review_warnings_acknowledged, blockers),
            }
        )
        updated_review = StatisticalResultReview(
            **{
                **review.to_dict(),
                "result_state": str(updated.get("result_state", "")),
                "report_ready_requested": True,
                "report_ready_granted": False,
                "report_ready_blockers": blockers,
                "audit_summary": dict(updated.get("audit_summary", {})),
            }
        )
        self._pairwise_executor.save_result(project_dir, PairwiseMetaExecutorResult(**_known_result_fields(updated)))
        self._persist(project_dir, updated_review, payload=updated, actor=reviewer_role, action="request_report_ready")
        return ResultReviewTransition(not blockers, updated_review, _safe_result_payload(updated), tuple(blockers))

    def grant_report_ready(
        self,
        project_dir: Path,
        result: PairwiseMetaExecutorResult | dict[str, Any] | None = None,
        *,
        reviewer_role: str = "reviewer",
    ) -> ResultReviewTransition:
        payload = _result_payload(result or self._pairwise_executor.load_latest_result(project_dir))
        review = self.load_review(project_dir)
        blockers = _report_ready_blockers(payload, review=review, requested=bool(payload.get("report_ready_requested", False) or review.report_ready_requested))
        if blockers:
            blocked_review = StatisticalResultReview(
                **{
                    **review.to_dict(),
                    "result_state": str(payload.get("result_state", "")),
                    "report_ready_granted": False,
                    "report_ready_blockers": blockers,
                    "audit_summary": _audit_summary("grant_report_ready_blocked", payload, str(payload.get("result_state", "")), review.review_warnings_acknowledged, blockers),
                }
            )
            self._persist(project_dir, blocked_review, payload=payload, actor=reviewer_role, action="grant_report_ready_blocked")
            return ResultReviewTransition(False, blocked_review, _safe_result_payload(payload), tuple(blockers))
        updated = dict(payload)
        updated.update(
            {
                "result_state": STATISTICAL_RESULT_STATE_REPORT_READY,
                "user_reviewed": True,
                "report_ready": True,
                "review_state": REVIEW_STATE_ACCEPTED_FOR_REPORT,
                "review_decision": REVIEW_STATE_ACCEPTED_FOR_REPORT,
                "report_ready_requested": True,
                "report_ready_granted": True,
                "report_ready_blockers": [],
                "audit_summary": _audit_summary("grant_report_ready", payload, STATISTICAL_RESULT_STATE_REPORT_READY, review.review_warnings_acknowledged, []),
            }
        )
        updated_review = self._review_from_payload(updated, action="grant_report_ready")
        self._pairwise_executor.save_result(project_dir, PairwiseMetaExecutorResult(**_known_result_fields(updated)))
        self._persist(project_dir, updated_review, payload=updated, actor=reviewer_role, action="grant_report_ready")
        return ResultReviewTransition(True, updated_review, _safe_result_payload(updated), ())

    def _mark_non_report_decision(
        self,
        project_dir: Path,
        result: PairwiseMetaExecutorResult | dict[str, Any] | None,
        *,
        reviewer_role: str,
        review_notes: str,
        review_state: str,
        action: str,
    ) -> ResultReviewTransition:
        payload = _result_payload(result or self._pairwise_executor.load_latest_result(project_dir))
        updated = dict(payload)
        updated.update(
            {
                "review_state": review_state,
                "reviewer_role": reviewer_role,
                "reviewed_at": _now(),
                "review_decision": review_state,
                "review_notes": review_notes,
                "report_ready_requested": False,
                "report_ready_granted": False,
                "report_ready": False,
                "report_ready_blockers": [f"review_state:{review_state}"],
                "audit_summary": _audit_summary(action, payload, str(payload.get("result_state", "")), bool(payload.get("review_warnings_acknowledged", False)), [f"review_state:{review_state}"]),
            }
        )
        review = self._review_from_payload(updated, action=action)
        if payload:
            self._pairwise_executor.save_result(project_dir, PairwiseMetaExecutorResult(**_known_result_fields(updated)))
        self._persist(project_dir, review, payload=updated, actor=reviewer_role, action=action)
        return ResultReviewTransition(True, review, _safe_result_payload(updated), tuple(updated["report_ready_blockers"]))

    def _build_review(
        self,
        payload: dict[str, Any],
        *,
        review_state: str,
        reviewer_role: str,
        review_decision: str,
        review_notes: str,
        warnings_acknowledged: bool,
        report_ready_requested: bool,
        report_ready_granted: bool,
        blockers: list[str],
        action: str,
    ) -> StatisticalResultReview:
        return StatisticalResultReview(
            result_ref=_safe_result_ref(payload),
            result_state=str(payload.get("result_state", "")),
            review_state=review_state,
            reviewer_role=reviewer_role or "reviewer",
            reviewed_at=_now(),
            review_decision=review_decision,
            review_notes=review_notes,
            review_warnings_acknowledged=warnings_acknowledged,
            report_ready_requested=report_ready_requested,
            report_ready_granted=report_ready_granted,
            report_ready_blockers=blockers,
            audit_summary=_audit_summary(action, payload, str(payload.get("result_state", "")), warnings_acknowledged, blockers),
            warnings_visible=_visible_warnings(payload),
        )

    def _review_from_payload(self, payload: dict[str, Any], *, action: str) -> StatisticalResultReview:
        return StatisticalResultReview(
            result_ref=_safe_result_ref(payload),
            result_state=str(payload.get("result_state", "")),
            review_state=str(payload.get("review_state") or REVIEW_STATE_NOT_REVIEWED),
            reviewer_role=str(payload.get("reviewer_role") or "reviewer"),
            reviewed_at=str(payload.get("reviewed_at") or _now()),
            review_decision=str(payload.get("review_decision") or ""),
            review_notes=str(payload.get("review_notes") or ""),
            review_warnings_acknowledged=bool(payload.get("review_warnings_acknowledged", False)),
            report_ready_requested=bool(payload.get("report_ready_requested", False)),
            report_ready_granted=bool(payload.get("report_ready_granted", False)),
            report_ready_blockers=list(payload.get("report_ready_blockers", [])) if isinstance(payload.get("report_ready_blockers"), list) else [],
            audit_summary=dict(payload.get("audit_summary") or _audit_summary(action, payload, str(payload.get("result_state", "")), bool(payload.get("review_warnings_acknowledged", False)), [])),
            warnings_visible=_visible_warnings(payload),
        )

    def _persist(self, project_dir: Path, review: StatisticalResultReview, *, payload: dict[str, Any], actor: str, action: str) -> Path:
        path = self.review_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(review.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_dir.expanduser().resolve().name,
            actor=actor or "reviewer",
            target_type="statistical_result_review",
            target_id=review.result_ref,
            source_path="analysis/pairwise_executor/latest_pairwise_meta_result.json",
            output_path=str(path.relative_to(project_dir.expanduser().resolve())),
            summary=str(review.audit_summary.get("user_facing_summary", f"Statistical result review action: {action}")),
            details={
                "action": action,
                "previous_state": review.audit_summary.get("previous_state", ""),
                "new_state": review.audit_summary.get("new_state", ""),
                "warnings_acknowledged": review.review_warnings_acknowledged,
                "blockers": list(review.report_ready_blockers),
                "result_state": str(payload.get("result_state", "")),
            },
        )
        return path


def _computed_review_blockers(payload: dict[str, Any], *, warnings_acknowledged: bool) -> list[str]:
    blockers: list[str] = []
    if str(payload.get("result_state", "")) != STATISTICAL_RESULT_STATE_COMPUTED:
        blockers.append(f"computed_result_required:{payload.get('result_state', '') or 'missing'}")
    if payload.get("validation_errors"):
        blockers.append("validation_errors_must_be_resolved")
    if _visible_warnings(payload) and not warnings_acknowledged:
        blockers.append("warnings_must_be_acknowledged")
    if _critical_warnings(payload):
        blockers.append("critical_warnings_block_report_ready")
    return _dedupe(blockers)


def _report_ready_blockers(payload: dict[str, Any], *, review: StatisticalResultReview, requested: bool) -> list[str]:
    blockers: list[str] = []
    state = str(payload.get("result_state", ""))
    if state not in {STATISTICAL_RESULT_STATE_USER_REVIEWED, STATISTICAL_RESULT_STATE_REPORT_READY}:
        blockers.append(f"user_reviewed_result_required:{state or 'missing'}")
    if review.review_state != REVIEW_STATE_ACCEPTED_FOR_REPORT or review.review_decision != REVIEW_STATE_ACCEPTED_FOR_REPORT:
        blockers.append(f"accepted_for_report_review_required:{review.review_state}")
    if payload.get("validation_errors"):
        blockers.append("validation_errors_must_be_resolved")
    if _critical_warnings(payload):
        blockers.append("critical_warnings_block_report_ready")
    if not review.review_warnings_acknowledged and _visible_warnings(payload):
        blockers.append("warnings_must_be_acknowledged")
    if not requested:
        blockers.append("report_ready_request_required")
    gate = can_enter_report_ready_state({**payload, "user_reviewed": True, "testing_level": bool(payload.get("testing_level", False))})
    if not gate.allowed:
        blockers.extend(gate.errors)
    return _dedupe(blockers)


def _result_payload(result: PairwiseMetaExecutorResult | dict[str, Any] | None) -> dict[str, Any]:
    if result is None:
        return {}
    if isinstance(result, PairwiseMetaExecutorResult):
        return result.to_dict()
    return dict(result)


def _safe_result_payload(payload: dict[str, Any]) -> dict[str, Any]:
    safe_keys = {
        "result_state",
        "model_used",
        "effect_measure_type",
        "pooled_effect",
        "pooled_ci_lower",
        "pooled_ci_upper",
        "pooled_standard_error",
        "heterogeneity_summary",
        "warnings",
        "validation_errors",
        "review_state",
        "review_decision",
        "review_warnings_acknowledged",
        "report_ready_requested",
        "report_ready_granted",
        "report_ready_blockers",
        "user_reviewed",
        "report_ready",
    }
    return {key: payload[key] for key in safe_keys if key in payload}


def _safe_result_ref(payload: dict[str, Any]) -> str:
    if not payload:
        return "latest_pairwise_result"
    model = str(payload.get("model_used") or "fixed_effect")
    effect = str(payload.get("effect_measure_type") or "effect")
    included = len(payload.get("included_studies", [])) if isinstance(payload.get("included_studies"), list) else 0
    return f"{model}:{effect}:studies-{included}"


def _known_result_fields(payload: dict[str, Any]) -> dict[str, Any]:
    names = set(PairwiseMetaExecutorResult.__dataclass_fields__.keys())
    return {name: payload[name] for name in names if name in payload}


def _known_review_fields(payload: dict[str, Any]) -> dict[str, Any]:
    names = set(StatisticalResultReview.__dataclass_fields__.keys())
    return {name: payload[name] for name in names if name in payload}


def _visible_warnings(payload: dict[str, Any]) -> list[str]:
    return [str(item) for item in payload.get("warnings", []) if str(item)] if isinstance(payload.get("warnings"), list) else []


def _critical_warnings(payload: dict[str, Any]) -> list[str]:
    critical: list[str] = []
    for warning in _visible_warnings(payload):
        lowered = warning.lower()
        if lowered.startswith("critical") or "critical_warning" in lowered or "unresolved_critical" in lowered:
            critical.append(warning)
    return critical


def _audit_summary(action: str, before: dict[str, Any], new_state: str, warnings_acknowledged: bool, blockers: list[str]) -> dict[str, Any]:
    return {
        "action": action,
        "previous_state": str(before.get("result_state", "")),
        "new_state": new_state,
        "timestamp": _now(),
        "user_facing_summary": _user_facing_summary(action, new_state, blockers),
        "warnings_acknowledged": warnings_acknowledged,
        "blockers": list(blockers),
    }


def _user_facing_summary(action: str, new_state: str, blockers: list[str]) -> str:
    if blockers:
        return f"统计结果审核未完成：{'; '.join(blockers)}"
    if action == "grant_report_ready":
        return "统计结果已标记为报告就绪；仍为 Developer Preview / testing。"
    if action == "accept_for_report":
        return "统计结果已完成用户审核，接受进入报告草稿。"
    if action == "needs_revision":
        return "统计结果审核标记为需要修订。"
    if action == "rejected_for_report":
        return "统计结果审核标记为不纳入报告。"
    return f"统计结果审核状态已更新：{new_state}"


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
