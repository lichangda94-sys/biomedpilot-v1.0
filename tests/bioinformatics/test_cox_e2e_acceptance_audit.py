from __future__ import annotations

from app.bioinformatics.clinical_analysis import build_survival_package
from app.bioinformatics.plots import create_cox_forest_plot_artifact
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result
from app.bioinformatics.survival_clinical import audit_cox_univariate_e2e_acceptance, build_cox_univariate_parameter_manifest, confirm_cox_univariate_parameters, run_controlled_cox_univariate


def test_cox_e2e_acceptance_passes_complete_chain(tmp_path) -> None:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tarm\n"
        "S1\t5\t1\tA\nS2\t8\t0\tA\nS3\t12\t1\tA\n"
        "S4\t6\t1\tB\nS5\t9\t0\tB\nS6\t15\t1\tB\n",
        encoding="utf-8",
    )
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    manifest = build_cox_univariate_parameter_manifest(package, outcome_gate={"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": []}, covariate="arm", dependency_snapshot={"status": "passed", "python_lifelines": {"available": True, "version": "test"}})
    confirmation = confirm_cox_univariate_parameters(tmp_path, manifest)
    result = run_controlled_cox_univariate(tmp_path, manifest, confirmation, allow_legacy_sidecar_execution=True)
    create_cox_forest_plot_artifact(str(tmp_path), result["result_id"])

    audit = audit_cox_univariate_e2e_acceptance(tmp_path, result["result_id"], confirmation=confirmation)

    assert audit["status"] == "passed"
    assert audit["traceability"]["plot_artifact_id"].startswith("plot-cox-")
    assert audit["report_ready_eligible"] is False


def test_cox_e2e_blocks_preflight_source(tmp_path) -> None:
    register_result(tmp_path, ResultIndexEntry(result_id="preflight", task_run_id="t", task_type="cox_univariate", result_semantics="preflight_only", validation_status="passed"))

    audit = audit_cox_univariate_e2e_acceptance(tmp_path, "preflight")

    assert "preflight_testing_or_imported_source_blocked" in audit["blockers"]


def test_cox_e2e_surfaces_missing_dependency_invalid_covariate_and_low_event_blockers(tmp_path) -> None:
    register_result(
        tmp_path,
        {
            "result_id": "cox-blocked",
            "task_run_id": "task",
            "task_type": "cox_univariate",
            "result_semantics": "formal_computed_result",
            "input_package_id": "surv",
            "source_dataset_id": "surv",
            "source_repository_manifest": "B12",
            "parameters_manifest": {
                "status": "blocked",
                "cox_parameter_id": "cox-param",
                "covariate": "case_id",
                "blockers": ["identifier_not_allowed_as_covariate", "minimum_event_count_not_met"],
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

    audit = audit_cox_univariate_e2e_acceptance(tmp_path, "cox-blocked")

    assert "missing_dependency" in audit["blockers"]
    assert "identifier_not_allowed_as_covariate" in audit["blockers"]
    assert "minimum_event_count_not_met" in audit["blockers"]
