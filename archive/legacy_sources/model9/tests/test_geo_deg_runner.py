import unittest

from analysis.deg_ready_matrix import (
    build_deg_ready_matrix_report,
    build_deg_ready_matrix_report_from_reports,
)
from geo_readiness.models import PlatformAnnotationMappingReport, SeriesMatrixExpressionReport


FAKE_EXPRESSION = [
    {"probe_id": "probe1", "case1": 10.0, "case2": 12.0, "control1": 4.0, "control2": 5.0},
    {"probe_id": "probe2", "case1": 8.0, "case2": 9.0, "control1": 3.0, "control2": 4.0},
    {"probe_id": "probe3", "case1": 2.0, "case2": 2.5, "control1": 2.0, "control2": 2.2},
]
FAKE_GROUPS = {
    "case1": "ptc",
    "case2": "ptc",
    "control1": "normal",
    "control2": "normal",
}
FAKE_MAPPING = {"probe1": "GENE1", "probe2": "GENE1", "probe3": "GENE2"}


class DegReadyMatrixTests(unittest.TestCase):
    def test_fake_probe_matrix_generates_gene_level_report(self) -> None:
        report = build_deg_ready_matrix_report(FAKE_EXPRESSION, FAKE_GROUPS, FAKE_MAPPING)

        self.assertTrue(report.ready)
        self.assertEqual(report.feature_count, 3)
        self.assertEqual(report.mapped_feature_count, 3)
        self.assertEqual(report.unmapped_feature_count, 0)
        self.assertEqual(report.gene_count, 2)
        self.assertEqual(report.gene_count_after_collapse, 2)
        self.assertEqual(report.sample_count, 4)
        self.assertEqual(report.case_count, 2)
        self.assertEqual(report.control_count, 2)
        self.assertEqual(report.collapse_strategy, "mean")

    def test_duplicated_gene_symbols_are_counted(self) -> None:
        report = build_deg_ready_matrix_report(FAKE_EXPRESSION, FAKE_GROUPS, FAKE_MAPPING)

        self.assertEqual(report.duplicated_gene_count, 1)
        self.assertIn("duplicated_genes_collapsed", report.warnings)

    def test_unmapped_probes_are_counted(self) -> None:
        mapping = {"probe1": "GENE1", "probe2": None, "probe3": "GENE2"}
        report = build_deg_ready_matrix_report(FAKE_EXPRESSION, FAKE_GROUPS, mapping)

        self.assertTrue(report.ready)
        self.assertEqual(report.mapped_feature_count, 2)
        self.assertEqual(report.unmapped_feature_count, 1)
        self.assertIn("unmapped_probes_excluded", report.warnings)

    def test_missing_mapping_blocks_readiness(self) -> None:
        report = build_deg_ready_matrix_report(FAKE_EXPRESSION, FAKE_GROUPS, None)

        self.assertFalse(report.ready)
        self.assertIn("probe_symbol_mapping_missing", report.errors)
        self.assertIn("mapped_features_missing", report.errors)

    def test_missing_group_blocks_readiness(self) -> None:
        report = build_deg_ready_matrix_report(
            FAKE_EXPRESSION,
            {"case1": "ptc", "case2": "ptc"},
            FAKE_MAPPING,
        )

        self.assertFalse(report.ready)
        self.assertEqual(report.control_count, 0)
        self.assertIn("control_group_has_no_samples", report.errors)

    def test_non_numeric_values_block_readiness(self) -> None:
        rows = [dict(FAKE_EXPRESSION[0], case1="not_numeric")]
        report = build_deg_ready_matrix_report(rows, FAKE_GROUPS, {"probe1": "GENE1"})

        self.assertFalse(report.ready)
        self.assertIn("non_numeric_expression_values", report.errors)

    def test_report_inputs_can_generate_deg_ready_summary(self) -> None:
        expression_report = SeriesMatrixExpressionReport(
            feature_count=3,
            sample_count=4,
            matrix_sample_ids=["case1", "case2", "control1", "control2"],
            numeric_value_status="numeric",
            sample_id_match_status="match",
        )
        mapping_report = PlatformAnnotationMappingReport(
            probe_count=3,
            mapped_probe_count=3,
            unmapped_probe_count=0,
            duplicated_symbol_count=1,
            acceptable=True,
        )

        report = build_deg_ready_matrix_report_from_reports(
            expression_report,
            mapping_report,
            FAKE_GROUPS,
        )

        self.assertTrue(report.ready)
        self.assertEqual(report.feature_count, 3)
        self.assertEqual(report.mapped_feature_count, 3)
        self.assertEqual(report.unmapped_feature_count, 0)
        self.assertEqual(report.duplicated_gene_count, 1)
        self.assertEqual(report.gene_count_after_collapse, 2)
        self.assertEqual(report.case_count, 2)
        self.assertEqual(report.control_count, 2)

    def test_report_inputs_block_when_group_missing(self) -> None:
        expression_report = SeriesMatrixExpressionReport(
            feature_count=3,
            sample_count=2,
            matrix_sample_ids=["case1", "case2"],
            numeric_value_status="numeric",
            sample_id_match_status="match",
        )
        mapping_report = PlatformAnnotationMappingReport(
            probe_count=3,
            mapped_probe_count=3,
            acceptable=True,
        )

        report = build_deg_ready_matrix_report_from_reports(
            expression_report,
            mapping_report,
            {"case1": "ptc", "case2": "ptc"},
        )

        self.assertFalse(report.ready)
        self.assertIn("control_group_has_no_samples", report.errors)

    def test_report_inputs_block_when_mapping_missing(self) -> None:
        expression_report = SeriesMatrixExpressionReport(
            feature_count=3,
            sample_count=4,
            matrix_sample_ids=["case1", "case2", "control1", "control2"],
            numeric_value_status="numeric",
            sample_id_match_status="match",
        )

        report = build_deg_ready_matrix_report_from_reports(
            expression_report,
            None,
            FAKE_GROUPS,
        )

        self.assertFalse(report.ready)
        self.assertIn("platform_mapping_report_missing", report.errors)
        self.assertIn("platform_mapping_not_acceptable", report.errors)


if __name__ == "__main__":
    unittest.main()
