"""Module 3 helpers for standard asset planning and consumption."""

from __future__ import annotations

from pathlib import Path
from typing import Any


STANDARD_ASSET_PATHS = {
    "expression_gene": "organized/expression_gene.tsv.gz",
    "sample_annotation": "organized/sample_annotation.tsv",
    "feature_annotation": "organized/feature_annotation.tsv",
    "dataset_manifest": "organized/dataset_manifest.json",
}


def _context_origin(handoff: dict[str, Any]) -> str:
    return str(handoff.get("_module3_context_origin") or "handoff").strip() or "handoff"


def _handoff_dataset_id(handoff: dict[str, Any]) -> str:
    dataset_info = handoff.get("dataset_info")
    if isinstance(dataset_info, dict):
        dataset_id = str(dataset_info.get("dataset_id") or "").strip()
        if dataset_id:
            return dataset_id
    return str(handoff.get("dataset_id") or "").strip()


def _preferred_asset_name(handoff: dict[str, Any], key: str) -> str | None:
    asset = handoff.get(key)
    if not isinstance(asset, dict):
        return None
    return str(asset.get("relative_path") or asset.get("file_name") or "").strip() or None


def _asset_expected(asset_key: str, handoff: dict[str, Any]) -> bool:
    manifest = handoff.get("dataset_manifest_draft", {})
    if asset_key == "expression_gene":
        return bool(handoff.get("may_generate_expression_gene"))
    if asset_key == "sample_annotation":
        return bool(
            handoff.get("may_generate_sample_annotation")
            or manifest.get("has_sample_annotation")
        )
    if asset_key == "feature_annotation":
        return bool(
            handoff.get("preferred_feature_annotation_asset")
            or manifest.get("platform_annotation_files")
        )
    if asset_key == "dataset_manifest":
        module1_state = handoff.get("module1_state", {}).get("current_state")
        return bool(_handoff_dataset_id(handoff)) and module1_state != "failed"
    return False


def _asset_source_hint(asset_key: str, handoff: dict[str, Any]) -> str | None:
    if asset_key == "expression_gene":
        return _preferred_asset_name(handoff, "preferred_expression_asset")
    if asset_key == "sample_annotation":
        return _preferred_asset_name(handoff, "preferred_metadata_asset")
    if asset_key == "feature_annotation":
        return _preferred_asset_name(handoff, "preferred_feature_annotation_asset")
    if asset_key == "dataset_manifest":
        strategy = str(handoff.get("recommended_strategy") or "").strip()
        return strategy or None
    return None


def _asset_reason_code(asset_key: str, handoff: dict[str, Any], *, exists: bool, expected: bool, source_hint: str | None) -> str:
    missing_required = set(handoff.get("missing_required_assets") or [])
    context_origin = _context_origin(handoff)

    if exists and expected:
        return "present_on_disk"
    if asset_key == "dataset_manifest" and not _handoff_dataset_id(handoff):
        return "missing_dataset_id"
    if asset_key == "expression_gene" and "expression_asset" in missing_required:
        return "missing_supporting_input"
    if asset_key == "sample_annotation" and "metadata_asset" in missing_required:
        return "missing_supporting_input"
    if (
        asset_key == "feature_annotation"
        and not expected
        and not handoff.get("preferred_feature_annotation_asset")
        and not handoff.get("dataset_manifest_draft", {}).get("platform_annotation_files")
    ):
        return "missing_supporting_input"
    if not expected:
        return "not_expected"
    if context_origin in {"legacy_supporting_files", "validation_payload"}:
        return "inferred_from_legacy"
    if source_hint:
        return "inferred_from_handoff"
    return "missing_on_disk"


def _asset_reason(asset_key: str, handoff: dict[str, Any], exists: bool, expected: bool) -> str:
    if exists:
        return "present_on_disk"
    if expected:
        if asset_key == "expression_gene":
            return "expression matrix is available; gene-level asset is expected downstream"
        if asset_key == "sample_annotation":
            return "metadata or family.soft context indicates sample annotation should be consumable"
        if asset_key == "feature_annotation":
            return "platform/feature annotation source is available for downstream normalization"
        if asset_key == "dataset_manifest":
            return "dataset manifest is the planned downstream entrypoint for standard assets"
    missing_required = set(handoff.get("missing_required_assets") or [])
    if asset_key == "expression_gene" and "expression_asset" in missing_required:
        return "expression asset is missing upstream"
    if asset_key == "sample_annotation" and "metadata_asset" in missing_required:
        return "metadata asset is missing upstream"
    if not expected:
        return "file may exist on disk but is not trusted for current handoff state"
    return "not_applicable_for_current_dataset"


def build_standard_asset_layout(
    dataset_root: str | Path,
    *,
    handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(dataset_root).expanduser().resolve()
    handoff = dict(handoff or {})

    assets: dict[str, Any] = {}
    for asset_key, relative_path in STANDARD_ASSET_PATHS.items():
        canonical_path = root / relative_path
        expected = _asset_expected(asset_key, handoff)
        exists = canonical_path.exists()
        is_present = exists and expected
        source_hint = _asset_source_hint(asset_key, handoff)
        assets[asset_key] = {
            "asset_key": asset_key,
            "relative_path": relative_path,
            "canonical_path": str(canonical_path),
            "exists": exists,
            "expected": expected,
            "status": "present" if is_present else ("planned" if expected else "not_applicable"),
            "source_hint": source_hint,
            "reason_code": _asset_reason_code(
                asset_key,
                handoff,
                exists=is_present,
                expected=expected,
                source_hint=source_hint,
            ),
            "reason": _asset_reason(asset_key, handoff, is_present, expected),
        }

    return {
        "dataset_root": str(root),
        "canonical_asset_paths": {key: value["canonical_path"] for key, value in assets.items()},
        "standard_assets": assets,
        "present_assets": [key for key, value in assets.items() if value["status"] == "present"],
        "planned_assets": [key for key, value in assets.items() if value["status"] == "planned"],
        "not_applicable_assets": [key for key, value in assets.items() if value["status"] == "not_applicable"],
    }


def merge_standard_asset_layout(existing: dict[str, Any], computed: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    merged["dataset_root"] = str(merged.get("dataset_root") or computed.get("dataset_root") or "")

    computed_paths = computed.get("canonical_asset_paths", {})
    existing_paths = merged.get("canonical_asset_paths")
    canonical_asset_paths = dict(existing_paths) if isinstance(existing_paths, dict) else {}
    if isinstance(computed_paths, dict):
        for key, value in computed_paths.items():
            canonical_asset_paths[key] = value
    merged["canonical_asset_paths"] = canonical_asset_paths

    existing_assets = merged.get("standard_assets")
    if not isinstance(existing_assets, dict):
        existing_assets = {}
    computed_assets = computed.get("standard_assets", {})
    for asset_key, computed_asset in computed_assets.items():
        current_asset = existing_assets.get(asset_key)
        if isinstance(current_asset, dict):
            merged_asset = dict(current_asset)
            previous_status = str(current_asset.get("status") or "").strip()
            for field in ("asset_key", "relative_path", "canonical_path", "exists", "expected", "status"):
                merged_asset[field] = computed_asset.get(field)
            if merged_asset.get("source_hint") in (None, ""):
                computed_source_hint = computed_asset.get("source_hint")
                if computed_source_hint not in (None, ""):
                    merged_asset["source_hint"] = computed_source_hint
            merged_asset["reason_code"] = computed_asset.get("reason_code")
            computed_reason = computed_asset.get("reason")
            if computed_reason not in (None, ""):
                merged_asset["reason"] = computed_reason
            else:
                merged_asset.setdefault("reason", current_asset.get("reason"))
            if previous_status and previous_status != merged_asset.get("status"):
                merged_asset["reason_code"] = "status_conflict_resolved"
                merged_asset["reason"] = "recomputed from current handoff and disk state; stale persisted asset status was replaced"
            for field, value in computed_asset.items():
                merged_asset.setdefault(field, value)
            existing_assets[asset_key] = merged_asset
        else:
            existing_assets[asset_key] = dict(computed_asset)
    merged["standard_assets"] = existing_assets

    def _derive(bucket: str, status: str) -> list[str]:
        return [
            key
            for key, value in existing_assets.items()
            if isinstance(value, dict) and value.get("status") == status
        ]

    merged["present_assets"] = _derive("present_assets", "present")
    merged["planned_assets"] = _derive("planned_assets", "planned")
    merged["not_applicable_assets"] = _derive("not_applicable_assets", "not_applicable")
    return merged
