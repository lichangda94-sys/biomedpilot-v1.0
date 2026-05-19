from __future__ import annotations

import csv
import json
from pathlib import Path

import app.bioinformatics.workflow_pages as workflow_pages
from app.bioinformatics.data_sources.tcga_download_executor import TCGADownloadPlanExecutor
from app.bioinformatics.data_sources.tcga_expression_builder import TCGAExpressionQuantificationBuilder, latest_tcga_raw_expression_record_path
from app.bioinformatics.data_sources.tcga_preview import TCGAMetadataPreviewService, build_tcga_preview_request, write_tcga_download_plan_draft
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


def test_tcga_expression_builder_rejects_missing_b6_3_raw_record(tmp_path: Path) -> None:
    assert latest_tcga_raw_expression_record_path(tmp_path) is None
    try:
        TCGAExpressionQuantificationBuilder().build_latest(tmp_path)
    except FileNotFoundError as exc:
        assert "等待 B6.4" in str(exc)
    else:
        raise AssertionError("build_latest should require a B6.3 raw acquisition record")
