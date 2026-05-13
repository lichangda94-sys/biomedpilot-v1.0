from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.meta_analysis.pages.extraction_page import initial_extraction_state, simplified_extraction_state_from_project
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.extraction_schema_registry_v1_service import (
    BINARY_OUTCOME_META,
    DIAGNOSTIC_ACCURACY_META_V1,
    DOSE_RESPONSE_META,
    EXTRACTION_SCHEMA_REGISTRY_V1_SCHEMA_VERSION,
    EXTRACTION_SCHEMA_SELECTION_SCHEMA_VERSION,
    SURVIVAL_OUTCOME_META,
    ExtractionSchemaRegistryV1Service,
)
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


def test_extraction_schema_registry_v1_writes_ten_schema_profiles(tmp_path: Path) -> None:
    service = ExtractionSchemaRegistryV1Service()

    registry = service.save_default_registry(tmp_path, project_id="meta-extraction-schema")
    payload = json.loads(service.registry_path(tmp_path).read_text(encoding="utf-8"))
    meta_types = {schema["meta_type"] for schema in payload["schemas"]}

    assert registry.schema_version == EXTRACTION_SCHEMA_REGISTRY_V1_SCHEMA_VERSION
    assert payload["schema_count"] == 10
    assert {
        BINARY_OUTCOME_META,
        SURVIVAL_OUTCOME_META,
        DIAGNOSTIC_ACCURACY_META_V1,
        DOSE_RESPONSE_META,
    } <= meta_types
    assert payload["safety_note"].startswith("Extraction schemas generate")


def test_extraction_schema_registry_v1_contains_required_fields_and_mappings(tmp_path: Path) -> None:
    service = ExtractionSchemaRegistryV1Service()
    service.save_default_registry(tmp_path)

    diagnostic = service.get_schema(tmp_path, DIAGNOSTIC_ACCURACY_META_V1)
    survival = service.get_schema(tmp_path, SURVIVAL_OUTCOME_META)
    dose = service.get_schema(tmp_path, DOSE_RESPONSE_META)

    assert diagnostic is not None
    assert {"tp", "fp", "fn", "tn"} <= set(diagnostic.required_fields)
    assert "QUADAS-2" in diagnostic.quality_tool_recommendation
    assert diagnostic.analysis_defaults["advanced_model"] == "bivariate_hsroc_not_implemented"
    assert survival is not None
    assert {"hr", "ci_lower", "ci_upper"} <= set(survival.required_fields)
    assert survival.effect_size_mapping["supported"] == ["HR"]
    assert dose is not None
    assert {"dose", "cases", "non_cases", "person_years"} <= set(dose.required_fields)


def test_extraction_schema_registry_v1_builds_form_template_from_confirmed_meta_alias(tmp_path: Path) -> None:
    service = ExtractionSchemaRegistryV1Service()
    service.save_default_registry(tmp_path)

    template = service.build_form_template(tmp_path, "diagnostic_accuracy_meta")

    assert template["meta_type"] == DIAGNOSTIC_ACCURACY_META_V1
    assert "tp" in template["field_order"]
    assert "diagnostic_counts_must_be_non_negative" in template["validation_rules"]
    assert template["safety_note"].startswith("Template fields require manual")


def test_extraction_schema_selection_writes_audit_governance_without_extraction_or_prisma(tmp_path: Path) -> None:
    service = ExtractionSchemaRegistryV1Service()
    service.save_default_registry(tmp_path)

    selection = service.save_schema_selection(tmp_path, meta_type="binary_outcome_meta", actor="reviewer", confirm=True)
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)
    audit = MetaAuditLogService().list_events(tmp_path)
    governance = MetaResearchGovernanceService().list_events(tmp_path)

    assert selection["schema_version"] == EXTRACTION_SCHEMA_SELECTION_SCHEMA_VERSION
    assert selection["selected_meta_type"] == BINARY_OUTCOME_META
    assert selection["status"] == "confirmed"
    assert selection["writes_final_extraction"] is False
    assert not (tmp_path / "extraction" / "extraction_records.json").exists()
    assert not (tmp_path / "analysis" / "analysis_ready_datasets.json").exists()
    assert prisma.studies_included == 0
    assert any(event.target_type == "extraction_schema_selection" for event in audit)
    assert any(event.target_type == "extraction_schema_selection" and event.status == "confirmed" for event in governance)


def test_extraction_schema_registry_v1_page_states_expose_schema_options(tmp_path: Path) -> None:
    service = ExtractionSchemaRegistryV1Service()
    service.save_default_registry(tmp_path)
    service.save_schema_selection(tmp_path, meta_type=SURVIVAL_OUTCOME_META, actor="reviewer")

    initial = initial_extraction_state()
    simplified = simplified_extraction_state_from_project(tmp_path, schema_registry_service=service)

    assert initial.extraction_schema_count == 10
    assert SURVIVAL_OUTCOME_META in initial.extraction_schema_options
    assert simplified.extraction_schema_registry_version == EXTRACTION_SCHEMA_REGISTRY_V1_SCHEMA_VERSION
    assert simplified.extraction_schema_count == 10
    assert simplified.selected_extraction_schema_path.endswith("extraction/selected_extraction_schema_v1.json")


def test_extraction_schema_registry_v1_rejects_unknown_meta_type(tmp_path: Path) -> None:
    service = ExtractionSchemaRegistryV1Service()
    service.save_default_registry(tmp_path)

    with pytest.raises(ValueError, match="unsupported_extraction_schema_meta_type"):
        service.build_form_template(tmp_path, "network_meta_coming_soon")
