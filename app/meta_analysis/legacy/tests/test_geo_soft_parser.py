import gzip
import tempfile
import unittest
from pathlib import Path

from geo_readiness.soft_parser import (
    parse_geo_soft_expression_report,
    parse_geo_soft_metadata,
    parse_geo_soft_platform_mapping_report,
)


FAKE_SOFT = """^DATABASE = GeoMiame
^SERIES = GSE27155
!Series_title = Human thyroid adenomas, carcinomas, and normals
!Series_geo_accession = GSE27155
!Series_sample_id = GSM001
!Series_sample_id = GSM002
!Series_sample_id = GSM003
!Series_platform_id = GPL96
^PLATFORM = GPL96
!Platform_geo_accession = GPL96
!platform_table_begin
ID\tGene Symbol
1007_s_at\tDDR1
1053_at\tRFC2
117_at\t---
!platform_table_end
^SAMPLE = GSM001
!Sample_title = Papillary Thyroid Carcinoma Thy001
!Sample_geo_accession = GSM001
!Sample_source_name_ch1 = Papillary Thyroid Carcinoma
!Sample_characteristics_ch1 = tissue: Papillary Thyroid Carcinoma
!Sample_characteristics_ch1 = morphology of papillary carcinomas: classical
!Sample_platform_id = GPL96
!sample_table_begin
ID_REF\tVALUE
1007_s_at\t1.0
!sample_table_end
^SAMPLE = GSM002
!Sample_title = Normal Thyroid Thy002
!Sample_geo_accession = GSM002
!Sample_source_name_ch1 = Normal Thyroid
!Sample_characteristics_ch1 = tissue: Normal Thyroid
!Sample_platform_id = GPL96
!sample_table_begin
ID_REF\tVALUE
1007_s_at\t2.0
!sample_table_end
^SAMPLE = GSM003
!Sample_title = Follicular Thyroid Carcinoma Thy003
!Sample_geo_accession = GSM003
!Sample_source_name_ch1 = Follicular Thyroid Carcinoma
!Sample_characteristics_ch1 = tissue: Follicular Thyroid Carcinoma
!Sample_platform_id = GPL96
!sample_table_begin
ID_REF\tVALUE
1007_s_at\t3.0
!sample_table_end
"""


class GeoSoftParserTests(unittest.TestCase):
    def test_fake_soft_parses_series_and_samples(self) -> None:
        report = parse_geo_soft_metadata(FAKE_SOFT)

        self.assertEqual(report.gse_id, "GSE27155")
        self.assertEqual(report.platform_ids, ["GPL96"])
        self.assertEqual(report.sample_ids, ["GSM001", "GSM002", "GSM003"])
        self.assertEqual(report.sample_count, 3)
        self.assertEqual(report.errors, [])

    def test_fake_soft_parses_sample_metadata_rows(self) -> None:
        report = parse_geo_soft_metadata(FAKE_SOFT)

        self.assertIn("title", report.sample_metadata_columns)
        self.assertIn("source_name_ch1", report.sample_metadata_columns)
        self.assertIn("characteristics_ch1", report.sample_metadata_columns)
        self.assertEqual(
            report.sample_metadata_rows[0]["title"],
            "Papillary Thyroid Carcinoma Thy001",
        )
        self.assertIn(
            "morphology of papillary carcinomas",
            report.sample_metadata_rows[0]["characteristics_ch1"],
        )

    def test_group_hints_include_multiclass_labels(self) -> None:
        report = parse_geo_soft_metadata(FAKE_SOFT)

        self.assertIn("papillary_thyroid_carcinoma", report.group_hints)
        self.assertIn("normal", report.group_hints)
        self.assertIn("follicular_thyroid_carcinoma", report.group_hints)

    def test_local_gzip_file_parses(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "family.soft.gz"
            with gzip.open(path, "wt", encoding="utf-8") as handle:
                handle.write(FAKE_SOFT)

            report = parse_geo_soft_metadata(path)

        self.assertEqual(report.gse_id, "GSE27155")
        self.assertEqual(report.sample_count, 3)

    def test_malformed_soft_returns_stable_error(self) -> None:
        report = parse_geo_soft_metadata("not geo soft")

        self.assertIn("geo_soft_metadata_not_found", report.errors)

    def test_sample_table_values_are_not_reported_as_metadata(self) -> None:
        report = parse_geo_soft_metadata(FAKE_SOFT)

        payload = report.to_dict()
        self.assertNotIn("1.0", str(payload["sample_metadata_rows"]))
        self.assertNotIn("1007_s_at", str(payload["sample_metadata_rows"]))

    def test_expression_report_counts_soft_sample_tables(self) -> None:
        metadata = parse_geo_soft_metadata(FAKE_SOFT)
        report = parse_geo_soft_expression_report(
            FAKE_SOFT,
            metadata_sample_ids=metadata.sample_ids,
        )

        self.assertEqual(report.feature_count, 1)
        self.assertEqual(report.sample_count, 3)
        self.assertEqual(report.feature_id_column, "ID_REF")
        self.assertEqual(report.matrix_sample_ids, ["GSM001", "GSM002", "GSM003"])
        self.assertEqual(report.numeric_value_status, "numeric")
        self.assertEqual(report.sample_id_match_status, "match")
        self.assertEqual(report.errors, [])

    def test_expression_report_flags_non_numeric_values(self) -> None:
        matrix = FAKE_SOFT.replace("1007_s_at\t2.0", "1007_s_at\tnot_numeric", 1)

        report = parse_geo_soft_expression_report(
            matrix,
            metadata_sample_ids=["GSM001", "GSM002", "GSM003"],
        )

        self.assertEqual(report.numeric_value_status, "non_numeric")
        self.assertIn("non_numeric_expression_values", report.errors)

    def test_expression_report_counts_missing_values(self) -> None:
        matrix = FAKE_SOFT.replace("1007_s_at\t3.0", "1007_s_at\t")

        report = parse_geo_soft_expression_report(
            matrix,
            metadata_sample_ids=["GSM001", "GSM002", "GSM003"],
        )

        self.assertEqual(report.numeric_value_status, "numeric_with_missing")
        self.assertEqual(report.missing_value_count, 1)
        self.assertIn("missing_expression_values", report.warnings)

    def test_expression_report_detects_sample_mismatch(self) -> None:
        report = parse_geo_soft_expression_report(
            FAKE_SOFT,
            metadata_sample_ids=["GSM001", "GSM999", "GSM003"],
        )

        self.assertEqual(report.sample_id_match_status, "mismatch")
        self.assertIn("matrix_metadata_sample_id_mismatch", report.errors)

    def test_expression_report_handles_missing_sample_tables(self) -> None:
        report = parse_geo_soft_expression_report("^SERIES = GSE27155")

        self.assertIn("geo_soft_sample_table_not_found", report.errors)
        self.assertEqual(report.numeric_value_status, "not_checked")

    def test_platform_mapping_report_uses_embedded_soft_platform_table(self) -> None:
        report = parse_geo_soft_platform_mapping_report(
            FAKE_SOFT,
            platform_id="GPL96",
            minimum_success_rate=0.5,
        )

        self.assertEqual(report.platform_id, "GPL96")
        self.assertEqual(report.probe_count, 3)
        self.assertEqual(report.mapped_probe_count, 2)
        self.assertEqual(report.unmapped_probe_count, 1)
        self.assertEqual(report.mapping_success_rate, 0.6667)
        self.assertTrue(report.acceptable)

    def test_platform_mapping_report_handles_missing_platform_table(self) -> None:
        report = parse_geo_soft_platform_mapping_report("^SERIES = GSE27155")

        self.assertIn("geo_soft_platform_table_not_found", report.errors)


if __name__ == "__main__":
    unittest.main()
