from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.protocol_page import build_pico_workspace_draft, confirm_pico_workspace_protocol
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.pico_workspace_service import (
    CONFIRMED_PROTOCOL_SCHEMA_VERSION,
    PICO_MODE_PECO,
    PICO_MODE_PICO,
    PICO_MODE_PICOS,
    PICO_PROTOCOL_DRAFT_SCHEMA_VERSION,
    PICOWorkspaceService,
)
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def test_pico_workspace_generates_chinese_peco_draft_with_shared_query_intelligence(tmp_path: Path) -> None:
    service = PICOWorkspaceService()

    draft = service.generate_draft(
        tmp_path,
        "高血压患者中高盐饮食暴露与卒中风险的关系",
        pico_mode="auto",
        project_id="pico-m5",
    )
    payload = json.loads(service.draft_path(tmp_path).read_text(encoding="utf-8"))
    rendered = json.dumps(payload, ensure_ascii=False).lower()
    governance_events = MetaResearchGovernanceService().list_events(tmp_path)

    assert draft.schema_version == PICO_PROTOCOL_DRAFT_SCHEMA_VERSION
    assert draft.research_question_language == "zh"
    assert draft.pico_mode == PICO_MODE_PECO
    assert draft.draft_source == "shared_query_intelligence"
    assert payload["status"] == "draft"
    assert payload["schema_version"] == PICO_PROTOCOL_DRAFT_SCHEMA_VERSION
    assert all(token not in rendered for token in ("geo", "gse", "tcga", "gtex"))
    assert any(event.action == "draft_created" and event.target_type == "final_peco" for event in governance_events)
    assert any(event.action == "suggestion_created" and event.target_type == "meta_type_candidate" for event in governance_events)
    assert not service.confirmed_path(tmp_path).exists()


def test_pico_workspace_supports_pico_peco_and_picos_modes(tmp_path: Path) -> None:
    service = PICOWorkspaceService()

    pico = service.generate_draft(tmp_path / "pico", "成人肺炎患者使用糖皮质激素能否降低死亡率", pico_mode="pico")
    peco = service.generate_draft(tmp_path / "peco", "肥胖暴露与甲状腺癌风险是否相关", pico_mode="peco")
    picos = service.generate_draft(tmp_path / "picos", "PICOS：成人肺炎、糖皮质激素、常规治疗、死亡率、随机对照试验", pico_mode="picos")

    assert pico.pico_mode == PICO_MODE_PICO
    assert peco.pico_mode == PICO_MODE_PECO
    assert picos.pico_mode == PICO_MODE_PICOS
    assert "requires_human_confirmation" in pico.warnings
    assert "requires_human_confirmation" in peco.warnings
    assert "requires_human_confirmation" in picos.warnings


def test_pico_workspace_edit_and_confirm_are_separate_versioned_artifacts(tmp_path: Path) -> None:
    service = PICOWorkspaceService()
    draft = service.generate_draft(tmp_path, "成人肺炎患者中糖皮质激素与死亡率", pico_mode="pico")

    edited = service.edit_draft(
        tmp_path,
        actor="reviewer",
        updates={
            "population": "成人重症肺炎患者",
            "intervention": "系统性糖皮质激素",
            "comparator": "安慰剂或常规治疗",
            "outcome": "死亡率",
            "study_design": "randomized controlled trial",
        },
    )
    confirmed = service.confirm_protocol(
        tmp_path,
        actor="reviewer",
        confirmed_meta_type="treatment_comparative_meta",
        user_notes="人工确认 PICO。",
    )
    draft_versions = json.loads(service.draft_versions_path(tmp_path).read_text(encoding="utf-8"))
    confirmed_payload = json.loads(service.confirmed_path(tmp_path).read_text(encoding="utf-8"))
    governance_events = MetaResearchGovernanceService().list_events(tmp_path)
    audit_events = MetaAuditLogService().list_events(tmp_path)

    assert draft.protocol_id == edited.protocol_id
    assert edited.version == draft.version + 1
    assert confirmed.schema_version == CONFIRMED_PROTOCOL_SCHEMA_VERSION
    assert confirmed.source_draft_id == draft.protocol_id
    assert confirmed.confirmed_population == "成人重症肺炎患者"
    assert confirmed.locked_for_search_strategy is True
    assert confirmed_payload["schema_version"] == CONFIRMED_PROTOCOL_SCHEMA_VERSION
    assert draft_versions["versions"][0]["status"] == "draft"
    assert draft_versions["versions"][-1]["population"] == "成人重症肺炎患者"
    assert any(event.action == "edit" and event.status == "user_edited" for event in governance_events)
    assert any(event.action == "confirm" and event.status == "confirmed" for event in governance_events)
    assert any(event.event_type == "record_saved" and event.target_type == "pico_workspace_confirmed_protocol_v2" for event in audit_events)


def test_pico_workspace_meta_type_candidates_are_not_final_until_confirmed(tmp_path: Path) -> None:
    service = PICOWorkspaceService()

    draft = service.generate_draft(tmp_path, "吸烟暴露与肺癌风险的病例对照研究", pico_mode="auto")
    candidate_types = [item["meta_type"] for item in draft.meta_type_candidates]

    assert candidate_types[0] == "exposure_disease_risk_meta"
    assert "network_meta_coming_soon" in candidate_types
    assert all(item["requires_user_confirmation"] is True for item in draft.meta_type_candidates)
    assert service.load_confirmed(tmp_path) is None

    confirmed = service.confirm_protocol(tmp_path, actor="reviewer", confirmed_meta_type="exposure_disease_risk_meta")

    assert confirmed.confirmed_meta_type == "exposure_disease_risk_meta"


def test_pico_workspace_does_not_execute_search_screening_or_prisma(tmp_path: Path) -> None:
    service = PICOWorkspaceService()

    service.generate_draft(tmp_path, "成人肺炎患者中糖皮质激素与死亡率", pico_mode="pico")
    service.confirm_protocol(tmp_path, actor="reviewer", confirmed_meta_type="treatment_comparative_meta")
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    assert not (tmp_path / "protocol" / "search_execution_report.json").exists()
    assert not (tmp_path / "screening").exists()
    assert prisma.records_screened == 0
    assert prisma.records_excluded_title_abstract == 0
    assert prisma.full_text_reports_assessed == 0
    assert prisma.studies_included == 0


def test_pico_workspace_page_helpers_write_v2_artifacts(tmp_path: Path) -> None:
    draft = build_pico_workspace_draft(tmp_path, "肥胖暴露与甲状腺癌风险", pico_mode="peco")
    confirmed = confirm_pico_workspace_protocol(
        tmp_path,
        actor="reviewer",
        confirmed_meta_type="exposure_disease_risk_meta",
    )

    assert draft.schema_version == PICO_PROTOCOL_DRAFT_SCHEMA_VERSION
    assert confirmed.source_draft_id == draft.protocol_id
