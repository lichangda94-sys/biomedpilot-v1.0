from __future__ import annotations

from pathlib import Path

from app.bioinformatics.reports import integrated
from app.bioinformatics.reports.integrated import (
    build_full_integrated_report_package_plan,
    create_full_integrated_report_package,
    evaluate_full_integrated_report_renderer_gate,
)
from app.bioinformatics.results.registry import save_registry


def test_integrated_report_package_is_blocked_while_gate_blocked(tmp_path: Path) -> None:
    _write_entries(tmp_path)

    package = create_full_integrated_report_package(tmp_path)

    assert package["status"] == "blocked"
    assert package["package_path"] == ""
    assert package["user_visible_package_path"] == ""
    assert package["package_plan"]["can_create_package"] is False
    assert "survival_clinical_report_ready_not_implemented" in package["blockers"]
    assert not (tmp_path / "report_package" / "integrated").exists()


def test_integrated_report_package_plan_lists_stable_layout(tmp_path: Path) -> None:
    plan = build_full_integrated_report_package_plan(tmp_path, gate={"status": "blocked", "blockers": ["survival_clinical_report_ready_not_implemented"]})

    assert plan["section_scope"] == "full_integrated_report"
    assert "prerequisite_summary" in plan
    assert "sections" in plan["required_directories"]
    assert "integrated_report.md" in plan["required_files"]
    assert "manifests/full_integrated_gate_snapshot.json" in plan["required_files"]
    assert plan["renderer_status"] == "passed"
    assert plan["renderer_id"] == "builtin_markdown"
    assert "preflight_only" in plan["artifact_policy"]["forbidden_sources"]


def test_integrated_report_package_blocks_non_markdown_format_even_when_gate_is_stubbed_passed(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: _passed_gate())

    package = create_full_integrated_report_package(tmp_path, export_format="pdf")

    assert package["status"] == "blocked"
    assert "full_integrated_pdf_renderer_not_enabled_in_b23_4" in package["blockers"]
    assert package["renderer_gate"]["export_format"] == "pdf"
    assert package["package_plan"]["can_create_package"] is False
    assert not (tmp_path / "report_package" / "integrated").exists()


def test_integrated_report_package_plan_surfaces_renderer_gate_for_docx(tmp_path: Path) -> None:
    gate = {"status": "eligible_for_full_integrated_report", "blockers": []}
    renderer = evaluate_full_integrated_report_renderer_gate("docx")

    plan = build_full_integrated_report_package_plan(tmp_path, gate=gate, export_format="docx", renderer_gate=renderer)

    assert plan["export_format"] == "docx"
    assert plan["renderer_id"] == "pandoc_docx"
    assert plan["renderer_status"] == "blocked"
    assert "full_integrated_docx_renderer_not_enabled_in_b23_4" in plan["disabled_reasons"]
    assert plan["can_create_package"] is False


def test_integrated_report_package_skeleton_writes_timestamped_auditable_layout_when_gate_passes(tmp_path: Path, monkeypatch) -> None:
    _write_entries(tmp_path)
    gate = _passed_gate()
    monkeypatch.setattr(integrated, "evaluate_full_integrated_report_gate", lambda *args, **kwargs: gate)

    first = create_full_integrated_report_package(tmp_path)
    second = create_full_integrated_report_package(tmp_path)

    assert first["status"] == "full_integrated_report_package_created"
    assert second["status"] == "full_integrated_report_package_created"
    assert first["package_path"] != second["package_path"]
    package_path = Path(first["package_path"])
    assert (package_path / "integrated_report.md").is_file()
    assert (package_path / "README_limitations.md").is_file()
    assert (package_path / "integrated_report_package_manifest.json").is_file()
    assert (package_path / "manifests" / "full_integrated_gate_snapshot.json").is_file()
    assert (package_path / "manifests" / "result_index_snapshot.json").is_file()
    assert (package_path / "manifests" / "section_manifest.json").is_file()
    assert (package_path / "manifests" / "dependency_snapshot.json").is_file()
    assert (package_path / "manifests" / "warnings_limitations.json").is_file()
    assert (package_path / "manifests" / "package_inventory.json").is_file()
    assert (package_path / "sections" / "formal_deg.md").is_file()
    assert (package_path / "sections" / "ora.md").is_file()
    assert (package_path / "sections" / "gsea.md").is_file()
    assert (package_path / "sections" / "survival_km.md").is_file()
    assert (package_path / "sections" / "cox.md").is_file()
    assert "treatment recommendation" in (package_path / "README_limitations.md").read_text(encoding="utf-8")
    assert first["package_inventory"]["required_files"]["integrated_report_package_manifest.json"] is True


def _write_entries(root: Path) -> None:
    entries = []
    for result_id, task_type, artifact_type in (
        ("deg-formal", "deg", "deg_result_table"),
        ("ora-formal", "ora_enrichment", "ora_result_table"),
        ("gsea-formal", "gsea_preranked", "gsea_result_table"),
        ("km-formal", "survival_km_logrank", "km_curve_table"),
        ("cox-formal", "cox_univariate", "cox_result_table"),
    ):
        table = _write_table(root, result_id, artifact_type)
        log = _write_log(root, result_id)
        plot = _write_plot(root, result_id)
        entries.append(
            {
                "result_id": result_id,
                "task_run_id": f"run-{result_id}",
                "task_type": task_type,
                "result_semantics": "formal_computed_result",
                "input_package_id": f"input-{result_id}",
                "source_dataset_id": "dataset",
                "source_repository_manifest": "manifest",
                "parameters_manifest": {"task_type": task_type},
                "engine_name": "engine",
                "engine_version": "1",
                "dependency_snapshot": {"status": "passed", "packages": {}},
                "output_artifacts": [{"artifact_type": artifact_type, "path": str(table)}],
                "plot_artifacts": [{"plot_id": f"plot-{result_id}", "plot_type": "km_curve", "image_artifacts": [{"path": str(plot), "format": "svg"}]}],
                "report_artifacts": [],
                "validation_status": "passed",
                "warnings": [],
                "blockers": [],
                "log_artifacts": [{"artifact_type": "task_run_log", "path": str(log)}],
                "failure_reason": "",
                "created_at": "2026-05-22T00:00:00+00:00",
                "updated_at": "2026-05-22T00:00:00+00:00",
                "schema_version": "biomedpilot.result_index_entry.v1",
                "report_ready_eligible": False,
                "migration_status": "native_v2",
            }
        )
    save_registry(root, entries)


def _passed_gate() -> dict:
    rows = [
        {"section_id": "formal_deg", "result_id": "deg-formal", "task_type": "deg", "result_semantics": "formal_computed_result", "validation_status": "passed", "plot_artifact_status": "real_artifact_registered", "section_report_ready_status": "passed"},
        {"section_id": "ora_enrichment", "result_id": "ora-formal", "task_type": "ora_enrichment", "result_semantics": "formal_computed_result", "validation_status": "passed", "plot_artifact_status": "real_artifact_registered", "section_report_ready_status": "passed"},
        {"section_id": "gsea_preranked", "result_id": "gsea-formal", "task_type": "gsea_preranked", "result_semantics": "formal_computed_result", "validation_status": "passed", "plot_artifact_status": "real_artifact_registered", "section_report_ready_status": "passed"},
        {"section_id": "survival_km_logrank", "result_id": "km-formal", "task_type": "survival_km_logrank", "result_semantics": "formal_computed_result", "validation_status": "passed", "plot_artifact_status": "real_artifact_registered", "section_report_ready_status": "passed"},
        {"section_id": "cox", "result_id": "cox-formal", "task_type": "cox_univariate", "result_semantics": "formal_computed_result", "validation_status": "passed", "plot_artifact_status": "real_artifact_registered", "section_report_ready_status": "passed"},
    ]
    return {
        "schema_version": "biomedpilot.full_integrated_report_gate.v1",
        "status": "eligible_for_full_integrated_report",
        "section_scope": "full_integrated_report",
        "section_rows": rows,
        "blockers": [],
        "warnings": [],
        "limitations_required": ["Statistical research report only."],
    }


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


def _write_plot(root: Path, result_id: str) -> Path:
    path = root / "results" / "plots" / f"{result_id}.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("<svg></svg>\n", encoding="utf-8")
    return path
