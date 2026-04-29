from __future__ import annotations

import hashlib
import re
from typing import Iterable

from literature.models import Creator, NormalizedLiteratureRecord, ParsedLiteratureRecord
from literature.schema import CREATOR_TYPES, PUBLICATION_TYPES


DOI_NOISE_PATTERN = re.compile(
    r"^(?:doi:\s*|doi\s+|https?://(?:dx\.)?doi\.org/)",
    re.IGNORECASE,
)
TITLE_PUNCT_PATTERN = re.compile(r"[^\w\s]", re.UNICODE)
IDENTIFIER_PATTERN = re.compile(r"\d+")
YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")


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
    cleaned = collapse_whitespace(value).rstrip(".。").lower()
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


def normalize_year(value: int | str | None) -> int | None:
    if isinstance(value, int):
        return value
    if value is None:
        return None
    match = YEAR_PATTERN.search(str(value))
    return int(match.group(0)) if match else None


def normalize_publication_type(value: str) -> str:
    cleaned = collapse_whitespace(value).lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "journal": "journal_article",
        "article": "journal_article",
        "clinicaltrial": "clinical_trial",
        "randomizedcontrolledtrial": "randomized_trial",
        "randomized_controlled_trial": "randomized_trial",
        "meta_analysis": "meta_analysis",
        "systematic_review": "systematic_review",
    }
    cleaned = aliases.get(cleaned, cleaned)
    return cleaned if cleaned in PUBLICATION_TYPES else "unknown"


def normalize_creator(raw: str | dict[str, object] | Creator, order: int) -> Creator:
    if isinstance(raw, Creator):
        creator_type = raw.creator_type if raw.creator_type in CREATOR_TYPES else "unknown"
        return Creator(
            first_name=collapse_whitespace(raw.first_name),
            last_name=collapse_whitespace(raw.last_name),
            full_name=collapse_whitespace(raw.full_name or raw.raw),
            creator_type=creator_type,
            order=raw.order or order,
            raw=collapse_whitespace(raw.raw or raw.full_name),
        )
    if isinstance(raw, dict):
        creator_type = str(raw.get("creator_type", "author")).strip().lower()
        if creator_type not in CREATOR_TYPES:
            creator_type = "unknown"
        full_name = collapse_whitespace(str(raw.get("full_name") or raw.get("name") or raw.get("raw") or ""))
        first_name = collapse_whitespace(str(raw.get("first_name", "")))
        last_name = collapse_whitespace(str(raw.get("last_name", "")))
        raw_text = collapse_whitespace(str(raw.get("raw") or full_name))
        if not full_name:
            full_name = collapse_whitespace(f"{first_name} {last_name}")
        return Creator(first_name=first_name, last_name=last_name, full_name=full_name, creator_type=creator_type, order=order, raw=raw_text)
    raw_text = collapse_whitespace(str(raw))
    if "," in raw_text:
        last_name, first_name = [part.strip() for part in raw_text.split(",", 1)]
        full_name = collapse_whitespace(f"{first_name} {last_name}")
    else:
        parts = raw_text.split()
        first_name = " ".join(parts[:-1]) if len(parts) > 1 else ""
        last_name = parts[-1] if parts else ""
        full_name = raw_text
    return Creator(first_name=first_name, last_name=last_name, full_name=full_name, creator_type="author", order=order, raw=raw_text)


def normalize_creators(record: ParsedLiteratureRecord) -> list[Creator]:
    source_creators: list[object] = list(record.creators) if record.creators else list(record.authors)
    return [normalize_creator(item, index) for index, item in enumerate(source_creators, start=1) if collapse_whitespace(str(item))]


class RecordNormalizationService:
    def normalize_record(self, record: ParsedLiteratureRecord) -> NormalizedLiteratureRecord:
        creators = normalize_creators(record)
        authors = [creator.full_name for creator in creators if creator.creator_type in {"author", "group_author", "corresponding_author"}]
        normalized_authors = [
            normalize_person_name(author)
            for author in authors
            if collapse_whitespace(author)
        ]
        record_id = record.record_id or self._build_record_id(record)
        year = normalize_year(record.year if record.year is not None else record.date)
        journal = record.journal or record.publication_title
        authors_text = record.authors_text or "; ".join(authors)
        return NormalizedLiteratureRecord(
            record_id=record_id,
            batch_id=record.batch_id,
            project_id=record.project_id,
            source=collapse_whitespace(record.source),
            source_record_id=collapse_whitespace(record.source_record_id),
            title=collapse_whitespace(record.title),
            abstract=collapse_whitespace(record.abstract),
            authors=[collapse_whitespace(author) for author in authors if collapse_whitespace(author)],
            authors_text=authors_text,
            creators=creators,
            first_author=authors[0] if authors else "",
            journal=collapse_whitespace(journal),
            publication_title=collapse_whitespace(record.publication_title or record.journal),
            date=collapse_whitespace(record.date),
            year=year,
            doi=collapse_whitespace(record.doi),
            pmid=collapse_whitespace(record.pmid),
            keywords=[collapse_whitespace(keyword) for keyword in record.keywords if collapse_whitespace(keyword)],
            publication_type=normalize_publication_type(record.publication_type),
            clinical_trials_ids=[collapse_whitespace(item) for item in record.clinical_trials_ids if collapse_whitespace(item)],
            external_key=collapse_whitespace(record.external_key),
            language=collapse_whitespace(record.language).lower(),
            raw_payload=dict(record.raw_payload),
            title_normalized=normalize_title(record.title),
            doi_normalized=normalize_doi(record.doi),
            pmid_normalized=normalize_pmid(record.pmid),
            authors_normalized=normalized_authors,
            journal_normalized=normalize_journal(journal),
            year_normalized=year,
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
