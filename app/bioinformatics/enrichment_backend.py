from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ENRICHMENT_BACKEND_GATE_SCHEMA_VERSION = "biomedpilot.enrichment_backend_gate.v1"
EXTERNAL_R_ENRICHMENT_DETECTION_SCHEMA_VERSION = "biomedpilot.external_enrichment_r_backend_detection.v1"
R_ENRICHMENT_BACKEND_DETECTION_FILENAME = "r_enrichment_backend_detection.json"

CORE_CAPABILITY_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "ora_enricher": ("clusterProfiler",),
    "ora_go": ("clusterProfiler", "AnnotationDbi", "org.Hs.eg.db"),
    "ora_kegg": ("clusterProfiler", "KEGGREST"),
    "ora_reactome": ("ReactomePA",),
    "gsea_preranked_fgsea": ("fgsea",),
    "gsea_preranked_clusterprofiler": ("clusterProfiler",),
    "enrichment_plot_dotplot": ("enrichplot", "ggplot2"),
    "enrichment_plot_barplot": ("enrichplot", "ggplot2"),
    "gsea_plot_curve": ("enrichplot", "ggplot2", "clusterProfiler"),
    "msigdbr_gene_set_catalog": ("msigdbr",),
}

DEFAULT_CAPABILITIES_BY_ANALYSIS_TYPE: dict[str, tuple[str, ...]] = {
    "ora": ("ora_enricher",),
    "ora_go": ("ora_go",),
    "ora_kegg": ("ora_kegg",),
    "ora_reactome": ("ora_reactome",),
    "gsea_preranked": ("gsea_preranked_fgsea",),
    "gsea_preranked_clusterprofiler": ("gsea_preranked_clusterprofiler",),
    "enrichment_plot": ("enrichment_plot_dotplot",),
    "gsea_plot": ("gsea_plot_curve",),
    "msigdbr_resource": ("msigdbr_gene_set_catalog",),
}


def build_enrichment_backend_gate(
    project_root: str | Path | None = None,
    *,
    analysis_type: str = "ora",
    required_capabilities: list[str] | tuple[str, ...] | None = None,
    detection_path: str | Path | None = None,
    search_roots: list[str | Path] | tuple[str | Path, ...] | None = None,
) -> dict[str, Any]:
    capabilities = tuple(required_capabilities or DEFAULT_CAPABILITIES_BY_ANALYSIS_TYPE.get(analysis_type, ()))
    blockers: list[str] = []
    warnings: list[str] = []
    if not capabilities:
        blockers.append(f"unsupported_enrichment_backend_analysis_type:{analysis_type}")

    resolved_path = _resolve_detection_path(project_root, detection_path=detection_path, search_roots=search_roots)
    if resolved_path is None:
        blockers.append("external_enrichment_backend_detection_missing")
        return _gate_payload(
            analysis_type=analysis_type,
            required_capabilities=capabilities,
            detection_path="",
            detection={},
            capability_rows=[],
            blockers=blockers,
            warnings=warnings,
        )

    detection, read_error = _read_detection_payload(resolved_path)
    if read_error:
        blockers.append(read_error)
        return _gate_payload(
            analysis_type=analysis_type,
            required_capabilities=capabilities,
            detection_path=str(resolved_path),
            detection={},
            capability_rows=[],
            blockers=blockers,
            warnings=warnings,
        )

    if detection.get("schema_version") != EXTERNAL_R_ENRICHMENT_DETECTION_SCHEMA_VERSION:
        blockers.append(f"external_enrichment_backend_schema_mismatch:{detection.get('schema_version') or 'missing'}")
    rscript = detection.get("rscript") if isinstance(detection.get("rscript"), dict) else {}
    if not rscript.get("available"):
        blockers.append("external_enrichment_rscript_missing")

    capability_rows = [_capability_row(capability, detection) for capability in capabilities]
    for row in capability_rows:
        if row["status"] != "passed":
            blockers.extend(row["blockers"])

    if detection.get("status") == "blocked" and not blockers:
        warnings.append("external_detection_global_status_blocked_by_unselected_capabilities")
    warnings.extend(str(item) for item in detection.get("warnings", []) or [])
    warnings.extend(_irrelevant_detection_blockers(detection, capabilities))

    return _gate_payload(
        analysis_type=analysis_type,
        required_capabilities=capabilities,
        detection_path=str(resolved_path),
        detection=detection,
        capability_rows=capability_rows,
        blockers=blockers,
        warnings=warnings,
    )


def _gate_payload(
    *,
    analysis_type: str,
    required_capabilities: tuple[str, ...],
    detection_path: str,
    detection: dict[str, Any],
    capability_rows: list[dict[str, Any]],
    blockers: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    packages = _package_map(detection)
    rscript = detection.get("rscript") if isinstance(detection.get("rscript"), dict) else {}
    available_capabilities = [capability for capability, passed in (detection.get("capabilities") or {}).items() if passed]
    blocked_capabilities = [capability for capability, passed in (detection.get("capabilities") or {}).items() if not passed]
    return {
        "schema_version": ENRICHMENT_BACKEND_GATE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "analysis_type": analysis_type,
        "required_capabilities": list(required_capabilities),
        "capability_rows": capability_rows,
        "available_capabilities": available_capabilities,
        "blocked_capabilities": blocked_capabilities,
        "detection_path": detection_path,
        "detection_schema_version": str(detection.get("schema_version") or ""),
        "detection_status": str(detection.get("status") or "missing"),
        "rscript": {
            "available": bool(rscript.get("available")),
            "path": str(rscript.get("path") or ""),
            "version": str(rscript.get("version") or ""),
            "architecture": str(rscript.get("architecture") or ""),
        },
        "packages": packages,
        "install_action": "none_detect_first_only",
        "packaging_policy": "external_runtime_not_bundled",
        "semantic_boundary": "backend_gate_only_not_enrichment_execution",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _capability_row(capability: str, detection: dict[str, Any]) -> dict[str, Any]:
    required_packages = CORE_CAPABILITY_REQUIREMENTS.get(capability)
    if not required_packages:
        return {
            "capability": capability,
            "status": "blocked",
            "required_packages": [],
            "package_versions": {},
            "missing_packages": [],
            "blockers": [f"unknown_enrichment_backend_capability:{capability}"],
        }
    packages = _package_map(detection)
    package_versions: dict[str, str] = {}
    missing_packages: list[str] = []
    blockers: list[str] = []
    for package in required_packages:
        status = packages.get(package, {})
        package_versions[package] = str(status.get("version") or "")
        if not status.get("available") or not status.get("importable"):
            missing_packages.append(package)
            reason = str(status.get("missing_reason") or f"{package}_not_importable")
            blockers.append(f"missing_required_r_package:{package}:{reason}")
    capabilities = detection.get("capabilities") if isinstance(detection.get("capabilities"), dict) else {}
    if capability in capabilities and not capabilities.get(capability) and not blockers:
        blockers.append(f"external_enrichment_capability_unavailable:{capability}")
    return {
        "capability": capability,
        "status": "blocked" if blockers else "passed",
        "required_packages": list(required_packages),
        "package_versions": package_versions,
        "missing_packages": missing_packages,
        "blockers": blockers,
    }


def _package_map(detection: dict[str, Any]) -> dict[str, dict[str, Any]]:
    packages: dict[str, dict[str, Any]] = {}
    for source_key in ("packages", "optional_packages"):
        raw = detection.get(source_key)
        if not isinstance(raw, dict):
            continue
        for name, status in raw.items():
            if isinstance(status, dict):
                packages[str(name)] = dict(status)
    return packages


def _irrelevant_detection_blockers(detection: dict[str, Any], required_capabilities: tuple[str, ...]) -> list[str]:
    required = set(required_capabilities)
    warnings: list[str] = []
    for blocker in detection.get("blockers", []) or []:
        if not isinstance(blocker, dict):
            continue
        required_by = {str(item) for item in blocker.get("required_by", []) or []}
        package = str(blocker.get("package") or "")
        if required_by and required_by.isdisjoint(required):
            warnings.append(f"external_detection_blocker_outside_selected_capabilities:{package or blocker.get('code')}")
        elif not required_by and package:
            warnings.append(f"external_detection_package_not_required_for_selected_capability:{package}")
    return warnings


def _resolve_detection_path(
    project_root: str | Path | None,
    *,
    detection_path: str | Path | None,
    search_roots: list[str | Path] | tuple[str | Path, ...] | None,
) -> Path | None:
    if detection_path is not None:
        path = Path(detection_path).expanduser().resolve()
        return path if path.is_file() else None
    candidates: list[Path] = []
    for root in _search_roots(project_root, search_roots):
        candidates.append(root / "project_storage" / "external_engines" / R_ENRICHMENT_BACKEND_DETECTION_FILENAME)
        candidates.append(root / "external_engines" / R_ENRICHMENT_BACKEND_DETECTION_FILENAME)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _search_roots(project_root: str | Path | None, search_roots: list[str | Path] | tuple[str | Path, ...] | None) -> list[Path]:
    roots: list[Path] = []
    if search_roots is not None:
        roots.extend(Path(root).expanduser().resolve() for root in search_roots)
    if project_root is not None:
        root = Path(project_root).expanduser().resolve()
        roots.append(root)
        parent = root.parent
        for sibling in ("ReleaseBuild", "Integration"):
            roots.append(parent / sibling)
    return list(dict.fromkeys(roots))


def _read_detection_payload(path: Path) -> tuple[dict[str, Any], str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, "external_enrichment_backend_detection_invalid_json"
    except OSError:
        return {}, "external_enrichment_backend_detection_unreadable"
    if not isinstance(payload, dict):
        return {}, "external_enrichment_backend_detection_not_object"
    return payload, ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
