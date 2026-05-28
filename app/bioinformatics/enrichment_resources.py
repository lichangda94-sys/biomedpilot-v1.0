from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gene_set_resources import GENE_SET_REGISTRY, list_downloadable_gene_set_resources, validate_gene_set_registry


ENRICHMENT_RESOURCE_REGISTRY_SCHEMA_VERSION = "biomedpilot.enrichment_resource_registry.v1"
ENRICHMENT_RESOURCE_GATE_SCHEMA_VERSION = "biomedpilot.enrichment_resource_gate.v1"
SUPPORTED_ENRICHMENT_ANALYSIS_TYPES = {"ora", "gsea_preranked"}


def build_enrichment_resource_registry(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    validation = validate_gene_set_registry(root)
    resources = [_resource_record(root, item) for item in validation.get("resources", []) if isinstance(item, dict)]
    selected = next((item for item in resources if item.get("selected_for_gsea")), {})
    return {
        "schema_version": ENRICHMENT_RESOURCE_REGISTRY_SCHEMA_VERSION,
        "created_at": _now(),
        "project_root": str(root),
        "source_registry_path": str(root / GENE_SET_REGISTRY),
        "resource_count": len(resources),
        "selected_resource_id": str(selected.get("resource_id") or ""),
        "resources": resources,
        "known_resource_catalog": _known_resource_catalog(root),
        "registry_policy": "local_registry_only_no_silent_download",
        "network_downloads": False,
        "auto_install": False,
        "warnings": list(validation.get("warnings", []) or []),
        "blockers": [],
    }


def build_enrichment_resource_gate(
    project_root: str | Path,
    *,
    analysis_type: str,
    required_species: str = "human",
    required_gene_id_type: str = "symbol",
    resource_id: str = "",
) -> dict[str, Any]:
    registry = build_enrichment_resource_registry(project_root)
    resources = [item for item in registry.get("resources", []) if isinstance(item, dict)]
    selected = _select_resource(resources, resource_id)
    blockers: list[str] = []
    warnings: list[str] = list(registry.get("warnings", []) or [])
    if analysis_type not in SUPPORTED_ENRICHMENT_ANALYSIS_TYPES:
        blockers.append(f"unsupported_enrichment_analysis_type:{analysis_type}")
    if not selected:
        blockers.append("enrichment_resource_not_selected")
    else:
        blockers.extend(_resource_blockers(selected, analysis_type=analysis_type, required_species=required_species, required_gene_id_type=required_gene_id_type))
        warnings.extend(_resource_warnings(selected))
    return {
        "schema_version": ENRICHMENT_RESOURCE_GATE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "analysis_type": analysis_type,
        "required_species": required_species,
        "required_gene_id_type": required_gene_id_type,
        "selected_resource_id": str(selected.get("resource_id") or resource_id),
        "selected_resource": selected,
        "resource_registry": registry,
        "required_fields": [
            "resource_id",
            "collection_type",
            "species",
            "gene_id_type",
            "source_name",
            "source_url",
            "license_note",
            "version",
            "checksum",
            "gene_set_count",
            "local_path",
        ],
        "semantic_boundary": "resource_gate_only_not_enrichment_execution",
        "network_downloads": False,
        "auto_install": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _resource_record(root: Path, resource: dict[str, Any]) -> dict[str, Any]:
    local_path = _resolve_local_path(root, str(resource.get("local_path") or ""))
    checksum = str(resource.get("checksum") or "")
    file_size = int(resource.get("file_size") or 0)
    if local_path and local_path.is_file():
        checksum = checksum or _sha256(local_path)
        file_size = file_size or local_path.stat().st_size
    status = str(resource.get("status") or "missing")
    allowed = []
    if status == "available":
        allowed = ["ora", "gsea_preranked"]
    return {
        "resource_id": str(resource.get("resource_id") or ""),
        "name": str(resource.get("name") or ""),
        "collection_type": str(resource.get("collection_type") or "Unknown"),
        "species": str(resource.get("species") or "unknown"),
        "gene_id_type": str(resource.get("gene_id_type") or "unknown"),
        "source_type": str(resource.get("source_type") or "configured"),
        "source_name": str(resource.get("source_name") or ""),
        "source_url": str(resource.get("source_url") or ""),
        "license_note": str(resource.get("license_note") or ""),
        "version": str(resource.get("version") or ""),
        "checksum": checksum,
        "checksum_algorithm": "sha256" if checksum else "",
        "file_size": file_size,
        "local_path": str(local_path or ""),
        "status": status,
        "selected_for_gsea": bool(resource.get("selected_for_gsea")),
        "gene_set_count": int(resource.get("gene_set_count") or 0),
        "validation_summary": str(resource.get("validation_summary") or ""),
        "allowed_analysis_types": allowed,
        "resource_semantics": "enrichment_gene_set_resource_not_analysis_result",
    }


def _known_resource_catalog(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in list_downloadable_gene_set_resources(root):
        rows.append(
            {
                "resource_id": str(item.get("resource_id") or ""),
                "name": str(item.get("name") or ""),
                "collection_type": str(item.get("collection_type") or "Unknown"),
                "species": str(item.get("species") or "unknown"),
                "gene_id_type": str(item.get("gene_id_type") or "unknown"),
                "source_name": str(item.get("source_name") or ""),
                "source_url": str(item.get("source_url") or ""),
                "license_note": str(item.get("license_note") or ""),
                "downloadable": bool(item.get("downloadable")),
                "operation": str(item.get("operation") or ""),
                "policy": "user_triggered_only_no_silent_download",
                "local_status": str(item.get("local_status") or ""),
                "local_version": str(item.get("local_version") or ""),
            }
        )
    return rows


def _select_resource(resources: list[dict[str, Any]], resource_id: str) -> dict[str, Any]:
    if resource_id:
        return next((item for item in resources if str(item.get("resource_id") or "") == resource_id), {})
    return next((item for item in resources if item.get("selected_for_gsea")), {})


def _resource_blockers(resource: dict[str, Any], *, analysis_type: str, required_species: str, required_gene_id_type: str) -> list[str]:
    blockers: list[str] = []
    if resource.get("status") != "available":
        blockers.append(f"enrichment_resource_{resource.get('status') or 'missing'}")
    if analysis_type not in resource.get("allowed_analysis_types", []):
        blockers.append(f"resource_not_allowed_for:{analysis_type}")
    species = str(resource.get("species") or "unknown")
    if required_species and species not in {required_species, "all_species"}:
        blockers.append(f"resource_species_mismatch:{species}!={required_species}")
    gene_id_type = str(resource.get("gene_id_type") or "unknown")
    if required_gene_id_type and gene_id_type != required_gene_id_type:
        blockers.append(f"resource_gene_id_type_mismatch:{gene_id_type}!={required_gene_id_type}")
    if not resource.get("source_name"):
        blockers.append("resource_source_name_missing")
    if not resource.get("license_note"):
        blockers.append("resource_license_note_missing")
    if not resource.get("version"):
        blockers.append("resource_version_missing")
    if not resource.get("checksum"):
        blockers.append("resource_checksum_missing")
    if int(resource.get("gene_set_count") or 0) <= 0:
        blockers.append("resource_gene_set_count_missing")
    if not resource.get("local_path"):
        blockers.append("resource_local_path_missing")
    return blockers


def _resource_warnings(resource: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not resource.get("source_url"):
        warnings.append("resource_source_url_missing")
    if str(resource.get("collection_type") or "Unknown") == "Unknown":
        warnings.append("resource_collection_type_unknown")
    return warnings


def _resolve_local_path(root: Path, value: str) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    resolved = path if path.is_absolute() else root / path
    try:
        resolved.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    return resolved.resolve()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
