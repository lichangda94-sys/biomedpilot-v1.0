from __future__ import annotations

import json
from pathlib import Path

from app.analysis_runtime import build_standard_analysis_package_catalog, validate_standard_result_package
from app.bioinformatics.clinical_analysis import build_survival_package
from app.bioinformatics.results.registry import load_registry
from app.bioinformatics.survival_clinical import build_km_logrank_parameter_manifest, confirm_km_logrank_parameters, run_controlled_km_logrank


def test_controlled_km_logrank_registers_formal_result_without_hr_or_report(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    confirmation = confirm_km_logrank_parameters(tmp_path, manifest)

    result = run_controlled_km_logrank(tmp_path, manifest, confirmation, allow_legacy_sidecar_execution=True)

    assert result["status"] == "passed"
    assert Path(result["km_curve_table"]).is_file()
    assert Path(result["logrank_result_table"]).is_file()
    standard_package_dir = Path(result["standard_result_package_dir"])
    assert standard_package_dir.is_dir()
    assert validate_standard_result_package(standard_package_dir)["status"] == "passed"
    invocation = json.loads((standard_package_dir / "logs" / "worker_invocation.json").read_text(encoding="utf-8"))
    assert invocation["worker_backend"] == "legacy_service_adapter"
    assert invocation["invocation_status"] == "sidecar_recorded"
    assert invocation["worker_boundary"]["task_system_invocation"] == "legacy_service_adapter_direct_call"
    table = Path(result["logrank_result_table"]).read_text(encoding="utf-8")
    assert "p_value" in table
    assert "hazard_ratio" not in table
    index = (tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8")
    assert "formal_computed_result" in index
    assert "survival_km_logrank" in index
    assert '"plot_artifacts": []' in index
    assert '"report_artifacts": []' in index
    assert '"report_ready_eligible": false' in index
    assert '"artifact_type": "standard_result_package"' in index
    entry = load_registry(tmp_path)["results"][0]
    assert any(item["artifact_type"] == "analysis_worker_invocation_manifest" for item in entry["log_artifacts"])
    catalog = build_standard_analysis_package_catalog(tmp_path)
    assert catalog["status"] == "passed"
    row = catalog["rows"][0]
    assert row["module_id"] == "survival"
    assert row["worker_boundary_type"] == "legacy_service_adapter_sidecar"
    assert row["worker_backend"] == "legacy_service_adapter"
    assert row["worker_invocation_status"] == "sidecar_recorded"
    assert row["ui_execution_eligible"] is False
    assert row["migration_evidence_eligible"] is False
    assert row["execution_readiness_policy"] == "legacy_sidecar_review_only_not_ui_execution_readiness"
    assert row["migration_evidence_policy"] == "forbidden_legacy_sidecar_not_standard_worker_migration_evidence"
    assert "legacy_sidecar_package_not_ui_execution_readiness" in row["policy_blockers"]
    assert row["artifact_counts"]["tables"] == 2
    assert row["artifact_counts"]["reports"] == 1
    assert row["artifact_manifest"]["tables"][0]["exists"] is True
    assert "clinical_conclusion_not_generated" in row["warnings"]
    assert "legacy_sidecar_package_not_standard_worker_migration_evidence" in row["warnings"]


def test_controlled_km_logrank_blocks_direct_legacy_sidecar_execution_by_default(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    confirmation = confirm_km_logrank_parameters(tmp_path, manifest)

    result = run_controlled_km_logrank(tmp_path, manifest, confirmation)

    assert result["status"] == "blocked"
    assert result["failure_reason"] == "legacy_sidecar_execution_gate_blocked"
    assert "legacy_service_adapter_sidecar_execution_disabled" in result["blockers"]
    assert "standard_worker_migration_required:survival" in result["blockers"]
    assert result["legacy_sidecar_execution_gate"]["required_task_system_invocation"] == "task_center_registered"
    assert load_registry(tmp_path)["results"] == []


def test_controlled_km_logrank_blocks_missing_confirmation_without_traceback(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    result = run_controlled_km_logrank(tmp_path, manifest, {})

    assert result["status"] == "blocked"
    assert "km_logrank_parameter_confirmation_missing" in result["blockers"]
    assert Path(result["task_run_log_path"]).is_file()


def _manifest(tmp_path: Path) -> dict[str, object]:
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text(
        "sample_id\tOS_time\tOS_event\tarm\n"
        "S1\t5\t1\tA\nS2\t8\t0\tA\nS3\t12\t1\tA\n"
        "S4\t6\t1\tB\nS5\t9\t0\tB\nS6\t15\t1\tB\n",
        encoding="utf-8",
    )
    package = build_survival_package({"input_package_id": "pkg", "clinical_asset": {"path": str(clinical)}})
    return build_km_logrank_parameter_manifest(package, outcome_gate={"status": "passed", "survival_outcome_gate_id": "outcome-1", "blockers": []}, grouping_variable="arm", group_a="A", group_b="B", dependency_snapshot={"status": "passed", "python_lifelines": {"available": True, "version": "test"}})
