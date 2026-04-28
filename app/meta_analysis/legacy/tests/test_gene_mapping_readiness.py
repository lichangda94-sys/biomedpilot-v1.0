import unittest

from core.dataset_readiness import build_gene_mapping_readiness_report


class GeneMappingReadinessTests(unittest.TestCase):
    def test_gene_symbol_input_maps_to_itself(self) -> None:
        report = build_gene_mapping_readiness_report(
            ["TP53", "EGFR", "BRCA1"],
            input_id_type="gene_symbol",
            target_id_type="gene_symbol",
        )

        self.assertTrue(report.acceptable)
        self.assertEqual(report.total_features, 3)
        self.assertEqual(report.mapped_features, 3)
        self.assertEqual(report.mapping_success_rate, 1.0)

    def test_ensembl_versions_are_stripped_before_mapping(self) -> None:
        report = build_gene_mapping_readiness_report(
            ["ENSG000001.5", "ENSG000002.1"],
            {"ENSG000001": "TP53", "ENSG000002": "EGFR"},
            input_id_type="ensembl_gene_id",
            target_id_type="gene_symbol",
        )

        self.assertTrue(report.acceptable)
        self.assertEqual(report.mapped_features, 2)
        self.assertIn("ensembl_versions_stripped", report.warnings)

    def test_probe_only_input_reports_warning(self) -> None:
        report = build_gene_mapping_readiness_report(
            ["1007_s_at", "1053_at"],
            {"1007_s_at": "DDR1", "1053_at": "RFC2"},
            input_id_type="probe_id",
            target_id_type="gene_symbol",
        )

        self.assertTrue(report.acceptable)
        self.assertIn("probe_identifier_mapping_required", report.warnings)

    def test_duplicated_targets_report_warning(self) -> None:
        report = build_gene_mapping_readiness_report(
            ["probe-a", "probe-b", "probe-c"],
            {"probe-a": "TP53", "probe-b": "TP53", "probe-c": "EGFR"},
            input_id_type="probe_id",
            target_id_type="gene_symbol",
        )

        self.assertEqual(report.duplicated_targets, 1)
        self.assertIn("duplicated_targets_detected", report.warnings)

    def test_mapping_success_rate_is_calculated(self) -> None:
        report = build_gene_mapping_readiness_report(
            ["a", "b", "c", "d"],
            {"a": "A", "b": "B", "c": None},
            input_id_type="custom_id",
            target_id_type="gene_symbol",
            minimum_success_rate=0.5,
        )

        self.assertEqual(report.mapped_features, 2)
        self.assertEqual(report.unmapped_features, 2)
        self.assertEqual(report.mapping_success_rate, 0.5)
        self.assertTrue(report.acceptable)

    def test_low_mapping_success_rate_is_not_acceptable(self) -> None:
        report = build_gene_mapping_readiness_report(
            ["a", "b", "c", "d"],
            {"a": "A"},
            input_id_type="custom_id",
            target_id_type="gene_symbol",
            minimum_success_rate=0.8,
        )

        self.assertFalse(report.acceptable)
        self.assertIn("mapping_success_rate_too_low", report.errors)


if __name__ == "__main__":
    unittest.main()
