from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reporting.profile_readiness import (
    PROFILE_READINESS_FILENAME,
    READINESS_DISCLAIMER,
    load_project_profile_readiness,
)
from tests.qt_test_utils import get_qapplication


class ProfileReadinessPanelTests(unittest.TestCase):
    def test_loader_returns_empty_dashboard_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dashboard = load_project_profile_readiness(Path(temp_dir))

            self.assertFalse(dashboard.has_rows)
            self.assertIn("No profile policy readiness", dashboard.warning)

    def test_loader_reads_profile_readiness_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / PROFILE_READINESS_FILENAME).write_text(
                json.dumps(
                    {
                        "rows": [
                            {
                                "method_profile": "DIAGNOSTIC_ACCURACY_META",
                                "support_status": "policy_ready",
                                "supported_now": False,
                                "policy_ready": True,
                                "unsupported_features": ["HSROC"],
                                "unimplemented_features": ["bivariate model"],
                                "warnings": ["reported metric only"],
                                "recommended_next_action": "Keep sensitivity/specificity as reported metrics.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            dashboard = load_project_profile_readiness(project_dir)

            self.assertTrue(dashboard.has_rows)
            self.assertEqual(dashboard.rows[0].profile, "DIAGNOSTIC_ACCURACY_META")
            self.assertEqual(dashboard.rows[0].support_status, "policy_ready")
            self.assertIn("HSROC", dashboard.rows[0].unsupported)

    def test_widget_displays_empty_state_and_disclaimer(self) -> None:
        get_qapplication()
        from app.profile_readiness_panel_widget import ProfileReadinessPanelWidget
        from reporting.profile_readiness import ProfileReadinessDashboard

        widget = ProfileReadinessPanelWidget()

        widget.set_dashboard(ProfileReadinessDashboard())

        self.assertEqual(widget.disclaimer_text(), READINESS_DISCLAIMER)
        self.assertIn("pooled statistical analysis", widget.disclaimer_text())
        self.assertIn("NMA", widget.disclaimer_text())
        self.assertIn("GLMM", widget.disclaimer_text())
        self.assertIn("No profile policy readiness", widget.empty_state_text())

    def test_meta_workspace_loads_project_readiness_dashboard(self) -> None:
        get_qapplication()
        from app.main_window import MainWindow
        from core.config import AppConfig
        from core.data_dirs import DataDirectories

        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            data_dirs = DataDirectories(
                root_dir=root_dir,
                config_dir=root_dir / "config",
                logs_dir=root_dir / "logs",
                state_dir=root_dir / "state",
                cache_dir=root_dir / "cache",
            )
            data_dirs.ensure_exists()
            window = MainWindow(
                config=AppConfig(app_name="Model9", app_slug="model9", organization_name="model9"),
                data_dirs=data_dirs,
            )
            project = window.create_project_workspace(
                project_type="meta_analysis",
                name="Readiness Demo",
                project_id="readiness-demo",
            )
            (project.project_dir / PROFILE_READINESS_FILENAME).write_text(
                json.dumps(
                    {
                        "rows": [
                            {
                                "profile": "BIOMARKER_PREVALENCE_ASSOCIATION_META",
                                "support_status": "mixed",
                                "supported_now": False,
                                "policy_ready": True,
                                "unsupported": "pooled prevalence runner",
                                "unimplemented": "Freeman-Tukey transformation",
                                "recommended_next_action": "Keep numerator/denominator metadata structured.",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            window.open_project_workspace(project.project_dir)
            panel = window._meta_analysis_workspace_widget.readiness_panel()

            self.assertEqual(
                panel.readiness_cell_text(0, 0),
                "BIOMARKER_PREVALENCE_ASSOCIATION_META",
            )
            self.assertEqual(panel.readiness_cell_text(0, 1), "mixed")
            self.assertIn("pooled prevalence", panel.readiness_cell_text(0, 4))
