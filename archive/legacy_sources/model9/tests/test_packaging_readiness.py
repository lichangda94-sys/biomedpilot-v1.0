import tempfile
import unittest
from pathlib import Path

from scripts.check_packaging_readiness import (
    REQUIRED_CORE_PACKAGE_DIRS,
    REQUIRED_FILES,
    RECOMMENDED_VALIDATION_COMMANDS,
    build_packaging_readiness_summary,
    inspect_packaging_readiness,
    main,
)


class PackagingReadinessTests(unittest.TestCase):
    def test_reports_ready_when_required_files_and_dirs_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for path in REQUIRED_FILES:
                file_path = root / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("placeholder\n", encoding="utf-8")
            for path in REQUIRED_CORE_PACKAGE_DIRS:
                (root / path).mkdir(parents=True, exist_ok=True)

            report = inspect_packaging_readiness(root)
            lines = build_packaging_readiness_summary(root)

        self.assertTrue(report.is_ready)
        self.assertEqual(report.missing_items, ())
        self.assertIn("- ready: yes", lines)
        self.assertIn("- pyproject.toml: present", lines)
        self.assertIn("- scripts/run_task_once.py: present", lines)
        self.assertIn("- scripts/run_fake_geo_preflight.py: present", lines)
        self.assertIn("- scripts/run_real_geo_readiness_test.py: present", lines)
        self.assertIn("- extraction: present", lines)
        self.assertIn("- none", lines)

    def test_reports_missing_items_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("placeholder\n", encoding="utf-8")
            (root / "core").mkdir()

            report = inspect_packaging_readiness(root)
            lines = build_packaging_readiness_summary(root)

        self.assertFalse(report.is_ready)
        self.assertGreater(len(report.missing_items), 0)
        self.assertIn("- ready: no", lines)
        self.assertIn("- pyproject.toml: missing", lines)
        self.assertIn("- scripts/run_smoke_tests.py: missing", lines)
        self.assertIn("- scripts/run_task_once.py: missing", lines)
        self.assertIn("- scripts/run_fake_geo_preflight.py: missing", lines)
        self.assertIn("- scripts/run_real_geo_readiness_test.py: missing", lines)
        self.assertIn("- app: missing", lines)
        self.assertIn("- reporting: missing", lines)

    def test_recommended_validation_commands_are_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = inspect_packaging_readiness(Path(temp_dir))
            lines = build_packaging_readiness_summary(Path(temp_dir))

        self.assertEqual(
            report.validation_commands,
            RECOMMENDED_VALIDATION_COMMANDS,
        )
        self.assertIn("Recommended validation commands:", lines)
        self.assertIn("- python3 scripts/run_smoke_tests.py", lines)
        self.assertIn("- python3 -m unittest discover -s tests", lines)

    def test_main_returns_success_for_reporting_only_check(self) -> None:
        self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
