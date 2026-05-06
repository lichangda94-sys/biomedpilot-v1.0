from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.meta_analysis.search.search_strategy_builder_service import (
    CONFIRMED_SEARCH_STRATEGY_SCHEMA_VERSION,
    DATABASE_CNKI,
    DATABASE_COCHRANE,
    DATABASE_EMBASE,
    DATABASE_PUBMED,
    DATABASE_VIP,
    DATABASE_WANFANG,
    DATABASE_WOS,
    SEARCH_STRATEGY_DATABASES,
    SEARCH_STRATEGY_DRAFT_SCHEMA_VERSION,
    SEARCH_STRATEGY_DRAFT_SET_SCHEMA_VERSION,
    SearchStrategyBuilderService,
)
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def test_search_strategy_v2_requires_confirmed_protocol(tmp_path: Path) -> None:
    PICOWorkspaceService().generate_draft(tmp_path, "肥胖暴露与甲状腺癌风险", pico_mode="peco")

    with pytest.raises(ValueError, match="confirmed_pico_protocol_v2_required"):
        SearchStrategyBuilderService().generate_from_confirmed_protocol(tmp_path)

    assert not (tmp_path / "protocol" / "search_strategy_v2" / "search_strategy_drafts.json").exists()


def test_search_strategy_v2_generates_all_database_drafts_from_confirmed_protocol(tmp_path: Path) -> None:
    _confirmed_protocol(tmp_path)

    result = SearchStrategyBuilderService().generate_from_confirmed_protocol(tmp_path)
    payload = json.loads(Path(result.draft_path).read_text(encoding="utf-8"))
    drafts = {draft.database: draft for draft in result.drafts}
    rendered = json.dumps(payload, ensure_ascii=False).lower()

    assert payload["schema_version"] == SEARCH_STRATEGY_DRAFT_SET_SCHEMA_VERSION
    assert result.draft_count == 7
    assert set(drafts) == set(SEARCH_STRATEGY_DATABASES)
    assert all(draft.schema_version == SEARCH_STRATEGY_DRAFT_SCHEMA_VERSION for draft in drafts.values())
    assert drafts[DATABASE_PUBMED].database_family == "biomedical_bibliographic"
    assert '"Obesity"[Mesh]' in drafts[DATABASE_PUBMED].boolean_query
    assert "[tiab]" in drafts[DATABASE_PUBMED].boolean_query
    assert drafts[DATABASE_WOS].boolean_query.startswith("TS=")
    assert "'Obesity'/exp" in drafts[DATABASE_EMBASE].boolean_query
    assert ":ti,ab,kw" in drafts[DATABASE_EMBASE].boolean_query
    assert ":ti,ab,kw" in drafts[DATABASE_COCHRANE].boolean_query
    assert "主题=" in drafts[DATABASE_CNKI].boolean_query
    assert "题名或关键词=" in drafts[DATABASE_WANFANG].boolean_query
    assert "题名/关键词/摘要=" in drafts[DATABASE_VIP].boolean_query
    assert all(token not in rendered for token in ("geo", "gse", "tcga", "gtex"))
    assert payload["auto_executed"] is False
    assert payload["auto_imported"] is False
    assert payload["screening_status"] == "not_started"
    assert payload["prisma_status"] == "not_updated"


def test_search_strategy_v2_edit_and_confirm_write_governance_versions(tmp_path: Path) -> None:
    _confirmed_protocol(tmp_path)
    service = SearchStrategyBuilderService()
    result = service.generate_from_confirmed_protocol(tmp_path)
    pubmed = next(draft for draft in result.drafts if draft.database == DATABASE_PUBMED)

    edited = service.edit_draft(
        tmp_path,
        search_strategy_id=pubmed.search_strategy_id,
        updates={"boolean_query": '("Obesity"[Mesh] OR "obesity"[tiab]) AND ("Thyroid Neoplasms"[Mesh])'},
        actor="reviewer",
    )
    confirmed = service.confirm_strategies(tmp_path, actor="reviewer")
    draft_versions = json.loads(service.draft_versions_path(tmp_path).read_text(encoding="utf-8"))
    confirmed_payload = json.loads(service.confirmed_set_path(tmp_path).read_text(encoding="utf-8"))
    governance_events = MetaResearchGovernanceService().list_events(tmp_path)

    assert edited.version == pubmed.version + 1
    assert edited.boolean_query.startswith('("Obesity"[Mesh]')
    assert draft_versions["schema_version"] == "meta_search_strategy_draft_versions.v2"
    assert confirmed_payload["schema_version"] == "meta_confirmed_search_strategy_set.v2"
    assert len(confirmed) == 7
    assert all(item.schema_version == CONFIRMED_SEARCH_STRATEGY_SCHEMA_VERSION for item in confirmed)
    assert next(item for item in confirmed if item.database == DATABASE_PUBMED).execution_allowed is True
    assert all(item.execution_allowed is False for item in confirmed if item.database != DATABASE_PUBMED)
    assert any(event.action == "edit" and event.target_type == "database_query" for event in governance_events)
    assert any(event.action == "confirm" and event.target_type == "final_search_strategy" for event in governance_events)


def test_search_strategy_v2_exports_markdown_and_text_without_execution(tmp_path: Path) -> None:
    _confirmed_protocol(tmp_path)
    result = SearchStrategyBuilderService().generate_from_confirmed_protocol(tmp_path)

    markdown = Path(result.export_markdown_path).read_text(encoding="utf-8")
    text = Path(result.export_text_path).read_text(encoding="utf-8")

    assert "# Search Strategy Draft v2" in markdown
    assert "## pubmed" in markdown
    assert "## cnki" in markdown
    assert "[pubmed]" in text
    assert "[vip]" in text
    assert "No search is executed" in text


def test_search_strategy_v2_does_not_import_screen_or_advance_prisma(tmp_path: Path) -> None:
    _confirmed_protocol(tmp_path)

    SearchStrategyBuilderService().generate_from_confirmed_protocol(tmp_path)
    SearchStrategyBuilderService().confirm_strategies(tmp_path, actor="reviewer")
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()
    assert not (tmp_path / "literature").exists()
    assert not (tmp_path / "screening").exists()
    assert prisma.records_screened == 0
    assert prisma.records_excluded_title_abstract == 0
    assert prisma.full_text_reports_assessed == 0
    assert prisma.studies_included == 0


def _confirmed_protocol(project_dir: Path) -> None:
    service = PICOWorkspaceService()
    service.generate_draft(project_dir, "肥胖暴露与甲状腺癌风险是否相关？", pico_mode="peco")
    service.edit_draft(
        project_dir,
        actor="reviewer",
        updates={
            "population": "甲状腺癌人群",
            "exposure": "肥胖",
            "comparator": "非肥胖",
            "outcome": "发病风险",
            "study_design": "observational study",
        },
    )
    service.confirm_protocol(
        project_dir,
        actor="reviewer",
        confirmed_meta_type="exposure_disease_risk_meta",
        overrides={
            "confirmed_population": "甲状腺癌人群",
            "confirmed_intervention_or_exposure": "肥胖",
            "confirmed_comparator": "非肥胖",
            "confirmed_outcomes": ("发病风险",),
            "confirmed_study_design": "observational study",
        },
    )
