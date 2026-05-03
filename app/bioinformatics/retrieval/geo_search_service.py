from __future__ import annotations

import json
import ssl
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from app.bioinformatics.retrieval.bio_query_adapter import BioinformaticsQueryStrategy, build_bioinformatics_query_strategy


EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@dataclass(frozen=True)
class GeoDatasetResult:
    accession: str
    title: str
    summary: str
    query_used: str
    rank_score: float
    disease_relevance_reason: str
    broad_query_match: bool = False


@dataclass(frozen=True)
class GeoSearchResponse:
    query_text: str
    strategy: BioinformaticsQueryStrategy
    executed_queries: tuple[str, ...]
    results: tuple[GeoDatasetResult, ...]
    total_found: int
    search_status: str
    warnings: tuple[str, ...] = ()
    error_message: str = ""


class GeoSearchService:
    def __init__(self, *, opener: object | None = None) -> None:
        self._opener = opener

    def search(
        self,
        query_text: str,
        *,
        max_results: int = 20,
        include_supplemental: bool = False,
    ) -> GeoSearchResponse:
        strategy = build_bioinformatics_query_strategy(query_text)
        if strategy.broad_query_guard_triggered and not include_supplemental:
            return GeoSearchResponse(
                query_text=query_text,
                strategy=strategy,
                executed_queries=(),
                results=(),
                total_found=0,
                search_status="blocked_broad_query",
                warnings=tuple([*strategy.warnings, "已阻止只有平台词的宽泛 GEO 检索。"]),
            )
        queries = list(strategy.confirmed_geo_queries)
        if include_supplemental:
            queries.extend(strategy.supplemental_geo_queries)
        queries = _unique(queries)[:6]
        if not queries:
            return GeoSearchResponse(
                query_text=query_text,
                strategy=strategy,
                executed_queries=(),
                results=(),
                total_found=0,
                search_status="no_query",
                warnings=tuple(strategy.warnings),
            )
        try:
            results = self._execute_queries(queries, strategy, max_results=max_results)
        except Exception as exc:
            return GeoSearchResponse(
                query_text=query_text,
                strategy=strategy,
                executed_queries=tuple(queries),
                results=(),
                total_found=0,
                search_status="failed",
                warnings=tuple(strategy.warnings),
                error_message=str(exc),
            )
        return GeoSearchResponse(
            query_text=query_text,
            strategy=strategy,
            executed_queries=tuple(queries),
            results=tuple(results[:max_results]),
            total_found=len(results),
            search_status="completed",
            warnings=tuple(strategy.warnings),
        )

    def _execute_queries(
        self,
        queries: list[str],
        strategy: BioinformaticsQueryStrategy,
        *,
        max_results: int,
    ) -> list[GeoDatasetResult]:
        by_accession: dict[str, GeoDatasetResult] = {}
        confirmed_keys = {query.lower() for query in strategy.confirmed_geo_queries}
        for query in queries:
            ids = self._esearch(_geo_series_query(query), retmax=max_results)
            for payload in self._esummary(ids):
                result = _result_from_payload(
                    payload,
                    query_used=query,
                    disease_terms=strategy.disease_terms,
                    broad_query_match=query.lower() not in confirmed_keys,
                )
                existing = by_accession.get(result.accession)
                if existing is None or result.rank_score > existing.rank_score:
                    by_accession[result.accession] = result
        return sorted(by_accession.values(), key=lambda item: (-item.rank_score, item.accession))

    def _esearch(self, term: str, *, retmax: int) -> list[str]:
        payload = self._get_json(
            f"{EUTILS_BASE}/esearch.fcgi",
            {
                "db": "gds",
                "term": term,
                "retmode": "json",
                "retmax": str(retmax),
            },
        )
        return [str(uid) for uid in payload.get("esearchresult", {}).get("idlist", [])]

    def _esummary(self, ids: list[str]) -> list[dict[str, Any]]:
        if not ids:
            return []
        payload = self._get_json(
            f"{EUTILS_BASE}/esummary.fcgi",
            {
                "db": "gds",
                "id": ",".join(ids),
                "retmode": "json",
            },
        )
        result = payload.get("result", {})
        return [item for uid, item in result.items() if uid != "uids" and isinstance(item, dict)]

    def _get_json(self, url: str, params: dict[str, str]) -> dict[str, Any]:
        full_url = f"{url}?{urlencode(params)}"
        if self._opener is not None:
            return self._opener(full_url)  # type: ignore[misc]
        with urlopen(full_url, timeout=20, context=_ssl_context()) as response:  # nosec B310 - fixed NCBI endpoint.
            return json.loads(response.read().decode("utf-8"))


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _geo_series_query(query: str) -> str:
    if "GSE[ETYP]" in query:
        return query
    return f"({query}) AND GSE[ETYP]"


def _result_from_payload(
    payload: dict[str, Any],
    *,
    query_used: str,
    disease_terms: tuple[str, ...],
    broad_query_match: bool,
) -> GeoDatasetResult:
    accession = str(payload.get("accession") or payload.get("Accession") or payload.get("gse") or payload.get("uid") or "")
    title = str(payload.get("title") or payload.get("Title") or "")
    summary = str(payload.get("summary") or payload.get("Summary") or "")
    score, reason = _relevance(title=title, summary=summary, disease_terms=disease_terms, broad_query_match=broad_query_match)
    return GeoDatasetResult(
        accession=accession,
        title=title,
        summary=summary,
        query_used=query_used,
        rank_score=score,
        disease_relevance_reason=reason,
        broad_query_match=broad_query_match,
    )


def _relevance(*, title: str, summary: str, disease_terms: tuple[str, ...], broad_query_match: bool) -> tuple[float, str]:
    text = f"{title} {summary}".lower()
    title_lower = title.lower()
    matched = [term for term in disease_terms if term.lower() in text]
    score = 0.0
    reasons: list[str] = []
    if matched:
        score += 4.0
        reasons.append(f"标题/摘要匹配疾病词：{', '.join(matched[:3])}")
    if any(term.lower() in title_lower for term in matched):
        score += 2.0
        reasons.append("标题包含疾病词")
    if broad_query_match:
        score -= 2.0
        reasons.append("仅由补充宽泛 query 命中，已降权")
    if not reasons:
        reasons.append("未在标题/摘要中发现明确疾病词")
    return score, "；".join(reasons)


def _unique(values: object) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:  # type: ignore[union-attr]
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            items.append(text)
    return items
