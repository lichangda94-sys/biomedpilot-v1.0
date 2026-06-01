from __future__ import annotations

import json
import re
import ssl
from dataclasses import dataclass
from pathlib import Path
import sys
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


@dataclass(frozen=True)
class GeoDatasetSearchItem:
    accession: str
    title: str
    summary: str
    organism: str
    sample_count: int | str
    platform_accessions: tuple[str, ...]
    platform_titles: tuple[str, ...]
    publication_date: str
    update_date: str
    geo_url: str
    data_type: str
    tissue_disease_keywords: tuple[str, ...]
    match_reason: str
    relevance_score: int
    can_register: bool = True
    can_download: bool = False
    query_used: str = ""
    has_series_matrix: bool = False
    has_supplementary_files: bool = False
    has_sample_metadata: bool = False
    has_group_hint: bool = False
    recommended_analyses: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeoDatasetSearchResponse:
    search_status: str
    executed_query: str
    total_found: int | None
    results: tuple[GeoDatasetSearchItem, ...]
    warnings: tuple[str, ...]
    error_message: str
    start: int
    next_start: int | None
    fetched_all: bool


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
        explicit_accessions = _explicit_gse_accessions(query_text)
        if explicit_accessions:
            queries = [f"{accession}[ACCN] AND GSE[ETYP]" for accession in explicit_accessions]
            try:
                results = self._execute_accession_queries(queries, max_results=max_results)
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
                warnings=tuple([*_warnings_without_broad_query_guard(strategy.warnings), "explicit_gse_accession_search"]),
            )
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

    def _execute_accession_queries(self, queries: list[str], *, max_results: int) -> list[GeoDatasetResult]:
        by_accession: dict[str, GeoDatasetResult] = {}
        for query in queries:
            ids = self._esearch(query, retmax=max_results)
            for payload in self._esummary(ids):
                result = _result_from_payload(
                    payload,
                    query_used=query,
                    disease_terms=(),
                    broad_query_match=False,
                )
                if result.accession:
                    by_accession[result.accession] = result
        return sorted(by_accession.values(), key=lambda item: item.accession)

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


def _explicit_gse_accessions(query_text: str) -> list[str]:
    return _unique(match.upper() for match in re.findall(r"\bGSE\d+\b", query_text, flags=re.IGNORECASE))


def _warnings_without_broad_query_guard(warnings: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(warning for warning in warnings if "宽泛 GEO query" not in warning)


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


def search_geo_datasets(
    query: str,
    *,
    max_results: int = 20,
    organism: str | None = None,
    platform_type: str | None = None,
    timeout: int = 8,
    offline_mode: bool = False,
    start: int = 0,
    fetcher_cls: type[Any] | None | object = ...,
) -> GeoDatasetSearchResponse:
    cleaned_query = _with_optional_filters(query.strip(), organism=organism, platform_type=platform_type)
    normalized_start = max(0, int(start or 0))
    normalized_max = max(1, min(int(max_results or 20), 100))
    if offline_mode:
        return GeoDatasetSearchResponse(
            search_status="offline",
            executed_query=cleaned_query,
            total_found=None,
            results=(),
            warnings=("当前仅生成检索词，尚未执行 GEO 在线检索。",),
            error_message="",
            start=normalized_start,
            next_start=None,
            fetched_all=True,
        )

    resolved_fetcher_cls = _geo_fetcher_class() if fetcher_cls is ... else fetcher_cls
    if resolved_fetcher_cls is None:
        return GeoDatasetSearchResponse(
            search_status="search_failed",
            executed_query=cleaned_query,
            total_found=None,
            results=(),
            warnings=("当前没有可用的 GEO 在线检索服务。",),
            error_message="GEO search service is unavailable",
            start=normalized_start,
            next_start=None,
            fetched_all=True,
        )

    try:
        response = resolved_fetcher_cls(timeout=timeout).search_series(
            cleaned_query,
            max_results=normalized_max,
            page_size=normalized_max,
            start=normalized_start,
        )
    except Exception as exc:
        return GeoDatasetSearchResponse(
            search_status="search_failed",
            executed_query=cleaned_query,
            total_found=None,
            results=(),
            warnings=("GEO 在线检索失败，请检查网络或稍后重试。已保留可复制检索式。",),
            error_message=str(exc),
            start=normalized_start,
            next_start=None,
            fetched_all=True,
        )

    terms = _query_terms(cleaned_query)
    items = tuple(_item_from_geo_series(item, terms) for item in getattr(response, "results", []) or [])
    next_start = int(getattr(response, "next_start", normalized_start) or normalized_start)
    fetched_all = bool(getattr(response, "fetched_all", True))
    total_found = int(getattr(response, "total_count", len(items)) or 0)
    return GeoDatasetSearchResponse(
        search_status="completed",
        executed_query=str(getattr(response, "query", cleaned_query) or cleaned_query),
        total_found=total_found,
        results=items,
        warnings=() if items else ("未检索到匹配数据集，可尝试减少限定词或改用英文关键词。",),
        error_message="",
        start=normalized_start,
        next_start=next_start if not fetched_all else None,
        fetched_all=fetched_all,
    )


def search_geo_datasets_for_queries(
    queries: list[str] | tuple[str, ...],
    *,
    max_results_per_query: int = 20,
    timeout: int = 8,
    start: int = 0,
    fetcher_cls: type[Any] | None | object = ...,
) -> GeoDatasetSearchResponse:
    cleaned_queries = tuple(dict.fromkeys(query.strip() for query in queries if query.strip()))
    if not cleaned_queries:
        return GeoDatasetSearchResponse(
            search_status="search_failed",
            executed_query="",
            total_found=None,
            results=(),
            warnings=("请先勾选至少一个 GEO query 草稿。",),
            error_message="No GEO queries selected",
            start=max(0, int(start or 0)),
            next_start=None,
            fetched_all=True,
        )
    warnings: list[str] = []
    errors: list[str] = []
    by_accession: dict[str, GeoDatasetSearchItem] = {}
    total_found = 0
    completed_count = 0
    next_values: list[int] = []
    fetched_all = True
    for query in cleaned_queries:
        response = search_geo_datasets(
            query,
            max_results=max_results_per_query,
            timeout=timeout,
            start=start,
            fetcher_cls=fetcher_cls,
        )
        if response.total_found is not None:
            total_found += response.total_found
        warnings.extend(response.warnings)
        if response.error_message:
            errors.append(response.error_message)
        if response.search_status == "completed":
            completed_count += 1
        if response.next_start is not None:
            next_values.append(response.next_start)
            fetched_all = False
        for item in response.results:
            key = item.accession.strip().upper()
            if not key:
                continue
            scored = GeoDatasetSearchItem(
                accession=item.accession,
                title=item.title,
                summary=item.summary,
                organism=item.organism,
                sample_count=item.sample_count,
                platform_accessions=item.platform_accessions,
                platform_titles=item.platform_titles,
                publication_date=item.publication_date,
                update_date=item.update_date,
                geo_url=item.geo_url,
                data_type=item.data_type,
                tissue_disease_keywords=item.tissue_disease_keywords,
                match_reason=item.match_reason,
                relevance_score=item.relevance_score,
                can_register=item.can_register,
                can_download=item.can_download,
                query_used=response.executed_query or query,
                has_series_matrix=item.has_series_matrix,
                has_supplementary_files=item.has_supplementary_files,
                has_sample_metadata=item.has_sample_metadata,
                has_group_hint=item.has_group_hint,
                recommended_analyses=item.recommended_analyses,
                warnings=item.warnings,
            )
            existing = by_accession.get(key)
            if existing is None or scored.relevance_score > existing.relevance_score:
                by_accession[key] = scored
    status = "completed" if completed_count else "search_failed"
    return GeoDatasetSearchResponse(
        search_status=status,
        executed_query=" | ".join(cleaned_queries),
        total_found=total_found if completed_count else None,
        results=tuple(by_accession.values()),
        warnings=tuple(dict.fromkeys(warnings)),
        error_message="；".join(dict.fromkeys(errors)),
        start=max(0, int(start or 0)),
        next_start=min(next_values) if next_values else None,
        fetched_all=fetched_all,
    )


def _item_from_geo_series(item: Any, query_terms: tuple[str, ...]) -> GeoDatasetSearchItem:
    accession = str(getattr(item, "gse_id", "") or "")
    title = str(getattr(item, "title_en", "") or getattr(item, "title", "") or "未记录标题")
    summary = str(getattr(item, "summary_en", "") or getattr(item, "summary", "") or "")
    organism = str(getattr(item, "organism", "") or "未记录")
    platform = str(getattr(item, "platform", "") or "")
    experiment_type = str(getattr(item, "experiment_type", "") or _infer_data_type(title, summary, platform))
    text = " ".join([title, summary, organism, platform, experiment_type]).lower()
    matched = tuple(dict.fromkeys(term for term in query_terms if term.lower() in text))
    score = _relevance_score(text, matched)
    has_sample_metadata = bool(getattr(item, "sample_count", 0))
    has_group_hint = any(token in text for token in ("normal", "tumor", "control", "case", "metastasis"))
    return GeoDatasetSearchItem(
        accession=accession,
        title=title,
        summary=summary,
        organism=organism,
        sample_count=getattr(item, "sample_count", 0) or "未记录",
        platform_accessions=_split_platforms(platform),
        platform_titles=(),
        publication_date=str(getattr(item, "publication_date", "") or ""),
        update_date=str(getattr(item, "update_date", "") or ""),
        geo_url=str(getattr(item, "geo_url", "") or f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}"),
        data_type=experiment_type or "未记录",
        tissue_disease_keywords=matched[:8],
        match_reason="、".join(matched[:5]) if matched else "与当前 GEO 查询返回结果匹配",
        relevance_score=score,
        can_register=bool(accession),
        can_download=False,
        query_used="",
        has_series_matrix=bool(accession),
        has_supplementary_files=bool(getattr(item, "has_supplementary_files", False)),
        has_sample_metadata=has_sample_metadata,
        has_group_hint=has_group_hint,
        recommended_analyses=_recommended_analyses(experiment_type, has_group_hint),
        warnings=_geo_candidate_warnings(accession, has_group_hint),
    )


def _with_optional_filters(query: str, *, organism: str | None, platform_type: str | None) -> str:
    parts = [query] if query else []
    if organism and "[Organism]" not in query:
        parts.append(f"{organism}[Organism]")
    if platform_type:
        parts.append(platform_type)
    return " AND ".join(part for part in parts if part)


def _query_terms(query: str) -> tuple[str, ...]:
    cleaned = query.replace("(", " ").replace(")", " ").replace('"', " ")
    for splitter in (" AND ", " OR "):
        cleaned = cleaned.replace(splitter, "|")
    tokens = [part.strip() for part in cleaned.split("|") if part.strip() and "[" not in part and len(part.strip()) > 2]
    return tuple(dict.fromkeys(tokens))


def _split_platforms(platform: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in platform.replace(";", ",").split(",") if part.strip())


def _infer_data_type(title: str, summary: str, platform: str) -> str:
    text = " ".join([title, summary, platform]).lower()
    if "rna-seq" in text or "rna seq" in text or "transcriptome" in text:
        return "RNA-seq / transcriptome"
    if "microarray" in text or "gpl" in text:
        return "microarray / expression profiling"
    if "expression" in text:
        return "expression profiling"
    return "未记录"


def _relevance_score(text: str, matched: tuple[str, ...]) -> int:
    base = 20 if matched else 10
    weighted = sum(18 if term in text[:300] else 10 for term in matched[:6])
    return min(100, base + weighted)


def _recommended_analyses(data_type: str, has_group_hint: bool) -> tuple[str, ...]:
    values = ["data_recognition"]
    if any(token in data_type.lower() for token in ("expression", "rna", "microarray", "transcriptome")):
        values.append("differential_expression")
    if has_group_hint:
        values.append("group_comparison")
    return tuple(values)


def _geo_candidate_warnings(accession: str, has_group_hint: bool) -> tuple[str, ...]:
    warnings: list[str] = []
    if not accession:
        warnings.append("缺少 GSE accession，无法登记。")
    if not has_group_hint:
        warnings.append("未识别到明确分组线索，需人工确认样本分组。")
    return tuple(warnings)


def _geo_fetcher_class() -> type[Any] | None:
    try:
        legacy_root = Path(__file__).resolve().parents[1] / "legacy"
        for path in (legacy_root, legacy_root / "geo_tool"):
            text = str(path)
            if text not in sys.path:
                sys.path.insert(0, text)
        from app.bioinformatics.legacy.geo_tool.geo_info_fetcher import GeoInfoFetcher

        return GeoInfoFetcher
    except Exception:
        return None
