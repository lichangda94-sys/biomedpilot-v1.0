from __future__ import annotations

import csv
import json
from pathlib import Path

from app.bioinformatics.standard_assets.tcga_assets import (
    TCGA_CLINICAL_LINKAGE_SUMMARY,
    TCGA_CLINICAL_TABLE,
    TCGA_EXPRESSION_MATRIX,
    TCGA_PREPARE_MANIFEST,
    TCGA_SAMPLE_METADATA,
)
from app.bioinformatics.tcga.clinical_importer import import_tcga_clinical_table
from app.bioinformatics.tcga.expression_importer import import_tcga_expression_matrix


def _read_csv(path: str | Path):
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_clinical_csv_import_standardizes_survival_fields(tmp_path) -> None:
    input_path = tmp_path / "clinical.csv"
    input_path.write_text(
        "\n".join(
            [
                "bcr_patient_barcode,days_to_death,days_to_last_follow_up,vital_status,age_at_diagnosis,gender,ajcc_pathologic_stage",
                "TCGA-AB-1234,120,,Dead,21915,FEMALE,Stage II",
                "TCGA-CD-5678,,300,Alive,60,Male,Stage I",
            ]
        ),
        encoding="utf-8",
    )

    result = import_tcga_clinical_table(input_path, tmp_path / "out", "TCGA-THCA", "batch-1")
    rows = _read_csv(result["asset_paths"][TCGA_CLINICAL_TABLE])

    assert rows[0]["patient_barcode"] == "TCGA-AB-1234"
    assert rows[0]["os_time_days"] == "120"
    assert rows[0]["os_event"] == "1"
    assert rows[0]["gender"] == "female"
    assert rows[0]["stage"] == "Stage II"
    assert rows[0]["age_at_diagnosis"] == "21915"
    assert rows[0]["age_at_diagnosis_years"] == "60.00"
    assert rows[1]["patient_barcode"] == "TCGA-CD-5678"
    assert rows[1]["os_time_days"] == "300"
    assert rows[1]["os_event"] == "0"
    assert rows[1]["gender"] == "male"
    assert result["manifest"]["clinical_patient_count"] == 2


def test_clinical_tsv_import_derives_patient_from_sample_barcode(tmp_path) -> None:
    input_path = tmp_path / "clinical.tsv"
    input_path.write_text(
        "\n".join(
            [
                "tcga_barcode\tdays_to_death\tdays_to_last_follow_up\tvital_status\tage_at_diagnosis\tgender\tpathologic_stage",
                "TCGA-AB-1234-11A\t\t42\tLiving\t45\tF\tStage III",
            ]
        ),
        encoding="utf-8",
    )

    result = import_tcga_clinical_table(input_path, tmp_path / "out", "TCGA-THCA", "batch-2")
    rows = _read_csv(result["asset_paths"][TCGA_CLINICAL_TABLE])

    assert rows[0]["patient_barcode"] == "TCGA-AB-1234"
    assert rows[0]["os_time_days"] == "42"
    assert rows[0]["os_event"] == "0"
    assert rows[0]["gender"] == "female"
    assert rows[0]["stage"] == "Stage III"


def test_duplicate_patient_and_missing_os_time_are_warnings(tmp_path) -> None:
    input_path = tmp_path / "clinical_duplicates.csv"
    input_path.write_text(
        "\n".join(
            [
                "submitter_id,days_to_death,days_to_last_follow_up,vital_status,gender,tumor_stage",
                "TCGA-AB-1234,10,,Dead,Female,Stage I",
                "TCGA-AB-1234,20,,Dead,Female,Stage II",
                "TCGA-CD-5678,,,Alive,Male,Stage III",
            ]
        ),
        encoding="utf-8",
    )

    result = import_tcga_clinical_table(input_path, tmp_path / "out", "TCGA-THCA", "batch-3")
    rows = _read_csv(result["asset_paths"][TCGA_CLINICAL_TABLE])

    assert len(rows) == 2
    assert rows[0]["patient_barcode"] == "TCGA-AB-1234"
    assert rows[0]["os_time_days"] == "10"
    assert any(
        warning.startswith("duplicate_patient_barcode_rows_removed:1:TCGA-AB-1234")
        for warning in result["warnings"]
    )
    assert "missing_os_time:TCGA-CD-5678" in result["warnings"]


def test_vital_status_conflict_is_warning_but_time_is_preserved(tmp_path) -> None:
    input_path = tmp_path / "clinical_conflict.csv"
    input_path.write_text(
        "\n".join(
            [
                "case_submitter_id,days_to_death,days_to_last_follow_up,vital_status,gender,stage",
                "TCGA-AB-1234,90,,Alive,Female,Stage I",
            ]
        ),
        encoding="utf-8",
    )

    result = import_tcga_clinical_table(input_path, tmp_path / "out", "TCGA-THCA", "batch-4")
    rows = _read_csv(result["asset_paths"][TCGA_CLINICAL_TABLE])

    assert rows[0]["os_time_days"] == "90"
    assert rows[0]["os_event"] == "1"
    assert "os_event_conflict:TCGA-AB-1234:time_event=1:vital_event=0" in result["warnings"]


def test_clinical_import_writes_linkage_summary_and_preserves_expression_manifest(tmp_path) -> None:
    expression_input = tmp_path / "expression.csv"
    expression_input.write_text(
        "\n".join(
            [
                "gene_id,TCGA-AB-1234-01A,TCGA-ZZ-9999-11A",
                "TP53,1.0,2.0",
            ]
        ),
        encoding="utf-8",
    )
    expression_result = import_tcga_expression_matrix(
        expression_input,
        tmp_path / "out",
        "TCGA-THCA",
        "batch-5",
        normalization="TPM",
    )

    clinical_input = tmp_path / "clinical.csv"
    clinical_input.write_text(
        "\n".join(
            [
                "bcr_patient_barcode,days_to_death,days_to_last_follow_up,vital_status,age_at_diagnosis,gender,ajcc_pathologic_stage",
                "TCGA-AB-1234,100,,Dead,21915,Female,Stage II",
                "TCGA-CD-5678,,200,Alive,50,Male,Stage I",
            ]
        ),
        encoding="utf-8",
    )

    result = import_tcga_clinical_table(
        clinical_input,
        tmp_path / "out",
        "TCGA-THCA",
        "batch-5",
        sample_metadata_path=expression_result["asset_paths"][TCGA_SAMPLE_METADATA],
        parameters={"fixture": "linkage"},
    )
    linkage_path = Path(result["asset_paths"][TCGA_CLINICAL_LINKAGE_SUMMARY])
    manifest_path = Path(result["asset_paths"][TCGA_PREPARE_MANIFEST])
    linkage = json.loads(linkage_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert linkage == {
        "sample_count": 2,
        "unique_sample_patients": 2,
        "clinical_patient_count": 2,
        "matched_patient_count": 1,
        "unmatched_sample_patients": ["TCGA-ZZ-9999"],
        "unmatched_clinical_patients": ["TCGA-CD-5678"],
    }
    assert result["matched_patient_count"] == 1
    assert manifest["gene_count"] == 1
    assert manifest["sample_count"] == 2
    assert manifest["normalization"] == "TPM"
    assert manifest["clinical_patient_count"] == 2
    assert manifest["matched_patient_count"] == 1
    assert manifest["parameters"]["clinical_import"]["fixture"] == "linkage"
    assert TCGA_EXPRESSION_MATRIX in manifest["asset_paths"]
    assert TCGA_SAMPLE_METADATA in manifest["asset_paths"]
    assert TCGA_CLINICAL_TABLE in manifest["asset_paths"]
    assert TCGA_CLINICAL_LINKAGE_SUMMARY in manifest["asset_paths"]

