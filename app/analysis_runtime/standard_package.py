from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = ("result.json", "provenance.json")
REQUIRED_DIRECTORIES = ("tables", "plots", "reports", "logs")


def validate_standard_result_package(
    package_dir: str | Path,
    *,
    expected_module_id: str = "",
    expected_task_id: str = "",
    expected_mode: str = "",
) -> dict[str, Any]:
    root = Path(package_dir).expanduser().resolve()
    blockers: list[str] = []
    warnings: list[str] = []
    for filename in REQUIRED_FILES:
        if not (root / filename).is_file():
            blockers.append(f"missing_required_file:{filename}")
    for dirname in REQUIRED_DIRECTORIES:
        if not (root / dirname).is_dir():
            blockers.append(f"missing_required_directory:{dirname}")

    result = _load_json(root / "result.json") if (root / "result.json").is_file() else {}
    provenance = _load_json(root / "provenance.json") if (root / "provenance.json").is_file() else {}
    for payload_name, payload in (("result", result), ("provenance", provenance)):
        if expected_module_id and payload.get("module_id") != expected_module_id:
            blockers.append(f"{payload_name}_module_id_mismatch")
        if expected_task_id and payload.get("task_id") != expected_task_id:
            blockers.append(f"{payload_name}_task_id_mismatch")
        if expected_mode and payload.get("mode") != expected_mode:
            blockers.append(f"{payload_name}_mode_mismatch")
    if result.get("status") not in {"passed", "blocked", "failed"}:
        blockers.append("result_status_invalid_or_missing")
    if not provenance.get("input_hash"):
        warnings.append("provenance_input_hash_missing")
    if not provenance.get("parameter_hash"):
        warnings.append("provenance_parameter_hash_missing")
    if not provenance.get("command"):
        warnings.append("provenance_command_missing")
    formal_blockers = _formal_package_provenance_blockers(result, provenance, expected_mode=expected_mode)
    blockers.extend(formal_blockers)
    return {
        "schema_version": "biomedpilot.analysis.result_package_validation.v1",
        "status": "blocked" if blockers else "passed",
        "package_dir": str(root),
        "result_status": str(result.get("status") or ""),
        "blockers": blockers,
        "warnings": warnings,
        "required_files": list(REQUIRED_FILES),
        "required_directories": list(REQUIRED_DIRECTORIES),
    }


def _formal_package_provenance_blockers(result: dict[str, Any], provenance: dict[str, Any], *, expected_mode: str) -> list[str]:
    status = str(result.get("status") or "")
    mode = str(result.get("mode") or provenance.get("mode") or expected_mode or "")
    semantics = str(result.get("result_semantics") or "")
    if status != "passed" or (mode != "full" and semantics != "formal_computed_result"):
        return []

    blockers: list[str] = []
    engine = provenance.get("engine") if isinstance(provenance.get("engine"), dict) else {}
    runtime = provenance.get("runtime") if isinstance(provenance.get("runtime"), dict) else {}
    worker_boundary = provenance.get("worker_boundary") if isinstance(provenance.get("worker_boundary"), dict) else {}

    for field in ("input_hash", "parameter_hash", "command"):
        if not provenance.get(field):
            blockers.append(f"formal_provenance_{field}_missing")
    if "random_seed" not in provenance:
        blockers.append("formal_provenance_random_seed_missing")
    for field in ("name", "version"):
        if not engine.get(field):
            blockers.append(f"formal_provenance_engine_{field}_missing")
    for field in ("r_version", "bioconductor_version", "package_versions", "external_tool_versions"):
        if field not in runtime:
            blockers.append(f"formal_provenance_runtime_{field}_missing")
    if not isinstance(runtime.get("package_versions"), dict):
        blockers.append("formal_provenance_runtime_package_versions_invalid")
    if not isinstance(runtime.get("external_tool_versions"), dict):
        blockers.append("formal_provenance_runtime_external_tool_versions_invalid")

    engine_name = str(engine.get("name") or "")
    if engine_name != "biomedpilot_standard_r_worker" and not worker_boundary.get("boundary_type"):
        blockers.append("formal_provenance_worker_boundary_missing")
    return blockers


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
