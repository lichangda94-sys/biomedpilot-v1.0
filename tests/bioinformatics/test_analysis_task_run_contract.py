from __future__ import annotations

from app.bioinformatics.analysis_task_runs import create_task_run_manifest, validate_task_run_manifest


def test_task_run_manifest_defaults_to_not_run_contract() -> None:
    manifest = create_task_run_manifest(task_type="differential_expression", input_package_id="pkg-1")

    payload = manifest.to_dict()

    assert payload["status"] == "not_run"
    assert payload["task_semantics"] == "config_only"
    assert validate_task_run_manifest(manifest)["status"] == "passed"


def test_task_run_contract_rejects_formal_b8_1_semantics() -> None:
    manifest = create_task_run_manifest(
        task_type="differential_expression",
        input_package_id="pkg-1",
        task_semantics="formal_computed_result",
    )

    validation = validate_task_run_manifest(manifest)

    assert validation["status"] == "blocked"
    assert "forbidden_b8_1_semantics:formal_computed_result" in validation["blockers"]
