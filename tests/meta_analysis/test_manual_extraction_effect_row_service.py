from __future__ import annotations

import csv
import json
from pathlib import Path

from app.meta_analysis.pages.extraction_page import manual_extraction_effect_row_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.extraction_schema_registry_v1_service import (
    BINARY_OUTCOME_META,
    CONTINUOUS_OUTCOME_META,
    DIAGNOSTIC_ACCURACY_META_V1,
    SURVIVAL_OUTCOME_META,
    ExtractionSchemaRegistryV1Service,
)
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.fulltext_management_service import (
    FULLTEXT_STATUS_FULL_TEXT_CONFIRMED,
    FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE,
)
from app.meta_analysis.services.manual_extraction_effect_row_service import (
    MANUAL_EXTRACTION_MANIFEST_SCHEMA_VERSION,
    STRUCTURED_EXTRACTION_EFFECT_MEASURES,
    STRUCTURED_EXTRACTION_EVIDENCE_STATES,
    STRUCTURED_EXTRACTION_TABLE_SCHEMA_VERSION,
    ManualExtractionEffectRowService,
)
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def test_manual_extraction_allows_multiple_study_units_and_effect_rows(tmp_path: Path) -> None:
    service = ManualExtractionEffectRowService()

    first_unit = service.create_study_unit(tmp_path, record_id="rec-1", study_unit_label="Trial cohort A")
    second_unit = service.create_study_unit(tmp_path, record_id="rec-1", study_unit_label="Trial cohort B")
    first_row = service.create_effect_row(
        tmp_path,
        study_unit_id=first_unit.payload["study_unit_id"],
        schema_meta_type=BINARY_OUTCOME_META,
        outcome_name="Response",
        data_fields={"group_1_n": 60, "group_1_events": 20, "group_2_n": 60, "group_2_events": 10},
    )
    second_row = service.create_effect_row(
        tmp_path,
        study_unit_id=first_unit.payload["study_unit_id"],
        schema_meta_type=BINARY_OUTCOME_META,
        outcome_name="Mortality",
        analysis_role="secondary_effect_candidate",
        data_fields={"group_1_n": 60, "group_1_events": 5, "group_2_n": 60, "group_2_events": 8},
    )

    assert len(service.load_study_units(tmp_path)) == 2
    assert len(service.load_effect_rows(tmp_path)) == 2
    assert first_row.payload["record_id"] == "rec-1"
    assert second_row.payload["study_unit_id"] == first_unit.payload["study_unit_id"]
    assert second_unit.payload["study_unit_label"] == "Trial cohort B"


def test_manual_extraction_validates_binary_continuous_survival_and_diagnostic_rows(tmp_path: Path) -> None:
    service = ManualExtractionEffectRowService()
    unit = service.create_study_unit(tmp_path, record_id="rec-1", study_unit_label="Study A").payload

    binary = service.create_effect_row(
        tmp_path,
        study_unit_id=unit["study_unit_id"],
        schema_meta_type=BINARY_OUTCOME_META,
        outcome_name="Response",
        data_fields={"group_1_n": 60, "group_1_events": 20, "group_2_n": 60, "group_2_events": 10},
    )
    continuous = service.create_effect_row(
        tmp_path,
        study_unit_id=unit["study_unit_id"],
        schema_meta_type=CONTINUOUS_OUTCOME_META,
        outcome_name="Score",
        analysis_role="secondary_effect_candidate",
        data_fields={"group_1_n": 30, "group_1_mean": 12.4, "group_1_sd": 2.1, "group_2_n": 30, "group_2_mean": 10.1, "group_2_sd": 2.4},
    )
    survival = service.create_effect_row(
        tmp_path,
        study_unit_id=unit["study_unit_id"],
        schema_meta_type=SURVIVAL_OUTCOME_META,
        data_input_mode="reported_effect_size",
        outcome_name="Overall survival",
        analysis_role="secondary_effect_candidate",
        data_fields={"effect_measure": "HR", "effect_value": 0.72, "ci_low": 0.55, "ci_high": 0.94},
    )
    diagnostic = service.create_effect_row(
        tmp_path,
        study_unit_id=unit["study_unit_id"],
        schema_meta_type=DIAGNOSTIC_ACCURACY_META_V1,
        outcome_name="Diagnosis",
        analysis_role="secondary_effect_candidate",
        data_fields={"tp": 42, "fp": 5, "fn": 8, "tn": 45},
    )

    assert binary.payload["validation_status"] == "valid"
    assert continuous.payload["validation_status"] == "valid"
    assert survival.payload["validation_status"] == "valid"
    assert diagnostic.payload["validation_status"] == "valid"


def test_manual_extraction_keeps_raw_and_reported_effect_size_separate(tmp_path: Path) -> None:
    service = ManualExtractionEffectRowService()
    unit = service.create_study_unit(tmp_path, record_id="rec-1", study_unit_label="Study A").payload

    raw = service.create_effect_row(
        tmp_path,
        study_unit_id=unit["study_unit_id"],
        schema_meta_type=BINARY_OUTCOME_META,
        outcome_name="Response",
        data_fields={"group_1_n": 60, "group_1_events": 20, "group_2_n": 60, "group_2_events": 10},
    )
    reported = service.create_effect_row(
        tmp_path,
        study_unit_id=unit["study_unit_id"],
        schema_meta_type=SURVIVAL_OUTCOME_META,
        data_input_mode="reported_effect_size",
        outcome_name="Overall survival",
        analysis_role="secondary_effect_candidate",
        data_fields={"effect_measure": "HR", "effect_value": 0.72, "ci_low": 0.55, "ci_high": 0.94},
    )

    assert raw.payload["raw_group_data"]["group_1_events"] == 20
    assert raw.payload["reported_effect_size"] == {}
    assert reported.payload["reported_effect_size"]["effect_measure"] == "HR"
    assert reported.payload["raw_group_data"] == {}


def test_manual_extraction_missing_required_fields_generate_chinese_diagnostics(tmp_path: Path) -> None:
    service = ManualExtractionEffectRowService()
    unit = service.create_study_unit(tmp_path, record_id="rec-1", study_unit_label="Study A").payload

    result = service.create_effect_row(
        tmp_path,
        study_unit_id=unit["study_unit_id"],
        schema_meta_type=BINARY_OUTCOME_META,
        outcome_name="Response",
        data_fields={"group_1_n": 60, "group_1_events": 20},
    )

    assert result.payload["validation_status"] == "invalid_missing_required_fields"
    assert "缺少必填字段：group_2_n" in result.payload["diagnostics"]
    assert "缺少必填字段：group_2_events" in result.payload["diagnostics"]


def test_manual_extraction_multiple_primary_candidates_warn(tmp_path: Path) -> None:
    service = ManualExtractionEffectRowService()
    unit = service.create_study_unit(tmp_path, record_id="rec-1", study_unit_label="Study A").payload
    data = {"group_1_n": 60, "group_1_events": 20, "group_2_n": 60, "group_2_events": 10}

    service.create_effect_row(tmp_path, study_unit_id=unit["study_unit_id"], schema_meta_type=BINARY_OUTCOME_META, outcome_name="Response", data_fields=data)
    service.create_effect_row(tmp_path, study_unit_id=unit["study_unit_id"], schema_meta_type=BINARY_OUTCOME_META, outcome_name="Mortality", data_fields=data)
    report = json.loads(service.validation_report_path(tmp_path).read_text(encoding="utf-8"))

    assert any("多个 primary_effect_candidate" in warning for warning in report["warnings"])


def test_completed_by_user_does_not_create_analysis_dataset_statistics_or_prisma(tmp_path: Path) -> None:
    service = ManualExtractionEffectRowService()
    unit = service.create_study_unit(tmp_path, record_id="rec-1", study_unit_label="Study A").payload
    row = service.create_effect_row(
        tmp_path,
        study_unit_id=unit["study_unit_id"],
        schema_meta_type=BINARY_OUTCOME_META,
        outcome_name="Response",
        data_fields={"group_1_n": 60, "group_1_events": 20, "group_2_n": 60, "group_2_events": 10},
    ).payload

    completed = service.complete_effect_row(tmp_path, effect_row_id=row["effect_row_id"], actor="reviewer")
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)
    manifest = json.loads(service.manifest_path(tmp_path).read_text(encoding="utf-8"))

    assert completed.payload["extraction_status"] == "completed_by_user"
    assert completed.payload["analysis_ready"] is False
    assert manifest["analysis_ready_dataset_created"] is False
    assert manifest["statistics_run"] is False
    assert manifest["prisma_advanced"] is False
    assert not (tmp_path / "analysis" / "analysis_ready_datasets.json").exists()
    assert not (tmp_path / "analysis" / "analysis_results.json").exists()
    assert prisma.studies_included == 0
    assert prisma.records_screened == 0


def test_manual_extraction_csv_template_and_import_as_draft_without_overwrite(tmp_path: Path) -> None:
    service = ManualExtractionEffectRowService()
    template = service.export_empty_template_csv(tmp_path, actor="reviewer", meta_type=BINARY_OUTCOME_META)
    csv_path = tmp_path / "import.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "record_id",
                "study_unit_label",
                "outcome_name",
                "data_input_mode",
                "group_1_n",
                "group_1_events",
                "group_2_n",
                "group_2_events",
                "analysis_role",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "record_id": "rec-1",
                "study_unit_label": "CSV Study",
                "outcome_name": "Response",
                "data_input_mode": "raw_group_data",
                "group_1_n": "60",
                "group_1_events": "20",
                "group_2_n": "60",
                "group_2_events": "10",
                "analysis_role": "primary_effect_candidate",
            }
        )
    imported = service.import_csv_as_draft(tmp_path, csv_path=csv_path, actor="reviewer")
    existing = service.load_effect_rows(tmp_path)[0]
    conflict_csv = tmp_path / "conflict.csv"
    with conflict_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["effect_row_id", "record_id"])
        writer.writeheader()
        writer.writerow({"effect_row_id": existing["effect_row_id"], "record_id": "rec-1"})
    conflict = service.import_csv_as_draft(tmp_path, csv_path=conflict_csv, actor="reviewer")

    assert template.output_path.endswith("manual_extraction_template.csv")
    assert imported.row_count == 1
    assert len(service.load_effect_rows(tmp_path)) == 1
    assert conflict.diagnostics["conflict_count"] == 1
    assert len(service.load_effect_rows(tmp_path)) == 1


def test_manual_extraction_writes_audit_and_research_governance(tmp_path: Path) -> None:
    audit_log = MetaAuditLogService()
    governance = MetaResearchGovernanceService(audit_log=audit_log)
    service = ManualExtractionEffectRowService(audit_log=audit_log, research_governance=governance)
    unit = service.create_study_unit(tmp_path, record_id="rec-1", study_unit_label="Study A", actor="reviewer").payload
    row = service.create_effect_row(
        tmp_path,
        study_unit_id=unit["study_unit_id"],
        schema_meta_type=BINARY_OUTCOME_META,
        outcome_name="Response",
        actor="reviewer",
        data_fields={"group_1_n": 60, "group_1_events": 20, "group_2_n": 60, "group_2_events": 10},
    ).payload
    service.save_effect_row_draft(tmp_path, effect_row_id=row["effect_row_id"], updates={"timepoint": "12 weeks"}, actor="reviewer")
    service.mark_missing_data(tmp_path, effect_row_id=row["effect_row_id"], missing_reason="No subgroup denominator", actor="reviewer")

    extraction_audit = service.extraction_audit_path(tmp_path).read_text(encoding="utf-8")
    governance_events = governance.list_events(tmp_path)
    audit_events = audit_log.list_events(tmp_path)

    assert "extraction_row draft_created" in extraction_audit
    assert "extraction_row user_edited" in extraction_audit
    assert "extraction_row marked_missing" in extraction_audit
    assert any(event.target_type == "extraction_row" and event.action == "draft_created" for event in governance_events)
    assert any(event.target_type == "extraction_row" and event.action == "edit" for event in governance_events)
    assert any(event.event_type == "extraction_updated" for event in audit_events)


def test_manual_extraction_page_state_exposes_effect_row_workspace(tmp_path: Path) -> None:
    schema_service = ExtractionSchemaRegistryV1Service()
    schema_service.save_default_registry(tmp_path)
    schema_service.save_schema_selection(tmp_path, meta_type=DIAGNOSTIC_ACCURACY_META_V1, actor="reviewer", confirm=True)
    service = ManualExtractionEffectRowService(schema_registry=schema_service)
    unit = service.create_study_unit(tmp_path, record_id="rec-1", study_unit_label="Study A").payload
    service.create_effect_row(
        tmp_path,
        study_unit_id=unit["study_unit_id"],
        schema_meta_type=DIAGNOSTIC_ACCURACY_META_V1,
        outcome_name="Diagnosis",
        data_fields={"tp": 42, "fp": 5, "fn": 8, "tn": 45},
    )

    state = manual_extraction_effect_row_state_from_project(tmp_path, service=service, schema_registry_service=schema_service)

    assert state.manifest_schema_version == MANUAL_EXTRACTION_MANIFEST_SCHEMA_VERSION
    assert state.overview.current_meta_type == DIAGNOSTIC_ACCURACY_META_V1
    assert state.overview.study_unit_count == 1
    assert state.overview.effect_row_count == 1
    assert state.editor.dynamic_data_fields == ("tp", "fp", "fn", "tn")
    assert "完成本行提取" in state.primary_actions
    assert state.safety_flags["creates_analysis_ready_dataset"] is False


def test_structured_extraction_creates_schema_row_from_confirmed_fulltext(tmp_path: Path) -> None:
    _seed_fulltext_management(tmp_path, status=FULLTEXT_STATUS_FULL_TEXT_CONFIRMED)
    service = ManualExtractionEffectRowService()

    eligible = service.literature_records_for_extraction(tmp_path)
    result = service.create_structured_extraction_row(
        tmp_path,
        record_id=eligible[0]["record_id"],
        fields={
            "study_id": "study-1",
            "title": "Confirmed full text trial",
            "first_author": "Zhang",
            "year": "2025",
            "country_or_region": "China",
            "study_design": "RCT",
            "population": "Adults",
            "sample_size_total": "120",
            "intervention_or_exposure": "Treatment",
            "comparator": "Control",
            "outcome": "Response",
            "effect_measure_type": "OR",
            "effect_estimate": "1.8",
            "ci_lower": "1.1",
            "ci_upper": "2.9",
        },
        actor="reviewer",
    )
    row = service.load_structured_extraction_table(tmp_path)[0]

    assert eligible[0]["extraction_source"] == "full_text_confirmed"
    assert result.success
    assert row["m5_schema_version"] == STRUCTURED_EXTRACTION_TABLE_SCHEMA_VERSION
    assert row["m5_structured_fields"]["study_id"] == "study-1"
    assert row["m5_structured_fields"]["effect_measure_type"] == "OR"
    assert row["evidence_state"] == "draft"
    assert row["m5_field_states"]["effect_estimate"] == "draft"
    assert row["analysis_ready"] is False


def test_structured_extraction_validation_rules() -> None:
    service = ManualExtractionEffectRowService()

    validation = service.validate_structured_extraction_fields(
        {
            "study_id": "study-1",
            "outcome": "Response",
            "effect_measure_type": "BAD",
            "effect_estimate": "not-number",
            "ci_lower": "3",
            "ci_upper": "2",
            "sample_size_total": "-1",
        },
        evidence_state="confirmed",
    )

    assert validation["validation_status"] == "invalid"
    assert "效应量类型不支持：effect_measure_type" in validation["errors"]
    assert "数值无效：effect_estimate" in validation["errors"]
    assert "数值无效：ci_lower 不能大于 ci_upper" in validation["errors"]
    assert "数值不能为负：sample_size_total" in validation["errors"]
    assert set(STRUCTURED_EXTRACTION_EFFECT_MEASURES) >= {"OR", "RR", "HR", "MD", "SMD", "proportion", "correlation", "diagnostic_accuracy", "other"}


def test_structured_extraction_suggestion_is_not_confirmed_until_user_confirms(tmp_path: Path) -> None:
    service = ManualExtractionEffectRowService()

    suggested = service.create_structured_extraction_row(
        tmp_path,
        fields={"study_id": "study-1", "outcome": "Response", "effect_measure_type": "RR", "effect_estimate": "1.2", "ci_lower": "1.0", "ci_upper": "1.5"},
        evidence_state="suggested",
        field_states={"effect_estimate": "suggested"},
        actor="model",
    )
    row = service.load_structured_extraction_table(tmp_path)[0]

    assert suggested.success
    assert row["evidence_state"] == "suggested"
    assert row["m5_field_states"]["effect_estimate"] == "suggested"
    assert row["extraction_status"] == "draft"
    assert "confirmed" in STRUCTURED_EXTRACTION_EVIDENCE_STATES
    assert not any(event.target_type == "data_extraction_final" for event in MetaResearchGovernanceService().list_events(tmp_path))


def test_structured_extraction_confirmation_requires_identity_and_effect(tmp_path: Path) -> None:
    service = ManualExtractionEffectRowService()
    incomplete = service.create_structured_extraction_row(tmp_path, fields={"study_id": "study-1"}, actor="reviewer")

    blocked = service.confirm_structured_extraction_row(tmp_path, effect_row_id=incomplete.payload["effect_row_id"], actor="reviewer")
    completed = service.update_structured_extraction_row(
        tmp_path,
        effect_row_id=incomplete.payload["effect_row_id"],
        fields={"outcome": "Response", "effect_measure_type": "OR", "effect_estimate": "1.4", "ci_lower": "1.1", "ci_upper": "1.8"},
        actor="reviewer",
    )
    confirmed = service.confirm_structured_extraction_row(tmp_path, effect_row_id=incomplete.payload["effect_row_id"], actor="reviewer")
    row = service.load_structured_extraction_table(tmp_path)[0]

    assert not blocked.success
    assert "确认提取行需要至少一个结局或效应量字段。" in blocked.diagnostics["errors"]
    assert completed.success
    assert confirmed.success
    assert confirmed.payload["evidence_state"] == "confirmed"
    assert row["m5_field_states"]["effect_estimate"] == "confirmed"
    assert row["extraction_status"] == "completed_by_user"
    assert row["analysis_ready"] is False


def test_structured_extraction_persistence_readback_and_unavailable_manual_source(tmp_path: Path) -> None:
    _seed_fulltext_management(tmp_path, record_id="rec-unavailable", title="Unavailable full text", status=FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE)
    service = ManualExtractionEffectRowService()

    eligible = service.literature_records_for_extraction(tmp_path)
    service.create_structured_extraction_row(
        tmp_path,
        record_id="rec-unavailable",
        fields={"study_id": "study-unavailable", "title": "Unavailable full text", "outcome": "Mortality", "effect_measure_type": "other", "notes": "Manual extraction allowed by reviewer."},
        actor="reviewer",
    )
    reloaded = ManualExtractionEffectRowService().load_structured_extraction_table(tmp_path)

    assert eligible[0]["extraction_source"] == "manual_full_text_unavailable"
    assert len(reloaded) == 1
    assert reloaded[0]["m5_structured_fields"]["study_id"] == "study-unavailable"
    assert reloaded[0]["m5_structured_fields"]["effect_measure_type"] == "other"


def _seed_fulltext_management(
    project_dir: Path,
    *,
    record_id: str = "rec-1",
    title: str = "Confirmed full text trial",
    status: str = FULLTEXT_STATUS_FULL_TEXT_CONFIRMED,
) -> None:
    path = project_dir / "fulltext" / "fulltext_management_registry_v1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "meta_fulltext_management_registry.v1",
                "records": [
                    {
                        "record_id": record_id,
                        "title": title,
                        "authors": "Zhang Wei",
                        "first_author": "Zhang",
                        "year": "2025",
                        "journal": "Journal A",
                        "fulltext_status": status,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
