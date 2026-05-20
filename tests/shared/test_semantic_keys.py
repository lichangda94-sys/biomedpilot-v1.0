from __future__ import annotations

import pytest

from app.shared.semantic_keys import (
    AnalysisStatusKey,
    BrandKey,
    FeatureStatusKey,
    NavKey,
    ReportStatusKey,
    ResourceStatusKey,
    ResultSemanticKey,
    SemanticKeyGroup,
    get_semantic_key,
    keys_for_group,
    semantic_key_values,
)


def test_key_registry_contains_required_brand_and_nav_keys() -> None:
    values = set(semantic_key_values())

    assert {
        "brand.primary",
        "brand.secondary",
        "nav.dashboard",
        "nav.bioinformatics",
        "nav.meta_analysis",
        "nav.labtools",
        "nav.settings",
    } <= values
    assert get_semantic_key(BrandKey.PRIMARY).default_label == "萤火虫 / Firefly"
    assert get_semantic_key(BrandKey.SECONDARY).default_label == "BioMedPilot / 医研智析"
    assert get_semantic_key(NavKey.LABTOOLS).group is SemanticKeyGroup.NAV


def test_semantic_status_enums_use_stable_full_keys() -> None:
    assert FeatureStatusKey.TESTING.value == "feature.status.testing"
    assert FeatureStatusKey.PLANNED.value == "feature.status.planned"
    assert FeatureStatusKey.SHELL_ONLY.value == "feature.status.shell_only"
    assert FeatureStatusKey.DEVELOPER_PREVIEW.value == "feature.status.developer_preview"
    assert FeatureStatusKey.BLOCKED.value == "feature.status.blocked"

    assert ResourceStatusKey.AVAILABLE.value == "resource.status.available"
    assert ResourceStatusKey.NOT_CONFIGURED.value == "resource.status.not_configured"
    assert ResourceStatusKey.PLANNED.value == "resource.status.planned"
    assert ResourceStatusKey.FAILED.value == "resource.status.failed"

    assert AnalysisStatusKey.PREFLIGHT_ONLY.value == "analysis.status.preflight_only"
    assert AnalysisStatusKey.TESTING_LEVEL.value == "analysis.status.testing_level"
    assert AnalysisStatusKey.BLOCKED.value == "analysis.status.blocked"

    assert ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value == "result.semantic.imported_external_result"
    assert ResultSemanticKey.FORMAL_COMPUTED_RESULT.value == "result.semantic.formal_computed_result"
    assert ReportStatusKey.DRAFT.value == "report.status.draft"
    assert ReportStatusKey.TESTING_SUMMARY.value == "report.status.testing_summary"
    assert ReportStatusKey.REPORT_READY_FUTURE.value == "report.status.report_ready_future"


def test_registry_groups_cover_brand_nav_module_status_report_export() -> None:
    grouped = {group: keys_for_group(group) for group in SemanticKeyGroup}

    assert all(grouped[group] for group in SemanticKeyGroup)
    assert {entry.key for entry in grouped[SemanticKeyGroup.REPORT]} >= {
        "report.status.draft",
        "report.status.testing_summary",
        "report.status.report_ready_future",
        "report.export_panel",
    }
    assert {entry.key for entry in grouped[SemanticKeyGroup.EXPORT]} >= {
        "export.format.markdown",
        "export.format.docx",
        "export.format.csv",
        "export.format.xlsx",
    }


def test_unknown_semantic_key_fails_closed() -> None:
    with pytest.raises(KeyError):
        get_semantic_key("language.switch.enabled")
