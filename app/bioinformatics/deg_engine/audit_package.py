from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry


DEG_AUDIT_PACKAGE_SCHEMA_VERSION = "biomedpilot.deg_production_audit_package.v1"


def create_deg_production_audit_package(
    project_root: str | Path,
    *,
    result_id: str,
    input_adaptation_gate: dict[str, Any] | None = None,
    design_quality_gate: dict[str, Any] | None = None,
    data_quality_gate: dict[str, Any] | None = None,
    method_recommendation_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entry = next((item for item in registry.get("results", []) or [] if isinstance(item, dict) and str(item.get("result_id") or "") == result_id), None)
    blockers: list[str] = []
    if entry is None:
        blockers.append("formal_deg_result_not_found")
    elif not _is_formal_deg(entry):
        blockers.append("deg_audit_package_requires_formal_computed_result")
    if blockers:
        return {
            "schema_version": DEG_AUDIT_PACKAGE_SCHEMA_VERSION,
            "status": "blocked",
            "package_path": "",
            "blockers": blockers,
            "warnings": [],
        }
    assert entry is not None
    package_dir = _next_package_dir(root, result_id)
    tables_dir = package_dir / "tables"
    manifests_dir = package_dir / "manifests"
    logs_dir = package_dir / "logs"
    for directory in (tables_dir, manifests_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    copied_files: list[Path] = []
    copied_files.extend(_copy_artifacts(root, entry.get("output_artifacts", []) or [], tables_dir))
    copied_files.extend(_copy_artifacts(root, entry.get("log_artifacts", []) or [], logs_dir))
    _write_json(manifests_dir / "input_adaptation.json", input_adaptation_gate or {})
    _write_json(manifests_dir / "design_quality.json", design_quality_gate or {})
    _write_json(manifests_dir / "data_quality.json", data_quality_gate or {})
    _write_json(manifests_dir / "method_recommendation.json", method_recommendation_gate or {})
    _write_json(manifests_dir / "parameters_manifest.json", entry.get("parameters_manifest", {}))
    _write_json(manifests_dir / "multifactor_design_provenance.json", _multifactor_design_provenance(entry))
    _write_json(manifests_dir / "dependency_snapshot.json", entry.get("dependency_snapshot", {}))
    _write_json(manifests_dir / "result_index_snapshot.json", registry)
    _write_json(manifests_dir / "formal_deg_result_entry.json", entry)
    _write_json(manifests_dir / "command_manifest.json", _command_manifest(entry))
    _write_json(manifests_dir / "checksums.json", _checksums(package_dir, copied_files))
    (package_dir / "README_limitations.md").write_text(_limitations_markdown(), encoding="utf-8")

    manifest = {
        "schema_version": DEG_AUDIT_PACKAGE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "deg_production_audit_package_created",
        "package_path": str(package_dir),
        "result_id": result_id,
        "result_semantics": "formal_computed_result",
        "package_layout": ["deg_audit_package_manifest.json", "tables/", "manifests/", "logs/", "README_limitations.md"],
        "report_ready_eligible_changed": False,
        "clinical_conclusion_enabled": False,
        "included_manifests": [
            "manifests/input_adaptation.json",
            "manifests/design_quality.json",
            "manifests/data_quality.json",
            "manifests/method_recommendation.json",
            "manifests/parameters_manifest.json",
            "manifests/multifactor_design_provenance.json",
            "manifests/dependency_snapshot.json",
            "manifests/result_index_snapshot.json",
            "manifests/command_manifest.json",
            "manifests/checksums.json",
        ],
        "warnings": list(entry.get("warnings", []) or []),
        "limitations": _limitations(),
        "provenance": {
            "input_package_id": str(entry.get("input_package_id") or ""),
            "task_run_id": str(entry.get("task_run_id") or ""),
            "engine_name": str(entry.get("engine_name") or ""),
            "engine_version": str(entry.get("engine_version") or ""),
            "multifactor_design": _multifactor_design_provenance(entry),
            "result_index_path": str(root / RESULT_INDEX),
        },
        "blockers": [],
    }
    _write_json(package_dir / "deg_audit_package_manifest.json", manifest)
    return manifest


def _is_formal_deg(entry: dict[str, Any]) -> bool:
    semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="")
    return semantics == "formal_computed_result" and str(entry.get("task_type") or "").lower() == "deg"


def _copy_artifacts(root: Path, artifacts: list[Any], target_dir: Path) -> list[Path]:
    copied: list[Path] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        path = Path(str(artifact.get("path") or artifact.get("file_path") or "")).expanduser()
        if not path.is_absolute():
            path = root / path
        if path.is_file():
            target = target_dir / path.name
            shutil.copy2(path, target)
            copied.append(target)
    return copied


def _checksums(package_dir: Path, paths: list[Path]) -> dict[str, Any]:
    rows = []
    for path in sorted(paths):
        rows.append({"path": str(path.relative_to(package_dir)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"algorithm": "sha256", "files": rows}


def _command_manifest(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_run_id": str(entry.get("task_run_id") or ""),
        "task_type": str(entry.get("task_type") or ""),
        "engine_name": str(entry.get("engine_name") or ""),
        "engine_version": str(entry.get("engine_version") or ""),
        "parameters_manifest_present": bool(entry.get("parameters_manifest")),
        "dependency_snapshot_present": bool(entry.get("dependency_snapshot")),
        "multifactor_design_present": bool(_multifactor_design_provenance(entry)),
    }


def _multifactor_design_provenance(entry: dict[str, Any]) -> dict[str, Any]:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    keys = ("design_formula", "contrast", "covariates", "batch_variables", "design_rank", "residual_degrees_of_freedom", "contrast_estimability", "backend_method")
    return {key: parameters.get(key) for key in keys if key in parameters}


def _limitations() -> list[str]:
    return [
        "Statistical research result only.",
        "No clinical diagnosis, prognosis, or treatment recommendation.",
        "Audit package is not a report-ready package.",
        "Imported, testing, exploratory, and preflight results are excluded.",
    ]


def _limitations_markdown() -> str:
    return "# DEG Audit Package Limitations\n\n" + "\n".join(f"- {item}" for item in _limitations()) + "\n"


def _next_package_dir(root: Path, result_id: str) -> Path:
    base = root / "audit_package" / "formal_deg" / _safe_name(result_id)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = base / stamp
    suffix = 1
    while candidate.exists():
        suffix += 1
        candidate = base / f"{stamp}_{suffix}"
    return candidate


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value) or "formal_deg"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
