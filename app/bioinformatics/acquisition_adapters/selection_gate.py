from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEGACY_ASSET_SELECTION_MANIFEST_VERSION = "biomedpilot.legacy_asset_selection_manifest.v1"
LEGACY_ASSET_SELECTION_PATH = Path("standardized_data") / "asset_candidates" / "legacy_asset_selection_manifest.json"
REPOSITORY_MANIFEST = Path("standardized_data") / "repositories" / "repository_manifest.json"
FORMAL_RESULT_SEMANTICS = {"formal_computed_result", "report_ready_result"}
EXPRESSION_ASSET_TYPES = {"raw_count_matrix", "expression_matrix", "normalized_expression_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}
SAMPLE_METADATA_ASSET_TYPES = {"sample_metadata", "phenotype_metadata", "tcga_sample_metadata", "gtex_sample_metadata"}
FEATURE_ASSET_TYPES = {"feature_annotation", "platform_annotation", "gene_annotation", "platform_reference_hint"}
CLINICAL_ASSET_TYPES = {"clinical_metadata", "survival_metadata", "tcga_clinical_metadata"}
GROUP_DESIGN_ASSET_TYPES = {"group_design"}
DISPLAY_VALUE_TYPES = {"TPM", "FPKM", "FPKM-UQ", "CPM", "normalized", "normalized_expression", "normalized_or_log_expression", "log_expression", "log2_transformed"}
COUNT_VALUE_TYPES = {"count", "raw_count", "raw_counts", "count_like_candidate"}
PROBE_GENE_ID_TYPES = {"probe", "probe_id", "ID_REF", "id_ref", "unknown"}


def build_legacy_asset_selection_manifest(
    project_root: str | Path,
    *,
    expression_asset_id: str = "",
    sample_metadata_asset_id: str = "",
    feature_annotation_asset_id: str = "",
    clinical_asset_id: str = "",
    group_design_asset_id: str = "",
    confirmed_by_user: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    repository_manifest = _read_json(root / REPOSITORY_MANIFEST)
    assets = [asset for asset in repository_manifest.get("assets", []) or [] if isinstance(asset, dict)]
    selected = {
        "expression": _selection_entry(assets, expression_asset_id, EXPRESSION_ASSET_TYPES),
        "sample_metadata": _selection_entry(assets, sample_metadata_asset_id, SAMPLE_METADATA_ASSET_TYPES),
        "feature_annotation": _selection_entry(assets, feature_annotation_asset_id, FEATURE_ASSET_TYPES),
        "clinical": _selection_entry(assets, clinical_asset_id, CLINICAL_ASSET_TYPES),
        "group_design": _selection_entry(assets, group_design_asset_id, GROUP_DESIGN_ASSET_TYPES),
    }
    manifest = {
        "schema_version": LEGACY_ASSET_SELECTION_MANIFEST_VERSION,
        "created_at": _now(),
        "project_root": str(root),
        "source_repository_manifest": str(root / REPOSITORY_MANIFEST),
        "confirmed_by_user": bool(confirmed_by_user),
        "selected_assets": selected,
        "downstream_gate_preview": _downstream_gate_preview(selected),
        "formal_analysis_ready": False,
        "ready_for_formal_analysis": False,
        "result_semantics": "not_a_result",
        "report_ready_eligible": False,
        "downstream_contract": {
            "writes_repository_manifest_default_selection": True,
            "writes_analysis_input_repository": False,
            "writes_result_index": False,
            "ready_for_formal_analysis": False,
            "requires_b8_resolver_after_selection": True,
            "requires_deg_ready_or_task_specific_gate": True,
        },
    }
    validation = validate_legacy_asset_selection_manifest(manifest)
    return {**manifest, "validation": validation, "status": "blocked" if validation["selection_blockers"] else "selection_recorded_preflight_only"}


def validate_legacy_asset_selection_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    selection_blockers: list[str] = []
    downstream_blockers: list[str] = []
    warnings: list[str] = []
    if manifest.get("schema_version") != LEGACY_ASSET_SELECTION_MANIFEST_VERSION:
        selection_blockers.append("legacy_asset_selection_schema_version_mismatch")
    if manifest.get("confirmed_by_user") is not True:
        selection_blockers.append("legacy_asset_selection_requires_user_confirmation")
    if manifest.get("formal_analysis_ready") is not False or manifest.get("ready_for_formal_analysis") is not False:
        selection_blockers.append("legacy_asset_selection_must_not_be_formal_ready")
    if str(manifest.get("result_semantics") or "") in FORMAL_RESULT_SEMANTICS:
        selection_blockers.append("legacy_asset_selection_must_not_set_formal_result_semantics")
    if manifest.get("report_ready_eligible") is True:
        selection_blockers.append("legacy_asset_selection_report_ready_forbidden")
    contract = manifest.get("downstream_contract") if isinstance(manifest.get("downstream_contract"), dict) else {}
    if contract.get("writes_analysis_input_repository") is not False:
        selection_blockers.append("legacy_asset_selection_must_not_write_analysis_input_repository")
    if contract.get("writes_result_index") is not False:
        selection_blockers.append("legacy_asset_selection_must_not_write_result_index")
    if contract.get("ready_for_formal_analysis") is not False:
        selection_blockers.append("legacy_asset_selection_contract_must_not_be_formal_ready")
    selected = manifest.get("selected_assets") if isinstance(manifest.get("selected_assets"), dict) else {}
    for role, entry in selected.items():
        if not isinstance(entry, dict):
            selection_blockers.append(f"{role}_selection_must_be_object")
            continue
        selection_blockers.extend(str(item) for item in entry.get("selection_blockers", []) or [])
        warnings.extend(str(item) for item in entry.get("warnings", []) or [])
        asset = entry.get("asset") if isinstance(entry.get("asset"), dict) else {}
        if _is_formalish_asset(asset):
            selection_blockers.append(f"{role}_selection_formalish_asset_forbidden")
    preview = manifest.get("downstream_gate_preview") if isinstance(manifest.get("downstream_gate_preview"), dict) else {}
    downstream_blockers.extend(str(item) for item in preview.get("blockers", []) or [])
    warnings.extend(str(item) for item in preview.get("warnings", []) or [])
    return {
        "schema_version": "biomedpilot.legacy_asset_selection_manifest_validation.v1",
        "status": "blocked" if selection_blockers else "passed_with_downstream_blockers",
        "can_update_repository_manifest": not selection_blockers,
        "selection_blockers": _dedupe(selection_blockers),
        "downstream_blockers": _dedupe(downstream_blockers),
        "warnings": _dedupe(warnings),
    }


def apply_legacy_asset_selection_to_repository_manifest(project_root: str | Path, selection_manifest: dict[str, Any]) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    payload = dict(selection_manifest)
    validation = validate_legacy_asset_selection_manifest(payload)
    payload["validation"] = validation
    payload["status"] = "blocked" if validation["selection_blockers"] else "selection_recorded_preflight_only"
    _write_json(root / LEGACY_ASSET_SELECTION_PATH, payload)
    if not validation["can_update_repository_manifest"]:
        return {
            "status": "blocked",
            "selection_manifest_path": str(root / LEGACY_ASSET_SELECTION_PATH),
            "validation": validation,
            "repository_manifest_updated": False,
        }
    repository_manifest = _read_json(root / REPOSITORY_MANIFEST)
    selected = payload.get("selected_assets") if isinstance(payload.get("selected_assets"), dict) else {}
    selected_ids = {
        role: str(entry.get("asset_id") or "")
        for role, entry in selected.items()
        if isinstance(entry, dict) and entry.get("asset_id")
    }
    assets = []
    for asset in repository_manifest.get("assets", []) or []:
        if not isinstance(asset, dict):
            continue
        asset_id = str(asset.get("asset_id") or "")
        updated = dict(asset)
        updated["default_selected"] = asset_id in selected_ids.values()
        if asset_id in selected_ids.values():
            updated["legacy_selection_confirmed"] = True
            updated["analysis_ready"] = False
            updated["formal_analysis_ready"] = False
            updated["result_semantics"] = "not_a_result"
            updated["report_ready_eligible"] = False
        assets.append(updated)
    repository_manifest["assets"] = assets
    repository_manifest["default_asset_selection"] = _default_asset_selection_payload(selected)
    source_state = repository_manifest.get("source_state") if isinstance(repository_manifest.get("source_state"), dict) else {}
    repository_manifest["source_state"] = {
        **source_state,
        "legacy_asset_selection": True,
        "legacy_asset_selection_manifest": str(root / LEGACY_ASSET_SELECTION_PATH),
    }
    repository_manifest["legacy_asset_selection_contract"] = payload["downstream_contract"]
    _write_json(root / REPOSITORY_MANIFEST, repository_manifest)
    return {
        "status": "selection_recorded_preflight_only",
        "selection_manifest_path": str(root / LEGACY_ASSET_SELECTION_PATH),
        "validation": validation,
        "repository_manifest_updated": True,
        "repository_manifest_path": str(root / REPOSITORY_MANIFEST),
    }


def _selection_entry(assets: list[dict[str, Any]], asset_id: str, allowed_types: set[str]) -> dict[str, Any]:
    asset_id = str(asset_id or "")
    if not asset_id:
        return {"asset_id": "", "status": "not_selected", "asset": {}, "selection_blockers": [], "warnings": []}
    asset = next((item for item in assets if str(item.get("asset_id") or "") == asset_id), None)
    if not isinstance(asset, dict):
        return {"asset_id": asset_id, "status": "blocked", "asset": {}, "selection_blockers": ["selected_asset_not_found"], "warnings": []}
    blockers: list[str] = []
    warnings: list[str] = []
    asset_type = str(asset.get("asset_type") or "")
    repository = str(asset.get("repository") or "")
    if asset_type not in allowed_types and repository not in allowed_types:
        blockers.append("selected_asset_role_or_type_mismatch")
    if asset.get("analysis_ready") is not True:
        warnings.append("selected_legacy_asset_is_not_analysis_ready_until_downstream_gates_pass")
    return {"asset_id": asset_id, "status": "selected" if not blockers else "blocked", "asset": asset, "selection_blockers": blockers, "warnings": warnings}


def _downstream_gate_preview(selected: dict[str, dict[str, Any]]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    expression = _asset(selected, "expression")
    sample = _asset(selected, "sample_metadata")
    feature = _asset(selected, "feature_annotation")
    group = _asset(selected, "group_design")
    clinical = _asset(selected, "clinical")
    if not expression:
        blockers.append("missing_expression_asset_selection")
    if not sample:
        blockers.append("missing_sample_metadata_selection")
    if not group:
        blockers.append("missing_group_design_selection")
    value_type = _value_type(expression)
    gene_id_type = _gene_id_type(expression, feature)
    if value_type == "unknown":
        blockers.append("selected_expression_unknown_value_type")
    elif value_type in DISPLAY_VALUE_TYPES:
        warnings.append("display_value_type_requires_controlled_two_group_method_not_count_model")
    elif value_type in COUNT_VALUE_TYPES:
        warnings.append("raw_counts_allowed_for_controlled_two_group_mvp_not_count_model")
    else:
        blockers.append("selected_expression_unsupported_value_type")
    if gene_id_type in PROBE_GENE_ID_TYPES and not _mapping_confirmed(feature):
        blockers.append("selected_expression_probe_or_unknown_gene_mapping_missing")
    if expression and _is_gtex_asset(expression):
        blockers.append("gtex_expression_cannot_be_selected_as_tcga_normal_control")
    if clinical and not expression:
        blockers.append("clinical_selection_requires_expression_selection")
    return {
        "status": "blocked" if blockers else "passes_selection_preview_not_formal_ready",
        "blockers": _dedupe(blockers),
        "warnings": _dedupe(warnings),
        "value_type": value_type,
        "gene_id_type": gene_id_type,
        "formal_analysis_ready": False,
    }


def _default_asset_selection_payload(selected: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for role, entry in selected.items():
        if not isinstance(entry, dict) or not entry.get("asset_id"):
            continue
        payload[role] = {
            "selection_state": "user_confirmed_legacy_selection",
            "asset_id": entry["asset_id"],
            "reason": "selected through B16.4 legacy asset selection gate; downstream formal analysis gates still required",
        }
    return payload


def _asset(selected: dict[str, dict[str, Any]], role: str) -> dict[str, Any]:
    entry = selected.get(role) if isinstance(selected.get(role), dict) else {}
    asset = entry.get("asset") if isinstance(entry.get("asset"), dict) else {}
    return asset


def _value_type(asset: dict[str, Any]) -> str:
    value = str(asset.get("expression_value_type") or asset.get("value_type") or "")
    if not value:
        asset_type = str(asset.get("asset_type") or "")
        if asset_type == "raw_count_matrix":
            return "count"
        if asset_type in {"normalized_expression_matrix", "gtex_expression_matrix"}:
            return "normalized_expression"
    mapping = {"raw_counts": "count", "count_like_candidate": "count", "tpm": "TPM", "fpkm": "FPKM", "fpkm-uq": "FPKM-UQ"}
    return mapping.get(value.strip().lower(), value or "unknown")


def _gene_id_type(expression: dict[str, Any], feature: dict[str, Any]) -> str:
    for source in (expression, feature):
        value = str(source.get("gene_id_type") or "")
        if value:
            return value
    return "unknown"


def _mapping_confirmed(feature: dict[str, Any]) -> bool:
    if not feature:
        return False
    if str(feature.get("validation_status") or "") == "blocked":
        return False
    path = Path(str(feature.get("path") or feature.get("file_path") or "")).expanduser()
    if path.is_file() and path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            payload = {}
        if isinstance(payload, dict) and payload:
            return str(payload.get("mapping_quality") or "") == "confirmed_or_not_required" or bool(payload.get("confirmed"))
    return bool(feature.get("analysis_ready"))


def _is_gtex_asset(asset: dict[str, Any]) -> bool:
    text = " ".join(str(asset.get(key) or "") for key in ("asset_type", "source_file", "path", "label_zh", "source_acquisition_id")).lower()
    return "gtex" in text


def _is_formalish_asset(asset: dict[str, Any]) -> bool:
    if not asset:
        return False
    if asset.get("formal_analysis_ready") is True or asset.get("report_ready_eligible") is True:
        return True
    return str(asset.get("result_semantics") or "") in FORMAL_RESULT_SEMANTICS


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
