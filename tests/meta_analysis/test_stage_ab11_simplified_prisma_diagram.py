from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.reporting_page import initial_reporting_state
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder, PRISMAService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.meta_analysis.services.report_manifest_service import ReportManifestService
from app.shared.data_center.service import DataCenter


def test_simplified_prisma_flow_outputs_json_markdown_and_svg(tmp_path: Path) -> None:
    project_dir = seed_prisma_project(tmp_path)
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    service = PRISMAService(data_center=data_center)

    summary = service.collect_prisma_numbers(project_dir)
    old_json = service.save_prisma_flow_summary(project_dir, summary)
    old_md = service.export_prisma_flow_markdown(project_dir, summary)
    outputs = service.export_simplified_prisma_flow(project_dir, summary)

    assert old_json.exists()
    assert old_md.exists()
    assert outputs["summary_json"] == project_dir / "reports" / "prisma_summary.json"
    assert outputs["flow_markdown"] == project_dir / "reports" / "prisma_flow.md"
    assert outputs["flow_svg"] == project_dir / "reports" / "prisma_flow.svg"
    assert "Simplified PRISMA Flow (Testing)" in outputs["flow_markdown"].read_text(encoding="utf-8")
    svg = outputs["flow_svg"].read_text(encoding="utf-8")
    assert "<svg" in svg
    assert "not formal PRISMA 2020" in svg
    assert any(asset.data_type == "simplified_prisma_flow" for asset in data_center.list_assets(project_dir.name))


def test_prisma_manifest_and_project_contract_include_simplified_flow(tmp_path: Path) -> None:
    project_dir = seed_prisma_project(tmp_path)
    service = PRISMAService()
    summary = service.collect_prisma_numbers(project_dir)
    service.save_prisma_flow_summary(project_dir, summary)
    service.export_prisma_flow_markdown(project_dir, summary)
    service.export_simplified_prisma_flow(project_dir, summary)

    report_manifest = ReportManifestService().save_report_manifest(project_dir)
    MetaProjectContractService().write_project_manifests(project_dir)

    report_payload = json.loads(report_manifest.read_text(encoding="utf-8"))
    prisma_section = next(section for section in report_payload["sections"] if section["section_id"] == "prisma")
    assert prisma_section["status"] == "available"
    assert "reports/prisma_flow.svg" in prisma_section["source_artifacts"]
    artifact_manifest = json.loads((project_dir / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert any(item["artifact_type"] == "prisma_flow_svg" for item in artifact_manifest["artifacts"])


def test_formal_report_builder_generates_simplified_prisma_flow_when_missing(tmp_path: Path) -> None:
    project_dir = seed_prisma_project(tmp_path)
    builder = FormalMarkdownReportBuilder()

    builder.build_formal_markdown_report(project_dir)

    assert (project_dir / "reports" / "prisma_flow.svg").exists()
    assert (project_dir / "reports" / "prisma_flow.md").exists()
    manifest_payload = json.loads((project_dir / "reports" / "report_manifest.json").read_text(encoding="utf-8"))
    prisma_section = next(section for section in manifest_payload["sections"] if section["section_id"] == "prisma")
    assert "reports/prisma_flow.svg" in prisma_section["source_artifacts"]


def test_reporting_page_state_mentions_simplified_testing_prisma_diagram() -> None:
    state = initial_reporting_state()

    assert "simplified_prisma_flow_svg" in state.prisma_summary_fields
    assert any("简化 PRISMA SVG" in item for item in state.testing_limitations)


def seed_prisma_project(tmp_path: Path) -> Path:
    project_dir = tmp_path / "meta-project"
    (project_dir / "literature").mkdir(parents=True)
    (project_dir / "deduplication").mkdir(parents=True)
    (project_dir / "screening").mkdir(parents=True)
    write_json(project_dir / "literature" / "literature_records.json", {"records": [{"record_id": "rec-1"}, {"record_id": "rec-2"}, {"record_id": "rec-3"}]})
    write_json(project_dir / "deduplication" / "deduplicated_literature.json", {"deduplicated_records": [{"record_id": "rec-1"}, {"record_id": "rec-2"}]})
    write_json(
        project_dir / "screening" / "screening_decisions.json",
        {
            "screening_records": [
                {"record_id": "rec-1", "decision": "included"},
                {"record_id": "rec-2", "decision": "excluded"},
            ]
        },
    )
    return project_dir


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")
