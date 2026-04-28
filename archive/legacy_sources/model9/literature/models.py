from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LiteratureProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ImportSourceKind(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"
    MANUAL = "manual"


class ImportFormatHint(StrEnum):
    UNKNOWN = "unknown"
    RIS = "ris"
    NBIB = "nbib"
    BIBTEX = "bibtex"
    CSV = "csv"
    MANUAL = "manual"


class ImportRecordStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportBatchStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScreeningDecision(StrEnum):
    PENDING = "pending"
    INCLUDED = "included"
    EXCLUDED = "excluded"
    MAYBE = "maybe"


class ScreeningStage(StrEnum):
    TITLE_ABSTRACT_SCREENING = "title_abstract_screening"
    FULL_TEXT_SCREENING = "full_text_screening"


@dataclass(slots=True)
class LiteratureProject:
    project_id: str
    name: str
    description: str = ""
    status: LiteratureProjectStatus = LiteratureProjectStatus.ACTIVE
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LiteratureProject":
        return cls(
            project_id=payload["project_id"],
            name=payload["name"],
            description=payload.get("description", ""),
            status=LiteratureProjectStatus(payload.get("status", LiteratureProjectStatus.ACTIVE.value)),
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
            tags=list(payload.get("tags", [])),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(slots=True)
class ImportRecord:
    import_id: str
    project_id: str
    source_path: str
    source_kind: ImportSourceKind = ImportSourceKind.FILE
    format_hint: ImportFormatHint = ImportFormatHint.UNKNOWN
    status: ImportRecordStatus = ImportRecordStatus.PENDING
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    discovered_count: int = 0
    imported_count: int = 0
    note: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition(
        self,
        status: ImportRecordStatus,
        note: str = "",
        *,
        discovered_count: int | None = None,
        imported_count: int | None = None,
    ) -> None:
        self.status = status
        self.note = note
        if discovered_count is not None:
            self.discovered_count = discovered_count
        if imported_count is not None:
            self.imported_count = imported_count
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "import_id": self.import_id,
            "project_id": self.project_id,
            "source_path": self.source_path,
            "source_kind": self.source_kind.value,
            "format_hint": self.format_hint.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "discovered_count": self.discovered_count,
            "imported_count": self.imported_count,
            "note": self.note,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ImportRecord":
        return cls(
            import_id=payload["import_id"],
            project_id=payload["project_id"],
            source_path=payload["source_path"],
            source_kind=ImportSourceKind(payload.get("source_kind", ImportSourceKind.FILE.value)),
            format_hint=ImportFormatHint(payload.get("format_hint", ImportFormatHint.UNKNOWN.value)),
            status=ImportRecordStatus(payload.get("status", ImportRecordStatus.PENDING.value)),
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
            discovered_count=int(payload.get("discovered_count", 0)),
            imported_count=int(payload.get("imported_count", 0)),
            note=payload.get("note", ""),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(slots=True)
class ImportBatch:
    batch_id: str
    project_id: str
    source_type: ImportSourceKind
    input_path: str
    format_hint: ImportFormatHint = ImportFormatHint.UNKNOWN
    status: ImportBatchStatus = ImportBatchStatus.PENDING
    total_records: int = 0
    imported_records: int = 0
    failed_records: int = 0
    warning_count: int = 0
    error_message: str = ""
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def mark_running(self) -> None:
        now = utc_now()
        self.status = ImportBatchStatus.RUNNING
        self.started_at = now
        self.finished_at = None
        self.error_message = ""
        self.updated_at = now

    def mark_completed(
        self,
        *,
        total_records: int,
        imported_records: int,
        failed_records: int = 0,
        warning_count: int = 0,
    ) -> None:
        now = utc_now()
        self.status = ImportBatchStatus.COMPLETED
        self.total_records = total_records
        self.imported_records = imported_records
        self.failed_records = failed_records
        self.warning_count = warning_count
        self.error_message = ""
        self.finished_at = now
        self.updated_at = now

    def mark_failed(self, error_message: str) -> None:
        now = utc_now()
        self.status = ImportBatchStatus.FAILED
        self.error_message = error_message
        self.finished_at = now
        self.updated_at = now

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "project_id": self.project_id,
            "source_type": self.source_type.value,
            "input_path": self.input_path,
            "format_hint": self.format_hint.value,
            "status": self.status.value,
            "total_records": self.total_records,
            "imported_records": self.imported_records,
            "failed_records": self.failed_records,
            "warning_count": self.warning_count,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ImportBatch":
        started_at = payload.get("started_at")
        finished_at = payload.get("finished_at")
        return cls(
            batch_id=payload["batch_id"],
            project_id=payload["project_id"],
            source_type=ImportSourceKind(payload["source_type"]),
            input_path=payload["input_path"],
            format_hint=ImportFormatHint(payload.get("format_hint", ImportFormatHint.UNKNOWN.value)),
            status=ImportBatchStatus(payload.get("status", ImportBatchStatus.PENDING.value)),
            total_records=int(payload.get("total_records", 0)),
            imported_records=int(payload.get("imported_records", 0)),
            failed_records=int(payload.get("failed_records", 0)),
            warning_count=int(payload.get("warning_count", 0)),
            error_message=payload.get("error_message", ""),
            started_at=datetime.fromisoformat(started_at) if started_at else None,
            finished_at=datetime.fromisoformat(finished_at) if finished_at else None,
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(slots=True)
class ParsedLiteratureRecord:
    batch_id: str
    project_id: str
    source: str
    record_id: str = ""
    source_record_id: str = ""
    title: str = ""
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    keywords: list[str] = field(default_factory=list)
    language: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "batch_id": self.batch_id,
            "project_id": self.project_id,
            "source": self.source,
            "source_record_id": self.source_record_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": list(self.authors),
            "journal": self.journal,
            "year": self.year,
            "doi": self.doi,
            "pmid": self.pmid,
            "keywords": list(self.keywords),
            "language": self.language,
            "raw_payload": dict(self.raw_payload),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ParsedLiteratureRecord":
        return cls(
            record_id=payload.get("record_id", ""),
            batch_id=payload["batch_id"],
            project_id=payload["project_id"],
            source=payload["source"],
            source_record_id=payload.get("source_record_id", ""),
            title=payload.get("title", ""),
            abstract=payload.get("abstract", ""),
            authors=list(payload.get("authors", [])),
            journal=payload.get("journal", ""),
            year=payload.get("year"),
            doi=payload.get("doi", ""),
            pmid=payload.get("pmid", ""),
            keywords=list(payload.get("keywords", [])),
            language=payload.get("language", ""),
            raw_payload=dict(payload.get("raw_payload", {})),
        )


@dataclass(slots=True)
class NormalizedLiteratureRecord:
    record_id: str
    batch_id: str
    project_id: str
    source: str
    source_record_id: str = ""
    title: str = ""
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    journal: str = ""
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    keywords: list[str] = field(default_factory=list)
    language: str = ""
    raw_payload: dict[str, Any] = field(default_factory=dict)
    title_normalized: str = ""
    doi_normalized: str = ""
    pmid_normalized: str = ""
    authors_normalized: list[str] = field(default_factory=list)
    journal_normalized: str = ""
    year_normalized: int | None = None
    source_trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "batch_id": self.batch_id,
            "project_id": self.project_id,
            "source": self.source,
            "source_record_id": self.source_record_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": list(self.authors),
            "journal": self.journal,
            "year": self.year,
            "doi": self.doi,
            "pmid": self.pmid,
            "keywords": list(self.keywords),
            "language": self.language,
            "raw_payload": dict(self.raw_payload),
            "title_normalized": self.title_normalized,
            "doi_normalized": self.doi_normalized,
            "pmid_normalized": self.pmid_normalized,
            "authors_normalized": list(self.authors_normalized),
            "journal_normalized": self.journal_normalized,
            "year_normalized": self.year_normalized,
            "source_trace": list(self.source_trace),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "NormalizedLiteratureRecord":
        return cls(
            record_id=payload["record_id"],
            batch_id=payload["batch_id"],
            project_id=payload["project_id"],
            source=payload["source"],
            source_record_id=payload.get("source_record_id", ""),
            title=payload.get("title", ""),
            abstract=payload.get("abstract", ""),
            authors=list(payload.get("authors", [])),
            journal=payload.get("journal", ""),
            year=payload.get("year"),
            doi=payload.get("doi", ""),
            pmid=payload.get("pmid", ""),
            keywords=list(payload.get("keywords", [])),
            language=payload.get("language", ""),
            raw_payload=dict(payload.get("raw_payload", {})),
            title_normalized=payload.get("title_normalized", ""),
            doi_normalized=payload.get("doi_normalized", ""),
            pmid_normalized=payload.get("pmid_normalized", ""),
            authors_normalized=list(payload.get("authors_normalized", [])),
            journal_normalized=payload.get("journal_normalized", ""),
            year_normalized=payload.get("year_normalized"),
            source_trace=list(payload.get("source_trace", [])),
        )


@dataclass(slots=True)
class DuplicateCandidateGroup:
    duplicate_group_id: str
    project_id: str
    candidate_record_ids: list[str]
    match_reason: str
    confidence: float
    suggested_primary_record_id: str
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "duplicate_group_id": self.duplicate_group_id,
            "project_id": self.project_id,
            "candidate_record_ids": list(self.candidate_record_ids),
            "match_reason": self.match_reason,
            "confidence": self.confidence,
            "suggested_primary_record_id": self.suggested_primary_record_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DuplicateCandidateGroup":
        return cls(
            duplicate_group_id=payload["duplicate_group_id"],
            project_id=payload["project_id"],
            candidate_record_ids=list(payload.get("candidate_record_ids", [])),
            match_reason=payload.get("match_reason", ""),
            confidence=float(payload.get("confidence", 0.0)),
            suggested_primary_record_id=payload.get("suggested_primary_record_id", ""),
            created_at=datetime.fromisoformat(payload["created_at"]),
        )


@dataclass(slots=True)
class DedupMergeResult:
    merge_result_id: str
    duplicate_group_id: str
    project_id: str
    primary_record_id: str
    merged_record: NormalizedLiteratureRecord
    merged_from_record_ids: list[str] = field(default_factory=list)
    field_sources: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "merge_result_id": self.merge_result_id,
            "duplicate_group_id": self.duplicate_group_id,
            "project_id": self.project_id,
            "primary_record_id": self.primary_record_id,
            "merged_record": self.merged_record.to_dict(),
            "merged_from_record_ids": list(self.merged_from_record_ids),
            "field_sources": dict(self.field_sources),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DedupMergeResult":
        return cls(
            merge_result_id=payload["merge_result_id"],
            duplicate_group_id=payload["duplicate_group_id"],
            project_id=payload["project_id"],
            primary_record_id=payload["primary_record_id"],
            merged_record=NormalizedLiteratureRecord.from_dict(payload["merged_record"]),
            merged_from_record_ids=list(payload.get("merged_from_record_ids", [])),
            field_sources=dict(payload.get("field_sources", {})),
            created_at=datetime.fromisoformat(payload["created_at"]),
        )


@dataclass(slots=True)
class ExclusionReason:
    reason_code: str
    label: str
    description: str
    applies_to_stage: ScreeningStage

    def to_dict(self) -> dict[str, Any]:
        return {
            "reason_code": self.reason_code,
            "label": self.label,
            "description": self.description,
            "applies_to_stage": self.applies_to_stage.value,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExclusionReason":
        return cls(
            reason_code=payload["reason_code"],
            label=payload["label"],
            description=payload.get("description", ""),
            applies_to_stage=ScreeningStage(payload["applies_to_stage"]),
        )


@dataclass(slots=True)
class ScreeningRecord:
    screening_record_id: str
    project_id: str
    source_record_id: str
    normalized_record_id: str
    stage: ScreeningStage
    decision: ScreeningDecision = ScreeningDecision.PENDING
    exclusion_reason_code: str = ""
    exclusion_reason_text: str = ""
    reviewer_id: str | None = None
    decided_at: datetime | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "screening_record_id": self.screening_record_id,
            "project_id": self.project_id,
            "source_record_id": self.source_record_id,
            "normalized_record_id": self.normalized_record_id,
            "stage": self.stage.value,
            "decision": self.decision.value,
            "exclusion_reason_code": self.exclusion_reason_code,
            "exclusion_reason_text": self.exclusion_reason_text,
            "reviewer_id": self.reviewer_id,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScreeningRecord":
        decided_at = payload.get("decided_at")
        return cls(
            screening_record_id=payload["screening_record_id"],
            project_id=payload["project_id"],
            source_record_id=payload.get("source_record_id", ""),
            normalized_record_id=payload["normalized_record_id"],
            stage=ScreeningStage(payload["stage"]),
            decision=ScreeningDecision(payload.get("decision", ScreeningDecision.PENDING.value)),
            exclusion_reason_code=payload.get("exclusion_reason_code", ""),
            exclusion_reason_text=payload.get("exclusion_reason_text", ""),
            reviewer_id=payload.get("reviewer_id"),
            decided_at=datetime.fromisoformat(decided_at) if decided_at else None,
            notes=payload.get("notes", ""),
        )
