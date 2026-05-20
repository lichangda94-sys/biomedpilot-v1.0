from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bioinformatics.analysis_inputs import resolve_analysis_inputs
from app.bioinformatics.clinical_analysis.dependency_check import check_survival_backend_dependencies
from app.bioinformatics.deg_engine import build_deg_parameter_manifest, build_formal_deg_result_schema_gate
from app.bioinformatics.deg_engine.confirmation import load_deg_parameter_confirmation, validate_deg_parameter_confirmation
from app.bioinformatics.deg_engine.dependency_check import check_deg_backend_dependencies
from app.bioinformatics.deg_ready.builder import build_deg_ready_package
from app.bioinformatics.project_analysis_tasks import TASK_CENTER, TASK_TEMPLATES, load_task_records
from app.bioinformatics.project_readiness import load_readiness_artifacts
from app.bioinformatics.reports.readiness import evaluate_report_ready_gate
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.project_results import load_result_index

from .action_rules import build_action_rows
from .labels import compact_list, label_package_type, label_semantics, label_status, repair_guidance


def build_analysis_center_state(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    resolver = resolve_analysis_inputs(root).to_dict()
    center = _load_task_center_snapshot(root)
    records = load_task_records(root)
    result_index = load_result_index(root)
    result_entries = [item for item in result_index.get("entries", []) or [] if isinstance(item, dict)]
    deg_dependency = check_deg_backend_dependencies()
    survival_dependency = check_survival_backend_dependencies()
    report_gate = evaluate_report_ready_gate(root)
    packages = [item for item in resolver.get("packages", []) or [] if isinstance(item, dict)]
    tasks = [item for item in center.get("tasks", []) or [] if isinstance(item, dict)]
    deg_gates = build_formal_deg_gate_state(packages=packages, deg_dependency=deg_dependency, project_root=root)
    package_rows = build_package_rows(packages)
    action_rows = build_action_rows(
        packages=packages,
        tasks=tasks,
        results=result_entries,
        deg_dependency=deg_dependency,
        deg_ready_gate=deg_gates["deg_ready_gate"],
        parameter_gate=deg_gates["parameter_gate"],
        confirmation_gate=deg_gates["confirmation_gate"],
        result_schema_gate=deg_gates["result_schema_gate"],
        survival_dependency=survival_dependency,
        report_gate=report_gate,
    )
    result_rows = build_result_gate_rows(result_entries)
    gate_rows = build_gate_preview_rows(result_entries=result_entries, report_gate=report_gate)
    dependency_rows = build_dependency_rows(deg_dependency=deg_dependency, survival_dependency=survival_dependency)
    survival_rows = build_survival_clinical_rows(packages=packages, survival_dependency=survival_dependency)
    blockers = _dedupe([*resolver.get("blockers", [])] + [item for row in package_rows for item in row["raw_blockers"]] + [row["disabled_reason"] for row in action_rows if not row["enabled"] and row["disabled_reason"]])
    warnings = _dedupe([*resolver.get("warnings", [])] + [item for row in package_rows for item in row["raw_warnings"]] + [item for row in dependency_rows for item in row["raw_warnings"]])
    return {
        "schema_version": "biomedpilot.analysis_center_ui_state.v1",
        "project_root": str(root),
        "project_summary": _project_summary(root),
        "standardized_asset_summary": _standardized_asset_summary(resolver),
        "resolver_source": {
            "repository_manifest_path": resolver.get("repository_manifest_path", ""),
            "registry_path": resolver.get("registry_path", ""),
            "source_policy": "standardized repository / registry / analysis_input_repository only",
        },
        "package_rows": package_rows,
        "action_rows": action_rows,
        "dependency_rows": dependency_rows,
        "formal_deg_gate_rows": deg_gates["gate_rows"],
        "result_rows": result_rows,
        "gate_rows": gate_rows,
        "survival_clinical_rows": survival_rows,
        "top_blockers": blockers[:8],
        "top_warnings": warnings[:8],
        "developer_diagnostics": {
            "analysis_task_center": center,
            "task_records": records,
            "result_index": result_index,
            "analysis_input_resolver": resolver,
            "deg_dependency_snapshot": deg_dependency,
            "formal_deg_gate_state": deg_gates,
            "survival_dependency_snapshot": survival_dependency,
            "report_ready_gate": report_gate,
        },
    }


def build_package_rows(packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for package in packages:
        blockers = _list(package.get("blockers"))
        warnings = _list(package.get("warnings"))
        rows.append(
            {
                "package_type": str(package.get("package_type") or ""),
                "package_label": label_package_type(package.get("package_type")),
                "input_package_id": str(package.get("input_package_id") or ""),
                "status": label_status(package.get("status")),
                "semantics": label_semantics(package.get("task_semantics")),
                "source_dataset_id": str(package.get("source_dataset_id") or ""),
                "value_type": str(package.get("value_type") or "unknown"),
                "gene_id_type": str(package.get("gene_id_type") or "unknown"),
                "allowed_downstream_tasks": compact_list(package.get("allowed_downstream_tasks", []) or []),
                "blockers": compact_list(blockers),
                "warnings": compact_list(warnings),
                "repair_action": repair_guidance(blockers, warnings),
                "raw_blockers": blockers,
                "raw_warnings": warnings,
            }
        )
    return rows


def build_dependency_rows(*, deg_dependency: dict[str, Any] | None = None, survival_dependency: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    deg_dependency = deg_dependency or check_deg_backend_dependencies()
    survival_dependency = survival_dependency or check_survival_backend_dependencies()
    rows: list[dict[str, Any]] = []
    packages = deg_dependency.get("packages") if isinstance(deg_dependency.get("packages"), dict) else {}
    for name in ("numpy", "pandas", "scipy", "statsmodels"):
        status = packages.get(name) if isinstance(packages, dict) and isinstance(packages.get(name), dict) else {}
        rows.append(_dependency_row(f"python:{name}", name, status, required=True))
    r_backend = deg_dependency.get("r_backend") if isinstance(deg_dependency.get("r_backend"), dict) else {}
    r_packages = r_backend.get("packages") if isinstance(r_backend.get("packages"), dict) else {}
    for name in ("R", "limma", "DESeq2", "edgeR"):
        rows.append(
            {
                "dependency_id": f"optional_r:{name}",
                "label": name,
                "status": "optional_not_configured",
                "version": str(r_packages.get(name) or "not_checked") if isinstance(r_packages, dict) else "not_checked",
                "blockers": "None",
                "warnings": "Optional R backend is detect-first and not called in B8.9.",
                "action": "Detect only; no install action.",
                "packaging_impact": "optional_not_bundled_for_b9_1",
                "raw_blockers": [],
                "raw_warnings": ["optional_r_backend_not_configured"],
            }
        )
    lifelines = survival_dependency.get("python_lifelines") if isinstance(survival_dependency.get("python_lifelines"), dict) else {}
    rows.append(_dependency_row("python:lifelines", "lifelines", lifelines, required=False, blocker_if_missing="lifelines_missing_formal_survival_disabled"))
    for name in ("survival", "survminer"):
        rows.append(
            {
                "dependency_id": f"optional_r_survival:{name}",
                "label": name,
                "status": "optional_not_configured",
                "version": "not_checked",
                "blockers": "None",
                "warnings": "Survival R backend is design-only; no KM/Cox/log-rank execution.",
                "action": "Detect only; no install action.",
                "packaging_impact": "optional_not_bundled_for_b9_1",
                "raw_blockers": [],
                "raw_warnings": ["survival_r_backend_not_configured"],
            }
        )
    return rows


def build_formal_deg_gate_state(*, packages: list[dict[str, Any]], deg_dependency: dict[str, Any], project_root: str | Path | None = None) -> dict[str, Any]:
    deg_package = next((item for item in packages if item.get("package_type") == "deg_recompute"), None)
    confirmation = load_deg_parameter_confirmation(project_root) if project_root is not None else {}
    confirmed_parameters = confirmation.get("parameter_manifest") if isinstance(confirmation.get("parameter_manifest"), dict) else {}
    if not deg_package:
        deg_ready_gate = {"status": "blocked", "blockers": ["missing_deg_recompute_input_package"], "warnings": []}
        parameter_gate = {"status": "blocked", "blockers": ["missing_deg_ready_package"], "warnings": []}
        result_schema_gate = build_formal_deg_result_schema_gate(parameter_manifest=parameter_gate, dependency_snapshot=deg_dependency)
        confirmation_gate = validate_deg_parameter_confirmation(confirmation, parameter_manifest=parameter_gate, dependency_snapshot=deg_dependency)
    else:
        deg_ready = build_deg_ready_package(deg_package).to_dict()
        deg_ready_gate = {
            "schema_version": deg_ready.get("schema_version", ""),
            "status": "passed" if not deg_ready.get("blockers") else "blocked",
            "deg_ready_package_id": deg_ready.get("deg_ready_package_id", ""),
            "blockers": list(deg_ready.get("blockers", []) or []),
            "warnings": list(deg_ready.get("warnings", []) or []),
            "package": deg_ready,
        }
        parameter_gate = build_deg_parameter_manifest(
            deg_ready,
            method=str(confirmed_parameters.get("method") or "welch_t_test"),
            log2fc_threshold=float(confirmed_parameters.get("log2fc_threshold") or 1.0),
            p_value_threshold=float(confirmed_parameters.get("p_value_threshold") or 0.05),
            fdr_threshold=float(confirmed_parameters.get("fdr_threshold") or 0.05),
            pseudocount=float(confirmed_parameters.get("pseudocount") or 1e-9),
            dependency_snapshot=deg_dependency,
        )
        result_schema_gate = build_formal_deg_result_schema_gate(parameter_manifest=parameter_gate, dependency_snapshot=deg_dependency)
        confirmation_gate = validate_deg_parameter_confirmation(confirmation, parameter_manifest=parameter_gate, dependency_snapshot=deg_dependency)
    gate_rows = [
        _formal_deg_gate_row("Resolver package", "passed" if deg_package and not deg_package.get("blockers") else "blocked", list(deg_package.get("blockers", []) or []) if deg_package else ["missing_deg_recompute_input_package"]),
        _formal_deg_gate_row("DEG-ready matrix", deg_ready_gate.get("status"), deg_ready_gate.get("blockers", []), deg_ready_gate.get("warnings", [])),
        _formal_deg_gate_row("Dependency policy", deg_dependency.get("status"), deg_dependency.get("blockers", []), deg_dependency.get("warnings", []), basis=str(deg_dependency.get("dependency_policy") or "")),
        _formal_deg_gate_row("Parameter manifest", parameter_gate.get("status"), parameter_gate.get("blockers", []), parameter_gate.get("warnings", [])),
        _formal_deg_gate_row("User parameter confirmation", confirmation_gate.get("status"), confirmation_gate.get("blockers", []), confirmation_gate.get("warnings", []), basis="User must confirm comparison, method, thresholds, value type, dependency versions and output plan."),
        _formal_deg_gate_row("Result schema gate", result_schema_gate.get("status"), result_schema_gate.get("blockers", []), result_schema_gate.get("warnings", [])),
        _formal_deg_gate_row("B9.2 controlled activation", "passed", [], [], basis="Enabled only for audited two-group controlled DEG MVP."),
    ]
    return {
        "deg_ready_gate": deg_ready_gate,
        "parameter_gate": parameter_gate,
        "confirmation_gate": confirmation_gate,
        "parameter_confirmation": confirmation,
        "result_schema_gate": result_schema_gate,
        "gate_rows": gate_rows,
    }


def _formal_deg_gate_row(gate: str, status: object, blockers: object, warnings: object = (), *, basis: str = "") -> dict[str, Any]:
    return {
        "gate": gate,
        "status": str(status or "blocked"),
        "basis": basis,
        "blockers": compact_list(blockers if isinstance(blockers, list | tuple) else []),
        "warnings": compact_list(warnings if isinstance(warnings, list | tuple) else []),
    }


def build_result_gate_rows(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not entries:
        return [
            {
                "result_id": "none",
                "semantics": "no result",
                "input_package_id": "",
                "engine": "",
                "dependency_snapshot": "missing",
                "validation_status": "not_validated",
                "plot_status": "blocked: no source result",
                "report_status": "blocked: result_index_missing_or_empty",
                "blockers": "result_index_missing_or_empty",
                "warnings": "None",
            }
        ]
    rows: list[dict[str, Any]] = []
    for entry in entries:
        semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"))
        blockers = _list(entry.get("blockers"))
        warnings = _list(entry.get("warnings"))
        plot_status = _plot_status(entry, semantics)
        report_status = "candidate only" if entry.get("report_ready_eligible") else "draft only / not report-ready"
        rows.append(
            {
                "result_id": str(entry.get("result_id") or entry.get("result_name") or ""),
                "semantics": label_semantics(semantics),
                "input_package_id": str(entry.get("input_package_id") or ""),
                "engine": _engine_text(entry),
                "dependency_snapshot": "present" if entry.get("dependency_snapshot") else "missing",
                "validation_status": str(entry.get("validation_status") or "not_validated"),
                "plot_status": plot_status,
                "report_status": report_status,
                "blockers": compact_list(blockers),
                "warnings": compact_list(warnings),
            }
        )
    return rows


def build_gate_preview_rows(*, result_entries: list[dict[str, Any]], report_gate: dict[str, Any]) -> list[dict[str, Any]]:
    result_blockers = []
    if not result_entries:
        result_blockers.append("result_index_missing_or_empty")
    plot_eligible = [entry for entry in result_entries if normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics")) not in {"preflight_only", "configured_not_run", "blocked", "failed"}]
    preflight_sources = [entry for entry in result_entries if normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics")) == "preflight_only"]
    return [
        {
            "gate": "Result index v2",
            "status": "available" if result_entries else "blocked_missing_result_schema",
            "basis": f"{len(result_entries)} result entries",
            "blockers": compact_list(result_blockers),
            "warnings": "Testing/imported/exploratory entries keep their semantics.",
        },
        {
            "gate": "Plot artifact",
            "status": "available" if plot_eligible else "blocked_missing_result_schema",
            "basis": f"{len(plot_eligible)} source-result-driven candidates",
            "blockers": compact_list(["preflight_only_source_cannot_generate_formal_plot"] if preflight_sources and not plot_eligible else []),
            "warnings": "No formal plotting upgrade; plot inherits source semantics.",
        },
        {
            "gate": "Report-ready export",
            "status": "available" if report_gate.get("status") == "eligible_for_internal_report" else "blocked_report_ready_gate",
            "basis": str(report_gate.get("status") or "blocked"),
            "blockers": compact_list(report_gate.get("blockers", []) or []),
            "warnings": compact_list(report_gate.get("warnings", []) or []),
        },
    ]


def build_survival_clinical_rows(*, packages: list[dict[str, Any]], survival_dependency: dict[str, Any]) -> list[dict[str, Any]]:
    package = next((item for item in packages if item.get("package_type") == "tcga_clinical_survival_preflight"), None)
    blockers = _list(package.get("blockers")) if package else ["missing_survival_preflight_package"]
    warnings = _list(package.get("warnings")) if package else []
    dep_blockers = _list(survival_dependency.get("blockers"))
    package_status = str(package.get("status") or "missing") if package else "missing"
    asset_status = "clinical asset present" if package and package.get("clinical_asset") else "clinical asset missing"
    return [
        {
            "row_id": "survival_preflight",
            "label": "Survival design preflight",
            "status": "preflight_only" if package and not blockers else "blocked",
            "asset_status": asset_status,
            "backend_status": str(survival_dependency.get("status") or "unknown"),
            "disabled_reason": compact_list(blockers + dep_blockers),
            "warnings": compact_list(warnings),
        },
        {
            "row_id": "km_cox_logrank",
            "label": "KM/Cox/log-rank/HR",
            "status": "hidden_until_ready",
            "asset_status": package_status,
            "backend_status": str(survival_dependency.get("status") or "unknown"),
            "disabled_reason": "Survival statistics are disabled in B8.9; no KM plot, HR, Cox or log-rank p-value.",
            "warnings": "design/preflight only",
        },
        {
            "row_id": "clinical_association",
            "label": "Clinical association preflight",
            "status": "preflight_only" if package and not blockers else "blocked",
            "asset_status": asset_status,
            "backend_status": "not used for formal statistics",
            "disabled_reason": "Formal p-values are disabled; only variable mapping/preflight is allowed.",
            "warnings": "No clinical advice.",
        },
    ]


def _dependency_row(dependency_id: str, label: str, status: dict[str, Any], *, required: bool, blocker_if_missing: str = "") -> dict[str, Any]:
    available = status.get("available") is True
    blocker = "" if available or not required else f"missing_python_package:{label}"
    if not available and blocker_if_missing:
        blocker = blocker_if_missing
    return {
        "dependency_id": dependency_id,
        "label": label,
        "status": "installed" if available else ("missing" if required else "optional_missing"),
        "version": str(status.get("version") or ""),
        "blockers": blocker or "None",
        "warnings": "Detect-first only; no auto-install.",
        "action": "Detect only; no install action.",
        "packaging_impact": str(status.get("packaging_impact") or ("required_in_packaged_app_for_formal_deg" if required else "optional")),
        "raw_blockers": [blocker] if blocker else [],
        "raw_warnings": ["detect_first_no_install"],
    }


def _project_summary(root: Path) -> dict[str, str]:
    return {"project_root": str(root), "project_name": root.name}


def _load_task_center_snapshot(root: Path) -> dict[str, Any]:
    existing = _read_json(root / TASK_CENTER)
    if existing:
        return existing
    matrix = load_readiness_artifacts(root).get("capability_matrix")
    capability_rows: dict[str, dict[str, Any]] = {}
    if isinstance(matrix, dict):
        for row in matrix.get("rows", []) or []:
            if isinstance(row, dict):
                capability_rows[str(row.get("analysis_type"))] = row
    tasks: list[dict[str, Any]] = []
    for template in TASK_TEMPLATES:
        task_type = str(template["task_type"])
        capability = capability_rows.get(task_type, {})
        warnings = [str(item) for item in capability.get("warnings", []) or []] if isinstance(capability, dict) else []
        if task_type == "tcga_gtex_joint" and not warnings:
            warnings.append("当前未进行正式 batch correction，结果仅用于 preview / testing。")
        missing = [str(item) for item in capability.get("missing_inputs", []) or []] if isinstance(capability, dict) else []
        available = [str(item) for item in capability.get("available_inputs", []) or []] if isinstance(capability, dict) else []
        can_run = bool(capability.get("can_run")) if isinstance(capability, dict) else False
        tasks.append(
            {
                "task_type": task_type,
                "label": template["label"],
                "can_run": can_run,
                "available_inputs": available,
                "missing_inputs": missing if matrix else ["analysis_capability_matrix.json 尚未生成"],
                "warnings": warnings,
                "default_parameters": template["default_parameters"],
                "preview_status": "testing / preview",
            }
        )
    return {
        "schema_version": "biomedpilot.analysis_task_center.v1",
        "generated_at": "",
        "project_root": str(root),
        "tasks": tasks,
        "snapshot_mode": "read_only_no_manifest_write",
    }


def _standardized_asset_summary(resolver: dict[str, Any]) -> dict[str, Any]:
    packages = [item for item in resolver.get("packages", []) or [] if isinstance(item, dict)]
    return {
        "package_count": len(packages),
        "blocked_package_count": sum(1 for item in packages if item.get("blockers")),
        "warning_package_count": sum(1 for item in packages if item.get("warnings")),
        "resolver_blockers": list(resolver.get("blockers", []) or []),
        "resolver_warnings": list(resolver.get("warnings", []) or []),
    }


def _engine_text(entry: dict[str, Any]) -> str:
    engine = str(entry.get("engine_name") or "")
    version = str(entry.get("engine_version") or "")
    return f"{engine} {version}".strip()


def _plot_status(entry: dict[str, Any], semantics: str) -> str:
    if semantics == "preflight_only":
        return "blocked: preflight-only source"
    if entry.get("plot_artifacts"):
        return "registered"
    if semantics in {"formal_computed_result", "testing_level", "exploratory", "imported_external_result"}:
        return "spec candidate; inherits semantics"
    return "blocked: missing result schema"


def _list(value: object) -> list[str]:
    if isinstance(value, list | tuple):
        return [str(item) for item in value if str(item)]
    return []


def _dedupe(values: list[object]) -> list[str]:
    return list(dict.fromkeys(str(item) for item in values if str(item)))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}
