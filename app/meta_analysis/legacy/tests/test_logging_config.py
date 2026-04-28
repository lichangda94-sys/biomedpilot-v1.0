import logging
import tempfile
import unittest
from pathlib import Path

from core.logging_config import configure_logging


class LoggingConfigTests(unittest.TestCase):
    def test_configure_logging_creates_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = configure_logging(Path(temp_dir), debug=True)
            logging.getLogger("model9.tests").info("hello")

            self.assertTrue(log_file.exists())
            self.assertIn("hello", log_file.read_text(encoding="utf-8"))
