import gzip
import tempfile
import unittest
from pathlib import Path

from geo_readiness.series_matrix_parser import (
    parse_series_matrix_expression_report,
    parse_series_matrix_metadata,
)


FAKE_SERIES_MATRIX = """!Series_title\t"GSE33630 fake fixture"
!Series_geo_accession\t"GSE33630"
!Series_platform_id\t"GPL570"
!Sample_title\t"PTC sample 1"\t"normal thyroid sample 1"\t"ATC sample 1"
!Sample_geo_accession\t"GSM001"\t"GSM002"\t"GSM003"
!Sample_platform_id\t"GPL570"\t"GPL570"\t"GPL570"
!Sample_source_name_ch1\t"papillary thyroid carcinoma"\t"normal thyroid"\t"anaplastic thyroid carcinoma"
!Sample_characteristics_ch1\t"disease: PTC"\t"disease: normal"\t"disease: ATC"
!Sample_characteristics_ch1\t"tissue: thyroid"\t"tissue: thyroid"\t"tissue: thyroid"
!series_matrix_table_begin
ID_REF\tGSM001\tGSM002\tGSM003
1007_s_at\t1.0\t2.0\t3.0
!series_matrix_table_end
"""


class SeriesMatrixParserTests(unittest.TestCase):
    def test_fake_series_matrix_parses_accession_and_samples(self) -> None:
        report = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)

        self.assertEqual(report.gse_id, "GSE33630")
        self.assertEqual(report.sample_ids, ["GSM001", "GSM002", "GSM003"])
        self.assertEqual(report.sample_count, 3)
        self.assertEqual(report.platform_ids, ["GPL570"])
        self.assertEqual(report.errors, [])

    def test_parses_title_source_and_characteristics_rows(self) -> None:
        report = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)

        self.assertIn("title", report.sample_metadata_columns)
        self.assertIn("source_name_ch1", report.sample_metadata_columns)
        self.assertIn("characteristics_ch1", report.sample_metadata_columns)
        self.assertEqual(report.sample_metadata_rows[0]["title"], "PTC sample 1")
        self.assertEqual(
            report.sample_metadata_rows[0]["source_name_ch1"],
            "papillary thyroid carcinoma",
        )
        self.assertIn("disease: PTC", report.sample_metadata_rows[0]["characteristics_ch1"])
        self.assertIn("tissue: thyroid", report.sample_metadata_rows[0]["characteristics_ch1"])

    def test_group_hints_are_metadata_only(self) -> None:
        report = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)

        self.assertIn("papillary_thyroid_carcinoma", report.group_hints)
        self.assertIn("normal", report.group_hints)
        self.assertIn("anaplastic_thyroid_carcinoma", report.group_hints)

    def test_local_txt_file_parses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "series_matrix.txt"
            path.write_text(FAKE_SERIES_MATRIX, encoding="utf-8")

            report = parse_series_matrix_metadata(path)

        self.assertEqual(report.gse_id, "GSE33630")
        self.assertEqual(report.sample_count, 3)

    def test_local_gzip_file_parses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "series_matrix.txt.gz"
            with gzip.open(path, "wt", encoding="utf-8") as handle:
                handle.write(FAKE_SERIES_MATRIX)

            report = parse_series_matrix_metadata(path)

        self.assertEqual(report.gse_id, "GSE33630")
        self.assertEqual(report.sample_count, 3)

    def test_malformed_input_returns_error(self) -> None:
        report = parse_series_matrix_metadata("not a series matrix")

        self.assertIn("series_matrix_metadata_not_found", report.errors)

    def test_numeric_matrix_values_are_not_parsed(self) -> None:
        report = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)

        for row in report.sample_metadata_rows:
            self.assertNotIn("1007_s_at", row.values())
            self.assertNotIn("1.0", row.values())

    def test_expression_report_counts_features_and_samples(self) -> None:
        metadata = parse_series_matrix_metadata(FAKE_SERIES_MATRIX)
        report = parse_series_matrix_expression_report(
            FAKE_SERIES_MATRIX,
            metadata_sample_ids=metadata.sample_ids,
        )

        self.assertEqual(report.feature_count, 1)
        self.assertEqual(report.sample_count, 3)
        self.assertEqual(report.feature_id_column, "ID_REF")
        self.assertEqual(report.matrix_sample_ids, ["GSM001", "GSM002", "GSM003"])
        self.assertEqual(report.numeric_value_status, "numeric")
        self.assertEqual(report.missing_value_count, 0)
        self.assertEqual(report.negative_value_count, 0)
        self.assertEqual(report.sample_id_match_status, "match")
        self.assertEqual(report.errors, [])

    def test_expression_report_flags_non_numeric_values(self) -> None:
        matrix = FAKE_SERIES_MATRIX.replace("2.0", "not_numeric")
        report = parse_series_matrix_expression_report(
            matrix,
            metadata_sample_ids=["GSM001", "GSM002", "GSM003"],
        )

        self.assertEqual(report.numeric_value_status, "non_numeric")
        self.assertIn("non_numeric_expression_values", report.errors)

    def test_expression_report_counts_missing_values(self) -> None:
        matrix = FAKE_SERIES_MATRIX.replace(
            "1007_s_at\t1.0\t2.0\t3.0",
            "1007_s_at\t1.0\t\t3.0",
        )
        report = parse_series_matrix_expression_report(
            matrix,
            metadata_sample_ids=["GSM001", "GSM002", "GSM003"],
        )

        self.assertEqual(report.numeric_value_status, "numeric_with_missing")
        self.assertEqual(report.missing_value_count, 1)
        self.assertIn("missing_expression_values", report.warnings)

    def test_expression_report_detects_sample_id_mismatch(self) -> None:
        report = parse_series_matrix_expression_report(
            FAKE_SERIES_MATRIX,
            metadata_sample_ids=["GSM001", "GSM999", "GSM003"],
        )

        self.assertEqual(report.sample_id_match_status, "mismatch")
        self.assertIn("matrix_metadata_sample_id_mismatch", report.errors)

    def test_expression_report_handles_missing_table(self) -> None:
        report = parse_series_matrix_expression_report("not a series matrix")

        self.assertIn("series_matrix_table_not_found", report.errors)
        self.assertEqual(report.numeric_value_status, "not_checked")

    def test_expression_report_does_not_return_full_matrix(self) -> None:
        report = parse_series_matrix_expression_report(
            FAKE_SERIES_MATRIX,
            metadata_sample_ids=["GSM001", "GSM002", "GSM003"],
        )

        payload = report.to_dict()
        self.assertNotIn("matrix", payload)
        self.assertNotIn("values", payload)


if __name__ == "__main__":
    unittest.main()
