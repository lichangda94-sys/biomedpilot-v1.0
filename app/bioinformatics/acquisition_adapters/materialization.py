from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .standardized_bridge import (
    LEGACY_ASSET_CANDIDATE_PATH,
    validate_legacy_standardized_asset_candidate,
)


LEGACY_MATERIALIZATION_MANIFEST_VERSION = "biomedpilot.legacy_candidate_materialization_manifest.v1"
LEGACY_MATERIALIZATION_PLAN_VERSION = "biomedpilot.legacy_candidate_materialization_plan.v1"
LEGACY_MATERIALIZATION_MANIFEST_PATH = Path("standardized_data") / "asset_candidates" / "legacy_materialized_assets_manifest.json"
LEGACY_MATERIALIZATION_LINEAGE_PATH = Path("standardized_data") / "asset_candidates" / "legacy_materialized_asset_lineage.jsonl"
FORMAL_RESULT_SEMANTICS = {"formal_computed_result", "report_ready_result"}
ROLE_REPOSITORIES = {
    "expression_matrix": Path("standardized_data") / "repositories" / "expression_repository",
    "sample_metadata": Path("standardized_data") / "repositories" / "sample_metadata_repository",
    "feature_annotation": Path("standardized_data") / "repositories" / "feature_annotation_repository",
    "clinical_metadata": Path("standardized_data") / "repositories" / "clinical_repository",
    "acquisition_manifest": Path("standardized_data") / "repositories" / "legacy_acquisition_repository",
}


def build_legacy_candidate_materialization_plan(
    project_root: str | Path,
    *,
    selected_candidate_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    bundle = _read_json(root / LEGACY_ASSET_CANDIDATE_PATH)
    candidates = [candidate for candidate in bundle.get("candidates", []) or [] if isinstance(candidate, dict)]
    selected_ids = {str(item) for item in selected_candidate_ids or [] if str(item)}
    if selected_ids:
        candidates = [candidate for candidate in candidates if str(candidate.get("candidate_id") or "") in selected_ids]
    plan_items = [_plan_item(root, candidate) for candidate in candidates]
    plan = {
        "schema_version": LEGACY_MATERIALIZATION_PLAN_VERSION,
        "created_at": _now(),
        "project_root": str(root),
        "source_candidate_bundle": str(root / LEGACY_ASSET_CANDIDATE_PATH),
        "selected_candidate_ids": sorted(selected_ids),
        "candidate_count": len(plan_items),
        "plan_items": plan_items,
        "downstream_contract": {
            "writes_repository_files": True,
            "writes_repository_manifest": False,
            "writes_analysis_input_repository": False,
            "writes_result_index": False,
            "ready_for_formal_analysis": False,
            "requires_later_repository_manifest_merge": True,
            "requires_b8_resolver_after_merge": True,
        },
    }
    validation = validate_legacy_candidate_materialization_plan(plan)
    return {**plan, "validation": validation, "status": "blocked" if validation["blockers"] else "materialization_plan_only"}


def validate_legacy_candidate_materialization_plan(plan: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if plan.get("schema_version") != LEGACY_MATERIALIZATION_PLAN_VERSION:
        blockers.append("legacy_materialization_plan_schema_version_mismatch")
    contract = plan.get("downstream_contract") if isinstance(plan.get("downstream_contract"), dict) else {}
    if contract.get("writes_repository_manifest") is not False:
        blockers.append("materialization_must_not_write_repository_manifest")
    if contract.get("writes_analysis_input_repository") is not False:
        blockers.append("materialization_must_not_write_analysis_input_repository")
    if contract.get("writes_result_index") is not False:
        blockers.append("materialization_must_not_write_result_index")
    if contract.get("ready_for_formal_analysis") is not False:
        blockers.append("materialization_must_not_be_formal_ready")
    for index, item in enumerate(plan.get("plan_items", []) or []):
        if not isinstance(item, dict):
            blockers.append(f"plan_item_{index}_must_be_object")
            continue
        blockers.extend(f"plan_item_{index}:{blocker}" for blocker in item.get("blockers", []) or [])
        warnings.extend(f"plan_item_{index}:{warning}" for warning in item.get("warnings", []) or [])
        if item.get("writes_repository_manifest") is not False:
            blockers.append(f"plan_item_{index}:writes_repository_manifest_forbidden")
        if item.get("writes_analysis_input_repository") is not False:
            blockers.append(f"plan_item_{index}:writes_analysis_input_repository_forbidden")
        if item.get("writes_result_index") is not False:
            blockers.append(f"plan_item_{index}:writes_result_index_forbidden")
        if item.get("formal_analysis_ready") is not False:
            blockers.append(f"plan_item_{index}:formal_analysis_ready_forbidden")
        if str(item.get("result_semantics") or "") in FORMAL_RESULT_SEMANTICS:
            blockers.append(f"plan_item_{index}:formal_result_semantics_forbidden")
    return {
        "schema_version": "biomedpilot.legacy_candidate_materialization_plan_validation.v1",
        "status": "blocked" if blockers else "passed",
        "blockers": _dedupe(blockers),
        "warnings": _dedupe(warnings),
    }


def materialize_legacy_standardized_asset_candidates(
    project_root: str | Path,
    *,
    selected_candidate_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    plan = build_legacy_candidate_materialization_plan(root, selected_candidate_ids=selected_candidate_ids)
    if plan["validation"]["status"] == "blocked":
        manifest = _materialization_manifest(root, plan, [], [], plan["validation"]["blockers"])
        _write_materialization_outputs(root, manifest, [])
        return manifest
    assets: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    blockers: list[str] = []
    for item in plan["plan_items"]:
        if item.get("blockers"):
            blockers.extend(str(blocker) for blocker in item.get("blockers") or [])
            continue
        asset = _materialize_plan_item(root, item)
        assets.append(asset)
        lineage.append(_lineage_record(asset, item))
    manifest = _materialization_manifest(root, plan, assets, lineage, blockers)
    _write_materialization_outputs(root, manifest, lineage)
    return manifest


def _plan_item(root: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    validation = validate_legacy_standardized_asset_candidate(candidate)
    blockers = [str(item) for item in validation.get("blockers") or []]
    blockers.extend(str(item) for item in candidate.get("blockers") or [] if str(item))
    warnings = [str(item) for item in validation.get("warnings") or []]
    warnings.extend(str(item) for item in candidate.get("warnings") or [] if str(item))
    if validation["status"] != "passed":
        blockers.append("candidate_validation_not_passed")
    source_value = str(candidate.get("path_or_query") or "")
    source_path = _candidate_source_path(root, source_value)
    repository = ROLE_REPOSITORIES.get(str(candidate.get("asset_role") or ""), ROLE_REPOSITORIES["acquisition_manifest"])
    asset_id = _asset_id(candidate)
    target_path = root / repository / _target_filename(asset_id, candidate, source_path)
    if not source_value:
        blockers.append("candidate_missing_path_or_query")
    if source_value and not source_path.exists():
        warnings.append("candidate_source_path_not_found_sidecar_only")
    if str(candidate.get("source") or "") == "gtex" and candidate.get("can_fill_tcga_normal_control") is not False:
        blockers.append("gtex_candidate_normal_control_forbidden")
    return {
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "asset_id": asset_id,
        "source": str(candidate.get("source") or ""),
        "source_candidate": candidate,
        "source_path_or_query": source_value,
        "source_path": str(source_path),
        "source_exists": source_path.exists(),
        "repository": str(repository),
        "target_path": str(target_path),
        "asset_type": _strip_candidate_suffix(str(candidate.get("asset_type") or "legacy_asset_candidate")),
        "asset_role": str(candidate.get("asset_role") or "acquisition_manifest"),
        "validation_status": "blocked" if blockers else ("warning" if warnings else "passed"),
        "formal_analysis_ready": False,
        "result_semantics": "not_a_result",
        "report_ready_eligible": False,
        "writes_repository_manifest": False,
        "writes_analysis_input_repository": False,
        "writes_result_index": False,
        "warnings": _dedupe(warnings),
        "blockers": _dedupe(blockers),
    }


def _materialize_plan_item(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    target = Path(str(item["target_path"]))
    source = Path(str(item["source_path"]))
    target.parent.mkdir(parents=True, exist_ok=True)
    materialization_mode = "sidecar_only"
    if source.exists() and source.is_file():
        shutil.copyfile(source, target)
        materialization_mode = "copied_file"
    else:
        target.write_text(json.dumps(_sidecar_payload(item), ensure_ascii=False, indent=2), encoding="utf-8")
    stats = _path_stats(target)
    return {
        "asset_id": item["asset_id"],
        "asset_type": item["asset_type"],
        "asset_role": item["asset_role"],
        "repository": item["repository"],
        "path": str(target),
        "file_path": str(target),
        "source_file": item["source_path_or_query"],
        "source_candidate_id": item["candidate_id"],
        "source_adapter_id": item["source_candidate"].get("source_adapter_id", ""),
        "source_manifest_path": item["source_candidate"].get("source_manifest_path", ""),
        "checksum": stats["sha256"],
        "size_bytes": stats["size_bytes"],
        "validation_status": item["validation_status"],
        "warnings": item["warnings"],
        "blockers": item["blockers"],
        "analysis_ready": False,
        "formal_analysis_ready": False,
        "result_semantics": "not_a_result",
        "report_ready_eligible": False,
        "materialize_strategy": "legacy_candidate_materialization_gate",
        "materialization_mode": materialization_mode,
        "biological_normalization_performed": False,
        "normalization_boundary": "Legacy candidate materialization copies or records assets only; it does not normalize or make analysis inputs.",
        "next_required_gates": ["repository_manifest_merge", "standardization_validation", "b8_analysis_input_resolver"],
    }


def _materialization_manifest(root: Path, plan: dict[str, Any], assets: list[dict[str, Any]], lineage: list[dict[str, Any]], blockers: list[str]) -> dict[str, Any]:
    return {
        "schema_version": LEGACY_MATERIALIZATION_MANIFEST_VERSION,
        "created_at": _now(),
        "project_root": str(root),
        "source_candidate_bundle": plan.get("source_candidate_bundle", ""),
        "manifest_path": str(root / LEGACY_MATERIALIZATION_MANIFEST_PATH),
        "lineage_path": str(root / LEGACY_MATERIALIZATION_LINEAGE_PATH),
        "status": "blocked" if blockers else "materialized_candidates_only",
        "materialized_asset_count": len(assets),
        "assets": assets,
        "lineage": lineage,
        "warnings": _dedupe([warning for item in plan.get("plan_items", []) for warning in item.get("warnings", []) or []]),
        "blockers": _dedupe(blockers),
        "downstream_contract": {
            "writes_repository_files": True,
            "writes_repository_manifest": False,
            "writes_analysis_input_repository": False,
            "writes_result_index": False,
            "ready_for_formal_analysis": False,
            "requires_later_repository_manifest_merge": True,
            "requires_b8_resolver_after_merge": True,
        },
    }


def _write_materialization_outputs(root: Path, manifest: dict[str, Any], lineage: list[dict[str, Any]]) -> None:
    manifest_path = root / LEGACY_MATERIALIZATION_MANIFEST_PATH
    lineage_path = root / LEGACY_MATERIALIZATION_LINEAGE_PATH
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    lineage_path.write_text("\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True) for item in lineage) + ("\n" if lineage else ""), encoding="utf-8")


def _candidate_source_path(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def _asset_id(candidate: dict[str, Any]) -> str:
    seed = "|".join(
        [
            str(candidate.get("candidate_id") or ""),
            str(candidate.get("source") or ""),
            str(candidate.get("asset_type") or ""),
            str(candidate.get("asset_role") or ""),
            str(candidate.get("path_or_query") or ""),
        ]
    )
    return f"legacy-materialized-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"


def _target_filename(asset_id: str, candidate: dict[str, Any], source_path: Path) -> str:
    suffix = source_path.suffix if source_path.suffix else ".asset.json"
    if str(candidate.get("asset_role") or "") == "expression_matrix" and suffix.lower() not in {".tsv", ".csv", ".txt", ".gz"}:
        suffix = ".matrix.json"
    return f"{asset_id}{suffix}"


def _strip_candidate_suffix(asset_type: str) -> str:
    return asset_type[: -len("_candidate")] if asset_type.endswith("_candidate") else asset_type


def _sidecar_payload(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.legacy_materialized_asset_sidecar.v1",
        "asset_id": item["asset_id"],
        "candidate_id": item["candidate_id"],
        "asset_type": item["asset_type"],
        "asset_role": item["asset_role"],
        "source_path_or_query": item["source_path_or_query"],
        "source_candidate": item["source_candidate"],
        "formal_analysis_ready": False,
        "result_semantics": "not_a_result",
        "report_ready_eligible": False,
    }


def _lineage_record(asset: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_id": asset["asset_id"],
        "asset_type": asset["asset_type"],
        "asset_role": asset["asset_role"],
        "source_candidate_id": item["candidate_id"],
        "source_adapter_id": asset.get("source_adapter_id", ""),
        "source_manifest_path": asset.get("source_manifest_path", ""),
        "path": asset["path"],
        "materialize_strategy": "legacy_candidate_materialization_gate",
        "biological_normalization_performed": False,
        "formal_analysis_ready": False,
    }


def _path_stats(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {"size_bytes": 0, "sha256": ""}
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"size_bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
