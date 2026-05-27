from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_engine import (
    build_multifactor_deg_parameter_manifest,
    load_multifactor_deg_parameter_confirmation,
    save_multifactor_deg_parameter_confirmation,
    validate_multifactor_deg_parameter_confirmation,
)


def test_multifactor_parameter_manifest_records_design_method_and_dependency() -> None:
    manifest = build_multifactor_deg_parameter_manifest(_ready(), design_manifest=_design(), method="limma", dependency_snapshot=_dependency())

    assert manifest["status"] == "passed"
    assert manifest["design_formula"] == "~ group + batch"
    assert manifest["contrast"]["contrast_id"] == "case_vs_control"
    assert manifest["batch_variables"] == ["batch"]
    assert manifest["backend_method"] == "limma"
    assert manifest["value_type_policy"].startswith("passed_limma")


def test_multifactor_confirmation_save_load_and_validate(tmp_path: Path) -> None:
    confirmation = save_multifactor_deg_parameter_confirmation(tmp_path, deg_ready_package=_ready(), design_manifest=_design(), method="limma", dependency_snapshot=_dependency())
    loaded = load_multifactor_deg_parameter_confirmation(tmp_path)
    gate = validate_multifactor_deg_parameter_confirmation(loaded, parameter_manifest=confirmation["parameter_manifest"], dependency_snapshot=_dependency())

    assert confirmation["status"] == "confirmed"
    assert loaded["schema_version"] == "biomedpilot.multifactor_deg_parameter_confirmation.v1"
    assert loaded["output_plan"]["result_table_path"].startswith("results/tables/multifactor-deg-limma-")
    assert gate["status"] == "passed"


def test_multifactor_confirmation_blocks_count_model_for_tpm(tmp_path: Path) -> None:
    ready = _ready(value_type="TPM")
    confirmation = save_multifactor_deg_parameter_confirmation(tmp_path, deg_ready_package=ready, design_manifest=_design(), method="DESeq2", dependency_snapshot=_dependency())

    assert confirmation["status"] == "blocked"
    assert "blocked_count_model_requires_raw_counts" in confirmation["parameter_manifest"]["value_type_policy"]


def _ready(value_type: str = "count") -> dict[str, object]:
    return {"source_input_package_id": "pkg-1", "deg_ready_package_id": "ready-1", "value_type": value_type}


def _design() -> dict[str, object]:
    return {
        "design_formula": "~ group + batch",
        "contrast": {"contrast_id": "case_vs_control", "case_group": "case", "control_group": "control"},
        "batch_assignments": {"batch": {"S1": "B1", "S2": "B2", "S3": "B1", "S4": "B2"}},
        "design_rank": 3,
        "residual_degrees_of_freedom": 3,
        "contrast_estimability": "estimable",
    }


def _dependency() -> dict[str, object]:
    return {"status": "passed", "r_backend": {"packages": {"R": {"version": "4.4.2"}, "limma": {"version": "3.62.2"}, "DESeq2": {"version": "1.46.0"}, "edgeR": {"version": "4.4.2"}}}}
