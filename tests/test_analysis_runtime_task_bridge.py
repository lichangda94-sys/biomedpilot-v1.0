from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.analysis_runtime import run_analysis_module_task, validate_standard_result_package
from app.analysis_runtime.registry import load_analysis_module_registry
from app.bioinformatics.results.registry import load_registry
from app.shared.task_center.service import TaskCenter, TaskStatus


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def module_input(tmp_path: Path, *, mode: str = "mock", module_id: str = "enrichment") -> dict[str, object]:
    return {
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
