#!/usr/bin/env python3
"""Interactive PubMed search, selection, download, and translation CLI."""

from __future__ import annotations

import argparse
import csv
from http.client import IncompleteRead
import json
import re
import ssl
import sys
import textwrap
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
GOOGLE_TRANSLATE = "https://translate.googleapis.com/translate_a/single"
USER_AGENT = "literature-cli/1.0"


class LiteratureError(Exception):
    """Base exception for the literature workflow."""


class SearchError(LiteratureError):
    """Raised when search fails."""


class DownloadError(LiteratureError):
    """Raised when download fails."""


class TranslationError(LiteratureError):
    """Raised when translation fails."""


@dataclass
class SearchConfig:
    max_results: int | None = 1000
    page_size: int = 20
    timeout: int = 30
    start: int = 0
    db: str = "pubmed"
    save_format: str = "both"
    allow_insecure_ssl: bool = True
    email: str | None = None
    tool: str = "literature_cli"
    language_target: str = "zh-CN"
    translation_chunk_size: int = 1
    output_root: str = "literature_output"
    cache_dirname: str = "_cache"
    request_pause_seconds: float = 0.4
    max_retries: int = 3


@dataclass
class SearchRecord:
    index: int
    pmid: str
    title: str
    year: str
    source: str
    abstract: str
    doi: str | None = None
    article_url: str | None = None
    full_text_url: str | None = None
    authors: list[str] = field(default_factory=list)

    def brief_abstract(self, width: int = 180) -> str:
        clean = re.sub(r"\s+", " ", self.abstract).strip()
        if not clean:
            return "No abstract available."
        return textwrap.shorten(clean, width=width, placeholder="...")

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "pmid": self.pmid,
            "title": self.title,
            "year": self.year,
            "source": self.source,
            "abstract": self.abstract,
            "doi": self.doi,
            "article_url": self.article_url,
            "full_text_url": self.full_text_url,
            "authors": self.authors,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SearchRecord":
        return cls(
            index=int(payload.get("index", 0)),
            pmid=str(payload.get("pmid", "")),
            title=str(payload.get("title", "")),
            year=str(payload.get("year", "")),
            source=str(payload.get("source", "")),
            abstract=str(payload.get("abstract", "")),
            doi=payload.get("doi"),
            article_url=payload.get("article_url"),
            full_text_url=payload.get("full_text_url"),
            authors=list(payload.get("authors", [])),
        )


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


class HttpClient:
    def __init__(
        self,
        timeout: int,
        allow_insecure_ssl: bool,
        request_pause_seconds: float = 0.0,
        max_retries: int = 3,
    ) -> None:
        self.timeout = timeout
        self.allow_insecure_ssl = allow_insecure_ssl
        self.request_pause_seconds = request_pause_seconds
        self.max_retries = max(max_retries, 1)
        self._ssl_context = ssl._create_unverified_context() if allow_insecure_ssl else ssl.create_default_context()

    def get_json(self, url: str, params: dict[str, Any]) -> Any:
        return json.loads(self.get_text(url, params))

    def get_text(self, url: str, params: dict[str, Any] | None = None) -> str:
        full_url = url
        if params:
            full_url = f"{url}?{urlencode(params, doseq=True)}"
        return self._request_text(full_url)

    def download_bytes(self, url: str) -> bytes:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=self.timeout, context=self._ssl_context) as response:
                return response.read()
        except HTTPError as exc:
            raise DownloadError(f"HTTP error {exc.code} while downloading {url}") from exc
        except URLError as exc:
            raise DownloadError(f"Network error while downloading {url}: {exc.reason}") from exc
        except TimeoutError as exc:
            raise DownloadError(f"Timed out while downloading {url}") from exc

    def _request_text(self, full_url: str) -> str:
        request = Request(full_url, headers={"User-Agent": USER_AGENT})
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                if self.request_pause_seconds > 0:
                    time.sleep(self.request_pause_seconds)
                with urlopen(request, timeout=self.timeout, context=self._ssl_context) as response:
                    return response.read().decode("utf-8", errors="ignore")
            except HTTPError as exc:
                last_error = exc
                if exc.code != 429 or attempt == self.max_retries:
                    raise LiteratureError(f"HTTP error {exc.code} for {full_url}") from exc
            except URLError as exc:
                last_error = exc
                if attempt == self.max_retries:
                    raise LiteratureError(f"Network error for {full_url}: {exc.reason}") from exc
            except TimeoutError as exc:
                last_error = exc
                if attempt == self.max_retries:
                    raise LiteratureError(f"Timed out while requesting {full_url}") from exc
            except IncompleteRead as exc:
                last_error = exc
                if attempt == self.max_retries:
                    raise LiteratureError(f"Incomplete response while requesting {full_url}") from exc
            time.sleep(0.8 * attempt)
        raise LiteratureError(f"Request failed for {full_url}: {last_error}")


class PubMedClient:
    def __init__(self, config: SearchConfig) -> None:
        self.config = config
        self.http = HttpClient(
            timeout=config.timeout,
            allow_insecure_ssl=config.allow_insecure_ssl,
            request_pause_seconds=config.request_pause_seconds,
            max_retries=config.max_retries,
        )

    def search(self, query: str) -> tuple[int, list[SearchRecord]]:
        return self.fetch_more(query, offset=self.config.start, limit=self.config.max_results)

    def fetch_more(
        self,
        query: str,
        offset: int,
        limit: int | None,
        existing_records: list[SearchRecord] | None = None,
    ) -> tuple[int, list[SearchRecord]]:
        total_count = self._fetch_total_count(query)
        if total_count == 0:
            return 0, []

        target = min(total_count - offset, limit) if limit is not None else total_count - offset
        target = max(target, 0)
        collected: list[SearchRecord] = list(existing_records or [])
        seen_pmids: set[str] = {record.pmid for record in collected}
        current_offset = offset

        while len(collected) < target:
            batch_size = min(self.config.page_size, target - len(collected))
            id_batch = self._search_ids(query, offset=current_offset, retmax=batch_size)
            if not id_batch:
                break
            unique_ids = [pmid for pmid in id_batch if pmid not in seen_pmids]
            if unique_ids:
                for pmid in unique_ids:
                    seen_pmids.add(pmid)
                records = self._fetch_details(unique_ids)
                collected.extend(records)
            current_offset += len(id_batch)
            if len(id_batch) < batch_size:
                break

        for idx, record in enumerate(collected, start=1):
            record.index = idx
        return total_count, collected

    def _base_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {"db": self.config.db, "retmode": "json", "tool": self.config.tool}
        if self.config.email:
            params["email"] = self.config.email
        return params

    def _fetch_total_count(self, query: str) -> int:
        params = self._base_params() | {"term": query, "retmax": 0}
        payload = self.http.get_json(PUBMED_ESEARCH, params)
        count = payload.get("esearchresult", {}).get("count", "0")
        return int(count)

    def _search_ids(self, query: str, offset: int, retmax: int) -> list[str]:
        params = self._base_params() | {
            "term": query,
            "retstart": offset,
            "retmax": retmax,
            "sort": "relevance",
        }
        payload = self.http.get_json(PUBMED_ESEARCH, params)
        return payload.get("esearchresult", {}).get("idlist", [])

    def _fetch_details(self, pmids: list[str]) -> list[SearchRecord]:
        params = {
            "db": self.config.db,
            "id": ",".join(pmids),
            "retmode": "xml",
            "tool": self.config.tool,
        }
        if self.config.email:
            params["email"] = self.config.email
        raw_xml = self.http.get_text(PUBMED_EFETCH, params)
        return self._parse_pubmed_xml(raw_xml)

    def _parse_pubmed_xml(self, raw_xml: str) -> list[SearchRecord]:
        try:
            root = ET.fromstring(raw_xml)
        except ET.ParseError as exc:
            raise SearchError("Failed to parse PubMed XML response") from exc

        records: list[SearchRecord] = []
        for article in root.findall(".//PubmedArticle"):
            pmid = _find_text(article, ".//PMID")
            title = _join_itertext(article.find(".//ArticleTitle")) or "Untitled"
            year = (
                _find_text(article, ".//PubDate/Year")
                or _find_text(article, ".//ArticleDate/Year")
                or _find_text(article, ".//PubMedPubDate[@PubStatus='pubmed']/Year")
                or "Unknown"
            )
            source = _find_text(article, ".//Journal/Title") or _find_text(article, ".//MedlineJournalInfo/MedlineTA") or "Unknown source"
            abstract_parts = [
                _join_itertext(node)
                for node in article.findall(".//Abstract/AbstractText")
                if _join_itertext(node)
            ]
            abstract = "\n".join(abstract_parts).strip()
            authors = []
            for author in article.findall(".//Author"):
                last = _find_text(author, "LastName")
                fore = _find_text(author, "ForeName")
                collective = _find_text(author, "CollectiveName")
                if collective:
                    authors.append(collective)
                elif last or fore:
                    authors.append(" ".join(part for part in [fore, last] if part))
            doi = None
            article_url = None
            full_text_url = None
            for eloc in article.findall(".//ELocationID"):
                if eloc.attrib.get("EIdType") == "doi" and (eloc.text or "").strip():
                    doi = (eloc.text or "").strip()
                    article_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                    break
            for article_id in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                id_type = article_id.attrib.get("IdType")
                value = (article_id.text or "").strip()
                if id_type == "doi" and value and not doi:
                    doi = value
                elif id_type == "pmc" and value:
                    full_text_url = f"https://pmc.ncbi.nlm.nih.gov/articles/{value}/pdf/"
            article_url = article_url or (f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None)
            records.append(
                SearchRecord(
                    index=0,
                    pmid=pmid,
                    title=unescape(title),
                    year=year,
                    source=unescape(source),
                    abstract=unescape(abstract),
                    doi=doi,
                    article_url=article_url,
                    full_text_url=full_text_url,
                    authors=authors,
                )
            )
        return records


class Translator:
    def __init__(self, config: SearchConfig) -> None:
        self.config = config
        self.http = HttpClient(
            timeout=config.timeout,
            allow_insecure_ssl=config.allow_insecure_ssl,
            request_pause_seconds=config.request_pause_seconds,
            max_retries=config.max_retries,
        )

    def translate_records(self, records: list[SearchRecord]) -> list[dict[str, Any]]:
        translations: list[dict[str, Any]] = []
        for record in records:
            combined = f"Title: {record.title}\n\nAbstract: {record.abstract or 'No abstract available.'}"
            translated = self.translate_text(combined)
            translations.append(
                {
                    "index": record.index,
                    "pmid": record.pmid,
                    "title": record.title,
                    "translated_text": translated,
                }
            )
        return translations

    def translate_text(self, text: str, target_lang: str | None = None) -> str:
        params = {
            "client": "gtx",
            "sl": "auto",
            "tl": target_lang or self.config.language_target,
            "dt": "t",
            "q": text,
        }
        raw = self.http.get_text(GOOGLE_TRANSLATE, params)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TranslationError("Failed to parse translation response") from exc

        if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
            raise TranslationError("Unexpected translation response shape")

        parts = []
        for item in payload[0]:
            if isinstance(item, list) and item and isinstance(item[0], str):
                parts.append(item[0])
        translated = "".join(parts).strip()
        if not translated:
            raise TranslationError("Translation response was empty")
        return translated


class WorkflowSession:
    def __init__(self, config: SearchConfig) -> None:
        self.config = config
        self.client = PubMedClient(config)
        self.translator = Translator(config)
        self.query: str | None = None
        self.total_count: int = 0
        self.results: list[SearchRecord] = []
        self.selected_indexes: list[int] = []
        self.last_output_dir: Path | None = None
        self.fetch_limit: int | None = config.max_results
        self.cache_path: Path | None = None
        self.search_query: str | None = None

    def run_search(self, query: str) -> list[SearchRecord]:
        query = query.strip()
        if not query:
            raise SearchError("Keyword cannot be empty")
        self.query = query
        self.search_query = self.resolve_search_query(query)
        self.fetch_limit = self.config.max_results
        self.total_count, self.results = self.client.search(self.search_query)
        self.selected_indexes = []
        self.last_output_dir = None
        self.cache_path = build_cache_path(self.config.output_root, query)
        self.save_cache()
        return self.results

    def fetch_more_results(self, additional_count: int | None = None, fetch_all: bool = False) -> list[SearchRecord]:
        if not self.query:
            raise SearchError("请先执行检索")
        if self.is_fully_fetched():
            return self.results

        if fetch_all:
            target_limit = None
        else:
            if additional_count is None or additional_count <= 0:
                additional_count = self.config.page_size
            current_target = len(self.results)
            target_limit = current_target + additional_count
            if self.total_count:
                target_limit = min(target_limit, self.total_count)

        offset = self.config.start
        self.fetch_limit = target_limit
        self.total_count, self.results = self.client.fetch_more(
            self.search_query or self.query or "",
            offset=offset,
            limit=target_limit,
            existing_records=[],
        )
        self.save_cache()
        return self.results

    def is_fully_fetched(self) -> bool:
        return self.total_count > 0 and len(self.results) >= self.total_count

    def status_line(self) -> str:
        fetched_all = "是" if self.is_fully_fetched() else "否"
        limit_label = "all" if self.fetch_limit is None else str(self.fetch_limit)
        query_info = ""
        if self.query and self.search_query and self.query != self.search_query:
            query_info = f" | 实际检索词: {self.search_query}"
        return f"总命中: {self.total_count} | 已抓取: {len(self.results)} | 抓取上限: {limit_label} | 是否抓完整: {fetched_all}{query_info}"

    def list_page(self, page: int) -> str:
        if not self.results:
            return "当前没有检索结果。请先执行检索。"
        if page < 1:
            page = 1
        start = (page - 1) * self.config.page_size
        end = min(start + self.config.page_size, len(self.results))
        if start >= len(self.results):
            return f"页码超出范围。当前共有 {self.total_pages()} 页。"
        lines = [
            f"查询词: {self.query}",
            f"{self.status_line()} | 当前页: {page}/{self.total_pages()}",
            "-" * 80,
        ]
        for record in self.results[start:end]:
            lines.extend(
                [
                    f"[{record.index}] {record.title}",
                    f"  年份: {record.year} | 来源: {record.source}",
                    f"  PMID: {record.pmid} | DOI: {record.doi or 'N/A'}",
                    f"  摘要: {record.brief_abstract()}",
                ]
            )
        return "\n".join(lines)

    def total_pages(self) -> int:
        if not self.results:
            return 0
        return (len(self.results) + self.config.page_size - 1) // self.config.page_size

    def select(self, raw: str) -> list[SearchRecord]:
        if not self.results:
            raise LiteratureError("No results available to select")
        indexes = parse_selection(raw, len(self.results))
        self.selected_indexes = indexes
        self.save_cache()
        return self.get_selected_records()

    def get_selected_records(self) -> list[SearchRecord]:
        index_map = {record.index: record for record in self.results}
        return [index_map[idx] for idx in self.selected_indexes if idx in index_map]

    def download_selected(self) -> Path:
        records = self.get_selected_records()
        if not records:
            raise DownloadError("No selected results to download")
        output_dir = build_output_dir(self.config.output_root, self.query or "query")
        save_search_results(records, output_dir, self.config.save_format)
        for record in records:
            if record.full_text_url:
                try:
                    data = self.client.http.download_bytes(record.full_text_url)
                    (output_dir / f"{record.index:03d}_{sanitize_filename(record.pmid)}.pdf").write_bytes(data)
                except DownloadError:
                    # Metadata is already saved. Keep the workflow moving even if PDF is unavailable.
                    pass
        self.last_output_dir = output_dir
        return output_dir

    def translate_selected(self) -> Path:
        records = self.get_selected_records()
        if not records:
            raise TranslationError("No selected results to translate")
        output_dir = self.last_output_dir or build_output_dir(self.config.output_root, self.query or "query")
        output_dir.mkdir(parents=True, exist_ok=True)
        translations = self.translator.translate_records(records)
        output_path = output_dir / "translations.json"
        output_path.write_text(json.dumps(translations, indent=2, ensure_ascii=False), encoding="utf-8")
        self.last_output_dir = output_dir
        return output_path

    def load_cache(self, query: str) -> list[SearchRecord]:
        cache_path = build_cache_path(self.config.output_root, query)
        if not cache_path.exists():
            raise SearchError(f"未找到关键词缓存: {cache_path}")
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        self.query = payload.get("query")
        self.search_query = payload.get("search_query") or self.query
        self.total_count = int(payload.get("total_count", 0))
        self.fetch_limit = payload.get("fetch_limit")
        self.selected_indexes = [int(item) for item in payload.get("selected_indexes", [])]
        last_output_dir = payload.get("last_output_dir")
        self.last_output_dir = Path(last_output_dir) if last_output_dir else None
        self.results = [SearchRecord.from_dict(item) for item in payload.get("results", [])]
        self.cache_path = cache_path
        return self.results

    def save_cache(self) -> None:
        if not self.query:
            return
        cache_path = self.cache_path or build_cache_path(self.config.output_root, self.query)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "query": self.query,
            "search_query": self.search_query,
            "total_count": self.total_count,
            "fetch_limit": self.fetch_limit,
            "selected_indexes": self.selected_indexes,
            "last_output_dir": str(self.last_output_dir) if self.last_output_dir else None,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "results": [record.to_dict() for record in self.results],
        }
        cache_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.cache_path = cache_path

    def resolve_search_query(self, query: str) -> str:
        if not contains_cjk(query):
            return query
        translated = self.translator.translate_text(query, target_lang="en").strip()
        if not translated:
            raise SearchError("中文关键词自动转换英文失败")
        return translated


def _find_text(node: ET.Element | None, path: str) -> str:
    if node is None:
        return ""
    target = node.find(path)
    if target is None or target.text is None:
        return ""
    return target.text.strip()


def _join_itertext(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return " ".join(text.strip() for text in node.itertext() if text and text.strip())


def sanitize_filename(value: str) -> str:
    clean = re.sub(r"[^0-9A-Za-z._-]+", "_", value.strip())
    return clean.strip("_") or "item"


def build_output_dir(root: str, query: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_part = sanitize_filename(query)[:60]
    output_dir = Path(root).expanduser().resolve() / f"{query_part}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def build_cache_path(root: str, query: str) -> Path:
    cache_dir = Path(root).expanduser().resolve() / "_cache"
    return cache_dir / f"{sanitize_filename(query)[:80]}.json"


def save_search_results(records: list[SearchRecord], output_dir: Path, save_format: str) -> None:
    payload = [record.to_dict() for record in records]
    if save_format in {"json", "both"}:
        (output_dir / "search_results.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    if save_format in {"csv", "both"}:
        with (output_dir / "search_results.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["index", "pmid", "title", "year", "source", "abstract", "doi", "article_url", "full_text_url", "authors"],
            )
            writer.writeheader()
            for row in payload:
                row = row.copy()
                row["authors"] = "; ".join(row["authors"])
                writer.writerow(row)


def parse_selection(raw: str, max_index: int) -> list[int]:
    cleaned = raw.strip().lower()
    if cleaned in {"all", "a", "全部", "全选"}:
        return list(range(1, max_index + 1))
    indexes: set[int] = set()
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start > end:
                start, end = end, start
            for idx in range(start, end + 1):
                if 1 <= idx <= max_index:
                    indexes.add(idx)
        else:
            idx = int(token)
            if 1 <= idx <= max_index:
                indexes.add(idx)
    if not indexes:
        raise LiteratureError("Selection did not match any result index")
    return sorted(indexes)


def interactive_menu(session: WorkflowSession) -> int:
    while True:
        print(
            "\n文献检索菜单\n"
            "a. 输入关键词并检索\n"
            "l. 从缓存加载结果\n"
            "b. 查看结果\n"
            "c. 选择结果\n"
            "d. 下载选中项\n"
            "e. 翻译选中项\n"
            "f. 继续抓取更多结果\n"
            "g. 抓取全部结果\n"
            "q. 退出\n"
        )
        choice = input("请选择操作: ").strip().lower()
        try:
            if choice == "a":
                query = input("输入关键词: ").strip()
                results = session.run_search(query)
                if not results:
                    print("没有检索到结果。")
                else:
                    print(session.list_page(1))
            elif choice == "l":
                query = input("输入要加载缓存的关键词: ").strip()
                results = session.load_cache(query)
                if not results:
                    print("缓存存在，但结果为空。")
                else:
                    print(session.list_page(1))
            elif choice == "b":
                page = int(input("输入页码: ").strip() or "1")
                print(session.list_page(page))
            elif choice == "c":
                raw = input("输入序号、范围(如 1,3-5)或 all: ").strip()
                selected = session.select(raw)
                print(f"已选择 {len(selected)} 条结果。")
            elif choice == "d":
                output_dir = session.download_selected()
                print(f"下载完成，输出目录: {output_dir}")
            elif choice == "e":
                output_path = session.translate_selected()
                print(f"翻译完成，输出文件: {output_path}")
            elif choice == "f":
                additional = int(input("继续抓取多少条（默认等于 page_size）: ").strip() or str(session.config.page_size))
                session.fetch_more_results(additional_count=additional)
                print(session.status_line())
            elif choice == "g":
                session.fetch_more_results(fetch_all=True)
                print(session.status_line())
            elif choice == "q":
                return 0
            else:
                print("无效选项，请重试。")
        except LiteratureError as exc:
            print(f"操作失败: {exc}")
        except ValueError:
            print("输入格式错误，请重试。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PubMed 文献检索、选择、下载和翻译 CLI")
    parser.add_argument("--query", help="直接执行检索的关键词")
    parser.add_argument("--max-results", default="1000", help="总共抓取多少条结果，默认 1000；传 all 表示抓取全部")
    parser.add_argument("--page-size", type=int, default=20, help="每页展示和抓取多少条")
    parser.add_argument("--start", type=int, default=0, help="分页起点")
    parser.add_argument("--timeout", type=int, default=30, help="网络超时秒数")
    parser.add_argument("--output-root", default="literature_output", help="输出根目录")
    parser.add_argument("--save-format", choices=["json", "csv", "both"], default="both", help="检索结果元数据保存格式")
    parser.add_argument("--target-lang", default="zh-CN", help="翻译目标语言")
    parser.add_argument("--email", default=None, help="传给 NCBI 的联系邮箱")
    parser.add_argument("--secure-ssl", action="store_true", help="启用严格 SSL 校验")
    parser.add_argument("--menu", action="store_true", help="启动交互式菜单")
    parser.add_argument("--show-page", type=int, default=1, help="直接打印某一页结果")
    parser.add_argument("--select", help="直接选择结果，例如 1,3-5 或 all")
    parser.add_argument("--download", action="store_true", help="对选中项执行下载")
    parser.add_argument("--translate", action="store_true", help="对选中项执行翻译")
    parser.add_argument("--fetch-more", type=int, default=0, help="在初次检索后继续多抓取多少条结果")
    parser.add_argument("--fetch-all", action="store_true", help="在初次检索后抓取全部结果")
    parser.add_argument("--load-cache", action="store_true", help="优先从本地缓存加载该关键词的检索结果")
    parser.add_argument("--print-config", action="store_true", help="打印当前配置")
    return parser


def parse_max_results(raw: str) -> int | None:
    value = raw.strip().lower()
    if value == "all":
        return None
    parsed = int(value)
    if parsed <= 0:
        raise ValueError("max_results must be a positive integer or 'all'")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        max_results = parse_max_results(str(args.max_results))
    except ValueError as exc:
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1
    config = SearchConfig(
        max_results=max_results,
        page_size=args.page_size,
        timeout=args.timeout,
        start=args.start,
        save_format=args.save_format,
        allow_insecure_ssl=not args.secure_ssl,
        email=args.email,
        language_target=args.target_lang,
        output_root=args.output_root,
    )
    if args.print_config:
        print(json.dumps(asdict(config), indent=2, ensure_ascii=False))

    session = WorkflowSession(config)
    if args.menu or not args.query:
        return interactive_menu(session)

    try:
        if args.load_cache:
            results = session.load_cache(args.query)
        else:
            results = session.run_search(args.query)
        if not results:
            print("没有检索到结果。")
            return 0
        if args.fetch_all:
            session.fetch_more_results(fetch_all=True)
        elif args.fetch_more > 0:
            session.fetch_more_results(additional_count=args.fetch_more)
        print(session.list_page(args.show_page))
        if args.select:
            selected = session.select(args.select)
            print(f"已选择 {len(selected)} 条结果。")
        if args.download:
            output_dir = session.download_selected()
            print(f"下载完成，输出目录: {output_dir}")
        if args.translate:
            output_path = session.translate_selected()
            print(f"翻译完成，输出文件: {output_path}")
    except LiteratureError as exc:
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
