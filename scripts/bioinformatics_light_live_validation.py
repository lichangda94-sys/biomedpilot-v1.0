from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.bioinformatics.data_sources.gtex_download_executor import GTExDownloadPlanExecutor
from app.bioinformatics.data_sources.gtex_expression_builder import GTExExpressionMatrixBuilder
from app.bioinformatics.data_sources.gtex_preview import GTExMetadataPreviewService, build_gtex_preview_request, write_gtex_download_plan_draft
from app.bioinformatics.data_sources.gtex_workflow import build_gtex_workflow_state
from app.bioinformatics.data_sources.tcga_clinical_builder import TCGAClinicalMetadataBuilder
from app.bioinformatics.data_sources.tcga_download_executor import TCGADownloadPlanExecutor
from app.bioinformatics.data_sources.tcga_expression_builder import TCGAExpressionQuantificationBuilder
from app.bioinformatics.data_sources.tcga_preview import TCGAMetadataPreviewService, build_tcga_preview_request, write_tcga_download_plan_draft
from app.bioinformatics.data_sources.tcga_workflow import build_tcga_workflow_state
from app.bioinformatics.gtex_tissue_registry import get_gtex_tissue, get_gtex_use_purpose
from app.bioinformatics.project_readiness import run_project_readiness
from app.bioinformatics.tcga_project_registry import get_tcga_analysis_purpose, get_tcga_project, get_tcga_sample_scope


def main() -> None:
    _set_default_env()
    run_root = REPO_ROOT / "project_storage" / "bioinformatics" / "validation_runs" / f"b6v_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_root.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "schema_version": "biomedpilot.b6v_light_live_validation.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project_root": str(run_root),
        "environment": {key: os.environ.get(key, "") for key in _ENV_KEYS},
        "tcga": {},
        "gtex": {},
        "readiness": {},
        "scoped_regression": {},
        "errors": [],
    }
    result["tcga"] = _run_tcga(run_root)
    result["gtex"] = _run_gtex(run_root)
    try:
        readiness = run_project_readiness(run_root)
        report = readiness.get("readiness_report") if isinstance(readiness, dict) else {}
        matrix = readiness.get("capability_matrix") if isinstance(readiness, dict) else {}
        result["readiness"] = {
            "overall_status": report.get("overall_status") if isinstance(report, dict) else "",
            "validation_limited": report.get("validation_limited") if isinstance(report, dict) else False,
            "available_inputs": report.get("available_inputs", []) if isinstance(report, dict) else [],
            "warnings": report.get("warnings", []) if isinstance(report, dict) else [],
            "blocked_analysis_rows": [
                row.get("analysis_type")
                for row in matrix.get("rows", [])
                if isinstance(row, dict) and not row.get("can_run")
            ]
            if isinstance(matrix, dict)
            else [],
        }
    except Exception as exc:
        result["errors"].append({"stage": "readiness", "message": str(exc)})
    output_path = run_root / "b6v_light_live_validation_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
    print(output_path)


def _run_tcga(root: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {"project_id": "TCGA-CHOL", "analysis_purpose": "expression_clinical", "sample_scope": "tumor"}
    try:
        request = build_tcga_preview_request(
            project=get_tcga_project("TCGA-CHOL"),
            purpose=get_tcga_analysis_purpose("expression_clinical"),
            scope=get_tcga_sample_scope("tumor"),
        )
        preview = TCGAMetadataPreviewService(page_size=500).build_preview(request, timeout=30)
        plan = write_tcga_download_plan_draft(root, preview)
        payload["preview"] = _preview_summary(preview.to_dict())
        payload["plan_path"] = str(plan.plan_path)
        payload["workflow_before_download"] = build_tcga_workflow_state(root, project_id="TCGA-CHOL").to_dict()
        download = TCGADownloadPlanExecutor().execute_plan(root, plan_path=plan.plan_path, timeout=30)
        payload["download"] = download.to_dict()
        if download.downloaded_files:
            build = TCGAExpressionQuantificationBuilder().build_latest(root, project_id="TCGA-CHOL")
            payload["expression_build"] = build.to_dict()
            try:
                clinical = TCGAClinicalMetadataBuilder().build_for_latest_expression_build(root, timeout=30, project_id="TCGA-CHOL")
                payload["clinical"] = clinical.to_dict()
            except Exception as exc:
                payload["clinical_error"] = str(exc)
        payload["workflow_after_build"] = build_tcga_workflow_state(root, project_id="TCGA-CHOL").to_dict()
        payload["scoped_uvm_before_plan"] = build_tcga_workflow_state(root, project_id="TCGA-UVM").to_dict()
        uvm_request = build_tcga_preview_request(
            project=get_tcga_project("TCGA-UVM"),
            purpose=get_tcga_analysis_purpose("expression_clinical"),
            scope=get_tcga_sample_scope("tumor"),
        )
        uvm_preview = TCGAMetadataPreviewService(page_size=500).build_preview(uvm_request, timeout=30)
        uvm_plan = write_tcga_download_plan_draft(root, uvm_preview)
        payload["uvm_preview"] = _preview_summary(uvm_preview.to_dict())
        payload["uvm_plan_path"] = str(uvm_plan.plan_path)
        payload["scoped_uvm_after_plan"] = build_tcga_workflow_state(root, project_id="TCGA-UVM").to_dict()
        payload["scoped_chol_after_uvm"] = build_tcga_workflow_state(root, project_id="TCGA-CHOL").to_dict()
    except Exception as exc:
        payload["error"] = str(exc)
    return payload


def _run_gtex(root: Path) -> dict[str, Any]:
    payload: dict[str, Any] = {"tissue_id": "gtex_minor_salivary_gland", "tissue": "Minor Salivary Gland", "use_purpose": "download_tissue_matrix"}
    try:
        request = build_gtex_preview_request(
            tissue=get_gtex_tissue("gtex_minor_salivary_gland"),
            purpose=get_gtex_use_purpose("download_tissue_matrix"),
        )
        preview = GTExMetadataPreviewService().build_preview(request, timeout=30)
        plan = write_gtex_download_plan_draft(root, preview)
        payload["preview"] = _preview_summary(preview.to_dict())
        payload["plan_path"] = str(plan.plan_path)
        payload["workflow_before_download"] = build_gtex_workflow_state(root, tissue_id="gtex_minor_salivary_gland", use_purpose="download_tissue_matrix").to_dict()
        download = GTExDownloadPlanExecutor().execute_plan(root, plan_path=plan.plan_path)
        payload["download"] = download.to_dict()
        if download.downloaded_files:
            build = GTExExpressionMatrixBuilder().build_latest(root, tissue_id="gtex_minor_salivary_gland")
            payload["expression_build"] = build.to_dict()
        payload["workflow_after_build"] = build_gtex_workflow_state(root, tissue_id="gtex_minor_salivary_gland", use_purpose="download_tissue_matrix").to_dict()
        payload["scoped_fallopian_before_plan"] = build_gtex_workflow_state(root, tissue_id="gtex_fallopian_tube", use_purpose="download_tissue_matrix").to_dict()
        other_request = build_gtex_preview_request(
            tissue=get_gtex_tissue("gtex_fallopian_tube"),
            purpose=get_gtex_use_purpose("download_tissue_matrix"),
        )
        other_preview = GTExMetadataPreviewService().build_preview(other_request, timeout=30)
        other_plan = write_gtex_download_plan_draft(root, other_preview)
        payload["fallopian_preview"] = _preview_summary(other_preview.to_dict())
        payload["fallopian_plan_path"] = str(other_plan.plan_path)
        payload["scoped_fallopian_after_plan"] = build_gtex_workflow_state(root, tissue_id="gtex_fallopian_tube", use_purpose="download_tissue_matrix").to_dict()
        payload["scoped_salivary_after_fallopian"] = build_gtex_workflow_state(root, tissue_id="gtex_minor_salivary_gland", use_purpose="download_tissue_matrix").to_dict()
    except Exception as exc:
        payload["error"] = str(exc)
    return payload


def _preview_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": payload.get("status"),
        "case_count": payload.get("case_count"),
        "sample_count": payload.get("sample_count"),
        "donor_count": payload.get("donor_count"),
        "file_count": payload.get("file_count"),
        "estimated_size_bytes": payload.get("estimated_size_bytes"),
        "warnings": payload.get("warnings", []),
    }


def _set_default_env() -> None:
    defaults = {
        "BIOINF_LIGHT_VALIDATION_MODE": "1",
        "BIOINF_TCGA_DOWNLOAD_LIMIT_FILES": "2",
        "BIOINF_GTEX_DOWNLOAD_LIMIT_FILES": "1",
        "BIOINF_GTEX_LIMIT_SAMPLES": "3",
        "BIOINF_GTEX_LIMIT_GENES": "3",
    }
    for key, value in defaults.items():
        os.environ.setdefault(key, value)


def _json_default(value: object) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)


_ENV_KEYS = (
    "BIOINF_LIGHT_VALIDATION_MODE",
    "BIOINF_TCGA_DOWNLOAD_LIMIT_FILES",
    "BIOINF_GTEX_DOWNLOAD_LIMIT_FILES",
    "BIOINF_GTEX_LIMIT_SAMPLES",
    "BIOINF_GTEX_LIMIT_GENES",
)


if __name__ == "__main__":
    main()
