from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import REPO_ROOT, load_analysis_module_registry
from .resources import validate_analysis_environment_registry, validate_analysis_resource_manifest
from .standard_package import validate_standard_result_package


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
    standard_worker_migration_matrix = build_standard_worker_migration_matrix(registry)
    environment_validation = validate_analysis_environment_registry(module_registry=registry)
    resource_validation = validate_analysis_resource_manifest()
    active_install_hits = _active_runtime_install_hits()
    heavy_default_hits = _default_dependency_hits()
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
            "No active runtime R package install commands",
            "pass" if not active_install_hits else "fail",
            "active non-legacy app/analysis/scripts/config scan",
            blockers=[f"runtime_install_command_found:{item}" for item in active_install_hits],
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
        "standard_worker_migration_matrix": standard_worker_migration_matrix,
        "environment_validation": environment_validation,
        "resource_validation": resource_validation,
    }


def build_standard_worker_migration_matrix(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Summarize module-by-module migration toward the standard worker boundary."""

    payload = registry if isinstance(registry, dict) else load_analysis_module_registry()
    modules = [item for item in payload.get("modules", []) if isinstance(item, dict)]
    standard_entrypoint = str(payload.get("standard_entrypoint") or "analysis/runners/run_module.R")
    rows = [_standard_worker_migration_row(module, standard_entrypoint=standard_entrypoint) for module in modules]
    formal_pending = [row for row in rows if row["formal_worker_status"] != "migrated_to_isolated_standard_worker"]
    full_blocked = [row for row in rows if row["full_status"] == "blocked"]
    return {
        "schema_version": "biomedpilot.analysis.standard_worker_migration_matrix.v1",
        "status": "passed" if not formal_pending and not full_blocked else "partial",
        "standard_entrypoint": standard_entrypoint,
        "module_count": len(rows),
        "formal_pending_count": len(formal_pending),
        "full_blocked_count": len(full_blocked),
        "rows": rows,
        "migration_policy": "module_by_module_standard_worker_migration_required",
        "boundary": "matrix_is_read_only_no_worker_execution",
    }


def build_analysis_remediation_queue(status: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic, read-only remediation queue for architecture gaps.

    The queue is advisory. It does not execute workers, mutate project storage,
    install packages, download resources, or mark full mode as ready.
    """

    snapshot = status if isinstance(status, dict) else build_analysis_architecture_status()
    p1_issues = [str(item) for item in snapshot.get("p1_issues", []) if item]
    issue_items = {
        "full_analysis_environment_locks_not_restored": {
            "item_id": "restore_full_analysis_environment_locks",
            "title": "Restore full analysis environment locks",
            "source_issue": "full_analysis_environment_locks_not_restored",
            "priority": "P1",
            "status": "blocked",
            "recommended_files": [
                "analysis/registry/analysis_environments.json",
                "renv/renv.bio-full.lock",
                "renv/renv.spatial-full.lock",
                "renv/renv.chem-full.lock",
                "docker/Dockerfile.r-bio-full",
                "docker/Dockerfile.r-spatial-full",
                "docker/Dockerfile.r-chem-full",
                "docker/Dockerfile.r-chem-gpu",
            ],
            "required_evidence": [
                "full environment locks restored from controlled external analysis environments",
                "Docker image build evidence captured outside default app-dev",
                "validate_analysis_environment_registry.full_mode_ready becomes true",
            ],
            "boundary": "detect-first external full environments only; default app-dev remains lightweight",
        },
        "full_analysis_resource_locks_not_complete": {
            "item_id": "lock_full_analysis_resources",
            "title": "Lock full analysis resources",
            "source_issue": "full_analysis_resource_locks_not_complete",
            "priority": "P1",
            "status": "blocked",
            "recommended_files": [
                "analysis/resources/manifest.json",
                "external_analysis_resources/",
            ],
            "required_evidence": [
                "each full resource declares version, source, hash, license, and cache path",
                "large resources are prelocked or explicitly imported before full mode",
                "validate_analysis_resource_manifest.full_mode_ready becomes true",
            ],
            "boundary": "resource lock only; no runtime database fetch in user request flow",
        },
        "formal_algorithms_not_universally_migrated_to_isolated_standard_worker": {
            "item_id": "migrate_formal_algorithms_to_isolated_standard_worker",
            "title": "Migrate formal algorithms to isolated standard worker",
            "source_issue": "formal_algorithms_not_universally_migrated_to_isolated_standard_worker",
            "priority": "P1",
            "status": "blocked",
            "recommended_files": [
                "app/bioinformatics/",
                "analysis/runners/run_module.R",
                "analysis/modules/",
                "analysis/schemas/input/module_input.schema.json",
                "analysis/schemas/output/result_package.schema.json",
            ],
            "required_evidence": [
                "validate_standard_worker_migration_evidence.status=passed",
                "selected formal module has formal_worker_status=migrated_to_isolated_standard_worker",
                "selected formal module executes through the task bridge and standard worker boundary",
                "standard package includes result.json, provenance.json, tables, plots, reports, and logs",
                "frontend consumes the standard package instead of module-private output paths",
            ],
            "boundary": "one module at a time; sidecar-only legacy adapter output is not full migration",
        },
    }
    items = [issue_items[issue] for issue in p1_issues if issue in issue_items]
    return {
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


def _standard_worker_migration_row(module: dict[str, Any], *, standard_entrypoint: str) -> dict[str, Any]:
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
    formal_worker_status = "migrated_to_isolated_standard_worker" if full_supported and lite_uses_standard_worker else "pending_standard_worker_migration"
    if current_adapter_status.startswith("contract_required"):
        formal_worker_status = "contract_only_pending_standard_worker_migration"
    return {
        "module_id": module_id,
        "title": str(module.get("title") or module_id),
        "mock_status": "passed" if mock_ready else "blocked",
        "lite_status": "standard_worker_lite_ready" if lite_uses_standard_worker else "blocked",
        "full_status": "ready_unverified" if full_supported else "blocked",
        "formal_worker_status": formal_worker_status,
        "current_adapter_status": current_adapter_status,
        "standard_entrypoint": standard_entrypoint if lite_uses_standard_worker else "",
        "analysis_environment": str(module.get("analysis_environment") or ""),
        "full_environment": str(module.get("full_environment") or ""),
        "full_blocker": str(full.get("blocker") or ""),
        "result_index_task_types": [str(item) for item in module.get("result_index_task_types", []) if item],
        "risk": "P1" if formal_worker_status != "migrated_to_isolated_standard_worker" else "none",
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
    for module_id in ("docking", "molecular_dynamics"):
        path = REPO_ROOT / "analysis" / "modules" / module_id / "module.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        policy = str(payload.get("external_tool_policy") or "")
        if "R_adapter_calls_" not in policy:
            return False
        if payload.get("analysis_environment") not in {"r-chem-full", "r-chem-gpu"}:
            return False
    return True


def _active_runtime_install_hits() -> list[str]:
    roots = [REPO_ROOT / "app", REPO_ROOT / "analysis", REPO_ROOT / "scripts", REPO_ROOT / "config"]
    hits: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or _is_excluded_source(path):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for pattern in BANNED_RUNTIME_INSTALL_PATTERNS:
                if pattern in text:
                    hits.append(f"{path.relative_to(REPO_ROOT)}:{pattern}")
    return sorted(set(hits))


def _default_dependency_hits() -> list[str]:
    paths = [
        REPO_ROOT / "requirements.txt",
        REPO_ROOT / "pyproject.toml",
        REPO_ROOT / "docker" / "Dockerfile.app-dev",
        REPO_ROOT / "renv" / "renv.app.lock",
    ]
    hits: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in HEAVY_DEFAULT_DEPENDENCY_NAMES:
            if name in text:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{name}")
    return sorted(set(hits))


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
