from __future__ import annotations

import json
from pathlib import Path

import app.bioinformatics.workflow_pages as workflow_pages
from app.bioinformatics.data_sources.tcga_download_executor import TCGADownloadPlanExecutor
from app.bioinformatics.data_sources.tcga_preview import (
    TCGAMetadataPreviewService,
    build_tcga_preview_request,
    write_tcga_download_plan_draft,
)
from app.bioinformatics.tcga_project_registry import get_tcga_analysis_purpose, get_tcga_project, get_tcga_sample_scope


class _FakeGdcDownloader:
    def __init__(self, *, fail_ids: set[str] | None = None, cache_ids: set[str] | None = None) -> None:
        self.fail_ids = fail_ids or set()
        self.cache_ids = cache_ids or set()

    def download_file(self, entry: dict[str, object], target_dir: Path) -> dict[str, object]:
        file_id = str(entry.get("file_id") or "")
        if file_id in self.fail_ids:
            raise RuntimeError("network error")
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / str(entry.get("file_name") or f"{file_id}.tsv")
        if file_id in self.cache_ids:
            target_path.write_bytes(b"cached\n")
            return {
                "status": "success",
                "cache_hit": True,
                "local_path": str(target_path),
                "bytes_downloaded": target_path.stat().st_size,
                "source_url": f"https://api.gdc.cancer.gov/data/{file_id}",
                "sha256": "fake",
            }
        target_path.write_bytes(f"{file_id}\n".encode("utf-8"))
        return {
            "status": "success",
            "cache_hit": False,
            "local_path": str(target_path),
            "bytes_downloaded": target_path.stat().st_size,
            "source_url": f"https://api.gdc.cancer.gov/data/{file_id}",
            "sha256": "fake",
        }


def _preview_summary(entries: list[dict[str, object]]):
    request = build_tcga_preview_request(
        project=get_tcga_project("TCGA-THCA"),
        purpose=get_tcga_analysis_purpose("differential_expression"),
        scope=get_tcga_sample_scope("tumor"),
    )

    def fake_fetcher(endpoint, params, timeout):
        if endpoint == "/files":
            return {"data": {"pagination": {"total": len(entries)}, "hits": entries}}
        return {"data": {"pagination": {"total": 1}, "hits": [{"case_id": "case-1", "samples": [{"sample_id": "s1", "sample_type": "Primary Tumor"}]}]}}

    return TCGAMetadataPreviewService(fake_fetcher).build_preview(request)


def test_tcga_download_plan_executor_registers_raw_source_files_not_ready(tmp_path: Path) -> None:
    entries = [
        {
            "file_id": "file-1",
            "file_name": "file-1.tsv",
            "file_size": 7,
            "access": "open",
            "data_type": "Gene Expression Quantification",
            "data_format": "TSV",
            "analysis": {"workflow_type": "STAR - Counts"},
            "cases": [{"case_id": "case-1", "samples": [{"sample_id": "s1", "sample_type": "Primary Tumor"}]}],
        }
    ]
    summary = _preview_summary(entries)
    draft = write_tcga_download_plan_draft(tmp_path, summary)

    result = TCGADownloadPlanExecutor(downloader=_FakeGdcDownloader()).execute_plan(tmp_path, plan_path=draft.plan_path)

    assert result.status == "tcga_gdc_raw_files_acquired"
    assert result.success_count == 1
    assert result.failed_count == 0
    assert result.cache_hit_count == 0
    assert len(result.downloaded_files) == 1
    receipt = json.loads(result.receipt_path.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "biomedpilot.tcga_gdc_download_receipt.v1"
    assert receipt["summary"]["acquired_count"] == 1
    assert receipt["analysis_gate_status"] == "waiting_b6_4_expression_matrix_build"
    assert result.acquisition_summary is not None
    record_path = tmp_path / "acquisition" / "records" / f"{result.acquisition_summary.acquisition_id}.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["strategy"] == "reference"
    assert record["source_files"] == list(result.downloaded_files)
    assert record["metadata"]["ready_for_recognition"] == "pending_expression_matrix_build"
    assert record["metadata"]["analysis_gate_status"] == "waiting_b6_4_expression_matrix_build"
    assert Path(record["metadata"]["source_manifest_path"]).is_file()
    assert workflow_pages._ready_registered_source_count(tmp_path) == 0


def test_tcga_download_plan_executor_fallback_blocks_and_records_failures(tmp_path: Path) -> None:
    plan_path = tmp_path / "acquisition" / "tcga_download_plans" / "legacy.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.tcga_gdc_download_plan_draft.v1",
                "plan_id": "legacy",
                "project_id": "TCGA-THCA",
                "analysis_purpose": "differential_expression",
                "sample_scope": "tumor",
                "gdc_filters": {"op": "and", "content": [{"op": "in", "content": {"field": "cases.project.project_id", "value": ["TCGA-THCA"]}}]},
                "case_filters": {"op": "and", "content": []},
                "file_count": 4,
                "estimated_size_bytes": 0,
                "selected_file_ids_preview": [],
                "warnings": [],
                "status": "draft_only",
                "created_at": "2026-05-19T00:00:00+00:00",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fake_fetcher(endpoint, params, timeout):
        assert endpoint == "/files"
        return {
            "data": {
                "pagination": {"total": 4},
                "hits": [
                    {"file_id": "ok", "file_name": "ok.tsv", "access": "open", "data_type": "Gene Expression Quantification", "data_format": "TSV"},
                    {"file_id": "cache", "file_name": "cache.tsv", "access": "open", "data_type": "Gene Expression Quantification", "data_format": "TSV"},
                    {"file_id": "fail", "file_name": "fail.tsv", "access": "open", "data_type": "Gene Expression Quantification", "data_format": "TSV"},
                    {"file_id": "bam", "file_name": "raw.bam", "access": "controlled", "data_type": "Aligned Reads", "data_format": "BAM"},
                ],
            }
        }

    result = TCGADownloadPlanExecutor(
        downloader=_FakeGdcDownloader(fail_ids={"fail"}, cache_ids={"cache"}),
        fetcher=fake_fetcher,
    ).execute_plan(tmp_path, plan_path=plan_path)

    assert result.status == "tcga_gdc_raw_files_acquired_with_warnings"
    assert result.success_count == 1
    assert result.cache_hit_count == 1
    assert result.failed_count == 1
    assert result.blocked_count == 1
    receipt = json.loads(result.receipt_path.read_text(encoding="utf-8"))
    statuses = [event["status"] for event in receipt["download_events"]]
    assert statuses == ["downloaded", "cache_hit", "failed", "blocked"]
    assert len(receipt["downloaded_files"]) == 2
    assert workflow_pages._ready_registered_source_count(tmp_path) == 0


def test_tcga_download_plan_executor_empty_plan_is_not_ready(tmp_path: Path) -> None:
    plan_path = tmp_path / "acquisition" / "tcga_download_plans" / "empty.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.tcga_gdc_download_plan_draft.v1",
                "plan_id": "empty",
                "project_id": "TCGA-THCA",
                "analysis_purpose": "differential_expression",
                "sample_scope": "tumor",
                "gdc_filters": {},
                "case_filters": {},
                "file_count": 0,
                "estimated_size_bytes": 0,
                "selected_file_ids_preview": [],
                "warnings": [],
                "status": "draft_only",
                "created_at": "2026-05-19T00:00:00+00:00",
                "file_manifest_entries": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = TCGADownloadPlanExecutor(downloader=_FakeGdcDownloader()).execute_plan(tmp_path, plan_path=plan_path)

    assert result.status == "tcga_gdc_download_plan_empty"
    assert result.downloaded_files == ()
    assert result.acquisition_summary is not None
    assert result.acquisition_summary.strategy == "plan_only"
    assert workflow_pages._ready_registered_source_count(tmp_path) == 0
