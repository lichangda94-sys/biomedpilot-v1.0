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
        build_pico_workspace_draft,
        build_search_strategy_v2_from_confirmed_protocol,
        build_protocol_search_strategy_draft,
        confirm_pico_workspace_protocol,
        confirm_search_strategy_v2,
        execute_protocol_pubmed_search,
        protocol_page_state_from_project,
        render_pico_workspace_draft_summary,
        render_pubmed_search_execution_summary,
        render_search_strategy_summary,
        render_search_strategy_v2_summary,
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


def test_meta_pico_workspace_v2_summary_requires_human_confirmation(tmp_path: Path) -> None:
    draft = build_pico_workspace_draft(tmp_path, "肥胖暴露与甲状腺癌风险是否相关？", pico_mode="auto")
    summary = render_pico_workspace_draft_summary(draft)
    state = protocol_page_state_from_project(tmp_path)

    assert "PICO/PICOS/PECO draft" in summary
    assert "mode=peco" in summary
    assert "需要人工确认" in summary
    assert "不会自动执行检索、筛选或 PRISMA。" in summary
    assert state.pico_workspace_status == "draft"
    assert state.pico_mode == "peco"
    assert state.confirmed_protocol_summary == "需要人工确认"


def test_meta_pico_workspace_v2_confirmed_state_is_separate_from_draft(tmp_path: Path) -> None:
    draft = build_pico_workspace_draft(tmp_path, "成人肺炎患者使用糖皮质激素能否降低死亡率？", pico_mode="pico")
    confirmed = confirm_pico_workspace_protocol(
        tmp_path,
        actor="reviewer",
        confirmed_meta_type="treatment_comparative_meta",
    )
    state = protocol_page_state_from_project(tmp_path)

    assert confirmed.source_draft_id == draft.protocol_id
    assert state.pico_workspace_status == "confirmed"
    assert state.pico_workspace_draft is not None
    assert state.confirmed_protocol is not None
    assert state.pico_workspace_draft.protocol_id != state.confirmed_protocol.confirmed_protocol_id
    assert "已确认" in state.confirmed_protocol_summary
    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()


def test_meta_search_strategy_v2_summary_from_confirmed_protocol(tmp_path: Path) -> None:
    build_pico_workspace_draft(tmp_path, "肥胖暴露与甲状腺癌风险是否相关？", pico_mode="peco")
    confirm_pico_workspace_protocol(
        tmp_path,
        actor="reviewer",
        confirmed_meta_type="exposure_disease_risk_meta",
    )

    result = build_search_strategy_v2_from_confirmed_protocol(tmp_path)
    summary = render_search_strategy_v2_summary(result.drafts)
    confirmed = confirm_search_strategy_v2(tmp_path, actor="reviewer")
    state = protocol_page_state_from_project(tmp_path)

    assert result.draft_count == 7
    assert "Search Strategy Builder v2" in summary
    assert "仅生成草稿" in summary
    assert "PubMed 可执行" in summary
    assert "其他数据库需手动检索" in summary
    assert "pubmed" in summary
    assert "vip" in summary
    assert len(confirmed) == 7
    assert state.search_strategy_v2_status == "draft"
    assert len(state.search_strategy_v2_drafts) == 7
    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()


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


def test_meta_protocol_page_generates_and_confirms_pico_workspace_v2(qt_app, tmp_path: Path) -> None:
    widget = ProtocolPage()
    widget.set_protocol_inputs(
        project_dir=tmp_path,
        project_title="肥胖与甲状腺癌发病风险 Meta 分析",
        review_question="肥胖暴露是否增加甲状腺癌发病风险？",
        pico="甲状腺癌人群; 肥胖; 非肥胖; 发病风险; systematic review; meta-analysis",
        method_profile="TREATMENT_EFFECT_META",
        pico_mode="peco",
    )

    draft = widget.generate_pico_workspace_draft()
    draft_summary = widget.pico_workspace_summary_text()
    confirmed = widget.confirm_research_question(confirmed_meta_type="exposure_disease_risk_meta")
    confirmed_summary = widget.pico_workspace_summary_text()

    assert draft.pico_mode == "peco"
    assert "需要人工确认" in draft_summary
    assert confirmed.source_draft_id == draft.protocol_id
    assert "已确认" in confirmed_summary
    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()
    assert not (tmp_path / "screening").exists()


def test_meta_protocol_page_builds_search_strategy_v2_after_confirmed_protocol(qt_app, tmp_path: Path) -> None:
    widget = ProtocolPage()
    widget.set_protocol_inputs(
        project_dir=tmp_path,
        project_title="肥胖与甲状腺癌发病风险 Meta 分析",
        review_question="肥胖暴露是否增加甲状腺癌发病风险？",
        pico="甲状腺癌人群; 肥胖; 非肥胖; 发病风险; observational study",
        method_profile="EXPOSURE_RISK_META",
        pico_mode="peco",
    )

    widget.generate_pico_workspace_draft()
    widget.confirm_research_question(confirmed_meta_type="exposure_disease_risk_meta")
    result = widget.build_search_strategy_v2()
    summary = widget.search_strategy_v2_summary_text()
    confirmed = widget.confirm_search_strategy_v2(actor="reviewer")

    assert result.draft_count == 7
    assert "Search Strategy Builder v2" in summary
    assert "cnki" in summary
    assert "vip" in summary
    assert len(confirmed) == 7
    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()
    assert not (tmp_path / "literature").exists()
    assert not (tmp_path / "screening").exists()


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
    preview = json.loads(Path(paths["pubmed_candidates_preview"]).read_text(encoding="utf-8"))

    assert report["database"] == "PubMed"
    assert report["search_execution_id"]
    assert report["query_used"] == query
    assert report["result_count"] == 2
    assert report["returned_count"] == 2
    assert report["pmids"] == ["111", "222"]
    assert confirmed["query_used"] == query
    assert confirmed["user_action"] == "confirm_and_search_pubmed"
    assert preview["schema_version"] == "meta_pubmed_candidate_preview.v1"
    assert preview["candidate_count"] == 2
    assert preview["auto_imported"] is False


def test_meta_pubmed_execution_does_not_auto_import_or_screen(tmp_path: Path) -> None:
    query = build_protocol_search_strategy_draft(_values()).pubmed_query_draft
    paths = execute_protocol_pubmed_search(tmp_path, query, service=_pubmed_service(), max_results=2)
    report = json.loads(Path(paths["search_execution_report"]).read_text(encoding="utf-8"))

    assert report["literature_import_status"] == "not_imported"
    assert report["screening_status"] == "not_started"
    assert report["auto_imported"] is False
    assert report["auto_screened"] is False
    assert not (tmp_path / "literature").exists()
    assert not any((tmp_path / "screening").glob("*"))


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
    assert "candidate_id=pcand-111" in summary
    assert "PMID 111" in summary
    assert "Obesity and thyroid cancer risk" in summary
    assert "query_used=" in summary
    assert (tmp_path / "protocol" / "search_execution_report.json").exists()
    assert (tmp_path / "protocol" / "pubmed_candidates").exists()


def test_meta_page_imports_only_selected_pubmed_candidates_after_reviewer_selection(qt_app, tmp_path: Path) -> None:
    widget = ProtocolPage()
    widget.set_protocol_inputs(
        project_dir=tmp_path,
        project_title="肥胖与甲状腺癌发病风险 Meta 分析",
        review_question="肥胖是否增加甲状腺癌发病风险？",
        pico="甲状腺癌人群; 肥胖; 非肥胖; 发病风险; systematic review; meta-analysis",
        method_profile="TREATMENT_EFFECT_META",
    )

    widget.save_protocol_draft()
    widget.execute_confirmed_pubmed_search(service=_pubmed_service(), max_results=2)
    result = widget.import_selected_pubmed_candidates(selected_candidate_ids=("pcand-111",), rejected_candidate_ids=("pcand-222",))
    handoff_summary = widget.pubmed_handoff_summary_text()
    library = json.loads((tmp_path / "literature" / "literature_records.json").read_text(encoding="utf-8"))

    assert result.success
    assert result.imported_count == 1
    assert library["records"][0]["pmid"] == "111"
    assert library["records"][0]["screening_status"] == "not_started"
    assert "PMID 111" in handoff_summary
    assert "No title/abstract screening is created" in handoff_summary
    assert not any((tmp_path / "screening").glob("*"))


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
