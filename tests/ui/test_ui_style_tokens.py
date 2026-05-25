from __future__ import annotations

from app.ui_style_tokens import (
    BUTTON_TOKENS,
    COLORS,
    RADIUS,
    STATUS_TOKENS,
    THEME_PALETTE,
    UIStatusKey,
    button_stylesheet,
    get_button_token,
    get_status_token,
    global_app_stylesheet,
    status_chip_stylesheet,
)


def test_theme_palette_uses_shared_color_tokens() -> None:
    assert THEME_PALETTE["window"] == COLORS["background"]
    assert THEME_PALETTE["window_text"] == COLORS["text"]
    assert THEME_PALETTE["base"] == COLORS["surface"]
    assert THEME_PALETTE["button"] == COLORS["surface"]
    assert THEME_PALETTE["highlight"] == COLORS["focus"]
    assert COLORS["background"] in global_app_stylesheet()
    assert COLORS["text"] in global_app_stylesheet()


def test_status_tokens_cover_rebuild_semantics() -> None:
    required = {
        "developer_preview",
        "testing",
        "planned",
        "shell_only",
        "preflight_only",
        "blocked",
        "disabled",
        "available",
        "not_configured",
        "missing",
        "failed",
        "draft",
        "adapter_needed",
        "report_disabled",
        "export_disabled",
        "report_ready",
    }
    assert required <= set(STATUS_TOKENS)
    assert get_status_token(UIStatusKey.PREFLIGHT_ONLY).key == "preflight_only"
    assert get_status_token("unknown").key == "not_configured"
    assert "border-radius" in status_chip_stylesheet("testing")


def test_button_tokens_and_radius_follow_b1_constraints() -> None:
    assert {"primary", "primary_action", "secondary", "ghost", "file_picker", "disabled_action", "danger"} <= set(BUTTON_TOKENS)
    assert get_button_token("unknown").role == "secondary"
    assert RADIUS["card"] <= 8
    assert RADIUS["control"] <= RADIUS["card"]
    assert COLORS["bio"] in button_stylesheet("primary")
