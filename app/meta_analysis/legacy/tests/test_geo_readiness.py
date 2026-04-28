from __future__ import annotations

import unittest

from local_data.geo_readiness import (
    GeoSubmissionReadinessLevel,
    build_geo_submission_readiness_report,
)


class GeoSubmissionReadinessTests(unittest.TestCase):
    def test_complete_package_is_likely_ready(self) -> None:
        report = build_geo_submission_readiness_report(
            has_raw_fastq=True,
            has_processed_count_matrix=True,
            has_sample_metadata=True,
            has_gene_annotation=True,
            has_sample_to_raw_file_mapping=True,
            has_reference_genome_info=True,
            has_annotation_version_info=True,
            has_processing_software_info=True,
            expression_samples=["S1", "S2"],
            metadata_samples=["S2", "S1"],
        )

        self.assertEqual(
            report.readiness_level,
            GeoSubmissionReadinessLevel.LIKELY_READY_FOR_MANUAL_GEO_SUBMISSION,
        )
        self.assertEqual(report.errors, [])
        self.assertEqual(report.warnings, [])

    def test_missing_processed_expression_is_insufficient(self) -> None:
        report = build_geo_submission_readiness_report(
            has_sample_metadata=True,
            expression_samples=[],
            metadata_samples=["S1"],
        )

        self.assertEqual(report.readiness_level, GeoSubmissionReadinessLevel.INSUFFICIENT)
        self.assertIn("processed_expression_matrix_missing", report.errors)

    def test_missing_sample_metadata_is_insufficient(self) -> None:
        report = build_geo_submission_readiness_report(
            has_processed_count_matrix=True,
            expression_samples=["S1"],
            metadata_samples=[],
        )

        self.assertEqual(report.readiness_level, GeoSubmissionReadinessLevel.INSUFFICIENT)
        self.assertIn("sample_metadata_missing", report.errors)

    def test_sample_mismatch_is_error(self) -> None:
        report = build_geo_submission_readiness_report(
            has_processed_count_matrix=True,
            has_sample_metadata=True,
            expression_samples=["S1", "S2"],
            metadata_samples=["S1", "S3"],
        )

        self.assertEqual(report.readiness_level, GeoSubmissionReadinessLevel.INSUFFICIENT)
        self.assertIn("expression_metadata_sample_mismatch", report.errors)

    def test_missing_fastq_and_submission_metadata_make_partial(self) -> None:
        report = build_geo_submission_readiness_report(
            has_processed_count_matrix=True,
            has_sample_metadata=True,
            has_gene_annotation=True,
            expression_samples=["S1"],
            metadata_samples=["S1"],
        )

        self.assertEqual(report.readiness_level, GeoSubmissionReadinessLevel.PARTIAL)
        self.assertIn("raw_fastq_missing", report.warnings)
        self.assertIn("reference_genome_info_missing", report.warnings)
        self.assertIn("annotation_version_info_missing", report.warnings)
        self.assertIn("processing_software_info_missing", report.warnings)

    def test_raw_fastq_without_mapping_warns(self) -> None:
        report = build_geo_submission_readiness_report(
            has_raw_fastq=True,
            has_processed_count_matrix=True,
            has_sample_metadata=True,
            has_gene_annotation=True,
            has_reference_genome_info=True,
            has_annotation_version_info=True,
            has_processing_software_info=True,
            expression_samples=["S1"],
            metadata_samples=["S1"],
        )

        self.assertEqual(report.readiness_level, GeoSubmissionReadinessLevel.PARTIAL)
        self.assertIn("sample_to_raw_file_mapping_missing", report.warnings)

    def test_human_subject_data_triggers_privacy_warning(self) -> None:
        report = build_geo_submission_readiness_report(
            has_raw_fastq=True,
            has_processed_count_matrix=True,
            has_sample_metadata=True,
            has_gene_annotation=True,
            has_sample_to_raw_file_mapping=True,
            has_reference_genome_info=True,
            has_annotation_version_info=True,
            has_processing_software_info=True,
            expression_samples=["S1"],
            metadata_samples=["S1"],
            is_human_subject_data=True,
        )

        self.assertTrue(report.has_human_subject_privacy_warning)
        self.assertIn("human_subject_privacy_review_required", report.warnings)
        self.assertEqual(report.readiness_level, GeoSubmissionReadinessLevel.PARTIAL)

    def test_normalized_expression_matrix_counts_as_processed_expression(self) -> None:
        report = build_geo_submission_readiness_report(
            has_raw_fastq=True,
            has_normalized_expression_matrix=True,
            has_sample_metadata=True,
            has_gene_annotation=True,
            has_sample_to_raw_file_mapping=True,
            has_reference_genome_info=True,
            has_annotation_version_info=True,
            has_processing_software_info=True,
            expression_samples=["S1"],
            metadata_samples=["S1"],
        )

        self.assertEqual(
            report.readiness_level,
            GeoSubmissionReadinessLevel.LIKELY_READY_FOR_MANUAL_GEO_SUBMISSION,
        )

    def test_to_dict_is_stable(self) -> None:
        report = build_geo_submission_readiness_report(
            has_processed_count_matrix=True,
            has_sample_metadata=True,
            expression_samples=["S1"],
            metadata_samples=["S1"],
        )

        payload = report.to_dict()

        self.assertTrue(payload["has_processed_count_matrix"])
        self.assertEqual(payload["readiness_level"], "partial")
        self.assertIn("raw_fastq_missing", payload["warnings"])


if __name__ == "__main__":
    unittest.main()
