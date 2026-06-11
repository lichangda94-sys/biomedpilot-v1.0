from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the BioMedPilot formal DEG ReleaseBuild gate.")
    parser.add_argument("--skip-full-tests", action="store_true", help="Skip full pytest suites and run runtime/formal DEG gate checks only.")
    parser.add_argument("--json-output", default="", help="Optional JSON output path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    checks: list[dict[str, Any]] = []
    if not args.skip_full_tests:
        checks.append(_run(root, [sys.executable, "-m", "pytest", "tests/bioinformatics", "-q"]))
        checks.append(_run(root, ["bash", "-lc", "QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui -q"]))
    checks.append(_run(root, [sys.executable, "-m", "app.main", "--bio-formal-deg-runtime-check"]))
    runtime_payload = _runtime_payload(root)
    multifactor_payload = _multifactor_runtime_payload(root)
    blockers = [check["check_id"] for check in checks if check["status"] != "passed"]
    if runtime_payload.get("status") not in {"passed", "blocked_missing_dependency"}:
        blockers.append("formal_deg_runtime_validation_failed")
    if multifactor_payload.get("status") != "passed":
        blockers.append("multifactor_deg_runtime_validation_failed")
    payload = {
        "schema_version": "biomedpilot.releasebuild_formal_deg_gate.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "worktree": str(root),
        "skip_full_tests": bool(args.skip_full_tests),
        "status": "blocked" if blockers else "passed",
        "checks": checks,
        "runtime_validation": runtime_payload,
        "multifactor_runtime_validation": multifactor_payload,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": ["runtime_dependencies_missing_but_gracefully_blocked"] if runtime_payload.get("status") == "blocked_missing_dependency" else [],
    }
    if args.json_output:
        output = Path(args.json_output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "passed" else 1


def _runtime_payload(root: Path) -> dict[str, Any]:
    try:
        from app.bioinformatics.deg_engine.runtime_validation import run_formal_deg_runtime_validation

        return run_formal_deg_runtime_validation()
    except Exception as exc:  # pragma: no cover - regression path.
        return {"status": "failed", "blockers": ["runtime_validation_raised_exception"], "error": f"{exc.__class__.__name__}: {exc}"}


def _multifactor_runtime_payload(root: Path) -> dict[str, Any]:
    try:
        from app.bioinformatics.deg_engine.multifactor_r_runner import (
            check_multifactor_r_backend,
            run_controlled_multifactor_deseq2_fixture,
            run_controlled_multifactor_edger_fixture,
            run_controlled_multifactor_limma_fixture,
        )
        from app.bioinformatics.deg_engine.multifactor_schema import validate_multifactor_deg_result_index_entry
        from app.bioinformatics.results.registry import load_registry

        fixture_runners = {
            "limma": lambda path: run_controlled_multifactor_limma_fixture(path, allow_legacy_sidecar_execution=True),
            "DESeq2": lambda path: run_controlled_multifactor_deseq2_fixture(path, allow_legacy_sidecar_execution=True),
            "edgeR": lambda path: run_controlled_multifactor_edger_fixture(path, allow_legacy_sidecar_execution=True),
        }
        dependency_checks = {method: check_multifactor_r_backend(method) for method in fixture_runners}
        fixture_results: dict[str, Any] = {}
        blockers: list[str] = []
        warnings: list[str] = []
        with tempfile.TemporaryDirectory(prefix="biomedpilot_releasebuild_multifactor_deg_") as tmpdir:
            work_root = Path(tmpdir)
            for method, runner in fixture_runners.items():
                method_root = work_root / method.lower()
                method_root.mkdir(parents=True, exist_ok=True)
                result = runner(method_root)
                summary = _summarize_multifactor_fixture(method_root, result, method, validate_multifactor_deg_result_index_entry, load_registry)
                fixture_results[method] = summary
                if summary.get("status") != "passed":
                    blockers.append(f"multifactor_{method}_fixture_not_passed")
                    blockers.extend(str(item) for item in summary.get("blockers", []) or [])
                warnings.extend(str(item) for item in summary.get("warnings", []) or [])
        negative_value_type_checks = _multifactor_negative_value_type_checks()
        for method, check in negative_value_type_checks.items():
            if check.get("status") != "passed":
                blockers.append(f"multifactor_{method}_non_count_blocker_failed")
                blockers.extend(str(item) for item in check.get("blockers", []) or [])
        return {
            "schema_version": "biomedpilot.releasebuild_multifactor_deg_runtime_validation.v1",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": "blocked" if blockers else "passed",
            "worktree": str(root),
            "methods": ["limma", "DESeq2", "edgeR"],
            "dependency_checks": dependency_checks,
            "fixture_results": fixture_results,
            "negative_value_type_checks": negative_value_type_checks,
            "result_schema": "result_index_v2_multifactor_deg",
            "plot_artifacts_expected": [],
            "report_artifacts_expected": [],
            "report_ready_eligible_expected": False,
            "blockers": list(dict.fromkeys(blockers)),
            "warnings": list(dict.fromkeys(warnings)),
        }
    except Exception as exc:  # pragma: no cover - regression path.
        return {"schema_version": "biomedpilot.releasebuild_multifactor_deg_runtime_validation.v1", "status": "failed", "blockers": ["multifactor_runtime_validation_raised_exception"], "error": f"{exc.__class__.__name__}: {exc}"}


def _summarize_multifactor_fixture(
    project_root: Path,
    result: dict[str, Any],
    method: str,
    validate_entry: Any,
    load_registry_fn: Any,
) -> dict[str, Any]:
    blockers = [str(item) for item in result.get("blockers", []) or []]
    warnings = [str(item) for item in result.get("warnings", []) or []]
    result_id = str(result.get("result_id") or "")
    entry: dict[str, Any] = {}
    table_summary = {"row_count": 0, "has_numeric_p_value": False, "has_numeric_fdr": False}
    entry_validation = {"status": "blocked", "blockers": ["result_entry_missing"], "warnings": []}
    if result.get("status") == "passed":
        registry = load_registry_fn(project_root)
        entry = next((item for item in registry.get("results", []) or [] if isinstance(item, dict) and str(item.get("result_id") or "") == result_id), {})
        if not entry:
            blockers.append("multifactor_result_index_entry_missing")
        else:
            entry_validation = validate_entry(entry)
            blockers.extend(str(item) for item in entry_validation.get("blockers", []) or [])
            warnings.extend(str(item) for item in entry_validation.get("warnings", []) or [])
            table_summary = _deg_table_summary(project_root, entry)
            if not table_summary["has_numeric_p_value"]:
                blockers.append("multifactor_result_table_missing_numeric_p_value")
            if not table_summary["has_numeric_fdr"]:
                blockers.append("multifactor_result_table_missing_numeric_adjusted_p_value")
            if entry.get("plot_artifacts") not in ([], ()):
                blockers.append("multifactor_fixture_must_not_register_plot_artifacts")
            if entry.get("report_artifacts") not in ([], ()):
                blockers.append("multifactor_fixture_must_not_register_report_artifacts")
            if entry.get("report_ready_eligible") is not False:
                blockers.append("multifactor_fixture_must_not_be_report_ready")
            if str(entry.get("engine_name") or "") != f"r_{method.lower()}_multifactor":
                blockers.append("multifactor_engine_name_mismatch")
    return {
        "status": "blocked" if blockers or result.get("status") != "passed" else "passed",
        "method": method,
        "result_id": result_id,
        "task_run_id": str(result.get("task_run_id") or ""),
        "result_semantics": str((entry or result.get("result_entry") or {}).get("result_semantics") or ""),
        "engine_name": str((entry or result.get("result_entry") or {}).get("engine_name") or ""),
        "dependency_status": str((result.get("dependency_snapshot") if isinstance(result.get("dependency_snapshot"), dict) else {}).get("status") or ""),
        "parameters_manifest_status": str((result.get("parameter_manifest") if isinstance(result.get("parameter_manifest"), dict) else {}).get("status") or ""),
        "result_index_v2_status": entry_validation.get("status"),
        "task_run_log_present": _task_run_log_present(project_root, entry),
        "output_artifacts": list((entry or {}).get("output_artifacts", []) or []),
        "plot_artifacts": list((entry or {}).get("plot_artifacts", []) or []),
        "report_artifacts": list((entry or {}).get("report_artifacts", []) or []),
        "report_ready_eligible": bool((entry or {}).get("report_ready_eligible")),
        **table_summary,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _multifactor_negative_value_type_checks() -> dict[str, dict[str, Any]]:
    from app.bioinformatics.deg_engine.multifactor_confirmation import build_multifactor_deg_parameter_manifest

    dependency = {"status": "passed", "r_backend": {"packages": {"DESeq2": {"available": True, "version": "test"}, "edgeR": {"available": True, "version": "test"}}}}
    design = {
        "design_formula": "~ batch + group",
        "contrast": {"contrast_id": "group_case_vs_control", "case_group": "case", "control_group": "control"},
        "batch_variables": ["batch"],
        "design_rank": 3,
        "residual_degrees_of_freedom": 3,
        "contrast_estimability": "estimable",
    }
    checks: dict[str, dict[str, Any]] = {}
    for method in ("DESeq2", "edgeR"):
        manifest = build_multifactor_deg_parameter_manifest(
            {"source_input_package_id": "negative-non-count", "deg_ready_package_id": "ready-negative", "value_type": "TPM"},
            design_manifest=design,
            method=method,
            dependency_snapshot=dependency,
        )
        passed = manifest.get("status") == "blocked" and "blocked_count_model_requires_raw_counts" in manifest.get("blockers", [])
        checks[method] = {
            "status": "passed" if passed else "blocked",
            "method": method,
            "value_type": "TPM",
            "expected_blocker": "blocked_count_model_requires_raw_counts",
            "manifest_status": manifest.get("status"),
            "blockers": [] if passed else ["count_model_non_count_value_type_not_blocked"],
        }
    return checks


def _deg_table_summary(project_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    import csv

    artifact = next((item for item in entry.get("output_artifacts", []) or [] if isinstance(item, dict) and item.get("artifact_type") == "deg_result_table"), {})
    table_path = Path(str(artifact.get("path") or ""))
    if not table_path.is_absolute():
        table_path = project_root / table_path
    row_count = 0
    has_numeric_p_value = False
    has_numeric_fdr = False
    if table_path.is_file():
        with table_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                row_count += 1
                has_numeric_p_value = has_numeric_p_value or _is_number(row.get("p_value"))
                has_numeric_fdr = has_numeric_fdr or _is_number(row.get("adjusted_p_value"))
    return {"result_table_row_count": row_count, "has_numeric_p_value": has_numeric_p_value, "has_numeric_fdr": has_numeric_fdr}


def _task_run_log_present(project_root: Path, entry: dict[str, Any]) -> bool:
    for artifact in entry.get("log_artifacts", []) or []:
        if not isinstance(artifact, dict):
            continue
        path = Path(str(artifact.get("path") or ""))
        if not path.is_absolute():
            path = project_root / path
        if path.is_file():
            return True
    return False


def _is_number(value: object) -> bool:
    try:
        float(str(value))
    except (TypeError, ValueError):
        return False
    return True


def _run(root: Path, cmd: list[str]) -> dict[str, Any]:
    completed = subprocess.run(cmd, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return {
        "check_id": " ".join(cmd),
        "status": "passed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "output_tail": completed.stdout[-4000:],
    }


if __name__ == "__main__":
    raise SystemExit(main())
