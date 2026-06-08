from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import REPO_ROOT, load_analysis_module_registry
from .resources import (
    load_analysis_resource_lock_evidence_registry,
    load_analysis_resource_manifest,
    validate_analysis_environment_registry,
    validate_analysis_resource_manifest,
)
from .standard_package import validate_standard_result_package


STANDARD_WORKER_MIGRATION_EVIDENCE_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "standard_worker_migration_evidence.schema.json"
STANDARD_WORKER_MIGRATION_EVIDENCE_REGISTRY_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "standard_worker_migration_evidence_registry.schema.json"
STANDARD_WORKER_MIGRATION_EVIDENCE_REGISTRY_PATH = REPO_ROOT / "analysis" / "registry" / "standard_worker_migration_evidence.json"
FULL_ANALYSIS_ACTIVATION_GATE_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "full_analysis_activation_gate.schema.json"
REMEDIATION_QUEUE_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "remediation_queue.schema.json"
PROVENANCE_PAYLOAD_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "provenance.schema.json"
WORKER_INVOCATION_SCHEMA_PATH = REPO_ROOT / "analysis" / "schemas" / "output" / "worker_invocation.schema.json"
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
    standard_worker_entrypoint_matrix = build_standard_worker_entrypoint_matrix(
        registry=registry,
        standard_worker_migration_matrix=standard_worker_migration_matrix,
    )
    environment_validation = validate_analysis_environment_registry(module_registry=registry)
    environment_artifact_matrix = build_environment_artifact_matrix(
        registry=registry,
        environment_validation=environment_validation,
    )
    resource_validation = validate_analysis_resource_manifest()
    resource_artifact_matrix = build_resource_artifact_matrix(resource_validation=resource_validation)
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
    module_mode_readiness_matrix = build_module_mode_readiness_matrix(
        registry=registry,
        full_activation_module_matrix=full_activation_module_matrix,
    )
    external_tool_adapter_matrix = build_external_tool_adapter_matrix(
        registry=registry,
        resource_validation=resource_validation,
    )
    task_system_boundary_matrix = build_task_system_boundary_matrix(
        registry=registry,
        standard_worker_migration_matrix=standard_worker_migration_matrix,
    )
    legacy_sidecar_transition_matrix = build_legacy_sidecar_transition_matrix(registry=registry)
    frontend_consumption_matrix = build_frontend_standard_package_consumption_matrix()
    reproducibility_provenance_matrix = build_reproducibility_provenance_matrix()
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
            "warn" if standard_worker_entrypoint_matrix.get("status") == "partial" else ("pass" if standard_worker_entrypoint_matrix.get("status") == "passed" else "fail"),
            str(registry.get("standard_entrypoint") or "missing"),
            warnings=list(standard_worker_entrypoint_matrix.get("warning_counts", {}).keys()),
            blockers=list(standard_worker_entrypoint_matrix.get("blocker_counts", {}).keys()),
        ),
        _row(
            "RARCH-04",
            "Mock / lite / full mode declarations",
            "warn" if module_mode_readiness_matrix.get("status") == "partial" else ("pass" if module_mode_readiness_matrix.get("status") == "passed" else "fail"),
            "analysis/registry/analysis_modules.json::modules[*].modes",
            warnings=list(module_mode_readiness_matrix.get("warning_counts", {}).keys()),
            blockers=list(module_mode_readiness_matrix.get("blocker_counts", {}).keys()),
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
            "warn" if legacy_sidecar_transition_matrix.get("status") == "partial" else ("pass" if legacy_sidecar_transition_matrix.get("status") == "passed" else "fail"),
            "app/analysis_runtime/task_bridge.py",
            blockers=list(legacy_sidecar_transition_matrix.get("blocker_counts", {}).keys()),
            warnings=list(legacy_sidecar_transition_matrix.get("warning_counts", {}).keys()),
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
            "warn" if environment_artifact_matrix.get("status") == "partial" else ("pass" if environment_artifact_matrix.get("status") == "passed" else "fail"),
            "analysis/registry/analysis_environments.json",
            blockers=list(environment_artifact_matrix.get("blocker_counts", {}).keys()),
            warnings=list(environment_artifact_matrix.get("warning_counts", {}).keys()),
        ),
        _row(
            "RARCH-13",
            "renv lock equivalent exists",
            "warn" if environment_artifact_matrix.get("status") == "partial" else ("pass" if environment_artifact_matrix.get("status") == "passed" else "fail"),
            "renv/renv.*.lock",
            warnings=[key for key in environment_artifact_matrix.get("warning_counts", {}) if key.startswith("environment_renv_lock_") or key == "full_environment_locks_are_scaffold_only_not_restored"],
            blockers=[key for key in environment_artifact_matrix.get("blocker_counts", {}) if "renv_lock" in key],
        ),
        _row(
            "RARCH-14",
            "Full analysis Docker image boundary",
            "warn" if environment_artifact_matrix.get("status") == "partial" else ("pass" if environment_artifact_matrix.get("status") == "passed" else "fail"),
            "docker/Dockerfile.r-*",
            warnings=[key for key in environment_artifact_matrix.get("warning_counts", {}) if key.startswith("environment_docker_image_") or key == "dockerfiles_exist_but_full_image_builds_not_proven"],
            blockers=[key for key in environment_artifact_matrix.get("blocker_counts", {}) if "dockerfile" in key],
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
            "warn" if reproducibility_provenance_matrix.get("status") == "partial" else ("pass" if reproducibility_provenance_matrix.get("status") == "passed" else "fail"),
            "analysis/schemas/output/provenance.schema.json and standard package validator",
            blockers=list(reproducibility_provenance_matrix.get("blocker_counts", {}).keys()),
            warnings=list(reproducibility_provenance_matrix.get("warning_counts", {}).keys()),
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
    requirement_summary = _requirement_summary(rows)
    priority_issue_lists = _priority_issue_lists(
        p0_issues=p0,
        p1_issues=p1,
        requirement_rows=rows,
        environment_validation=environment_validation,
        resource_validation=resource_validation,
        standard_worker_migration_matrix=standard_worker_migration_matrix,
    )
    top_architecture_risks = _top_architecture_risks(priority_issue_lists)
    status = "failed" if p0 else ("partial_with_p1_gaps" if p1 else "passed")
    return {
        "schema_version": "biomedpilot.analysis.architecture_status.v1",
        "status": status,
        "requirement_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "pass"),
        "warn_count": sum(1 for row in rows if row["status"] == "warn"),
        "fail_count": sum(1 for row in rows if row["status"] == "fail"),
        "requirement_summary": requirement_summary,
        "requirement_rows": rows,
        "p0_issues": p0,
        "p1_issues": p1,
        "p2_issues": [str(item.get("issue_id") or "") for item in priority_issue_lists.get("P2", []) if isinstance(item, dict)],
        "p3_issues": [str(item.get("issue_id") or "") for item in priority_issue_lists.get("P3", []) if isinstance(item, dict)],
        "priority_issue_lists": priority_issue_lists,
        "top_architecture_risks": top_architecture_risks,
        "module_interface_matrix": module_interface_matrix,
        "module_mode_readiness_matrix": module_mode_readiness_matrix,
        "environment_artifact_matrix": environment_artifact_matrix,
        "resource_artifact_matrix": resource_artifact_matrix,
        "standard_worker_entrypoint_matrix": standard_worker_entrypoint_matrix,
        "external_tool_adapter_matrix": external_tool_adapter_matrix,
        "task_system_boundary_matrix": task_system_boundary_matrix,
        "legacy_sidecar_transition_matrix": legacy_sidecar_transition_matrix,
        "frontend_consumption_matrix": frontend_consumption_matrix,
        "reproducibility_provenance_matrix": reproducibility_provenance_matrix,
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


def build_environment_artifact_matrix(
    *,
    registry: dict[str, Any] | None = None,
    environment_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return per-environment Dockerfile and renv lock artifact diagnostics.

    This matrix is read-only. It verifies the declared split and artifact
    surfaces for RARCH-12/13/14 without building images, restoring renv locks,
    installing packages, or marking full mode ready.
    """

    environment_registry = _read_json(REPO_ROOT / "analysis" / "registry" / "analysis_environments.json")
    validation = (
        environment_validation
        if isinstance(environment_validation, dict)
        else validate_analysis_environment_registry(module_registry=registry if isinstance(registry, dict) else None)
    )
    environments = [
        item
        for item in environment_registry.get("environments", [])
        if isinstance(item, dict)
    ]
    readiness_by_environment = {
        blocker.split(":")[1]: blocker
        for blocker in validation.get("readiness_blockers", [])
        if isinstance(blocker, str) and len(blocker.split(":")) >= 2
    }
    rows = [
        _environment_artifact_row(environment, readiness_blocker=readiness_by_environment.get(str(environment.get("environment_id") or ""), ""))
        for environment in environments
    ]
    blocker_counts = _count_row_blockers(rows, "blockers")
    warning_counts = _count_row_blockers(rows, "warnings")
    status_counts = _count_row_values(rows, "status")
    return {
        "schema_version": "biomedpilot.analysis.environment_artifact_matrix.v1",
        "status": "blocked" if blocker_counts else ("partial" if warning_counts else "passed"),
        "environment_count": len(rows),
        "passed_environment_count": sum(1 for row in rows if row.get("status") == "passed"),
        "partial_environment_count": sum(1 for row in rows if row.get("status") == "partial"),
        "blocked_environment_count": sum(1 for row in rows if row.get("status") == "blocked"),
        "status_counts": status_counts,
        "blocker_counts": blocker_counts,
        "warning_counts": warning_counts,
        "full_environment_ids": [
            str(row.get("environment_id") or "")
            for row in rows
            if row.get("environment_class") == "full"
        ],
        "restored_full_environment_ids": [
            str(row.get("environment_id") or "")
            for row in rows
            if row.get("environment_class") == "full" and row.get("renv_policy_status") in {"restored", "locked", "active"}
        ],
        "rows": rows,
        "boundary": "read_only_environment_artifact_split_diagnostics",
    }


def _environment_artifact_row(environment: dict[str, Any], *, readiness_blocker: str) -> dict[str, Any]:
    environment_id = str(environment.get("environment_id") or "")
    dockerfile = str(environment.get("dockerfile") or "")
    renv_lock = str(environment.get("renv_lock") or "")
    dockerfile_path = REPO_ROOT / dockerfile if dockerfile else REPO_ROOT / "__missing_dockerfile__"
    renv_path = REPO_ROOT / renv_lock if renv_lock else REPO_ROOT / "__missing_renv_lock__"
    blockers: list[str] = []
    warnings: list[str] = []
    docker_text = dockerfile_path.read_text(encoding="utf-8", errors="ignore") if dockerfile_path.is_file() else ""
    renv_payload = _read_json(renv_path) if renv_path.is_file() else {}
    policy = renv_payload.get("BioMedPilotPolicy") if isinstance(renv_payload.get("BioMedPilotPolicy"), dict) else {}
    packages = renv_payload.get("Packages") if isinstance(renv_payload.get("Packages"), dict) else {}
    is_default = environment_id == "app-dev"
    is_lite = environment_id == "r-bio-core"
    is_full = not is_default and not is_lite
    if not dockerfile:
        blockers.append(f"environment_dockerfile_missing:{environment_id}")
    elif not dockerfile_path.is_file():
        blockers.append(f"environment_dockerfile_not_found:{environment_id}:{dockerfile}")
    else:
        if f'org.biomedpilot.environment="{environment_id}"' not in docker_text:
            blockers.append(f"environment_dockerfile_label_missing:{environment_id}")
        if 'org.biomedpilot.runtime-package-install="forbidden"' not in docker_text:
            blockers.append(f"environment_dockerfile_runtime_install_policy_missing:{environment_id}")
    if not renv_lock:
        blockers.append(f"environment_renv_lock_missing:{environment_id}")
    elif not renv_path.is_file():
        blockers.append(f"environment_renv_lock_not_found:{environment_id}:{renv_lock}")
    else:
        policy_environment = str(policy.get("environment") or "")
        if policy_environment and not (policy_environment == environment_id or (environment_id == "r-chem-gpu" and policy_environment == "r-chem-full")):
            blockers.append(f"environment_renv_lock_environment_mismatch:{environment_id}")
        if policy.get("runtime_package_install") != "forbidden":
            blockers.append(f"environment_renv_lock_runtime_install_policy_invalid:{environment_id}")
    if is_default:
        if environment.get("r_runtime") != "not_required":
            blockers.append("environment_app_dev_r_runtime_required")
        if environment.get("allowed_module_ids"):
            blockers.append("environment_app_dev_allows_modules")
        if environment.get("allows_heavy_analysis_dependencies") is not False:
            blockers.append("environment_app_dev_heavy_dependency_policy_invalid")
    if is_lite and environment.get("allows_heavy_analysis_dependencies") is not False:
        blockers.append("environment_lite_heavy_dependency_policy_invalid:r-bio-core")
    if is_full:
        if environment.get("allows_heavy_analysis_dependencies") is not True:
            blockers.append(f"environment_full_heavy_dependency_policy_invalid:{environment_id}")
        if str(policy.get("status") or "") not in {"restored", "locked", "active"}:
            warnings.append(f"environment_renv_lock_scaffold_only_not_restored:{environment_id}")
        warnings.append(f"environment_docker_image_build_not_proven:{environment_id}")
        if readiness_blocker:
            warnings.append(readiness_blocker)
    if is_full and not blockers:
        warnings.append("full_environment_locks_are_scaffold_only_not_restored")
        warnings.append("dockerfiles_exist_but_full_image_builds_not_proven")
    return {
        "environment_id": environment_id,
        "title": str(environment.get("title") or environment_id),
        "status": "blocked" if blockers else ("partial" if warnings else "passed"),
        "environment_class": "app-dev" if is_default else ("lite" if is_lite else "full"),
        "purpose": str(environment.get("purpose") or ""),
        "dockerfile": dockerfile,
        "dockerfile_status": "present" if dockerfile_path.is_file() else "missing",
        "renv_lock": renv_lock,
        "renv_lock_status": "present" if renv_path.is_file() else "missing",
        "renv_policy_status": str(policy.get("status") or ""),
        "renv_policy_environment": str(policy.get("environment") or ""),
        "renv_package_count": len(packages),
        "r_runtime": str(environment.get("r_runtime") or ""),
        "allows_heavy_analysis_dependencies": environment.get("allows_heavy_analysis_dependencies"),
        "runtime_package_install": str(policy.get("runtime_package_install") or ""),
        "resource_lock_required": bool(environment.get("resource_lock_required")),
        "external_tool_lock_required": bool(environment.get("external_tool_lock_required")),
        "allowed_module_ids": [str(item) for item in environment.get("allowed_module_ids", []) if item],
        "readiness_blocker": readiness_blocker,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_resource_artifact_matrix(
    *,
    manifest: dict[str, Any] | None = None,
    resource_validation: dict[str, Any] | None = None,
    evidence_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return per-resource lock artifact diagnostics without preparing resources."""

    resource_manifest = manifest if isinstance(manifest, dict) else load_analysis_resource_manifest()
    registry = evidence_registry if isinstance(evidence_registry, dict) else load_analysis_resource_lock_evidence_registry()
    validation = (
        resource_validation
        if isinstance(resource_validation, dict)
        else validate_analysis_resource_manifest(
            resource_manifest,
            resource_lock_evidence_registry=registry,
        )
    )
    resources = [item for item in resource_manifest.get("resources", []) if isinstance(item, dict)]
    expected_resource_ids = {str(item) for item in validation.get("expected_resource_ids", []) if item}
    missing_resource_ids = {str(item) for item in validation.get("missing_resource_ids", []) if item}
    evidence_entries = {
        str(item.get("resource_id") or ""): str(item.get("evidence_path") or "")
        for item in registry.get("evidence_entries", [])
        if isinstance(item, dict)
    }
    rows = [
        _resource_artifact_row(
            resource,
            expected_resource_ids=expected_resource_ids,
            missing_resource_ids=missing_resource_ids,
            evidence_entries=evidence_entries,
        )
        for resource in resources
    ]
    blocker_counts = _count_row_blockers(rows, "blockers")
    warning_counts = _count_row_blockers(rows, "warnings")
    status_counts = _count_row_values(rows, "status")
    return {
        "schema_version": "biomedpilot.analysis.resource_artifact_matrix.v1",
        "status": "blocked" if blocker_counts else ("partial" if warning_counts else "passed"),
        "resource_count": len(rows),
        "locked_resource_count": sum(1 for row in rows if row.get("lock_status") == "locked"),
        "blocked_resource_count": sum(1 for row in rows if row.get("lock_status") != "locked"),
        "passed_resource_count": sum(1 for row in rows if row.get("status") == "passed"),
        "partial_resource_count": sum(1 for row in rows if row.get("status") == "partial"),
        "failed_resource_count": sum(1 for row in rows if row.get("status") == "blocked"),
        "evidence_registry_status": validation.get("evidence_registry_status"),
        "evidence_entry_count": validation.get("evidence_registry_entry_count"),
        "expected_resource_ids": list(validation.get("expected_resource_ids", [])),
        "missing_resource_ids": list(validation.get("missing_resource_ids", [])),
        "status_counts": status_counts,
        "blocker_counts": blocker_counts,
        "warning_counts": warning_counts,
        "rows": rows,
        "boundary": "read_only_full_resource_lock_artifact_diagnostics",
    }


def _resource_artifact_row(
    resource: dict[str, Any],
    *,
    expected_resource_ids: set[str],
    missing_resource_ids: set[str],
    evidence_entries: dict[str, str],
) -> dict[str, Any]:
    resource_id = str(resource.get("resource_id") or "")
    status = str(resource.get("status") or "")
    runtime_download_allowed = resource.get("runtime_download_allowed")
    cache_path = str(resource.get("cache_path") or "")
    cache_exists = (REPO_ROOT / cache_path).exists() if cache_path else False
    lock_evidence = str(resource.get("lock_evidence") or evidence_entries.get(resource_id) or "")
    evidence_path = REPO_ROOT / lock_evidence if lock_evidence else REPO_ROOT / "__missing_resource_lock_evidence__"
    evidence_status = "present" if evidence_path.is_file() else ("missing" if resource_id in expected_resource_ids or status == "locked" else "not_required")
    placeholder_fields = [
        field
        for field in ("version", "hash", "license")
        if _is_placeholder_value(resource.get(field))
    ]
    blockers: list[str] = []
    warnings: list[str] = []
    if not resource_id:
        blockers.append("resource_artifact_resource_id_missing")
    if runtime_download_allowed is not False:
        blockers.append(f"resource_artifact_runtime_download_not_forbidden:{resource_id or 'unknown'}")
    if status == "locked":
        if placeholder_fields:
            blockers.append(f"resource_artifact_locked_placeholder_fields:{resource_id}:{','.join(placeholder_fields)}")
        if evidence_status != "present":
            blockers.append(f"resource_artifact_locked_evidence_missing:{resource_id}")
    elif resource_id in expected_resource_ids or status:
        warnings.append(f"resource_full_lock_not_ready:{resource_id}")
        for field in placeholder_fields:
            warnings.append(f"resource_placeholder_field:{resource_id}:{field}")
        if resource_id in missing_resource_ids:
            warnings.append(f"resource_lock_evidence_registry_entry_missing:{resource_id}")
        if evidence_status != "present":
            warnings.append(f"resource_lock_evidence_missing:{resource_id}")
        if cache_path and not cache_exists:
            warnings.append(f"resource_cache_path_not_prepared:{resource_id}")
    else:
        blockers.append(f"resource_artifact_status_missing:{resource_id or 'unknown'}")
    return {
        "resource_id": resource_id,
        "title": str(resource.get("title") or resource_id),
        "status": "blocked" if blockers else ("partial" if warnings else "passed"),
        "resource_family": str(resource.get("resource_family") or ""),
        "lock_status": status,
        "resource_lock_required": resource_id in expected_resource_ids,
        "version": str(resource.get("version") or ""),
        "version_status": "placeholder" if "version" in placeholder_fields else "declared",
        "source": str(resource.get("source") or ""),
        "hash": str(resource.get("hash") or ""),
        "hash_status": "placeholder" if "hash" in placeholder_fields else "declared",
        "license": str(resource.get("license") or ""),
        "license_status": "placeholder" if "license" in placeholder_fields else "declared",
        "cache_path": cache_path,
        "cache_path_status": "present" if cache_exists else "missing",
        "lock_evidence": lock_evidence,
        "lock_evidence_status": evidence_status,
        "runtime_download_allowed": runtime_download_allowed,
        "required_for_modules": [str(item) for item in resource.get("required_for_modules", []) if item],
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _is_placeholder_value(value: Any) -> bool:
    text = str(value or "").strip()
    return not text or text in {"required_before_full_mode", "<version>", "<source>", "<sha256>", "<license>"}


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


def build_module_mode_readiness_matrix(
    *,
    registry: dict[str, Any] | None = None,
    full_activation_module_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return module-by-module mock/lite/full mode layering diagnostics.

    This is a read-only RARCH-04 contract surface. It proves that mock/lite/full
    are declared and makes full-mode blockers visible, but it does not run or
    enable full analysis.
    """

    payload = registry if isinstance(registry, dict) else load_analysis_module_registry()
    activation_matrix = (
        full_activation_module_matrix
        if isinstance(full_activation_module_matrix, dict)
        else build_full_activation_module_matrix(registry=payload)
    )
    activation_by_module = {
        str(row.get("module_id") or ""): row
        for row in activation_matrix.get("rows", [])
        if isinstance(row, dict) and row.get("module_id")
    }
    modules = [
        item
        for item in payload.get("modules", [])
        if isinstance(item, dict) and item.get("module_id") in TARGET_MODULE_IDS
    ]
    rows = [_module_mode_readiness_row(module, activation_row=activation_by_module.get(str(module.get("module_id") or ""), {})) for module in modules]
    blocker_counts = _count_row_blockers(rows, "blockers")
    warning_counts = _count_row_blockers(rows, "warnings")
    status_counts = _count_row_values(rows, "status")
    return {
        "schema_version": "biomedpilot.analysis.module_mode_readiness_matrix.v1",
        "status": "blocked" if blocker_counts else ("partial" if warning_counts else "passed"),
        "module_count": len(rows),
        "passed_module_count": sum(1 for row in rows if row.get("status") == "passed"),
        "partial_module_count": sum(1 for row in rows if row.get("status") == "partial"),
        "blocked_module_count": sum(1 for row in rows if row.get("status") == "blocked"),
        "status_counts": status_counts,
        "blocker_counts": blocker_counts,
        "warning_counts": warning_counts,
        "full_blocked_module_ids": [
            str(row.get("module_id") or "")
            for row in rows
            if row.get("full_status") == "blocked"
        ],
        "rows": rows,
        "boundary": "read_only_mock_lite_full_mode_layering_diagnostics",
    }


def _module_mode_readiness_row(module: dict[str, Any], *, activation_row: dict[str, Any]) -> dict[str, Any]:
    module_id = str(module.get("module_id") or "")
    module_manifest = str(module.get("module_manifest") or f"analysis/modules/{module_id}/module.json")
    manifest = _read_json(REPO_ROOT / module_manifest) if (REPO_ROOT / module_manifest).is_file() else {}
    source = manifest if isinstance(manifest, dict) and manifest else module
    modes = source.get("modes") if isinstance(source.get("modes"), dict) else {}
    mock = modes.get("mock") if isinstance(modes.get("mock"), dict) else {}
    lite = modes.get("lite") if isinstance(modes.get("lite"), dict) else {}
    full = modes.get("full") if isinstance(modes.get("full"), dict) else {}
    blockers: list[str] = []
    warnings: list[str] = []
    if not module_id:
        blockers.append("module_mode_module_id_missing")
    if not (REPO_ROOT / module_manifest).is_file():
        blockers.append(f"module_mode_manifest_missing:{module_id}:{module_manifest}")
    for mode_name, mode_payload in (("mock", mock), ("lite", lite), ("full", full)):
        if not mode_payload:
            blockers.append(f"module_mode_missing:{module_id}:{mode_name}")
        elif "supported" not in mode_payload:
            blockers.append(f"module_mode_supported_flag_missing:{module_id}:{mode_name}")
    mock_status = "passed" if mock.get("supported") is True else "blocked"
    lite_status = "passed" if lite.get("supported") is True else "blocked"
    if mock_status == "blocked":
        blockers.append(f"module_mode_mock_not_supported:{module_id}")
    if lite_status == "blocked":
        blockers.append(f"module_mode_lite_not_supported:{module_id}")
    full_supported = full.get("supported") is True
    activation_blockers = [str(item) for item in activation_row.get("blockers", []) if item]
    full_blocker = str(full.get("blocker") or "")
    full_status = "passed" if full_supported and not activation_blockers else "blocked"
    if full_status == "blocked":
        warnings.append(f"module_full_mode_blocked:{module_id}")
        if full_blocker:
            warnings.append(f"module_full_mode_declared_blocker:{module_id}:{full_blocker}")
    return {
        "module_id": module_id,
        "title": str(source.get("title") or module.get("title") or module_id),
        "status": "blocked" if blockers else ("partial" if warnings else "passed"),
        "module_manifest": module_manifest,
        "mock_supported": bool(mock.get("supported")),
        "mock_fixture_input": str(mock.get("fixture_input") or ""),
        "mock_fixture_output_package": str(mock.get("fixture_output_package") or ""),
        "mock_status": mock_status,
        "lite_supported": bool(lite.get("supported")),
        "lite_environment": str(lite.get("environment") or source.get("analysis_environment") or module.get("analysis_environment") or ""),
        "lite_runner": str(lite.get("runner") or source.get("standard_entrypoint") or module.get("standard_entrypoint") or ""),
        "lite_worker_backend": str(lite.get("worker_backend") or ""),
        "lite_result_semantics": str(lite.get("result_semantics") or "testing_level"),
        "lite_status": lite_status,
        "full_supported": full_supported,
        "full_environment": str(source.get("full_environment") or module.get("full_environment") or ""),
        "full_blocker": full_blocker,
        "full_status": full_status,
        "full_activation_status": str(activation_row.get("status") or "blocked"),
        "full_activation_blockers": activation_blockers,
        "migration_next_action": str(activation_row.get("migration_next_action") or "inspect_full_mode_blockers"),
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def build_standard_worker_entrypoint_matrix(
    *,
    registry: dict[str, Any] | None = None,
    standard_worker_migration_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return static diagnostics for the repository-owned standard R entrypoint."""

    payload = registry if isinstance(registry, dict) else load_analysis_module_registry()
    migration_matrix = (
        standard_worker_migration_matrix
        if isinstance(standard_worker_migration_matrix, dict)
        else build_standard_worker_migration_matrix(payload)
    )
    modules = [
        item
        for item in payload.get("modules", [])
        if isinstance(item, dict) and item.get("module_id") in TARGET_MODULE_IDS
    ]
    standard_entrypoint = str(payload.get("standard_entrypoint") or "analysis/runners/run_module.R")
    runner_text = (REPO_ROOT / standard_entrypoint).read_text(encoding="utf-8", errors="ignore") if (REPO_ROOT / standard_entrypoint).is_file() else ""
    lite_modules = _standard_entrypoint_lite_module_ids(modules, standard_entrypoint=standard_entrypoint)
    formal_pending = [
        str(row.get("module_id") or "")
        for row in migration_matrix.get("rows", [])
        if isinstance(row, dict) and row.get("formal_worker_status") != "migrated_to_isolated_standard_worker"
    ]
    rows = [
        _source_token_contract_row(
            row_id="standard_r_worker_cli_contract",
            title="Standard R worker accepts input_json, output_dir, and mode",
            file_path=standard_entrypoint,
            required_tokens=[
                "usage: run_module.R <input_json> <output_dir> <mode>",
                "input_json <- normalizePath(args[[1]], mustWork = TRUE)",
                "output_dir <- args[[2]]",
                "mode <- args[[3]]",
                "repo_root <- normalizePath",
            ],
            evidence_path=f"{standard_entrypoint}::cli_args",
        ),
        _source_token_contract_row(
            row_id="standard_r_worker_package_output_contract",
            title="Standard R worker writes standard package files and directories",
            file_path=standard_entrypoint,
            required_tokens=[
                'required_dirs <- c("tables", "plots", "reports", "logs")',
                'writeLines(input_text, file.path(output_dir, "module_input.json")',
                'writeLines(result, file.path(output_dir, "result.json"))',
                'writeLines(provenance, file.path(output_dir, "provenance.json"))',
                "write_worker_invocation <- function",
                'file.path(output_dir, "logs", "worker_invocation.json")',
                'file.path(output_dir, "logs", "worker.log")',
            ],
            evidence_path=f"{standard_entrypoint}::standard_package_writers",
        ),
        _standard_worker_lite_dispatch_row(
            runner_text=runner_text,
            lite_module_ids=lite_modules,
            standard_entrypoint=standard_entrypoint,
        ),
        _standard_worker_main_backend_invocation_row(),
        _standard_worker_runtime_acquisition_row(runner_text=runner_text, standard_entrypoint=standard_entrypoint),
        {
            "row_id": "standard_r_worker_formal_migration_boundary",
            "title": "Formal/full algorithms still require migration evidence",
            "status": "partial" if formal_pending else "passed",
            "evidence_path": "analysis/registry/standard_worker_migration_evidence.json",
            "formal_pending_module_count": len(formal_pending),
            "formal_pending_module_ids": formal_pending,
            "blockers": [],
            "warnings": [f"standard_worker_entrypoint_formal_migration_pending:{module_id}" for module_id in formal_pending],
            "boundary": "entrypoint_contract_is_not_formal_full_migration_evidence",
        },
    ]
    blocker_counts = _count_row_blockers(rows, "blockers")
    warning_counts = _count_row_blockers(rows, "warnings")
    status_counts = _count_row_values(rows, "status")
    return {
        "schema_version": "biomedpilot.analysis.standard_worker_entrypoint_matrix.v1",
        "status": "blocked" if blocker_counts else ("partial" if warning_counts else "passed"),
        "row_count": len(rows),
        "passed_row_count": sum(1 for row in rows if row.get("status") == "passed"),
        "partial_row_count": sum(1 for row in rows if row.get("status") == "partial"),
        "blocked_row_count": sum(1 for row in rows if row.get("status") == "blocked"),
        "status_counts": status_counts,
        "blocker_counts": blocker_counts,
        "warning_counts": warning_counts,
        "standard_entrypoint": standard_entrypoint,
        "lite_module_ids": lite_modules,
        "formal_pending_module_ids": formal_pending,
        "rows": rows,
        "boundary": "read_only_standard_r_worker_entrypoint_contract_diagnostics",
    }


def _standard_entrypoint_lite_module_ids(modules: list[dict[str, Any]], *, standard_entrypoint: str) -> list[str]:
    ids: list[str] = []
    for module in modules:
        modes = module.get("modes") if isinstance(module.get("modes"), dict) else {}
        lite = modes.get("lite") if isinstance(modes.get("lite"), dict) else {}
        if lite.get("supported") is True and lite.get("runner") == standard_entrypoint and lite.get("worker_backend") == "rscript":
            ids.append(str(module.get("module_id") or ""))
    return [item for item in ids if item]


def _standard_worker_lite_dispatch_row(
    *,
    runner_text: str,
    lite_module_ids: list[str],
    standard_entrypoint: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    for module_id in lite_module_ids:
        token = f'if (mode == "lite" && module_id == "{module_id}")'
        if token not in runner_text:
            blockers.append(f"standard_worker_lite_dispatch_missing:{module_id}")
    for token in (
        'if (mode != "mock")',
        'standard_worker_mode_not_enabled:',
        'fixture_package <- file.path(repo_root, "analysis", "fixtures", "outputs", module_id, "mock_result_package")',
    ):
        if token not in runner_text:
            blockers.append(f"standard_worker_mode_gate_token_missing:{token}")
    return {
        "row_id": "standard_r_worker_lite_dispatch_contract",
        "title": "Standard R worker dispatches registered lite modules and blocks non-mock fallback modes",
        "status": "blocked" if blockers else "passed",
        "evidence_path": f"{standard_entrypoint}::lite_dispatch",
        "lite_module_ids": lite_module_ids,
        "lite_module_count": len(lite_module_ids),
        "blockers": blockers,
        "warnings": [],
        "boundary": "lite_dispatch_only_full_mode_still_blocked_by_gate",
    }


def _standard_worker_main_backend_invocation_row() -> dict[str, Any]:
    checks = [
        (
            "app/analysis_runtime/r_worker.py",
            [
                "STANDARD_R_RUNNER = REPO_ROOT / \"analysis\" / \"runners\" / \"run_module.R\"",
                "def run_standard_r_worker",
                "shutil.which(\"Rscript\")",
                "command = [rscript, str(STANDARD_R_RUNNER), str(input_path), str(package_dir), mode]",
                "subprocess.run(",
                "\"rscript_not_available\"",
            ],
        ),
        (
            "app/analysis_runtime/task_bridge.py",
            [
                "from .r_worker import run_standard_r_worker",
                "worker_required = str(mode_policy.get(\"worker_backend\") or \"\") == \"rscript\"",
                "worker_result = run_standard_r_worker(worker_input, package_dir, mode)",
                "worker_backend=worker_backend",
                "task_center_registered",
            ],
        ),
    ]
    blockers: list[str] = []
    evidence_paths: list[str] = []
    for file_path, tokens in checks:
        path = REPO_ROOT / file_path
        text = path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""
        evidence_paths.append(file_path)
        if not path.is_file():
            blockers.append(f"standard_worker_invocation_file_missing:{file_path}")
            continue
        for token in tokens:
            if token not in text:
                blockers.append(f"standard_worker_invocation_token_missing:{file_path}:{token}")
    return {
        "row_id": "standard_r_worker_main_backend_invocation_contract",
        "title": "Main backend invokes standard R worker through task bridge helper",
        "status": "blocked" if blockers else "passed",
        "evidence_path": "; ".join(evidence_paths),
        "blockers": blockers,
        "warnings": [],
        "boundary": "main_backend_invokes_repo_owned_runner_no_module_private_r_outputs",
    }


def _standard_worker_runtime_acquisition_row(*, runner_text: str, standard_entrypoint: str) -> dict[str, Any]:
    hits = [pattern for pattern in (*BANNED_RUNTIME_INSTALL_PATTERNS, *BANNED_RUNTIME_RESOURCE_DOWNLOAD_PATTERNS) if pattern in runner_text]
    return {
        "row_id": "standard_r_worker_no_runtime_acquisition",
        "title": "Standard R worker contains no runtime install or resource download commands",
        "status": "blocked" if hits else "passed",
        "evidence_path": standard_entrypoint,
        "forbidden_patterns": list(BANNED_RUNTIME_INSTALL_PATTERNS) + list(BANNED_RUNTIME_RESOURCE_DOWNLOAD_PATTERNS),
        "blockers": [f"standard_worker_runtime_acquisition_pattern_found:{pattern}" for pattern in hits],
        "warnings": [],
        "boundary": "no_install_no_download_in_standard_worker_entrypoint",
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
        _frontend_detailed_result_views_migration_row(),
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
        "pending_detail_view_count": sum(int(row.get("pending_detail_view_count") or 0) for row in rows),
        "pending_detail_view_ids": [
            str(item)
            for row in rows
            for item in (row.get("pending_detail_view_ids", []) if isinstance(row.get("pending_detail_view_ids"), list) else [])
        ],
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


def _frontend_detailed_result_views_migration_row() -> dict[str, Any]:
    file_path = "app/bioinformatics/workflow_pages.py"
    path = REPO_ROOT / file_path
    text = path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""
    targets = [
        {
            "view_id": "formal_deg_review_panel",
            "consumer_surface": "BioinformaticsResultsBrowserWidget.formal_deg_review",
            "current_private_tokens": [
                "build_formal_deg_result_review",
                "export_formal_deg_review_table",
                "formalDegReviewTable",
            ],
            "migration_next_action": "read DEG review rows from standard package artifact manifest and package-local tables",
        },
        {
            "view_id": "formal_deg_plot_report_controls",
            "consumer_surface": "BioinformaticsResultsBrowserWidget.formal_deg_plot_report_export",
            "current_private_tokens": [
                "build_formal_deg_plot_gate",
                "create_formal_deg_plot_artifact",
                "create_formal_deg_report_ready_package",
            ],
            "migration_next_action": "drive plot/report/export controls from standard package artifacts and report package manifests",
        },
        {
            "view_id": "immune_tme_scoring_page",
            "consumer_surface": "BioinformaticsImmuneScoringWidget",
            "current_private_tokens": [
                "build_immune_infiltration_readiness",
                "run_immune_scoring",
                "generate_immune_tme_report",
            ],
            "migration_next_action": "replace module-private score/report previews with standard package catalog/detail artifacts",
        },
    ]
    blockers: list[str] = []
    if not path.is_file():
        blockers.append(f"frontend_consumption_file_missing:{file_path}")
    pending: list[dict[str, Any]] = []
    for target in targets:
        missing_tokens = [token for token in target["current_private_tokens"] if token not in text]
        if missing_tokens:
            blockers.append(f"detailed_result_view_inventory_token_missing:{target['view_id']}:{','.join(missing_tokens)}")
            continue
        pending.append(dict(target))
    pending_ids = [str(item["view_id"]) for item in pending]
    warnings = ["detailed_result_views_still_need_standard_package_only_migration"]
    warnings.extend(f"detailed_result_view_pending_standard_package_migration:{view_id}" for view_id in pending_ids)
    return {
        "row_id": "detailed_result_views_migration",
        "title": "Detailed result views still need standard-package-only migration",
        "status": "blocked" if blockers else "partial",
        "file_path": file_path,
        "consumer_surface": "module_specific_detailed_result_views",
        "source_policy": "transitional_legacy_detail_views_must_not_be_formal_readiness_evidence",
        "pending_detail_view_count": len(pending),
        "pending_detail_view_ids": pending_ids,
        "pending_detail_views": pending,
        "migration_next_action": "migrate listed detailed result views to consume build_standard_analysis_package_detail() and standard package artifact manifests before closing RARCH-08",
        "blockers": blockers,
        "warnings": warnings,
    }


def build_reproducibility_provenance_matrix() -> dict[str, Any]:
    """Return static evidence for reproducibility provenance coverage.

    This matrix proves the current contracts require the reproducibility fields
    and that bridge/worker writers materialize them. It remains partial until
    formal/full modules register standard-worker migration evidence.
    """

    provenance_schema = _read_json(PROVENANCE_PAYLOAD_SCHEMA_PATH)
    runtime_schema = (
        provenance_schema.get("properties", {}).get("runtime", {})
        if isinstance(provenance_schema.get("properties"), dict)
        else {}
    )
    engine_schema = (
        provenance_schema.get("properties", {}).get("engine", {})
        if isinstance(provenance_schema.get("properties"), dict)
        else {}
    )
    required_fields = [str(item) for item in provenance_schema.get("required", []) if item]
    runtime_required_fields = [str(item) for item in runtime_schema.get("required", []) if item] if isinstance(runtime_schema, dict) else []
    engine_required_fields = [str(item) for item in engine_schema.get("required", []) if item] if isinstance(engine_schema, dict) else []
    rows = [
        _provenance_schema_row(
            required_fields=required_fields,
            runtime_required_fields=runtime_required_fields,
            engine_required_fields=engine_required_fields,
        ),
        _source_token_contract_row(
            row_id="standard_package_validator_required_provenance",
            title="Standard package validator blocks incomplete passed provenance",
            file_path="app/analysis_runtime/standard_package.py",
            required_tokens=[
                "_passed_package_provenance_blockers",
                "for field in (\"input_hash\", \"parameter_hash\", \"command\")",
                "blockers.append(f\"passed_provenance_{field}_missing\")",
                "passed_provenance_random_seed_missing",
                "for field in (\"name\", \"version\")",
                "blockers.append(f\"passed_provenance_engine_{field}_missing\")",
                "for field in (\"r_version\", \"bioconductor_version\", \"package_versions\", \"external_tool_versions\")",
                "blockers.append(f\"passed_provenance_runtime_{field}_missing\")",
                "passed_provenance_runtime_package_versions_invalid",
                "passed_provenance_runtime_external_tool_versions_invalid",
            ],
            evidence_path="app/analysis_runtime/standard_package.py::_passed_package_provenance_blockers",
        ),
        _source_token_contract_row(
            row_id="task_bridge_provenance_writer",
            title="Task bridge writes deterministic input/parameter hashes and runtime snapshot",
            file_path="app/analysis_runtime/task_bridge.py",
            required_tokens=[
                "input_hash = _hash_payload(payload.get(\"inputs\", {}))",
                "parameter_hash = _hash_payload(payload.get(\"parameters\", {}))",
                "\"random_seed\": (payload.get(\"runtime\") or {}).get(\"random_seed\")",
                "\"engine\": {\"name\": \"biomedpilot_analysis_task_bridge\", \"version\": \"v1\"}",
                "\"runtime\": {",
                "\"package_versions\": {}",
                "\"external_tool_versions\": {}",
                "\"command\": command",
                "analysis_environment",
            ],
            evidence_path="app/analysis_runtime/task_bridge.py::_write_standard_package",
        ),
        _source_token_contract_row(
            row_id="standard_r_worker_provenance_writer",
            title="Standard R worker writes R/Bioc/hash/seed/command provenance",
            file_path="analysis/runners/run_module.R",
            required_tokens=[
                "write_provenance <- function(module_id, task_id, mode, command, r_version, bioc_version",
                "seed <- read_integer_field(input_text, \"random_seed\")",
                "input_hash <- as.character(tools::md5sum(input_json))",
                "parameter_hash <- hash_string(read_object_field_text(input_text, \"parameters\", \"{}\"))",
                "\"engine\": {\"name\": \"biomedpilot_standard_r_worker\", \"version\": \"v1\"}",
                "\"runtime\": {\"r_version\": ",
                "\"bioconductor_version\": ",
                "\"package_versions\": {}",
                "\"external_tool_versions\": ",
                "\"command\": ",
            ],
            evidence_path="analysis/runners/run_module.R::write_provenance",
        ),
        _worker_invocation_schema_row(),
        {
            "row_id": "legacy_sidecar_provenance_boundary",
            "title": "Legacy service adapter sidecars remain transitional provenance only",
            "status": "partial",
            "evidence_path": "app/analysis_runtime/standard_package.py::write_legacy_service_adapter_invocation_manifest",
            "required_fields": [],
            "required_runtime_fields": [],
            "required_engine_fields": [],
            "blockers": [],
            "warnings": ["legacy_service_adapter_sidecars_are_not_isolated_standard_worker_provenance_evidence"],
            "boundary": "formal_full_completion_requires_standard_worker_migration_evidence_not_sidecar_provenance",
        },
    ]
    blocker_counts = _count_row_blockers(rows, "blockers")
    warning_counts = _count_row_blockers(rows, "warnings")
    status_counts = _count_row_values(rows, "status")
    return {
        "schema_version": "biomedpilot.analysis.reproducibility_provenance_matrix.v1",
        "status": "blocked" if blocker_counts else ("partial" if warning_counts else "passed"),
        "row_count": len(rows),
        "passed_row_count": sum(1 for row in rows if row.get("status") == "passed"),
        "partial_row_count": sum(1 for row in rows if row.get("status") == "partial"),
        "blocked_row_count": sum(1 for row in rows if row.get("status") == "blocked"),
        "status_counts": status_counts,
        "blocker_counts": blocker_counts,
        "warning_counts": warning_counts,
        "required_fields": required_fields,
        "required_runtime_fields": runtime_required_fields,
        "required_engine_fields": engine_required_fields,
        "rows": rows,
        "boundary": "read_only_reproducibility_provenance_contract_diagnostics",
    }


def _provenance_schema_row(
    *,
    required_fields: list[str],
    runtime_required_fields: list[str],
    engine_required_fields: list[str],
) -> dict[str, Any]:
    required = {
        "schema_version",
        "module_id",
        "mode",
        "task_id",
        "created_at",
        "input_hash",
        "parameter_hash",
        "random_seed",
        "engine",
        "runtime",
        "command",
    }
    runtime_required = {"r_version", "bioconductor_version", "package_versions", "external_tool_versions"}
    engine_required = {"name", "version"}
    blockers: list[str] = []
    missing = sorted(required - set(required_fields))
    missing_runtime = sorted(runtime_required - set(runtime_required_fields))
    missing_engine = sorted(engine_required - set(engine_required_fields))
    blockers.extend(f"provenance_schema_required_field_missing:{field}" for field in missing)
    blockers.extend(f"provenance_schema_runtime_field_missing:{field}" for field in missing_runtime)
    blockers.extend(f"provenance_schema_engine_field_missing:{field}" for field in missing_engine)
    return {
        "row_id": "provenance_payload_schema",
        "title": "Provenance payload schema requires reproducibility fields",
        "status": "blocked" if blockers else "passed",
        "evidence_path": "analysis/schemas/output/provenance.schema.json",
        "required_fields": required_fields,
        "required_runtime_fields": runtime_required_fields,
        "required_engine_fields": engine_required_fields,
        "blockers": blockers,
        "warnings": [],
        "boundary": "schema_contract_only_no_worker_execution",
    }


def _worker_invocation_schema_row() -> dict[str, Any]:
    schema = _read_json(WORKER_INVOCATION_SCHEMA_PATH)
    required_fields = [str(item) for item in schema.get("required", []) if item]
    required = {
        "schema_version",
        "module_id",
        "mode",
        "task_id",
        "worker_backend",
        "invocation_status",
        "standard_worker_entrypoint",
        "input_manifest",
        "output_contract",
        "runtime_install_policy",
        "resource_download_policy",
        "command",
        "worker_boundary",
    }
    missing = sorted(required - set(required_fields))
    blockers = [f"worker_invocation_schema_required_field_missing:{field}" for field in missing]
    return {
        "row_id": "worker_invocation_schema",
        "title": "Worker invocation manifest captures command and no-install/no-download policy",
        "status": "blocked" if blockers else "passed",
        "evidence_path": "analysis/schemas/output/worker_invocation.schema.json",
        "required_fields": required_fields,
        "required_runtime_fields": [],
        "required_engine_fields": [],
        "blockers": blockers,
        "warnings": [],
        "boundary": "worker_invocation_contract_only_no_worker_execution",
    }


def _source_token_contract_row(
    *,
    row_id: str,
    title: str,
    file_path: str,
    required_tokens: list[str],
    evidence_path: str,
) -> dict[str, Any]:
    path = REPO_ROOT / file_path
    text = path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""
    blockers: list[str] = []
    if not path.is_file():
        blockers.append(f"provenance_contract_file_missing:{file_path}")
    for token in required_tokens:
        if token not in text:
            blockers.append(f"provenance_contract_required_token_missing:{row_id}:{token}")
    return {
        "row_id": row_id,
        "title": title,
        "status": "blocked" if blockers else "passed",
        "evidence_path": evidence_path,
        "required_tokens": required_tokens,
        "required_fields": [],
        "required_runtime_fields": [],
        "required_engine_fields": [],
        "blockers": blockers,
        "warnings": [],
        "boundary": "static_source_contract_check_no_worker_execution",
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


def build_legacy_sidecar_transition_matrix(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return read-only diagnostics for transitional legacy service sidecars."""

    payload = registry if isinstance(registry, dict) else load_analysis_module_registry()
    modules = [
        item
        for item in payload.get("modules", [])
        if isinstance(item, dict) and item.get("module_id") in TARGET_MODULE_IDS
    ]
    adapter_statuses = {
        str(module.get("module_id") or ""): str(module.get("current_adapter_status") or "")
        for module in modules
    }
    transitional_modules = [
        module_id
        for module_id, status in adapter_statuses.items()
        if any(token in status for token in ("legacy", "sidecar", "existing_", "pending", "planned"))
    ]
    rows = [
        _source_token_contract_row(
            row_id="legacy_sidecar_writer_contract",
            title="Legacy sidecar writer marks direct-call transition boundary",
            file_path="app/analysis_runtime/standard_package.py",
            required_tokens=[
                "write_legacy_service_adapter_invocation_manifest",
                "\"worker_backend\": \"legacy_service_adapter\"",
                "\"invocation_status\": \"sidecar_recorded\"",
                "\"standard_worker_entrypoint\": \"not_used\"",
                "\"task_system_invocation\": \"legacy_service_adapter_direct_call\"",
                "\"migration_status\": \"sidecar_only_not_isolated_standard_worker\"",
            ],
            evidence_path="app/analysis_runtime/standard_package.py::write_legacy_service_adapter_invocation_manifest",
        ),
        _source_token_contract_row(
            row_id="catalog_task_center_guard",
            title="Catalog blocks direct standard-worker packages from UI task readiness",
            file_path="app/analysis_runtime/package_catalog.py",
            required_tokens=[
                "_catalog_task_system_boundary_blockers",
                "boundary.get(\"boundary_type\") != \"standard_r_worker\"",
                "task_system_invocation == \"task_center_registered\"",
                "standard_r_worker_package_not_task_center_registered",
            ],
            evidence_path="app/analysis_runtime/package_catalog.py::_catalog_task_system_boundary_blockers",
        ),
        _source_token_contract_row(
            row_id="migration_evidence_forbids_sidecar",
            title="Standard-worker migration evidence forbids legacy sidecar sources",
            file_path="app/analysis_runtime/architecture_status.py",
            required_tokens=[
                "\"legacy_service_adapter_sidecar\"",
                "\"module_private_output_path\"",
                "required_task_system_invocation",
                "task_center_registered",
                "required_worker_boundary",
                "standard_r_worker",
            ],
            evidence_path="app/analysis_runtime/architecture_status.py::_standard_worker_migration_evidence_template",
        ),
        {
            "row_id": "registry_adapter_transition_scope",
            "title": "Registry adapter statuses remain transition scoped",
            "status": "partial" if transitional_modules else "passed",
            "evidence_path": "analysis/registry/analysis_modules.json::modules[*].current_adapter_status",
            "module_count": len(adapter_statuses),
            "transitional_module_count": len(transitional_modules),
            "adapter_status_counts": _count_adapter_statuses(adapter_statuses),
            "transitional_module_ids": transitional_modules,
            "blockers": [],
            "warnings": [f"registry_current_adapter_status_transitional:{module_id}" for module_id in transitional_modules],
            "boundary": "adapter_status_is_inventory_only_not_worker_migration_evidence",
        },
        _source_token_contract_row(
            row_id="sidecar_boundary_test_coverage",
            title="Tests cover sidecar direct-call and not-migration boundaries",
            file_path="tests/bioinformatics/test_immune_infiltration.py",
            required_tokens=[
                "legacy_service_adapter_direct_call",
                "legacy_service_adapter_sidecar",
                "testing_level",
            ],
            evidence_path="tests/bioinformatics/test_immune_infiltration.py and tests/test_analysis_runtime_task_bridge.py",
        ),
    ]
    blocker_counts = _count_row_blockers(rows, "blockers")
    warning_counts = _count_row_blockers(rows, "warnings")
    status_counts = _count_row_values(rows, "status")
    return {
        "schema_version": "biomedpilot.analysis.legacy_sidecar_transition_matrix.v1",
        "status": "blocked" if blocker_counts else ("partial" if warning_counts else "passed"),
        "row_count": len(rows),
        "passed_row_count": sum(1 for row in rows if row.get("status") == "passed"),
        "partial_row_count": sum(1 for row in rows if row.get("status") == "partial"),
        "blocked_row_count": sum(1 for row in rows if row.get("status") == "blocked"),
        "status_counts": status_counts,
        "blocker_counts": blocker_counts,
        "warning_counts": warning_counts,
        "adapter_status_counts": _count_adapter_statuses(adapter_statuses),
        "transitional_module_ids": transitional_modules,
        "rows": rows,
        "boundary": "read_only_legacy_sidecar_transition_diagnostics",
    }


def _count_adapter_statuses(adapter_statuses: dict[str, str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for status in adapter_statuses.values():
        key = status or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


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


def _requirement_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"pass": 0, "warn": 0, "fail": 0, "other": 0}
    for row in rows:
        status = str(row.get("status") or "other")
        if status in counts:
            counts[status] += 1
        else:
            counts["other"] += 1
    return {
        "requirement_count": len(rows),
        "pass_count": counts["pass"],
        "warn_count": counts["warn"],
        "fail_count": counts["fail"],
        "other_count": counts["other"],
        "status_order": ["fail", "warn", "pass"],
    }


def _priority_issue_lists(
    *,
    p0_issues: list[str],
    p1_issues: list[str],
    requirement_rows: list[dict[str, Any]],
    environment_validation: dict[str, Any],
    resource_validation: dict[str, Any],
    standard_worker_migration_matrix: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    p0 = [
        _issue("P0", issue, "architecture_p0_guard", "P0 issue is present in architecture status.")
        for issue in p0_issues
    ]
    p1: list[dict[str, Any]] = []
    if "full_analysis_environment_locks_not_restored" in p1_issues:
        p1.append(
            _issue(
                "P1",
                "full_analysis_environment_locks_not_restored",
                "environment_readiness",
                "Full analysis environments remain scaffold-only or lack restored lock evidence.",
                evidence={
                    "blocked_environment_ids": environment_validation.get("blocked_environment_ids", []),
                    "readiness_blockers": environment_validation.get("readiness_blockers", []),
                },
            )
        )
    if "full_analysis_resource_locks_not_complete" in p1_issues:
        p1.append(
            _issue(
                "P1",
                "full_analysis_resource_locks_not_complete",
                "resource_readiness",
                "Full analysis resources/tools remain blocked until version/hash/license/cache evidence is complete.",
                evidence={
                    "blocked_resource_ids": resource_validation.get("blocked_resource_ids", []),
                    "warnings": resource_validation.get("warnings", []),
                },
            )
        )
    if "formal_algorithms_not_universally_migrated_to_isolated_standard_worker" in p1_issues:
        p1.append(
            _issue(
                "P1",
                "formal_algorithms_not_universally_migrated_to_isolated_standard_worker",
                "standard_worker_migration_matrix",
                "Formal algorithms still have pending isolated standard-worker migration rows.",
                evidence={
                    "formal_pending_count": standard_worker_migration_matrix.get("formal_pending_count"),
                    "full_blocked_count": standard_worker_migration_matrix.get("full_blocked_count"),
                    "evidence_entry_count": standard_worker_migration_matrix.get("evidence_entry_count"),
                },
            )
        )
    p2_requirement_ids = {"RARCH-03", "RARCH-08", "RARCH-09", "RARCH-16", "RARCH-17"}
    p3_requirement_ids = {"RARCH-04", "RARCH-12", "RARCH-13", "RARCH-14", "RARCH-15", "RARCH-18"}
    p2 = [
        _issue_from_requirement("P2", row)
        for row in requirement_rows
        if row.get("requirement_id") in p2_requirement_ids and row.get("status") == "warn"
    ]
    p3 = [
        _issue_from_requirement("P3", row)
        for row in requirement_rows
        if row.get("requirement_id") in p3_requirement_ids and row.get("status") == "warn"
    ]
    return {"P0": p0, "P1": p1, "P2": p2, "P3": p3}


def _issue_from_requirement(priority: str, row: dict[str, Any]) -> dict[str, Any]:
    return _issue(
        priority,
        str(row.get("requirement_id") or "unknown_requirement"),
        str(row.get("evidence") or ""),
        str(row.get("label") or ""),
        evidence={
            "status": row.get("status"),
            "warnings": row.get("warnings", []),
            "blockers": row.get("blockers", []),
        },
    )


def _issue(priority: str, issue_id: str, source: str, summary: str, *, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "priority": priority,
        "issue_id": issue_id,
        "source": source,
        "summary": summary,
        "evidence": evidence or {},
    }


def _top_architecture_risks(priority_issues: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for priority in ("P0", "P1", "P2", "P3"):
        for issue in priority_issues.get(priority, []):
            risks.append(
                {
                    "priority": priority,
                    "risk_id": str(issue.get("issue_id") or ""),
                    "source": str(issue.get("source") or ""),
                    "summary": str(issue.get("summary") or ""),
                    "evidence": issue.get("evidence", {}),
                }
            )
    return risks[:5]
