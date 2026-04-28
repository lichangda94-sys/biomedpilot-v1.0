"""Integration helpers for GEO search -> download -> process workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geo_pipeline import ProcessConfig, download_core_geo_records, process_from_local_family_soft
from geo_processing import (
    detect_dataset,
    handoff_recommended_strategy,
    load_module1_dataset_context,
    validate_downloaded_dataset,
)
from geo_processing.detector.models import RecommendedStrategy


@dataclass
class WorkflowConfig:
    accession: str
    base_dir: str
    gpl_gene_col: str | None = None


def run_download_and_process_workflow(config: WorkflowConfig) -> dict[str, Any]:
    base_dir = Path(config.base_dir).expanduser().resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    dataset_dir = base_dir / config.accession.upper()
    geo_dir = dataset_dir / "raw_downloads" / "geo_downloads"
    processed_dir = base_dir / f"processed_{config.accession.upper()}"

    download_result = download_core_geo_records(config.accession, str(dataset_dir))
    if download_result["status"] != "success":
        raise RuntimeError(download_result.get("note") or download_result.get("error") or "GEO download failed")

    validation_result = validate_downloaded_dataset(config.accession, str(dataset_dir))
    validation_payload = validation_result.to_dict()
    module1_handoff = load_module1_dataset_context(str(dataset_dir), validation_payload=validation_payload)

    detection_result = detect_dataset(config.accession, str(geo_dir))
    detection_payload = asdict(detection_result)
    family_soft_path = download_result["family_soft_path"]
    recommended_strategy = handoff_recommended_strategy(module1_handoff)
    if (
        recommended_strategy == RecommendedStrategy.MANUAL_REVIEW_REQUIRED.value
        and detection_result.recommended_strategy
    ):
        recommended_strategy = detection_result.recommended_strategy

    process_result: dict[str, Any]
    should_process_family_soft = (
        bool(family_soft_path)
        and recommended_strategy
        not in {
            RecommendedStrategy.RAW_MICROARRAY_EXTERNAL_PREPROCESS.value,
            RecommendedStrategy.RAW_RNASEQ_EXTERNAL_PREPROCESS.value,
            RecommendedStrategy.UNSUPPORTED_SINGLE_CELL.value,
            RecommendedStrategy.UNSUPPORTED_SPATIAL.value,
        }
    )

    if should_process_family_soft:
        process_result = process_from_local_family_soft(
            family_soft_path,
            ProcessConfig(
                accession=config.accession,
                outdir=str(processed_dir),
                geo_dir=str(geo_dir),
                gpl_gene_col=config.gpl_gene_col,
            ),
        )
    else:
        processed_dir.mkdir(parents=True, exist_ok=True)
        process_result = {
            "accession": config.accession.upper(),
            "input_source": family_soft_path,
            "outdir": str(processed_dir),
            "status": "partial_success",
            "metadata_parse_success": False,
            "expression_matrix_success": False,
            "matrix_build_success": False,
            "matrix_build_skipped": True,
            "matrix_build_failed": False,
            "expression_matrix_error": detection_result.failure_reason,
            "metadata_error": None,
            "group_column_guess": None,
            "probe_log2_applied": False,
            "annotation_performed": False,
            "gene_level_generated": False,
            "next_action": module1_handoff.get("dataset_manifest_draft", {}).get("module1_state", {}).get("current_state")
            or detection_result.next_action,
        }

    workflow_status = (
        "success"
        if process_result.get("status") == "success"
        else "partial_success"
    )

    return {
        "status": workflow_status,
        "accession": config.accession.upper(),
        "base_dir": str(base_dir),
        "download_result": download_result,
        "validation_result": validation_payload,
        "detection_result": detection_payload,
        "module1_handoff": module1_handoff,
        "process_result": process_result,
        "family_soft_path": family_soft_path,
        "processed_dir": str(processed_dir),
        "run_summary_path": str(processed_dir / "run_summary.json"),
        "download_success": download_result.get("download_success", download_result.get("full_download_success", False)),
        "metadata_parse_success": process_result.get("metadata_parse_success", False),
        "expression_matrix_success": process_result.get("expression_matrix_success", False),
        "matrix_build_success": process_result.get("matrix_build_success", False),
        "matrix_build_skipped": process_result.get("matrix_build_skipped", False),
        "matrix_build_failed": process_result.get("matrix_build_failed", False),
        "expression_matrix_error": process_result.get("expression_matrix_error"),
    }
