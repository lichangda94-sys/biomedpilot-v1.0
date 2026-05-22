from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .materialization import LEGACY_MATERIALIZATION_MANIFEST_PATH


LEGACY_REPOSITORY_MERGE_PLAN_VERSION = "biomedpilot.legacy_repository_manifest_merge_plan.v1"
LEGACY_REPOSITORY_MERGE_MANIFEST_VERSION = "biomedpilot.legacy_repository_manifest_merge_manifest.v1"
REPOSITORY_ROOT = Path("standardized_data") / "repositories"
REPOSITORY_MANIFEST = REPOSITORY_ROOT / "repository_manifest.json"
REPOSITORY_VALIDATION_REPORT = REPOSITORY_ROOT / "validation_report.json"
ASSET_LINEAGE = REPOSITORY_ROOT / "asset_lineage.jsonl"
LEGACY_REPOSITORY_MERGE_MANIFEST = Path("standardized_data") / "asset_candidates" / "legacy_repository_manifest_merge.json"
FORMAL_RESULT_SEMANTICS = {"formal_computed_result", "report_ready_result"}


def plan_legacy_repository_manifest_merge(
    project_root: str | Path,
    *,
    selected_asset_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    materialized = _read_json(root / LEGACY_MATERIALIZATION_MANIFEST_PATH)
    assets = [asset for asset in materialized.get("assets", []) or [] if isinstance(asset, dict)]
    selected = {str(item) for item in selected_asset_ids or [] if str(item)}
    if selected:
        assets = [asset for asset in assets if str(asset.get("asset_id") or "") in selected]
    merge_assets = [_merge_asset_record(asset) for asset in assets]
    plan = {
        "schema_version": LEGACY_REPOSITORY_MERGE_PLAN_VERSION,
        "created_at": _now(),
        "project_root": str(root),
        "source_materialization_manifest": str(root / LEGACY_MATERIALIZATION_MANIFEST_PATH),
        "selected_asset_ids": sorted(selected),
        "merge_asset_count": len(merge_assets),
        "merge_assets": merge_assets,
        "downstream_contract": {
            "writes_repository_manifest": True,
            "writes_validation_report": True,
            "writes_asset_lineage": True,
            "writes_analysis_input_repository": False,
            "writes_result_index": False,
            "ready_for_formal_analysis": False,
            "requires_b8_resolver_after_merge": True,
        },
    }
    validation = validate_legacy_repository_manifest_merge_plan(plan)
    return {**plan, "validation": validation, "status": "blocked" if validation["blockers"] else "merge_plan_only"}


def validate_legacy_repository_manifest_merge_plan(plan: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if plan.get("schema_version") != LEGACY_REPOSITORY_MERGE_PLAN_VERSION:
        blockers.append("legacy_repository_merge_plan_schema_version_mismatch")
    contract = plan.get("downstream_contract") if isinstance(plan.get("downstream_contract"), dict) else {}
    if contract.get("writes_repository_manifest") is not True:
        blockers.append("repository_merge_must_write_repository_manifest")
    if contract.get("writes_analysis_input_repository") is not False:
        blockers.append("repository_merge_must_not_write_analysis_input_repository")
    if contract.get("writes_result_index") is not False:
        blockers.append("repository_merge_must_not_write_result_index")
    if contract.get("ready_for_formal_analysis") is not False:
        blockers.append("repository_merge_must_not_be_formal_ready")
    for index, asset in enumerate(plan.get("merge_assets", []) or []):
        if not isinstance(asset, dict):
            blockers.append(f"merge_asset_{index}_must_be_object")
            continue
        blockers.extend(f"merge_asset_{index}:{blocker}" for blocker in asset.get("blockers", []) or [])
        warnings.extend(f"merge_asset_{index}:{warning}" for warning in asset.get("warnings", []) or [])
        if asset.get("analysis_ready") is not False:
            blockers.append(f"merge_asset_{index}:analysis_ready_forbidden_in_b16_3")
        if asset.get("formal_analysis_ready") is not False:
            blockers.append(f"merge_asset_{index}:formal_analysis_ready_forbidden")
        if str(asset.get("result_semantics") or "") in FORMAL_RESULT_SEMANTICS:
            blockers.append(f"merge_asset_{index}:formal_result_semantics_forbidden")
        if asset.get("report_ready_eligible") is True:
            blockers.append(f"merge_asset_{index}:report_ready_forbidden")
        if not asset.get("asset_id") or not asset.get("path"):
            blockers.append(f"merge_asset_{index}:missing_asset_id_or_path")
    return {
        "schema_version": "biomedpilot.legacy_repository_manifest_merge_plan_validation.v1",
        "status": "blocked" if blockers else "passed",
        "blockers": _dedupe(blockers),
        "warnings": _dedupe(warnings),
    }


def merge_legacy_materialized_assets_into_repository_manifest(
    project_root: str | Path,
    *,
    selected_asset_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    plan = plan_legacy_repository_manifest_merge(root, selected_asset_ids=selected_asset_ids)
    if plan["validation"]["status"] == "blocked":
        merge_manifest = _merge_manifest(root, plan, [], plan["validation"]["blockers"])
        _write_json(root / LEGACY_REPOSITORY_MERGE_MANIFEST, merge_manifest)
        return merge_manifest
    existing = _read_json(root / REPOSITORY_MANIFEST)
    existing_assets = [asset for asset in existing.get("assets", []) or [] if isinstance(asset, dict)]
    merged_assets = _dedupe_assets([*existing_assets, *plan["merge_assets"]])
    repository_manifest = {
        "schema_version": "biomedpilot.repository_manifest.v1",
        "generated_at": _now(),
        "project_root": str(root),
        "source_state": {
            **(existing.get("source_state") if isinstance(existing.get("source_state"), dict) else {}),
            "legacy_repository_merge": True,
            "legacy_repository_merge_manifest": str(root / LEGACY_REPOSITORY_MERGE_MANIFEST),
        },
        "repositories": _repository_summary(merged_assets),
        "assets": merged_assets,
        "analysis_input_packages": list(existing.get("analysis_input_packages", []) or []),
        "default_asset_selection": existing.get("default_asset_selection", {}) if isinstance(existing.get("default_asset_selection"), dict) else {},
        "biological_normalization_performed": False,
        "normalization_boundary": "Legacy repository merge registers materialized assets only; it does not normalize, create analysis input packages, or execute analysis.",
        "legacy_merge_contract": plan["downstream_contract"],
    }
    validation_report = _validation_report(plan, merged_assets)
    lineage = _lineage_records(plan["merge_assets"])
    _write_json(root / REPOSITORY_MANIFEST, repository_manifest)
    _write_json(root / REPOSITORY_VALIDATION_REPORT, validation_report)
    _write_lineage(root / ASSET_LINEAGE, [*_existing_lineage(root / ASSET_LINEAGE), *lineage])
    merge_manifest = _merge_manifest(root, plan, plan["merge_assets"], [])
    _write_json(root / LEGACY_REPOSITORY_MERGE_MANIFEST, merge_manifest)
    return merge_manifest


def _merge_asset_record(asset: dict[str, Any]) -> dict[str, Any]:
    warnings = [str(item) for item in asset.get("warnings", []) or [] if str(item)]
    warnings.append("legacy_repository_asset_requires_b8_resolver_and_downstream_gates")
    blockers = [str(item) for item in asset.get("blockers", []) or [] if str(item)]
    standard_type = _standard_asset_type(str(asset.get("asset_role") or ""), str(asset.get("asset_type") or ""), str(asset.get("source_file") or ""))
    record = {
        "asset_id": str(asset.get("asset_id") or ""),
        "repository": str(asset.get("repository") or ""),
        "asset_role": str(asset.get("asset_role") or ""),
        "asset_type": standard_type,
        "legacy_asset_type": str(asset.get("asset_type") or ""),
        "label_zh": standard_type,
        "source_file": str(asset.get("source_file") or ""),
        "source_acquisition_id": str(asset.get("source_adapter_id") or asset.get("source_candidate_id") or ""),
        "source_recognition_run_id": "",
        "path": str(asset.get("path") or ""),
        "file_path": str(asset.get("file_path") or asset.get("path") or ""),
        "format": _format_for_path(str(asset.get("path") or "")),
        "checksum": str(asset.get("checksum") or ""),
        "size": int(asset.get("size_bytes") or 0),
        "size_bytes": int(asset.get("size_bytes") or 0),
        "row_count": 0,
        "column_count": 0,
        "validation_status": "warning" if warnings and not blockers else ("blocked" if blockers else "registered"),
        "warnings": _dedupe(warnings),
        "warning": "; ".join(_dedupe(warnings)),
        "blockers": _dedupe(blockers),
        "consumable_by": [],
        "analysis_ready": False,
        "formal_analysis_ready": False,
        "result_semantics": "not_a_result",
        "report_ready_eligible": False,
        "materialize_strategy": "legacy_repository_manifest_merge_gate",
        "biological_normalization_performed": False,
        "normalization_boundary": "Merged from legacy materialized asset; not normalized and not formal analysis ready.",
        "expression_value_type": _value_type_for_asset(asset),
        "gene_id_type": _gene_id_type_for_asset(asset),
        "default_selected": False,
        "next_required_gates": ["b8_analysis_input_resolver", "deg_ready_or_downstream_specific_gate"],
    }
    return record


def _standard_asset_type(role: str, asset_type: str, source_file: str) -> str:
    text = f"{asset_type} {source_file}".lower()
    if role == "expression_matrix":
        if "tcga" in text:
            return "tcga_expression_matrix"
        if "gtex" in text:
            return "gtex_expression_matrix"
        return "expression_matrix"
    if role == "sample_metadata":
        if "tcga" in text:
            return "tcga_sample_metadata"
        if "gtex" in text:
            return "gtex_sample_metadata"
        return "sample_metadata"
    if role == "feature_annotation":
        return "platform_annotation"
    if role == "clinical_metadata":
        return "tcga_clinical_metadata" if "tcga" in text else "clinical_metadata"
    return "legacy_acquisition_manifest"


def _value_type_for_asset(asset: dict[str, Any]) -> str:
    text = " ".join(str(asset.get(key) or "") for key in ("asset_type", "source_file", "path")).lower()
    if "star_counts" in text or "counts" in text or "raw_count" in text:
        return "count"
    if "tpm" in text:
        return "TPM"
    if "fpkm" in text:
        return "FPKM"
    if "gtex" in text:
        return "normalized_expression"
    return "unknown"


def _gene_id_type_for_asset(asset: dict[str, Any]) -> str:
    text = " ".join(str(asset.get(key) or "") for key in ("asset_type", "source_file", "path")).lower()
    if "probe" in text or "id_ref" in text:
        return "probe"
    if "ensembl" in text:
        return "ensembl"
    if "symbol" in text or "gene" in text:
        return "symbol"
    return "unknown"


def _format_for_path(path: str) -> str:
    suffixes = [suffix.lower().lstrip(".") for suffix in Path(path).suffixes]
    return ".".join(suffixes) if suffixes else "json"


def _repository_summary(assets: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(asset.get("repository") or "") for asset in assets)
    return {
        repository: {
            "asset_count": count,
            "ready_count": 0,
            "blocked_count": sum(1 for asset in assets if str(asset.get("repository") or "") == repository and str(asset.get("validation_status") or "") == "blocked"),
            "analysis_ready": False,
        }
        for repository, count in sorted(counts.items())
        if repository
    }


def _validation_report(plan: dict[str, Any], assets: list[dict[str, Any]]) -> dict[str, Any]:
    issues = []
    for asset in plan.get("merge_assets", []) or []:
        for warning in asset.get("warnings", []) or []:
            issues.append({"severity": "warning", "asset_id": asset.get("asset_id", ""), "code": str(warning)})
        for blocker in asset.get("blockers", []) or []:
            issues.append({"severity": "blocker", "asset_id": asset.get("asset_id", ""), "code": str(blocker)})
    return {
        "schema_version": "biomedpilot.repository_validation_report.v1",
        "generated_at": _now(),
        "overall_status": "blocked" if any(issue["severity"] == "blocker" for issue in issues) else ("warning" if issues else "passed"),
        "issues": issues,
        "asset_validation": {
            str(asset.get("asset_id") or ""): {
                "status": asset.get("validation_status", "registered"),
                "warnings": asset.get("warnings", []),
                "blockers": asset.get("blockers", []),
            }
            for asset in assets
            if asset.get("asset_id")
        },
    }


def _lineage_records(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "asset_id": asset.get("asset_id"),
            "repository": asset.get("repository"),
            "asset_type": asset.get("asset_type"),
            "legacy_asset_type": asset.get("legacy_asset_type", ""),
            "source_file": asset.get("source_file"),
            "source_acquisition_id": asset.get("source_acquisition_id"),
            "path": asset.get("path"),
            "materialize_strategy": "legacy_repository_manifest_merge_gate",
            "biological_normalization_performed": False,
            "formal_analysis_ready": False,
        }
        for asset in assets
    ]


def _merge_manifest(root: Path, plan: dict[str, Any], merged_assets: list[dict[str, Any]], blockers: list[str]) -> dict[str, Any]:
    return {
        "schema_version": LEGACY_REPOSITORY_MERGE_MANIFEST_VERSION,
        "created_at": _now(),
        "project_root": str(root),
        "status": "blocked" if blockers else "merged_repository_manifest_only",
        "source_materialization_manifest": plan.get("source_materialization_manifest", ""),
        "repository_manifest_path": str(root / REPOSITORY_MANIFEST),
        "validation_report_path": str(root / REPOSITORY_VALIDATION_REPORT),
        "asset_lineage_path": str(root / ASSET_LINEAGE),
        "merged_asset_count": len(merged_assets),
        "merged_assets": merged_assets,
        "warnings": _dedupe([warning for asset in merged_assets for warning in asset.get("warnings", []) or []]),
        "blockers": _dedupe(blockers),
        "downstream_contract": plan.get("downstream_contract", {}),
    }


def _dedupe_assets(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for asset in assets:
        asset_id = str(asset.get("asset_id") or "")
        if asset_id:
            by_id[asset_id] = asset
    return list(by_id.values())


def _existing_lineage(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _write_lineage(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if str(value)))
