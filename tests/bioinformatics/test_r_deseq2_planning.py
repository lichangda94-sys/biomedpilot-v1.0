from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_engine.r_deseq2_planning import (
    build_r_deseq2_parameter_manifest,
    build_r_deseq2_rscript_adapter_plan,
    load_r_deseq2_parameter_confirmation,
    save_r_deseq2_parameter_confirmation,
    validate_r_deseq2_parameter_confirmation,
)
from app.bioinformatics.deg_engine.r_adapter_contract import build_r_deg_runtime_gate


def test_deseq2_parameter_manifest_passes_for_raw_count_design() -> None:
    preflight = _preflight()
    manifest = build_r_deseq2_parameter_manifest(
        _deg_ready("count", "raw_count_matrix"),
        multi_factor_preflight=preflight,
        dependency_snapshot=_dependency_snapshot(),
        minimum_count_filter=5,
        size_factor_policy="poscounts",
        dispersion_fit_type="local",
    )

    assert manifest["status"] == "passed"
    assert manifest["method"] == "deseq2"
    assert manifest["method_family"] == "deseq2_count_model"
    assert manifest["count_integer_policy"] == "raw_integer_counts_required_no_tpm_fpkm_or_log_values"
    assert manifest["minimum_count_filter"] == 5
    assert manifest["size_factor_policy"] == "poscounts"
    assert manifest["dispersion_fit_type"] == "local"


def test_deseq2_parameter_manifest_blocks_display_values_and_bad_policy() -> None:
    manifest = build_r_deseq2_parameter_manifest(
        _deg_ready("TPM", "normalized_expression_matrix"),
        multi_factor_preflight={**_preflight(value_type="TPM"), "blockers": []},
        dependency_snapshot={"status": "blocked", "blockers": ["DESeq2_missing"]},
        minimum_count_filter=-1,
        size_factor_policy="invalid",
        dispersion_fit_type="invalid",
    )

    assert manifest["status"] == "blocked"
    assert "r_deseq2_display_value_type_not_allowed" in manifest["blockers"]
    assert "r_deseq2_raw_integer_counts_required" in manifest["blockers"]
    assert "r_deseq2_dependency_snapshot_not_passed" in manifest["blockers"]
    assert "invalid_minimum_count_filter" in manifest["blockers"]
    assert "invalid_deseq2_size_factor_policy" in manifest["blockers"]
    assert "invalid_deseq2_dispersion_fit_type" in manifest["blockers"]


def test_deseq2_parameter_confirmation_can_be_saved_and_validated(tmp_path: Path) -> None:
    confirmation = save_r_deseq2_parameter_confirmation(
        tmp_path,
        deg_ready_package=_deg_ready("count", "raw_count_matrix"),
        multi_factor_preflight=_preflight(),
        dependency_snapshot=_dependency_snapshot(),
        fdr_threshold=0.1,
    )
    loaded = load_r_deseq2_parameter_confirmation(tmp_path)
    current = build_r_deseq2_parameter_manifest(
        _deg_ready("count", "raw_count_matrix"),
        multi_factor_preflight=_preflight(),
        dependency_snapshot=_dependency_snapshot(),
        fdr_threshold=0.1,
    )
    gate = validate_r_deseq2_parameter_confirmation(
        loaded,
        parameter_manifest=current,
        dependency_snapshot=_dependency_snapshot(),
    )

    assert confirmation["status"] == "confirmed"
    assert loaded["schema_version"] == "biomedpilot.r_deseq2_parameter_confirmation.v1"
    assert gate["status"] == "passed"
    assert loaded["output_plan"]["result_index_registry_path"] == "results/summaries/result_index.json"


def test_deseq2_adapter_plan_never_enables_execution_before_real_fixture_activation() -> None:
    preflight = _preflight()
    manifest = build_r_deseq2_parameter_manifest(
        _deg_ready("count", "raw_count_matrix"),
        multi_factor_preflight=preflight,
        dependency_snapshot=_dependency_snapshot(),
    )
    runtime_gate = build_r_deg_runtime_gate(
        method="deseq2",
        multi_factor_preflight=preflight,
        external_capabilities=_capabilities(),
        dependency_snapshot=_dependency_snapshot(),
    )
    confirmation_gate = {"status": "passed", "blockers": [], "warnings": []}
    plan = build_r_deseq2_rscript_adapter_plan(
        parameter_manifest=manifest,
        runtime_gate=runtime_gate,
        confirmation_gate=confirmation_gate,
    )

    assert runtime_gate["status"] == "ready_for_external_runtime_execution"
    assert plan["status"] == "planned_not_enabled"
    assert plan["formal_execution_enabled"] is False
    assert plan["can_execute"] is False
    assert plan["writes_result_index"] is False
    assert "b25_7_deseq2_rscript_adapter_planning_only" in plan["blockers"]
    assert "deseq2_rscript_execution_adapter_not_implemented" in plan["blockers"]
    assert "deseq2_result_registration_handoff_not_implemented" in plan["blockers"]


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
        "method": "deseq2",
        "method_family": "deseq2_count_model",
        "value_type": value_type,
        "value_type_policy": "deseq2_requires_raw_integer_counts",
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
            "DESeq2": {"version": "1.46.0"},
        },
        "blockers": [],
    }


def _capabilities() -> dict[str, object]:
    return {
        "runtime.r.available": {"available": True, "version": "4.4.2"},
        "runtime.bioconductor.available": {"available": True, "version": "3.20"},
        "package.r.deseq2.available": {"available": True, "version": "1.46.0"},
    }
