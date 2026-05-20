from __future__ import annotations

from app.bioinformatics.deg_engine import build_deg_parameter_manifest, validate_deg_parameter_manifest


def test_deg_parameter_gate_builds_required_manifest_fields() -> None:
    manifest = build_deg_parameter_manifest(
        _deg_ready(value_type="count"),
        case_samples=["case1", "case2"],
        control_samples=["ctrl1", "ctrl2"],
        method="welch_t_test",
        dependency_snapshot={"status": "passed", "engine_candidate": "python_scipy_statsmodels", "blockers": []},
    )

    assert manifest["status"] == "passed"
    for field_name in (
        "schema_version",
        "created_at",
        "input_package_id",
        "deg_ready_package_id",
        "comparison_id",
        "case_group",
        "control_group",
        "case_samples",
        "control_samples",
        "group_design_source",
        "method",
        "method_family",
        "value_type",
        "value_type_policy",
        "gene_id_type",
        "gene_mapping_policy",
        "sample_alignment_policy",
        "log2fc_threshold",
        "p_value_threshold",
        "fdr_threshold",
        "fdr_policy",
        "pseudocount",
        "pseudocount_policy",
        "minimum_group_size",
        "missing_value_policy",
        "multiple_testing_policy",
        "engine_candidate",
        "dependency_snapshot",
        "warnings",
        "blockers",
    ):
        assert field_name in manifest
    assert manifest["semantic_boundary"] == "formal_deg_parameter_gate_only_not_execution"


def test_deg_parameter_gate_blocks_missing_same_groups_samples_and_dependency() -> None:
    manifest = build_deg_parameter_manifest(
        _deg_ready(value_type="count"),
        case_group="tumor",
        control_group="tumor",
        case_samples=[],
        control_samples=[],
        method="welch_t_test",
        dependency_snapshot={"status": "blocked", "blockers": ["missing_python_package:scipy"]},
    )

    assert manifest["status"] == "blocked"
    assert "same_case_control_group" in manifest["blockers"]
    assert "missing_case_samples" in manifest["blockers"]
    assert "missing_control_samples" in manifest["blockers"]
    assert "dependency_snapshot_not_passed" in manifest["blockers"]
    assert "missing_python_package:scipy" in manifest["blockers"]


def test_deg_parameter_gate_blocks_count_model_backend_in_controlled_mvp() -> None:
    manifest = build_deg_parameter_manifest(
        _deg_ready(value_type="count"),
        case_samples=["case1"],
        control_samples=["ctrl1"],
        method="count_model",
        dependency_snapshot={"status": "passed", "blockers": []},
    )

    assert manifest["status"] == "blocked"
    assert "count_model_backend_not_activated_in_b9_2_controlled_mvp" in manifest["blockers"]


def test_deg_parameter_gate_blocks_value_type_method_mapping_threshold_and_fdr_errors() -> None:
    manifest = build_deg_parameter_manifest(
        _deg_ready(value_type="TPM", gene_mapping={"status": "blocked", "requires_mapping": True}),
        case_samples=["case1"],
        control_samples=["ctrl1"],
        method="count_model",
        fdr_policy="",
        pseudocount=-1,
        p_value_threshold=1.5,
        fdr_threshold=-0.1,
        dependency_snapshot={"status": "passed", "blockers": []},
    )

    assert manifest["status"] == "blocked"
    assert "count_model_requested_for_display_value_type" in manifest["blockers"]
    assert "probe_or_id_ref_mapping_missing" in manifest["blockers"]
    assert "invalid_pseudocount" in manifest["blockers"]
    assert "missing_fdr_policy" in manifest["blockers"]
    assert "invalid_threshold:p_value_threshold" in manifest["blockers"]
    assert "invalid_threshold:fdr_threshold" in manifest["blockers"]


def test_deg_parameter_gate_blocks_unknown_value_type_and_sample_mismatch() -> None:
    manifest = {
        "schema_version": "biomedpilot.deg_parameter_gate.v1",
        "created_at": "now",
        "input_package_id": "pkg",
        "deg_ready_package_id": "ready",
        "comparison_id": "case_vs_control",
        "case_group": "case",
        "control_group": "control",
        "case_samples": ["S1"],
        "control_samples": ["S2"],
        "group_design_source": "group.json",
        "method": "welch_t_test",
        "method_family": "display_value_statistical_test",
        "value_type": "unknown",
        "value_type_policy": "blocked_unknown_or_incompatible_value_type",
        "gene_id_type": "symbol",
        "gene_mapping_policy": "passed",
        "sample_alignment_policy": "blocked_mismatch",
        "log2fc_threshold": 1.0,
        "p_value_threshold": 0.05,
        "fdr_threshold": 0.05,
        "fdr_policy": "benjamini_hochberg",
        "pseudocount": 1e-9,
        "pseudocount_policy": "required_non_negative_for_log2fc_ratio",
        "minimum_group_size": 1,
        "missing_value_policy": "omit_missing_values_per_feature",
        "multiple_testing_policy": "benjamini_hochberg",
        "engine_candidate": "python_scipy_statsmodels",
        "dependency_snapshot": {"status": "passed"},
        "warnings": [],
        "blockers": [],
    }

    validation = validate_deg_parameter_manifest(manifest)

    assert "unknown_value_type" in validation["blockers"]
    assert "sample_group_mismatch" in validation["blockers"]


def _deg_ready(*, value_type: str, gene_mapping: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "deg_ready_package_id": "deg-ready-1",
        "source_input_package_id": "pkg-1",
        "group_design_asset": {"path": "group.json"},
        "value_type": value_type,
        "gene_id_type": "ID_REF" if gene_mapping else "symbol",
        "sample_alignment_status": {"status": "passed"},
        "gene_mapping_status": gene_mapping or {"status": "passed", "requires_mapping": False},
        "warnings": [],
        "blockers": [],
    }
