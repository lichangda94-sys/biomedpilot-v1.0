from __future__ import annotations

from app.bioinformatics.deg_engine import build_multifactor_deg_controlled_gate


def test_multifactor_gate_passes_readiness_but_keeps_execution_disabled() -> None:
    gate = build_multifactor_deg_controlled_gate(_ready(), design_manifest=_design(), dependency_snapshot=_dependency(), method_family="limma")

    assert gate["status"] == "passed"
    assert gate["formal_execution_enabled"] is False
    assert gate["activation_required"] == "future_multifactor_runtime_and_result_schema_activation_required"


def test_multifactor_gate_blocks_missing_formula_and_contrast() -> None:
    gate = build_multifactor_deg_controlled_gate(_ready(), design_manifest={}, dependency_snapshot=_dependency(), method_family="limma")

    assert "missing_multifactor_design_manifest" in gate["blockers"]
    assert "missing_design_formula" in gate["blockers"]
    assert "missing_contrast_manifest" in gate["blockers"]


def test_multifactor_gate_blocks_count_model_on_display_values_and_missing_backend() -> None:
    ready = _ready(value_type="TPM")
    dependency = _dependency(deseq2=False)

    gate = build_multifactor_deg_controlled_gate(ready, design_manifest=_design(), dependency_snapshot=dependency, method_family="DESeq2")

    assert "count_model_multifactor_requires_raw_counts" in gate["blockers"]
    assert "r_backend_package_missing:DESeq2" in gate["blockers"]


def test_multifactor_gate_blocks_confounded_design() -> None:
    design = _design()
    design["batch_assignments"] = {"batch": {"S1": "B1", "S2": "B1", "S3": "B2", "S4": "B2"}}

    gate = build_multifactor_deg_controlled_gate(_ready(), design_manifest=design, dependency_snapshot=_dependency(), method_family="limma")

    assert "group_covariate_fully_confounded:batch" in gate["blockers"]


def _ready(value_type: str = "count") -> dict[str, object]:
    return {
        "source_input_package_id": "pkg-1",
        "deg_ready_package_id": "ready-1",
        "value_type": value_type,
        "sample_alignment_status": {
            "status": "passed",
            "group_counts": {"case": 2, "control": 2},
            "sample_group_assignments": {"S1": "case", "S2": "case", "S3": "control", "S4": "control"},
        },
        "blockers": [],
        "warnings": [],
    }


def _design() -> dict[str, object]:
    return {
        "design_formula": "~ group + batch",
        "contrast": {"contrast_id": "case_vs_control", "case_group": "case", "control_group": "control"},
        "batch_assignments": {"batch": {"S1": "B1", "S2": "B2", "S3": "B1", "S4": "B2"}},
    }


def _dependency(*, deseq2: bool = True) -> dict[str, object]:
    return {
        "status": "passed",
        "blockers": [],
        "r_backend": {"packages": {"limma": {"available": True}, "DESeq2": {"available": deseq2}, "edgeR": {"available": True}}},
    }
