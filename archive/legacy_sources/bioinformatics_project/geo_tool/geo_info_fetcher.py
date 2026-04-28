"""Fetch GEO Series metadata from NCBI E-Utils and GEO accession pages."""

from __future__ import annotations

import html
import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

import requests
from geo_processing.module1_readers import read_search_result_item


LOGGER = logging.getLogger(__name__)

DEFAULT_ORGANISM_FILTER = (
    "(Homo sapiens[Organism] OR Mus musculus[Organism] OR Rattus norvegicus[Organism])"
)


@dataclass
class GeoSeriesInfo:
    gse_id: str
    title_en: str = ""
    title_zh: str = ""
    organism: str = ""
    experiment_type: str = ""
    summary_en: str = ""
    summary_zh: str = ""
    overall_design_en: str = ""
    overall_design_zh: str = ""
    sample_count: int = 0
    platform: str = ""
    pubmed_id: str = ""
    geo_url: str = ""
    brief_zh: str = ""

    @classmethod
    def from_search_payload(cls, payload: dict) -> "GeoSeriesInfo":
        item = read_search_result_item(payload)
        return cls(
            gse_id=str(item.get("gse_id") or item.get("dataset_id") or ""),
            title_en=str(item.get("title_en") or ""),
            title_zh=str(item.get("title_zh") or ""),
            organism=str(item.get("organism") or ""),
            experiment_type=str(item.get("experiment_type") or item.get("assay_type") or ""),
            summary_en=str(item.get("summary_en") or ""),
            summary_zh=str(item.get("summary_zh") or ""),
            overall_design_en=str(item.get("overall_design_en") or ""),
            overall_design_zh=str(item.get("overall_design_zh") or ""),
            sample_count=int(item.get("sample_count") or 0),
            platform=str(item.get("platform") or ""),
            pubmed_id=str(item.get("pubmed_id") or ""),
            geo_url=str(item.get("geo_url") or item.get("source_url") or ""),
            brief_zh=str(item.get("brief_zh") or ""),
        )

    def to_search_payload(self) -> dict:
        return read_search_result_item(
            {
                "gse_id": self.gse_id,
                "title_en": self.title_en,
                "title_zh": self.title_zh,
                "organism": self.organism,
                "experiment_type": self.experiment_type,
                "summary_en": self.summary_en,
                "summary_zh": self.summary_zh,
                "overall_design_en": self.overall_design_en,
                "overall_design_zh": self.overall_design_zh,
                "sample_count": self.sample_count,
                "platform": self.platform,
                "pubmed_id": self.pubmed_id,
                "geo_url": self.geo_url,
                "brief_zh": self.brief_zh,
            }
        )


@dataclass
class GeoSearchResult:
    query: str
    strategy_label: str
    total_count: int
    results: List[GeoSeriesInfo]
    requested_max: int | None
    start: int
    next_start: int
    fetched_all: bool


class GeoInfoFetcher:
    """Search and hydrate GEO Series metadata without downloading datasets."""

    EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    GEO_TEXT_URL = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"

    def __init__(
        self,
        timeout: int = 30,
        session: Optional[requests.Session] = None,
        debug_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.timeout = timeout
        self.session = session or requests.Session()
        self.debug_callback = debug_callback
        self.session.headers.update(
            {
                "User-Agent": "geo_tool/1.0 (local PySide6 client)",
                "Accept": "application/json,text/plain,*/*",
            }
        )

    def _debug(self, message: str) -> None:
        LOGGER.info(message)
        if self.debug_callback:
            self.debug_callback(message)

    def search_series(
        self,
        query_text: str,
        max_results: int | None = 1000,
        page_size: int = 100,
        start: int = 0,
        pause_callback: Optional[Callable[[], None]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> GeoSearchResult:
        self._wait_if_paused(pause_callback)
        final_query = self.build_series_query(query_text)
        self._debug(f"[GEO] 最终 query: {final_query}")
        total_count, _ = self._esearch_page(final_query, retstart=start, retmax=0)
        self._debug(f"[GEO] 首次 esearch 总命中: {total_count}")

        if total_count == 0:
            relaxed_query = self._build_relaxed_query(query_text)
            if relaxed_query and relaxed_query != final_query:
                self._wait_if_paused(pause_callback)
                self._debug(f"[GEO] 0 结果，尝试宽松 query: {relaxed_query}")
                relaxed_total, _ = self._esearch_page(relaxed_query, retstart=start, retmax=0)
                self._debug(f"[GEO] 宽松 query 总命中: {relaxed_total}")
                if relaxed_total > 0:
                    final_query = relaxed_query
                    total_count = relaxed_total

        available = max(total_count - start, 0)

        if max_results is None:
            target = available
        else:
            target = max(min(max_results, available), 0)

        if target == 0:
            return GeoSearchResult(
                query=final_query,
                strategy_label="完整检索",
                total_count=total_count,
                results=[],
                requested_max=max_results,
                start=start,
                next_start=start,
                fetched_all=available == 0,
            )

        collected: List[GeoSeriesInfo] = []
        seen_accessions: set[str] = set()
        current_start = start
        batch_size_limit = max(page_size, 1)

        while len(collected) < target:
            self._wait_if_paused(pause_callback)
            current_batch_size = min(batch_size_limit, target - len(collected))
            _, uid_batch = self._esearch_page(final_query, retstart=current_start, retmax=current_batch_size)
            if not uid_batch:
                self._debug("[GEO] esearch idlist 为空，结束抓取")
                break

            self._wait_if_paused(pause_callback)
            summary_records = self._esummary(uid_batch)
            self._debug(f"[GEO] esummary 返回记录数: {len(summary_records)}")
            self._wait_if_paused(pause_callback)
            hydrated_batch = self._hydrate_summary_records(summary_records)
            self._debug(f"[GEO] 解析出的 GSE 数量: {len(hydrated_batch)}")
            for info in hydrated_batch:
                if info.gse_id in seen_accessions:
                    continue
                seen_accessions.add(info.gse_id)
                collected.append(info)
                if progress_callback:
                    progress_callback(len(collected), target)
                if len(collected) >= target:
                    break

            current_start += len(uid_batch)
            if len(uid_batch) < current_batch_size:
                break

        fetched_all = current_start >= total_count or len(collected) >= available
        return GeoSearchResult(
            query=final_query,
            strategy_label="完整检索",
            total_count=total_count,
            results=collected,
            requested_max=max_results,
            start=start,
            next_start=current_start,
            fetched_all=fetched_all,
        )

    @staticmethod
    def _wait_if_paused(pause_callback: Optional[Callable[[], None]]) -> None:
        if pause_callback is not None:
            pause_callback()

    @staticmethod
    def build_series_query(query_text: str) -> str:
        core = query_text.strip() if query_text else ""
        if any(token in core for token in ("GSE[ETYP]", "[Organism]")):
            return core
        if core:
            return f"({core}) AND GSE[ETYP] AND {DEFAULT_ORGANISM_FILTER}"
        return f"GSE[ETYP] AND {DEFAULT_ORGANISM_FILTER}"

    @staticmethod
    def _build_relaxed_query(query_text: str) -> str:
        core = (query_text or "").strip()
        if not core:
            return ""
        normalized = unicodedata.normalize("NFKD", core).encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r'"', "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if not normalized:
            return ""
        if any(token in normalized for token in ("GSE[ETYP]", "[Organism]")):
            return normalized
        return f"({normalized}) AND GSE[ETYP] AND {DEFAULT_ORGANISM_FILTER}"

    def _esearch_page(self, query: str, retstart: int = 0, retmax: int = 20) -> tuple[int, List[str]]:
        params = {
            "db": "gds",
            "term": query,
            "retstart": retstart,
            "retmax": retmax,
            "retmode": "json",
        }
        self._debug(f"[GEO] esearch 参数: {params}")
        response = self.session.get(
            f"{self.EUTILS_BASE}/esearch.fcgi",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json().get("esearchresult", {})
        count = self._safe_int(payload.get("count"))
        idlist = payload.get("idlist", [])
        self._debug(f"[GEO] esearch 返回 count={count}, idlist={len(idlist)}")
        return count, idlist

    def _esummary(self, ids: Iterable[str]) -> List[dict]:
        params = {
            "db": "gds",
            "id": ",".join(ids),
            "retmode": "json",
            "version": "2.0",
        }
        self._debug(f"[GEO] esummary 参数: {params}")
        response = self.session.get(
            f"{self.EUTILS_BASE}/esummary.fcgi",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("result", {})
        summaries = []
        for uid in result.get("uids", []):
            record = result.get(uid)
            if isinstance(record, dict):
                summaries.append(record)
        return summaries

    def _hydrate_summary_records(self, summary_records: Iterable[dict]) -> List[GeoSeriesInfo]:
        series_list: List[GeoSeriesInfo] = []
        for item in summary_records:
            try:
                accession = self._safe_text(item.get("accession") or item.get("uid"))
                if not accession.startswith("GSE"):
                    continue

                info = GeoSeriesInfo(
                    gse_id=accession,
                    title_en=self._safe_text(item.get("title")),
                    organism=self._safe_text(item.get("taxon")),
                    experiment_type=self._safe_text(item.get("gdstype") or item.get("entrytype")),
                    summary_en=self._safe_text(item.get("summary")),
                    sample_count=self._safe_int(item.get("n_samples")),
                    platform=self._extract_platform(item),
                    pubmed_id=self._extract_pubmed_id(item),
                    geo_url=f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}",
                )

                supplement = self._fetch_series_text_fields(accession)
                if supplement:
                    info.overall_design_en = supplement.get("overall_design", info.overall_design_en)
                    if not info.experiment_type:
                        info.experiment_type = supplement.get("series_type", "")
                    if not info.platform:
                        info.platform = supplement.get("platform", "")
                    if not info.summary_en:
                        info.summary_en = supplement.get("summary", "")
                    if not info.pubmed_id:
                        info.pubmed_id = supplement.get("pubmed_id", "")
                    if not info.organism:
                        info.organism = supplement.get("organism", "")

                series_list.append(info)
            except Exception as exc:
                LOGGER.warning("Skipping one GEO record due to parse failure: %s", exc)
        return series_list

    def _fetch_series_text_fields(self, accession: str) -> dict[str, str]:
        try:
            response = self.session.get(
                self.GEO_TEXT_URL,
                params={
                    "acc": accession,
                    "targ": "self",
                    "form": "text",
                    "view": "quick",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            text = response.text
        except Exception as exc:
            LOGGER.warning("Failed to fetch GEO accession page for %s: %s", accession, exc)
            return {}

        summaries = self._extract_repeated_values(text, "!Series_summary")
        overall_design = self._extract_repeated_values(text, "!Series_overall_design")
        platforms = self._extract_repeated_values(text, "!Series_platform_id")
        pubmed_ids = self._extract_repeated_values(text, "!Series_pubmed_id")
        organisms = self._extract_repeated_values(text, "!Series_sample_organism")
        series_types = self._extract_repeated_values(text, "!Series_type")

        return {
            "summary": " ".join(summaries).strip(),
            "overall_design": " ".join(overall_design).strip(),
            "platform": "; ".join(platforms).strip(),
            "pubmed_id": "; ".join(pubmed_ids).strip(),
            "organism": "; ".join(dict.fromkeys(organisms)).strip(),
            "series_type": "; ".join(dict.fromkeys(series_types)).strip(),
        }

    @staticmethod
    def _extract_repeated_values(text: str, key: str) -> List[str]:
        pattern = re.compile(rf"^{re.escape(key)}\s*=\s*(.+)$", re.MULTILINE)
        return [html.unescape(match.strip()) for match in pattern.findall(text) if match.strip()]

    @staticmethod
    def _extract_platform(item: dict) -> str:
        platform_text = item.get("platformtitle") or item.get("gpl") or ""
        if isinstance(platform_text, list):
            return "; ".join(str(x) for x in platform_text if x)
        if isinstance(platform_text, str) and platform_text.strip():
            return platform_text.strip()
        gpl_value = item.get("gpl")
        if isinstance(gpl_value, str) and gpl_value.strip():
            return f"GPL{gpl_value.strip()}" if not gpl_value.startswith("GPL") else gpl_value
        return ""

    @staticmethod
    def _extract_pubmed_id(item: dict) -> str:
        pubmed_ids = item.get("pubmedids") or []
        if isinstance(pubmed_ids, list):
            return "; ".join(str(value) for value in pubmed_ids if value)
        if isinstance(pubmed_ids, str):
            return pubmed_ids.strip()
        return ""

    @staticmethod
    def _safe_text(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return "; ".join(str(item).strip() for item in value if str(item).strip())
        return str(value).strip()

    @staticmethod
    def _safe_int(value: object) -> int:
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0
