from __future__ import annotations

from pathlib import Path

from app.meta_analysis.services.internal_beta_sample_project_service import InternalBetaSampleProjectService


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_internal_beta_sample_project_pack_lists_required_samples() -> None:
    service = InternalBetaSampleProjectService()

    samples = service.list_sample_projects(REPO_ROOT)
    sample_ids = {sample.sample_id for sample in samples}

    assert {"treatment_effect_binary_or", "biomarker_prevalence_correlation"} <= sample_ids
    treatment = next(sample for sample in samples if sample.sample_id == "treatment_effect_binary_or")
    biomarker = next(sample for sample in samples if sample.sample_id == "biomarker_prevalence_correlation")
    assert treatment.expected_import_count == 3
    assert treatment.expected_duplicate_count == 1
    assert treatment.expected_extraction["effect_measure"] == "OR"
    assert biomarker.expected_analysis_result["correlation_method"] == "Fisher z transform"


def test_internal_beta_sample_project_pack_validates_source_inputs_only() -> None:
    service = InternalBetaSampleProjectService()

    treatment = service.validate_sample_project(REPO_ROOT, "treatment_effect_binary_or")
    biomarker = service.validate_sample_project(REPO_ROOT, "biomarker_prevalence_correlation")

    assert treatment.valid is True
    assert treatment.errors == []
    assert biomarker.valid is True
    assert biomarker.errors == []


def test_missing_internal_beta_sample_reports_clear_error() -> None:
    service = InternalBetaSampleProjectService()

    result = service.validate_sample_project(REPO_ROOT, "missing-sample")

    assert result.valid is False
    assert result.errors == ["sample_project_missing"]


def test_internal_beta_sample_docs_exist_and_mark_developer_preview() -> None:
    walkthrough = REPO_ROOT / "docs" / "meta_internal_beta_walkthrough.md"
    sample_walkthrough = REPO_ROOT / "docs" / "meta_sample_project_walkthrough.md"
    known_limitations = REPO_ROOT / "docs" / "meta_known_limitations.md"

    for path in (walkthrough, sample_walkthrough, known_limitations):
        assert path.exists()
    text = walkthrough.read_text(encoding="utf-8")
    assert "Developer Preview / testing" in text
    assert "treatment_effect_binary_or" in text
    assert "biomarker_prevalence_correlation" in text
    assert "automatic PDF download" in text
    assert "AB13 internal beta sample projects" in known_limitations.read_text(encoding="utf-8")
