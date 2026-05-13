from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


CREATOR_TYPES = {"author", "group_author", "editor", "corresponding_author"}
PUBLICATION_TYPES = {"journal_article", "randomized_trial", "clinical_trial", "review", "unknown"}
SYSTEM_CONTROLLED_FIELDS = {"record_id", "project_id", "batch_id", "screening_status", "attachment_id"}
IMPORTABLE_FIELDS = {
    "source_record_id",
    "title",
    "abstract",
    "authors",
    "authors_text",
    "creators",
    "first_author",
    "journal",
    "publication_title",
    "date",
    "doi",
    "pmid",
    "year",
    "keywords",
    "publication_type",
    "clinical_trials_ids",
    "external_key",
    "language",
    "raw_payload",
}


@dataclass(frozen=True)
class ParsedLiteratureRecord:
    record_id: str
    title: str = ""
    source_record_id: str = ""
    abstract: str = ""
    authors: list[str] = field(default_factory=list)
    authors_text: str = ""
    creators: list[dict[str, object]] = field(default_factory=list)
    first_author: str = ""
    journal: str = ""
    publication_title: str = ""
    date: str = ""
    doi: str = ""
    pmid: str = ""
    year: int | None = None
    keywords: list[str] = field(default_factory=list)
    publication_type: str = "unknown"
    clinical_trials_ids: list[str] = field(default_factory=list)
    external_key: str = ""
    language: str = ""
    raw_payload: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ImportAdapterResult:
    batch_id: str
    records: list[ParsedLiteratureRecord]


@dataclass(frozen=True)
class SanitizedImportPayload:
    sanitized: dict[str, object]
    removed_fields: list[str]


@dataclass(frozen=True)
class ImportDiagnostics:
    raw_record_count: int
    parsed_record_count: int
    normalized_record_count: int
    failed_record_count: int
    warning_count: int
    missing_title_count: int
    missing_author_count: int
    missing_year_count: int
    missing_doi_count: int
    missing_pmid_count: int
    empty_abstract_count: int
    invalid_year_count: int
    invalid_doi_count: int
    duplicate_identifier_count: int
    duplicate_candidate_count: int
    records_after_dedup_count: int
    parse_warning_examples: list[str] = field(default_factory=list)
    failed_record_examples: list[str] = field(default_factory=list)


def parse_literature_file(source_path: Path, project_id: str, source_type: str) -> ImportAdapterResult:
    batch_id = f"batch-{uuid4().hex[:12]}"
    source_type = source_type.strip().lower()
    if source_type == "ris":
        records = _parse_ris(source_path, batch_id, project_id)
    elif source_type == "nbib":
        records = _parse_nbib(source_path, batch_id, project_id)
    elif source_type == "csv":
        records = _parse_csv(source_path, batch_id, project_id)
    else:
        raise ValueError(f"Unsupported literature import format: {source_type}")
    return ImportAdapterResult(batch_id=batch_id, records=records)


def normalize_record_payload(record: dict[str, object], *, batch_id: str, project_id: str, source_type: str) -> dict[str, object]:
    authors = _authors_from_payload(record)
    title = _clean_text(record.get("title", ""))
    journal = _clean_text(record.get("journal") or record.get("publication_title", ""))
    doi = normalize_doi(str(record.get("doi", "")))
    pmid = normalize_pmid(str(record.get("pmid", "")))
    year = _parse_year(record.get("year") or record.get("date"))
    first_author = _clean_text(record.get("first_author", "")) or (_first_author(authors) if authors else "")
    return {
        **record,
        "record_id": str(record.get("record_id") or f"rec-{uuid4().hex[:12]}"),
        "batch_id": batch_id,
        "project_id": project_id,
        "source": source_type,
        "title": title,
        "abstract": _clean_multiline(record.get("abstract", "")),
        "authors": authors,
        "authors_text": str(record.get("authors_text") or "; ".join(authors)),
        "creators": _creator_dicts(authors),
        "first_author": first_author,
        "journal": journal,
        "publication_title": _clean_text(record.get("publication_title") or journal),
        "date": _clean_text(record.get("date", "")),
        "doi": doi,
        "pmid": pmid,
        "year": year,
        "keywords": _list_text(record.get("keywords", [])),
        "publication_type": normalize_publication_type(str(record.get("publication_type", "unknown"))),
        "clinical_trials_ids": _list_text(record.get("clinical_trials_ids", [])),
        "external_key": _clean_text(record.get("external_key", "")),
        "language": _clean_text(record.get("language", "")),
        "raw_payload": record.get("raw_payload", {}) if isinstance(record.get("raw_payload", {}), dict) else {},
        "title_normalized": normalize_title(title),
        "doi_normalized": doi,
        "pmid_normalized": pmid,
        "authors_normalized": [normalize_author(author) for author in authors if normalize_author(author)],
        "journal_normalized": normalize_title(journal),
        "year_normalized": year,
        "source_trace": list(record.get("source_trace", [])) or [str(record.get("record_id") or "")],
    }


def sanitize_import_payload(payload: dict[str, object]) -> SanitizedImportPayload:
    sanitized = {key: value for key, value in payload.items() if key in IMPORTABLE_FIELDS}
    removed_fields = sorted(key for key in payload if key not in IMPORTABLE_FIELDS)
    return SanitizedImportPayload(sanitized=sanitized, removed_fields=removed_fields)


def build_import_diagnostics(batch_id: str, records: list[dict[str, object]]) -> ImportDiagnostics:
    duplicate_buckets: dict[str, list[str]] = {}
    failed_examples: list[str] = []
    parse_examples: list[str] = []

    for index, record in enumerate(records, start=1):
        title = str(record.get("title", "")).strip()
        if not title:
            failed_examples.append(f"record_{index}:missing_title")
        doi = normalize_doi(str(record.get("doi", "")))
        pmid = normalize_pmid(str(record.get("pmid", "")))
        if doi:
            duplicate_buckets.setdefault(f"doi:{doi}", []).append(str(record.get("record_id", "")))
        if pmid:
            duplicate_buckets.setdefault(f"pmid:{pmid}", []).append(str(record.get("record_id", "")))
        raw_doi = _raw_identifier(record, "doi", "DO", "AID")
        if raw_doi and not doi:
            parse_examples.append(f"record_{index}:invalid_doi")
        if record.get("year") is None and str(record.get("date", "")).strip():
            parse_examples.append(f"record_{index}:invalid_year")

    duplicate_record_sets = {
        tuple(sorted(record_ids))
        for record_ids in duplicate_buckets.values()
        if len(record_ids) > 1
    }
    duplicate_identifier_count = len(duplicate_record_sets)
    missing_title_count = sum(1 for record in records if not str(record.get("title", "")).strip())
    missing_author_count = sum(1 for record in records if not _authors_from_payload(record))
    missing_year_count = sum(1 for record in records if record.get("year") is None)
    missing_doi_count = sum(1 for record in records if not _raw_identifier(record, "doi", "DO", "AID"))
    missing_pmid_count = sum(1 for record in records if not normalize_pmid(str(record.get("pmid", ""))))
    empty_abstract_count = sum(1 for record in records if not str(record.get("abstract", "")).strip())
    invalid_year_count = sum(1 for record in records if record.get("year") is None and str(record.get("date", "")).strip())
    invalid_doi_count = sum(
        1
        for record in records
        if _raw_identifier(record, "doi", "DO", "AID") and not normalize_doi(str(record.get("doi", "")))
    )
    warning_count = sum(
        (
            missing_title_count,
            missing_author_count,
            missing_year_count,
            missing_doi_count,
            missing_pmid_count,
            empty_abstract_count,
            invalid_year_count,
            invalid_doi_count,
            duplicate_identifier_count,
        )
    )
    return ImportDiagnostics(
        raw_record_count=len(records),
        parsed_record_count=len(records),
        normalized_record_count=len(records),
        failed_record_count=len(failed_examples),
        warning_count=warning_count,
        missing_title_count=missing_title_count,
        missing_author_count=missing_author_count,
        missing_year_count=missing_year_count,
        missing_doi_count=missing_doi_count,
        missing_pmid_count=missing_pmid_count,
        empty_abstract_count=empty_abstract_count,
        invalid_year_count=invalid_year_count,
        invalid_doi_count=invalid_doi_count,
        duplicate_identifier_count=duplicate_identifier_count,
        duplicate_candidate_count=duplicate_identifier_count,
        records_after_dedup_count=max(len(records) - duplicate_identifier_count, 0),
        parse_warning_examples=parse_examples[:5],
        failed_record_examples=failed_examples[:5],
    )


def write_import_diagnostics(project_dir: Path, batch_id: str, diagnostics: ImportDiagnostics) -> tuple[Path, Path]:
    diagnostics_dir = project_dir / "literature" / "import_diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    diagnostics_path = diagnostics_dir / f"{batch_id}_import_diagnostics.json"
    warnings_path = diagnostics_dir / f"{batch_id}_import_warnings.csv"
    diagnostics_path.write_text(json.dumps(asdict(diagnostics), ensure_ascii=False, indent=2), encoding="utf-8")
    with warnings_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["key", "count"])
        writer.writeheader()
        for key, value in asdict(diagnostics).items():
            if key.endswith("_count") and isinstance(value, int) and value > 0:
                writer.writerow({"key": key, "count": value})
        for example in diagnostics.parse_warning_examples:
            writer.writerow({"key": example, "count": ""})
        for example in diagnostics.failed_record_examples:
            writer.writerow({"key": example, "count": ""})
    return diagnostics_path, warnings_path


def append_import_batch(project_dir: Path, payload: dict[str, object]) -> Path:
    literature_dir = project_dir / "literature"
    literature_dir.mkdir(parents=True, exist_ok=True)
    path = literature_dir / "import_batches.json"
    batches: list[dict[str, object]] = []
    if path.exists():
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, list):
            batches = [dict(item) for item in loaded if isinstance(item, dict)]
    batches.append(payload)
    path.write_text(json.dumps(batches, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def duplicate_groups_for_records(project_id: str, records: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    seen_pairs: set[tuple[str, ...]] = set()
    for key_name in ("doi_normalized", "pmid_normalized"):
        buckets: dict[str, list[dict[str, object]]] = {}
        for record in records:
            if key_name == "doi_normalized":
                key = str(record.get(key_name) or normalize_doi(str(record.get("doi", ""))))
            else:
                key = str(record.get(key_name) or normalize_pmid(str(record.get("pmid", ""))))
            if key:
                buckets.setdefault(key, []).append(record)
        for key, bucket in buckets.items():
            if len(bucket) < 2:
                continue
            record_ids = tuple(sorted(str(record.get("record_id", "")) for record in bucket))
            if record_ids in seen_pairs:
                reason = key_name.replace("_normalized", "_exact")
                for group in groups:
                    if tuple(sorted(str(record_id) for record_id in group.get("candidate_record_ids", []))) == record_ids:
                        existing_reason = str(group.get("match_reason", ""))
                        if reason not in existing_reason.split(","):
                            group["match_reason"] = ",".join(part for part in (existing_reason, reason) if part)
                        break
                continue
            seen_pairs.add(record_ids)
            groups.append(_duplicate_group(project_id, key_name.replace("_normalized", "_exact"), key, bucket, confidence=0.99))

    title_buckets: dict[tuple[str, str, str], list[dict[str, object]]] = {}
    for record in records:
        title = str(record.get("title_normalized") or normalize_title(str(record.get("title", ""))))
        first_author = ""
        authors = _authors_from_payload(record)
        if authors:
            first_author = normalize_author(authors[0])
        year = str(record.get("year_normalized") or record.get("year") or "")
        if title and first_author:
            title_buckets.setdefault((title, first_author, year), []).append(record)
    for (_title, _author, _year), bucket in title_buckets.items():
        if len(bucket) < 2:
            continue
        record_ids = tuple(sorted(str(record.get("record_id", "")) for record in bucket))
        if record_ids in seen_pairs:
            continue
        seen_pairs.add(record_ids)
        groups.append(_duplicate_group(project_id, "title_author_year_suspected", _title, bucket, confidence=0.9))
    return groups


def normalize_doi(value: str) -> str:
    text = value.strip()
    text = re.sub(r"^\s*(doi:|https?://(dx\.)?doi\.org/)", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s*\[doi\]\s*$", "", text, flags=re.IGNORECASE).strip()
    text = text.rstrip(".")
    if not text or not re.match(r"^10\.\S+/.+", text, flags=re.IGNORECASE):
        return ""
    return text.lower()


def normalize_pmid(value: str) -> str:
    match = re.search(r"\d+", value)
    return match.group(0) if match else ""


def normalize_title(value: str) -> str:
    text = _clean_text(value).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def normalize_author(value: str) -> str:
    text = _clean_text(value).lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def normalize_publication_type(value: str) -> str:
    text = normalize_title(value).replace(" ", "_")
    if "randomized" in text or "randomised" in text:
        return "randomized_trial"
    if "clinical_trial" in text:
        return "clinical_trial"
    if "review" in text:
        return "review"
    if "journal_article" in text or text == "article":
        return "journal_article"
    return text if text in PUBLICATION_TYPES else "unknown"


def _parse_ris(path: Path, batch_id: str, project_id: str) -> list[ParsedLiteratureRecord]:
    records: list[ParsedLiteratureRecord] = []
    current: dict[str, list[str]] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        if re.match(r"^[A-Z0-9]{2}\s+-", raw_line):
            tag, value = raw_line.split("-", 1)
            tag = tag.strip()
            value = value.strip()
            if tag == "ER":
                if current:
                    records.append(_record_from_ris(current, batch_id, project_id))
                current = {}
            else:
                current.setdefault(tag, []).append(value)
        elif current:
            last_key = next(reversed(current))
            current[last_key][-1] = current[last_key][-1] + " " + raw_line.strip()
    if current:
        records.append(_record_from_ris(current, batch_id, project_id))
    return records


def _parse_nbib(path: Path, batch_id: str, project_id: str) -> list[ParsedLiteratureRecord]:
    records: list[ParsedLiteratureRecord] = []
    current: dict[str, list[str]] = {}
    last_key = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            if current:
                records.append(_record_from_nbib(current, batch_id, project_id))
                current = {}
                last_key = ""
            continue
        match = re.match(r"^([A-Z]{2,4})\s*-\s*(.*)$", raw_line)
        if match:
            last_key = match.group(1)
            current.setdefault(last_key, []).append(match.group(2).strip())
        elif last_key:
            current[last_key][-1] = current[last_key][-1] + " " + raw_line.strip()
    if current:
        records.append(_record_from_nbib(current, batch_id, project_id))
    return records


def _parse_csv(path: Path, batch_id: str, project_id: str) -> list[ParsedLiteratureRecord]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [_record_from_csv(row, batch_id, project_id, index) for index, row in enumerate(reader, start=1)]


def _record_from_ris(fields: dict[str, list[str]], batch_id: str, project_id: str) -> ParsedLiteratureRecord:
    title = _first(fields, "TI", "T1")
    authors = _list_text(fields.get("AU") or fields.get("A1") or [])
    date = _first(fields, "PY", "Y1")
    doi = normalize_doi(_first(fields, "DO", "M3"))
    pmid = normalize_pmid(_first(fields, "PM"))
    source_record_id = _first(fields, "ID", "AN", "C7")
    return _build_record(
        batch_id=batch_id,
        project_id=project_id,
        source="ris",
        source_record_id=source_record_id,
        title=title,
        abstract=_first(fields, "AB", "N2"),
        authors=authors,
        journal=_first(fields, "JO", "JF", "T2"),
        date=date,
        doi=doi,
        pmid=pmid,
        keywords=_list_text(fields.get("KW") or []),
        publication_type=_first(fields, "TY") or "journal_article",
        language=_first(fields, "LA"),
        raw_payload=_flatten_raw_payload(fields),
    )


def _record_from_nbib(fields: dict[str, list[str]], batch_id: str, project_id: str) -> ParsedLiteratureRecord:
    title = _first(fields, "TI")
    authors = _list_text(fields.get("FAU") or fields.get("AU") or [])
    date = _first(fields, "DP")
    aid_values = fields.get("AID", [])
    doi = normalize_doi(next((value for value in aid_values if "[doi]" in value.lower() or value.lower().startswith("10.")), ""))
    pmid = normalize_pmid(_first(fields, "PMID"))
    publication_types = fields.get("PT", [])
    return _build_record(
        batch_id=batch_id,
        project_id=project_id,
        source="nbib",
        source_record_id=pmid,
        title=title,
        abstract=_first(fields, "AB"),
        authors=authors,
        journal=_first(fields, "JT", "TA"),
        date=date,
        doi=doi,
        pmid=pmid,
        keywords=_list_text(fields.get("OT") or []),
        publication_type=next((normalize_publication_type(item) for item in publication_types if normalize_publication_type(item) != "journal_article"), normalize_publication_type(publication_types[0] if publication_types else "")),
        language=_first(fields, "LA"),
        raw_payload=_flatten_raw_payload(fields),
    )


def _record_from_csv(row: dict[str, str], batch_id: str, project_id: str, index: int) -> ParsedLiteratureRecord:
    authors = _split_authors(row.get("authors", ""))
    date = row.get("date", "") or row.get("year", "")
    return _build_record(
        batch_id=batch_id,
        project_id=project_id,
        source="csv",
        source_record_id=row.get("source_record_id", "") or row.get("id", "") or f"csv-{index:03d}",
        title=row.get("title", ""),
        abstract=row.get("abstract", ""),
        authors=authors,
        journal=row.get("journal", "") or row.get("publication_title", ""),
        date=date,
        doi=normalize_doi(row.get("doi", "")),
        pmid=normalize_pmid(row.get("pmid", "")),
        keywords=_split_keywords(row.get("keywords", "")),
        publication_type=normalize_publication_type(row.get("publication_type", "")),
        language=row.get("language", ""),
        raw_payload=dict(row),
    )


def _build_record(
    *,
    batch_id: str,
    project_id: str,
    source: str,
    source_record_id: str,
    title: str,
    abstract: str,
    authors: list[str],
    journal: str,
    date: str,
    doi: str,
    pmid: str,
    keywords: list[str],
    publication_type: str,
    language: str,
    raw_payload: dict[str, object],
) -> ParsedLiteratureRecord:
    record_id = f"rec-{uuid4().hex[:12]}"
    parsed_year = _parse_year(date)
    normalized_authors = [_normalize_author_display(author) for author in authors if _clean_text(author)]
    first_author = _first_author(normalized_authors)
    return ParsedLiteratureRecord(
        record_id=record_id,
        title=_clean_text(title),
        source_record_id=_clean_text(source_record_id),
        abstract=_clean_multiline(abstract),
        authors=authors,
        authors_text="; ".join(authors),
        creators=_creator_dicts(authors),
        first_author=first_author,
        journal=_clean_text(journal),
        publication_title=_clean_text(journal),
        date=_clean_text(date),
        doi=doi,
        pmid=pmid,
        year=parsed_year,
        keywords=keywords,
        publication_type=normalize_publication_type(publication_type),
        external_key=_clean_text(source_record_id),
        language=_clean_text(language),
        raw_payload={**raw_payload, "batch_id": batch_id, "project_id": project_id, "source": source},
    )


def _duplicate_group(project_id: str, reason: str, key: str, records: list[dict[str, object]], *, confidence: float) -> dict[str, object]:
    record_ids = [str(record.get("record_id", "")) for record in records]
    return {
        "duplicate_group_id": f"dup-{uuid4().hex[:12]}",
        "project_id": project_id,
        "candidate_record_ids": record_ids,
        "match_reason": reason,
        "confidence": confidence,
        "suggested_primary_record_id": _most_complete_record_id(records),
        "status": "pending",
        "match_key": key,
    }


def _most_complete_record_id(records: list[dict[str, object]]) -> str:
    def score(record: dict[str, object]) -> int:
        return sum(1 for key in ("title", "abstract", "authors", "journal", "year", "doi", "pmid") if record.get(key))

    return str(max(records, key=score).get("record_id", ""))


def _first(fields: dict[str, list[str]], *keys: str) -> str:
    for key in keys:
        values = fields.get(key)
        if values:
            return _clean_text(values[0])
    return ""


def _flatten_raw_payload(fields: dict[str, list[str]]) -> dict[str, object]:
    return {
        key: values[0] if len(values) == 1 else list(values)
        for key, values in fields.items()
    }


def _raw_identifier(record: dict[str, object], normalized_key: str, *raw_keys: str) -> str:
    raw_payload = record.get("raw_payload", {})
    if isinstance(raw_payload, dict):
        for key in raw_keys:
            value = raw_payload.get(key)
            if isinstance(value, list):
                value = next((item for item in value if str(item).strip()), "")
            text = str(value or "").strip()
            if text:
                return text
    return str(record.get(normalized_key, "")).strip()


def _parse_year(value: object) -> int | None:
    if isinstance(value, int):
        return value
    match = re.search(r"(19|20)\d{2}", str(value))
    return int(match.group(0)) if match else None


def _authors_from_payload(record: dict[str, object]) -> list[str]:
    authors = record.get("authors", [])
    if isinstance(authors, str):
        return _split_authors(authors)
    return [str(author).strip() for author in list(authors or []) if str(author).strip()]


def _split_authors(value: str) -> list[str]:
    return [part.strip() for part in re.split(r";|\|", value) if part.strip()]


def _split_keywords(value: str) -> list[str]:
    return [part.strip() for part in re.split(r";|\||,", value) if part.strip()]


def _list_text(values: object) -> list[str]:
    if isinstance(values, str):
        return [values.strip()] if values.strip() else []
    return [str(value).strip() for value in list(values or []) if str(value).strip()]


def _clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _clean_multiline(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_author_display(author: str) -> str:
    raw = _clean_text(author)
    if "," in raw:
        last_name, first_name = [part.strip() for part in raw.split(",", 1)]
        return " ".join(part for part in (first_name, last_name) if part)
    return raw


def _first_author(authors: list[str]) -> str:
    return _normalize_author_display(authors[0]) if authors else ""


def _creator_dicts(authors: list[str]) -> list[dict[str, object]]:
    return [_creator_from_author(author, index) for index, author in enumerate(authors, start=1)]


def _creator_from_author(author: str, order: int) -> dict[str, object]:
    raw = _clean_text(author)
    parts = raw.split()
    first_name = " ".join(parts[:-1]) if len(parts) > 1 else ""
    last_name = parts[-1] if parts else ""
    return {
        "first_name": first_name,
        "last_name": last_name,
        "full_name": raw,
        "creator_type": "author",
        "order": order,
        "raw": raw,
    }
