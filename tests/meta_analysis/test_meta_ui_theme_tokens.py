from __future__ import annotations

from pathlib import Path

from app.ui_style_tokens import COLORS, meta_workspace_stylesheet


def test_meta_theme_tokens_use_biomedpilot_main_palette() -> None:
    assert COLORS["meta"] == COLORS["deep_navy"] == "#12324A"
    assert COLORS["meta_accent"] == COLORS["teal"] == "#1BAE9F"
    assert COLORS["meta_soft"] == COLORS["light_gray"] == "#F5F7F9"
    assert "#6B4FD8" not in COLORS.values()
    assert "#F0EDFF" not in COLORS.values()


def test_meta_workspace_stylesheet_uses_shared_tokens() -> None:
    stylesheet = meta_workspace_stylesheet()

    assert COLORS["deep_navy"] in stylesheet
    assert COLORS["teal"] in stylesheet
    assert COLORS["light_gray"] in stylesheet
    assert COLORS["white"] in stylesheet
    for retired_color in ("#0F766E", "#E6FFFB", "#99F6E4", "#D8DEE9", "#111827", "#B42318"):
        assert retired_color not in stylesheet


def test_active_meta_ui_source_has_no_retired_theme_colors_or_legacy_ui_imports() -> None:
    root = Path(__file__).resolve().parents[2] / "app" / "meta_analysis"
    retired_colors = ("#6B4FD8", "#F0EDFF", "#0F766E", "#E6FFFB", "#99F6E4", "#D8DEE9", "#111827", "#B42318")
    forbidden_legacy_ui_imports = (
        "app.meta_analysis.legacy.app",
        "app.meta_analysis.legacy.app_meta",
        "app_meta.ui",
        "create_demo_project_state",
        "create_demo_meta_readiness_project",
        "run_task_execution_request_mock",
    )

    for path in root.rglob("*.py"):
        if "legacy" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for color in retired_colors:
            assert color not in text, f"{path} still contains retired Meta UI color {color}"
        for forbidden in forbidden_legacy_ui_imports:
            assert forbidden not in text, f"{path} still references legacy UI/demo runtime {forbidden}"
