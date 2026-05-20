from __future__ import annotations

import csv
import json
from pathlib import Path

import app.bioinformatics.workflow_pages as workflow_pages
import app.bioinformatics.data_sources.gtex_download_executor as gtex_download_executor
from app.bioinformatics.data_sources.gtex_download_executor import GTExDownloadPlanExecutor, latest_gtex_raw_expression_record_path
from app.bioinformatics.data_sources.gtex_expression_builder import GTExExpressionMatrixBuilder, latest_gtex_expression_build_manifest_path
from app.bioinformatics.data_sources.gtex_preview import GTExMetadataPreviewService, build_gtex_preview_request, write_gtex_download_plan_draft
from app.bioinformatics.data_sources.gtex_workflow import build_gtex_workflow_state
from app.bioinformatics.gtex_tissue_registry import get_gtex_tissue, get_gtex_use_purpose
from app.bioinformatics.project_readiness import build_gtex_readiness_summary, run_project_readiness


class _FakeDownloader:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def download_file(self, entry: dict[str, object], target_dir: Path) -> dict[str, object]:
        if self.fail:
            raise RuntimeError("network error")
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / str(entry.get("file_name") or "gtex_expression.tsv")
        target.write_text("gene_id\tGTEX-1111-0001-SM-A\tGTEX-2222-0001-SM-B\nTP53\t1.2\t2.4\nPTEN\t0.5\t0.8\n", encoding="utf-8")
        return {"status": "success", "cache_hit": False, "local_path": str(target), "bytes_downloaded": target.stat().st_size, "source_url": str(entry.get("url") or "")}


def _preview(tmp_path: Path):
    request = build_gtex_preview_request(tissue=get_gtex_tissue("gtex_thyroid"), purpose=get_gtex_use_purpose("download_tissue_matrix"))

    def fake_fetcher(url, params, timeout):
        return {
            "data": [
                {
                    "tissueSiteDetailId": "Thyroid",
                    "tissueSiteDetail": "Thyroid",
                    "rnaSeqSampleCount": 2,
                    "donorCount": 2,
                    "datasetId": "GTEx_v8",
                    "file_manifest_entries": [
                        {"file_id": "gtex-thyroid", "file_name": "gtex_thyroid_tpm.tsv", "file_size": 10, "url": "https://example.org/gtex_thyroid_tpm.tsv", "value_type": "TPM"}
                    ],
                }
            ]
        }

    summary = GTExMetadataPreviewService(fake_fetcher).build_preview(request)
    draft = write_gtex_download_plan_draft(tmp_path, summary)
    return summary, draft


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_gtex_preview_writes_plan_without_source_files(tmp_path: Path) -> None:
    summary, draft = _preview(tmp_path)

    assert summary.status == "ready"
    assert summary.sample_count == 2
    assert summary.file_count == 1
    payload = json.loads(draft.plan_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "biomedpilot.gtex_download_plan_draft.v1"
    assert payload["constraints"]["not_tcga_normal_control"] is True
    assert "source_files" not in payload


def test_gtex_download_build_and_readiness_do_not_enable_tcga_merge(tmp_path: Path) -> None:
    _, draft = _preview(tmp_path)
    download = GTExDownloadPlanExecutor(downloader=_FakeDownloader()).execute_plan(tmp_path, plan_path=draft.plan_path)

    assert download.status == "gtex_raw_files_acquired"
    assert latest_gtex_raw_expression_record_path(tmp_path) is not None
    assert workflow_pages._ready_registered_source_count(tmp_path) == 0
    raw_state = build_gtex_workflow_state(tmp_path, tissue_id="gtex_thyroid")
    assert raw_state.step("expression_build").enabled is True

    build = GTExExpressionMatrixBuilder().build_latest(tmp_path)
    assert build.status == "gtex_expression_matrix_built"
    assert build.sample_count == 2
    assert build.donor_count == 2
    assert build.gene_count == 2
    assert latest_gtex_expression_build_manifest_path(tmp_path) == build.build_manifest_path
    assert _csv_rows(build.sample_metadata_path)[0]["tcga_default_control_status"] == "disabled"
    manifest = json.loads(build.build_manifest_path.read_text(encoding="utf-8"))
    assert manifest["tcga_merge_status"] == "not_merged"
    assert manifest["tcga_default_control_status"] == "disabled"

    gtex = build_gtex_readiness_summary(tmp_path)
    assert gtex["has_gtex_expression_build"] is True
    assert gtex["tcga_default_control_status"] == "disabled"
    assert gtex["requires_explicit_joint_config"] is True
    readiness = run_project_readiness(tmp_path)
    report = readiness["readiness_report"]
    assert "gtex_expression_matrix" in report["available_inputs"]
    joint_row = next(row for row in readiness["capability_matrix"]["rows"] if row["analysis_type"] == "tcga_gtex_joint")
    assert joint_row["can_run"] is False
    assert any("不会自动作为 TCGA normal control" in warning for warning in joint_row["warnings"])


def test_gtex_failed_download_does_not_unlock_build(tmp_path: Path) -> None:
    _, draft = _preview(tmp_path)
    result = GTExDownloadPlanExecutor(downloader=_FakeDownloader(fail=True)).execute_plan(tmp_path, plan_path=draft.plan_path)

    assert result.status == "gtex_raw_file_download_failed"
    assert latest_gtex_raw_expression_record_path(tmp_path) is None
    state = build_gtex_workflow_state(tmp_path, tissue_id="gtex_thyroid")
    assert state.step("download").status == "failed"
    assert state.step("expression_build").status == "blocked"


def test_gtex_preview_selects_requested_tissue_from_unfiltered_api_list(tmp_path: Path) -> None:
    request = build_gtex_preview_request(tissue=get_gtex_tissue("gtex_minor_salivary_gland"), purpose=get_gtex_use_purpose("download_tissue_matrix"))

    def fake_fetcher(url, params, timeout):
        return {
            "data": [
                {"tissueSiteDetailId": "Adipose_Subcutaneous", "tissueSiteDetail": "Adipose - Subcutaneous", "rnaSeqSampleCount": 663},
                {"tissueSiteDetailId": "Minor_Salivary_Gland", "tissueSiteDetail": "Minor Salivary Gland", "rnaSeqSampleCount": 162, "donorCount": 162},
            ]
        }

    summary = GTExMetadataPreviewService(fake_fetcher).build_preview(request)

    assert summary.tissue_metadata["tissueSiteDetail"] == "Minor Salivary Gland"
    assert summary.sample_count == 162


def test_gtex_light_validation_slice_download_build_and_readiness(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("BIOINF_LIGHT_VALIDATION_MODE", "1")
    monkeypatch.setenv("BIOINF_GTEX_DOWNLOAD_LIMIT_FILES", "1")
    monkeypatch.setenv("BIOINF_GTEX_LIMIT_SAMPLES", "3")
    monkeypatch.setenv("BIOINF_GTEX_LIMIT_GENES", "2")
    request = build_gtex_preview_request(tissue=get_gtex_tissue("gtex_minor_salivary_gland"), purpose=get_gtex_use_purpose("download_tissue_matrix"))

    def fake_fetcher(url, params, timeout):
        return {"data": [{"tissueSiteDetailId": "Minor_Salivary_Gland", "tissueSiteDetail": "Minor Salivary Gland", "rnaSeqSampleCount": 162, "donorCount": 162}]}

    def fake_gtex_json(url, params, timeout):
        if url.endswith("topExpressedGene"):
            return {
                "data": [
                    {"gencodeId": "ENSG000001.1", "geneSymbol": "GENE1"},
                    {"gencodeId": "ENSG000002.1", "geneSymbol": "GENE2"},
                    {"gencodeId": "ENSG000003.1", "geneSymbol": "GENE3"},
                ]
            }
        return {"data": [{"gencodeId": params["gencodeId"], "geneSymbol": params["gencodeId"], "data": [1.0, 2.0, 3.0, 4.0]}]}

    monkeypatch.setattr(gtex_download_executor, "_fetch_gtex_json", fake_gtex_json)
    summary = GTExMetadataPreviewService(fake_fetcher).build_preview(request)
    draft = write_gtex_download_plan_draft(tmp_path, summary)
    plan = json.loads(draft.plan_path.read_text(encoding="utf-8"))
    assert plan["validation_limited"] is True
    assert plan["file_count"] == 1

    download = GTExDownloadPlanExecutor().execute_plan(tmp_path, plan_path=draft.plan_path)
    assert download.success_count == 1
    receipt = json.loads(download.receipt_path.read_text(encoding="utf-8"))
    assert receipt["validation_limited"] is True

    build = GTExExpressionMatrixBuilder().build_latest(tmp_path, tissue_id="gtex_minor_salivary_gland")
    assert build.sample_count == 3
    assert build.gene_count == 2
    manifest = json.loads(build.build_manifest_path.read_text(encoding="utf-8"))
    assert manifest["validation_limited"] is True
    readiness = run_project_readiness(tmp_path)
    report = readiness["readiness_report"]
    assert report["validation_limited"] is True
    deg = next(row for row in readiness["capability_matrix"]["rows"] if row["analysis_type"] == "differential_expression")
    assert deg["can_run"] is False
    assert any("轻量联网验收数据" in warning for warning in deg["warnings"])


def test_gtex_workflow_state_is_tissue_scoped(tmp_path: Path) -> None:
    summary, draft = _preview(tmp_path)
    GTExDownloadPlanExecutor(downloader=_FakeDownloader()).execute_plan(tmp_path, plan_path=draft.plan_path)
    GTExExpressionMatrixBuilder().build_latest(tmp_path, tissue_id="gtex_thyroid")

    other = build_gtex_workflow_state(tmp_path, tissue_id="gtex_fallopian_tube")
    assert other.step("download").status == "blocked"
    assert other.step("expression_build").status == "blocked"

    thyroid = build_gtex_workflow_state(tmp_path, tissue_id="gtex_thyroid")
    assert thyroid.step("expression_build").status == "completed"
