from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.services.online_retrieval_validation_service import OnlineRetrievalValidationService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskStatus, TaskType


ESEARCH_RESPONSE = b'{"esearchresult":{"idlist":["111","222"]}}'
EFETCH_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>111</PMID>
      <Article>
        <ArticleTitle>Mock PubMed Trial One</ArticleTitle>
        <Abstract><AbstractText>First read-only validation abstract.</AbstractText></Abstract>
        <Journal><Title>Mock Journal</Title><JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue></Journal>
        <AuthorList><Author><ForeName>Alice</ForeName><LastName>Adams</LastName></Author></AuthorList>
        <Language>eng</Language>
      </Article>
    </MedlineCitation>
    <PubmedData><ArticleIdList><ArticleId IdType="doi">10.1000/mock.111</ArticleId></ArticleIdList></PubmedData>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>222</PMID>
      <Article>
        <ArticleTitle>Mock PubMed Trial Two</ArticleTitle>
        <Abstract><AbstractText>Second read-only validation abstract.</AbstractText></Abstract>
        <Journal><Title>Mock Journal 2</Title><JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue></Journal>
        <AuthorList><Author><ForeName>Ben</ForeName><LastName>Baker</LastName></Author></AuthorList>
        <Language>eng</Language>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_pubmed_validation_success_writes_literature_records_history_data_and_task(tmp_path: Path) -> None:
    calls: list[str] = []

    def fetcher(url: str, timeout_seconds: float) -> bytes:
        calls.append(url)
        return ESEARCH_RESPONSE if "esearch.fcgi" in url else EFETCH_RESPONSE

    task_center = TaskCenter(tmp_path / "tasks.json")
    data_center = DataCenter(tmp_path / "data.json")
    service = OnlineRetrievalValidationService(fetcher=fetcher, task_center=task_center, data_center=data_center)

    result = service.validate_pubmed_retrieval(tmp_path / "project", query="statin mortality", retmax=2)

    assert result.success
    assert result.fetched_count == 2
    assert Path(result.output_path).exists()
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    assert payload["source_type"] == "pubmed"
    assert payload["records"][0]["pmid"] == "111"
    assert payload["records"][0]["doi"] == "10.1000/mock.111"
    assert result.details["api_key_saved"] is False
    assert result.details["private_data_uploaded"] is False
    assert Path(result.history_path).exists()
    history = json.loads(Path(result.history_path).read_text(encoding="utf-8"))["retrieval_history"]
    assert history[0]["success"] is True
    assert not any("api_key" in call.lower() for call in calls)
    assert "literature_records" in {asset.data_type for asset in data_center.list_assets("project")}
    tasks = task_center.list_tasks()
    assert tasks[0].task_type is TaskType.LITERATURE_IMPORT
    assert tasks[0].status is TaskStatus.COMPLETED


def test_pubmed_validation_failure_is_non_crashing_and_records_history(tmp_path: Path) -> None:
    def fetcher(url: str, timeout_seconds: float) -> bytes:
        raise TimeoutError("network timeout")

    task_center = TaskCenter(tmp_path / "tasks.json")
    service = OnlineRetrievalValidationService(fetcher=fetcher, task_center=task_center)

    result = service.validate_pubmed_retrieval(tmp_path / "project", query="statin mortality", retmax=2)

    assert not result.success
    assert result.output_path == ""
    assert "PubMed 联网验证失败" in result.message
    assert "pubmed_network_validation_failed" in result.warnings
    history = json.loads(Path(result.history_path).read_text(encoding="utf-8"))["retrieval_history"]
    assert history[0]["success"] is False
    assert history[0]["details"]["error"] == "network timeout"
    assert task_center.list_tasks()[0].status is TaskStatus.FAILED

