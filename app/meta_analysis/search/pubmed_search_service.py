from __future__ import annotations

import json
import re
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4


Fetcher = Callable[[str, float], bytes]


@dataclass(frozen=True)
class PubMedCountPreview:
    success: bool
    query: str
    result_count: int = 0
    errors: tuple[dict[str, str], ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "database": "PubMed",
            "query_used": self.query,
            "success": self.success,
            "result_count": self.result_count,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class PubMedSearchResult:
    pmid: str
    title: str
    journal: str
    year: str
    authors: tuple[str, ...]
    abstract: str
    snippet: str
    url: str
    query_used: str
    doi: str = ""
    pmcid: str = ""
    publication_date: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "pmid": self.pmid,
            "doi": self.doi,
            "pmcid": self.pmcid,
            "title": self.title,
            "journal": self.journal,
            "year": self.year,
            "publication_date": self.publication_date,
            "authors": list(self.authors),
            "abstract": self.abstract,
            "snippet": self.snippet,
            "url": self.url,
            "query_used": self.query_used,
        }


@dataclass(frozen=True)
class PubMedSearchExecution:
    success: bool
    query_used: str
    executed_at: str
    result_count: int = 0
    returned_count: int = 0
    records: tuple[PubMedSearchResult, ...] = ()
    dedup_summary: dict[str, int] = field(default_factory=dict)
    errors: tuple[dict[str, str], ...] = ()
    warnings: tuple[str, ...] = ()
    search_execution_id: str = field(default_factory=lambda: f"pubmedexec-{uuid4().hex[:12]}")

    @property
    def pmids(self) -> tuple[str, ...]:
        return tuple(record.pmid for record in self.records if record.pmid)

    def to_report(self) -> dict[str, object]:
        return {
            "schema_version": "meta_pubmed_search_execution.v1",
            "search_execution_id": self.search_execution_id,
            "database": "PubMed",
            "query_used": self.query_used,
            "executed_at": self.executed_at,
            "success": self.success,
            "result_count": self.result_count,
            "returned_count": self.returned_count,
            "pmids": list(self.pmids),
            "records": [record.to_dict() for record in self.records],
            "dedup_summary": self.dedup_summary,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "literature_import_status": "not_imported",
            "screening_status": "not_started",
            "auto_imported": False,
            "auto_screened": False,
            "wos_status": "draft_only",
            "embase_status": "draft_only",
            "cnki_status": "draft_only",
        }


class PubMedSearchService:
    def __init__(self, *, fetcher: Fetcher | None = None) -> None:
        self._fetcher = fetcher or _default_fetcher

    def preview_pubmed_count(self, query: str, *, timeout_seconds: float = 10.0) -> PubMedCountPreview:
        normalized_query = query.strip()
        if not normalized_query:
            return PubMedCountPreview(
                success=False,
                query=query,
                errors=({"code": "empty_query", "message": "PubMed query is empty."},),
            )
        try:
            search = self._esearch(normalized_query, retmax=0, timeout_seconds=timeout_seconds)
            return PubMedCountPreview(success=True, query=normalized_query, result_count=search["count"])
        except Exception as exc:
            return PubMedCountPreview(
                success=False,
                query=normalized_query,
                errors=({"code": "pubmed_preview_failed", "message": str(exc)},),
            )

    def search_pubmed(
        self,
        query: str,
        *,
        max_results: int = 20,
        timeout_seconds: float = 10.0,
    ) -> PubMedSearchExecution:
        normalized_query = query.strip()
        executed_at = _now()
        if not normalized_query:
            return PubMedSearchExecution(
                success=False,
                query_used=query,
                executed_at=executed_at,
                errors=({"code": "empty_query", "message": "PubMed query is empty."},),
            )
        try:
            search = self._esearch(normalized_query, retmax=max_results, timeout_seconds=timeout_seconds)
            records = self._efetch(search["ids"], query_used=normalized_query, timeout_seconds=timeout_seconds)
            records, duplicate_count = _deduplicate_records(records)
            warnings = ("pubmed_search_returned_no_records",) if not records else ()
            return PubMedSearchExecution(
                success=True,
                query_used=normalized_query,
                executed_at=executed_at,
                result_count=search["count"],
                returned_count=len(records),
                records=tuple(records),
                dedup_summary={
                    "requested_pmids": len(search["ids"]),
                    "unique_pmids": len(records),
                    "duplicate_pmids_removed": duplicate_count,
                },
                warnings=warnings,
            )
        except Exception as exc:
            return PubMedSearchExecution(
                success=False,
                query_used=normalized_query,
                executed_at=executed_at,
                errors=({"code": "pubmed_search_failed", "message": str(exc)},),
            )

    def search_pubmed_for_queries(
        self,
        queries: list[str],
        *,
        max_results: int = 20,
        timeout_seconds: float = 10.0,
    ) -> PubMedSearchExecution:
        normalized_queries = [query.strip() for query in queries if query.strip()]
        executed_at = _now()
        if not normalized_queries:
            return PubMedSearchExecution(
                success=False,
                query_used="",
                executed_at=executed_at,
                errors=({"code": "empty_query", "message": "No PubMed queries were provided."},),
            )
        records: list[PubMedSearchResult] = []
        result_count = 0
        errors: list[dict[str, str]] = []
        requested_pmids = 0
        for query in normalized_queries:
            execution = self.search_pubmed(query, max_results=max_results, timeout_seconds=timeout_seconds)
            result_count += execution.result_count
            requested_pmids += execution.dedup_summary.get("requested_pmids", 0)
            records.extend(execution.records)
            errors.extend(execution.errors)
        records, duplicate_count = _deduplicate_records(records)
        return PubMedSearchExecution(
            success=not errors,
            query_used=" OR ".join(normalized_queries),
            executed_at=executed_at,
            result_count=result_count,
            returned_count=len(records),
            records=tuple(records),
            dedup_summary={
                "requested_pmids": requested_pmids,
                "unique_pmids": len(records),
                "duplicate_pmids_removed": duplicate_count,
            },
            errors=tuple(errors),
        )

    def _esearch(self, query: str, *, retmax: int, timeout_seconds: float) -> dict[str, object]:
        url = _pubmed_url(
            "esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmax": str(max(0, min(retmax, 100))),
                "retmode": "json",
                "tool": "BioMedPilot",
            },
        )
        payload = json.loads(self._fetcher(url, timeout_seconds).decode("utf-8"))
        result = payload.get("esearchresult", {})
        ids = [str(item) for item in result.get("idlist", [])]
        count = str(result.get("count") or len(ids))
        return {"ids": ids, "count": int(count) if count.isdigit() else len(ids)}

    def _efetch(
        self,
        pmids: list[str],
        *,
        query_used: str,
        timeout_seconds: float,
    ) -> list[PubMedSearchResult]:
        if not pmids:
            return []
        url = _pubmed_url(
            "efetch.fcgi",
            {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "tool": "BioMedPilot",
            },
        )
        root = ET.fromstring(self._fetcher(url, timeout_seconds).decode("utf-8"))
        return [_record_from_pubmed_article(article, query_used=query_used) for article in root.findall(".//PubmedArticle")]


def _deduplicate_records(records: list[PubMedSearchResult]) -> tuple[list[PubMedSearchResult], int]:
    seen: set[str] = set()
    unique: list[PubMedSearchResult] = []
    duplicate_count = 0
    for record in records:
        key = record.pmid or f"{record.title.lower()}|{record.journal.lower()}|{record.year}"
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        unique.append(record)
    return unique, duplicate_count


def _record_from_pubmed_article(article: ET.Element, *, query_used: str) -> PubMedSearchResult:
    pmid = _text(article, ".//MedlineCitation/PMID")
    doi = ""
    pmcid = ""
    for article_id in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
        id_type = str(article_id.attrib.get("IdType", "")).lower()
        value = _text_from(article_id)
        if id_type == "doi":
            doi = value
        elif id_type == "pmc":
            pmcid = value
    title = _iter_text(article.find(".//ArticleTitle"))
    abstract = " ".join(_iter_text(item) for item in article.findall(".//Abstract/AbstractText")).strip()
    journal = _text(article, ".//Journal/Title")
    year = _year_from_article(article)
    authors: list[str] = []
    for author in article.findall(".//AuthorList/Author"):
        collective = _text_from(author.find("CollectiveName"))
        if collective:
            authors.append(collective)
            continue
        last = _text_from(author.find("LastName"))
        fore = _text_from(author.find("ForeName"))
        full = " ".join(part for part in (fore, last) if part).strip()
        if full:
            authors.append(full)
    return PubMedSearchResult(
        pmid=pmid,
        doi=doi,
        pmcid=pmcid,
        title=title,
        journal=journal,
        year=str(year or ""),
        publication_date=_publication_date_from_article(article),
        authors=tuple(authors),
        abstract=abstract,
        snippet=abstract[:280],
        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        query_used=query_used,
    )


def _default_fetcher(url: str, timeout_seconds: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "BioMedPilot Developer Preview"})
    context = _ssl_context()
    with urllib.request.urlopen(request, timeout=timeout_seconds, context=context) as response:  # nosec B310 - PubMed E-utilities read-only query.
        return response.read()


def _ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi
    except Exception:
        return None
    return ssl.create_default_context(cafile=certifi.where())


def _pubmed_url(endpoint: str, params: dict[str, str]) -> str:
    return "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/" + endpoint + "?" + urllib.parse.urlencode(params)


def _text(root: ET.Element, path: str) -> str:
    return _text_from(root.find(path))


def _text_from(element: ET.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def _iter_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join(text.strip() for text in element.itertext() if text and text.strip())


def _year_from_article(article: ET.Element) -> int | None:
    year = _text(article, ".//JournalIssue/PubDate/Year") or _text(article, ".//ArticleDate/Year")
    if year.isdigit():
        return int(year)
    medline = _text(article, ".//JournalIssue/PubDate/MedlineDate")
    match = re.search(r"\b(19|20)\d{2}\b", medline)
    return int(match.group(0)) if match else None


def _publication_date_from_article(article: ET.Element) -> str:
    year = _text(article, ".//JournalIssue/PubDate/Year") or _text(article, ".//ArticleDate/Year")
    month = _text(article, ".//JournalIssue/PubDate/Month") or _text(article, ".//ArticleDate/Month")
    day = _text(article, ".//JournalIssue/PubDate/Day") or _text(article, ".//ArticleDate/Day")
    return "-".join(part for part in (year, month, day) if part)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
