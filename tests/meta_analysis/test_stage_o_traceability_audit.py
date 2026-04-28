from __future__ import annotations

import json
import zipfile
from pathlib import Path

from app.meta_analysis.services.ai_suggestion_service import AISuggestionService
from app.meta_analysis.services.publication_export_service import PublicationExportService
from app.meta_analysis.services.traceability_audit_service import TraceabilityAuditService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter
from tests.meta_analysis.e2e_project_builder import build_meta_analysis_e2e_project


def test_traceability_audit_passes_for_stage_m_project(tmp_path: Path) -> None:
    project = build_meta_analysis_e2e_project(tmp_path)
    service = TraceabilityAuditService()

    audit = service.run_traceability_audit(project["project_dir"], project["paths"]["reproducibility_package"])

    assert audit.passed
    assert audit.lineage_checks["analysis_result_to_dataset"] is True
    assert audit.lineage_checks["analysis_ready_dataset_to_extraction_records"] is True
    assert audit.lineage_checks["extraction_records_to_included_literature"] is True
    assert audit.lineage_checks["figures_to_analysis_result"] is True
    assert audit.reproducibility_checks["complete"] is True
    assert audit.report_checks["declares_testing_status"] is True
    assert any(item["artifact_type"] == "analysis_result" for item in audit.artifact_manifest)


def test_traceability_audit_warns_without_crashing_when_sources_are_missing(tmp_path: Path) -> None:
    project_dir = tmp_path / "broken-project"
    (project_dir / "analysis").mkdir(parents=True)
    (project_dir / "reports").mkdir(parents=True)
    (project_dir / "analysis" / "analysis_results.json").write_text(
        json.dumps({"results": [{"result_id": "ares-missing", "dataset_id": "ards-missing"}]}),
        encoding="utf-8",
    )
    (project_dir / "reports" / "formal_meta_report.md").write_text(
        "# Formal Meta Analysis Report Draft\n\n- Current software status: testing / developer preview\n- forest_plot: missing / not generated\n",
        encoding="utf-8",
    )
    service = TraceabilityAuditService()

    audit = service.run_traceability_audit(project_dir)

    assert audit.passed
    assert "analysis_result_dataset_missing:ares-missing:ards-missing" in audit.warnings
    assert "reproducibility_package_missing" in audit.warnings
    assert any(warning.startswith("formal_report_missing_artifact:") for warning in audit.warnings)


def test_reproducibility_package_checker_detects_required_entries(tmp_path: Path) -> None:
    project = build_meta_analysis_e2e_project(tmp_path)
    service = TraceabilityAuditService()

    checks, warnings = service.check_reproducibility_package(project["project_dir"], project["paths"]["reproducibility_package"])

    assert warnings == []
    assert checks["complete"] is True
    with zipfile.ZipFile(project["paths"]["reproducibility_package"]) as archive:
        assert "software_version.json" in archive.namelist()


def test_artifact_lock_prevents_overwrite_and_creates_versioned_report(tmp_path: Path) -> None:
    project = build_meta_analysis_e2e_project(tmp_path)
    service = PublicationExportService()
    first_html = service.export_html_report(project["project_dir"])

    service.lock_formal_report(project["project_dir"])
    second_html = service.export_html_report(project["project_dir"])

    assert Path(first_html.output_path).exists()
    assert Path(second_html.output_path).exists()
    assert Path(first_html.output_path) != Path(second_html.output_path)
    assert "formal_report_locked_new_version_created" in second_html.warnings


def test_ai_suggestion_apply_records_safety_note_without_overwriting_formal_data(tmp_path: Path) -> None:
    project_dir = tmp_path / "ai-project"
    (project_dir / "extraction").mkdir(parents=True)
    original_payload = json.dumps({"records": [{"extraction_id": "extr-1", "record_id": "rec-1"}]})
    (project_dir / "extraction" / "extraction_records.json").write_text(original_payload, encoding="utf-8")
    task_center = TaskCenter(tmp_path / "tasks.json")
    data_center = DataCenter(tmp_path / "data.json")
    service = AISuggestionService(task_center=task_center, data_center=data_center)

    suggestion = service.create_ai_suggestion(
        project_dir,
        project_id="ai-project",
        target_type="extraction_candidate",
        target_id="extr-1",
        suggestion_type="extraction_candidate",
        suggested_value={"outcome_name": "Mortality"},
        rationale="Mock candidate only.",
        confidence=0.6,
    )
    service.accept_ai_suggestion(project_dir, suggestion.suggestion_id)
    applied = service.apply_accepted_suggestion(project_dir, suggestion.suggestion_id)

    assert applied.success
    assert (project_dir / "extraction" / "extraction_records.json").read_text(encoding="utf-8") == original_payload
    applications = json.loads(Path(applied.output_path).read_text(encoding="utf-8"))["applications"]
    assert "formal screening/extraction/analysis artifacts are not overwritten" in applications[0]["safety_note"]

