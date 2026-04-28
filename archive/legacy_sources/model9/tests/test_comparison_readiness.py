import unittest

from analysis.comparison_readiness import build_comparison_readiness_report


class ComparisonReadinessTests(unittest.TestCase):
    def test_case_control_groups_are_runnable(self) -> None:
        report = build_comparison_readiness_report(
            [
                {"sample_id": "S1", "group": "case"},
                {"sample_id": "S2", "group": "case"},
                {"sample_id": "S3", "group": "control"},
                {"sample_id": "S4", "group": "control"},
            ],
            {
                "comparison_id": "case_vs_control",
                "group_column": "group",
                "case_group": "case",
                "control_group": "control",
            },
        )

        self.assertTrue(report.runnable)
        self.assertEqual(report.case_count, 2)
        self.assertEqual(report.control_count, 2)

    def test_missing_case_group_is_not_runnable(self) -> None:
        report = build_comparison_readiness_report(
            [
                {"sample_id": "S1", "group": "control"},
                {"sample_id": "S2", "group": "control"},
            ],
            {"group_column": "group", "case_group": "case", "control_group": "control"},
        )

        self.assertFalse(report.runnable)
        self.assertIn("case_group_has_no_samples", report.errors)

    def test_missing_control_group_is_not_runnable(self) -> None:
        report = build_comparison_readiness_report(
            [
                {"sample_id": "S1", "group": "case"},
                {"sample_id": "S2", "group": "case"},
            ],
            {"group_column": "group", "case_group": "case", "control_group": "control"},
        )

        self.assertFalse(report.runnable)
        self.assertIn("control_group_has_no_samples", report.errors)

    def test_missing_group_column_is_not_runnable(self) -> None:
        report = build_comparison_readiness_report(
            [{"sample_id": "S1", "group": "case"}],
            {"case_group": "case", "control_group": "control"},
        )

        self.assertFalse(report.runnable)
        self.assertIn("group_column_missing", report.errors)

    def test_small_group_sizes_are_warned(self) -> None:
        report = build_comparison_readiness_report(
            [
                {"sample_id": "S1", "group": "case"},
                {"sample_id": "S2", "group": "control"},
            ],
            {"group_column": "group", "case_group": "case", "control_group": "control"},
        )

        self.assertTrue(report.runnable)
        self.assertIn("case_group_below_minimum_size", report.warnings)
        self.assertIn("control_group_below_minimum_size", report.warnings)

    def test_missing_group_samples_are_recorded(self) -> None:
        report = build_comparison_readiness_report(
            [
                {"sample_id": "S1", "group": "case"},
                {"sample_id": "S2", "group": ""},
                {"sample_id": "S3"},
                {"sample_id": "S4", "group": "control"},
            ],
            {"group_column": "group", "case_group": "case", "control_group": "control"},
            minimum_group_size=1,
        )

        self.assertTrue(report.runnable)
        self.assertEqual(report.missing_group_samples, ["S2", "S3"])
        self.assertIn("samples_missing_group_assignment", report.warnings)


if __name__ == "__main__":
    unittest.main()
