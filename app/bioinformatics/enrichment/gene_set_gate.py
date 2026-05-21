from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.gene_set_resources import get_gene_set, list_local_gene_sets, validate_gmt_file

from .models import ORA_GENE_SET_GATE_SCHEMA_VERSION


def build_ora_gene_set_resource_gate(
    project_root: str | Path,
    *,
    resource_id: str = "",
    resource_path: str | Path | None = None,
    expected_species: str = "unknown",
    expected_gene_id_type: str = "unknown",
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    resource = _resolve_resource(root, resource_id=resource_id, resource_path=resource_path)
    blockers: list[str] = []
    warnings: list[str] = []
    if not resource:
        blockers.append("ora_gene_set_resource_missing")
        return _payload(blockers=blockers, warnings=warnings)

    path = _resource_path(root, resource)
    if path is None:
        blockers.append("ora_gene_set_resource_path_missing")
    elif not path.is_file():
        blockers.append("ora_gene_set_resource_file_missing")
    validation = validate_gmt_file(path) if path is not None and path.exists() else None
    if validation is not None:
        blockers.extend(f"gmt:{item}" for item in validation.errors)
        warnings.extend(f"gmt:{item}" for item in validation.warnings)
        if validation.status != "available":
            blockers.append(f"ora_gene_set_gmt_{validation.status}")
        term_count = validation.gene_set_count
        gene_count = _gene_count(path) if validation.is_valid else 0
    else:
        term_count = int(resource.get("gene_set_count") or 0)
        gene_count = 0
    if term_count <= 0:
        blockers.append("ora_gene_set_empty_terms")
    if path is not None and path.exists() and gene_count <= 0:
        blockers.append("ora_gene_set_empty_genes")

    species = str(resource.get("species") or "unknown")
    gene_id_type = str(resource.get("gene_id_type") or "unknown")
    if _known(expected_species) and _known(species) and species not in {expected_species, "all_species"}:
        blockers.append(f"ora_gene_set_species_mismatch:{species}!={expected_species}")
    if _known(expected_gene_id_type) and _known(gene_id_type) and gene_id_type != expected_gene_id_type:
        blockers.append(f"ora_gene_set_gene_id_mismatch:{gene_id_type}!={expected_gene_id_type}")
    if _looks_like_msigdb(resource) and not str(resource.get("license_note") or resource.get("source_name") or resource.get("source") or ""):
        blockers.append("msigdb_manual_license_or_source_missing")
    elif _looks_like_msigdb(resource):
        warnings.append("msigdb_resource_requires_user_license_confirmation")

    payload = _payload(blockers=blockers, warnings=warnings)
    payload.update(
        {
            "gene_set_resource_id": str(resource.get("resource_id") or resource.get("id") or (path.stem if path else "")),
            "resource_type": str(resource.get("collection_type") or resource.get("resource_type") or "Custom"),
            "resource_name": str(resource.get("name") or resource.get("resource_name") or (path.stem if path else "")),
            "resource_path": str(path or ""),
            "resource_format": "GMT",
            "species": species,
            "gene_id_type": gene_id_type,
            "collection_name": str(resource.get("collection_name") or resource.get("collection_type") or "Custom"),
            "term_count": term_count,
            "gene_count": gene_count,
            "license_warning": "msigdb_resource_requires_user_license_confirmation" if _looks_like_msigdb(resource) else str(resource.get("license_note") or ""),
            "source": str(resource.get("source_name") or resource.get("source") or resource.get("source_type") or "local_gmt"),
            "checksum": _checksum(path) if path is not None and path.is_file() else str(resource.get("checksum") or ""),
        }
    )
    payload["validation_status"] = "blocked" if blockers else "passed"
    payload["status"] = payload["validation_status"]
    return payload


def _payload(*, blockers: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "schema_version": ORA_GENE_SET_GATE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gene_set_resource_id": "",
        "resource_type": "",
        "resource_name": "",
        "resource_path": "",
        "resource_format": "GMT",
        "species": "unknown",
        "gene_id_type": "unknown",
        "collection_name": "",
        "term_count": 0,
        "gene_count": 0,
        "license_warning": "",
        "source": "",
        "checksum": "",
        "validation_status": "blocked" if blockers else "passed",
        "status": "blocked" if blockers else "passed",
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
    }


def _resolve_resource(root: Path, *, resource_id: str, resource_path: str | Path | None) -> dict[str, Any]:
    if resource_id:
        resource = get_gene_set(root, resource_id)
        if resource:
            return dict(resource)
        for item in list_local_gene_sets(root):
            if str(item.get("resource_id") or "") == resource_id:
                return dict(item)
        return {}
    if resource_path is not None:
        path = Path(resource_path).expanduser()
        return {
            "resource_id": path.stem,
            "name": path.stem,
            "collection_type": "Custom",
            "species": "unknown",
            "gene_id_type": "unknown",
            "source": "local_gmt",
            "local_path": str(path),
        }
    return {}


def _resource_path(root: Path, resource: dict[str, Any]) -> Path | None:
    raw = str(resource.get("local_path") or resource.get("resource_path") or resource.get("path") or "")
    if not raw:
        return None
    path = Path(raw).expanduser()
    return path if path.is_absolute() else root / path


def _gene_count(path: Path) -> int:
    genes: set[str] = set()
    try:
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            parts = line.split("\t")
            genes.update(gene.strip() for gene in parts[2:] if gene.strip())
    except OSError:
        return 0
    return len(genes)


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _known(value: str) -> bool:
    return bool(value and value not in {"unknown", "all_species"})


def _looks_like_msigdb(resource: dict[str, Any]) -> bool:
    text = " ".join(str(resource.get(key) or "") for key in ("resource_id", "name", "collection_type", "source_name", "source"))
    return "msigdb" in text.lower()
