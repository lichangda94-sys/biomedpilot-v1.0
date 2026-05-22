from __future__ import annotations

from pathlib import Path

from app.bioinformatics.reports.integrated import evaluate_full_integrated_report_gate
from app.bioinformatics.results.registry import save_registry


def test_full_integrated_gate_blocks_until_survival_clinical_section_packages_pass(tmp_path: Path) -> None:
    _write_full_layer_fixture(tmp_path)

    gate = evaluate_full_integrated_report_gate(tmp_path)

    assert gate["status"] == "blocked"
    assert gate["section_scope"] == "full_integrated_report"
    assert "survival_clinical_report_ready_not_implemented" not in gate["blockers"]
    assert "full_integrated_report_export_not_enabled_in_b23_1" in gate["blockers"]
    sections = {row["section_id"]: row for row in gate["section_rows"]}
    assert sections["formal_deg"]["result_id"] == "deg-formal"
    assert sections["survival_km_logrank"]["plot_artifact_status"] == "real_artifact_registered"
    assert sections["cox"]["plot_artifact_status"] == "real_artifact_registered"
    assert sections["survival_km_logrank"]["section_report_ready_status"] == "blocked"
    prerequisites = {row["section_id"]: row for row in gate["prerequisite_rows"]}
    assert gate["prerequisite_summary"]["status"] == "blocked"
    assert gate["prerequisite_summary"]["survival_clinical_report_ready_required"] is True
    assert prerequisites["formal_deg"]["required_result_semantics"] == "formal_computed_result"
    assert prerequisites["survival_km_logrank"]["section_only_package_sufficient"] is False
    assert "full_integrated_prerequisite_survival_clinical_section_package_not_passed:survival_km_logrank" in prerequisites["survival_km_logrank"]["blockers"]


def test_full_integrated_gate_blocks_missing_required_sections(tmp_path: Path) -> None:
    _write_full_layer_fixture(tmp_path, omit={"gsea_preranked", "cox"})

    gate = evaluate_full_integrated_report_gate(tmp_path)

    assert "section_result_missing:gsea_preranked" in gate["blockers"]
    assert "section_result_missing:cox" in gate["blockers"]
    assert gate["checks"]["required_sections_present"] is False
    prerequisites = {row["section_id"]: row for row in gate["prerequisite_rows"]}
    assert "full_integrated_prerequisite_missing_result:gsea_preranked" in prerequisites["gsea_preranked"]["blockers"]


def test_full_integrated_gate_blocks_non_formal_sources(tmp_path: Path) -> None:
    _write_full_layer_fixture(tmp_path, semantics={"gsea_preranked": "imported_external_result", "survival_km_logrank": "preflight_only"})

    gate = evaluate_full_integrated_report_gate(tmp_path)

    assert "section_result_not_formal:gsea_preranked:gsea-formal" in gate["blockers"]
    assert "non_formal_result_forbidden_in_full_integrated_report:gsea-formal" in gate["blockers"]
    assert "section_result_not_formal:survival_km_logrank:km-formal" in gate["blockers"]
    assert "non_formal_result_forbidden_in_full_integrated_report:km-formal" in gate["blockers"]
    assert gate["checks"]["no_imported_testing_exploratory_or_preflight"] is False
    prerequisites = {row["section_id"]: row for row in gate["prerequisite_rows"]}
    assert "full_integrated_prerequisite_requires_formal_result:gsea_preranked" in prerequisites["gsea_preranked"]["blockers"]


def test_section_only_report_artifacts_do_not_make_full_integrated_report(tmp_path: Path) -> None:
    _write_full_layer_fixture(tmp_path, section_only_reports=True)

    gate = evaluate_full_integrated_report_gate(tmp_path)

    assert gate["status"] == "blocked"
    assert gate["section_scope"] == "full_integrated_report"
    assert "survival_clinical_report_ready_not_implemented" not in gate["blockers"]
    assert gate["package_layout"][0] == "integrated_report.md"
    assert all("full_integrated_report" not in str(row.get("section_report_ready_gate", {}).get("package_layout", "")) for row in gate["section_rows"])
    prerequisites = {row["section_id"]: row for row in gate["prerequisite_rows"]}
    assert "full_integrated_prerequisite_forbids_section_package_as_full_report:formal_deg" in prerequisites["formal_deg"]["blockers"]
    assert "section_package_manifest_missing:survival_km_logrank:survival_km_logrank_only" in prerequisites["survival_km_logrank"]["blockers"]
    assert prerequisites["formal_deg"]["registered_report_scopes"] == ["formal_deg_only"]


def _write_full_layer_fixture(
    root: Path,
    *,
    omit: set[str] | None = None,
    semantics: dict[str, str] | None = None,
    section_only_reports: bool = False,
) -> None:
    omit = omit or set()
    semantics = semantics or {}
    entries = []
    for section_id, result_id, task_type, artifact_type in (
        ("formal_deg", "deg-formal", "deg", "deg_result_table"),
        ("ora_enrichment", "ora-formal", "ora_enrichment", "ora_result_table"),
        ("gsea_preranked", "gsea-formal", "gsea_preranked", "gsea_result_table"),
        ("survival_km_logrank", "km-formal", "survival_km_logrank", "km_curve_table"),
        ("cox", "cox-formal", "cox_univariate", "cox_result_table"),
    ):
        if section_id in omit:
            continue
        table_path = _write_table(root, result_id, artifact_type)
        log_path = _write_log(root, result_id)
        plots = [{"plot_id": f"plot-{result_id}", "plot_type": "km_curve" if section_id == "survival_km_logrank" else "cox_forest_plot", "image_artifacts": [{"path": str(root / "plot.svg"), "format": "svg"}]}] if section_id in {"survival_km_logrank", "cox"} else []
        report_artifacts = [{"artifact_type": f"{section_id}_report_ready_package", "path": f"reports/{result_id}.json", "section_scope": f"{section_id}_only"}] if section_only_reports else []
        entries.append(
            {
                "result_id": result_id,
                "task_run_id": f"run-{result_id}",
                "task_type": task_type,
                "result_semantics": semantics.get(section_id, "formal_computed_result"),
                "input_package_id": f"input-{result_id}",
                "source_dataset_id": "dataset",
                "source_repository_manifest": "manifest",
                "parameters_manifest": {"section": section_id},
                "engine_name": "engine",
                "engine_version": "1",
                "dependency_snapshot": {"status": "passed", "packages": {}},
                "output_artifacts": [{"artifact_type": artifact_type, "path": str(table_path)}],
                "plot_artifacts": plots,
                "report_artifacts": report_artifacts,
                "validation_status": "passed",
                "warnings": [],
                "blockers": [],
                "log_artifacts": [{"artifact_type": "task_run_log", "path": str(log_path)}],
                "failure_reason": "",
                "created_at": "2026-05-22T00:00:00+00:00",
                "updated_at": "2026-05-22T00:00:00+00:00",
                "schema_version": "biomedpilot.result_index_entry.v1",
                "report_ready_eligible": section_only_reports,
                "migration_status": "native_v2",
            }
        )
    save_registry(root, entries)


def _write_table(root: Path, result_id: str, artifact_type: str) -> Path:
    path = root / "results" / "tables" / f"{result_id}.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{artifact_type}\nvalue\n", encoding="utf-8")
    return path


def _write_log(root: Path, result_id: str) -> Path:
    path = root / "analysis" / f"{result_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"status": "succeeded"}\n', encoding="utf-8")
    return path
