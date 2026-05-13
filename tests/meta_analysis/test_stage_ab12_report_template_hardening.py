from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder, PRISMAService
from app.meta_analysis.services.publication_export_service import PublicationExportService
from app.meta_analysis.services.report_manifest_service import ReportManifestService


def test_internal_beta_formal_report_contains_hardened_sections(tmp_path: Path) -> None:
    project_dir = seed_report_project(tmp_path)
    builder = FormalMarkdownReportBuilder()

    report_path = builder.build_formal_markdown_report(project_dir)
    report_text = report_path.read_text(encoding="utf-8")

    for heading in (
        "## Protocol summary",
        "## Study selection",
        "## PRISMA summary",
        "## Quality assessment",
        "## Statistical methods",
        "## Figures",
        "## Tables",
        "## Applicability warnings",
        "## Reproducibility notes",
    ):
        assert heading in report_text
    assert "Developer Preview / testing" in report_text
    assert "not a production journal submission" in report_text
    assert "formal PRISMA 2020" in (project_dir / "reports" / "prisma_flow.svg").read_text(encoding="utf-8")


def test_report_manifest_lists_protocol_analysis_and_applicability_sources(tmp_path: Path) -> None:
    project_dir = seed_report_project(tmp_path)
    FormalMarkdownReportBuilder().build_formal_markdown_report(project_dir)

    payload = json.loads((project_dir / "reports" / "report_manifest.json").read_text(encoding="utf-8"))
    sections = {section["section_id"]: section for section in payload["sections"]}

    assert "protocol" in sections
    assert "criteria/criteria_summary.md" in sections["protocol"]["source_artifacts"]
    assert "analysis/applicability_warnings.json" in sections["analysis"]["source_artifacts"]
    assert sections["applicability"]["source_artifacts"] == ["analysis/applicability_warnings.json"]
    assert "reports/prisma_flow.svg" in sections["prisma"]["source_artifacts"]


def test_html_and_docx_exports_share_hardened_markdown_content(tmp_path: Path) -> None:
    project_dir = seed_report_project(tmp_path)
    service = PublicationExportService()

    html = Path(service.export_html_report(project_dir).output_path)
    docx = Path(service.export_word_report(project_dir).output_path)

    html_text = html.read_text(encoding="utf-8")
    assert "Protocol summary" in html_text
    assert "Applicability warnings" in html_text
    with ZipFile(docx) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8")
    assert "Protocol summary" in document_xml
    assert "Statistical methods" in document_xml


def test_pdf_strategy_remains_placeholder_not_formal_pdf(tmp_path: Path) -> None:
    project_dir = seed_report_project(tmp_path)
    service = PublicationExportService()

    placeholder = Path(service.export_pdf_report_placeholder(project_dir).output_path)
    manifest = ReportManifestService().build_report_manifest(project_dir)

    assert placeholder.exists()
    assert "pdf_export_not_implemented" in placeholder.read_text(encoding="utf-8")
    pdf_section = next(section for section in manifest["sections"] if section["section_id"] == "pdf_strategy")
    assert pdf_section["status"] == "placeholder"
    assert "pdf_export_not_implemented" in pdf_section["warnings"]


def seed_report_project(tmp_path: Path) -> Path:
    project_dir = tmp_path / "meta-project"
    for name in ("protocol", "criteria", "literature", "deduplication", "screening", "fulltext", "extraction", "quality", "analysis", "figures", "exports", "reports"):
        (project_dir / name).mkdir(parents=True)
    write_json(project_dir / "project.json", {"project_id": "meta-project"})
    write_json(project_dir / "protocol" / "review_protocol.json", {"project_title": "Testing protocol"})
    (project_dir / "protocol" / "search_strategy_preview.md").write_text("# Search Strategy\n", encoding="utf-8")
    (project_dir / "criteria" / "criteria_summary.md").write_text("# Criteria\n", encoding="utf-8")
    write_json(project_dir / "literature" / "literature_records.json", {"records": [{"record_id": "rec-1"}, {"record_id": "rec-2"}]})
    write_json(project_dir / "deduplication" / "duplicate_candidate_groups.json", {"duplicate_candidate_groups": []})
    write_json(project_dir / "deduplication" / "deduplicated_literature.json", {"deduplicated_records": [{"record_id": "rec-1"}, {"record_id": "rec-2"}]})
    write_json(project_dir / "screening" / "screening_decisions.json", {"screening_records": [{"record_id": "rec-1", "decision": "included"}]})
    write_json(project_dir / "fulltext" / "fulltext_registry.json", {"records": []})
    write_json(project_dir / "fulltext" / "fulltext_screening_decisions.json", {"decisions": []})
    (project_dir / "reports" / "full_text_exclusion_report.csv").write_text("record_id,reason\n", encoding="utf-8")
    write_json(project_dir / "extraction" / "extraction_records.json", {"records": [{"extraction_id": "extr-1"}]})
    write_json(project_dir / "quality" / "quality_assessments.json", {"assessments": []})
    (project_dir / "exports" / "quality_assessment_table.csv").write_text("study_id,overall\n", encoding="utf-8")
    write_json(project_dir / "analysis" / "analysis_plan.json", {"plan": {"effect_measure": "OR"}})
    write_json(project_dir / "analysis" / "analysis_ready_datasets.json", {"datasets": [{"dataset_id": "ards-1"}]})
    write_json(project_dir / "analysis" / "analysis_results.json", {"results": [{"result_id": "ares-1"}]})
    write_json(project_dir / "analysis" / "applicability_warnings.json", {"warnings": ["developer_preview"]})
    write_json(project_dir / "figures" / "figure_artifacts.json", {"artifacts": []})
    (project_dir / "figures" / "forest_plot_ares-1.png").write_bytes(b"png")
    (project_dir / "figures" / "funnel_plot_ares-1.png").write_bytes(b"png")
    (project_dir / "exports" / "analysis_result_table_ares-1.csv").write_text("row_type,study_id\npooled,pooled\n", encoding="utf-8")
    service = PRISMAService()
    summary = service.collect_prisma_numbers(project_dir)
    service.save_prisma_flow_summary(project_dir, summary)
    service.export_prisma_flow_markdown(project_dir, summary)
    service.export_simplified_prisma_flow(project_dir, summary)
    return project_dir


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
