from __future__ import annotations

import csv
import json
from pathlib import Path

import app.bioinformatics.workflow_pages as workflow_pages
from app.bioinformatics.data_sources.tcga_download_executor import TCGADownloadPlanExecutor
from app.bioinformatics.data_sources.tcga_expression_builder import TCGAExpressionQuantificationBuilder, latest_tcga_raw_expression_record_path
from app.bioinformatics.data_sources.tcga_preview import TCGAMetadataPreviewService, build_tcga_preview_request, write_tcga_download_plan_draft
from app.bioinformatics.project_readiness import build_tcga_b6_4_readiness_summary, run_project_readiness
from app.bioinformatics.project_recognition import run_project_recognition
from app.bioinformatics.project_workspace_binding import register_acquisition
from app.bioinformatics.standardization_confirmation import collect_standardization_candidates
from app.bioinformatics.tcga_project_registry import get_tcga_analysis_purpose, get_tcga_project, get_tcga_sample_scope


class _QuantDownloader:
    def download_file(self, entry: dict[str, object], target_dir: Path) -> dict[str, object]:
        target_dir.mkdir(parents=True, exist_ok=True)
        file_id = str(entry["file_id"])
        target = target_dir / str(entry["file_name"])
        if file_id == "file-tumor":
            counts = ("100", "9.1", "4.1", "5.1")
        else:
            counts = ("20", "2.2", "1.2", "1.7")
        target.write_text(
            "\n".join(
                [
                    "# GDC STAR - Counts fixture",
                    "gene_id\tgene_name\tgene_type\tunstranded\ttpm_unstranded\tfpkm_unstranded\tfpkm_uq_unstranded",
                    f"ENSG00000141510.18\tTP53\tprotein_coding\t{counts[0]}\t{counts[1]}\t{counts[2]}\t{counts[3]}",
                    "ENSG00000171862.12\tPTEN\tprotein_coding\t3\t0.5\t0.2\t0.3",
                    "N_unmapped\tN_unmapped\t\t4\t0\t0\t0",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return {
            "status": "success",
            "cache_hit": False,
            "local_path": str(target),
            "bytes_downloaded": target.stat().st_size,
            "source_url": f"https://api.gdc.cancer.gov/data/{file_id}",
            "sha256": "fake",
        }


def _tcga_preview(entries: list[dict[str, object]]):
    request = build_tcga_preview_request(
        project=get_tcga_project("TCGA-THCA"),
        purpose=get_tcga_analysis_purpose("differential_expression"),
        scope=get_tcga_sample_scope("tumor"),
    )

    def fake_fetcher(endpoint, params, timeout):
        if endpoint == "/files":
            return {"data": {"pagination": {"total": len(entries)}, "hits": entries}}
        return {
            "data": {
                "pagination": {"total": 2},
                "hits": [
                    {"case_id": "case-tumor", "submitter_id": "TCGA-AA-0001", "samples": [{"sample_id": "sample-tumor", "submitter_id": "TCGA-AA-0001-01A", "sample_type": "Primary Tumor"}]},
                    {"case_id": "case-normal", "submitter_id": "TCGA-AA-0002", "samples": [{"sample_id": "sample-normal", "submitter_id": "TCGA-AA-0002-11A", "sample_type": "Solid Tissue Normal"}]},
                ],
            }
        }

    return TCGAMetadataPreviewService(fake_fetcher).build_preview(request)


def _create_b6_3_raw_record(tmp_path: Path):
    entries = [
        {
            "file_id": "file-tumor",
            "file_name": "tumor_star_counts.tsv",
            "file_size": 100,
            "access": "open",
            "data_type": "Gene Expression Quantification",
            "data_format": "TSV",
            "analysis": {"workflow_type": "STAR - Counts"},
            "cases": [{"case_id": "case-tumor", "submitter_id": "TCGA-AA-0001", "samples": [{"sample_id": "sample-tumor", "submitter_id": "TCGA-AA-0001-01A", "sample_type": "Primary Tumor"}]}],
        },
        {
            "file_id": "file-normal",
            "file_name": "normal_star_counts.tsv",
            "file_size": 100,
            "access": "open",
            "data_type": "Gene Expression Quantification",
            "data_format": "TSV",
            "analysis": {"workflow_type": "STAR - Counts"},
            "cases": [{"case_id": "case-normal", "submitter_id": "TCGA-AA-0002", "samples": [{"sample_id": "sample-normal", "submitter_id": "TCGA-AA-0002-11A", "sample_type": "Solid Tissue Normal"}]}],
        },
    ]
    summary = _tcga_preview(entries)
    draft = write_tcga_download_plan_draft(tmp_path, summary)
    plan_payload = json.loads(draft.plan_path.read_text(encoding="utf-8"))
    sample_submitters = {
        item
        for entry in plan_payload["file_manifest_entries"]
        for item in entry["sample_submitter_ids"]
    }
    assert sample_submitters == {"TCGA-AA-0001-01A", "TCGA-AA-0002-11A"}
    return TCGADownloadPlanExecutor(downloader=_QuantDownloader()).execute_plan(tmp_path, plan_path=draft.plan_path)


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_tcga_expression_builder_parses_b6_3_quant_files_and_registers_pending_data_check(tmp_path: Path) -> None:
    download_result = _create_b6_3_raw_record(tmp_path)
    raw_record_path = latest_tcga_raw_expression_record_path(tmp_path)

    result = TCGAExpressionQuantificationBuilder().build_latest(tmp_path)

    assert raw_record_path is not None
    assert result.status == "tcga_expression_matrix_built"
    assert result.raw_acquisition_record_path == raw_record_path
    assert result.parsed_file_count == 2
    assert result.sample_count == 2
    assert result.gene_count == 2
    matrix_rows = _csv_rows(result.expression_matrix_path)
    assert matrix_rows[0]["gene_id"] == "ENSG00000141510"
    assert matrix_rows[0]["TCGA-AA-0001-01A"] == "100"
    assert matrix_rows[0]["TCGA-AA-0002-11A"] == "20"
    tpm_rows = _csv_rows(Path(result.metric_matrix_paths["tpm"]))
    assert tpm_rows[0]["TCGA-AA-0001-01A"] == "9.1"
    annotation_rows = _csv_rows(result.gene_annotation_path)
    assert annotation_rows[0]["gene_name"] == "TP53"
    mapping_rows = _csv_rows(result.sample_mapping_path)
    assert {row["case_submitter_id"] for row in mapping_rows} == {"TCGA-AA-0001", "TCGA-AA-0002"}
    metadata_rows = _csv_rows(result.sample_metadata_path)
    assert {row["sample_type_code"] for row in metadata_rows} == {"01", "11"}
    manifest = json.loads(result.build_manifest_path.read_text(encoding="utf-8"))
    assert manifest["analysis_gate_status"] == "pending_data_check"
    assert result.acquisition_summary is not None
    record = json.loads((tmp_path / "acquisition" / "records" / f"{result.acquisition_summary.acquisition_id}.json").read_text(encoding="utf-8"))
    assert record["metadata"]["download_status"] == "tcga_expression_matrix_built"
    assert record["metadata"]["ready_for_recognition"] == "pending_data_check"
    assert workflow_pages._ready_registered_source_count(tmp_path) == 1
    entries = workflow_pages._current_project_dataset_entries(tmp_path)
    assert entries[0].status == "TCGA 表达矩阵已构建，等待数据检查与准备"
    assert entries[0].missing_content == "统一数据检查与准备"
    assert download_result.acquisition_summary is not None


def test_tcga_b6_4_readiness_exposes_value_type_policy_and_default_group(tmp_path: Path) -> None:
    _create_b6_3_raw_record(tmp_path)
    build_result = TCGAExpressionQuantificationBuilder().build_latest(tmp_path)

    readiness_artifacts = run_project_readiness(tmp_path)
    report = readiness_artifacts["readiness_report"]
    tcga = report["tcga_readiness"]

    assert tcga["status"] == "ready_for_deg_preflight_candidate"
    assert tcga["sample_match_status"] == "matched"
    assert tcga["default_group_status"] == "available"
    assert tcga["default_group_suggestion"]["case_count"] == 1
    assert tcga["default_group_suggestion"]["control_count"] == 1
    assert tcga["value_type_policy"]["raw_counts"]["value_type"] == "count"
    assert tcga["value_type_policy"]["raw_counts"]["default_for_deg"] is True
    assert tcga["value_type_policy"]["TPM"]["default_for_deg"] is False
    assert {"tcga_expression_matrix", "raw_count_matrix", "sample_metadata", "gene_annotation"} <= set(report["available_inputs"])
    assert report["deg_ready"] is False
    diff_row = next(row for row in readiness_artifacts["capability_matrix"]["rows"] if row["analysis_type"] == "differential_expression")
    assert "comparison_config" in diff_row["missing_inputs"]
    assert any("Primary Tumor vs Solid Tissue Normal" in warning for warning in diff_row["warnings"])

    run_project_recognition(tmp_path)
    candidates = collect_standardization_candidates(tmp_path)
    expression_candidates = [
        item for item in candidates["expression_matrix_candidates"]
        if item["source_path"] == str(build_result.expression_matrix_path)
    ]
    assert expression_candidates
    assert expression_candidates[0]["expression_value_type_candidate"] == "count"


def test_tcga_b6_4_readiness_marks_tumor_only_as_display_or_manual_group(tmp_path: Path) -> None:
    matrix = tmp_path / "standardized_data" / "tcga" / "tcga_thca" / "tumor_only" / "data_prepared" / "tcga" / "expression" / "tcga_expression_matrix.csv"
    sample_metadata = matrix.parents[1] / "sample_metadata" / "tcga_sample_metadata.csv"
    gene_annotation = matrix.parent / "tcga_gene_annotation.csv"
    build_manifest = matrix.parents[1] / "tcga_expression_build_manifest.json"
    matrix.parent.mkdir(parents=True, exist_ok=True)
    sample_metadata.parent.mkdir(parents=True, exist_ok=True)
    matrix.write_text("gene_id\tTCGA-AA-0001-01A\nENSG00000141510\t10\n".replace("\t", ","), encoding="utf-8")
    sample_metadata.write_text(
        "sample_id,barcode,tcga_barcode,sample_type_code,sample_type_label\n"
        "TCGA-AA-0001-01A,TCGA-AA-0001-01A,TCGA-AA-0001-01A,01,Primary Tumor\n",
        encoding="utf-8",
    )
    gene_annotation.write_text("gene_id,gene_name,gene_type\nENSG00000141510,TP53,protein_coding\n", encoding="utf-8")
    build_manifest.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.tcga_expression_build_manifest.v1",
                "build_id": "tumor-only",
                "project_id": "TCGA-THCA",
                "metric_matrix_paths": {"raw_counts": str(matrix)},
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
        selected_paths=[matrix, sample_metadata, gene_annotation, build_manifest],
        metadata={
            "source": "tcga_gdc",
            "download_status": "tcga_expression_matrix_built",
            "ready_for_recognition": "pending_data_check",
            "analysis_gate_status": "pending_data_check",
            "project_id": "TCGA-THCA",
            "build_id": "tumor-only",
            "tcga_expression_build_manifest_path": str(build_manifest),
            "tcga_expression_matrix_path": str(matrix),
            "tcga_sample_metadata_path": str(sample_metadata),
            "tcga_gene_annotation_path": str(gene_annotation),
        },
    )

    tcga = build_tcga_b6_4_readiness_summary(tmp_path)

    assert tcga["status"] == "expression_display_or_manual_group_only"
    assert tcga["default_group_status"] == "insufficient"
    assert tcga["sample_type_counts"] == {"Primary Tumor": 1}
    assert "tcga_default_tumor_normal_group_insufficient" in tcga["warnings"]


def test_tcga_expression_builder_rejects_missing_b6_3_raw_record(tmp_path: Path) -> None:
    assert latest_tcga_raw_expression_record_path(tmp_path) is None
    try:
        TCGAExpressionQuantificationBuilder().build_latest(tmp_path)
    except FileNotFoundError as exc:
        assert "等待 B6.4" in str(exc)
    else:
        raise AssertionError("build_latest should require a B6.3 raw acquisition record")
