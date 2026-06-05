from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .registry import REPO_ROOT, load_analysis_module_registry
from .resources import validate_analysis_environment_registry, validate_analysis_resource_manifest


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
            warnings=["formal_full_migration_pending_for_multiple_modules"],
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
    p1 = _p1_issues(environment_validation, resource_validation)
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
        "environment_validation": environment_validation,
        "resource_validation": resource_validation,
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


def _p1_issues(environment_validation: dict[str, Any], resource_validation: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if environment_validation.get("full_mode_ready") is not True:
        issues.append("full_analysis_environment_locks_not_restored")
    if resource_validation.get("full_mode_ready") is not True:
        issues.append("full_analysis_resource_locks_not_complete")
    issues.append("formal_algorithms_not_universally_migrated_to_isolated_standard_worker")
    return issues
