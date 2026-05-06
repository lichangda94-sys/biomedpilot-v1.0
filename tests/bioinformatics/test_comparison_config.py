from __future__ import annotations

from app.bioinformatics.comparison_config import (
    build_geo_comparison_config_text,
    comparison_sample_match_status,
    group_label_zh,
    parse_comparison_config_text,
)
from app.bioinformatics.services.geo_metadata_profile_service import (
    GeoCandidateComparison,
    GeoMetadataProfile,
    GeoSampleGroupAssignment,
)


def _profile() -> GeoMetadataProfile:
    assignments = (
        GeoSampleGroupAssignment("GSM1", "normal", "pathological_diagnostic", "diagnosis: normal", "high"),
        GeoSampleGroupAssignment("GSM2", "normal", "pathological_diagnostic", "diagnosis: normal", "high"),
        GeoSampleGroupAssignment("GSM3", "tumor", "pathological_diagnostic", "diagnosis: tumor", "high"),
        GeoSampleGroupAssignment("GSM4", "tumor", "pathological_diagnostic", "diagnosis: tumor", "high"),
    )
    return GeoMetadataProfile(
        accession="GSETEST",
        candidate_comparisons=(
            GeoCandidateComparison(
                comparison_id="pathological_diagnostic:tumor_vs_normal",
                label="tumor vs normal",
                control_group="normal",
                case_group="tumor",
                group_sizes={"normal": 2, "tumor": 2},
                sample_assignments=assignments,
                confidence="high",
            ),
        ),
    )


def test_geo_comparison_config_builds_sample_assignment_section() -> None:
    text = build_geo_comparison_config_text(_profile())
    config = parse_comparison_config_text(text)

    assert config.case_group == "tumor"
    assert config.control_group == "normal"
    assert config.case_label_zh == "肿瘤组"
    assert config.control_label_zh == "正常/对照组"
    assert config.group_assignments == {
        "GSM1": "normal",
        "GSM2": "normal",
        "GSM3": "tumor",
        "GSM4": "tumor",
    }


def test_geo_comparison_config_allows_swap_remove_and_adjust_sample() -> None:
    text = build_geo_comparison_config_text(
        _profile(),
        case_group="normal",
        control_group="tumor",
        included_sample_ids=["GSM1", "GSM3", "GSM4"],
        assignment_overrides={"GSM4": "normal"},
    )
    config = parse_comparison_config_text(text)

    assert config.case_group == "normal"
    assert config.control_group == "tumor"
    assert "GSM2" not in config.group_assignments
    assert config.group_assignments["GSM4"] == "normal"
    assert config.group_sizes == {"normal": 2, "tumor": 1}


def test_comparison_sample_match_status_reports_mismatch_layers() -> None:
    config = parse_comparison_config_text(build_geo_comparison_config_text(_profile()))
    status = comparison_sample_match_status(config, ["GSM1", "GSM2", "GSM5"])

    assert status["expression_sample_count"] == 3
    assert status["metadata_sample_count"] == 4
    assert status["matched_sample_count"] == 2
    assert status["sample_id_match_status"] == "partial"
    assert "GSM5" in status["unmatched_expression_samples"]
    assert "GSM3" in status["unmatched_metadata_samples"]


def test_group_label_zh_uses_user_facing_terms() -> None:
    assert group_label_zh("tumor") == "肿瘤组"
    assert group_label_zh("adjacent normal") == "正常/对照组"
    assert group_label_zh("resistant") == "耐药组"
