from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GENE_SET_REGISTRY = Path("manifests") / "gene_set_registry.json"
GENE_SET_REGISTRY_SCHEMA_VERSION = "biomedpilot.gene_set_registry.v1"

RESOURCE_STATUSES = {"available", "missing", "invalid", "pending_download"}
COLLECTION_TYPES = {"GO_BP", "GO_CC", "GO_MF", "Reactome", "KEGG", "Hallmark", "Custom"}
GENE_ID_TYPES = {"symbol", "entrez", "ensembl", "unknown"}
SOURCE_TYPES = {"user_import", "downloaded", "configured"}


def list_local_gene_sets(project_root: str | Path) -> list[dict[str, Any]]:
    registry = _load_registry(project_root)
    return [dict(item) for item in registry.get("resources", []) if isinstance(item, dict)]


def select_gene_set(project_root: str | Path, resource_id: str) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = _load_registry(root)
    resources = [dict(item) for item in registry.get("resources", []) if isinstance(item, dict)]
    matched = False
    for resource in resources:
        if str(resource.get("resource_id") or "") == resource_id:
            matched = True
            resource["selected_for_gsea"] = True
            resource["updated_at"] = _now()
        else:
            resource["selected_for_gsea"] = False
    if not matched:
        raise ValueError(f"Unknown gene set resource: {resource_id}")
    registry["resources"] = resources
    registry["updated_at"] = _now()
    _write_registry(root, registry)
    return registry


def get_selected_gene_set(project_root: str | Path) -> dict[str, Any] | None:
    for resource in list_local_gene_sets(project_root):
        if resource.get("selected_for_gsea"):
            return resource
    return None


def validate_gene_set_registry(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = _load_registry(root)
    resources: list[dict[str, Any]] = []
    warnings: list[str] = []
    selected_count = 0
    for raw in registry.get("resources", []):
        if not isinstance(raw, dict):
            warnings.append("invalid_resource_entry")
            continue
        resource = _normalize_resource(raw)
        local_path = Path(str(resource.get("local_path") or "")).expanduser()
        if resource["status"] == "available" and resource.get("local_path") and not local_path.is_file():
            resource["status"] = "missing"
            warnings.append(f"missing_local_path:{resource.get('resource_id')}")
        if resource.get("selected_for_gsea"):
            selected_count += 1
        resources.append(resource)
    if selected_count > 1:
        first = True
        for resource in resources:
            if not resource.get("selected_for_gsea"):
                continue
            if first:
                first = False
                continue
            resource["selected_for_gsea"] = False
        warnings.append("multiple_selected_resources_normalized")
    registry["resources"] = resources
    registry["updated_at"] = _now()
    _write_registry(root, registry)
    return {
        "schema_version": GENE_SET_REGISTRY_SCHEMA_VERSION,
        "registry_path": str(root / GENE_SET_REGISTRY),
        "resource_count": len(resources),
        "selected_resource": get_selected_gene_set(root) or {},
        "warnings": warnings,
        "resources": resources,
    }


def _load_registry(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    path = root / GENE_SET_REGISTRY
    if not path.exists():
        return _empty_registry(root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_registry(root)
    if not isinstance(payload, dict):
        return _empty_registry(root)
    payload.setdefault("schema_version", GENE_SET_REGISTRY_SCHEMA_VERSION)
    payload.setdefault("project_root", str(root))
    payload.setdefault("resources", [])
    payload.setdefault("created_at", _now())
    payload.setdefault("updated_at", _now())
    return payload


def _write_registry(project_root: str | Path, payload: dict[str, Any]) -> None:
    root = Path(project_root).expanduser().resolve()
    path = root / GENE_SET_REGISTRY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _empty_registry(root: Path) -> dict[str, Any]:
    now = _now()
    return {
        "schema_version": GENE_SET_REGISTRY_SCHEMA_VERSION,
        "project_root": str(root),
        "created_at": now,
        "updated_at": now,
        "resources": [],
    }


def _normalize_resource(resource: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "resource_id": str(resource.get("resource_id") or ""),
        "name": str(resource.get("name") or "未命名 GSEA 基因集"),
        "collection_type": str(resource.get("collection_type") or "Custom"),
        "species": str(resource.get("species") or "unknown"),
        "gene_id_type": str(resource.get("gene_id_type") or "unknown"),
        "source_type": str(resource.get("source_type") or "user_import"),
        "source_name": str(resource.get("source_name") or ""),
        "source_url": str(resource.get("source_url") or ""),
        "license_note": str(resource.get("license_note") or ""),
        "version": str(resource.get("version") or ""),
        "created_at": str(resource.get("created_at") or _now()),
        "updated_at": str(resource.get("updated_at") or _now()),
        "local_path": str(resource.get("local_path") or ""),
        "status": str(resource.get("status") or "missing"),
        "selected_for_gsea": bool(resource.get("selected_for_gsea")),
    }
    if normalized["collection_type"] not in COLLECTION_TYPES:
        normalized["collection_type"] = "Custom"
    if normalized["gene_id_type"] not in GENE_ID_TYPES:
        normalized["gene_id_type"] = "unknown"
    if normalized["source_type"] not in SOURCE_TYPES:
        normalized["source_type"] = "user_import"
    if normalized["status"] not in RESOURCE_STATUSES:
        normalized["status"] = "invalid"
    return normalized


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
