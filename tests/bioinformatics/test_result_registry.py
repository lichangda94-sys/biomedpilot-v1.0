from __future__ import annotations

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, register_result


def test_result_registry_registers_complete_formal_entry(tmp_path) -> None:
    entry = ResultIndexEntry(
        result_id="res-1",
        task_run_id="task-1",
        task_type="deg",
        result_semantics="formal_computed_result",
        input_package_id="pkg-1",
        source_dataset_id="dataset",
        source_repository_manifest="manifest.json",
        parameters_manifest={"method": "welch"},
        engine_name="python",
        engine_version="1",
        dependency_snapshot={"scipy": "ok"},
        validation_status="passed",
        report_ready_eligible=True,
    )

    register_result(tmp_path, entry)

    registry = load_registry(tmp_path)
    assert registry["results"][0]["result_semantics"] == "formal_computed_result"


def test_legacy_unknown_result_migrates_conservatively(tmp_path) -> None:
    from app.bioinformatics.results.project_results import write_result_index

    write_result_index(tmp_path, [{"result_id": "legacy", "path": "old.csv"}])

    registry = load_registry(tmp_path)

    assert registry["results"][0]["result_semantics"] == "testing_level"
    assert registry["results"][0]["migration_status"] == "legacy_unverified"
