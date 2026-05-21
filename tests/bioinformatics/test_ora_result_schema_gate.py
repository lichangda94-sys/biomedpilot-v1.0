from __future__ import annotations

from datetime import datetime, timezone

from app.bioinformatics.enrichment.result_schema import build_ora_result_schema_gate, validate_ora_result_index_entry, validate_ora_result_table_row


def test_ora_result_schema_gate_passes_for_future_valid_bundle_shape() -> None:
    entry = _ora_entry()

    validation = validate_ora_result_index_entry(entry)

    assert validation["status"] == "passed"
    assert validation["blockers"] == []


def test_ora_result_schema_blocks_missing_required_fields_and_report_ready() -> None:
    entry = _ora_entry()
    entry.pop("ora_input_id")
    entry.pop("input_package_id")
    entry["report_ready_eligible"] = True

    validation = validate_ora_result_index_entry(entry)

    assert "ora_result_missing_input_package_or_ora_input_id" in validation["blockers"]
    assert "ora_result_must_not_be_report_ready_in_b10_1" in validation["blockers"]


def test_non_deg_semantics_are_not_upgraded_to_ora_formal_result() -> None:
    entry = _ora_entry()
    entry["result_semantics"] = "testing_level"

    validation = validate_ora_result_index_entry(entry)

    assert "ora_result_semantics_not_allowed:testing_level" in validation["blockers"]


def test_required_ora_table_columns_are_validated() -> None:
    row = {
        "term_id": "T1",
        "term_name": "Term 1",
        "gene_set_size": "10",
        "overlap_count": "2",
        "overlap_genes": "TP53;BRCA1",
        "background_size": "2000",
        "selected_gene_count": "25",
        "p_value": "0.01",
        "adjusted_p_value": "0.03",
        "enrichment_ratio": "2.5",
        "source_gene_list": "up_down",
        "warnings": "",
    }
    assert validate_ora_result_table_row(row)["status"] == "passed"
    row.pop("adjusted_p_value")
    assert "missing_column:adjusted_p_value" in validate_ora_result_table_row(row)["blockers"]


def test_schema_gate_remains_blocked_when_parameter_gate_fails() -> None:
    gate = build_ora_result_schema_gate(parameter_manifest={"status": "blocked", "blockers": ["ora_selected_gene_list_empty"]})

    assert gate["status"] == "blocked"
    assert "ora_parameter_gate_not_passed" in gate["blockers"]
    assert gate["report_ready_eligible"] is False


def _ora_entry() -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "result_id": "ora-1",
        "task_run_id": "ora-run-1",
        "task_type": "ora_enrichment",
        "result_semantics": "formal_computed_result",
        "input_package_id": "ora-input-1",
        "ora_input_id": "ora-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
        "source_deg_result_id": "deg-1",
        "source_result_semantics": "formal_computed_result",
        "gene_set_resource_id": "sets",
        "parameters_manifest": {"status": "passed"},
        "engine_name": "future_ora_engine",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": "passed"},
        "output_artifacts": [{"artifact_type": "ora_result_table", "path": "results/tables/ora.tsv"}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [],
        "failure_reason": "",
        "created_at": now,
        "updated_at": now,
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }
