from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ImportDiagnostics:
    batch_id: str
    raw_record_count: int
    parsed_record_count: int
    normalized_record_count: int
    failed_record_count: int = 0
    warning_count: int = 0
    duplicate_candidate_count: int = 0
    records_after_dedup_count: int = 0
    missing_title_count: int = 0
    missing_author_count: int = 0
    missing_year_count: int = 0
    missing_doi_count: int = 0
    missing_pmid_count: int = 0
    empty_abstract_count: int = 0
    invalid_year_count: int = 0
    invalid_doi_count: int = 0
    duplicate_identifier_count: int = 0
    unsupported_record_type_count: int = 0
    parse_warning_examples: list[str] = field(default_factory=list)
    failed_record_examples: list[str] = field(default_factory=list)


DOI_RE = re.compile(r"^10\.\S+/\S+", re.IGNORECASE)


def build_import_diagnostics(batch_id: str, records: list[dict[str, Any]], *, raw_record_count: int | None = None) -> ImportDiagnostics:
    doi_seen: set[str] = set()
    pmid_seen: set[str] = set()
    duplicate_identifier_count = 0
    warnings: list[str] = []
    missing_title = missing_author = missing_year = missing_doi = missing_pmid = 0
    empty_abstract = invalid_year = invalid_doi = 0
    for index, record in enumerate(records, start=1):
        title = str(record.get("title", "")).strip()
        authors = record.get("authors") or record.get("creators") or record.get("authors_text")
        year = record.get("year")
        doi = str(record.get("doi", "")).strip()
        pmid = str(record.get("pmid", "")).strip()
        if not title:
            missing_title += 1
            warnings.append(f"record_{index}:missing_title")
        if not authors:
            missing_author += 1
        if year in ("", None):
            missing_year += 1
        elif not isinstance(year, int):
            invalid_year += 1
        if not doi:
            missing_doi += 1
        elif not DOI_RE.match(doi.lower()):
            invalid_doi += 1
        if not pmid:
            missing_pmid += 1
        if not str(record.get("abstract", "")).strip():
            empty_abstract += 1
        identifier = doi.lower() or pmid
        if doi:
            if doi.lower() in doi_seen:
                duplicate_identifier_count += 1
            doi_seen.add(doi.lower())
        if pmid:
            if pmid in pmid_seen and not doi:
                duplicate_identifier_count += 1
            pmid_seen.add(pmid)
        if identifier and duplicate_identifier_count:
            pass
    warning_count = len(warnings) + missing_author + missing_year + missing_doi + missing_pmid + empty_abstract + invalid_year + invalid_doi + duplicate_identifier_count
    return ImportDiagnostics(
        batch_id=batch_id,
        raw_record_count=raw_record_count if raw_record_count is not None else len(records),
        parsed_record_count=len(records),
        normalized_record_count=len(records),
        failed_record_count=missing_title,
        warning_count=warning_count,
        duplicate_candidate_count=duplicate_identifier_count,
        records_after_dedup_count=max(len(records) - duplicate_identifier_count, 0),
        missing_title_count=missing_title,
        missing_author_count=missing_author,
        missing_year_count=missing_year,
        missing_doi_count=missing_doi,
        missing_pmid_count=missing_pmid,
        empty_abstract_count=empty_abstract,
        invalid_year_count=invalid_year,
        invalid_doi_count=invalid_doi,
        duplicate_identifier_count=duplicate_identifier_count,
        parse_warning_examples=warnings[:10],
        failed_record_examples=warnings[:10],
    )


def write_import_diagnostics(project_dir: Path, diagnostics: ImportDiagnostics) -> tuple[Path, Path]:
    output_dir = project_dir.expanduser().resolve() / "literature" / "import_diagnostics"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{diagnostics.batch_id}_import_diagnostics.json"
    csv_path = output_dir / f"{diagnostics.batch_id}_import_warnings.csv"
    json_path.write_text(json.dumps(asdict(diagnostics), ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["batch_id", "warning"])
        writer.writeheader()
        for warning in diagnostics.parse_warning_examples:
            writer.writerow({"batch_id": diagnostics.batch_id, "warning": warning})
    return json_path, csv_path
