import unittest

from geo_readiness.real_dataset_report import (
    GAP_CATEGORIES,
    build_real_dataset_readiness_report,
    classify_real_dataset_gaps,
)


class RealDatasetReadinessReportTests(unittest.TestCase):
    def test_gap_categories_are_stable(self) -> None:
        self.assertIn("metadata_parse_gap", GAP_CATEGORIES)
        self.assertIn("group_detection_gap", GAP_CATEGORIES)
        self.assertIn("manual_confirmation_required", GAP_CATEGORIES)

    def test_builds_clean_runnable_report(self) -> None:
        report = build_real_dataset_readiness_report(
            dataset_id="GSE33630",
            metadata_parse={"gse_id": "GSE33630", "errors": [], "warnings": []},
            series_matrix_metadata={"sample_count": 105, "errors": [], "warnings": []},
            group_detection={"detected_groups": ["ptc", "normal"], "warnings": [], "errors": []},
            expression_report={
                "sample_id_match_status": "match",
                "errors": [],
                "warnings": [],
            },
            platform_mapping={"acceptable": True, "errors": [], "warnings": []},
            preflight={"runnable": True, "blocking_errors": [], "warnings": []},
        )

        self.assertEqual(report.dataset_id, "GSE33630")
        self.assertEqual(report.gaps, [])
        self.assertEqual(report.errors, [])
        self.assertEqual(report.recommended_action, "ready_for_manual_review")

    def test_classifies_common_gaps(self) -> None:
        gaps = classify_real_dataset_gaps(
            metadata_errors=["metadata_parse_failed"],
            expression_errors=["non_numeric_expression_values"],
            sample_mapping_status="mismatch",
            platform_mapping_acceptable=False,
            platform_mapping_errors=["mapping_success_rate_too_low"],
            group_warnings=["ambiguous_samples"],
            preflight_blocking_errors=["comparison:control_group_has_no_samples"],
        )

        categories = {gap.category for gap in gaps}
        self.assertIn("metadata_parse_gap", categories)
        self.assertIn("expression_matrix_gap", categories)
        self.assertIn("sample_mapping_gap", categories)
        self.assertIn("gene_mapping_gap", categories)
        self.assertIn("group_detection_gap", categories)
        self.assertIn("comparison_readiness_gap", categories)

    def test_excluded_non_target_samples_do_not_create_gap(self) -> None:
        gaps = classify_real_dataset_gaps(
            group_warnings=["excluded_non_target_samples"],
            preflight_blocking_errors=[],
        )

        self.assertEqual(gaps, [])

    def test_report_deduplicates_preflight_and_direct_gaps(self) -> None:
        report = build_real_dataset_readiness_report(
            dataset_id="GSE-bad",
            expression_report={
                "errors": ["matrix_metadata_sample_id_mismatch"],
                "sample_id_match_status": "mismatch",
                "warnings": [],
            },
            preflight={
                "runnable": False,
                "blocking_errors": ["expression_matrix:matrix_metadata_sample_id_mismatch"],
                "warnings": [],
            },
        )

        payload = report.to_dict()
        self.assertEqual(report.recommended_action, "fix_expression_matrix_readiness")
        self.assertGreaterEqual(len(payload["gaps"]), 2)
        self.assertIn("matrix_metadata_sample_id_mismatch", report.errors)


if __name__ == "__main__":
    unittest.main()
