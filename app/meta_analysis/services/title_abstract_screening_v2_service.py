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
TITLE_ABSTRACT_SCREENING_SUMMARY_SCHEMA_VERSION = "meta_title_abstract_screening_summary.v1"

DECISION_INCLUDE = "include"
DECISION_EXCLUDE = "exclude"
DECISION_UNCERTAIN = "uncertain"
DECISION_NEED_FULL_TEXT = "need_full_text"
DECISION_NEEDS_REVIEW = "needs_review"
DECISION_NOT_SCREENED = "not_screened"
DECISION_RESET_TO_UNSCREENED = "reset_to_unscreened"

SUGGESTED_DECISION_STATES = {
    DECISION_INCLUDE: "suggested_include",
    DECISION_EXCLUDE: "suggested_exclude",
    DECISION_UNCERTAIN: "suggested_uncertain",
    DECISION_NEED_FULL_TEXT: "suggested_need_full_text",
}

FINAL_EVIDENCE_STATES = ("user_accepted", "user_edited", "user_rejected", "confirmed")

EXCLUSION_REASON_LABELS_ZH = {
    "population_mismatch": "研究对象不符合",
    "intervention_or_exposure_mismatch": "干预/暴露不符合",
    "comparator_mismatch": "对照不符合",
    "outcome_mismatch": "结局不符合",
    "study_type_mismatch": "研究类型不符合",
    "duplicate": "重复文献",
    "non_original_research": "非原始研究",
    "full_text_unavailable": "全文不可获取",
    "language_or_access_issue": "语言或获取限制",
    "other": "其他",
}

EXCLUSION_REASON_ALIASES = {
    "wrong_population": "population_mismatch",
    "wrong population": "population_mismatch",
    "研究对象不符": "population_mismatch",
    "研究对象不符合": "population_mismatch",
    "wrong_intervention_exposure": "intervention_or_exposure_mismatch",
    "wrong_intervention_or_exposure": "intervention_or_exposure_mismatch",
    "wrong intervention / exposure": "intervention_or_exposure_mismatch",
    "干预或暴露不符": "intervention_or_exposure_mismatch",
    "干预/暴露不符合": "intervention_or_exposure_mismatch",
    "wrong_comparator": "comparator_mismatch",
    "wrong comparator": "comparator_mismatch",
    "对照不符": "comparator_mismatch",
    "对照不符合": "comparator_mismatch",
    "wrong_outcome": "outcome_mismatch",
    "wrong outcome": "outcome_mismatch",
    "结局不符": "outcome_mismatch",
    "结局不符合": "outcome_mismatch",
    "animal_study": "study_type_mismatch",
    "cell_study": "study_type_mismatch",
    "case_report": "study_type_mismatch",
    "protocol_only": "study_type_mismatch",
    "preprint_only": "study_type_mismatch",
    "研究类型不符合": "study_type_mismatch",
    "duplicate_publication": "duplicate",
    "重复发表": "duplicate",
    "重复文献": "duplicate",
    "review": "non_original_research",
    "meta_analysis": "non_original_research",
    "non_original_article": "non_original_research",
    "non-original article": "non_original_research",
    "非原始研究": "non_original_research",
    "full_text_unavailable": "full_text_unavailable",
    "full text unavailable": "full_text_unavailable",
    "全文不可得": "full_text_unavailable",
    "全文不可获取": "full_text_unavailable",
    "non_target_language": "language_or_access_issue",
    "non-english / 非目标语言": "language_or_access_issue",
    "非目标语言": "language_or_access_issue",
    "语言或获取限制": "language_or_access_issue",
    "other": "other",
    "其他": "other",
}

LEGACY_DECISION_MAP = {
    DECISION_INCLUDE: "included",
    DECISION_EXCLUDE: "excluded",
    DECISION_UNCERTAIN: "maybe",
    DECISION_NEED_FULL_TEXT: "maybe",
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


@dataclass(frozen=True)
class ScreeningSummaryCounts:
    imported_total: int
    after_dedup_total: int
    title_abstract_unscreened: int
    title_abstract_included: int
    title_abstract_excluded: int
    title_abstract_uncertain: int
    full_text_needed: int
    full_text_included: int
    full_text_excluded: int
    output_path: str = ""

    def to_dict(self) -> dict[str, int | str]:
        return {
            "schema_version": TITLE_ABSTRACT_SCREENING_SUMMARY_SCHEMA_VERSION,
            "imported_total": self.imported_total,
            "after_dedup_total": self.after_dedup_total,
            "title_abstract_unscreened": self.title_abstract_unscreened,
            "title_abstract_included": self.title_abstract_included,
            "title_abstract_excluded": self.title_abstract_excluded,
            "title_abstract_uncertain": self.title_abstract_uncertain,
            "full_text_needed": self.full_text_needed,
            "full_text_included": self.full_text_included,
            "full_text_excluded": self.full_text_excluded,
            "output_path": self.output_path,
        }


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

    def summary_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "screening" / "title_abstract_screening_summary_v1.json"

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
        reason_code = _normalize_exclusion_reason(exclusion_reason_code or exclusion_reason_text)
        if normalized == DECISION_EXCLUDE and not reason_code:
            return self._decision_error(project_dir, project_id, record_id, normalized, "unsupported exclusion reason.")
        queue_record = self._require_queue_record(project_dir, record_id)
        existing = self._load_decisions(project_dir)
        before = next((item for item in existing if str(item.get("record_id", "")) == record_id), {})
        if normalized == DECISION_NOT_SCREENED:
            decisions = [item for item in existing if str(item.get("record_id", "")) != record_id]
            self._write_decision_logs(project_dir, project_id=project_id, decisions=decisions)
            self._audit_log.record_event(
                project_dir,
                event_type="screening_decision",
                project_id=project_id,
                actor=actor.strip(),
                target_type="title_abstract_screening",
                target_id=record_id,
                source_path=str(self.queue_path(project_dir).relative_to(project_dir)),
                output_path=str(self.decisions_path(project_dir).relative_to(project_dir)),
                summary="Title/abstract screening v2 decision reset to unscreened.",
                details={"decision": normalized, "auto_decided": False},
            )
            self._governance.record_user_confirmation(
                project_dir,
                project_id=project_id,
                action="edit",
                actor=actor.strip(),
                target_type="title_abstract_screening",
                target_id=record_id,
                before=dict(before),
                after={"record_id": record_id, "decision": normalized, "evidence_state": "user_edited"},
                source_suggestion_id=source_suggestion_id.strip(),
                metadata={"decision": normalized, "stage": "title_abstract_screening"},
            )
            self.write_screening_summary(project_dir)
            return TitleAbstractDecisionResult(
                success=True,
                project_id=project_id,
                record_id=record_id,
                decision=normalized,
                decisions_path=str(self.decisions_path(project_dir)),
                compatible_decisions_path=str(self.compatible_decisions_path(project_dir)),
                message=f"Title/abstract screening decision reset: {record_id} -> not_screened.",
                decision_counts=_decision_counts(decisions),
            )
        evidence_state = _evidence_state(source_suggestion_id=source_suggestion_id, notes=notes, exclusion_reason_code=reason_code)
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
            "database_source": str(queue_record.get("database_source", "")),
            "dedup_status": str(queue_record.get("dedup_status", "")),
            "decision": normalized,
            "legacy_decision": LEGACY_DECISION_MAP[normalized],
            "screening_status": "reviewer_decided" if normalized in {DECISION_INCLUDE, DECISION_EXCLUDE, DECISION_UNCERTAIN, DECISION_NEED_FULL_TEXT} else "needs_review",
            "exclusion_reason_code": reason_code,
            "exclusion_reason_text": EXCLUSION_REASON_LABELS_ZH.get(reason_code, exclusion_reason_text.strip()),
            "notes": notes.strip(),
            "actor": actor.strip(),
            "source_suggestion_id": source_suggestion_id.strip(),
            "created_at": _now(),
            "auto_decided": False,
            "ai_suggestion_only": False,
            "evidence_state": evidence_state,
            "final_state_options": list(FINAL_EVIDENCE_STATES),
        }
        decisions = [item for item in existing if str(item.get("record_id", "")) != record_id]
        decisions.append(decision_payload)
        decisions_path = self._write_decision_logs(project_dir, project_id=project_id, decisions=decisions)
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
                "evidence_state": evidence_state,
            },
        )
        governance_action = {
            "confirmed": "confirm",
            "user_accepted": "accept",
            "user_edited": "edit",
            "user_rejected": "reject",
        }[evidence_state]
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
        self.write_screening_summary(project_dir)
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
        if normalized not in SUGGESTED_DECISION_STATES:
            raise ValueError("unsupported_title_abstract_screening_suggestion")
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
            "status": SUGGESTED_DECISION_STATES[normalized],
            "evidence_state": "suggested",
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

    def screening_summary(self, project_dir: Path) -> ScreeningSummaryCounts:
        project_dir = project_dir.expanduser().resolve()
        imported_total = len(self._library.list_records(project_dir))
        dedup_payload = _load_json(self._dedup.deduplicated_set_path(project_dir))
        queue_payload = self.load_queue(project_dir)
        queue_records = [dict(item) for item in queue_payload.get("queue_records", []) if isinstance(item, dict)]
        decisions = self._load_decisions(project_dir)
        after_dedup_total = _after_dedup_count(dedup_payload, fallback=len(queue_records) or imported_total)
        by_record = {str(item.get("record_id", "")): item for item in decisions if str(item.get("record_id", ""))}
        counts = {DECISION_INCLUDE: 0, DECISION_EXCLUDE: 0, DECISION_UNCERTAIN: 0, DECISION_NEED_FULL_TEXT: 0}
        for item in by_record.values():
            decision = _normalize_decision(str(item.get("decision", DECISION_NOT_SCREENED)))
            if decision in counts:
                counts[decision] += 1
        fulltext_included, fulltext_excluded = _fulltext_counts(project_dir)
        total_for_screening = len(queue_records) or after_dedup_total
        unscreened = max(total_for_screening - sum(counts.values()), 0)
        return ScreeningSummaryCounts(
            imported_total=imported_total,
            after_dedup_total=after_dedup_total,
            title_abstract_unscreened=unscreened,
            title_abstract_included=counts[DECISION_INCLUDE],
            title_abstract_excluded=counts[DECISION_EXCLUDE],
            title_abstract_uncertain=counts[DECISION_UNCERTAIN],
            full_text_needed=counts[DECISION_INCLUDE] + counts[DECISION_UNCERTAIN] + counts[DECISION_NEED_FULL_TEXT],
            full_text_included=fulltext_included,
            full_text_excluded=fulltext_excluded,
            output_path=str(self.summary_path(project_dir)),
        )

    def write_screening_summary(self, project_dir: Path) -> ScreeningSummaryCounts:
        summary = self.screening_summary(project_dir)
        _write_json(self.summary_path(project_dir), summary.to_dict())
        return summary

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

    def _write_decision_logs(self, project_dir: Path, *, project_id: str, decisions: list[dict[str, Any]]) -> Path:
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
                "evidence_state_options": list(FINAL_EVIDENCE_STATES),
            },
        )
        self._write_compatible_decisions(project_dir, decisions)
        return decisions_path

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
        "dedup_status": _text(record.get("dedup_status") or record.get("record_status") or "去重后待筛选"),
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
        "need_full_text": DECISION_NEED_FULL_TEXT,
        "needs_full_text": DECISION_NEED_FULL_TEXT,
        "full_text_needed": DECISION_NEED_FULL_TEXT,
        "需要全文": DECISION_NEED_FULL_TEXT,
        "pending": DECISION_NEEDS_REVIEW,
        "needs_review": DECISION_NEEDS_REVIEW,
        "unscreened": DECISION_NOT_SCREENED,
        "not_screened": DECISION_NOT_SCREENED,
        "reset_to_unscreened": DECISION_NOT_SCREENED,
    }
    if normalized not in aliases:
        raise ValueError("unsupported_title_abstract_screening_decision")
    return aliases[normalized]


def _decision_counts(decisions: list[dict[str, Any]]) -> dict[str, int]:
    counts = {DECISION_INCLUDE: 0, DECISION_EXCLUDE: 0, DECISION_UNCERTAIN: 0, DECISION_NEED_FULL_TEXT: 0, DECISION_NEEDS_REVIEW: 0, DECISION_NOT_SCREENED: 0, "total": len(decisions)}
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


def _normalize_exclusion_reason(reason: str) -> str:
    value = reason.strip()
    if not value:
        return ""
    normalized = "_".join(value.lower().replace("/", " ").replace("-", " ").split())
    direct = normalized if normalized in EXCLUSION_REASON_LABELS_ZH else ""
    if direct:
        return direct
    return EXCLUSION_REASON_ALIASES.get(normalized, EXCLUSION_REASON_ALIASES.get(value.lower(), ""))


def _evidence_state(*, source_suggestion_id: str, notes: str, exclusion_reason_code: str) -> str:
    if not source_suggestion_id.strip():
        return "confirmed"
    if notes.strip() or exclusion_reason_code.strip():
        return "user_edited"
    return "user_accepted"


def _after_dedup_count(payload: dict[str, Any], *, fallback: int) -> int:
    if payload:
        for key in ("active_record_count", "deduplicated_count", "record_count"):
            value = payload.get(key)
            if isinstance(value, int):
                return value
        records = _records_from_payload(payload)
        if records:
            return len(records)
    return fallback


def _fulltext_counts(project_dir: Path) -> tuple[int, int]:
    payload = _load_json(project_dir / "fulltext" / "fulltext_eligibility_decisions.json")
    decisions = payload.get("decisions", []) if isinstance(payload, dict) else []
    included = 0
    excluded = 0
    for item in decisions:
        if not isinstance(item, dict):
            continue
        status = str(item.get("eligibility_status", "")).lower()
        if status in {"available_online", "local_pdf_linked", "local_pdf_copied", "included_for_extraction"}:
            included += 1
        if status in {"missing_full_text", "failed_to_access", "excluded_after_full_text_review"}:
            excluded += 1
    return included, excluded


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
