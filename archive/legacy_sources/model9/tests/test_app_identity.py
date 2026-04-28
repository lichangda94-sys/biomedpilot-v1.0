from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.qt_test_utils import get_qapplication


class AppIdentityTests(unittest.TestCase):
    def test_app_identity_assets_exist_and_icon_loads(self) -> None:
        get_qapplication()
        from app.app_identity import (
            APP_ICON_ICNS_PATH,
            APP_ICON_PNG_PATH,
            APP_NAME,
            APP_WINDOW_TITLE,
            apply_app_identity,
            load_app_icon,
        )

        self.assertEqual(APP_NAME, "BioMedPilot")
        self.assertEqual(APP_WINDOW_TITLE, "BioMedPilot · 生信分析")
        self.assertTrue(APP_ICON_PNG_PATH.exists())
        self.assertTrue(APP_ICON_ICNS_PATH.exists())
        self.assertGreater(APP_ICON_PNG_PATH.stat().st_size, 0)
        self.assertGreater(APP_ICON_ICNS_PATH.stat().st_size, 0)
        self.assertFalse(load_app_icon().isNull())

        app = get_qapplication()
        apply_app_identity(app)
        self.assertEqual(app.applicationName(), "BioMedPilot")
        self.assertEqual(app.applicationDisplayName(), "BioMedPilot")
        self.assertFalse(app.windowIcon().isNull())

    def test_icon_registry_assets_are_grouped_for_future_replacement(self) -> None:
        get_qapplication()
        from app.ui_icon_registry import (
            APP_ICON_DIR,
            CONTACT_SHEET_DIR,
            DASHBOARD_ICON_DIR,
            EMPTY_STATE_ILLUSTRATION_DIR,
            ICON_ASSET_ROOT,
            ICON_MANIFEST_PATH,
            SIDEBAR_ICON_DIR,
            STATUS_ICON_DIR,
            TOOLBAR_ICON_DIR,
            IconFactory,
        )

        self.assertEqual(ICON_ASSET_ROOT.name, "icons")
        for path in [
            APP_ICON_DIR,
            SIDEBAR_ICON_DIR,
            STATUS_ICON_DIR,
            DASHBOARD_ICON_DIR,
            TOOLBAR_ICON_DIR,
            EMPTY_STATE_ILLUSTRATION_DIR,
            CONTACT_SHEET_DIR,
        ]:
            self.assertTrue(path.exists())
            self.assertTrue(path.is_dir())

        self.assertTrue(ICON_MANIFEST_PATH.exists())
        self.assertFalse(IconFactory.app_icon().isNull())
        self.assertFalse(IconFactory.sidebar_icon("home").isNull())
        self.assertFalse(IconFactory.dashboard_icon("data_sources").isNull())
        self.assertFalse(IconFactory.status_icon("needs_attention").isNull())
        self.assertFalse(IconFactory.toolbar_icon("notifications").isNull())
        self.assertFalse(IconFactory.empty_state_icon("no_data").isNull())

    def test_icon_manifest_files_exist_and_load(self) -> None:
        get_qapplication()
        import json
        from app.ui_icon_registry import ICON_ASSET_ROOT, ICON_MANIFEST_PATH

        manifest = json.loads(ICON_MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(manifest["assets"]), 29)
        for record in manifest["assets"]:
            path = ICON_ASSET_ROOT / record["filename"]
            self.assertTrue(path.exists(), record["filename"])
            self.assertGreater(path.stat().st_size, 0, record["filename"])

    def test_main_window_uses_biomedpilot_title_and_icon_on_startup(self) -> None:
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

            self.assertEqual(window.current_system_title(), "BioMedPilot · 生信分析")
            self.assertEqual(window.current_workspace_key(), "bioinformatics")
            self.assertFalse(window.windowIcon().isNull())
