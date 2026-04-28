import tempfile
import unittest
from pathlib import Path

from scripts.check_local_environment import (
    RECOMMENDED_BOOTSTRAP_COMMANDS,
    REQUIRED_LOCAL_FILES,
    build_local_environment_summary,
    inspect_local_environment,
    main,
)


class LocalEnvironmentCheckTests(unittest.TestCase):
    def test_reports_ready_when_required_files_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for path in REQUIRED_LOCAL_FILES:
                file_path = root / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("placeholder\n", encoding="utf-8")

            report = inspect_local_environment(root, version_info=(3, 11, 0))
            lines = build_local_environment_summary(root, version_info=(3, 11, 0))

        self.assertTrue(report.is_ready)
        self.assertEqual(report.missing_items, ())
        self.assertIn("- ready: yes", lines)
        self.assertIn("- python version: 3.11.0", lines)
        self.assertIn("- requirements.txt: present", lines)
        self.assertIn("- scripts/run_task_once.py: present", lines)
        self.assertIn("- scripts/run_fake_geo_preflight.py: present", lines)
        self.assertIn("- scripts/run_real_geo_readiness_test.py: present", lines)
        self.assertIn("- none", lines)

    def test_reports_missing_items_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pyproject.toml").write_text(
                "placeholder\n",
                encoding="utf-8",
            )

            report = inspect_local_environment(root, version_info=(3, 11, 0))
            lines = build_local_environment_summary(root, version_info=(3, 11, 0))

        self.assertFalse(report.is_ready)
        self.assertGreater(len(report.missing_items), 0)
        self.assertIn("- ready: no", lines)
        self.assertIn("- requirements.txt: missing", lines)
        self.assertIn("- scripts/run_smoke_tests.py: missing", lines)
        self.assertIn("- scripts/export_requirements.py: missing", lines)
        self.assertIn("- scripts/run_task_once.py: missing", lines)
        self.assertIn("- scripts/run_fake_geo_preflight.py: missing", lines)
        self.assertIn("- scripts/run_real_geo_readiness_test.py: missing", lines)

    def test_reports_unsupported_python_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for path in REQUIRED_LOCAL_FILES:
                file_path = root / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("placeholder\n", encoding="utf-8")

            report = inspect_local_environment(root, version_info=(3, 9, 18))
            lines = build_local_environment_summary(root, version_info=(3, 9, 18))

        self.assertFalse(report.is_ready)
        self.assertFalse(report.python_version_supported)
        self.assertIn("- python version: 3.9.18", lines)
        self.assertIn("- python version supported: no", lines)

    def test_recommended_bootstrap_commands_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = inspect_local_environment(
                Path(temp_dir),
                version_info=(3, 11, 0),
            )
            lines = build_local_environment_summary(
                Path(temp_dir),
                version_info=(3, 11, 0),
            )

        self.assertEqual(report.bootstrap_commands, RECOMMENDED_BOOTSTRAP_COMMANDS)
        self.assertIn("Recommended local bootstrap commands:", lines)
        self.assertIn("- python3 -m venv .venv", lines)
        self.assertIn("- source .venv/bin/activate", lines)
        self.assertIn("- pip install -r requirements.txt", lines)

    def test_main_returns_success_for_reporting_only_check(self) -> None:
        self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
