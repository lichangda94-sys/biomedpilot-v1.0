import os
import unittest
from unittest.mock import patch

from core.config import AppConfig


class AppConfigTests(unittest.TestCase):
    def test_load_config_uses_env(self) -> None:
        env = {
            "MODEL9_APP_NAME": "Model Nine",
            "MODEL9_APP_SLUG": "model-nine",
            "MODEL9_ORG_NAME": "Open Desk",
            "MODEL9_DEBUG": "true",
            "MODEL9_STARTUP_TEST_MS": "250",
        }

        with patch.dict(os.environ, env, clear=False):
            config = AppConfig.load()

        self.assertEqual(config.app_name, "Model Nine")
        self.assertEqual(config.app_slug, "model-nine")
        self.assertEqual(config.organization_name, "Open Desk")
        self.assertTrue(config.debug)
        self.assertEqual(config.startup_test_ms, 250)
