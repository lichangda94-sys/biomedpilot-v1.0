from __future__ import annotations

import csv
import json
from pathlib import Path

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
