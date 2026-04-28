"""Structured output contracts for Module 1 (retrieval and data ingress)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .module3_assets import build_standard_asset_layout


SEARCH_RESULT_SCHEMA_VERSION = "module1.search_result.v1"
DOWNLOAD_PLAN_SCHEMA_VERSION = "module1.download_plan.v1"
DOWNLOAD_RECEIPT_SCHEMA_VERSION = "module1.download_receipt.v1"
FILE_INVENTORY_SCHEMA_VERSION = "module1.file_inventory.v1"
PARSER_HINTS_SCHEMA_VERSION = "module1.parser_hints.v1"
DATASET_MANIFEST_DRAFT_SCHEMA_VERSION = "module1.dataset_manifest_draft.v1"
HANDOFF_PACKAGE_SCHEMA_VERSION = "module1.handoff.v1"


LEGACY_VALIDATION_TO_MODULE1_STATE = {
    "ANALYSIS_READY": "handoff_ready",
    "PARTIAL_BUT_USABLE": "partial_success",
    "EXPRESSION_ONLY": "classified",
    "METADATA_ONLY": "classified",
    "RAW_ONLY": "classified",
    "NO_EXPRESSION_PAYLOAD": "classified",
    "EMPTY_OR_BROKEN": "failed",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Unsupported contract value: {type(value)!r}")


def _stable_file_id(dataset_id: str, relative_or_name: str) -> str:
    digest = hashlib.sha1(f"{dataset_id}:{relative_or_name}".encode("utf-8")).hexdigest()[:12]
    return f"{dataset_id}:{digest}"


def infer_search_result_confidence(item: dict[str, Any]) -> float:
    score = 0.3
    if item.get("title_en") or item.get("title_zh"):
        score += 0.2
    if item.get("summary_en") or item.get("summary_zh") or item.get("overall_design_en") or item.get("overall_design_zh"):
        score += 0.2
    if item.get("organism"):
        score += 0.1
    if item.get("platform"):
        score += 0.1
    if item.get("experiment_type"):
        score += 0.1
    return round(min(score, 0.95), 3)


def build_search_result_item(info: Any) -> dict[str, Any]:
    item = _to_dict(info)
    dataset_id = str(item.get("gse_id") or item.get("dataset_id") or "").strip()
    summary = (
        item.get("summary_zh")
        or item.get("summary_en")
        or item.get("overall_design_zh")
        or item.get("overall_design_en")
        or ""
    )
    assay_type = str(item.get("experiment_type") or item.get("assay_type") or "").strip() or "unknown"
    preview_text = summary or item.get("title_zh") or item.get("title_en") or ""
    preview_available = bool(preview_text.strip())
    return {
        "schema_version": SEARCH_RESULT_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "source_db": "geo",
        "title": str(item.get("title_zh") or item.get("title_en") or dataset_id),
        "summary": str(summary).strip(),
        "organism": str(item.get("organism") or "").strip() or "unknown",
        "platform": str(item.get("platform") or "").strip() or "unknown",
        "assay_type": assay_type,
        "candidate_files": [],
        "recommended_strategy": "MANUAL_REVIEW_REQUIRED",
        "confidence": infer_search_result_confidence(item),
        "preview_available": preview_available,
        "preview": str(preview_text).strip(),
        "sample_count": int(item.get("sample_count") or 0),
        "source_url": str(item.get("geo_url") or "").strip(),
        "legacy": item,
    }


def build_search_results_payload(items: list[Any], *, query: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": SEARCH_RESULT_SCHEMA_VERSION,
        "query": query or "",
        "items": [build_search_result_item(item) for item in items],
        "generated_at": _utc_now_iso(),
    }


def derive_module1_state(
    *,
    has_candidates: bool = False,
    has_plan: bool = False,
    has_downloaded_files: bool = False,
    has_validation: bool = False,
    has_classification: bool = False,
    handoff_ready: bool = False,
    failed: bool = False,
    legacy_status: str | None = None,
) -> dict[str, Any]:
    if legacy_status and legacy_status in LEGACY_VALIDATION_TO_MODULE1_STATE:
        current = LEGACY_VALIDATION_TO_MODULE1_STATE[legacy_status]
    elif failed:
        current = "failed"
    elif handoff_ready:
        current = "handoff_ready"
    elif has_classification:
        current = "classified"
    elif has_validation:
        current = "validated"
    elif has_downloaded_files:
        current = "downloaded"
    elif has_plan:
        current = "planned"
    elif has_candidates:
        current = "discovered"
    else:
        current = "failed" if failed else "discovered"

    history: list[str] = []
    if has_candidates:
        history.append("discovered")
    if has_plan:
        history.append("planned")
    if has_downloaded_files:
        history.append("downloaded")
    if has_validation:
        history.append("validated")
    if has_classification:
        history.append("classified")
    if handoff_ready:
        history.append("handoff_ready")
    if current == "partial_success":
        history.append("partial_success")
    if current == "failed":
        history.append("failed")

    return {
        "current_state": current,
        "state_history": history,
        "legacy_status": legacy_status,
        "generated_at": _utc_now_iso(),
    }


def build_download_plan_payload(
    dataset_id: str,
    dataset_root: str,
    plan_items: list[dict[str, Any]],
    *,
    source_db: str = "geo",
) -> dict[str, Any]:
    state = derive_module1_state(has_candidates=bool(plan_items), has_plan=bool(plan_items))
    return {
        "schema_version": DOWNLOAD_PLAN_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "source_db": source_db,
        "dataset_root": str(Path(dataset_root).expanduser().resolve()),
        "state": state,
        "generated_at": _utc_now_iso(),
        "plan": plan_items,
    }


def _normalize_detected_type(file_name: str, guessed_role: str | None) -> str:
    lowered = file_name.lower()
    role = (guessed_role or "").strip() or "unknown"
    if lowered.endswith(".xlsx"):
        return "xlsx"
    if lowered.endswith(".xls"):
        return "xls"
    if lowered.endswith(".csv.gz"):
        return "csv.gz"
    if lowered.endswith(".tsv.gz"):
        return "tsv.gz"
    if lowered.endswith(".txt.gz") or lowered.endswith(".soft.gz"):
        return "gz_text"
    if lowered.endswith(".csv"):
        return "csv"
    if lowered.endswith(".tsv"):
        return "tsv"
    if lowered.endswith(".txt") or lowered.endswith(".soft"):
        return "text"
    if lowered.endswith(".tgz") or lowered.endswith(".tar.gz") or lowered.endswith(".tar") or lowered.endswith(".zip"):
        return "archive"
    return role


def build_download_receipt_item(entry: dict[str, Any], dataset_id: str) -> dict[str, Any]:
    local_path = str(entry.get("final_saved_path") or "")
    file_name = Path(local_path).name or str(entry.get("file_name") or entry.get("source_accession") or "unknown")
    status_map = {
        "success": "downloaded",
        "recorded_only": "partial_success",
        "failed": "failed",
    }
    response_status = str(entry.get("response_status") or "failed")
    return {
        "file_id": _stable_file_id(dataset_id, file_name or local_path),
        "file_name": file_name,
        "source_url": entry.get("remote_url"),
        "local_path": local_path or None,
        "size": int(entry.get("final_size_on_disk") or entry.get("file_size_on_disk") or 0),
        "detected_type": _normalize_detected_type(file_name, entry.get("guessed_role")),
        "status": status_map.get(response_status, "failed"),
        "error_message": entry.get("error_message"),
        "timestamp": datetime.fromtimestamp(
            float(entry.get("request_finished_at") or entry.get("request_started_at") or 0),
            tz=timezone.utc,
        ).replace(microsecond=0).isoformat()
        if entry.get("request_finished_at") or entry.get("request_started_at")
        else _utc_now_iso(),
        "source_level": entry.get("source_level"),
        "source_accession": entry.get("source_accession"),
        "guessed_role": entry.get("guessed_role"),
        "response_status": response_status,
    }


def build_download_receipt_payload(
    dataset_id: str,
    dataset_root: str,
    transaction_log: list[dict[str, Any]],
    *,
    source_db: str = "geo",
    legacy_status: str | None = None,
) -> dict[str, Any]:
    items = [build_download_receipt_item(entry, dataset_id) for entry in transaction_log]
    has_downloaded = any(item["status"] == "downloaded" for item in items)
    state = derive_module1_state(
        has_candidates=bool(items),
        has_plan=bool(items),
        has_downloaded_files=has_downloaded,
        failed=not has_downloaded,
        legacy_status=legacy_status,
    )
    return {
        "schema_version": DOWNLOAD_RECEIPT_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "source_db": source_db,
        "dataset_root": str(Path(dataset_root).expanduser().resolve()),
        "state": state,
        "generated_at": _utc_now_iso(),
        "files": items,
    }


def normalize_file_role(score_payload: dict[str, Any]) -> str:
    primary = str(score_payload.get("primary_label") or score_payload.get("file_role") or "").strip()
    relative_path = str(score_payload.get("relative_path") or score_payload.get("path") or "").lower()
    preview_text = "\n".join(score_payload.get("preview_lines") or []).lower()
    secondary = {str(item) for item in score_payload.get("secondary_labels", [])}
    if any(token in relative_path for token in ("mutation", ".maf", ".vcf", ".vcf.gz", "variant")):
        return "mutation_candidate"
    if primary == "expression_payload" or "expression_candidate" in secondary:
        return "expression_candidate"
    if primary == "sample_annotation":
        return "metadata_candidate"
    if primary == "platform_annotation":
        return "feature_annotation_candidate"
    if primary == "clinical_annotation" or any(token in relative_path for token in ("clinical", "survival", "stage", "grade", "outcome")):
        return "clinical_candidate"
    if any(token in preview_text for token in ("survival", "stage", "grade", "pathology", "response")):
        return "clinical_candidate"
    if primary == "archive":
        return "archive"
    return "unknown"


def infer_value_type_hint(score_payload: dict[str, Any], *, dataset_value_semantic: str | None = None) -> str:
    relative_path = str(score_payload.get("relative_path") or "").lower()
    if "tpm" in relative_path:
        return "TPM"
    if "fpkm" in relative_path or "rpkm" in relative_path:
        return "TPM"
    if "count" in relative_path:
        return "count"
    if dataset_value_semantic == "raw_counts":
        return "count"
    if dataset_value_semantic == "normalized_counts":
        return "normalized_count"
    if dataset_value_semantic == "intensity":
        return "microarray intensity"
    if dataset_value_semantic == "log2_expression":
        return "log2 expression"
    return "unknown"


def build_file_inventory_payload(
    dataset_id: str,
    dataset_root: str,
    file_scores: list[dict[str, Any]],
    *,
    source_db: str = "geo",
    dataset_value_semantic: str | None = None,
    legacy_status: str | None = None,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for score in file_scores:
        relative_path = str(score.get("relative_path") or Path(str(score.get("path") or "")).name)
        file_name = Path(relative_path).name
        local_path = str(Path(dataset_root).expanduser().resolve() / relative_path)
        items.append(
            {
                "file_id": _stable_file_id(dataset_id, relative_path),
                "file_name": file_name,
                "relative_path": relative_path,
                "local_path": local_path,
                "size": int(score.get("size_bytes") or 0),
                "detected_type": _normalize_detected_type(file_name, score.get("primary_label")),
                "status": "validated" if not score.get("excluded") else "failed",
                "error_message": score.get("excluded_reason"),
                "timestamp": _utc_now_iso(),
                "file_role": normalize_file_role(score),
                "confidence": float(score.get("confidence") or 0.0),
                "primary_label": score.get("primary_label"),
                "secondary_labels": list(score.get("secondary_labels") or []),
                "value_type_hint": infer_value_type_hint(score, dataset_value_semantic=dataset_value_semantic),
                "preview_available": bool(score.get("preview_lines")),
                "organized_targets": list(score.get("organized_targets") or []),
                "source_level": score.get("source_level"),
                "source_path": score.get("source_path"),
            }
        )
    state = derive_module1_state(
        has_downloaded_files=bool(items),
        has_validation=True,
        has_classification=True,
        legacy_status=legacy_status,
        failed=not bool(items),
    )
    return {
        "schema_version": FILE_INVENTORY_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "source_db": source_db,
        "dataset_root": str(Path(dataset_root).expanduser().resolve()),
        "state": state,
        "generated_at": _utc_now_iso(),
        "files": items,
    }


def _pick_preferred_asset(files: list[dict[str, Any]], role: str) -> dict[str, Any] | None:
    candidates = [item for item in files if item.get("file_role") == role]
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            float(item.get("confidence") or 0.0),
            1 if item.get("preview_available") else 0,
            1 if item.get("status") == "validated" else 0,
            -len(str(item.get("relative_path") or item.get("file_name") or "")),
        ),
        reverse=True,
    )
    return candidates[0]


def _asset_role_counts(files: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "expression_candidate": 0,
        "metadata_candidate": 0,
        "feature_annotation_candidate": 0,
        "clinical_candidate": 0,
        "mutation_candidate": 0,
        "archive": 0,
        "unknown": 0,
    }
    for item in files:
        role = str(item.get("file_role") or "unknown")
        counts[role] = counts.get(role, 0) + 1
    return counts


def _available_capabilities(manifest_draft: dict[str, Any], parser_hints: dict[str, Any], role_counts: dict[str, int]) -> list[str]:
    capabilities: list[str] = []
    if manifest_draft.get("has_expression_payload"):
        capabilities.append("expression_matrix_available")
    if manifest_draft.get("has_sample_annotation"):
        capabilities.append("sample_annotation_available")
    if manifest_draft.get("has_clinical_info"):
        capabilities.append("clinical_available")
    if manifest_draft.get("has_mutation_info"):
        capabilities.append("mutation_available")
    if manifest_draft.get("has_batch_info"):
        capabilities.append("batch_hint_available")
    if role_counts.get("feature_annotation_candidate", 0):
        capabilities.append("feature_annotation_available")
    if role_counts.get("archive", 0):
        capabilities.append("archive_available")
    if parser_hints.get("may_generate_expression_gene"):
        capabilities.append("expression_gene_possible")
    if parser_hints.get("may_generate_sample_annotation"):
        capabilities.append("sample_annotation_possible")
    return capabilities


def _missing_required_assets(manifest_draft: dict[str, Any], parser_hints: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not manifest_draft.get("has_expression_payload"):
        missing.append("expression_asset")
    if not manifest_draft.get("has_sample_annotation") and parser_hints.get("may_generate_expression_gene"):
        missing.append("metadata_asset")
    return missing


def _warnings_summary(validation_payload: dict[str, Any], files: list[dict[str, Any]], missing_assets: list[str]) -> list[str]:
    warnings: list[str] = []
    for item in validation_payload.get("warnings", [])[:5]:
        if item not in warnings:
            warnings.append(str(item))
    if missing_assets:
        warnings.append(f"missing_required_assets: {', '.join(missing_assets)}")
    if len([item for item in files if item.get("file_role") == "expression_candidate"]) > 1:
        warnings.append("multiple_expression_candidates_detected")
    return warnings


def infer_recommended_strategy(validation_payload: dict[str, Any]) -> str:
    expression_sources = [str(item) for item in validation_payload.get("expression_sources", [])]
    if validation_payload.get("has_expression_payload"):
        if any("series_matrix" in item.lower() for item in expression_sources):
            return "SERIES_MATRIX_FIRST"
        if validation_payload.get("has_family_soft"):
            return "SOFT_METADATA_PLUS_SUPP_MATRIX"
        return "SUPPLEMENTARY_MATRIX_FIRST"
    if validation_payload.get("payload_type") == "raw_only":
        if validation_payload.get("platform_annotation_files") or validation_payload.get("has_platform_hint"):
            return "RAW_MICROARRAY_EXTERNAL_PREPROCESS"
        return "RAW_RNASEQ_EXTERNAL_PREPROCESS"
    if validation_payload.get("payload_type") in {"metadata_only", "annotation_only", "sample_id_only", "diff_result_only"}:
        return "METADATA_ONLY"
    return "MANUAL_REVIEW_REQUIRED"


def _batch_info_present(file_scores: list[dict[str, Any]]) -> bool:
    haystack = "\n".join(
        " ".join(
            [
                str(item.get("relative_path") or ""),
                " ".join(item.get("preview_lines") or []),
                json.dumps(item.get("extra") or {}, ensure_ascii=False),
            ]
        )
        for item in file_scores
    ).lower()
    return "batch" in haystack


def build_parser_hints_payload(validation_payload: dict[str, Any]) -> dict[str, Any]:
    dataset_id = str(validation_payload.get("gse_id") or validation_payload.get("dataset_id") or "")
    file_scores = list(validation_payload.get("extra", {}).get("file_scores", []))
    file_inventory = build_file_inventory_payload(
        dataset_id,
        validation_payload.get("download_dir") or validation_payload.get("dataset_root") or ".",
        file_scores,
        legacy_status=validation_payload.get("status"),
    )
    matrix_items = [item for item in file_inventory["files"] if item["file_role"] == "expression_candidate"]
    metadata_items = [item for item in file_inventory["files"] if item["file_role"] == "metadata_candidate"]
    clinical_items = [item for item in file_inventory["files"] if item["file_role"] == "clinical_candidate"]
    feature_items = [item for item in file_inventory["files"] if item["file_role"] == "feature_annotation_candidate"]
    mutation_items = [item for item in file_inventory["files"] if item["file_role"] == "mutation_candidate"]
    recommended_strategy = infer_recommended_strategy(validation_payload)
    default_value_hint = "unknown"
    for item in matrix_items:
        if item["value_type_hint"] != "unknown":
            default_value_hint = item["value_type_hint"]
            break
    return {
        "schema_version": PARSER_HINTS_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "state": derive_module1_state(
            has_downloaded_files=bool(file_scores),
            has_validation=True,
            has_classification=True,
            legacy_status=validation_payload.get("status"),
            failed=validation_payload.get("status") == "EMPTY_OR_BROKEN",
        ),
        "generated_at": _utc_now_iso(),
        "recommended_strategy": recommended_strategy,
        "default_value_type_hint": default_value_hint,
        "matrix_candidates": matrix_items,
        "metadata_candidates": metadata_items,
        "feature_annotation_candidates": feature_items,
        "clinical_candidates": clinical_items,
        "mutation_candidates": mutation_items,
        "may_generate_expression_gene": bool(matrix_items),
        "may_generate_sample_annotation": bool(metadata_items or validation_payload.get("has_family_soft")),
        "has_clinical_info": bool(clinical_items or validation_payload.get("has_clinical_annotation")),
        "has_mutation_info": bool(mutation_items),
        "has_batch_info": _batch_info_present(file_scores),
    }


def build_dataset_manifest_draft_payload(validation_payload: dict[str, Any]) -> dict[str, Any]:
    dataset_id = str(validation_payload.get("gse_id") or validation_payload.get("dataset_id") or "")
    parser_hints = build_parser_hints_payload(validation_payload)
    file_inventory = build_file_inventory_payload(
        dataset_id,
        validation_payload.get("download_dir") or validation_payload.get("dataset_root") or ".",
        list(validation_payload.get("extra", {}).get("file_scores", [])),
        legacy_status=validation_payload.get("status"),
    )
    expression_files = [item["relative_path"] for item in file_inventory["files"] if item["file_role"] == "expression_candidate"]
    metadata_files = [item["relative_path"] for item in file_inventory["files"] if item["file_role"] == "metadata_candidate"]
    clinical_files = [item["relative_path"] for item in file_inventory["files"] if item["file_role"] == "clinical_candidate"]
    mutation_files = [item["relative_path"] for item in file_inventory["files"] if item["file_role"] == "mutation_candidate"]
    value_hint = parser_hints["default_value_type_hint"]
    handoff_ready = bool(expression_files or metadata_files or clinical_files or mutation_files)
    return {
        "schema_version": DATASET_MANIFEST_DRAFT_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "source_db": "geo",
        "dataset_root": validation_payload.get("download_dir"),
        "title": dataset_id,
        "status": validation_payload.get("status"),
        "module1_state": derive_module1_state(
            has_downloaded_files=bool(file_inventory["files"]),
            has_validation=True,
            has_classification=True,
            handoff_ready=handoff_ready,
            legacy_status=validation_payload.get("status"),
            failed=validation_payload.get("status") == "EMPTY_OR_BROKEN",
        ),
        "generated_at": _utc_now_iso(),
        "recommended_strategy": parser_hints["recommended_strategy"],
        "value_type_hint": value_hint,
        "has_expression_payload": bool(expression_files),
        "has_sample_annotation": bool(metadata_files or validation_payload.get("has_family_soft")),
        "has_clinical_info": bool(clinical_files),
        "has_mutation_info": bool(mutation_files),
        "has_batch_info": parser_hints["has_batch_info"],
        "expression_candidate_files": expression_files,
        "sample_annotation_candidate_files": metadata_files,
        "clinical_candidate_files": clinical_files,
        "mutation_candidate_files": mutation_files,
        "platform_annotation_files": list(validation_payload.get("platform_annotation_files", [])),
        "archive_files": list(validation_payload.get("archive_files", [])),
        "supporting_files": list(validation_payload.get("supporting_files", [])),
        "external_sources": list(validation_payload.get("external_sources", [])),
    }


def build_handoff_package_payload(validation_payload: dict[str, Any]) -> dict[str, Any]:
    dataset_id = str(validation_payload.get("gse_id") or validation_payload.get("dataset_id") or "")
    dataset_root = validation_payload.get("download_dir") or validation_payload.get("dataset_root") or "."
    manifest_draft = build_dataset_manifest_draft_payload(validation_payload)
    file_inventory = build_file_inventory_payload(
        dataset_id,
        dataset_root,
        list(validation_payload.get("extra", {}).get("file_scores", [])),
        legacy_status=validation_payload.get("status"),
    )
    parser_hints = build_parser_hints_payload(validation_payload)
    role_counts = _asset_role_counts(file_inventory["files"])
    preferred_expression_asset = _pick_preferred_asset(file_inventory["files"], "expression_candidate")
    preferred_metadata_asset = _pick_preferred_asset(file_inventory["files"], "metadata_candidate")
    preferred_feature_annotation_asset = _pick_preferred_asset(file_inventory["files"], "feature_annotation_candidate")
    preferred_clinical_asset = _pick_preferred_asset(file_inventory["files"], "clinical_candidate")
    preferred_mutation_asset = _pick_preferred_asset(file_inventory["files"], "mutation_candidate")
    missing_required_assets = _missing_required_assets(manifest_draft, parser_hints)
    warnings_summary = _warnings_summary(validation_payload, file_inventory["files"], missing_required_assets)
    available_capabilities = _available_capabilities(manifest_draft, parser_hints, role_counts)
    handoff = {
        "schema_version": HANDOFF_PACKAGE_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "generated_at": _utc_now_iso(),
        "module1_state": manifest_draft["module1_state"],
        "recommended_strategy": manifest_draft["recommended_strategy"],
        "value_type_hint": manifest_draft["value_type_hint"],
        "dataset_info": {
            "dataset_id": dataset_id,
            "source_db": "geo",
            "legacy_status": validation_payload.get("status"),
            "download_dir": validation_payload.get("download_dir"),
            "recommended_strategy": manifest_draft["recommended_strategy"],
            "value_type_hint": manifest_draft["value_type_hint"],
        },
        "file_inventory": file_inventory["files"],
        "file_roles": {item["relative_path"]: item["file_role"] for item in file_inventory["files"]},
        "preferred_expression_asset": preferred_expression_asset,
        "preferred_metadata_asset": preferred_metadata_asset,
        "preferred_feature_annotation_asset": preferred_feature_annotation_asset,
        "preferred_clinical_asset": preferred_clinical_asset,
        "preferred_mutation_asset": preferred_mutation_asset,
        "asset_role_counts": role_counts,
        "available_capabilities": available_capabilities,
        "warnings_summary": warnings_summary,
        "missing_required_assets": missing_required_assets,
        "parser_hints": parser_hints,
        "dataset_manifest_draft": manifest_draft,
        "supporting_contracts": {
            "file_inventory": "organized/reports/file_inventory.json",
            "parser_hints": "organized/reports/parser_hints.json",
            "dataset_manifest_draft": "organized/reports/dataset_manifest_draft.json",
        },
        "may_generate_expression_gene": parser_hints["may_generate_expression_gene"],
        "may_generate_sample_annotation": parser_hints["may_generate_sample_annotation"],
        "has_clinical_info": parser_hints["has_clinical_info"],
        "has_mutation_info": parser_hints["has_mutation_info"],
        "has_batch_info": parser_hints["has_batch_info"],
    }
    handoff.update(build_standard_asset_layout(dataset_root, handoff=handoff))
    return handoff
