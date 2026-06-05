from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import REPO_ROOT, load_analysis_module_registry
from .resources import validate_analysis_environment_registry, validate_analysis_resource_manifest
from .standard_package import validate_standard_result_package


STANDARD_WORKER_MIGRATION_EVIDENCE_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "standard_worker_migration_evidence.schema.json"
STANDARD_WORKER_MIGRATION_EVIDENCE_REGISTRY_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "standard_worker_migration_evidence_registry.schema.json"
STANDARD_WORKER_MIGRATION_EVIDENCE_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "standard_worker_migration_evidence.json"
FULL_ANALYSIS_ACTIVATION_GATE_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "full_analysis_activation_gate.schema.json"
REMEDIATION_QUEUE_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "remediation_queue.schema.json"
TARGET_MODULE_IDS = (
    "deg",
    "survival",
    "univariate",
    "multivariate",
    "enrichment",
    "immune_infiltration",
    "correlation",
    "spatial_transcriptomics",
    "docking",
    "molecular_dynamics",
)
BANNED_RUNTIME_INSTALL_PATTERNS = (
    "install" + ".packages",
    "BiocManager" + "::install",
    "pak" + "::pkg_install",
    "remotes" + "::install_github",
)
BANNED_RUNTIME_RESOURCE_DOWNLOAD_PATTERNS = (
    "download" + ".file",
    "curl" + "::curl_download",
    "BiocFile" + "Cache(",
    "Annotation" + "Hub(",
    "Experiment" + "Hub(",
    "w" + "get ",
    "curl" + " -",
)
HEAVY_DEFAULT_DEPENDENCY_NAMES = (
    "ReactomePA",
    "reactome.db",
    "Seurat",
    "CellChat",
    "GSVA",
    "AutoDock Vina",
    "GROMACS",
    "clusterProfiler",
    "fgsea",
)


def build_analysis_architecture_status() -> dict[str, Any]:
    """Build a machine-readable snapshot of the R analysis architecture boundary.

    The snapshot is intentionally read-only. It does not execute workers, install
    packages, download resources, or inspect module-private R outputs.
    """

    registry = load_analysis_module_registry()
    modules = [item for item in registry.get("modules", []) if isinstance(item, dict)]
    module_ids = [str(item.get("module_id") or "") for item in modules if item.get("module_id")]
    module_interface_matrix = build_module_interface_matrix(registry)
    standard_worker_migration_matrix = build_standard_worker_migration_matrix(registry)
    environment_validation = validate_analysis_environment_registry(module_registry=registry)
    resource_validation = validate_analysis_resource_manifest()
    full_analysis_activation_gate = build_full_analysis_activation_gate(
        environment_validation=environment_validation,
        resource_validation=resource_validation,
        standard_worker_migration_matrix=standard_worker_migration_matrix,
    )
    full_activation_module_matrix = build_full_activation_module_matrix(
        registry=registry,
        environment_validation=environment_validation,
        resource_validation=resource_validation,
        standard_worker_migration_matrix=standard_worker_migration_matrix,
    )
    external_tool_adapter_matrix = build_external_tool_adapter_matrix(
        registry=registry,
        resource_validation=resource_validation,
    )
    task_system_boundary_matrix = build_task_system_boundary_matrix(
        registry=registry,
        standard_worker_migration_matrix=standard_worker_migration_matrix,
    )
    frontend_consumption_matrix = build_frontend_standard_package_consumption_matrix()
    runtime_acquisition_scan = build_runtime_acquisition_scan_summary()
    default_dependency_scan = build_default_dependency_scan_summary()
    active_install_hits = list(runtime_acquisition_scan.get("install_hits", []))
    active_download_hits = list(runtime_acquisition_scan.get("resource_download_hits", []))
    heavy_default_hits = list(default_dependency_scan.get("heavy_dependency_hits", []))
    rows = [
        _row(
            "RARCH-01",
            "Unified analysis module directory",
            "pass" if _all_module_dirs_exist(module_ids) else "fail",
            "analysis/modules/<module_id>/module.json",
            blockers=[] if _all_module_dirs_exist(module_ids) else ["analysis_module_directory_missing"],
        ),
        _row(
            "RARCH-02",
            "Module registry",
            "pass" if registry.get("schema_version") == "biomedpilot.analysis_modules.v1" and modules else "fail",
            "analysis/registry/analysis_modules.json",
        ),
        _row(
            "RARCH-03",
            "Unified worker entrypoint",
            "warn" if _path_exists(registry.get("standard_entrypoint")) else "fail",
            str(registry.get("standard_entrypoint") or "missing"),
            warnings=["existing_formal_algorithms_still_need_standard_worker_migration"] if _path_exists(registry.get("standard_entrypoint")) else [],
            blockers=[] if _path_exists(registry.get("standard_entrypoint")) else ["standard_entrypoint_missing"],
        ),
        _row(
            "RARCH-04",
            "Mock / lite / full mode declarations",
            "warn" if _all_modules_declare_modes(modules) else "fail",
            "analysis/registry/analysis_modules.json::modules[*].modes",
            warnings=["full_modes_declared_but_currently_blocked"] if _all_modules_declare_modes(modules) else [],
            blockers=[] if _all_modules_declare_modes(modules) else ["analysis_module_modes_incomplete"],
        ),
        _row("RARCH-05", "Unified input and output schemas", "pass" if _required_schemas_exist() else "fail", "analysis/schemas/input and analysis/schemas/output"),
        _row(
            "RARCH-06",
            "Mock packages contain result.json and provenance.json",
            "pass" if _mock_packages_have_payloads(modules) else "fail",
            "analysis/fixtures/outputs/<module>/mock_result_package",
            blockers=[] if _mock_packages_have_payloads(modules) else ["mock_result_or_provenance_missing"],
        ),
        _row(
            "RARCH-07",
            "Mock packages contain tables/plots/reports/logs",
            "pass" if _mock_packages_have_directories(modules) else "fail",
            "analysis/fixtures/outputs/<module>/mock_result_package",
            blockers=[] if _mock_packages_have_directories(modules) else ["mock_standard_package_directories_missing"],
        ),
        _row(
            "RARCH-08",
            "Frontend standard package consumption boundary",
            "warn",
            "build_standard_analysis_package_catalog and Analysis Center standard package gates",
            warnings=["detailed_result_views_still_need_standard_package_only_migration"],
        ),
        _row(
            "RARCH-09",
            "Main backend task-system invocation boundary",
            "warn",
            "app/analysis_runtime/task_bridge.py",
            warnings=["legacy_service_adapter_sidecars_remain_transitional"],
        ),
        _row(
            "RARCH-10",
            "No active runtime R package install or resource download commands",
            "pass" if not active_install_hits and not active_download_hits else "fail",
            "active non-legacy app/analysis/scripts/config scan",
            blockers=[f"runtime_install_command_found:{item}" for item in active_install_hits]
            + [f"runtime_resource_download_command_found:{item}" for item in active_download_hits],
        ),
        _row(
            "RARCH-11",
            "Heavy analysis dependencies excluded from default app-dev deps",
            "pass" if not heavy_default_hits else "fail",
            "requirements.txt, pyproject.toml, docker/Dockerfile.app-dev, renv/renv.app.lock",
            blockers=[f"heavy_dependency_in_default_dev_surface:{item}" for item in heavy_default_hits],
        ),
        _row(
            "RARCH-12",
            "Dedicated environment split",
            "warn" if environment_validation.get("status") == "passed" else "fail",
            "analysis/registry/analysis_environments.json",
            blockers=list(environment_validation.get("blockers", [])),
            warnings=list(environment_validation.get("readiness_blockers", [])),
        ),
        _row(
            "RARCH-13",
            "renv lock equivalent exists",
            "warn" if _renv_locks_exist() else "fail",
            "renv/renv.*.lock",
            warnings=["full_environment_locks_are_scaffold_only_not_restored"] if _renv_locks_exist() else [],
            blockers=[] if _renv_locks_exist() else ["renv_locks_missing"],
        ),
        _row(
            "RARCH-14",
            "Full analysis Docker image boundary",
            "warn" if _dockerfiles_exist() else "fail",
            "docker/Dockerfile.r-*",
            warnings=["dockerfiles_exist_but_full_image_builds_not_proven"] if _dockerfiles_exist() else [],
            blockers=[] if _dockerfiles_exist() else ["analysis_dockerfiles_missing"],
        ),
        _row(
            "RARCH-15",
            "Large resource version/source/hash/license/cache governance",
            "warn" if resource_validation.get("status") == "passed" else "fail",
            "analysis/resources/manifest.json",
            blockers=list(resource_validation.get("blockers", [])),
            warnings=[*list(resource_validation.get("warnings", [])), *[f"blocked_resource:{item}" for item in resource_validation.get("blocked_resource_ids", [])]],
        ),
        _row(
            "RARCH-16",
            "Reproducibility provenance contract",
            "warn",
            "analysis/schemas/output/provenance.schema.json and standard package validator",
            warnings=["unmigrated_formal_or_full_modules_still_need_complete_runtime_package_version_capture"],
        ),
        _row(
            "RARCH-17",
            "Target analysis modules share the standard interface",
            "warn" if set(TARGET_MODULE_IDS) <= set(module_ids) else "fail",
            "analysis/registry/analysis_modules.json and analysis/modules/*/module.json",
            blockers=[] if set(TARGET_MODULE_IDS) <= set(module_ids) else [f"target_module_missing:{item}" for item in sorted(set(TARGET_MODULE_IDS) - set(module_ids))],
            warnings=[f"formal_standard_worker_pending_modules={standard_worker_migration_matrix.get('formal_pending_count', 0)}"],
        ),
        _row(
            "RARCH-18",
            "Docking and molecular dynamics are external-tool adapters",
            "warn" if _chem_modules_use_external_tool_policy() else "fail",
            "analysis/modules/docking/module.json and analysis/modules/molecular_dynamics/module.json",
            warnings=["lite_mode_writes_command_manifest_only_no_AutoDock_or_GROMACS_execution"] if _chem_modules_use_external_tool_policy() else [],
            blockers=[] if _chem_modules_use_external_tool_policy() else ["chem_external_tool_policy_missing"],
        ),
        _row(
            "RARCH-19",
            "Default development starts without full analysis deps",
            "pass" if not heavy_default_hits else "fail",
            "source smoke and default dependency surface",
            blockers=[f"default_dev_requires_heavy_dependency:{item}" for item in heavy_default_hits],
        ),
        _row(
            "RARCH-20",
            "Full mode remains blocked until resources and environments are restored",
            "pass" if environment_validation.get("full_mode_ready") is False and resource_validation.get("full_mode_ready") is False else "fail",
            "environment/resource validators",
            blockers=[] if environment_validation.get("full_mode_ready") is False and resource_validation.get("full_mode_ready") is False else ["full_mode_unexpectedly_ready"],
        ),
    ]
    p0 = _p0_issues(rows)
    p1 = _p1_issues(environment_validation, resource_validation, standard_worker_migration_matrix)
    status = "failed" if p0 else ("partial_with_p1_gaps" if p1 else "passed")
    return {
        "schema_version": "biomedpilot.analysis.architecture_status.v1",
        "status": status,
        "requirement_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "pass"),
        "warn_count": sum(1 for row in rows if row["status"] == "warn"),
        "fail_count": sum(1 for row in rows if row["status"] == "fail"),
        "requirement_rows": rows,
        "p0_issues": p0,
        "p1_issues": p1,
        "module_interface_matrix": module_interface_matrix,
        "external_tool_adapter_matrix": external_tool_adapter_matrix,
        "task_system_boundary_matrix": task_system_boundary_matrix,
        "frontend_consumption_matrix": frontend_consumption_matrix,
        "standard_worker_migration_matrix": standard_worker_migration_matrix,
        "full_activation_module_matrix": full_activation_module_matrix,
        "runtime_acquisition_scan": runtime_acquisition_scan,
        "default_dependency_scan": default_dependency_scan,
        "full_analysis_activation_gate": full_analysis_activation_gate,
        "environment_validation": environment_validation,
        "resource_validation": resource_validation,
    }


def build_runtime_acquisition_scan_summary() -> dict[str, Any]:
    install_scan = _active_runtime_command_scan(
        BANNED_RUNTIME_INSTALL_PATTERNS,
        scan_id="runtime_install_command_scan",
    )
    download_scan = _active_runtime_command_scan(
        BANNED_RUNTIME_RESOURCE_DOWNLOAD_PATTERNS,
        scan_id="runtime_resource_download_command_scan",
    )
    install_hits = list(install_scan.get("hits", []))
    download_hits = list(download_scan.get("hits", []))
    return {
        "schema_version": "biomedpilot.analysis.runtime_acquisition_scan.v1",
        "status": "passed" if not install_hits and not download_hits else "blocked",
        "install_scan": install_scan,
        "resource_download_scan": download_scan,
        "install_hits": install_hits,
        "resource_download_hits": download_hits,
        "hit_count": len(install_hits) + len(download_hits),
        "scanned_roots": install_scan.get("scanned_roots", []),
        "excluded_path_parts": install_scan.get("excluded_path_parts", []),
        "policy": "runtime_package_install_and_resource_download_forbidden_in_active_app_analysis_scripts_config",
    }


def build_default_dependency_scan_summary() -> dict[str, Any]:
    paths = [
        REPO_ROOT / "requirements.txt",
        REPO_ROOT / "pyproject.toml",
        REPO_ROOT / "docker" / "Dockerfile.app-dev",
        REPO_ROOT / "renv" / "renv.app.lock",
    ]
    hits: list[str] = []
    scanned_files: list[str] = []
    missing_files: list[str] = []
    for path in paths:
        relative = str(path.relative_to(REPO_ROOT))
        if not path.is_file():
            missing_files.append(relative)
            continue
        scanned_files.append(relative)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in HEAVY_DEFAULT_DEPENDENCY_NAMES:
            if name in text:
                hits.append(f"{relative}:{name}")
    return {
        "schema_version": "biomedpilot.analysis.default_dependency_scan.v1",
        "status": "passed" if not hits else "blocked",
        "scanned_files": scanned_files,
        "missing_files": missing_files,
        "heavy_dependency_names": list(HEAVY_DEFAULT_DEPENDENCY_NAMES),
        "heavy_dependency_hits": sorted(set(hits)),
        "hit_count": len(set(hits)),
        "policy": "heavy_full_analysis_dependencies_excluded_from_default_app_dev_surface",
    }


def build_module_interface_matrix(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return per-module evidence for the standard analysis module interface."""

    payload = registry if isinstance(registry, dict) else load_analysis_module_registry()
    modules = [
        item
        for item in payload.get("modules", [])
        if isinstance(item, dict) and item.get("module_id") in TARGET_MODULE_IDS
    ]
    standard_entrypoint = str(payload.get("standard_entrypoint") or "analysis/runners/run_module.R")
    rows = [_module_interface_row(module, standard_entrypoint=standard_entrypoint) for module in modules]
    blocker_counts = _count_row_blockers(rows, "blockers")
    return {
        "schema_version": "biomedpilot.analysis.module_interface_matrix.v1",
        "status": "passed" if rows and not blocker_counts else "blocked",
        "module_count": len(rows),
        "passed_module_count": sum(1 for row in rows if row.get("status") == "passed"),
        "blocked_module_count": sum(1 for row in rows if row.get("status") != "passed"),
        "blocker_counts": blocker_counts,
        "rows": rows,
        "boundary": "read_only_standard_module_interface_diagnostics",
    }


def _module_interface_row(module: dict[str, Any], *, standard_entrypoint: str) -> dict[str, Any]:
    module_id = str(module.get("module_id") or "")
    module_manifest = str(module.get("module_manifest") or f"analysis/modules/{module_id}/module.json")
    manifest_payload = _read_json(REPO_ROOT / module_manifest) if (REPO_ROOT / module_manifest).is_file() else {}
    source = manifest_payload if isinstance(manifest_payload, dict) and manifest_payload else module
    modes = source.get("modes") if isinstance(source.get("modes"), dict) else {}
    mock = modes.get("mock") if isinstance(modes.get("mock"), dict) else {}
    lite = modes.get("lite") if isinstance(modes.get("lite"), dict) else {}
    full = modes.get("full") if isinstance(modes.get("full"), dict) else {}
    mock_package = str(mock.get("fixture_output_package") or "")
    blockers: list[str] = []
    if not module_id:
        blockers.append("module_interface_module_id_missing")
    if not (REPO_ROOT / module_manifest).is_file():
        blockers.append(f"module_interface_manifest_missing:{module_id}:{module_manifest}")
    if source.get("schema_version") != "biomedpilot.analysis_module_manifest.v1":
        blockers.append(f"module_interface_manifest_schema_version_invalid:{module_id}")
    if str(source.get("module_id") or "") != module_id:
        blockers.append(f"module_interface_manifest_module_id_mismatch:{module_id}")
    if str(source.get("standard_entrypoint") or "") != standard_entrypoint:
        blockers.append(f"module_interface_standard_entrypoint_mismatch:{module_id}")
    for field in ("input_schema", "output_schema"):
        path = str(source.get(field) or "")
        if not path:
            blockers.append(f"module_interface_{field}_missing:{module_id}")
        elif not (REPO_ROOT / path).is_file():
            blockers.append(f"module_interface_{field}_not_found:{module_id}:{path}")
    for mode_name, mode_payload in (("mock", mock), ("lite", lite), ("full", full)):
        if not mode_payload:
            blockers.append(f"module_interface_mode_missing:{module_id}:{mode_name}")
        elif "supported" not in mode_payload:
            blockers.append(f"module_interface_mode_supported_flag_missing:{module_id}:{mode_name}")
    fixture_validation: dict[str, Any] = {}
    if not mock_package:
        blockers.append(f"module_interface_mock_fixture_package_missing:{module_id}")
    elif not (REPO_ROOT / mock_package).is_dir():
        blockers.append(f"module_interface_mock_fixture_package_not_found:{module_id}:{mock_package}")
    else:
        fixture_validation = validate_standard_result_package(REPO_ROOT / mock_package)
        if fixture_validation.get("status") != "passed":
            blockers.extend(
                f"module_interface_mock_fixture_package:{module_id}:{blocker}"
                for blocker in fixture_validation.get("blockers", [])
            )
    return {
        "module_id": module_id,
        "title": str(source.get("title") or module.get("title") or module_id),
        "status": "blocked" if blockers else "passed",
        "module_manifest": module_manifest,
        "standard_entrypoint": str(source.get("standard_entrypoint") or ""),
        "input_schema": str(source.get("input_schema") or ""),
        "output_schema": str(source.get("output_schema") or ""),
        "mock_supported": bool(mock.get("supported")),
        "lite_supported": bool(lite.get("supported")),
        "full_supported": bool(full.get("supported")),
        "mock_fixture_output_package": mock_package,
        "mock_fixture_validation_status": str(fixture_validation.get("status") or ("missing" if not mock_package else "blocked")),
        "analysis_environment": str(source.get("analysis_environment") or module.get("analysis_environment") or ""),
        "full_environment": str(source.get("full_environment") or module.get("full_environment") or ""),
        "result_package_required": [str(item) for item in source.get("result_package_required", []) if item],
        "blockers": list(dict.fromkeys(blockers)),
    }


def build_external_tool_adapter_matrix(
    *,
    registry: dict[str, Any] | None = None,
    resource_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return read-only isolation evidence for chemistry external-tool adapters."""

    payload = registry if isinstance(registry, dict) else load_analysis_module_registry()
    resources = resource_validation if isinstance(resource_validation, dict) else validate_analysis_resource_manifest()
    modules = [
        item
        for item in payload.get("modules", [])
        if isinstance(item, dict) and item.get("module_id") in {"docking", "molecular_dynamics"}
    ]
    resource_templates = [
        item
        for item in resources.get("resource_lock_evidence_templates", [])
        if isinstance(item, dict)
    ]
    blocked_resource_ids = {str(item) for item in resources.get("blocked_resource_ids", []) if item}
    rows = [
        _external_tool_adapter_row(
            module,
            resource_templates=resource_templates,
            blocked_resource_ids=blocked_resource_ids,
        )
        for module in modules
    ]
    blocker_counts = _count_row_blockers(rows, "blockers")
    warning_counts = _count_row_blockers(rows, "warnings")
    return {
        "schema_version": "biomedpilot.analysis.external_tool_adapter_matrix.v1",
        "status": "passed" if rows and not blocker_counts else "blocked",
        "module_count": len(rows),
        "passed_module_count": sum(1 for row in rows if row.get("status") == "passed"),
        "blocked_module_count": sum(1 for row in rows if row.get("status") != "passed"),
        "blocker_counts": blocker_counts,
        "warning_counts": warning_counts,
        "rows": rows,
        "boundary": "read_only_external_tool_adapter_isolation_diagnostics",
    }


def _external_tool_adapter_row(
    module: dict[str, Any],
    *,
    resource_templates: list[dict[str, Any]],
    blocked_resource_ids: set[str],
) -> dict[str, Any]:
    module_id = str(module.get("module_id") or "")
    module_manifest = str(module.get("module_manifest") or f"analysis/modules/{module_id}/module.json")
    manifest_payload = _read_json(REPO_ROOT / module_manifest) if (REPO_ROOT / module_manifest).is_file() else {}
    source = manifest_payload if isinstance(manifest_payload, dict) and manifest_payload else module
    modes = source.get("modes") if isinstance(source.get("modes"), dict) else {}
    lite = modes.get("lite") if isinstance(modes.get("lite"), dict) else {}
    full = modes.get("full") if isinstance(modes.get("full"), dict) else {}
    dependency_policy = source.get("dependency_policy") if isinstance(source.get("dependency_policy"), dict) else {}
    expected_full_environment = {
        "docking": "r-chem-full",
        "molecular_dynamics": "r-chem-gpu",
    }.get(module_id, "")
    expected_tool_name = {
        "docking": "AutoDock_Vina",
        "molecular_dynamics": "GROMACS",
    }.get(module_id, "")
    required_resource_ids = [
        str(template.get("resource_id") or "")
        for template in resource_templates
        if module_id in {str(value) for value in template.get("approved_for_modules", []) if value is not None}
    ]
    required_resource_ids = [item for item in required_resource_ids if item]
    blocked_required_resources = [resource_id for resource_id in required_resource_ids if resource_id in blocked_resource_ids]
    blockers: list[str] = []
    warnings: list[str] = []
    if not module_id:
        blockers.append("external_tool_adapter_module_id_missing")
    if not (REPO_ROOT / module_manifest).is_file():
        blockers.append(f"external_tool_adapter_manifest_missing:{module_id}:{module_manifest}")
    if source.get("schema_version") != "biomedpilot.analysis_module_manifest.v1":
        blockers.append(f"external_tool_adapter_manifest_schema_version_invalid:{module_id}")
    policy = str(source.get("external_tool_policy") or "")
    if not policy:
        blockers.append(f"external_tool_adapter_policy_missing:{module_id}")
    elif expected_tool_name and f"R_adapter_calls_{expected_tool_name}" not in policy:
        blockers.append(f"external_tool_adapter_policy_tool_mismatch:{module_id}")
    if expected_full_environment and str(source.get("full_environment") or "") != expected_full_environment:
        blockers.append(f"external_tool_adapter_full_environment_mismatch:{module_id}:{expected_full_environment}")
    if str(source.get("analysis_environment") or "") != "r-bio-core":
        blockers.append(f"external_tool_adapter_lite_analysis_environment_not_core:{module_id}")
    if str(lite.get("environment") or "") != "r-bio-core":
        blockers.append(f"external_tool_adapter_lite_environment_not_core:{module_id}")
    if str(lite.get("external_tool_execution") or "") != "not_executed_in_lite_mode":
        blockers.append(f"external_tool_adapter_lite_executes_external_tool:{module_id}")
    if str(lite.get("worker_backend") or "") != "rscript":
        blockers.append(f"external_tool_adapter_lite_worker_backend_invalid:{module_id}")
    if dependency_policy.get("runtime_install") != "forbidden":
        blockers.append(f"external_tool_adapter_runtime_install_not_forbidden:{module_id}")
    if dependency_policy.get("default_app_dependency") is not False:
        blockers.append(f"external_tool_adapter_default_app_dependency_not_false:{module_id}")
    if not required_resource_ids:
        blockers.append(f"external_tool_adapter_required_resources_missing:{module_id}")
    if str(full.get("blocker") or ""):
        warnings.append(str(full.get("blocker")))
    if blocked_required_resources:
        warnings.append(f"full_mode_blocked_until_tool_or_resource_lock:{','.join(blocked_required_resources)}")
    if not blockers:
        warnings.append("lite_mode_writes_command_manifest_only_no_external_tool_execution")
    return {
        "module_id": module_id,
        "title": str(source.get("title") or module.get("title") or module_id),
        "status": "blocked" if blockers else "passed",
        "module_manifest": module_manifest,
        "analysis_environment": str(source.get("analysis_environment") or ""),
        "lite_environment": str(lite.get("environment") or ""),
        "lite_worker_backend": str(lite.get("worker_backend") or ""),
        "lite_capability": str(lite.get("capability") or ""),
        "lite_external_tool_execution": str(lite.get("external_tool_execution") or ""),
        "full_supported": bool(full.get("supported")),
        "full_blocker": str(full.get("blocker") or ""),
        "full_environment": str(source.get("full_environment") or ""),
        "environment_lock": str(source.get("environment_lock") or ""),
        "dockerfile": str(source.get("dockerfile") or ""),
        "external_tool_policy": policy,
        "runtime_install_policy": str(dependency_policy.get("runtime_install") or ""),
        "default_app_dependency": dependency_policy.get("default_app_dependency"),
        "required_resource_ids": required_resource_ids,
        "blocked_required_resource_ids": blocked_required_resources,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_task_system_boundary_matrix(
    *,
    registry: dict[str, Any] | None = None,
    standard_worker_migration_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return per-module diagnostics for the main-backend task boundary."""

    payload = registry if isinstance(registry, dict) else load_analysis_module_registry()
    migration_matrix = (
        standard_worker_migration_matrix
        if isinstance(standard_worker_migration_matrix, dict)
        else build_standard_worker_migration_matrix(payload)
    )
    migration_by_module = {
        str(row.get("module_id") or ""): row
        for row in migration_matrix.get("rows", [])
        if isinstance(row, dict) and row.get("module_id")
    }
    modules = [
        item
        for item in payload.get("modules", [])
        if isinstance(item, dict) and item.get("module_id") in TARGET_MODULE_IDS
    ]
    rows = [
        _task_system_boundary_row(
            module,
            migration_row=migration_by_module.get(str(module.get("module_id") or ""), {}),
        )
        for module in modules
    ]
    blocker_counts = _count_row_blockers(rows, "blockers")
    warning_counts = _count_row_blockers(rows, "warnings")
    return {
        "schema_version": "biomedpilot.analysis.task_system_boundary_matrix.v1",
        "status": "passed" if rows and not blocker_counts else "blocked",
        "module_count": len(rows),
        "passed_module_count": sum(1 for row in rows if row.get("status") == "passed"),
        "blocked_module_count": sum(1 for row in rows if row.get("status") != "passed"),
        "blocker_counts": blocker_counts,
        "warning_counts": warning_counts,
        "rows": rows,
        "boundary": "read_only_main_backend_task_system_boundary_diagnostics",
    }


def build_frontend_standard_package_consumption_matrix() -> dict[str, Any]:
    """Return read-only diagnostics for UI standard-package consumption."""

    rows = [
        _frontend_consumption_row(
            row_id="catalog_source_policy",
            title="Standard package catalog reads result-index package artifacts only",
            file_path="app/analysis_runtime/package_catalog.py",
            required_tokens=[
                "source_policy\": \"result_index_standard_result_package_artifacts_only\"",
                "It does not scan arbitrary folders",
                "standard_result_package_path_outside_project_root",
            ],
            consumer_surface="build_standard_analysis_package_catalog",
        ),
        _frontend_consumption_row(
            row_id="catalog_detail_policy",
            title="Standard package detail reads declared package artifacts only",
            file_path="app/analysis_runtime/package_catalog.py",
            required_tokens=[
                "build_standard_analysis_package_detail",
                "does not inspect module-private output folders",
                "standard_result_package_declared_artifacts_and_logs_only",
            ],
            consumer_surface="build_standard_analysis_package_detail",
        ),
        _frontend_consumption_row(
            row_id="analysis_center_state",
            title="Analysis Center exposes standard package catalog and gates",
            file_path="app/bioinformatics/analysis_ui/state.py",
            required_tokens=[
                "standard_analysis_packages",
                "standard_package_gate_rows",
                "build_result_gate_rows",
            ],
            consumer_surface="build_analysis_center_state",
        ),
        _frontend_consumption_row(
            row_id="results_browser_tables",
            title="Results Browser renders standard package provenance, manifest, input, and artifact tables",
            file_path="app/bioinformatics/workflow_pages.py",
            required_tokens=[
                "resultsStandardPackageProvenanceTable",
                "resultsStandardPackageManifestTable",
                "resultsStandardPackageInputManifestTable",
                "resultsStandardPackageArtifactTable",
            ],
            consumer_surface="BioinformaticsResultsBrowserWidget",
        ),
        {
            "row_id": "detailed_result_views_migration",
            "title": "Detailed result views still need standard-package-only migration",
            "status": "partial",
            "file_path": "app/bioinformatics/workflow_pages.py",
            "consumer_surface": "module_specific_detailed_result_views",
            "source_policy": "transitional_legacy_detail_views_must_not_be_formal_readiness_evidence",
            "blockers": [],
            "warnings": ["detailed_result_views_still_need_standard_package_only_migration"],
        },
    ]
    blocker_counts = _count_row_blockers(rows, "blockers")
    warning_counts = _count_row_blockers(rows, "warnings")
    status_counts = _count_row_values(rows, "status")
    return {
        "schema_version": "biomedpilot.analysis.frontend_standard_package_consumption_matrix.v1",
        "status": "blocked" if blocker_counts else ("partial" if warning_counts else "passed"),
        "consumer_count": len(rows),
        "passed_consumer_count": sum(1 for row in rows if row.get("status") == "passed"),
        "partial_consumer_count": sum(1 for row in rows if row.get("status") == "partial"),
        "blocked_consumer_count": sum(1 for row in rows if row.get("status") == "blocked"),
        "status_counts": status_counts,
        "blocker_counts": blocker_counts,
        "warning_counts": warning_counts,
        "rows": rows,
        "boundary": "read_only_frontend_standard_package_consumption_diagnostics",
    }


def _frontend_consumption_row(
    *,
    row_id: str,
    title: str,
    file_path: str,
    required_tokens: list[str],
    consumer_surface: str,
) -> dict[str, Any]:
    path = REPO_ROOT / file_path
    text = path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""
    blockers: list[str] = []
    if not path.is_file():
        blockers.append(f"frontend_consumption_file_missing:{file_path}")
    for token in required_tokens:
        if token not in text:
            blockers.append(f"frontend_consumption_required_token_missing:{row_id}:{token}")
    return {
        "row_id": row_id,
        "title": title,
        "status": "blocked" if blockers else "passed",
        "file_path": file_path,
        "consumer_surface": consumer_surface,
        "source_policy": "consume_result_index_registered_standard_result_packages_only",
        "required_tokens": required_tokens,
        "blockers": blockers,
        "warnings": [],
    }


def _task_system_boundary_row(module: dict[str, Any], *, migration_row: dict[str, Any]) -> dict[str, Any]:
    module_id = str(module.get("module_id") or "")
    modes = module.get("modes") if isinstance(module.get("modes"), dict) else {}
    mock = modes.get("mock") if isinstance(modes.get("mock"), dict) else {}
    lite = modes.get("lite") if isinstance(modes.get("lite"), dict) else {}
    full = modes.get("full") if isinstance(modes.get("full"), dict) else {}
    result_index_task_types = [str(item) for item in module.get("result_index_task_types", []) if item]
    blockers: list[str] = []
    warnings: list[str] = []
    required_paths = {
        "task_bridge": "app/analysis_runtime/task_bridge.py",
        "task_center_service": "app/shared/task_center/service.py",
        "worker_invocation_schema": "analysis/schemas/output/worker_invocation.schema.json",
        "input_schema": str(module.get("input_schema") or "analysis/schemas/input/module_input.schema.json"),
        "result_package_schema": str(module.get("result_package_contract") or "analysis/schemas/output/result_package.schema.json"),
        "result_registry": "app/bioinformatics/results/registry.py",
    }
    for key, path in required_paths.items():
        if not path or not (REPO_ROOT / path).is_file():
            blockers.append(f"task_system_boundary_required_path_missing:{module_id}:{key}:{path}")
    if not result_index_task_types:
        blockers.append(f"task_system_boundary_result_index_task_types_missing:{module_id}")
    if mock.get("supported") is not True:
        blockers.append(f"task_system_boundary_mock_mode_missing:{module_id}")
    if "supported" not in lite:
        blockers.append(f"task_system_boundary_lite_mode_declaration_missing:{module_id}")
    if "supported" not in full:
        blockers.append(f"task_system_boundary_full_mode_declaration_missing:{module_id}")
    current_adapter_status = str(module.get("current_adapter_status") or "")
    formal_worker_status = str(migration_row.get("formal_worker_status") or "pending_standard_worker_migration")
    if formal_worker_status != "migrated_to_isolated_standard_worker":
        warnings.append(f"formal_worker_migration_pending:{module_id}")
    if "legacy" in current_adapter_status or "sidecar" in current_adapter_status:
        warnings.append(f"legacy_sidecar_boundary_transitional:{module_id}")
    elif "pending" in current_adapter_status or "existing" in current_adapter_status or "planned" in current_adapter_status:
        warnings.append(f"current_adapter_pending_standard_worker_migration:{module_id}")
    return {
        "module_id": module_id,
        "title": str(module.get("title") or module_id),
        "status": "blocked" if blockers else "passed",
        "current_adapter_status": current_adapter_status,
        "formal_worker_status": formal_worker_status,
        "task_bridge_entrypoint": "app/analysis_runtime/task_bridge.py::run_analysis_module_task",
        "task_center_service": "app/shared/task_center/service.py::TaskCenter",
        "worker_invocation_schema": "analysis/schemas/output/worker_invocation.schema.json",
        "input_schema": required_paths["input_schema"],
        "result_package_schema": required_paths["result_package_schema"],
        "result_index_task_types": result_index_task_types,
        "mock_task_bridge_supported": bool(mock.get("supported")),
        "lite_task_bridge_supported": bool(lite.get("supported")),
        "lite_worker_backend": str(lite.get("worker_backend") or ""),
        "full_task_bridge_policy": "blocked_before_worker_until_full_ready",
        "required_task_system_invocation": "task_center_registered",
        "worker_invocation_manifest_required": True,
        "direct_cli_is_not_ui_task_result": True,
        "legacy_sidecar_is_transitional_only": True,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_full_activation_module_matrix(
    *,
    registry: dict[str, Any] | None = None,
    environment_validation: dict[str, Any] | None = None,
    resource_validation: dict[str, Any] | None = None,
    standard_worker_migration_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a module-by-module full activation blocker matrix.

    The matrix is diagnostic only. It does not relax the global full activation
    gate, execute workers, restore environments, lock resources, or register
    migration evidence.
    """

    payload = registry if isinstance(registry, dict) else load_analysis_module_registry()
    env_validation = environment_validation if isinstance(environment_validation, dict) else validate_analysis_environment_registry(module_registry=payload)
    resources = resource_validation if isinstance(resource_validation, dict) else validate_analysis_resource_manifest()
    migration_matrix = standard_worker_migration_matrix if isinstance(standard_worker_migration_matrix, dict) else build_standard_worker_migration_matrix(payload)
    modules = [
        item
        for item in payload.get("modules", [])
        if isinstance(item, dict) and item.get("module_id") in TARGET_MODULE_IDS
    ]
    migration_by_module = {
        str(row.get("module_id") or ""): row
        for row in migration_matrix.get("rows", [])
        if isinstance(row, dict) and row.get("module_id")
    }
    resource_templates = [
        item
        for item in resources.get("resource_lock_evidence_templates", [])
        if isinstance(item, dict)
    ]
    blocked_resource_ids = {str(item) for item in resources.get("blocked_resource_ids", []) if item}
    blocked_environment_ids = {str(item) for item in env_validation.get("blocked_environment_ids", []) if item}
    rows = [
        _full_activation_module_row(
            module,
            migration_row=migration_by_module.get(str(module.get("module_id") or ""), {}),
            resource_templates=resource_templates,
            blocked_resource_ids=blocked_resource_ids,
            blocked_environment_ids=blocked_environment_ids,
        )
        for module in modules
    ]
    blocker_counts = _count_row_blockers(rows, "blockers")
    status_counts = _count_row_values(rows, "status")
    return {
        "schema_version": "biomedpilot.analysis.full_activation_module_matrix.v1",
        "status": "eligible" if rows and all(row.get("status") == "eligible" for row in rows) else "blocked",
        "module_count": len(rows),
        "eligible_module_count": sum(1 for row in rows if row.get("status") == "eligible"),
        "blocked_module_count": sum(1 for row in rows if row.get("status") != "eligible"),
        "status_counts": status_counts,
        "blocker_counts": blocker_counts,
        "rows": rows,
        "boundary": "read_only_module_level_full_activation_diagnostics",
    }


def _full_activation_module_row(
    module: dict[str, Any],
    *,
    migration_row: dict[str, Any],
    resource_templates: list[dict[str, Any]],
    blocked_resource_ids: set[str],
    blocked_environment_ids: set[str],
) -> dict[str, Any]:
    module_id = str(module.get("module_id") or "")
    full_environment = str(module.get("full_environment") or "")
    required_resource_ids = [
        str(template.get("resource_id") or "")
        for template in resource_templates
        if module_id in {str(value) for value in template.get("approved_for_modules", []) if value is not None}
    ]
    required_resource_ids = [item for item in required_resource_ids if item]
    blocked_required_resources = [resource_id for resource_id in required_resource_ids if resource_id in blocked_resource_ids]
    environment_blockers: list[str] = []
    if not full_environment:
        environment_blockers.append(f"analysis_full_environment_missing:{module_id}")
    elif full_environment in blocked_environment_ids:
        environment_blockers.append(f"analysis_full_environment_lock_not_restored:{full_environment}")
    migration_blockers = [str(item) for item in migration_row.get("migration_blockers", []) if item]
    resource_blockers = [f"analysis_resource_not_locked:{resource_id}" for resource_id in blocked_required_resources]
    blockers = [*environment_blockers, *resource_blockers, *migration_blockers]
    return {
        "module_id": module_id,
        "title": str(module.get("title") or module_id),
        "status": "eligible" if not blockers else "blocked",
        "analysis_environment": str(module.get("analysis_environment") or ""),
        "full_environment": full_environment,
        "required_resource_ids": required_resource_ids,
        "blocked_required_resource_ids": blocked_required_resources,
        "environment_status": "passed" if not environment_blockers else "blocked",
        "resource_status": "not_required" if not required_resource_ids else ("passed" if not resource_blockers else "blocked"),
        "standard_worker_migration_status": str(migration_row.get("formal_worker_status") or "pending_standard_worker_migration"),
        "migration_next_action": str(migration_row.get("migration_next_action") or "inspect_migration_blockers"),
        "blockers": list(dict.fromkeys(blockers)),
    }


def build_full_analysis_activation_gate(
    *,
    environment_validation: dict[str, Any] | None = None,
    resource_validation: dict[str, Any] | None = None,
    standard_worker_migration_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Combine full-mode prerequisites into one read-only activation gate."""

    env = environment_validation if isinstance(environment_validation, dict) else validate_analysis_environment_registry()
    resources = resource_validation if isinstance(resource_validation, dict) else validate_analysis_resource_manifest()
    matrix = standard_worker_migration_matrix if isinstance(standard_worker_migration_matrix, dict) else build_standard_worker_migration_matrix()
    checks = {
        "environment_registry_passed": env.get("status") == "passed",
        "full_environment_locks_ready": env.get("full_mode_ready") is True,
        "resource_manifest_passed": resources.get("status") == "passed",
        "full_resource_locks_ready": resources.get("full_mode_ready") is True,
        "standard_worker_migration_registry_passed": matrix.get("evidence_registry_status") == "passed",
        "all_modules_migrated_to_standard_worker": matrix.get("status") == "passed"
        and int(matrix.get("formal_pending_count") or 0) == 0
        and int(matrix.get("full_blocked_count") or 0) == 0,
    }
    blockers: list[str] = []
    if not checks["environment_registry_passed"]:
        blockers.append("full_analysis_environment_registry_failed")
    if not checks["full_environment_locks_ready"]:
        blockers.append("full_analysis_environment_locks_not_ready")
    if not checks["resource_manifest_passed"]:
        blockers.append("full_analysis_resource_manifest_failed")
    if not checks["full_resource_locks_ready"]:
        blockers.append("full_analysis_resource_locks_not_ready")
    if not checks["standard_worker_migration_registry_passed"]:
        blockers.append("full_analysis_standard_worker_evidence_registry_failed")
    if not checks["all_modules_migrated_to_standard_worker"]:
        blockers.append("full_analysis_standard_worker_migration_incomplete")
    payload = {
        "schema_version": "biomedpilot.analysis.full_analysis_activation_gate.v1",
        "status": "eligible" if not blockers else "blocked",
        "checks": checks,
        "blockers": blockers,
        "policy": "full_analysis_requires_environment_resource_and_standard_worker_evidence",
        "execution_policy": "read_only_no_worker_execution_no_runtime_install_no_resource_download",
    }
    schema_blockers = _full_activation_gate_schema_blockers(payload)
    payload["schema_validation_status"] = "blocked" if schema_blockers else "passed"
    payload["schema_blockers"] = schema_blockers
    if schema_blockers and "full_analysis_activation_gate_schema_invalid" not in payload["blockers"]:
        payload["blockers"] = [*payload["blockers"], "full_analysis_activation_gate_schema_invalid"]
        payload["status"] = "blocked"
    return payload


def build_standard_worker_migration_matrix(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Summarize module-by-module migration toward the standard worker boundary."""

    payload = registry if isinstance(registry, dict) else load_analysis_module_registry()
    evidence_registry = load_standard_worker_migration_evidence_registry()
    evidence_registry_validation = validate_standard_worker_migration_evidence_registry(evidence_registry, registry=payload)
    valid_evidence_by_module = {
        str(item.get("module_id") or ""): item
        for item in evidence_registry_validation.get("entries", [])
        if isinstance(item, dict) and item.get("status") == "passed"
    }
    modules = [item for item in payload.get("modules", []) if isinstance(item, dict)]
    standard_entrypoint = str(payload.get("standard_entrypoint") or "analysis/runners/run_module.R")
    rows = [
        _standard_worker_migration_row(
            module,
            standard_entrypoint=standard_entrypoint,
            valid_evidence_by_module=valid_evidence_by_module,
        )
        for module in modules
    ]
    formal_pending = [row for row in rows if row["formal_worker_status"] != "migrated_to_isolated_standard_worker"]
    full_blocked = [row for row in rows if row["full_status"] == "blocked"]
    adapter_status_counts = _count_row_values(rows, "current_adapter_status")
    migration_next_action_counts = _count_row_values(rows, "migration_next_action")
    migration_blocker_counts = _count_row_blockers(rows, "migration_blockers")
    return {
        "schema_version": "biomedpilot.analysis.standard_worker_migration_matrix.v1",
        "status": "passed" if not formal_pending and not full_blocked else "partial",
        "standard_entrypoint": standard_entrypoint,
        "module_count": len(rows),
        "formal_pending_count": len(formal_pending),
        "full_blocked_count": len(full_blocked),
        "adapter_status_counts": adapter_status_counts,
        "migration_next_action_counts": migration_next_action_counts,
        "migration_blocker_counts": migration_blocker_counts,
        "rows": rows,
        "evidence_registry_status": str(evidence_registry_validation.get("status") or "blocked"),
        "evidence_entry_count": int(evidence_registry_validation.get("entry_count") or 0),
        "evidence_registry_blockers": list(evidence_registry_validation.get("blockers", [])),
        "expected_evidence_module_ids": list(evidence_registry_validation.get("expected_module_ids", [])),
        "passed_evidence_module_ids": list(evidence_registry_validation.get("passed_module_ids", [])),
        "blocked_evidence_module_ids": list(evidence_registry_validation.get("blocked_module_ids", [])),
        "missing_evidence_module_ids": list(evidence_registry_validation.get("missing_module_ids", [])),
        "migration_policy": "module_by_module_standard_worker_migration_required",
        "boundary": "matrix_is_read_only_no_worker_execution",
    }


def _count_row_values(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(field) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _count_row_blockers(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for value in row.get(field, []) or []:
            key = str(value)
            if key:
                counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def load_standard_worker_migration_evidence_registry(path: str | Path | None = None) -> dict[str, Any]:
    registry_path = Path(path).expanduser().resolve() if path else STANDARD_WORKER_MIGRATION_EVIDENCE_REGISTRY_PATH
    return _read_json(registry_path)


def validate_standard_worker_migration_evidence_registry(
    evidence_registry: dict[str, Any] | None = None,
    *,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate the centralized standard-worker migration evidence registry."""

    payload = evidence_registry if isinstance(evidence_registry, dict) else load_standard_worker_migration_evidence_registry()
    module_registry = registry if isinstance(registry, dict) else load_analysis_module_registry()
    blockers: list[str] = []
    warnings: list[str] = []
    entries = payload.get("evidence_entries")
    schema_blockers = _migration_evidence_registry_schema_blockers(payload)
    blockers.extend(schema_blockers)
    module_ids = [
        str(item.get("module_id") or "")
        for item in module_registry.get("modules", [])
        if isinstance(item, dict) and item.get("module_id")
    ]
    expected_module_ids = [module_id for module_id in TARGET_MODULE_IDS if module_id in set(module_ids)]
    if payload.get("schema_version") != "biomedpilot.analysis.standard_worker_migration_evidence_registry.v1":
        blockers.append("standard_worker_migration_evidence_registry_schema_version_mismatch")
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
    if policy.get("registry_is_authoritative") is not True:
        blockers.append("standard_worker_migration_evidence_registry_authoritative_policy_invalid")
    if policy.get("expected_module_ids_are_authoritative") is not True:
        blockers.append("standard_worker_migration_evidence_registry_expected_module_policy_invalid")
    if policy.get("migration_completion_requires_schema_valid_evidence") is not True:
        blockers.append("standard_worker_migration_evidence_registry_schema_policy_invalid")
    if policy.get("mock_lite_and_legacy_sidecar_evidence_forbidden") is not True:
        blockers.append("standard_worker_migration_evidence_registry_sidecar_policy_invalid")
    declared_expected_module_ids = payload.get("expected_module_ids")
    if not isinstance(declared_expected_module_ids, list):
        blockers.append("standard_worker_migration_evidence_registry_expected_module_ids_invalid")
        declared_expected_module_ids = []
    else:
        normalized_expected_module_ids = [
            str(item)
            for item in declared_expected_module_ids
            if isinstance(item, str) and item
        ]
        if len(normalized_expected_module_ids) != len(declared_expected_module_ids):
            blockers.append("standard_worker_migration_evidence_registry_expected_module_ids_invalid")
        duplicate_expected_ids = sorted(
            module_id
            for module_id in set(normalized_expected_module_ids)
            if normalized_expected_module_ids.count(module_id) > 1
        )
        blockers.extend(
            f"standard_worker_migration_evidence_registry_expected_module_id_duplicate:{module_id}"
            for module_id in duplicate_expected_ids
        )
        if normalized_expected_module_ids != expected_module_ids:
            blockers.append("standard_worker_migration_evidence_registry_expected_module_ids_mismatch")
    if not isinstance(entries, list):
        blockers.append("standard_worker_migration_evidence_registry_entries_invalid")
        entries = []

    seen: set[str] = set()
    entry_results: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            blockers.append("standard_worker_migration_evidence_registry_entry_invalid")
            continue
        module_id = str(entry.get("module_id") or "")
        if not module_id:
            blockers.append("standard_worker_migration_evidence_registry_entry_module_id_missing")
        elif module_id in seen:
            blockers.append(f"standard_worker_migration_evidence_registry_entry_duplicate:{module_id}")
        elif module_id not in expected_module_ids:
            blockers.append(f"standard_worker_migration_evidence_registry_entry_unexpected_module:{module_id}")
        seen.add(module_id)
        evidence = entry.get("evidence") if isinstance(entry.get("evidence"), dict) else {}
        if not evidence:
            validation = {
                "schema_version": "biomedpilot.analysis.standard_worker_migration_evidence.v1",
                "status": "blocked",
                "module_id": module_id,
                "blockers": ["standard_worker_migration_evidence_registry_entry_evidence_missing"],
                "warnings": [],
            }
        else:
            validation = validate_standard_worker_migration_evidence(module_id, evidence, registry=module_registry)
        if validation.get("status") != "passed":
            blockers.extend(
                f"standard_worker_migration_evidence_registry_entry:{module_id}:{blocker}"
                for blocker in validation.get("blockers", [])
            )
        entry_results.append(
            {
                "module_id": module_id,
                "status": str(validation.get("status") or "blocked"),
                "blockers": list(validation.get("blockers", [])),
                "warnings": list(validation.get("warnings", [])),
            }
        )
    passed_module_ids = sorted(
        str(item.get("module_id") or "")
        for item in entry_results
        if item.get("module_id") and item.get("status") == "passed"
    )
    blocked_module_ids = sorted(
        str(item.get("module_id") or "")
        for item in entry_results
        if item.get("module_id") and item.get("status") != "passed"
    )
    missing_module_ids = [module_id for module_id in expected_module_ids if module_id not in set(passed_module_ids)]
    return {
        "schema_version": "biomedpilot.analysis.standard_worker_migration_evidence_registry_validation.v1",
        "status": "blocked" if blockers else "passed",
        "entry_count": len(entries),
        "entries": entry_results,
        "expected_module_ids": expected_module_ids,
        "passed_module_ids": passed_module_ids,
        "blocked_module_ids": blocked_module_ids,
        "missing_module_ids": missing_module_ids,
        "missing_count": len(missing_module_ids),
        "schema_validation_status": "blocked" if schema_blockers else "passed",
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": warnings,
    }


def build_analysis_remediation_queue(status: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic, read-only remediation queue for architecture gaps.

    The queue is advisory. It does not execute workers, mutate project storage,
    install packages, download resources, or mark full mode as ready.
    """

    snapshot = status if isinstance(status, dict) else build_analysis_architecture_status()
    p1_issues = [str(item) for item in snapshot.get("p1_issues", []) if item]
    migration_matrix = snapshot.get("standard_worker_migration_matrix") if isinstance(snapshot.get("standard_worker_migration_matrix"), dict) else {}
    environment_validation = snapshot.get("environment_validation") if isinstance(snapshot.get("environment_validation"), dict) else {}
    resource_validation = snapshot.get("resource_validation") if isinstance(snapshot.get("resource_validation"), dict) else {}
    migration_module_scope = {
        "expected_module_ids": list(migration_matrix.get("expected_evidence_module_ids", [])),
        "passed_module_ids": list(migration_matrix.get("passed_evidence_module_ids", [])),
        "blocked_module_ids": list(migration_matrix.get("blocked_evidence_module_ids", [])),
        "missing_module_ids": list(migration_matrix.get("missing_evidence_module_ids", [])),
        "missing_count": len(migration_matrix.get("missing_evidence_module_ids", [])),
        "scope_policy": "module_by_module_standard_worker_migration_required",
    }
    migration_module_actions = _standard_worker_migration_remediation_actions(migration_matrix)
    migration_action_summary = _standard_worker_migration_action_summary(migration_module_actions)
    environment_actions = _full_environment_lock_remediation_actions(environment_validation)
    environment_action_summary = _full_environment_lock_action_summary(environment_actions)
    resource_actions = _full_resource_lock_remediation_actions(resource_validation)
    resource_action_summary = _full_resource_lock_action_summary(resource_actions)
    issue_items = {
        "full_analysis_environment_locks_not_restored": {
            "item_id": "restore_full_analysis_environment_locks",
            "title": "Restore full analysis environment locks",
            "source_issue": "full_analysis_environment_locks_not_restored",
            "priority": "P1",
            "status": "blocked",
            "recommended_files": [
                "analysis/registry/analysis_environments.json",
                "analysis/registry/environment_lock_evidence.json",
                "renv/renv.bio-full.lock",
                "renv/renv.spatial-full.lock",
                "renv/renv.chem-full.lock",
                "analysis/schemas/output/environment_lock_evidence.schema.json",
                "analysis/schemas/output/environment_lock_evidence_registry.schema.json",
                "external_analysis_environments/",
                "docker/Dockerfile.r-bio-full",
                "docker/Dockerfile.r-spatial-full",
                "docker/Dockerfile.r-chem-full",
                "docker/Dockerfile.r-chem-gpu",
            ],
            "required_evidence": [
                "full environment locks restored from controlled external analysis environments",
                "each restored full environment lock has schema-valid environment_lock_evidence",
                "Docker image build evidence captured outside default app-dev",
                "validate_analysis_environment_registry.full_mode_ready becomes true",
            ],
            "boundary": "detect-first external full environments only; default app-dev remains lightweight",
            "environment_next_actions": environment_actions,
            "environment_action_summary": environment_action_summary,
        },
        "full_analysis_resource_locks_not_complete": {
            "item_id": "lock_full_analysis_resources",
            "title": "Lock full analysis resources",
            "source_issue": "full_analysis_resource_locks_not_complete",
            "priority": "P1",
            "status": "blocked",
            "recommended_files": [
                "analysis/resources/manifest.json",
                "analysis/registry/resource_lock_evidence.json",
                "analysis/schemas/output/resource_lock_evidence.schema.json",
                "analysis/schemas/output/resource_lock_evidence_registry.schema.json",
                "analysis/resources/locks/",
                "external_analysis_resources/",
            ],
            "required_evidence": [
                "each full resource declares version, source, hash, license, and cache path",
                "each locked full resource has schema-valid resource_lock_evidence",
                "large resources are prelocked or explicitly imported before full mode",
                "validate_analysis_resource_manifest.full_mode_ready becomes true",
            ],
            "boundary": "resource lock only; no runtime database fetch in user request flow",
            "resource_next_actions": resource_actions,
            "resource_action_summary": resource_action_summary,
        },
        "formal_algorithms_not_universally_migrated_to_isolated_standard_worker": {
            "item_id": "migrate_formal_algorithms_to_isolated_standard_worker",
            "title": "Migrate formal algorithms to isolated standard worker",
            "source_issue": "formal_algorithms_not_universally_migrated_to_isolated_standard_worker",
            "priority": "P1",
            "status": "blocked",
            "recommended_files": [
                "app/bioinformatics/",
                "analysis/registry/standard_worker_migration_evidence.json",
                "analysis/runners/run_module.R",
                "analysis/modules/",
                "analysis/schemas/input/module_input.schema.json",
                "analysis/schemas/output/standard_worker_migration_evidence.schema.json",
                "analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json",
                "analysis/schemas/output/result_package.schema.json",
            ],
            "required_evidence": [
                "selected formal module has registry-owned schema-valid standard worker migration evidence",
                "validate_standard_worker_migration_evidence.status=passed",
                "selected formal module has formal_worker_status=migrated_to_isolated_standard_worker",
                "selected formal module executes through the task bridge and standard worker boundary",
                "standard package includes result.json, provenance.json, tables, plots, reports, and logs",
                "frontend consumes the standard package instead of module-private output paths",
            ],
            "boundary": "one module at a time; sidecar-only legacy adapter output is not full migration",
            "module_scope": migration_module_scope,
            "module_next_actions": migration_module_actions,
            "module_action_summary": migration_action_summary,
        },
    }
    items = [issue_items[issue] for issue in p1_issues if issue in issue_items]
    payload = {
        "schema_version": "biomedpilot.analysis.remediation_queue.v1",
        "status": "open" if items else "empty",
        "source_status": str(snapshot.get("status") or ""),
        "item_count": len(items),
        "items": items,
        "automation_policy": "manual_scoped_changes_only",
        "execution_policy": "read_only_no_runtime_mutation",
        "install_policy": "no_runtime_package_install_or_resource_download",
        "full_mode_policy": "full_mode_remains_blocked_until_environment_and_resource_evidence_passes",
    }
    schema_blockers = _remediation_queue_schema_blockers(payload)
    payload["schema_validation_status"] = "blocked" if schema_blockers else "passed"
    payload["schema_blockers"] = schema_blockers
    if schema_blockers:
        payload["status"] = "blocked"
    return payload


def _full_environment_lock_remediation_actions(environment_validation: dict[str, Any]) -> list[dict[str, Any]]:
    templates = [
        item
        for item in environment_validation.get("environment_lock_evidence_templates", [])
        if isinstance(item, dict)
    ]
    blocked_ids = {str(item) for item in environment_validation.get("blocked_environment_ids", []) if item}
    actions: list[dict[str, Any]] = []
    for template in templates:
        environment_id = str(template.get("environment_id") or "")
        if environment_id and environment_id not in blocked_ids:
            continue
        docker_image = template.get("docker_image") if isinstance(template.get("docker_image"), dict) else {}
        package_lock_hash = template.get("package_lock_hash") if isinstance(template.get("package_lock_hash"), dict) else {}
        actions.append(
            {
                "environment_id": environment_id,
                "status": "blocked",
                "next_action": "register_schema_valid_restored_environment_evidence",
                "allowed_module_ids": [str(item) for item in template.get("allowed_module_ids", []) if item],
                "dockerfile": str(template.get("dockerfile") or ""),
                "renv_lock": str(template.get("renv_lock") or ""),
                "evidence_files": [str(item) for item in template.get("evidence_files", []) if item],
                "runtime_package_install": str(template.get("runtime_package_install") or ""),
                "runtime_resource_download": str(template.get("runtime_resource_download") or ""),
                "required_package_lock_hash_algorithm": str(package_lock_hash.get("algorithm") or "sha256"),
                "required_docker_image_status": str(docker_image.get("build_status") or "built"),
                "required_docker_image_digest_algorithm": str((docker_image.get("digest") if isinstance(docker_image.get("digest"), dict) else {}).get("algorithm") or "sha256"),
                "required_docker_build_log": str(docker_image.get("build_log") or ""),
                "renv_lock_content": template.get("renv_lock_content") if isinstance(template.get("renv_lock_content"), dict) else {},
                "forbidden_evidence_sources": [str(item) for item in template.get("forbidden_evidence_sources", []) if item],
                "recommended_files": [
                    "analysis/registry/analysis_environments.json",
                    "analysis/registry/environment_lock_evidence.json",
                    "analysis/schemas/output/environment_lock_evidence.schema.json",
                    "analysis/schemas/output/environment_lock_evidence_registry.schema.json",
                    str(template.get("dockerfile") or ""),
                    str(template.get("renv_lock") or ""),
                    *[str(item) for item in template.get("evidence_files", []) if item],
                    str(docker_image.get("build_log") or ""),
                ],
            }
        )
    return actions


def _full_environment_lock_action_summary(actions: list[dict[str, Any]]) -> dict[str, Any]:
    module_environments: dict[str, list[str]] = {}
    for action in actions:
        for module_id in action.get("allowed_module_ids", []) or []:
            module_key = str(module_id)
            module_environments.setdefault(module_key, []).append(str(action.get("environment_id") or ""))
    return {
        "schema_version": "biomedpilot.analysis.environment_lock_action_summary.v1",
        "environment_count": len(actions),
        "blocked_environment_count": sum(1 for action in actions if action.get("status") == "blocked"),
        "module_environment_counts": {module_id: len(environments) for module_id, environments in sorted(module_environments.items())},
        "module_environments": {module_id: environments for module_id, environments in sorted(module_environments.items())},
        "next_action_counts": {
            "register_schema_valid_restored_environment_evidence": len(actions),
        },
    }


def _full_resource_lock_remediation_actions(resource_validation: dict[str, Any]) -> list[dict[str, Any]]:
    templates = [
        item
        for item in resource_validation.get("resource_lock_evidence_templates", [])
        if isinstance(item, dict)
    ]
    blocked_ids = {str(item) for item in resource_validation.get("blocked_resource_ids", []) if item}
    actions: list[dict[str, Any]] = []
    for template in templates:
        resource_id = str(template.get("resource_id") or "")
        if resource_id and resource_id not in blocked_ids:
            continue
        approved_modules = [str(item) for item in template.get("approved_for_modules", []) if item]
        cache_path = str(template.get("cache_path") or "")
        evidence_files = [str(item) for item in template.get("evidence_files", []) if item]
        actions.append(
            {
                "resource_id": resource_id,
                "status": "blocked",
                "next_action": "register_schema_valid_prelocked_resource_evidence",
                "required_for_modules": approved_modules,
                "cache_path": cache_path,
                "evidence_files": evidence_files,
                "runtime_download_allowed": template.get("runtime_download_allowed") is True,
                "required_hash_algorithm": str((template.get("hash") if isinstance(template.get("hash"), dict) else {}).get("algorithm") or "sha256"),
                "required_cache_content": template.get("cache_content") if isinstance(template.get("cache_content"), dict) else {},
                "forbidden_evidence_sources": [str(item) for item in template.get("forbidden_evidence_sources", []) if item],
                "recommended_files": [
                    "analysis/resources/manifest.json",
                    "analysis/registry/resource_lock_evidence.json",
                    "analysis/schemas/output/resource_lock_evidence.schema.json",
                    "analysis/schemas/output/resource_lock_evidence_registry.schema.json",
                    cache_path,
                    *evidence_files,
                ],
            }
        )
    return actions


def _full_resource_lock_action_summary(actions: list[dict[str, Any]]) -> dict[str, Any]:
    by_module: dict[str, list[str]] = {}
    for action in actions:
        for module_id in action.get("required_for_modules", []) or []:
            module_key = str(module_id)
            by_module.setdefault(module_key, []).append(str(action.get("resource_id") or ""))
    return {
        "schema_version": "biomedpilot.analysis.resource_lock_action_summary.v1",
        "resource_count": len(actions),
        "blocked_resource_count": sum(1 for action in actions if action.get("status") == "blocked"),
        "module_resource_counts": {module_id: len(resources) for module_id, resources in sorted(by_module.items())},
        "module_resources": {module_id: resources for module_id, resources in sorted(by_module.items())},
        "next_action_counts": {
            "register_schema_valid_prelocked_resource_evidence": len(actions),
        },
    }


def _standard_worker_migration_remediation_actions(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [row for row in matrix.get("rows", []) if isinstance(row, dict)]
    actions: list[dict[str, Any]] = []
    for row in rows:
        prerequisites = row.get("migration_prerequisite_status") if isinstance(row.get("migration_prerequisite_status"), dict) else {}
        actions.append(
            {
                "module_id": str(row.get("module_id") or ""),
                "title": str(row.get("title") or row.get("module_id") or ""),
                "priority": str(row.get("risk") or "P1"),
                "migration_readiness_status": str(row.get("migration_readiness_status") or "blocked"),
                "formal_worker_status": str(row.get("formal_worker_status") or ""),
                "migration_next_action": str(row.get("migration_next_action") or "inspect_migration_blockers"),
                "migration_blockers": [str(item) for item in row.get("migration_blockers", []) if item],
                "prerequisite_status": {
                    "overall": str(prerequisites.get("overall") or "blocked"),
                    "lite_standard_worker_path": str(prerequisites.get("lite_standard_worker_path") or ""),
                    "full_mode_registry": str(prerequisites.get("full_mode_registry") or ""),
                    "registry_evidence": str(prerequisites.get("registry_evidence") or ""),
                    "formal_runtime_contract": str(prerequisites.get("formal_runtime_contract") or ""),
                    "legacy_sidecar_boundary": str(prerequisites.get("legacy_sidecar_boundary") or ""),
                    "required_full_environment": str(prerequisites.get("required_full_environment") or ""),
                    "required_environment_lock": str(prerequisites.get("required_environment_lock") or ""),
                    "required_resource_lock": str(prerequisites.get("required_resource_lock") or ""),
                    "required_task_boundary": str(prerequisites.get("required_task_boundary") or ""),
                },
                "recommended_files": _standard_worker_migration_recommended_files(row),
            }
        )
    return actions


def _standard_worker_migration_action_summary(actions: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for action in actions:
        next_action = str(action.get("migration_next_action") or "inspect_migration_blockers")
        counts[next_action] = counts.get(next_action, 0) + 1
    return {
        "schema_version": "biomedpilot.analysis.standard_worker_migration_action_summary.v1",
        "module_count": len(actions),
        "next_action_counts": counts,
        "blocked_module_count": sum(1 for action in actions if action.get("migration_readiness_status") == "blocked"),
    }


def _standard_worker_migration_recommended_files(row: dict[str, Any]) -> list[str]:
    files = [
        "analysis/registry/standard_worker_migration_evidence.json",
        "analysis/schemas/output/standard_worker_migration_evidence.schema.json",
        "analysis/schemas/output/result_package.schema.json",
    ]
    module_id = str(row.get("module_id") or "")
    next_action = str(row.get("migration_next_action") or "")
    if module_id:
        files.append(f"analysis/modules/{module_id}/module.json")
    if next_action == "implement_formal_runtime_contract_before_standard_worker_migration":
        files.extend(["analysis/runners/run_module.R", "app/bioinformatics/"])
    elif next_action == "declare_scoped_full_mode_only_after_environment_and_resource_locks":
        files.extend(["analysis/registry/analysis_environments.json", "analysis/resources/manifest.json"])
    elif next_action == "replace_legacy_sidecar_with_task_center_registered_standard_worker_execution":
        files.extend(["app/analysis_runtime/task_bridge.py", "analysis/runners/run_module.R"])
    elif next_action == "register_schema_valid_standard_worker_migration_evidence":
        files.extend(["analysis/registry/standard_worker_migration_evidence.json", "analysis/standard_packages/"])
    return list(dict.fromkeys(files))


def validate_standard_worker_migration_evidence(
    module_id: str,
    evidence: dict[str, Any],
    *,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate evidence before a formal module can be marked worker-migrated."""

    payload = registry if isinstance(registry, dict) else load_analysis_module_registry()
    registered = {
        str(item.get("module_id") or ""): item
        for item in payload.get("modules", [])
        if isinstance(item, dict) and item.get("module_id")
    }
    blockers: list[str] = []
    warnings: list[str] = []
    blockers.extend(_migration_evidence_schema_blockers(evidence))
    module_key = str(module_id or evidence.get("module_id") or "")
    if module_key not in registered:
        blockers.append(f"standard_worker_migration_module_unregistered:{module_key}")
    if str(evidence.get("module_id") or module_key) != module_key:
        blockers.append("standard_worker_migration_evidence_module_id_mismatch")

    mode = str(evidence.get("mode") or "")
    if mode != "full":
        blockers.append("standard_worker_migration_requires_full_mode_standard_package")
    task_id = str(evidence.get("task_id") or "")
    if not task_id:
        blockers.append("standard_worker_migration_task_id_missing")

    package_dir = REPO_ROOT / str(evidence.get("result_package_dir") or "")
    if not str(evidence.get("result_package_dir") or ""):
        blockers.append("standard_worker_migration_result_package_dir_missing")
    elif not package_dir.is_dir():
        blockers.append("standard_worker_migration_result_package_dir_not_found")
    else:
        validation = validate_standard_result_package(package_dir, expected_module_id=module_key, expected_task_id=task_id, expected_mode=mode)
        if validation.get("status") != "passed":
            blockers.extend(f"standard_worker_migration_package_validation:{item}" for item in validation.get("blockers", []) or [])
        warnings.extend(f"standard_worker_migration_package_warning:{item}" for item in validation.get("warnings", []) or [])
        result = _read_json(package_dir / "result.json")
        provenance = _read_json(package_dir / "provenance.json")
        blockers.extend(_standard_worker_migration_result_blockers(result, provenance))
        invocation = _read_json(package_dir / "logs" / "worker_invocation.json")
        boundary = invocation.get("worker_boundary") if isinstance(invocation.get("worker_boundary"), dict) else {}
        if boundary.get("boundary_type") != "standard_r_worker":
            blockers.append("standard_worker_migration_requires_standard_r_worker_boundary")
        if boundary.get("task_system_invocation") != "task_center_registered":
            blockers.append("standard_worker_migration_requires_task_center_registered_invocation")
        if boundary.get("migration_status") != "standard_worker_contract":
            blockers.append("standard_worker_migration_requires_standard_worker_contract_status")
        if invocation.get("runtime_install_policy") != "forbidden":
            blockers.append("standard_worker_migration_runtime_install_policy_not_forbidden")
        if invocation.get("resource_download_policy") != "forbidden":
            blockers.append("standard_worker_migration_resource_download_policy_not_forbidden")

    if evidence.get("frontend_consumes_standard_package") is not True:
        blockers.append("standard_worker_migration_frontend_standard_package_consumption_missing")
    if evidence.get("result_index_registered") is not True:
        blockers.append("standard_worker_migration_result_index_registration_missing")
    if evidence.get("formal_result_semantics_preserved") is not True:
        blockers.append("standard_worker_migration_formal_result_semantics_not_preserved")
    if evidence.get("required_worker_boundary") != "standard_r_worker":
        blockers.append("standard_worker_migration_required_worker_boundary_invalid")
    if evidence.get("required_task_system_invocation") != "task_center_registered":
        blockers.append("standard_worker_migration_required_task_system_invocation_invalid")
    if evidence.get("required_worker_migration_status") != "standard_worker_contract":
        blockers.append("standard_worker_migration_required_worker_migration_status_invalid")
    forbidden_sources = evidence.get("forbidden_evidence_sources")
    if not isinstance(forbidden_sources, list):
        blockers.append("standard_worker_migration_forbidden_evidence_sources_invalid")
        forbidden_source_values: set[str] = set()
    else:
        forbidden_source_values = {str(item) for item in forbidden_sources if item}
    required_forbidden_sources = {
        "mock_fixture_package",
        "lite_testing_level_package",
        "legacy_service_adapter_sidecar",
        "module_private_output_path",
    }
    missing_forbidden_sources = sorted(required_forbidden_sources - forbidden_source_values)
    blockers.extend(
        f"standard_worker_migration_forbidden_evidence_source_missing:{item}"
        for item in missing_forbidden_sources
    )

    return {
        "schema_version": "biomedpilot.analysis.standard_worker_migration_evidence.v1",
        "status": "blocked" if blockers else "passed",
        "module_id": module_key,
        "mode": mode,
        "result_package_dir": str(evidence.get("result_package_dir") or ""),
        "blockers": blockers,
        "warnings": warnings,
        "required_boundary": "standard_r_worker",
        "required_invocation": "task_center_registered",
        "required_migration_status": "standard_worker_contract",
    }


def _standard_worker_migration_result_blockers(result: dict[str, Any], provenance: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if result.get("status") != "passed":
        blockers.append("standard_worker_migration_requires_passed_result")
    if result.get("result_semantics") != "formal_computed_result":
        blockers.append("standard_worker_migration_requires_formal_computed_result")
    result_blockers = result.get("blockers")
    if not isinstance(result_blockers, list):
        blockers.append("standard_worker_migration_result_blockers_invalid")
    elif result_blockers:
        blockers.append("standard_worker_migration_result_blockers_present")

    engine = provenance.get("engine") if isinstance(provenance.get("engine"), dict) else {}
    if engine.get("name") != "biomedpilot_standard_r_worker":
        blockers.append("standard_worker_migration_requires_standard_worker_engine")

    environment = provenance.get("analysis_environment")
    if not isinstance(environment, dict):
        blockers.append("standard_worker_migration_analysis_environment_missing")
        return blockers
    if environment.get("mode") != "full":
        blockers.append("standard_worker_migration_analysis_environment_mode_not_full")
    if environment.get("status") != "passed":
        blockers.append("standard_worker_migration_analysis_environment_not_ready")
    environment_lock_status = environment.get("environment_lock_status")
    if not isinstance(environment_lock_status, dict) or environment_lock_status.get("ready") is not True:
        blockers.append("standard_worker_migration_environment_lock_not_ready")
    elif environment_lock_status.get("blockers"):
        blockers.append("standard_worker_migration_environment_lock_blockers_present")
    resource_lock_status = environment.get("resource_lock_status")
    if not isinstance(resource_lock_status, dict) or resource_lock_status.get("full_mode_ready") is not True:
        blockers.append("standard_worker_migration_resource_lock_not_ready")
    elif resource_lock_status.get("blockers"):
        blockers.append("standard_worker_migration_resource_lock_blockers_present")
    return blockers


def _migration_evidence_schema_blockers(evidence: dict[str, Any]) -> list[str]:
    schema = _read_json(STANDARD_WORKER_MIGRATION_EVIDENCE_SCHEMA_PATH)
    blockers: list[str] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field in required:
        if isinstance(field, str) and field not in evidence:
            blockers.append(f"standard_worker_migration_evidence_required_field_missing:{field}")
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in evidence or not isinstance(field_schema, dict):
            continue
        value = evidence[field]
        if "const" in field_schema and value != field_schema["const"]:
            blockers.append(f"standard_worker_migration_evidence_const_mismatch:{field}")
        expected_type = field_schema.get("type")
        if isinstance(expected_type, str) and not _schema_type_matches(value, expected_type):
            blockers.append(f"standard_worker_migration_evidence_type_invalid:{field}")
            continue
        min_length = field_schema.get("minLength")
        if isinstance(min_length, int) and isinstance(value, str) and len(value) < min_length:
            blockers.append(f"standard_worker_migration_evidence_min_length_invalid:{field}")
    return blockers


def _full_activation_gate_schema_blockers(payload: dict[str, Any]) -> list[str]:
    schema = _read_json(FULL_ANALYSIS_ACTIVATION_GATE_SCHEMA_PATH)
    blockers: list[str] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field in required:
        if isinstance(field, str) and field not in payload:
            blockers.append(f"full_analysis_activation_gate_required_field_missing:{field}")
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in payload or not isinstance(field_schema, dict):
            continue
        value = payload[field]
        if "const" in field_schema and value != field_schema["const"]:
            blockers.append(f"full_analysis_activation_gate_const_mismatch:{field}")
        expected_type = field_schema.get("type")
        if isinstance(expected_type, str) and not _schema_type_matches(value, expected_type):
            blockers.append(f"full_analysis_activation_gate_type_invalid:{field}")
            continue
        min_length = field_schema.get("minLength")
        if isinstance(min_length, int) and isinstance(value, str) and len(value) < min_length:
            blockers.append(f"full_analysis_activation_gate_min_length_invalid:{field}")
    return blockers


def _remediation_queue_schema_blockers(payload: dict[str, Any]) -> list[str]:
    schema = _read_json(REMEDIATION_QUEUE_SCHEMA_PATH)
    blockers: list[str] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field in required:
        if isinstance(field, str) and field not in payload:
            blockers.append(f"analysis_remediation_queue_required_field_missing:{field}")
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in payload or not isinstance(field_schema, dict):
            continue
        value = payload[field]
        if "const" in field_schema and value != field_schema["const"]:
            blockers.append(f"analysis_remediation_queue_const_mismatch:{field}")
        expected_type = field_schema.get("type")
        if isinstance(expected_type, str) and not _schema_type_matches(value, expected_type):
            blockers.append(f"analysis_remediation_queue_type_invalid:{field}")
            continue
        min_length = field_schema.get("minLength")
        if isinstance(min_length, int) and isinstance(value, str) and len(value) < min_length:
            blockers.append(f"analysis_remediation_queue_min_length_invalid:{field}")
    return blockers


def _migration_evidence_registry_schema_blockers(payload: dict[str, Any]) -> list[str]:
    schema = _read_json(STANDARD_WORKER_MIGRATION_EVIDENCE_REGISTRY_SCHEMA_PATH)
    blockers: list[str] = []
    required = schema.get("required") if isinstance(schema.get("required"), list) else []
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for field in required:
        if isinstance(field, str) and field not in payload:
            blockers.append(f"standard_worker_migration_evidence_registry_required_field_missing:{field}")
    for field, field_schema in properties.items():
        if not isinstance(field, str) or field not in payload or not isinstance(field_schema, dict):
            continue
        value = payload[field]
        if "const" in field_schema and value != field_schema["const"]:
            blockers.append(f"standard_worker_migration_evidence_registry_const_mismatch:{field}")
        expected_type = field_schema.get("type")
        if isinstance(expected_type, str) and not _schema_type_matches(value, expected_type):
            blockers.append(f"standard_worker_migration_evidence_registry_type_invalid:{field}")
    return blockers


def _schema_type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return True


def _standard_worker_migration_row(
    module: dict[str, Any],
    *,
    standard_entrypoint: str,
    valid_evidence_by_module: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    module_id = str(module.get("module_id") or "")
    modes = module.get("modes") if isinstance(module.get("modes"), dict) else {}
    mock = modes.get("mock") if isinstance(modes.get("mock"), dict) else {}
    lite = modes.get("lite") if isinstance(modes.get("lite"), dict) else {}
    full = modes.get("full") if isinstance(modes.get("full"), dict) else {}
    mock_package = REPO_ROOT / str(mock.get("fixture_output_package") or "")
    mock_ready = bool(mock.get("supported")) and mock_package.joinpath("result.json").is_file() and mock_package.joinpath("provenance.json").is_file()
    lite_uses_standard_worker = (
        bool(lite.get("supported"))
        and str(lite.get("runner") or "") == standard_entrypoint
        and str(lite.get("worker_backend") or "") == "rscript"
    )
    full_supported = bool(full.get("supported"))
    current_adapter_status = str(module.get("current_adapter_status") or "")
    evidence_status = "passed" if module_id in valid_evidence_by_module else "missing"
    formal_worker_status = (
        "migrated_to_isolated_standard_worker"
        if full_supported and lite_uses_standard_worker and evidence_status == "passed"
        else "pending_standard_worker_migration"
    )
    if current_adapter_status.startswith("contract_required"):
        formal_worker_status = "contract_only_pending_standard_worker_migration"
    migration_blockers = _standard_worker_migration_blockers(
        full_supported=full_supported,
        lite_uses_standard_worker=lite_uses_standard_worker,
        evidence_status=evidence_status,
        current_adapter_status=current_adapter_status,
    )
    prerequisite_status = _standard_worker_migration_prerequisite_status(
        blockers=migration_blockers,
        formal_worker_status=formal_worker_status,
        full_environment=str(module.get("full_environment") or ""),
        current_adapter_status=current_adapter_status,
    )
    return {
        "module_id": module_id,
        "title": str(module.get("title") or module_id),
        "mock_status": "passed" if mock_ready else "blocked",
        "lite_status": "standard_worker_lite_ready" if lite_uses_standard_worker else "blocked",
        "full_status": "ready_unverified" if full_supported else "blocked",
        "formal_worker_status": formal_worker_status,
        "migration_evidence_status": evidence_status,
        "current_adapter_status": current_adapter_status,
        "standard_entrypoint": standard_entrypoint if lite_uses_standard_worker else "",
        "analysis_environment": str(module.get("analysis_environment") or ""),
        "full_environment": str(module.get("full_environment") or ""),
        "full_blocker": str(full.get("blocker") or ""),
        "result_index_task_types": [str(item) for item in module.get("result_index_task_types", []) if item],
        "migration_readiness_status": "blocked" if migration_blockers else "candidate_evidence_ready",
        "migration_blockers": migration_blockers,
        "migration_prerequisite_status": prerequisite_status,
        "migration_next_action": _standard_worker_migration_next_action(
            migration_blockers,
            formal_worker_status=formal_worker_status,
            current_adapter_status=current_adapter_status,
        ),
        "migration_evidence_template": _standard_worker_migration_evidence_template(
            module_id=module_id,
            current_adapter_status=current_adapter_status,
        ),
        "risk": "P1" if formal_worker_status != "migrated_to_isolated_standard_worker" else "none",
    }


def _standard_worker_migration_blockers(
    *,
    full_supported: bool,
    lite_uses_standard_worker: bool,
    evidence_status: str,
    current_adapter_status: str,
) -> list[str]:
    blockers: list[str] = []
    if not full_supported:
        blockers.append("full_mode_not_supported_in_registry")
    if not lite_uses_standard_worker:
        blockers.append("lite_standard_worker_path_missing")
    if evidence_status != "passed":
        blockers.append("registry_evidence_entry_missing_or_blocked")
    if current_adapter_status.startswith("contract_required"):
        blockers.append("formal_runtime_contract_not_implemented")
    if "sidecar" in current_adapter_status:
        blockers.append("legacy_sidecar_output_is_not_migration_evidence")
    return blockers


def _standard_worker_migration_prerequisite_status(
    *,
    blockers: list[str],
    formal_worker_status: str,
    full_environment: str,
    current_adapter_status: str,
) -> dict[str, Any]:
    return {
        "overall": "passed" if formal_worker_status == "migrated_to_isolated_standard_worker" and not blockers else "blocked",
        "lite_standard_worker_path": "blocked" if "lite_standard_worker_path_missing" in blockers else "passed",
        "full_mode_registry": "blocked" if "full_mode_not_supported_in_registry" in blockers else "ready_unverified",
        "registry_evidence": "missing_or_blocked" if "registry_evidence_entry_missing_or_blocked" in blockers else "passed",
        "formal_runtime_contract": "blocked" if "formal_runtime_contract_not_implemented" in blockers else "available_or_not_required",
        "legacy_sidecar_boundary": "not_migration_evidence" if "legacy_sidecar_output_is_not_migration_evidence" in blockers else "not_present",
        "required_full_environment": full_environment or "missing",
        "required_environment_lock": "passed" if formal_worker_status == "migrated_to_isolated_standard_worker" else "required_before_migration_evidence",
        "required_resource_lock": "passed" if formal_worker_status == "migrated_to_isolated_standard_worker" else "required_before_migration_evidence",
        "required_task_boundary": "task_center_registered_standard_r_worker",
        "current_adapter_status": current_adapter_status,
    }


def _standard_worker_migration_next_action(
    blockers: list[str],
    *,
    formal_worker_status: str,
    current_adapter_status: str,
) -> str:
    if formal_worker_status == "migrated_to_isolated_standard_worker" and not blockers:
        return "no_action_migration_evidence_passed"
    if "lite_standard_worker_path_missing" in blockers:
        return "add_lite_standard_worker_path_before_formal_migration"
    if "formal_runtime_contract_not_implemented" in blockers:
        return "implement_formal_runtime_contract_before_standard_worker_migration"
    if "full_mode_not_supported_in_registry" in blockers:
        return "declare_scoped_full_mode_only_after_environment_and_resource_locks"
    if "legacy_sidecar_output_is_not_migration_evidence" in blockers:
        return "replace_legacy_sidecar_with_task_center_registered_standard_worker_execution"
    if "registry_evidence_entry_missing_or_blocked" in blockers:
        return "register_schema_valid_standard_worker_migration_evidence"
    if current_adapter_status.startswith("planned_"):
        return "implement_scoped_worker_adapter_before_evidence_registration"
    return "inspect_migration_blockers"


def _standard_worker_migration_evidence_template(*, module_id: str, current_adapter_status: str) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.analysis.standard_worker_migration_evidence.v1",
        "module_id": module_id,
        "mode": "full",
        "task_id": "<task_center_task_id>",
        "result_package_dir": "analysis/standard_packages/<result_id>",
        "frontend_consumes_standard_package": False,
        "result_index_registered": False,
        "formal_result_semantics_preserved": False,
        "required_result_status": "passed",
        "required_result_semantics": "formal_computed_result",
        "required_engine_name": "biomedpilot_standard_r_worker",
        "required_analysis_environment_status": "passed",
        "required_worker_boundary": "standard_r_worker",
        "required_task_system_invocation": "task_center_registered",
        "required_worker_migration_status": "standard_worker_contract",
        "forbidden_evidence_sources": [
            "mock_fixture_package",
            "lite_testing_level_package",
            "legacy_service_adapter_sidecar",
            "module_private_output_path",
        ],
        "current_adapter_status": current_adapter_status,
    }


def _row(
    requirement_id: str,
    label: str,
    status: str,
    evidence: str,
    *,
    blockers: list[str] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "status": status,
        "evidence": evidence,
        "blockers": blockers or [],
        "warnings": warnings or [],
    }


def _all_module_dirs_exist(module_ids: list[str]) -> bool:
    return bool(module_ids) and all((REPO_ROOT / "analysis" / "modules" / module_id / "module.json").is_file() for module_id in module_ids)


def _all_modules_declare_modes(modules: list[dict[str, Any]]) -> bool:
    for module in modules:
        modes = module.get("modes") if isinstance(module.get("modes"), dict) else {}
        if not all(name in modes for name in ("mock", "full")):
            return False
    return bool(modules)


def _required_schemas_exist() -> bool:
    paths = (
        "analysis/schemas/input/module_input.schema.json",
        "analysis/schemas/output/result.schema.json",
        "analysis/schemas/output/provenance.schema.json",
        "analysis/schemas/output/result_package.schema.json",
        "analysis/schemas/output/worker_invocation.schema.json",
        "analysis/schemas/output/standard_worker_migration_evidence.schema.json",
        "analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json",
        "analysis/schemas/output/full_analysis_activation_gate.schema.json",
        "analysis/schemas/output/remediation_queue.schema.json",
        "analysis/schemas/output/resource_lock_evidence.schema.json",
        "analysis/schemas/output/resource_lock_evidence_registry.schema.json",
        "analysis/schemas/output/environment_lock_evidence.schema.json",
        "analysis/schemas/output/environment_lock_evidence_registry.schema.json",
    )
    return all((REPO_ROOT / path).is_file() for path in paths)


def _mock_packages_have_payloads(modules: list[dict[str, Any]]) -> bool:
    return all(_mock_package_path(module).joinpath("result.json").is_file() and _mock_package_path(module).joinpath("provenance.json").is_file() for module in modules)


def _mock_packages_have_directories(modules: list[dict[str, Any]]) -> bool:
    return all(all(_mock_package_path(module).joinpath(name).is_dir() for name in ("tables", "plots", "reports", "logs")) for module in modules)


def _mock_package_path(module: dict[str, Any]) -> Path:
    modes = module.get("modes") if isinstance(module.get("modes"), dict) else {}
    mock = modes.get("mock") if isinstance(modes.get("mock"), dict) else {}
    return REPO_ROOT / str(mock.get("fixture_output_package") or "")


def _path_exists(value: object) -> bool:
    return bool(value) and (REPO_ROOT / str(value)).exists()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _renv_locks_exist() -> bool:
    return all((REPO_ROOT / path).is_file() for path in ("renv/renv.app.lock", "renv/renv.bio-core.lock", "renv/renv.bio-full.lock", "renv/renv.spatial-full.lock", "renv/renv.chem-full.lock"))


def _dockerfiles_exist() -> bool:
    return all((REPO_ROOT / path).is_file() for path in ("docker/Dockerfile.app-dev", "docker/Dockerfile.r-bio-core", "docker/Dockerfile.r-bio-full", "docker/Dockerfile.r-spatial-full", "docker/Dockerfile.r-chem-full", "docker/Dockerfile.r-chem-gpu"))


def _chem_modules_use_external_tool_policy() -> bool:
    expected_full_environments = {
        "docking": "r-chem-full",
        "molecular_dynamics": "r-chem-gpu",
    }
    expected_tool_names = {
        "docking": "AutoDock_Vina",
        "molecular_dynamics": "GROMACS",
    }
    for module_id, expected_full_environment in expected_full_environments.items():
        path = REPO_ROOT / "analysis" / "modules" / module_id / "module.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        policy = str(payload.get("external_tool_policy") or "")
        modes = payload.get("modes") if isinstance(payload.get("modes"), dict) else {}
        lite = modes.get("lite") if isinstance(modes.get("lite"), dict) else {}
        if f"R_adapter_calls_{expected_tool_names[module_id]}" not in policy:
            return False
        if payload.get("full_environment") != expected_full_environment:
            return False
        if lite.get("environment") != "r-bio-core":
            return False
        if lite.get("external_tool_execution") != "not_executed_in_lite_mode":
            return False
    return True


def _active_runtime_install_hits() -> list[str]:
    return list(_active_runtime_command_scan(BANNED_RUNTIME_INSTALL_PATTERNS, scan_id="runtime_install_command_scan").get("hits", []))


def _active_runtime_resource_download_hits() -> list[str]:
    return list(_active_runtime_command_scan(BANNED_RUNTIME_RESOURCE_DOWNLOAD_PATTERNS, scan_id="runtime_resource_download_command_scan").get("hits", []))


def _active_runtime_command_scan(patterns: tuple[str, ...], *, scan_id: str) -> dict[str, Any]:
    roots = [REPO_ROOT / "app", REPO_ROOT / "analysis", REPO_ROOT / "scripts", REPO_ROOT / "config"]
    hits: list[str] = []
    scanned_files: list[str] = []
    skipped_non_text_files: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or _is_excluded_source(path):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                skipped_non_text_files.append(str(path.relative_to(REPO_ROOT)))
                continue
            scanned_files.append(str(path.relative_to(REPO_ROOT)))
            for pattern in patterns:
                if pattern in text:
                    hits.append(f"{path.relative_to(REPO_ROOT)}:{pattern}")
    return {
        "schema_version": "biomedpilot.analysis.active_runtime_command_scan.v1",
        "scan_id": scan_id,
        "status": "passed" if not hits else "blocked",
        "scanned_roots": [str(root.relative_to(REPO_ROOT)) for root in roots if root.exists()],
        "excluded_path_parts": ["legacy", "__pycache__", ".git"],
        "patterns": list(patterns),
        "scanned_file_count": len(scanned_files),
        "skipped_non_text_file_count": len(skipped_non_text_files),
        "skipped_non_text_files": skipped_non_text_files[:20],
        "hits": sorted(set(hits)),
        "hit_count": len(set(hits)),
    }


def _default_dependency_hits() -> list[str]:
    return list(build_default_dependency_scan_summary().get("heavy_dependency_hits", []))


def _is_excluded_source(path: Path) -> bool:
    parts = set(path.relative_to(REPO_ROOT).parts)
    return bool(parts & {"legacy", "__pycache__", ".git"})


def _p0_issues(rows: list[dict[str, Any]]) -> list[str]:
    p0_ids = {"RARCH-06", "RARCH-10", "RARCH-11", "RARCH-19"}
    return [f"{row['requirement_id']}:{row['label']}" for row in rows if row["requirement_id"] in p0_ids and row["status"] == "fail"]


def _p1_issues(environment_validation: dict[str, Any], resource_validation: dict[str, Any], standard_worker_migration_matrix: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if environment_validation.get("full_mode_ready") is not True:
        issues.append("full_analysis_environment_locks_not_restored")
    if resource_validation.get("full_mode_ready") is not True:
        issues.append("full_analysis_resource_locks_not_complete")
    if int(standard_worker_migration_matrix.get("formal_pending_count") or 0) > 0:
        issues.append("formal_algorithms_not_universally_migrated_to_isolated_standard_worker")
    return issues
