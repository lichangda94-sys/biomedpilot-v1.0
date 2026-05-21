from __future__ import annotations

from app.bioinformatics.clinical_analysis import build_survival_package
from app.bioinformatics.plots import create_km_plot_artifact
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result
from app.bioinformatics.survival_clinical import audit_survival_km_e2e_acceptance, build_km_logrank_parameter_manifest, confirm_km_logrank_parameters, run_controlled_km_logrank


def test_survival_km_e2e_acceptance_passes_complete_chain(tmp_path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tarm\n"
        "S1\t5\t1\tA\nS2\t8\t0\tA\nS3\t12\t1\tA\n"
        "S4\t6\t1\tB\nS5\t9\t0\tB\nS6\t15\t1\tB\n",
        encoding="utf-8",
    )
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    manifest = build_km_logrank_parameter_manifest(package, outcome_gate={"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": []}, grouping_variable="arm", group_a="A", group_b="B", dependency_snapshot={"status": "passed", "python_lifelines": {"available": True, "version": "test"}})
    confirmation = confirm_km_logrank_parameters(tmp_path, manifest)
    result = run_controlled_km_logrank(tmp_path, manifest, confirmation)
    create_km_plot_artifact(str(tmp_path), result["result_id"])

    audit = audit_survival_km_e2e_acceptance(tmp_path, result["result_id"], confirmation=confirmation)

    assert audit["status"] == "passed"
    assert audit["traceability"]["plot_artifact_id"].startswith("plot-km-")
    assert audit["report_ready_eligible"] is False


def test_survival_km_e2e_blocks_preflight_source(tmp_path) -> None:
    register_result(tmp_path, ResultIndexEntry(result_id="preflight", task_run_id="t", task_type="survival_km_logrank", result_semantics="preflight_only", validation_status="passed"))

    audit = audit_survival_km_e2e_acceptance(tmp_path, "preflight")

    assert "preflight_testing_or_imported_source_blocked" in audit["blockers"]


def test_survival_km_e2e_surfaces_missing_dependency_and_low_event_blockers(tmp_path) -> None:
    register_result(
        tmp_path,
        {
            "result_id": "km-blocked",
            "task_run_id": "task",
            "task_type": "survival_km_logrank",
            "result_semantics": "formal_computed_result",
            "input_package_id": "surv",
            "source_dataset_id": "surv",
            "source_repository_manifest": "B12",
            "parameters_manifest": {
                "status": "blocked",
                "km_parameter_id": "km-param",
                "blockers": ["minimum_event_count_not_met"],
            },
            "engine_name": "engine",
            "engine_version": "1",
            "dependency_snapshot": {"status": "preflight_only", "blockers": ["lifelines_missing_formal_survival_disabled"]},
            "output_artifacts": (),
            "validation_status": "blocked",
            "survival_clinical_input_id": "surv",
            "survival_outcome_gate_id": "outcome",
        },
    )

    audit = audit_survival_km_e2e_acceptance(tmp_path, "km-blocked")

    assert "missing_dependency" in audit["blockers"]
    assert "minimum_event_count_not_met" in audit["blockers"]
