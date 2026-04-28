from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.config import AppConfig
from core.data_dirs import DataDirectories
from tests.qt_test_utils import get_qapplication


class WorkbenchDesktopEntryTests(unittest.TestCase):
    def test_main_window_exposes_desktop_entry_labels_and_project_state(self) -> None:
        get_qapplication()
        from app.main_window import MainWindow

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

            home = window._workbench_home_widget
            self.assertEqual(window.current_workspace_key(), "bioinformatics")
            self.assertEqual(window.current_system_title(), "BioMedPilot · 生信分析")
            self.assertIn("Bioinformatics", home.entry_titles())
            self.assertIn("Meta Analysis", home.entry_titles())
            self.assertIn("not a formal release", home.capability_notice_text())
            self.assertIn("No project opened", home.current_project_text())

    def test_meta_workspace_exposes_expected_workflow_navigation(self) -> None:
        get_qapplication()
        from app.meta_analysis_workspace_widget import MetaAnalysisWorkspaceWidget

        widget = MetaAnalysisWorkspaceWidget()

        self.assertEqual(
            widget.navigation_titles()[:8],
            [
                "项目总览",
                "PICO / 检索",
                "文献导入",
                "文献筛选",
                "数据提取",
                "Profile Readiness",
                "统计分析",
                "报告导出",
            ],
        )

    def test_demo_project_loads_readiness_and_row_editor_controls(self) -> None:
        get_qapplication()
        from app.main_window import MainWindow

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

            project = window.load_demo_profile_readiness_project()
            panel = window._meta_analysis_workspace_widget.readiness_panel()
            editor = window._meta_analysis_workspace_widget.row_editor()

            self.assertEqual(project.project_id, "demo-profile-readiness")
            self.assertEqual(panel.readiness_cell_text(0, 0), "TREATMENT_EFFECT_META")
            self.assertTrue(editor.save_rows_button_enabled())
            self.assertTrue(editor.load_rows_button_enabled())
            self.assertIn("does not run meta-analysis", editor.note_text())
