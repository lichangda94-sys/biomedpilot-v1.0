from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.bioinformatics.deg_engine.confirmation import CONFIRMATION_PATH, CONFIRMATION_SCHEMA_VERSION, load_deg_parameter_confirmation
from app.bioinformatics.deg_engine.models import REQUIRED_DEG_RESULT_COLUMNS
from app.bioinformatics.deg_engine.result_schema import validate_deg_result_entry, validate_formal_deg_result_index_entry
from app.bioinformatics.plots.schema import validate_plot_artifact
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.registry import RESULT_INDEX, load_registry, save_registry


FORMAL_DEG_REPORT_READY_SCHEMA_VERSION = "biomedpilot.formal_deg_report_ready_gate.v1"
FORMAL_DEG_REPORT_PACKAGE_SCHEMA_VERSION = "biomedpilot.formal_deg_report_ready_package.v1"
FORMAL_DEG_CONFIRMATION_MAX_AGE_DAYS = 7


def evaluate_formal_deg_report_ready_gate(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
    max_confirmation_age_days: int = FORMAL_DEG_CONFIRMATION_MAX_AGE_DAYS,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = _select_formal_deg_entry(entries, result_id)
    confirmation = load_deg_parameter_confirmation(root)
    blockers: list[str] = []
    warnings: list[str] = []
    checks: dict[str, bool] = {
        "formal_deg_result_present": selected is not None,
        "result_index_v2_complete": False,
        "parameter_confirmation_present": bool(confirmation),
        "parameter_confirmation_not_expired": False,
        "dependency_snapshot_passed": False,
        "deg_result_table_validation_passed": False,
        "plot_artifact_or_table_only_mode": False,
        "warnings_limitations_provenance_included": True,
        "formal_deg_only": False,
        "no_gsea_survival_or_clinical_conclusion": True,
    }
    if selected is None:
        blockers.append("formal_deg_result_not_found")
    else:
        checks["formal_deg_only"] = _is_formal_deg(selected)
        if not checks["formal_deg_only"]:
            blockers.append("formal_deg_report_ready_requires_formal_computed_deg_result")
        schema_validation = validate_formal_deg_result_index_entry(selected)
        checks["result_index_v2_complete"] = schema_validation.get("status") == "passed"
        blockers.extend(f"result_index:{item}" for item in schema_validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in schema_validation.get("warnings", []) or [])
        dependency = selected.get("dependency_snapshot") if isinstance(selected.get("dependency_snapshot"), dict) else {}
        checks["dependency_snapshot_passed"] = dependency.get("status") == "passed"
        if not checks["dependency_snapshot_passed"]:
            blockers.append("formal_deg_dependency_snapshot_not_passed")
        table_validation = _validate_deg_table(root, selected)
        checks["deg_result_table_validation_passed"] = table_validation["status"] == "passed"
        blockers.extend(f"deg_table:{item}" for item in table_validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in table_validation.get("warnings", []) or [])
        plot_validation = _validate_plot_requirement(selected, allow_table_only_report=allow_table_only_report)
        checks["plot_artifact_or_table_only_mode"] = plot_validation["status"] == "passed"
        blockers.extend(str(item) for item in plot_validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in plot_validation.get("warnings", []) or [])
        confirmation_validation = _validate_confirmation(confirmation, selected, max_age_days=max_confirmation_age_days)
        checks["parameter_confirmation_not_expired"] = confirmation_validation["not_expired"]
        blockers.extend(str(item) for item in confirmation_validation.get("blockers", []) or [])
        warnings.extend(str(item) for item in confirmation_validation.get("warnings", []) or [])
    for check_name, passed in checks.items():
        if not passed and check_name not in {"formal_deg_result_present", "parameter_confirmation_present"}:
            blockers.append(check_name)
    if not checks["parameter_confirmation_present"]:
        blockers.append("formal_deg_parameter_confirmation_missing")
    status = "blocked" if blockers else "eligible_for_formal_deg_report_ready"
    return {
        "schema_version": FORMAL_DEG_REPORT_READY_SCHEMA_VERSION,
        "created_at": _now(),
        "status": status,
        "selected_result_id": str((selected or {}).get("result_id") or result_id or ""),
        "result_index_path": str(root / RESULT_INDEX),
        "confirmation_path": str(root / CONFIRMATION_PATH),
        "allow_table_only_report": allow_table_only_report,
        "max_confirmation_age_days": max_confirmation_age_days,
        "checks": checks,
        "limitations_required": _limitations(),
        "provenance_required": _provenance(selected or {}, root),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def create_formal_deg_report_ready_package(
    project_root: str | Path,
    *,
    result_id: str | None = None,
    allow_table_only_report: bool = False,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    gate = evaluate_formal_deg_report_ready_gate(root, result_id=result_id, allow_table_only_report=allow_table_only_report)
    if gate["status"] == "blocked":
        return {
            "schema_version": FORMAL_DEG_REPORT_PACKAGE_SCHEMA_VERSION,
            "status": "blocked",
            "package_path": "",
            "gate": gate,
            "blockers": gate["blockers"],
            "warnings": gate["warnings"],
        }
    registry = load_registry(root)
    entries = [entry for entry in registry.get("results", []) if isinstance(entry, dict)]
    selected = next(entry for entry in entries if str(entry.get("result_id") or "") == str(gate["selected_result_id"]))
    package_dir = root / "report_package" / "formal_deg"
    tables_dir = package_dir / "tables"
    plots_dir = package_dir / "plots"
    manifests_dir = package_dir / "manifests"
    logs_dir = package_dir / "logs"
    for directory in (tables_dir, plots_dir, manifests_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    table_path = _deg_table_path(root, selected)
    if table_path.is_file():
        shutil.copy2(table_path, tables_dir / table_path.name)
    _copy_artifacts(root, selected.get("log_artifacts", []) or [], logs_dir)
    _write_json(manifests_dir / "formal_deg_result_entry.json", selected)
    _write_json(manifests_dir / "formal_deg_parameter_confirmation.json", load_deg_parameter_confirmation(root))
    _write_json(manifests_dir / "dependency_snapshot.json", selected.get("dependency_snapshot", {}))
    _write_json(manifests_dir / "plot_artifacts.json", selected.get("plot_artifacts", []) or [])
    _write_json(manifests_dir / "validation_report.json", gate)
    _write_json(manifests_dir / "provenance.json", gate.get("provenance_required", {}))
    _write_json(manifests_dir / "warnings.json", {"warnings": gate.get("warnings", []), "result_warnings": selected.get("warnings", []) or []})
    (package_dir / "README_limitations.md").write_text(_limitations_markdown(), encoding="utf-8")
    (package_dir / "formal_deg_report.md").write_text(_formal_deg_report_markdown(selected, gate), encoding="utf-8")
    manifest = {
        "schema_version": FORMAL_DEG_REPORT_PACKAGE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "formal_deg_report_ready_package_created",
        "package_path": str(package_dir),
        "section_scope": "formal_deg_only",
        "included_result_ids": [str(selected.get("result_id") or "")],
        "excluded_result_semantics": ["imported_external_result", "testing_level", "exploratory", "preflight_only"],
        "gsea_enabled": False,
        "survival_enabled": False,
        "clinical_conclusion_enabled": False,
        "allow_table_only_report": allow_table_only_report,
        "gate": gate,
    }
    _write_json(package_dir / "formal_deg_report_package_manifest.json", manifest)
    selected["report_ready_eligible"] = True
    selected["report_artifacts"] = [
        *[item for item in selected.get("report_artifacts", []) or [] if isinstance(item, dict) and item.get("artifact_type") != "formal_deg_report_ready_package"],
        {
            "artifact_type": "formal_deg_report_ready_package",
            "path": str((package_dir / "formal_deg_report_package_manifest.json").relative_to(root)),
            "schema": FORMAL_DEG_REPORT_PACKAGE_SCHEMA_VERSION,
            "section_scope": "formal_deg_only",
        },
    ]
    selected["updated_at"] = _now()
    save_registry(root, entries)
    return manifest


def _select_formal_deg_entry(entries: list[dict[str, Any]], result_id: str | None) -> dict[str, Any] | None:
    if result_id:
        return next((entry for entry in entries if str(entry.get("result_id") or "") == result_id), None)
    candidates = [entry for entry in entries if _is_formal_deg(entry)]
    return candidates[-1] if candidates else None


def _is_formal_deg(entry: dict[str, Any]) -> bool:
    return normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") == "formal_computed_result" and str(entry.get("task_type") or "").lower() == "deg"


def _validate_confirmation(confirmation: dict[str, Any], entry: dict[str, Any], *, max_age_days: int) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    if not confirmation:
        return {"not_expired": False, "blockers": ["formal_deg_parameter_confirmation_missing"], "warnings": warnings}
    if confirmation.get("schema_version") != CONFIRMATION_SCHEMA_VERSION:
        blockers.append("formal_deg_parameter_confirmation_schema_mismatch")
    if confirmation.get("status") != "confirmed" or confirmation.get("confirmed_by_user") is not True:
        blockers.append("formal_deg_parameters_not_user_confirmed")
    created_at = _parse_datetime(confirmation.get("created_at"))
    not_expired = bool(created_at and datetime.now(timezone.utc) - created_at <= timedelta(days=max_age_days))
    if not not_expired:
        blockers.append("formal_deg_parameter_confirmation_expired")
    output_plan = confirmation.get("output_plan") if isinstance(confirmation.get("output_plan"), dict) else {}
    if output_plan.get("result_id") != entry.get("result_id"):
        blockers.append("formal_deg_confirmation_result_id_mismatch")
    confirmed_parameters = confirmation.get("parameter_manifest") if isinstance(confirmation.get("parameter_manifest"), dict) else {}
    if confirmed_parameters != entry.get("parameters_manifest"):
        blockers.append("formal_deg_confirmation_parameters_mismatch_result_index")
    confirmed_dependency = confirmation.get("dependency_snapshot") if isinstance(confirmation.get("dependency_snapshot"), dict) else {}
    if confirmed_dependency.get("status") != "passed":
        blockers.append("formal_deg_confirmation_dependency_not_passed")
    return {"not_expired": not_expired, "blockers": blockers, "warnings": warnings}


def _validate_deg_table(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    path = _deg_table_path(root, entry)
    blockers: list[str] = []
    warnings: list[str] = []
    if not path.is_file():
        return {"status": "blocked", "path": str(path), "row_count": 0, "blockers": ["deg_result_table_missing"], "warnings": warnings}
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        reader = csv.DictReader([first, *handle.readlines()], delimiter=delimiter)
        columns = reader.fieldnames or []
        for column in REQUIRED_DEG_RESULT_COLUMNS:
            if column not in columns:
                blockers.append(f"missing_column:{column}")
        row_count = 0
        for row_count, row in enumerate(reader, start=1):
            validation = validate_deg_result_entry(row)
            blockers.extend(f"row_{row_count}:{item}" for item in validation.get("blockers", []) or [])
    if row_count == 0:
        blockers.append("deg_result_table_has_no_rows")
    return {"status": "blocked" if blockers else "passed", "path": str(path), "row_count": row_count, "blockers": list(dict.fromkeys(blockers)), "warnings": warnings}


def _validate_plot_requirement(entry: dict[str, Any], *, allow_table_only_report: bool) -> dict[str, Any]:
    artifacts = [item for item in entry.get("plot_artifacts", []) or [] if isinstance(item, dict)]
    passed_plots: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    for artifact in artifacts:
        validation = validate_plot_artifact(artifact)
        if (
            validation.get("status") == "passed"
            and artifact.get("plot_artifact_scope") == "formal_deg_plot"
            and artifact.get("source_result_id") == entry.get("result_id")
            and normalize_result_semantics(artifact.get("source_result_semantics"), default="") == "formal_computed_result"
            and normalize_result_semantics(artifact.get("plot_semantics"), default="") == "formal_computed_result"
            and not artifact.get("blockers")
        ):
            passed_plots.append(str(artifact.get("plot_id") or "plot"))
    if passed_plots:
        return {"status": "passed", "plot_ids": passed_plots, "blockers": [], "warnings": warnings}
    if allow_table_only_report:
        warnings.append("formal_deg_table_only_report_mode_no_plot_artifact")
        return {"status": "passed", "plot_ids": [], "blockers": [], "warnings": warnings}
    blockers.append("formal_deg_report_ready_requires_formal_plot_artifact_or_table_only_mode")
    return {"status": "blocked", "plot_ids": [], "blockers": blockers, "warnings": warnings}


def _deg_table_path(root: Path, entry: dict[str, Any]) -> Path:
    artifacts = entry.get("output_artifacts") if isinstance(entry.get("output_artifacts"), list) else []
    artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("artifact_type") == "deg_result_table"), {})
    path = Path(str(artifact.get("path") or ""))
    return path if path.is_absolute() else root / path


def _provenance(entry: dict[str, Any], root: Path) -> dict[str, Any]:
    return {
        "result_id": str(entry.get("result_id") or ""),
        "task_run_id": str(entry.get("task_run_id") or ""),
        "input_package_id": str(entry.get("input_package_id") or ""),
        "source_repository_manifest": str(entry.get("source_repository_manifest") or ""),
        "parameter_confirmation_path": str(root / CONFIRMATION_PATH),
        "dependency_snapshot_present": bool(entry.get("dependency_snapshot")),
        "result_index_path": str(root / RESULT_INDEX),
        "result_table_path": str(_deg_table_path(root, entry)) if entry else "",
        "plot_artifact_count": len(entry.get("plot_artifacts", []) or []) if entry else 0,
        "log_artifacts": entry.get("log_artifacts", []) if entry else [],
    }


def _formal_deg_report_markdown(entry: dict[str, Any], gate: dict[str, Any]) -> str:
    parameters = entry.get("parameters_manifest") if isinstance(entry.get("parameters_manifest"), dict) else {}
    deps = entry.get("dependency_snapshot") if isinstance(entry.get("dependency_snapshot"), dict) else {}
    packages = deps.get("packages") if isinstance(deps.get("packages"), dict) else {}
    lines = [
        "# Formal DEG Report-Ready Section",
        "",
        "This report-ready package is limited to the audited formal DEG result section.",
        "It does not include GSEA, survival analysis, clinical association, or clinical conclusions.",
        "",
        "## Formal DEG Result",
        "",
        f"- result_id: {entry.get('result_id', '')}",
        f"- task_run_id: {entry.get('task_run_id', '')}",
        f"- input_package_id: {entry.get('input_package_id', '')}",
        f"- method: {parameters.get('method', '')}",
        f"- thresholds: log2FC={parameters.get('log2fc_threshold', '')}, p={parameters.get('p_value_threshold', '')}, FDR={parameters.get('fdr_threshold', '')}",
        f"- samples: case={len(parameters.get('case_samples', []) or [])}, control={len(parameters.get('control_samples', []) or [])}",
        "",
        "## Dependency Snapshot",
        "",
    ]
    for name in ("numpy", "pandas", "scipy", "statsmodels"):
        status = packages.get(name) if isinstance(packages.get(name), dict) else {}
        lines.append(f"- {name}: {status.get('version', '')}")
    warning_lines = [f"- {item}" for item in [*(entry.get("warnings", []) or []), *(gate.get("warnings", []) or [])]] or ["- None"]
    lines.extend(["", "## Warnings", "", *warning_lines, "", "## Limitations", "", *[f"- {item}" for item in _limitations()], "", "## Provenance", ""])
    for key, value in (gate.get("provenance_required", {}) or {}).items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines).rstrip() + "\n"


def _limitations() -> list[str]:
    return [
        "Formal DEG statistical results only; not a clinical conclusion or treatment recommendation.",
        "GSEA is disabled and not included.",
        "Survival, KM, Cox, log-rank, HR, and clinical association are disabled and not included.",
        "Imported, testing, exploratory, and preflight outputs are excluded from this formal report-ready package.",
        "Warnings, limitations, dependencies, parameters, and provenance must stay attached to the report package.",
    ]


def _limitations_markdown() -> str:
    return "# Limitations\n\n" + "\n".join(f"- {item}" for item in _limitations()) + "\n"


def _copy_artifacts(root: Path, artifacts: object, target_dir: Path) -> None:
    if not isinstance(artifacts, list | tuple):
        return
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        path = Path(str(artifact.get("path") or artifact.get("file_path") or "")).expanduser()
        if not path.is_absolute():
            path = root / path
        if path.is_file():
            shutil.copy2(path, target_dir / path.name)


def _parse_datetime(value: object) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
