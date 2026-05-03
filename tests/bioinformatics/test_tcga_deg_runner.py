from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from app.bioinformatics.tcga.deg_runner import run_tcga_deg_analysis
from app.bioinformatics.tcga.prepared_package import prepare_tcga_local_package


def _read_csv(path: str | Path):
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _scipy_available() -> bool:
    try:
        import scipy  # noqa: F401
    except Exception:
        return False
    return True


def _write_clinical(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "bcr_patient_barcode,days_to_death,days_to_last_follow_up,vital_status,age_at_diagnosis,gender,ajcc_pathologic_stage",
                "TCGA-AB-1234,100,,Dead,21915,Female,Stage II",
                "TCGA-CD-5678,,200,Alive,50,Male,Stage I",
            ]
        ),
        encoding="utf-8",
    )


def _prepare_deg_fixture(tmp_path, expression_text: str, batch_id: str = "batch-deg"):
    expression_path = tmp_path / f"{batch_id}_expression.csv"
    clinical_path = tmp_path / f"{batch_id}_clinical.csv"
    expression_path.write_text(expression_text, encoding="utf-8")
    _write_clinical(clinical_path)
    return prepare_tcga_local_package(
        expression_path,
        clinical_path,
        tmp_path / "prepared",
        "TCGA-THCA",
        batch_id,
        normalization="TPM",
    )


def test_run_tcga_deg_analysis_writes_results_and_summary(tmp_path) -> None:
    summary = _prepare_deg_fixture(
        tmp_path,
        "\n".join(
            [
                "gene_id,TCGA-AB-1234-01A,TCGA-CD-5678-01A,TCGA-AB-1234-11A",
                "UP,8.0,10.0,2.0",
                "DOWN,1.0,3.0,8.0",
            ]
        ),
    )

    deg_summary = run_tcga_deg_analysis(summary["manifest_path"], output_dir=tmp_path / "analysis_out")
    rows = _read_csv(deg_summary["result_path"])
    summary_payload = json.loads(Path(deg_summary["summary_path"]).read_text(encoding="utf-8"))

    assert Path(deg_summary["result_path"]).exists()
    assert Path(deg_summary["summary_path"]).exists()
    assert rows[0].keys() >= {
        "gene_id",
        "tumor_mean",
        "normal_mean",
        "log2_fold_change",
        "mean_difference",
        "tumor_sample_count",
        "normal_sample_count",
        "p_value",
    }
    up_row = next(row for row in rows if row["gene_id"] == "UP")
    assert up_row["tumor_sample_count"] == "2"
    assert up_row["normal_sample_count"] == "1"
    assert float(up_row["tumor_mean"]) == 9.0
    assert float(up_row["normal_mean"]) == 2.0
    assert float(up_row["log2_fold_change"]) > 0
    assert float(up_row["mean_difference"]) == 7.0
    assert deg_summary["project_id"] == "TCGA-THCA"
    assert deg_summary["batch_id"] == "batch-deg"
    assert deg_summary["gene_count_tested"] == 2
    assert deg_summary["tumor_sample_count"] == 2
    assert deg_summary["normal_sample_count"] == 1
    assert summary_payload == deg_summary


def test_p_value_field_follows_optional_scipy_availability(tmp_path) -> None:
    summary = _prepare_deg_fixture(
        tmp_path,
        "\n".join(
            [
                "gene_id,TCGA-AB-1234-01A,TCGA-CD-5678-01A,TCGA-AB-1234-11A,TCGA-ZZ-9999-11A",
                "GENE1,8.0,10.0,2.0,3.0",
            ]
        ),
        batch_id="batch-pvalue",
    )

    deg_summary = run_tcga_deg_analysis(summary["manifest_path"], output_dir=tmp_path / "analysis_out")
    rows = _read_csv(deg_summary["result_path"])

    if _scipy_available():
        assert rows[0]["p_value"] != ""
    else:
        assert rows[0]["p_value"] == ""
        assert "statistical_test_unavailable" in deg_summary["warnings"]


def test_missing_normal_samples_warns_and_does_not_crash(tmp_path) -> None:
    summary = _prepare_deg_fixture(
        tmp_path,
        "\n".join(
            [
                "gene_id,TCGA-AB-1234-01A",
                "GENE1,8.0",
            ]
        ),
        batch_id="batch-no-normal",
    )

    deg_summary = run_tcga_deg_analysis(summary["manifest_path"], output_dir=tmp_path / "analysis_out")
    rows = _read_csv(deg_summary["result_path"])

    assert rows == []
    assert "no_normal_samples" in deg_summary["warnings"]
    assert any(warning.startswith("gene_skipped_insufficient_samples:GENE1") for warning in deg_summary["warnings"])


def test_non_numeric_expression_values_are_missing_not_crashing(tmp_path) -> None:
    summary = _prepare_deg_fixture(
        tmp_path,
        "\n".join(
            [
                "gene_id,TCGA-AB-1234-01A,TCGA-CD-5678-01A,TCGA-AB-1234-11A",
                "GENE1,bad,10.0,2.0",
                "GENE2,bad,also_bad,2.0",
            ]
        ),
        batch_id="batch-nonnumeric",
    )

    deg_summary = run_tcga_deg_analysis(summary["manifest_path"], output_dir=tmp_path / "analysis_out")
    rows = _read_csv(deg_summary["result_path"])

    assert [row["gene_id"] for row in rows] == ["GENE1"]
    assert float(rows[0]["tumor_mean"]) == 10.0
    assert math.isclose(float(rows[0]["log2_fold_change"]), math.log2((10.0 + 1e-9) / (2.0 + 1e-9)))
    assert any(warning.startswith("gene_skipped_insufficient_samples:GENE2") for warning in deg_summary["warnings"])


def test_min_samples_per_group_can_skip_underpowered_genes(tmp_path) -> None:
    summary = _prepare_deg_fixture(
        tmp_path,
        "\n".join(
            [
                "gene_id,TCGA-AB-1234-01A,TCGA-CD-5678-01A,TCGA-AB-1234-11A",
                "GENE1,8.0,10.0,2.0",
            ]
        ),
        batch_id="batch-min-samples",
    )

    deg_summary = run_tcga_deg_analysis(
        summary["manifest_path"],
        output_dir=tmp_path / "analysis_out",
        min_samples_per_group=2,
    )

    assert _read_csv(deg_summary["result_path"]) == []
    assert any(warning.startswith("gene_skipped_insufficient_samples:GENE1") for warning in deg_summary["warnings"])

