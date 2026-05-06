from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.fulltext_service import FullTextService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


FULLTEXT_MANAGEMENT_REGISTRY_SCHEMA_VERSION = "meta_fulltext_management_registry.v1"
FULLTEXT_MANAGEMENT_RECORD_SCHEMA_VERSION = "meta_fulltext_management_record.v1"

FULLTEXT_STATUS_PDF_ATTACHED = "pdf_attached"
FULLTEXT_STATUS_LINK_AVAILABLE = "link_available"
FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE = "full_text_unavailable"
FULLTEXT_STATUS_NEEDS_MANUAL_RETRIEVAL = "needs_manual_retrieval"
FULLTEXT_STATUS_PARSED = "parsed"
FULLTEXT_STATUS_PARSE_FAILED = "parse_failed"

FULLTEXT_MANAGEMENT_STATUSES = (
    FULLTEXT_STATUS_PDF_ATTACHED,
    FULLTEXT_STATUS_LINK_AVAILABLE,
    FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE,
    FULLTEXT_STATUS_NEEDS_MANUAL_RETRIEVAL,
    FULLTEXT_STATUS_PARSED,
    FULLTEXT_STATUS_PARSE_FAILED,
)

FULLTEXT_LINK_TYPES = ("doi", "pmid", "pubmed", "publisher", "pmcid", "open_access", "manual")


@dataclass(frozen=True)
class FullTextManagementRecord:
    record_id: str
    title: str = ""
    doi: str = ""
    pmid: str = ""
    pmcid: str = ""
    source_screening_decision: str = ""
    fulltext_status: str = FULLTEXT_STATUS_NEEDS_MANUAL_RETRIEVAL
    pdf_path: str = ""
    links: tuple[dict[str, str], ...] = ()
    unavailable_reason: str = ""
    manual_notes: str = ""
    updated_by: str = ""
    created_at: str = ""
    updated_at: str = ""
    audit_refs: tuple[str, ...] = ()
    governance_refs: tuple[str, ...] = ()
    schema_version: str = FULLTEXT_MANAGEMENT_RECORD_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["links"] = [dict(item) for item in self.links]
        payload["audit_refs"] = list(self.audit_refs)
        payload["governance_refs"] = list(self.governance_refs)
        return payload


@dataclass(frozen=True)
class FullTextManagementResult:
    success: bool
    project_id: str
    record_id: str
    status: str
    output_path: str
    message: str
    record: FullTextManagementRecord | None = None
    warnings: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)


class FullTextManagementService:
    def __init__(
        self,
        *,
        fulltext_service: FullTextService | None = None,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)
        self._fulltext_service = fulltext_service or FullTextService(audit_log=self._audit_log)

    def registry_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "fulltext" / "fulltext_management_registry_v1.json"

    def build_registry_from_screening(self, project_dir: Path, *, project_id: str | None = None) -> FullTextManagementResult:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        screening_records = _load_screening_records(project_dir)
        existing = {record.record_id: record for record in self.list_records(project_dir)}
        now = _now()
        records: dict[str, FullTextManagementRecord] = dict(existing)
        for item in screening_records:
            decision = str(item.get("decision") or item.get("v2_decision") or "").lower()
            if decision not in {"included", "include", "maybe", "uncertain"}:
                continue
            record_id = _record_id(item)
            if not record_id or record_id in records:
                continue
            records[record_id] = FullTextManagementRecord(
                record_id=record_id,
                title=str(item.get("title") or ""),
                doi=str(item.get("doi") or ""),
                pmid=str(item.get("pmid") or ""),
                pmcid=str(item.get("pmcid") or ""),
                source_screening_decision=decision,
                fulltext_status=FULLTEXT_STATUS_NEEDS_MANUAL_RETRIEVAL,
                links=tuple(_source_links(item)),
                created_at=now,
                updated_at=now,
            )
        output_path = self._write_registry(project_dir, tuple(records.values()), project_id=project_id)
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_id,
            target_type="fulltext_management_registry",
            target_id="fulltext_management_registry_v1",
            source_path="screening/screening_decisions.json",
            output_path=str(output_path.relative_to(project_dir)),
            summary="Full-text management registry built from reviewer screening decisions.",
            details={"record_count": len(records), "auto_screening_decision": False, "auto_pdf_fetch": False},
        )
        self._governance.record_draft_created(
            project_dir,
            project_id=project_id,
            target_type="fulltext_management",
            target_id="fulltext_management_registry_v1",
            after={"record_count": len(records), "status": "needs_manual_retrieval"},
            metadata={"auto_screening_decision": False, "auto_pdf_fetch": False},
        )
        return FullTextManagementResult(
            success=True,
            project_id=project_id,
            record_id="",
            status="registry_built",
            output_path=str(output_path),
            message=f"Full-text management registry contains {len(records)} records.",
            details={"record_count": len(records)},
        )

    def list_records(self, project_dir: Path) -> tuple[FullTextManagementRecord, ...]:
        payload = _load_json(self.registry_path(project_dir))
        return tuple(_record_from_payload(item) for item in payload.get("records", []) if isinstance(item, dict))

    def get_record(self, project_dir: Path, record_id: str) -> FullTextManagementRecord | None:
        for record in self.list_records(project_dir):
            if record.record_id == record_id:
                return record
        return None

    def attach_pdf(
        self,
        project_dir: Path,
        *,
        record_id: str,
        source_file_path: str,
        actor: str,
        mode: str = "copy_to_project_library",
        notes: str = "",
    ) -> FullTextManagementResult:
        if not actor.strip():
            return self._error(project_dir, record_id, "reviewer actor is required.")
        fulltext = self._fulltext_service.attach_pdf(project_dir, record_id, source_file_path, mode=mode, notes=notes)
        return self._upsert_record(
            project_dir,
            record_id=record_id,
            actor=actor,
            updates={"fulltext_status": FULLTEXT_STATUS_PDF_ATTACHED, "pdf_path": fulltext.pdf_path, "manual_notes": notes},
            action_summary="Local PDF attached.",
        )

    def add_link(
        self,
        project_dir: Path,
        *,
        record_id: str,
        link_type: str,
        url: str,
        actor: str,
        notes: str = "",
    ) -> FullTextManagementResult:
        if link_type not in FULLTEXT_LINK_TYPES:
            return self._error(project_dir, record_id, "unsupported full-text link type.")
        if not url.strip():
            return self._error(project_dir, record_id, "full-text link url is required.")
        record = self.get_record(project_dir, record_id) or FullTextManagementRecord(record_id=record_id, created_at=_now())
        links = [dict(item) for item in record.links]
        links.append({"link_type": link_type, "url": url.strip()})
        return self._upsert_record(
            project_dir,
            record_id=record_id,
            actor=actor,
            updates={"fulltext_status": FULLTEXT_STATUS_LINK_AVAILABLE, "links": tuple(links), "manual_notes": notes},
            action_summary="Full-text link recorded.",
        )

    def mark_unavailable(
        self,
        project_dir: Path,
        *,
        record_id: str,
        reason: str,
        actor: str,
        notes: str = "",
    ) -> FullTextManagementResult:
        if not reason.strip():
            return self._error(project_dir, record_id, "full-text unavailable reason is required.")
        return self._upsert_record(
            project_dir,
            record_id=record_id,
            actor=actor,
            updates={"fulltext_status": FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE, "unavailable_reason": reason.strip(), "manual_notes": notes},
            action_summary="Full text marked unavailable.",
        )

    def update_status(
        self,
        project_dir: Path,
        *,
        record_id: str,
        status: str,
        actor: str,
        notes: str = "",
    ) -> FullTextManagementResult:
        if status not in FULLTEXT_MANAGEMENT_STATUSES:
            return self._error(project_dir, record_id, "unsupported full-text management status.")
        return self._upsert_record(project_dir, record_id=record_id, actor=actor, updates={"fulltext_status": status, "manual_notes": notes}, action_summary=f"Full-text status changed to {status}.")

    def _upsert_record(
        self,
        project_dir: Path,
        *,
        record_id: str,
        actor: str,
        updates: dict[str, Any],
        action_summary: str,
    ) -> FullTextManagementResult:
        project_dir = project_dir.expanduser().resolve()
        if not actor.strip():
            return self._error(project_dir, record_id, "reviewer actor is required.")
        records = {record.record_id: record for record in self.list_records(project_dir)}
        before = records.get(record_id)
        now = _now()
        base = before or FullTextManagementRecord(record_id=record_id, created_at=now)
        data = base.to_dict()
        data.update(updates)
        data["updated_by"] = actor.strip()
        data["updated_at"] = now
        data["created_at"] = base.created_at or now
        if isinstance(data.get("links"), list):
            data["links"] = tuple(dict(item) for item in data["links"])
        updated = _record_from_payload(data)
        records[record_id] = updated
        output_path = self._write_registry(project_dir, tuple(records.values()), project_id=project_dir.name)
        self._audit_log.record_event(
            project_dir,
            event_type="fulltext_status_changed",
            project_id=project_dir.name,
            actor=actor.strip(),
            target_type="fulltext_management_record",
            target_id=record_id,
            source_path=str(self.registry_path(project_dir).relative_to(project_dir)),
            output_path=str(output_path.relative_to(project_dir)),
            summary=action_summary,
            details={"before": before.to_dict() if before else {}, "after": updated.to_dict(), "auto_screening_decision": False},
        )
        self._governance.record_user_confirmation(
            project_dir,
            project_id=project_dir.name,
            action="confirm",
            actor=actor.strip(),
            target_type="fulltext_management",
            target_id=record_id,
            before=before.to_dict() if before else {},
            after=updated.to_dict(),
            metadata={"status": updated.fulltext_status, "does_not_write_fulltext_screening_decision": True},
        )
        return FullTextManagementResult(
            success=True,
            project_id=project_dir.name,
            record_id=record_id,
            status=updated.fulltext_status,
            output_path=str(output_path),
            message=action_summary,
            record=updated,
        )

    def _write_registry(self, project_dir: Path, records: tuple[FullTextManagementRecord, ...], *, project_id: str) -> Path:
        path = self.registry_path(project_dir)
        _write_json(
            path,
            {
                "schema_version": FULLTEXT_MANAGEMENT_REGISTRY_SCHEMA_VERSION,
                "record_schema_version": FULLTEXT_MANAGEMENT_RECORD_SCHEMA_VERSION,
                "project_id": project_id,
                "updated_at": _now(),
                "record_count": len(records),
                "records": [record.to_dict() for record in records],
                "auto_pdf_fetch": False,
                "auto_fulltext_screening": False,
            },
        )
        return path

    def _error(self, project_dir: Path, record_id: str, message: str) -> FullTextManagementResult:
        project_dir = project_dir.expanduser().resolve()
        return FullTextManagementResult(
            success=False,
            project_id=project_dir.name,
            record_id=record_id,
            status="error",
            output_path=str(self.registry_path(project_dir)),
            message=message,
            warnings=(message,),
        )


def _load_screening_records(project_dir: Path) -> list[dict[str, Any]]:
    for path in (
        project_dir / "screening" / "screening_decisions.json",
        project_dir / "screening" / "title_abstract_decisions_v2.json",
        project_dir / "screening" / "title_abstract_decisions.json",
    ):
        payload = _load_json(path)
        for key in ("screening_records", "records", "decisions"):
            records = payload.get(key)
            if isinstance(records, list) and records:
                return [dict(item) for item in records if isinstance(item, dict)]
    return []


def _source_links(item: dict[str, Any]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    doi = str(item.get("doi") or "").strip()
    pmid = str(item.get("pmid") or "").strip()
    pmcid = str(item.get("pmcid") or "").strip()
    if doi:
        links.append({"link_type": "doi", "url": f"https://doi.org/{doi}"})
    if pmid:
        links.append({"link_type": "pubmed", "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"})
    if pmcid:
        links.append({"link_type": "pmcid", "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/"})
    return links


def _record_id(item: dict[str, Any]) -> str:
    return str(item.get("record_id") or item.get("normalized_record_id") or item.get("screening_record_id") or "").strip()


def _record_from_payload(payload: dict[str, Any]) -> FullTextManagementRecord:
    return FullTextManagementRecord(
        record_id=str(payload.get("record_id", "")),
        title=str(payload.get("title", "")),
        doi=str(payload.get("doi", "")),
        pmid=str(payload.get("pmid", "")),
        pmcid=str(payload.get("pmcid", "")),
        source_screening_decision=str(payload.get("source_screening_decision", "")),
        fulltext_status=str(payload.get("fulltext_status", FULLTEXT_STATUS_NEEDS_MANUAL_RETRIEVAL)),
        pdf_path=str(payload.get("pdf_path", "")),
        links=tuple(dict(item) for item in payload.get("links", []) if isinstance(item, dict)),
        unavailable_reason=str(payload.get("unavailable_reason", "")),
        manual_notes=str(payload.get("manual_notes", "")),
        updated_by=str(payload.get("updated_by", "")),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        audit_refs=tuple(str(item) for item in payload.get("audit_refs", []) if str(item)),
        governance_refs=tuple(str(item) for item in payload.get("governance_refs", []) if str(item)),
        schema_version=str(payload.get("schema_version", FULLTEXT_MANAGEMENT_RECORD_SCHEMA_VERSION)),
    )


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
