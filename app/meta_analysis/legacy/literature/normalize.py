from __future__ import annotations

import hashlib
import re
from typing import Iterable

from literature.models import NormalizedLiteratureRecord, ParsedLiteratureRecord


DOI_NOISE_PATTERN = re.compile(
    r"^(?:doi:\s*|doi\s+|https?://(?:dx\.)?doi\.org/)",
    re.IGNORECASE,
)
TITLE_PUNCT_PATTERN = re.compile(r"[^\w\s]", re.UNICODE)
IDENTIFIER_PATTERN = re.compile(r"\d+")


def collapse_whitespace(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_doi(value: str) -> str:
    cleaned = collapse_whitespace(value).lower()
    cleaned = DOI_NOISE_PATTERN.sub("", cleaned)
    cleaned = cleaned.strip(" .;")
    return cleaned


def normalize_pmid(value: str) -> str:
    cleaned = collapse_whitespace(value)
    match = IDENTIFIER_PATTERN.search(cleaned)
    if match is None:
        return ""
    return match.group(0)


def normalize_title(value: str) -> str:
    cleaned = collapse_whitespace(value).lower()
    cleaned = TITLE_PUNCT_PATTERN.sub(" ", cleaned)
    return collapse_whitespace(cleaned)


def normalize_person_name(value: str) -> str:
    cleaned = collapse_whitespace(value).lower()
    cleaned = TITLE_PUNCT_PATTERN.sub(" ", cleaned)
    return collapse_whitespace(cleaned)


def normalize_journal(value: str) -> str:
    cleaned = collapse_whitespace(value).lower()
    cleaned = TITLE_PUNCT_PATTERN.sub(" ", cleaned)
    return collapse_whitespace(cleaned)


class RecordNormalizationService:
    def normalize_record(self, record: ParsedLiteratureRecord) -> NormalizedLiteratureRecord:
        normalized_authors = [
            normalize_person_name(author)
            for author in record.authors
            if collapse_whitespace(author)
        ]
        record_id = record.record_id or self._build_record_id(record)
        return NormalizedLiteratureRecord(
            record_id=record_id,
            batch_id=record.batch_id,
            project_id=record.project_id,
            source=collapse_whitespace(record.source),
            source_record_id=collapse_whitespace(record.source_record_id),
            title=collapse_whitespace(record.title),
            abstract=collapse_whitespace(record.abstract),
            authors=[collapse_whitespace(author) for author in record.authors if collapse_whitespace(author)],
            journal=collapse_whitespace(record.journal),
            year=record.year,
            doi=collapse_whitespace(record.doi),
            pmid=collapse_whitespace(record.pmid),
            keywords=[collapse_whitespace(keyword) for keyword in record.keywords if collapse_whitespace(keyword)],
            language=collapse_whitespace(record.language).lower(),
            raw_payload=dict(record.raw_payload),
            title_normalized=normalize_title(record.title),
            doi_normalized=normalize_doi(record.doi),
            pmid_normalized=normalize_pmid(record.pmid),
            authors_normalized=normalized_authors,
            journal_normalized=normalize_journal(record.journal),
            year_normalized=record.year if isinstance(record.year, int) else None,
            source_trace=[record_id],
        )

    def normalize_records(
        self,
        records: Iterable[ParsedLiteratureRecord],
    ) -> list[NormalizedLiteratureRecord]:
        return [self.normalize_record(record) for record in records]

    def _build_record_id(self, record: ParsedLiteratureRecord) -> str:
        basis = "|".join(
            [
                record.project_id,
                record.batch_id,
                record.source,
                record.source_record_id,
                record.title,
                record.doi,
                record.pmid,
            ]
        )
        digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]
        return f"nrec-{digest}"
