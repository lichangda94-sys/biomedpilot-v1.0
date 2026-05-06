from __future__ import annotations

import csv
import json
from pathlib import Path

from app.bioinformatics.services.enrichment_runner import run_over_representation_enrichment


def test_over_representation_enrichment_runs_against_user_gmt(tmp_path: Path) -> None:
    deg = tmp_path / "geo_differential_expression_results.csv"
    deg.write_text(
        "\n".join(
            [
                "gene_id,log2_fold_change,adjusted_p_value",
                "TP53,2.1,0.001",
                "EGFR,1.5,0.01",
                "GAPDH,0.1,0.8",
                "ACTB,0.2,0.9",
                "CDKN1A,1.8,0.02",
            ]
        ),
        encoding="utf-8",
    )
    gmt = tmp_path / "toy.gmt"
    gmt.write_text(
        "DNA_DAMAGE\ttoy\tTP53\tCDKN1A\tEGFR\nHOUSEKEEPING\ttoy\tGAPDH\tACTB\n",
        encoding="utf-8",
    )

    summary = run_over_representation_enrichment(deg, gmt, output_dir=tmp_path / "enrichment", dataset_id="GSETEST")

    assert summary["enrichment_executed"] is True
    assert summary["network_used"] is False
    assert summary["significant_gene_count"] == 3
    rows = list(csv.DictReader(Path(str(summary["result_path"])).open(encoding="utf-8")))
    assert rows[0]["term_name"] == "DNA_DAMAGE"
    assert rows[0]["overlap_count"] == "3"
    payload = json.loads(Path(str(summary["summary_path"])).read_text(encoding="utf-8"))
    assert payload["database_download_executed"] is False
