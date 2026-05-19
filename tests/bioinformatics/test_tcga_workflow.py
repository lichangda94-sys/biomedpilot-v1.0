from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.data_sources.tcga_workflow import build_tcga_workflow_state
from app.bioinformatics.project_workspace_binding import register_acquisition


def _write_plan(root: Path, *, file_count: int = 2, warnings: list[str] | None = None) -> Path:
    path = root / "acquisition" / "tcga_download_plans" / "tcga-plan-test.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.tcga_gdc_download_plan_draft.v1",
                "plan_id": "tcga-plan-test",
                "project_id": "TCGA-THCA",
                "analysis_purpose": "differential_expression",
                "sample_scope": "tumor",
                "file_count": file_count,
                "estimated_size_bytes": 2048,
                "warnings": warnings or [],
                "status": "draft_only",
                "preview_summary": {"case_count": 2, "sample_count": 2, "file_count": file_count, "estimated_size_bytes": 2048},
                "file_manifest_entries": [{"file_id": "file-1", "file_name": "file-1.tsv"}] if file_count else [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _register_request(root: Path) -> None:
    register_acquisition(
        root,
        source_type="tcga_project",
        source_label="TCGA-THCA",
        strategy="plan_only",
        selected_paths=[],
        metadata={"source": "tcga_gdc", "project_id": "TCGA-THCA", "download_status": "registered_pending_tcga_build", "ready_for_recognition": "pending_download"},
    )


def _register_raw(root: Path, *, acquired: int = 1, failed: int = 0, blocked: int = 0, status: str = "tcga_gdc_raw_files_acquired") -> None:
    raw_file = root / "raw_data" / "tcga" / "TCGA-THCA" / "dl" / "file-1.tsv"
    raw_file.parent.mkdir(parents=True, exist_ok=True)
    if acquired:
        raw_file.write_text("gene_id\tvalue\nTP53\t1\n", encoding="utf-8")
    selected = [raw_file] if acquired else []
    register_acquisition(
        root,
        source_type="tcga_project",
        source_label="TCGA-THCA",
        strategy="reference" if acquired else "plan_only",
        selected_paths=selected,
        metadata={
            "source": "tcga_gdc",
            "project_id": "TCGA-THCA",
            "download_status": status,
            "ready_for_recognition": "pending_expression_matrix_build",
            "analysis_gate_status": "waiting_b6_4_expression_matrix_build",
            "download_receipt_path": str(root / "acquisition" / "download_receipts" / "receipt.json"),
            "source_manifest_path": str(root / "acquisition" / "source_manifests" / "source.json"),
            "tcga_download_summary": {
                "acquired_count": acquired,
                "success_count": acquired,
                "failed_count": failed,
                "blocked_count": blocked,
                "total_size_display": "1.0 KB",
            },
        },
    )


def _register_expression(root: Path, *, project: str = "TCGA-THCA") -> Path:
    base = root / "standardized_data" / "tcga" / project.lower() / "build" / "data_prepared" / "tcga"
    manifest = base / "tcga_expression_build_manifest.json"
    matrix = base / "expression" / "tcga_expression_matrix.csv"
    sample = base / "sample_metadata" / "tcga_sample_metadata.csv"
    gene = base / "expression" / "tcga_gene_annotation.csv"
    matrix.parent.mkdir(parents=True, exist_ok=True)
    sample.parent.mkdir(parents=True, exist_ok=True)
    matrix.write_text("gene_id,TCGA-AA-0001-01A\nTP53,1\n", encoding="utf-8")
    sample.write_text("sample_id\nTCGA-AA-0001-01A\n", encoding="utf-8")
    gene.write_text("gene_id,gene_name\nTP53,TP53\n", encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.tcga_expression_build_manifest.v1",
                "project_id": project,
                "build_id": "build",
                "sample_count": 1,
                "gene_count": 1,
                "metric_matrix_paths": {"raw_counts": str(matrix)},
                "sample_metadata_path": str(sample),
                "gene_annotation_path": str(gene),
                "warnings": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    register_acquisition(
        root,
        source_type="tcga_project",
        source_label=project,
        strategy="reference",
        selected_paths=[matrix, sample, gene, manifest],
        metadata={
            "source": "tcga_gdc",
            "project_id": project,
            "download_status": "tcga_expression_matrix_built",
            "ready_for_recognition": "pending_data_check",
            "analysis_gate_status": "pending_data_check",
            "tcga_expression_build_manifest_path": str(manifest),
            "tcga_expression_build_summary": {"sample_count": 1, "gene_count": 1},
        },
    )
    return manifest


def _register_clinical(root: Path, *, mode: str = "expression_matched_cases") -> Path:
    manifest = root / "standardized_data" / "tcga" / "tcga-thca" / "build" / "data_prepared" / "tcga" / "clinical" / "tcga_clinical_build_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "case_count": 2,
        "matched_case_count": 2 if mode != "project_clinical_preview_only" else 0,
        "matched_sample_count": 2 if mode != "project_clinical_preview_only" else 0,
        "survival_case_count": 1,
        "death_event_count": 1,
        "clinical_gate_status": "clinical_ready" if mode != "project_clinical_preview_only" else "clinical_partial",
        "survival_gate_status": "survival_ready_basic",
    }
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.tcga_clinical_build_manifest.v1",
                "project_id": "TCGA-THCA",
                "clinical_build_id": "clinical",
                "mode": mode,
                "summary": summary,
                "warnings": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    register_acquisition(
        root,
        source_type="tcga_project",
        source_label="TCGA-THCA",
        strategy="reference",
        selected_paths=[manifest],
        metadata={
            "source": "tcga_gdc",
            "project_id": "TCGA-THCA",
            "download_status": "tcga_clinical_metadata_built",
            "ready_for_recognition": "pending_data_check",
            "analysis_gate_status": "pending_data_check",
            "tcga_clinical_build_manifest_path": str(manifest),
            "tcga_clinical_summary": summary,
            "mode": mode,
        },
    )
    return manifest


def test_tcga_workflow_empty_project_only_allows_preview(tmp_path: Path) -> None:
    state = build_tcga_workflow_state(tmp_path, project_id="TCGA-THCA", analysis_purpose="differential_expression", sample_scope="tumor")

    assert state.step("preview").status == "available"
    assert state.step("preview").enabled is True
    assert state.step("download").status == "blocked"
    assert state.step("clinical").enabled is False
    assert state.can_enter_data_check is False
    assert "GTEx" in " ".join(state.warnings)


def test_tcga_workflow_request_and_plan_unlock_download(tmp_path: Path) -> None:
    _register_request(tmp_path)
    request_state = build_tcga_workflow_state(tmp_path, project_id="TCGA-THCA")
    assert request_state.step("preview").status == "available"

    _write_plan(tmp_path)
    state = build_tcga_workflow_state(tmp_path, project_id="TCGA-THCA")

    assert state.step("preview").status == "completed"
    assert state.step("download").status == "available"
    assert state.step("download").enabled is True


def test_tcga_workflow_download_unlocks_expression_and_failed_download_does_not(tmp_path: Path) -> None:
    _write_plan(tmp_path)
    _register_raw(tmp_path, acquired=1, failed=1, blocked=1, status="tcga_gdc_raw_files_acquired_with_warnings")
    state = build_tcga_workflow_state(tmp_path, project_id="TCGA-THCA")

    assert state.step("download").status == "completed"
    assert state.step("expression_build").status == "available"
    assert any("阻断" in warning for warning in state.warnings)

    failed_root = tmp_path / "failed"
    _write_plan(failed_root)
    _register_raw(failed_root, acquired=0, status="tcga_gdc_raw_file_download_failed")
    failed = build_tcga_workflow_state(failed_root, project_id="TCGA-THCA")
    assert failed.step("download").status == "failed"
    assert failed.step("expression_build").status == "blocked"


def test_tcga_workflow_expression_unlocks_clinical_and_data_check(tmp_path: Path) -> None:
    _register_expression(tmp_path)

    state = build_tcga_workflow_state(tmp_path, project_id="TCGA-THCA")

    assert state.step("expression_build").status == "completed"
    assert state.step("clinical").status == "available"
    assert state.step("clinical").enabled is True
    assert state.step("data_check").enabled is True
    assert state.can_enter_data_check is True


def test_tcga_workflow_clinical_completes_full_flow_and_preview_is_not_mapping_ready(tmp_path: Path) -> None:
    _register_expression(tmp_path)
    _register_clinical(tmp_path)
    state = build_tcga_workflow_state(tmp_path, project_id="TCGA-THCA")

    assert state.step("clinical").status == "completed"
    assert state.current_stage == "clinical"
    assert "basic OS" in state.step("data_check").summary

    preview_root = tmp_path / "preview"
    _register_clinical(preview_root, mode="project_clinical_preview_only")
    preview_state = build_tcga_workflow_state(preview_root, project_id="TCGA-THCA")
    assert preview_state.step("clinical").status == "skipped"
    assert "尚未完成表达-临床映射" in (preview_state.step("clinical").warning or "")


def test_tcga_workflow_prefers_highest_stage_over_old_plan(tmp_path: Path) -> None:
    _write_plan(tmp_path)
    _register_raw(tmp_path)
    _register_expression(tmp_path)
    _register_clinical(tmp_path)

    state = build_tcga_workflow_state(tmp_path, project_id="TCGA-THCA")

    assert state.developer_diagnostics["highest_stage_record"]["download_status"] == "tcga_clinical_metadata_built"
    assert state.step("download").status == "completed"
    assert state.step("expression_build").status == "completed"
    assert state.step("clinical").status == "completed"
