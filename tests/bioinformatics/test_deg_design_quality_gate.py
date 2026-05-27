from __future__ import annotations

from app.bioinformatics.deg_engine import build_deg_design_quality_gate


def test_design_quality_passes_simple_two_group_design_with_warning() -> None:
    gate = build_deg_design_quality_gate(_ready_package())

    assert gate["status"] == "passed"
    assert gate["degrees_of_freedom"] == 2
    assert "batch_covariate_manifest_missing" in gate["warnings"]


def test_design_quality_blocks_group_batch_full_confounding() -> None:
    design = {"batch_assignments": {"batch": {"S1": "B1", "S2": "B1", "S3": "B2", "S4": "B2"}}}

    gate = build_deg_design_quality_gate(_ready_package(), design_manifest=design)

    assert gate["status"] == "blocked"
    assert "group_covariate_fully_confounded:batch" in gate["blockers"]


def test_design_quality_blocks_single_value_covariate_and_rank_deficiency() -> None:
    design = {
        "covariates": {"age_group": {"S1": "adult", "S2": "adult", "S3": "adult", "S4": "adult"}},
        "rank_deficient": True,
        "contrast_estimable": False,
    }

    gate = build_deg_design_quality_gate(_ready_package(), design_manifest=design)

    assert "covariate_single_value:age_group" in gate["blockers"]
    assert "design_matrix_rank_deficient" in gate["blockers"]
    assert "contrast_not_estimable" in gate["blockers"]


def test_design_quality_blocks_insufficient_degrees_of_freedom() -> None:
    design = {
        "covariates": {
            "age": {"S1": "50", "S2": "60", "S3": "70", "S4": "80"},
            "sex": {"S1": "F", "S2": "M", "S3": "F", "S4": "M"},
        },
        "batch_assignments": {"site": {"S1": "A", "S2": "B", "S3": "A", "S4": "B"}},
    }

    gate = build_deg_design_quality_gate(_ready_package(), design_manifest=design)

    assert "insufficient_degrees_of_freedom" in gate["blockers"]


def _ready_package() -> dict[str, object]:
    return {
        "source_input_package_id": "pkg-1",
        "deg_ready_package_id": "ready-1",
        "sample_alignment_status": {
            "status": "passed",
            "group_counts": {"case": 2, "control": 2},
            "sample_group_assignments": {"S1": "case", "S2": "case", "S3": "control", "S4": "control"},
        },
        "blockers": [],
        "warnings": [],
    }
