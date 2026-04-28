from __future__ import annotations

from app.meta_analysis.pages.analysis_page import initial_analysis_state
from app.meta_analysis.pages.extraction_page import initial_extraction_state
from app.meta_analysis.pages.quality_page import initial_quality_state
from app.meta_analysis.pages.reporting_page import initial_reporting_state
from app.meta_analysis.services.internal_beta_rc_service import InternalBetaRCAuditService


def test_ui_polish_audit_confirms_testing_guidance_and_placeholders() -> None:
    result = InternalBetaRCAuditService().build_ui_polish_audit()

    assert result.status in {"pass", "warn"}
    assert not result.blockers
    assert {check.check_id for check in result.checks} >= {
        "analysis_distinctions",
        "reporting_distinctions",
        "placeholder_visibility",
    }


def test_extraction_quality_analysis_reporting_states_are_beta_readable() -> None:
    extraction = initial_extraction_state()
    quality = initial_quality_state()
    analysis = initial_analysis_state()
    reporting = initial_reporting_state()

    assert "testing" in extraction.description.lower()
    assert "field_name" in extraction.field_error_targets
    assert "completeness_score" in extraction.completeness_summary_fields
    assert quality.domain_note_support
    assert "不强制" in quality.overall_judgement_suggestion
    assert "preflight" in analysis.input_summary.lower()
    assert "analysis_result" in analysis.output_summary
    assert "PDF" in reporting.warning_summary
    assert "missing / not generated" in reporting.empty_state

