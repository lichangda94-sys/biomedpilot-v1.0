from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.bioinformatics.deg_engine import run_formal_controlled_deg, save_deg_parameter_confirmation
from app.bioinformatics.deg_engine.confirmation import CONFIRMATION_PATH
from app.bioinformatics.deg_engine.standard_package import write_formal_deg_standard_result_package
from app.bioinformatics.plots import create_formal_deg_plot_artifact
from app.bioinformatics.reports.e2e_audit import audit_formal_deg_e2e_acceptance
from app.bioinformatics.reports.formal_deg import create_formal_deg_report_ready_package, evaluate_formal_deg_report_ready_gate
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, register_result


def test_formal_deg_e2e_acceptance_audit_passes_full_user_flow(tmp_path: Path, monkeypatch) -> None:
    _write_standardized_state(tmp_path)
    _patch_backend(monkeypatch)
    dependency = _dependency()
    confirmation = save_deg_parameter_confirmation(tmp_path, dependency_snapshot=dependency)
    run = run_formal_controlled_deg(tmp_path, dependency_snapshot=dependency, allow_legacy_sidecar_execution=True)
    result_id = str(run["result_id"])
    imported = ResultIndexEntry(result_id="imported", task_run_id="task-imported", task_type="deg", result_semantics="imported_external_result", validation_status="passed")
    register_result(tmp_path, imported)
    plot = create_formal_deg_plot_artifact(tmp_path, result_id=result_id, plot_type="volcano_plot")
    gate = evaluate_formal_deg_report_ready_gate(tmp_path, result_id=result_id)
    package = create_formal_deg_report_ready_package(tmp_path, result_id=result_id)
    audit = audit_formal_deg_e2e_acceptance(tmp_path, result_id=result_id)

    assert confirmation["status"] == "confirmed"
    assert run["status"] == "passed"
    assert plot["status"] == "passed"
    assert gate["status"] == "eligible_for_formal_deg_report_ready"
    assert package["status"] == "formal_deg_report_ready_package_created"
    assert audit["status"] == "passed"
    assert audit["traceability"]["confirmation_result_id"] == result_id
    assert audit["traceability"]["result_id"] == result_id
    assert audit["traceability"]["review_selected_result_id"] == result_id
    assert result_id in audit["traceability"]["report_included_result_ids"]
    assert audit["checklist"]["review_matches_result_table"] is True
    assert audit["checklist"]["review_matches_report_package_table"] is True
    assert audit["checklist"]["plot_artifact_registered_and_packaged"] is True
    assert audit["checklist"]["export_path_visible_stable_no_overwrite"] is True
    assert audit["checklist"]["package_independently_reviewable"] is True
    assert audit["checklist"]["non_formal_outputs_not_upgraded"] is True
    assert audit["checklist"]["statistical_only_boundaries_present"] is True
    imported_entry = next(entry for entry in load_registry(tmp_path)["results"] if entry["result_id"] == "imported")
    assert imported_entry["report_ready_eligible"] is False


def test_formal_deg_e2e_audit_blocks_missing_plot_with_clear_reason(tmp_path: Path, monkeypatch) -> None:
    _write_standardized_state(tmp_path)
    _patch_backend(monkeypatch)
    dependency = _dependency()
    save_deg_parameter_confirmation(tmp_path, dependency_snapshot=dependency)
    run = run_formal_controlled_deg(tmp_path, dependency_snapshot=dependency, allow_legacy_sidecar_execution=True)

    audit = audit_formal_deg_e2e_acceptance(tmp_path, result_id=str(run["result_id"]))

    assert audit["status"] == "blocked"
    assert "plot_artifact_registered_and_packaged" in audit["blockers"]
    assert "formal_deg_report_ready_requires_formal_plot_artifact_or_table_only_mode" in audit["failure_diagnostics"]["report_gate_blockers"]


def test_formal_deg_e2e_audit_accepts_explicit_table_only_without_plot_misleading(tmp_path: Path, monkeypatch) -> None:
    _write_standardized_state(tmp_path)
    _patch_backend(monkeypatch)
    dependency = _dependency()
    save_deg_parameter_confirmation(tmp_path, dependency_snapshot=dependency)
    run = run_formal_controlled_deg(tmp_path, dependency_snapshot=dependency, allow_legacy_sidecar_execution=True)
    result_id = str(run["result_id"])
    package = create_formal_deg_report_ready_package(tmp_path, result_id=result_id, allow_table_only_report=True)

    audit = audit_formal_deg_e2e_acceptance(tmp_path, result_id=result_id, allow_table_only_report=True)

    assert package["status"] == "formal_deg_report_ready_package_created"
    assert audit["status"] == "passed"
    assert audit["checklist"]["table_only_mode_not_misleading"] is True
    report_text = (Path(str(package["package_path"])) / "formal_deg_report.md").read_text(encoding="utf-8")
    assert "does not mean plot generation failed" in report_text
    assert "must not imply that volcano or heatmap figures were generated" in report_text


def test_formal_deg_e2e_audit_surfaces_expired_confirmation_dependency_and_invalid_table(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "formal.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text("feature_id\tgene_symbol\tp_value\nf1\tTP53\t0.01\n", encoding="utf-8")
    parameters = {
        "status": "passed",
        "method": "welch_t_test",
        "case_samples": ["case1", "case2"],
        "control_samples": ["ctrl1", "ctrl2"],
    }
    dependency = {"status": "blocked", "blockers": ["missing_python_package:scipy"], "packages": {}}
    log_path = tmp_path / "analysis" / "formal_deg" / "formal-failed-audit_run_log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps({"schema_version": "biomedpilot.formal_deg_run_log.v1", "result_id": "formal-failed-audit"}), encoding="utf-8")
    standard_package = write_formal_deg_standard_result_package(
        tmp_path,
        result_id="formal-failed-audit",
        task_run_id="task-formal-failed-audit",
        result_table_path=table,
        log_path=log_path,
        parameter_manifest=parameters,
        dependency_snapshot=dependency,
        engine_name="python_scipy_statsmodels_deg_mvp",
        engine_version="0.1.0",
    )
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="formal-failed-audit",
            task_run_id="task-formal-failed-audit",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="pkg",
            source_dataset_id="dataset",
            source_repository_manifest="manifest",
            parameters_manifest=parameters,
            engine_name="python_scipy_statsmodels_deg_mvp",
            engine_version="0.1.0",
            dependency_snapshot=dependency,
            output_artifacts=(
                {"artifact_type": "deg_result_table", "path": str(table.relative_to(tmp_path)), "schema": "biomedpilot.deg_result_table.v1"},
                {"artifact_type": "standard_result_package", "path": str(standard_package.relative_to(tmp_path)), "schema": "biomedpilot.analysis.result_package.v1"},
            ),
            log_artifacts=(
                {"artifact_type": "formal_deg_run_log", "path": str(log_path.relative_to(tmp_path))},
                {
                    "artifact_type": "analysis_worker_invocation_manifest",
                    "path": str((standard_package / "logs" / "worker_invocation.json").relative_to(tmp_path)),
                    "schema": "biomedpilot.analysis.worker_invocation.v1",
                },
            ),
            validation_status="passed",
            report_ready_eligible=False,
        ),
    )
    confirmation_path = tmp_path / CONFIRMATION_PATH
    confirmation_path.parent.mkdir(parents=True, exist_ok=True)
    confirmation_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.formal_deg_parameter_confirmation.v1",
                "created_at": "2000-01-01T00:00:00+00:00",
                "status": "confirmed",
                "confirmed_by_user": True,
                "parameter_manifest": parameters,
                "dependency_snapshot": dependency,
                "output_plan": {"result_id": "formal-failed-audit"},
            }
        ),
        encoding="utf-8",
    )

    audit = audit_formal_deg_e2e_acceptance(tmp_path, result_id="formal-failed-audit", allow_table_only_report=True)
    blockers = " ".join(str(item) for item in audit["failure_diagnostics"]["report_gate_blockers"])

    assert audit["status"] == "blocked"
    assert "formal_deg_parameter_confirmation_expired" in blockers
    assert "formal_deg_dependency_snapshot_not_passed" in blockers
    assert "deg_table:missing_column:adjusted_p_value" in blockers


def _patch_backend(monkeypatch) -> None:
    class Stats:
        @staticmethod
        def ttest_ind(case_values, control_values, equal_var=False, nan_policy="omit"):
            return SimpleNamespace(pvalue=0.01, statistic=2.5)

        @staticmethod
        def mannwhitneyu(case_values, control_values, alternative="two-sided"):
            return SimpleNamespace(pvalue=0.02, statistic=3.0)

    def multipletests(p_values, method="fdr_bh"):
        return None, [min(1.0, value * len(p_values)) for value in p_values]

    from app.bioinformatics.deg_engine import python_backend

    monkeypatch.setattr(python_backend, "_import_backends", lambda: (Stats, multipletests))


def _write_standardized_state(root: Path) -> None:
    matrix = root / "matrix.tsv"
    matrix.write_text("gene\tcase1\tcase2\tctrl1\tctrl2\nTP53\t10\t12\t5\t6\nEGFR\t2\t2\t8\t9\n", encoding="utf-8")
    sample = root / "sample.tsv"
    sample.write_text("sample_id\tgroup\ncase1\tcase\ncase2\tcase\nctrl1\tcontrol\nctrl2\tcontrol\n", encoding="utf-8")
    group = root / "group.json"
    group.write_text(json.dumps({"group_design": {"sample_group_assignments": {"case1": "case", "case2": "case", "ctrl1": "control", "ctrl2": "control"}}}), encoding="utf-8")
    assets = [
        _asset("expr", "raw_count_matrix", "expression_repository", matrix, value_type="count", gene_id_type="symbol"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", group),
    ]
    selection = {"expression": {"asset_id": "expr", "selection_state": "user_confirmed"}}
    payload = {"schema_version": "biomedpilot.repository_manifest.v1", "assets": assets, "default_asset_selection": selection}
    registry = {"schema_version": "biomedpilot.standardized_assets_registry.v2", "assets": assets, "default_asset_selection": selection}
    repo_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.write_text(json.dumps(payload), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")


def _asset(asset_id: str, asset_type: str, repository: str, path: Path, *, value_type: str = "", gene_id_type: str = "symbol") -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_role": "expression_matrix" if "expression" in asset_type or "count" in asset_type else asset_type,
        "repository": repository,
        "path": str(path),
        "file_path": str(path),
        "validation_status": "passed",
        "analysis_ready": True,
        "expression_value_type": value_type,
        "gene_id_type": gene_id_type,
    }


def _dependency() -> dict[str, object]:
    return {
        "status": "passed",
        "engine_candidate": "python_scipy_statsmodels",
        "blockers": [],
        "packages": {
            "numpy": {"version": "2.4.6"},
            "pandas": {"version": "3.0.3"},
            "scipy": {"version": "1.17.1"},
            "statsmodels": {"version": "0.14.6"},
        },
    }
