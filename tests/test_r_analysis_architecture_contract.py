from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from app.analysis_runtime.architecture_status import (
    build_analysis_architecture_status,
    build_environment_artifact_matrix,
    build_external_tool_adapter_matrix,
    build_frontend_standard_package_consumption_matrix,
    build_full_analysis_activation_gate,
    build_full_activation_module_matrix,
    build_legacy_sidecar_transition_matrix,
    build_lite_task_bridge_coverage_matrix,
    build_module_interface_matrix,
    build_module_mode_readiness_matrix,
    build_reproducibility_provenance_matrix,
    build_resource_artifact_matrix,
    build_standard_worker_entrypoint_matrix,
    build_task_system_boundary_matrix,
    build_analysis_remediation_queue,
    build_standard_worker_migration_matrix,
    load_standard_worker_migration_evidence_registry,
    validate_standard_worker_migration_evidence_registry,
    validate_standard_worker_migration_evidence,
)
from app.analysis_runtime.standard_package import validate_standard_result_package
from app.analysis_runtime.resources import (
    full_mode_environment_blockers,
    full_mode_resource_blockers,
    load_analysis_environment_lock_evidence_registry,
    load_analysis_resource_lock_evidence_registry,
    validate_analysis_environment_lock_evidence,
    validate_analysis_environment_lock_evidence_registry,
    validate_analysis_resource_lock_evidence,
    validate_analysis_resource_lock_evidence_registry,
    validate_analysis_environment_registry,
    validate_analysis_resource_manifest,
)
from app.analysis_runtime.registry import build_result_index_task_type_module_map


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_MODULES = {
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
}
REQUIRED_FULL_RESOURCE_IDS = [
    "reactome_full",
    "msigdb_full",
    "go_full",
    "kegg_full",
    "orgdb_human_full",
    "spatial_reference_full",
    "cellchatdb_full",
    "autodock_vina_tool",
    "docking_template_bundle",
    "gromacs_tool",
    "md_forcefield_template_bundle",
]
REQUIRED_FULL_ENVIRONMENT_IDS = [
    "r-bio-full",
    "r-spatial-full",
    "r-chem-full",
    "r-chem-gpu",
]
REQUIRED_STANDARD_WORKER_FORBIDDEN_EVIDENCE_SOURCES = [
    "mock_fixture_package",
    "lite_testing_level_package",
    "legacy_service_adapter_sidecar",
    "module_private_output_path",
]
RESULT_PAYLOAD_SCHEMA = "analysis/schemas/output/result.schema.json"
PROVENANCE_PAYLOAD_SCHEMA = "analysis/schemas/output/provenance.schema.json"


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_candidate_standard_worker_package(
    tmp_path: Path,
    *,
    result_status: str,
    result_semantics: str,
    environment_status: str,
    environment_ready: bool,
    resource_ready: bool,
    result_blockers: list[str] | None = None,
) -> Path:
    package_dir = tmp_path / "candidate-standard-worker-package"
    for dirname in ("tables", "plots", "reports", "logs"):
        (package_dir / dirname).mkdir(parents=True, exist_ok=True)
    result_blockers = list(result_blockers or [])
    task_id = "deg-full-standard-worker-task"
    now = "2026-06-05T00:00:00+00:00"
    environment_blockers = [] if environment_ready else ["analysis_environment_renv_lock_not_restored:r-bio-full:scaffold_only_not_restored"]
    resource_blockers = [] if resource_ready else ["analysis_resource_not_locked:reactome_full"]
    _write_json(
        package_dir / "result.json",
        {
            "schema_version": "biomedpilot.analysis.result.v1",
            "module_id": "deg",
            "mode": "full",
            "task_id": task_id,
            "status": result_status,
            "result_semantics": result_semantics,
            "summary": {"message": "candidate full standard worker package"},
            "tables": [],
            "plots": [],
            "reports": [],
            "blockers": result_blockers,
            "warnings": [],
            "created_at": now,
        },
    )
    _write_json(
        package_dir / "provenance.json",
        {
            "schema_version": "biomedpilot.analysis.provenance.v1",
            "module_id": "deg",
            "mode": "full",
            "task_id": task_id,
            "created_at": now,
            "input_hash": "input-hash",
            "parameter_hash": "parameter-hash",
            "random_seed": 7,
            "engine": {"name": "biomedpilot_standard_r_worker", "version": "v1"},
            "runtime": {
                "r_version": "R 4.4.2",
                "bioconductor_version": "3.20",
                "package_versions": {"limma": "3.62.2"},
                "external_tool_versions": {},
            },
            "command": "task-center -> analysis/runners/run_module.R",
            "analysis_environment": {
                "schema_version": "biomedpilot.analysis_environment_snapshot.v1",
                "status": environment_status,
                "mode": "full",
                "module_id": "deg",
                "environment_id": "r-bio-full",
                "dockerfile": "docker/Dockerfile.r-bio-full",
                "renv_lock": "renv/renv.bio-full.lock",
                "allows_heavy_analysis_dependencies": True,
                "resource_lock_required": True,
                "external_tool_lock_required": False,
                "full_mode_requires_isolated_environment": True,
                "environment_registry_is_authoritative": True,
                "runtime_package_install": "forbidden",
                "runtime_resource_download": "forbidden",
                "module_manifest": "analysis/modules/deg/module.json",
                "environment_lock_status": {
                    "ready": environment_ready,
                    "blockers": environment_blockers,
                },
                "resource_lock_status": {
                    "full_mode_ready": resource_ready,
                    "required_resource_ids": [],
                    "blocked_resource_ids": [],
                    "blockers": resource_blockers,
                    "warnings": [],
                },
            },
            "worker_boundary": {
                "boundary_type": "standard_r_worker",
                "task_system_invocation": "task_center_registered",
                "migration_status": "standard_worker_contract",
            },
        },
    )
    _write_json(
        package_dir / "module_input.json",
        {
            "schema_version": "biomedpilot.analysis.module_input.v1",
            "module_id": "deg",
            "mode": "full",
            "task_id": task_id,
            "project_id": "migration-evidence-test",
            "inputs": {"input_package_id": "input-1", "source_dataset_id": "dataset-1"},
            "parameters": {"comparison": "case_vs_control"},
            "runtime": {"random_seed": 7, "requested_environment": "r-bio-full"},
        },
    )
    _write_json(
        package_dir / "logs" / "worker_invocation.json",
        {
            "schema_version": "biomedpilot.analysis.worker_invocation.v1",
            "created_at": now,
            "module_id": "deg",
            "mode": "full",
            "task_id": task_id,
            "worker_backend": "rscript",
            "invocation_status": "completed",
            "standard_worker_entrypoint": "analysis/runners/run_module.R",
            "input_manifest": "module_input.json",
            "output_contract": "standard_result_package",
            "runtime_install_policy": "forbidden",
            "resource_download_policy": "forbidden",
            "returncode": 0,
            "command": ["Rscript", "analysis/runners/run_module.R"],
            "stdout": "",
            "stderr": "",
            "blockers": [],
            "worker_boundary": {
                "boundary_type": "standard_r_worker",
                "task_system_invocation": "task_center_registered",
                "migration_status": "standard_worker_contract",
            },
        },
    )
    (package_dir / "logs" / "worker.log").write_text(f"{now} status={result_status}\n", encoding="utf-8")
    return package_dir


def _standard_worker_migration_evidence(package_dir: Path) -> dict[str, object]:
    return {
        "schema_version": "biomedpilot.analysis.standard_worker_migration_evidence.v1",
        "module_id": "deg",
        "mode": "full",
        "task_id": "deg-full-standard-worker-task",
        "result_package_dir": str(package_dir),
        "frontend_consumes_standard_package": True,
        "result_index_registered": True,
        "formal_result_semantics_preserved": True,
        "required_result_status": "passed",
        "required_result_semantics": "formal_computed_result",
        "required_engine_name": "biomedpilot_standard_r_worker",
        "required_analysis_environment_status": "passed",
        "required_worker_boundary": "standard_r_worker",
        "required_task_system_invocation": "task_center_registered",
        "required_worker_migration_status": "standard_worker_contract",
        "forbidden_evidence_sources": REQUIRED_STANDARD_WORKER_FORBIDDEN_EVIDENCE_SOURCES,
    }


def rscript_path() -> str:
    path = shutil.which("Rscript")
    if path is None:
        pytest.skip("Rscript is not available in this environment")
    return path


def modules_lite_full_boundaries(module_registry: dict[str, object]) -> dict[str, tuple[str, str]]:
    selected = {"spatial_transcriptomics", "docking", "molecular_dynamics"}
    boundaries: dict[str, tuple[str, str]] = {}
    for module in module_registry["modules"]:  # type: ignore[index]
        module_id = str(module["module_id"])  # type: ignore[index]
        if module_id in selected:
            boundaries[module_id] = (
                str(module["modes"]["lite"].get("environment")),  # type: ignore[index]
                str(module["full_environment"]),  # type: ignore[index]
            )
    return boundaries


def test_analysis_registry_declares_standard_modules_modes_and_package_contract() -> None:
    registry = read_json(ROOT / "analysis" / "registry" / "analysis_modules.json")

    assert registry["schema_version"] == "biomedpilot.analysis_modules.v1"
    assert registry["standard_entrypoint"] == "analysis/runners/run_module.R"
    standard_package = registry["standard_result_package"]
    assert standard_package["required_files"] == ["result.json", "provenance.json"]
    assert standard_package["required_directories"] == ["tables", "plots", "reports", "logs"]
    assert standard_package["payload_schemas"] == {
        "result.json": RESULT_PAYLOAD_SCHEMA,
        "provenance.json": PROVENANCE_PAYLOAD_SCHEMA,
    }
    modules = {item["module_id"]: item for item in registry["modules"]}  # type: ignore[index]
    assert REQUIRED_MODULES <= set(modules)
    for module_id, module in modules.items():
        modes = module["modes"]
        assert modes["mock"]["supported"] is True
        assert (ROOT / modes["mock"]["fixture_input"]).is_file()
        assert (ROOT / modes["mock"]["fixture_output_package"]).is_dir()
        assert "lite" in modes
        assert "full" in modes
        assert module["result_package_contract"] == "analysis/schemas/output/result_package.schema.json"
        assert module["result_payload_schema"] == RESULT_PAYLOAD_SCHEMA
        assert module["provenance_payload_schema"] == PROVENANCE_PAYLOAD_SCHEMA
        assert (ROOT / module["result_payload_schema"]).is_file()
        assert (ROOT / module["provenance_payload_schema"]).is_file()
        assert module["analysis_environment"]
        assert (ROOT / module["module_manifest"]).exists()


def test_analysis_registry_owns_result_index_task_type_aliases() -> None:
    registry = read_json(ROOT / "analysis" / "registry" / "analysis_modules.json")
    modules = {item["module_id"]: item for item in registry["modules"]}  # type: ignore[index]
    task_type_map = build_result_index_task_type_module_map(registry=registry)

    assert task_type_map["deg"] == "deg"
    assert task_type_map["recomputed_deg"] == "deg"
    assert task_type_map["ora"] == "enrichment"
    assert task_type_map["gsea_preranked"] == "enrichment"
    assert task_type_map["survival_km_logrank"] == "survival"
    assert task_type_map["cox_univariate"] == "survival"
    assert task_type_map["immune_tme_scoring"] == "immune_infiltration"
    assert task_type_map["correlation"] == "correlation"
    for task_type, module_id in task_type_map.items():
        assert task_type == task_type.lower()
        assert module_id in modules


def test_registered_module_manifests_declare_worker_environment_and_package_contract() -> None:
    registry = read_json(ROOT / "analysis" / "registry" / "analysis_modules.json")
    modules = {item["module_id"]: item for item in registry["modules"]}  # type: ignore[index]

    for module_id, module in modules.items():
        manifest_path = ROOT / module["module_manifest"]
        manifest = read_json(manifest_path)
        modes = manifest["modes"]
        environment = manifest["environment"]
        dependency_policy = manifest["dependency_policy"]

        assert manifest["schema_version"] == "biomedpilot.analysis_module_manifest.v1"
        assert manifest["module_id"] == module_id
        assert manifest["standard_entrypoint"] == registry["standard_entrypoint"]
        assert manifest["input_schema"] == "analysis/schemas/input/module_input.schema.json"
        assert manifest["output_schema"] == "analysis/schemas/output/result_package.schema.json"
        assert manifest["result_package_contract"] == "analysis/schemas/output/result_package.schema.json"
        assert manifest["result_payload_schema"] == RESULT_PAYLOAD_SCHEMA
        assert manifest["provenance_payload_schema"] == PROVENANCE_PAYLOAD_SCHEMA
        assert manifest["result_payload_schema"] == module["result_payload_schema"]
        assert manifest["provenance_payload_schema"] == module["provenance_payload_schema"]
        assert manifest["result_package_required"] == ["result.json", "provenance.json", "tables", "plots", "reports", "logs"]
        assert modes["mock"]["supported"] is True
        assert (ROOT / modes["mock"]["fixture_input"]).is_file()
        assert (ROOT / modes["mock"]["fixture_output_package"]).is_dir()
        if module_id in {"deg", "enrichment", "survival", "univariate", "multivariate", "immune_infiltration", "correlation", "spatial_transcriptomics", "docking", "molecular_dynamics"}:
            assert modes["lite"]["supported"] is True
            assert modes["lite"]["runner"] == registry["standard_entrypoint"]
            assert modes["lite"]["worker_backend"] == "rscript"
            assert (ROOT / modes["lite"]["fixture_input"]).is_file()
        else:
            assert modes["lite"]["supported"] is False
        assert modes["full"]["supported"] is False
        assert environment["app_dev"] == "docker/Dockerfile.app-dev"
        assert (ROOT / manifest["dockerfile"]).exists()
        assert (ROOT / manifest["environment_lock"]).exists()
        assert dependency_policy == {
            "detection": "detect_first",
            "runtime_install": "forbidden",
            "default_app_dependency": False,
        }


def test_per_module_mock_fixtures_are_standard_result_packages() -> None:
    registry = read_json(ROOT / "analysis" / "registry" / "analysis_modules.json")

    for module in registry["modules"]:  # type: ignore[index]
        module_id = module["module_id"]
        mode_policy = module["modes"]["mock"]
        fixture_input = read_json(ROOT / mode_policy["fixture_input"])
        fixture_package = ROOT / mode_policy["fixture_output_package"]
        result = read_json(fixture_package / "result.json")
        provenance = read_json(fixture_package / "provenance.json")

        assert fixture_input["schema_version"] == "biomedpilot.analysis.module_input.v1"
        assert fixture_input["module_id"] == module_id
        assert fixture_input["mode"] == "mock"
        assert result["module_id"] == module_id
        assert result["mode"] == "mock"
        assert result["status"] == "passed"
        assert result["result_semantics"] == "testing_level"
        assert "mock_result_not_scientific_output" in result["warnings"]
        assert provenance["module_id"] == module_id
        assert provenance["runtime"]["r_version"] == "not_required_for_mock"
        for dirname in ("tables", "plots", "reports", "logs"):
            assert (fixture_package / dirname).is_dir()


def test_analysis_environment_split_scaffold_exists_without_claiming_full_readiness() -> None:
    environment_registry = read_json(ROOT / "analysis" / "registry" / "analysis_environments.json")
    dockerfiles = {
        "docker/Dockerfile.app-dev",
        "docker/Dockerfile.r-bio-core",
        "docker/Dockerfile.r-bio-full",
        "docker/Dockerfile.r-spatial-full",
        "docker/Dockerfile.r-chem-full",
        "docker/Dockerfile.r-chem-gpu",
    }
    locks = {
        "renv/renv.app.lock",
        "renv/renv.bio-core.lock",
        "renv/renv.bio-full.lock",
        "renv/renv.spatial-full.lock",
        "renv/renv.chem-full.lock",
    }

    assert environment_registry["schema_version"] == "biomedpilot.analysis_environments.v1"
    assert environment_registry["policy"] == {
        "default_app_dependency": False,
        "runtime_package_install": "forbidden",
        "runtime_resource_download": "forbidden",
        "full_mode_requires_isolated_environment": True,
        "environment_registry_is_authoritative": True,
    }
    for relative in dockerfiles:
        text = (ROOT / relative).read_text(encoding="utf-8")
        assert "runtime-package-install=\"forbidden\"" in text
        assert (ROOT / relative).exists()
    for relative in locks:
        lock = read_json(ROOT / relative)
        assert lock["Packages"] == {}
        assert lock["BioMedPilotPolicy"]["status"] == "scaffold_only_not_restored"  # type: ignore[index]
        assert lock["BioMedPilotPolicy"]["runtime_package_install"] == "forbidden"  # type: ignore[index]


def test_locked_analysis_resource_requires_schema_valid_lock_evidence() -> None:
    manifest = read_json(ROOT / "analysis" / "resources" / "manifest.json")
    evidence = read_json(ROOT / "analysis" / "resources" / "locks" / "mock_fixture_builtin_v1.lock.json")
    validation = validate_analysis_resource_lock_evidence("mock_fixture_builtin_v1", evidence, manifest=manifest)
    manifest_validation = validate_analysis_resource_manifest(manifest)

    assert validation["schema_version"] == "biomedpilot.analysis.resource_lock_evidence_validation.v1"
    assert validation["status"] == "passed"
    assert validation["blockers"] == []
    assert manifest_validation["status"] == "passed"
    assert manifest_validation["evidence_registry_status"] == "passed"
    assert manifest_validation["evidence_registry_entry_count"] == 0
    assert "mock_fixture_builtin_v1" in manifest_validation["locked_resource_ids"]


def test_full_resource_lock_evidence_requires_sha256_hash_algorithm() -> None:
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resource = manifest["resources"][1]  # type: ignore[index]
    resource.update(
        {
            "version": "2026.05",
            "hash": "abc123",
            "license": "approved_test_license",
            "status": "locked",
        }
    )
    validation = validate_analysis_resource_lock_evidence(
        "reactome_full",
        {
            "schema_version": "biomedpilot.analysis.resource_lock_evidence.v1",
            "resource_id": "reactome_full",
            "status": "locked",
            "version": "2026.05",
            "source": "Reactome / Bioconductor package metadata",
            "hash": {"algorithm": "repository_fixture", "value": "abc123"},
            "license": "approved_test_license",
            "cache_path": "external_analysis_resources/reactome",
            "runtime_download_allowed": False,
            "approved_for_modules": ["enrichment"],
            "evidence_files": ["analysis/resources/manifest.json"],
        },
        manifest=manifest,
    )

    assert validation["status"] == "blocked"
    assert "analysis_resource_lock_evidence_hash_algorithm_not_allowed" in validation["blockers"]
    assert "analysis_resource_lock_evidence_repository_fixture_hash_for_full_resource" in validation["blockers"]


def test_full_resource_lock_evidence_requires_sha256_hex_value() -> None:
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resource = manifest["resources"][1]  # type: ignore[index]
    resource.update(
        {
            "version": "2026.05",
            "hash": "not-a-sha256",
            "license": "approved_test_license",
            "status": "locked",
        }
    )
    validation = validate_analysis_resource_lock_evidence(
        "reactome_full",
        {
            "schema_version": "biomedpilot.analysis.resource_lock_evidence.v1",
            "resource_id": "reactome_full",
            "status": "locked",
            "version": "2026.05",
            "source": "Reactome / Bioconductor package metadata",
            "hash": {"algorithm": "sha256", "value": "not-a-sha256"},
            "license": "approved_test_license",
            "cache_path": "external_analysis_resources/reactome",
            "runtime_download_allowed": False,
            "approved_for_modules": ["enrichment"],
            "evidence_files": ["analysis/resources/manifest.json"],
        },
        manifest=manifest,
    )

    assert validation["status"] == "blocked"
    assert "analysis_resource_lock_evidence_hash_value_not_sha256" in validation["blockers"]


def test_full_resource_lock_evidence_hash_must_match_cache_path(tmp_path: Path) -> None:
    cache_file = tmp_path / "reactome_resource_bundle.gmt"
    cache_file.write_text("TERM1\tDescription\tGENE1\tGENE2\n", encoding="utf-8")
    cache_hash = hashlib.sha256(cache_file.read_bytes()).hexdigest()
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resource = manifest["resources"][1]  # type: ignore[index]
    resource.update(
        {
            "version": "2026.05",
            "hash": cache_hash,
            "license": "approved_test_license",
            "cache_path": str(cache_file),
            "status": "locked",
        }
    )
    validation = validate_analysis_resource_lock_evidence(
        "reactome_full",
        {
            "schema_version": "biomedpilot.analysis.resource_lock_evidence.v1",
            "resource_id": "reactome_full",
            "status": "locked",
            "version": "2026.05",
            "source": "Reactome / Bioconductor package metadata",
            "hash": {"algorithm": "sha256", "value": cache_hash},
            "cache_content": {"non_empty": True, "content_source": "prelocked_cache_path", "file_count": 1},
            "license": "approved_test_license",
            "cache_path": str(cache_file),
            "runtime_download_allowed": False,
            "approved_for_modules": ["enrichment"],
            "evidence_files": ["analysis/resources/manifest.json"],
        },
        manifest=manifest,
    )

    assert validation["status"] == "passed"
    assert validation["blockers"] == []


def test_full_resource_lock_evidence_blocks_cache_hash_mismatch(tmp_path: Path) -> None:
    cache_file = tmp_path / "reactome_resource_bundle.gmt"
    cache_file.write_text("TERM1\tDescription\tGENE1\tGENE2\n", encoding="utf-8")
    wrong_hash = "c" * 64
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resource = manifest["resources"][1]  # type: ignore[index]
    resource.update(
        {
            "version": "2026.05",
            "hash": wrong_hash,
            "license": "approved_test_license",
            "cache_path": str(cache_file),
            "status": "locked",
        }
    )
    validation = validate_analysis_resource_lock_evidence(
        "reactome_full",
        {
            "schema_version": "biomedpilot.analysis.resource_lock_evidence.v1",
            "resource_id": "reactome_full",
            "status": "locked",
            "version": "2026.05",
            "source": "Reactome / Bioconductor package metadata",
            "hash": {"algorithm": "sha256", "value": wrong_hash},
            "license": "approved_test_license",
            "cache_path": str(cache_file),
            "runtime_download_allowed": False,
            "approved_for_modules": ["enrichment"],
            "evidence_files": ["analysis/resources/manifest.json"],
        },
        manifest=manifest,
    )

    assert validation["status"] == "blocked"
    assert "analysis_resource_lock_evidence_hash_mismatch" in validation["blockers"]


def test_full_resource_lock_evidence_blocks_cache_file_count_mismatch(tmp_path: Path) -> None:
    cache_dir = tmp_path / "reactome-cache"
    cache_dir.mkdir()
    first = cache_dir / "reactome_terms.gmt"
    second = cache_dir / "reactome_metadata.json"
    first.write_text("TERM1\tDescription\tGENE1\tGENE2\n", encoding="utf-8")
    second.write_text('{"version":"2026.05"}\n', encoding="utf-8")
    digest = hashlib.sha256()
    for child in sorted(item for item in cache_dir.rglob("*") if item.is_file()):
        relative = child.relative_to(cache_dir).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(child.read_bytes())
        digest.update(b"\0")
    cache_hash = digest.hexdigest()
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resource = manifest["resources"][1]  # type: ignore[index]
    resource.update(
        {
            "version": "2026.05",
            "hash": cache_hash,
            "license": "approved_test_license",
            "cache_path": str(cache_dir),
            "status": "locked",
        }
    )
    validation = validate_analysis_resource_lock_evidence(
        "reactome_full",
        {
            "schema_version": "biomedpilot.analysis.resource_lock_evidence.v1",
            "resource_id": "reactome_full",
            "status": "locked",
            "version": "2026.05",
            "source": "Reactome / Bioconductor package metadata",
            "hash": {"algorithm": "sha256", "value": cache_hash},
            "cache_content": {"non_empty": True, "content_source": "prelocked_cache_path", "file_count": 1},
            "license": "approved_test_license",
            "cache_path": str(cache_dir),
            "runtime_download_allowed": False,
            "approved_for_modules": ["enrichment"],
            "evidence_files": ["analysis/resources/manifest.json"],
        },
        manifest=manifest,
    )

    assert validation["status"] == "blocked"
    assert "analysis_resource_lock_evidence_cache_content_file_count_mismatch" in validation["blockers"]


def test_full_resource_lock_evidence_blocks_empty_cache_directory(tmp_path: Path) -> None:
    cache_dir = tmp_path / "reactome-empty-cache"
    cache_dir.mkdir()
    empty_dir_hash = hashlib.sha256().hexdigest()
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resource = manifest["resources"][1]  # type: ignore[index]
    resource.update(
        {
            "version": "2026.05",
            "hash": empty_dir_hash,
            "license": "approved_test_license",
            "cache_path": str(cache_dir),
            "status": "locked",
        }
    )
    validation = validate_analysis_resource_lock_evidence(
        "reactome_full",
        {
            "schema_version": "biomedpilot.analysis.resource_lock_evidence.v1",
            "resource_id": "reactome_full",
            "status": "locked",
            "version": "2026.05",
            "source": "Reactome / Bioconductor package metadata",
            "hash": {"algorithm": "sha256", "value": empty_dir_hash},
            "license": "approved_test_license",
            "cache_path": str(cache_dir),
            "runtime_download_allowed": False,
            "approved_for_modules": ["enrichment"],
            "evidence_files": ["analysis/resources/manifest.json"],
        },
        manifest=manifest,
    )

    assert validation["status"] == "blocked"
    assert "analysis_resource_lock_evidence_cache_path_empty" in validation["blockers"]


def test_analysis_resource_lock_evidence_registry_is_authoritative_and_empty_by_default() -> None:
    registry = load_analysis_resource_lock_evidence_registry()
    validation = validate_analysis_resource_lock_evidence_registry(registry)

    assert registry["schema_version"] == "biomedpilot.analysis.resource_lock_evidence_registry.v1"
    assert registry["policy"]["registry_is_authoritative"] is True
    assert registry["policy"]["expected_resource_ids_are_authoritative"] is True
    assert registry["expected_resource_ids"] == REQUIRED_FULL_RESOURCE_IDS
    assert registry["evidence_entries"] == []
    assert validation["schema_version"] == "biomedpilot.analysis.resource_lock_evidence_registry_validation.v1"
    assert validation["status"] == "passed"
    assert validation["entry_count"] == 0
    assert validation["expected_resource_ids"] == REQUIRED_FULL_RESOURCE_IDS
    assert validation["missing_resource_ids"] == REQUIRED_FULL_RESOURCE_IDS
    assert validation["missing_count"] == len(REQUIRED_FULL_RESOURCE_IDS)


def test_locked_analysis_resource_can_use_registry_evidence_path() -> None:
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resource = manifest["resources"][0]  # type: ignore[index]
    resource.pop("lock_evidence")
    evidence_registry = {
        "schema_version": "biomedpilot.analysis.resource_lock_evidence_registry.v1",
        "policy": {
            "registry_is_authoritative": True,
            "expected_resource_ids_are_authoritative": True,
            "locked_resource_requires_schema_valid_evidence": True,
            "manual_scoped_resource_lock_only": True,
            "runtime_download_allowed": False,
        },
        "expected_resource_ids": REQUIRED_FULL_RESOURCE_IDS,
        "evidence_entries": [
            {
                "resource_id": "mock_fixture_builtin_v1",
                "evidence_path": "analysis/resources/locks/mock_fixture_builtin_v1.lock.json",
            }
        ],
    }

    registry_validation = validate_analysis_resource_lock_evidence_registry(
        evidence_registry,
        manifest=manifest,
    )
    manifest_validation = validate_analysis_resource_manifest(
        manifest,
        resource_lock_evidence_registry=evidence_registry,
    )

    assert registry_validation["status"] == "passed"
    assert registry_validation["registered_resource_ids"] == ["mock_fixture_builtin_v1"]
    assert manifest_validation["status"] == "passed"
    assert manifest_validation["evidence_registry_entry_count"] == 1


def test_analysis_resource_lock_evidence_registry_blocks_expected_scope_drift() -> None:
    registry = deepcopy(load_analysis_resource_lock_evidence_registry())
    registry["expected_resource_ids"] = ["reactome_full"]

    validation = validate_analysis_resource_lock_evidence_registry(registry)

    assert validation["status"] == "blocked"
    assert "analysis_resource_lock_evidence_registry_expected_resource_ids_mismatch" in validation["blockers"]
    assert validation["expected_resource_ids"] == REQUIRED_FULL_RESOURCE_IDS


def test_analysis_resource_lock_evidence_registry_blocks_unregistered_entries() -> None:
    registry = deepcopy(load_analysis_resource_lock_evidence_registry())
    registry["evidence_entries"] = [
        {
            "resource_id": "unknown_resource",
            "evidence_path": "analysis/resources/locks/mock_fixture_builtin_v1.lock.json",
        }
    ]

    validation = validate_analysis_resource_lock_evidence_registry(registry)

    assert validation["status"] == "blocked"
    assert "analysis_resource_lock_evidence_registry_unregistered_resource:unknown_resource" in validation["blockers"]


def test_locked_analysis_resource_without_evidence_is_blocked() -> None:
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    first_resource = manifest["resources"][0]  # type: ignore[index]
    first_resource.pop("lock_evidence")
    validation = validate_analysis_resource_manifest(manifest)

    assert validation["status"] == "blocked"
    assert "analysis_resource_lock_evidence_missing:mock_fixture_builtin_v1" in validation["blockers"]


def test_analysis_resource_lock_evidence_blocks_placeholder_or_mismatched_payloads() -> None:
    manifest = read_json(ROOT / "analysis" / "resources" / "manifest.json")
    validation = validate_analysis_resource_lock_evidence(
        "mock_fixture_builtin_v1",
        {
            "schema_version": "wrong",
            "resource_id": "",
            "status": "blocked_until_resource_lock",
            "version": "required_before_full_mode",
            "source": "pending",
            "hash": {"algorithm": "", "value": "required_before_full_mode"},
            "license": "tbd",
            "cache_path": "missing/cache/path",
            "runtime_download_allowed": True,
            "approved_for_modules": ["unknown"],
            "evidence_files": ["missing/evidence.json"],
        },
        manifest=manifest,
    )

    assert validation["status"] == "blocked"
    assert "analysis_resource_lock_evidence_const_mismatch:schema_version" in validation["blockers"]
    assert "analysis_resource_lock_evidence_min_length_invalid:resource_id" in validation["blockers"]
    assert "analysis_resource_lock_evidence_const_mismatch:status" in validation["blockers"]
    assert "analysis_resource_lock_evidence_runtime_download_not_forbidden" in validation["blockers"]
    assert "analysis_resource_lock_evidence_hash_algorithm_missing" in validation["blockers"]
    assert "analysis_resource_lock_evidence_hash_value_missing" in validation["blockers"]
    assert "analysis_resource_lock_evidence_placeholder_field:version" in validation["blockers"]
    assert "analysis_resource_lock_evidence_cache_path_not_found:missing/cache/path" in validation["blockers"]
    assert "analysis_resource_lock_evidence_file_not_found:missing/evidence.json" in validation["blockers"]
    assert "analysis_resource_lock_evidence_approved_modules_mismatch" in validation["blockers"]
    assert "analysis_resource_lock_evidence_manifest_field_mismatch:hash" in validation["blockers"]


def test_analysis_environment_registry_is_authoritative_for_module_worker_boundaries() -> None:
    module_registry = read_json(ROOT / "analysis" / "registry" / "analysis_modules.json")
    environment_registry = read_json(ROOT / "analysis" / "registry" / "analysis_environments.json")
    environments = {item["environment_id"]: item for item in environment_registry["environments"]}  # type: ignore[index]

    assert {
        "app-dev",
        "r-bio-core",
        "r-bio-full",
        "r-spatial-full",
        "r-chem-full",
        "r-chem-gpu",
    } <= set(environments)
    app_dev = environments["app-dev"]
    assert app_dev["allowed_module_ids"] == []
    assert app_dev["allows_heavy_analysis_dependencies"] is False
    assert app_dev["r_runtime"] == "not_required"

    for environment_id, environment in environments.items():
        dockerfile = ROOT / environment["dockerfile"]
        lockfile = ROOT / environment["renv_lock"]
        docker_text = dockerfile.read_text(encoding="utf-8")
        lock = read_json(lockfile)
        assert dockerfile.exists()
        assert lockfile.exists()
        assert f'org.biomedpilot.environment="{environment_id}"' in docker_text
        assert 'runtime-package-install="forbidden"' in docker_text
        assert lock["BioMedPilotPolicy"]["runtime_package_install"] == "forbidden"  # type: ignore[index]
        if environment_id in {"app-dev", "r-bio-core"}:
            assert environment["allows_heavy_analysis_dependencies"] is False
        else:
            assert environment["allows_heavy_analysis_dependencies"] is True

    for module in module_registry["modules"]:  # type: ignore[index]
        module_id = module["module_id"]
        manifest = read_json(ROOT / module["module_manifest"])
        manifest_environment = manifest["environment"]
        lite_environment_id = manifest["modes"]["lite"].get("environment")
        full_environment_id = manifest["full_environment"]
        lite_environment = environments[lite_environment_id]
        full_environment = environments[full_environment_id]

        assert module_id in lite_environment["allowed_module_ids"]
        assert module_id in full_environment["allowed_module_ids"]
        assert manifest_environment["app_dev"] == environments["app-dev"]["dockerfile"]
        assert manifest_environment["lite"] == lite_environment["dockerfile"]
        assert manifest_environment["renv_lite"] == lite_environment["renv_lock"]
        assert manifest_environment["full"] == full_environment["dockerfile"]
        assert manifest_environment["renv_full"] == full_environment["renv_lock"]
        assert manifest["dockerfile"] == full_environment["dockerfile"]
        assert manifest["environment_lock"] == full_environment["renv_lock"]
        assert manifest["dependency_policy"]["runtime_install"] == "forbidden"
        assert manifest["dependency_policy"]["default_app_dependency"] is False

        if module_id in {"spatial_transcriptomics", "docking", "molecular_dynamics"}:
            assert lite_environment_id == "r-bio-core"
            assert lite_environment["allows_heavy_analysis_dependencies"] is False
            assert manifest_environment["lite"] == "docker/Dockerfile.r-bio-core"
            assert manifest_environment["renv_lite"] == "renv/renv.bio-core.lock"

    assert modules_lite_full_boundaries(module_registry) == {
        "spatial_transcriptomics": ("r-bio-core", "r-spatial-full"),
        "docking": ("r-bio-core", "r-chem-full"),
        "molecular_dynamics": ("r-bio-core", "r-chem-gpu"),
    }


def test_analysis_environment_registry_validator_separates_structure_from_full_readiness() -> None:
    validation = validate_analysis_environment_registry()

    assert validation["schema_version"] == "biomedpilot.analysis_environment_registry_validation.v1"
    assert validation["status"] == "passed"
    assert validation["full_mode_ready"] is False
    assert validation["evidence_registry_status"] == "passed"
    assert validation["evidence_registry_entry_count"] == 0
    assert set(validation["blocked_environment_ids"]) == {
        "r-bio-full",
        "r-spatial-full",
        "r-chem-full",
        "r-chem-gpu",
    }
    templates = {item["environment_id"]: item for item in validation["environment_lock_evidence_templates"]}
    assert set(templates) == {
        "r-bio-full",
        "r-spatial-full",
        "r-chem-full",
        "r-chem-gpu",
    }
    assert templates["r-bio-full"]["schema_version"] == "biomedpilot.analysis.environment_lock_evidence.v1"
    assert templates["r-bio-full"]["runtime_package_install"] == "forbidden"
    assert templates["r-bio-full"]["runtime_resource_download"] == "forbidden"
    assert templates["r-bio-full"]["dockerfile"] == "docker/Dockerfile.r-bio-full"
    assert templates["r-bio-full"]["renv_lock"] == "renv/renv.bio-full.lock"
    assert templates["r-bio-full"]["renv_lock_content"]["packages_non_empty"] is True
    assert templates["r-bio-full"]["renv_lock_content"]["policy_status"] == "restored"
    assert "scaffold_only_lockfile" in templates["r-bio-full"]["forbidden_evidence_sources"]
    assert "analysis_environment_renv_lock_not_restored:r-bio-full:scaffold_only_not_restored" in validation["readiness_blockers"]
    assert validation["blockers"] == []


def test_analysis_environment_lock_evidence_registry_is_authoritative_and_empty_by_default() -> None:
    registry = load_analysis_environment_lock_evidence_registry()
    validation = validate_analysis_environment_lock_evidence_registry(registry)

    assert registry["schema_version"] == "biomedpilot.analysis.environment_lock_evidence_registry.v1"
    assert registry["policy"]["registry_is_authoritative"] is True
    assert registry["policy"]["expected_environment_ids_are_authoritative"] is True
    assert registry["expected_environment_ids"] == REQUIRED_FULL_ENVIRONMENT_IDS
    assert registry["evidence_entries"] == []
    assert validation["schema_version"] == "biomedpilot.analysis.environment_lock_evidence_registry_validation.v1"
    assert validation["status"] == "passed"
    assert validation["entry_count"] == 0
    assert validation["expected_environment_ids"] == REQUIRED_FULL_ENVIRONMENT_IDS
    assert validation["missing_environment_ids"] == REQUIRED_FULL_ENVIRONMENT_IDS
    assert validation["missing_count"] == len(REQUIRED_FULL_ENVIRONMENT_IDS)


def test_analysis_environment_lock_evidence_registry_blocks_expected_scope_drift() -> None:
    registry = deepcopy(load_analysis_environment_lock_evidence_registry())
    registry["expected_environment_ids"] = ["r-bio-full"]

    validation = validate_analysis_environment_lock_evidence_registry(registry)

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_registry_expected_environment_ids_mismatch" in validation["blockers"]
    assert validation["expected_environment_ids"] == REQUIRED_FULL_ENVIRONMENT_IDS


def test_analysis_environment_lock_evidence_registry_blocks_unregistered_entries() -> None:
    registry = deepcopy(load_analysis_environment_lock_evidence_registry())
    registry["evidence_entries"] = [
        {
            "environment_id": "unknown-environment",
            "evidence_path": "analysis/registry/analysis_environments.json",
        }
    ]

    validation = validate_analysis_environment_lock_evidence_registry(registry)

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_registry_unregistered_environment:unknown-environment" in validation["blockers"]


def test_restored_full_environment_lock_requires_schema_valid_evidence(tmp_path: Path) -> None:
    environment_registry = deepcopy(read_json(ROOT / "analysis" / "registry" / "analysis_environments.json"))
    environments = {item["environment_id"]: item for item in environment_registry["environments"]}  # type: ignore[index]
    restored_lock = tmp_path / "renv.bio-full.restored.lock"
    restored_lock.write_text(
        json.dumps(
            {
                "R": {"Version": "4.4.2", "Repositories": []},
                "Packages": {
                    "limma": {"Package": "limma", "Version": "3.62.2"}
                },
                "BioMedPilotPolicy": {
                    "schema_version": "biomedpilot.renv_policy.v1",
                    "environment": "r-bio-full",
                    "status": "restored",
                    "heavy_analysis_dependencies_allowed": True,
                    "runtime_package_install": "forbidden",
                    "resource_lock_required": True,
                },
            }
        ),
        encoding="utf-8",
    )
    environments["r-bio-full"]["renv_lock"] = str(restored_lock)
    validation = validate_analysis_environment_registry(environment_registry)

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_missing:r-bio-full" in validation["blockers"]
    assert "r-bio-full" not in validation["blocked_environment_ids"]


def test_restored_full_environment_lock_can_be_proven_by_registry_evidence(tmp_path: Path) -> None:
    environment_registry = deepcopy(read_json(ROOT / "analysis" / "registry" / "analysis_environments.json"))
    environments = {item["environment_id"]: item for item in environment_registry["environments"]}  # type: ignore[index]
    restored_lock = tmp_path / "renv.bio-full.restored.lock"
    restored_lock.write_text(
        json.dumps(
            {
                "R": {"Version": "4.4.2", "Repositories": []},
                "Packages": {
                    "limma": {"Package": "limma", "Version": "3.62.2"}
                },
                "BioMedPilotPolicy": {
                    "schema_version": "biomedpilot.renv_policy.v1",
                    "environment": "r-bio-full",
                    "status": "restored",
                    "heavy_analysis_dependencies_allowed": True,
                    "runtime_package_install": "forbidden",
                    "resource_lock_required": True,
                },
            }
        ),
        encoding="utf-8",
    )
    evidence_note = tmp_path / "bio_full_environment_build_evidence.txt"
    evidence_note.write_text("controlled external environment build evidence\n", encoding="utf-8")
    docker_build_log = tmp_path / "r-bio-full.docker-build.log"
    docker_build_log.write_text("docker buildx build --platform linux/arm64\n", encoding="utf-8")
    restored_lock_hash = hashlib.sha256(restored_lock.read_bytes()).hexdigest()
    evidence_path = tmp_path / "r-bio-full.environment_lock_evidence.json"
    evidence_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.analysis.environment_lock_evidence.v1",
                "environment_id": "r-bio-full",
                "status": "restored",
                "r_version": "R 4.4.2",
                "bioconductor_version": "3.20",
                "package_lock_hash": {"algorithm": "sha256", "value": restored_lock_hash},
                "renv_lock_content": {"policy_status": "restored", "packages_non_empty": True, "package_count": 1},
                "docker_image": {
                    "image_ref": "biomedpilot/r-bio-full:test",
                    "digest": {"algorithm": "sha256", "value": "a" * 64},
                    "architecture": "linux/arm64",
                    "build_status": "built",
                    "build_log": str(docker_build_log),
                },
                "dockerfile": "docker/Dockerfile.r-bio-full",
                "renv_lock": str(restored_lock),
                "runtime_package_install": "forbidden",
                "runtime_resource_download": "forbidden",
                "allowed_module_ids": environments["r-bio-full"]["allowed_module_ids"],
                "evidence_files": [str(evidence_note)],
            }
        ),
        encoding="utf-8",
    )
    environments["r-bio-full"]["renv_lock"] = str(restored_lock)
    evidence_registry = {
        "schema_version": "biomedpilot.analysis.environment_lock_evidence_registry.v1",
        "policy": {
            "registry_is_authoritative": True,
            "expected_environment_ids_are_authoritative": True,
            "restored_full_environment_requires_schema_valid_evidence": True,
            "manual_scoped_environment_restoration_only": True,
            "runtime_package_install": "forbidden",
            "runtime_resource_download": "forbidden",
        },
        "expected_environment_ids": REQUIRED_FULL_ENVIRONMENT_IDS,
        "evidence_entries": [
            {"environment_id": "r-bio-full", "evidence_path": str(evidence_path)}
        ],
    }

    evidence_validation = validate_analysis_environment_lock_evidence_registry(
        evidence_registry,
        environment_registry=environment_registry,
    )
    registry_validation = validate_analysis_environment_registry(
        environment_registry,
        environment_lock_evidence_registry=evidence_registry,
    )
    deg_environment_blockers = full_mode_environment_blockers(
        "deg",
        environment_registry=environment_registry,
        environment_lock_evidence_registry=evidence_registry,
    )

    assert evidence_validation["status"] == "passed"
    assert evidence_validation["registered_environment_ids"] == ["r-bio-full"]
    assert registry_validation["status"] == "passed"
    assert registry_validation["full_mode_ready"] is False
    assert "r-bio-full" not in registry_validation["blocked_environment_ids"]
    assert "r-spatial-full" in registry_validation["blocked_environment_ids"]
    assert deg_environment_blockers == []


def test_environment_lock_evidence_requires_docker_image_build_evidence(tmp_path: Path) -> None:
    environment_registry = deepcopy(read_json(ROOT / "analysis" / "registry" / "analysis_environments.json"))
    environments = {item["environment_id"]: item for item in environment_registry["environments"]}  # type: ignore[index]
    restored_lock = tmp_path / "renv.bio-full.restored.lock"
    restored_lock.write_text(
        json.dumps(
            {
                "R": {"Version": "4.4.2", "Repositories": []},
                "Packages": {"limma": {"Package": "limma", "Version": "3.62.2"}},
                "BioMedPilotPolicy": {
                    "schema_version": "biomedpilot.renv_policy.v1",
                    "environment": "r-bio-full",
                    "status": "restored",
                    "heavy_analysis_dependencies_allowed": True,
                    "runtime_package_install": "forbidden",
                    "resource_lock_required": True,
                },
            }
        ),
        encoding="utf-8",
    )
    environments["r-bio-full"]["renv_lock"] = str(restored_lock)
    restored_lock_hash = hashlib.sha256(restored_lock.read_bytes()).hexdigest()

    validation = validate_analysis_environment_lock_evidence(
        "r-bio-full",
        {
            "schema_version": "biomedpilot.analysis.environment_lock_evidence.v1",
            "environment_id": "r-bio-full",
            "status": "restored",
            "r_version": "R 4.4.2",
            "bioconductor_version": "3.20",
            "package_lock_hash": {"algorithm": "sha256", "value": restored_lock_hash},
            "renv_lock_content": {"policy_status": "restored", "packages_non_empty": True, "package_count": 1},
            "dockerfile": "docker/Dockerfile.r-bio-full",
            "renv_lock": str(restored_lock),
            "runtime_package_install": "forbidden",
            "runtime_resource_download": "forbidden",
            "allowed_module_ids": environments["r-bio-full"]["allowed_module_ids"],
            "evidence_files": ["analysis/registry/analysis_environments.json"],
        },
        environment_registry=environment_registry,
    )

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_required_field_missing:docker_image" in validation["blockers"]
    assert "analysis_environment_lock_evidence_docker_image_invalid" in validation["blockers"]


def test_environment_lock_evidence_blocks_empty_restored_renv_packages(tmp_path: Path) -> None:
    environment_registry = deepcopy(read_json(ROOT / "analysis" / "registry" / "analysis_environments.json"))
    environments = {item["environment_id"]: item for item in environment_registry["environments"]}  # type: ignore[index]
    restored_lock = tmp_path / "renv.bio-full.empty-packages.lock"
    restored_lock.write_text(
        json.dumps(
            {
                "R": {"Version": "4.4.2", "Repositories": []},
                "Packages": {},
                "BioMedPilotPolicy": {
                    "schema_version": "biomedpilot.renv_policy.v1",
                    "environment": "r-bio-full",
                    "status": "restored",
                    "heavy_analysis_dependencies_allowed": True,
                    "runtime_package_install": "forbidden",
                    "resource_lock_required": True,
                },
            }
        ),
        encoding="utf-8",
    )
    environments["r-bio-full"]["renv_lock"] = str(restored_lock)
    restored_lock_hash = hashlib.sha256(restored_lock.read_bytes()).hexdigest()
    validation = validate_analysis_environment_lock_evidence(
        "r-bio-full",
        {
            "schema_version": "biomedpilot.analysis.environment_lock_evidence.v1",
            "environment_id": "r-bio-full",
            "status": "restored",
            "r_version": "R 4.4.2",
            "bioconductor_version": "3.20",
            "package_lock_hash": {"algorithm": "sha256", "value": restored_lock_hash},
            "dockerfile": "docker/Dockerfile.r-bio-full",
            "renv_lock": str(restored_lock),
            "runtime_package_install": "forbidden",
            "runtime_resource_download": "forbidden",
            "allowed_module_ids": environments["r-bio-full"]["allowed_module_ids"],
            "evidence_files": ["analysis/registry/analysis_environments.json"],
        },
        environment_registry=environment_registry,
    )

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_renv_lock_packages_empty" in validation["blockers"]


def test_environment_lock_evidence_blocks_package_count_mismatch(tmp_path: Path) -> None:
    environment_registry = deepcopy(read_json(ROOT / "analysis" / "registry" / "analysis_environments.json"))
    environments = {item["environment_id"]: item for item in environment_registry["environments"]}  # type: ignore[index]
    restored_lock = tmp_path / "renv.bio-full.two-packages.lock"
    restored_lock.write_text(
        json.dumps(
            {
                "R": {"Version": "4.4.2", "Repositories": []},
                "Packages": {
                    "limma": {"Package": "limma", "Version": "3.62.2"},
                    "edgeR": {"Package": "edgeR", "Version": "4.4.2"},
                },
                "BioMedPilotPolicy": {
                    "schema_version": "biomedpilot.renv_policy.v1",
                    "environment": "r-bio-full",
                    "status": "restored",
                    "heavy_analysis_dependencies_allowed": True,
                    "runtime_package_install": "forbidden",
                    "resource_lock_required": True,
                },
            }
        ),
        encoding="utf-8",
    )
    environments["r-bio-full"]["renv_lock"] = str(restored_lock)
    restored_lock_hash = hashlib.sha256(restored_lock.read_bytes()).hexdigest()
    validation = validate_analysis_environment_lock_evidence(
        "r-bio-full",
        {
            "schema_version": "biomedpilot.analysis.environment_lock_evidence.v1",
            "environment_id": "r-bio-full",
            "status": "restored",
            "r_version": "R 4.4.2",
            "bioconductor_version": "3.20",
            "package_lock_hash": {"algorithm": "sha256", "value": restored_lock_hash},
            "renv_lock_content": {"policy_status": "restored", "packages_non_empty": True, "package_count": 1},
            "dockerfile": "docker/Dockerfile.r-bio-full",
            "renv_lock": str(restored_lock),
            "runtime_package_install": "forbidden",
            "runtime_resource_download": "forbidden",
            "allowed_module_ids": environments["r-bio-full"]["allowed_module_ids"],
            "evidence_files": ["analysis/registry/analysis_environments.json"],
        },
        environment_registry=environment_registry,
    )

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_renv_lock_content_package_count_mismatch" in validation["blockers"]


def test_environment_lock_evidence_blocks_scaffold_only_renv_lock_even_with_matching_hash() -> None:
    environment_registry = read_json(ROOT / "analysis" / "registry" / "analysis_environments.json")
    lock_path = ROOT / "renv" / "renv.bio-full.lock"
    lock_hash = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    validation = validate_analysis_environment_lock_evidence(
        "r-bio-full",
        {
            "schema_version": "biomedpilot.analysis.environment_lock_evidence.v1",
            "environment_id": "r-bio-full",
            "status": "restored",
            "r_version": "R 4.4.2",
            "bioconductor_version": "3.20",
            "package_lock_hash": {"algorithm": "sha256", "value": lock_hash},
            "dockerfile": "docker/Dockerfile.r-bio-full",
            "renv_lock": "renv/renv.bio-full.lock",
            "runtime_package_install": "forbidden",
            "runtime_resource_download": "forbidden",
            "allowed_module_ids": ["deg", "survival", "univariate", "multivariate", "enrichment", "immune_infiltration", "correlation"],
            "evidence_files": ["analysis/registry/analysis_environments.json"],
        },
        environment_registry=environment_registry,
    )

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_renv_lock_not_restored:scaffold_only_not_restored" in validation["blockers"]
    assert "analysis_environment_lock_evidence_renv_lock_packages_empty" in validation["blockers"]


def test_environment_lock_evidence_blocks_placeholder_or_mismatched_payloads() -> None:
    environment_registry = read_json(ROOT / "analysis" / "registry" / "analysis_environments.json")
    validation = validate_analysis_environment_lock_evidence(
        "r-bio-full",
        {
            "schema_version": "wrong",
            "environment_id": "",
            "status": "scaffold_only_not_restored",
            "r_version": "pending",
            "bioconductor_version": "",
            "package_lock_hash": {"algorithm": "md5", "value": "required_before_full_mode"},
            "dockerfile": "missing/Dockerfile",
            "renv_lock": "missing/renv.lock",
            "runtime_package_install": "allowed",
            "runtime_resource_download": "allowed",
            "allowed_module_ids": ["unknown"],
            "evidence_files": ["missing/evidence.json"],
        },
        environment_registry=environment_registry,
    )

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_const_mismatch:schema_version" in validation["blockers"]
    assert "analysis_environment_lock_evidence_min_length_invalid:environment_id" in validation["blockers"]
    assert "analysis_environment_lock_evidence_status_not_restored" in validation["blockers"]
    assert "analysis_environment_lock_evidence_runtime_install_not_forbidden" in validation["blockers"]
    assert "analysis_environment_lock_evidence_runtime_download_not_forbidden" in validation["blockers"]
    assert "analysis_environment_lock_evidence_package_lock_hash_algorithm_not_sha256" in validation["blockers"]
    assert "analysis_environment_lock_evidence_package_lock_hash_value_missing" in validation["blockers"]
    assert "analysis_environment_lock_evidence_placeholder_field:r_version" in validation["blockers"]
    assert "analysis_environment_lock_evidence_placeholder_field:bioconductor_version" in validation["blockers"]
    assert "analysis_environment_lock_evidence_dockerfile_not_found:missing/Dockerfile" in validation["blockers"]
    assert "analysis_environment_lock_evidence_renv_lock_not_found:missing/renv.lock" in validation["blockers"]
    assert "analysis_environment_lock_evidence_file_not_found:missing/evidence.json" in validation["blockers"]
    assert "analysis_environment_lock_evidence_allowed_modules_mismatch" in validation["blockers"]
    assert "analysis_environment_lock_evidence_registry_field_mismatch:dockerfile" in validation["blockers"]
    assert "analysis_environment_lock_evidence_registry_field_mismatch:renv_lock" in validation["blockers"]


def test_environment_lock_evidence_requires_sha256_hex_package_lock_hash() -> None:
    environment_registry = read_json(ROOT / "analysis" / "registry" / "analysis_environments.json")
    validation = validate_analysis_environment_lock_evidence(
        "r-bio-full",
        {
            "schema_version": "biomedpilot.analysis.environment_lock_evidence.v1",
            "environment_id": "r-bio-full",
            "status": "restored",
            "r_version": "R 4.4.2",
            "bioconductor_version": "3.20",
            "package_lock_hash": {"algorithm": "sha256", "value": "not-a-sha256"},
            "dockerfile": "docker/Dockerfile.r-bio-full",
            "renv_lock": "renv/renv.bio-full.lock",
            "runtime_package_install": "forbidden",
            "runtime_resource_download": "forbidden",
            "allowed_module_ids": ["deg", "survival", "univariate", "multivariate", "enrichment", "immune_infiltration", "correlation"],
            "evidence_files": ["analysis/registry/analysis_environments.json"],
        },
        environment_registry=environment_registry,
    )

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_package_lock_hash_value_not_sha256" in validation["blockers"]


def test_environment_lock_evidence_package_lock_hash_must_match_renv_lock(tmp_path: Path) -> None:
    environment_registry = deepcopy(read_json(ROOT / "analysis" / "registry" / "analysis_environments.json"))
    environments = {item["environment_id"]: item for item in environment_registry["environments"]}  # type: ignore[index]
    restored_lock = tmp_path / "renv.bio-full.restored.lock"
    restored_lock.write_text(
        json.dumps(
            {
                "R": {"Version": "4.4.2", "Repositories": []},
                "Packages": {},
                "BioMedPilotPolicy": {
                    "schema_version": "biomedpilot.renv_policy.v1",
                    "environment": "r-bio-full",
                    "status": "restored",
                    "heavy_analysis_dependencies_allowed": True,
                    "runtime_package_install": "forbidden",
                    "resource_lock_required": True,
                },
            }
        ),
        encoding="utf-8",
    )
    environments["r-bio-full"]["renv_lock"] = str(restored_lock)
    validation = validate_analysis_environment_lock_evidence(
        "r-bio-full",
        {
            "schema_version": "biomedpilot.analysis.environment_lock_evidence.v1",
            "environment_id": "r-bio-full",
            "status": "restored",
            "r_version": "R 4.4.2",
            "bioconductor_version": "3.20",
            "package_lock_hash": {"algorithm": "sha256", "value": "b" * 64},
            "dockerfile": "docker/Dockerfile.r-bio-full",
            "renv_lock": str(restored_lock),
            "runtime_package_install": "forbidden",
            "runtime_resource_download": "forbidden",
            "allowed_module_ids": environments["r-bio-full"]["allowed_module_ids"],
            "evidence_files": ["analysis/registry/analysis_environments.json"],
        },
        environment_registry=environment_registry,
    )

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_package_lock_hash_mismatch" in validation["blockers"]


def test_full_mode_environment_blockers_allow_chem_gpu_shared_lock_policy() -> None:
    docking_blockers = full_mode_environment_blockers("docking")
    md_blockers = full_mode_environment_blockers("molecular_dynamics")

    assert "analysis_environment_renv_lock_environment_mismatch:r-chem-full" not in docking_blockers
    assert "analysis_environment_renv_lock_environment_mismatch:r-chem-gpu" not in md_blockers
    assert "analysis_environment_renv_lock_not_restored:r-chem-full:scaffold_only_not_restored" in docking_blockers
    assert "analysis_environment_renv_lock_not_restored:r-chem-gpu:scaffold_only_not_restored" in md_blockers
    assert not any("analysis_environment_lock_evidence" in blocker for blocker in docking_blockers)
    assert not any("analysis_environment_lock_evidence" in blocker for blocker in md_blockers)


def test_analysis_environment_registry_validator_blocks_invalid_app_dev_and_unknown_modules() -> None:
    environment_registry = deepcopy(read_json(ROOT / "analysis" / "registry" / "analysis_environments.json"))
    environments = {item["environment_id"]: item for item in environment_registry["environments"]}  # type: ignore[index]
    environments["app-dev"]["allowed_module_ids"] = ["deg"]
    environments["r-bio-core"]["allowed_module_ids"].append("unknown_module")

    validation = validate_analysis_environment_registry(environment_registry)

    assert validation["status"] == "blocked"
    assert "analysis_environment_app_dev_allows_analysis_modules" in validation["blockers"]
    assert "analysis_environment_allowed_module_unregistered:r-bio-core:unknown_module" in validation["blockers"]
    assert validation["full_mode_ready"] is False


def test_analysis_architecture_status_summarizes_twenty_required_gates_without_p0_failures() -> None:
    status = build_analysis_architecture_status()
    rows = {row["requirement_id"]: row for row in status["requirement_rows"]}
    full_gate = status["full_analysis_activation_gate"]

    assert status["schema_version"] == "biomedpilot.analysis.architecture_status.v1"
    assert status["requirement_count"] == 20
    assert status["status"] == "partial_with_p1_gaps"
    assert status["requirement_summary"]["requirement_count"] == 20
    assert status["requirement_summary"]["pass_count"] == status["pass_count"]
    assert status["requirement_summary"]["warn_count"] == status["warn_count"]
    assert status["requirement_summary"]["fail_count"] == status["fail_count"]
    assert status["p0_issues"] == []
    assert "full_analysis_environment_locks_not_restored" in status["p1_issues"]
    assert "full_analysis_resource_locks_not_complete" in status["p1_issues"]
    assert "RARCH-03" in status["p2_issues"]
    assert "RARCH-08" in status["p2_issues"]
    assert "RARCH-12" in status["p3_issues"]
    assert status["priority_issue_lists"]["P0"] == []
    assert {item["issue_id"] for item in status["priority_issue_lists"]["P1"]} == {
        "full_analysis_environment_locks_not_restored",
        "full_analysis_resource_locks_not_complete",
        "formal_algorithms_not_universally_migrated_to_isolated_standard_worker",
    }
    assert any(item["issue_id"] == "RARCH-16" for item in status["priority_issue_lists"]["P2"])
    assert any(item["issue_id"] == "RARCH-15" for item in status["priority_issue_lists"]["P3"])
    assert len(status["top_architecture_risks"]) == 5
    assert status["top_architecture_risks"][0]["risk_id"] == "full_analysis_environment_locks_not_restored"
    assert rows["RARCH-01"]["status"] == "pass"
    assert rows["RARCH-10"]["status"] == "pass"
    assert rows["RARCH-10"]["label"] == "No active runtime R package install or resource download commands"
    assert rows["RARCH-10"]["blockers"] == []
    assert rows["RARCH-11"]["status"] == "pass"
    assert rows["RARCH-12"]["status"] == "warn"
    assert rows["RARCH-18"]["status"] == "warn"
    assert rows["RARCH-18"]["blockers"] == []
    assert "lite_mode_writes_command_manifest_only_no_AutoDock_or_GROMACS_execution" in rows["RARCH-18"]["warnings"]
    assert rows["RARCH-20"]["status"] == "pass"
    runtime_scan = status["runtime_acquisition_scan"]
    dependency_scan = status["default_dependency_scan"]
    assert runtime_scan["schema_version"] == "biomedpilot.analysis.runtime_acquisition_scan.v1"
    assert runtime_scan["status"] == "passed"
    assert runtime_scan["install_hits"] == []
    assert runtime_scan["resource_download_hits"] == []
    assert runtime_scan["hit_count"] == 0
    assert runtime_scan["scanned_roots"] == ["app", "analysis", "scripts", "config"]
    assert runtime_scan["install_scan"]["scan_id"] == "runtime_install_command_scan"
    assert runtime_scan["resource_download_scan"]["scan_id"] == "runtime_resource_download_command_scan"
    assert runtime_scan["install_scan"]["scanned_file_count"] > 0
    assert "install.packages" in runtime_scan["install_scan"]["patterns"]
    assert "download.file" in runtime_scan["resource_download_scan"]["patterns"]
    assert dependency_scan["schema_version"] == "biomedpilot.analysis.default_dependency_scan.v1"
    assert dependency_scan["status"] == "passed"
    assert dependency_scan["heavy_dependency_hits"] == []
    assert dependency_scan["hit_count"] == 0
    assert "requirements.txt" in dependency_scan["scanned_files"]
    assert "ReactomePA" in dependency_scan["heavy_dependency_names"]
    assert status["module_interface_matrix"]["status"] == "passed"
    assert status["module_interface_matrix"]["passed_module_count"] == 10
    assert status["module_interface_matrix"]["blocked_module_count"] == 0
    assert status["module_mode_readiness_matrix"]["status"] == "partial"
    assert status["module_mode_readiness_matrix"]["passed_module_count"] == 0
    assert status["module_mode_readiness_matrix"]["partial_module_count"] == 10
    assert status["module_mode_readiness_matrix"]["blocked_module_count"] == 0
    assert set(status["module_mode_readiness_matrix"]["full_blocked_module_ids"]) == REQUIRED_MODULES
    assert status["module_mode_readiness_matrix"]["warning_counts"]["module_full_mode_blocked:deg"] == 1
    assert status["environment_artifact_matrix"]["status"] == "partial"
    assert status["environment_artifact_matrix"]["passed_environment_count"] == 2
    assert status["environment_artifact_matrix"]["partial_environment_count"] == 4
    assert status["environment_artifact_matrix"]["blocked_environment_count"] == 0
    assert status["environment_artifact_matrix"]["warning_counts"]["environment_renv_lock_scaffold_only_not_restored:r-bio-full"] == 1
    assert status["resource_artifact_matrix"]["status"] == "partial"
    assert status["resource_artifact_matrix"]["locked_resource_count"] == 1
    assert status["resource_artifact_matrix"]["blocked_resource_count"] == 11
    assert status["resource_artifact_matrix"]["warning_counts"]["resource_full_lock_not_ready:reactome_full"] == 1
    assert status["standard_worker_entrypoint_matrix"]["status"] == "partial"
    assert status["standard_worker_entrypoint_matrix"]["passed_row_count"] == 5
    assert status["standard_worker_entrypoint_matrix"]["partial_row_count"] == 1
    assert status["standard_worker_entrypoint_matrix"]["blocked_row_count"] == 0
    assert status["standard_worker_entrypoint_matrix"]["standard_entrypoint"] == "analysis/runners/run_module.R"
    assert set(status["standard_worker_entrypoint_matrix"]["lite_module_ids"]) == REQUIRED_MODULES
    assert status["external_tool_adapter_matrix"]["status"] == "passed"
    assert status["external_tool_adapter_matrix"]["passed_module_count"] == 2
    assert status["external_tool_adapter_matrix"]["blocked_module_count"] == 0
    assert status["task_system_boundary_matrix"]["status"] == "passed"
    assert status["task_system_boundary_matrix"]["passed_module_count"] == 10
    assert status["task_system_boundary_matrix"]["blocked_module_count"] == 0
    assert status["lite_task_bridge_coverage_matrix"]["status"] == "passed"
    assert status["lite_task_bridge_coverage_matrix"]["covered_module_count"] == 10
    assert status["lite_task_bridge_coverage_matrix"]["blocked_module_count"] == 0
    assert status["legacy_sidecar_transition_matrix"]["status"] == "partial"
    assert status["legacy_sidecar_transition_matrix"]["passed_row_count"] == 4
    assert status["legacy_sidecar_transition_matrix"]["partial_row_count"] == 1
    assert status["legacy_sidecar_transition_matrix"]["blocked_row_count"] == 0
    assert "deg" in status["legacy_sidecar_transition_matrix"]["transitional_module_ids"]
    assert "correlation" in status["legacy_sidecar_transition_matrix"]["transitional_module_ids"]
    assert status["frontend_consumption_matrix"]["status"] == "partial"
    assert status["frontend_consumption_matrix"]["passed_consumer_count"] == 4
    assert status["frontend_consumption_matrix"]["partial_consumer_count"] == 1
    assert status["reproducibility_provenance_matrix"]["status"] == "partial"
    assert status["reproducibility_provenance_matrix"]["passed_row_count"] == 5
    assert status["reproducibility_provenance_matrix"]["partial_row_count"] == 1
    assert status["reproducibility_provenance_matrix"]["blocked_row_count"] == 0
    assert "input_hash" in status["reproducibility_provenance_matrix"]["required_fields"]
    assert "package_versions" in status["reproducibility_provenance_matrix"]["required_runtime_fields"]
    assert status["environment_validation"]["full_mode_ready"] is False
    assert status["resource_validation"]["full_mode_ready"] is False
    assert full_gate["schema_version"] == "biomedpilot.analysis.full_analysis_activation_gate.v1"
    assert full_gate["status"] == "blocked"
    assert full_gate["schema_validation_status"] == "passed"
    assert full_gate["schema_blockers"] == []
    assert full_gate["checks"]["environment_registry_passed"] is True
    assert full_gate["checks"]["resource_manifest_passed"] is True
    assert full_gate["checks"]["standard_worker_migration_registry_passed"] is True
    assert full_gate["checks"]["full_environment_locks_ready"] is False
    assert full_gate["checks"]["full_resource_locks_ready"] is False
    assert full_gate["checks"]["all_modules_migrated_to_standard_worker"] is False
    assert full_gate["blockers"] == [
        "full_analysis_environment_locks_not_ready",
        "full_analysis_resource_locks_not_ready",
        "full_analysis_standard_worker_migration_incomplete",
    ]


def test_full_analysis_activation_gate_requires_all_prerequisites() -> None:
    gate = build_full_analysis_activation_gate(
        environment_validation={"status": "passed", "full_mode_ready": True},
        resource_validation={"status": "passed", "full_mode_ready": True},
        standard_worker_migration_matrix={
            "status": "passed",
            "evidence_registry_status": "passed",
            "formal_pending_count": 0,
            "full_blocked_count": 0,
        },
    )

    assert gate["status"] == "eligible"
    assert gate["blockers"] == []
    assert gate["schema_validation_status"] == "passed"
    assert gate["schema_blockers"] == []
    assert gate["policy"] == "full_analysis_requires_environment_resource_and_standard_worker_evidence"
    assert gate["execution_policy"] == "read_only_no_worker_execution_no_runtime_install_no_resource_download"


def test_full_analysis_activation_gate_blocks_partial_or_failed_prerequisites() -> None:
    gate = build_full_analysis_activation_gate(
        environment_validation={"status": "blocked", "full_mode_ready": False},
        resource_validation={"status": "passed", "full_mode_ready": False},
        standard_worker_migration_matrix={
            "status": "partial",
            "evidence_registry_status": "blocked",
            "formal_pending_count": 2,
            "full_blocked_count": 1,
        },
    )

    assert gate["status"] == "blocked"
    assert gate["blockers"] == [
        "full_analysis_environment_registry_failed",
        "full_analysis_environment_locks_not_ready",
        "full_analysis_resource_locks_not_ready",
        "full_analysis_standard_worker_evidence_registry_failed",
        "full_analysis_standard_worker_migration_incomplete",
    ]
    assert gate["schema_validation_status"] == "passed"
    assert gate["schema_blockers"] == []


def test_analysis_remediation_queue_turns_p1_gaps_into_manual_scoped_items() -> None:
    status = build_analysis_architecture_status()
    queue = build_analysis_remediation_queue(status)
    items = {item["item_id"]: item for item in queue["items"]}

    assert queue["schema_version"] == "biomedpilot.analysis.remediation_queue.v1"
    assert queue["status"] == "open"
    assert queue["source_status"] == "partial_with_p1_gaps"
    assert queue["automation_policy"] == "manual_scoped_changes_only"
    assert queue["execution_policy"] == "read_only_no_runtime_mutation"
    assert queue["install_policy"] == "no_runtime_package_install_or_resource_download"
    assert queue["full_mode_policy"] == "full_mode_remains_blocked_until_environment_and_resource_evidence_passes"
    assert queue["schema_validation_status"] == "passed"
    assert queue["schema_blockers"] == []
    assert set(items) == {
        "restore_full_analysis_environment_locks",
        "lock_full_analysis_resources",
        "migrate_formal_algorithms_to_isolated_standard_worker",
    }
    assert items["restore_full_analysis_environment_locks"]["source_issue"] == "full_analysis_environment_locks_not_restored"
    assert "renv/renv.bio-full.lock" in items["restore_full_analysis_environment_locks"]["recommended_files"]
    assert "analysis/registry/environment_lock_evidence.json" in items["restore_full_analysis_environment_locks"]["recommended_files"]
    assert "analysis/schemas/output/environment_lock_evidence.schema.json" in items["restore_full_analysis_environment_locks"]["recommended_files"]
    assert "analysis/schemas/output/environment_lock_evidence_registry.schema.json" in items["restore_full_analysis_environment_locks"]["recommended_files"]
    assert "each restored full environment lock has schema-valid environment_lock_evidence" in items["restore_full_analysis_environment_locks"]["required_evidence"]
    environment_actions = {item["environment_id"]: item for item in items["restore_full_analysis_environment_locks"]["environment_next_actions"]}
    environment_summary = items["restore_full_analysis_environment_locks"]["environment_action_summary"]
    assert environment_summary["environment_count"] == len(REQUIRED_FULL_ENVIRONMENT_IDS)
    assert environment_summary["blocked_environment_count"] == len(REQUIRED_FULL_ENVIRONMENT_IDS)
    assert environment_summary["next_action_counts"]["register_schema_valid_restored_environment_evidence"] == len(REQUIRED_FULL_ENVIRONMENT_IDS)
    assert set(environment_actions) == set(REQUIRED_FULL_ENVIRONMENT_IDS)
    assert environment_actions["r-bio-full"]["next_action"] == "register_schema_valid_restored_environment_evidence"
    assert environment_actions["r-bio-full"]["runtime_package_install"] == "forbidden"
    assert environment_actions["r-bio-full"]["runtime_resource_download"] == "forbidden"
    assert environment_actions["r-bio-full"]["required_package_lock_hash_algorithm"] == "sha256"
    assert environment_actions["r-bio-full"]["required_docker_image_status"] == "built"
    assert "deg" in environment_actions["r-bio-full"]["allowed_module_ids"]
    assert "runtime_package_install" in environment_actions["r-bio-full"]["forbidden_evidence_sources"]
    assert environment_summary["module_environments"]["deg"] == ["r-bio-full"]
    assert environment_summary["module_environments"]["spatial_transcriptomics"] == ["r-spatial-full"]
    assert environment_summary["module_environments"]["docking"] == ["r-chem-full"]
    assert environment_summary["module_environments"]["molecular_dynamics"] == ["r-chem-gpu"]
    assert "analysis/resources/manifest.json" in items["lock_full_analysis_resources"]["recommended_files"]
    assert "analysis/registry/resource_lock_evidence.json" in items["lock_full_analysis_resources"]["recommended_files"]
    assert "analysis/schemas/output/resource_lock_evidence.schema.json" in items["lock_full_analysis_resources"]["recommended_files"]
    assert "analysis/schemas/output/resource_lock_evidence_registry.schema.json" in items["lock_full_analysis_resources"]["recommended_files"]
    assert "each locked full resource has schema-valid resource_lock_evidence" in items["lock_full_analysis_resources"]["required_evidence"]
    resource_actions = {item["resource_id"]: item for item in items["lock_full_analysis_resources"]["resource_next_actions"]}
    resource_summary = items["lock_full_analysis_resources"]["resource_action_summary"]
    assert resource_summary["resource_count"] == len(REQUIRED_FULL_RESOURCE_IDS)
    assert resource_summary["blocked_resource_count"] == len(REQUIRED_FULL_RESOURCE_IDS)
    assert resource_summary["next_action_counts"]["register_schema_valid_prelocked_resource_evidence"] == len(REQUIRED_FULL_RESOURCE_IDS)
    assert set(resource_actions) == set(REQUIRED_FULL_RESOURCE_IDS)
    assert resource_actions["reactome_full"]["next_action"] == "register_schema_valid_prelocked_resource_evidence"
    assert resource_actions["reactome_full"]["runtime_download_allowed"] is False
    assert resource_actions["reactome_full"]["required_hash_algorithm"] == "sha256"
    assert resource_actions["reactome_full"]["required_for_modules"] == ["enrichment"]
    assert "runtime_download" in resource_actions["reactome_full"]["forbidden_evidence_sources"]
    assert resource_summary["module_resources"]["enrichment"] == [
        "reactome_full",
        "msigdb_full",
        "go_full",
        "kegg_full",
        "orgdb_human_full",
    ]
    assert resource_summary["module_resources"]["docking"] == ["autodock_vina_tool", "docking_template_bundle"]
    assert resource_summary["module_resources"]["molecular_dynamics"] == ["gromacs_tool", "md_forcefield_template_bundle"]
    assert (
        "analysis/registry/standard_worker_migration_evidence.json"
        in items["migrate_formal_algorithms_to_isolated_standard_worker"]["recommended_files"]
    )
    assert "analysis/runners/run_module.R" in items["migrate_formal_algorithms_to_isolated_standard_worker"]["recommended_files"]
    assert (
        "analysis/schemas/output/standard_worker_migration_evidence.schema.json"
        in items["migrate_formal_algorithms_to_isolated_standard_worker"]["recommended_files"]
    )
    assert (
        "analysis/schemas/output/standard_worker_migration_evidence_registry.schema.json"
        in items["migrate_formal_algorithms_to_isolated_standard_worker"]["recommended_files"]
    )
    assert (
        "selected formal module has registry-owned schema-valid standard worker migration evidence"
        in items["migrate_formal_algorithms_to_isolated_standard_worker"]["required_evidence"]
    )
    migration_scope = items["migrate_formal_algorithms_to_isolated_standard_worker"]["module_scope"]
    migration_actions = {
        item["module_id"]: item
        for item in items["migrate_formal_algorithms_to_isolated_standard_worker"]["module_next_actions"]
    }
    action_summary = items["migrate_formal_algorithms_to_isolated_standard_worker"]["module_action_summary"]
    assert migration_scope["scope_policy"] == "module_by_module_standard_worker_migration_required"
    assert migration_scope["passed_module_ids"] == []
    assert migration_scope["blocked_module_ids"] == []
    assert migration_scope["missing_module_ids"] == migration_scope["expected_module_ids"]
    assert migration_scope["missing_count"] == len(migration_scope["expected_module_ids"])
    assert "deg" in migration_scope["missing_module_ids"]
    assert "molecular_dynamics" in migration_scope["missing_module_ids"]
    assert action_summary["module_count"] == len(migration_actions)
    assert action_summary["blocked_module_count"] == len(migration_actions)
    assert action_summary["next_action_counts"]["declare_scoped_full_mode_only_after_environment_and_resource_locks"] >= 1
    assert migration_actions["deg"]["migration_next_action"] == "declare_scoped_full_mode_only_after_environment_and_resource_locks"
    assert migration_actions["deg"]["prerequisite_status"]["required_environment_lock"] == "required_before_migration_evidence"
    assert "analysis/modules/deg/module.json" in migration_actions["deg"]["recommended_files"]
    assert "analysis/registry/analysis_environments.json" in migration_actions["deg"]["recommended_files"]
    assert migration_actions["univariate"]["migration_next_action"] == "declare_scoped_full_mode_only_after_environment_and_resource_locks"
    assert migration_actions["univariate"]["prerequisite_status"]["formal_runtime_contract"] == "available_or_not_required"
    assert "analysis/registry/analysis_environments.json" in migration_actions["univariate"]["recommended_files"]
    assert migration_actions["correlation"]["prerequisite_status"]["legacy_sidecar_boundary"] == "not_migration_evidence"
    assert all(item["status"] == "blocked" for item in items.values())


def test_external_full_analysis_handoff_directories_are_lightweight_evidence_only() -> None:
    environment_readme = ROOT / "external_analysis_environments" / "README.md"
    resource_readme = ROOT / "external_analysis_resources" / "README.md"
    environment_gitignore = ROOT / "external_analysis_environments" / ".gitignore"
    resource_gitignore = ROOT / "external_analysis_resources" / ".gitignore"

    for path in (
        environment_readme,
        resource_readme,
        environment_gitignore,
        resource_gitignore,
        ROOT / "external_analysis_environments" / "evidence" / ".gitkeep",
        ROOT / "external_analysis_environments" / "logs" / ".gitkeep",
        ROOT / "external_analysis_resources" / "evidence" / ".gitkeep",
        ROOT / "external_analysis_resources" / "logs" / ".gitkeep",
    ):
        assert path.exists()

    environment_text = environment_readme.read_text(encoding="utf-8")
    resource_text = resource_readme.read_text(encoding="utf-8")
    assert "not part of the default app-dev runtime" in environment_text
    assert "runtime_package_install=forbidden" in environment_text
    assert "runtime_resource_download=forbidden" in environment_text
    assert "no full environment evidence is registered" in environment_text
    assert "not a runtime download cache for user requests" in resource_text
    assert "runtime_download_allowed=false" in resource_text
    assert "no full resource evidence is registered" in resource_text
    assert "*" in environment_gitignore.read_text(encoding="utf-8")
    assert "*" in resource_gitignore.read_text(encoding="utf-8")


def test_standard_worker_migration_matrix_is_module_level_and_read_only() -> None:
    matrix = build_standard_worker_migration_matrix()
    rows = {row["module_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.standard_worker_migration_matrix.v1"
    assert matrix["status"] == "partial"
    assert matrix["boundary"] == "matrix_is_read_only_no_worker_execution"
    assert matrix["evidence_registry_status"] == "passed"
    assert matrix["evidence_entry_count"] == 0
    assert matrix["evidence_registry_blockers"] == []
    assert matrix["expected_evidence_module_ids"] == [
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
    ]
    assert matrix["passed_evidence_module_ids"] == []
    assert matrix["blocked_evidence_module_ids"] == []
    assert matrix["missing_evidence_module_ids"] == matrix["expected_evidence_module_ids"]
    assert matrix["module_count"] >= 10
    assert matrix["formal_pending_count"] == matrix["module_count"]
    assert matrix["full_blocked_count"] == matrix["module_count"]
    assert matrix["adapter_status_counts"]["existing_controlled_python_and_r_contracts_pending_standard_worker_migration"] == 1
    assert matrix["adapter_status_counts"]["r_native_lite_contract_exists_pending_full_environment_and_standard_worker_migration"] == 2
    assert matrix["adapter_status_counts"]["planned_external_tool_adapter_only"] == 2
    assert matrix["migration_next_action_counts"]["declare_scoped_full_mode_only_after_environment_and_resource_locks"] == matrix["module_count"]
    assert matrix["migration_blocker_counts"]["full_mode_not_supported_in_registry"] == matrix["module_count"]
    assert matrix["migration_blocker_counts"]["registry_evidence_entry_missing_or_blocked"] == matrix["module_count"]
    assert matrix["migration_blocker_counts"]["legacy_sidecar_output_is_not_migration_evidence"] == 1
    assert {"deg", "survival", "univariate", "multivariate", "enrichment", "immune_infiltration", "spatial_transcriptomics", "docking", "molecular_dynamics"} <= set(rows)
    assert rows["deg"]["mock_status"] == "passed"
    assert rows["deg"]["lite_status"] == "standard_worker_lite_ready"
    assert rows["deg"]["full_status"] == "blocked"
    assert rows["deg"]["formal_worker_status"] == "pending_standard_worker_migration"
    assert rows["deg"]["migration_evidence_status"] == "missing"
    assert rows["deg"]["migration_readiness_status"] == "blocked"
    assert rows["deg"]["migration_prerequisite_status"]["overall"] == "blocked"
    assert rows["deg"]["migration_prerequisite_status"]["lite_standard_worker_path"] == "passed"
    assert rows["deg"]["migration_prerequisite_status"]["full_mode_registry"] == "blocked"
    assert rows["deg"]["migration_prerequisite_status"]["required_environment_lock"] == "required_before_migration_evidence"
    assert rows["deg"]["migration_prerequisite_status"]["required_resource_lock"] == "required_before_migration_evidence"
    assert rows["deg"]["migration_next_action"] == "declare_scoped_full_mode_only_after_environment_and_resource_locks"
    assert rows["deg"]["migration_evidence_template"]["schema_version"] == "biomedpilot.analysis.standard_worker_migration_evidence.v1"
    assert rows["deg"]["migration_evidence_template"]["module_id"] == "deg"
    assert rows["deg"]["migration_evidence_template"]["mode"] == "full"
    assert rows["deg"]["migration_evidence_template"]["required_worker_boundary"] == "standard_r_worker"
    assert rows["deg"]["migration_evidence_template"]["required_task_system_invocation"] == "task_center_registered"
    assert "legacy_service_adapter_sidecar" in rows["deg"]["migration_evidence_template"]["forbidden_evidence_sources"]
    assert "full_mode_not_supported_in_registry" in rows["deg"]["migration_blockers"]
    assert "registry_evidence_entry_missing_or_blocked" in rows["deg"]["migration_blockers"]
    assert rows["correlation"]["lite_status"] == "standard_worker_lite_ready"
    assert rows["correlation"]["standard_entrypoint"] == "analysis/runners/run_module.R"
    assert "legacy_sidecar_output_is_not_migration_evidence" in rows["correlation"]["migration_blockers"]
    assert rows["correlation"]["migration_prerequisite_status"]["legacy_sidecar_boundary"] == "not_migration_evidence"
    assert rows["univariate"]["formal_worker_status"] == "pending_standard_worker_migration"
    assert "formal_runtime_contract_not_implemented" not in rows["univariate"]["migration_blockers"]
    assert rows["univariate"]["migration_next_action"] == "declare_scoped_full_mode_only_after_environment_and_resource_locks"
    assert rows["enrichment"]["standard_entrypoint"] == "analysis/runners/run_module.R"
    assert rows["docking"]["full_environment"] == "r-chem-full"
    assert rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"


def test_full_activation_module_matrix_is_module_level_and_read_only() -> None:
    matrix = build_full_activation_module_matrix()
    rows = {row["module_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.full_activation_module_matrix.v1"
    assert matrix["status"] == "blocked"
    assert matrix["boundary"] == "read_only_module_level_full_activation_diagnostics"
    assert matrix["module_count"] == 10
    assert matrix["eligible_module_count"] == 0
    assert matrix["blocked_module_count"] == 10
    assert matrix["status_counts"]["blocked"] == 10
    assert matrix["blocker_counts"]["full_mode_not_supported_in_registry"] == 10
    assert matrix["blocker_counts"]["registry_evidence_entry_missing_or_blocked"] == 10
    assert matrix["blocker_counts"]["analysis_full_environment_lock_not_restored:r-bio-full"] == 7
    assert matrix["blocker_counts"]["analysis_resource_not_locked:reactome_full"] == 1
    assert matrix["blocker_counts"]["analysis_resource_not_locked:gromacs_tool"] == 1
    assert rows["deg"]["resource_status"] == "not_required"
    assert rows["deg"]["environment_status"] == "blocked"
    assert rows["deg"]["standard_worker_migration_status"] == "pending_standard_worker_migration"
    assert rows["enrichment"]["required_resource_ids"] == [
        "reactome_full",
        "msigdb_full",
        "go_full",
        "kegg_full",
        "orgdb_human_full",
    ]
    assert rows["enrichment"]["resource_status"] == "blocked"
    assert "analysis_resource_not_locked:reactome_full" in rows["enrichment"]["blockers"]
    assert rows["docking"]["full_environment"] == "r-chem-full"
    assert rows["docking"]["required_resource_ids"] == ["autodock_vina_tool", "docking_template_bundle"]
    assert rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
    assert rows["molecular_dynamics"]["required_resource_ids"] == ["gromacs_tool", "md_forcefield_template_bundle"]


def test_external_tool_adapter_matrix_tracks_chem_tool_isolation_without_execution() -> None:
    matrix = build_external_tool_adapter_matrix()
    rows = {row["module_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.external_tool_adapter_matrix.v1"
    assert matrix["status"] == "passed"
    assert matrix["boundary"] == "read_only_external_tool_adapter_isolation_diagnostics"
    assert matrix["module_count"] == 2
    assert matrix["passed_module_count"] == 2
    assert matrix["blocked_module_count"] == 0
    assert matrix["blocker_counts"] == {}
    assert matrix["warning_counts"]["lite_mode_writes_command_manifest_only_no_external_tool_execution"] == 2
    assert set(rows) == {"docking", "molecular_dynamics"}
    assert rows["docking"]["module_manifest"] == "analysis/modules/docking/module.json"
    assert rows["docking"]["analysis_environment"] == "r-bio-core"
    assert rows["docking"]["lite_environment"] == "r-bio-core"
    assert rows["docking"]["lite_worker_backend"] == "rscript"
    assert rows["docking"]["lite_external_tool_execution"] == "not_executed_in_lite_mode"
    assert rows["docking"]["full_supported"] is False
    assert rows["docking"]["full_environment"] == "r-chem-full"
    assert rows["docking"]["environment_lock"] == "renv/renv.chem-full.lock"
    assert rows["docking"]["dockerfile"] == "docker/Dockerfile.r-chem-full"
    assert rows["docking"]["external_tool_policy"] == "R_adapter_calls_AutoDock_Vina_in_chem_environment_only"
    assert rows["docking"]["runtime_install_policy"] == "forbidden"
    assert rows["docking"]["default_app_dependency"] is False
    assert rows["docking"]["required_resource_ids"] == ["autodock_vina_tool", "docking_template_bundle"]
    assert rows["docking"]["blocked_required_resource_ids"] == ["autodock_vina_tool", "docking_template_bundle"]
    assert rows["docking"]["blockers"] == []
    assert "lite_mode_writes_command_manifest_only_no_external_tool_execution" in rows["docking"]["warnings"]
    assert rows["molecular_dynamics"]["lite_external_tool_execution"] == "not_executed_in_lite_mode"
    assert rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
    assert rows["molecular_dynamics"]["dockerfile"] == "docker/Dockerfile.r-chem-gpu"
    assert rows["molecular_dynamics"]["external_tool_policy"] == "R_adapter_calls_GROMACS_in_chem_gpu_environment_only"
    assert rows["molecular_dynamics"]["required_resource_ids"] == ["gromacs_tool", "md_forcefield_template_bundle"]
    assert rows["molecular_dynamics"]["blocked_required_resource_ids"] == ["gromacs_tool", "md_forcefield_template_bundle"]
    assert rows["molecular_dynamics"]["blockers"] == []
    assert not any("AutoDock" in str(item) or "GROMACS" in str(item) for item in matrix["blocker_counts"])


def test_task_system_boundary_matrix_tracks_main_backend_task_contracts() -> None:
    matrix = build_task_system_boundary_matrix()
    rows = {row["module_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.task_system_boundary_matrix.v1"
    assert matrix["status"] == "passed"
    assert matrix["boundary"] == "read_only_main_backend_task_system_boundary_diagnostics"
    assert matrix["module_count"] == 10
    assert matrix["passed_module_count"] == 10
    assert matrix["blocked_module_count"] == 0
    assert matrix["blocker_counts"] == {}
    assert matrix["warning_counts"]["formal_worker_migration_pending:deg"] == 1
    assert matrix["warning_counts"]["formal_worker_migration_pending:molecular_dynamics"] == 1
    assert rows["deg"]["task_bridge_entrypoint"] == "app/analysis_runtime/task_bridge.py::run_analysis_module_task"
    assert rows["deg"]["task_center_service"] == "app/shared/task_center/service.py::TaskCenter"
    assert rows["deg"]["worker_invocation_schema"] == "analysis/schemas/output/worker_invocation.schema.json"
    assert rows["deg"]["input_schema"] == "analysis/schemas/input/module_input.schema.json"
    assert rows["deg"]["result_package_schema"] == "analysis/schemas/output/result_package.schema.json"
    assert rows["deg"]["result_index_task_types"] == ["deg", "recomputed_deg", "differential_expression"]
    assert rows["deg"]["mock_task_bridge_supported"] is True
    assert rows["deg"]["lite_task_bridge_supported"] is True
    assert rows["deg"]["lite_worker_backend"] == "rscript"
    assert rows["deg"]["full_task_bridge_policy"] == "blocked_before_worker_until_full_ready"
    assert rows["deg"]["required_task_system_invocation"] == "task_center_registered"
    assert rows["deg"]["worker_invocation_manifest_required"] is True
    assert rows["deg"]["direct_cli_is_not_ui_task_result"] is True
    assert rows["deg"]["legacy_sidecar_is_transitional_only"] is True
    assert rows["deg"]["formal_worker_status"] == "pending_standard_worker_migration"
    assert rows["deg"]["blockers"] == []
    assert "formal_worker_migration_pending:deg" in rows["deg"]["warnings"]
    assert rows["correlation"]["result_index_task_types"] == ["correlation"]
    assert "legacy_sidecar_boundary_transitional:correlation" in rows["correlation"]["warnings"]
    assert rows["docking"]["result_index_task_types"] == ["docking"]
    assert rows["docking"]["required_task_system_invocation"] == "task_center_registered"
    assert rows["molecular_dynamics"]["result_index_task_types"] == ["molecular_dynamics"]
    assert rows["molecular_dynamics"]["direct_cli_is_not_ui_task_result"] is True


def test_lite_task_bridge_coverage_matrix_tracks_all_lite_worker_contract_tests() -> None:
    matrix = build_lite_task_bridge_coverage_matrix()
    rows = {row["module_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.lite_task_bridge_coverage_matrix.v1"
    assert matrix["status"] == "passed"
    assert matrix["boundary"] == "static_lite_task_bridge_coverage_diagnostics_no_worker_execution"
    assert matrix["test_file"] == "tests/test_analysis_runtime_task_bridge.py"
    assert matrix["module_count"] == 10
    assert matrix["covered_module_count"] == 10
    assert matrix["blocked_module_count"] == 0
    assert matrix["blocker_counts"] == {}
    assert set(rows) == REQUIRED_MODULES
    assert rows["deg"]["fixture_input_status"] == "present"
    assert rows["deg"]["worker_backend"] == "rscript"
    assert rows["deg"]["coverage_test"] == "test_all_registered_lite_modules_run_through_standard_r_worker_package_contract"
    assert "standard_result_package validation passed" in rows["deg"]["required_contracts"]
    assert "worker_invocation boundary standard_r_worker" in rows["deg"]["required_contracts"]
    assert rows["molecular_dynamics"]["fixture_input"] == "analysis/fixtures/inputs/molecular_dynamics/module_input_lite.json"
    assert rows["correlation"]["status"] == "passed"


def test_legacy_sidecar_transition_matrix_tracks_transition_only_boundary() -> None:
    matrix = build_legacy_sidecar_transition_matrix()
    rows = {row["row_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.legacy_sidecar_transition_matrix.v1"
    assert matrix["status"] == "partial"
    assert matrix["boundary"] == "read_only_legacy_sidecar_transition_diagnostics"
    assert matrix["row_count"] == 5
    assert matrix["passed_row_count"] == 4
    assert matrix["partial_row_count"] == 1
    assert matrix["blocked_row_count"] == 0
    assert matrix["blocker_counts"] == {}
    assert set(matrix["transitional_module_ids"]) == REQUIRED_MODULES
    assert matrix["adapter_status_counts"]["existing_python_testing_level_sidecar_pending_standard_worker_migration"] == 1
    assert matrix["warning_counts"]["registry_current_adapter_status_transitional:correlation"] == 1
    assert rows["legacy_sidecar_writer_contract"]["status"] == "passed"
    assert rows["catalog_task_center_guard"]["status"] == "passed"
    assert rows["migration_evidence_forbids_sidecar"]["status"] == "passed"
    assert rows["sidecar_boundary_test_coverage"]["status"] == "passed"
    assert rows["registry_adapter_transition_scope"]["status"] == "partial"
    assert "correlation" in rows["registry_adapter_transition_scope"]["transitional_module_ids"]
    assert "registry_current_adapter_status_transitional:deg" in rows["registry_adapter_transition_scope"]["warnings"]
    assert rows["registry_adapter_transition_scope"]["boundary"] == "adapter_status_is_inventory_only_not_worker_migration_evidence"


def test_frontend_standard_package_consumption_matrix_tracks_partial_ui_boundary() -> None:
    matrix = build_frontend_standard_package_consumption_matrix()
    rows = {row["row_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.frontend_standard_package_consumption_matrix.v1"
    assert matrix["status"] == "partial"
    assert matrix["boundary"] == "read_only_frontend_standard_package_consumption_diagnostics"
    assert matrix["consumer_count"] == 5
    assert matrix["passed_consumer_count"] == 4
    assert matrix["partial_consumer_count"] == 1
    assert matrix["blocked_consumer_count"] == 0
    assert matrix["pending_detail_view_count"] == 3
    assert matrix["pending_detail_view_ids"] == [
        "formal_deg_review_panel",
        "formal_deg_plot_report_controls",
        "immune_tme_scoring_page",
    ]
    assert matrix["blocker_counts"] == {}
    assert matrix["warning_counts"]["detailed_result_views_still_need_standard_package_only_migration"] == 1
    assert matrix["warning_counts"]["detailed_result_view_pending_standard_package_migration:formal_deg_review_panel"] == 1
    assert rows["catalog_source_policy"]["status"] == "passed"
    assert rows["catalog_source_policy"]["consumer_surface"] == "build_standard_analysis_package_catalog"
    assert rows["catalog_source_policy"]["source_policy"] == "consume_result_index_registered_standard_result_packages_only"
    assert rows["catalog_detail_policy"]["status"] == "passed"
    assert rows["catalog_detail_policy"]["consumer_surface"] == "build_standard_analysis_package_detail"
    assert rows["analysis_center_state"]["status"] == "passed"
    assert rows["analysis_center_state"]["file_path"] == "app/bioinformatics/analysis_ui/state.py"
    assert rows["results_browser_tables"]["status"] == "passed"
    assert rows["results_browser_tables"]["consumer_surface"] == "BioinformaticsResultsBrowserWidget"
    assert rows["detailed_result_views_migration"]["status"] == "partial"
    assert rows["detailed_result_views_migration"]["pending_detail_view_count"] == 3
    assert rows["detailed_result_views_migration"]["pending_detail_view_ids"] == [
        "formal_deg_review_panel",
        "formal_deg_plot_report_controls",
        "immune_tme_scoring_page",
    ]
    assert rows["detailed_result_views_migration"]["pending_detail_views"][0]["consumer_surface"] == "BioinformaticsResultsBrowserWidget.formal_deg_review"
    assert "build_formal_deg_result_review" in rows["detailed_result_views_migration"]["pending_detail_views"][0]["current_private_tokens"]
    assert "build_standard_analysis_package_detail()" in rows["detailed_result_views_migration"]["migration_next_action"]
    assert rows["detailed_result_views_migration"]["blockers"] == []
    assert "detailed_result_views_still_need_standard_package_only_migration" in rows["detailed_result_views_migration"]["warnings"]
    assert "detailed_result_view_pending_standard_package_migration:immune_tme_scoring_page" in rows["detailed_result_views_migration"]["warnings"]


def test_reproducibility_provenance_matrix_tracks_static_contract_evidence() -> None:
    matrix = build_reproducibility_provenance_matrix()
    rows = {row["row_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.reproducibility_provenance_matrix.v1"
    assert matrix["status"] == "partial"
    assert matrix["boundary"] == "read_only_reproducibility_provenance_contract_diagnostics"
    assert matrix["row_count"] == 6
    assert matrix["passed_row_count"] == 5
    assert matrix["partial_row_count"] == 1
    assert matrix["blocked_row_count"] == 0
    assert matrix["blocker_counts"] == {}
    assert matrix["warning_counts"]["legacy_service_adapter_sidecars_are_not_isolated_standard_worker_provenance_evidence"] == 1
    assert {"input_hash", "parameter_hash", "random_seed", "engine", "runtime", "command"} <= set(matrix["required_fields"])
    assert {"r_version", "bioconductor_version", "package_versions", "external_tool_versions"} <= set(matrix["required_runtime_fields"])
    assert {"name", "version"} <= set(matrix["required_engine_fields"])
    assert rows["provenance_payload_schema"]["status"] == "passed"
    assert rows["provenance_payload_schema"]["required_runtime_fields"] == [
        "r_version",
        "bioconductor_version",
        "package_versions",
        "external_tool_versions",
    ]
    assert rows["standard_package_validator_required_provenance"]["status"] == "passed"
    assert rows["task_bridge_provenance_writer"]["status"] == "passed"
    assert rows["standard_r_worker_provenance_writer"]["status"] == "passed"
    assert rows["worker_invocation_schema"]["status"] == "passed"
    assert "runtime_install_policy" in rows["worker_invocation_schema"]["required_fields"]
    assert "resource_download_policy" in rows["worker_invocation_schema"]["required_fields"]
    assert rows["legacy_sidecar_provenance_boundary"]["status"] == "partial"
    assert rows["legacy_sidecar_provenance_boundary"]["warnings"] == [
        "legacy_service_adapter_sidecars_are_not_isolated_standard_worker_provenance_evidence"
    ]


def test_module_interface_matrix_tracks_standard_module_contracts() -> None:
    matrix = build_module_interface_matrix()
    rows = {row["module_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.module_interface_matrix.v1"
    assert matrix["status"] == "passed"
    assert matrix["boundary"] == "read_only_standard_module_interface_diagnostics"
    assert matrix["module_count"] == 10
    assert matrix["passed_module_count"] == 10
    assert matrix["blocked_module_count"] == 0
    assert matrix["blocker_counts"] == {}
    assert rows["deg"]["module_manifest"] == "analysis/modules/deg/module.json"
    assert rows["deg"]["standard_entrypoint"] == "analysis/runners/run_module.R"
    assert rows["deg"]["input_schema"] == "analysis/schemas/input/module_input.schema.json"
    assert rows["deg"]["output_schema"] == "analysis/schemas/output/result_package.schema.json"
    assert rows["deg"]["mock_supported"] is True
    assert rows["deg"]["lite_supported"] is True
    assert rows["deg"]["lite_runner"] == "analysis/runners/run_module.R"
    assert rows["deg"]["lite_worker_backend"] == "rscript"
    assert rows["deg"]["full_supported"] is False
    assert rows["deg"]["mock_fixture_validation_status"] == "passed"
    assert rows["deg"]["result_package_required"] == ["result.json", "provenance.json", "tables", "plots", "reports", "logs"]
    assert rows["docking"]["full_environment"] == "r-chem-full"
    assert rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
    assert rows["correlation"]["lite_runner"] == "analysis/runners/run_module.R"


def test_module_mode_readiness_matrix_tracks_mock_lite_full_layering_without_enabling_full() -> None:
    matrix = build_module_mode_readiness_matrix()
    rows = {row["module_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.module_mode_readiness_matrix.v1"
    assert matrix["status"] == "partial"
    assert matrix["module_count"] == 10
    assert matrix["passed_module_count"] == 0
    assert matrix["partial_module_count"] == 10
    assert matrix["blocked_module_count"] == 0
    assert set(matrix["full_blocked_module_ids"]) == REQUIRED_MODULES
    assert matrix["blocker_counts"] == {}
    assert matrix["warning_counts"]["module_full_mode_blocked:deg"] == 1
    assert matrix["boundary"] == "read_only_mock_lite_full_mode_layering_diagnostics"
    assert rows["deg"]["mock_status"] == "passed"
    assert rows["deg"]["lite_status"] == "passed"
    assert rows["deg"]["lite_environment"] == "r-bio-core"
    assert rows["deg"]["lite_worker_backend"] == "rscript"
    assert rows["deg"]["full_status"] == "blocked"
    assert rows["deg"]["full_supported"] is False
    assert rows["deg"]["full_environment"] == "r-bio-full"
    assert rows["deg"]["full_blocker"] == "full_r_worker_container_not_available"
    assert "module_full_mode_blocked:deg" in rows["deg"]["warnings"]
    assert rows["docking"]["full_environment"] == "r-chem-full"
    assert rows["docking"]["lite_result_semantics"] == "testing_level"
    assert rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"
    assert rows["molecular_dynamics"]["full_status"] == "blocked"


def test_environment_artifact_matrix_tracks_docker_renv_split_without_restoring_full() -> None:
    matrix = build_environment_artifact_matrix()
    rows = {row["environment_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.environment_artifact_matrix.v1"
    assert matrix["status"] == "partial"
    assert matrix["environment_count"] == 6
    assert matrix["passed_environment_count"] == 2
    assert matrix["partial_environment_count"] == 4
    assert matrix["blocked_environment_count"] == 0
    assert matrix["blocker_counts"] == {}
    assert matrix["full_environment_ids"] == ["r-bio-full", "r-spatial-full", "r-chem-full", "r-chem-gpu"]
    assert matrix["restored_full_environment_ids"] == []
    assert matrix["warning_counts"]["environment_renv_lock_scaffold_only_not_restored:r-bio-full"] == 1
    assert matrix["warning_counts"]["environment_docker_image_build_not_proven:r-chem-gpu"] == 1
    assert matrix["boundary"] == "read_only_environment_artifact_split_diagnostics"
    assert rows["app-dev"]["status"] == "passed"
    assert rows["app-dev"]["environment_class"] == "app-dev"
    assert rows["app-dev"]["dockerfile_status"] == "present"
    assert rows["app-dev"]["renv_lock_status"] == "present"
    assert rows["app-dev"]["allows_heavy_analysis_dependencies"] is False
    assert rows["app-dev"]["allowed_module_ids"] == []
    assert rows["r-bio-core"]["status"] == "passed"
    assert rows["r-bio-core"]["environment_class"] == "lite"
    assert rows["r-bio-core"]["allows_heavy_analysis_dependencies"] is False
    assert "deg" in rows["r-bio-core"]["allowed_module_ids"]
    assert rows["r-bio-full"]["status"] == "partial"
    assert rows["r-bio-full"]["environment_class"] == "full"
    assert rows["r-bio-full"]["renv_policy_status"] == "scaffold_only_not_restored"
    assert rows["r-bio-full"]["renv_package_count"] == 0
    assert rows["r-bio-full"]["resource_lock_required"] is True
    assert "analysis_environment_renv_lock_not_restored:r-bio-full:scaffold_only_not_restored" in rows["r-bio-full"]["warnings"]
    assert rows["r-chem-gpu"]["renv_policy_environment"] == "r-chem-full"
    assert rows["r-chem-gpu"]["external_tool_lock_required"] is True
    assert rows["r-chem-gpu"]["status"] == "partial"


def test_resource_artifact_matrix_tracks_full_resource_locks_without_preparing_resources() -> None:
    matrix = build_resource_artifact_matrix()
    rows = {row["resource_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.resource_artifact_matrix.v1"
    assert matrix["status"] == "partial"
    assert matrix["resource_count"] == 12
    assert matrix["locked_resource_count"] == 1
    assert matrix["blocked_resource_count"] == 11
    assert matrix["passed_resource_count"] == 1
    assert matrix["partial_resource_count"] == 11
    assert matrix["failed_resource_count"] == 0
    assert matrix["evidence_entry_count"] == 0
    assert "reactome_full" in matrix["missing_resource_ids"]
    assert matrix["warning_counts"]["resource_full_lock_not_ready:reactome_full"] == 1
    assert matrix["warning_counts"]["resource_lock_evidence_registry_entry_missing:gromacs_tool"] == 1
    assert matrix["boundary"] == "read_only_full_resource_lock_artifact_diagnostics"
    assert rows["mock_fixture_builtin_v1"]["status"] == "passed"
    assert rows["mock_fixture_builtin_v1"]["lock_status"] == "locked"
    assert rows["mock_fixture_builtin_v1"]["resource_lock_required"] is False
    assert rows["mock_fixture_builtin_v1"]["lock_evidence_status"] == "present"
    assert rows["reactome_full"]["status"] == "partial"
    assert rows["reactome_full"]["resource_family"] == "pathway_database"
    assert rows["reactome_full"]["version_status"] == "placeholder"
    assert rows["reactome_full"]["hash_status"] == "placeholder"
    assert rows["reactome_full"]["license_status"] == "placeholder"
    assert rows["reactome_full"]["cache_path_status"] == "missing"
    assert rows["reactome_full"]["lock_evidence_status"] == "missing"
    assert rows["reactome_full"]["runtime_download_allowed"] is False
    assert rows["gromacs_tool"]["resource_family"] == "external_scientific_tool"
    assert rows["gromacs_tool"]["required_for_modules"] == ["molecular_dynamics"]


def test_standard_worker_entrypoint_matrix_tracks_runner_contract_and_partial_migration() -> None:
    matrix = build_standard_worker_entrypoint_matrix()
    rows = {row["row_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.standard_worker_entrypoint_matrix.v1"
    assert matrix["status"] == "partial"
    assert matrix["boundary"] == "read_only_standard_r_worker_entrypoint_contract_diagnostics"
    assert matrix["standard_entrypoint"] == "analysis/runners/run_module.R"
    assert set(matrix["lite_module_ids"]) == REQUIRED_MODULES
    assert set(matrix["formal_pending_module_ids"]) == REQUIRED_MODULES
    assert matrix["row_count"] == 6
    assert matrix["passed_row_count"] == 5
    assert matrix["partial_row_count"] == 1
    assert matrix["blocked_row_count"] == 0
    assert matrix["blocker_counts"] == {}
    assert matrix["warning_counts"]["standard_worker_entrypoint_formal_migration_pending:deg"] == 1
    assert rows["standard_r_worker_cli_contract"]["status"] == "passed"
    assert rows["standard_r_worker_package_output_contract"]["status"] == "passed"
    assert rows["standard_r_worker_lite_dispatch_contract"]["status"] == "passed"
    assert rows["standard_r_worker_lite_dispatch_contract"]["lite_module_count"] == 10
    assert set(rows["standard_r_worker_lite_dispatch_contract"]["lite_module_ids"]) == REQUIRED_MODULES
    assert rows["standard_r_worker_main_backend_invocation_contract"]["status"] == "passed"
    assert rows["standard_r_worker_no_runtime_acquisition"]["status"] == "passed"
    assert rows["standard_r_worker_no_runtime_acquisition"]["blockers"] == []
    assert rows["standard_r_worker_formal_migration_boundary"]["status"] == "partial"
    assert "standard_worker_entrypoint_formal_migration_pending:survival" in rows["standard_r_worker_formal_migration_boundary"]["warnings"]


def test_standard_worker_matrices_use_module_manifest_when_registry_lite_runner_drifts() -> None:
    registry = deepcopy(read_json(ROOT / "analysis" / "registry" / "analysis_modules.json"))
    for module in registry["modules"]:
        if module["module_id"] == "correlation":
            module["modes"]["lite"].pop("runner", None)
            module["modes"]["lite"]["worker_backend"] = "python_fixture"

    entrypoint = build_standard_worker_entrypoint_matrix(registry=registry)
    migration = build_standard_worker_migration_matrix(registry=registry)
    migration_rows = {row["module_id"]: row for row in migration["rows"]}

    assert "correlation" in entrypoint["lite_module_ids"]
    assert migration_rows["correlation"]["lite_status"] == "standard_worker_lite_ready"
    assert migration_rows["correlation"]["standard_entrypoint"] == "analysis/runners/run_module.R"


def test_standard_worker_migration_evidence_registry_is_authoritative_and_empty_by_default() -> None:
    registry = load_standard_worker_migration_evidence_registry()
    validation = validate_standard_worker_migration_evidence_registry(registry)

    assert registry["schema_version"] == "biomedpilot.analysis.standard_worker_migration_evidence_registry.v1"
    assert registry["policy"]["registry_is_authoritative"] is True
    assert registry["policy"]["expected_module_ids_are_authoritative"] is True
    assert registry["policy"]["migration_completion_requires_schema_valid_evidence"] is True
    assert registry["policy"]["mock_lite_and_legacy_sidecar_evidence_forbidden"] is True
    assert registry["expected_module_ids"] == [
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
    ]
    assert registry["evidence_entries"] == []
    assert validation["schema_version"] == "biomedpilot.analysis.standard_worker_migration_evidence_registry_validation.v1"
    assert validation["status"] == "passed"
    assert validation["schema_validation_status"] == "passed"
    assert validation["entry_count"] == 0
    assert validation["expected_module_ids"] == [
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
    ]
    assert validation["passed_module_ids"] == []
    assert validation["blocked_module_ids"] == []
    assert validation["missing_module_ids"] == validation["expected_module_ids"]
    assert validation["missing_count"] == len(validation["expected_module_ids"])
    assert validation["blockers"] == []


def test_standard_worker_migration_evidence_registry_schema_blocks_shape_drift() -> None:
    validation = validate_standard_worker_migration_evidence_registry(
        {
            "schema_version": "wrong",
            "policy": [],
            "evidence_entries": {},
        }
    )

    assert validation["status"] == "blocked"
    assert validation["schema_validation_status"] == "blocked"
    assert "standard_worker_migration_evidence_registry_const_mismatch:schema_version" in validation["blockers"]
    assert "standard_worker_migration_evidence_registry_type_invalid:policy" in validation["blockers"]
    assert "standard_worker_migration_evidence_registry_required_field_missing:expected_module_ids" in validation["blockers"]
    assert "standard_worker_migration_evidence_registry_expected_module_ids_invalid" in validation["blockers"]
    assert "standard_worker_migration_evidence_registry_type_invalid:evidence_entries" in validation["blockers"]


def test_standard_worker_migration_evidence_registry_blocks_expected_module_scope_drift() -> None:
    registry = deepcopy(load_standard_worker_migration_evidence_registry())
    registry["expected_module_ids"] = ["deg"]

    validation = validate_standard_worker_migration_evidence_registry(registry)

    assert validation["status"] == "blocked"
    assert "standard_worker_migration_evidence_registry_expected_module_ids_mismatch" in validation["blockers"]
    assert validation["expected_module_ids"] == [
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
    ]


def test_standard_worker_migration_matrix_does_not_accept_registry_only_full_supported_drift() -> None:
    registry = deepcopy(read_json(ROOT / "analysis" / "registry" / "analysis_modules.json"))
    modules = {item["module_id"]: item for item in registry["modules"]}  # type: ignore[index]
    modules["deg"]["modes"]["full"]["supported"] = True
    modules["deg"]["modes"]["full"]["blocker"] = ""
    matrix = build_standard_worker_migration_matrix(registry)
    rows = {row["module_id"]: row for row in matrix["rows"]}

    assert rows["deg"]["full_status"] == "blocked"
    assert rows["deg"]["lite_status"] == "standard_worker_lite_ready"
    assert rows["deg"]["migration_evidence_status"] == "missing"
    assert rows["deg"]["formal_worker_status"] == "pending_standard_worker_migration"
    assert "full_mode_not_supported_in_registry" in rows["deg"]["migration_blockers"]
    assert rows["deg"]["migration_prerequisite_status"]["full_mode_registry"] == "blocked"
    assert rows["deg"]["migration_next_action"] == "declare_scoped_full_mode_only_after_environment_and_resource_locks"
    assert matrix["formal_pending_count"] == matrix["module_count"]


def test_standard_worker_migration_evidence_registry_blocks_bad_entries() -> None:
    validation = validate_standard_worker_migration_evidence_registry(
        {
            "schema_version": "biomedpilot.analysis.standard_worker_migration_evidence_registry.v1",
            "policy": {
                "registry_is_authoritative": True,
                "migration_completion_requires_schema_valid_evidence": True,
                "mock_lite_and_legacy_sidecar_evidence_forbidden": True,
                "manual_scoped_migration_only": True,
            },
            "evidence_entries": [
                {
                    "module_id": "deg",
                    "evidence": {
                        "schema_version": "biomedpilot.analysis.standard_worker_migration_evidence.v1",
                        "module_id": "deg",
                        "mode": "mock",
                        "task_id": "mock-deg",
                        "result_package_dir": "analysis/fixtures/outputs/deg/mock_result_package",
                        "frontend_consumes_standard_package": True,
                        "result_index_registered": True,
                        "formal_result_semantics_preserved": True,
                    },
                }
            ],
        }
    )

    assert validation["status"] == "blocked"
    assert validation["entry_count"] == 1
    assert validation["blocked_module_ids"] == ["deg"]
    assert "deg" in validation["missing_module_ids"]
    assert any(
        blocker.startswith("standard_worker_migration_evidence_registry_entry:deg:")
        for blocker in validation["blockers"]
    )


def test_standard_worker_migration_evidence_blocks_missing_package_and_ui_contract() -> None:
    validation = validate_standard_worker_migration_evidence(
        "deg",
        {
            "schema_version": "biomedpilot.analysis.standard_worker_migration_evidence.v1",
            "module_id": "deg",
            "mode": "full",
            "task_id": "task-deg-full",
            "result_package_dir": "missing/package",
            "frontend_consumes_standard_package": False,
            "result_index_registered": False,
            "formal_result_semantics_preserved": False,
        },
    )

    assert validation["status"] == "blocked"
    assert "standard_worker_migration_result_package_dir_not_found" in validation["blockers"]
    assert "standard_worker_migration_frontend_standard_package_consumption_missing" in validation["blockers"]
    assert "standard_worker_migration_result_index_registration_missing" in validation["blockers"]
    assert "standard_worker_migration_formal_result_semantics_not_preserved" in validation["blockers"]


def test_standard_worker_migration_evidence_schema_is_checked_before_completion_claim() -> None:
    schema = read_json(ROOT / "analysis" / "schemas" / "output" / "standard_worker_migration_evidence.schema.json")
    validation = validate_standard_worker_migration_evidence(
        "deg",
        {
            "schema_version": "wrong",
            "module_id": "",
            "mode": "lite",
            "task_id": "",
            "result_package_dir": "",
            "frontend_consumes_standard_package": "yes",
            "result_index_registered": "yes",
            "formal_result_semantics_preserved": "yes",
        },
    )

    assert schema["$id"] == "biomedpilot.analysis.standard_worker_migration_evidence.v1"
    assert "standard_worker_migration_evidence_const_mismatch:schema_version" in validation["blockers"]
    assert "standard_worker_migration_evidence_const_mismatch:mode" in validation["blockers"]
    assert "standard_worker_migration_evidence_min_length_invalid:module_id" in validation["blockers"]
    assert "standard_worker_migration_evidence_type_invalid:frontend_consumes_standard_package" in validation["blockers"]
    assert "standard_worker_migration_evidence_type_invalid:result_index_registered" in validation["blockers"]
    assert "standard_worker_migration_evidence_type_invalid:formal_result_semantics_preserved" in validation["blockers"]
    assert "required_worker_boundary" in schema["required"]
    assert "required_task_system_invocation" in schema["required"]
    assert "required_worker_migration_status" in schema["required"]
    assert "forbidden_evidence_sources" in schema["required"]
    assert schema["properties"]["required_worker_boundary"]["const"] == "standard_r_worker"
    assert schema["properties"]["required_task_system_invocation"]["const"] == "task_center_registered"
    assert schema["properties"]["required_worker_migration_status"]["const"] == "standard_worker_contract"
    assert "standard_worker_migration_required_worker_boundary_invalid" in validation["blockers"]
    assert "standard_worker_migration_required_task_system_invocation_invalid" in validation["blockers"]
    assert "standard_worker_migration_required_worker_migration_status_invalid" in validation["blockers"]
    assert "standard_worker_migration_forbidden_evidence_sources_invalid" in validation["blockers"]


def test_standard_worker_migration_evidence_does_not_accept_mock_or_lite_fixture_package() -> None:
    validation = validate_standard_worker_migration_evidence(
        "deg",
        {
            "schema_version": "biomedpilot.analysis.standard_worker_migration_evidence.v1",
            "module_id": "deg",
            "mode": "mock",
            "task_id": "mock-deg",
            "result_package_dir": "analysis/fixtures/outputs/deg/mock_result_package",
            "frontend_consumes_standard_package": True,
            "result_index_registered": True,
            "formal_result_semantics_preserved": True,
        },
    )

    assert validation["status"] == "blocked"
    assert "standard_worker_migration_requires_full_mode_standard_package" in validation["blockers"]
    assert "standard_worker_migration_requires_standard_r_worker_boundary" in validation["blockers"]
    assert "standard_worker_migration_requires_task_center_registered_invocation" in validation["blockers"]
    assert "standard_worker_migration_requires_standard_worker_contract_status" in validation["blockers"]


def test_standard_worker_migration_evidence_requires_passed_formal_ready_package(tmp_path: Path) -> None:
    package_dir = _write_candidate_standard_worker_package(
        tmp_path,
        result_status="passed",
        result_semantics="testing_level",
        environment_status="blocked_full_mode_environment_lock",
        environment_ready=False,
        resource_ready=False,
    )

    validation = validate_standard_worker_migration_evidence(
        "deg",
        _standard_worker_migration_evidence(package_dir),
    )

    assert validation["status"] == "blocked"
    assert "standard_worker_migration_requires_formal_computed_result" in validation["blockers"]
    assert "standard_worker_migration_analysis_environment_not_ready" in validation["blockers"]
    assert "standard_worker_migration_environment_lock_not_ready" in validation["blockers"]
    assert "standard_worker_migration_resource_lock_not_ready" in validation["blockers"]
    assert "standard_worker_migration_requires_standard_r_worker_boundary" not in validation["blockers"]
    assert "standard_worker_migration_requires_task_center_registered_invocation" not in validation["blockers"]
    assert "standard_worker_migration_requires_standard_worker_contract_status" not in validation["blockers"]


def test_standard_worker_migration_evidence_requires_passed_result_without_blockers(tmp_path: Path) -> None:
    package_dir = _write_candidate_standard_worker_package(
        tmp_path,
        result_status="blocked",
        result_semantics="formal_computed_result",
        result_blockers=["blocked_full_mode_worker_not_enabled"],
        environment_status="passed",
        environment_ready=True,
        resource_ready=True,
    )

    validation = validate_standard_worker_migration_evidence(
        "deg",
        _standard_worker_migration_evidence(package_dir),
    )

    assert validation["status"] == "blocked"
    assert "standard_worker_migration_requires_passed_result" in validation["blockers"]
    assert "standard_worker_migration_result_blockers_present" in validation["blockers"]
    assert "standard_worker_migration_analysis_environment_not_ready" not in validation["blockers"]


def test_standard_worker_migration_evidence_accepts_schema_valid_standard_worker_package(tmp_path: Path) -> None:
    package_dir = _write_candidate_standard_worker_package(
        tmp_path,
        result_status="passed",
        result_semantics="formal_computed_result",
        environment_status="passed",
        environment_ready=True,
        resource_ready=True,
    )

    validation = validate_standard_worker_migration_evidence(
        "deg",
        _standard_worker_migration_evidence(package_dir),
    )

    assert validation["status"] == "passed"
    assert validation["blockers"] == []
    assert validation["required_boundary"] == "standard_r_worker"
    assert validation["required_invocation"] == "task_center_registered"
    assert validation["required_migration_status"] == "standard_worker_contract"


def test_spatial_and_chem_modules_are_isolated_from_app_dev_and_bio_core() -> None:
    spatial = read_json(ROOT / "analysis" / "modules" / "spatial_transcriptomics" / "module.json")
    docking = read_json(ROOT / "analysis" / "modules" / "docking" / "module.json")
    molecular_dynamics = read_json(ROOT / "analysis" / "modules" / "molecular_dynamics" / "module.json")

    assert spatial["dockerfile"] == "docker/Dockerfile.r-spatial-full"
    assert spatial["environment_lock"] == "renv/renv.spatial-full.lock"
    assert docking["dockerfile"] == "docker/Dockerfile.r-chem-full"
    assert molecular_dynamics["dockerfile"] == "docker/Dockerfile.r-chem-gpu"
    assert "external_tool_policy" in docking
    assert "external_tool_policy" in molecular_dynamics


def test_standard_schemas_and_mock_result_package_exist_without_r_dependency() -> None:
    input_schema = read_json(ROOT / "analysis" / "schemas" / "input" / "module_input.schema.json")
    output_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "result_package.schema.json")
    result_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "result.schema.json")
    provenance_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "provenance.schema.json")
    invocation_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "worker_invocation.schema.json")
    migration_registry_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "standard_worker_migration_evidence_registry.schema.json")
    full_activation_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "full_analysis_activation_gate.schema.json")
    remediation_queue_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "remediation_queue.schema.json")
    resource_lock_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "resource_lock_evidence.schema.json")
    resource_lock_registry_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "resource_lock_evidence_registry.schema.json")
    environment_lock_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "environment_lock_evidence.schema.json")
    environment_lock_registry_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "environment_lock_evidence_registry.schema.json")
    evidence_template_package_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "evidence_template_package.schema.json")
    result = read_json(ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / "result.json")
    provenance = read_json(ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / "provenance.json")

    assert "module_id" in input_schema["required"]
    assert "result_json" in output_schema["required"]
    assert "provenance_json" in output_schema["required"]
    directory_schema = output_schema["properties"]["directories"]
    assert directory_schema["minItems"] == 4
    assert directory_schema["uniqueItems"] is True
    required_directories = [
        item["contains"]["const"]
        for item in directory_schema["allOf"]
    ]
    assert required_directories == ["tables", "plots", "reports", "logs"]
    assert result_schema["$id"] == "biomedpilot.analysis.result.v1"
    assert provenance_schema["$id"] == "biomedpilot.analysis.provenance.v1"
    assert {"result_semantics", "tables", "plots", "reports", "blockers", "warnings"} <= set(result_schema["required"])
    assert {"input_hash", "parameter_hash", "random_seed", "engine", "runtime", "command"} <= set(provenance_schema["required"])
    assert {"name", "version"} <= set(provenance_schema["properties"]["engine"]["required"])  # type: ignore[index]
    runtime_required = set(provenance_schema["properties"]["runtime"]["required"])  # type: ignore[index]
    assert {"r_version", "bioconductor_version", "package_versions", "external_tool_versions"} <= runtime_required
    assert invocation_schema["$id"] == "biomedpilot.analysis.worker_invocation.v1"
    assert migration_registry_schema["$id"] == "biomedpilot.analysis.standard_worker_migration_evidence_registry.v1"
    assert "evidence_entries" in migration_registry_schema["required"]
    migration_evidence_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "standard_worker_migration_evidence.schema.json")
    assert migration_evidence_schema["properties"]["required_result_status"]["const"] == "passed"
    assert migration_evidence_schema["properties"]["required_result_semantics"]["const"] == "formal_computed_result"
    assert migration_evidence_schema["properties"]["required_engine_name"]["const"] == "biomedpilot_standard_r_worker"
    assert migration_evidence_schema["properties"]["required_analysis_environment_status"]["const"] == "passed"
    assert migration_evidence_schema["properties"]["required_worker_boundary"]["const"] == "standard_r_worker"
    assert migration_evidence_schema["properties"]["required_task_system_invocation"]["const"] == "task_center_registered"
    assert migration_evidence_schema["properties"]["required_worker_migration_status"]["const"] == "standard_worker_contract"
    assert "forbidden_evidence_sources" in migration_evidence_schema["required"]
    assert full_activation_schema["$id"] == "biomedpilot.analysis.full_analysis_activation_gate.v1"
    assert "checks" in full_activation_schema["required"]
    assert "execution_policy" in full_activation_schema["required"]
    assert remediation_queue_schema["$id"] == "biomedpilot.analysis.remediation_queue.v1"
    assert "items" in remediation_queue_schema["required"]
    assert "install_policy" in remediation_queue_schema["required"]
    assert resource_lock_schema["$id"] == "biomedpilot.analysis.resource_lock_evidence.v1"
    assert "runtime_download_allowed" in resource_lock_schema["required"]
    assert "cache_content" in resource_lock_schema["required"]
    assert resource_lock_schema["properties"]["hash"]["required"] == ["algorithm", "value"]
    assert resource_lock_schema["properties"]["cache_content"]["required"] == ["non_empty"]
    assert resource_lock_registry_schema["$id"] == "biomedpilot.analysis.resource_lock_evidence_registry.v1"
    assert "expected_resource_ids" in resource_lock_registry_schema["required"]
    assert "evidence_entries" in resource_lock_registry_schema["required"]
    assert environment_lock_schema["$id"] == "biomedpilot.analysis.environment_lock_evidence.v1"
    assert "renv_lock_content" in environment_lock_schema["required"]
    assert "docker_image" in environment_lock_schema["required"]
    assert environment_lock_schema["properties"]["package_lock_hash"]["required"] == ["algorithm", "value"]
    assert environment_lock_schema["properties"]["renv_lock_content"]["required"] == ["policy_status", "packages_non_empty"]
    assert environment_lock_schema["properties"]["docker_image"]["required"] == ["image_ref", "digest", "architecture", "build_status", "build_log"]
    assert evidence_template_package_schema["$id"] == "biomedpilot.analysis.evidence_template_package.v1"
    assert "environment_lock_evidence_templates" in evidence_template_package_schema["required"]
    assert "resource_lock_evidence_templates" in evidence_template_package_schema["required"]
    assert "standard_worker_migration_evidence_templates" in evidence_template_package_schema["required"]
    assert "package_lock_hash" in environment_lock_schema["required"]
    assert "runtime_package_install" in environment_lock_schema["required"]
    assert environment_lock_registry_schema["$id"] == "biomedpilot.analysis.environment_lock_evidence_registry.v1"
    assert "expected_environment_ids" in environment_lock_registry_schema["required"]
    assert "evidence_entries" in environment_lock_registry_schema["required"]
    assert "worker_backend" in invocation_schema["required"]
    assert "invocation_status" in invocation_schema["required"]
    assert "runtime_install_policy" in invocation_schema["required"]
    assert invocation_schema["properties"]["runtime_install_policy"]["const"] == "forbidden"  # type: ignore[index]
    assert invocation_schema["properties"]["resource_download_policy"]["const"] == "forbidden"  # type: ignore[index]
    assert "legacy_service_adapter" in invocation_schema["properties"]["worker_backend"]["enum"]  # type: ignore[index]
    assert "sidecar_recorded" in invocation_schema["properties"]["invocation_status"]["enum"]  # type: ignore[index]
    task_invocation_enum = invocation_schema["properties"]["worker_boundary"]["properties"]["task_system_invocation"]["enum"]  # type: ignore[index]
    assert {"task_center_registered", "standard_worker_direct_cli", "legacy_service_adapter_direct_call"} <= set(task_invocation_enum)
    assert result["mode"] == "mock"
    assert result["status"] == "passed"
    assert provenance["mode"] == "mock"
    for dirname in ("tables", "plots", "reports", "logs"):
        assert (ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / dirname).exists()


def test_default_source_tree_does_not_install_r_packages_or_download_resources_in_request_flow() -> None:
    forbidden = (
        "install.packages",
        "BiocManager::install",
        "pak::pkg_install",
        "remotes::install_github",
        "download.file",
        "curl::curl_download",
        "BiocFileCache(",
        "AnnotationHub(",
        "ExperimentHub(",
        "wget ",
        "curl -",
    )
    searched_roots = [ROOT / "app", ROOT / "scripts", ROOT / "analysis", ROOT / "docker"]
    offenders: list[str] = []
    for root in searched_roots:
        for path in root.rglob("*"):
            is_dockerfile = path.name.startswith("Dockerfile")
            if not path.is_file() or (path.suffix.lower() not in {".py", ".r", ".rscript", ".sh"} and not is_dockerfile):
                continue
            if "__pycache__" in path.parts or "legacy" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for needle in forbidden:
                if needle in text:
                    offenders.append(f"{path.relative_to(ROOT)}:{needle}")
    assert offenders == []


def test_standard_r_runner_has_no_runtime_package_installer_or_library_imports() -> None:
    runner = (ROOT / "analysis" / "runners" / "run_module.R").read_text(encoding="utf-8")

    assert "install.packages" not in runner
    assert "BiocManager::install" not in runner
    assert "pak::pkg_install" not in runner
    assert "remotes::install_github" not in runner
    assert "library(" not in runner
    assert "require(" not in runner
    assert "run_module.R <input_json> <output_dir> <mode>" in runner
    assert "result.json" in runner
    assert "provenance.json" in runner


def test_active_bioinformatics_r_subprocess_invocation_is_centralized_in_analysis_runtime() -> None:
    offenders: list[str] = []
    for path in (ROOT / "app" / "bioinformatics").rglob("*.py"):
        if "__pycache__" in path.parts or "legacy" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "subprocess.run(" in text and ("--vanilla" in text or "Rscript" in text or "library(" in text):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == []


def test_transition_r_adapters_do_not_own_subprocess_defaults() -> None:
    adapter_paths = [
        ROOT / "app" / "bioinformatics" / "enrichment_r_adapter.py",
        ROOT / "app" / "bioinformatics" / "deg_engine" / "multifactor_r_runner.py",
    ]

    for path in adapter_paths:
        text = path.read_text(encoding="utf-8")
        assert "import subprocess" not in text
        assert "subprocess.run" not in text
        assert "Popen(" not in text
        assert "run_external_r_command" in text


def test_standard_r_runner_mock_mode_copies_module_fixture_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "enrichment" / "module_input.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "mock"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    assert result["module_id"] == "enrichment"
    assert result["task_id"] == "enrichment-mock-fixture"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "mock_result_not_scientific_output" in result["warnings"]
    assert (output_dir / "tables" / "mock_summary.tsv").is_file()
    assert (output_dir / "reports" / "README_mock.md").is_file()
    assert (output_dir / "logs" / "worker.log").is_file()
    assert (output_dir / "logs" / "worker_invocation.json").is_file()
    assert read_json(output_dir / "module_input.json") == read_json(input_json)
    assert provenance["module_id"] == "enrichment"
    assert provenance["task_id"] == "enrichment-mock-fixture"
    assert provenance["runtime"]["r_version"] != "not_required_for_mock"  # type: ignore[index]
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["input_hash"] != "fixture"
    assert provenance["parameter_hash"] != "fixture"
    assert provenance["parameter_hash"] != provenance["input_hash"]
    assert "analysis/runners/run_module.R" in provenance["command"]
    validation = validate_standard_result_package(
        output_dir,
        expected_module_id="enrichment",
        expected_task_id="enrichment-mock-fixture",
        expected_mode="mock",
    )
    invocation = read_json(output_dir / "logs" / "worker_invocation.json")
    assert validation["status"] == "passed"
    assert invocation["input_manifest"] == "module_input.json"
    assert invocation["worker_boundary"]["task_system_invocation"] == "standard_worker_direct_cli"  # type: ignore[index]


def test_standard_r_runner_lite_full_modes_write_blocked_standard_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-full-output"
    payload = read_json(ROOT / "analysis" / "fixtures" / "inputs" / "enrichment" / "module_input.json")
    payload["mode"] = "full"
    input_json = tmp_path / "full_input.json"
    input_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "full"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    assert result["module_id"] == "enrichment"
    assert result["mode"] == "full"
    assert result["status"] == "blocked"
    assert "standard_worker_mode_not_enabled:full" in result["blockers"]
    assert "analysis_environment_renv_lock_not_restored:r-bio-full:scaffold_only_not_restored" in result["blockers"]
    assert "analysis_resource_not_locked:reactome_full" in result["blockers"]
    assert "analysis_resource_not_locked:msigdb_full" in result["blockers"]
    assert provenance["runtime"]["r_version"] == "not_executed"  # type: ignore[index]
    assert provenance["analysis_environment"]["status"] == "blocked_full_mode_environment_lock"  # type: ignore[index]
    assert provenance["analysis_environment"]["environment_id"] == "r-bio-full"  # type: ignore[index]
    assert provenance["analysis_environment"]["dockerfile"] == "docker/Dockerfile.r-bio-full"  # type: ignore[index]
    assert provenance["analysis_environment"]["renv_lock"] == "renv/renv.bio-full.lock"  # type: ignore[index]
    assert provenance["analysis_environment"]["environment_lock_status"]["blockers"] == [  # type: ignore[index]
        "analysis_environment_renv_lock_not_restored:r-bio-full:scaffold_only_not_restored"
    ]
    assert provenance["analysis_environment"]["resource_lock_status"]["blockers"]  # type: ignore[index]
    assert provenance["parameter_hash"] != provenance["input_hash"]
    assert read_json(output_dir / "module_input.json") == payload
    assert (output_dir / "logs" / "worker.log").is_file()
    assert (output_dir / "logs" / "worker_invocation.json").is_file()
    validation = validate_standard_result_package(
        output_dir,
        expected_module_id="enrichment",
        expected_task_id="enrichment-mock-fixture",
        expected_mode="full",
    )
    invocation = read_json(output_dir / "logs" / "worker_invocation.json")
    assert validation["status"] == "passed"
    assert invocation["input_manifest"] == "module_input.json"
    assert invocation["invocation_status"] == "not_invoked_mode_gate"
    assert invocation["worker_boundary"]["task_system_invocation"] == "standard_worker_direct_cli"  # type: ignore[index]


def test_standard_r_runner_enrichment_lite_mode_writes_real_fixture_ora_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-lite-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "enrichment" / "module_input_lite.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "lite"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    table = (output_dir / "tables" / "lite_ora_result.tsv").read_text(encoding="utf-8")
    assert result["module_id"] == "enrichment"
    assert result["mode"] == "lite"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "lite_result_not_formal_analysis" in result["warnings"]
    assert "lite_enrichment_ora_result_table" in str(result["tables"])
    assert "DNA_DAMAGE" in table
    assert "p.adjust" in table.splitlines()[0]
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["runtime"]["bioconductor_version"] == "not_required_for_lite_base_r"  # type: ignore[index]
    assert provenance["parameter_hash"] != provenance["input_hash"]
    assert (output_dir / "reports" / "README_lite.md").is_file()


def test_standard_r_runner_survival_lite_mode_writes_real_fixture_km_logrank_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-survival-lite-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "survival" / "module_input_lite.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "lite"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    km_table = (output_dir / "tables" / "lite_km_curve.tsv").read_text(encoding="utf-8")
    logrank_table = (output_dir / "tables" / "lite_logrank_result.tsv").read_text(encoding="utf-8")
    assert result["module_id"] == "survival"
    assert result["mode"] == "lite"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "clinical_conclusion_not_generated" in result["warnings"]
    assert "lite_survival_km_curve_table" in str(result["tables"])
    assert "lite_survival_logrank_result_table" in str(result["tables"])
    assert "survival" in km_table.splitlines()[0]
    assert "p_value" in logrank_table.splitlines()[0]
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["runtime"]["bioconductor_version"] == "not_required_for_lite_base_r"  # type: ignore[index]
    assert (output_dir / "reports" / "README_lite.md").is_file()


def test_standard_r_runner_univariate_lite_mode_writes_real_fixture_association_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-univariate-lite-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "univariate" / "module_input_lite.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "lite"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    table = (output_dir / "tables" / "lite_univariate_association.tsv").read_text(encoding="utf-8")
    assert result["module_id"] == "univariate"
    assert result["mode"] == "lite"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "clinical_conclusion_not_generated" in result["warnings"]
    assert "lite_univariate_clinical_association_table" in str(result["tables"])
    assert "p_value" in table.splitlines()[0]
    assert "not_generated" in table
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["runtime"]["bioconductor_version"] == "not_required_for_lite_base_r"  # type: ignore[index]
    assert (output_dir / "reports" / "README_lite.md").is_file()


def test_standard_r_runner_multivariate_lite_mode_writes_real_fixture_association_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-multivariate-lite-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "multivariate" / "module_input_lite.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "lite"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    table = (output_dir / "tables" / "lite_multivariate_association.tsv").read_text(encoding="utf-8")
    assert result["module_id"] == "multivariate"
    assert result["mode"] == "lite"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "clinical_conclusion_not_generated" in result["warnings"]
    assert "lite_multivariate_clinical_association_table" in str(result["tables"])
    assert "model_formula" in table.splitlines()[0]
    assert "p_value" in table.splitlines()[0]
    assert "not_generated" in table
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["runtime"]["bioconductor_version"] == "not_required_for_lite_base_r"  # type: ignore[index]
    assert (output_dir / "reports" / "README_lite.md").is_file()


def test_standard_r_runner_immune_lite_mode_writes_real_fixture_heatmap_package(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-immune-lite-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "immune_infiltration" / "module_input_lite.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "lite"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    result = read_json(output_dir / "result.json")
    provenance = read_json(output_dir / "provenance.json")
    table = (output_dir / "tables" / "lite_immune_scores.tsv").read_text(encoding="utf-8")
    plot = output_dir / "plots" / "lite_immune_heatmap.svg"
    assert result["module_id"] == "immune_infiltration"
    assert result["mode"] == "lite"
    assert result["status"] == "passed"
    assert result["result_semantics"] == "testing_level"
    assert "clinical_conclusion_not_generated" in result["warnings"]
    assert "lite_immune_infiltration_heatmap_svg" in str(result["plots"])
    assert "signature" in table.splitlines()[0]
    assert "score" in table.splitlines()[0]
    assert "not_generated" in table
    assert plot.is_file()
    assert "<svg" in plot.read_text(encoding="utf-8", errors="ignore")
    assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
    assert provenance["runtime"]["bioconductor_version"] == "not_required_for_lite_base_r"  # type: ignore[index]
    assert (output_dir / "reports" / "README_lite.md").is_file()


def test_standard_r_runner_blocks_input_manifest_mode_mismatch(tmp_path: Path) -> None:
    rscript = rscript_path()
    output_dir = tmp_path / "r-runner-mismatch-output"
    input_json = ROOT / "analysis" / "fixtures" / "inputs" / "enrichment" / "module_input.json"

    completed = subprocess.run(
        [rscript, str(ROOT / "analysis" / "runners" / "run_module.R"), str(input_json), str(output_dir), "full"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    result = read_json(output_dir / "result.json")
    assert result["status"] == "blocked"
    assert "module_input_mode_arg_mismatch:input=mock,arg=full" in result["blockers"]


def test_analysis_resource_manifest_declares_full_mode_resource_locks_without_downloads() -> None:
    manifest = read_json(ROOT / "analysis" / "resources" / "manifest.json")
    validation = validate_analysis_resource_manifest(manifest)
    resources = {item["resource_id"]: item for item in manifest["resources"]}  # type: ignore[index]

    assert validation["status"] == "passed"
    assert validation["full_mode_ready"] is False
    assert resources["mock_fixture_builtin_v1"]["status"] == "locked"
    required_resource_ids = set(REQUIRED_FULL_RESOURCE_IDS)
    assert required_resource_ids <= set(resources)
    templates = {item["resource_id"]: item for item in validation["resource_lock_evidence_templates"]}
    assert required_resource_ids <= set(templates)
    assert "mock_fixture_builtin_v1" not in templates
    assert templates["reactome_full"]["schema_version"] == "biomedpilot.analysis.resource_lock_evidence.v1"
    assert templates["reactome_full"]["status"] == "locked"
    assert templates["reactome_full"]["runtime_download_allowed"] is False
    assert templates["reactome_full"]["hash"]["algorithm"] == "sha256"
    assert templates["reactome_full"]["cache_content"]["non_empty"] is True
    assert templates["reactome_full"]["cache_content"]["content_source"] == "prelocked_cache_path"
    assert templates["reactome_full"]["registry_entry"]["resource_id"] == "reactome_full"
    assert "runtime_download" in templates["reactome_full"]["forbidden_evidence_sources"]
    for resource_id in required_resource_ids:
        resource = resources[resource_id]
        assert resource["runtime_download_allowed"] is False
        assert resource["version"] == "required_before_full_mode"
        assert resource["hash"] == "required_before_full_mode"
        assert resource["license"] == "required_before_full_mode"
        assert resource["cache_path"].startswith("external_analysis_resources/")
        assert resource["status"].startswith("blocked_until_")


def test_full_mode_resource_blockers_are_module_specific() -> None:
    enrichment_blockers = full_mode_resource_blockers("enrichment")
    spatial_blockers = full_mode_resource_blockers("spatial_transcriptomics")
    docking_blockers = full_mode_resource_blockers("docking")
    md_blockers = full_mode_resource_blockers("molecular_dynamics")

    assert "analysis_resource_not_locked:reactome_full" in enrichment_blockers
    assert "analysis_resource_not_locked:msigdb_full" in enrichment_blockers
    assert "analysis_resource_not_locked:spatial_reference_full" in spatial_blockers
    assert "analysis_resource_not_locked:autodock_vina_tool" in docking_blockers
    assert "analysis_resource_not_locked:gromacs_tool" in md_blockers
    assert "analysis_resource_not_locked:gromacs_tool" not in enrichment_blockers


def test_full_mode_environment_blockers_require_restored_isolated_locks() -> None:
    enrichment_blockers = full_mode_environment_blockers("enrichment")
    spatial_blockers = full_mode_environment_blockers("spatial_transcriptomics")
    docking_blockers = full_mode_environment_blockers("docking")
    md_blockers = full_mode_environment_blockers("molecular_dynamics")

    assert "analysis_environment_renv_lock_not_restored:r-bio-full:scaffold_only_not_restored" in enrichment_blockers
    assert "analysis_environment_renv_lock_not_restored:r-spatial-full:scaffold_only_not_restored" in spatial_blockers
    assert "analysis_environment_renv_lock_not_restored:r-chem-full:scaffold_only_not_restored" in docking_blockers
    assert "analysis_environment_renv_lock_not_restored:r-chem-gpu:scaffold_only_not_restored" in md_blockers
    assert not any("analysis_resource_not_locked" in blocker for blocker in enrichment_blockers)


def test_locked_resource_with_placeholder_fields_blocks_full_mode() -> None:
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resources = {item["resource_id"]: item for item in manifest["resources"]}  # type: ignore[index]
    reactome = resources["reactome_full"]
    reactome["status"] = "locked"
    reactome["version"] = "Reactome-2026-04"
    reactome["source"] = "Reactome release archive"
    reactome["hash"] = "required_before_full_mode"
    reactome["license"] = "Reactome Content Service License"
    reactome["cache_path"] = "external_analysis_resources/reactome/Reactome-2026-04"

    validation = validate_analysis_resource_manifest(manifest)
    blockers = validation["blockers"]

    assert validation["status"] == "blocked"
    assert (
        "analysis_resource_locked_with_placeholder_fields:reactome_full:hash"
        in blockers
    )
    assert validation["full_mode_ready"] is False
    assert "analysis_resource_locked_with_placeholder_fields:reactome_full:hash" in full_mode_resource_blockers(
        "enrichment", manifest
    )


def test_blocked_resource_with_partial_final_lock_warns_but_still_blocks_module_full_mode() -> None:
    manifest = deepcopy(read_json(ROOT / "analysis" / "resources" / "manifest.json"))
    resources = {item["resource_id"]: item for item in manifest["resources"]}  # type: ignore[index]
    reactome = resources["reactome_full"]
    reactome["version"] = "Reactome-2026-04"
    reactome["hash"] = "sha256:0123456789abcdef"

    validation = validate_analysis_resource_manifest(manifest)

    assert validation["status"] == "passed"
    assert "blocked_resource_has_partial_final_lock:reactome_full" in validation["warnings"]
    blockers = full_mode_resource_blockers("enrichment", manifest)
    assert "analysis_resource_not_locked:reactome_full" in blockers


def test_app_dev_dockerfile_excludes_heavy_analysis_dependency_names() -> None:
    app_dev = (ROOT / "docker" / "Dockerfile.app-dev").read_text(encoding="utf-8")
    heavy_dependency_names = (
        "ReactomePA",
        "reactome.db",
        "Seurat",
        "CellChat",
        "GSVA",
        "AutoDock",
        "GROMACS",
        "survminer",
        "clusterProfiler",
    )

    offenders = [name for name in heavy_dependency_names if name in app_dev]
    assert offenders == []


def test_default_app_dependency_manifests_exclude_heavy_r_and_external_tool_dependencies() -> None:
    heavy_dependency_names = (
        "ReactomePA",
        "reactome.db",
        "Seurat",
        "CellChat",
        "GSVA",
        "AutoDock",
        "AutoDock Vina",
        "GROMACS",
        "survminer",
        "clusterProfiler",
        "DESeq2",
        "edgeR",
        "limma",
        "fgsea",
        "msigdbr",
    )
    default_dependency_files = (
        ROOT / "requirements.txt",
        ROOT / "pyproject.toml",
        ROOT / "docker" / "Dockerfile.app-dev",
        ROOT / "renv" / "renv.app.lock",
    )
    offenders: list[str] = []
    for path in default_dependency_files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name in heavy_dependency_names:
            if name in text:
                offenders.append(f"{path.relative_to(ROOT)}:{name}")

    assert offenders == []


def test_bioinformatics_package_requirements_config_is_detect_first_not_install_manifest() -> None:
    config = ROOT / "config" / "bioinformatics" / "package_requirements.yaml"
    text = config.read_text(encoding="utf-8", errors="ignore")
    forbidden_install_markers = (
        "install.packages",
        "BiocManager::install",
        "pak::pkg_install",
        "remotes::install_github",
        "runtime_install_allowed: true",
        "default_app_dependency: true",
        "download_allowed: true",
    )
    required_policy_markers = (
        "dependency_policy: detect-first; no automatic installation",
        "runtime_install_allowed: false",
        "default_app_dependency: false",
        "purpose: capability and dependency detection inventory only; not an install manifest.",
    )

    offenders = [marker for marker in forbidden_install_markers if marker in text]
    missing_policy = [marker for marker in required_policy_markers if marker not in text]

    assert offenders == []
    assert missing_policy == []


def test_bioinformatics_analysis_default_configs_are_gated_capabilities_not_install_manifests() -> None:
    config_paths = (
        ROOT / "config" / "bioinformatics" / "analysis_defaults.yaml",
        ROOT / "config" / "bioinformatics" / "enrichment_defaults.yaml",
        ROOT / "config" / "bioinformatics" / "survival_defaults.yaml",
    )
    forbidden_markers = (
        "install.packages",
        "BiocManager::install",
        "pak::pkg_install",
        "remotes::install_github",
        "runtime_install_allowed: true",
        "default_app_dependency: true",
        "download_allowed: true",
    )
    required_policy_markers = (
        "dependency_policy:",
        "execution_policy: detect_first_external_worker_only",
        "runtime_install_allowed: false",
        "default_app_dependency: false",
        "download_allowed: false",
        "not an install manifest",
    )

    for path in config_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        offenders = [marker for marker in forbidden_markers if marker in text]
        missing_policy = [marker for marker in required_policy_markers if marker not in text]
        assert offenders == [], path
        assert missing_policy == [], path
