from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.literature_library_service import LiteratureLibraryImportResult, LiteratureLibraryService


MULTISOURCE_IMPORT_SCHEMA_VERSION = "meta_multisource_literature_import.v2"
MULTISOURCE_IMPORT_DIAGNOSTICS_SCHEMA_VERSION = "meta_multisource_import_diagnostics.v2"

SOURCE_NBIB = "nbib"
SOURCE_RIS = "ris"
SOURCE_CSV = "csv"
SOURCE_PUBMED_XML = "pubmed_xml"
SOURCE_MEDLINE = "medline"
SOURCE_ENDNOTE = "endnote_export"
SOURCE_ZOTERO = "zotero_export"
SOURCE_WOS_PLAIN = "wos_plain_text"
SOURCE_WOS_TAB = "wos_tab_delimited"
SOURCE_CNKI = "cnki_export"
SOURCE_EMBASE_RIS = "embase_ris"
SOURCE_COCHRANE_RIS = "cochrane_ris"

MULTISOURCE_SUPPORTED_FORMATS = (
    SOURCE_NBIB,
    SOURCE_RIS,
    SOURCE_CSV,
    SOURCE_PUBMED_XML,
    SOURCE_MEDLINE,
    SOURCE_ENDNOTE,
    SOURCE_ZOTERO,
    SOURCE_WOS_PLAIN,
    SOURCE_WOS_TAB,
    SOURCE_CNKI,
    SOURCE_EMBASE_RIS,
    SOURCE_COCHRANE_RIS,
)

_RIS_BASED_FORMATS = {SOURCE_RIS, SOURCE_ENDNOTE, SOURCE_ZOTERO, SOURCE_EMBASE_RIS, SOURCE_COCHRANE_RIS}


@dataclass(frozen=True)
class MultiSourceParseResult:
    schema_version: str
    source_format: str
    source_path: str
    raw_record_count: int
    parsed_record_count: int
    failed_record_count: int
    records: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MultiSourceLiteratureImportResult:
    success: bool
    project_id: str
    source_format: str
    source_path: str
    parsed_record_count: int
    imported_count: int
    skipped_count: int
    diagnostics_path: str
    library_records_path: str
    import_batch_id: str
    message: str
    library_result: LiteratureLibraryImportResult | None = None
    error_message: str = ""


class MultiSourceLiteratureImportService:
    def __init__(
        self,
        *,
        literature_library: LiteratureLibraryService | None = None,
        audit_log: MetaAuditLogService | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._library = literature_library or LiteratureLibraryService(audit_log=self._audit_log)

    def diagnostics_dir(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "literature" / "multisource_import_diagnostics"

    def parse_file(self, source_path: Path, *, source_format: str = "auto") -> MultiSourceParseResult:
        source_path = source_path.expanduser().resolve()
        if not source_path.exists() or not source_path.is_file():
            raise ValueError("source_file_not_found")
        detected = self.detect_format(source_path, requested_format=source_format)
        text = source_path.read_text(encoding="utf-8", errors="ignore")
        if detected in _RIS_BASED_FORMATS:
            records = _parse_ris(text, source_format=detected)
        elif detected in {SOURCE_NBIB, SOURCE_MEDLINE}:
            records = _parse_nbib_or_medline(text, source_format=detected)
        elif detected == SOURCE_CSV:
            records = _parse_csv(source_path)
        elif detected == SOURCE_PUBMED_XML:
            records = _parse_pubmed_xml(text)
        elif detected == SOURCE_WOS_PLAIN:
            records = _parse_wos_plain(text)
        elif detected == SOURCE_WOS_TAB:
            records = _parse_tabular(source_path, source_format=detected)
        elif detected == SOURCE_CNKI:
            records = _parse_cnki(text)
        else:
            raise ValueError(f"unsupported_multisource_import_format:{detected}")
        diagnostics = _diagnostics(records, source_format=detected)
        return MultiSourceParseResult(
            schema_version=MULTISOURCE_IMPORT_SCHEMA_VERSION,
            source_format=detected,
            source_path=str(source_path),
            raw_record_count=len(records),
            parsed_record_count=len(records),
            failed_record_count=0,
            records=tuple(records),
            diagnostics=diagnostics,
        )

    def import_file(
        self,
        project_dir: Path,
        *,
        project_id: str | None = None,
        source_path: Path,
        source_format: str = "auto",
        source_database: str = "",
        search_strategy: str = "",
        search_date: str = "",
    ) -> MultiSourceLiteratureImportResult:
        project_dir = project_dir.expanduser().resolve()
        try:
            parsed = self.parse_file(source_path, source_format=source_format)
            source_name = source_database or _source_name(parsed.source_format)
            diagnostics_path = self._write_diagnostics(project_dir, parsed, source_database=source_name, search_date=search_date)
            library = self._library.import_records(
                project_dir,
                project_id=project_id or project_dir.name,
                raw_records=list(parsed.records),
                source_type=parsed.source_format,
                source_name=source_name,
                source_file=parsed.source_path,
                source_query=search_strategy,
                provenance_base={
                    "multisource_import_schema_version": MULTISOURCE_IMPORT_SCHEMA_VERSION,
                    "source_database": source_name,
                    "search_date": search_date,
                    "diagnostics_path": str(diagnostics_path.relative_to(project_dir)),
                    "online_execution": False,
                },
                diagnostics={
                    **parsed.diagnostics,
                    "diagnostics_path": str(diagnostics_path),
                    "adapter": "active_meta_multisource_import_service",
                    "legacy_dependency": False,
                    "online_execution": False,
                    "screening_status": "not_started",
                    "prisma_status": "not_updated",
                },
            )
            self._audit_log.record_event(
                project_dir,
                event_type="import_batch_created",
                project_id=project_id or project_dir.name,
                target_type="multisource_literature_import",
                target_id=library.import_batch_id,
                source_path=parsed.source_path,
                output_path=str(self._library.records_path(project_dir).relative_to(project_dir)),
                summary=f"Multi-source literature import completed for {parsed.source_format}.",
                details={"source_format": parsed.source_format, "online_execution": False, "screening_status": "not_started"},
            )
            return MultiSourceLiteratureImportResult(
                success=True,
                project_id=project_id or project_dir.name,
                source_format=parsed.source_format,
                source_path=parsed.source_path,
                parsed_record_count=parsed.parsed_record_count,
                imported_count=library.imported_count,
                skipped_count=library.skipped_count,
                diagnostics_path=str(diagnostics_path),
                library_records_path=library.records_path,
                import_batch_id=library.import_batch_id,
                message=f"Imported {library.imported_count} records from {parsed.source_format}; no screening or PRISMA update.",
                library_result=library,
            )
        except Exception as exc:
            return MultiSourceLiteratureImportResult(
                success=False,
                project_id=project_id or project_dir.expanduser().resolve().name,
                source_format=source_format,
                source_path=str(source_path),
                parsed_record_count=0,
                imported_count=0,
                skipped_count=0,
                diagnostics_path="",
                library_records_path="",
                import_batch_id="",
                message="多来源文献导入失败，请检查文件格式和字段。",
                error_message=str(exc),
            )

    def detect_format(self, source_path: Path, *, requested_format: str = "auto") -> str:
        requested = (requested_format or "auto").strip().lower()
        if requested in MULTISOURCE_SUPPORTED_FORMATS:
            return requested
        if requested not in {"auto", "auto-detect", "autodetect", ""}:
            return "unknown"
        suffix = source_path.suffix.lower()
        if suffix == ".nbib":
            return SOURCE_NBIB
        if suffix == ".ris":
            return SOURCE_RIS
        if suffix == ".csv":
            return SOURCE_CSV
        if suffix == ".xml":
            return SOURCE_PUBMED_XML
        if suffix in {".tsv", ".tab"}:
            return SOURCE_WOS_TAB
        if suffix in {".txt", ".ciw"}:
            text = source_path.read_text(encoding="utf-8", errors="ignore")[:2000]
            if "\nER" in text and ("\nUT " in text or "\nTI " in text):
                return SOURCE_WOS_PLAIN
            if "题名" in text or "作者" in text or "来源" in text:
                return SOURCE_CNKI
            return SOURCE_MEDLINE
        return "unknown"

    def _write_diagnostics(self, project_dir: Path, parsed: MultiSourceParseResult, *, source_database: str, search_date: str) -> Path:
        path = self.diagnostics_dir(project_dir) / f"{_slug(parsed.source_format)}_{_timestamp_slug()}_diagnostics.json"
        payload = {
            "schema_version": MULTISOURCE_IMPORT_DIAGNOSTICS_SCHEMA_VERSION,
            "source_format": parsed.source_format,
            "source_database": source_database,
            "source_path": parsed.source_path,
            "source_file_name": Path(parsed.source_path).name,
            "search_date": search_date,
            "raw_record_count": parsed.raw_record_count,
            "parsed_record_count": parsed.parsed_record_count,
            "failed_record_count": parsed.failed_record_count,
            "error_examples": [],
            "warning_count": parsed.diagnostics.get("warning_count", 0),
            "warning_counts": parsed.diagnostics.get("warning_counts", {}),
            "field_coverage": parsed.diagnostics.get("field_coverage", {}),
            "field_mapping_warnings": parsed.diagnostics.get("field_mapping_warnings", []),
            "title_abnormality_count": parsed.diagnostics.get("title_abnormality_count", 0),
            "title_abnormality_examples": parsed.diagnostics.get("title_abnormality_examples", [])[:5],
            "online_execution": False,
            "screening_status": "not_started",
            "prisma_status": "not_updated",
            "created_at": _now(),
            "imported_at": _now(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._audit_log.record_event(
            project_dir,
            event_type="diagnostics_generated",
            project_id=project_dir.name,
            target_type="multisource_import_diagnostics",
            target_id=path.stem,
            source_path=parsed.source_path,
            output_path=str(path.relative_to(project_dir)),
            summary="Multi-source literature import diagnostics generated.",
            details={"source_format": parsed.source_format, "warning_count": payload["warning_count"]},
        )
        return path


def _parse_ris(text: str, *, source_format: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, list[str]] = {}
    for line in text.splitlines():
        if len(line) < 6 or "  -" not in line[:6]:
            continue
        tag = line[:2].strip().upper()
        value = line[6:].strip()
        if tag == "TY" and current:
            records.append(_record_from_ris(current, source_format=source_format))
            current = {}
        current.setdefault(tag, []).append(value)
        if tag == "ER":
            records.append(_record_from_ris(current, source_format=source_format))
            current = {}
    if current:
        records.append(_record_from_ris(current, source_format=source_format))
    return [record for record in records if any(record.get(key) for key in ("title", "doi", "pmid"))]


def _record_from_ris(payload: dict[str, list[str]], *, source_format: str) -> dict[str, Any]:
    authors = payload.get("AU") or payload.get("A1") or []
    year = _year(payload.get("PY", [""])[0] or payload.get("Y1", [""])[0])
    return {
        "title": _first(payload, "TI", "T1", "CT"),
        "abstract": _first(payload, "AB", "N2"),
        "authors": authors,
        "first_author": authors[0] if authors else "",
        "journal": _first(payload, "JO", "JF", "T2"),
        "year": year,
        "publication_date": _first(payload, "Y1", "PY"),
        "doi": _first(payload, "DO"),
        "pmid": _first(payload, "PMID", "M1"),
        "database_source": _source_name(source_format),
        "source_type": source_format,
        "source_record_id": _first(payload, "ID", "UT"),
        "keywords": payload.get("KW", []),
        "raw_extra": {"ris_tags": payload},
    }


def _parse_nbib_or_medline(text: str, *, source_format: str) -> list[dict[str, Any]]:
    records: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] = {}
    last_tag = ""
    for line in text.splitlines():
        if not line.strip():
            if current:
                records.append(current)
                current = {}
                last_tag = ""
            continue
        if len(line) > 6 and line[4] == "-":
            tag = line[:4].strip().upper()
            value = line[6:].strip()
            current.setdefault(tag, []).append(value)
            last_tag = tag
        elif last_tag:
            current[last_tag][-1] = f"{current[last_tag][-1]} {line.strip()}".strip()
    if current:
        records.append(current)
    return [_record_from_nbib(item, source_format=source_format) for item in records]


def _record_from_nbib(payload: dict[str, list[str]], *, source_format: str) -> dict[str, Any]:
    authors = payload.get("FAU") or payload.get("AU") or []
    doi = _doi_from_values([*payload.get("LID", []), *payload.get("AID", [])])
    return {
        "title": _first(payload, "TI"),
        "abstract": " ".join(payload.get("AB", [])),
        "authors": authors,
        "first_author": authors[0] if authors else "",
        "journal": _first(payload, "JT", "TA"),
        "year": _year(_first(payload, "DP")),
        "publication_date": _first(payload, "DP"),
        "doi": doi,
        "pmid": _first(payload, "PMID"),
        "pmcid": _first(payload, "PMC"),
        "database_source": _source_name(source_format),
        "source_type": source_format,
        "source_record_id": _first(payload, "PMID"),
        "keywords": payload.get("OT", []),
        "raw_extra": {"nbib_tags": payload},
    }


def _parse_csv(source_path: Path) -> list[dict[str, Any]]:
    with source_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [_record_from_tabular(row, source_format=SOURCE_CSV) for row in rows]


def _parse_tabular(source_path: Path, *, source_format: str) -> list[dict[str, Any]]:
    with source_path.open("r", encoding="utf-8", newline="") as handle:
        delimiter = "\t" if source_path.suffix.lower() in {".tsv", ".tab"} else ","
        rows = list(csv.DictReader(handle, delimiter=delimiter))
    return [_record_from_tabular(row, source_format=source_format) for row in rows]


def _record_from_tabular(row: dict[str, Any], *, source_format: str) -> dict[str, Any]:
    authors = _split_authors(_alias(row, "authors", "AU", "Author Full Names", "Authors"))
    return {
        "title": _alias(row, "title", "Title", "Article Title", "TI"),
        "abstract": _alias(row, "abstract", "Abstract", "AB"),
        "authors": authors,
        "first_author": authors[0] if authors else "",
        "journal": _alias(row, "journal", "Source Title", "Publication Name", "SO"),
        "year": _year(_alias(row, "year", "Publication Year", "PY")),
        "publication_date": _alias(row, "publication_date", "Publication Date", "PD", "PY"),
        "doi": _alias(row, "doi", "DOI", "DI"),
        "pmid": _alias(row, "pmid", "PMID"),
        "pmcid": _alias(row, "pmcid", "PMCID"),
        "database_source": _source_name(source_format),
        "source_type": source_format,
        "source_record_id": _alias(row, "record_id", "UT", "Accession Number"),
        "raw_extra": {"tabular_row": row},
    }


def _parse_pubmed_xml(text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(text)
    records: list[dict[str, Any]] = []
    for article in root.findall(".//PubmedArticle"):
        pmid = _xml_text(article, ".//MedlineCitation/PMID")
        title = _xml_text(article, ".//ArticleTitle")
        abstract = " ".join(node.text or "" for node in article.findall(".//AbstractText")).strip()
        authors = [
            " ".join(part for part in (_xml_text(author, "ForeName"), _xml_text(author, "LastName")) if part).strip()
            for author in article.findall(".//Author")
        ]
        doi = ""
        for article_id in article.findall(".//ArticleId"):
            if article_id.attrib.get("IdType") == "doi":
                doi = article_id.text or ""
        records.append(
            {
                "title": title,
                "abstract": abstract,
                "authors": [author for author in authors if author],
                "first_author": next((author for author in authors if author), ""),
                "journal": _xml_text(article, ".//Journal/Title"),
                "year": _xml_text(article, ".//PubDate/Year"),
                "publication_date": _xml_text(article, ".//PubDate/Year"),
                "doi": doi,
                "pmid": pmid,
                "database_source": "PubMed XML",
                "source_type": SOURCE_PUBMED_XML,
                "source_record_id": pmid,
                "raw_extra": {"xml_source": "PubMedArticle"},
            }
        )
    return records


def _parse_wos_plain(text: str) -> list[dict[str, Any]]:
    blocks = re.split(r"\nER\s*\n", text)
    records: list[dict[str, Any]] = []
    for block in blocks:
        tags: dict[str, list[str]] = {}
        current = ""
        for line in block.splitlines():
            if len(line) >= 3 and re.match(r"^[A-Z0-9]{2} ", line[:3]):
                current = line[:2].strip()
                tags.setdefault(current, []).append(line[3:].strip())
            elif current and line.strip():
                tags[current][-1] = f"{tags[current][-1]} {line.strip()}".strip()
        if tags:
            records.append(_record_from_wos(tags))
    return records


def _record_from_wos(payload: dict[str, list[str]]) -> dict[str, Any]:
    authors = payload.get("AU") or []
    return {
        "title": _first(payload, "TI"),
        "abstract": _first(payload, "AB"),
        "authors": authors,
        "first_author": authors[0] if authors else "",
        "journal": _first(payload, "SO"),
        "year": _year(_first(payload, "PY")),
        "publication_date": _first(payload, "PY"),
        "doi": _first(payload, "DI"),
        "database_source": "Web of Science",
        "source_type": SOURCE_WOS_PLAIN,
        "source_record_id": _first(payload, "UT"),
        "keywords": [*_values(payload, "DE"), *_values(payload, "ID")],
        "raw_extra": {"wos_tags": payload},
    }


def _parse_cnki(text: str) -> list[dict[str, Any]]:
    blocks = [block for block in re.split(r"\n\s*\n", text) if block.strip()]
    records: list[dict[str, Any]] = []
    for block in blocks:
        fields: dict[str, str] = {}
        for line in block.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
            elif "：" in line:
                key, value = line.split("：", 1)
            else:
                continue
            fields[key.strip()] = value.strip()
        if fields:
            authors = _split_authors(fields.get("作者", ""))
            records.append(
                {
                    "title": fields.get("题名", "") or fields.get("篇名", ""),
                    "abstract": fields.get("摘要", ""),
                    "authors": authors,
                    "first_author": authors[0] if authors else "",
                    "journal": fields.get("来源", "") or fields.get("刊名", ""),
                    "year": _year(fields.get("年", "") or fields.get("发表时间", "")),
                    "publication_date": fields.get("发表时间", ""),
                    "doi": fields.get("DOI", ""),
                    "database_source": "CNKI",
                    "source_type": SOURCE_CNKI,
                    "source_record_id": fields.get("编号", ""),
                    "keywords": _split_authors(fields.get("关键词", "")),
                    "raw_extra": {"cnki_fields": fields},
                }
            )
    return records


def _diagnostics(records: list[dict[str, Any]], *, source_format: str) -> dict[str, Any]:
    warning_counts = {
        "缺少 DOI": 0,
        "缺少 PMID": 0,
        "缺少摘要": 0,
        "缺少年份": 0,
        "缺少期刊": 0,
        "作者字段不完整": 0,
        "标题可能异常": 0,
    }
    title_examples: list[str] = []
    for record in records:
        if not record.get("doi"):
            warning_counts["缺少 DOI"] += 1
        if not record.get("pmid"):
            warning_counts["缺少 PMID"] += 1
        if not record.get("abstract"):
            warning_counts["缺少摘要"] += 1
        if not record.get("year"):
            warning_counts["缺少年份"] += 1
        if not record.get("journal"):
            warning_counts["缺少期刊"] += 1
        if not record.get("authors"):
            warning_counts["作者字段不完整"] += 1
        title = str(record.get("title") or "")
        if _title_looks_abnormal(title):
            warning_counts["标题可能异常"] += 1
            if len(title_examples) < 5:
                title_examples.append(title[:160] or "(empty title)")
    return {
        "schema_version": MULTISOURCE_IMPORT_DIAGNOSTICS_SCHEMA_VERSION,
        "source_format": source_format,
        "warning_counts": warning_counts,
        "warning_count": sum(warning_counts.values()),
        "field_coverage": {
            "title": sum(1 for record in records if record.get("title")),
            "doi": sum(1 for record in records if record.get("doi")),
            "pmid": sum(1 for record in records if record.get("pmid")),
            "abstract": sum(1 for record in records if record.get("abstract")),
            "authors": sum(1 for record in records if record.get("authors")),
            "journal": sum(1 for record in records if record.get("journal")),
        },
        "field_mapping_warnings": _field_mapping_warnings(records, source_format=source_format),
        "title_abnormality_count": warning_counts["标题可能异常"],
        "title_abnormality_examples": title_examples,
    }


def _title_looks_abnormal(title: str) -> bool:
    text = title.strip()
    if not text:
        return True
    if "\ufffd" in text or "�" in text:
        return True
    if text.count("?") >= 3:
        return True
    letters = sum(1 for char in text if char.isalpha())
    return len(text) >= 12 and letters == 0


def _field_mapping_warnings(records: list[dict[str, Any]], *, source_format: str) -> list[str]:
    if not records:
        return [f"{source_format}: 未解析到可导入记录"]
    warnings: list[str] = []
    if all(not record.get("title") for record in records):
        warnings.append("未映射到标题字段")
    if all(not record.get("authors") for record in records):
        warnings.append("未映射到作者字段")
    if all(not record.get("journal") for record in records):
        warnings.append("未映射到期刊字段")
    return warnings[:5]


def _first(payload: dict[str, list[str]], *keys: str) -> str:
    for key in keys:
        values = payload.get(key, [])
        for value in values:
            if str(value).strip():
                return str(value).strip()
    return ""


def _values(payload: dict[str, list[str]], key: str) -> list[str]:
    return [str(item).strip() for item in payload.get(key, []) if str(item).strip()]


def _alias(row: dict[str, Any], *keys: str) -> str:
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for key in keys:
        value = normalized.get(key.strip().lower())
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _split_authors(value: str) -> list[str]:
    return [item.strip() for item in re.split(r";|\||, and | and ", value or "") if item.strip()]


def _doi_from_values(values: list[str]) -> str:
    for value in values:
        text = str(value)
        match = re.search(r"10\.\S+", text)
        if match:
            return match.group(0).rstrip(".")
    return ""


def _year(value: str) -> str:
    match = re.search(r"\b(19|20)\d{2}\b", str(value or ""))
    return match.group(0) if match else ""


def _xml_text(node: ET.Element, path: str) -> str:
    found = node.find(path)
    return (found.text or "").strip() if found is not None and found.text else ""


def _source_name(source_format: str) -> str:
    return {
        SOURCE_NBIB: "PubMed NBIB",
        SOURCE_MEDLINE: "PubMed MEDLINE",
        SOURCE_RIS: "RIS",
        SOURCE_PUBMED_XML: "PubMed XML",
        SOURCE_ENDNOTE: "EndNote",
        SOURCE_ZOTERO: "Zotero",
        SOURCE_WOS_PLAIN: "Web of Science",
        SOURCE_WOS_TAB: "Web of Science",
        SOURCE_CNKI: "CNKI",
        SOURCE_EMBASE_RIS: "Embase",
        SOURCE_COCHRANE_RIS: "Cochrane",
        SOURCE_CSV: "CSV",
    }.get(source_format, source_format)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "source"


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
