from __future__ import annotations

from app.bioinformatics.deg_engine.r_count_model_planning import build_r_count_model_activation_plan, build_r_count_model_activation_plans


def test_deseq2_count_model_plan_requires_user_confirmation_before_execution() -> None:
    plan = build_r_count_model_activation_plan(
        "DESeq2",
        deg_ready_package=_deg_ready("count", "raw_count_matrix"),
        design_config=_design_config(),
        external_capabilities=_capabilities("deseq2"),
        dependency_snapshot=_dependency_snapshot(),
    )

    assert plan["status"] == "planned_not_enabled"
    assert plan["formal_execution_enabled"] is False
    assert plan["can_register_formal_result"] is False
    assert plan["writes_result_index"] is False
    assert plan["preflight"]["status"] == "design_ready"
    assert plan["runtime_gate"]["status"] == "ready_for_external_runtime_execution"
    assert "b25_10_deseq2_ui_activation_preflight_only" not in plan["blockers"]
    assert "b25_11_deseq2_ui_activation_required" not in plan["blockers"]
    assert "r_deseq2_parameter_confirmation_missing" in plan["blockers"]
    assert plan["parameter_manifest"]["status"] == "passed"
    assert plan["parameter_confirmation_gate"]["status"] == "blocked"
    assert plan["rscript_adapter_plan"]["formal_execution_enabled"] is False
    assert plan["input_policy"]["accepted_value_types"] == ["count", "raw_count", "raw_counts", "integer_count"]


def test_edger_count_model_plan_blocks_display_value_type_and_missing_count_matrix() -> None:
    plan = build_r_count_model_activation_plan(
        "edgeR",
        deg_ready_package=_deg_ready("TPM", "normalized_expression_matrix"),
        design_config=_design_config(),
        external_capabilities=_capabilities("edger"),
        dependency_snapshot=_dependency_snapshot(),
    )

    assert plan["formal_execution_enabled"] is False
    assert "count_model_requested_for_display_value_type" in plan["blockers"]
    assert "count_model_requires_count_value_type" in plan["blockers"]
    assert "count_matrix_missing_for_deseq2_or_edger" in plan["blockers"]
    assert "b25_12_edger_planning_only_no_execution" in plan["blockers"]
    assert "edger_rscript_execution_adapter_not_implemented" in plan["blockers"]


def test_count_model_plan_matrix_contains_deseq2_and_edger_without_execution() -> None:
    matrix = build_r_count_model_activation_plans(
        deg_ready_package=_deg_ready("count", "raw_count_matrix"),
        design_config=_design_config(),
        external_capabilities={**_capabilities("deseq2"), **_capabilities("edger")},
        dependency_snapshot=_dependency_snapshot(),
    )

    assert matrix["status"] == "planned_not_enabled"
    assert matrix["formal_execution_enabled"] is False
    assert set(matrix["plans"]) == {"deseq2", "edger"}
    assert "r_deseq2_parameter_confirmation_missing" in matrix["blockers"]
    assert "b25_10_deseq2_ui_activation_preflight_only" not in matrix["blockers"]
    assert "b25_11_deseq2_ui_activation_required" not in matrix["blockers"]
    assert "b25_12_edger_planning_only_no_execution" in matrix["blockers"]
    assert "b25_13_edger_real_fixture_required" in matrix["blockers"]
    assert "b25_14_edger_ui_activation_required" in matrix["blockers"]
    assert matrix["plans"]["deseq2"]["parameter_manifest"]["method"] == "deseq2"
    assert matrix["plans"]["edger"]["parameter_manifest"]["method"] == "edger"
    assert matrix["plans"]["edger"]["rscript_adapter_plan"]["formal_execution_enabled"] is False


def _deg_ready(value_type: str, asset_type: str) -> dict[str, object]:
    return {
        "input_package_id": "input-count-1",
        "deg_ready_package_id": "deg-ready-count-1",
        "value_type": value_type,
        "gene_id_type": "symbol",
        "matrix_asset": {"asset_type": asset_type, "path": "/tmp/counts.tsv"},
        "gene_mapping_status": {"status": "passed"},
        "sample_alignment_status": {"status": "passed"},
        "blockers": [],
        "warnings": [],
    }


def _design_config() -> dict[str, object]:
    return {
        "schema_version": "biomedpilot.deg_multifactor_design_config.v1",
        "primary_factor": "group",
        "case_group": "case",
        "control_group": "control",
        "sample_table": [
            {"sample_id": "case_1", "group": "case"},
            {"sample_id": "case_2", "group": "case"},
            {"sample_id": "control_1", "group": "control"},
            {"sample_id": "control_2", "group": "control"},
        ],
        "contrast": {
            "contrast_id": "case_vs_control",
            "factor": "group",
            "case_level": "case",
            "control_level": "control",
        },
        "covariates": [],
        "blockers": [],
        "warnings": [],
    }


def _capabilities(method: str) -> dict[str, object]:
    package_key = "package.r.deseq2.available" if method == "deseq2" else "package.r.edger.available"
    return {
        "runtime.r.available": {"available": True, "version": "4.4.2"},
        "runtime.bioconductor.available": {"available": True, "version": "3.20"},
        package_key: {"available": True, "version": "1.0.0"},
    }


def _dependency_snapshot() -> dict[str, object]:
    return {
        "status": "passed",
        "runtime": "system_rscript_detect_only",
        "dependencies": {},
        "blockers": [],
    }
