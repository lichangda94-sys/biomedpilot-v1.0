from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

WorkspaceKey = Literal[
    "dashboard",
    "bioinformatics",
    "meta_analysis",
    "labtools",
    "settings",
    "test_feedback",
    "about",
]


@dataclass
class ShellNavigationState:
    current_workspace: WorkspaceKey = "dashboard"

    def show_dashboard(self) -> None:
        self.current_workspace = "dashboard"

    def show_bioinformatics(self) -> None:
        self.current_workspace = "bioinformatics"

    def show_meta_analysis(self) -> None:
        self.current_workspace = "meta_analysis"

    def show_labtools(self) -> None:
        self.current_workspace = "labtools"

    def show_settings(self) -> None:
        self.current_workspace = "settings"

    def show_test_feedback(self) -> None:
        self.current_workspace = "test_feedback"

    def show_testing(self) -> None:
        self.show_test_feedback()

    def show_about(self) -> None:
        self.current_workspace = "about"
