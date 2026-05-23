from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_engine.r_deseq2_planning import (
    build_r_deseq2_dry_run_acceptance_gate,
    build_r_deseq2_parameter_manifest,
    build_r_deseq2_rscript_adapter_plan,
    load_r_deseq2_parameter_confirmation,
    save_r_deseq2_parameter_confirmation,
    validate_r_deseq2_count_fixture,
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


def test_deseq2_adapter_plan_keeps_ui_execution_blocked_after_runtime_preflight() -> None:
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
    assert plan["status"] == "adapter_available_ui_activation_blocked"
    assert plan["formal_execution_enabled"] is False
    assert plan["can_execute"] is False
    assert plan["can_register_formal_result"] is True
    assert plan["writes_result_index"] is True
    assert "b25_10_deseq2_ui_activation_preflight_only" in plan["blockers"]
    assert "b25_11_deseq2_ui_activation_required" in plan["blockers"]
    assert "deseq2_rscript_execution_adapter_not_implemented" not in plan["blockers"]


def test_deseq2_dry_run_acceptance_validates_candidate_index_without_writing(tmp_path: Path) -> None:
    manifest = build_r_deseq2_parameter_manifest(
        _deg_ready("count", "raw_count_matrix"),
        multi_factor_preflight=_preflight(),
        dependency_snapshot=_dependency_snapshot(),
    )
    gate = build_r_deseq2_dry_run_acceptance_gate(
        parameter_manifest=manifest,
        dependency_snapshot=_dependency_snapshot(),
        output_rows=_deseq2_output_rows(),
        count_fixture=_count_fixture(),
    )

    assert gate["status"] == "planned_not_enabled"
    assert gate["dry_run_validation_status"] == "passed"
    assert gate["formal_execution_enabled"] is False
    assert gate["can_register_formal_result"] is False
    assert gate["writes_result_index"] is False
    assert gate["count_fixture_gate"]["status"] == "passed"
    assert gate["output_schema_gate"]["status"] == "passed"
    assert gate["result_registration_gate"]["status"] == "passed"
    assert gate["result_index_gate"]["status"] == "passed"
    assert gate["candidate_result_index_entry"]["result_semantics"] == "formal_computed_result"
    assert gate["candidate_result_index_entry"]["report_ready_eligible"] is False
    assert "b25_8_deseq2_dry_run_only_no_result_index_write" in gate["blockers"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_deseq2_dry_run_acceptance_blocks_bad_output_and_fixture() -> None:
    manifest = build_r_deseq2_parameter_manifest(
        _deg_ready("count", "raw_count_matrix"),
        multi_factor_preflight=_preflight(),
        dependency_snapshot=_dependency_snapshot(),
    )
    gate = build_r_deseq2_dry_run_acceptance_gate(
        parameter_manifest=manifest,
        dependency_snapshot=_dependency_snapshot(),
        output_rows=[{"feature_id": "ENSG000001", "baseMean": 20}],
        count_fixture={"sample_ids": ["case_1"], "rows": [{"feature_id": "ENSG000001", "case_1": 1.5}]},
    )

    assert gate["dry_run_validation_status"] == "blocked"
    assert "missing_output_column:log2FoldChange" in gate["blockers"]
    assert "r_deseq2_count_fixture_requires_at_least_four_samples" in gate["blockers"]
    assert "count_fixture_row_0:non_integer_count:case_1" in gate["blockers"]


def test_deseq2_count_fixture_validator_requires_integer_counts() -> None:
    gate = validate_r_deseq2_count_fixture(_count_fixture())
    blocked = validate_r_deseq2_count_fixture({"sample_ids": ["s1", "s2", "s3", "s4"], "rows": [{"feature_id": "g1", "s1": -1, "s2": 1, "s3": 1, "s4": 1}]})

    assert gate["status"] == "passed"
    assert blocked["status"] == "blocked"
    assert "count_fixture_row_0:non_integer_count:s1" in blocked["blockers"]


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


def _count_fixture() -> dict[str, object]:
    return {
        "sample_ids": ["case_1", "case_2", "control_1", "control_2"],
        "rows": [
            {"feature_id": "ENSG000001", "gene_symbol": "GENE1", "case_1": 120, "case_2": 115, "control_1": 24, "control_2": 31},
            {"feature_id": "ENSG000002", "gene_symbol": "GENE2", "case_1": 20, "case_2": 23, "control_1": 80, "control_2": 77},
        ],
    }


def _deseq2_output_rows() -> list[dict[str, object]]:
    return [
        {
            "feature_id": "ENSG000001",
            "gene_symbol": "GENE1",
            "baseMean": 72.5,
            "log2FoldChange": 2.1,
            "lfcSE": 0.4,
            "stat": 5.25,
            "pvalue": 0.001,
            "padj": 0.01,
        },
        {
            "feature_id": "ENSG000002",
            "gene_symbol": "GENE2",
            "baseMean": 50.0,
            "log2FoldChange": -1.8,
            "lfcSE": 0.5,
            "stat": -3.6,
            "pvalue": 0.004,
            "padj": 0.02,
        },
    ]
