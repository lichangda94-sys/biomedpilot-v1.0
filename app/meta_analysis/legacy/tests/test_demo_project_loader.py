from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.demo_project_loader import create_demo_meta_readiness_project
from core.project_workspace import PROJECT_MANIFEST_FILENAME
from reporting.profile_readiness import PROFILE_READINESS_FILENAME, load_project_profile_readiness


class DemoProjectLoaderTests(unittest.TestCase):
    def test_create_demo_meta_readiness_project_writes_readiness_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state = create_demo_meta_readiness_project(Path(temp_dir))

            dashboard = load_project_profile_readiness(state.project_dir)

            self.assertEqual(state.project_type, "meta_analysis")
            self.assertEqual(state.project_id, "demo-profile-readiness")
            self.assertTrue((state.project_dir / PROJECT_MANIFEST_FILENAME).exists())
            self.assertTrue((state.project_dir / PROFILE_READINESS_FILENAME).exists())
            self.assertEqual(len(dashboard.rows), 3)
            self.assertEqual(
                [row.profile for row in dashboard.rows],
                [
                    "TREATMENT_EFFECT_META",
                    "DIAGNOSTIC_ACCURACY_META",
                    "BIOMARKER_PREVALENCE_ASSOCIATION_META",
                ],
            )
            self.assertEqual(
                [row.support_status for row in dashboard.rows],
                ["supported", "policy_ready", "mixed"],
            )
            self.assertIn(
                "BIOMARKER_PREVALENCE_ASSOCIATION_META",
                [row.profile for row in dashboard.rows],
            )

    def test_main_window_loads_demo_project_into_meta_workspace(self) -> None:
        from tests.qt_test_utils import get_qapplication

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

            state = window.load_demo_profile_readiness_project()

            self.assertEqual(state.project_id, "demo-profile-readiness")
            self.assertEqual(window.current_workspace_key(), "meta_analysis")
            panel = window._meta_analysis_workspace_widget.readiness_panel()
            self.assertEqual(panel.readiness_cell_text(0, 0), "TREATMENT_EFFECT_META")
