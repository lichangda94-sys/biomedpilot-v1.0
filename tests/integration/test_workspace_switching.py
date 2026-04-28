from __future__ import annotations

from app.shell.navigation import ShellNavigationState


def test_shell_navigation_state_switches_workspaces() -> None:
    navigation = ShellNavigationState()
    assert navigation.current_workspace == "dashboard"
    navigation.show_bioinformatics()
    assert navigation.current_workspace == "bioinformatics"
    navigation.show_meta_analysis()
    assert navigation.current_workspace == "meta_analysis"
    navigation.show_settings()
    assert navigation.current_workspace == "settings"
    navigation.show_testing()
    assert navigation.current_workspace == "testing"
    navigation.show_dashboard()
    assert navigation.current_workspace == "dashboard"
