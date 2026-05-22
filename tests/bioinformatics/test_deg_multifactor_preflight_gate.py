from __future__ import annotations

from app.bioinformatics.deg_engine.multifactor_gate import (
    build_multifactor_deg_preflight_manifest,
    validate_multifactor_deg_preflight_manifest,
)


def test_multifactor_preflight_accepts_full_rank_limma_normalized_design() -> None:
    manifest = build_multifactor_deg_preflight_manifest(
        _deg_ready(value_type="TPM", asset_type="normalized_expression_matrix"),
        design_config=_design_config(),
        method="limma",
        dependency_snapshot={"status": "passed"},
    )

    assert manifest["status"] == "design_ready"
    assert manifest["method_family"] == "limma_normalized_expression"
    assert manifest["result_semantics"] == "preflight_only"
    assert manifest["formal_execution_enabled"] is False
    assert manifest["writes_result_index"] is False
    assert manifest["report_ready_eligible"] is False
    assert manifest["rank"] == manifest["column_count"]
    assert validate_multifactor_deg_preflight_manifest(manifest)["status"] == "passed"


def test_multifactor_preflight_blocks_non_full_rank_design() -> None:
    manifest = build_multifactor_deg_preflight_manifest(
        _deg_ready(value_type="TPM", asset_type="normalized_expression_matrix"),
        design_config=_design_config(confounded_batch=True),
        method="limma",
    )

    assert manifest["status"] == "blocked"
    assert "design_matrix_not_full_rank" in manifest["blockers"]
    assert manifest["result_semantics"] != "formal_computed_result"


def test_multifactor_preflight_blocks_insufficient_sample_count() -> None:
    manifest = build_multifactor_deg_preflight_manifest(
        _deg_ready(value_type="TPM", asset_type="normalized_expression_matrix"),
        design_config={
            "sample_table": [
                {"sample_id": "S1", "group": "case", "batch": "b1", "age": 50},
                {"sample_id": "S2", "group": "control", "batch": "b2", "age": 60},
            ],
            "primary_factor": "group",
            "case_group": "case",
            "control_group": "control",
            "covariates": [{"name": "batch", "variable_type": "categorical"}, {"name": "age", "variable_type": "continuous"}],
            "contrast": {"contrast_id": "case_vs_control", "factor": "group", "case_level": "case", "control_level": "control"},
        },
        method="limma",
    )

    assert manifest["status"] == "blocked"
    assert "sample_count_insufficient_for_multifactor_design" in manifest["blockers"]


def test_multifactor_preflight_blocks_tpm_for_deseq2_or_edger_count_models() -> None:
    for method in ("deseq2", "edgeR"):
        manifest = build_multifactor_deg_preflight_manifest(
            _deg_ready(value_type="FPKM", asset_type="normalized_expression_matrix"),
            design_config=_design_config(),
            method=method,
        )

        assert manifest["status"] == "blocked"
        assert "count_model_requested_for_display_value_type" in manifest["blockers"]
        assert "count_matrix_missing_for_deseq2_or_edger" in manifest["blockers"]


def test_multifactor_preflight_blocks_missing_count_matrix_for_count_model() -> None:
    manifest = build_multifactor_deg_preflight_manifest(
        _deg_ready(value_type="count", asset_type="normalized_expression_matrix"),
        design_config=_design_config(),
        method="deseq2",
    )

    assert manifest["status"] == "blocked"
    assert "count_matrix_missing_for_deseq2_or_edger" in manifest["blockers"]


def test_multifactor_preflight_distinguishes_limma_voom_from_limma_normalized_policy() -> None:
    voom = build_multifactor_deg_preflight_manifest(
        _deg_ready(value_type="count", asset_type="raw_count_matrix"),
        design_config=_design_config(),
        method="limma_voom",
    )
    limma = build_multifactor_deg_preflight_manifest(
        _deg_ready(value_type="count", asset_type="raw_count_matrix"),
        design_config=_design_config(),
        method="limma",
    )

    assert voom["method_family"] == "limma_voom_count_model"
    assert voom["status"] == "design_ready"
    assert limma["method_family"] == "limma_normalized_expression"
    assert "limma_normalized_expression_requires_normalized_or_log_values" in limma["blockers"]


def test_multifactor_preflight_never_validates_formal_result_semantics() -> None:
    manifest = build_multifactor_deg_preflight_manifest(
        _deg_ready(value_type="TPM", asset_type="normalized_expression_matrix"),
        design_config=_design_config(),
        method="limma",
    )
    manifest["result_semantics"] = "formal_computed_result"

    validation = validate_multifactor_deg_preflight_manifest(manifest)

    assert validation["status"] == "blocked"
    assert "multi_factor_preflight_must_not_use_formal_result_semantics" in validation["blockers"]


def _deg_ready(*, value_type: str, asset_type: str) -> dict[str, object]:
    return {
        "deg_ready_package_id": "deg-ready-test",
        "source_input_package_id": "input-test",
        "value_type": value_type,
        "gene_id_type": "symbol",
        "matrix_asset": {"asset_id": "expr", "asset_type": asset_type, "path": "/tmp/expression.tsv"},
        "sample_alignment_status": {"status": "passed"},
        "gene_mapping_status": {"status": "passed"},
        "blockers": [],
        "warnings": [],
    }


def _design_config(*, confounded_batch: bool = False) -> dict[str, object]:
    if confounded_batch:
        batches = ["b1", "b1", "b1", "b2", "b2", "b2"]
    else:
        batches = ["b1", "b1", "b2", "b1", "b2", "b2"]
    rows = [
        {"sample_id": "S1", "group": "case", "batch": batches[0], "age": 50},
        {"sample_id": "S2", "group": "case", "batch": batches[1], "age": 55},
        {"sample_id": "S3", "group": "case", "batch": batches[2], "age": 65},
        {"sample_id": "S4", "group": "control", "batch": batches[3], "age": 52},
        {"sample_id": "S5", "group": "control", "batch": batches[4], "age": 59},
        {"sample_id": "S6", "group": "control", "batch": batches[5], "age": 70},
    ]
    return {
        "schema_version": "biomedpilot.deg_multifactor_design_config.v1",
        "sample_table": rows,
        "primary_factor": "group",
        "case_group": "case",
        "control_group": "control",
        "covariates": [{"name": "batch", "variable_type": "categorical", "role": "batch"}, {"name": "age", "variable_type": "continuous"}],
        "contrast": {"contrast_id": "case_vs_control", "factor": "group", "case_level": "case", "control_level": "control"},
    }
