from __future__ import annotations

import csv
import json
from pathlib import Path

from app.analysis_runtime import build_standard_analysis_package_catalog, validate_standard_result_package
from app.bioinformatics.services.correlation_runner import run_expression_correlation


def test_expression_correlation_runs_against_target_gene(tmp_path: Path) -> None:
    expression = tmp_path / "expression.tsv"
    expression.write_text(
        "\n".join(
            [
                "gene\tS1\tS2\tS3\tS4",
                "TP53\t1\t2\t3\t4",
                "EGFR\t2\t4\t6\t8",
                "GAPDH\t4\t3\t2\t1",
                "ACTB\t1\t1\t1\t1",
            ]
        ),
        encoding="utf-8",
    )

    summary = run_expression_correlation(expression, target_gene="TP53", output_dir=tmp_path / "correlation", dataset_id="GSETEST")

    assert summary["correlation_executed"] is True
    assert summary["network_used"] is False
    assert summary["gene_count_tested"] == 2
    rows = list(csv.DictReader(Path(str(summary["result_path"])).open(encoding="utf-8")))
    assert rows[0]["gene_id"] in {"EGFR", "GAPDH"}
    assert abs(float(rows[0]["pearson_r"])) == 1.0
    payload = json.loads(Path(str(summary["summary_path"])).read_text(encoding="utf-8"))
    assert payload["target_gene"] == "TP53"
    standard_package_dir = Path(str(summary["standard_result_package_dir"]))
    assert standard_package_dir.is_dir()
    validation = validate_standard_result_package(
        standard_package_dir,
        expected_module_id="correlation",
        expected_task_id=str(summary["task_run_id"]),
        expected_mode="lite",
    )
    assert validation["status"] == "passed"
    invocation = json.loads((standard_package_dir / "logs" / "worker_invocation.json").read_text(encoding="utf-8"))
    assert invocation["worker_backend"] == "legacy_service_adapter"
    assert invocation["invocation_status"] == "sidecar_recorded"
    assert invocation["worker_boundary"]["task_system_invocation"] == "legacy_service_adapter_direct_call"
    index = json.loads((tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8"))
    entry = next(item for item in index["results"] if item["result_id"] == summary["result_id"])
    assert entry["result_semantics"] == "testing_level"
    assert entry["report_ready_eligible"] is False
    assert any(item["artifact_type"] == "analysis_worker_invocation_manifest" for item in entry["log_artifacts"])
    assert any(item["artifact_type"] == "standard_result_package" for item in entry["output_artifacts"])
    catalog = build_standard_analysis_package_catalog(tmp_path)
    row = next(item for item in catalog["rows"] if item["result_id"] == summary["result_id"])
    assert row["module_id"] == "correlation"
    assert row["mode"] == "lite"
    assert row["result_semantics"] == "testing_level"
    assert row["worker_boundary_type"] == "legacy_service_adapter_sidecar"
    assert row["worker_backend"] == "legacy_service_adapter"
    assert row["worker_invocation_status"] == "sidecar_recorded"
    assert row["artifact_counts"]["tables"] == 1
    assert row["artifact_counts"]["reports"] == 1
    assert row["artifact_manifest"]["tables"][0]["exists"] is True
    assert "clinical_conclusion_not_generated" in row["warnings"]


def test_expression_correlation_reads_geo_series_matrix_table_block(tmp_path: Path) -> None:
    expression = tmp_path / "GSE_series_matrix.txt"
    expression.write_text(
        "\n".join(
            [
                "!Series_title = demo",
                "!series_matrix_table_begin",
                "ID_REF\tGSM1\tGSM2\tGSM3\tGSM4",
                "TP53\t1\t2\t3\t4",
                "EGFR\t2\t4\t6\t8",
                "!series_matrix_table_end",
            ]
        ),
        encoding="utf-8",
    )

    summary = run_expression_correlation(expression, target_gene="TP53", output_dir=tmp_path / "correlation")

    assert summary["gene_count_tested"] == 1
    rows = list(csv.DictReader(Path(str(summary["result_path"])).open(encoding="utf-8")))
    assert rows[0]["gene_id"] == "EGFR"
