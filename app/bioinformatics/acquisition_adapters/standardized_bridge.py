from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .legacy_contract import LEGACY_ADAPTER_MANIFEST_DIR, validate_legacy_acquisition_manifest


LEGACY_ASSET_CANDIDATE_SCHEMA_VERSION = "biomedpilot.legacy_standardized_asset_candidate.v1"
LEGACY_ASSET_CANDIDATE_BUNDLE_VERSION = "biomedpilot.legacy_standardized_asset_candidate_bundle.v1"
LEGACY_ASSET_CANDIDATE_PATH = Path("standardized_data") / "asset_candidates" / "legacy_acquisition_asset_candidates.json"
FORMAL_RESULT_SEMANTICS = {"formal_computed_result", "report_ready_result"}


def build_legacy_standardized_asset_candidates(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    manifest_paths = sorted((root / LEGACY_ADAPTER_MANIFEST_DIR).glob("*.json"))
    candidates: list[dict[str, Any]] = []
    manifest_summaries: list[dict[str, Any]] = []
    warnings: list[str] = []
    blockers: list[str] = []
    for path in manifest_paths:
        manifest = _read_json(path)
        validation = validate_legacy_acquisition_manifest(manifest)
        summary = {
            "manifest_path": str(path),
            "adapter_id": str(manifest.get("adapter_id") or ""),
            "source": str(manifest.get("source") or ""),
            "validation_status": validation["status"],
            "validation_blockers": list(validation.get("blockers") or []),
            "manifest_blockers": list(manifest.get("blockers") or []),
        }
        manifest_summaries.append(summary)
        if validation["status"] != "passed":
            blockers.extend(str(item) for item in validation.get("blockers") or [])
            continue
        generated = _candidates_from_manifest(manifest, path)
        if not generated:
            warnings.append(f"legacy_manifest_has_no_candidate_assets:{manifest.get('adapter_id', path.name)}")
        candidates.extend(generated)
    candidate_validations = [validate_legacy_standardized_asset_candidate(candidate) for candidate in candidates]
    for validation in candidate_validations:
        blockers.extend(str(item) for item in validation.get("blockers") or [])
        warnings.extend(str(item) for item in validation.get("warnings") or [])
    return {
        "schema_version": LEGACY_ASSET_CANDIDATE_BUNDLE_VERSION,
        "generated_at": _now(),
        "project_root": str(root),
        "source_manifest_dir": str(root / LEGACY_ADAPTER_MANIFEST_DIR),
        "output_path": str(root / LEGACY_ASSET_CANDIDATE_PATH),
        "candidate_count": len(candidates),
        "manifest_count": len(manifest_paths),
        "manifests": manifest_summaries,
        "candidates": candidates,
        "candidate_validations": candidate_validations,
        "status": "blocked" if blockers else "candidate_only",
        "warnings": _dedupe(warnings),
        "blockers": _dedupe(blockers),
        "downstream_contract": {
            "writes_repository_manifest": False,
            "writes_analysis_input_repository": False,
            "writes_result_index": False,
            "ready_for_formal_analysis": False,
            "must_pass_standardization_validation": True,
            "must_pass_b8_resolver": True,
        },
    }


def write_legacy_standardized_asset_candidates(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    bundle = build_legacy_standardized_asset_candidates(root)
    output_path = root / LEGACY_ASSET_CANDIDATE_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    return bundle


def validate_legacy_standardized_asset_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    for field_name in (
        "schema_version",
        "candidate_id",
        "source",
        "source_adapter_id",
        "source_manifest_path",
        "asset_type",
        "asset_role",
        "path_or_query",
        "validation_status",
        "formal_analysis_ready",
        "result_semantics",
        "report_ready_eligible",
        "next_required_gates",
    ):
        if field_name not in candidate:
            blockers.append(f"missing_required_field:{field_name}")
    if candidate.get("schema_version") != LEGACY_ASSET_CANDIDATE_SCHEMA_VERSION:
        blockers.append("legacy_asset_candidate_schema_version_mismatch")
    if candidate.get("formal_analysis_ready") is not False:
        blockers.append("legacy_asset_candidate_must_not_be_formal_ready")
    if candidate.get("report_ready_eligible") is True:
        blockers.append("legacy_asset_candidate_report_ready_forbidden")
    if str(candidate.get("result_semantics") or "") in FORMAL_RESULT_SEMANTICS:
        blockers.append("legacy_asset_candidate_must_not_set_formal_result_semantics")
    gates = candidate.get("next_required_gates") if isinstance(candidate.get("next_required_gates"), list) else []
    if "standardization_validation" not in gates:
        blockers.append("legacy_asset_candidate_missing_standardization_gate")
    if "b8_analysis_input_resolver" not in gates:
        blockers.append("legacy_asset_candidate_missing_b8_resolver_gate")
    if str(candidate.get("source") or "") == "gtex" and candidate.get("can_fill_tcga_normal_control") is not False:
        blockers.append("gtex_asset_candidate_must_not_fill_tcga_normal_control")
    if candidate.get("validation_status") == "candidate_only":
        warnings.append("candidate_only_not_repository_asset")
    return {
        "schema_version": "biomedpilot.legacy_standardized_asset_candidate_validation.v1",
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "status": "blocked" if blockers else "passed",
        "blockers": _dedupe(blockers),
        "warnings": _dedupe(warnings),
    }


def _candidates_from_manifest(manifest: dict[str, Any], manifest_path: Path) -> list[dict[str, Any]]:
    source = str(manifest.get("source") or "")
    output_type = str(manifest.get("output_asset_type") or "")
    provenance = manifest.get("provenance") if isinstance(manifest.get("provenance"), dict) else {}
    if source == "geo" or output_type == "geo_detection_acquisition_candidate":
        return _geo_candidates(manifest, manifest_path, provenance)
    if source == "tcga_gdc" or output_type == "tcga_gdc_acquisition_manifest_candidate":
        return _file_manifest_candidates(manifest, manifest_path, provenance, source="tcga_gdc")
    if source == "gtex" or output_type == "gtex_acquisition_manifest_candidate":
        return _file_manifest_candidates(manifest, manifest_path, provenance, source="gtex")
    return [_candidate(manifest, manifest_path, source=source or "legacy", asset_type=f"{output_type}_asset_candidate", asset_role="acquisition_manifest", path_or_query=str(manifest.get("input_path_or_query") or ""), provenance=provenance)]


def _geo_candidates(manifest: dict[str, Any], manifest_path: Path, provenance: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in provenance.get("candidate_expression_files") or []:
        candidates.append(_candidate(manifest, manifest_path, source="geo", asset_type="geo_expression_matrix_candidate", asset_role="expression_matrix", path_or_query=str(path), provenance=provenance))
    for path in provenance.get("candidate_metadata_files") or []:
        candidates.append(_candidate(manifest, manifest_path, source="geo", asset_type="geo_sample_metadata_candidate", asset_role="sample_metadata", path_or_query=str(path), provenance=provenance))
    for path in provenance.get("candidate_annotation_files") or []:
        candidates.append(_candidate(manifest, manifest_path, source="geo", asset_type="geo_platform_annotation_candidate", asset_role="feature_annotation", path_or_query=str(path), provenance=provenance))
    if not candidates:
        candidates.append(_candidate(manifest, manifest_path, source="geo", asset_type="geo_detection_manifest_candidate", asset_role="acquisition_manifest", path_or_query=str(manifest.get("input_path_or_query") or ""), provenance=provenance))
    return candidates


def _file_manifest_candidates(manifest: dict[str, Any], manifest_path: Path, provenance: dict[str, Any], *, source: str) -> list[dict[str, Any]]:
    entries = provenance.get("file_manifest_entries") if isinstance(provenance.get("file_manifest_entries"), list) else []
    candidates: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        path_or_query = str(entry.get("file_name") or entry.get("file_id") or entry.get("resource_name") or manifest.get("input_path_or_query") or "")
        candidates.append(
            _candidate(
                manifest,
                manifest_path,
                source=source,
                asset_type=_asset_type_for_file_entry(source, entry),
                asset_role=_asset_role_for_file_entry(source, entry),
                path_or_query=path_or_query,
                provenance={**provenance, "file_manifest_entry": entry},
            )
        )
    if not candidates:
        candidates.append(_candidate(manifest, manifest_path, source=source, asset_type=f"{source}_manifest_candidate", asset_role="acquisition_manifest", path_or_query=str(manifest.get("input_path_or_query") or ""), provenance=provenance))
    return candidates


def _asset_type_for_file_entry(source: str, entry: dict[str, Any]) -> str:
    text = " ".join(str(entry.get(key) or "") for key in ("data_type", "file_name", "file_type", "resource_name", "guessed_role")).lower()
    if source == "tcga_gdc":
        if "clinical" in text:
            return "tcga_clinical_metadata_candidate"
        if "expression" in text or "counts" in text or "rna-seq" in text:
            return "tcga_expression_matrix_candidate"
        return "tcga_gdc_file_candidate"
    if source == "gtex":
        if "annotation" in text or "sample" in text:
            return "gtex_sample_metadata_candidate"
        return "gtex_expression_matrix_candidate"
    return f"{source}_file_candidate"


def _asset_role_for_file_entry(source: str, entry: dict[str, Any]) -> str:
    asset_type = _asset_type_for_file_entry(source, entry)
    if "clinical" in asset_type:
        return "clinical_metadata"
    if "metadata" in asset_type:
        return "sample_metadata"
    if "expression" in asset_type:
        return "expression_matrix"
    return "acquisition_manifest"


def _candidate(
    manifest: dict[str, Any],
    manifest_path: Path,
    *,
    source: str,
    asset_type: str,
    asset_role: str,
    path_or_query: str,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    manifest_blockers = [str(item) for item in manifest.get("blockers") or [] if str(item)]
    manifest_warnings = [str(item) for item in manifest.get("warnings") or [] if str(item)]
    seed = "|".join([str(manifest.get("adapter_id") or ""), source, asset_type, asset_role, path_or_query])
    return {
        "schema_version": LEGACY_ASSET_CANDIDATE_SCHEMA_VERSION,
        "created_at": _now(),
        "candidate_id": f"legacy-asset-candidate-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}",
        "source": source,
        "source_adapter_id": str(manifest.get("adapter_id") or ""),
        "source_manifest_path": str(manifest_path),
        "source_manifest_checksum": str(manifest.get("checksum") or ""),
        "asset_type": asset_type,
        "asset_role": asset_role,
        "path_or_query": path_or_query,
        "provenance": {
            "legacy_module_reference": manifest.get("legacy_module_reference", ""),
            "source_version": manifest.get("source_version", ""),
            "source_output_asset_type": manifest.get("output_asset_type", ""),
            "source_provenance": provenance,
        },
        "warnings": _dedupe(manifest_warnings + ["legacy_asset_candidate_requires_standardization_validation"]),
        "blockers": _dedupe(manifest_blockers),
        "validation_status": "blocked" if manifest_blockers else "candidate_only",
        "formal_analysis_ready": False,
        "result_semantics": "not_a_result",
        "report_ready_eligible": False,
        "can_fill_tcga_normal_control": False,
        "next_required_gates": ["standardization_validation", "b8_analysis_input_resolver"],
    }


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
