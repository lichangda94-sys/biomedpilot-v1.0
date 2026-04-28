import unittest

from analysis.group_detection import detect_geo_sample_groups


class GeoSampleGroupDetectionTests(unittest.TestCase):
    def test_detects_ptc_samples(self) -> None:
        report = detect_geo_sample_groups(
            [
                {
                    "sample_id": "GSM001",
                    "title": "PTC sample",
                    "source_name_ch1": "papillary thyroid carcinoma",
                }
            ]
        )

        self.assertEqual(report.sample_to_group["GSM001"], "ptc")
        self.assertIn("ptc", report.detected_groups)
        self.assertGreater(report.confidence, 0)

    def test_detects_normal_samples(self) -> None:
        report = detect_geo_sample_groups(
            [
                {
                    "sample_id": "GSM002",
                    "title": "normal thyroid sample",
                    "source_name_ch1": "normal thyroid",
                }
            ]
        )

        self.assertEqual(report.sample_to_group["GSM002"], "normal")
        self.assertIn("normal", report.detected_groups)

    def test_detects_patient_matched_non_tumor_control(self) -> None:
        report = detect_geo_sample_groups(
            [
                {
                    "sample_id": "GSM33630N",
                    "title": "1030N",
                    "source_name_ch1": "patient-matched non-tumor control",
                    "characteristics_ch1": (
                        "pathological diagnostic: patient-matched non-tumor control; "
                        "tissue type: patient-matched non-tumor"
                    ),
                }
            ]
        )

        self.assertEqual(report.sample_to_group["GSM33630N"], "normal")
        self.assertIn("normal", report.detected_groups)
        self.assertNotIn("GSM33630N", report.ambiguous_samples)

    def test_detects_normal_control_synonyms(self) -> None:
        rows = [
            {"sample_id": "S1", "source_name_ch1": "non tumor control"},
            {"sample_id": "S2", "source_name_ch1": "matched non-tumor"},
            {"sample_id": "S3", "source_name_ch1": "non-tumoral"},
            {"sample_id": "S4", "source_name_ch1": "adjacent non-tumor"},
            {"sample_id": "S5", "source_name_ch1": "adjacent normal"},
            {"sample_id": "S6", "source_name_ch1": "normal control"},
        ]

        report = detect_geo_sample_groups(rows)

        self.assertEqual(set(report.sample_to_group.values()), {"normal"})
        self.assertEqual(report.ambiguous_samples, [])

    def test_marks_atc_as_excluded_candidate(self) -> None:
        report = detect_geo_sample_groups(
            [
                {
                    "sample_id": "GSM003",
                    "title": "ATC sample",
                    "source_name_ch1": "anaplastic thyroid carcinoma",
                }
            ]
        )

        self.assertEqual(report.sample_to_group["GSM003"], "excluded_atc")
        self.assertIn("GSM003", report.excluded_group_candidates)
        self.assertNotIn("atc", report.detected_groups)
        self.assertIn("excluded_atc_samples", report.warnings)

    def test_marks_lnm_and_recurrence_as_excluded_non_target(self) -> None:
        report = detect_geo_sample_groups(
            [
                {
                    "sample_id": "GSM-LNM",
                    "title": "12-LNM,Lymph node metastasis,N1",
                    "source_name_ch1": "12-LNM,Lymph node metastasis,N1",
                    "characteristics_ch1": "largest.dimension.ln.metastasis..cm.: 0.3",
                },
                {
                    "sample_id": "GSM-R",
                    "title": "4-R,Recurrence,N1",
                    "source_name_ch1": "4-R,Recurrence,N1",
                },
            ]
        )

        self.assertEqual(report.sample_to_group["GSM-LNM"], "excluded_non_target")
        self.assertEqual(report.sample_to_group["GSM-R"], "excluded_non_target")
        self.assertEqual(report.ambiguous_samples, [])
        self.assertIn("excluded_non_target_samples", report.warnings)

    def test_metastasis_clinical_field_name_does_not_exclude_target_sample(self) -> None:
        report = detect_geo_sample_groups(
            [
                {
                    "sample_id": "GSM-PTC",
                    "title": "12-PT-N1,Papillary thyroid carcinoma,N1",
                    "source_name_ch1": "12-PT-N1,Papillary thyroid carcinoma,N1",
                    "characteristics_ch1": "largest.dimension.ln.metastasis..cm.: 0.3",
                }
            ]
        )

        self.assertEqual(report.sample_to_group["GSM-PTC"], "ptc")
        self.assertNotIn("GSM-PTC", report.excluded_group_candidates)

    def test_gse27155_morphology_na_does_not_mark_non_ptc_as_ptc(self) -> None:
        report = detect_geo_sample_groups(
            [
                {
                    "sample_id": "GSM-FC",
                    "title": "Follicular Thyroid Carcinoma Thy085",
                    "source_name_ch1": "Follicular Thyroid Carcinoma",
                    "characteristics_ch1": (
                        "tissue: Follicular Thyroid Carcinoma; "
                        "morphology of papillary carcinomas: NA"
                    ),
                },
                {
                    "sample_id": "GSM-PTC",
                    "title": "Papillary Thyroid Carcinoma Thy169",
                    "source_name_ch1": "Papillary Thyroid Carcinoma",
                    "characteristics_ch1": (
                        "tissue: Papillary Thyroid Carcinoma; "
                        "morphology of papillary carcinomas: classical type of papillary carcinoma"
                    ),
                },
            ]
        )

        self.assertEqual(report.sample_to_group["GSM-FC"], "excluded_non_target")
        self.assertEqual(report.sample_to_group["GSM-PTC"], "ptc")
        self.assertEqual(report.ambiguous_samples, [])

    def test_ambiguous_samples_warn(self) -> None:
        report = detect_geo_sample_groups(
            [
                {
                    "sample_id": "GSM004",
                    "title": "mixed PTC normal review sample",
                    "source_name_ch1": "ambiguous",
                }
            ]
        )

        self.assertIn("GSM004", report.ambiguous_samples)
        self.assertIn("ambiguous_samples", report.warnings)

    def test_confidence_is_stable(self) -> None:
        report = detect_geo_sample_groups(
            [
                {"sample_id": "GSM001", "source_name_ch1": "PTC"},
                {"sample_id": "GSM002", "source_name_ch1": "normal thyroid"},
                {"sample_id": "GSM003", "source_name_ch1": "unknown"},
            ]
        )

        self.assertEqual(report.confidence, 0.667)
        self.assertIn("GSM003", report.ambiguous_samples)

    def test_empty_metadata_returns_error_without_analysis(self) -> None:
        report = detect_geo_sample_groups([])

        self.assertIn("sample_metadata_missing", report.errors)
        self.assertIn("sample_metadata_missing", report.warnings)

    def test_to_dict_is_stable(self) -> None:
        report = detect_geo_sample_groups(
            [{"sample_id": "GSM001", "source_name_ch1": "PTC"}]
        )

        payload = report.to_dict()
        self.assertEqual(payload["sample_to_group"], {"GSM001": "ptc"})
        self.assertIn("confidence", payload)


if __name__ == "__main__":
    unittest.main()
