from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService


class ResearchDecisionStatus(StrEnum):
    DRAFT = "draft"
    SUGGESTED = "suggested"
    USER_ACCEPTED = "user_accepted"
    USER_REJECTED = "user_rejected"
    USER_EDITED = "user_edited"
    CONFIRMED = "confirmed"


class ResearchDecisionAction(StrEnum):
    DRAFT_CREATED = "draft_created"
    SUGGESTION_CREATED = "suggestion_created"
    ACCEPT = "accept"
    REJECT = "reject"
    EDIT = "edit"
    CONFIRM = "confirm"


AUTONOMOUS_ENGINEERING_SCOPES = (
    "schema",
    "service",
    "adapter",
    "manifest",
    "audit",
    "ui_skeleton",
    "preview",
    "validation",
    "report_draft",
    "figure_output",
    "reproducibility_package",
    "boundary_tests",
)


HUMAN_CONFIRMATION_TARGETS = (
    "final_pico",
    "final_picos",
    "final_peco",
    "final_search_strategy",
    "literature_inclusion",
    "dedup_merge",
    "title_abstract_screening",
    "fulltext_screening",
    "data_extraction_final",
    "quality_assessment_score",
    "analysis_plan",
    "medical_interpretation",
    "discussion_conclusion",
)


_ACTION_TO_STATUS = {
    ResearchDecisionAction.DRAFT_CREATED.value: ResearchDecisionStatus.DRAFT.value,
    ResearchDecisionAction.SUGGESTION_CREATED.value: ResearchDecisionStatus.SUGGESTED.value,
    ResearchDecisionAction.ACCEPT.value: ResearchDecisionStatus.USER_ACCEPTED.value,
    ResearchDecisionAction.REJECT.value: ResearchDecisionStatus.USER_REJECTED.value,
    ResearchDecisionAction.EDIT.value: ResearchDecisionStatus.USER_EDITED.value,
    ResearchDecisionAction.CONFIRM.value: ResearchDecisionStatus.CONFIRMED.value,
}


@dataclass(frozen=True)
class ResearchGovernanceEvent:
    event_id: str
    project_id: str
    actor: str
    action: str
    target_type: str
    target_id: str
    status: str
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)
    source_suggestion_id: str = ""
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "meta_research_governance_event.v1"


class MetaResearchGovernanceService:
    def __init__(self, *, audit_log: MetaAuditLogService | None = None) -> None:
        self._audit_log = audit_log or MetaAuditLogService()

    def governance_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "audit" / "research_governance_log.jsonl"

    def record_draft_created(
        self,
        project_dir: Path,
        *,
        target_type: str,
        target_id: str,
        after: dict[str, Any],
        actor: str = "system",
        project_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResearchGovernanceEvent:
        return self.record_event(
            project_dir,
            action=ResearchDecisionAction.DRAFT_CREATED.value,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
            after=after,
            project_id=project_id,
            metadata=metadata,
        )

    def record_suggestion_created(
        self,
        project_dir: Path,
        *,
        target_type: str,
        target_id: str,
        after: dict[str, Any],
        source_suggestion_id: str = "",
        actor: str = "model",
        project_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResearchGovernanceEvent:
        return self.record_event(
            project_dir,
            action=ResearchDecisionAction.SUGGESTION_CREATED.value,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
            after=after,
            source_suggestion_id=source_suggestion_id,
            project_id=project_id,
            metadata=metadata,
        )

    def record_user_confirmation(
        self,
        project_dir: Path,
        *,
        action: str,
        actor: str,
        target_type: str,
        target_id: str,
        before: dict[str, Any],
        after: dict[str, Any],
        source_suggestion_id: str = "",
        project_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResearchGovernanceEvent:
        if action not in {
            ResearchDecisionAction.ACCEPT.value,
            ResearchDecisionAction.REJECT.value,
            ResearchDecisionAction.EDIT.value,
            ResearchDecisionAction.CONFIRM.value,
        }:
            raise ValueError(f"unsupported_user_confirmation_action:{action}")
        if not actor.strip():
            raise ValueError("user_confirmation_actor_required")
        return self.record_event(
            project_dir,
            action=action,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
            before=before,
            after=after,
            source_suggestion_id=source_suggestion_id,
            project_id=project_id,
            metadata=metadata,
        )

    def record_event(
        self,
        project_dir: Path,
        *,
        action: str,
        actor: str,
        target_type: str,
        target_id: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        source_suggestion_id: str = "",
        project_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ResearchGovernanceEvent:
        if action not in _ACTION_TO_STATUS:
            raise ValueError(f"unsupported_research_governance_action:{action}")
        if not target_type.strip():
            raise ValueError("target_type_required")
        if not target_id.strip():
            raise ValueError("target_id_required")
        project_dir = project_dir.expanduser().resolve()
        path = self.governance_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        event = ResearchGovernanceEvent(
            event_id=f"gov-{uuid4().hex[:12]}",
            project_id=project_id or project_dir.name,
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            status=_ACTION_TO_STATUS[action],
            before=dict(before or {}),
            after=dict(after or {}),
            source_suggestion_id=source_suggestion_id,
            created_at=_now(),
            metadata=dict(metadata or {}),
        )
        payload = asdict(event)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        self._audit_log.record_event(
            project_dir,
            event_type="research_governance_event",
            project_id=event.project_id,
            actor=event.actor,
            target_type=event.target_type,
            target_id=event.target_id,
            source_path="Meta research governance",
            output_path=str(path.relative_to(project_dir)),
            summary=f"{event.action}:{event.status}",
            details={
                "governance_event_id": event.event_id,
                "action": event.action,
                "status": event.status,
                "source_suggestion_id": event.source_suggestion_id,
                "before": event.before,
                "after": event.after,
                "metadata": event.metadata,
            },
        )
        return event

    def list_events(self, project_dir: Path) -> list[ResearchGovernanceEvent]:
        path = self.governance_path(project_dir)
        if not path.exists():
            return []
        events: list[ResearchGovernanceEvent] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            events.append(
                ResearchGovernanceEvent(
                    event_id=str(payload.get("event_id", "")),
                    project_id=str(payload.get("project_id", "")),
                    actor=str(payload.get("actor", "")),
                    action=str(payload.get("action", "")),
                    target_type=str(payload.get("target_type", "")),
                    target_id=str(payload.get("target_id", "")),
                    status=str(payload.get("status", "")),
                    before=dict(payload.get("before", {})),
                    after=dict(payload.get("after", {})),
                    source_suggestion_id=str(payload.get("source_suggestion_id", "")),
                    created_at=str(payload.get("created_at", "")),
                    metadata=dict(payload.get("metadata", {})),
                    schema_version=str(payload.get("schema_version", "meta_research_governance_event.v1")),
                )
            )
        return events

    def latest_event(self, project_dir: Path, *, target_type: str, target_id: str) -> ResearchGovernanceEvent | None:
        matches = [
            event
            for event in self.list_events(project_dir)
            if event.target_type == target_type and event.target_id == target_id
        ]
        return matches[-1] if matches else None

    def latest_status(self, project_dir: Path, *, target_type: str, target_id: str) -> str:
        event = self.latest_event(project_dir, target_type=target_type, target_id=target_id)
        return event.status if event is not None else ""

    def can_consume_confirmed(self, project_dir: Path, *, target_type: str, target_id: str) -> bool:
        return self.latest_status(project_dir, target_type=target_type, target_id=target_id) == ResearchDecisionStatus.CONFIRMED.value

    def assert_can_consume_confirmed(self, project_dir: Path, *, target_type: str, target_id: str) -> None:
        if not self.can_consume_confirmed(project_dir, target_type=target_type, target_id=target_id):
            raise ValueError(f"research_decision_not_confirmed:{target_type}:{target_id}")


def requires_human_confirmation(target_type: str) -> bool:
    return target_type in HUMAN_CONFIRMATION_TARGETS


def is_autonomous_engineering_scope(scope: str) -> bool:
    return scope in AUTONOMOUS_ENGINEERING_SCOPES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
