from __future__ import annotations

import json
import platform
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.version import app_version_summary

from .r_edger_runtime import detect_r_edger_runtime_capabilities


R_EDGER_RUNTIME_VALIDATION_SCHEMA_VERSION = "biomedpilot.b25_12_r_edger_runtime_validation.v1"


def run_r_edger_runtime_validation(*, output_path: str | Path | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    runtime_detection = detect_r_edger_runtime_capabilities(timeout_seconds=20)
    payload = {
        "schema_version": R_EDGER_RUNTIME_VALIDATION_SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "runtime_context": _runtime_context(),
        "runtime_detection": runtime_detection,
        "packaging_checks": _packaging_checks(runtime_detection),
        "execution_activation_preflight": _execution_activation_preflight(runtime_detection),
        "status": "passed" if runtime_detection.get("status") == "passed" else "blocked_missing_dependency",
        "elapsed_seconds": round(time.perf_counter() - started, 4),
    }
    if output_path is not None:
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _execution_activation_preflight(runtime_detection: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if runtime_detection.get("status") != "passed":
        blockers.extend(str(item) for item in runtime_detection.get("blockers", []) or ["r_edger_runtime_detection_not_passed"])
    blockers.extend(
        [
            "b25_12_edger_planning_only_no_execution",
            "b25_13_edger_real_fixture_required",
            "b25_14_edger_ui_activation_required",
        ]
    )
    return {
        "schema_version": "biomedpilot.b25_12_r_edger_execution_activation_preflight.v1",
        "status": "blocked",
        "runtime_detection_passed": runtime_detection.get("status") == "passed",
        "formal_execution_enabled": False,
        "normal_user_button_enabled": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": ["B25.12 detects edgeR only; no edgeR result table, result index write, plot or report is produced."],
    }


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


def _packaging_checks(runtime_detection: dict[str, Any]) -> dict[str, Any]:
    app_root = Path.cwd().resolve()
    bundle_root = _bundle_root(app_root)
    return {
        "bundle_root": str(bundle_root) if bundle_root is not None else "",
        "bundle_size_bytes": _directory_size(bundle_root) if bundle_root is not None else None,
        "packaged_local_python_launcher": (app_root / "BUILD_INFO.json").is_file(),
        "rscript_path": str(runtime_detection.get("rscript_path") or ""),
        "rscript_is_bundled_in_app": _is_relative_to(str(runtime_detection.get("rscript_path") or ""), bundle_root) if bundle_root is not None else False,
        "r_bioconductor_policy": "detect_first_external_rscript_no_install_no_bundle",
    }


def _bundle_root(path: Path) -> Path | None:
    for parent in (path, *path.parents):
        if parent.suffix == ".app":
            return parent
    return None


def _directory_size(path: Path | None) -> int | None:
    if path is None or not path.exists():
        return None
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def _is_relative_to(path: str, base: Path | None) -> bool:
    if base is None or not path:
        return False
    try:
        Path(path).resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True
