from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService


NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION = "meta_normalized_literature_record.v2"
LITERATURE_LIBRARY_SCHEMA_VERSION = "meta_literature_library.v2"
LITERATURE_IMPORT_BATCH_SCHEMA_VERSION = "meta_literature_import_batch.v2"
LITERATURE_IMPORT_BATCHES_SCHEMA_VERSION = "meta_literature_import_batches.v2"
LITERATURE_LIBRARY_MANIFEST_SCHEMA_VERSION = "meta_literature_library_manifest.v1"
LITERATURE_RECORD_AUDIT_SCHEMA_VERSION = "meta_literature_record_audit.v1"


NORMALIZED_RECORD_FIELDS = (
    "record_id",
    "title",
    "abstract",
    "authors",
    "first_author",
    "corresponding_author",
    "journal",
    "year",
    "publication_date",
    "doi",
    "pmid",
    "pmcid",
    "clinical_trial_id",
    "database_source",
    "source_type",
    "source_file",
    "source_query",
    "search_execution_id",
    "import_batch_id",
    "provenance",
    "raw_extra",
    "dedup_status",
    "screening_status",
    "full_text_status",
    "extraction_status",
    "quality_status",
    "record_status",
    "created_at",
    "updated_at",
    "audit_refs",
)


@dataclass(frozen=True)
class LiteratureLibraryImportResult:
    success: bool
    project_id: str
    import_batch_id: str
    source_type: str
    imported_count: int
    skipped_count: int
    duplicate_candidate_count: int
    records_path: str
    import_batches_path: str
    manifest_path: str
    record_audit_path: str
    diagnostics: dict[str, Any] = field(default_factory=dict)
    imported_records: tuple[dict[str, Any], ...] = ()
    skipped_record_ids: tuple[str, ...] = ()
    message: str = ""


class LiteratureLibraryService:
    def __init__(self, *, audit_log: MetaAuditLogService | None = None) -> None:
        self._audit_log = audit_log or MetaAuditLogService()

    def records_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "literature" / "literature_records.json"

    def import_batches_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "literature" / "import_batches.json"

    def manifest_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "literature" / "library_manifest.json"

    def record_audit_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "audit" / "literature_record_audit.jsonl"

    def import_records(
        self,
        project_dir: Path,
        *,
        project_id: str | None = None,
        raw_records: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        source_type: str,
        source_name: str = "",
        source_file: str = "",
        source_query: str = "",
        search_execution_id: str = "",
        import_batch_id: str | None = None,
        provenance_base: dict[str, Any] | None = None,
        governance_refs: tuple[str, ...] | list[str] = (),
        audit_refs: tuple[str, ...] | list[str] = (),
        diagnostics: dict[str, Any] | None = None,
    ) -> LiteratureLibraryImportResult:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        now = _now()
        import_batch_id = import_batch_id or f"batch-{uuid4().hex[:12]}"
        existing_records = self.list_records(project_dir)
        existing_ids = {str(record.get("record_id", "")) for record in existing_records}
        imported: list[dict[str, Any]] = []
        skipped: list[str] = []
        diagnostic_rows: list[dict[str, Any]] = []
        for raw_record in raw_records:
            normalized = self.normalize_record(
                raw_record,
                project_id=project_id,
                source_type=source_type,
                source_name=source_name,
                source_file=source_file,
                source_query=source_query,
                search_execution_id=search_execution_id,
                import_batch_id=import_batch_id,
                provenance_base=provenance_base,
                audit_refs=audit_refs,
                created_at=now,
            )
            record_id = str(normalized["record_id"])
            diagnostic_rows.append(_diagnostics_for_record(normalized))
            if record_id in existing_ids:
                skipped.append(record_id)
                continue
            existing_ids.add(record_id)
            imported.append(normalized)
        merged_records = [*existing_records, *imported]
        records_path = self.records_path(project_dir)
        _write_json(
            records_path,
            {
                "schema_version": LITERATURE_LIBRARY_SCHEMA_VERSION,
                "record_schema_version": NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION,
                "project_id": project_id,
                "updated_at": now,
                "record_count": len(merged_records),
                "records": merged_records,
            },
        )
        batch_payload = self._append_import_batch(
            project_dir,
            project_id=project_id,
            import_batch_id=import_batch_id,
            source_type=source_type,
            source_name=source_name,
            source_file=source_file,
            source_query=source_query,
            search_execution_id=search_execution_id,
            imported_count=len(imported),
            skipped_count=len(skipped),
            duplicate_candidate_count=int((diagnostics or {}).get("duplicate_candidate_count", 0)),
            diagnostics=_diagnostics_summary(diagnostic_rows, diagnostics or {}),
            governance_refs=tuple(str(item) for item in governance_refs),
            audit_refs=tuple(str(item) for item in audit_refs),
            created_at=now,
        )
        audit_path = self.record_audit_path(project_dir)
        for record in imported:
            audit_ref = self._append_record_audit(
                project_dir,
                project_id=project_id,
                record=record,
                import_batch_id=import_batch_id,
                source=source_type,
                action="imported",
                previous_status="",
                new_status=str(record.get("record_status", "")),
                actor="system",
            )
            record.setdefault("audit_refs", [])
            if audit_ref not in record["audit_refs"]:
                record["audit_refs"].append(audit_ref)
            self._audit_log.record_event(
                project_dir,
                event_type="record_saved",
                project_id=project_id,
                target_type="literature_record",
                target_id=str(record.get("record_id", "")),
                source_path=source_file,
                output_path=str(records_path.relative_to(project_dir)),
                summary="Normalized literature record saved.",
                details={
                    "schema_version": NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION,
                    "source_type": source_type,
                    "import_batch_id": import_batch_id,
                    "provenance": record.get("provenance", {}),
                },
            )
        if imported:
            _write_json(
                records_path,
                {
                    "schema_version": LITERATURE_LIBRARY_SCHEMA_VERSION,
                    "record_schema_version": NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION,
                    "project_id": project_id,
                    "updated_at": _now(),
                    "record_count": len(merged_records),
                    "records": merged_records,
                },
            )
        manifest_path = self.update_manifest(project_dir, project_id=project_id)
        return LiteratureLibraryImportResult(
            success=True,
            project_id=project_id,
            import_batch_id=import_batch_id,
            source_type=source_type,
            imported_count=len(imported),
            skipped_count=len(skipped),
            duplicate_candidate_count=int(batch_payload.get("duplicate_candidate_count", 0)),
            records_path=str(records_path),
            import_batches_path=str(self.import_batches_path(project_dir)),
            manifest_path=str(manifest_path),
            record_audit_path=str(audit_path),
            diagnostics=batch_payload["diagnostics"],
            imported_records=tuple(imported),
            skipped_record_ids=tuple(skipped),
            message=f"Imported {len(imported)} normalized literature records; skipped {len(skipped)} existing records.",
        )

    def normalize_record(
        self,
        raw_record: dict[str, Any],
        *,
        project_id: str,
        source_type: str,
        source_name: str = "",
        source_file: str = "",
        source_query: str = "",
        search_execution_id: str = "",
        import_batch_id: str,
        provenance_base: dict[str, Any] | None = None,
        audit_refs: tuple[str, ...] | list[str] = (),
        created_at: str | None = None,
    ) -> dict[str, Any]:
        created_at = created_at or _now()
        authors = _authors(raw_record)
        doi = _first_text(raw_record, "doi", "DOI")
        pmid = _first_text(raw_record, "pmid", "PMID")
        source_type = source_type or _first_text(raw_record, "source_type", "source") or "unknown"
        source_name = source_name or _first_text(raw_record, "database_source", "source_database", "source") or source_type
        provenance = {
            "schema_version": "meta_literature_provenance.v1",
            "source_type": source_type,
            "source_name": source_name,
            "source_file": source_file or _first_text(raw_record, "source_file"),
            "source_query": source_query or _first_text(raw_record, "source_query"),
            "search_execution_id": search_execution_id or _first_text(raw_record, "search_execution_id"),
            "import_batch_id": import_batch_id,
            **dict(raw_record.get("provenance", {}) if isinstance(raw_record.get("provenance"), dict) else {}),
            **dict(provenance_base or {}),
        }
        record_id = _record_id(raw_record, source_type=source_type, doi=doi, pmid=pmid)
        clinical_trials = _clinical_trial_ids(raw_record)
        return {
            "schema_version": NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION,
            "record_id": record_id,
            "project_id": project_id,
            "title": _first_text(raw_record, "title"),
            "abstract": _first_text(raw_record, "abstract"),
            "authors": authors,
            "authors_text": "; ".join(authors),
            "first_author": _first_text(raw_record, "first_author") or (authors[0] if authors else ""),
            "corresponding_author": _first_text(raw_record, "corresponding_author"),
            "journal": _first_text(raw_record, "journal", "publication_title"),
            "publication_title": _first_text(raw_record, "publication_title", "journal"),
            "year": str(_first_text(raw_record, "year") or _year_from_date(_first_text(raw_record, "date", "publication_date"))),
            "publication_date": _first_text(raw_record, "publication_date", "date"),
            "date": _first_text(raw_record, "publication_date", "date"),
            "doi": doi,
            "pmid": pmid,
            "pmcid": _first_text(raw_record, "pmcid", "PMCID"),
            "clinical_trial_id": "; ".join(clinical_trials),
            "clinical_trials_ids": clinical_trials,
            "database_source": source_name,
            "source_database": source_name,
            "source_type": source_type,
            "source": source_type,
            "source_file": provenance["source_file"],
            "source_query": provenance["source_query"],
            "search_execution_id": provenance["search_execution_id"],
            "source_record_id": _first_text(raw_record, "source_record_id") or pmid or doi,
            "import_batch_id": import_batch_id,
            "batch_id": import_batch_id,
            "provenance": provenance,
            "raw_extra": _raw_extra(raw_record),
            "dedup_status": _first_text(raw_record, "dedup_status") or "pending_review",
            "screening_status": _first_text(raw_record, "screening_status") or "not_started",
            "full_text_status": _first_text(raw_record, "full_text_status", "fulltext_status") or "not_checked",
            "fulltext_status": _first_text(raw_record, "full_text_status", "fulltext_status") or "not_checked",
            "extraction_status": _first_text(raw_record, "extraction_status") or "not_started",
            "quality_status": _first_text(raw_record, "quality_status") or "not_started",
            "record_status": _first_text(raw_record, "record_status") or "imported_pending_dedup",
            "publication_type": _first_text(raw_record, "publication_type") or "unknown",
            "notes": _first_text(raw_record, "notes"),
            "created_at": _first_text(raw_record, "created_at") or created_at,
            "updated_at": _now(),
            "audit_refs": [str(item) for item in audit_refs],
        }

    def list_records(self, project_dir: Path) -> list[dict[str, Any]]:
        return _records_from_payload(_load_json(self.records_path(project_dir)))

    def get_record(self, project_dir: Path, record_id: str) -> dict[str, Any] | None:
        for record in self.list_records(project_dir):
            if str(record.get("record_id", "")) == record_id:
                return record
        return None

    def filter_records(
        self,
        project_dir: Path,
        *,
        source_type: str = "",
        pmid: str = "",
        doi: str = "",
        title_keyword: str = "",
        import_batch_id: str = "",
    ) -> list[dict[str, Any]]:
        records = self.list_records(project_dir)
        if source_type:
            records = [record for record in records if str(record.get("source_type") or record.get("source")) == source_type]
        if pmid:
            records = [record for record in records if str(record.get("pmid", "")).lower() == pmid.lower()]
        if doi:
            records = [record for record in records if str(record.get("doi", "")).lower() == doi.lower()]
        if title_keyword:
            keyword = title_keyword.lower()
            records = [record for record in records if keyword in str(record.get("title", "")).lower()]
        if import_batch_id:
            records = [record for record in records if str(record.get("import_batch_id") or record.get("batch_id")) == import_batch_id]
        return records

    def read_manifest(self, project_dir: Path) -> dict[str, Any]:
        manifest = _load_json(self.manifest_path(project_dir))
        return manifest if isinstance(manifest, dict) else {}

    def update_manifest(self, project_dir: Path, *, project_id: str | None = None) -> Path:
        project_dir = project_dir.expanduser().resolve()
        records = self.list_records(project_dir)
        batches = self._list_batches(project_dir)
        source_counts: dict[str, int] = {}
        for record in records:
            source = str(record.get("source_type") or record.get("source") or "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1
        manifest_path = self.manifest_path(project_dir)
        _write_json(
            manifest_path,
            {
                "schema_version": LITERATURE_LIBRARY_MANIFEST_SCHEMA_VERSION,
                "project_id": project_id or project_dir.name,
                "records_path": str(self.records_path(project_dir).relative_to(project_dir)),
                "import_batches_path": str(self.import_batches_path(project_dir).relative_to(project_dir)),
                "dedup_queue_path": "deduplication/pubmed_candidate_duplicate_groups.json",
                "total_records": len(records),
                "total_batches": len(batches),
                "source_counts": source_counts,
                "last_updated": _now(),
            },
        )
        return manifest_path

    def _append_import_batch(
        self,
        project_dir: Path,
        *,
        project_id: str,
        import_batch_id: str,
        source_type: str,
        source_name: str,
        source_file: str,
        source_query: str,
        search_execution_id: str,
        imported_count: int,
        skipped_count: int,
        duplicate_candidate_count: int,
        diagnostics: dict[str, Any],
        governance_refs: tuple[str, ...],
        audit_refs: tuple[str, ...],
        created_at: str,
    ) -> dict[str, Any]:
        path = self.import_batches_path(project_dir)
        batches = self._list_batches(project_dir)
        payload = {
            "schema_version": LITERATURE_IMPORT_BATCH_SCHEMA_VERSION,
            "import_batch_id": import_batch_id,
            "batch_id": import_batch_id,
            "project_id": project_id,
            "source_type": source_type,
            "source_name": source_name or source_type,
            "source_file": source_file,
            "source_query": source_query,
            "search_execution_id": search_execution_id,
            "created_at": created_at,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "duplicate_candidate_count": duplicate_candidate_count,
            "selected_count": int(diagnostics.get("selected_count", imported_count) or 0),
            "rejected_count": int(diagnostics.get("rejected_count", 0) or 0),
            "diagnostics": diagnostics,
            "governance_refs": list(governance_refs),
            "audit_refs": list(audit_refs),
            "record_status": "imported_pending_dedup",
            "screening_status": "not_started",
            "dedup_status": "pending_review",
        }
        batches.append(payload)
        _write_json(
            path,
            {
                "schema_version": LITERATURE_IMPORT_BATCHES_SCHEMA_VERSION,
                "project_id": project_id,
                "import_batches": batches,
            },
        )
        self._audit_log.record_event(
            project_dir,
            event_type="import_batch_created",
            project_id=project_id,
            target_type="import_batch",
            target_id=import_batch_id,
            source_path=source_file,
            output_path=str(path.relative_to(project_dir)),
            summary="Normalized literature import batch created.",
            details={"source_type": source_type, "imported_count": imported_count, "skipped_count": skipped_count},
        )
        return payload

    def _list_batches(self, project_dir: Path) -> list[dict[str, Any]]:
        payload = _load_json(self.import_batches_path(project_dir))
        if isinstance(payload, list):
            return [dict(item) for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict) and isinstance(payload.get("import_batches"), list):
            return [dict(item) for item in payload["import_batches"] if isinstance(item, dict)]
        return []

    def _append_record_audit(
        self,
        project_dir: Path,
        *,
        project_id: str,
        record: dict[str, Any],
        import_batch_id: str,
        source: str,
        action: str,
        previous_status: str,
        new_status: str,
        actor: str,
    ) -> str:
        path = self.record_audit_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "schema_version": LITERATURE_RECORD_AUDIT_SCHEMA_VERSION,
            "event_id": f"litrec-{uuid4().hex[:12]}",
            "project_id": project_id,
            "record_id": record.get("record_id", ""),
            "source": source,
            "action": action,
            "previous_status": previous_status,
            "new_status": new_status,
            "import_batch_id": import_batch_id,
            "actor": actor,
            "created_at": _now(),
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        return f"audit:LiteratureRecord:{event['event_id']}"


def _diagnostics_for_record(record: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    if not record.get("doi"):
        warnings.append("缺少 DOI")
    if not record.get("pmid"):
        warnings.append("缺少 PMID")
    if not record.get("abstract"):
        warnings.append("缺少摘要")
    if not record.get("year"):
        warnings.append("缺少年份")
    if not record.get("authors") or not record.get("first_author"):
        warnings.append("作者字段不完整")
    if not record.get("source_type") or not record.get("source_file") and not record.get("source_query"):
        warnings.append("来源信息不完整")
    return {"record_id": record.get("record_id", ""), "warnings": warnings}


def _diagnostics_summary(rows: list[dict[str, Any]], extra: dict[str, Any]) -> dict[str, Any]:
    warning_counts: dict[str, int] = {}
    for row in rows:
        for warning in row.get("warnings", []):
            warning_counts[str(warning)] = warning_counts.get(str(warning), 0) + 1
    return {
        "schema_version": "meta_literature_import_diagnostics.v1",
        "warning_counts": warning_counts,
        "record_warnings": rows,
        "warning_count": sum(warning_counts.values()),
        **extra,
    }


def _record_id(raw_record: dict[str, Any], *, source_type: str, doi: str, pmid: str) -> str:
    existing = _first_text(raw_record, "record_id")
    if existing.startswith("lit-"):
        return existing
    if pmid:
        return f"lit-pubmed-{_slug(pmid)}" if source_type.startswith("pubmed") or source_type == "nbib" else f"lit-pmid-{_slug(pmid)}"
    if doi:
        return f"lit-doi-{_slug(doi)}"
    if existing:
        return f"lit-{_slug(existing)}"
    return f"lit-{uuid4().hex[:12]}"


def _raw_extra(raw_record: dict[str, Any]) -> dict[str, Any]:
    return dict(raw_record.get("raw_extra", {}) if isinstance(raw_record.get("raw_extra"), dict) else {"source_payload": raw_record})


def _authors(raw_record: dict[str, Any]) -> list[str]:
    value = raw_record.get("authors")
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        parts = re.split(r";|\|", value)
        return [part.strip() for part in parts if part.strip()]
    creators = raw_record.get("creators")
    if isinstance(creators, list):
        authors: list[str] = []
        for creator in creators:
            if isinstance(creator, dict):
                text = str(creator.get("full_name") or creator.get("raw") or "").strip()
                if text:
                    authors.append(text)
        return authors
    text = _first_text(raw_record, "authors_text", "first_author")
    return [text] if text else []


def _clinical_trial_ids(raw_record: dict[str, Any]) -> list[str]:
    value = raw_record.get("clinical_trial_id") or raw_record.get("clinical_trials_ids") or []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r";|,", value) if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _year_from_date(value: str) -> str:
    match = re.search(r"\b(19|20)\d{2}\b", value)
    return match.group(0) if match else ""


def _first_text(record: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, list):
            text = "; ".join(str(item) for item in value if str(item).strip())
        elif value is None:
            text = ""
        else:
            text = str(value).strip()
        if text:
            return text
    return ""


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


def _slug(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or uuid4().hex[:12]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
