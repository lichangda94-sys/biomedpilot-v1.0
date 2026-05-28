from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .models import (
    CLINICAL_ASSET_TYPES,
    EVENT_FIELD_CANDIDATES,
    EXPRESSION_ASSET_TYPES,
    SAMPLE_METADATA_ASSET_TYPES,
    SURVIVAL_CLINICAL_INPUT_SCHEMA_VERSION,
    TIME_FIELD_CANDIDATES,
    utc_now,
)
from .source_mapping import build_case_sample_mapping


REPOSITORY_MANIFEST = Path("standardized_data") / "repositories" / "repository_manifest.json"
STANDARDIZED_REGISTRY = Path("manifests") / "standardized_assets_registry.json"
ANALYSIS_INPUT_REPOSITORY = Path("standardized_data") / "repositories" / "analysis_input_repository"
CLINICAL_REPOSITORY = Path("standardized_data") / "repositories" / "clinical_repository"
VALIDATION_REPORT = Path("standardized_data") / "repositories" / "validation_report.json"
ASSET_LINEAGE = Path("standardized_data") / "repositories" / "asset_lineage.jsonl"


def resolve_survival_clinical_inputs(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    repository_manifest = _read_json(root / REPOSITORY_MANIFEST)
    registry = _read_json(root / STANDARDIZED_REGISTRY)
    assets = _collect_assets(repository_manifest, registry)
    clinical_asset = _first_asset(assets, CLINICAL_ASSET_TYPES)
    sample_asset = _first_asset(assets, SAMPLE_METADATA_ASSET_TYPES)
    expression_asset = _first_asset(assets, EXPRESSION_ASSET_TYPES)
    clinical_rows = _read_table(_asset_path(root, clinical_asset))
    sample_rows = _read_table(_asset_path(root, sample_asset))
    expression_sample_ids = _expression_sample_ids(_asset_path(root, expression_asset))
    mapping = build_case_sample_mapping(clinical_rows=clinical_rows, sample_rows=sample_rows, expression_sample_ids=expression_sample_ids)
    fields = list(clinical_rows[0].keys()) if clinical_rows else []
    blockers: list[str] = []
    warnings: list[str] = []
    if not repository_manifest:
        blockers.append("missing_repository_manifest")
    if clinical_asset is None:
        blockers.append("missing_clinical_asset")
    if expression_asset is None:
        warnings.append("missing_expression_asset_survival_expression_grouping_unavailable")
    if sample_asset is None:
        warnings.append("missing_sample_metadata_asset_survival_mapping_may_use_expression_ids")
    blockers.extend(mapping["blockers"])
    warnings.extend(mapping["warnings"])
    status = "passed" if not blockers else "blocked"
    if not blockers and warnings:
        status = "passed_with_warnings"
    clinical_ref = _asset_ref(clinical_asset)
    sample_ref = _asset_ref(sample_asset)
    expression_ref = _asset_ref(expression_asset)
    package_id = _input_id(clinical_ref, sample_ref, expression_ref)
    return {
        "schema_version": SURVIVAL_CLINICAL_INPUT_SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": status,
        "survival_clinical_input_id": package_id,
        "source_dataset_id": _source_dataset_id(repository_manifest, clinical_asset or expression_asset),
        "project_root": str(root),
        "clinical_asset": clinical_ref,
        "sample_metadata_asset": sample_ref,
        "expression_asset": expression_ref,
        "case_id_column": mapping["case_id_column"],
        "sample_id_column": mapping["sample_id_column"],
        "patient_id_column": mapping["patient_id_column"],
        "tcga_barcode_policy": "normalize TCGA sample barcode to TCGA-XX-YYYY case id; record warning when truncation occurs",
        "case_sample_mapping_status": mapping["case_sample_mapping_status"],
        "case_sample_mapping_table": mapping["case_sample_mapping_table"],
        "available_time_fields": _matching_fields(fields, TIME_FIELD_CANDIDATES),
        "available_event_fields": _matching_fields(fields, EVENT_FIELD_CANDIDATES),
        "available_clinical_variables": fields,
        "available_expression_grouping_candidates": _grouping_candidates(sample_rows),
        "sample_count": mapping["sample_count"],
        "case_count": mapping["case_count"],
        "mapped_case_count": mapping["mapped_case_count"],
        "mapped_sample_count": mapping["mapped_sample_count"],
        "duplicate_case_ids": mapping["duplicate_case_ids"],
        "duplicate_sample_ids": mapping["duplicate_sample_ids"],
        "unmapped_cases": mapping["unmapped_cases"],
        "unmapped_samples": mapping["unmapped_samples"],
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
        "provenance": {
            "allowed_sources": [
                str(REPOSITORY_MANIFEST),
                str(STANDARDIZED_REGISTRY),
                str(ANALYSIS_INPUT_REPOSITORY),
                str(CLINICAL_REPOSITORY),
                str(VALIDATION_REPORT),
                str(ASSET_LINEAGE),
            ],
            "forbidden_sources": ["recognition_report.json", "UI table contents", "runner temp output", "plot artifact", "report package", "unregistered raw clinical file"],
            "mapping": mapping["provenance"],
            "repository_manifest_path": str(root / REPOSITORY_MANIFEST),
            "registry_path": str(root / STANDARDIZED_REGISTRY),
        },
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _collect_assets(repository_manifest: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    assets: dict[str, dict[str, Any]] = {}
    for source in (repository_manifest, registry):
        for asset in source.get("assets", []) or []:
            if isinstance(asset, dict) and asset.get("asset_id"):
                assets[str(asset["asset_id"])] = asset
    return list(assets.values())


def _first_asset(assets: list[dict[str, Any]], asset_types: set[str]) -> dict[str, Any] | None:
    for asset in assets:
        if str(asset.get("asset_type") or "") in asset_types or str(asset.get("repository") or "") in asset_types:
            return asset
    return None


def _asset_path(root: Path, asset: dict[str, Any] | None) -> Path | None:
    if not isinstance(asset, dict):
        return None
    value = str(asset.get("path") or asset.get("file_path") or "")
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def _read_table(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.is_file():
        return []
    try:
        first = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return []
    delimiter = "," if first.count(",") > first.count("\t") else "\t"
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter=delimiter)]


def _expression_sample_ids(path: Path | None) -> list[str]:
    if path is None or not path.is_file():
        return []
    try:
        first = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return []
    delimiter = "," if first.count(",") > first.count("\t") else "\t"
    fields = [field.strip() for field in first.split(delimiter)]
    return [field for field in fields[1:] if field]


def _matching_fields(fields: list[str], candidates: tuple[str, ...]) -> list[str]:
    lowered = {field.lower(): field for field in fields}
    exact = [lowered[candidate.lower()] for candidate in candidates if candidate.lower() in lowered]
    fuzzy = [field for field in fields if field not in exact and any(candidate.lower() in field.lower() for candidate in candidates)]
    return [*exact, *fuzzy]


def _grouping_candidates(sample_rows: list[dict[str, str]]) -> list[str]:
    if not sample_rows:
        return []
    fields = list(sample_rows[0].keys())
    blocked = {"sample_id", "sample", "case_id", "patient_id", "barcode", "tcga_barcode"}
    return [field for field in fields if field.lower() not in blocked]


def _asset_ref(asset: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(asset, dict):
        return {}
    return {
        "asset_id": str(asset.get("asset_id") or ""),
        "asset_type": str(asset.get("asset_type") or ""),
        "repository": str(asset.get("repository") or ""),
        "path": str(asset.get("path") or asset.get("file_path") or ""),
        "validation_status": str(asset.get("validation_status") or ""),
    }


def _source_dataset_id(repository_manifest: dict[str, Any], asset: dict[str, Any] | None) -> str:
    if isinstance(asset, dict):
        for key in ("source_acquisition_id", "asset_id"):
            value = str(asset.get(key) or "")
            if value:
                return value
    state = repository_manifest.get("source_state") if isinstance(repository_manifest.get("source_state"), dict) else {}
    return str(state.get("source_state_hash") or "")


def _input_id(*refs: dict[str, Any]) -> str:
    raw = "|".join(str(ref.get("asset_id") or "") for ref in refs if ref)
    return f"survival-clinical-{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"
