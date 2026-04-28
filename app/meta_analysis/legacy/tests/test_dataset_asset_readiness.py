import unittest

from core.dataset_readiness import (
    DatasetAssetStatus,
    build_dataset_asset_readiness_report,
)


class DatasetAssetReadinessTests(unittest.TestCase):
    def test_complete_assets_are_runnable(self) -> None:
        report = build_dataset_asset_readiness_report(
            "GSE-complete",
            {
                "expression_matrix": True,
                "sample_annotation": True,
                "platform_annotation": True,
                "gene_annotation": True,
                "clinical_annotation": True,
                "metadata": {"source": "fake-fixture"},
            },
        )

        self.assertTrue(report.runnable)
        self.assertEqual(report.expression_matrix_status, DatasetAssetStatus.PRESENT)
        self.assertEqual(report.recommended_action, "ready_for_preflight")
        self.assertEqual(report.metadata["source"], "fake-fixture")

    def test_missing_expression_matrix_blocks_runnable(self) -> None:
        report = build_dataset_asset_readiness_report(
            "GSE-missing-expression",
            {
                "sample_annotation": True,
                "gene_annotation": True,
            },
        )

        self.assertFalse(report.runnable)
        self.assertIn("expression_matrix_missing", report.errors)
        self.assertEqual(report.recommended_action, "provide_expression_matrix")

    def test_missing_sample_annotation_adds_warning(self) -> None:
        report = build_dataset_asset_readiness_report(
            "GSE-missing-samples",
            {
                "expression_matrix": True,
                "gene_annotation": True,
            },
        )

        self.assertTrue(report.runnable)
        self.assertEqual(report.sample_annotation_status, DatasetAssetStatus.MISSING)
        self.assertIn("sample_annotation_missing", report.warnings)

    def test_missing_gene_annotation_adds_warning(self) -> None:
        report = build_dataset_asset_readiness_report(
            "GSE-missing-gene-annotation",
            {
                "expression_matrix": True,
                "sample_annotation": True,
            },
        )

        self.assertTrue(report.runnable)
        self.assertEqual(report.gene_annotation_status, DatasetAssetStatus.MISSING)
        self.assertIn("gene_annotation_missing", report.warnings)

    def test_suspicious_asset_adds_warning(self) -> None:
        report = build_dataset_asset_readiness_report(
            "GSE-suspicious",
            {
                "expression_matrix": {"status": "suspicious"},
                "sample_annotation": True,
                "gene_annotation": True,
            },
        )

        self.assertTrue(report.runnable)
        self.assertEqual(report.expression_matrix_status, DatasetAssetStatus.SUSPICIOUS)
        self.assertIn("expression_matrix_suspicious", report.warnings)
        self.assertEqual(report.recommended_action, "review_warnings_before_analysis")

    def test_empty_assets_have_stable_recommended_action(self) -> None:
        report = build_dataset_asset_readiness_report("GSE-empty", {})

        self.assertFalse(report.runnable)
        self.assertEqual(report.recommended_action, "provide_expression_matrix")
        self.assertEqual(report.platform_annotation_status, DatasetAssetStatus.NOT_APPLICABLE)
        self.assertEqual(report.clinical_annotation_status, DatasetAssetStatus.NOT_APPLICABLE)


if __name__ == "__main__":
    unittest.main()
