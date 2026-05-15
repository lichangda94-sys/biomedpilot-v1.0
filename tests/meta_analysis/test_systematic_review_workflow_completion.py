from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.quality.tool_registry import get_quality_tool
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder
from app.meta_analysis.services.fulltext_service import FullTextService
from app.meta_analysis.services.quality_service import QualityAssessmentService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def test_fulltext_attach_registry_decision_and_exclusion_report(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(b"%PDF-1.4 test")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = FullTextService(task_center=task_center, data_center=data_center)

    attached = service.attach_fulltext(project_dir, "rec-1", str(source_pdf))
    reloaded = service.load_fulltext_registry(project_dir)
    decision = service.save_fulltext_decision(
        project_dir,
        record_id="rec-1",
        reviewer_id="rev-1",
        decision="exclude",
        exclusion_reason="wrong outcome",
    )
    report_path = service.export_full_text_exclusion_report(project_dir)

    assert Path(attached.pdf_path).exists()
    assert str(project_dir / "fulltext") in attached.pdf_path
    assert reloaded[0].record_id == "rec-1"
    assert decision.exclusion_reason == "wrong outcome"
    assert "wrong outcome" in report_path.read_text(encoding="utf-8")
    assert "wrong population" in service.exclusion_reasons()
    task_types = {task.task_type for task in task_center.list_tasks()}
    assert TaskType.FULLTEXT_ATTACH in task_types
    assert TaskType.FULLTEXT_SCREENING_DECISION in task_types
    assert TaskType.FULLTEXT_EXCLUSION_EXPORT in task_types
    data_types = {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert {"fulltext_registry", "fulltext_screening_decisions", "full_text_exclusion_report"} <= data_types


def test_quality_registry_assessment_and_table_export(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = QualityAssessmentService(task_center=task_center, data_center=data_center)

    assert get_quality_tool("NOS") is not None
    assert get_quality_tool("QUADAS-2") is not None
    assert get_quality_tool("RoB2 simplified") is not None
    assessment = service.create_quality_assessment(
        project_id=project_dir.name,
        study_id="study-1",
        record_id="rec-1",
        tool_name="NOS",
        domains={"selection": "low risk", "comparability": "moderate risk"},
        overall_judgement="moderate risk",
        reviewer_id="rev-1",
    )
    service.save_quality_assessment(project_dir, assessment)
    table_path = service.export_quality_table_csv(project_dir)

    assert service.load_quality_assessments(project_dir)[0].assessment_id == assessment.assessment_id
    assert service.summarize_quality_assessments(project_dir)["assessment_count"] == 1
    assert "moderate risk" in table_path.read_text(encoding="utf-8")
    task_types = {task.task_type for task in task_center.list_tasks()}
    assert TaskType.QUALITY_ASSESSMENT_SAVE in task_types
    assert TaskType.QUALITY_ASSESSMENT_EXPORT in task_types
    data_types = {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert {"quality_assessments", "quality_assessment_table"} <= data_types


def test_formal_report_references_fulltext_and_quality_outputs(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    (project_dir / "fulltext").mkdir(parents=True)
    (project_dir / "reports").mkdir(parents=True)
    (project_dir / "quality").mkdir(parents=True)
    (project_dir / "exports").mkdir(parents=True)
    (project_dir / "fulltext" / "fulltext_registry.json").write_text(json.dumps({"fulltext_files": []}), encoding="utf-8")
    (project_dir / "fulltext" / "fulltext_screening_decisions.json").write_text(json.dumps({"decisions": []}), encoding="utf-8")
    (project_dir / "reports" / "full_text_exclusion_report.csv").write_text("record_id,decision\n", encoding="utf-8")
    (project_dir / "quality" / "quality_assessments.json").write_text(json.dumps({"quality_assessments": []}), encoding="utf-8")
    (project_dir / "exports" / "quality_assessment_table.csv").write_text("assessment_id\n", encoding="utf-8")

    report_path = FormalMarkdownReportBuilder().build_formal_markdown_report(project_dir)
    text = report_path.read_text(encoding="utf-8")

    assert "Full-text registry" in text
    assert "Quality assessment summary" in text
    assert "quality_assessment_table.csv" not in text
    assert "报告正文不展示原始清单路径" in text
