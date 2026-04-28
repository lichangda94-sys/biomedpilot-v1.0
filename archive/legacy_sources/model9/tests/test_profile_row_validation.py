from __future__ import annotations

import unittest

from core.profile_row_validation import validate_profile_rows


class ProfileRowValidationTests(unittest.TestCase):
    def test_blank_rows_do_not_create_validation_issues(self) -> None:
        issues = validate_profile_rows(
            "TREATMENT_EFFECT_META",
            [{"row_id": "", "outcome_name": "", "effect_measure": ""}],
        )

        self.assertEqual(issues, [])

    def test_treatment_effect_requires_core_fields(self) -> None:
        issues = validate_profile_rows(
            "TREATMENT_EFFECT_META",
            [{"row_id": "row-1", "outcome_name": "", "effect_measure": ""}],
        )

        self.assertEqual([issue.field for issue in issues], ["outcome_name", "effect_measure"])

    def test_diagnostic_accepts_reported_metric_only_shape(self) -> None:
        issues = validate_profile_rows(
            "DIAGNOSTIC_ACCURACY_META",
            [
                {
                    "row_id": "dta-1",
                    "index_test_name": "NLR",
                    "target_condition": "Thyroid carcinoma",
                    "reference_standard": "Histology",
                    "sensitivity": "0.80",
                    "specificity": "0.70",
                    "reported_metric_only": "yes",
                }
            ],
        )

        self.assertEqual(issues, [])

    def test_diagnostic_rejects_missing_metric_shape(self) -> None:
        issues = validate_profile_rows(
            "DIAGNOSTIC_ACCURACY_META",
            [
                {
                    "row_id": "dta-1",
                    "index_test_name": "NLR",
                    "target_condition": "Thyroid carcinoma",
                    "reference_standard": "Histology",
                }
            ],
        )

        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field, "tp/fp/fn/tn")

    def test_biomarker_prevalence_requires_events_and_total(self) -> None:
        issues = validate_profile_rows(
            "BIOMARKER_PREVALENCE_ASSOCIATION_META",
            [
                {
                    "row_id": "bio-1",
                    "row_subtype": "BIOMARKER_PREVALENCE",
                    "biomarker_name": "HER2",
                    "effect_measure": "prevalence",
                }
            ],
        )

        self.assertEqual([issue.field for issue in issues], ["positive_events", "total_n"])
