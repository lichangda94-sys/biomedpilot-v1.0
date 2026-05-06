from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.ai_suggestion_service import AISuggestionService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.dedup_review_v2_service import DedupReviewV2Service
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


TITLE_ABSTRACT_SCREENING_QUEUE_SCHEMA_VERSION = "meta_title_abstract_screening_queue.v2"
TITLE_ABSTRACT_SCREENING_RECORD_SCHEMA_VERSION = "meta_title_abstract_screening_record.v2"
TITLE_ABSTRACT_SCREENING_DECISION_SCHEMA_VERSION = "meta_title_abstract_screening_decision.v2"
TITLE_ABSTRACT_SCREENING_DECISION_LOG_SCHEMA_VERSION = "meta_title_abstract_screening_decision_log.v2"
TITLE_ABSTRACT_SCREENING_SUGGESTION_SCHEMA_VERSION = "meta_title_abstract_screening_suggestion.v1"

DECISION_INCLUDE = "include"
DECISION_EXCLUDE = "exclude"
DECISION_UNCERTAIN = "uncertain"
DECISION_NEEDS_REVIEW = "needs_review"
DECISION_NOT_SCREENED = "not_screened"

LEGACY_DECISION_MAP = {
    DECISION_INCLUDE: "included",
    DECISION_EXCLUDE: "excluded",
    DECISION_UNCERTAIN: "maybe",
    DECISION_NEEDS_REVIEW: "pending",
    DECISION_NOT_SCREENED: "pending",
}

DEFAULT_EXCLUSION_REASONS = (
    "Review",
    "Meta-analysis",
    "Conference abstract",
    "Editorial",
    "Letter",
    "Comment",
    "Case report",
    "Animal study",
    "Cell study",
    "Non-original article",
    "Wrong population",
    "Wrong intervention / exposure",
    "Wrong comparator",
    "Wrong outcome",
    "Insufficient data",
    "Full text unavailable",
    "Duplicate publication",
    "Non-English / 非目标语言",
    "Protocol only",
    "Preprint only",
)


@dataclass(frozen=True)
class TitleAbstractQueueBuildResult:
    success: bool
    project_id: str
    source_type: str
    record_count: int
    output_path: str
    message: str
    warnings: tuple[str, ...] = ()
    records: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class TitleAbstractDecisionResult:
    success: bool
    project_id: str
    record_id: str
    decision: str
    decisions_path: str
    compatible_decisions_path: str
    message: str
    error_count: int = 0
    decision_counts: dict[str, int] = field(default_factory=dict)


class TitleAbstractScreeningV2Service:
    def __init__(
        self,
        *,
        literature_library: LiteratureLibraryService | None = None,
        dedup_review: DedupReviewV2Service | None = None,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
        ai_suggestions: AISuggestionService | None = None,
    ) -> None:
        self._library = literature_library or LiteratureLibraryService()
        self._dedup = dedup_review or DedupReviewV2Service(literature_library=self._library)
        self._audit_log = audit_log or MetaAuditLogService()
        self._governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)
        self._ai_suggestions = ai_suggestions or AISuggestionService(research_governance=self._governance)

    def queue_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "screening" / "title_abstract_queue_v2.json"

    def decisions_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "screening" / "title_abstract_decisions_v2.json"

    def compatible_decisions_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "screening" / "screening_decisions.json"

    def suggestion_queue_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "screening" / "title_abstract_ai_suggestions_v2.json"

    def build_queue(self, project_dir: Path, *, project_id: str | None = None) -> TitleAbstractQueueBuildResult:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        records, source_type, source_path, warnings = self._load_screening_source(project_dir)
        queue_records = tuple(_queue_record(record) for record in records)
        payload = {
            "schema_version": TITLE_ABSTRACT_SCREENING_QUEUE_SCHEMA_VERSION,
            "project_id": project_id,
            "source_type": source_type,
            "source_path": str(source_path.relative_to(project_dir)) if source_path else "",
            "created_at": _now(),
            "status": "preview_needs_reviewer_decision",
            "record_count": len(queue_records),
            "decision_status": "not_screened",
            "auto_screening_enabled": False,
            "auto_prisma_update": False,
            "warnings": list(warnings),
            "queue_records": [dict(record) for record in queue_records],
        }
        output_path = self.queue_path(project_dir)
        _write_json(output_path, payload)
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_id,
            target_type="title_abstract_screening_queue_v2",
            target_id="title_abstract_queue_v2",
            source_path=str(source_path.relative_to(project_dir)) if source_path else "",
            output_path=str(output_path.relative_to(project_dir)),
            summary="Title/abstract screening v2 queue created as preview only.",
            details={
                "schema_version": TITLE_ABSTRACT_SCREENING_QUEUE_SCHEMA_VERSION,
                "record_count": len(queue_records),
                "auto_screening_enabled": False,
                "auto_prisma_update": False,
            },
        )
        self._governance.record_draft_created(
            project_dir,
            project_id=project_id,
            target_type="title_abstract_screening",
            target_id="title_abstract_queue_v2",
            after={"record_count": len(queue_records), "status": "preview_needs_reviewer_decision"},
            metadata={"source_type": source_type, "auto_screening_enabled": False},
        )
        return TitleAbstractQueueBuildResult(
            success=True,
            project_id=project_id,
            source_type=source_type,
            record_count=len(queue_records),
            output_path=str(output_path),
            message=f"Title/abstract screening v2 queue created: {len(queue_records)} records require reviewer decisions.",
            warnings=warnings,
            records=queue_records,
        )

    def load_queue(self, project_dir: Path) -> dict[str, Any]:
        payload = _load_json(self.queue_path(project_dir))
        return payload if isinstance(payload, dict) else {}

    def save_decision(
        self,
        project_dir: Path,
        *,
        record_id: str,
        decision: str,
        actor: str,
        exclusion_reason_code: str = "",
        exclusion_reason_text: str = "",
        notes: str = "",
        source_suggestion_id: str = "",
    ) -> TitleAbstractDecisionResult:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_dir.name
        normalized = _normalize_decision(decision)
        if not actor.strip():
            return self._decision_error(project_dir, project_id, record_id, normalized, "reviewer actor is required.")
        if normalized == DECISION_EXCLUDE and not (exclusion_reason_code.strip() or exclusion_reason_text.strip()):
            return self._decision_error(project_dir, project_id, record_id, normalized, "exclude decision requires a structured exclusion reason.")
        queue_record = self._require_queue_record(project_dir, record_id)
        existing = self._load_decisions(project_dir)
        before = next((item for item in existing if str(item.get("record_id", "")) == record_id), {})
        decision_payload = {
            "schema_version": TITLE_ABSTRACT_SCREENING_DECISION_SCHEMA_VERSION,
            "decision_id": f"tascr-{uuid4().hex[:12]}",
            "record_id": record_id,
            "source_record_id": str(queue_record.get("source_record_id", "")),
            "title": str(queue_record.get("title", "")),
            "abstract": str(queue_record.get("abstract", "")),
            "authors": list(queue_record.get("authors", [])) if isinstance(queue_record.get("authors"), list) else [],
            "journal": str(queue_record.get("journal", "")),
            "year": str(queue_record.get("year", "")),
            "doi": str(queue_record.get("doi", "")),
            "pmid": str(queue_record.get("pmid", "")),
            "source_type": str(queue_record.get("source_type", "")),
            "decision": normalized,
            "legacy_decision": LEGACY_DECISION_MAP[normalized],
            "screening_status": "reviewer_decided" if normalized in {DECISION_INCLUDE, DECISION_EXCLUDE, DECISION_UNCERTAIN} else "needs_review",
            "exclusion_reason_code": exclusion_reason_code.strip(),
            "exclusion_reason_text": exclusion_reason_text.strip(),
            "notes": notes.strip(),
            "actor": actor.strip(),
            "source_suggestion_id": source_suggestion_id.strip(),
            "created_at": _now(),
            "auto_decided": False,
            "ai_suggestion_only": False,
        }
        decisions = [item for item in existing if str(item.get("record_id", "")) != record_id]
        decisions.append(decision_payload)
        decisions_path = self.decisions_path(project_dir)
        _write_json(
            decisions_path,
            {
                "schema_version": TITLE_ABSTRACT_SCREENING_DECISION_LOG_SCHEMA_VERSION,
                "project_id": project_id,
                "updated_at": _now(),
                "stage": "title_abstract_screening",
                "decision_counts": _decision_counts(decisions),
                "screening_records": decisions,
                "auto_screening_enabled": False,
            },
        )
        self._write_compatible_decisions(project_dir, decisions)
        self._audit_log.record_event(
            project_dir,
            event_type="screening_decision",
            project_id=project_id,
            actor=actor.strip(),
            target_type="title_abstract_screening",
            target_id=record_id,
            source_path=str(self.queue_path(project_dir).relative_to(project_dir)),
            output_path=str(decisions_path.relative_to(project_dir)),
            summary=f"Title/abstract screening v2 decision saved: {normalized}",
            details={
                "decision_id": decision_payload["decision_id"],
                "decision": normalized,
                "source_suggestion_id": source_suggestion_id.strip(),
                "exclusion_reason_code": exclusion_reason_code.strip(),
                "exclusion_reason_text": exclusion_reason_text.strip(),
                "auto_decided": False,
            },
        )
        governance_action = "confirm" if normalized in {DECISION_INCLUDE, DECISION_EXCLUDE, DECISION_UNCERTAIN} else "edit"
        self._governance.record_user_confirmation(
            project_dir,
            project_id=project_id,
            action=governance_action,
            actor=actor.strip(),
            target_type="title_abstract_screening",
            target_id=record_id,
            before=dict(before),
            after=decision_payload,
            source_suggestion_id=source_suggestion_id.strip(),
            metadata={"decision": normalized, "stage": "title_abstract_screening"},
        )
        return TitleAbstractDecisionResult(
            success=True,
            project_id=project_id,
            record_id=record_id,
            decision=normalized,
            decisions_path=str(decisions_path),
            compatible_decisions_path=str(self.compatible_decisions_path(project_dir)),
            message=f"Title/abstract screening decision saved: {record_id} -> {normalized}.",
            decision_counts=_decision_counts(decisions),
        )

    def create_screening_suggestion(
        self,
        project_dir: Path,
        *,
        record_id: str,
        suggested_decision: str,
        rationale: str,
        confidence: float,
        suggested_exclusion_reason: str = "",
        project_id: str | None = None,
    ) -> dict[str, Any]:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        queue_record = self._require_queue_record(project_dir, record_id)
        normalized = _normalize_decision(suggested_decision)
        suggestion = self._ai_suggestions.create_ai_suggestion(
            project_dir,
            project_id=project_id,
            target_type="screening_decision",
            target_id=record_id,
            suggestion_type="relevance_screening",
            suggested_value={
                "decision": normalized,
                "exclusion_reason": suggested_exclusion_reason.strip(),
                "title": queue_record.get("title", ""),
            },
            rationale=rationale,
            confidence=confidence,
        )
        payload = _load_json(self.suggestion_queue_path(project_dir))
        suggestions = [dict(item) for item in payload.get("suggestions", [])] if isinstance(payload, dict) else []
        row = {
            "schema_version": TITLE_ABSTRACT_SCREENING_SUGGESTION_SCHEMA_VERSION,
            "suggestion_id": suggestion.suggestion_id,
            "record_id": record_id,
            "suggested_decision": normalized,
            "suggested_exclusion_reason": suggested_exclusion_reason.strip(),
            "rationale": rationale,
            "confidence": max(0.0, min(1.0, float(confidence))),
            "created_at": suggestion.created_at,
            "status": "suggested",
            "requires_user_accept_reject_edit": True,
            "writes_final_decision": False,
        }
        suggestions.append(row)
        _write_json(
            self.suggestion_queue_path(project_dir),
            {
                "schema_version": "meta_title_abstract_screening_suggestion_queue.v1",
                "project_id": project_id,
                "updated_at": _now(),
                "suggestions": suggestions,
                "safety_note": "AI/model suggestions do not write final title/abstract screening decisions.",
            },
        )
        return row

    def _load_screening_source(self, project_dir: Path) -> tuple[list[dict[str, Any]], str, Path | None, tuple[str, ...]]:
        deduplicated_path = self._dedup.deduplicated_set_path(project_dir)
        if deduplicated_path.exists():
            payload = _load_json(deduplicated_path)
            return _records_from_payload(payload), "deduplicated_literature_v2", deduplicated_path, tuple(str(item) for item in payload.get("unresolved_group_ids", []))
        records_path = self._library.records_path(project_dir)
        records = self._library.list_records(project_dir)
        warnings = ("deduplicated_set_missing_using_literature_library",) if records else ("no_literature_records_available",)
        return records, "literature_library_v2", records_path if records_path.exists() else None, warnings

    def _require_queue_record(self, project_dir: Path, record_id: str) -> dict[str, Any]:
        payload = self.load_queue(project_dir)
        for record in payload.get("queue_records", []):
            if isinstance(record, dict) and str(record.get("record_id", "")) == record_id:
                return dict(record)
        raise ValueError(f"title_abstract_queue_record_not_found:{record_id}")

    def _load_decisions(self, project_dir: Path) -> list[dict[str, Any]]:
        payload = _load_json(self.decisions_path(project_dir))
        records = payload.get("screening_records", []) if isinstance(payload, dict) else []
        return [dict(item) for item in records if isinstance(item, dict)]

    def _write_compatible_decisions(self, project_dir: Path, decisions: list[dict[str, Any]]) -> None:
        compatible = []
        for item in decisions:
            compatible.append(
                {
                    **dict(item),
                    "decision": item.get("legacy_decision", LEGACY_DECISION_MAP.get(str(item.get("decision", "")), "pending")),
                    "v2_decision": item.get("decision", ""),
                    "screening_record_id": item.get("record_id", ""),
                    "normalized_record_id": item.get("record_id", ""),
                }
            )
        _write_json(
            self.compatible_decisions_path(project_dir),
            {
                "schema_version": "meta_title_abstract_screening_compatible_decisions.v1",
                "project_id": project_dir.name,
                "updated_at": _now(),
                "stage": "title_abstract_screening",
                "source_decisions_path": str(self.decisions_path(project_dir).relative_to(project_dir)),
                "screening_records": compatible,
                "decision_counts": _legacy_decision_counts(compatible),
            },
        )

    def _decision_error(self, project_dir: Path, project_id: str, record_id: str, decision: str, message: str) -> TitleAbstractDecisionResult:
        return TitleAbstractDecisionResult(
            success=False,
            project_id=project_id,
            record_id=record_id,
            decision=decision,
            decisions_path=str(self.decisions_path(project_dir)),
            compatible_decisions_path=str(self.compatible_decisions_path(project_dir)),
            message=message,
            error_count=1,
        )


def _queue_record(record: dict[str, Any]) -> dict[str, Any]:
    doi = _text(record.get("doi"))
    pmid = _text(record.get("pmid"))
    return {
        "schema_version": TITLE_ABSTRACT_SCREENING_RECORD_SCHEMA_VERSION,
        "record_id": _text(record.get("record_id")) or _text(record.get("source_record_id")),
        "source_record_id": _text(record.get("source_record_id")),
        "title": _text(record.get("title")),
        "abstract": _text(record.get("abstract")),
        "authors": _authors(record),
        "authors_text": _text(record.get("authors_text")) or "; ".join(_authors(record)),
        "journal": _text(record.get("journal") or record.get("publication_title")),
        "year": _text(record.get("year")),
        "doi": doi,
        "pmid": pmid,
        "source_type": _text(record.get("source_type") or record.get("source")),
        "database_source": _text(record.get("database_source") or record.get("source_database")),
        "source_links": [link for link in (_doi_link(doi), _pmid_link(pmid)) if link],
        "decision": DECISION_NOT_SCREENED,
        "screening_status": "needs_review",
        "reviewer_decision_required": True,
        "ai_suggestion_status": "not_requested",
        "created_at": _now(),
    }


def _normalize_decision(decision: str) -> str:
    normalized = decision.strip().lower()
    aliases = {
        "included": DECISION_INCLUDE,
        "include": DECISION_INCLUDE,
        "excluded": DECISION_EXCLUDE,
        "exclude": DECISION_EXCLUDE,
        "maybe": DECISION_UNCERTAIN,
        "uncertain": DECISION_UNCERTAIN,
        "pending": DECISION_NEEDS_REVIEW,
        "needs_review": DECISION_NEEDS_REVIEW,
        "not_screened": DECISION_NOT_SCREENED,
    }
    if normalized not in aliases:
        raise ValueError("unsupported_title_abstract_screening_decision")
    return aliases[normalized]


def _decision_counts(decisions: list[dict[str, Any]]) -> dict[str, int]:
    counts = {DECISION_INCLUDE: 0, DECISION_EXCLUDE: 0, DECISION_UNCERTAIN: 0, DECISION_NEEDS_REVIEW: 0, DECISION_NOT_SCREENED: 0, "total": len(decisions)}
    for item in decisions:
        decision = _normalize_decision(str(item.get("decision", DECISION_NEEDS_REVIEW)))
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def _legacy_decision_counts(decisions: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"pending": 0, "included": 0, "excluded": 0, "maybe": 0, "total": len(decisions)}
    for item in decisions:
        decision = str(item.get("decision") or "pending")
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    for key in ("records", "deduplicated_records", "literature_records"):
        value = payload.get(key)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
    return []


def _authors(record: dict[str, Any]) -> list[str]:
    value = record.get("authors")
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(";") if part.strip()]
    authors_text = _text(record.get("authors_text"))
    return [part.strip() for part in authors_text.split(";") if part.strip()] if authors_text else []


def _doi_link(doi: str) -> str:
    return f"https://doi.org/{doi}" if doi else ""


def _pmid_link(pmid: str) -> str:
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


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
