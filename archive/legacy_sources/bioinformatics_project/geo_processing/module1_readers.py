"""Shared readers and adapters for Module 1 contract consumption."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .module1_contracts import (
    DATASET_MANIFEST_DRAFT_SCHEMA_VERSION,
    DOWNLOAD_PLAN_SCHEMA_VERSION,
    DOWNLOAD_RECEIPT_SCHEMA_VERSION,
    FILE_INVENTORY_SCHEMA_VERSION,
    HANDOFF_PACKAGE_SCHEMA_VERSION,
    PARSER_HINTS_SCHEMA_VERSION,
    SEARCH_RESULT_SCHEMA_VERSION,
    build_dataset_manifest_draft_payload,
    build_download_receipt_payload,
    build_file_inventory_payload,
    build_handoff_package_payload,
    build_parser_hints_payload,
    build_search_result_item,
)
from .module3_assets import build_standard_asset_layout, merge_standard_asset_layout


def _first_text(*values: Any, default: str = "", skip: set[str] | None = None) -> str:
    skip = skip or set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text not in skip:
            return text
    return default


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _load_json_file(path: str | Path) -> Any:
    resolved = Path(path).expanduser().resolve()
    return json.loads(resolved.read_text(encoding="utf-8"))


def _maybe_load(source: str | Path | dict[str, Any] | list[Any]) -> Any:
    if isinstance(source, (str, Path)):
        return _load_json_file(source)
    return source


def read_search_result_item(source: dict[str, Any]) -> dict[str, Any]:
    item = dict(source)
    if item.get("schema_version") == SEARCH_RESULT_SCHEMA_VERSION and item.get("dataset_id"):
        normalized = dict(item)
    else:
        normalized = build_search_result_item(item)

    dataset_id = str(normalized.get("dataset_id") or item.get("gse_id") or item.get("dataset_id") or "").strip()
    normalized.setdefault("dataset_id", dataset_id)
    normalized.setdefault("gse_id", dataset_id)
    normalized.setdefault("source_db", "geo")
    normalized.setdefault("title", str(item.get("title_zh") or item.get("title_en") or normalized.get("title") or dataset_id))
    normalized.setdefault("summary", str(item.get("summary_zh") or item.get("summary_en") or item.get("overall_design_zh") or item.get("overall_design_en") or ""))
    normalized.setdefault("organism", str(item.get("organism") or normalized.get("organism") or "unknown"))
    normalized.setdefault("platform", str(item.get("platform") or normalized.get("platform") or "unknown"))
    normalized.setdefault("assay_type", str(item.get("experiment_type") or item.get("assay_type") or normalized.get("assay_type") or "unknown"))
    normalized.setdefault("preview_available", bool(normalized.get("summary") or item.get("summary_zh") or item.get("summary_en")))
    normalized.setdefault("candidate_files", [])
    normalized.setdefault("recommended_strategy", "MANUAL_REVIEW_REQUIRED")
    normalized["title_en"] = str(item.get("title_en") or normalized.get("legacy", {}).get("title_en") or normalized.get("title") or "")
    normalized["title_zh"] = str(item.get("title_zh") or normalized.get("legacy", {}).get("title_zh") or "")
    normalized["summary_en"] = str(item.get("summary_en") or normalized.get("legacy", {}).get("summary_en") or "")
    normalized["summary_zh"] = str(item.get("summary_zh") or normalized.get("legacy", {}).get("summary_zh") or "")
    normalized["overall_design_en"] = str(item.get("overall_design_en") or normalized.get("legacy", {}).get("overall_design_en") or "")
    normalized["overall_design_zh"] = str(item.get("overall_design_zh") or normalized.get("legacy", {}).get("overall_design_zh") or "")
    normalized["experiment_type"] = str(item.get("experiment_type") or normalized.get("assay_type") or "")
    normalized["sample_count"] = int(item.get("sample_count") or normalized.get("sample_count") or 0)
    normalized["geo_url"] = str(item.get("geo_url") or item.get("source_url") or normalized.get("source_url") or "")
    normalized["brief_zh"] = str(item.get("brief_zh") or normalized.get("legacy", {}).get("brief_zh") or "")
    return normalized


def read_selected_results(source: str | Path | dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    payload = _maybe_load(source)
    items = payload.get("items", []) if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return []
    return [read_search_result_item(item) for item in items if isinstance(item, dict)]


def read_download_plan(source: str | Path | dict[str, Any] | list[Any]) -> dict[str, Any]:
    payload = _maybe_load(source)
    if isinstance(payload, dict) and payload.get("schema_version") == DOWNLOAD_PLAN_SCHEMA_VERSION:
        return payload
    if isinstance(payload, dict):
        plan = payload.get("plan") or payload.get("items") or payload.get("candidates") or []
        dataset_id = str(payload.get("dataset_id") or payload.get("accession") or "")
        dataset_root = str(payload.get("dataset_root") or payload.get("download_dir") or payload.get("output_dir") or ".")
    elif isinstance(payload, list):
        plan = payload
        dataset_id = str(plan[0].get("accession") or "") if plan and isinstance(plan[0], dict) else ""
        dataset_root = "."
    else:
        plan = []
        dataset_id = ""
        dataset_root = "."
    return {
        "schema_version": DOWNLOAD_PLAN_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "source_db": "geo",
        "dataset_root": str(Path(dataset_root).expanduser().resolve()),
        "plan": plan,
    }


def read_download_receipt(source: str | Path | dict[str, Any] | list[Any], *, dataset_id: str = "", dataset_root: str = ".") -> dict[str, Any]:
    payload = _maybe_load(source)
    if isinstance(payload, dict) and payload.get("schema_version") == DOWNLOAD_RECEIPT_SCHEMA_VERSION:
        return payload
    transaction_log = payload.get("files") if isinstance(payload, dict) and "files" in payload else payload
    if isinstance(transaction_log, dict) and "download_transaction_log" in transaction_log:
        transaction_log = transaction_log["download_transaction_log"]
    if not isinstance(transaction_log, list):
        transaction_log = []
    inferred_id = dataset_id
    if not inferred_id and transaction_log and isinstance(transaction_log[0], dict):
        inferred_id = str(transaction_log[0].get("accession") or "")
    return build_download_receipt_payload(inferred_id, dataset_root, transaction_log)


def read_file_inventory(source: str | Path | dict[str, Any] | None = None, *, dataset_id: str = "", dataset_root: str = ".", validation_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = _maybe_load(source) if source is not None else None
    if isinstance(payload, dict) and payload.get("schema_version") == FILE_INVENTORY_SCHEMA_VERSION:
        return payload
    if validation_payload:
        return build_file_inventory_payload(
            dataset_id or str(validation_payload.get("gse_id") or validation_payload.get("dataset_id") or ""),
            dataset_root or str(validation_payload.get("download_dir") or "."),
            list(validation_payload.get("extra", {}).get("file_scores", [])),
            legacy_status=validation_payload.get("status"),
        )
    if isinstance(payload, dict) and "files" in payload:
        return {
            "schema_version": FILE_INVENTORY_SCHEMA_VERSION,
            "dataset_id": dataset_id,
            "source_db": "geo",
            "dataset_root": str(Path(dataset_root).expanduser().resolve()),
            "files": payload.get("files", []),
        }
    return {
        "schema_version": FILE_INVENTORY_SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "source_db": "geo",
        "dataset_root": str(Path(dataset_root).expanduser().resolve()),
        "files": [],
    }


def read_parser_hints(source: str | Path | dict[str, Any] | None = None, *, validation_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = _maybe_load(source) if source is not None else None
    if isinstance(payload, dict) and payload.get("schema_version") == PARSER_HINTS_SCHEMA_VERSION:
        return payload
    if validation_payload:
        return build_parser_hints_payload(validation_payload)
    return {
        "schema_version": PARSER_HINTS_SCHEMA_VERSION,
        "dataset_id": "",
        "recommended_strategy": "MANUAL_REVIEW_REQUIRED",
        "default_value_type_hint": "unknown",
        "matrix_candidates": [],
        "metadata_candidates": [],
        "feature_annotation_candidates": [],
        "clinical_candidates": [],
        "mutation_candidates": [],
        "may_generate_expression_gene": False,
        "may_generate_sample_annotation": False,
        "has_clinical_info": False,
        "has_mutation_info": False,
        "has_batch_info": False,
    }


def read_dataset_manifest_draft(source: str | Path | dict[str, Any] | None = None, *, validation_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = _maybe_load(source) if source is not None else None
    if isinstance(payload, dict) and payload.get("schema_version") == DATASET_MANIFEST_DRAFT_SCHEMA_VERSION:
        return payload
    if validation_payload:
        return build_dataset_manifest_draft_payload(validation_payload)
    return {
        "schema_version": DATASET_MANIFEST_DRAFT_SCHEMA_VERSION,
        "dataset_id": "",
        "recommended_strategy": "MANUAL_REVIEW_REQUIRED",
        "value_type_hint": "unknown",
    }


def read_module1_handoff(source: str | Path | dict[str, Any] | None = None, *, validation_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = _maybe_load(source) if source is not None else None
    if isinstance(payload, dict) and payload.get("schema_version") == HANDOFF_PACKAGE_SCHEMA_VERSION:
        return payload
    if validation_payload:
        return build_handoff_package_payload(validation_payload)
    return {
        "schema_version": HANDOFF_PACKAGE_SCHEMA_VERSION,
        "dataset_id": "",
        "recommended_strategy": "MANUAL_REVIEW_REQUIRED",
        "value_type_hint": "unknown",
        "dataset_info": {
            "dataset_id": "",
            "source_db": "geo",
            "legacy_status": None,
            "download_dir": None,
            "recommended_strategy": "MANUAL_REVIEW_REQUIRED",
            "value_type_hint": "unknown",
        },
        "file_inventory": [],
        "file_roles": {},
        "preferred_expression_asset": None,
        "preferred_metadata_asset": None,
        "preferred_feature_annotation_asset": None,
        "preferred_clinical_asset": None,
        "preferred_mutation_asset": None,
        "asset_role_counts": {},
        "available_capabilities": [],
        "warnings_summary": [],
        "missing_required_assets": [],
        "parser_hints": read_parser_hints(),
        "dataset_manifest_draft": read_dataset_manifest_draft(),
        "may_generate_expression_gene": False,
        "may_generate_sample_annotation": False,
        "has_clinical_info": False,
        "has_mutation_info": False,
        "has_batch_info": False,
        "supporting_contracts": {
            "module1_handoff": None,
            "dataset_manifest_draft": None,
            "parser_hints": None,
            "file_inventory": None,
        },
        "canonical_asset_paths": {},
        "standard_assets": {},
        "present_assets": [],
        "planned_assets": [],
        "not_applicable_assets": [],
    }


def load_module1_dataset_context(dataset_root: str | Path, *, validation_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(dataset_root).expanduser().resolve()
    reports_dir = root / "organized" / "reports"
    handoff_path = reports_dir / "module1_handoff.json"
    manifest_path = reports_dir / "dataset_manifest_draft.json"
    parser_hints_path = reports_dir / "parser_hints.json"
    file_inventory_path = reports_dir / "file_inventory.json"

    handoff_source = "handoff" if handoff_path.exists() else ("validation_payload" if validation_payload else "empty")
    handoff = (
        read_module1_handoff(handoff_path)
        if handoff_path.exists()
        else read_module1_handoff(validation_payload=validation_payload)
    )
    parser_hints = (
        read_parser_hints(parser_hints_path)
        if parser_hints_path.exists()
        else read_parser_hints(validation_payload=validation_payload)
    )
    manifest = (
        read_dataset_manifest_draft(manifest_path)
        if manifest_path.exists()
        else read_dataset_manifest_draft(validation_payload=validation_payload)
    )
    inventory = (
        read_file_inventory(file_inventory_path)
        if file_inventory_path.exists()
        else read_file_inventory(validation_payload=validation_payload, dataset_root=str(root))
    )

    if handoff.get("schema_version") != HANDOFF_PACKAGE_SCHEMA_VERSION and validation_payload:
        handoff = read_module1_handoff(validation_payload=validation_payload)

    handoff = _as_dict(handoff)
    parser_hints = _as_dict(parser_hints)
    manifest = _as_dict(manifest)
    inventory = _as_dict(inventory)
    dataset_info = _as_dict(handoff.get("dataset_info"))
    file_inventory = _as_list(handoff.get("file_inventory")) or _as_list(inventory.get("files"))

    dataset_id = _first_text(
        handoff.get("dataset_id"),
        dataset_info.get("dataset_id"),
        manifest.get("dataset_id"),
        parser_hints.get("dataset_id"),
        inventory.get("dataset_id"),
    )
    recommended_strategy = _first_text(
        handoff.get("recommended_strategy"),
        dataset_info.get("recommended_strategy"),
        manifest.get("recommended_strategy"),
        parser_hints.get("recommended_strategy"),
        default="MANUAL_REVIEW_REQUIRED",
        skip={"MANUAL_REVIEW_REQUIRED"},
    )
    value_type_hint = _first_text(
        handoff.get("value_type_hint"),
        dataset_info.get("value_type_hint"),
        manifest.get("value_type_hint"),
        parser_hints.get("default_value_type_hint"),
        default="unknown",
        skip={"unknown"},
    )

    handoff["dataset_id"] = dataset_id
    handoff["recommended_strategy"] = recommended_strategy
    handoff["value_type_hint"] = value_type_hint
    handoff["parser_hints"] = parser_hints
    handoff["dataset_manifest_draft"] = manifest
    handoff["file_inventory"] = file_inventory
    handoff["dataset_info"] = dataset_info
    handoff["may_generate_expression_gene"] = bool(
        handoff.get("may_generate_expression_gene") or parser_hints.get("may_generate_expression_gene")
    )
    handoff["may_generate_sample_annotation"] = bool(
        handoff.get("may_generate_sample_annotation") or parser_hints.get("may_generate_sample_annotation")
    )
    handoff["has_clinical_info"] = bool(
        handoff.get("has_clinical_info") or parser_hints.get("has_clinical_info")
    )
    handoff["has_mutation_info"] = bool(
        handoff.get("has_mutation_info") or parser_hints.get("has_mutation_info")
    )
    handoff["has_batch_info"] = bool(
        handoff.get("has_batch_info") or parser_hints.get("has_batch_info")
    )

    dataset_info["dataset_id"] = dataset_id
    dataset_info.setdefault("source_db", "geo")
    dataset_info["download_dir"] = _first_text(dataset_info.get("download_dir"), handoff.get("dataset_root"), str(root))
    dataset_info["recommended_strategy"] = recommended_strategy
    dataset_info["value_type_hint"] = value_type_hint

    for key in (
        "preferred_expression_asset",
        "preferred_metadata_asset",
        "preferred_feature_annotation_asset",
        "preferred_clinical_asset",
        "preferred_mutation_asset",
    ):
        if not isinstance(handoff.get(key), dict):
            handoff[key] = None
    if not isinstance(handoff.get("asset_role_counts"), dict):
        handoff["asset_role_counts"] = {}
    if not isinstance(handoff.get("available_capabilities"), list):
        handoff["available_capabilities"] = []
    if not isinstance(handoff.get("warnings_summary"), list):
        handoff["warnings_summary"] = []
    if not isinstance(handoff.get("missing_required_assets"), list):
        handoff["missing_required_assets"] = []
    if not isinstance(handoff.get("canonical_asset_paths"), dict):
        handoff["canonical_asset_paths"] = {}
    if not isinstance(handoff.get("standard_assets"), dict):
        handoff["standard_assets"] = {}
    if not isinstance(handoff.get("present_assets"), list):
        handoff["present_assets"] = []
    if not isinstance(handoff.get("planned_assets"), list):
        handoff["planned_assets"] = []
    if not isinstance(handoff.get("not_applicable_assets"), list):
        handoff["not_applicable_assets"] = []

    supporting_contracts = _as_dict(handoff.get("supporting_contracts"))
    default_supporting_contracts = {
        "module1_handoff": str(handoff_path) if handoff_path.exists() else None,
        "dataset_manifest_draft": str(manifest_path) if manifest_path.exists() else None,
        "parser_hints": str(parser_hints_path) if parser_hints_path.exists() else None,
        "file_inventory": str(file_inventory_path) if file_inventory_path.exists() else None,
    }
    for key, value in default_supporting_contracts.items():
        if not supporting_contracts.get(key):
            supporting_contracts[key] = value

    handoff["supporting_contracts"] = supporting_contracts
    if handoff_source == "empty" and any(default_supporting_contracts.values()):
        handoff_source = "legacy_supporting_files"
    handoff["_module3_context_origin"] = handoff_source
    handoff = merge_standard_asset_layout(
        handoff,
        build_standard_asset_layout(root, handoff=handoff),
    )
    return handoff


def handoff_recommended_strategy(handoff: dict[str, Any]) -> str:
    return str(
        handoff.get("dataset_info", {}).get("recommended_strategy")
        or handoff.get("dataset_manifest_draft", {}).get("recommended_strategy")
        or handoff.get("parser_hints", {}).get("recommended_strategy")
        or "MANUAL_REVIEW_REQUIRED"
    )


def handoff_value_type_hint(handoff: dict[str, Any]) -> str:
    return str(
        handoff.get("dataset_info", {}).get("value_type_hint")
        or handoff.get("dataset_manifest_draft", {}).get("value_type_hint")
        or handoff.get("parser_hints", {}).get("default_value_type_hint")
        or "unknown"
    )
