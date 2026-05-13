from __future__ import annotations

import json
import re
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


Fetcher = Callable[[str, float], bytes]


@dataclass(frozen=True)
class PubMedRetrievalValidationResult:
    success: bool
    project_id: str
    query: str
    requested_count: int
    fetched_count: int
    output_path: str
    history_path: str
    message: str
    warnings: list[str] = field(default_factory=list)
    details: dict[str, object] = field(default_factory=dict)


class OnlineRetrievalValidationService:
    def __init__(
        self,
        *,
        fetcher: Fetcher | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
    ) -> None:
        self._fetcher = fetcher or _default_fetcher
        self._task_center = task_center
        self._data_center = data_center

    def validate_pubmed_retrieval(
        self,
        project_dir: Path,
        *,
        query: str,
        retmax: int = 3,
        timeout_seconds: float = 10.0,
    ) -> PubMedRetrievalValidationResult:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_dir.name
        task = self._start_task(project_id, f"Validating read-only PubMed retrieval for query: {query}")
        history_path = self._history_path(project_dir)
        warnings: list[str] = []
        normalized_query = query.strip()
        if not normalized_query:
            result = PubMedRetrievalValidationResult(
                success=False,
                project_id=project_id,
                query=query,
                requested_count=retmax,
                fetched_count=0,
                output_path="",
                history_path=str(history_path),
                message="请输入 PubMed 检索词后再运行联网验证。",
                warnings=[],
                details={},
            )
            self._append_history(project_dir, result)
            self._finish_task(task, result)
            return result
        try:
            ids = self._search_pubmed(normalized_query, retmax=retmax, timeout_seconds=timeout_seconds)
            if not ids:
                warnings.append("pubmed_search_returned_no_records")
                records: list[dict[str, object]] = []
            else:
                records = self._fetch_pubmed_records(ids, timeout_seconds=timeout_seconds)
            output_path = self._write_literature_records(project_dir, normalized_query, records)
            result = PubMedRetrievalValidationResult(
                success=True,
                project_id=project_id,
                query=normalized_query,
                requested_count=retmax,
                fetched_count=len(records),
                output_path=str(output_path),
                history_path=str(history_path),
                message=f"PubMed 只读检索验证完成：获取 {len(records)} 条记录。",
                warnings=warnings,
                details={
                    "pmids": [record.get("pmid", "") for record in records],
                    "network_mode": "read_only_pubmed_eutils",
                    "api_key_saved": False,
                    "private_data_uploaded": False,
                },
            )
            self._append_history(project_dir, result)
            self._register_asset(project_id=project_id, query=normalized_query, output_path=output_path, status="available")
            self._finish_task(task, result)
            return result
        except Exception as exc:
            result = PubMedRetrievalValidationResult(
                success=False,
                project_id=project_id,
                query=normalized_query,
                requested_count=retmax,
                fetched_count=0,
                output_path="",
                history_path=str(history_path),
                message="PubMed 联网验证失败；本地 Meta Analysis 流程未受影响，请稍后重试或检查网络。",
                warnings=["pubmed_network_validation_failed"],
                details={"error": str(exc), "network_mode": "read_only_pubmed_eutils"},
            )
            self._append_history(project_dir, result)
            self._finish_task(task, result)
            return result

    def _search_pubmed(self, query: str, *, retmax: int, timeout_seconds: float) -> list[str]:
        url = _pubmed_url(
            "esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmax": str(max(1, min(retmax, 20))),
                "retmode": "json",
                "tool": "BioMedPilot",
            },
        )
        payload = json.loads(self._fetcher(url, timeout_seconds).decode("utf-8"))
        ids = payload.get("esearchresult", {}).get("idlist", [])
        return [str(item) for item in ids]

    def _fetch_pubmed_records(self, pmids: list[str], *, timeout_seconds: float) -> list[dict[str, object]]:
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
        records: list[dict[str, object]] = []
        for article in root.findall(".//PubmedArticle"):
            records.append(_record_from_pubmed_article(article))
        return records

    def _write_literature_records(self, project_dir: Path, query: str, records: list[dict[str, object]]) -> Path:
        output_dir = project_dir / "literature"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = _safe_timestamp()
        output_path = output_dir / f"pubmed_retrieval_{timestamp}_records.json"
        payload = {
            "project_id": project_dir.name,
            "batch_id": f"pubmed-{timestamp}",
            "source_path": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
            "source_type": "pubmed",
            "query": query,
            "created_at": _now(),
            "records": records,
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def _append_history(self, project_dir: Path, result: PubMedRetrievalValidationResult) -> Path:
        path = self._history_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        history = []
        if path.exists():
            try:
                history = json.loads(path.read_text(encoding="utf-8")).get("retrieval_history", [])
            except Exception:
                history = []
        history.insert(
            0,
            {
                "created_at": _now(),
                "provider": "pubmed",
                "query": result.query,
                "requested_count": result.requested_count,
                "fetched_count": result.fetched_count,
                "success": result.success,
                "output_path": result.output_path,
                "message": result.message,
                "warnings": result.warnings,
                "details": result.details,
            },
        )
        path.write_text(
            json.dumps({"project_id": project_dir.name, "retrieval_history": history}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def _history_path(self, project_dir: Path) -> Path:
        return project_dir / "retrieval" / "pubmed_retrieval_history.json"

    def _register_asset(self, *, project_id: str, query: str, output_path: Path, status: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type="literature_records",
            source_path=f"pubmed:{query}",
            output_path=str(output_path),
            status=status,
        )

    def _start_task(self, project_id: str, summary: str) -> TaskRecord:
        now = _now()
        if self._task_center is None:
            return TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=TaskType.LITERATURE_IMPORT,
                status=TaskStatus.RUNNING,
                module="meta_analysis",
                title="PubMed Online Retrieval Validation",
                created_at=now,
                updated_at=now,
                project_id=project_id,
                started_at=now,
                summary=summary,
            )
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.LITERATURE_IMPORT,
            module="meta_analysis",
            title="PubMed Online Retrieval Validation",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=summary,
        )

    def _finish_task(self, task: TaskRecord, result: PubMedRetrievalValidationResult) -> None:
        if self._task_center is None:
            return
        now = _now()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if result.success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=result.message,
                error_message="" if result.success else result.message,
            )
        )


def _default_fetcher(url: str, timeout_seconds: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "BioMedPilot Developer Preview"})
    context = _ssl_context()
    with urllib.request.urlopen(request, timeout=timeout_seconds, context=context) as response:  # nosec B310 - explicit read-only validation URL.
        return response.read()


def _ssl_context() -> ssl.SSLContext | None:
    try:
        import certifi
    except Exception:
        return None
    return ssl.create_default_context(cafile=certifi.where())


def _pubmed_url(endpoint: str, params: dict[str, str]) -> str:
    return "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/" + endpoint + "?" + urllib.parse.urlencode(params)


def _record_from_pubmed_article(article: ET.Element) -> dict[str, object]:
    pmid = _text(article, ".//MedlineCitation/PMID")
    title = _iter_text(article.find(".//ArticleTitle"))
    abstract = " ".join(_iter_text(item) for item in article.findall(".//Abstract/AbstractText")).strip()
    journal = _text(article, ".//Journal/Title")
    year = _year_from_article(article)
    doi = ""
    for article_id in article.findall(".//ArticleIdList/ArticleId"):
        if article_id.attrib.get("IdType") == "doi":
            doi = (article_id.text or "").strip()
            break
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
    keywords = [_iter_text(item) for item in article.findall(".//KeywordList/Keyword") if _iter_text(item)]
    language = _text(article, ".//Language")
    return {
        "record_id": f"pubmed-{pmid}" if pmid else f"pubmed-{uuid4().hex[:12]}",
        "title": title,
        "source_record_id": pmid,
        "abstract": abstract,
        "authors": authors,
        "journal": journal,
        "doi": doi,
        "pmid": pmid,
        "year": year,
        "keywords": keywords,
        "language": language,
    }


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


def _safe_timestamp() -> str:
    return _now().replace(":", "").replace("+", "Z")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
