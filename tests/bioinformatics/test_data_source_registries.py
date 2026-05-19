from __future__ import annotations

import json

from app.bioinformatics.data_sources.tcga_preview import (
    TCGAMetadataPreviewService,
    build_gdc_file_filters,
    build_tcga_preview_request,
    format_bytes_zh,
    write_tcga_download_plan_draft,
)
from app.bioinformatics.gtex_tissue_registry import get_gtex_tissue, get_gtex_use_purpose, grouped_gtex_tissues, list_gtex_tissues
from app.bioinformatics.tcga_project_registry import get_tcga_analysis_purpose, get_tcga_project, get_tcga_sample_scope, grouped_tcga_projects, list_tcga_projects


def test_tcga_registry_contains_primary_33_projects() -> None:
    projects = list_tcga_projects()

    assert len(projects) == 33
    assert get_tcga_project("TCGA-THCA").chinese_name == "甲状腺癌"
    assert get_tcga_project("TCGA-THCA").project_id == "TCGA-THCA"
    assert get_tcga_project("TCGA-LIHC").chinese_name == "肝细胞癌"
    assert get_tcga_project("TCGA-BRCA").chinese_name == "乳腺浸润癌"
    assert get_tcga_project("TCGA-LUAD").chinese_name == "肺腺癌"
    assert "内分泌/神经内分泌" in grouped_tcga_projects()


def test_tcga_analysis_purpose_maps_expected_assets() -> None:
    deg = get_tcga_analysis_purpose("differential_expression")
    clinical = get_tcga_analysis_purpose("expression_clinical")

    assert deg.chinese_name == "表达差异分析"
    assert deg.required_internal_assets == ("rna_seq_expression", "sample_metadata")
    assert "clinical_metadata" in clinical.required_internal_assets


def test_gtex_registry_contains_key_v8_tissues() -> None:
    tissues = list_gtex_tissues()
    names = {tissue.tissue_site_detail for tissue in tissues}

    assert "Thyroid" in names
    assert "Liver" in names
    assert "Lung" in names
    assert "Whole Blood" in names
    assert "Breast - Mammary Tissue" in names
    assert get_gtex_tissue("gtex_thyroid").chinese_name == "甲状腺"
    assert get_gtex_tissue("gtex_thyroid").version == "GTEx V8"
    assert "内分泌系统" in grouped_gtex_tissues()


def test_gtex_use_purpose_maps_expected_assets_and_boundary() -> None:
    reference = get_gtex_use_purpose("external_reference")

    assert reference.chinese_name == "作为外部参考数据"
    assert reference.required_internal_assets == ("gene_expression", "sample_annotation")
    assert reference.readiness_profile == "external_reference_not_tcga_control"


def test_tcga_preview_builds_gdc_filters_and_summary(tmp_path) -> None:
    request = build_tcga_preview_request(
        project=get_tcga_project("TCGA-THCA"),
        purpose=get_tcga_analysis_purpose("differential_expression"),
        scope=get_tcga_sample_scope("tumor_normal"),
    )
    file_filters = build_gdc_file_filters(request)

    assert request.include_expression is True
    assert request.sample_types == ("Primary Tumor", "Solid Tissue Normal")
    assert any(item["content"]["field"] == "analysis.workflow_type" for item in file_filters["content"])
    assert any(item["content"]["value"] == ["Primary Tumor", "Solid Tissue Normal"] for item in file_filters["content"])

    def fake_fetcher(endpoint, params, timeout):
        if endpoint == "/files":
            return {
                "data": {
                    "pagination": {"total": 2},
                    "hits": [
                        {
                            "file_id": "file-1",
                            "file_name": "a.tsv",
                            "file_size": 1024 * 1024,
                            "access": "open",
                            "data_format": "TSV",
                            "analysis": {"workflow_type": "STAR - Counts"},
                            "cases": [{"case_id": "case-1", "samples": [{"sample_id": "sample-1", "sample_type": "Primary Tumor"}]}],
                        },
                        {
                            "file_id": "file-2",
                            "file_name": "b.tsv",
                            "file_size": 2 * 1024 * 1024,
                            "access": "open",
                            "data_format": "TSV",
                            "analysis": {"workflow_type": "STAR - Counts"},
                            "cases": [{"case_id": "case-2", "samples": [{"sample_id": "sample-2", "sample_type": "Solid Tissue Normal"}]}],
                        },
                    ],
                }
            }
        return {
            "data": {
                "pagination": {"total": 2},
                "hits": [
                    {"case_id": "case-1", "samples": [{"sample_id": "sample-1", "sample_type": "Primary Tumor"}]},
                    {"case_id": "case-2", "samples": [{"sample_id": "sample-2", "sample_type": "Solid Tissue Normal"}]},
                ],
            }
        }

    summary = TCGAMetadataPreviewService(fake_fetcher, page_size=50).build_preview(request)
    draft = write_tcga_download_plan_draft(tmp_path, summary)
    payload = json.loads(draft.plan_path.read_text(encoding="utf-8"))

    assert summary.status == "ready"
    assert summary.case_count == 2
    assert summary.sample_count == 2
    assert summary.file_count == 2
    assert summary.estimated_size_bytes == 3 * 1024 * 1024
    assert format_bytes_zh(summary.estimated_size_bytes) == "3.0 MB"
    assert summary.sample_type_counts == {"Primary Tumor": 1, "Solid Tissue Normal": 1}
    assert summary.access_counts == {"open": 2}
    assert summary.workflow_type_counts == {"STAR - Counts": 2}
    assert summary.data_format_counts == {"TSV": 2}
    assert summary.is_download_plan_available is True
    assert draft.status == "draft_only"
    assert payload["constraints"]["downloads_files"] is False
    assert payload["constraints"]["writes_source_files"] is False
    assert "source_files" not in payload


def test_tcga_preview_handles_empty_normal_and_network_failure() -> None:
    normal_request = build_tcga_preview_request(
        project=get_tcga_project("TCGA-THCA"),
        purpose=get_tcga_analysis_purpose("differential_expression"),
        scope=get_tcga_sample_scope("normal"),
    )

    def empty_fetcher(endpoint, params, timeout):
        return {"data": {"pagination": {"total": 0}, "hits": []}}

    empty_summary = TCGAMetadataPreviewService(empty_fetcher).build_preview(normal_request)

    assert empty_summary.status == "empty"
    assert empty_summary.is_download_plan_available is False
    assert any("未找到癌旁正常样本" in warning for warning in empty_summary.warnings)
    assert any("未找到符合当前项目" in warning for warning in empty_summary.warnings)

    def failing_fetcher(endpoint, params, timeout):
        raise TimeoutError("timeout")

    failed_summary = TCGAMetadataPreviewService(failing_fetcher).build_preview(normal_request)

    assert failed_summary.status == "failed"
    assert failed_summary.is_download_plan_available is False
    assert failed_summary.error_message == "timeout"
