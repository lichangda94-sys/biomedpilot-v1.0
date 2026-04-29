from __future__ import annotations

import csv
from pathlib import Path
import re

from literature.models import ImportFormatHint, ParsedLiteratureRecord
from literature.parser import ImportParseContext, LiteratureParser


RIS_TAG_PATTERN = re.compile(r"^([A-Z0-9]{2})\s{2}-\s?(.*)$")
NBIB_TAG_PATTERN = re.compile(r"^([A-Z0-9]{2,4})\s*-\s?(.*)$")
DOI_PATTERN = re.compile(r"(10\.\S+?)(?:\s*\[doi\])?$", re.IGNORECASE)
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


class BaseImportAdapter(LiteratureParser):
    supported_format: ImportFormatHint = ImportFormatHint.UNKNOWN
    adapter_name: str = "base"
    supported_formats: tuple[str, ...] = ("unknown",)

    def detect(self, input_path: Path) -> bool:
        return input_path.suffix.lower().lstrip(".") in self.supported_formats

    def get_diagnostics(self) -> dict[str, object]:
        return {"adapter_name": self.adapter_name, "supported_formats": list(self.supported_formats)}

    def parse(
        self,
        file_path: Path,
        context: ImportParseContext,
    ) -> list[ParsedLiteratureRecord]:
        return []

    def _read_text(self, file_path: Path) -> str:
        if not file_path.exists():
            raise ValueError(f"Input file does not exist: {file_path}")

        try:
            return file_path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"Could not decode {self.supported_format.value} file: {file_path}"
            ) from exc

    def _build_record(
        self,
        context: ImportParseContext,
        *,
        source: str,
        raw_payload: dict[str, object],
        source_record_id: str = "",
        title: str = "",
        abstract: str = "",
        authors: list[str] | None = None,
        journal: str = "",
        publication_title: str = "",
        date: str = "",
        year: int | None = None,
        doi: str = "",
        pmid: str = "",
        keywords: list[str] | None = None,
        publication_type: str = "unknown",
        clinical_trials_ids: list[str] | None = None,
        external_key: str = "",
        language: str = "",
    ) -> ParsedLiteratureRecord:
        return ParsedLiteratureRecord(
            batch_id=context.batch_id,
            project_id=context.project_id,
            source=source,
            source_record_id=source_record_id,
            title=title,
            abstract=abstract,
            authors=list(authors or []),
            authors_text="; ".join(authors or []),
            journal=journal,
            publication_title=publication_title or journal,
            date=date,
            year=year,
            doi=doi,
            pmid=pmid,
            keywords=list(keywords or []),
            publication_type=publication_type,
            clinical_trials_ids=list(clinical_trials_ids or []),
            external_key=external_key,
            language=language,
            raw_payload=raw_payload,
        )


class RisImportAdapter(BaseImportAdapter):
    supported_format = ImportFormatHint.RIS
    adapter_name = "ris"
    supported_formats = ("ris",)

    def parse(
        self,
        file_path: Path,
        context: ImportParseContext,
    ) -> list[ParsedLiteratureRecord]:
        text = self._read_text(file_path)
        records = _parse_tagged_records(text, RIS_TAG_PATTERN, terminator_tag="ER")
        if not records:
            raise ValueError(f"Could not parse RIS file: no records found in {file_path}")

        return [
            self._build_record(
                context,
                source=self.supported_format.value,
                source_record_id=_first_value(raw, "ID", "AN"),
                title=_first_value(raw, "TI", "T1", "CT"),
                abstract=_join_values(raw, "AB", "N2"),
                authors=_all_values(raw, "AU", "A1", "A2"),
                journal=_first_value(raw, "JO", "JF", "T2", "JA", "J1"),
                publication_title=_first_value(raw, "JO", "JF", "T2", "JA", "J1"),
                date=_first_value(raw, "PY", "Y1", "DA"),
                year=_extract_year(_first_value(raw, "PY", "Y1", "DA")),
                doi=_extract_doi(_first_value(raw, "DO", "M3")),
                pmid=_first_value(raw, "PM"),
                keywords=_all_values(raw, "KW"),
                publication_type=_publication_type_from_ris(_first_value(raw, "TY")),
                clinical_trials_ids=_clinical_trials_ids(_collapse_raw_payload(raw)),
                external_key=_first_value(raw, "ID", "C7"),
                language=_first_value(raw, "LA"),
                raw_payload=_collapse_raw_payload(raw),
            )
            for raw in records
        ]


class NbibImportAdapter(BaseImportAdapter):
    supported_format = ImportFormatHint.NBIB
    adapter_name = "nbib"
    supported_formats = ("nbib",)

    def parse(
        self,
        file_path: Path,
        context: ImportParseContext,
    ) -> list[ParsedLiteratureRecord]:
        text = self._read_text(file_path)
        records = _parse_tagged_records(text, NBIB_TAG_PATTERN)
        if not records:
            raise ValueError(
                f"Could not parse NBIB file: no records found in {file_path}"
            )

        return [
            self._build_record(
                context,
                source=self.supported_format.value,
                source_record_id=_first_value(raw, "PMID", "PMC", "PMCID"),
                title=_first_value(raw, "TI"),
                abstract=_join_values(raw, "AB"),
                authors=_all_values(raw, "FAU", "AU"),
                journal=_first_value(raw, "JT", "TA"),
                publication_title=_first_value(raw, "JT", "TA"),
                date=_first_value(raw, "DP", "DEP", "EDAT"),
                year=_extract_year(_first_value(raw, "DP", "DEP", "EDAT")),
                doi=_extract_doi(_first_value(raw, "AID", "LID")),
                pmid=_first_value(raw, "PMID"),
                keywords=_all_values(raw, "OT", "MH"),
                publication_type=_publication_type_from_nbib(_all_values(raw, "PT")),
                clinical_trials_ids=_clinical_trials_ids(_collapse_raw_payload(raw)),
                language=_first_value(raw, "LA"),
                raw_payload=_collapse_raw_payload(raw),
            )
            for raw in records
        ]


class CsvImportAdapter(BaseImportAdapter):
    supported_format = ImportFormatHint.CSV
    adapter_name = "csv"
    supported_formats = ("csv",)

    _ALIASES = {
        "source_record_id": {"source_record_id", "record_id", "source_id", "id"},
        "title": {"title", "article_title", "name"},
        "abstract": {"abstract", "summary", "description"},
        "authors": {"authors", "author", "creators"},
        "journal": {"journal", "journal_title", "publication", "source"},
        "publication_title": {"publication_title", "publicationtitle", "journal_title"},
        "year": {"year", "publication_year", "pub_year", "date"},
        "date": {"date", "publication_date"},
        "doi": {"doi"},
        "pmid": {"pmid"},
        "keywords": {"keywords", "keyword", "tags", "mesh_terms"},
        "publication_type": {"publication_type", "type", "item_type"},
        "clinical_trials_ids": {"clinical_trials_ids", "clinicaltrials", "nct", "trial_id"},
        "external_key": {"external_key", "citation_key", "better_bibtex_key"},
        "language": {"language", "lang"},
    }

    def parse(
        self,
        file_path: Path,
        context: ImportParseContext,
    ) -> list[ParsedLiteratureRecord]:
        if not file_path.exists():
            raise ValueError(f"Input file does not exist: {file_path}")

        try:
            with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    raise ValueError(
                        f"Could not parse CSV file: missing header row in {file_path}"
                    )

                normalized_headers = {_normalize_header(name) for name in reader.fieldnames if name}
                supported_headers = {
                    alias
                    for aliases in self._ALIASES.values()
                    for alias in aliases
                }
                if not normalized_headers.intersection(supported_headers):
                    raise ValueError(
                        f"Could not parse CSV file: no supported headers found in {file_path}"
                    )

                records: list[ParsedLiteratureRecord] = []
                for row in reader:
                    cleaned_row = {
                        key: (value.strip() if isinstance(value, str) else "")
                        for key, value in row.items()
                        if key is not None
                    }
                    if not any(cleaned_row.values()):
                        continue

                    source_record_id = self._get_value(cleaned_row, "source_record_id")
                    doi = self._get_value(cleaned_row, "doi")
                    pmid = self._get_value(cleaned_row, "pmid")
                    records.append(
                        self._build_record(
                            context,
                            source=self.supported_format.value,
                            source_record_id=source_record_id or pmid or doi,
                            title=self._get_value(cleaned_row, "title"),
                            abstract=self._get_value(cleaned_row, "abstract"),
                            authors=_split_multi_value(self._get_value(cleaned_row, "authors")),
                            journal=self._get_value(cleaned_row, "journal"),
                            publication_title=self._get_value(cleaned_row, "publication_title"),
                            date=self._get_value(cleaned_row, "date"),
                            year=_extract_year(self._get_value(cleaned_row, "year")),
                            doi=_extract_doi(doi),
                            pmid=pmid,
                            keywords=_split_multi_value(self._get_value(cleaned_row, "keywords")),
                            publication_type=self._get_value(cleaned_row, "publication_type") or "unknown",
                            clinical_trials_ids=_split_multi_value(self._get_value(cleaned_row, "clinical_trials_ids")),
                            external_key=self._get_value(cleaned_row, "external_key"),
                            language=self._get_value(cleaned_row, "language"),
                            raw_payload=cleaned_row,
                        )
                    )
                return records
        except UnicodeDecodeError as exc:
            raise ValueError(f"Could not decode csv file: {file_path}") from exc

    def _get_value(self, row: dict[str, str], field_name: str) -> str:
        for alias in self._ALIASES[field_name]:
            for key, value in row.items():
                if _normalize_header(key) == alias:
                    return value
        return ""


class ManualImportAdapter(BaseImportAdapter):
    supported_format = ImportFormatHint.MANUAL
    adapter_name = "manual"
    supported_formats = ("manual",)


def _parse_tagged_records(
    text: str,
    pattern: re.Pattern[str],
    *,
    terminator_tag: str | None = None,
) -> list[dict[str, list[str]]]:
    records: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] = {}
    last_tag: str | None = None
    saw_tag = False

    for line in text.splitlines():
        if not line.strip():
            if current and terminator_tag is None:
                records.append(current)
                current = {}
                last_tag = None
            continue

        match = pattern.match(line)
        if match:
            tag, value = match.groups()
            if terminator_tag is None and tag == "PMID" and current.get("PMID"):
                records.append(current)
                current = {}
            current.setdefault(tag, []).append(value.strip())
            last_tag = tag
            saw_tag = True
            if terminator_tag is not None and tag == terminator_tag:
                records.append(current)
                current = {}
                last_tag = None
            continue

        if last_tag is not None and current.get(last_tag):
            current[last_tag][-1] = f"{current[last_tag][-1]} {line.strip()}".strip()

    if current:
        records.append(current)

    if not saw_tag:
        return []
    return records


def _first_value(raw: dict[str, list[str]], *tags: str) -> str:
    for tag in tags:
        values = raw.get(tag, [])
        for value in values:
            if value:
                return value.strip()
    return ""


def _all_values(raw: dict[str, list[str]], *tags: str) -> list[str]:
    values: list[str] = []
    for tag in tags:
        values.extend(item.strip() for item in raw.get(tag, []) if item.strip())
    return values


def _join_values(raw: dict[str, list[str]], *tags: str) -> str:
    return " ".join(_all_values(raw, *tags)).strip()


def _extract_year(value: str) -> int | None:
    if not value:
        return None
    match = YEAR_PATTERN.search(value)
    if match is None:
        return None
    return int(match.group(0))


def _extract_doi(value: str) -> str:
    if not value:
        return ""
    stripped = value.strip()
    match = DOI_PATTERN.search(stripped)
    if match is not None:
        return match.group(1).rstrip(".,;")
    return stripped.replace("[doi]", "").strip()


def _collapse_raw_payload(raw: dict[str, list[str]]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for key, values in raw.items():
        if len(values) == 1:
            payload[key] = values[0]
        else:
            payload[key] = list(values)
    return payload


def _publication_type_from_ris(value: str) -> str:
    normalized = value.strip().upper()
    return {
        "JOUR": "journal_article",
        "CLIN": "clinical_trial",
        "CONF": "conference_abstract",
        "RPRT": "report",
        "THES": "thesis",
        "DATA": "dataset",
    }.get(normalized, "unknown")


def _publication_type_from_nbib(values: list[str]) -> str:
    lowered = " ".join(values).lower()
    if "randomized controlled trial" in lowered:
        return "randomized_trial"
    if "clinical trial" in lowered:
        return "clinical_trial"
    if "meta-analysis" in lowered:
        return "meta_analysis"
    if "systematic review" in lowered:
        return "systematic_review"
    if "review" in lowered:
        return "review"
    if "journal article" in lowered:
        return "journal_article"
    return "unknown"


def _clinical_trials_ids(payload: dict[str, object]) -> list[str]:
    joined = " ".join(str(value) for value in payload.values())
    return sorted(set(re.findall(r"\bNCT\d{8}\b", joined, flags=re.IGNORECASE)))


def _normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _split_multi_value(value: str) -> list[str]:
    if not value:
        return []
    for delimiter in (";", "|"):
        if delimiter in value:
            return [item.strip() for item in value.split(delimiter) if item.strip()]
    if " and " in value:
        return [item.strip() for item in value.split(" and ") if item.strip()]
    return [value.strip()]
