from __future__ import annotations

from datetime import datetime, timezone

from app.bioinformatics.gsea import build_gsea_result_schema_gate, validate_gsea_result_index_entry, validate_gsea_result_table_row


def test_gsea_result_schema_gate_defines_future_result_contract() -> None:
    gate = build_gsea_result_schema_gate(parameter_manifest={"status": "passed", "blockers": []})

    assert gate["status"] == "passed"
    assert gate["execution_enabled"] is True
    assert gate["task_type"] == "gsea_preranked"
    assert "normalized_enrichment_score" in gate["required_gsea_result_table_columns"]
    assert gate["report_ready_eligible"] is False


def test_gsea_result_schema_gate_blocks_failed_parameter_manifest() -> None:
    gate = build_gsea_result_schema_gate(parameter_manifest={"status": "blocked", "blockers": ["gsea_parameter_random_seed_missing"]})
    assert "gsea_parameter_random_seed_missing" in gate["blockers"]


def test_validate_gsea_result_index_entry_accepts_complete_future_entry() -> None:
    validation = validate_gsea_result_index_entry(_entry())
    assert validation["status"] == "passed"


def test_validate_gsea_result_index_entry_blocks_non_gsea_and_report_ready() -> None:
    entry = _entry()
    entry["task_type"] = "ora_enrichment"
    entry["report_ready_eligible"] = True
    validation = validate_gsea_result_index_entry(entry)
    assert "gsea_result_task_type_must_be_gsea_preranked" in validation["blockers"]
    assert "gsea_result_must_not_be_report_ready_in_b11_2" in validation["blockers"]


def test_validate_gsea_result_table_row_checks_required_columns_and_numeric_fields() -> None:
    row = {
        "term_id": "T1",
        "term_name": "Term",
        "set_size": "bad",
        "overlap_size": "2",
        "enrichment_score": "0.5",
        "normalized_enrichment_score": "1.2",
        "p_value": "0.01",
        "adjusted_p_value": "0.02",
        "leading_edge_genes": "A;B",
        "rank_metric": "signed_log10_fdr_by_log2fc",
        "warnings": "",
    }
    validation = validate_gsea_result_table_row(row)
    assert "non_numeric:set_size" in validation["blockers"]


def _entry() -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "result_id": "gsea-1",
        "task_run_id": "gsea-run-1",
        "task_type": "gsea_preranked",
        "result_semantics": "formal_computed_result",
        "input_package_id": "gsea-input-1",
        "gsea_input_id": "gsea-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
        "source_deg_result_id": "deg-1",
        "source_result_semantics": "formal_computed_result",
        "gene_set_resource_id": "sets",
        "parameters_manifest": {"rank_metric": "signed_log10_fdr_by_log2fc"},
        "engine_name": "biomedpilot_gsea_preranked",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": "passed"},
        "output_artifacts": [{"artifact_type": "gsea_result_table", "path": "results/tables/gsea.tsv"}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [{"artifact_type": "gsea_task_run_log", "path": "analysis/gsea/run/task_run.json"}],
        "failure_reason": "",
        "created_at": now,
        "updated_at": now,
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }
