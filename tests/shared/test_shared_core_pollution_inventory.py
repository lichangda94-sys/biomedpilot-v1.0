from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TERMS = ROOT / "data" / "medical_terms"
REPORTS = TERMS / "review_reports"
SCHEMA = TERMS / "schema" / "medical_terms_scope_usage_schema.json"


def test_shared_core_pollution_inventory_artifacts_exist_and_do_not_modify_runtime() -> None:
    inventory = json.loads((REPORTS / "shared_core_pollution_inventory.json").read_text(encoding="utf-8"))
    manual_review = (REPORTS / "shared_core_pollution_manual_review.jsonl").read_text(encoding="utf-8").splitlines()

    assert inventory["inventory_name"] == "shared_core_pollution_inventory"
    assert inventory["inventory_date"] == "2026-05-20"
    assert inventory["runtime_modified"] is False
    assert inventory["source"] == "data/medical_terms/mini_medical_terms_index.json"
    assert inventory["total_suspected_pollution_terms"] == len(inventory["items"])
    assert inventory["total_suspected_pollution_terms"] >= 100
    assert len(manual_review) > 0
    assert (TERMS / "mini_medical_terms_index.json").exists()
    assert (TERMS / "zh_term_overrides.json").exists()
    assert (TERMS / "meta_analysis" / "meta_migrated_from_shared_terms.json").exists()
    assert (TERMS / "meta_analysis" / "legacy_meta_compatibility_map.json").exists()


def test_shared_core_pollution_inventory_classifies_known_meta_terms() -> None:
    inventory = json.loads((REPORTS / "shared_core_pollution_inventory.json").read_text(encoding="utf-8"))
    by_concept = {item["concept_id"]: item for item in inventory["items"]}

    assert by_concept["mini:meta_outcomes_core"]["pollution_category"] == "meta_outcome"
    assert by_concept["mini:effect_size_core"]["pollution_category"] == "meta_effect_measure"
    assert by_concept["mini:study_design_core"]["pollution_category"] == "meta_study_design"
    assert by_concept["mini:meta_analysis_hazard_ratio"]["pollution_category"] == "meta_effect_measure"
    assert by_concept["mini:meta_analysis_overall_survival"]["pollution_category"] == "meta_outcome"
    assert by_concept["mini:meta_analysis_cohort_study"]["pollution_category"] == "meta_study_design"
    assert by_concept["mini:meta_analysis_exposure"]["pollution_category"] == "meta_research_intent"
    assert by_concept["mini:modality_survival_data"]["manual_review_required"] is True


def test_shared_core_pollution_manual_review_rows_are_structured() -> None:
    rows = [
        json.loads(line)
        for line in (REPORTS / "shared_core_pollution_manual_review.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert rows
    assert all(row["phase"] == "S1_shared_core_pollution_inventory" for row in rows)
    assert all(row["recommended_action"] == "manual_review" for row in rows)
    assert all(row["auto_fix_applied"] is False for row in rows)
    assert any(row["concept_id"] == "mini:modality_survival_data" for row in rows)


def test_scope_usage_schema_contains_required_fields_and_allowed_values() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    required = set(schema["required"])
    query_values = set(_jsonable_enum(schema["properties"]["usage"]["properties"]["query_expansion_allowed"]["enum"]))
    migration_statuses = set(schema["properties"]["migration"]["properties"]["migration_status"]["enum"])

    assert {"scope", "usage", "requires_context", "migration"} <= required
    assert {
        "shared_core_allowed",
        "bioinformatics_allowed",
        "meta_analysis_allowed",
    } <= set(schema["properties"]["scope"]["required"])
    assert {"true", "false", "conditional", "filter_only"} <= query_values
    assert {
        "not_migrated",
        "candidate_for_migration",
        "mirrored_to_meta_scoped",
        "mirrored_to_bioinformatics_scoped",
        "deprecated_in_shared",
        "removed_from_shared",
        "manual_review_required",
    } <= migration_statuses
    assert {
        "legacy_concept_id",
        "new_concept_id",
        "migration_status",
        "compatibility_alias",
        "active_in_shared",
    } <= set(schema["properties"]["migration"]["required"])
    assert "profile_hint_allowed" in schema["properties"]["usage"]["properties"]


def test_inventory_docs_exist() -> None:
    assert (ROOT / "docs" / "medical_terms" / "shared_core_pollution_inventory_20260520.md").exists()
    assert (ROOT / "docs" / "medical_terms" / "shared_core_pollution_manual_review_required.md").exists()
    assert (ROOT / "docs" / "medical_terms" / "medical_terms_scope_usage_schema_20260520.md").exists()


def _jsonable_enum(values: list[object]) -> list[str]:
    converted: list[str] = []
    for value in values:
        if value is True:
            converted.append("true")
        elif value is False:
            converted.append("false")
        else:
            converted.append(str(value))
    return converted
