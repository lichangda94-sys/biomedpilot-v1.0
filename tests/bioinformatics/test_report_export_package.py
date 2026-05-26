from __future__ import annotations

import json

from app.bioinformatics.reports.export_package import create_report_export_package
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result
from app.shared.local_engines import ExternalEngineRegistry


def test_report_export_package_contains_required_manifests(tmp_path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="formal",
            task_run_id="task",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg",
            source_dataset_id="dataset",
            source_repository_manifest="manifest",
            parameters_manifest={"method": "welch"},
            engine_name="python",
            engine_version="1",
            dependency_snapshot={"scipy": {"available": True}},
            validation_status="passed",
            report_ready_eligible=True,
        ),
    )

    manifest = create_report_export_package(tmp_path, report_markdown="# Report\n")

    package = tmp_path / "report_package"
    assert manifest["status"] == "report_ready_package_created"
    assert (package / "report.md").exists()
    assert (package / "manifests" / "result_index_snapshot.json").exists()
    assert (package / "README_limitations.md").read_text(encoding="utf-8").count("clinical advice") == 1


def test_report_export_package_records_renderer_handoff_without_blocking_report_ready(tmp_path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="formal",
            task_run_id="task",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg",
            source_dataset_id="dataset",
            source_repository_manifest="manifest",
            parameters_manifest={"method": "welch"},
            engine_name="python",
            engine_version="1",
            dependency_snapshot={"scipy": {"available": True}},
            validation_status="passed",
            report_ready_eligible=True,
        ),
    )
    registry = ExternalEngineRegistry((_snapshot("report_renderer", "renderer.latex.available", "missing"),))

    manifest = create_report_export_package(tmp_path, report_markdown="# Report\n", external_registry=registry)
    dependency_snapshot = json.loads((tmp_path / "report_package" / "manifests" / "dependency_snapshot.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "report_ready_package_created"
    assert dependency_snapshot["formal"]["scipy"]["available"] is True
    assert dependency_snapshot["_boundary"] == "renderer_dependency_state_does_not_decide_report_ready"
    assert dependency_snapshot["_external_engine_handoffs"]["report_renderer"]["all_required_available"] is False
    assert dependency_snapshot["_external_engine_handoffs"]["report_renderer"]["snapshot_path"].endswith("report_renderer_snapshot.json")


def _snapshot(engine_family: str, capability_key: str, capability_status: str) -> dict[str, object]:
    return {
        "schema_version": "biomedpilot_external_engine_dependency_snapshot.v1",
        "engine_family": engine_family,
        "engine_name": engine_family,
        "status": "available" if capability_status == "available" else "partially_available",
        "runtime_path": "/usr/bin/env",
        "version": "1.0.0",
        "architecture": "arm64",
        "checked_at": "2026-05-22T00:00:00+00:00",
        "snapshot_path": f"/tmp/{engine_family}_snapshot.json",
        "packages": [
            {
                "name": capability_key,
                "required_for": ["test_runtime"],
                "status": capability_status,
                "version": "1.0.0" if capability_status == "available" else "",
                "minimum_version": "",
                "blocker": None if capability_status == "available" else {"code": "missing_dependency", "message": "missing", "required_by": ["test_runtime"]},
                "capability_key": capability_key,
            }
        ],
        "blockers": [] if capability_status == "available" else [{"code": "missing_dependency", "message": "missing", "required_by": ["test_runtime"]}],
        "install_guidance": {"safe_to_show": True, "commands": [], "manual_steps": []},
    }
