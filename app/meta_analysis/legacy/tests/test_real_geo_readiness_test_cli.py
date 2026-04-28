import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts.run_real_geo_readiness_test import main


FAKE_METADATA = """
Accession: GSE33630
Title: fake PTC dataset
Summary: fake saved GEO metadata
Organism: Homo sapiens
Samples: 3
Platform: GPL570
GSE33630_series_matrix.txt.gz
"""

FAKE_SERIES_MATRIX = """!Series_geo_accession\t"GSE33630"
!Series_platform_id\t"GPL570"
!Sample_title\t"PTC sample 1"\t"normal thyroid sample 1"\t"ATC sample 1"
!Sample_geo_accession\t"GSM001"\t"GSM002"\t"GSM003"
!Sample_source_name_ch1\t"papillary thyroid carcinoma"\t"normal thyroid"\t"anaplastic thyroid carcinoma"
!Sample_characteristics_ch1\t"disease: PTC"\t"disease: normal"\t"disease: ATC"
!series_matrix_table_begin
ID_REF\tGSM001\tGSM002\tGSM003
1007_s_at\t1.0\t2.0\t3.0
1053_at\t4.0\t5.0\t6.0
!series_matrix_table_end
"""

FAKE_PLATFORM = """ID\tGene Symbol
1007_s_at\tDDR1
1053_at\tRFC2
"""

FAKE_SOFT = """^SERIES = GSE27155
!Series_geo_accession = GSE27155
!Series_sample_id = GSM001
!Series_sample_id = GSM002
!Series_platform_id = GPL96
^PLATFORM = GPL96
!Platform_geo_accession = GPL96
!platform_table_begin
ID\tGene Symbol
1007_s_at\tDDR1
!platform_table_end
^SAMPLE = GSM001
!Sample_title = Papillary Thyroid Carcinoma Thy001
!Sample_geo_accession = GSM001
!Sample_source_name_ch1 = Papillary Thyroid Carcinoma
!Sample_characteristics_ch1 = tissue: Papillary Thyroid Carcinoma
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
"""


class RealGeoReadinessTestCliTests(unittest.TestCase):
    def test_help_runs(self) -> None:
        with self.assertRaises(SystemExit) as context:
            main(["--help"])

        self.assertEqual(context.exception.code, 0)

    def test_local_files_json_report_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            metadata = root / "metadata.html"
            series = root / "series_matrix.txt"
            platform = root / "GPL570.txt"
            metadata.write_text(FAKE_METADATA, encoding="utf-8")
            series.write_text(FAKE_SERIES_MATRIX, encoding="utf-8")
            platform.write_text(FAKE_PLATFORM, encoding="utf-8")
            buffer = io.StringIO()

            with redirect_stdout(buffer):
                result = main(
                    [
                        "--dataset-id",
                        "GSE33630",
                        "--metadata-file",
                        str(metadata),
                        "--series-matrix-file",
                        str(series),
                        "--platform-annotation-file",
                        str(platform),
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["dataset_id"], "GSE33630")
        self.assertEqual(payload["metadata_parse"]["gse_id"], "GSE33630")
        self.assertEqual(payload["series_matrix_metadata"]["sample_count"], 3)
        self.assertEqual(payload["expression_report"]["feature_count"], 2)
        self.assertEqual(payload["platform_mapping"]["mapped_probe_count"], 2)
        self.assertEqual(payload["preflight"]["runnable"], True)
        self.assertEqual(payload["gaps"], [])

    def test_output_dir_writes_small_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            metadata = root / "metadata.html"
            series = root / "series_matrix.txt"
            output_dir = root / "report"
            metadata.write_text(FAKE_METADATA, encoding="utf-8")
            series.write_text(FAKE_SERIES_MATRIX, encoding="utf-8")

            result = main(
                [
                    "--dataset-id",
                    "GSE33630",
                    "--metadata-file",
                    str(metadata),
                    "--series-matrix-file",
                    str(series),
                    "--output-dir",
                    str(output_dir),
                ]
            )

            json_path = output_dir / "readiness_report.json"
            markdown_path = output_dir / "readiness_report.md"
            self.assertEqual(result, 0)
            self.assertTrue(json_path.exists())
            self.assertTrue(markdown_path.exists())

    def test_missing_series_matrix_classifies_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata = Path(tmpdir) / "metadata.html"
            metadata.write_text(FAKE_METADATA, encoding="utf-8")
            buffer = io.StringIO()

            with redirect_stdout(buffer):
                result = main(
                    [
                        "--dataset-id",
                        "GSE33630",
                        "--metadata-file",
                        str(metadata),
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["metadata_parse"]["gse_id"], "GSE33630")
        self.assertEqual(payload["series_matrix_metadata"], {})

    def test_soft_file_report_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            soft = Path(tmpdir) / "family.soft"
            soft.write_text(FAKE_SOFT, encoding="utf-8")
            buffer = io.StringIO()

            with redirect_stdout(buffer):
                result = main(
                    [
                        "--dataset-id",
                        "GSE27155",
                        "--soft-file",
                        str(soft),
                        "--json",
                    ]
                )

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["dataset_id"], "GSE27155")
        self.assertEqual(payload["series_matrix_metadata"]["gse_id"], "GSE27155")
        self.assertEqual(payload["series_matrix_metadata"]["platform_ids"], ["GPL96"])
        self.assertEqual(payload["series_matrix_metadata"]["sample_count"], 2)
        self.assertEqual(payload["expression_report"]["feature_count"], 1)
        self.assertEqual(payload["expression_report"]["sample_id_match_status"], "match")
        self.assertEqual(payload["platform_mapping"]["platform_id"], "GPL96")
        self.assertEqual(payload["platform_mapping"]["mapped_probe_count"], 1)
        self.assertEqual(payload["group_detection"]["detected_groups"], ["ptc", "normal"])
        self.assertEqual(payload["gaps"], [])


if __name__ == "__main__":
    unittest.main()
