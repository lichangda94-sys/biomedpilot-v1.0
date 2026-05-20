from __future__ import annotations

import csv
import json
from pathlib import Path

import app.bioinformatics.workflow_pages as workflow_pages
from app.bioinformatics.data_sources.tcga_clinical_builder import (
    TCGAClinicalMetadataBuilder,
    build_gdc_clinical_case_filters,
    latest_tcga_expression_build_manifest_path,
)
from app.bioinformatics.project_readiness import build_tcga_clinical_readiness_summary, run_project_readiness
from app.bioinformatics.project_workspace_binding import register_acquisition


def _tsv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _create_expression_build_record(tmp_path: Path) -> Path:
    base = tmp_path / "standardized_data" / "tcga" / "tcga-thca" / "build-1" / "data_prepared" / "tcga"
    expression = base / "expression" / "tcga_expression_matrix.csv"
    sample_mapping = base / "sample_metadata" / "tcga_sample_file_mapping.csv"
    sample_metadata = base / "sample_metadata" / "tcga_sample_metadata.csv"
    gene_annotation = base / "expression" / "tcga_gene_annotation.csv"
    manifest = base / "tcga_expression_build_manifest.json"
    expression.parent.mkdir(parents=True, exist_ok=True)
    sample_mapping.parent.mkdir(parents=True, exist_ok=True)
    expression.write_text("gene_id,TCGA-AA-0001-01A,TCGA-AA-0001-11A,TCGA-BB-0002-01A\nENSG00000141510,10,3,7\n", encoding="utf-8")
    sample_mapping.write_text(
        "\n".join(
            [
                "sample_barcode,case_id,case_submitter_id,sample_id,sample_type,file_id,file_name,local_path",
                "TCGA-AA-0001-01A,case-1,TCGA-AA-0001,sample-1,Primary Tumor,file-1,tumor.tsv,/raw/tumor.tsv",
                "TCGA-AA-0001-11A,case-1,TCGA-AA-0001,sample-2,Solid Tissue Normal,file-2,normal.tsv,/raw/normal.tsv",
                "TCGA-BB-0002-01A,,TCGA-BB-0002,sample-3,Primary Tumor,file-3,tumor2.tsv,/raw/tumor2.tsv",
                "",
            ]
        ),
        encoding="utf-8",
    )
    sample_metadata.write_text("sample_id,sample_type_label\nTCGA-AA-0001-01A,Primary Tumor\n", encoding="utf-8")
    gene_annotation.write_text("gene_id,gene_name\nENSG00000141510,TP53\n", encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.tcga_expression_build_manifest.v1",
                "project_id": "TCGA-THCA",
                "build_id": "build-1",
                "metric_matrix_paths": {"raw_counts": str(expression)},
                "sample_mapping_path": str(sample_mapping),
                "sample_metadata_path": str(sample_metadata),
                "gene_annotation_path": str(gene_annotation),
                "gene_count": 1,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    register_acquisition(
        tmp_path,
        source_type="tcga_project",
        source_label="TCGA-THCA",
        strategy="reference",
        selected_paths=[expression, sample_mapping, sample_metadata, gene_annotation, manifest],
        metadata={
            "source": "tcga_gdc",
            "ui_source": "tcga_database_page",
            "download_status": "tcga_expression_matrix_built",
            "ready_for_recognition": "pending_data_check",
            "analysis_gate_status": "pending_data_check",
            "project_id": "TCGA-THCA",
            "build_id": "build-1",
            "tcga_expression_build_manifest_path": str(manifest),
            "tcga_expression_matrix_path": str(expression),
            "tcga_sample_mapping_path": str(sample_mapping),
            "tcga_sample_metadata_path": str(sample_metadata),
            "tcga_gene_annotation_path": str(gene_annotation),
        },
    )
    return manifest


def _cases_response() -> list[dict[str, object]]:
    return [
        {
            "case_id": "case-1",
            "submitter_id": "TCGA-AA-0001",
            "project": {"project_id": "TCGA-THCA"},
            "primary_site": "Thyroid gland",
            "disease_type": "Papillary thyroid carcinoma",
            "demographic": {
                "gender": "female",
                "race": "white",
                "ethnicity": "not hispanic or latino",
                "vital_status": "Dead",
                "days_to_death": 400,
                "age_at_index": 52,
            },
            "diagnoses": [
                {
                    "diagnosis_id": "diag-1",
                    "primary_diagnosis": "Papillary carcinoma",
                    "tumor_stage": "stage ii",
                    "ajcc_pathologic_stage": "Stage II",
                    "days_to_last_follow_up": 390,
                },
                {
                    "diagnosis_id": "diag-2",
                    "primary_diagnosis": "Second diagnosis",
                },
            ],
            "follow_ups": [{"follow_up_id": "fu-1", "days_to_follow_up": 399}],
        },
        {
            "case_id": "case-2",
            "submitter_id": "TCGA-BB-0002",
            "project": {"project_id": "TCGA-THCA"},
            "demographic": {"gender": "male", "vital_status": "Alive"},
            "diagnoses": [{"diagnosis_id": "diag-3", "days_to_last_follow_up": ""}],
            "follow_ups": [{"follow_up_id": "fu-2", "days_to_follow_up": 900}],
        },
    ]


def test_gdc_clinical_filters_support_project_case_id_and_submitter() -> None:
    filters = build_gdc_clinical_case_filters(project_id="TCGA-THCA", case_ids=["case-1"], case_submitter_ids=["TCGA-AA-0001"])

    assert filters["op"] == "and"
    content = filters["content"]
    assert content[0]["content"]["field"] == "project.project_id"
    assert content[1]["op"] == "or"
    fields = {item["content"]["field"] for item in content[1]["content"]}
    assert fields == {"case_id", "submitter_id"}


def test_tcga_clinical_builder_fetches_cases_maps_expression_and_registers_artifacts(tmp_path: Path) -> None:
    manifest = _create_expression_build_record(tmp_path)
    seen_params: list[dict[str, object]] = []

    def fake_fetcher(endpoint, params, timeout):
        assert endpoint == "/cases"
        seen_params.append(params)
        return {"data": {"pagination": {"total": 2}, "hits": _cases_response()}}

    result = TCGAClinicalMetadataBuilder(fake_fetcher).build_for_latest_expression_build(tmp_path)

    assert latest_tcga_expression_build_manifest_path(tmp_path) == manifest
    assert result.status == "tcga_clinical_metadata_built"
    assert result.mode == "expression_matched_cases"
    assert result.case_count == 2
    assert result.matched_case_count == 2
    assert result.matched_sample_count == 3
    assert result.survival_case_count == 2
    assert result.death_event_count == 1
    assert seen_params[0]["fields"]
    raw_payload = json.loads(result.raw_cases_path.read_text(encoding="utf-8"))
    assert raw_payload["endpoint"] == "/cases"
    case_rows = _tsv_rows(result.case_table_path)
    assert case_rows[0]["gender"] == "female"
    diagnosis_rows = _tsv_rows(result.diagnosis_table_path)
    assert len(diagnosis_rows) == 3
    followup_rows = _tsv_rows(result.followup_table_path)
    assert {row["follow_up_id"] for row in followup_rows} == {"fu-1", "fu-2"}
    survival_rows = _tsv_rows(result.survival_table_path)
    dead = next(row for row in survival_rows if row["case_submitter_id"] == "TCGA-AA-0001")
    assert dead["OS_event"] == "1"
    assert dead["OS_time"] == "400"
    alive = next(row for row in survival_rows if row["case_submitter_id"] == "TCGA-BB-0002")
    assert alive["OS_event"] == "0"
    assert alive["OS_time"] == "900"
    mapping_rows = _tsv_rows(result.mapping_table_path)
    assert [row["mapping_status"] for row in mapping_rows].count("matched_by_case_id") == 2
    assert any(row["mapping_status"] == "matched_by_case_submitter_id" for row in mapping_rows)
    clinical_manifest = json.loads(result.clinical_manifest_path.read_text(encoding="utf-8"))
    assert clinical_manifest["not_expression_source_files"] is True
    assert "case_table" in clinical_manifest["derived_artifacts"]
    record = json.loads(result.acquisition_summary.record_path.read_text(encoding="utf-8"))
    assert record["source_files"] == [str(result.raw_cases_path)]
    assert record["metadata"]["download_status"] == "tcga_clinical_metadata_built"
    assert record["metadata"]["clinical_gate_status"] == "clinical_ready"
    assert record["metadata"]["survival_gate_status"] == "survival_ready_basic"
    source_manifest = json.loads(Path(record["metadata"]["source_manifest_path"]).read_text(encoding="utf-8"))
    assert [item["role"] for item in source_manifest["file_records"]] == ["tcga_gdc_raw_cases_json"]
    assert str(result.case_table_path) not in record["source_files"]
    assert workflow_pages._ready_registered_source_count(tmp_path) == 1


def test_tcga_clinical_builder_allows_project_preview_without_expression_build(tmp_path: Path) -> None:
    def fake_fetcher(endpoint, params, timeout):
        return {"data": {"pagination": {"total": 1}, "hits": [_cases_response()[0]]}}

    result = TCGAClinicalMetadataBuilder(fake_fetcher).build_for_project(tmp_path, "TCGA-THCA")

    assert result.mode == "project_clinical_preview_only"
    assert result.case_count == 1
    assert result.matched_case_count == 0
    assert "project_clinical_preview_only_no_expression_mapping" in result.warnings
    record = json.loads(result.acquisition_summary.record_path.read_text(encoding="utf-8"))
    assert record["metadata"]["clinical_gate_status"] == "clinical_partial"
    assert workflow_pages._ready_registered_source_count(tmp_path) == 0


def test_tcga_clinical_readiness_reports_basic_survival_preflight_only(tmp_path: Path) -> None:
    _create_expression_build_record(tmp_path)

    def fake_fetcher(endpoint, params, timeout):
        return {"data": {"pagination": {"total": 2}, "hits": _cases_response()}}

    result = TCGAClinicalMetadataBuilder(fake_fetcher).build_for_latest_expression_build(tmp_path)
    clinical = build_tcga_clinical_readiness_summary(tmp_path)
    readiness = run_project_readiness(tmp_path)
    report = readiness["readiness_report"]
    survival_row = next(row for row in readiness["capability_matrix"]["rows"] if row["analysis_type"] == "survival")

    assert clinical["clinical_gate_status"] == "clinical_ready"
    assert clinical["survival_gate_status"] == "survival_ready_basic"
    assert clinical["survival_execution_status"] == "not_executed"
    assert {"tcga_clinical_metadata", "clinical_metadata", "basic_survival_metadata"} <= set(report["available_inputs"])
    assert report["tcga_clinical_readiness"]["clinical_gate_status"] == "clinical_ready"
    assert Path(str(report["tcga_clinical_readiness"]["build_manifest_path"])).is_file()
    assert any("不执行 KM/Cox/log-rank" in warning for warning in survival_row["warnings"])
