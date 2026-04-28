import unittest

from analysis.analysis_preflight import build_analysis_preflight_summary
from analysis.analysis_preflight import (
    build_geo_series_matrix_preflight_summary,
    format_analysis_preflight_summary,
    summarize_analysis_preflight_summaries,
)
from analysis.comparison_readiness import build_comparison_readiness_report
from analysis.group_detection import detect_geo_sample_groups
from core.dataset_readiness import (
    build_dataset_asset_readiness_report,
    build_gene_mapping_readiness_report,
    build_sample_mapping_readiness_report,
)
from geo_readiness.series_matrix_parser import (
    parse_series_matrix_expression_report,
    parse_series_matrix_metadata,
)
from geo_readiness.platform_annotation_parser import (
    parse_platform_annotation_mapping_report,
)


FAKE_SERIES_MATRIX = """!Series_geo_accession\t"GSE33630"
!Series_platform_id\t"GPL570"
!Sample_title\t"PTC sample 1"\t"normal thyroid sample 1"\t"ATC sample 1"
!Sample_geo_accession\t"GSM001"\t"GSM002"\t"GSM003"
!Sample_source_name_ch1\t"papillary thyroid carcinoma"\t"normal thyroid"\t"anaplastic thyroid carcinoma"
!Sample_characteristics_ch1\t"disease: PTC"\t"disease: normal"\t"disease: ATC"
!series_matrix_table_begin
ID_REF\tGSM001\tGSM002\tGSM003
1007_s_at\t1.0\t2.0\t3.0
!series_matrix_table_end
"""


def _comparison_report(case: int = 2, control: int = 2):
    metadata = [
        *({"sample_id": f"C{i}", "group": "case"} for i in range(case)),
        *({"sample_id": f"N{i}", "group": "control"} for i in range(control)),
    ]
    return build_comparison_readiness_report(
        metadata,
        {"group_column": "group", "case_group": "case", "control_group": "control"},
    )


class AnalysisPreflightTests(unittest.TestCase):
    def test_format_analysis_preflight_summary_empty_state_is_stable(self) -> None:
        self.assertEqual(
            format_analysis_preflight_summary(None),
            [
                "Analysis preflight readiness summary:",
                "- total checks: 0",
                "- runnable checks: 0",
                "- blocked checks: 0",
                "- warning count: 0",
                "- blocking error count: 0",
            ],
        )

    def test_all_readiness_acceptable_is_runnable(self) -> None:
        summary = build_analysis_preflight_summary(
            dataset_id="GSE-ready",
            profile_id="profile-a",
            asset_readiness=build_dataset_asset_readiness_report(
                "GSE-ready",
                {"expression_matrix": True, "sample_annotation": True, "gene_annotation": True},
            ),
            gene_mapping_readiness=build_gene_mapping_readiness_report(
                ["TP53", "EGFR"],
                input_id_type="gene_symbol",
                target_id_type="gene_symbol",
            ),
            sample_mapping_readiness=build_sample_mapping_readiness_report(
                ["S1", "S2"],
                ["S1", "S2"],
            ),
            comparison_readiness=_comparison_report(),
        )

        self.assertTrue(summary.runnable)
        self.assertEqual(summary.recommended_action, "ready_for_analysis")

    def test_missing_expression_matrix_blocks_preflight(self) -> None:
        summary = build_analysis_preflight_summary(
            dataset_id="GSE-no-expression",
            profile_id="profile-a",
            asset_readiness=build_dataset_asset_readiness_report("GSE-no-expression", {}),
            gene_mapping_readiness=build_gene_mapping_readiness_report(
                ["TP53"],
                input_id_type="gene_symbol",
            ),
            sample_mapping_readiness=build_sample_mapping_readiness_report(["S1"], ["S1"]),
            comparison_readiness=_comparison_report(),
        )

        self.assertFalse(summary.runnable)
        self.assertIn("asset:expression_matrix_missing", summary.blocking_errors)
        self.assertEqual(summary.recommended_action, "provide_expression_matrix")

    def test_unacceptable_sample_mapping_blocks_preflight(self) -> None:
        summary = build_analysis_preflight_summary(
            dataset_id="GSE-bad-samples",
            profile_id="profile-a",
            asset_readiness=build_dataset_asset_readiness_report(
                "GSE-bad-samples",
                {"expression_matrix": True, "sample_annotation": True, "gene_annotation": True},
            ),
            gene_mapping_readiness=build_gene_mapping_readiness_report(
                ["TP53"],
                input_id_type="gene_symbol",
            ),
            sample_mapping_readiness=build_sample_mapping_readiness_report(
                ["S1", "S2", "S3"],
                ["S1"],
            ),
            comparison_readiness=_comparison_report(),
        )

        self.assertFalse(summary.runnable)
        self.assertIn("sample_mapping:sample_match_rate_too_low", summary.blocking_errors)
        self.assertEqual(summary.recommended_action, "fix_sample_mapping")

    def test_unrunnable_comparison_blocks_preflight(self) -> None:
        summary = build_analysis_preflight_summary(
            dataset_id="GSE-bad-comparison",
            profile_id="profile-a",
            asset_readiness=build_dataset_asset_readiness_report(
                "GSE-bad-comparison",
                {"expression_matrix": True, "sample_annotation": True, "gene_annotation": True},
            ),
            gene_mapping_readiness=build_gene_mapping_readiness_report(
                ["TP53"],
                input_id_type="gene_symbol",
            ),
            sample_mapping_readiness=build_sample_mapping_readiness_report(["S1"], ["S1"]),
            comparison_readiness=build_comparison_readiness_report(
                [{"sample_id": "S1", "group": "case"}],
                {"group_column": "group", "case_group": "case", "control_group": "control"},
            ),
        )

        self.assertFalse(summary.runnable)
        self.assertIn("comparison:control_group_has_no_samples", summary.blocking_errors)
        self.assertEqual(summary.recommended_action, "fix_comparison_definition")

    def test_gene_mapping_warning_does_not_block_if_acceptable(self) -> None:
        summary = build_analysis_preflight_summary(
            dataset_id="GSE-gene-warning",
            profile_id="profile-a",
            asset_readiness=build_dataset_asset_readiness_report(
                "GSE-gene-warning",
                {"expression_matrix": True, "sample_annotation": True, "gene_annotation": True},
            ),
            gene_mapping_readiness=build_gene_mapping_readiness_report(
                ["probe-a", "probe-b"],
                {"probe-a": "TP53", "probe-b": "EGFR"},
                input_id_type="probe_id",
            ),
            sample_mapping_readiness=build_sample_mapping_readiness_report(["S1"], ["S1"]),
            comparison_readiness=_comparison_report(),
        )

        self.assertTrue(summary.runnable)
        self.assertIn("gene_mapping:probe_identifier_mapping_required", summary.warnings)
        self.assertEqual(summary.recommended_action, "review_warnings_before_analysis")

    def test_unacceptable_gene_mapping_blocks_preflight(self) -> None:
        summary = build_analysis_preflight_summary(
            dataset_id="GSE-bad-gene-map",
            profile_id="profile-a",
            asset_readiness=build_dataset_asset_readiness_report(
                "GSE-bad-gene-map",
                {"expression_matrix": True, "sample_annotation": True, "gene_annotation": True},
            ),
            gene_mapping_readiness=build_gene_mapping_readiness_report(
                ["a", "b", "c"],
                {"a": "TP53"},
                input_id_type="custom_id",
            ),
            sample_mapping_readiness=build_sample_mapping_readiness_report(["S1"], ["S1"]),
            comparison_readiness=_comparison_report(),
        )

        self.assertFalse(summary.runnable)
        self.assertIn("gene_mapping:mapping_success_rate_too_low", summary.blocking_errors)
        self.assertEqual(summary.recommended_action, "fix_gene_mapping")

    def test_preflight_summary_counts_runnable_and_blocked(self) -> None:
        runnable = build_analysis_preflight_summary(
            dataset_id="GSE-ready",
            profile_id="profile-a",
            asset_readiness=build_dataset_asset_readiness_report(
                "GSE-ready",
                {"expression_matrix": True, "sample_annotation": True, "gene_annotation": True},
            ),
            gene_mapping_readiness=build_gene_mapping_readiness_report(
                ["probe-a"],
                {"probe-a": "TP53"},
                input_id_type="probe_id",
            ),
            sample_mapping_readiness=build_sample_mapping_readiness_report(["S1"], ["S1"]),
            comparison_readiness=_comparison_report(),
        )
        blocked = build_analysis_preflight_summary(
            dataset_id="GSE-blocked",
            profile_id="profile-a",
            asset_readiness=build_dataset_asset_readiness_report("GSE-blocked", {}),
            gene_mapping_readiness=build_gene_mapping_readiness_report(
                ["TP53"],
                input_id_type="gene_symbol",
            ),
            sample_mapping_readiness=build_sample_mapping_readiness_report(["S1"], ["S1"]),
            comparison_readiness=_comparison_report(),
        )

        summary = summarize_analysis_preflight_summaries([runnable, blocked])

        self.assertEqual(summary["total_checks"], 2)
        self.assertEqual(summary["runnable_checks"], 1)
        self.assertEqual(summary["blocked_checks"], 1)
        self.assertEqual(summary["warning_count"], 3)
        self.assertEqual(summary["blocking_error_count"], 1)

    def test_geo_series_matrix_metadata_only_preflight_blocks_expression_values(self) -> None:
        metadata = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)
        groups = detect_geo_sample_groups(metadata.sample_metadata_rows)

        summary = build_geo_series_matrix_preflight_summary(
            series_matrix_metadata=metadata,
            group_detection=groups,
        )

        self.assertFalse(summary.runnable)
        self.assertIn("expression_matrix_values_not_parsed", summary.blocking_errors)
        self.assertEqual(
            summary.recommended_action,
            "parse_expression_matrix_values_before_analysis",
        )

    def test_geo_series_matrix_group_detection_warnings_feed_preflight(self) -> None:
        metadata = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)
        groups = detect_geo_sample_groups(metadata.sample_metadata_rows)

        summary = build_geo_series_matrix_preflight_summary(
            series_matrix_metadata=metadata,
            group_detection=groups,
        )

        self.assertIn("comparison:ptc_vs_normal_candidate_detected", summary.warnings)
        self.assertIn("group_detection:atc_samples_excluded_from_candidate", summary.warnings)

    def test_geo_series_matrix_preflight_does_not_create_external_outputs(self) -> None:
        metadata = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)
        groups = detect_geo_sample_groups(metadata.sample_metadata_rows)

        summary = build_geo_series_matrix_preflight_summary(
            series_matrix_metadata=metadata,
            group_detection=groups,
        )

        self.assertEqual(summary.dataset_id, "GSE33630")
        self.assertNotIn("result_id", summary.to_dict())
        self.assertNotIn("artifact_path", summary.to_dict())

    def test_geo_series_matrix_expression_report_clears_expression_blocker(self) -> None:
        metadata = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)
        expression = parse_series_matrix_expression_report(
            FAKE_SERIES_MATRIX,
            metadata_sample_ids=metadata.sample_ids,
        )
        groups = detect_geo_sample_groups(metadata.sample_metadata_rows)

        summary = build_geo_series_matrix_preflight_summary(
            series_matrix_metadata=metadata,
            group_detection=groups,
            expression_report=expression,
        )

        self.assertNotIn("expression_matrix_values_not_parsed", summary.blocking_errors)
        self.assertTrue(summary.runnable)
        self.assertIn("asset:gene_annotation_missing", summary.warnings)
        self.assertIn("gene_mapping:probe_identifier_mapping_required", summary.warnings)

    def test_geo_series_matrix_expression_sample_mismatch_blocks_preflight(self) -> None:
        metadata = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)
        expression = parse_series_matrix_expression_report(
            FAKE_SERIES_MATRIX,
            metadata_sample_ids=["GSM001", "GSM999", "GSM003"],
        )
        groups = detect_geo_sample_groups(metadata.sample_metadata_rows)

        summary = build_geo_series_matrix_preflight_summary(
            series_matrix_metadata=metadata,
            group_detection=groups,
            expression_report=expression,
        )

        self.assertFalse(summary.runnable)
        self.assertIn(
            "expression_matrix:matrix_metadata_sample_id_mismatch",
            summary.blocking_errors,
        )

    def test_geo_series_matrix_non_numeric_expression_blocks_preflight(self) -> None:
        matrix = FAKE_SERIES_MATRIX.replace("2.0", "not_numeric")
        metadata = parse_series_matrix_metadata(matrix)
        expression = parse_series_matrix_expression_report(
            matrix,
            metadata_sample_ids=metadata.sample_ids,
        )
        groups = detect_geo_sample_groups(metadata.sample_metadata_rows)

        summary = build_geo_series_matrix_preflight_summary(
            series_matrix_metadata=metadata,
            group_detection=groups,
            expression_report=expression,
        )

        self.assertFalse(summary.runnable)
        self.assertIn(
            "expression_matrix:non_numeric_expression_values",
            summary.blocking_errors,
        )

    def test_geo_series_matrix_platform_mapping_clears_probe_mapping_warning(self) -> None:
        metadata = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)
        expression = parse_series_matrix_expression_report(
            FAKE_SERIES_MATRIX,
            metadata_sample_ids=metadata.sample_ids,
        )
        platform_mapping = parse_platform_annotation_mapping_report(
            "ID\tGene Symbol\n1007_s_at\tDDR1\n1053_at\tRFC2\n"
        )
        groups = detect_geo_sample_groups(metadata.sample_metadata_rows)

        summary = build_geo_series_matrix_preflight_summary(
            series_matrix_metadata=metadata,
            group_detection=groups,
            expression_report=expression,
            platform_mapping_report=platform_mapping,
        )

        self.assertTrue(summary.runnable)
        self.assertNotIn("asset:gene_annotation_missing", summary.warnings)
        self.assertNotIn("gene_mapping:probe_identifier_mapping_required", summary.warnings)

    def test_geo_series_matrix_unacceptable_platform_mapping_blocks_preflight(self) -> None:
        metadata = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)
        expression = parse_series_matrix_expression_report(
            FAKE_SERIES_MATRIX,
            metadata_sample_ids=metadata.sample_ids,
        )
        platform_mapping = parse_platform_annotation_mapping_report(
            "ID\tGene Symbol\n1007_s_at\t---\n1053_at\t\n"
        )
        groups = detect_geo_sample_groups(metadata.sample_metadata_rows)

        summary = build_geo_series_matrix_preflight_summary(
            series_matrix_metadata=metadata,
            group_detection=groups,
            expression_report=expression,
            platform_mapping_report=platform_mapping,
        )

        self.assertFalse(summary.runnable)
        self.assertIn(
            "platform_mapping:mapping_success_rate_too_low",
            summary.blocking_errors,
        )


if __name__ == "__main__":
    unittest.main()
