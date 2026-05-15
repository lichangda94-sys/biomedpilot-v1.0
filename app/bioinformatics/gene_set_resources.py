from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


GENE_SET_REGISTRY = Path("user_data") / "bioinformatics" / "gene_sets" / "gene_set_registry.json"
LEGACY_GENE_SET_REGISTRY = Path("manifests") / "gene_set_registry.json"
GENE_SET_REPOSITORY = Path("user_data") / "bioinformatics" / "gene_sets"
CUSTOM_GENE_SET_REPOSITORY = GENE_SET_REPOSITORY / "custom"
GENE_SET_REGISTRY_SCHEMA_VERSION = "biomedpilot.gene_set_registry.v1"

RESOURCE_STATUSES = {"available", "missing", "invalid", "pending_download"}
COLLECTION_TYPES = {"GO_BP", "GO_CC", "GO_MF", "Reactome", "KEGG", "Hallmark", "Custom", "Unknown"}
GENE_ID_TYPES = {"symbol", "entrez", "ensembl", "unknown"}
SPECIES_VALUES = {"human", "mouse", "other", "unknown"}
SOURCE_TYPES = {"user_import", "downloaded", "configured", "bundled_stub"}


@dataclass(frozen=True)
class GmtValidationResult:
    is_valid: bool
    status: str
    validation_summary: str
    gene_set_count: int
    gene_count_preview: tuple[dict[str, object], ...]
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "is_valid": self.is_valid,
            "status": self.status,
            "validation_summary": self.validation_summary,
            "gene_set_count": self.gene_set_count,
            "gene_count_preview": [dict(item) for item in self.gene_count_preview],
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def registry_path(project_root: str | Path) -> Path:
    return Path(project_root).expanduser().resolve() / GENE_SET_REGISTRY


def gene_set_repository_path(project_root: str | Path) -> Path:
    return Path(project_root).expanduser().resolve() / GENE_SET_REPOSITORY


def initialize_gene_set_registry(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = _load_registry(root)
    _write_registry(root, registry)
    return registry


def list_local_gene_sets(project_root: str | Path) -> list[dict[str, Any]]:
    registry = _load_registry(project_root)
    return [dict(item) for item in registry.get("resources", []) if isinstance(item, dict)]


def get_gene_set(project_root: str | Path, resource_id: str) -> dict[str, Any] | None:
    for resource in list_local_gene_sets(project_root):
        if str(resource.get("resource_id") or "") == resource_id:
            return resource
    return None


def get_selected_gene_set(project_root: str | Path) -> dict[str, Any] | None:
    for resource in list_local_gene_sets(project_root):
        if resource.get("selected_for_gsea"):
            return resource
    return None


def select_gene_set(project_root: str | Path, resource_id: str) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    validation = validate_gene_set_registry(root)
    resources = [dict(item) for item in validation.get("resources", []) if isinstance(item, dict)]
    matched = False
    selected_resource: dict[str, Any] | None = None
    for resource in resources:
        if str(resource.get("resource_id") or "") == resource_id:
            matched = True
            if str(resource.get("status") or "") != "available":
                raise ValueError(f"Gene set resource is not available: {resource_id}")
            resource["selected_for_gsea"] = True
            resource["updated_at"] = _now()
            selected_resource = resource
        else:
            resource["selected_for_gsea"] = False
    if not matched:
        raise ValueError(f"Unknown gene set resource: {resource_id}")
    registry = _load_registry(root)
    registry["resources"] = resources
    registry["updated_at"] = _now()
    _write_registry(root, registry)
    return selected_resource or {}


def unselect_gene_set(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = _load_registry(root)
    resources = []
    for raw in registry.get("resources", []):
        if not isinstance(raw, dict):
            continue
        resource = _normalize_resource(raw)
        if resource.get("selected_for_gsea"):
            resource["selected_for_gsea"] = False
            resource["updated_at"] = _now()
        resources.append(resource)
    registry["resources"] = resources
    registry["updated_at"] = _now()
    _write_registry(root, registry)
    return registry


def remove_gene_set(project_root: str | Path, resource_id: str) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = _load_registry(root)
    resources: list[dict[str, Any]] = []
    removed: dict[str, Any] | None = None
    for raw in registry.get("resources", []):
        if not isinstance(raw, dict):
            continue
        resource = _normalize_resource(raw)
        if str(resource.get("resource_id") or "") == resource_id:
            removed = resource
            continue
        resources.append(resource)
    if removed is None:
        raise ValueError(f"Unknown gene set resource: {resource_id}")
    local_path = _resource_local_path(root, str(removed.get("local_path") or ""))
    if local_path is not None and _is_within(local_path, root / GENE_SET_REPOSITORY) and local_path.exists():
        local_path.unlink()
    registry["resources"] = resources
    registry["updated_at"] = _now()
    _write_registry(root, registry)
    return {"removed_resource": removed, "resources": resources}


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
        local_path = _resource_local_path(root, str(resource.get("local_path") or ""))
        if local_path is None:
            resource["status"] = "invalid"
            resource["validation_summary"] = "local_path is outside the Bioinformatics project or is empty."
            warnings.append(f"invalid_local_path:{resource.get('resource_id')}")
        elif not local_path.is_file():
            resource["status"] = "missing"
            resource["validation_summary"] = "Registered GMT file is missing."
            warnings.append(f"missing_local_path:{resource.get('resource_id')}")
        elif str(resource.get("status") or "") in {"available", "missing"}:
            validation = validate_gmt_file(local_path)
            resource["status"] = validation.status
            resource["validation_summary"] = validation.validation_summary
            resource["gene_set_count"] = validation.gene_set_count
            resource["gene_count_preview"] = [dict(item) for item in validation.gene_count_preview]
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
        "selected_resource": next((dict(item) for item in resources if item.get("selected_for_gsea")), {}),
        "warnings": warnings,
        "resources": resources,
    }


def validate_gmt_file(path: str | Path) -> GmtValidationResult:
    gmt_path = Path(path).expanduser()
    errors: list[str] = []
    warnings: list[str] = []
    preview: list[dict[str, object]] = []
    if not gmt_path.exists():
        return GmtValidationResult(False, "missing", "GMT file does not exist.", 0, (), ("file_missing",), ())
    if not gmt_path.is_file():
        return GmtValidationResult(False, "invalid", "GMT path is not a file.", 0, (), ("not_a_file",), ())
    if gmt_path.suffix.lower() != ".gmt":
        warnings.append("non_gmt_extension")
    try:
        text = gmt_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = gmt_path.read_text(encoding="utf-8", errors="replace")
            warnings.append("encoding_replacement_used")
        except OSError as exc:
            return GmtValidationResult(False, "invalid", f"Failed to read GMT file: {exc}", 0, (), ("read_failed",), tuple(warnings))
    except OSError as exc:
        return GmtValidationResult(False, "invalid", f"Failed to read GMT file: {exc}", 0, (), ("read_failed",), tuple(warnings))
    if not text.strip():
        return GmtValidationResult(False, "invalid", "GMT file is empty.", 0, (), ("empty_file",), tuple(warnings))
    gene_set_count = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = line.rstrip("\n\r").split("\t")
        if len(parts) < 3:
            errors.append(f"line_{line_number}:expected_name_description_and_gene")
            continue
        name = parts[0].strip()
        genes = [gene.strip() for gene in parts[2:] if gene.strip()]
        if not name:
            errors.append(f"line_{line_number}:missing_gene_set_name")
            continue
        if not genes:
            errors.append(f"line_{line_number}:missing_genes")
            continue
        gene_set_count += 1
        if len(preview) < 5:
            preview.append({"gene_set_name": name, "gene_count": len(genes), "gene_preview": genes[:5]})
    if errors:
        summary = f"Invalid GMT: {len(errors)} malformed line(s); {gene_set_count} valid gene set(s) parsed."
        return GmtValidationResult(False, "invalid", summary, gene_set_count, tuple(preview), tuple(errors[:20]), tuple(warnings))
    if gene_set_count <= 0:
        return GmtValidationResult(False, "invalid", "GMT file contains no valid gene sets.", 0, tuple(preview), ("no_valid_gene_sets",), tuple(warnings))
    summary = f"Valid GMT: {gene_set_count} gene set(s) parsed."
    if warnings:
        summary = f"{summary} Warnings: {', '.join(warnings)}."
    return GmtValidationResult(True, "available", summary, gene_set_count, tuple(preview), (), tuple(warnings))


def import_gmt_file(project_root: str | Path, source_path: str | Path, metadata: dict[str, object] | None = None) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    source = Path(source_path).expanduser().resolve()
    validation = validate_gmt_file(source)
    metadata_payload = dict(metadata or {})
    resource_id = _safe_resource_id(str(metadata_payload.get("resource_id") or source.stem))
    repository = root / CUSTOM_GENE_SET_REPOSITORY
    repository.mkdir(parents=True, exist_ok=True)
    target = _unique_resource_path(repository, resource_id)
    shutil.copy2(source, target)
    local_path = target.relative_to(root)
    now = _now()
    resource = _normalize_resource(
        {
            "resource_id": target.stem,
            "name": str(metadata_payload.get("name") or source.stem or "Imported GMT"),
            "collection_type": str(metadata_payload.get("collection_type") or "Custom"),
            "species": str(metadata_payload.get("species") or "unknown"),
            "gene_id_type": str(metadata_payload.get("gene_id_type") or "unknown"),
            "source_type": "user_import",
            "source_name": str(metadata_payload.get("source_name") or source.name),
            "source_url": str(metadata_payload.get("source_url") or ""),
            "license_note": str(metadata_payload.get("license_note") or ""),
            "version": str(metadata_payload.get("version") or ""),
            "created_at": now,
            "updated_at": now,
            "local_path": str(local_path),
            "status": validation.status,
            "selected_for_gsea": False,
            "validation_summary": validation.validation_summary,
            "gene_set_count": validation.gene_set_count,
            "gene_count_preview": [dict(item) for item in validation.gene_count_preview],
        }
    )
    registry = _load_registry(root)
    resources = [_normalize_resource(item) for item in registry.get("resources", []) if isinstance(item, dict)]
    resources = [item for item in resources if str(item.get("resource_id") or "") != str(resource.get("resource_id") or "")]
    resources.append(resource)
    registry["resources"] = resources
    registry["updated_at"] = now
    _write_registry(root, registry)
    return {"resource": resource, "validation": validation.to_dict(), "registry": registry, "copied_path": str(target)}


def get_selected_gene_set_for_gsea(project_root: str | Path) -> dict[str, Any] | None:
    validate_gene_set_registry(project_root)
    return get_selected_gene_set(project_root)


def validate_selected_gene_set_for_gsea(project_root: str | Path) -> dict[str, Any]:
    return build_gsea_gene_set_readiness(project_root)


def build_gsea_gene_set_readiness(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    validation = validate_gene_set_registry(root)
    selected = validation.get("selected_resource")
    blocking_errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(selected, dict) or not selected:
        blocking_errors.append("gsea_gene_set_not_selected")
        return {
            "selected": False,
            "resource_id": "",
            "name": "",
            "local_path": "",
            "species": "unknown",
            "gene_id_type": "unknown",
            "status": "not_selected",
            "gene_set_count": 0,
            "blocking_errors": blocking_errors,
            "warnings": warnings,
        }
    status = str(selected.get("status") or "missing")
    local_path = _resource_local_path(root, str(selected.get("local_path") or ""))
    if status != "available":
        blocking_errors.append(f"gsea_gene_set_{status}")
    if local_path is None or not local_path.is_file():
        blocking_errors.append("gsea_gene_set_file_missing")
    if str(selected.get("gene_id_type") or "unknown") == "unknown":
        warnings.append("gene_id_type_unknown")
    return {
        "selected": True,
        "resource_id": str(selected.get("resource_id") or ""),
        "name": str(selected.get("name") or ""),
        "local_path": str(local_path or ""),
        "species": str(selected.get("species") or "unknown"),
        "gene_id_type": str(selected.get("gene_id_type") or "unknown"),
        "status": status,
        "gene_set_count": int(selected.get("gene_set_count") or 0),
        "blocking_errors": blocking_errors,
        "warnings": warnings,
    }


def _load_registry(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    path = root / GENE_SET_REGISTRY
    legacy_path = root / LEGACY_GENE_SET_REGISTRY
    if not path.exists() and legacy_path.exists():
        payload = _read_registry_payload(legacy_path, root)
    elif path.exists():
        payload = _read_registry_payload(path, root)
    else:
        payload = _empty_registry(root)
    payload["resources"] = [_normalize_resource(item) for item in payload.get("resources", []) if isinstance(item, dict)]
    return payload


def _read_registry_payload(path: Path, root: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_registry(root)
    if not isinstance(payload, dict):
        return _empty_registry(root)
    payload.setdefault("schema_version", GENE_SET_REGISTRY_SCHEMA_VERSION)
    payload.setdefault("project_root", str(root))
    payload.setdefault("created_at", _now())
    payload.setdefault("updated_at", _now())
    payload.setdefault("resources", [])
    return payload


def _write_registry(project_root: str | Path, payload: dict[str, Any]) -> None:
    root = Path(project_root).expanduser().resolve()
    path = root / GENE_SET_REGISTRY
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["schema_version"] = GENE_SET_REGISTRY_SCHEMA_VERSION
    payload["project_root"] = str(root)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
        "validation_summary": str(resource.get("validation_summary") or ""),
        "gene_set_count": _int_or_zero(resource.get("gene_set_count")),
        "gene_count_preview": [dict(item) for item in resource.get("gene_count_preview", []) or [] if isinstance(item, dict)],
    }
    if normalized["collection_type"] not in COLLECTION_TYPES:
        normalized["collection_type"] = "Unknown"
    if normalized["species"] not in SPECIES_VALUES:
        normalized["species"] = "unknown"
    if normalized["gene_id_type"] not in GENE_ID_TYPES:
        normalized["gene_id_type"] = "unknown"
    if normalized["source_type"] not in SOURCE_TYPES:
        normalized["source_type"] = "configured"
    if normalized["status"] not in RESOURCE_STATUSES:
        normalized["status"] = "invalid"
    if not normalized["resource_id"]:
        normalized["resource_id"] = f"gene_set_{uuid4().hex[:10]}"
    return normalized


def _resource_local_path(root: Path, local_path: str) -> Path | None:
    if not local_path:
        return None
    candidate = Path(local_path).expanduser()
    resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    if not _is_within(resolved, root):
        return None
    return resolved


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _unique_resource_path(repository: Path, resource_id: str) -> Path:
    candidate = repository / f"{resource_id}.gmt"
    if not candidate.exists():
        return candidate
    suffix = uuid4().hex[:8]
    return repository / f"{resource_id}_{suffix}.gmt"


def _safe_resource_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip()).strip("._-")
    return cleaned[:80] or f"gene_set_{uuid4().hex[:10]}"


def _int_or_zero(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
