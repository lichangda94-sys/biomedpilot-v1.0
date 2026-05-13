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
    status_style,
    status_styles,
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
    assert status_style("Ready").label_zh == "已就绪"
    assert status_style("not-ready").label_zh == "未就绪"
    assert status_style("unknown").label_zh == "未就绪"


def test_shared_theme_has_foundation_for_future_components() -> None:
    assert BioMedPilotTypography.PAGE_TITLE >= BioMedPilotTypography.CARD_TITLE
    assert BioMedPilotRadii.CARD == 8
    assert BioMedPilotButtonRoles.PRIMARY_ACTION == "primary_action"
