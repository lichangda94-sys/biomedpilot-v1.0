from __future__ import annotations

from pathlib import Path
from typing import Any

from app.analysis_runtime.architecture_status import build_analysis_architecture_status, build_analysis_remediation_queue
from app.analysis_runtime.package_catalog import build_standard_analysis_package_catalog
from app.analysis_runtime.resources import validate_analysis_environment_registry
from app.bioinformatics.analysis_inputs import resolve_analysis_inputs
from app.bioinformatics.acquisition_adapters.legacy_contract import LEGACY_ADAPTER_MANIFEST_DIR
from app.bioinformatics.acquisition_adapters.materialization import LEGACY_MATERIALIZATION_MANIFEST_PATH
from app.bioinformatics.acquisition_adapters.repository_merge import LEGACY_REPOSITORY_MERGE_MANIFEST
from app.bioinformatics.acquisition_adapters.selection_gate import LEGACY_ASSET_SELECTION_PATH
from app.bioinformatics.acquisition_adapters.standardized_bridge import LEGACY_ASSET_CANDIDATE_PATH
from app.bioinformatics.clinical_analysis import build_clinical_association_preflight, build_survival_package, build_survival_preflight
from app.bioinformatics.clinical_analysis.dependency_check import check_survival_backend_dependencies
from app.bioinformatics.deg_engine import (
    build_deg_data_quality_gate,
    build_deg_design_quality_gate,
    build_deg_input_adaptation_gate,
    build_deg_method_recommendation_gate,
    build_deg_parameter_manifest,
    build_formal_deg_result_schema_gate,
    build_multifactor_deg_parameter_manifest,
    build_multifactor_deg_result_schema_gate,
    check_multifactor_r_backend,
    load_multifactor_deg_parameter_confirmation,
    validate_multifactor_deg_parameter_confirmation,
)
from app.bioinformatics.deg_engine.confirmation import load_deg_parameter_confirmation, validate_deg_parameter_confirmation
from app.bioinformatics.deg_engine.dependency_check import check_deg_backend_dependencies
from app.bioinformatics.deg_ready.builder import build_deg_ready_package
from app.bioinformatics.enrichment_backend import build_enrichment_backend_gate
from app.bioinformatics.enrichment_acceptance import build_enrichment_cross_library_acceptance_gate
from app.bioinformatics.enrichment_execution_gate import build_enrichment_execution_gate
from app.bioinformatics.enrichment_input_contract import build_enrichment_input_contract_gate
from app.bioinformatics.enrichment_plot_report import build_enrichment_plot_gate, evaluate_enrichment_section_report_ready_gate
from app.bioinformatics.enrichment_result_review import build_enrichment_result_review
from app.bioinformatics.enrichment_result_schema import build_enrichment_statistical_policy, validate_enrichment_result_schema_gate
from app.bioinformatics.enrichment_resources import build_enrichment_library_policy, build_enrichment_resource_lock
from app.bioinformatics.gene_set_resources import GENE_SET_REGISTRY
from app.bioinformatics.survival_clinical import (
    audit_cox_multivariate_design,
    build_cox_univariate_parameter_manifest,
    build_km_logrank_parameter_manifest,
    load_cox_univariate_confirmation,
    load_km_logrank_confirmation,
    validate_cox_univariate_confirmation,
    validate_km_logrank_confirmation,
)
from app.bioinformatics.survival_clinical._io import asset_path, read_table
from app.bioinformatics.project_analysis_tasks import TASK_CENTER, TASK_TEMPLATES, load_task_records
from app.bioinformatics.project_readiness import load_readiness_artifacts
from app.bioinformatics.reports.formal_deg import evaluate_formal_deg_report_ready_gate
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
    analysis_architecture_status = build_analysis_architecture_status()
    analysis_architecture_gate_rows = build_analysis_architecture_gate_rows(analysis_architecture_status)
    module_interface_matrix = analysis_architecture_status.get("module_interface_matrix") if isinstance(analysis_architecture_status.get("module_interface_matrix"), dict) else {}
    module_interface_rows = build_module_interface_rows(module_interface_matrix)
    external_tool_adapter_matrix = analysis_architecture_status.get("external_tool_adapter_matrix") if isinstance(analysis_architecture_status.get("external_tool_adapter_matrix"), dict) else {}
    external_tool_adapter_rows = build_external_tool_adapter_rows(external_tool_adapter_matrix)
    task_system_boundary_matrix = analysis_architecture_status.get("task_system_boundary_matrix") if isinstance(analysis_architecture_status.get("task_system_boundary_matrix"), dict) else {}
    task_system_boundary_rows = build_task_system_boundary_rows(task_system_boundary_matrix)
    frontend_consumption_matrix = analysis_architecture_status.get("frontend_consumption_matrix") if isinstance(analysis_architecture_status.get("frontend_consumption_matrix"), dict) else {}
    frontend_consumption_rows = build_frontend_consumption_rows(frontend_consumption_matrix)
    full_activation_module_matrix = analysis_architecture_status.get("full_activation_module_matrix") if isinstance(analysis_architecture_status.get("full_activation_module_matrix"), dict) else {}
    full_activation_module_rows = build_full_activation_module_rows(full_activation_module_matrix)
    standard_worker_migration_matrix = analysis_architecture_status.get("standard_worker_migration_matrix") if isinstance(analysis_architecture_status.get("standard_worker_migration_matrix"), dict) else {}
    standard_worker_migration_rows = build_standard_worker_migration_rows(standard_worker_migration_matrix)
    analysis_architecture_remediation_queue = build_analysis_remediation_queue(analysis_architecture_status)
    analysis_architecture_remediation_rows = build_analysis_architecture_remediation_rows(analysis_architecture_remediation_queue)
    standard_package_catalog = build_standard_analysis_package_catalog(root)
    analysis_environment_validation = validate_analysis_environment_registry()
    analysis_environment_gate_rows = build_analysis_environment_gate_rows(analysis_environment_validation)
    deg_dependency = check_deg_backend_dependencies()
    survival_dependency = check_survival_backend_dependencies()
    enrichment_backend_gate = build_enrichment_backend_gate(root, analysis_type="ora")
    report_gate = evaluate_report_ready_gate(root)
    formal_deg_report_gate = evaluate_formal_deg_report_ready_gate(root)
    packages = [item for item in resolver.get("packages", []) or [] if isinstance(item, dict)]
    tasks = [item for item in center.get("tasks", []) or [] if isinstance(item, dict)]
    deg_gates = build_formal_deg_gate_state(packages=packages, deg_dependency=deg_dependency, project_root=root)
    multifactor_deg_gates = build_multifactor_deg_gate_state(packages=packages, project_root=root)
    survival_gates = build_km_logrank_gate_state(packages=packages, survival_dependency=survival_dependency, project_root=root)
    enrichment_gates = build_enrichment_ui_gate_state(project_root=root, result_entries=result_entries)
    legacy_pipeline = build_legacy_asset_pipeline_state(root)
    package_rows = build_package_rows(packages)
    action_rows = build_action_rows(
        packages=packages,
        tasks=tasks,
        results=result_entries,
        deg_dependency=deg_dependency,
        deg_ready_gate=deg_gates["deg_ready_gate"],
        input_adaptation_gate=deg_gates["input_adaptation_gate"],
        design_quality_gate=deg_gates["design_quality_gate"],
        data_quality_gate=deg_gates["data_quality_gate"],
        method_recommendation_gate=deg_gates["method_recommendation_gate"],
        parameter_gate=deg_gates["parameter_gate"],
        confirmation_gate=deg_gates["confirmation_gate"],
        result_schema_gate=deg_gates["result_schema_gate"],
        multifactor_gate_state=multifactor_deg_gates,
        survival_dependency=survival_dependency,
        km_parameter_gate=survival_gates["parameter_gate"],
        km_confirmation_gate=survival_gates["confirmation_gate"],
        cox_parameter_gate=survival_gates["cox_parameter_gate"],
        cox_confirmation_gate=survival_gates["cox_confirmation_gate"],
        report_gate=report_gate,
        formal_deg_report_gate=formal_deg_report_gate,
        legacy_asset_pipeline=legacy_pipeline,
        enrichment_gate_state=enrichment_gates,
    )
    result_rows = build_result_gate_rows(result_entries, standard_package_catalog=standard_package_catalog)
    gate_rows = build_gate_preview_rows(result_entries=result_entries, report_gate=report_gate, formal_deg_report_gate=formal_deg_report_gate)
    standard_package_gate_rows = build_standard_package_gate_rows(standard_package_catalog)
    dependency_rows = build_dependency_rows(deg_dependency=deg_dependency, survival_dependency=survival_dependency, enrichment_backend_gate=enrichment_backend_gate)
    survival_rows = build_survival_clinical_rows(packages=packages, survival_dependency=survival_dependency, km_gate_state=survival_gates)
    blockers = _dedupe(_list(standard_package_catalog.get("blockers")) + [*resolver.get("blockers", [])] + [item for row in package_rows for item in row["raw_blockers"]] + [row["disabled_reason"] for row in action_rows if not row["enabled"] and row["disabled_reason"]])
    warnings = _dedupe([*resolver.get("warnings", [])] + [item for row in package_rows for item in row["raw_warnings"]] + [item for row in dependency_rows for item in row["raw_warnings"]] + _list(standard_package_catalog.get("warnings")))
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
        "multifactor_deg_gate_rows": multifactor_deg_gates["gate_rows"],
        "legacy_asset_pipeline": legacy_pipeline,
        "result_rows": result_rows,
        "standard_analysis_packages": standard_package_catalog,
        "analysis_architecture_status": analysis_architecture_status,
        "analysis_architecture_gate_rows": analysis_architecture_gate_rows,
        "module_interface_matrix": module_interface_matrix,
        "module_interface_rows": module_interface_rows,
        "external_tool_adapter_matrix": external_tool_adapter_matrix,
        "external_tool_adapter_rows": external_tool_adapter_rows,
        "task_system_boundary_matrix": task_system_boundary_matrix,
        "task_system_boundary_rows": task_system_boundary_rows,
        "frontend_consumption_matrix": frontend_consumption_matrix,
        "frontend_consumption_rows": frontend_consumption_rows,
        "full_activation_module_matrix": full_activation_module_matrix,
        "full_activation_module_rows": full_activation_module_rows,
        "standard_worker_migration_matrix": standard_worker_migration_matrix,
        "standard_worker_migration_rows": standard_worker_migration_rows,
        "analysis_architecture_remediation_queue": analysis_architecture_remediation_queue,
        "analysis_architecture_remediation_rows": analysis_architecture_remediation_rows,
        "standard_package_gate_rows": standard_package_gate_rows,
        "analysis_environment_gate_rows": analysis_environment_gate_rows,
        "gate_rows": gate_rows,
        "survival_clinical_rows": survival_rows,
        "enrichment_gate_rows": enrichment_gates["gate_rows"],
        "top_blockers": blockers[:8],
        "top_warnings": warnings[:8],
        "developer_diagnostics": {
            "analysis_task_center": center,
            "task_records": records,
            "result_index": result_index,
            "analysis_architecture_status": analysis_architecture_status,
            "analysis_architecture_gate_rows": analysis_architecture_gate_rows,
            "module_interface_matrix": module_interface_matrix,
            "module_interface_rows": module_interface_rows,
            "external_tool_adapter_matrix": external_tool_adapter_matrix,
            "external_tool_adapter_rows": external_tool_adapter_rows,
            "task_system_boundary_matrix": task_system_boundary_matrix,
            "task_system_boundary_rows": task_system_boundary_rows,
            "frontend_consumption_matrix": frontend_consumption_matrix,
            "frontend_consumption_rows": frontend_consumption_rows,
            "full_activation_module_matrix": full_activation_module_matrix,
            "full_activation_module_rows": full_activation_module_rows,
            "standard_worker_migration_matrix": standard_worker_migration_matrix,
            "standard_worker_migration_rows": standard_worker_migration_rows,
            "analysis_architecture_remediation_queue": analysis_architecture_remediation_queue,
            "analysis_architecture_remediation_rows": analysis_architecture_remediation_rows,
            "standard_analysis_package_catalog": standard_package_catalog,
            "standard_package_gate_rows": standard_package_gate_rows,
            "analysis_environment_registry_validation": analysis_environment_validation,
            "analysis_environment_gate_rows": analysis_environment_gate_rows,
            "analysis_input_resolver": resolver,
            "deg_dependency_snapshot": deg_dependency,
            "formal_deg_gate_state": deg_gates,
            "multifactor_deg_gate_state": multifactor_deg_gates,
            "legacy_asset_pipeline": legacy_pipeline,
            "survival_dependency_snapshot": survival_dependency,
            "enrichment_backend_gate": enrichment_backend_gate,
            "enrichment_gate_state": enrichment_gates,
            "report_ready_gate": report_gate,
            "formal_deg_report_ready_gate": formal_deg_report_gate,
            "km_logrank_gate_state": survival_gates,
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


def build_dependency_rows(
    *,
    deg_dependency: dict[str, Any] | None = None,
    survival_dependency: dict[str, Any] | None = None,
    enrichment_backend_gate: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    deg_dependency = deg_dependency or check_deg_backend_dependencies()
    survival_dependency = survival_dependency or check_survival_backend_dependencies()
    enrichment_backend_gate = enrichment_backend_gate or build_enrichment_backend_gate(analysis_type="ora")
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
    rows.extend(_enrichment_dependency_rows(enrichment_backend_gate))
    return rows


def _enrichment_dependency_rows(gate: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rscript = gate.get("rscript") if isinstance(gate.get("rscript"), dict) else {}
    gate_blockers = _list(gate.get("blockers"))
    gate_warnings = _list(gate.get("warnings"))
    rows.append(
        {
            "dependency_id": "external_r_enrichment:Rscript",
            "label": "Rscript enrichment backend",
            "status": "passed" if rscript.get("available") and not gate_blockers else ("available_with_blocked_capabilities" if rscript.get("available") else "blocked"),
            "version": str(rscript.get("version") or "not_detected"),
            "blockers": compact_list(gate_blockers),
            "warnings": compact_list(gate_warnings),
            "action": "Detect only; no install action.",
            "packaging_impact": str(gate.get("packaging_policy") or "external_runtime_not_bundled"),
            "raw_blockers": gate_blockers,
            "raw_warnings": gate_warnings,
        }
    )
    packages = gate.get("packages") if isinstance(gate.get("packages"), dict) else {}
    if not packages:
        return rows
    package_names = (
        "clusterProfiler",
        "fgsea",
        "DOSE",
        "enrichplot",
        "ggplot2",
        "AnnotationDbi",
        "org.Hs.eg.db",
        "KEGGREST",
        "GO.db",
        "ReactomePA",
        "msigdbr",
    )
    for name in package_names:
        status = packages.get(name) if isinstance(packages.get(name), dict) else {}
        available = bool(status.get("available") and status.get("importable"))
        blocker = "" if available else f"missing_required_r_package:{name}"
        rows.append(
            {
                "dependency_id": f"external_r_enrichment:{name}",
                "label": name,
                "status": "available" if available else "blocked",
                "version": str(status.get("version") or "not_detected"),
                "blockers": blocker or "None",
                "warnings": "Reactome/MSigDB blockers do not stop selected core ORA/GSEA capabilities." if name in {"ReactomePA", "msigdbr"} and not available else "None",
                "action": "Detect only; no install action.",
                "packaging_impact": str(gate.get("packaging_policy") or "external_runtime_not_bundled"),
                "raw_blockers": [blocker] if blocker else [],
                "raw_warnings": [f"enrichment_r_package_missing:{name}"] if blocker else [],
            }
        )
    return rows


def build_formal_deg_gate_state(*, packages: list[dict[str, Any]], deg_dependency: dict[str, Any], project_root: str | Path | None = None) -> dict[str, Any]:
    deg_package = next((item for item in packages if item.get("package_type") == "deg_recompute"), None)
    confirmation = load_deg_parameter_confirmation(project_root) if project_root is not None else {}
    confirmed_parameters = confirmation.get("parameter_manifest") if isinstance(confirmation.get("parameter_manifest"), dict) else {}
    if not deg_package:
        deg_ready_gate = {"status": "blocked", "blockers": ["missing_deg_recompute_input_package"], "warnings": []}
        input_adaptation_gate = build_deg_input_adaptation_gate(None, None)
        design_quality_gate = build_deg_design_quality_gate(None)
        data_quality_gate = build_deg_data_quality_gate(None)
        method_recommendation_gate = build_deg_method_recommendation_gate(input_adaptation_gate=input_adaptation_gate, design_quality_gate=design_quality_gate, data_quality_gate=data_quality_gate, dependency_snapshot=deg_dependency)
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
        input_adaptation_gate = build_deg_input_adaptation_gate(deg_package, deg_ready)
        design_quality_gate = build_deg_design_quality_gate(deg_ready, method_family=str(confirmed_parameters.get("method_family") or ""))
        data_quality_gate = build_deg_data_quality_gate(deg_ready)
        method_recommendation_gate = build_deg_method_recommendation_gate(input_adaptation_gate=input_adaptation_gate, design_quality_gate=design_quality_gate, data_quality_gate=data_quality_gate, dependency_snapshot=deg_dependency)
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
        _formal_deg_gate_row(
            "DEG real-project input adaptation",
            input_adaptation_gate.get("status"),
            input_adaptation_gate.get("blockers", []),
            input_adaptation_gate.get("warnings", []),
            basis=f"value_type={input_adaptation_gate.get('value_type', '')}; gene_id_type={input_adaptation_gate.get('gene_id_type', '')}; methods={compact_list(input_adaptation_gate.get('allowed_methods', []) or [])}",
        ),
        _formal_deg_gate_row(
            "DEG batch/design QA",
            design_quality_gate.get("status"),
            design_quality_gate.get("blockers", []),
            design_quality_gate.get("warnings", []),
            basis=f"df={design_quality_gate.get('degrees_of_freedom', 0)}; covariates={compact_list(design_quality_gate.get('covariate_names', []) or [])}; batches={compact_list(design_quality_gate.get('batch_names', []) or [])}",
        ),
        _formal_deg_gate_row(
            "DEG data quality / repair guidance",
            data_quality_gate.get("status"),
            data_quality_gate.get("blockers", []),
            data_quality_gate.get("warnings", []),
            basis=f"features={data_quality_gate.get('feature_count', 0)}; samples={data_quality_gate.get('sample_count', 0)}; auto_repaired={data_quality_gate.get('auto_repaired', False)}",
        ),
        _formal_deg_gate_row(
            "DEG method recommendation",
            method_recommendation_gate.get("status"),
            method_recommendation_gate.get("blockers", []),
            method_recommendation_gate.get("warnings", []),
            basis=compact_list([f"{item.get('method')}={item.get('state')}" for item in method_recommendation_gate.get("methods", []) or [] if isinstance(item, dict)]),
        ),
        _formal_deg_gate_row("DEG-ready matrix", deg_ready_gate.get("status"), deg_ready_gate.get("blockers", []), deg_ready_gate.get("warnings", [])),
        _formal_deg_gate_row("Dependency policy", deg_dependency.get("status"), deg_dependency.get("blockers", []), deg_dependency.get("warnings", []), basis=str(deg_dependency.get("dependency_policy") or "")),
        _formal_deg_gate_row("Parameter manifest", parameter_gate.get("status"), parameter_gate.get("blockers", []), parameter_gate.get("warnings", [])),
        _formal_deg_gate_row("User parameter confirmation", confirmation_gate.get("status"), confirmation_gate.get("blockers", []), confirmation_gate.get("warnings", []), basis="User must confirm comparison, method, thresholds, value type, dependency versions and output plan."),
        _formal_deg_gate_row("Result schema gate", result_schema_gate.get("status"), result_schema_gate.get("blockers", []), result_schema_gate.get("warnings", [])),
        _formal_deg_gate_row("B9.2 controlled activation", "passed", [], [], basis="Enabled only for audited two-group controlled DEG MVP."),
    ]
    return {
        "deg_ready_gate": deg_ready_gate,
        "input_adaptation_gate": input_adaptation_gate,
        "design_quality_gate": design_quality_gate,
        "data_quality_gate": data_quality_gate,
        "method_recommendation_gate": method_recommendation_gate,
        "parameter_gate": parameter_gate,
        "confirmation_gate": confirmation_gate,
        "parameter_confirmation": confirmation,
        "result_schema_gate": result_schema_gate,
        "gate_rows": gate_rows,
    }


def build_multifactor_deg_gate_state(*, packages: list[dict[str, Any]], project_root: str | Path | None = None) -> dict[str, Any]:
    deg_package = next((item for item in packages if item.get("package_type") == "deg_recompute"), None)
    confirmation = load_multifactor_deg_parameter_confirmation(project_root) if project_root is not None else {}
    confirmed_parameters = confirmation.get("parameter_manifest") if isinstance(confirmation.get("parameter_manifest"), dict) else {}
    method = str(confirmed_parameters.get("backend_method") or "limma")
    dependency = check_multifactor_r_backend(method)
    if not deg_package:
        deg_ready_gate = {"status": "blocked", "blockers": ["missing_deg_recompute_input_package"], "warnings": []}
        design_quality_gate = build_deg_design_quality_gate(None)
        design_manifest = _multifactor_design_manifest(confirmed_parameters, design_quality_gate)
        parameter_gate = {"status": "blocked", "blockers": ["missing_deg_ready_package"], "warnings": [], **design_manifest, "backend_method": method}
    else:
        deg_ready = build_deg_ready_package(deg_package).to_dict()
        deg_ready_gate = {
            "status": "passed" if not deg_ready.get("blockers") else "blocked",
            "blockers": list(deg_ready.get("blockers", []) or []),
            "warnings": list(deg_ready.get("warnings", []) or []),
            "package": deg_ready,
        }
        design_quality_gate = build_deg_design_quality_gate(deg_ready, method_family="linear_model_multifactor")
        design_manifest = _multifactor_design_manifest(confirmed_parameters, design_quality_gate)
        parameter_gate = build_multifactor_deg_parameter_manifest(deg_ready, design_manifest=design_manifest, method=method, dependency_snapshot=dependency)
    confirmation_gate = validate_multifactor_deg_parameter_confirmation(confirmation, parameter_manifest=parameter_gate, dependency_snapshot=dependency)
    result_schema_gate = build_multifactor_deg_result_schema_gate(parameter_manifest=parameter_gate, dependency_snapshot=dependency)
    blockers = _dedupe(
        [
            *[str(item) for item in deg_ready_gate.get("blockers", []) or []],
            *[str(item) for item in design_quality_gate.get("blockers", []) or []],
            *[str(item) for item in parameter_gate.get("blockers", []) or []],
            *[str(item) for item in dependency.get("blockers", []) or []],
            *[str(item) for item in confirmation_gate.get("blockers", []) or []],
            *[str(item) for item in result_schema_gate.get("blockers", []) or []],
        ]
    )
    gate_rows = [
        _formal_deg_gate_row("Multi-factor resolver package", deg_ready_gate.get("status"), deg_ready_gate.get("blockers", []), deg_ready_gate.get("warnings", [])),
        _formal_deg_gate_row(
            "Multi-factor design QA",
            design_quality_gate.get("status"),
            design_quality_gate.get("blockers", []),
            design_quality_gate.get("warnings", []),
            basis=f"formula={design_manifest.get('design_formula', '')}; rank={design_manifest.get('design_rank', 0)}; df={design_manifest.get('residual_degrees_of_freedom', 0)}; batches={compact_list(design_manifest.get('batch_variables', []) or [])}",
        ),
        _formal_deg_gate_row("Multi-factor contrast", "passed" if design_manifest.get("contrast", {}).get("contrast_id") else "blocked", [] if design_manifest.get("contrast", {}).get("contrast_id") else ["missing_contrast_id"], basis=str(design_manifest.get("contrast", {}))),
        _formal_deg_gate_row("Multi-factor method", parameter_gate.get("status"), parameter_gate.get("blockers", []), parameter_gate.get("warnings", []), basis=f"method={method}; value_type_policy={parameter_gate.get('value_type_policy', '')}"),
        _formal_deg_gate_row("Multi-factor R dependency", dependency.get("status"), dependency.get("blockers", []), dependency.get("warnings", []), basis=f"method={method}; policy={dependency.get('dependency_policy', '')}"),
        _formal_deg_gate_row("Multi-factor user confirmation", confirmation_gate.get("status"), confirmation_gate.get("blockers", []), confirmation_gate.get("warnings", []), basis="User must confirm formula, contrast, covariates, batch, method, value type, dependencies and output path."),
        _formal_deg_gate_row("Multi-factor result schema", result_schema_gate.get("status"), result_schema_gate.get("blockers", []), result_schema_gate.get("warnings", [])),
    ]
    return {
        "schema_version": "biomedpilot.multifactor_deg_ui_gate_state.v1",
        "status": "blocked" if blockers else "passed",
        "method": method,
        "deg_ready_gate": deg_ready_gate,
        "design_quality_gate": design_quality_gate,
        "parameter_gate": parameter_gate,
        "dependency_snapshot": dependency,
        "confirmation_gate": confirmation_gate,
        "parameter_confirmation": confirmation,
        "result_schema_gate": result_schema_gate,
        "gate_rows": gate_rows,
        "blockers": blockers,
        "warnings": _dedupe(
            [
                *[str(item) for item in deg_ready_gate.get("warnings", []) or []],
                *[str(item) for item in design_quality_gate.get("warnings", []) or []],
                *[str(item) for item in parameter_gate.get("warnings", []) or []],
                *[str(item) for item in dependency.get("warnings", []) or []],
                *[str(item) for item in confirmation_gate.get("warnings", []) or []],
                *[str(item) for item in result_schema_gate.get("warnings", []) or []],
            ]
        ),
    }


def _multifactor_design_manifest(confirmed_parameters: dict[str, Any], design_quality_gate: dict[str, Any]) -> dict[str, Any]:
    contrast = confirmed_parameters.get("contrast") if isinstance(confirmed_parameters.get("contrast"), dict) else {}
    covariates = confirmed_parameters.get("covariates") if isinstance(confirmed_parameters.get("covariates"), list) else []
    batch_variables = confirmed_parameters.get("batch_variables") if isinstance(confirmed_parameters.get("batch_variables"), list) else list(design_quality_gate.get("batch_names", []) or [])
    return {
        "design_formula": str(confirmed_parameters.get("design_formula") or ""),
        "contrast": contrast,
        "covariates": covariates,
        "batch_variables": batch_variables,
        "design_rank": int(confirmed_parameters.get("design_rank") or design_quality_gate.get("design_rank") or 0),
        "residual_degrees_of_freedom": int(confirmed_parameters.get("residual_degrees_of_freedom") or design_quality_gate.get("degrees_of_freedom") or 0),
        "contrast_estimability": str(confirmed_parameters.get("contrast_estimability") or "not_confirmed"),
    }


def build_km_logrank_gate_state(*, packages: list[dict[str, Any]], survival_dependency: dict[str, Any], project_root: str | Path | None = None) -> dict[str, Any]:
    package = next((item for item in packages if item.get("package_type") == "tcga_clinical_survival_preflight"), None)
    if not package:
        parameter_gate = {"status": "blocked", "blockers": ["missing_survival_preflight_package"], "warnings": []}
        confirmation_gate = validate_km_logrank_confirmation({}, parameter_gate)
        cox_parameter_gate = {"status": "blocked", "blockers": ["missing_survival_preflight_package"], "warnings": []}
        cox_confirmation_gate = validate_cox_univariate_confirmation({}, cox_parameter_gate)
        return {"survival_package": {}, "outcome_gate": {}, "clinical_variable_audit": {}, "parameter_gate": parameter_gate, "confirmation_gate": confirmation_gate, "cox_parameter_gate": cox_parameter_gate, "cox_confirmation_gate": cox_confirmation_gate, "cox_multivariate_design": {}}
    survival_package = build_survival_package(package)
    outcome_gate = build_survival_preflight(survival_package)
    clinical_rows = read_table(asset_path(package.get("clinical_asset") if isinstance(package.get("clinical_asset"), dict) else None))
    audit = build_clinical_association_preflight(clinical_rows)
    grouping_variable, group_a, group_b = _default_km_grouping(clinical_rows, survival_package.to_dict())
    parameter_gate = build_km_logrank_parameter_manifest(
        survival_package,
        outcome_gate=outcome_gate,
        clinical_variable_audit=audit,
        grouping_variable=grouping_variable,
        group_a=group_a,
        group_b=group_b,
        dependency_snapshot=survival_dependency,
    )
    confirmation = load_km_logrank_confirmation(project_root) if project_root is not None else {}
    confirmation_gate = validate_km_logrank_confirmation(confirmation, parameter_gate)
    covariate = _default_cox_covariate(clinical_rows, survival_package.to_dict(), audit)
    cox_parameter_gate = build_cox_univariate_parameter_manifest(
        survival_package,
        outcome_gate=outcome_gate,
        clinical_variable_audit=audit,
        covariate=covariate,
        dependency_snapshot=survival_dependency,
    )
    cox_confirmation = load_cox_univariate_confirmation(project_root) if project_root is not None else {}
    cox_confirmation_gate = validate_cox_univariate_confirmation(cox_confirmation, cox_parameter_gate)
    cox_multivariate_design = audit_cox_multivariate_design(survival_package, audit)
    gate_rows = [
        _formal_deg_gate_row("B12 survival input", "passed" if not survival_package.blockers else "blocked", list(survival_package.blockers), list(survival_package.warnings)),
        _formal_deg_gate_row("B12 outcome gate", outcome_gate.get("status"), outcome_gate.get("blockers", []), outcome_gate.get("warnings", [])),
        _formal_deg_gate_row("B13 KM/log-rank parameters", parameter_gate.get("status"), parameter_gate.get("blockers", []), parameter_gate.get("warnings", [])),
        _formal_deg_gate_row("B13 user confirmation", confirmation_gate.get("status"), confirmation_gate.get("blockers", []), confirmation_gate.get("warnings", [])),
        _formal_deg_gate_row("B14 Cox univariate parameters", cox_parameter_gate.get("status"), cox_parameter_gate.get("blockers", []), cox_parameter_gate.get("warnings", [])),
        _formal_deg_gate_row("B14 Cox user confirmation", cox_confirmation_gate.get("status"), cox_confirmation_gate.get("blockers", []), cox_confirmation_gate.get("warnings", [])),
        _formal_deg_gate_row("B14 Cox multivariate design audit", "blocked" if cox_multivariate_design.get("blockers") else "design_only", cox_multivariate_design.get("blockers", []), cox_multivariate_design.get("warnings", []), basis="design audit only; no multivariate execution"),
        _formal_deg_gate_row("Survival dependency", survival_dependency.get("status"), survival_dependency.get("blockers", []), survival_dependency.get("warnings", []), basis="lifelines detect-first; no install action"),
    ]
    return {
        "survival_package": survival_package.to_dict(),
        "outcome_gate": outcome_gate,
        "clinical_variable_audit": audit,
        "parameter_gate": parameter_gate,
        "confirmation_gate": confirmation_gate,
        "parameter_confirmation": confirmation,
        "cox_parameter_gate": cox_parameter_gate,
        "cox_confirmation_gate": cox_confirmation_gate,
        "cox_parameter_confirmation": cox_confirmation,
        "cox_multivariate_design": cox_multivariate_design,
        "gate_rows": gate_rows,
    }


def build_enrichment_ui_gate_state(*, project_root: str | Path, result_entries: list[dict[str, Any]]) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    source = _select_formal_deg_source_for_enrichment(result_entries)
    source_result_id = str(source.get("result_id") or "") if source else ""
    source_semantics = str(source.get("result_semantics") or "") if source else ""
    registry_exists = (root / GENE_SET_REGISTRY).is_file()
    if registry_exists:
        ora_gate = build_enrichment_execution_gate(root, analysis_type="ora", source_result_id=source_result_id, source_result_semantics=source_semantics)
        gsea_gate = build_enrichment_execution_gate(root, analysis_type="gsea_preranked", source_result_id=source_result_id, source_result_semantics=source_semantics)
    else:
        source_blockers = [] if source_result_id else ["enrichment_source_result_id_missing"]
        ora_gate = _blocked_enrichment_execution_gate("ora", source_result_id, [*source_blockers, "enrichment_resource_not_selected"])
        gsea_gate = _blocked_enrichment_execution_gate("gsea_preranked", source_result_id, [*source_blockers, "enrichment_resource_not_selected"])
    review = build_enrichment_result_review(root)
    selected_enrichment_id = str(review.get("selected_result_id") or "")
    selected_task_type = str(review.get("task_type") or "")
    plot_type = "gsea_preranked_plot" if selected_task_type == "gsea_preranked" else "ora_dotplot"
    plot_gate = build_enrichment_plot_gate(root, result_id=selected_enrichment_id or None, plot_type=plot_type)
    section_report_gate = evaluate_enrichment_section_report_ready_gate(root, result_id=selected_enrichment_id or None, allow_table_only_report=False)
    preview_analysis_type = selected_task_type if selected_task_type in {"ora", "gsea_preranked"} else "ora"
    preview_execution_gate = ora_gate if preview_analysis_type == "ora" else gsea_gate
    preview_manifest = preview_execution_gate.get("parameter_manifest") if isinstance(preview_execution_gate.get("parameter_manifest"), dict) else {}
    preview_resource_id = str(preview_manifest.get("resource_id") or "")
    if registry_exists:
        resource_lock = build_enrichment_resource_lock(root, analysis_type=preview_analysis_type, resource_id=preview_resource_id)
        library_policy = build_enrichment_library_policy(root, analysis_type=preview_analysis_type, resource_id=preview_resource_id)
        input_contract_gate = build_enrichment_input_contract_gate(root, analysis_type=preview_analysis_type, source_result_id=source_result_id, resource_id=preview_resource_id)
    else:
        resource_lock = _blocked_enrichment_resource_lock_preview(preview_analysis_type, preview_resource_id)
        library_policy = _blocked_enrichment_library_policy_preview(preview_analysis_type, preview_resource_id)
        input_contract_gate = _blocked_enrichment_input_contract_preview(preview_analysis_type, source_result_id, preview_resource_id)
    background_universe = input_contract_gate.get("background_universe") if isinstance(input_contract_gate.get("background_universe"), dict) else {}
    identifier_gate = input_contract_gate.get("identifier_compatibility_gate") if isinstance(input_contract_gate.get("identifier_compatibility_gate"), dict) else {}
    statistical_policy = build_enrichment_statistical_policy(analysis_type=preview_analysis_type)
    result_schema_gate = (
        validate_enrichment_result_schema_gate(root, result_id=selected_enrichment_id)
        if selected_enrichment_id
        else _blocked_enrichment_preview_gate("result_schema", ["formal_enrichment_result_not_found"])
    )
    production_audit_preview = _enrichment_production_audit_preview(result_schema_gate)
    cross_library_acceptance = build_enrichment_cross_library_acceptance_gate(root)
    gate_rows = [
        _formal_deg_gate_row("Enrichment DEG source", "passed" if source_result_id else "blocked", [] if source_result_id else ["formal_deg_source_result_missing"], basis=f"source_result_id={source_result_id or 'missing'}"),
        _formal_deg_gate_row("Enrichment resource lock", resource_lock.get("status"), resource_lock.get("blockers", []), resource_lock.get("warnings", []), basis=f"analysis_type={preview_analysis_type}; resource={resource_lock.get('resource_id') or 'missing'}; library={resource_lock.get('collection_type') or 'missing'}"),
        _formal_deg_gate_row("Enrichment library capability", library_policy.get("status"), library_policy.get("blockers", []), library_policy.get("warnings", []), basis=f"collection={library_policy.get('selected_collection_type') or 'missing'}; policy=no_download_no_install"),
        _formal_deg_gate_row("Enrichment background universe", background_universe.get("status"), background_universe.get("blockers", []), background_universe.get("warnings", []), basis=f"strategy={background_universe.get('background_strategy') or 'missing'}; genes={background_universe.get('gene_count', 0)}"),
        _formal_deg_gate_row("Enrichment identifier compatibility", identifier_gate.get("status"), identifier_gate.get("blockers", []), identifier_gate.get("warnings", []), basis=f"source_gene_id_type={identifier_gate.get('source_gene_id_type') or 'missing'}; resource_gene_id_type={identifier_gate.get('resource_gene_id_type') or 'missing'}"),
        _formal_deg_gate_row("Enrichment statistical policy", statistical_policy.get("status"), statistical_policy.get("blockers", []), statistical_policy.get("warnings", []), basis=f"method={statistical_policy.get('p_adjust_method')}; boundary=statistical_research_only"),
        _formal_deg_gate_row("ORA execution gate", ora_gate.get("status"), ora_gate.get("blockers", []), ora_gate.get("warnings", []), basis=_enrichment_gate_basis(ora_gate)),
        _formal_deg_gate_row("Preranked GSEA execution gate", gsea_gate.get("status"), gsea_gate.get("blockers", []), gsea_gate.get("warnings", []), basis=_enrichment_gate_basis(gsea_gate)),
        _formal_deg_gate_row("Enrichment result review", review.get("status"), review.get("blockers", []), review.get("warnings", []), basis=f"selected_result_id={selected_enrichment_id or 'missing'}"),
        _formal_deg_gate_row("Enrichment result schema", result_schema_gate.get("status"), result_schema_gate.get("blockers", []), result_schema_gate.get("warnings", []), basis=f"selected_result_id={selected_enrichment_id or 'missing'}"),
        _formal_deg_gate_row("Enrichment plot artifact", plot_gate.get("status"), plot_gate.get("blockers", []), plot_gate.get("warnings", []), basis=f"plot_type={plot_type}"),
        _formal_deg_gate_row("Enrichment section report", section_report_gate.get("status"), section_report_gate.get("blockers", []), section_report_gate.get("warnings", []), basis="section_scope=formal_enrichment_only"),
        _formal_deg_gate_row("Enrichment production audit package", production_audit_preview.get("status"), production_audit_preview.get("blockers", []), production_audit_preview.get("warnings", []), basis="preview_only_no_package_write"),
        _formal_deg_gate_row("Enrichment cross-library acceptance", cross_library_acceptance.get("status"), cross_library_acceptance.get("blockers", []), cross_library_acceptance.get("warnings", []), basis=f"scenarios={cross_library_acceptance.get('passed_scenario_count', 0)}/{cross_library_acceptance.get('scenario_count', 0)}"),
    ]
    blockers = _dedupe(
        [
            *[str(item) for item in resource_lock.get("blockers", []) or []],
            *[str(item) for item in library_policy.get("blockers", []) or []],
            *[str(item) for item in input_contract_gate.get("blockers", []) or []],
            *[str(item) for item in statistical_policy.get("blockers", []) or []],
            *[str(item) for item in ora_gate.get("blockers", []) or []],
            *[str(item) for item in gsea_gate.get("blockers", []) or []],
            *[str(item) for item in review.get("blockers", []) or []],
            *[str(item) for item in result_schema_gate.get("blockers", []) or []],
            *[str(item) for item in plot_gate.get("blockers", []) or []],
            *[str(item) for item in section_report_gate.get("blockers", []) or []],
            *[str(item) for item in production_audit_preview.get("blockers", []) or []],
            *[str(item) for item in cross_library_acceptance.get("blockers", []) or []],
        ]
    )
    warnings = _dedupe(
        [
            *[str(item) for item in resource_lock.get("warnings", []) or []],
            *[str(item) for item in library_policy.get("warnings", []) or []],
            *[str(item) for item in input_contract_gate.get("warnings", []) or []],
            *[str(item) for item in statistical_policy.get("warnings", []) or []],
            *[str(item) for item in ora_gate.get("warnings", []) or []],
            *[str(item) for item in gsea_gate.get("warnings", []) or []],
            *[str(item) for item in review.get("warnings", []) or []],
            *[str(item) for item in result_schema_gate.get("warnings", []) or []],
            *[str(item) for item in plot_gate.get("warnings", []) or []],
            *[str(item) for item in section_report_gate.get("warnings", []) or []],
            *[str(item) for item in production_audit_preview.get("warnings", []) or []],
            *[str(item) for item in cross_library_acceptance.get("warnings", []) or []],
        ]
    )
    return {
        "schema_version": "biomedpilot.enrichment_analysis_ui_gate_state.v1",
        "status": "blocked" if blockers else "passed",
        "source_result_id": source_result_id,
        "production_preview_status": "blocked" if blockers else "passed",
        "resource_lock": resource_lock,
        "library_policy": library_policy,
        "input_contract_gate": input_contract_gate,
        "statistical_policy": statistical_policy,
        "execution_gates": {"ora": ora_gate, "gsea_preranked": gsea_gate},
        "review": review,
        "result_schema_gate": result_schema_gate,
        "plot_gate": plot_gate,
        "section_report_gate": section_report_gate,
        "production_audit_preview": production_audit_preview,
        "cross_library_acceptance": cross_library_acceptance,
        "gate_rows": gate_rows,
        "reactomepa_msigdbr_policy": "blocked_capability_until_external_backend_and_resource_gates_pass",
        "formal_ui_activation_boundary": "B98 previews B93-B97 production gates only; handlers must still call audited gates before writing artifacts.",
        "blockers": blockers,
        "warnings": warnings,
    }


def _select_formal_deg_source_for_enrichment(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [
        entry
        for entry in entries
        if normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"), default="") == "formal_computed_result"
        and str(entry.get("task_type") or "").lower() == "deg"
    ]
    return candidates[-1] if candidates else None


def _enrichment_gate_basis(gate: dict[str, Any]) -> str:
    manifest = gate.get("parameter_manifest") if isinstance(gate.get("parameter_manifest"), dict) else {}
    return f"source={manifest.get('source_result_id', '') or 'missing'}; resource={manifest.get('resource_id', '') or 'missing'}; capability={manifest.get('required_backend_capability', '') or 'missing'}"


def _blocked_enrichment_execution_gate(analysis_type: str, source_result_id: str, blockers: list[str]) -> dict[str, Any]:
    capability = "ora_enricher" if analysis_type == "ora" else "gsea_preranked_fgsea"
    manifest = {
        "schema_version": "biomedpilot.enrichment_parameter_manifest.v2",
        "status": "blocked",
        "analysis_type": analysis_type,
        "source_result_id": source_result_id,
        "resource_id": "",
        "required_backend_capability": capability,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": [],
    }
    return {
        "schema_version": "biomedpilot.enrichment_execution_gate.v1",
        "status": "blocked",
        "analysis_type": analysis_type,
        "parameter_manifest": manifest,
        "confirmation_gate": {"status": "blocked", "blockers": ["enrichment_parameter_confirmation_missing"], "warnings": []},
        "can_execute_controlled_r_adapter": False,
        "formal_ui_button_enabled": False,
        "disabled_reason": "; ".join(dict.fromkeys(blockers)),
        "boundary": "read_only_ui_state_no_gene_set_registry",
        "blockers": list(dict.fromkeys([*blockers, "enrichment_parameter_confirmation_missing"])),
        "warnings": [],
    }


def _blocked_enrichment_preview_gate(gate_name: str, blockers: list[str]) -> dict[str, Any]:
    return {
        "schema_version": f"biomedpilot.enrichment_{gate_name}_preview.v1",
        "status": "blocked",
        "semantic_boundary": "ui_preview_only_no_artifact_write",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": [],
    }


def _blocked_enrichment_resource_lock_preview(analysis_type: str, resource_id: str) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.enrichment_resource_lock.v1",
        "status": "blocked",
        "analysis_type": analysis_type,
        "resource_id": resource_id,
        "collection_type": "",
        "semantic_boundary": "resource_lock_only_not_enrichment_execution",
        "network_downloads": False,
        "auto_install": False,
        "blockers": ["enrichment_resource_registry_missing", "enrichment_resource_not_selected"],
        "warnings": [],
    }


def _blocked_enrichment_library_policy_preview(analysis_type: str, resource_id: str) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.enrichment_library_policy.v1",
        "status": "blocked",
        "analysis_type": analysis_type,
        "selected_resource_id": resource_id,
        "selected_collection_type": "",
        "policy_boundary": "library_policy_only_no_download_no_execution",
        "network_downloads": False,
        "auto_install": False,
        "blockers": ["enrichment_resource_registry_missing"],
        "warnings": [],
    }


def _blocked_enrichment_input_contract_preview(analysis_type: str, source_result_id: str, resource_id: str) -> dict[str, Any]:
    background = _blocked_enrichment_preview_gate("background_universe", ["background_universe_empty"])
    background.update({"source_result_id": source_result_id, "background_strategy": "formal_deg_result_table_all_features", "gene_count": 0})
    compatibility = _blocked_enrichment_preview_gate("identifier_compatibility", ["resource_gene_id_type_unknown"])
    compatibility.update({"source_gene_id_type": "unknown", "resource_gene_id_type": "unknown", "required_gene_id_type": "symbol"})
    return {
        "schema_version": "biomedpilot.enrichment_input_contract_gate.v1",
        "status": "blocked",
        "analysis_type": analysis_type,
        "source_result_id": source_result_id,
        "resource_id": resource_id,
        "background_universe": background,
        "identifier_compatibility_gate": compatibility,
        "semantic_boundary": "input_contract_only_not_enrichment_execution",
        "blockers": ["enrichment_resource_registry_missing", "enrichment_resource_not_selected", *_list(background.get("blockers")), *_list(compatibility.get("blockers"))],
        "warnings": [],
    }


def _enrichment_production_audit_preview(result_schema_gate: dict[str, Any]) -> dict[str, Any]:
    blockers = _list(result_schema_gate.get("blockers"))
    if result_schema_gate.get("status") != "passed":
        blockers = blockers or ["enrichment_result_schema_gate_not_passed"]
    return {
        "schema_version": "biomedpilot.enrichment_production_audit_preview.v1",
        "status": "blocked" if blockers else "passed",
        "semantic_boundary": "preview_only_no_package_write_no_report_ready_upgrade",
        "required_gate": "B96 create_enrichment_production_audit_package requires B95 result schema gate to pass before writing.",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": _list(result_schema_gate.get("warnings")),
    }


def _formal_deg_gate_row(gate: str, status: object, blockers: object, warnings: object = (), *, basis: str = "") -> dict[str, Any]:
    return {
        "gate": gate,
        "status": str(status or "blocked"),
        "basis": basis,
        "blockers": compact_list(blockers if isinstance(blockers, list | tuple) else []),
        "warnings": compact_list(warnings if isinstance(warnings, list | tuple) else []),
    }


def build_result_gate_rows(entries: list[dict[str, Any]], *, standard_package_catalog: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    standard_package_rows = _standard_package_rows_by_result_id(standard_package_catalog or {})
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
                "standard_package_status": "missing",
                "standard_package_validation_status": "not_applicable",
                "standard_package_path": "",
                "standard_package_artifacts": "None",
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
        result_id = str(entry.get("result_id") or entry.get("result_name") or "")
        standard_package = standard_package_rows.get(result_id, {})
        artifact_counts = standard_package.get("artifact_counts") if isinstance(standard_package.get("artifact_counts"), dict) else {}
        rows.append(
            {
                "result_id": result_id,
                "semantics": label_semantics(semantics),
                "input_package_id": str(entry.get("input_package_id") or ""),
                "engine": _engine_text(entry),
                "dependency_snapshot": "present" if entry.get("dependency_snapshot") else "missing",
                "validation_status": str(entry.get("validation_status") or "not_validated"),
                "plot_status": plot_status,
                "report_status": report_status,
                "standard_package_status": "registered" if standard_package else "missing_standard_result_package",
                "standard_package_validation_status": str(standard_package.get("validation_status") or "missing"),
                "standard_package_path": str(standard_package.get("package_path_relative") or ""),
                "standard_package_artifacts": _standard_package_artifact_count_text(artifact_counts),
                "blockers": compact_list(blockers),
                "warnings": compact_list(warnings),
            }
        )
    return rows


def _standard_package_rows_by_result_id(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = catalog.get("rows")
    if not isinstance(rows, list | tuple):
        return {}
    return {str(row.get("result_id") or ""): row for row in rows if isinstance(row, dict) and row.get("result_id")}


def _standard_package_artifact_count_text(counts: dict[str, Any]) -> str:
    if not counts:
        return "None"
    return "; ".join(f"{key}={counts.get(key, 0)}" for key in ("tables", "plots", "reports", "logs"))


def build_standard_package_gate_rows(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [row for row in catalog.get("rows", []) if isinstance(row, dict)] if isinstance(catalog.get("rows"), list | tuple) else []
    blockers = _list(catalog.get("blockers"))
    warnings = _list(catalog.get("warnings"))
    invalid_packages = [
        str(row.get("result_id") or row.get("package_path_relative") or "")
        for row in rows
        if isinstance(row, dict) and str(row.get("validation_status") or "") != "passed"
    ]
    artifact_blockers = [
        item
        for item in blockers
        if any(marker in item for marker in ("declared_artifact", "artifact_manifest", "standard_result_package"))
    ]
    input_manifest_blockers = [
        item
        for item in blockers
        if any(marker in item for marker in ("input_manifest", "module_input_manifest"))
    ]
    input_manifest_statuses = [
        f"{row.get('result_id') or row.get('package_path_relative') or 'package'}={row.get('input_manifest_validation_status') or 'missing'}"
        for row in rows
        if isinstance(row, dict)
    ]
    return [
        _formal_deg_gate_row(
            "Standard package catalog source",
            "passed",
            [],
            [],
            basis=f"policy={catalog.get('source_policy') or 'unknown'}; packages={catalog.get('package_count', len(rows))}",
        ),
        _formal_deg_gate_row(
            "Standard package validation",
            catalog.get("status") or "passed",
            blockers,
            warnings,
            basis=f"invalid_packages={compact_list(invalid_packages)}",
        ),
        _formal_deg_gate_row(
            "Standard package artifact manifest",
            "blocked" if artifact_blockers else "passed",
            artifact_blockers,
            [],
            basis="UI may read only declared tables/plots/reports/logs inside the standard result package.",
        ),
        _formal_deg_gate_row(
            "Standard package input manifest",
            "blocked" if input_manifest_blockers else "passed",
            input_manifest_blockers,
            [],
            basis=f"worker_invocation.input_manifest diagnostics={compact_list(input_manifest_statuses)}",
        ),
    ]


def build_analysis_environment_gate_rows(validation: dict[str, Any]) -> list[dict[str, Any]]:
    structural_blockers = _list(validation.get("blockers"))
    readiness_blockers = _list(validation.get("readiness_blockers"))
    environment_ids = _list(validation.get("environment_ids"))
    blocked_environment_ids = _list(validation.get("blocked_environment_ids"))
    return [
        _formal_deg_gate_row(
            "Analysis environment registry",
            validation.get("status") or "blocked",
            structural_blockers,
            _list(validation.get("warnings")),
            basis="analysis/registry/analysis_environments.json",
        ),
        _formal_deg_gate_row(
            "Full R environment readiness",
            "passed" if validation.get("full_mode_ready") is True else "blocked",
            readiness_blockers,
            [f"blocked_full_environments={','.join(blocked_environment_ids)}"] if blocked_environment_ids else [],
            basis=f"environments={','.join(environment_ids)}",
        ),
    ]


def build_analysis_architecture_gate_rows(status: dict[str, Any]) -> list[dict[str, Any]]:
    p0_issues = _list(status.get("p0_issues"))
    p1_issues = _list(status.get("p1_issues"))
    full_gate = status.get("full_analysis_activation_gate") if isinstance(status.get("full_analysis_activation_gate"), dict) else {}
    runtime_scan = status.get("runtime_acquisition_scan") if isinstance(status.get("runtime_acquisition_scan"), dict) else {}
    dependency_scan = status.get("default_dependency_scan") if isinstance(status.get("default_dependency_scan"), dict) else {}
    return [
        _formal_deg_gate_row(
            "R analysis architecture snapshot",
            status.get("status") or "blocked",
            [],
            p1_issues,
            basis=f"requirements={status.get('requirement_count', 0)}; pass={status.get('pass_count', 0)}; warn={status.get('warn_count', 0)}; fail={status.get('fail_count', 0)}",
        ),
        _formal_deg_gate_row(
            "R architecture P0 guard",
            "passed" if not p0_issues else "blocked",
            p0_issues,
            [],
            basis="default app-dev, mock package, result.json, and runtime install boundaries",
        ),
        _formal_deg_gate_row(
            "Full analysis activation gate",
            full_gate.get("status") or "blocked",
            _list(full_gate.get("blockers")),
            [],
            basis=str(full_gate.get("policy") or "full_analysis_requires_environment_resource_and_standard_worker_evidence"),
        ),
        _formal_deg_gate_row(
            "Runtime acquisition scan",
            runtime_scan.get("status") or "blocked",
            [*_list(runtime_scan.get("install_hits")), *_list(runtime_scan.get("resource_download_hits"))],
            [
                f"hits={runtime_scan.get('hit_count', 0)}",
                f"roots={compact_list(_list(runtime_scan.get('scanned_roots')))}",
            ],
            basis=str(runtime_scan.get("policy") or "runtime_package_install_and_resource_download_forbidden"),
        ),
        _formal_deg_gate_row(
            "Default dependency scan",
            dependency_scan.get("status") or "blocked",
            _list(dependency_scan.get("heavy_dependency_hits")),
            [
                f"hits={dependency_scan.get('hit_count', 0)}",
                f"files={compact_list(_list(dependency_scan.get('scanned_files')))}",
            ],
            basis=str(dependency_scan.get("policy") or "heavy_dependencies_excluded_from_app_dev"),
        ),
    ]


def build_analysis_architecture_remediation_rows(queue: dict[str, Any]) -> list[dict[str, Any]]:
    items = [item for item in queue.get("items", []) or [] if isinstance(item, dict)]
    handoff = _analysis_architecture_evidence_handoff_preview(items)
    rows = [
        _formal_deg_gate_row(
            "R architecture remediation queue",
            queue.get("status") or "blocked",
            [],
            [f"items={queue.get('item_count', 0)}", str(queue.get("install_policy") or "")],
            basis=str(queue.get("execution_policy") or "read_only_no_runtime_mutation"),
        )
    ]
    if handoff["total_action_count"]:
        rows.append(
            _formal_deg_gate_row(
                "R evidence template handoff preview",
                handoff["status"],
                [],
                [
                    f"environment_actions={handoff['environment_action_count']}",
                    f"resource_actions={handoff['resource_action_count']}",
                    f"module_actions={handoff['module_action_count']}",
                    handoff["action_policy"],
                ],
                basis=handoff["basis"],
            )
        )
    for item in items:
        module_scope = item.get("module_scope") if isinstance(item.get("module_scope"), dict) else {}
        missing_modules = _list(module_scope.get("missing_module_ids"))
        environment_summary = item.get("environment_action_summary") if isinstance(item.get("environment_action_summary"), dict) else {}
        environment_next_actions = [action for action in item.get("environment_next_actions", []) or [] if isinstance(action, dict)]
        environment_action_counts = environment_summary.get("next_action_counts") if isinstance(environment_summary.get("next_action_counts"), dict) else {}
        action_summary = item.get("module_action_summary") if isinstance(item.get("module_action_summary"), dict) else {}
        next_action_counts = action_summary.get("next_action_counts") if isinstance(action_summary.get("next_action_counts"), dict) else {}
        module_next_actions = [action for action in item.get("module_next_actions", []) or [] if isinstance(action, dict)]
        resource_summary = item.get("resource_action_summary") if isinstance(item.get("resource_action_summary"), dict) else {}
        resource_next_actions = [action for action in item.get("resource_next_actions", []) or [] if isinstance(action, dict)]
        resource_action_counts = resource_summary.get("next_action_counts") if isinstance(resource_summary.get("next_action_counts"), dict) else {}
        action_warnings = [
            *[f"{action}={count}" for action, count in sorted(environment_action_counts.items())],
            *[f"{action}={count}" for action, count in sorted(next_action_counts.items())],
            *[f"{action}={count}" for action, count in sorted(resource_action_counts.items())],
        ]
        scope_basis = ""
        if module_scope:
            scope_basis = f"; missing_modules={len(missing_modules)}; modules={compact_list(missing_modules)}"
        rows.append(
            _formal_deg_gate_row(
                f"R remediation: {item.get('item_id')}",
                item.get("status") or "blocked",
                [str(item.get("source_issue") or "")],
                [
                    *_list(item.get("required_evidence"))[:2],
                    *[f"{action.get('environment_id')}:{action.get('next_action')}" for action in environment_next_actions[:5]],
                    *[f"missing_module:{module_id}" for module_id in missing_modules[:5]],
                    *[f"{action.get('module_id')}:{action.get('migration_next_action')}" for action in module_next_actions[:5]],
                    *[f"{action.get('resource_id')}:{action.get('next_action')}" for action in resource_next_actions[:5]],
                    *action_warnings,
                ],
                basis=f"{item.get('priority', 'P1')}; files={compact_list(_list(item.get('recommended_files'))[:3])}{scope_basis}",
            )
        )
    return rows


def build_module_interface_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    module_rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    blocker_counts = matrix.get("blocker_counts") if isinstance(matrix.get("blocker_counts"), dict) else {}
    rows = [
        _formal_deg_gate_row(
            "Analysis module interface matrix",
            matrix.get("status") or "blocked",
            [f"{key}={value}" for key, value in sorted(blocker_counts.items())],
            [
                f"passed={matrix.get('passed_module_count', 0)}",
                f"blocked={matrix.get('blocked_module_count', 0)}",
            ],
            basis=f"modules={matrix.get('module_count', 0)}; {matrix.get('boundary', 'read_only_standard_module_interface_diagnostics')}",
        )
    ]
    for row in module_rows:
        rows.append(
            _formal_deg_gate_row(
                f"Module interface: {row.get('module_id')}",
                row.get("status") or "blocked",
                _list(row.get("blockers")),
                [
                    f"mock={row.get('mock_supported')}",
                    f"lite={row.get('lite_supported')}",
                    f"full={row.get('full_supported')}",
                    f"fixture={row.get('mock_fixture_validation_status')}",
                ],
                basis=(
                    f"{row.get('module_manifest')}; "
                    f"{row.get('analysis_environment')}->{row.get('full_environment')}"
                ),
            )
        )
    return rows


def build_external_tool_adapter_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    adapter_rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    blocker_counts = matrix.get("blocker_counts") if isinstance(matrix.get("blocker_counts"), dict) else {}
    warning_counts = matrix.get("warning_counts") if isinstance(matrix.get("warning_counts"), dict) else {}
    rows = [
        _formal_deg_gate_row(
            "External tool adapter isolation matrix",
            matrix.get("status") or "blocked",
            [f"{key}={value}" for key, value in sorted(blocker_counts.items())],
            [
                f"passed={matrix.get('passed_module_count', 0)}",
                f"blocked={matrix.get('blocked_module_count', 0)}",
                *[f"warning:{key}={value}" for key, value in sorted(warning_counts.items())],
            ],
            basis=f"modules={matrix.get('module_count', 0)}; {matrix.get('boundary', 'read_only_external_tool_adapter_isolation_diagnostics')}",
        )
    ]
    for row in adapter_rows:
        rows.append(
            _formal_deg_gate_row(
                f"External tool adapter: {row.get('module_id')}",
                row.get("status") or "blocked",
                _list(row.get("blockers")),
                [
                    f"lite={row.get('lite_environment')}",
                    f"exec={row.get('lite_external_tool_execution')}",
                    f"full={row.get('full_environment')}",
                    f"resources={compact_list(_list(row.get('required_resource_ids')))}",
                ],
                basis=(
                    f"{row.get('module_manifest')}; "
                    f"{row.get('external_tool_policy')}; "
                    f"default_app_dependency={row.get('default_app_dependency')}"
                ),
            )
        )
    return rows


def build_task_system_boundary_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    module_rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    blocker_counts = matrix.get("blocker_counts") if isinstance(matrix.get("blocker_counts"), dict) else {}
    warning_counts = matrix.get("warning_counts") if isinstance(matrix.get("warning_counts"), dict) else {}
    rows = [
        _formal_deg_gate_row(
            "Task system boundary matrix",
            matrix.get("status") or "blocked",
            [f"{key}={value}" for key, value in sorted(blocker_counts.items())],
            [
                f"passed={matrix.get('passed_module_count', 0)}",
                f"blocked={matrix.get('blocked_module_count', 0)}",
                *[f"warning:{key}={value}" for key, value in sorted(warning_counts.items())],
            ],
            basis=f"modules={matrix.get('module_count', 0)}; {matrix.get('boundary', 'read_only_main_backend_task_system_boundary_diagnostics')}",
        )
    ]
    for row in module_rows:
        rows.append(
            _formal_deg_gate_row(
                f"Task boundary: {row.get('module_id')}",
                row.get("status") or "blocked",
                _list(row.get("blockers")),
                [
                    f"task_invocation={row.get('required_task_system_invocation')}",
                    f"worker_manifest={row.get('worker_invocation_manifest_required')}",
                    f"mock={row.get('mock_task_bridge_supported')}",
                    f"lite={row.get('lite_task_bridge_supported')}",
                ],
                basis=(
                    f"{row.get('task_bridge_entrypoint')}; "
                    f"task_types={compact_list(_list(row.get('result_index_task_types')))}; "
                    f"formal_worker={row.get('formal_worker_status')}"
                ),
            )
        )
    return rows


def build_frontend_consumption_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    consumer_rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    blocker_counts = matrix.get("blocker_counts") if isinstance(matrix.get("blocker_counts"), dict) else {}
    warning_counts = matrix.get("warning_counts") if isinstance(matrix.get("warning_counts"), dict) else {}
    rows = [
        _formal_deg_gate_row(
            "Frontend standard package consumption matrix",
            matrix.get("status") or "blocked",
            [f"{key}={value}" for key, value in sorted(blocker_counts.items())],
            [
                f"passed={matrix.get('passed_consumer_count', 0)}",
                f"partial={matrix.get('partial_consumer_count', 0)}",
                f"blocked={matrix.get('blocked_consumer_count', 0)}",
                *[f"warning:{key}={value}" for key, value in sorted(warning_counts.items())],
            ],
            basis=f"consumers={matrix.get('consumer_count', 0)}; {matrix.get('boundary', 'read_only_frontend_standard_package_consumption_diagnostics')}",
        )
    ]
    for row in consumer_rows:
        rows.append(
            _formal_deg_gate_row(
                f"Frontend standard package consumer: {row.get('row_id')}",
                row.get("status") or "blocked",
                _list(row.get("blockers")),
                _list(row.get("warnings")),
                basis=(
                    f"{row.get('consumer_surface')}; "
                    f"{row.get('file_path')}; "
                    f"{row.get('source_policy')}"
                ),
            )
        )
    return rows


def _analysis_architecture_evidence_handoff_preview(items: list[dict[str, Any]]) -> dict[str, Any]:
    environment_action_count = 0
    resource_action_count = 0
    module_action_count = 0
    for item in items:
        environment_action_count += len([action for action in item.get("environment_next_actions", []) or [] if isinstance(action, dict)])
        resource_action_count += len([action for action in item.get("resource_next_actions", []) or [] if isinstance(action, dict)])
        module_action_count += len([action for action in item.get("module_next_actions", []) or [] if isinstance(action, dict)])
    total = environment_action_count + resource_action_count + module_action_count
    return {
        "status": "available_for_handoff" if total else "not_available",
        "environment_action_count": environment_action_count,
        "resource_action_count": resource_action_count,
        "module_action_count": module_action_count,
        "total_action_count": total,
        "action_policy": "planning_only_not_readiness_evidence",
        "basis": "scripts/analysis_architecture_gate.py --evidence-template-output <path>",
    }


def build_standard_worker_migration_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    module_rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    expected_modules = _list(matrix.get("expected_evidence_module_ids"))
    passed_modules = _list(matrix.get("passed_evidence_module_ids"))
    blocked_modules = _list(matrix.get("blocked_evidence_module_ids"))
    missing_modules = _list(matrix.get("missing_evidence_module_ids"))
    adapter_status_counts = matrix.get("adapter_status_counts") if isinstance(matrix.get("adapter_status_counts"), dict) else {}
    migration_next_action_counts = matrix.get("migration_next_action_counts") if isinstance(matrix.get("migration_next_action_counts"), dict) else {}
    migration_blocker_counts = matrix.get("migration_blocker_counts") if isinstance(matrix.get("migration_blocker_counts"), dict) else {}
    rows = [
        _formal_deg_gate_row(
            "R standard worker migration matrix",
            matrix.get("status") or "blocked",
            [f"formal_pending_count={matrix.get('formal_pending_count', 0)}"] if int(matrix.get("formal_pending_count") or 0) else [],
            [f"full_blocked_count={matrix.get('full_blocked_count', 0)}"] if int(matrix.get("full_blocked_count") or 0) else [],
            basis=f"modules={matrix.get('module_count', 0)}; {matrix.get('boundary', 'matrix_is_read_only_no_worker_execution')}",
        ),
        _formal_deg_gate_row(
            "R worker migration evidence coverage",
            "passed" if expected_modules and not missing_modules and not blocked_modules else "blocked",
            [f"missing_standard_worker_migration_evidence:{module_id}" for module_id in missing_modules],
            [f"passed={len(passed_modules)}", f"blocked={len(blocked_modules)}"],
            basis=f"expected={len(expected_modules)}; missing={len(missing_modules)}; modules={compact_list(missing_modules)}",
        ),
        _formal_deg_gate_row(
            "R worker migration adapter status summary",
            "passed" if not migration_blocker_counts and expected_modules else "blocked",
            [f"{key}={value}" for key, value in sorted(migration_blocker_counts.items())],
            [
                *[f"adapter:{key}={value}" for key, value in sorted(adapter_status_counts.items())],
                *[f"next:{key}={value}" for key, value in sorted(migration_next_action_counts.items())],
            ],
            basis="read_only_standard_worker_migration_grouping",
        )
    ]
    for row in module_rows:
        prerequisites = row.get("migration_prerequisite_status") if isinstance(row.get("migration_prerequisite_status"), dict) else {}
        rows.append(
            _formal_deg_gate_row(
                f"R worker migration: {row.get('module_id')}",
                "passed" if row.get("formal_worker_status") == "migrated_to_isolated_standard_worker" else "blocked",
                [str(row.get("formal_worker_status") or ""), str(row.get("migration_next_action") or "")],
                [
                    f"lite={row.get('lite_status')}",
                    f"full={row.get('full_status')}",
                    f"prereq={prerequisites.get('overall', 'blocked')}",
                ],
                basis=f"{row.get('analysis_environment')}->{row.get('full_environment')}; {row.get('current_adapter_status')}; next={row.get('migration_next_action')}",
            )
        )
    return rows


def build_full_activation_module_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    module_rows = [row for row in matrix.get("rows", []) or [] if isinstance(row, dict)]
    blocker_counts = matrix.get("blocker_counts") if isinstance(matrix.get("blocker_counts"), dict) else {}
    rows = [
        _formal_deg_gate_row(
            "Full analysis module activation matrix",
            matrix.get("status") or "blocked",
            [f"{key}={value}" for key, value in sorted(blocker_counts.items())],
            [
                f"eligible={matrix.get('eligible_module_count', 0)}",
                f"blocked={matrix.get('blocked_module_count', 0)}",
            ],
            basis=f"modules={matrix.get('module_count', 0)}; {matrix.get('boundary', 'read_only_module_level_full_activation_diagnostics')}",
        )
    ]
    for row in module_rows:
        rows.append(
            _formal_deg_gate_row(
                f"Full activation: {row.get('module_id')}",
                row.get("status") or "blocked",
                _list(row.get("blockers"))[:6],
                [
                    f"environment={row.get('environment_status')}",
                    f"resources={row.get('resource_status')}",
                    f"worker={row.get('standard_worker_migration_status')}",
                    f"next={row.get('migration_next_action')}",
                ],
                basis=(
                    f"{row.get('analysis_environment')}->{row.get('full_environment')}; "
                    f"resources={compact_list(_list(row.get('required_resource_ids')))}"
                ),
            )
        )
    return rows


def build_gate_preview_rows(*, result_entries: list[dict[str, Any]], report_gate: dict[str, Any], formal_deg_report_gate: dict[str, Any] | None = None) -> list[dict[str, Any]]:
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
            "gate": "Report-ready export",
            "status": "available" if report_gate.get("status") == "eligible_for_internal_report" else "blocked_report_ready_gate",
            "basis": str(report_gate.get("status") or "blocked"),
            "blockers": compact_list(report_gate.get("blockers", []) or []),
            "warnings": compact_list(report_gate.get("warnings", []) or []),
        },
    ]


def build_survival_clinical_rows(*, packages: list[dict[str, Any]], survival_dependency: dict[str, Any], km_gate_state: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    package = next((item for item in packages if item.get("package_type") == "tcga_clinical_survival_preflight"), None)
    km_gate_state = km_gate_state or {}
    parameter_gate = km_gate_state.get("parameter_gate") if isinstance(km_gate_state.get("parameter_gate"), dict) else {}
    confirmation_gate = km_gate_state.get("confirmation_gate") if isinstance(km_gate_state.get("confirmation_gate"), dict) else {}
    cox_parameter_gate = km_gate_state.get("cox_parameter_gate") if isinstance(km_gate_state.get("cox_parameter_gate"), dict) else {}
    cox_confirmation_gate = km_gate_state.get("cox_confirmation_gate") if isinstance(km_gate_state.get("cox_confirmation_gate"), dict) else {}
    cox_multivariate_design = km_gate_state.get("cox_multivariate_design") if isinstance(km_gate_state.get("cox_multivariate_design"), dict) else {}
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
            "label": "Two-group KM/log-rank",
            "status": str(parameter_gate.get("status") or "blocked"),
            "asset_status": package_status,
            "backend_status": str(survival_dependency.get("status") or "unknown"),
            "disabled_reason": compact_list(_list(parameter_gate.get("blockers")) + _list(confirmation_gate.get("blockers")) + _list(survival_dependency.get("blockers"))),
            "warnings": compact_list(_list(parameter_gate.get("warnings"))),
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


def _default_km_grouping(rows: list[dict[str, str]], survival_package: dict[str, Any]) -> tuple[str, str, str]:
    excluded = {str(survival_package.get("time_field") or ""), str(survival_package.get("event_field") or "")}
    for field in rows[0].keys() if rows else []:
        if field in excluded or field in {"sample_id", "case_id", "barcode", "tcga_barcode", "patient_barcode", "participant_barcode"}:
            continue
        values = sorted({str(row.get(field) or "").strip() for row in rows if str(row.get(field) or "").strip()})
        if len(values) == 2:
            return field, values[0], values[1]
    return "", "", ""


def _default_cox_covariate(rows: list[dict[str, str]], survival_package: dict[str, Any], audit: dict[str, Any]) -> str:
    excluded = {str(survival_package.get("time_field") or ""), str(survival_package.get("event_field") or "")}
    mapping = audit.get("variable_mapping") if isinstance(audit.get("variable_mapping"), dict) else {}
    for name, spec in mapping.items():
        if name in excluded or name in {"sample_id", "case_id", "barcode", "tcga_barcode", "patient_barcode", "participant_barcode"}:
            continue
        if isinstance(spec, dict) and spec.get("variable_type") in {"binary_variable", "categorical_variable", "continuous_variable", "ordinal_variable"}:
            return str(name)
    for field in rows[0].keys() if rows else []:
        if field not in excluded:
            return field
    return ""


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
