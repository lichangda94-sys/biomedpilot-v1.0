from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.analysis_runtime import (
    build_standard_analysis_package_catalog,
    build_standard_analysis_package_detail,
    full_mode_resource_blockers,
    run_analysis_module_task,
    run_external_r_command,
    validate_standard_result_package,
)
from app.analysis_runtime.registry import load_analysis_module_registry
from app.bioinformatics.results.registry import load_registry, save_registry
from app.shared.task_center.service import TaskCenter, TaskStatus


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def module_input(tmp_path: Path, *, mode: str = "mock", module_id: str = "enrichment") -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "biomedpilot.analysis.module_input.v1",
        "module_id": module_id,
        "mode": mode,
        "task_id": f"{module_id}-{mode}-task",
        "project_id": tmp_path.name,
        "inputs": {
            "input_package_id": "input-package-001",
            "source_dataset_id": "dataset-001",
            "fixture_matrix": "analysis/fixtures/inputs/mock_analysis_input.json",
        },
        "parameters": {"comparison": "case_vs_control"},
        "runtime": {"random_seed": 7, "requested_environment": "app-dev"},
    }
    if module_id == "enrichment" and mode == "lite":
        payload["inputs"] = {
            "input_package_id": "fixture-enrichment-lite-input",
            "source_dataset_id": "fixture-enrichment-lite-dataset",
            "gene_list_path": "analysis/fixtures/inputs/enrichment/lite_genes.txt",
            "term2gene_path": "analysis/fixtures/inputs/enrichment/lite_term2gene.tsv",
            "term2name_path": "analysis/fixtures/inputs/enrichment/lite_term2name.tsv",
        }
        payload["parameters"] = {"analysis_family": "enrichment", "method": "base_r_hypergeometric_ora"}
        payload["runtime"] = {"random_seed": 7, "requested_environment": "r-bio-core-lite"}
    if module_id == "deg" and mode == "lite":
        payload["inputs"] = {
            "input_package_id": "fixture-deg-lite-input",
            "source_dataset_id": "fixture-deg-lite-dataset",
            "expression_matrix_path": "analysis/fixtures/inputs/deg/lite_counts.tsv",
            "sample_metadata_path": "analysis/fixtures/inputs/deg/lite_metadata.tsv",
        }
        payload["parameters"] = {
            "analysis_family": "differential_expression",
            "method": "base_r_welch_t_test_fixture",
            "comparison": "case_vs_control",
            "case_group": "case",
            "control_group": "control",
            "value_type": "raw_count",
            "clinical_conclusion_policy": "not_generated",
        }
        payload["runtime"] = {"random_seed": 7, "requested_environment": "r-bio-core-lite"}
    if module_id == "survival" and mode == "lite":
        payload["inputs"] = {
            "input_package_id": "fixture-survival-lite-input",
            "source_dataset_id": "fixture-survival-lite-dataset",
            "survival_table_path": "analysis/fixtures/inputs/survival/lite_survival.tsv",
        }
        payload["parameters"] = {
            "analysis_family": "survival",
            "method": "base_r_km_logrank",
            "clinical_conclusion_policy": "not_generated",
        }
        payload["runtime"] = {"random_seed": 7, "requested_environment": "r-bio-core-lite"}
    if module_id == "univariate" and mode == "lite":
        payload["inputs"] = {
            "input_package_id": "fixture-univariate-lite-input",
            "source_dataset_id": "fixture-univariate-lite-dataset",
            "clinical_table_path": "analysis/fixtures/inputs/univariate/lite_clinical.tsv",
        }
        payload["parameters"] = {
            "analysis_family": "univariate_clinical_association",
            "method": "base_r_univariate_fixture",
            "clinical_conclusion_policy": "not_generated",
        }
        payload["runtime"] = {"random_seed": 7, "requested_environment": "r-bio-core-lite"}
    if module_id == "multivariate" and mode == "lite":
        payload["inputs"] = {
            "input_package_id": "fixture-multivariate-lite-input",
            "source_dataset_id": "fixture-multivariate-lite-dataset",
            "clinical_table_path": "analysis/fixtures/inputs/multivariate/lite_clinical.tsv",
        }
        payload["parameters"] = {
            "analysis_family": "multivariate_clinical_association",
            "method": "base_r_lm_fixture",
            "model_formula": "biomarker ~ group + age + batch",
            "clinical_conclusion_policy": "not_generated",
        }
        payload["runtime"] = {"random_seed": 7, "requested_environment": "r-bio-core-lite"}
    if module_id == "immune_infiltration" and mode == "lite":
        payload["inputs"] = {
            "input_package_id": "fixture-immune-lite-input",
            "source_dataset_id": "fixture-immune-lite-dataset",
            "expression_matrix_path": "analysis/fixtures/inputs/immune_infiltration/lite_expression.tsv",
            "signature_table_path": "analysis/fixtures/inputs/immune_infiltration/lite_signatures.tsv",
        }
        payload["parameters"] = {
            "analysis_family": "immune_infiltration",
            "method": "base_r_signature_mean_fixture",
            "clinical_conclusion_policy": "not_generated",
        }
        payload["runtime"] = {"random_seed": 7, "requested_environment": "r-bio-core-lite"}
    if module_id == "spatial_transcriptomics" and mode == "lite":
        payload["inputs"] = {
            "input_package_id": "fixture-spatial-lite-input",
            "source_dataset_id": "fixture-spatial-lite-dataset",
            "expression_matrix_path": "analysis/fixtures/inputs/spatial_transcriptomics/lite_expression.tsv",
            "coordinate_table_path": "analysis/fixtures/inputs/spatial_transcriptomics/lite_coordinates.tsv",
        }
        payload["parameters"] = {
            "analysis_family": "spatial_transcriptomics",
            "method": "base_r_spot_qc_fixture",
            "execute_heavy_spatial_methods": False,
            "spatial_interpretation_policy": "not_generated_in_lite_mode",
        }
        payload["runtime"] = {"random_seed": 7, "requested_environment": "r-spatial-lite-contract"}
    if module_id == "docking" and mode == "lite":
        payload["inputs"] = {
            "input_package_id": "fixture-docking-lite-input",
            "source_dataset_id": "fixture-docking-lite-dataset",
            "receptor_path": "analysis/fixtures/inputs/docking/lite_receptor.pdbqt",
            "ligand_path": "analysis/fixtures/inputs/docking/lite_ligand.pdbqt",
            "config_path": "analysis/fixtures/inputs/docking/lite_vina_config.txt",
        }
        payload["parameters"] = {
            "analysis_family": "molecular_docking",
            "adapter_contract": "autodock_vina_command_manifest_only",
            "external_tool": "AutoDock Vina",
            "execute_external_tool": False,
            "scientific_result_policy": "not_generated_in_lite_mode",
        }
        payload["runtime"] = {"random_seed": 7, "requested_environment": "r-chem-lite-contract"}
    if module_id == "molecular_dynamics" and mode == "lite":
        payload["inputs"] = {
            "input_package_id": "fixture-md-lite-input",
            "source_dataset_id": "fixture-md-lite-dataset",
            "topology_path": "analysis/fixtures/inputs/molecular_dynamics/lite_topology.top",
            "coordinate_path": "analysis/fixtures/inputs/molecular_dynamics/lite_coordinates.gro",
            "mdp_path": "analysis/fixtures/inputs/molecular_dynamics/lite_mdp.mdp",
        }
        payload["parameters"] = {
            "analysis_family": "molecular_dynamics",
            "adapter_contract": "gromacs_command_manifest_only",
            "external_tool": "GROMACS",
            "execute_external_tool": False,
            "scientific_result_policy": "not_generated_in_lite_mode",
        }
        payload["runtime"] = {"random_seed": 7, "requested_environment": "r-chem-gpu-lite-contract"}
    return payload


def test_mock_analysis_task_bridge_writes_standard_package_task_and_result_index(tmp_path: Path) -> None:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    result = run_analysis_module_task(tmp_path, module_input(tmp_path), task_center=task_center)

    package_dir = Path(result["result_package_dir"])
    validation = validate_standard_result_package(
        package_dir,
        expected_module_id="enrichment",
        expected_task_id="enrichment-mock-task",
        expected_mode="mock",
    )
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    invocation = read_json(package_dir / "logs" / "worker_invocation.json")
    tasks = task_center.list_tasks()
    registry = load_registry(tmp_path)

    assert result["status"] == "passed"
    assert validation["status"] == "passed"
    assert result_json["status"] == "passed"
    assert result_json["summary"]["clinical_conclusion_status"] == "not_generated"  # type: ignore[index]
    assert "mock enrichment package" in result_json["summary"]["message"].lower()  # type: ignore[index]
    assert provenance["runtime"]["r_version"] == "not_required_for_mock"  # type: ignore[index]
    assert provenance["input_hash"] != "fixture"
    assert provenance["command"] == "analysis_task_bridge_mock_fixture_copy"
    assert tasks[0].status == TaskStatus.COMPLETED
    assert registry["results"][0]["result_id"] == "analysis-package-enrichment-mock-task"
    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["output_artifacts"][0]["artifact_type"] == "standard_result_package"
    assert registry["results"][0]["log_artifacts"][0]["artifact_type"] == "analysis_worker_log"
    assert registry["results"][0]["log_artifacts"][1]["artifact_type"] == "analysis_worker_invocation_manifest"
    assert invocation["worker_backend"] == "python_fixture"
    assert invocation["invocation_status"] == "fixture_copy_completed"
    assert invocation["input_manifest"] == "not_materialized"
    assert invocation["runtime_install_policy"] == "forbidden"
    assert invocation["resource_download_policy"] == "forbidden"
    assert invocation["worker_boundary"]["boundary_type"] == "analysis_task_bridge_fixture"  # type: ignore[index]
    assert invocation["worker_boundary"]["migration_status"] == "mock_fixture_contract"  # type: ignore[index]


def test_standard_analysis_package_catalog_reads_result_index_packages(tmp_path: Path) -> None:
    run_analysis_module_task(tmp_path, module_input(tmp_path))

    catalog = build_standard_analysis_package_catalog(tmp_path)
    row = catalog["rows"][0]

    assert catalog["status"] == "passed"
    assert catalog["source_policy"] == "result_index_standard_result_package_artifacts_only"
    assert catalog["package_count"] == 1
    assert row["result_id"] == "analysis-package-enrichment-mock-task"
    assert row["module_id"] == "enrichment"
    assert row["mode"] == "mock"
    assert row["status"] == "passed"
    assert row["validation_status"] == "passed"
    assert row["engine_name"] == "biomedpilot_analysis_task_bridge"
    assert row["package_path_relative"] == "analysis_results/enrichment-mock-task"
    assert row["worker_backend"] == "python_fixture"
    assert row["worker_invocation_status"] == "fixture_copy_completed"
    assert row["worker_boundary_type"] == "analysis_task_bridge_fixture"
    assert row["worker_migration_status"] == "mock_fixture_contract"
    assert row["worker_invocation"]["runtime_install_policy"] == "forbidden"
    assert row["worker_invocation"]["resource_download_policy"] == "forbidden"
    assert row["artifact_counts"] == {"tables": 1, "plots": 0, "reports": 1, "logs": 2}
    manifest = row["artifact_manifest"]
    assert manifest["source_policy"] == "standard_result_package_declared_artifacts_and_logs_only"
    assert manifest["tables"][0]["package_relative_path"] == "tables/mock_summary.tsv"
    assert manifest["tables"][0]["exists"] is True
    assert manifest["tables"][0]["within_standard_package"] is True
    assert manifest["reports"][0]["package_relative_path"] == "reports/README_mock.md"
    assert {item["artifact_type"] for item in manifest["logs"]} == {"analysis_worker_log", "analysis_worker_invocation_manifest"}
    assert all(item["source_policy"] == "standard_result_package_only" for group in ("tables", "reports", "logs") for item in manifest[group])
    assert "mock_result_not_scientific_output" in row["warnings"]


def test_standard_analysis_package_catalog_requires_result_index_worker_invocation_log_artifact(tmp_path: Path) -> None:
    run_analysis_module_task(tmp_path, module_input(tmp_path))
    registry = load_registry(tmp_path)
    entry = registry["results"][0]
    entry["log_artifacts"] = [item for item in entry["log_artifacts"] if item["artifact_type"] != "analysis_worker_invocation_manifest"]
    save_registry(tmp_path, [entry])

    catalog = build_standard_analysis_package_catalog(tmp_path)

    assert catalog["status"] == "blocked"
    assert any("result_index_worker_invocation_manifest_missing" in item for item in catalog["blockers"])


def test_standard_analysis_package_catalog_maps_bio_task_type_to_expected_module(tmp_path: Path) -> None:
    run_analysis_module_task(tmp_path, module_input(tmp_path))
    registry = load_registry(tmp_path)
    entry = registry["results"][0]
    entry["task_type"] = "deg"
    save_registry(tmp_path, [entry])

    catalog = build_standard_analysis_package_catalog(tmp_path)

    assert catalog["status"] == "blocked"
    assert any("result_module_id_mismatch" in item for item in catalog["blockers"])
    assert any("provenance_module_id_mismatch" in item for item in catalog["blockers"])


def test_standard_analysis_package_detail_reads_only_standard_package_artifacts(tmp_path: Path) -> None:
    result = run_analysis_module_task(tmp_path, module_input(tmp_path))
    package_dir = Path(result["result_package_dir"])

    detail = build_standard_analysis_package_detail(package_dir, project_root=tmp_path)

    assert detail["schema_version"] == "biomedpilot.analysis.standard_package_detail.v1"
    assert detail["validation_status"] == "passed"
    assert detail["result"]["module_id"] == "enrichment"
    assert detail["result"]["result_semantics"] == "testing_level"
    assert detail["provenance"]["engine"]["name"] == "biomedpilot_analysis_task_bridge"  # type: ignore[index]
    assert detail["worker_invocation"]["worker_backend"] == "python_fixture"
    assert detail["artifact_manifest"]["tables"][0]["path_relative"] == "analysis_results/enrichment-mock-task/tables/mock_summary.tsv"
    assert detail["artifact_manifest"]["tables"][0]["size_bytes"] > 0
    assert detail["artifact_manifest"]["plots"] == []
    assert len(detail["artifact_manifest"]["logs"]) == 2


def test_standard_package_validation_blocks_missing_or_outside_declared_artifacts(tmp_path: Path) -> None:
    result = run_analysis_module_task(tmp_path, module_input(tmp_path))
    package_dir = Path(result["result_package_dir"])
    result_path = package_dir / "result.json"
    result_json = read_json(result_path)
    result_json["tables"] = [
        {"artifact_type": "valid_table", "path": "tables/mock_summary.tsv"},
        {"artifact_type": "missing_table", "path": "tables/missing.tsv"},
        {"artifact_type": "outside_table", "path": "../outside.tsv"},
    ]
    result_json["plots"] = [{"artifact_type": "wrong_group_plot", "path": "tables/mock_summary.tsv"}]
    result_json["reports"] = ["not-an-artifact"]
    result_path.write_text(json.dumps(result_json, indent=2), encoding="utf-8")

    validation = validate_standard_result_package(
        package_dir,
        expected_module_id="enrichment",
        expected_task_id="enrichment-mock-task",
        expected_mode="mock",
    )

    assert validation["status"] == "blocked"
    assert "declared_artifact_tables_1_file_missing" in validation["blockers"]
    assert "declared_artifact_tables_2_path_outside_standard_group" in validation["blockers"]
    assert "declared_artifact_plots_0_path_outside_standard_group" in validation["blockers"]
    assert "declared_artifact_reports_0_invalid" in validation["blockers"]


def test_task_bridge_standard_package_validation_requires_worker_invocation_manifest(tmp_path: Path) -> None:
    result = run_analysis_module_task(tmp_path, module_input(tmp_path))
    package_dir = Path(result["result_package_dir"])
    (package_dir / "logs" / "worker_invocation.json").unlink()

    validation = validate_standard_result_package(
        package_dir,
        expected_module_id="enrichment",
        expected_task_id="enrichment-mock-task",
        expected_mode="mock",
    )

    assert validation["status"] == "blocked"
    assert "worker_invocation_manifest_missing" in validation["blockers"]


def test_worker_invocation_manifest_schema_and_policy_are_validated(tmp_path: Path) -> None:
    result = run_analysis_module_task(tmp_path, module_input(tmp_path))
    package_dir = Path(result["result_package_dir"])
    invocation_path = package_dir / "logs" / "worker_invocation.json"
    invocation = read_json(invocation_path)
    invocation["schema_version"] = "wrong"
    invocation["runtime_install_policy"] = "install_allowed"
    invocation["worker_boundary"]["task_system_invocation"] = "direct_ui_call"  # type: ignore[index]
    invocation_path.write_text(json.dumps(invocation, indent=2), encoding="utf-8")

    validation = validate_standard_result_package(
        package_dir,
        expected_module_id="enrichment",
        expected_task_id="enrichment-mock-task",
        expected_mode="mock",
    )

    assert validation["status"] == "blocked"
    assert "worker_invocation_schema_version_mismatch" in validation["blockers"]
    assert "worker_invocation_runtime_install_policy_invalid" in validation["blockers"]
    assert "worker_invocation_task_system_invocation_invalid" in validation["blockers"]


def test_formal_standard_package_validation_blocks_missing_worker_boundary(tmp_path: Path) -> None:
    package_dir = tmp_path / "formal-package"
    for dirname in ("tables", "plots", "reports", "logs"):
        (package_dir / dirname).mkdir(parents=True, exist_ok=True)
    (package_dir / "result.json").write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.analysis.result.v1",
                "module_id": "enrichment",
                "mode": "full",
                "task_id": "formal-task",
                "status": "passed",
                "result_semantics": "formal_computed_result",
                "summary": {},
                "tables": [],
                "plots": [],
                "reports": [],
                "blockers": [],
                "warnings": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (package_dir / "provenance.json").write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.analysis.provenance.v1",
                "module_id": "enrichment",
                "mode": "full",
                "task_id": "formal-task",
                "input_hash": "abc",
                "parameter_hash": "def",
                "random_seed": None,
                "engine": {"name": "r_clusterProfiler_enricher", "version": "4.14.6"},
                "runtime": {
                    "r_version": "R 4.4.2",
                    "bioconductor_version": "3.20",
                    "package_versions": {"clusterProfiler": "4.14.6"},
                    "external_tool_versions": {},
                },
                "command": "Rscript --vanilla -e ...",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    validation = validate_standard_result_package(
        package_dir,
        expected_module_id="enrichment",
        expected_task_id="formal-task",
        expected_mode="full",
    )

    assert validation["status"] == "blocked"
    assert "formal_provenance_worker_boundary_missing" in validation["blockers"]
    assert "analysis_environment_snapshot_missing_or_invalid" in validation["blockers"]


def test_full_standard_package_validation_requires_analysis_environment_snapshot(tmp_path: Path) -> None:
    package_dir = tmp_path / "blocked-full-package"
    for dirname in ("tables", "plots", "reports", "logs"):
        (package_dir / dirname).mkdir(parents=True, exist_ok=True)
    (package_dir / "result.json").write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.analysis.result.v1",
                "module_id": "enrichment",
                "mode": "full",
                "task_id": "blocked-full-task",
                "status": "blocked",
                "result_semantics": "testing_level",
                "summary": {},
                "tables": [],
                "plots": [],
                "reports": [],
                "blockers": ["full_resource_manifest_and_container_not_available"],
                "warnings": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (package_dir / "provenance.json").write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.analysis.provenance.v1",
                "module_id": "enrichment",
                "mode": "full",
                "task_id": "blocked-full-task",
                "input_hash": "abc",
                "parameter_hash": "def",
                "random_seed": None,
                "engine": {"name": "biomedpilot_analysis_task_bridge", "version": "v1"},
                "runtime": {
                    "r_version": "not_executed",
                    "bioconductor_version": "not_executed",
                    "package_versions": {},
                    "external_tool_versions": {},
                },
                "command": "analysis_task_bridge_mode_gate",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (package_dir / "logs" / "worker_invocation.json").write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.analysis.worker_invocation.v1",
                "created_at": "2026-06-04T00:00:00Z",
                "module_id": "enrichment",
                "mode": "full",
                "task_id": "blocked-full-task",
                "worker_backend": "rscript",
                "invocation_status": "not_invoked_mode_gate",
                "standard_worker_entrypoint": "analysis/runners/run_module.R",
                "input_manifest": "not_materialized",
                "output_contract": "standard_result_package",
                "runtime_install_policy": "forbidden",
                "resource_download_policy": "forbidden",
                "returncode": None,
                "command": [],
                "stdout": "",
                "stderr": "",
                "blockers": ["full_resource_manifest_and_container_not_available"],
                "worker_boundary": {
                    "boundary_type": "analysis_task_bridge_gate",
                    "task_system_invocation": "task_center_registered",
                    "migration_status": "blocked_before_worker_execution",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    validation = validate_standard_result_package(
        package_dir,
        expected_module_id="enrichment",
        expected_task_id="blocked-full-task",
        expected_mode="full",
    )

    assert validation["status"] == "blocked"
    assert "analysis_environment_snapshot_missing_or_invalid" in validation["blockers"]


def test_external_r_command_runs_through_shared_runtime_boundary() -> None:
    def fake_runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    result = run_external_r_command(
        ["/fake/Rscript", "--vanilla", "-e", "cat('ok')"],
        owner="tests.fake_r_owner",
        timeout_seconds=5,
        failure_blocker="fake_r_failed",
        runner=fake_runner,
    )

    assert result["schema_version"] == "biomedpilot.analysis.external_r_command_invocation.v1"
    assert result["status"] == "passed"
    assert result["owner"] == "tests.fake_r_owner"
    assert result["stdout"] == "ok"
    assert result["worker_boundary"] == {
        "boundary_type": "analysis_runtime_external_r_command",
        "standard_worker_entrypoint": "not_used",
        "subprocess_owner": "tests.fake_r_owner",
        "migration_status": "shared_subprocess_boundary_not_isolated_standard_worker",
        "task_system_invocation": "not_yet_migrated",
    }


def test_all_registered_modules_run_mock_bridge_with_standard_package(tmp_path: Path) -> None:
    registry = load_analysis_module_registry()

    for module in registry["modules"]:
        module_id = module["module_id"]
        task_center = TaskCenter(tmp_path / module_id / "tasks" / "tasks.json")
        result = run_analysis_module_task(tmp_path / module_id, module_input(tmp_path, module_id=module_id), task_center=task_center)
        package_dir = Path(result["result_package_dir"])
        result_json = read_json(package_dir / "result.json")
        provenance = read_json(package_dir / "provenance.json")

        assert result["status"] == "passed"
        assert result_json["module_id"] == module_id
        assert result_json["task_id"] == f"{module_id}-mock-task"
        assert result_json["result_semantics"] == "testing_level"
        assert "mock_result_not_scientific_output" in result_json["warnings"]
        assert provenance["module_id"] == module_id
        assert provenance["task_id"] == f"{module_id}-mock-task"
        assert provenance["input_hash"] != "fixture"
        assert (package_dir / "logs" / "worker_invocation.json").is_file()
        assert task_center.list_tasks()[0].status == TaskStatus.COMPLETED


def test_mock_analysis_task_bridge_can_invoke_standard_r_worker(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    registry = load_registry(tmp_path)
    assert result["status"] == "passed"
    assert result_json["status"] == "passed"
    assert result_json["result_semantics"] == "testing_level"
    assert provenance["engine"]["name"] == "biomedpilot_standard_r_worker"  # type: ignore[index]
    assert provenance["runtime"]["r_version"] != "not_required_for_mock"  # type: ignore[index]
    assert "analysis/runners/run_module.R" in provenance["command"]
    assert task_center.list_tasks()[0].status == TaskStatus.COMPLETED
    assert registry["results"][0]["engine_name"] == "biomedpilot_standard_r_worker"
    assert registry["results"][0]["dependency_snapshot"]["runtime"]["r_version"] != "not_required_for_mock"  # type: ignore[index]


def test_r_worker_backend_missing_rscript_returns_blocked_standard_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.analysis_runtime.r_worker.shutil.which", lambda _name: None)
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    invocation = read_json(package_dir / "logs" / "worker_invocation.json")
    assert result["status"] == "blocked"
    assert "rscript_not_available" in result["blockers"]
    assert result_json["status"] == "blocked"
    assert provenance["runtime"]["r_version"] == "not_executed"  # type: ignore[index]
    assert invocation["schema_version"] == "biomedpilot.analysis.worker_invocation.v1"
    assert invocation["worker_backend"] == "rscript"
    assert invocation["invocation_status"] == "blocked_before_process"
    assert invocation["runtime_install_policy"] == "forbidden"
    assert invocation["resource_download_policy"] == "forbidden"
    assert "rscript_not_available" in invocation["blockers"]
    assert task_center.list_tasks()[0].status == TaskStatus.FAILED


def test_enrichment_lite_mode_requires_rscript_worker_backend(tmp_path: Path) -> None:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(tmp_path, module_input(tmp_path, mode="lite"), task_center=task_center)

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    assert result["status"] == "blocked"
    assert "analysis_mode_requires_rscript_worker:lite" in result["blockers"]
    assert result_json["status"] == "blocked"
    assert task_center.list_tasks()[0].status == TaskStatus.FAILED


def test_enrichment_lite_mode_runs_through_standard_r_worker_and_catalog(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path, mode="lite"),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    catalog = build_standard_analysis_package_catalog(tmp_path)
    registry = load_registry(tmp_path)
    assert result["status"] == "passed"
    assert result_json["mode"] == "lite"
    assert result_json["status"] == "passed"
    assert result_json["result_semantics"] == "testing_level"
    assert "lite_result_not_formal_analysis" in result_json["warnings"]
    assert (package_dir / "tables" / "lite_ora_result.tsv").is_file()
    assert provenance["engine"]["name"] == "biomedpilot_standard_r_worker"  # type: ignore[index]
    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["engine_name"] == "biomedpilot_standard_r_worker"
    assert catalog["rows"][0]["mode"] == "lite"
    assert catalog["rows"][0]["worker_boundary_type"] == "standard_r_worker"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1


def test_deg_lite_mode_runs_through_standard_r_worker_without_formal_upgrade(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path, mode="lite", module_id="deg"),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    catalog = build_standard_analysis_package_catalog(tmp_path)
    registry = load_registry(tmp_path)
    table_text = (package_dir / "tables" / "lite_deg_result.tsv").read_text(encoding="utf-8")
    assert result["status"] == "passed"
    assert result_json["module_id"] == "deg"
    assert result_json["mode"] == "lite"
    assert result_json["result_semantics"] == "testing_level"
    assert "lite_result_not_formal_analysis" in result_json["warnings"]
    assert "clinical_conclusion_not_generated" in result_json["warnings"]
    assert "adjusted_p_value" in table_text
    assert "significance_label" in table_text
    assert provenance["engine"]["name"] == "biomedpilot_standard_r_worker"  # type: ignore[index]
    assert provenance["parameter_hash"] != provenance["input_hash"]
    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["engine_name"] == "biomedpilot_standard_r_worker"
    assert catalog["rows"][0]["module_id"] == "deg"
    assert catalog["rows"][0]["mode"] == "lite"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1
    assert registry["results"][0]["report_ready_eligible"] is False


def test_survival_lite_mode_runs_through_standard_r_worker_without_clinical_upgrade(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path, mode="lite", module_id="survival"),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    catalog = build_standard_analysis_package_catalog(tmp_path)
    registry = load_registry(tmp_path)
    assert result["status"] == "passed"
    assert result_json["module_id"] == "survival"
    assert result_json["mode"] == "lite"
    assert result_json["result_semantics"] == "testing_level"
    assert result_json["summary"]["clinical_conclusion_status"] == "not_generated"  # type: ignore[index]
    assert "clinical_conclusion_not_generated" in result_json["warnings"]
    assert (package_dir / "tables" / "lite_km_curve.tsv").is_file()
    assert (package_dir / "tables" / "lite_logrank_result.tsv").is_file()
    assert provenance["engine"]["name"] == "biomedpilot_standard_r_worker"  # type: ignore[index]
    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["report_ready_eligible"] is False
    assert catalog["rows"][0]["module_id"] == "survival"
    assert catalog["rows"][0]["mode"] == "lite"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 2


def test_univariate_lite_mode_runs_through_standard_r_worker_without_clinical_upgrade(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path, mode="lite", module_id="univariate"),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    catalog = build_standard_analysis_package_catalog(tmp_path)
    registry = load_registry(tmp_path)
    assert result["status"] == "passed"
    assert result_json["module_id"] == "univariate"
    assert result_json["mode"] == "lite"
    assert result_json["result_semantics"] == "testing_level"
    assert result_json["summary"]["clinical_conclusion_status"] == "not_generated"  # type: ignore[index]
    assert "clinical_conclusion_not_generated" in result_json["warnings"]
    assert (package_dir / "tables" / "lite_univariate_association.tsv").is_file()
    assert provenance["engine"]["name"] == "biomedpilot_standard_r_worker"  # type: ignore[index]
    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["report_ready_eligible"] is False
    assert catalog["rows"][0]["module_id"] == "univariate"
    assert catalog["rows"][0]["mode"] == "lite"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1


def test_multivariate_lite_mode_runs_through_standard_r_worker_without_clinical_upgrade(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path, mode="lite", module_id="multivariate"),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    table = (package_dir / "tables" / "lite_multivariate_association.tsv").read_text(encoding="utf-8")
    catalog = build_standard_analysis_package_catalog(tmp_path)
    registry = load_registry(tmp_path)
    assert result["status"] == "passed"
    assert result_json["module_id"] == "multivariate"
    assert result_json["mode"] == "lite"
    assert result_json["result_semantics"] == "testing_level"
    assert result_json["summary"]["clinical_conclusion_status"] == "not_generated"  # type: ignore[index]
    assert "clinical_conclusion_not_generated" in result_json["warnings"]
    assert "model_formula" in table.splitlines()[0]
    assert "not_generated" in table
    assert provenance["engine"]["name"] == "biomedpilot_standard_r_worker"  # type: ignore[index]
    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["report_ready_eligible"] is False
    assert catalog["rows"][0]["module_id"] == "multivariate"
    assert catalog["rows"][0]["mode"] == "lite"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1


def test_immune_lite_mode_runs_through_standard_r_worker_with_real_heatmap_artifact(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path, mode="lite", module_id="immune_infiltration"),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    table = (package_dir / "tables" / "lite_immune_scores.tsv").read_text(encoding="utf-8")
    plot = package_dir / "plots" / "lite_immune_heatmap.svg"
    catalog = build_standard_analysis_package_catalog(tmp_path)
    registry = load_registry(tmp_path)
    assert result["status"] == "passed"
    assert result_json["module_id"] == "immune_infiltration"
    assert result_json["mode"] == "lite"
    assert result_json["result_semantics"] == "testing_level"
    assert result_json["summary"]["clinical_conclusion_status"] == "not_generated"  # type: ignore[index]
    assert "clinical_conclusion_not_generated" in result_json["warnings"]
    assert "lite_immune_infiltration_heatmap_svg" in str(result_json["plots"])
    assert "signature" in table.splitlines()[0]
    assert "not_generated" in table
    assert plot.is_file()
    assert "<svg" in plot.read_text(encoding="utf-8", errors="ignore")
    assert provenance["engine"]["name"] == "biomedpilot_standard_r_worker"  # type: ignore[index]
    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["report_ready_eligible"] is False
    assert catalog["rows"][0]["module_id"] == "immune_infiltration"
    assert catalog["rows"][0]["mode"] == "lite"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1
    assert catalog["rows"][0]["artifact_counts"]["plots"] == 1


def test_docking_lite_mode_writes_external_tool_command_manifest_without_execution(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path, mode="lite", module_id="docking"),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    table = (package_dir / "tables" / "lite_docking_command_manifest.tsv").read_text(encoding="utf-8")
    readme = (package_dir / "reports" / "README_lite.md").read_text(encoding="utf-8")
    catalog = build_standard_analysis_package_catalog(tmp_path)
    registry = load_registry(tmp_path)
    assert result["status"] == "passed"
    assert result_json["module_id"] == "docking"
    assert result_json["mode"] == "lite"
    assert result_json["result_semantics"] == "testing_level"
    assert "external_tool_not_executed_in_lite_mode" in result_json["warnings"]
    assert "scientific_docking_result_not_generated" in result_json["warnings"]
    assert "AutoDock Vina" in table
    assert "not_executed_lite_contract" in table
    assert "command_preview" in table.splitlines()[0]
    assert "No docking score" in readme
    assert provenance["engine"]["name"] == "biomedpilot_standard_r_worker"  # type: ignore[index]
    assert provenance["runtime"]["external_tool_versions"]["AutoDock Vina"] == "not_executed_lite_contract"  # type: ignore[index]
    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["report_ready_eligible"] is False
    assert catalog["rows"][0]["module_id"] == "docking"
    assert catalog["rows"][0]["mode"] == "lite"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1
    assert catalog["rows"][0]["artifact_counts"]["plots"] == 0


def test_spatial_transcriptomics_lite_mode_writes_base_r_qc_package_without_heavy_spatial_packages(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path, mode="lite", module_id="spatial_transcriptomics"),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    spot_metrics = (package_dir / "tables" / "lite_spatial_spot_metrics.tsv").read_text(encoding="utf-8")
    qc_summary = (package_dir / "tables" / "lite_spatial_qc_summary.tsv").read_text(encoding="utf-8")
    svg = (package_dir / "plots" / "lite_spatial_spot_qc.svg").read_text(encoding="utf-8")
    readme = (package_dir / "reports" / "README_lite.md").read_text(encoding="utf-8")
    catalog = build_standard_analysis_package_catalog(tmp_path)
    registry = load_registry(tmp_path)
    assert result["status"] == "passed"
    assert result_json["module_id"] == "spatial_transcriptomics"
    assert result_json["mode"] == "lite"
    assert result_json["result_semantics"] == "testing_level"
    assert "base_r_fixture_only_no_heavy_spatial_packages" in result_json["warnings"]
    assert "spatial_interpretation_not_generated" in result_json["warnings"]
    assert "spot_A" in spot_metrics
    assert "total_counts" in spot_metrics.splitlines()[0]
    assert "gene_count" in qc_summary
    assert "Lite spatial spot QC" in svg
    assert "No Seurat" in svg
    assert "does not use Seurat, CellChat, spacexr" in readme
    assert provenance["runtime"]["package_versions"] == {}  # type: ignore[index]
    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["report_ready_eligible"] is False
    assert catalog["rows"][0]["module_id"] == "spatial_transcriptomics"
    assert catalog["rows"][0]["mode"] == "lite"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 2
    assert catalog["rows"][0]["artifact_counts"]["plots"] == 1


def test_molecular_dynamics_lite_mode_writes_gromacs_command_manifest_without_execution(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")

    result = run_analysis_module_task(
        tmp_path,
        module_input(tmp_path, mode="lite", module_id="molecular_dynamics"),
        task_center=task_center,
        worker_backend="rscript",
    )

    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    table = (package_dir / "tables" / "lite_md_command_manifest.tsv").read_text(encoding="utf-8")
    readme = (package_dir / "reports" / "README_lite.md").read_text(encoding="utf-8")
    catalog = build_standard_analysis_package_catalog(tmp_path)
    registry = load_registry(tmp_path)
    assert result["status"] == "passed"
    assert result_json["module_id"] == "molecular_dynamics"
    assert result_json["mode"] == "lite"
    assert result_json["result_semantics"] == "testing_level"
    assert "external_tool_not_executed_in_lite_mode" in result_json["warnings"]
    assert "scientific_molecular_dynamics_result_not_generated" in result_json["warnings"]
    assert "GROMACS" in table
    assert "not_executed_lite_contract" in table
    assert "grompp_command_preview" in table.splitlines()[0]
    assert "mdrun_command_preview" in table.splitlines()[0]
    assert "No trajectory" in readme
    assert provenance["engine"]["name"] == "biomedpilot_standard_r_worker"  # type: ignore[index]
    assert provenance["runtime"]["external_tool_versions"]["GROMACS"] == "not_executed_lite_contract"  # type: ignore[index]
    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["report_ready_eligible"] is False
    assert catalog["rows"][0]["module_id"] == "molecular_dynamics"
    assert catalog["rows"][0]["mode"] == "lite"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1
    assert catalog["rows"][0]["artifact_counts"]["plots"] == 0


def test_all_registered_lite_modules_run_through_standard_r_worker_package_contract(tmp_path: Path) -> None:
    if shutil.which("Rscript") is None:
        pytest.skip("Rscript is not available in this environment")
    registry = load_analysis_module_registry()
    lite_module_ids = [
        str(module["module_id"])
        for module in registry["modules"]
        if bool(module.get("modes", {}).get("lite", {}).get("supported"))
    ]

    assert lite_module_ids

    for module_id in lite_module_ids:
        project_root = tmp_path / module_id
        task_center = TaskCenter(project_root / "tasks" / "tasks.json")
        result = run_analysis_module_task(
            project_root,
            module_input(tmp_path, mode="lite", module_id=module_id),
            task_center=task_center,
            worker_backend="rscript",
        )
        package_dir = Path(result["result_package_dir"])
        result_json = read_json(package_dir / "result.json")
        provenance = read_json(package_dir / "provenance.json")
        invocation = read_json(package_dir / "logs" / "worker_invocation.json")
        validation = validate_standard_result_package(
            package_dir,
            expected_module_id=module_id,
            expected_task_id=f"{module_id}-lite-task",
            expected_mode="lite",
        )
        catalog = build_standard_analysis_package_catalog(project_root)
        result_index = load_registry(project_root)

        assert result["status"] == "passed", module_id
        assert validation["status"] == "passed", module_id
        assert result_json["module_id"] == module_id
        assert result_json["mode"] == "lite"
        assert result_json["status"] == "passed"
        assert result_json["result_semantics"] == "testing_level"
        assert "formal_computed_result" not in str(result_json)
        assert result_json["summary"]["clinical_conclusion_status"] == "not_generated"  # type: ignore[index]
        assert len(result_json["tables"]) >= 1
        assert len(result_json["reports"]) >= 1
        assert provenance["engine"]["name"] == "biomedpilot_standard_r_worker"  # type: ignore[index]
        assert provenance["runtime"]["r_version"] != "not_executed"  # type: ignore[index]
        assert provenance["input_hash"] != provenance["parameter_hash"]
        assert invocation["module_id"] == module_id
        assert invocation["mode"] == "lite"
        assert invocation["worker_backend"] == "rscript"
        assert invocation["invocation_status"] == "completed"
        assert invocation["runtime_install_policy"] == "forbidden"
        assert invocation["resource_download_policy"] == "forbidden"
        assert invocation["worker_boundary"]["boundary_type"] == "standard_r_worker"  # type: ignore[index]
        assert task_center.list_tasks()[0].status == TaskStatus.COMPLETED
        assert result_index["results"][0]["result_semantics"] == "testing_level"
        assert result_index["results"][0]["validation_status"] == "passed"
        assert result_index["results"][0]["report_ready_eligible"] is False
        assert result_index["results"][0]["log_artifacts"][1]["artifact_type"] == "analysis_worker_invocation_manifest"
        assert catalog["status"] == "passed"
        assert catalog["rows"][0]["module_id"] == module_id
        assert catalog["rows"][0]["mode"] == "lite"
        assert catalog["rows"][0]["worker_boundary_type"] == "standard_r_worker"


def test_all_registered_full_modules_are_blocked_by_task_bridge_with_standard_package(tmp_path: Path) -> None:
    registry = load_analysis_module_registry()
    full_module_ids = [
        str(module["module_id"])
        for module in registry["modules"]
        if "full" in module.get("modes", {})
    ]

    assert full_module_ids

    for module_id in full_module_ids:
        project_root = tmp_path / module_id
        task_center = TaskCenter(project_root / "tasks" / "tasks.json")
        payload = module_input(tmp_path, mode="full", module_id=module_id)
        module = next(item for item in registry["modules"] if item["module_id"] == module_id)
        module_manifest = read_json(Path(module["module_manifest"]))
        full_mode_blocker = str(module["modes"]["full"].get("blocker") or f"analysis_mode_not_enabled:full")
        expected_resource_blockers = full_mode_resource_blockers(module_id)

        result = run_analysis_module_task(
            project_root,
            payload,
            task_center=task_center,
            worker_backend="rscript",
        )
        package_dir = Path(result["result_package_dir"])
        result_json = read_json(package_dir / "result.json")
        provenance = read_json(package_dir / "provenance.json")
        invocation = read_json(package_dir / "logs" / "worker_invocation.json")
        validation = validate_standard_result_package(
            package_dir,
            expected_module_id=module_id,
            expected_task_id=f"{module_id}-full-task",
            expected_mode="full",
        )
        catalog = build_standard_analysis_package_catalog(project_root)
        result_index = load_registry(project_root)

        assert result["status"] == "blocked", module_id
        assert validation["status"] == "passed", module_id
        assert result_json["module_id"] == module_id
        assert result_json["mode"] == "full"
        assert result_json["status"] == "blocked"
        assert full_mode_blocker in result_json["blockers"]
        for blocker in expected_resource_blockers:
            assert blocker in result_json["blockers"]
        assert result_json["tables"] == []
        assert result_json["plots"] == []
        assert result_json["reports"] == []
        assert provenance["engine"]["name"] == "biomedpilot_analysis_task_bridge"  # type: ignore[index]
        assert provenance["runtime"]["r_version"] == "not_executed"  # type: ignore[index]
        assert provenance["runtime"]["bioconductor_version"] == "not_executed"  # type: ignore[index]
        assert provenance["runtime"]["package_versions"] == {}  # type: ignore[index]
        assert provenance["runtime"]["external_tool_versions"] == {}  # type: ignore[index]
        environment = provenance["analysis_environment"]
        assert environment["schema_version"] == "biomedpilot.analysis_environment_snapshot.v1"  # type: ignore[index]
        assert environment["mode"] == "full"  # type: ignore[index]
        assert environment["module_id"] == module_id  # type: ignore[index]
        assert environment["environment_id"] == module["full_environment"]  # type: ignore[index]
        assert environment["dockerfile"] == module_manifest["dockerfile"]  # type: ignore[index]
        assert environment["renv_lock"] == module_manifest["environment_lock"]  # type: ignore[index]
        assert environment["full_mode_requires_isolated_environment"] is True  # type: ignore[index]
        assert environment["runtime_package_install"] == "forbidden"  # type: ignore[index]
        assert environment["runtime_resource_download"] == "forbidden"  # type: ignore[index]
        assert environment["resource_lock_status"]["blockers"] == expected_resource_blockers  # type: ignore[index]
        assert provenance["command"] == "analysis_task_bridge_mode_gate"
        assert invocation["module_id"] == module_id
        assert invocation["mode"] == "full"
        assert invocation["worker_backend"] == "rscript"
        assert invocation["invocation_status"] == "not_invoked_mode_gate"
        assert invocation["returncode"] is None
        assert invocation["command"] == []
        assert invocation["worker_boundary"]["boundary_type"] == "analysis_task_bridge_gate"  # type: ignore[index]
        assert invocation["worker_boundary"]["migration_status"] == "blocked_before_worker_execution"  # type: ignore[index]
        assert task_center.list_tasks()[0].status == TaskStatus.FAILED
        assert result_index["results"][0]["result_semantics"] == "blocked"
        assert result_index["results"][0]["validation_status"] == "blocked"
        dependency_environment = result_index["results"][0]["dependency_snapshot"]["analysis_environment"]
        assert dependency_environment["environment_id"] == module["full_environment"]
        assert dependency_environment["dockerfile"] == module_manifest["dockerfile"]
        assert dependency_environment["renv_lock"] == module_manifest["environment_lock"]
        assert result_index["results"][0]["report_ready_eligible"] is False
        assert result_index["results"][0]["log_artifacts"][1]["artifact_type"] == "analysis_worker_invocation_manifest"
        assert catalog["status"] == "blocked"
        assert catalog["rows"][0]["module_id"] == module_id
        assert catalog["rows"][0]["mode"] == "full"
        assert catalog["rows"][0]["analysis_environment"]["environment_id"] == module["full_environment"]
        assert full_mode_blocker in catalog["rows"][0]["blockers"]


def test_lite_or_full_mode_returns_blocked_standard_package_without_worker_execution(tmp_path: Path) -> None:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    result = run_analysis_module_task(tmp_path, module_input(tmp_path, mode="full"), task_center=task_center)
    package_dir = Path(result["result_package_dir"])
    result_json = read_json(package_dir / "result.json")
    provenance = read_json(package_dir / "provenance.json")
    registry = load_registry(tmp_path)

    assert result["status"] == "blocked"
    assert result_json["status"] == "blocked"
    assert "full_resource_manifest_and_container_not_available" in result_json["blockers"]
    assert "analysis_resource_not_locked:reactome_full" in result_json["blockers"]
    assert "analysis_resource_not_locked:msigdb_full" in result_json["blockers"]
    assert provenance["runtime"]["r_version"] == "not_executed"  # type: ignore[index]
    assert provenance["analysis_environment"]["environment_id"] == "r-bio-full"  # type: ignore[index]
    assert provenance["analysis_environment"]["dockerfile"] == "docker/Dockerfile.r-bio-full"  # type: ignore[index]
    assert provenance["analysis_environment"]["renv_lock"] == "renv/renv.bio-full.lock"  # type: ignore[index]
    assert provenance["analysis_environment"]["status"] == "blocked_full_mode_resource_or_tool_lock"  # type: ignore[index]
    assert "analysis_resource_not_locked:reactome_full" in provenance["analysis_environment"]["resource_lock_status"]["blockers"]  # type: ignore[index]
    assert task_center.list_tasks()[0].status == TaskStatus.FAILED
    assert registry["results"][0]["result_semantics"] == "blocked"
    assert registry["results"][0]["dependency_snapshot"]["analysis_environment"]["environment_id"] == "r-bio-full"
    assert registry["results"][0]["report_ready_eligible"] is False
    detail = build_standard_analysis_package_detail(package_dir, project_root=tmp_path)
    assert detail["provenance"]["analysis_environment"]["environment_id"] == "r-bio-full"
    assert detail["provenance"]["analysis_environment"]["resource_lock_status"]["blockers"]


def test_invalid_module_input_is_blocked_but_still_has_standard_package(tmp_path: Path) -> None:
    payload = module_input(tmp_path)
    payload.pop("parameters")

    result = run_analysis_module_task(tmp_path, payload)
    package_dir = Path(result["result_package_dir"])
    validation = validate_standard_result_package(package_dir, expected_module_id="enrichment", expected_task_id="enrichment-mock-task", expected_mode="mock")
    invocation = read_json(package_dir / "logs" / "worker_invocation.json")
    registry = load_registry(tmp_path)

    assert result["status"] == "blocked"
    assert validation["status"] == "passed"
    assert "module_input_parameters_missing_or_invalid" in read_json(package_dir / "result.json")["blockers"]
    assert invocation["worker_backend"] == "python_fixture"
    assert invocation["invocation_status"] == "blocked_validation_gate"
    assert invocation["worker_boundary"]["boundary_type"] == "analysis_task_bridge_gate"  # type: ignore[index]
    assert "module_input_parameters_missing_or_invalid" in invocation["blockers"]
    assert registry["results"][0]["log_artifacts"][1]["artifact_type"] == "analysis_worker_invocation_manifest"
