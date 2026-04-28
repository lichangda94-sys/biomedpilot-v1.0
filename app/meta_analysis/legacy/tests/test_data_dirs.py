from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import core.data_dirs as data_dirs_module
from core.data_dirs import DataDirectories


class DataDirectoriesTests(unittest.TestCase):
    def test_data_directories_create_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(data_dirs_module.platform, "system", return_value="Linux"):
                with patch.dict("os.environ", {"XDG_DATA_HOME": temp_dir}, clear=False):
                    data_dirs = DataDirectories.for_app("model9")
                    data_dirs.ensure_exists()

            self.assertEqual(data_dirs.root_dir, Path(temp_dir) / "model9")
            self.assertTrue(data_dirs.logs_dir.exists())
            self.assertTrue(data_dirs.state_dir.exists())
            self.assertTrue(data_dirs.cache_dir.exists())
            self.assertIsInstance(data_dirs.config_dir, Path)
