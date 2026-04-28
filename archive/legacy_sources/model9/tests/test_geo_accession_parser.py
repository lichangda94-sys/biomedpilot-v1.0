import unittest

from geo_readiness.accession_parser import parse_geo_accession_metadata


GSE33630_LIKE_METADATA = """
Accession: GSE33630
Title: normal thyrocytes vs papillary vs anaplastic thyroid carcinomas
Summary: Fake GEO-like metadata for controlled readiness tests.
Organism: Homo sapiens
Samples: 105
Platform: GPL570
Download family: Series Matrix File(s)
GSE33630_series_matrix.txt.gz
Supplementary file: GSE33630_RAW.tar 849.1 Mb
Supplementary file: GSE33630_clinical-annotation.txt.gz 2.8 Kb
Processed data are included within the Sample table.
"""

GSE33630_LIKE_HTML = """
<html>
<body>
<table>
<tr><td>Accession</td><td>GSE33630</td></tr>
<tr><td>Title</td><td>normal thyrocytes vs papillary vs anaplastic thyroid carcinomas</td></tr>
<tr><td>Summary</td><td>HTML metadata fixture for controlled readiness tests.</td></tr>
<tr><td>Organism</td><td>Homo sapiens</td></tr>
<tr><td>Samples (105)</td><td>expandable sample table</td></tr>
<tr><td>Platforms</td><td>GPL570</td></tr>
</table>
<a href="GSE33630_series_matrix.txt.gz">Series Matrix File(s)</a>
<a href="GSE33630_clinical-annotation.txt.gz">GSE33630_clinical-annotation.txt.gz</a>
<a href="GSE33630_RAW.tar">GSE33630_RAW.tar</a>
<p>Processed data are included within the Sample table.</p>
</body>
</html>
"""


class GeoAccessionParserTests(unittest.TestCase):
    def test_minimal_gse33630_like_fixture_parses(self) -> None:
        inventory = parse_geo_accession_metadata(GSE33630_LIKE_METADATA)

        self.assertEqual(inventory.gse_id, "GSE33630")
        self.assertIn("papillary", inventory.title)
        self.assertEqual(inventory.organism, "Homo sapiens")
        self.assertEqual(inventory.errors, [])

    def test_platform_and_sample_count_are_extracted(self) -> None:
        inventory = parse_geo_accession_metadata(GSE33630_LIKE_METADATA)

        self.assertEqual(inventory.sample_count, 105)
        self.assertEqual(inventory.platform_ids, ["GPL570"])

    def test_supplementary_and_series_hints_are_extracted(self) -> None:
        inventory = parse_geo_accession_metadata(GSE33630_LIKE_METADATA)

        self.assertEqual(len(inventory.series_matrix_candidates), 1)
        self.assertTrue(
            any(
                candidate.name == "GSE33630_clinical-annotation.txt.gz"
                for candidate in inventory.supplementary_candidates
            )
        )
        self.assertTrue(
            any(
                candidate.name == "GSE33630_RAW.tar"
                for candidate in inventory.supplementary_candidates
            )
        )

    def test_expression_and_sample_metadata_candidates_are_inferred(self) -> None:
        inventory = parse_geo_accession_metadata(GSE33630_LIKE_METADATA)

        self.assertGreaterEqual(len(inventory.expression_candidates), 1)
        self.assertGreaterEqual(len(inventory.sample_metadata_candidates), 1)

    def test_malformed_metadata_returns_errors(self) -> None:
        inventory = parse_geo_accession_metadata("not a geo accession")

        self.assertEqual(inventory.gse_id, "")
        self.assertIn("metadata_parse_failed", inventory.errors)

    def test_empty_metadata_returns_errors(self) -> None:
        inventory = parse_geo_accession_metadata("")

        self.assertEqual(inventory.gse_id, "")
        self.assertIn("metadata_parse_failed", inventory.errors)

    def test_gse33630_like_html_extracts_title_summary_organism_and_samples(self) -> None:
        inventory = parse_geo_accession_metadata(GSE33630_LIKE_HTML)

        self.assertEqual(inventory.gse_id, "GSE33630")
        self.assertIn("papillary", inventory.title)
        self.assertEqual(
            inventory.summary,
            "HTML metadata fixture for controlled readiness tests.",
        )
        self.assertEqual(inventory.organism, "Homo sapiens")
        self.assertEqual(inventory.sample_count, 105)
        self.assertEqual(inventory.platform_ids, ["GPL570"])
        self.assertEqual(inventory.errors, [])

    def test_missing_optional_fields_add_warnings_without_crashing(self) -> None:
        inventory = parse_geo_accession_metadata("Accession: GSE99999")

        self.assertEqual(inventory.gse_id, "GSE99999")
        self.assertIn("title_missing", inventory.warnings)
        self.assertIn("summary_missing", inventory.warnings)
        self.assertIn("organism_missing", inventory.warnings)
        self.assertIn("sample_count_missing", inventory.warnings)
        self.assertEqual(inventory.errors, [])


if __name__ == "__main__":
    unittest.main()
