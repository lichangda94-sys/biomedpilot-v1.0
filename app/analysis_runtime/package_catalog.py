from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.bioinformatics.results.registry import load_registry

from .standard_package import validate_standard_result_package


def build_standard_analysis_package_catalog(project_root: str | Path) -> dict[str, Any]:
    """Build a read-only catalog of standard analysis result packages.

    The catalog is intentionally derived from the current result index and the
    standard package contract. It does not scan arbitrary folders, execute
    workers, or infer formal readiness from module-specific payloads.
    """

    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    rows: list[dict[str, Any]] = []
    for entry in [item for item in registry.get("results", []) if isinstance(item, dict)]:
        for artifact in _standard_package_artifacts(entry):
            package_dir = _resolve_artifact_path(root, artifact.get("path"))
            validation = validate_standard_result_package(
                package_dir,
                expected_module_id=_module_id_from_entry(entry),
                expected_task_id=str(entry.get("task_run_id") or ""),
                expected_mode=str((entry.get("dependency_snapshot") or {}).get("mode") or ""),
            )
            result_payload = _read_json(package_dir / "result.json")
            provenance_payload = _read_json(package_dir / "provenance.json")
            rows.append(
                {
                    "schema_version": "biomedpilot.analysis.standard_package_catalog_row.v1",
                    "result_id": str(entry.get("result_id") or ""),
                    "task_run_id": str(entry.get("task_run_id") or ""),
                    "task_type": str(entry.get("task_type") or ""),
                    "result_semantics": str(entry.get("result_semantics") or ""),
                    "package_path": str(package_dir),
                    "package_path_relative": _relative_or_absolute(root, package_dir),
                    "module_id": str(result_payload.get("module_id") or _module_id_from_entry(entry)),
                    "mode": str(result_payload.get("mode") or (entry.get("dependency_snapshot") or {}).get("mode") or ""),
                    "status": str(result_payload.get("status") or validation.get("result_status") or ""),
                    "validation_status": str(validation.get("status") or "blocked"),
                    "engine_name": str((provenance_payload.get("engine") or {}).get("name") or entry.get("engine_name") or ""),
                    "engine_version": str((provenance_payload.get("engine") or {}).get("version") or entry.get("engine_version") or ""),
                    "runtime": provenance_payload.get("runtime") if isinstance(provenance_payload.get("runtime"), dict) else {},
                    "command": str(provenance_payload.get("command") or ""),
                    "artifact_counts": {
                        "tables": len(result_payload.get("tables") or []),
                        "plots": len(result_payload.get("plots") or []),
                        "reports": len(result_payload.get("reports") or []),
                    },
                    "blockers": list(dict.fromkeys([*validation.get("blockers", []), *result_payload.get("blockers", [])])),
                    "warnings": list(dict.fromkeys([*validation.get("warnings", []), *result_payload.get("warnings", [])])),
                }
            )
    blockers = [f"standard_analysis_package_invalid:{row['result_id']}:{item}" for row in rows for item in row["blockers"]]
    return {
        "schema_version": "biomedpilot.analysis.standard_package_catalog.v1",
        "status": "blocked" if blockers else "passed",
        "project_root": str(root),
        "source_policy": "result_index_standard_result_package_artifacts_only",
        "package_count": len(rows),
        "rows": rows,
        "blockers": blockers,
        "warnings": [item for row in rows for item in row["warnings"]],
    }


def _standard_package_artifacts(entry: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = entry.get("output_artifacts")
    if not isinstance(artifacts, list | tuple):
        return []
    return [item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "standard_result_package" and item.get("path")]


def _resolve_artifact_path(root: Path, value: object) -> Path:
    path = Path(str(value or "")).expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _module_id_from_entry(entry: dict[str, Any]) -> str:
    task_type = str(entry.get("task_type") or "")
    if task_type.startswith("analysis:"):
        return task_type.split(":", 1)[1]
    return ""


def _relative_or_absolute(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
