from __future__ import annotations

import json
import zipfile
from pathlib import Path

from app.meta_analysis.services.publication_export_service import PublicationExportService
from app.meta_analysis.services.report_manifest_service import ReportManifestService
from tests.meta_analysis.e2e_project_builder import build_meta_analysis_e2e_project


def test_report_manifest_sections_sources_and_missing_warnings(tmp_path: Path) -> None:
    project = build_meta_analysis_e2e_project(tmp_path)
    manifest_path = ReportManifestService().save_report_manifest(project["project_dir"])

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["software_status"] == "Developer Preview / testing"
    sections = {section["section_id"]: section for section in payload["sections"]}
    assert sections["analysis"]["status"] == "available"
    assert "analysis/analysis_results.json" in sections["analysis"]["source_artifacts"]
    assert sections["pdf_strategy"]["status"] == "placeholder"
    assert "pdf_export_not_implemented" in payload["warnings"]


def test_report_manifest_records_missing_artifacts(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    (project_dir / "reports").mkdir(parents=True)
    payload = ReportManifestService().build_report_manifest(project_dir)

    assert any(warning.startswith("report_section_source_missing:analysis") for warning in payload["warnings"])


def test_markdown_html_docx_and_packages_align_with_report_manifest(tmp_path: Path) -> None:
    project = build_meta_analysis_e2e_project(tmp_path)
    service = PublicationExportService()
    pdf = service.export_pdf_report_placeholder(project["project_dir"])
    html = service.export_html_report(project["project_dir"])
    word = service.export_word_report(project["project_dir"])
    supplementary = service.export_supplementary_exports(project["project_dir"])
    figure_package = service.export_figure_package(project["project_dir"])
    report_manifest = project["project_dir"] / "reports" / "report_manifest.json"

    assert not pdf.success
    assert "pdf_export_not_implemented" in pdf.warnings
    assert Path(html.output_path).exists()
    assert Path(word.output_path).exists()
    assert Path(supplementary.output_path, "manifest.json").exists()
    with zipfile.ZipFile(Path(figure_package.output_path)) as archive:
        assert any(name.startswith("figures/") for name in archive.namelist())
    assert report_manifest.exists()
