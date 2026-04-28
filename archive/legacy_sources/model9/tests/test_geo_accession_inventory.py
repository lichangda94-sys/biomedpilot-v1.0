import unittest

from geo_readiness.models import GeoAccessionInventory, GeoRemoteAssetCandidate


class GeoAccessionInventoryTests(unittest.TestCase):
    def test_fake_gse_metadata_can_construct_inventory(self) -> None:
        inventory = GeoAccessionInventory(
            gse_id="GSE33630",
            title="normal thyrocytes vs papillary thyroid carcinoma",
            summary="Fake metadata fixture for readiness inventory.",
            organism="Homo sapiens",
            sample_count=105,
            platform_ids=["GPL570"],
            series_matrix_candidates=[
                GeoRemoteAssetCandidate(
                    candidate_type="series_matrix",
                    name="GSE33630_series_matrix.txt.gz",
                    confidence=0.9,
                    reasons=["geo_family_series_matrix"],
                )
            ],
            supplementary_candidates=[
                GeoRemoteAssetCandidate(
                    candidate_type="supplementary_file",
                    name="GSE33630_clinical-annotation.txt.gz",
                    size_hint="2.8 Kb",
                    confidence=0.7,
                    reasons=["clinical_annotation_name"],
                )
            ],
            sample_metadata_candidates=[
                GeoRemoteAssetCandidate(
                    candidate_type="sample_metadata",
                    name="GEO sample table",
                    confidence=0.8,
                    reasons=["geo_sample_table"],
                )
            ],
            expression_candidates=[
                GeoRemoteAssetCandidate(
                    candidate_type="expression_matrix",
                    name="GSE33630_series_matrix.txt.gz",
                    confidence=0.6,
                    reasons=["series_matrix_may_include_processed_values"],
                )
            ],
        )

        self.assertEqual(inventory.gse_id, "GSE33630")
        self.assertEqual(inventory.sample_count, 105)
        self.assertEqual(inventory.platform_ids, ["GPL570"])
        self.assertEqual(len(inventory.series_matrix_candidates), 1)
        self.assertEqual(len(inventory.supplementary_candidates), 1)
        self.assertEqual(len(inventory.sample_metadata_candidates), 1)
        self.assertEqual(len(inventory.expression_candidates), 1)
        self.assertEqual(inventory.warnings, [])

    def test_to_dict_serializes_candidates(self) -> None:
        inventory = GeoAccessionInventory(
            gse_id="GSE-fake",
            series_matrix_candidates=[
                GeoRemoteAssetCandidate(
                    candidate_type="series_matrix",
                    name="matrix.txt.gz",
                    url="https://example.invalid/matrix.txt.gz",
                    size_hint="10 Kb",
                    confidence=0.95,
                    reasons=["test_reason"],
                    warnings=["test_warning"],
                )
            ],
        )

        payload = inventory.to_dict()

        self.assertEqual(payload["gse_id"], "GSE-fake")
        self.assertEqual(
            payload["series_matrix_candidates"][0]["candidate_type"],
            "series_matrix",
        )
        self.assertEqual(payload["series_matrix_candidates"][0]["name"], "matrix.txt.gz")
        self.assertEqual(
            payload["series_matrix_candidates"][0]["url"],
            "https://example.invalid/matrix.txt.gz",
        )

    def test_no_expression_candidate_adds_warning(self) -> None:
        inventory = GeoAccessionInventory(
            gse_id="GSE-no-expression",
            supplementary_candidates=[
                GeoRemoteAssetCandidate(
                    candidate_type="supplementary_file",
                    name="raw.tar",
                    confidence=0.4,
                )
            ],
        )

        self.assertIn("no_expression_candidate", inventory.warnings)


if __name__ == "__main__":
    unittest.main()
