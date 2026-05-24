from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_engine.r_adapter_contract import build_r_deg_runtime_gate
from app.bioinformatics.deg_engine.r_edger_planning import (
    build_r_edger_parameter_manifest,
    build_r_edger_rscript_adapter_plan,
    validate_r_edger_parameter_confirmation,
)
from app.bioinformatics.deg_engine.r_edger_runtime import detect_r_edger_runtime_capabilities
from app.bioinformatics.deg_engine.r_edger_runtime_validation import run_r_edger_runtime_validation


def test_edger_parameter_manifest_passes_for_raw_count_design() -> None:
    manifest = build_r_edger_parameter_manifest(
        _deg_ready("count", "raw_count_matrix"),
        multi_factor_preflight=_preflight(),
        dependency_snapshot=_dependency_snapshot(),
        minimum_count_filter=5,
        normalization_method="TMM",
        dispersion_policy="estimate_common_trended_tagwise",
        test_method="exact_test",
    )

    assert manifest["status"] == "passed"
    assert manifest["method"] == "edger"
    assert manifest["method_family"] == "edger_count_model"
    assert manifest["normalization_method"] == "TMM"
    assert manifest["dispersion_policy"] == "estimate_common_trended_tagwise"
    assert manifest["test_method"] == "exact_test"
    assert manifest["count_integer_policy"] == "raw_integer_counts_required_no_tpm_fpkm_or_log_values"


def test_edger_parameter_manifest_blocks_display_values_and_bad_policy() -> None:
    manifest = build_r_edger_parameter_manifest(
        _deg_ready("TPM", "normalized_expression_matrix"),
        multi_factor_preflight={**_preflight(value_type="TPM"), "blockers": []},
        dependency_snapshot={"status": "blocked", "blockers": ["edgeR_missing"]},
        minimum_count_filter=-1,
        normalization_method="bad",
        dispersion_policy="bad",
        test_method="bad",
    )

    assert manifest["status"] == "blocked"
    assert "r_edger_display_value_type_not_allowed" in manifest["blockers"]
    assert "r_edger_raw_integer_counts_required" in manifest["blockers"]
    assert "r_edger_dependency_snapshot_not_passed" in manifest["blockers"]
    assert "invalid_minimum_count_filter" in manifest["blockers"]
    assert "invalid_edger_normalization_method" in manifest["blockers"]
    assert "invalid_edger_dispersion_policy" in manifest["blockers"]
    assert "invalid_edger_test_method" in manifest["blockers"]


def test_edger_adapter_plan_is_planning_only_even_when_runtime_ready() -> None:
    preflight = _preflight()
    manifest = build_r_edger_parameter_manifest(
        _deg_ready("count", "raw_count_matrix"),
        multi_factor_preflight=preflight,
        dependency_snapshot=_dependency_snapshot(),
    )
    runtime_gate = build_r_deg_runtime_gate(
        method="edger",
        multi_factor_preflight=preflight,
        external_capabilities=_capabilities(),
        dependency_snapshot=_dependency_snapshot(),
    )
    confirmation_gate = validate_r_edger_parameter_confirmation(
        {},
        parameter_manifest=manifest,
        dependency_snapshot=_dependency_snapshot(),
    )
    plan = build_r_edger_rscript_adapter_plan(
        parameter_manifest=manifest,
        runtime_gate=runtime_gate,
        confirmation_gate=confirmation_gate,
    )

    assert runtime_gate["status"] == "ready_for_external_runtime_execution"
    assert plan["status"] == "planned_not_enabled"
    assert plan["formal_execution_enabled"] is False
    assert plan["can_execute"] is False
    assert plan["writes_result_index"] is False
    assert plan["result_semantics"] == "not_executed"
    assert "b25_12_edger_planning_only_no_execution" in plan["blockers"]
    assert "b25_13_edger_real_fixture_required" in plan["blockers"]
    assert "b25_14_edger_ui_activation_required" in plan["blockers"]
    assert "edger_rscript_execution_adapter_not_implemented" in plan["blockers"]


def test_edger_runtime_detection_is_detect_first_graceful() -> None:
    detection = detect_r_edger_runtime_capabilities(timeout_seconds=20)

    assert detection["schema_version"] == "biomedpilot.r_edger_runtime_detection.v1"
    assert detection["status"] in {"passed", "blocked"}
    assert "dependency_snapshot" in detection
    assert detection["dependency_snapshot"]["runtime"] == "system_rscript"
    assert detection["dependency_snapshot"]["dependencies"]["edgeR"]["available"] in {True, False}


def test_edger_runtime_validation_does_not_enable_execution(tmp_path: Path) -> None:
    output_path = tmp_path / "edger_runtime.json"
    validation = run_r_edger_runtime_validation(output_path=output_path)

    assert output_path.is_file()
    assert validation["schema_version"] == "biomedpilot.b25_12_r_edger_runtime_validation.v1"
    assert validation["status"] in {"passed", "blocked_missing_dependency"}
    preflight = validation["execution_activation_preflight"]
    assert preflight["formal_execution_enabled"] is False
    assert preflight["normal_user_button_enabled"] is False
    assert "b25_12_edger_planning_only_no_execution" in preflight["blockers"]
    assert "b25_13_edger_real_fixture_required" in preflight["blockers"]
    assert "b25_14_edger_ui_activation_required" in preflight["blockers"]


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


def _preflight(value_type: str = "count") -> dict[str, object]:
    return {
        "status": "design_ready",
        "method": "edger",
        "method_family": "edger_count_model",
        "value_type": value_type,
        "value_type_policy": "edger_requires_raw_integer_counts",
        "input_package_id": "input-count-1",
        "deg_ready_package_id": "deg-ready-count-1",
        "gene_id_type": "symbol",
        "contrast": {
            "contrast_id": "case_vs_control",
            "factor": "group",
            "case_level": "case",
            "control_level": "control",
            "case_samples": ["case_1", "case_2"],
            "control_samples": ["control_1", "control_2"],
        },
        "blockers": [],
        "warnings": [],
    }


def _dependency_snapshot() -> dict[str, object]:
    return {
        "status": "passed",
        "runtime": "system_rscript_detect_only",
        "dependencies": {
            "R": {"version": "4.4.2"},
            "BiocManager": {"version": "1.30.25"},
            "edgeR": {"version": "4.4.2"},
        },
        "blockers": [],
    }


def _capabilities() -> dict[str, object]:
    return {
        "runtime.r.available": {"available": True, "version": "4.4.2"},
        "runtime.bioconductor.available": {"available": True, "version": "3.20"},
        "package.r.edger.available": {"available": True, "version": "4.4.2"},
    }
