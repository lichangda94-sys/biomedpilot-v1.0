from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.enrichment_result_schema import validate_enrichment_result_schema_gate
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry


ENRICHMENT_AUDIT_PACKAGE_SCHEMA_VERSION = "biomedpilot.enrichment_production_audit_package.v1"
ENRICHMENT_TASK_TYPES = {"ora", "gsea_preranked"}


def create_enrichment_production_audit_package(project_root: str | Path, *, result_id: str) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entry = next((item for item in registry.get("results", []) or [] if isinstance(item, dict) and str(item.get("result_id") or "") == result_id), None)
    blockers: list[str] = []
    if entry is None:
        blockers.append("formal_enrichment_result_not_found")
    elif not _is_formal_enrichment(entry):
        blockers.append("enrichment_audit_package_requires_formal_computed_result")
    schema_gate = validate_enrichment_result_schema_gate(root, result_id=result_id) if entry is not None else {}
    if schema_gate and schema_gate.get("status") != "passed":
        blockers.extend(str(item) for item in schema_gate.get("blockers", []) or ["enrichment_result_schema_gate_not_passed"])
    if blockers:
        return {
            "schema_version": ENRICHMENT_AUDIT_PACKAGE_SCHEMA_VERSION,
            "status": "blocked",
            "package_path": "",
            "result_id": result_id,
            "result_schema_gate": schema_gate,
            "blockers": list(dict.fromkeys(blockers)),
            "warnings": [],
        }
    assert entry is not None
    package_dir = _next_package_dir(root, result_id)
    tables_dir = package_dir / "tables"
    plots_dir = package_dir / "plots"
    manifests_dir = package_dir / "manifests"
    logs_dir = package_dir / "logs"
    for directory in (tables_dir, plots_dir, manifests_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    copied_files: list[Path] = []
    copied_files.extend(_copy_artifacts(root, entry.get("output_artifacts", []) or [], tables_dir))
    copied_files.extend(_copy_plot_artifacts(root, entry.get("plot_artifacts", []) or [], plots_dir))
    copied_files.extend(_copy_artifacts(root, entry.get("log_artifacts", []) or [], logs_dir))
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    _write_json(manifests_dir / "resource_lock.json", parameters.get("resource_lock", {}))
    _write_json(manifests_dir / "background_universe.json", parameters.get("background_universe", {}))
    _write_json(manifests_dir / "identifier_compatibility.json", parameters.get("identifier_compatibility_gate", {}))
    _write_json(manifests_dir / "statistical_policy.json", parameters.get("statistical_policy", {}))
    _write_json(manifests_dir / "parameter_confirmation.json", parameters.get("parameter_confirmation", {}))
    _write_json(manifests_dir / "parameters_manifest.json", parameters)
    _write_json(manifests_dir / "dependency_snapshot.json", entry.get("dependency_snapshot", {}))
    _write_json(manifests_dir / "result_schema_gate.json", schema_gate)
    _write_json(manifests_dir / "result_index_snapshot.json", registry)
    _write_json(manifests_dir / "enrichment_result_entry.json", entry)
    _write_json(manifests_dir / "plot_artifacts.json", entry.get("plot_artifacts", []) or [])
    copied_files.extend([path for path in manifests_dir.glob("*.json") if path.name != "checksums.json"])
    _write_json(manifests_dir / "checksums.json", _checksums(package_dir, copied_files))
    (package_dir / "README_limitations.md").write_text(_limitations_markdown(), encoding="utf-8")

    manifest = {
        "schema_version": ENRICHMENT_AUDIT_PACKAGE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "enrichment_production_audit_package_created",
        "package_path": str(package_dir),
        "result_id": result_id,
        "result_semantics": "formal_computed_result",
        "task_type": str(entry.get("task_type") or ""),
        "package_layout": ["enrichment_audit_package_manifest.json", "tables/", "plots/", "manifests/", "logs/", "README_limitations.md"],
        "included_manifests": [
            "manifests/resource_lock.json",
            "manifests/background_universe.json",
            "manifests/identifier_compatibility.json",
            "manifests/statistical_policy.json",
            "manifests/parameter_confirmation.json",
            "manifests/parameters_manifest.json",
            "manifests/dependency_snapshot.json",
            "manifests/result_schema_gate.json",
            "manifests/result_index_snapshot.json",
            "manifests/enrichment_result_entry.json",
            "manifests/plot_artifacts.json",
            "manifests/checksums.json",
        ],
        "report_ready_eligible_changed": False,
        "section_report_created": False,
        "full_integrated_report_enabled": False,
        "clinical_interpretation_enabled": False,
        "result_schema_gate": schema_gate,
        "warnings": list(entry.get("warnings", []) or []),
        "limitations": _limitations(),
        "provenance": {
            "input_package_id": str(entry.get("input_package_id") or ""),
            "task_run_id": str(entry.get("task_run_id") or ""),
            "engine_name": str(entry.get("engine_name") or ""),
            "engine_version": str(entry.get("engine_version") or ""),
            "resource_id": str(parameters.get("resource_id") or parameters.get("resource_lock", {}).get("resource_id") or ""),
            "source_result_id": str(parameters.get("source_result_id") or ""),
            "result_index_path": str(root / RESULT_INDEX),
        },
        "blockers": [],
    }
    _write_json(package_dir / "enrichment_audit_package_manifest.json", manifest)
    return manifest


def _is_formal_enrichment(entry: dict[str, Any]) -> bool:
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    return semantics == "formal_computed_result" and str(entry.get("task_type") or "") in ENRICHMENT_TASK_TYPES


def _copy_artifacts(root: Path, artifacts: list[Any], target_dir: Path) -> list[Path]:
    copied: list[Path] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        path = _artifact_path(root, artifact)
        if path and path.is_file():
            target = target_dir / path.name
            shutil.copy2(path, target)
            copied.append(target)
    return copied


def _copy_plot_artifacts(root: Path, artifacts: list[Any], target_dir: Path) -> list[Path]:
    copied: list[Path] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        image_artifacts = artifact.get("image_artifacts", []) or []
        table_artifacts = artifact.get("table_artifacts", []) or []
        for child in [*image_artifacts, *table_artifacts]:
            if not isinstance(child, dict):
                continue
            path = _artifact_path(root, child)
            if path and path.is_file():
                target = target_dir / path.name
                shutil.copy2(path, target)
                copied.append(target)
    return copied


def _artifact_path(root: Path, artifact: dict[str, Any]) -> Path | None:
    value = str(artifact.get("path") or artifact.get("file_path") or "")
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def _checksums(package_dir: Path, paths: list[Path]) -> dict[str, Any]:
    rows = []
    for path in sorted(paths):
        rows.append({"path": str(path.relative_to(package_dir)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"algorithm": "sha256", "files": rows}


def _limitations() -> list[str]:
    return [
        "Statistical research enrichment audit package only.",
        "No pathway biology conclusion is generated.",
        "No clinical diagnosis, prognosis, or treatment recommendation.",
        "Audit package is not a report-ready package.",
        "Imported, testing, exploratory, and preflight results are excluded.",
    ]


def _limitations_markdown() -> str:
    return "# Enrichment Audit Package Limitations\n\n" + "\n".join(f"- {item}" for item in _limitations()) + "\n"


def _next_package_dir(root: Path, result_id: str) -> Path:
    base = root / "audit_package" / "enrichment" / _safe_name(result_id)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = base / stamp
    suffix = 1
    while candidate.exists():
        suffix += 1
        candidate = base / f"{stamp}_{suffix}"
    return candidate


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value) or "enrichment"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
