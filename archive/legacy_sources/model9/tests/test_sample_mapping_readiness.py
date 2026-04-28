import unittest

from core.dataset_readiness import build_sample_mapping_readiness_report


class SampleMappingReadinessTests(unittest.TestCase):
    def test_complete_sample_match_is_acceptable(self) -> None:
        report = build_sample_mapping_readiness_report(
            ["GSM1", "GSM2", "GSM3"],
            ["GSM1", "GSM2", "GSM3"],
        )

        self.assertTrue(report.acceptable)
        self.assertEqual(report.matched_sample_count, 3)
        self.assertEqual(report.match_rate, 1.0)
        self.assertEqual(report.unmatched_matrix_samples, [])

    def test_partial_missing_samples_are_reported(self) -> None:
        report = build_sample_mapping_readiness_report(
            ["GSM1", "GSM2", "GSM3"],
            ["GSM1", "GSM2"],
            minimum_match_rate=0.5,
        )

        self.assertTrue(report.acceptable)
        self.assertEqual(report.unmatched_matrix_samples, ["GSM3"])
        self.assertIn("unmatched_matrix_samples", report.warnings)

    def test_metadata_can_have_extra_samples(self) -> None:
        report = build_sample_mapping_readiness_report(
            ["GSM1", "GSM2"],
            ["GSM1", "GSM2", "GSM4"],
        )

        self.assertTrue(report.acceptable)
        self.assertEqual(report.unmatched_metadata_samples, ["GSM4"])
        self.assertIn("unmatched_metadata_samples", report.warnings)

    def test_matrix_can_have_extra_samples(self) -> None:
        report = build_sample_mapping_readiness_report(
            ["GSM1", "GSM2", "GSM5"],
            ["GSM1", "GSM2"],
            minimum_match_rate=0.5,
        )

        self.assertTrue(report.acceptable)
        self.assertEqual(report.unmatched_matrix_samples, ["GSM5"])

    def test_duplicate_sample_ids_are_reported(self) -> None:
        report = build_sample_mapping_readiness_report(
            ["GSM1", "GSM1", "GSM2"],
            ["GSM1", "GSM2", "GSM2"],
        )

        self.assertTrue(report.acceptable)
        self.assertEqual(report.duplicate_sample_ids, ["GSM1", "GSM2"])
        self.assertIn("duplicate_sample_ids_detected", report.warnings)

    def test_match_rate_below_threshold_is_unacceptable(self) -> None:
        report = build_sample_mapping_readiness_report(
            ["GSM1", "GSM2", "GSM3", "GSM4"],
            ["GSM1"],
            minimum_match_rate=0.75,
        )

        self.assertFalse(report.acceptable)
        self.assertEqual(report.match_rate, 0.25)
        self.assertIn("sample_match_rate_too_low", report.errors)


if __name__ == "__main__":
    unittest.main()
