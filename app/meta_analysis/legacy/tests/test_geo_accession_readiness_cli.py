import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from geo_readiness.live_fetch import GeoMetadataFetchError

from scripts.run_geo_accession_readiness import main


GSE33630_METADATA = """
Accession: GSE33630
Title: normal thyrocytes vs papillary vs anaplastic thyroid carcinomas
Summary: Fake metadata fixture.
Organism: Homo sapiens
Samples: 105
Platform: GPL570
Download family: Series Matrix File(s)
GSE33630_series_matrix.txt.gz
Supplementary file: GSE33630_clinical-annotation.txt.gz 2.8 Kb
Processed data are included within the Sample table.
"""


class GeoAccessionReadinessCliTests(unittest.TestCase):
    def test_help_runs(self) -> None:
        with self.assertRaises(SystemExit) as context:
            main(["--help"])

        self.assertEqual(context.exception.code, 0)

    def test_metadata_file_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_path = Path(temp_dir) / "gse33630.txt"
            metadata_path.write_text(GSE33630_METADATA, encoding="utf-8")
            buffer = io.StringIO()

            with redirect_stdout(buffer):
                result = main(["--metadata-file", str(metadata_path), "--gse", "GSE33630"])

        output = buffer.getvalue()
        self.assertEqual(result, 0)
        self.assertIn("GEO accession readiness:", output)
        self.assertIn("- gse id: GSE33630", output)
        self.assertIn("- sample count: 105", output)
        self.assertIn("- platform ids: GPL570", output)

    def test_json_output_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_path = Path(temp_dir) / "gse33630.txt"
            metadata_path.write_text(GSE33630_METADATA, encoding="utf-8")
            buffer = io.StringIO()

            with redirect_stdout(buffer):
                result = main(["--metadata-file", str(metadata_path), "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(payload["gse_id"], "GSE33630")
        self.assertEqual(payload["sample_count"], 105)
        self.assertEqual(payload["platform_ids"], ["GPL570"])
        self.assertGreaterEqual(payload["series_matrix_candidates"], 1)
        self.assertGreaterEqual(payload["expression_candidates"], 1)
        self.assertEqual(payload["recommended_action"], "ready_for_candidate_inventory_review")

    def test_malformed_metadata_returns_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_path = Path(temp_dir) / "bad.txt"
            metadata_path.write_text("not a geo accession", encoding="utf-8")
            buffer = io.StringIO()

            with redirect_stdout(buffer):
                result = main(["--metadata-file", str(metadata_path), "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 1)
        self.assertIn("metadata_parse_failed", payload["errors"])

    def test_missing_metadata_file_returns_error(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["--gse", "GSE33630", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 1)
        self.assertEqual(payload["gse_id"], "GSE33630")
        self.assertIn("metadata_file_required", payload["errors"])

    def test_live_uses_mocked_fetch(self) -> None:
        buffer = io.StringIO()
        with patch(
            "scripts.run_geo_accession_readiness.fetch_geo_accession_metadata",
            return_value=GSE33630_METADATA,
        ) as fetch:
            with redirect_stdout(buffer):
                result = main(["--gse", "GSE33630", "--live", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 0)
        fetch.assert_called_once_with("GSE33630", timeout=15.0)
        self.assertEqual(payload["gse_id"], "GSE33630")
        self.assertEqual(payload["sample_count"], 105)

    def test_live_network_error_returns_stable_error(self) -> None:
        buffer = io.StringIO()
        with patch(
            "scripts.run_geo_accession_readiness.fetch_geo_accession_metadata",
            side_effect=GeoMetadataFetchError("network_unavailable", "offline"),
        ):
            with redirect_stdout(buffer):
                result = main(["--gse", "GSE33630", "--live", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 1)
        self.assertIn("network_unavailable", payload["errors"])
        self.assertIn("--metadata-file", payload["recommended_action"])

    def test_live_ssl_error_returns_stable_error(self) -> None:
        buffer = io.StringIO()
        with patch(
            "scripts.run_geo_accession_readiness.fetch_geo_accession_metadata",
            side_effect=GeoMetadataFetchError("ssl_error", "ssl failed"),
        ):
            with redirect_stdout(buffer):
                result = main(["--gse", "GSE33630", "--live", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 1)
        self.assertIn("ssl_error", payload["errors"])
        self.assertIn("local certificate/Python SSL environment", payload["recommended_action"])
        self.assertIn("--metadata-file", payload["recommended_action"])
        self.assertIn("do not disable SSL verification", payload["recommended_action"])

    def test_live_timeout_returns_stable_error(self) -> None:
        buffer = io.StringIO()
        with patch(
            "scripts.run_geo_accession_readiness.fetch_geo_accession_metadata",
            side_effect=GeoMetadataFetchError("fetch_timeout", "timed out"),
        ):
            with redirect_stdout(buffer):
                result = main(["--gse", "GSE33630", "--live", "--timeout", "3", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 1)
        self.assertIn("fetch_timeout", payload["errors"])
        self.assertIn("--timeout", payload["recommended_action"])

    def test_live_http_error_returns_stable_error(self) -> None:
        buffer = io.StringIO()
        with patch(
            "scripts.run_geo_accession_readiness.fetch_geo_accession_metadata",
            side_effect=GeoMetadataFetchError("http_error", "bad status"),
        ):
            with redirect_stdout(buffer):
                result = main(["--gse", "GSE33630", "--live", "--json"])

        payload = json.loads(buffer.getvalue())
        self.assertEqual(result, 1)
        self.assertIn("http_error", payload["errors"])
        self.assertIn("GEO accession page", payload["recommended_action"])


if __name__ == "__main__":
    unittest.main()
