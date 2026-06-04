from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .registry import REPO_ROOT
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType

from .registry import get_analysis_module, load_analysis_module_registry
from .r_worker import run_standard_r_worker
from .resources import full_mode_resource_blockers
from .standard_package import REQUIRED_DIRECTORIES, validate_standard_result_package


def run_analysis_module_task(
    project_root: str | Path,
    module_input: dict[str, Any],
    *,
    output_dir: str | Path | None = None,
    task_center: TaskCenter | None = None,
    worker_backend: Literal["python_fixture", "rscript"] = "python_fixture",
) -> dict[str, Any]:
    """Run the standard analysis boundary in mock mode or return a blocked package.

    This is the main-backend bridge. It does not install R packages, download
    resources, or call module-specific R package outputs directly.
    """

    project = Path(project_root).expanduser().resolve()
    registry = load_analysis_module_registry()
    module_id = str(module_input.get("module_id") or "")
    mode = str(module_input.get("mode") or "")
    task_id = str(module_input.get("task_id") or f"analysis-task-{_short_hash(json.dumps(module_input, sort_keys=True))}")
    module = get_analysis_module(module_id, registry=registry)
    package_dir = Path(output_dir).expanduser().resolve() if output_dir else project / "analysis_results" / task_id
    center = task_center or TaskCenter(project / "tasks" / "tasks.json")
    task = _start_task(center, project_id=str(module_input.get("project_id") or project.name), task_id=task_id, module_id=module_id, mode=mode)
    blockers = _validate_input_payload(module_input, module=module)
    if blockers:
        _write_standard_package(package_dir, module_input, status="blocked", blockers=blockers, command="analysis_task_bridge_validation")
        validation = validate_standard_result_package(package_dir, expected_module_id=module_id, expected_task_id=task_id, expected_mode=mode)
        _finish_task(center, task, success=False, summary=f"Analysis task blocked: {', '.join(blockers)}")
        result_entry = _register_standard_package(project, package_dir, module_input, validation, status="blocked", blockers=blockers)
        return _bridge_result(package_dir, module_input, validation, result_entry, status="blocked", blockers=blockers)

    mode_policy = module.get("modes", {}).get(mode, {}) if isinstance(module.get("modes"), dict) else {}
    mode_supported = bool(mode_policy.get("supported"))
    worker_required = str(mode_policy.get("worker_backend") or "") == "rscript"
    mode_worker_blocked = mode_supported and worker_required and worker_backend != "rscript"
    if not mode_supported or mode_worker_blocked or mode == "full":
        blocker = str(mode_policy.get("blocker") or f"analysis_mode_not_enabled:{mode}")
        if mode_worker_blocked:
            blocker = f"analysis_mode_requires_rscript_worker:{mode}"
        mode_blockers = [blocker]
        if mode == "full":
            mode_blockers.extend(full_mode_resource_blockers(module_id))
            mode_blockers = list(dict.fromkeys(mode_blockers))
        _write_standard_package(package_dir, module_input, status="blocked", blockers=mode_blockers, command="analysis_task_bridge_mode_gate")
        validation = validate_standard_result_package(package_dir, expected_module_id=module_id, expected_task_id=task_id, expected_mode=mode)
        _finish_task(center, task, success=False, summary=f"Analysis task blocked: {', '.join(mode_blockers)}")
        result_entry = _register_standard_package(project, package_dir, module_input, validation, status="blocked", blockers=mode_blockers)
        return _bridge_result(package_dir, module_input, validation, result_entry, status="blocked", blockers=mode_blockers)

    if worker_backend == "rscript":
        worker_input = _write_worker_input_manifest(package_dir, module_input)
        worker_result = run_standard_r_worker(worker_input, package_dir, mode)
        fixture_blockers = list(worker_result.get("blockers", []))
        if worker_result["status"] == "blocked" and not (package_dir / "result.json").is_file():
            _write_standard_package(
                package_dir,
                module_input,
                status="blocked",
                blockers=fixture_blockers,
                warnings=["r_worker_unavailable"],
                command="analysis_task_bridge_rscript_worker",
            )
    else:
        fixture_blockers = _write_mock_fixture_package(
            package_dir,
            module_input,
            mode_policy=mode_policy,
        )
        if fixture_blockers:
            _write_standard_package(
                package_dir,
                module_input,
                status="blocked",
                blockers=fixture_blockers,
                warnings=["mock_fixture_unavailable"],
                command="analysis_task_bridge_mock_fixture_gate",
            )
    validation = validate_standard_result_package(package_dir, expected_module_id=module_id, expected_task_id=task_id, expected_mode=mode)
    success = validation["status"] == "passed" and not fixture_blockers
    _finish_task(center, task, success=success, summary="Mock analysis task completed." if success else "Mock analysis task package validation failed.")
    blockers = list(fixture_blockers or validation.get("blockers", []))
    result_entry = _register_standard_package(project, package_dir, module_input, validation, status="passed" if success else "blocked", blockers=blockers)
    return _bridge_result(package_dir, module_input, validation, result_entry, status="passed" if success else "blocked", blockers=blockers)


def _validate_input_payload(payload: dict[str, Any], *, module: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if payload.get("schema_version") != "biomedpilot.analysis.module_input.v1":
        blockers.append("module_input_schema_version_mismatch")
    if payload.get("module_id") != module.get("module_id"):
        blockers.append("module_input_module_id_mismatch")
    if payload.get("mode") not in {"mock", "lite", "full"}:
        blockers.append("module_input_mode_invalid")
    if not payload.get("task_id"):
        blockers.append("module_input_task_id_missing")
    if not isinstance(payload.get("inputs"), dict):
        blockers.append("module_input_inputs_missing_or_invalid")
    if not isinstance(payload.get("parameters"), dict):
        blockers.append("module_input_parameters_missing_or_invalid")
    return blockers


def _write_worker_input_manifest(package_dir: Path, payload: dict[str, Any]) -> Path:
    package_dir.mkdir(parents=True, exist_ok=True)
    input_path = package_dir / "module_input.json"
    _write_json(input_path, payload)
    return input_path


def _write_standard_package(
    package_dir: Path,
    payload: dict[str, Any],
    *,
    status: str,
    blockers: list[str],
    warnings: list[str] | None = None,
    command: str,
) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    for dirname in REQUIRED_DIRECTORIES:
        (package_dir / dirname).mkdir(parents=True, exist_ok=True)
    now = _now()
    module_id = str(payload.get("module_id") or "")
    task_id = str(payload.get("task_id") or "")
    mode = str(payload.get("mode") or "")
    input_hash = _hash_payload(payload.get("inputs", {}))
    parameter_hash = _hash_payload(payload.get("parameters", {}))
    r_not_required = mode == "mock" and command != "analysis_task_bridge_rscript_worker"
    r_runtime_status = "not_required_for_mock" if r_not_required else "not_executed"
    result = {
        "schema_version": "biomedpilot.analysis.result.v1",
        "module_id": module_id,
        "mode": mode,
        "task_id": task_id,
        "status": status,
        "summary": {
            "message": "Standard analysis result package generated by the main-backend task bridge.",
            "clinical_conclusion_status": "not_generated",
        },
        "tables": [],
        "plots": [],
        "reports": [],
        "blockers": blockers,
        "warnings": list(warnings or []),
        "created_at": now,
    }
    provenance = {
        "schema_version": "biomedpilot.analysis.provenance.v1",
        "module_id": module_id,
        "mode": mode,
        "task_id": task_id,
        "created_at": now,
        "input_hash": input_hash,
        "parameter_hash": parameter_hash,
        "random_seed": (payload.get("runtime") or {}).get("random_seed") if isinstance(payload.get("runtime"), dict) else None,
        "engine": {"name": "biomedpilot_analysis_task_bridge", "version": "v1"},
        "runtime": {
            "r_version": r_runtime_status,
            "bioconductor_version": r_runtime_status,
            "package_versions": {},
            "external_tool_versions": {},
        },
        "command": command,
    }
    _write_json(package_dir / "result.json", result)
    _write_json(package_dir / "provenance.json", provenance)
    (package_dir / "logs" / "worker.log").write_text(
        f"{now} status={status} module_id={module_id} mode={mode} task_id={task_id}\n",
        encoding="utf-8",
    )


def _write_mock_fixture_package(package_dir: Path, payload: dict[str, Any], *, mode_policy: dict[str, Any]) -> list[str]:
    fixture_package = mode_policy.get("fixture_output_package")
    if not isinstance(fixture_package, str) or not fixture_package:
        return ["mock_fixture_output_package_missing"]
    source = (REPO_ROOT / fixture_package).resolve()
    if not source.is_dir():
        return [f"mock_fixture_output_package_not_found:{fixture_package}"]

    package_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, package_dir, dirs_exist_ok=True)
    for dirname in REQUIRED_DIRECTORIES:
        (package_dir / dirname).mkdir(parents=True, exist_ok=True)

    now = _now()
    task_id = str(payload.get("task_id") or "")
    module_id = str(payload.get("module_id") or "")
    mode = str(payload.get("mode") or "")
    input_hash = _hash_payload(payload.get("inputs", {}))
    parameter_hash = _hash_payload(payload.get("parameters", {}))
    result = _load_json(package_dir / "result.json")
    provenance = _load_json(package_dir / "provenance.json")
    result.update(
        {
            "module_id": module_id,
            "mode": mode,
            "task_id": task_id,
            "status": "passed",
            "created_at": now,
        }
    )
    warnings = list(result.get("warnings") or [])
    if "mock_result_not_scientific_output" not in warnings:
        warnings.append("mock_result_not_scientific_output")
    result["warnings"] = warnings
    result["blockers"] = []
    provenance.update(
        {
            "module_id": module_id,
            "mode": mode,
            "task_id": task_id,
            "created_at": now,
            "input_hash": input_hash,
            "parameter_hash": parameter_hash,
            "random_seed": (payload.get("runtime") or {}).get("random_seed") if isinstance(payload.get("runtime"), dict) else None,
            "command": "analysis_task_bridge_mock_fixture_copy",
        }
    )
    runtime = provenance.get("runtime")
    if not isinstance(runtime, dict):
        runtime = {}
    runtime.update(
        {
            "r_version": "not_required_for_mock",
            "bioconductor_version": "not_required_for_mock",
            "package_versions": {},
            "external_tool_versions": {},
        }
    )
    provenance["runtime"] = runtime
    engine = provenance.get("engine")
    if not isinstance(engine, dict):
        engine = {}
    engine.update({"name": "biomedpilot_analysis_task_bridge", "version": "v1"})
    provenance["engine"] = engine
    _write_json(package_dir / "result.json", result)
    _write_json(package_dir / "provenance.json", provenance)
    (package_dir / "logs" / "worker.log").write_text(
        f"{now} status=passed module_id={module_id} mode={mode} task_id={task_id} fixture_source={fixture_package}\n",
        encoding="utf-8",
    )
    return []


def _register_standard_package(
    project: Path,
    package_dir: Path,
    payload: dict[str, Any],
    validation: dict[str, Any],
    *,
    status: str,
    blockers: list[str],
) -> dict[str, Any]:
    now = _now()
    task_id = str(payload.get("task_id") or "")
    module_id = str(payload.get("module_id") or "")
    rel_package = str(package_dir.relative_to(project)) if package_dir.is_relative_to(project) else str(package_dir)
    provenance = _load_json(package_dir / "provenance.json") if (package_dir / "provenance.json").is_file() else {}
    engine = provenance.get("engine") if isinstance(provenance.get("engine"), dict) else {}
    runtime = provenance.get("runtime") if isinstance(provenance.get("runtime"), dict) else {}
    engine_name = str(engine.get("name") or "biomedpilot_analysis_task_bridge")
    engine_version = str(engine.get("version") or "v1")
    entry = ResultIndexEntry(
        result_id=f"analysis-package-{task_id}",
        task_run_id=task_id,
        task_type=f"analysis:{module_id}",
        result_semantics="testing_level" if status == "passed" else "blocked",
        input_package_id=str((payload.get("inputs") or {}).get("input_package_id") or ""),
        source_dataset_id=str((payload.get("inputs") or {}).get("source_dataset_id") or ""),
        source_repository_manifest="analysis/registry/analysis_modules.json",
        parameters_manifest=dict(payload.get("parameters") or {}),
        engine_name=engine_name,
        engine_version=engine_version,
        dependency_snapshot={
            "policy": "detect_first_no_runtime_install",
            "mode": str(payload.get("mode") or ""),
            "runtime": runtime,
            "command": str(provenance.get("command") or ""),
        },
        output_artifacts=(
            {"artifact_type": "standard_result_package", "path": rel_package, "schema": "biomedpilot.analysis.result_package.v1"},
            {"artifact_type": "analysis_result_json", "path": f"{rel_package}/result.json", "schema": "biomedpilot.analysis.result.v1"},
            {"artifact_type": "analysis_provenance_json", "path": f"{rel_package}/provenance.json", "schema": "biomedpilot.analysis.provenance.v1"},
        ),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed" if validation["status"] == "passed" and not blockers else "blocked",
        warnings=tuple(str(item) for item in validation.get("warnings", [])),
        blockers=tuple(str(item) for item in blockers),
        log_artifacts=({"artifact_type": "analysis_worker_log", "path": f"{rel_package}/logs/worker.log"},),
        failure_reason=";".join(blockers),
        created_at=now,
        updated_at=now,
        report_ready_eligible=False,
    )
    return register_result(project, entry)


def _bridge_result(
    package_dir: Path,
    payload: dict[str, Any],
    validation: dict[str, Any],
    result_entry: dict[str, Any],
    *,
    status: str,
    blockers: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "biomedpilot.analysis_task_bridge_result.v1",
        "status": status,
        "module_id": str(payload.get("module_id") or ""),
        "mode": str(payload.get("mode") or ""),
        "task_id": str(payload.get("task_id") or ""),
        "result_package_dir": str(package_dir),
        "validation": validation,
        "result_entry": result_entry,
        "blockers": list(blockers),
        "warnings": list(validation.get("warnings", [])),
    }


def _start_task(center: TaskCenter, *, project_id: str, task_id: str, module_id: str, mode: str) -> TaskRecord:
    now = _now()
    return center.register_task(
        task_id=task_id,
        task_type=TaskType.ANALYSIS,
        module="analysis_runtime",
        title=f"Analysis module {module_id}",
        project_id=project_id,
        status=TaskStatus.RUNNING,
        started_at=now,
        summary=f"Running analysis module boundary in {mode} mode.",
    )


def _finish_task(center: TaskCenter, task: TaskRecord, *, success: bool, summary: str) -> None:
    now = _now()
    center.save_task(
        TaskRecord(
            task_id=task.task_id,
            task_type=task.task_type,
            status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
            module=task.module,
            title=task.title,
            created_at=task.created_at,
            updated_at=now,
            project_id=task.project_id,
            started_at=task.started_at,
            finished_at=now,
            summary=summary,
            error_message="" if success else summary,
        )
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _hash_payload(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
