from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.adapters.duplicate_review_adapter import DuplicateReviewAdapter
from app.meta_analysis.search.pubmed_search_service import PubMedSearchExecution, PubMedSearchResult
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


PUBMED_CANDIDATE_PREVIEW_SCHEMA = "meta_pubmed_candidate_preview.v1"
PUBMED_CANDIDATE_SELECTION_SCHEMA = "meta_pubmed_candidate_selection.v1"
PUBMED_CANDIDATE_HANDOFF_SCHEMA = "meta_pubmed_candidate_handoff.v1"
LITERATURE_LIBRARY_SCHEMA = "meta_literature_library.v1"


@dataclass(frozen=True)
class PubMedLiteratureCandidate:
    candidate_id: str
    pmid: str
    doi: str
    title: str
    authors: tuple[str, ...]
    journal: str
    year: str
    abstract: str
    source_query: str
    search_execution_id: str
    selected: bool = False
    rejected: bool = False
    user_decision: str = "pending"
    decision_time: str = ""
    pmcid: str = ""
    publication_date: str = ""
    url: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["authors"] = list(self.authors)
        return payload


@dataclass(frozen=True)
class PubMedCandidatePreview:
    preview_id: str
    project_id: str
    search_execution_id: str
    source_query: str
    execution_report_path: str
    search_strategy_snapshot_path: str
    candidates: tuple[PubMedLiteratureCandidate, ...]
    created_at: str
    status: str = "preview_only"
    schema_version: str = PUBMED_CANDIDATE_PREVIEW_SCHEMA

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "preview_id": self.preview_id,
            "project_id": self.project_id,
            "search_execution_id": self.search_execution_id,
            "source_query": self.source_query,
            "execution_report_path": self.execution_report_path,
            "search_strategy_snapshot_path": self.search_strategy_snapshot_path,
            "created_at": self.created_at,
            "status": self.status,
            "candidate_count": len(self.candidates),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "auto_imported": False,
            "auto_screened": False,
            "prisma_status": "not_updated",
        }


@dataclass(frozen=True)
class PubMedCandidateSelectionResult:
    success: bool
    preview_id: str
    selected_count: int
    rejected_count: int
    pending_count: int
    output_path: str
    message: str
    candidates: tuple[PubMedLiteratureCandidate, ...] = ()
    error_count: int = 0


@dataclass(frozen=True)
class PubMedCandidateHandoffResult:
    success: bool
    preview_id: str
    import_batch_id: str
    selected_count: int
    rejected_count: int
    imported_count: int
    literature_records_path: str
    import_batch_path: str
    dedup_queue_path: str
    handoff_audit_path: str
    message: str
    imported_records: tuple[dict[str, Any], ...] = ()
    error_count: int = 0
    details: dict[str, Any] = field(default_factory=dict)


class PubMedCandidatesHandoffService:
    def __init__(
        self,
        *,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
        duplicate_adapter: DuplicateReviewAdapter | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._research_governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)
        self._duplicate_adapter = duplicate_adapter or DuplicateReviewAdapter()

    def create_candidates_preview(
        self,
        project_dir: Path,
        *,
        execution: PubMedSearchExecution,
        execution_report_path: str = "",
        search_strategy_snapshot_path: str = "",
        project_id: str | None = None,
    ) -> PubMedCandidatePreview:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        preview = PubMedCandidatePreview(
            preview_id=f"pubmedprev-{uuid4().hex[:12]}",
            project_id=project_id,
            search_execution_id=execution.search_execution_id,
            source_query=execution.query_used,
            execution_report_path=execution_report_path,
            search_strategy_snapshot_path=search_strategy_snapshot_path,
            candidates=tuple(
                _candidate_from_record(record, execution_id=execution.search_execution_id, index=index)
                for index, record in enumerate(execution.records, start=1)
            ),
            created_at=_now(),
        )
        path = self.preview_path(project_dir, preview.preview_id)
        _write_json(path, preview.to_dict())
        self._audit_log.record_event(
            project_dir,
            event_type="pubmed_candidate_preview_created",
            project_id=project_id,
            target_type="pubmed_candidate_preview",
            target_id=preview.preview_id,
            source_path=execution_report_path,
            output_path=str(path.relative_to(project_dir)),
            summary=f"PubMed candidate preview created: {len(preview.candidates)} candidates.",
            details={
                "search_execution_id": preview.search_execution_id,
                "auto_imported": False,
                "auto_screened": False,
                "prisma_status": "not_updated",
            },
        )
        for candidate in preview.candidates:
            self._research_governance.record_draft_created(
                project_dir,
                project_id=project_id,
                target_type="literature_inclusion",
                target_id=candidate.candidate_id,
                after=candidate.to_dict(),
                metadata={
                    "preview_id": preview.preview_id,
                    "search_execution_id": preview.search_execution_id,
                    "decision_required": True,
                    "auto_imported": False,
                },
            )
        return preview

    def select_candidates(
        self,
        project_dir: Path,
        *,
        preview_id: str,
        selected_candidate_ids: tuple[str, ...] | list[str],
        rejected_candidate_ids: tuple[str, ...] | list[str] = (),
        actor: str = "reviewer",
    ) -> PubMedCandidateSelectionResult:
        project_dir = project_dir.expanduser().resolve()
        preview = self.load_preview(project_dir, preview_id=preview_id)
        selected = _candidate_ids_from_inputs(preview.candidates, _clean_ids(selected_candidate_ids))
        rejected = _candidate_ids_from_inputs(preview.candidates, _clean_ids(rejected_candidate_ids))
        known = {candidate.candidate_id for candidate in preview.candidates}
        unknown = sorted((selected | rejected) - known)
        if unknown:
            return PubMedCandidateSelectionResult(
                success=False,
                preview_id=preview_id,
                selected_count=0,
                rejected_count=0,
                pending_count=len(preview.candidates),
                output_path="",
                message=f"Unknown candidate ids: {', '.join(unknown)}",
                error_count=1,
            )
        now = _now()
        updated_candidates: list[PubMedLiteratureCandidate] = []
        for candidate in preview.candidates:
            before = candidate.to_dict()
            if candidate.candidate_id in selected:
                updated = replace(candidate, selected=True, rejected=False, user_decision="selected", decision_time=now)
                action = "accept"
            elif candidate.candidate_id in rejected:
                updated = replace(candidate, selected=False, rejected=True, user_decision="rejected", decision_time=now)
                action = "reject"
            else:
                updated = replace(candidate, selected=False, rejected=False, user_decision="pending", decision_time="")
                action = ""
            updated_candidates.append(updated)
            if action:
                self._research_governance.record_user_confirmation(
                    project_dir,
                    project_id=preview.project_id,
                    action=action,
                    actor=actor,
                    target_type="literature_inclusion",
                    target_id=candidate.candidate_id,
                    before=before,
                    after=updated.to_dict(),
                    metadata={
                        "preview_id": preview.preview_id,
                        "search_execution_id": preview.search_execution_id,
                        "source": "pubmed_confirmed_candidates",
                    },
                )
                self._audit_log.record_event(
                    project_dir,
                    event_type="pubmed_candidate_decision",
                    project_id=preview.project_id,
                    actor=actor,
                    target_type="pubmed_literature_candidate",
                    target_id=candidate.candidate_id,
                    source_path=str(self.preview_path(project_dir, preview.preview_id).relative_to(project_dir)),
                    summary=f"PubMed candidate {updated.user_decision}.",
                    details={"preview_id": preview.preview_id, "pmid": updated.pmid, "decision": updated.user_decision},
                )
        selected_count = len([candidate for candidate in updated_candidates if candidate.selected])
        rejected_count = len([candidate for candidate in updated_candidates if candidate.rejected])
        pending_count = len(updated_candidates) - selected_count - rejected_count
        payload = {
            "schema_version": PUBMED_CANDIDATE_SELECTION_SCHEMA,
            "preview_id": preview.preview_id,
            "project_id": preview.project_id,
            "search_execution_id": preview.search_execution_id,
            "selected_count": selected_count,
            "rejected_count": rejected_count,
            "pending_count": pending_count,
            "actor": actor,
            "created_at": now,
            "candidates": [candidate.to_dict() for candidate in updated_candidates],
            "auto_imported": False,
            "auto_screened": False,
            "prisma_status": "not_updated",
        }
        path = self.selection_path(project_dir, preview_id)
        _write_json(path, payload)
        return PubMedCandidateSelectionResult(
            success=True,
            preview_id=preview_id,
            selected_count=selected_count,
            rejected_count=rejected_count,
            pending_count=pending_count,
            output_path=str(path),
            message=f"Candidate selection saved: {selected_count} selected, {rejected_count} rejected.",
            candidates=tuple(updated_candidates),
        )

    def import_selected_candidates(
        self,
        project_dir: Path,
        *,
        preview_id: str,
        selected_candidate_ids: tuple[str, ...] | list[str],
        rejected_candidate_ids: tuple[str, ...] | list[str] = (),
        actor: str = "reviewer",
    ) -> PubMedCandidateHandoffResult:
        project_dir = project_dir.expanduser().resolve()
        selection = self.select_candidates(
            project_dir,
            preview_id=preview_id,
            selected_candidate_ids=selected_candidate_ids,
            rejected_candidate_ids=rejected_candidate_ids,
            actor=actor,
        )
        if not selection.success:
            return PubMedCandidateHandoffResult(
                success=False,
                preview_id=preview_id,
                import_batch_id="",
                selected_count=0,
                rejected_count=0,
                imported_count=0,
                literature_records_path="",
                import_batch_path="",
                dedup_queue_path="",
                handoff_audit_path="",
                message=selection.message,
                error_count=selection.error_count,
            )
        selected = [candidate for candidate in selection.candidates if candidate.selected]
        if not selected:
            return PubMedCandidateHandoffResult(
                success=False,
                preview_id=preview_id,
                import_batch_id="",
                selected_count=0,
                rejected_count=selection.rejected_count,
                imported_count=0,
                literature_records_path="",
                import_batch_path="",
                dedup_queue_path="",
                handoff_audit_path="",
                message="No selected PubMed candidates to import.",
                error_count=1,
            )
        preview = self.load_preview(project_dir, preview_id=preview_id)
        batch_id = f"pubmedbatch-{uuid4().hex[:12]}"
        imported_records = [
            _normalized_record_from_candidate(
                candidate,
                project_id=preview.project_id,
                batch_id=batch_id,
                preview=preview,
                user_decision_event=f"literature_inclusion:{candidate.candidate_id}",
            )
            for candidate in selected
        ]
        literature_path = self._append_literature_records(project_dir, preview.project_id, imported_records)
        import_batch_path = self._append_import_batch(
            project_dir,
            project_id=preview.project_id,
            batch_id=batch_id,
            preview=preview,
            selected_count=selection.selected_count,
            rejected_count=selection.rejected_count,
            imported_count=len(imported_records),
        )
        dedup_queue_path = self._write_dedup_preparation(project_dir, preview.project_id, batch_id, imported_records)
        handoff_audit_path = self._write_handoff_audit(
            project_dir,
            preview=preview,
            batch_id=batch_id,
            selected_count=selection.selected_count,
            rejected_count=selection.rejected_count,
            imported_records=imported_records,
            literature_path=literature_path,
            dedup_queue_path=dedup_queue_path,
            actor=actor,
        )
        self._audit_log.record_event(
            project_dir,
            event_type="import_batch_created",
            project_id=preview.project_id,
            actor=actor,
            target_type="import_batch",
            target_id=batch_id,
            source_path=preview.execution_report_path,
            output_path=str(literature_path.relative_to(project_dir)),
            summary="PubMed confirmed candidates imported after reviewer selection.",
            details={
                "source_type": "pubmed_confirmed_candidates",
                "source_execution_id": preview.search_execution_id,
                "selected_count": selection.selected_count,
                "rejected_count": selection.rejected_count,
                "imported_count": len(imported_records),
                "screening_status": "not_started",
                "auto_screened": False,
            },
        )
        self._audit_log.record_event(
            project_dir,
            event_type="pubmed_candidate_handoff",
            project_id=preview.project_id,
            actor=actor,
            target_type="pubmed_candidate_handoff",
            target_id=batch_id,
            source_path=str(self.selection_path(project_dir, preview_id).relative_to(project_dir)),
            output_path=str(handoff_audit_path.relative_to(project_dir)),
            summary="PubMed candidate handoff confirmed by reviewer.",
            details={
                "preview_id": preview_id,
                "source_execution_id": preview.search_execution_id,
                "literature_records_path": str(literature_path.relative_to(project_dir)),
                "dedup_queue_path": str(dedup_queue_path.relative_to(project_dir)),
                "prisma_status": "not_updated",
            },
        )
        self._research_governance.record_user_confirmation(
            project_dir,
            project_id=preview.project_id,
            action="confirm",
            actor=actor,
            target_type="literature_inclusion",
            target_id=batch_id,
            before={"preview_id": preview_id, "selected_count": selection.selected_count, "status": "selected_not_imported"},
            after={
                "import_batch_id": batch_id,
                "imported_count": len(imported_records),
                "record_status": "imported_pending_dedup",
                "screening_status": "not_started",
                "dedup_status": "pending_review",
            },
            metadata={
                "source_type": "pubmed_confirmed_candidates",
                "source_execution_id": preview.search_execution_id,
                "prisma_status": "not_updated",
            },
        )
        return PubMedCandidateHandoffResult(
            success=True,
            preview_id=preview_id,
            import_batch_id=batch_id,
            selected_count=selection.selected_count,
            rejected_count=selection.rejected_count,
            imported_count=len(imported_records),
            literature_records_path=str(literature_path),
            import_batch_path=str(import_batch_path),
            dedup_queue_path=str(dedup_queue_path),
            handoff_audit_path=str(handoff_audit_path),
            message=f"Imported {len(imported_records)} selected PubMed candidates into literature library; screening not started.",
            imported_records=tuple(imported_records),
            details={
                "screening_status": "not_started",
                "auto_screened": False,
                "prisma_status": "not_updated",
            },
        )

    def load_preview(self, project_dir: Path, *, preview_id: str) -> PubMedCandidatePreview:
        payload = _load_json(self.preview_path(project_dir, preview_id))
        if not payload:
            raise ValueError(f"pubmed_candidate_preview_not_found:{preview_id}")
        return _preview_from_payload(payload)

    def preview_path(self, project_dir: Path, preview_id: str) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "pubmed_candidates" / f"{preview_id}_candidates_preview.json"

    def selection_path(self, project_dir: Path, preview_id: str) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "pubmed_candidates" / f"{preview_id}_candidate_selection.json"

    def _append_literature_records(self, project_dir: Path, project_id: str, imported_records: list[dict[str, Any]]) -> Path:
        path = project_dir / "literature" / "literature_records.json"
        payload = _load_json(path)
        existing = _records_from_payload(payload)
        seen = {str(record.get("record_id", "")) for record in existing}
        merged = [*existing]
        for record in imported_records:
            if str(record.get("record_id", "")) not in seen:
                merged.append(record)
        _write_json(
            path,
            {
                "schema_version": LITERATURE_LIBRARY_SCHEMA,
                "project_id": project_id,
                "updated_at": _now(),
                "record_count": len(merged),
                "records": merged,
            },
        )
        for record in imported_records:
            self._audit_log.record_event(
                project_dir,
                event_type="record_saved",
                project_id=project_id,
                target_type="literature_record",
                target_id=str(record.get("record_id", "")),
                source_path=str(record.get("source_file", "")),
                output_path=str(path.relative_to(project_dir)),
                summary="Selected PubMed candidate saved as normalized literature record.",
                details={"pmid": record.get("pmid", ""), "doi": record.get("doi", ""), "provenance": record.get("provenance", {})},
            )
        return path

    def _append_import_batch(
        self,
        project_dir: Path,
        *,
        project_id: str,
        batch_id: str,
        preview: PubMedCandidatePreview,
        selected_count: int,
        rejected_count: int,
        imported_count: int,
    ) -> Path:
        path = project_dir / "literature" / "import_batches.json"
        payload = _load_json(path)
        batches = payload if isinstance(payload, list) else list(payload.get("import_batches", [])) if isinstance(payload, dict) else []
        batches.append(
            {
                "schema_version": "meta_literature_import_batch.v1",
                "batch_id": batch_id,
                "project_id": project_id,
                "source_type": "pubmed_confirmed_candidates",
                "source_execution_id": preview.search_execution_id,
                "source_query": preview.source_query,
                "source_preview_id": preview.preview_id,
                "execution_report_path": preview.execution_report_path,
                "search_strategy_snapshot_path": preview.search_strategy_snapshot_path,
                "selected_count": selected_count,
                "rejected_count": rejected_count,
                "imported_count": imported_count,
                "record_status": "imported_pending_dedup",
                "screening_status": "not_started",
                "dedup_status": "pending_review",
                "created_at": _now(),
            }
        )
        _write_json(path, {"schema_version": "meta_literature_import_batches.v1", "project_id": project_id, "import_batches": batches})
        return path

    def _write_dedup_preparation(
        self,
        project_dir: Path,
        project_id: str,
        batch_id: str,
        imported_records: list[dict[str, Any]],
    ) -> Path:
        groups = self._duplicate_adapter.identify_duplicate_groups(project_id=project_id, records=imported_records)
        path = project_dir / "deduplication" / "pubmed_candidate_duplicate_groups.json"
        _write_json(
            path,
            {
                "schema_version": "meta_dedup_review_preparation.v1",
                "project_id": project_id,
                "batch_id": batch_id,
                "source_type": "pubmed_confirmed_candidates",
                "created_at": _now(),
                "status": "pending_reviewer_decision",
                "auto_merged": False,
                "screening_status": "not_started",
                "records": imported_records,
                "duplicate_groups": [_group_payload(group) for group in groups],
            },
        )
        for group in groups:
            self._audit_log.record_event(
                project_dir,
                event_type="duplicate_detected",
                project_id=project_id,
                target_type="duplicate_candidate_group",
                target_id=str(group.duplicate_group_id),
                source_path=str(path.relative_to(project_dir)),
                output_path=str(path.relative_to(project_dir)),
                summary=f"Duplicate candidate detected from PubMed handoff: {group.match_reason}",
                details={"record_ids": list(group.candidate_record_ids), "confidence": group.confidence, "auto_merged": False},
            )
        return path

    def _write_handoff_audit(
        self,
        project_dir: Path,
        *,
        preview: PubMedCandidatePreview,
        batch_id: str,
        selected_count: int,
        rejected_count: int,
        imported_records: list[dict[str, Any]],
        literature_path: Path,
        dedup_queue_path: Path,
        actor: str,
    ) -> Path:
        path = project_dir / "audit" / f"{batch_id}_pubmed_handoff_audit.json"
        _write_json(
            path,
            {
                "schema_version": PUBMED_CANDIDATE_HANDOFF_SCHEMA,
                "project_id": preview.project_id,
                "preview_id": preview.preview_id,
                "import_batch_id": batch_id,
                "source_type": "pubmed_confirmed_candidates",
                "source_execution_id": preview.search_execution_id,
                "actor": actor,
                "selected_count": selected_count,
                "rejected_count": rejected_count,
                "imported_count": len(imported_records),
                "literature_records_path": str(literature_path.relative_to(project_dir)),
                "dedup_queue_path": str(dedup_queue_path.relative_to(project_dir)),
                "screening_status": "not_started",
                "auto_screened": False,
                "auto_merged": False,
                "prisma_status": "not_updated",
                "created_at": _now(),
                "imported_record_ids": [str(record.get("record_id", "")) for record in imported_records],
            },
        )
        return path


def _candidate_from_record(record: PubMedSearchResult, *, execution_id: str, index: int) -> PubMedLiteratureCandidate:
    candidate_id = f"pcand-{record.pmid}" if record.pmid else f"pcand-{index}-{uuid4().hex[:8]}"
    return PubMedLiteratureCandidate(
        candidate_id=candidate_id,
        pmid=record.pmid,
        doi=record.doi,
        title=record.title,
        authors=tuple(record.authors),
        journal=record.journal,
        year=record.year,
        abstract=record.abstract,
        source_query=record.query_used,
        search_execution_id=execution_id,
        pmcid=record.pmcid,
        publication_date=record.publication_date,
        url=record.url,
    )


def _normalized_record_from_candidate(
    candidate: PubMedLiteratureCandidate,
    *,
    project_id: str,
    batch_id: str,
    preview: PubMedCandidatePreview,
    user_decision_event: str,
) -> dict[str, Any]:
    record_id = f"lit-pubmed-{candidate.pmid}" if candidate.pmid else f"lit-{uuid4().hex[:12]}"
    first_author = candidate.authors[0] if candidate.authors else ""
    provenance = {
        "source_type": "pubmed_confirmed_candidates",
        "database_source": "PubMed",
        "pubmed_execution_report_path": preview.execution_report_path,
        "search_strategy_snapshot": preview.search_strategy_snapshot_path,
        "candidate_preview_id": preview.preview_id,
        "candidate_id": candidate.candidate_id,
        "source_execution_id": preview.search_execution_id,
        "user_decision_event": user_decision_event,
    }
    return {
        "record_id": record_id,
        "project_id": project_id,
        "title": candidate.title,
        "abstract": candidate.abstract,
        "authors": list(candidate.authors),
        "authors_text": "; ".join(candidate.authors),
        "first_author": first_author,
        "corresponding_author": "",
        "journal": candidate.journal,
        "publication_title": candidate.journal,
        "year": candidate.year,
        "publication_date": candidate.publication_date,
        "date": candidate.publication_date or candidate.year,
        "doi": candidate.doi,
        "pmid": candidate.pmid,
        "pmcid": candidate.pmcid,
        "database_source": "PubMed",
        "source_database": "PubMed",
        "source": "pubmed_confirmed_candidates",
        "source_file": preview.execution_report_path,
        "source_query": candidate.source_query,
        "source_record_id": candidate.pmid,
        "record_status": "imported_pending_dedup",
        "import_batch_id": batch_id,
        "batch_id": batch_id,
        "provenance": provenance,
        "notes": "",
        "screening_status": "not_started",
        "dedup_status": "pending_review",
        "publication_type": "journal_article",
        "raw_extra": {"pubmed_candidate": candidate.to_dict()},
    }


def _preview_from_payload(payload: dict[str, Any]) -> PubMedCandidatePreview:
    return PubMedCandidatePreview(
        preview_id=str(payload.get("preview_id", "")),
        project_id=str(payload.get("project_id", "")),
        search_execution_id=str(payload.get("search_execution_id", "")),
        source_query=str(payload.get("source_query", "")),
        execution_report_path=str(payload.get("execution_report_path", "")),
        search_strategy_snapshot_path=str(payload.get("search_strategy_snapshot_path", "")),
        candidates=tuple(_candidate_from_payload(item) for item in payload.get("candidates", []) if isinstance(item, dict)),
        created_at=str(payload.get("created_at", "")),
        status=str(payload.get("status", "preview_only")),
        schema_version=str(payload.get("schema_version", PUBMED_CANDIDATE_PREVIEW_SCHEMA)),
    )


def _candidate_from_payload(payload: dict[str, Any]) -> PubMedLiteratureCandidate:
    return PubMedLiteratureCandidate(
        candidate_id=str(payload.get("candidate_id", "")),
        pmid=str(payload.get("pmid", "")),
        doi=str(payload.get("doi", "")),
        title=str(payload.get("title", "")),
        authors=tuple(str(item) for item in payload.get("authors", []) if str(item).strip()),
        journal=str(payload.get("journal", "")),
        year=str(payload.get("year", "")),
        abstract=str(payload.get("abstract", "")),
        source_query=str(payload.get("source_query", "")),
        search_execution_id=str(payload.get("search_execution_id", "")),
        selected=bool(payload.get("selected", False)),
        rejected=bool(payload.get("rejected", False)),
        user_decision=str(payload.get("user_decision", "pending")),
        decision_time=str(payload.get("decision_time", "")),
        pmcid=str(payload.get("pmcid", "")),
        publication_date=str(payload.get("publication_date", "")),
        url=str(payload.get("url", "")),
    )


def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("records", "literature_records", "imported_records"):
        value = payload.get(key)
        if isinstance(value, list):
            return [dict(item) for item in value if isinstance(item, dict)]
    return []


def _group_payload(group: Any) -> dict[str, Any]:
    payload = asdict(group)
    payload["group_id"] = payload.get("duplicate_group_id", "")
    payload["record_ids"] = list(payload.get("candidate_record_ids", []))
    payload["reason"] = payload.get("match_reason", "")
    payload.setdefault("status", "pending")
    return payload


def _clean_ids(values: tuple[str, ...] | list[str]) -> set[str]:
    return {str(value).strip() for value in values if str(value).strip()}


def _candidate_ids_from_inputs(candidates: tuple[PubMedLiteratureCandidate, ...], values: set[str]) -> set[str]:
    by_pmid = {candidate.pmid: candidate.candidate_id for candidate in candidates if candidate.pmid}
    by_candidate_id = {candidate.candidate_id: candidate.candidate_id for candidate in candidates}
    return {by_candidate_id.get(value) or by_pmid.get(value) or value for value in values}


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
