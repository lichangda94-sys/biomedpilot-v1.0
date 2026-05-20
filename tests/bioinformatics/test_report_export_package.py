from __future__ import annotations

from app.bioinformatics.reports.export_package import create_report_export_package
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


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
