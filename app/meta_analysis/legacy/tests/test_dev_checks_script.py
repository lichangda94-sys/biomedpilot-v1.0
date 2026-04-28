import unittest

from scripts.run_dev_checks import (
    DEFAULT_CHECKS,
    QUICK_CHECKS,
    build_dev_checks_summary,
    run_dev_checks,
    select_checks,
)


class DevChecksScriptTests(unittest.TestCase):
    def test_default_checks_run_in_expected_order(self) -> None:
        seen: list[tuple[str, ...]] = []

        def runner(command: tuple[str, ...]) -> int:
            seen.append(tuple(command))
            return 0

        results = run_dev_checks(runner=runner)

        self.assertEqual(tuple(seen), DEFAULT_CHECKS)
        self.assertTrue(all(result.passed for result in results))

    def test_quick_checks_run_reduced_order(self) -> None:
        seen: list[tuple[str, ...]] = []

        def runner(command: tuple[str, ...]) -> int:
            seen.append(tuple(command))
            return 0

        results = run_dev_checks(quick=True, runner=runner)

        self.assertEqual(tuple(seen), QUICK_CHECKS)
        self.assertNotIn(
            ("python3", "scripts/export_requirements.py", "--check"),
            tuple(seen),
        )
        self.assertIn(
            ("python3", "scripts/run_task_once.py", "--help"),
            tuple(seen),
        )
        self.assertIn(
            ("python3", "scripts/run_fake_geo_preflight.py"),
            tuple(seen),
        )
        self.assertIn(
            ("python3", "scripts/run_real_geo_readiness_test.py", "--help"),
            tuple(seen),
        )
        self.assertTrue(all(result.passed for result in results))

    def test_failure_stops_later_checks_and_reports_non_pass(self) -> None:
        seen: list[tuple[str, ...]] = []

        def runner(command: tuple[str, ...]) -> int:
            seen.append(tuple(command))
            if command == ("python3", "scripts/check_packaging_readiness.py"):
                return 2
            return 0

        results = run_dev_checks(runner=runner)
        lines = build_dev_checks_summary(results)

        self.assertEqual(tuple(seen), DEFAULT_CHECKS[:2])
        self.assertFalse(results[-1].passed)
        self.assertIn(
            "- python3 scripts/check_packaging_readiness.py: fail",
            lines,
        )
        self.assertIn("Overall: fail", lines)

    def test_summary_reports_pass_and_command_names(self) -> None:
        results = run_dev_checks(quick=True, runner=lambda command: 0)
        lines = build_dev_checks_summary(results)

        self.assertIn("Developer verification checks:", lines)
        self.assertIn("- python3 scripts/check_local_environment.py: pass", lines)
        self.assertIn("- python3 scripts/run_task_once.py --help: pass", lines)
        self.assertIn("- python3 scripts/run_fake_geo_preflight.py: pass", lines)
        self.assertIn(
            "- python3 scripts/run_real_geo_readiness_test.py --help: pass",
            lines,
        )
        self.assertIn("- python3 scripts/run_smoke_tests.py: pass", lines)
        self.assertIn("Overall: pass", lines)

    def test_select_checks_matches_modes(self) -> None:
        self.assertEqual(select_checks(quick=False), DEFAULT_CHECKS)
        self.assertEqual(select_checks(quick=True), QUICK_CHECKS)


if __name__ == "__main__":
    unittest.main()
