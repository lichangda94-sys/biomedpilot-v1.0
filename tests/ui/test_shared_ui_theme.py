from __future__ import annotations

from app.shared.ui.theme import (
    BioMedPilotButtonRoles,
    BioMedPilotColors,
    BioMedPilotRadii,
    BioMedPilotSpacing,
    BioMedPilotStatusColors,
    BioMedPilotTypography,
    as_legacy_color_dict,
    as_legacy_spacing_dict,
    button_qss,
    danger_button_qss,
    diagnostic_card_qss,
    empty_result_card_qss,
    error_text_qss,
    page_title_qss,
    parameter_group_card_qss,
    primary_button_qss,
    result_summary_card_qss,
    shell_sidebar_qss,
    status_badge_qss,
    status_style,
    status_styles,
    surface_card_qss,
    tool_input_card_qss,
    warning_text_qss,
)
from app.ui_style_tokens import COLORS, SPACING


def test_shared_ui_palette_exposes_governance_colors() -> None:
    assert BioMedPilotColors.PRIMARY_NAVY == "#12324A"
    assert BioMedPilotColors.ACCENT_TEAL == "#1BAE9F"
    assert BioMedPilotColors.BACKGROUND_LIGHT == "#F5F7F9"
    assert BioMedPilotColors.SURFACE_WHITE == "#FFFFFF"


def test_legacy_style_token_entry_uses_shared_theme_values() -> None:
    legacy_colors = as_legacy_color_dict()
    legacy_spacing = as_legacy_spacing_dict()

    assert COLORS["bio"] == BioMedPilotColors.PRIMARY_NAVY
    assert COLORS["bio_accent"] == BioMedPilotColors.ACCENT_TEAL
    assert COLORS["background"] == legacy_colors["background"]
    assert SPACING["md"] == legacy_spacing["md"] == BioMedPilotSpacing.MD


def test_status_styles_cover_cross_module_status_language() -> None:
    styles = status_styles()

    assert styles["ready"] == BioMedPilotStatusColors.READY
    assert styles["pending"] == BioMedPilotStatusColors.NOT_READY
    assert styles["analysis_ready"] == BioMedPilotStatusColors.READY
    assert styles["developer_preview"] == BioMedPilotStatusColors.TESTING
    assert status_style("Ready").label_zh == "已就绪"
    assert status_style("not-ready").label_zh == "未就绪"
    assert status_style("testing-level").label_zh == "测试中"
    assert status_style("unknown").label_zh == "未就绪"


def test_shared_theme_has_foundation_for_future_components() -> None:
    assert BioMedPilotTypography.PAGE_TITLE >= BioMedPilotTypography.CARD_TITLE
    assert BioMedPilotRadii.CARD == 8
    assert BioMedPilotButtonRoles.PRIMARY_ACTION == "primary_action"


def test_shared_qss_helpers_generate_token_backed_styles() -> None:
    card_qss = surface_card_qss("QFrame#entryCard")
    sidebar_qss = shell_sidebar_qss()

    assert "QFrame#entryCard" in card_qss
    assert BioMedPilotColors.BORDER_MEDIUM in card_qss
    assert BioMedPilotColors.SURFACE_WHITE in card_qss
    assert BioMedPilotColors.SURFACE_MUTED in sidebar_qss
    assert BioMedPilotColors.BIO_SOFT in sidebar_qss
    assert str(BioMedPilotRadii.CARD) in card_qss
    assert "font-weight: 700" in page_title_qss()
    assert BioMedPilotColors.STATUS_ERROR in error_text_qss()
    assert BioMedPilotColors.STATUS_WARNING in warning_text_qss()


def test_status_badge_and_button_helpers_generate_role_styles() -> None:
    ready_badge = status_badge_qss("analysis-ready")
    primary_button = primary_button_qss()
    danger_button = danger_button_qss()

    assert BioMedPilotColors.STATUS_READY in ready_badge
    assert BioMedPilotColors.TEAL_SOFT in ready_badge
    assert BioMedPilotColors.PRIMARY_NAVY in primary_button
    assert BioMedPilotColors.TEXT_INVERSE in primary_button
    assert BioMedPilotColors.STATUS_ERROR in danger_button
    assert button_qss("primary_action") == primary_button
    assert button_qss("destructive_action") == danger_button
    assert BioMedPilotColors.WARNING_SOFT in diagnostic_card_qss()


def test_tool_page_card_helpers_generate_token_backed_styles() -> None:
    input_card = tool_input_card_qss("QFrame#toolInput")
    parameter_card = parameter_group_card_qss("QFrame#parameterGroup")
    result_card = result_summary_card_qss("QFrame#resultSummary")
    empty_card = empty_result_card_qss("QFrame#emptyResult")

    assert "QFrame#toolInput" in input_card
    assert BioMedPilotColors.SURFACE_WHITE in input_card
    assert BioMedPilotColors.BORDER_MEDIUM in input_card
    assert "QFrame#parameterGroup" in parameter_card
    assert BioMedPilotColors.BORDER_SUBTLE in parameter_card
    assert "QFrame#resultSummary" in result_card
    assert BioMedPilotColors.TEAL_SOFT in result_card
    assert BioMedPilotColors.TEAL_BORDER in result_card
    assert "QFrame#emptyResult" in empty_card
    assert "dashed" in empty_card
    assert BioMedPilotColors.SURFACE_MUTED in empty_card
