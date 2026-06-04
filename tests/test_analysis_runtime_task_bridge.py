from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.analysis_runtime import build_standard_analysis_package_catalog, run_analysis_module_task, validate_standard_result_package
from app.analysis_runtime.registry import load_analysis_module_registry
from app.bioinformatics.results.registry import load_registry
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
    assert "mock_result_not_scientific_output" in row["warnings"]


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
    assert result["status"] == "blocked"
    assert "rscript_not_available" in result["blockers"]
    assert result_json["status"] == "blocked"
    assert provenance["runtime"]["r_version"] == "not_executed"  # type: ignore[index]
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
    assert task_center.list_tasks()[0].status == TaskStatus.FAILED
    assert registry["results"][0]["result_semantics"] == "blocked"
    assert registry["results"][0]["report_ready_eligible"] is False


def test_invalid_module_input_is_blocked_but_still_has_standard_package(tmp_path: Path) -> None:
    payload = module_input(tmp_path)
    payload.pop("parameters")

    result = run_analysis_module_task(tmp_path, payload)
    package_dir = Path(result["result_package_dir"])
    validation = validate_standard_result_package(package_dir, expected_module_id="enrichment", expected_task_id="enrichment-mock-task", expected_mode="mock")

    assert result["status"] == "blocked"
    assert validation["status"] == "passed"
    assert "module_input_parameters_missing_or_invalid" in read_json(package_dir / "result.json")["blockers"]
