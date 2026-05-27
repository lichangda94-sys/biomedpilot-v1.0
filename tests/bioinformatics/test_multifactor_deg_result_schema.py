from __future__ import annotations

from app.bioinformatics.deg_engine import (
    build_multifactor_deg_result_schema_gate,
    validate_multifactor_deg_result_bundle,
    validate_multifactor_deg_result_index_entry,
)
from app.bioinformatics.results.models import ResultIndexEntry


def test_multifactor_result_schema_gate_requires_design_and_contrast_provenance() -> None:
    gate = build_multifactor_deg_result_schema_gate(parameter_manifest={}, dependency_snapshot={"status": "passed"})

    assert gate["status"] == "blocked"
    assert "missing_multifactor_field:design_formula" in gate["blockers"]
    assert "missing_multifactor_field:backend_method" in gate["blockers"]


def test_multifactor_result_schema_gate_passes_complete_manifest() -> None:
    gate = build_multifactor_deg_result_schema_gate(parameter_manifest=_manifest(), dependency_snapshot={"status": "passed"})

    assert gate["status"] == "passed"
    assert "design_formula" in gate["required_multifactor_provenance_fields"]


def test_multifactor_result_bundle_validates_manifest_and_rows() -> None:
    bundle = {
        "result_semantics": "formal_computed_result",
        "engine_name": "limma",
        "engine_version": "3.62.2",
        "dependency_snapshot": {"status": "passed"},
        "parameters_manifest": _manifest(),
        "rows": [{"feature_id": "TP53"}],
    }

    validation = validate_multifactor_deg_result_bundle(bundle)

    assert validation["status"] == "passed"


def test_multifactor_result_index_entry_blocks_missing_provenance_and_report_ready() -> None:
    entry = ResultIndexEntry(
        result_id="mf",
        task_run_id="task",
        task_type="deg",
        result_semantics="formal_computed_result",
        input_package_id="pkg",
        source_dataset_id="dataset",
        source_repository_manifest="manifest",
        parameters_manifest={"backend_method": "limma"},
        engine_name="limma",
        engine_version="3.62.2",
        dependency_snapshot={"status": "passed"},
        output_artifacts=({"artifact_type": "deg_result_table", "path": "results/tables/mf.tsv"},),
        validation_status="passed",
        report_ready_eligible=True,
    ).to_dict()

    validation = validate_multifactor_deg_result_index_entry(entry)

    assert validation["status"] == "blocked"
    assert "missing_multifactor_field:design_formula" in validation["blockers"]
    assert "multifactor_deg_result_must_not_start_report_ready" in validation["blockers"]


def _manifest() -> dict[str, object]:
    return {
        "design_formula": "~ group + batch",
        "contrast": {"contrast_id": "case_vs_control", "case_group": "case", "control_group": "control"},
        "covariates": [],
        "batch_variables": ["batch"],
        "design_rank": 3,
        "residual_degrees_of_freedom": 3,
        "contrast_estimability": "estimable",
        "backend_method": "limma",
    }
