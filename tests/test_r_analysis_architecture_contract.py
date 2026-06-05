from __future__ import annotations

import json
import shutil
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from app.analysis_runtime.architecture_status import (
    build_analysis_architecture_status,
    build_analysis_remediation_queue,
    build_standard_worker_migration_matrix,
    validate_standard_worker_migration_evidence,
)
from app.analysis_runtime.standard_package import validate_standard_result_package
from app.analysis_runtime.resources import (
    full_mode_environment_blockers,
    full_mode_resource_blockers,
    validate_analysis_environment_lock_evidence,
    validate_analysis_resource_lock_evidence,
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
RESULT_PAYLOAD_SCHEMA = "analysis/schemas/output/result.schema.json"
PROVENANCE_PAYLOAD_SCHEMA = "analysis/schemas/output/provenance.schema.json"


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def rscript_path() -> str:
    path = shutil.which("Rscript")
    if path is None:
        pytest.skip("Rscript is not available in this environment")
    return path


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
        if module_id in {"deg", "enrichment", "survival", "univariate", "multivariate", "immune_infiltration", "spatial_transcriptomics", "docking", "molecular_dynamics"}:
            assert modes["lite"]["supported"] is True
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
    assert "mock_fixture_builtin_v1" in manifest_validation["locked_resource_ids"]


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


def test_analysis_environment_registry_validator_separates_structure_from_full_readiness() -> None:
    validation = validate_analysis_environment_registry()

    assert validation["schema_version"] == "biomedpilot.analysis_environment_registry_validation.v1"
    assert validation["status"] == "passed"
    assert validation["full_mode_ready"] is False
    assert set(validation["blocked_environment_ids"]) == {
        "r-bio-full",
        "r-spatial-full",
        "r-chem-full",
        "r-chem-gpu",
    }
    assert "analysis_environment_renv_lock_not_restored:r-bio-full:scaffold_only_not_restored" in validation["readiness_blockers"]
    assert validation["blockers"] == []


def test_restored_full_environment_lock_requires_schema_valid_evidence(tmp_path: Path) -> None:
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
    validation = validate_analysis_environment_registry(environment_registry)

    assert validation["status"] == "blocked"
    assert "analysis_environment_lock_evidence_missing:r-bio-full" in validation["blockers"]
    assert "r-bio-full" not in validation["blocked_environment_ids"]


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
            "package_lock_hash": {"algorithm": "", "value": "required_before_full_mode"},
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
    assert "analysis_environment_lock_evidence_package_lock_hash_algorithm_missing" in validation["blockers"]
    assert "analysis_environment_lock_evidence_package_lock_hash_value_missing" in validation["blockers"]
    assert "analysis_environment_lock_evidence_placeholder_field:r_version" in validation["blockers"]
    assert "analysis_environment_lock_evidence_placeholder_field:bioconductor_version" in validation["blockers"]
    assert "analysis_environment_lock_evidence_dockerfile_not_found:missing/Dockerfile" in validation["blockers"]
    assert "analysis_environment_lock_evidence_renv_lock_not_found:missing/renv.lock" in validation["blockers"]
    assert "analysis_environment_lock_evidence_file_not_found:missing/evidence.json" in validation["blockers"]
    assert "analysis_environment_lock_evidence_allowed_modules_mismatch" in validation["blockers"]
    assert "analysis_environment_lock_evidence_registry_field_mismatch:dockerfile" in validation["blockers"]
    assert "analysis_environment_lock_evidence_registry_field_mismatch:renv_lock" in validation["blockers"]


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

    assert status["schema_version"] == "biomedpilot.analysis.architecture_status.v1"
    assert status["requirement_count"] == 20
    assert status["status"] == "partial_with_p1_gaps"
    assert status["p0_issues"] == []
    assert "full_analysis_environment_locks_not_restored" in status["p1_issues"]
    assert "full_analysis_resource_locks_not_complete" in status["p1_issues"]
    assert rows["RARCH-01"]["status"] == "pass"
    assert rows["RARCH-10"]["status"] == "pass"
    assert rows["RARCH-11"]["status"] == "pass"
    assert rows["RARCH-12"]["status"] == "warn"
    assert rows["RARCH-20"]["status"] == "pass"
    assert status["environment_validation"]["full_mode_ready"] is False
    assert status["resource_validation"]["full_mode_ready"] is False


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
    assert set(items) == {
        "restore_full_analysis_environment_locks",
        "lock_full_analysis_resources",
        "migrate_formal_algorithms_to_isolated_standard_worker",
    }
    assert items["restore_full_analysis_environment_locks"]["source_issue"] == "full_analysis_environment_locks_not_restored"
    assert "renv/renv.bio-full.lock" in items["restore_full_analysis_environment_locks"]["recommended_files"]
    assert "analysis/schemas/output/environment_lock_evidence.schema.json" in items["restore_full_analysis_environment_locks"]["recommended_files"]
    assert "each restored full environment lock has schema-valid environment_lock_evidence" in items["restore_full_analysis_environment_locks"]["required_evidence"]
    assert "analysis/resources/manifest.json" in items["lock_full_analysis_resources"]["recommended_files"]
    assert "analysis/schemas/output/resource_lock_evidence.schema.json" in items["lock_full_analysis_resources"]["recommended_files"]
    assert "each locked full resource has schema-valid resource_lock_evidence" in items["lock_full_analysis_resources"]["required_evidence"]
    assert "analysis/runners/run_module.R" in items["migrate_formal_algorithms_to_isolated_standard_worker"]["recommended_files"]
    assert all(item["status"] == "blocked" for item in items.values())


def test_standard_worker_migration_matrix_is_module_level_and_read_only() -> None:
    matrix = build_standard_worker_migration_matrix()
    rows = {row["module_id"]: row for row in matrix["rows"]}

    assert matrix["schema_version"] == "biomedpilot.analysis.standard_worker_migration_matrix.v1"
    assert matrix["status"] == "partial"
    assert matrix["boundary"] == "matrix_is_read_only_no_worker_execution"
    assert matrix["module_count"] >= 10
    assert matrix["formal_pending_count"] == matrix["module_count"]
    assert matrix["full_blocked_count"] == matrix["module_count"]
    assert {"deg", "survival", "univariate", "multivariate", "enrichment", "immune_infiltration", "spatial_transcriptomics", "docking", "molecular_dynamics"} <= set(rows)
    assert rows["deg"]["mock_status"] == "passed"
    assert rows["deg"]["lite_status"] == "standard_worker_lite_ready"
    assert rows["deg"]["full_status"] == "blocked"
    assert rows["deg"]["formal_worker_status"] == "pending_standard_worker_migration"
    assert rows["enrichment"]["standard_entrypoint"] == "analysis/runners/run_module.R"
    assert rows["docking"]["full_environment"] == "r-chem-full"
    assert rows["molecular_dynamics"]["full_environment"] == "r-chem-gpu"


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
    resource_lock_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "resource_lock_evidence.schema.json")
    environment_lock_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "environment_lock_evidence.schema.json")
    result = read_json(ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / "result.json")
    provenance = read_json(ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / "provenance.json")

    assert "module_id" in input_schema["required"]
    assert "result_json" in output_schema["required"]
    assert "provenance_json" in output_schema["required"]
    assert result_schema["$id"] == "biomedpilot.analysis.result.v1"
    assert provenance_schema["$id"] == "biomedpilot.analysis.provenance.v1"
    assert {"result_semantics", "tables", "plots", "reports", "blockers", "warnings"} <= set(result_schema["required"])
    assert {"input_hash", "parameter_hash", "random_seed", "engine", "runtime", "command"} <= set(provenance_schema["required"])
    assert {"name", "version"} <= set(provenance_schema["properties"]["engine"]["required"])  # type: ignore[index]
    runtime_required = set(provenance_schema["properties"]["runtime"]["required"])  # type: ignore[index]
    assert {"r_version", "bioconductor_version", "package_versions", "external_tool_versions"} <= runtime_required
    assert invocation_schema["$id"] == "biomedpilot.analysis.worker_invocation.v1"
    assert resource_lock_schema["$id"] == "biomedpilot.analysis.resource_lock_evidence.v1"
    assert "runtime_download_allowed" in resource_lock_schema["required"]
    assert environment_lock_schema["$id"] == "biomedpilot.analysis.environment_lock_evidence.v1"
    assert "package_lock_hash" in environment_lock_schema["required"]
    assert "runtime_package_install" in environment_lock_schema["required"]
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


def test_default_source_tree_does_not_install_r_packages_in_request_flow() -> None:
    forbidden = (
        "install.packages",
        "BiocManager::install",
        "pak::pkg_install",
        "remotes::install_github",
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
    required_resource_ids = {
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
    }
    assert required_resource_ids <= set(resources)
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
