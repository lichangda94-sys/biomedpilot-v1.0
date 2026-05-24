from __future__ import annotations

import json
import platform
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.version import app_version_summary
from app.bioinformatics.results.registry import RESULT_INDEX

from .r_edger_planning import build_r_edger_parameter_manifest
from .r_edger_runtime import detect_r_edger_runtime_capabilities, run_r_edger_rscript_execution


R_EDGER_RUNTIME_VALIDATION_SCHEMA_VERSION = "biomedpilot.b25_13_r_edger_runtime_validation.v1"


def run_r_edger_runtime_validation(*, output_path: str | Path | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    runtime_detection = detect_r_edger_runtime_capabilities(timeout_seconds=20)
    fixture_result = _run_fixture(runtime_detection)
    payload = {
        "schema_version": R_EDGER_RUNTIME_VALIDATION_SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "runtime_context": _runtime_context(),
        "runtime_detection": runtime_detection,
        "packaging_checks": _packaging_checks(runtime_detection),
        "fixture_result": fixture_result,
        "execution_activation_preflight": _execution_activation_preflight(runtime_detection, fixture_result),
        "status": _overall_status(runtime_detection, fixture_result),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
    }
    if output_path is not None:
        path = Path(output_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _run_fixture(runtime_detection: dict[str, Any]) -> dict[str, Any]:
    if runtime_detection.get("status") != "passed":
        return {
            "status": "blocked",
            "graceful_missing_dependency_block": True,
            "blockers": list(runtime_detection.get("blockers", []) or ["r_edger_runtime_detection_not_passed"]),
            "warnings": [],
        }
    with tempfile.TemporaryDirectory(prefix="biomedpilot_b25_13_edger_") as tmpdir:
        root = Path(tmpdir)
        count_table = _write_count_fixture(root)
        preflight = _preflight()
        dependency_snapshot = runtime_detection.get("dependency_snapshot") if isinstance(runtime_detection.get("dependency_snapshot"), dict) else {}
        parameter_manifest = build_r_edger_parameter_manifest(
            _deg_ready(count_table),
            multi_factor_preflight=preflight,
            dependency_snapshot=dependency_snapshot,
            fdr_threshold=0.5,
            minimum_count_filter=0,
        )
        if parameter_manifest.get("status") != "passed":
            return {
                "status": "blocked",
                "graceful_missing_dependency_block": False,
                "blockers": list(parameter_manifest.get("blockers", []) or ["r_edger_parameter_manifest_not_passed"]),
                "warnings": list(parameter_manifest.get("warnings", []) or []),
            }
        try:
            result = run_r_edger_rscript_execution(
                root,
                count_table_path=count_table,
                sample_group_map=parameter_manifest["sample_group_map"],
                case_group=parameter_manifest["case_group"],
                control_group=parameter_manifest["control_group"],
                multi_factor_preflight=preflight,
                parameters_manifest=parameter_manifest,
                rscript_path=str(runtime_detection.get("rscript_path") or "Rscript"),
                external_capabilities=runtime_detection.get("external_capabilities") if isinstance(runtime_detection.get("external_capabilities"), dict) else None,
                dependency_snapshot=dependency_snapshot,
                timeout_seconds=120,
                result_id="r-edger-b25-13-runtime-fixture",
                task_run_id="task-r-edger-b25-13-runtime-fixture",
                input_package_id=parameter_manifest["input_package_id"],
                source_dataset_id="edger-b25-13-count-fixture",
                source_repository_manifest="standardized_data/repositories/repository_manifest.json",
            )
        except Exception as exc:  # pragma: no cover - indicates a runtime regression.
            return {
                "status": "failed",
                "graceful_missing_dependency_block": False,
                "error": f"{exc.__class__.__name__}: {exc}",
                "blockers": ["r_edger_runtime_validation_raised_exception"],
                "warnings": [],
            }
        return _validate_fixture_result(root, result)


def _validate_fixture_result(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    if result.get("status") != "passed":
        return {
            "status": "blocked" if result.get("status") == "blocked" else "failed",
            "graceful_missing_dependency_block": False,
            "blockers": list(result.get("blockers", []) or ["r_edger_fixture_not_passed"]),
            "warnings": list(result.get("warnings", []) or []),
        }
    canonical_rows = _read_tsv(Path(str(result.get("canonical_table_path") or "")))
    edger_rows = _read_tsv(Path(str(result.get("edger_table_path") or "")))
    entry = result.get("result_index_entry") if isinstance(result.get("result_index_entry"), dict) else {}
    blockers: list[str] = []
    if not canonical_rows:
        blockers.append("r_edger_runtime_fixture_canonical_table_empty")
    if not edger_rows:
        blockers.append("r_edger_runtime_fixture_method_table_empty")
    if not all(_numeric(row.get("p_value")) for row in canonical_rows):
        blockers.append("r_edger_runtime_fixture_missing_numeric_p_value")
    if not all(_numeric(row.get("adjusted_p_value")) for row in canonical_rows):
        blockers.append("r_edger_runtime_fixture_missing_numeric_adjusted_p_value")
    if entry.get("result_semantics") != "formal_computed_result":
        blockers.append("r_edger_runtime_fixture_result_semantics_not_formal")
    if entry.get("report_ready_eligible") is not False:
        blockers.append("r_edger_runtime_fixture_report_ready_not_false")
    if entry.get("plot_artifacts") != []:
        blockers.append("r_edger_runtime_fixture_plot_artifacts_not_empty")
    if entry.get("report_artifacts") != []:
        blockers.append("r_edger_runtime_fixture_report_artifacts_not_empty")
    if not (root / RESULT_INDEX).is_file():
        blockers.append("r_edger_runtime_fixture_result_index_missing")
    return {
        "status": "failed" if blockers else "passed",
        "result_id": result.get("result_id", ""),
        "task_run_id": result.get("task_run_id", ""),
        "result_semantics": entry.get("result_semantics", ""),
        "engine_name": entry.get("engine_name", ""),
        "result_index_registry_path": str(RESULT_INDEX),
        "output_artifacts": entry.get("output_artifacts", []),
        "plot_artifacts": entry.get("plot_artifacts", []),
        "report_artifacts": entry.get("report_artifacts", []),
        "report_ready_eligible": entry.get("report_ready_eligible"),
        "canonical_row_count": len(canonical_rows),
        "edger_row_count": len(edger_rows),
        "has_numeric_p_value": bool(canonical_rows) and all(_numeric(row.get("p_value")) for row in canonical_rows),
        "has_numeric_adjusted_p_value": bool(canonical_rows) and all(_numeric(row.get("adjusted_p_value")) for row in canonical_rows),
        "output_schema_status": (result.get("output_schema_gate") or {}).get("status") if isinstance(result.get("output_schema_gate"), dict) else "",
        "registration_status": (result.get("registration_gate") or {}).get("status") if isinstance(result.get("registration_gate"), dict) else "",
        "result_index_status": (result.get("result_index_gate") or {}).get("status") if isinstance(result.get("result_index_gate"), dict) else "",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(result.get("warnings", []) or []),
    }


def _execution_activation_preflight(runtime_detection: dict[str, Any], fixture_result: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    if runtime_detection.get("status") != "passed":
        blockers.extend(str(item) for item in runtime_detection.get("blockers", []) or ["r_edger_runtime_detection_not_passed"])
    if fixture_result.get("status") != "passed":
        blockers.extend(str(item) for item in fixture_result.get("blockers", []) or ["r_edger_controlled_fixture_not_passed"])
    blockers.append("b25_14_edger_ui_activation_required")
    return {
        "schema_version": "biomedpilot.b25_13_r_edger_execution_activation_preflight.v1",
        "status": "blocked",
        "runtime_validation_passed": runtime_detection.get("status") == "passed" and fixture_result.get("status") == "passed",
        "formal_execution_enabled": False,
        "normal_user_button_enabled": False,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": ["B25.13 validates runtime/fixture/result-index only; user-facing edgeR execution remains blocked until B25.14 UI activation."],
    }


def _overall_status(runtime_detection: dict[str, Any], fixture_result: dict[str, Any]) -> str:
    if runtime_detection.get("status") != "passed":
        return "blocked_missing_dependency"
    if fixture_result.get("status") == "passed":
        return "passed"
    return "failed"


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


def _write_count_fixture(root: Path) -> Path:
    path = root / "counts.tsv"
    lines = ["feature_id\tgene_symbol\tcase_1\tcase_2\tcontrol_1\tcontrol_2"]
    for index in range(1, 25):
        if index <= 8:
            values = (120 + index * 2, 116 + index * 2, 24 + index, 28 + index)
        elif index <= 16:
            values = (24 + index, 28 + index, 118 + index * 2, 122 + index * 2)
        else:
            values = (60 + index, 58 + index, 61 + index, 59 + index)
        lines.append(f"ENSG{index:06d}\tGENE{index}\t{values[0]}\t{values[1]}\t{values[2]}\t{values[3]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _deg_ready(count_table: Path) -> dict[str, object]:
    return {
        "input_package_id": "input-edger-b25-13-fixture",
        "deg_ready_package_id": "deg-ready-edger-b25-13-fixture",
        "value_type": "count",
        "gene_id_type": "symbol",
        "matrix_asset": {"asset_type": "raw_count_matrix", "path": str(count_table)},
        "gene_mapping_status": {"status": "passed"},
        "sample_alignment_status": {"status": "passed"},
        "blockers": [],
        "warnings": [],
    }


def _preflight() -> dict[str, object]:
    return {
        "status": "design_ready",
        "method": "edger",
        "method_family": "edger_count_model",
        "value_type": "count",
        "value_type_policy": "edger_requires_raw_integer_counts",
        "input_package_id": "input-edger-b25-13-fixture",
        "deg_ready_package_id": "deg-ready-edger-b25-13-fixture",
        "gene_id_type": "symbol",
        "contrast": {
            "contrast_id": "case_vs_control",
            "factor": "group",
            "case_level": "case",
            "control_level": "control",
            "case_samples": ["case_1", "case_2"],
            "control_samples": ["control_1", "control_2"],
        },
        "blockers": [],
        "warnings": [],
    }


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    import csv

    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def _numeric(value: object) -> bool:
    try:
        float(str(value))
    except (TypeError, ValueError):
        return False
    return True
