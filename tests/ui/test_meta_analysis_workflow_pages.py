from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from app.meta_analysis.workflow_pages import (
        ProtocolPage,
        build_protocol_search_strategy_draft,
        execute_protocol_pubmed_search,
        protocol_page_state_from_project,
        render_pubmed_search_execution_summary,
        render_search_strategy_summary,
        write_pubmed_search_execution_artifacts,
        write_protocol_search_strategy_artifacts,
    )
    from app.meta_analysis.search.pubmed_search_service import PubMedSearchService
except Exception as exc:  # pragma: no cover - depends on optional local GUI runtime.
    QApplication = None  # type: ignore[assignment]
    ProtocolPage = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


ESEARCH_RESPONSE = b'{"esearchresult":{"count":"2","idlist":["111","222"]}}'
EFETCH_RESPONSE = b"""<?xml version="1.0" encoding="UTF-8"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>111</PMID>
      <Article>
        <ArticleTitle>Obesity and thyroid cancer risk</ArticleTitle>
        <Abstract><AbstractText>Candidate abstract for thyroid cancer risk.</AbstractText></Abstract>
        <Journal><Title>Meta Trial Journal</Title><JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue></Journal>
        <AuthorList><Author><ForeName>Alice</ForeName><LastName>Adams</LastName></Author></AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>222</PMID>
      <Article>
        <ArticleTitle>BMI and thyroid neoplasms</ArticleTitle>
        <Abstract><AbstractText>Second candidate abstract.</AbstractText></Abstract>
        <Journal><Title>Meta Review Journal</Title><JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue></Journal>
        <AuthorList><Author><ForeName>Ben</ForeName><LastName>Baker</LastName></Author></AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


@pytest.fixture
def qt_app():
    if QApplication is None:
        pytest.skip(f"PySide6 UI runtime unavailable: {IMPORT_ERROR}")
    return QApplication.instance() or QApplication([])


def _values() -> dict[str, object]:
    return {
        "project_title": "肥胖与甲状腺癌发病风险 Meta 分析",
        "review_question": "肥胖是否增加甲状腺癌发病风险？",
        "population": "甲状腺癌人群",
        "intervention_or_exposure": "肥胖",
        "comparator": "非肥胖",
        "outcomes": "发病风险",
        "primary_outcome": "发病风险",
        "study_design": "systematic review; meta-analysis",
    }


def test_meta_protocol_search_strategy_summary_displays_database_drafts() -> None:
    draft = build_protocol_search_strategy_draft(_values())
    summary = render_search_strategy_summary(draft)

    assert "PICO/PECO mode: PECO" in summary
    assert "target_context: meta_analysis" in summary
    assert "Concept blocks:" in summary
    assert "PubMed query draft (MeSH + tiab):" in summary
    assert '"Obesity"[Mesh]' in summary
    assert '"obesity"[tiab]' in summary
    assert "WOS query draft (draft-only):" in summary
    assert "TS=" in summary
    assert "Embase query draft (draft-only):" in summary
    assert ":ti,ab,kw" in summary
    assert "CNKI query draft (draft-only):" in summary
    assert "主题=" in summary
    assert "search_execution_status=draft_only" in summary
    assert "local_model_status:" in summary
    assert "当前仅生成检索式草稿，尚未执行在线检索。" in summary


def test_meta_protocol_search_strategy_artifacts_are_draft_only_without_execution_report(tmp_path: Path) -> None:
    draft = build_protocol_search_strategy_draft(_values())
    paths = write_protocol_search_strategy_artifacts(tmp_path, draft)

    payload = json.loads(Path(paths["search_strategy_draft"]).read_text(encoding="utf-8"))
    audit = json.loads(Path(paths["search_strategy_audit"]).read_text(encoding="utf-8"))

    assert payload["target_context"] == "meta_analysis"
    assert payload["search_execution_status"] == "draft_only"
    assert audit["search_execution_status"] == "draft_only"
    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()


def test_meta_protocol_search_strategy_payload_does_not_show_dataset_sources(tmp_path: Path) -> None:
    draft = build_protocol_search_strategy_draft(_values())
    paths = write_protocol_search_strategy_artifacts(tmp_path, draft)
    rendered = (
        Path(paths["search_strategy_draft"]).read_text(encoding="utf-8")
        + Path(paths["search_strategy_audit"]).read_text(encoding="utf-8")
        + render_search_strategy_summary(draft)
    ).lower()

    assert "geo" not in rendered
    assert "gse" not in rendered
    assert "tcga" not in rendered
    assert "gtex" not in rendered


def test_meta_protocol_page_saves_and_displays_search_strategy_draft(qt_app, tmp_path: Path) -> None:
    widget = ProtocolPage()
    widget.set_protocol_inputs(
        project_dir=tmp_path,
        project_title="肥胖与甲状腺癌发病风险 Meta 分析",
        review_question="肥胖是否增加甲状腺癌发病风险？",
        pico="甲状腺癌人群; 肥胖; 非肥胖; 发病风险; systematic review; meta-analysis",
        method_profile="TREATMENT_EFFECT_META",
    )

    draft = widget.save_protocol_draft()
    summary = widget.search_strategy_summary_text()
    state = protocol_page_state_from_project(tmp_path)

    assert draft.target_context == "meta_analysis"
    assert draft.search_execution_status == "draft_only"
    assert "PubMed query draft (MeSH + tiab):" in summary
    assert "WOS query draft (draft-only):" in summary
    assert "Embase query draft (draft-only):" in summary
    assert "CNKI query draft (draft-only):" in summary
    assert state.output_paths["search_strategy_draft"].endswith("protocol/search_strategy_draft.json")
    assert state.output_paths["search_strategy_audit"].endswith("protocol/search_strategy_audit.json")
    assert "PubMed query draft" in state.search_strategy_summary
    assert state.search_execution_status == "draft_only"
    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()


def test_meta_page_displays_pubmed_query_draft() -> None:
    summary = render_search_strategy_summary(build_protocol_search_strategy_draft(_values()))

    assert "PubMed query draft (MeSH + tiab):" in summary
    assert '"Obesity"[Mesh]' in summary
    assert '"obesity"[tiab]' in summary


def test_meta_page_displays_wos_embase_cnki_draft_only() -> None:
    summary = render_search_strategy_summary(build_protocol_search_strategy_draft(_values()))

    assert "WOS query draft (draft-only):" in summary
    assert "TS=" in summary
    assert "Embase query draft (draft-only):" in summary
    assert ":ti,ab,kw" in summary
    assert "CNKI query draft (draft-only):" in summary
    assert "主题=" in summary


def test_meta_page_uses_mesh_and_tiab() -> None:
    draft = build_protocol_search_strategy_draft(_values())

    assert '"Obesity"[Mesh]' in draft.pubmed_query_draft
    assert '"obesity"[tiab]' in draft.pubmed_query_draft
    assert '"Thyroid Neoplasms"[Mesh]' in draft.pubmed_query_draft
    assert '"thyroid cancer"[tiab]' in draft.pubmed_query_draft


def test_meta_page_does_not_show_geo_tcga_gtex() -> None:
    rendered = render_search_strategy_summary(build_protocol_search_strategy_draft(_values())).lower()

    assert "geo" not in rendered
    assert "gse" not in rendered
    assert "tcga" not in rendered
    assert "gtex" not in rendered


def test_meta_search_strategy_writes_draft_and_audit(tmp_path: Path) -> None:
    paths = write_protocol_search_strategy_artifacts(tmp_path, build_protocol_search_strategy_draft(_values()))

    assert Path(paths["search_strategy_draft"]).exists()
    assert Path(paths["search_strategy_audit"]).exists()
    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()


def test_meta_search_does_not_execute_network(tmp_path: Path) -> None:
    draft = build_protocol_search_strategy_draft(_values())
    write_protocol_search_strategy_artifacts(tmp_path, draft)

    assert draft.search_execution_status == "draft_only"
    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()


def _pubmed_service() -> PubMedSearchService:
    def fetcher(url: str, timeout_seconds: float) -> bytes:
        return ESEARCH_RESPONSE if "esearch.fcgi" in url else EFETCH_RESPONSE

    return PubMedSearchService(fetcher=fetcher)


def test_pubmed_search_report_written(tmp_path: Path) -> None:
    query = build_protocol_search_strategy_draft(_values()).pubmed_query_draft
    paths = execute_protocol_pubmed_search(tmp_path, query, service=_pubmed_service(), max_results=2)

    report = json.loads(Path(paths["search_execution_report"]).read_text(encoding="utf-8"))
    confirmed = json.loads(Path(paths["search_strategy_user_confirmed"]).read_text(encoding="utf-8"))

    assert report["database"] == "PubMed"
    assert report["query_used"] == query
    assert report["result_count"] == 2
    assert report["returned_count"] == 2
    assert report["pmids"] == ["111", "222"]
    assert confirmed["query_used"] == query
    assert confirmed["user_action"] == "confirm_and_search_pubmed"


def test_meta_pubmed_execution_does_not_auto_import_or_screen(tmp_path: Path) -> None:
    query = build_protocol_search_strategy_draft(_values()).pubmed_query_draft
    paths = execute_protocol_pubmed_search(tmp_path, query, service=_pubmed_service(), max_results=2)
    report = json.loads(Path(paths["search_execution_report"]).read_text(encoding="utf-8"))

    assert report["literature_import_status"] == "not_imported"
    assert report["screening_status"] == "not_started"
    assert report["auto_imported"] is False
    assert report["auto_screened"] is False
    assert not (tmp_path / "literature").exists()
    assert not (tmp_path / "screening").exists()


def test_meta_page_pubmed_results_table(qt_app, tmp_path: Path) -> None:
    widget = ProtocolPage()
    widget.set_protocol_inputs(
        project_dir=tmp_path,
        project_title="肥胖与甲状腺癌发病风险 Meta 分析",
        review_question="肥胖是否增加甲状腺癌发病风险？",
        pico="甲状腺癌人群; 肥胖; 非肥胖; 发病风险; systematic review; meta-analysis",
        method_profile="TREATMENT_EFFECT_META",
    )

    widget.save_protocol_draft()
    execution = widget.execute_confirmed_pubmed_search(service=_pubmed_service(), max_results=2)
    summary = widget.pubmed_execution_summary_text()

    assert execution.returned_count == 2
    assert "PMID 111" in summary
    assert "Obesity and thyroid cancer risk" in summary
    assert "query_used=" in summary
    assert (tmp_path / "protocol" / "search_execution_report.json").exists()


def test_wos_embase_cnki_remain_draft_only(tmp_path: Path) -> None:
    query = build_protocol_search_strategy_draft(_values()).pubmed_query_draft
    paths = execute_protocol_pubmed_search(tmp_path, query, service=_pubmed_service(), max_results=2)
    report = json.loads(Path(paths["search_execution_report"]).read_text(encoding="utf-8"))
    confirmed = json.loads(Path(paths["search_strategy_user_confirmed"]).read_text(encoding="utf-8"))

    assert report["wos_status"] == "draft_only"
    assert report["embase_status"] == "draft_only"
    assert report["cnki_status"] == "draft_only"
    assert confirmed["wos_status"] == "draft_only"
    assert confirmed["embase_status"] == "draft_only"
    assert confirmed["cnki_status"] == "draft_only"


def test_pubmed_execution_summary_lists_literature_candidates() -> None:
    execution = _pubmed_service().search_pubmed('"Obesity"[Mesh]', max_results=2)
    summary = render_pubmed_search_execution_summary(execution)

    assert "Literature candidates:" in summary
    assert "PMID 111" in summary
    assert "No literature is auto-imported or auto-screened." in summary
