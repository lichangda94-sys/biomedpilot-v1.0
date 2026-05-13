from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.workflow_dashboard_page import (
    RELEASE_STATUS_DEVELOPER_PREVIEW,
    WORKFLOW_STEP_DEFINITIONS,
    workflow_dashboard_state_from_project,
)
from app.meta_analysis.services.analysis_setup_service import AnalysisSetupService
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder, PRISMAService
from app.meta_analysis.services.internal_beta_sample_project_service import InternalBetaSampleProjectService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.shared.feature_availability import FeatureAvailabilityStatus, get_feature
from tests.meta_analysis.e2e_project_builder import build_meta_analysis_e2e_project


REPO_ROOT = Path(__file__).resolve().parents[2]
TREATMENT_SAMPLE = REPO_ROOT / "examples" / "meta_analysis_internal_beta_samples" / "treatment_effect_binary_or"
BIOMARKER_SAMPLE = REPO_ROOT / "examples" / "meta_analysis_internal_beta_samples" / "biomarker_prevalence_correlation"


def test_ab14_workflow_dashboard_preserves_fifteen_internal_beta_steps() -> None:
    titles = [str(item["title"]) for item in WORKFLOW_STEP_DEFINITIONS]

    assert titles == [
        "Project Setup",
        "Protocol / Research Question",
        "Literature Import",
        "Import Diagnostics",
        "Duplicate Review",
        "Criteria Builder",
        "Title / Abstract Screening",
        "Full-text / Attachment",
        "Extraction",
        "Quality Assessment",
        "Analysis-ready Dataset",
        "Meta-analysis Run",
        "Figures / Tables",
        "PRISMA / Report",
        "Reproducibility Package",
    ]
    empty_state = workflow_dashboard_state_from_project(REPO_ROOT / "project_storage" / "projects" / "empty-ab14")
    assert empty_state.status_label == RELEASE_STATUS_DEVELOPER_PREVIEW
    assert len(empty_state.steps) == 15
    assert all(step.release_status == RELEASE_STATUS_DEVELOPER_PREVIEW for step in empty_state.steps)


def test_ab14_internal_beta_sample_manifests_validate_and_match_walkthrough() -> None:
    service = InternalBetaSampleProjectService()

    samples = {sample.sample_id: sample for sample in service.list_sample_projects(REPO_ROOT)}
    assert {"treatment_effect_binary_or", "biomarker_prevalence_correlation"} <= set(samples)
    for sample_id in ("treatment_effect_binary_or", "biomarker_prevalence_correlation"):
        result = service.validate_sample_project(REPO_ROOT, sample_id)
        assert result.valid, result.errors
        assert result.warnings == []

    walkthrough = (REPO_ROOT / "docs" / "meta_sample_project_walkthrough.md").read_text(encoding="utf-8")
    assert str(TREATMENT_SAMPLE.relative_to(REPO_ROOT) / "inputs" / "literature.csv") in walkthrough
    assert str(BIOMARKER_SAMPLE.relative_to(REPO_ROOT) / "inputs" / "literature.csv") in walkthrough


def test_ab14_treatment_sample_generates_acceptance_artifacts(tmp_path: Path) -> None:
    result = build_meta_analysis_e2e_project(
        tmp_path,
        project_id="ab14-treatment-sample",
        intervention_or_exposure="Treatment",
        comparator="Placebo",
        outcome_name="Mortality",
        source_location="AB13 treatment sample seeded extraction",
        seeded_note="AB14 validation-only seeded data; not for clinical interpretation.",
    )
    project_dir = result["project_dir"]

    setup = AnalysisSetupService()
    plan = setup.create_plan(
        project_dir,
        profile_type="TREATMENT_EFFECT_META",
        outcome_name="Mortality",
        effect_measure="OR",
        model="random",
        zero_event_correction="continuity_0.5",
    )
    summary = setup.run_analysis_from_plan(project_dir, plan)
    assert summary.success is True
    FormalMarkdownReportBuilder().build_formal_markdown_report(project_dir)
    MetaProjectContractService().write_project_manifests(project_dir)

    expected_artifacts = (
        "analysis/analysis_plan.json",
        "analysis/analysis_ready_dataset.json",
        "analysis/analysis_ready_datasets.json",
        "analysis/analysis_result.json",
        "analysis/analysis_results.json",
        "analysis/applicability_warnings.json",
        "reports/prisma_summary.json",
        "reports/prisma_flow.md",
        "reports/prisma_flow.svg",
        "reports/formal_meta_report.md",
    )
    for relative in expected_artifacts:
        assert (project_dir / relative).exists(), relative
    assert list((project_dir / "exports").glob("reproducibility_package_*.zip"))

    prisma_summary = json.loads((project_dir / "reports" / "prisma_summary.json").read_text(encoding="utf-8"))
    source_types = {item["source_type"] for item in prisma_summary["source_references"]}
    assert {"ImportBatch", "ScreeningRecord", "ExtractionRecord"} <= source_types
    assert any("full-text workflow incomplete" in note for note in prisma_summary["notes"])

    report_text = (project_dir / "reports" / "formal_meta_report.md").read_text(encoding="utf-8")
    assert "Developer Preview / testing" in report_text
    assert "not a production journal submission" in report_text
    assert "analysis/applicability_warnings.json" not in report_text
    assert "统计分析结果尚未作为正式可发表结论生成" in report_text

    dashboard = workflow_dashboard_state_from_project(project_dir)
    step_status = {step.title: step.workflow_status for step in dashboard.steps}
    assert step_status["Literature Import"] in {"Completed", "Needs review"}
    assert step_status["Extraction"] == "Completed"
    assert step_status["Meta-analysis Run"] in {"Completed", "Needs review"}
    assert step_status["PRISMA / Report"] in {"Completed", "Needs review"}


def test_ab14_missing_artifacts_remain_warning_based(tmp_path: Path) -> None:
    project_dir = tmp_path / "missing-artifacts"
    project_dir.mkdir()

    contract = MetaProjectContractService().validate_project_contract(project_dir)
    dashboard = workflow_dashboard_state_from_project(project_dir)

    assert contract.valid is True
    assert any(item.startswith("manifest_missing:") for item in contract.warnings)
    assert dashboard.manifest_status == "Needs review"
    assert dashboard.not_started_count == 15


def test_ab14_meta_feature_availability_remains_testing_not_production() -> None:
    feature_ids = (
        "meta-literature-import",
        "meta-dedup-prep",
        "meta-duplicate-review",
        "meta-screening",
        "meta-extraction",
        "meta-analysis",
        "meta-reporting",
        "meta-ai-assisted-review",
    )

    for feature_id in feature_ids:
        feature = get_feature(feature_id)
        assert feature is not None
        assert feature.status is FeatureAvailabilityStatus.TESTING
        text = f"{feature.description} {feature.next_step}".lower()
        assert "production-ready" not in text
        assert "自动下载 pdf" not in text
        assert "ocr" not in text
