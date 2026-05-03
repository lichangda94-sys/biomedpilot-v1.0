from __future__ import annotations

from pathlib import Path

from app.bioinformatics.tcga.analysis_inputs import (
    build_tcga_correlation_input,
    build_tcga_deg_input,
    build_tcga_survival_input,
)
from app.bioinformatics.tcga.prepared_package import prepare_tcga_local_package


def _write_expression(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "gene_id,TCGA-AB-1234-01A,TCGA-AB-1234-06A,TCGA-AB-1234-11A,TCGA-CD-5678-01A",
                "ENSG000001234.5,1.0,3.0,2.0,9.0",
                "TP53,5.0,7.0,6.0,8.0",
            ]
        ),
        encoding="utf-8",
    )


def _write_clinical(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "bcr_patient_barcode,days_to_death,days_to_last_follow_up,vital_status,age_at_diagnosis,gender,ajcc_pathologic_stage",
                "TCGA-AB-1234,100,,Dead,21915,Female,Stage II",
                "TCGA-CD-5678,,,Alive,50,Male,Stage I",
            ]
        ),
        encoding="utf-8",
    )


def _prepare_package(tmp_path):
    expression_path = tmp_path / "expression.csv"
    clinical_path = tmp_path / "clinical.csv"
    _write_expression(expression_path)
    _write_clinical(clinical_path)
    return prepare_tcga_local_package(
        expression_path,
        clinical_path,
        tmp_path / "out",
        "TCGA-THCA",
        "batch-analysis",
        normalization="TPM",
    )


def test_deg_input_identifies_tumor_normal_and_pairs(tmp_path) -> None:
    summary = _prepare_package(tmp_path)

    deg_input = build_tcga_deg_input(summary["manifest_path"], paired=True)

    assert deg_input["sample_count"] == 4
    assert deg_input["tumor_count"] == 3
    assert deg_input["normal_count"] == 1
    assert deg_input["tumor_samples"] == [
        "TCGA-AB-1234-01A",
        "TCGA-AB-1234-06A",
        "TCGA-CD-5678-01A",
    ]
    assert deg_input["normal_samples"] == ["TCGA-AB-1234-11A"]
    assert deg_input["paired_patients"] == ["TCGA-AB-1234"]
    assert deg_input["paired_samples"] == [
        {
            "patient_barcode": "TCGA-AB-1234",
            "tumor_sample": "TCGA-AB-1234-01A",
            "normal_sample": "TCGA-AB-1234-11A",
        }
    ]
    assert {"barcode": "TCGA-AB-1234-11A", "patient_barcode": "TCGA-AB-1234", "group": "normal"} in deg_input[
        "sample_groups"
    ]


def test_deg_input_warns_when_normal_group_missing(tmp_path) -> None:
    expression_path = tmp_path / "expression_tumor_only.csv"
    clinical_path = tmp_path / "clinical.csv"
    expression_path.write_text(
        "\n".join(["gene_id,TCGA-AB-1234-01A", "TP53,1.0"]),
        encoding="utf-8",
    )
    _write_clinical(clinical_path)
    summary = prepare_tcga_local_package(expression_path, clinical_path, tmp_path / "out", "TCGA-THCA", "batch-no-normal")

    deg_input = build_tcga_deg_input(summary["manifest_path"], paired=True)

    assert deg_input["tumor_count"] == 1
    assert deg_input["normal_count"] == 0
    assert "no_normal_samples" in deg_input["warnings"]
    assert "no_paired_patients" in deg_input["warnings"]


def test_survival_input_builds_patient_table_with_gene_expression_first(tmp_path) -> None:
    summary = _prepare_package(tmp_path)

    survival_input = build_tcga_survival_input(summary["manifest_path"], gene_id="ENSG000001234")

    assert survival_input["available_patient_count"] == 1
    assert survival_input["matched_gene_id"] == "ENSG000001234"
    assert survival_input["survival_table"] == [
        {
            "patient_barcode": "TCGA-AB-1234",
            "os_time_days": "100",
            "os_event": "1",
            "gene_expression": "1.0",
        }
    ]
    assert survival_input["expression_by_patient"]["TCGA-AB-1234"] == "1.0"
    assert "TCGA-CD-5678" in survival_input["missing_survival_patients"]


def test_survival_input_mean_aggregation_handles_multiple_patient_samples(tmp_path) -> None:
    summary = _prepare_package(tmp_path)

    survival_input = build_tcga_survival_input(summary["manifest_path"], gene_id="ENSG000001234.5", aggregation="mean")

    assert survival_input["matched_gene_id"] == "ENSG000001234"
    assert survival_input["expression_by_patient"]["TCGA-AB-1234"] == "2.0"
    assert survival_input["survival_table"][0]["gene_expression"] == "2.0"


def test_survival_input_warns_when_gene_is_missing(tmp_path) -> None:
    summary = _prepare_package(tmp_path)

    survival_input = build_tcga_survival_input(summary["manifest_path"], gene_id="NOT_A_GENE")

    assert "gene_not_found:NOT_A_GENE" in survival_input["warnings"]
    assert "TCGA-AB-1234" in survival_input["missing_expression_patients"]


def test_correlation_input_matches_target_gene_case_insensitive_and_without_version(tmp_path) -> None:
    summary = _prepare_package(tmp_path)

    correlation_input = build_tcga_correlation_input(summary["manifest_path"], target_gene="ensg000001234.5")

    assert correlation_input["matched_gene_id"] == "ENSG000001234"
    assert correlation_input["sample_count"] == 4
    assert correlation_input["target_expression"]["TCGA-AB-1234-01A"] == "1.0"
    assert correlation_input["target_expression"]["TCGA-CD-5678-01A"] == "9.0"
    assert correlation_input["warnings"] == []


def test_correlation_input_warns_when_target_gene_missing(tmp_path) -> None:
    summary = _prepare_package(tmp_path)

    correlation_input = build_tcga_correlation_input(summary["manifest_path"], target_gene="MISSING")

    assert correlation_input["matched_gene_id"] == ""
    assert correlation_input["target_expression"] == {}
    assert "target_gene_not_found:MISSING" in correlation_input["warnings"]

