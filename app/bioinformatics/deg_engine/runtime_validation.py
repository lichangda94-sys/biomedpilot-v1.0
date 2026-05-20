from __future__ import annotations

import csv
import importlib
import importlib.util
import json
import platform
import sys
import tempfile
import time
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

from app.bioinformatics.results.registry import RESULT_INDEX
from app.version import app_version_summary

from .dependency_check import REQUIRED_PACKAGES, check_deg_backend_dependencies
from .formal_runner import run_formal_controlled_deg
from .result_schema import validate_formal_deg_result_index_entry


RUNTIME_VALIDATION_SCHEMA_VERSION = "biomedpilot.b9_3_formal_deg_runtime_validation.v1"


def run_formal_deg_runtime_validation(*, output_path: str | Path | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    dependency_snapshot = check_deg_backend_dependencies()
    fixture_result = _run_fixture(dependency_snapshot)
    payload = {
        "schema_version": RUNTIME_VALIDATION_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runtime_context": _runtime_context(),
        "dependency_snapshot": dependency_snapshot,
        "import_checks": {name: _import_check(name) for name in REQUIRED_PACKAGES},
        "packaging_checks": _packaging_checks(),
        "fixture_result": fixture_result,
        "status": _overall_status(dependency_snapshot, fixture_result),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
    }
    if output_path is not None:
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _runtime_context() -> dict[str, Any]:
    version = app_version_summary()
    return {
        "launch_mode": version.launch_mode,
        "app_root": version.app_root,
        "git_head": version.git_head,
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "platform_machine": platform.machine(),
        "platform": platform.platform(),
        "argv": sys.argv[1:],
    }


def _import_check(name: str) -> dict[str, Any]:
    status: dict[str, Any] = {
        "available": importlib.util.find_spec(name) is not None,
        "importable": False,
        "version": "",
        "module_file": "",
        "error": "",
    }
    if not status["available"]:
        status["error"] = f"{name}_not_found_by_importlib"
        return status
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - exercised only by broken local environments.
        status["error"] = f"{exc.__class__.__name__}: {exc}"
        return status
    status["importable"] = True
    status["module_file"] = str(getattr(module, "__file__", "") or "")
    try:
        status["version"] = metadata.version(name)
    except metadata.PackageNotFoundError:
        status["version"] = str(getattr(module, "__version__", "") or "unknown")
    return status


def _packaging_checks() -> dict[str, Any]:
    app_root = Path.cwd().resolve()
    bundle_root = _bundle_root(app_root)
    bundle_size_bytes = _directory_size(bundle_root) if bundle_root is not None else None
    import_checks = {name: _import_check(name) for name in REQUIRED_PACKAGES}
    package_locations = {name: str(check.get("module_file") or "") for name, check in import_checks.items()}
    return {
        "bundle_root": str(bundle_root) if bundle_root is not None else "",
        "bundle_size_bytes": bundle_size_bytes,
        "packaged_local_python_launcher": (app_root / "BUILD_INFO.json").is_file(),
        "required_packages_declared_for_runtime": list(REQUIRED_PACKAGES),
        "required_package_locations": package_locations,
        "required_packages_loaded_from_bundle": {
            name: _is_relative_to(location, bundle_root) if bundle_root is not None else False
            for name, location in package_locations.items()
        },
    }


def _bundle_root(app_root: Path) -> Path | None:
    for parent in (app_root, *app_root.parents):
        if parent.suffix == ".app":
            return parent
    return None


def _directory_size(path: Path | None) -> int | None:
    if path is None or not path.exists():
        return None
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total


def _is_relative_to(path_value: str, root: Path | None) -> bool:
    if not path_value or root is None:
        return False
    try:
        Path(path_value).resolve().relative_to(root)
    except ValueError:
        return False
    return True


def _run_fixture(dependency_snapshot: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="biomedpilot_b9_3_formal_deg_") as tmpdir:
        root = Path(tmpdir)
        _write_fixture_project(root)
        try:
            result = run_formal_controlled_deg(root, dependency_snapshot=dependency_snapshot)
        except Exception as exc:  # pragma: no cover - indicates a B9.3 regression.
            return {
                "status": "failed",
                "graceful_missing_dependency_block": False,
                "error": f"{exc.__class__.__name__}: {exc}",
                "blockers": ["formal_deg_runtime_validation_raised_exception"],
            }
        return _validate_fixture_result(root, result, dependency_snapshot)


def _validate_fixture_result(root: Path, result: dict[str, Any], dependency_snapshot: dict[str, Any]) -> dict[str, Any]:
    if result.get("status") == "blocked":
        missing_blockers = [str(item) for item in dependency_snapshot.get("blockers", []) or [] if str(item).startswith("missing_python_package:")]
        return {
            "status": "blocked",
            "graceful_missing_dependency_block": bool(missing_blockers) and "dependency_snapshot_not_passed" in result.get("blockers", []),
            "blockers": list(result.get("blockers", []) or []),
            "warnings": list(result.get("warnings", []) or []),
        }
    if result.get("status") != "passed":
        return {
            "status": "failed",
            "graceful_missing_dependency_block": False,
            "blockers": list(result.get("blockers", []) or ["formal_deg_fixture_not_passed"]),
            "warnings": list(result.get("warnings", []) or []),
        }

    table_path = Path(str(result.get("result_table_path") or ""))
    rows = _read_table_rows(table_path)
    result_entry = result.get("result_entry") if isinstance(result.get("result_entry"), dict) else {}
    entry_validation = validate_formal_deg_result_index_entry(result_entry)
    log_artifacts = result_entry.get("log_artifacts") if isinstance(result_entry.get("log_artifacts"), list) else []
    log_path = root / str(log_artifacts[0].get("path") or "") if log_artifacts and isinstance(log_artifacts[0], dict) else None
    parameter_manifest = result.get("parameter_manifest") if isinstance(result.get("parameter_manifest"), dict) else {}
    blockers: list[str] = []
    if not rows:
        blockers.append("fixture_result_table_empty")
    if not all(_numeric(row.get("p_value")) for row in rows):
        blockers.append("fixture_missing_numeric_p_value")
    if not all(_numeric(row.get("adjusted_p_value")) for row in rows):
        blockers.append("fixture_missing_numeric_fdr")
    if entry_validation.get("status") != "passed":
        blockers.extend(str(item) for item in entry_validation.get("blockers", []) or [])
    if log_path is None or not log_path.is_file():
        blockers.append("fixture_missing_task_run_log")
    if parameter_manifest.get("dependency_snapshot", {}).get("status") != "passed":
        blockers.append("fixture_parameter_manifest_missing_passed_dependency_snapshot")
    return {
        "status": "failed" if blockers else "passed",
        "result_id": result.get("result_id", ""),
        "task_run_id": result.get("task_run_id", ""),
        "result_semantics": result_entry.get("result_semantics", ""),
        "result_index_registry_path": str(RESULT_INDEX),
        "output_artifacts": result_entry.get("output_artifacts", []),
        "plot_artifacts": result_entry.get("plot_artifacts", []),
        "report_artifacts": result_entry.get("report_artifacts", []),
        "log_artifacts": result_entry.get("log_artifacts", []),
        "report_ready_eligible": result_entry.get("report_ready_eligible"),
        "result_table_row_count": len(rows),
        "has_numeric_p_value": bool(rows) and all(_numeric(row.get("p_value")) for row in rows),
        "has_numeric_fdr": bool(rows) and all(_numeric(row.get("adjusted_p_value")) for row in rows),
        "result_index_v2_status": entry_validation.get("status"),
        "task_run_log_present": log_path is not None and log_path.is_file(),
        "parameters_manifest_status": parameter_manifest.get("status", ""),
        "dependency_snapshot_status": parameter_manifest.get("dependency_snapshot", {}).get("status", ""),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(result.get("warnings", []) or []),
    }


def _read_table_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _numeric(value: object) -> bool:
    try:
        float(str(value))
    except (TypeError, ValueError):
        return False
    return True


def _overall_status(dependency_snapshot: dict[str, Any], fixture_result: dict[str, Any]) -> str:
    if dependency_snapshot.get("status") != "passed":
        return "blocked_missing_dependency" if fixture_result.get("graceful_missing_dependency_block") else "failed"
    return "passed" if fixture_result.get("status") == "passed" else "failed"


def _write_fixture_project(root: Path) -> None:
    matrix = root / "matrix.tsv"
    matrix.write_text(
        "gene\tcase1\tcase2\tcase3\tctrl1\tctrl2\tctrl3\n"
        "TP53\t12\t13\t11\t4\t5\t4\n"
        "EGFR\t2\t3\t2\t10\t11\t9\n"
        "GAPDH\t7\t7\t8\t7\t8\t7\n",
        encoding="utf-8",
    )
    sample = root / "sample.tsv"
    sample.write_text(
        "sample_id\tgroup\n"
        "case1\tcase\ncase2\tcase\ncase3\tcase\n"
        "ctrl1\tcontrol\nctrl2\tcontrol\nctrl3\tcontrol\n",
        encoding="utf-8",
    )
    group = root / "group.json"
    group.write_text(
        json.dumps(
            {
                "group_design": {
                    "sample_group_assignments": {
                        "case1": "case",
                        "case2": "case",
                        "case3": "case",
                        "ctrl1": "control",
                        "ctrl2": "control",
                        "ctrl3": "control",
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    assets = [
        _asset("expr", "raw_count_matrix", "expression_repository", matrix, value_type="count", gene_id_type="symbol"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", group),
    ]
    selection = {"expression": {"asset_id": "expr", "selection_state": "user_confirmed"}}
    manifest = {
        "schema_version": "biomedpilot.repository_manifest.v1",
        "source_dataset_id": "B9_3_CONTROLLED_FIXTURE",
        "source_state": {"source_state_hash": "b9-3-fixture"},
        "assets": assets,
        "default_asset_selection": selection,
    }
    registry = {
        "schema_version": "biomedpilot.standardized_assets_registry.v2",
        "assets": assets,
        "default_asset_selection": selection,
    }
    manifest_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")


def _asset(asset_id: str, asset_type: str, repository: str, path: Path, *, value_type: str = "", gene_id_type: str = "symbol") -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_role": "expression_matrix" if "expression" in asset_type or "count" in asset_type else asset_type,
        "repository": repository,
        "path": str(path),
        "file_path": str(path),
        "validation_status": "passed",
        "analysis_ready": True,
        "expression_value_type": value_type,
        "gene_id_type": gene_id_type,
    }
