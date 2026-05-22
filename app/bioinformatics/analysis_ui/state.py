from __future__ import annotations

from pathlib import Path
from typing import Any

from app.bioinformatics.analysis_inputs import resolve_analysis_inputs
from app.bioinformatics.acquisition_adapters.legacy_contract import LEGACY_ADAPTER_MANIFEST_DIR
from app.bioinformatics.acquisition_adapters.materialization import LEGACY_MATERIALIZATION_MANIFEST_PATH
from app.bioinformatics.acquisition_adapters.repository_merge import LEGACY_REPOSITORY_MERGE_MANIFEST
from app.bioinformatics.acquisition_adapters.selection_gate import LEGACY_ASSET_SELECTION_PATH
from app.bioinformatics.acquisition_adapters.standardized_bridge import LEGACY_ASSET_CANDIDATE_PATH
from app.bioinformatics.clinical_analysis.dependency_check import check_survival_backend_dependencies
from app.bioinformatics.deg_engine import build_deg_parameter_manifest, build_formal_deg_result_schema_gate, build_multifactor_deg_preflight_manifest
from app.bioinformatics.deg_engine.confirmation import load_deg_parameter_confirmation, validate_deg_parameter_confirmation
from app.bioinformatics.deg_engine.dependency_check import check_deg_backend_dependencies
from app.bioinformatics.deg_ready.builder import build_deg_ready_package
from app.bioinformatics.enrichment import build_ora_gene_set_resource_gate, build_ora_input_gate, build_ora_parameter_manifest, build_ora_result_schema_gate, check_ora_backend_dependencies
from app.bioinformatics.gsea import build_gsea_gene_set_resource_gate, build_gsea_parameter_manifest, build_gsea_preranked_input_gate, build_gsea_result_schema_gate, check_gsea_backend_dependencies
from app.bioinformatics.project_analysis_tasks import TASK_CENTER, TASK_TEMPLATES, load_task_records
from app.bioinformatics.project_readiness import load_readiness_artifacts
from app.bioinformatics.reports.formal_deg import evaluate_formal_deg_report_ready_gate
from app.bioinformatics.reports.gsea import evaluate_gsea_report_ready_gate
from app.bioinformatics.reports.ora import evaluate_ora_report_ready_gate
from app.bioinformatics.reports.readiness import evaluate_report_ready_gate
from app.bioinformatics.results.models import normalize_result_semantics
from app.bioinformatics.results.project_results import load_result_index
from app.bioinformatics.plots import build_gsea_plot_gate, build_ora_plot_gate
from app.bioinformatics.survival_clinical import (
    audit_clinical_variables,
    audit_cox_multivariate_design,
    build_cox_univariate_parameter_manifest,
    build_km_logrank_parameter_manifest,
    build_survival_outcome_gate,
    load_cox_univariate_confirmation,
    load_km_logrank_confirmation,
    resolve_survival_clinical_inputs,
    validate_cox_univariate_confirmation,
    validate_km_logrank_confirmation,
)
from app.bioinformatics.survival_clinical._io import read_table

from .action_rules import build_action_rows
from .capability_map import build_analysis_capability_map
from .labels import compact_list, label_package_type, label_semantics, label_status, repair_guidance


def build_analysis_center_state(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    resolver = resolve_analysis_inputs(root).to_dict()
    center = _load_task_center_snapshot(root)
    records = load_task_records(root)
    result_index = load_result_index(root, persist_generated=False)
    result_entries = [item for item in result_index.get("entries", []) or [] if isinstance(item, dict)]
    deg_dependency = check_deg_backend_dependencies()
    survival_dependency = check_survival_backend_dependencies()
    report_gate = evaluate_report_ready_gate(root)
    formal_deg_report_gate = evaluate_formal_deg_report_ready_gate(root)
    ora_report_gate = evaluate_ora_report_ready_gate(root)
    gsea_report_gate = evaluate_gsea_report_ready_gate(root)
    packages = [item for item in resolver.get("packages", []) or [] if isinstance(item, dict)]
    tasks = [item for item in center.get("tasks", []) or [] if isinstance(item, dict)]
    deg_gates = build_formal_deg_gate_state(packages=packages, deg_dependency=deg_dependency, project_root=root)
    multi_factor_deg_gate = build_multifactor_deg_preflight_manifest(
        deg_gates.get("deg_ready_package") if isinstance(deg_gates.get("deg_ready_package"), dict) else {},
        dependency_snapshot=deg_dependency,
    )
    deg_gates["multi_factor_deg_gate"] = multi_factor_deg_gate
    deg_gates["gate_rows"].append(
        _formal_deg_gate_row(
            "Multi-factor DEG preflight",
            multi_factor_deg_gate.get("status"),
            multi_factor_deg_gate.get("blockers", []),
            multi_factor_deg_gate.get("warnings", []),
            basis=f"{multi_factor_deg_gate.get('method_family') or 'missing'} / {multi_factor_deg_gate.get('value_type_policy') or 'missing'}",
        )
    )
    ora_gates = build_ora_gate_state(project_root=root)
    ora_plot_gate = build_ora_plot_gate(root)
    gsea_plot_gate = build_gsea_plot_gate(root)
    gsea_gates = build_gsea_gate_state(project_root=root)
    survival_clinical_state = build_survival_clinical_gate_state(project_root=root)
    legacy_pipeline = build_legacy_asset_pipeline_state(root)
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
        km_parameter_gate=survival_clinical_state["km_parameter_gate"],
        km_confirmation_gate=survival_clinical_state["km_confirmation_gate"],
        cox_parameter_gate=survival_clinical_state["cox_parameter_gate"],
        cox_confirmation_gate=survival_clinical_state["cox_confirmation_gate"],
        report_gate=report_gate,
        formal_deg_report_gate=formal_deg_report_gate,
        ora_input_gate=ora_gates["input_gate"],
        ora_gene_set_gate=ora_gates["gene_set_gate"],
        ora_parameter_gate=ora_gates["parameter_gate"],
        ora_result_schema_gate=ora_gates["result_schema_gate"],
        ora_dependency=ora_gates["dependency_snapshot"],
        ora_plot_gate=ora_plot_gate,
        ora_report_gate=ora_report_gate,
        gsea_plot_gate=gsea_plot_gate,
        gsea_report_gate=gsea_report_gate,
        gsea_input_gate=gsea_gates["input_gate"],
        gsea_rank_metric_gate=gsea_gates["rank_metric_gate"],
        gsea_gene_set_gate=gsea_gates["gene_set_gate"],
        gsea_parameter_gate=gsea_gates["parameter_gate"],
        gsea_result_schema_gate=gsea_gates["result_schema_gate"],
        gsea_dependency=gsea_gates["dependency_snapshot"],
        survival_clinical_state=survival_clinical_state,
        legacy_asset_pipeline=legacy_pipeline,
    )
    result_rows = build_result_gate_rows(result_entries)
    gate_rows = build_gate_preview_rows(result_entries=result_entries, report_gate=report_gate, formal_deg_report_gate=formal_deg_report_gate, ora_report_gate=ora_report_gate)
    dependency_rows = build_dependency_rows(deg_dependency=deg_dependency, survival_dependency=survival_dependency)
    survival_rows = build_survival_clinical_rows(packages=packages, survival_dependency=survival_dependency, survival_clinical_state=survival_clinical_state)
    capability_map = build_analysis_capability_map(
        action_rows=action_rows,
        formal_deg_gate_rows=deg_gates["gate_rows"],
        ora_gate_rows=ora_gates["gate_rows"],
        gsea_gate_rows=gsea_gates["gate_rows"],
        survival_clinical_rows=survival_rows,
        dependency_rows=dependency_rows,
        multi_factor_deg_gate=multi_factor_deg_gate,
    )
    blockers = _dedupe(
        [*resolver.get("blockers", [])]
        + [item for row in package_rows for item in row["raw_blockers"]]
        + [row["disabled_reason"] for row in action_rows if not row["enabled"] and row["disabled_reason"]]
        + [item for item in multi_factor_deg_gate.get("blockers", []) or []]
        + [item for gate in (ora_gates["input_gate"], ora_gates["gene_set_gate"], ora_gates["parameter_gate"], ora_gates["result_schema_gate"], ora_gates["dependency_snapshot"], ora_plot_gate, ora_report_gate, gsea_plot_gate, gsea_report_gate) for item in gate.get("blockers", []) or []]
        + [item for gate in (gsea_gates["input_gate"], gsea_gates["rank_metric_gate"], gsea_gates["gene_set_gate"], gsea_gates["parameter_gate"], gsea_gates["result_schema_gate"], gsea_gates["dependency_snapshot"]) for item in gate.get("blockers", []) or []]
    )
    warnings = _dedupe(
        [*resolver.get("warnings", [])]
        + [item for row in package_rows for item in row["raw_warnings"]]
        + [item for row in dependency_rows for item in row["raw_warnings"]]
        + [item for item in multi_factor_deg_gate.get("warnings", []) or []]
        + [item for gate in (ora_gates["input_gate"], ora_gates["gene_set_gate"], ora_gates["parameter_gate"], ora_gates["result_schema_gate"], ora_gates["dependency_snapshot"], ora_plot_gate, ora_report_gate, gsea_plot_gate, gsea_report_gate) for item in gate.get("warnings", []) or []]
        + [item for gate in (gsea_gates["input_gate"], gsea_gates["rank_metric_gate"], gsea_gates["gene_set_gate"], gsea_gates["parameter_gate"], gsea_gates["result_schema_gate"], gsea_gates["dependency_snapshot"]) for item in gate.get("warnings", []) or []]
    )
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
        "multi_factor_deg_gate": multi_factor_deg_gate,
        "ora_gate_rows": ora_gates["gate_rows"],
        "gsea_gate_rows": gsea_gates["gate_rows"],
        "legacy_asset_pipeline": legacy_pipeline,
        "analysis_capability_map": capability_map,
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
            "multi_factor_deg_gate": multi_factor_deg_gate,
            "ora_gate_state": ora_gates,
            "ora_plot_gate": ora_plot_gate,
            "ora_report_ready_gate": ora_report_gate,
            "gsea_plot_gate": gsea_plot_gate,
            "gsea_report_ready_gate": gsea_report_gate,
            "gsea_gate_state": gsea_gates,
            "survival_clinical_state": survival_clinical_state,
            "legacy_asset_pipeline": legacy_pipeline,
            "analysis_capability_map": capability_map,
            "survival_dependency_snapshot": survival_dependency,
            "report_ready_gate": report_gate,
            "formal_deg_report_ready_gate": formal_deg_report_gate,
        },
    }


def build_legacy_asset_pipeline_state(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    adapter_manifest_paths = sorted((root / LEGACY_ADAPTER_MANIFEST_DIR).glob("*.json"))
    candidate_bundle = _read_json(root / LEGACY_ASSET_CANDIDATE_PATH)
    materialized_manifest = _read_json(root / LEGACY_MATERIALIZATION_MANIFEST_PATH)
    merge_manifest = _read_json(root / LEGACY_REPOSITORY_MERGE_MANIFEST)
    selection_manifest = _read_json(root / LEGACY_ASSET_SELECTION_PATH)
    rows = [
        _legacy_pipeline_row(
            "legacy_adapter_manifests",
            "Legacy acquisition adapter manifests",
            root / LEGACY_ADAPTER_MANIFEST_DIR,
            exists=bool(adapter_manifest_paths),
            count=len(adapter_manifest_paths),
            status="candidate_input_available" if adapter_manifest_paths else "not_started",
            blockers=[],
            warnings=[],
            next_action="Build standardized asset candidates from audited legacy adapter manifests.",
        ),
        _legacy_pipeline_payload_row(
            "legacy_asset_candidates",
            "Standardized asset candidates",
            root / LEGACY_ASSET_CANDIDATE_PATH,
            candidate_bundle,
            count_field="candidate_count",
            default_present_status="candidate_only",
            next_action="Select candidates for materialization; candidates are not repository assets yet.",
        ),
        _legacy_pipeline_payload_row(
            "legacy_materialized_assets",
            "Materialized candidate assets",
            root / LEGACY_MATERIALIZATION_MANIFEST_PATH,
            materialized_manifest,
            count_field="materialized_asset_count",
            default_present_status="materialized_candidates_only",
            next_action="Merge materialized assets into the standardized repository manifest.",
        ),
        _legacy_pipeline_payload_row(
            "legacy_repository_merge",
            "Repository manifest merge",
            root / LEGACY_REPOSITORY_MERGE_MANIFEST,
            merge_manifest,
            count_field="merged_asset_count",
            default_present_status="merged_repository_manifest_only",
            next_action="Run B16.4 user asset selection and then B8 resolver/DEG-ready gates.",
        ),
        _legacy_selection_row(root / LEGACY_ASSET_SELECTION_PATH, selection_manifest),
    ]
    present_rows = [row for row in rows if row["artifact_present"]]
    blockers = _dedupe([item for row in rows for item in row["raw_blockers"]])
    warnings = _dedupe([item for row in rows for item in row["raw_warnings"]])
    operations = _legacy_pipeline_operations(rows)
    return {
        "schema_version": "biomedpilot.analysis_ui_legacy_asset_pipeline_state.v1",
        "status": "available_for_review" if present_rows and not blockers else ("blocked" if blockers else "not_started"),
        "project_root": str(root),
        "row_count": len(rows),
        "artifact_count": len(present_rows),
        "rows": rows,
        "operations": operations,
        "blockers": blockers,
        "warnings": warnings,
        "formal_analysis_enabled": False,
        "writes_analysis_input_repository": False,
        "writes_result_index": False,
        "report_ready_eligible": False,
        "boundary_message": "Legacy assets are acquisition/standardization inputs only; formal analysis still requires B8 resolver and downstream task gates.",
    }


def _legacy_pipeline_operations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(row.get("row_id") or ""): row for row in rows}
    adapter_ready = bool(by_id.get("legacy_adapter_manifests", {}).get("artifact_present"))
    candidates_ready = bool(by_id.get("legacy_asset_candidates", {}).get("artifact_present"))
    materialized_ready = bool(by_id.get("legacy_materialized_assets", {}).get("artifact_present"))
    merge_ready = bool(by_id.get("legacy_repository_merge", {}).get("artifact_present"))
    return [
        _legacy_operation("legacy_build_candidates", "Build legacy asset candidates", adapter_ready, "legacy_adapter_manifests_missing", "Writes candidate-only standardized asset bundle."),
        _legacy_operation("legacy_materialize_candidates", "Materialize legacy candidates", candidates_ready, "legacy_asset_candidates_missing", "Writes isolated repository files and materialization manifest only."),
        _legacy_operation("legacy_merge_repository_manifest", "Merge legacy assets into repository manifest", materialized_ready, "legacy_materialized_assets_missing", "Writes standardized repository manifest/validation/lineage only."),
        _legacy_operation("legacy_confirm_asset_selection", "Confirm legacy asset selection", merge_ready, "legacy_repository_merge_missing", "Writes user-confirmed default asset selection only; downstream gates still decide readiness."),
    ]


def _legacy_operation(operation_id: str, label: str, enabled: bool, blocker: str, next_action: str) -> dict[str, Any]:
    return {
        "operation_id": operation_id,
        "label": label,
        "enabled": enabled,
        "state": "available" if enabled else "blocked",
        "disabled_reason": "" if enabled else blocker,
        "button_behavior": "controlled_standardization_artifact_write_no_formal_execution",
        "next_action": next_action,
    }


def _legacy_pipeline_payload_row(
    row_id: str,
    label: str,
    artifact_path: Path,
    payload: dict[str, Any],
    *,
    count_field: str,
    default_present_status: str,
    next_action: str,
) -> dict[str, Any]:
    exists = bool(payload)
    status = str(payload.get("status") or default_present_status) if exists else "not_started"
    return _legacy_pipeline_row(
        row_id,
        label,
        artifact_path,
        exists=exists,
        count=int(payload.get(count_field) or len(payload.get("assets", []) or []) if exists else 0),
        status=status,
        blockers=_list(payload.get("blockers")),
        warnings=_list(payload.get("warnings")),
        next_action=next_action,
    )


def _legacy_selection_row(artifact_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    validation = payload.get("validation") if isinstance(payload.get("validation"), dict) else {}
    selected = payload.get("selected_assets") if isinstance(payload.get("selected_assets"), dict) else {}
    selected_count = sum(1 for item in selected.values() if isinstance(item, dict) and item.get("asset_id"))
    blockers = _list(validation.get("selection_blockers")) + _list(validation.get("downstream_blockers"))
    warnings = _list(validation.get("warnings")) + _list(payload.get("warnings"))
    return _legacy_pipeline_row(
        "legacy_asset_selection",
        "User-confirmed asset selection",
        artifact_path,
        exists=bool(payload),
        count=selected_count,
        status=str(payload.get("status") or "not_started") if payload else "not_started",
        blockers=blockers,
        warnings=warnings,
        next_action="Use selection only as standardized repository default selection; resolver and downstream gates decide analysis eligibility.",
    )


def _legacy_pipeline_row(
    row_id: str,
    label: str,
    artifact_path: Path,
    *,
    exists: bool,
    count: int,
    status: str,
    blockers: list[str],
    warnings: list[str],
    next_action: str,
) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "label": label,
        "status": status,
        "artifact_present": exists,
        "artifact_path": str(artifact_path),
        "count_summary": str(count) if exists else "0",
        "blockers": compact_list(blockers),
        "warnings": compact_list(warnings),
        "disabled_reason": "Legacy pipeline is review/materialization/standardization only; it cannot run formal DEG/GSEA/survival/report-ready.",
        "next_action": next_action,
        "raw_blockers": blockers,
        "raw_warnings": warnings,
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
    deg_ready_package: dict[str, Any] = {}
    if not deg_package:
        deg_ready_gate = {"status": "blocked", "blockers": ["missing_deg_recompute_input_package"], "warnings": []}
        parameter_gate = {"status": "blocked", "blockers": ["missing_deg_ready_package"], "warnings": []}
        result_schema_gate = build_formal_deg_result_schema_gate(parameter_manifest=parameter_gate, dependency_snapshot=deg_dependency)
        confirmation_gate = validate_deg_parameter_confirmation(confirmation, parameter_manifest=parameter_gate, dependency_snapshot=deg_dependency)
    else:
        deg_ready = build_deg_ready_package(deg_package).to_dict()
        deg_ready_package = deg_ready
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
        "deg_ready_package": deg_ready_package,
        "gate_rows": gate_rows,
    }


def build_ora_gate_state(*, project_root: str | Path) -> dict[str, Any]:
    input_gate = build_ora_input_gate(project_root)
    gene_set_gate = build_ora_gene_set_resource_gate(
        project_root,
        expected_species=str(input_gate.get("species") or "unknown"),
        expected_gene_id_type=str(input_gate.get("source_gene_id_type") or "unknown"),
    )
    parameter_gate = build_ora_parameter_manifest(input_gate, gene_set_gate)
    dependency = check_ora_backend_dependencies()
    result_schema_gate = build_ora_result_schema_gate(parameter_manifest=parameter_gate)
    gate_rows = [
        _formal_deg_gate_row(
            "ORA source DEG result",
            input_gate.get("status"),
            input_gate.get("blockers", []),
            input_gate.get("warnings", []),
            basis=f"{input_gate.get('source_result_id') or 'missing'} / {input_gate.get('source_result_semantics') or 'missing'}",
        ),
        _formal_deg_gate_row(
            "ORA gene set resource",
            gene_set_gate.get("status") or gene_set_gate.get("validation_status"),
            gene_set_gate.get("blockers", []),
            gene_set_gate.get("warnings", []),
            basis=str(gene_set_gate.get("resource_name") or "local GMT or project registry only"),
        ),
        _formal_deg_gate_row(
            "ORA parameter manifest",
            parameter_gate.get("status"),
            parameter_gate.get("blockers", []),
            parameter_gate.get("warnings", []),
            basis=f"{parameter_gate.get('test_method') or 'hypergeometric'} / {parameter_gate.get('multiple_testing_policy') or 'missing'}",
        ),
        _formal_deg_gate_row(
            "ORA dependency policy",
            dependency.get("status"),
            dependency.get("blockers", []),
            dependency.get("warnings", []),
            basis="Detect-first scipy/statsmodels; no install action.",
        ),
        _formal_deg_gate_row(
            "ORA future result schema",
            result_schema_gate.get("status"),
            result_schema_gate.get("blockers", []),
            result_schema_gate.get("warnings", []),
            basis="Defines future ora_enrichment result index v2 fields only; no execution in B10.1.",
        ),
        _formal_deg_gate_row(
            "B10.2 controlled ORA execution",
            "passed" if not _dedupe([*input_gate.get("blockers", []), *gene_set_gate.get("blockers", []), *parameter_gate.get("blockers", []), *result_schema_gate.get("blockers", []), *dependency.get("blockers", [])]) else "blocked",
            [],
            [],
            basis="Run controlled ORA is enabled only when source, local GMT, parameters, schema and dependencies pass.",
        ),
    ]
    return {
        "input_gate": input_gate,
        "gene_set_gate": gene_set_gate,
        "parameter_gate": parameter_gate,
        "dependency_snapshot": dependency,
        "result_schema_gate": result_schema_gate,
        "gate_rows": gate_rows,
    }


def build_gsea_gate_state(*, project_root: str | Path) -> dict[str, Any]:
    input_gate = build_gsea_preranked_input_gate(project_root)
    rank_metric_gate = input_gate.get("rank_metric_gate") if isinstance(input_gate.get("rank_metric_gate"), dict) else {}
    gene_set_gate = build_gsea_gene_set_resource_gate(project_root, gsea_input=input_gate)
    parameter_gate = build_gsea_parameter_manifest(input_gate, gene_set_gate)
    dependency = check_gsea_backend_dependencies()
    result_schema_gate = build_gsea_result_schema_gate(parameter_manifest=parameter_gate)
    gate_rows = [
        _formal_deg_gate_row(
            "GSEA source DEG result",
            input_gate.get("status"),
            input_gate.get("blockers", []),
            input_gate.get("warnings", []),
            basis=f"{input_gate.get('source_result_id') or 'missing'} / {input_gate.get('source_result_semantics') or 'missing'}",
        ),
        _formal_deg_gate_row(
            "GSEA rank metric",
            rank_metric_gate.get("status"),
            rank_metric_gate.get("blockers", []),
            rank_metric_gate.get("warnings", []),
            basis=f"{rank_metric_gate.get('rank_metric') or input_gate.get('rank_metric') or 'missing'} / ranked genes={rank_metric_gate.get('ranked_gene_count', 0)}",
        ),
        _formal_deg_gate_row(
            "GSEA gene set resource",
            gene_set_gate.get("status"),
            gene_set_gate.get("blockers", []),
            gene_set_gate.get("warnings", []),
            basis=f"{gene_set_gate.get('resource_name') or 'local GMT/project registry only'} / overlap terms={gene_set_gate.get('overlapping_term_count', 0)}",
        ),
        _formal_deg_gate_row(
            "GSEA parameter manifest",
            parameter_gate.get("status"),
            parameter_gate.get("blockers", []),
            parameter_gate.get("warnings", []),
            basis=f"{parameter_gate.get('rank_metric') or 'missing'} / permutations planned={parameter_gate.get('permutation_count', '')}",
        ),
        _formal_deg_gate_row(
            "GSEA dependency policy",
            dependency.get("status"),
            dependency.get("blockers", []),
            dependency.get("warnings", []),
            basis="Detect-first numpy/pandas/scipy/statsmodels; no install action.",
        ),
        _formal_deg_gate_row(
            "GSEA future result schema",
            result_schema_gate.get("status"),
            result_schema_gate.get("blockers", []),
            result_schema_gate.get("warnings", []),
            basis="Requires B11.2 gsea_preranked result index v2 fields.",
        ),
        _formal_deg_gate_row(
            "B11.2 controlled GSEA execution",
            "passed" if not _dedupe([*input_gate.get("blockers", []), *rank_metric_gate.get("blockers", []), *gene_set_gate.get("blockers", []), *parameter_gate.get("blockers", []), *result_schema_gate.get("blockers", []), *dependency.get("blockers", [])]) else "blocked",
            [],
            [],
            basis="Enabled only for controlled preranked GSEA MVP; no phenotype permutation, plot or report-ready.",
        ),
    ]
    return {
        "input_gate": input_gate,
        "rank_metric_gate": rank_metric_gate,
        "gene_set_gate": gene_set_gate,
        "parameter_gate": parameter_gate,
        "dependency_snapshot": dependency,
        "result_schema_gate": result_schema_gate,
        "gate_rows": gate_rows,
    }


def build_survival_clinical_gate_state(*, project_root: str | Path) -> dict[str, Any]:
    input_state = resolve_survival_clinical_inputs(project_root)
    outcome_gate = build_survival_outcome_gate(project_root, input_state) if input_state.get("clinical_asset") else {"status": "blocked", "blockers": ["missing_clinical_asset"], "warnings": []}
    variable_audit = audit_clinical_variables(project_root, input_state) if input_state.get("clinical_asset") else {"status": "blocked", "blockers": ["missing_clinical_asset"], "warnings": [], "variables": [], "summary": {}}
    runtime_variable_audit = _clinical_variable_audit_for_runtime(variable_audit)
    runtime_package = _survival_runtime_package(input_state, outcome_gate)
    clinical_rows = read_table(_clinical_asset_path(Path(project_root), input_state))
    grouping_variable, group_a, group_b = _default_km_grouping(clinical_rows, runtime_package)
    dependency = check_survival_backend_dependencies()
    km_parameter_gate = build_km_logrank_parameter_manifest(
        runtime_package,
        outcome_gate=outcome_gate,
        clinical_variable_audit=runtime_variable_audit,
        grouping_variable=grouping_variable,
        group_a=group_a,
        group_b=group_b,
        dependency_snapshot=dependency,
    )
    km_confirmation = load_km_logrank_confirmation(project_root)
    km_confirmation_gate = validate_km_logrank_confirmation(km_confirmation, km_parameter_gate)
    covariate = _default_cox_covariate(clinical_rows, runtime_package, runtime_variable_audit)
    cox_parameter_gate = build_cox_univariate_parameter_manifest(
        runtime_package,
        outcome_gate=outcome_gate,
        clinical_variable_audit=runtime_variable_audit,
        covariate=covariate,
        dependency_snapshot=dependency,
    )
    cox_confirmation = load_cox_univariate_confirmation(project_root)
    cox_confirmation_gate = validate_cox_univariate_confirmation(cox_confirmation, cox_parameter_gate)
    cox_multivariate_design = audit_cox_multivariate_design(runtime_package, runtime_variable_audit)
    gate_rows = [
        _formal_deg_gate_row(
            "Survival/clinical input resolver",
            input_state.get("status"),
            input_state.get("blockers", []),
            input_state.get("warnings", []),
            basis=f"mapped cases={input_state.get('mapped_case_count', 0)}; mapped samples={input_state.get('mapped_sample_count', 0)}",
        ),
        _formal_deg_gate_row(
            "OS_time / OS_event / censoring gate",
            outcome_gate.get("status"),
            outcome_gate.get("blockers", []),
            outcome_gate.get("warnings", []),
            basis=f"time={outcome_gate.get('time_field', '')}; event={outcome_gate.get('event_field', '')}; events={outcome_gate.get('event_count', 0)}",
        ),
        _formal_deg_gate_row(
            "Clinical variable typing / missingness",
            variable_audit.get("status"),
            variable_audit.get("blockers", []),
            variable_audit.get("warnings", []),
            basis=f"variables={variable_audit.get('variable_count', 0)}; candidates={variable_audit.get('summary', {})}",
        ),
        _formal_deg_gate_row(
            "B13 KM/log-rank parameters",
            km_parameter_gate.get("status"),
            km_parameter_gate.get("blockers", []),
            km_parameter_gate.get("warnings", []),
        ),
        _formal_deg_gate_row(
            "B13 KM/log-rank user confirmation",
            km_confirmation_gate.get("status"),
            km_confirmation_gate.get("blockers", []),
            km_confirmation_gate.get("warnings", []),
        ),
        _formal_deg_gate_row(
            "B14 Cox univariate parameters",
            cox_parameter_gate.get("status"),
            cox_parameter_gate.get("blockers", []),
            cox_parameter_gate.get("warnings", []),
        ),
        _formal_deg_gate_row(
            "B14 Cox user confirmation",
            cox_confirmation_gate.get("status"),
            cox_confirmation_gate.get("blockers", []),
            cox_confirmation_gate.get("warnings", []),
        ),
        _formal_deg_gate_row(
            "B14 Cox multivariate design audit",
            "blocked" if cox_multivariate_design.get("blockers") else "design_only",
            cox_multivariate_design.get("blockers", []),
            cox_multivariate_design.get("warnings", []),
            basis="design audit only; no multivariate execution",
        ),
        _formal_deg_gate_row(
            "Survival dependency",
            dependency.get("status"),
            dependency.get("blockers", []),
            dependency.get("warnings", []),
            basis="lifelines detect-first; no install action",
        ),
    ]
    return {
        "input_resolver": input_state,
        "outcome_gate": outcome_gate,
        "clinical_variable_audit": variable_audit,
        "clinical_variable_runtime_audit": runtime_variable_audit,
        "runtime_package": runtime_package,
        "km_parameter_gate": km_parameter_gate,
        "km_confirmation_gate": km_confirmation_gate,
        "km_parameter_confirmation": km_confirmation,
        "cox_parameter_gate": cox_parameter_gate,
        "cox_confirmation_gate": cox_confirmation_gate,
        "cox_parameter_confirmation": cox_confirmation,
        "cox_multivariate_design": cox_multivariate_design,
        "gate_rows": gate_rows,
    }


def _survival_runtime_package(input_state: dict[str, Any], outcome_gate: dict[str, Any]) -> dict[str, Any]:
    event_coding = outcome_gate.get("event_coding") if isinstance(outcome_gate.get("event_coding"), dict) else {}
    return {
        **input_state,
        "survival_package_id": str(input_state.get("survival_clinical_input_id") or ""),
        "time_field": str(outcome_gate.get("time_field") or ""),
        "event_field": str(outcome_gate.get("event_field") or ""),
        "time_unit": str(outcome_gate.get("time_unit") or "days"),
        "event_coding": event_coding,
        "censoring_policy": str(outcome_gate.get("censoring_policy") or "event=1 observed, event=0 censored; ambiguous coding blocks"),
        "missingness_report": {},
        "event_count": int(outcome_gate.get("event_count") or 0),
        "sample_count": int(outcome_gate.get("sample_count") or input_state.get("sample_count") or 0),
    }


def _clinical_variable_audit_for_runtime(variable_audit: dict[str, Any]) -> dict[str, Any]:
    if isinstance(variable_audit.get("variable_mapping"), dict):
        return variable_audit
    mapping: dict[str, dict[str, Any]] = {}
    variables = variable_audit.get("variables") if isinstance(variable_audit.get("variables"), list) else []
    type_map = {
        "binary": "binary_variable",
        "categorical": "categorical_variable",
        "continuous": "continuous_variable",
        "ordinal": "ordinal_variable",
        "time_to_event": "time_to_event_variable",
        "identifier": "identifier",
        "unknown": "unknown_variable",
        "date": "date_variable",
        "text": "unknown_variable",
    }
    for item in variables:
        if not isinstance(item, dict):
            continue
        name = str(item.get("variable_name") or "")
        if not name:
            continue
        source_type = str(item.get("variable_type") or "")
        mapping[name] = {
            **item,
            "variable_type": type_map.get(source_type, source_type or "unknown_variable"),
            "missing_fraction": item.get("missing_rate", item.get("missing_fraction", 0.0)),
        }
    return {**variable_audit, "variable_mapping": mapping}


def _clinical_asset_path(root: Path, input_state: dict[str, Any]) -> Path | None:
    asset = input_state.get("clinical_asset") if isinstance(input_state.get("clinical_asset"), dict) else {}
    value = str(asset.get("path") or asset.get("file_path") or "")
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def _default_km_grouping(rows: list[dict[str, str]], survival_package: dict[str, Any]) -> tuple[str, str, str]:
    excluded = {str(survival_package.get("time_field") or ""), str(survival_package.get("event_field") or "")}
    identifier_fields = {"sample_id", "case_id", "barcode", "tcga_barcode", "patient_barcode", "participant_barcode", "bcr_patient_barcode"}
    for field in rows[0].keys() if rows else []:
        if field in excluded or field in identifier_fields:
            continue
        values = sorted({str(row.get(field) or "").strip() for row in rows if str(row.get(field) or "").strip()})
        if len(values) == 2:
            return field, values[0], values[1]
    return "", "", ""


def _default_cox_covariate(rows: list[dict[str, str]], survival_package: dict[str, Any], audit: dict[str, Any]) -> str:
    excluded = {str(survival_package.get("time_field") or ""), str(survival_package.get("event_field") or "")}
    identifier_fields = {"sample_id", "case_id", "barcode", "tcga_barcode", "patient_barcode", "participant_barcode", "bcr_patient_barcode"}
    variables = audit.get("variables") if isinstance(audit.get("variables"), list) else []
    for spec in variables:
        if not isinstance(spec, dict):
            continue
        name = str(spec.get("variable_name") or "")
        variable_type = str(spec.get("variable_type") or "")
        if name in excluded or name in identifier_fields:
            continue
        if variable_type in {"binary", "categorical", "continuous", "ordinal"} and not spec.get("blockers"):
            return name
    for field in rows[0].keys() if rows else []:
        if field not in excluded and field not in identifier_fields:
            return field
    return ""


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


def build_gate_preview_rows(
    *,
    result_entries: list[dict[str, Any]],
    report_gate: dict[str, Any],
    formal_deg_report_gate: dict[str, Any] | None = None,
    ora_report_gate: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    result_blockers = []
    if not result_entries:
        result_blockers.append("result_index_missing_or_empty")
    plot_eligible = [
        entry
        for entry in result_entries
        if normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics")) == "formal_computed_result"
        and str(entry.get("task_type") or "").lower() == "deg"
        and any(isinstance(item, dict) and item.get("artifact_type") == "deg_result_table" for item in entry.get("output_artifacts", []) or [])
    ]
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
            "basis": f"{len(plot_eligible)} formal DEG result candidates",
            "blockers": compact_list(["preflight_only_source_cannot_generate_formal_plot"] if preflight_sources and not plot_eligible else []),
            "warnings": "Formal DEG plot artifacts require formal_computed_result DEG sources and inherit source semantics.",
        },
        {
            "gate": "Formal DEG report-ready",
            "status": "available" if (formal_deg_report_gate or {}).get("status") == "eligible_for_formal_deg_report_ready" else "blocked_formal_deg_report_ready_gate",
            "basis": str((formal_deg_report_gate or {}).get("status") or "blocked"),
            "blockers": compact_list((formal_deg_report_gate or {}).get("blockers", []) or []),
            "warnings": compact_list((formal_deg_report_gate or {}).get("warnings", []) or []),
        },
        {
            "gate": "ORA report-ready",
            "status": "available" if (ora_report_gate or {}).get("status") in {"eligible_for_ora_report_ready", "eligible_for_imported_derived_ora_report_package"} else "blocked_ora_report_ready_gate",
            "basis": str((ora_report_gate or {}).get("status") or "blocked"),
            "blockers": compact_list((ora_report_gate or {}).get("blockers", []) or []),
            "warnings": compact_list((ora_report_gate or {}).get("warnings", []) or []),
        },
        {
            "gate": "Report-ready export",
            "status": "available" if report_gate.get("status") == "eligible_for_internal_report" else "blocked_report_ready_gate",
            "basis": str(report_gate.get("status") or "blocked"),
            "blockers": compact_list(report_gate.get("blockers", []) or []),
            "warnings": compact_list(report_gate.get("warnings", []) or []),
        },
    ]


def build_survival_clinical_rows(*, packages: list[dict[str, Any]], survival_dependency: dict[str, Any], survival_clinical_state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    package = next((item for item in packages if item.get("package_type") == "tcga_clinical_survival_preflight"), None)
    survival_clinical_state = survival_clinical_state or {}
    input_state = survival_clinical_state.get("input_resolver") if isinstance(survival_clinical_state.get("input_resolver"), dict) else {}
    outcome_gate = survival_clinical_state.get("outcome_gate") if isinstance(survival_clinical_state.get("outcome_gate"), dict) else {}
    variable_audit = survival_clinical_state.get("clinical_variable_audit") if isinstance(survival_clinical_state.get("clinical_variable_audit"), dict) else {}
    km_parameter_gate = survival_clinical_state.get("km_parameter_gate") if isinstance(survival_clinical_state.get("km_parameter_gate"), dict) else {}
    km_confirmation_gate = survival_clinical_state.get("km_confirmation_gate") if isinstance(survival_clinical_state.get("km_confirmation_gate"), dict) else {}
    cox_parameter_gate = survival_clinical_state.get("cox_parameter_gate") if isinstance(survival_clinical_state.get("cox_parameter_gate"), dict) else {}
    cox_confirmation_gate = survival_clinical_state.get("cox_confirmation_gate") if isinstance(survival_clinical_state.get("cox_confirmation_gate"), dict) else {}
    cox_multivariate_design = survival_clinical_state.get("cox_multivariate_design") if isinstance(survival_clinical_state.get("cox_multivariate_design"), dict) else {}
    blockers = _list(package.get("blockers")) if package else ["missing_survival_preflight_package"]
    warnings = _list(package.get("warnings")) if package else []
    dep_blockers = _list(survival_dependency.get("blockers"))
    package_status = str(package.get("status") or "missing") if package else "missing"
    asset_status = "clinical asset present" if package and package.get("clinical_asset") else "clinical asset missing"
    return [
        {
            "row_id": "survival_clinical_input_resolver",
            "label": "Survival / clinical input resolver",
            "status": str(input_state.get("status") or "blocked"),
            "asset_status": f"clinical={bool(input_state.get('clinical_asset'))}; expression={bool(input_state.get('expression_asset'))}; sample_metadata={bool(input_state.get('sample_metadata_asset'))}",
            "backend_status": "not used for input resolver",
            "disabled_reason": compact_list(input_state.get("blockers", []) or []),
            "warnings": compact_list(input_state.get("warnings", []) or []),
        },
        {
            "row_id": "case_sample_mapping",
            "label": "Case/sample mapping",
            "status": str(input_state.get("case_sample_mapping_status") or "blocked"),
            "asset_status": f"mapped cases={input_state.get('mapped_case_count', 0)}; mapped samples={input_state.get('mapped_sample_count', 0)}",
            "backend_status": "not used for mapping",
            "disabled_reason": compact_list(input_state.get("blockers", []) or []),
            "warnings": compact_list([*input_state.get("unmapped_cases", [])[:3], *input_state.get("unmapped_samples", [])[:3]] if isinstance(input_state.get("unmapped_cases"), list) and isinstance(input_state.get("unmapped_samples"), list) else input_state.get("warnings", []) or []),
        },
        {
            "row_id": "survival_outcome_gate",
            "label": "OS_time / OS_event / censoring gate",
            "status": str(outcome_gate.get("status") or "blocked"),
            "asset_status": f"time={outcome_gate.get('time_field', '')}; event={outcome_gate.get('event_field', '')}; events={outcome_gate.get('event_count', 0)}; censored={outcome_gate.get('censored_count', 0)}",
            "backend_status": "not used for KM/Cox",
            "disabled_reason": compact_list(outcome_gate.get("blockers", []) or []),
            "warnings": compact_list(outcome_gate.get("warnings", []) or []),
        },
        {
            "row_id": "clinical_variable_audit",
            "label": "Clinical variable typing / missingness",
            "status": str(variable_audit.get("status") or "blocked"),
            "asset_status": f"variables={variable_audit.get('variable_count', 0)}; candidates={variable_audit.get('summary', {})}",
            "backend_status": "not used for statistics",
            "disabled_reason": compact_list(variable_audit.get("blockers", []) or []),
            "warnings": compact_list(variable_audit.get("warnings", []) or []),
        },
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
            "label": "Two-group KM/log-rank",
            "status": str(km_parameter_gate.get("status") or "blocked"),
            "asset_status": package_status,
            "backend_status": str(survival_dependency.get("status") or "unknown"),
            "disabled_reason": compact_list(_list(km_parameter_gate.get("blockers")) + _list(km_confirmation_gate.get("blockers")) + _list(survival_dependency.get("blockers"))),
            "warnings": compact_list(_list(km_parameter_gate.get("warnings"))),
        },
        {
            "row_id": "km_plot_artifact",
            "label": "KM plot artifact/spec",
            "status": "available_after_survival_km_logrank_result",
            "asset_status": "spec-only no image dependency",
            "backend_status": "not matplotlib/R/survminer",
            "disabled_reason": "Requires formal_computed_result survival_km_logrank source; image_artifacts=[] in B13.",
            "warnings": "No PNG/SVG/PDF generated in B13.",
        },
        {
            "row_id": "cox_hr",
            "label": "Single-variable Cox",
            "status": str(cox_parameter_gate.get("status") or "blocked"),
            "asset_status": package_status,
            "backend_status": str(survival_dependency.get("status") or "unknown"),
            "disabled_reason": compact_list(_list(cox_parameter_gate.get("blockers")) + _list(cox_confirmation_gate.get("blockers")) + _list(survival_dependency.get("blockers"))),
            "warnings": compact_list(_list(cox_parameter_gate.get("warnings"))),
        },
        {
            "row_id": "cox_forest_plot",
            "label": "Cox forest plot artifact/spec",
            "status": "available_after_cox_univariate_result",
            "asset_status": "spec-only no image dependency",
            "backend_status": "not matplotlib/R/ggplot2",
            "disabled_reason": "Requires formal_computed_result cox_univariate source; image_artifacts=[] in B14.",
            "warnings": "No PNG/SVG/PDF generated in B14.",
        },
        {
            "row_id": "cox_multivariate_design",
            "label": "Multivariate Cox design audit",
            "status": "blocked" if cox_multivariate_design.get("blockers") else "design_only",
            "asset_status": f"event_per_variable={cox_multivariate_design.get('event_per_variable', '')}",
            "backend_status": "execution disabled",
            "disabled_reason": compact_list(_list(cox_multivariate_design.get("blockers"))),
            "warnings": compact_list(_list(cox_multivariate_design.get("warnings"))),
        },
        {
            "row_id": "risk_score",
            "label": "Risk score / nomogram",
            "status": "disabled",
            "asset_status": package_status,
            "backend_status": "not enabled",
            "disabled_reason": "Risk score, nomogram and clinical risk grouping are not implemented in B14.",
            "warnings": "No prognosis or treatment recommendation.",
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
    if semantics == "formal_computed_result" and str(entry.get("task_type") or "").lower() == "deg":
        return "formal DEG plot artifact candidate; inherits semantics"
    if semantics in {"testing_level", "exploratory", "imported_external_result"}:
        return "blocked: not a formal DEG plot source"
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
