from __future__ import annotations

from app.bioinformatics.deg_engine import build_formal_deg_result_schema_gate, validate_formal_deg_result_index_entry


def test_formal_deg_result_schema_gate_accepts_complete_result_index_v2_entry() -> None:
    entry = _formal_entry()

    validation = validate_formal_deg_result_index_entry(entry)

    assert validation["status"] == "passed"


def test_formal_deg_result_schema_gate_blocks_missing_required_formal_fields() -> None:
    entry = _formal_entry()
    entry["input_package_id"] = ""
    entry["parameters_manifest"] = {}
    entry["dependency_snapshot"] = {}
    entry["engine_name"] = ""
    entry["output_artifacts"] = []
    entry["validation_status"] = "blocked"
    entry["blockers"] = ["upstream_blocker"]

    validation = validate_formal_deg_result_index_entry(entry)

    assert validation["status"] == "blocked"
    assert "missing_input_package_id" in validation["blockers"]
    assert "missing_parameters_manifest" in validation["blockers"]
    assert "missing_dependency_snapshot" in validation["blockers"]
    assert "missing_engine_or_version" in validation["blockers"]
    assert "missing_output_artifact" in validation["blockers"]
    assert "validation_status_failed_or_blocked" in validation["blockers"]
    assert "formal_result_has_blockers" in validation["blockers"]


def test_formal_deg_result_schema_gate_blocks_non_formal_semantics_marked_for_formal() -> None:
    entry = _formal_entry()
    entry["result_semantics"] = "testing_level"
    entry["canonical_result_semantics"] = "testing_level"

    validation = validate_formal_deg_result_index_entry(entry)

    assert validation["status"] == "blocked"
    assert "non_formal_result_marked_for_formal_deg_schema" in validation["blockers"]
    assert any(item.startswith("non_formal_semantics") for item in validation["blockers"])


def test_result_schema_gate_blocks_when_parameter_or_dependency_gate_not_passed() -> None:
    gate = build_formal_deg_result_schema_gate(
        parameter_manifest={"status": "blocked", "blockers": ["missing_fdr_policy"]},
        dependency_snapshot={"status": "blocked", "blockers": ["missing_python_package:statsmodels"]},
    )

    assert gate["status"] == "blocked"
    assert "missing_fdr_policy" in gate["blockers"]
    assert "missing_python_package:statsmodels" in gate["blockers"]
    assert "input_package_id" in gate["required_result_index_fields"]
    assert "adjusted_p_value" in gate["required_deg_table_columns"]


def _formal_entry() -> dict[str, object]:
    return {
        "result_id": "deg-formal-1",
        "task_run_id": "task-run-1",
        "task_type": "deg",
        "result_semantics": "formal_computed_result",
        "input_package_id": "pkg-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "repository_manifest.json",
        "parameters_manifest": {"method": "count_model"},
        "engine_name": "python_scipy_statsmodels_deg_mvp",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": "passed"},
        "output_artifacts": [{"artifact_type": "deg_table", "path": "results/deg.tsv"}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [],
        "failure_reason": "",
        "created_at": "now",
        "updated_at": "now",
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }
