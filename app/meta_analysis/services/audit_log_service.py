from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


AUDIT_EVENT_TYPES = (
    "import_batch_created",
    "record_parsed",
    "field_sanitized",
    "record_normalized",
    "record_saved",
    "diagnostics_generated",
    "duplicate_detected",
    "duplicate_decision",
    "fulltext_status_changed",
    "screening_decision",
    "extraction_updated",
    "analysis_run_completed",
    "analysis_profile_config_saved",
    "task_lifecycle_changed",
    "research_governance_event",
    "pubmed_candidate_preview_created",
    "pubmed_candidate_decision",
    "pubmed_candidate_handoff",
    "report_exported",
)


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    project_id: str
    actor: str
    target_type: str
    target_id: str
    source_path: str
    output_path: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


class MetaAuditLogService:
    def audit_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "audit" / "audit_log.jsonl"

    def record_event(
        self,
        project_dir: Path,
        *,
        event_type: str,
        project_id: str | None = None,
        actor: str = "system",
        target_type: str = "",
        target_id: str = "",
        source_path: str = "",
        output_path: str = "",
        summary: str = "",
        details: dict[str, Any] | None = None,
    ) -> AuditEvent:
        if event_type not in AUDIT_EVENT_TYPES:
            raise ValueError(f"unsupported_audit_event_type:{event_type}")
        project_dir = project_dir.expanduser().resolve()
        path = self.audit_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        event = AuditEvent(
            event_id=f"audit-{uuid4().hex[:12]}",
            event_type=event_type,
            project_id=project_id or project_dir.name,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
            source_path=source_path,
            output_path=output_path,
            summary=summary,
            details=dict(details or {}),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")
        return event

    def list_events(self, project_dir: Path) -> list[AuditEvent]:
        path = self.audit_path(project_dir)
        if not path.exists():
            return []
        events: list[AuditEvent] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            events.append(
                AuditEvent(
                    event_id=str(payload.get("event_id", "")),
                    event_type=str(payload.get("event_type", "")),
                    project_id=str(payload.get("project_id", "")),
                    actor=str(payload.get("actor", "")),
                    target_type=str(payload.get("target_type", "")),
                    target_id=str(payload.get("target_id", "")),
                    source_path=str(payload.get("source_path", "")),
                    output_path=str(payload.get("output_path", "")),
                    summary=str(payload.get("summary", "")),
                    details=dict(payload.get("details", {})),
                    created_at=str(payload.get("created_at", "")),
                )
            )
        return events

    def export_review_log_jsonl(self, project_dir: Path, output_path: Path | None = None) -> Path:
        project_dir = project_dir.expanduser().resolve()
        target = output_path.expanduser().resolve() if output_path is not None else project_dir / "reports" / "review_log.jsonl"
        target.parent.mkdir(parents=True, exist_ok=True)
        source = self.audit_path(project_dir)
        target.write_text(source.read_text(encoding="utf-8") if source.exists() else "", encoding="utf-8")
        return target

    def export_review_log_csv(self, project_dir: Path, output_path: Path | None = None) -> Path:
        project_dir = project_dir.expanduser().resolve()
        target = output_path.expanduser().resolve() if output_path is not None else project_dir / "reports" / "review_log.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "event_id",
                    "event_type",
                    "project_id",
                    "actor",
                    "target_type",
                    "target_id",
                    "source_path",
                    "output_path",
                    "summary",
                    "created_at",
                ],
            )
            writer.writeheader()
            for event in self.list_events(project_dir):
                writer.writerow(
                    {
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "project_id": event.project_id,
                        "actor": event.actor,
                        "target_type": event.target_type,
                        "target_id": event.target_id,
                        "source_path": event.source_path,
                        "output_path": event.output_path,
                        "summary": event.summary,
                        "created_at": event.created_at,
                    }
                )
        return target
