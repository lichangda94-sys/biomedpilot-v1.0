from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.project_standardization import STANDARDIZED_REGISTRY, load_standardization_artifacts


STANDARDIZED_ASSET_SELECTION = Path("manifests") / "standardized_asset_selection.json"
SELECTION_SCHEMA_VERSION = "bioinformatics.standardized_asset_selection.v1"
SELECTABLE_ASSET_TYPES = {
    "count_matrix",
    "normalized_expression_matrix",
    "deg_result_table",
    "gene_annotation",
    "gene_identifier_metadata",
}


def standardized_asset_selection_path(project_root: str | Path) -> Path:
    return Path(project_root).expanduser().resolve() / STANDARDIZED_ASSET_SELECTION


def load_standardized_asset_selection(project_root: str | Path) -> dict[str, object] | None:
    path = standardized_asset_selection_path(project_root)
    if not path.is_file():
        return None
    payload = _read_json(path)
    return payload if payload.get("schema_version") == SELECTION_SCHEMA_VERSION else None


def build_asset_selection_context(project_root: str | Path) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    assets = _registry_assets(root)
    manifest = load_standardized_asset_selection(root) or {}
    selected_by_type = {
        str(item.get("asset_type") or ""): str(item.get("selected_asset_id") or "")
        for item in manifest.get("asset_selections", []) or []
        if isinstance(item, dict)
    }
    groups = [_asset_group(asset_type, candidates, selected_by_type.get(asset_type, "")) for asset_type, candidates in _group_assets(assets).items()]
    warnings = [str(item) for item in manifest.get("warnings", []) or [] if str(item)]
    warnings.extend(str(group.get("warning") or "") for group in groups if group.get("warning"))
    return {
        "schema_version": "bioinformatics.standardized_asset_selection_context.v1",
        "project_root": str(root),
        "selection_path": str(root / STANDARDIZED_ASSET_SELECTION),
        "source_registry_path": str(root / STANDARDIZED_REGISTRY),
        "selection_exists": bool(manifest),
        "assets": assets,
        "groups": groups,
        "warnings": list(dict.fromkeys(warnings)),
    }


def save_standardized_asset_selection(project_root: str | Path, selected_asset_ids: dict[str, str]) -> dict[str, object]:
    root = Path(project_root).expanduser().resolve()
    context = build_asset_selection_context(root)
    groups = [group for group in context.get("groups", []) or [] if isinstance(group, dict)]
    now = _now()
    existing = load_standardized_asset_selection(root) or {}
    selections = []
    warnings: list[str] = []
    for group in groups:
        asset_type = str(group.get("asset_type") or "")
        candidates = [asset for asset in group.get("candidates", []) or [] if isinstance(asset, dict)]
        candidate_ids = {str(asset.get("asset_id") or "") for asset in candidates}
        selected_asset_id = str(selected_asset_ids.get(asset_type) or group.get("selected_asset_id") or "")
        if not selected_asset_id and len(candidates) == 1:
            selected_asset_id = str(candidates[0].get("asset_id") or "")
        if selected_asset_id not in candidate_ids:
            if selected_asset_id:
                warnings.append(f"{asset_type} 选择的资产不存在：{selected_asset_id}")
            if len(candidates) > 1:
                warnings.append(f"{asset_type} 有多个候选资产，请选择默认资产。")
            continue
        selections.append(
            {
                "asset_type": asset_type,
                "selected_asset_id": selected_asset_id,
                "selection_state": "confirmed",
                "candidate_count": len(candidates),
                "reason": f"用户选择默认 {asset_type}",
            }
        )
    payload = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "generated_at": existing.get("generated_at") or now,
        "updated_at": now,
        "source_registry_path": str(root / STANDARDIZED_REGISTRY),
        "asset_selections": selections,
        "warnings": list(dict.fromkeys(warnings)),
    }
    _atomic_write_json(root / STANDARDIZED_ASSET_SELECTION, payload)
    return payload


def resolve_standardized_assets(
    project_root: str | Path,
    *,
    asset_types: set[str] | None = None,
    allow_recommended: bool = True,
) -> dict[str, object]:
    context = build_asset_selection_context(project_root)
    wanted = asset_types or SELECTABLE_ASSET_TYPES
    groups = [group for group in context.get("groups", []) or [] if isinstance(group, dict) and str(group.get("asset_type") or "") in wanted]
    assets: list[dict[str, object]] = []
    blocked_asset_types: list[str] = []
    warnings: list[str] = [str(item) for item in context.get("warnings", []) or [] if str(item)]
    for group in groups:
        state = str(group.get("selection_state") or "")
        asset_type = str(group.get("asset_type") or "")
        selected_asset = group.get("selected_asset")
        if state == "confirmed" and isinstance(selected_asset, dict):
            assets.append(selected_asset)
        elif state == "recommended_default" and allow_recommended and isinstance(selected_asset, dict):
            assets.append(selected_asset)
        elif state in {"needs_selection", "invalid"}:
            blocked_asset_types.append(asset_type)
            warnings.append(str(group.get("reason") or "请先在标准化资产页选择默认资产。"))
    return {
        "assets": assets,
        "groups": groups,
        "blocked_asset_types": list(dict.fromkeys(blocked_asset_types)),
        "warnings": list(dict.fromkeys(warnings)),
        "context": context,
    }


def selected_asset_by_type(project_root: str | Path, asset_type: str, *, allow_recommended: bool = True) -> dict[str, object] | None:
    resolved = resolve_standardized_assets(project_root, asset_types={asset_type}, allow_recommended=allow_recommended)
    for asset in resolved.get("assets", []) or []:
        if isinstance(asset, dict) and asset.get("asset_type") == asset_type:
            return asset
    return None


def selection_status_label(state: str) -> str:
    return {
        "recommended_default": "推荐默认",
        "needs_selection": "需要选择默认资产",
        "confirmed": "已确认默认",
        "invalid": "默认资产失效",
    }.get(state, state or "未知")


def _registry_assets(root: Path) -> list[dict[str, object]]:
    artifacts = load_standardization_artifacts(root)
    registry = artifacts.get("registry")
    if not isinstance(registry, dict):
        return []
    assets = registry.get("assets") or registry.get("standardized_assets") or []
    return [asset for asset in assets if isinstance(asset, dict)]


def _group_assets(assets: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for asset in assets:
        asset_type = str(asset.get("asset_type") or "")
        if asset_type in SELECTABLE_ASSET_TYPES:
            grouped.setdefault(asset_type, []).append(asset)
    return dict(sorted(grouped.items()))


def _asset_group(asset_type: str, candidates: list[dict[str, object]], selected_asset_id: str) -> dict[str, object]:
    candidate_by_id = {str(asset.get("asset_id") or ""): asset for asset in candidates}
    selected_asset = candidate_by_id.get(selected_asset_id) if selected_asset_id else None
    if selected_asset:
        state = "confirmed"
        reason = "已保存默认资产选择。"
        warning = ""
    elif selected_asset_id:
        state = "invalid"
        reason = "已保存的默认资产不存在，请重新选择。"
        warning = f"{asset_type} 默认资产失效：{selected_asset_id}"
    elif len(candidates) == 1:
        state = "recommended_default"
        selected_asset = candidates[0]
        selected_asset_id = str(selected_asset.get("asset_id") or "")
        reason = "单个候选资产，推荐作为默认。"
        warning = ""
    else:
        state = "needs_selection"
        reason = "多个同类资产，请先选择默认资产。"
        warning = ""
    return {
        "asset_type": asset_type,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "selected_asset_id": selected_asset_id,
        "selected_asset": selected_asset or {},
        "selection_state": state,
        "status_label": selection_status_label(state),
        "reason": reason,
        "warning": warning,
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    data = json.dumps(payload, ensure_ascii=False, indent=2)
    with temp_path.open("w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp_path, path)
