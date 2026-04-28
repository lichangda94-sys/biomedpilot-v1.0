from __future__ import annotations

import unittest

from core.profile_row_editor_policy import (
    evaluate_profile_row_load,
    evaluate_profile_row_save,
    evaluate_profile_row_switch,
)


class ProfileRowEditorPolicyTests(unittest.TestCase):
    def test_save_allowed_when_rows_validate(self) -> None:
        decision = evaluate_profile_row_save(
            "TREATMENT_EFFECT_META",
            [
                {
                    "row_id": "te-1",
                    "outcome_name": "Mortality",
                    "effect_measure": "OR",
                }
            ],
        )

        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_confirmation)

    def test_save_blocked_when_rows_have_validation_issues(self) -> None:
        decision = evaluate_profile_row_save(
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

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.issue_count, 2)
        self.assertIn("Save blocked", decision.message)

    def test_load_requires_confirmation_when_dirty(self) -> None:
        decision = evaluate_profile_row_load(is_dirty=True)

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)

    def test_switch_requires_confirmation_when_dirty(self) -> None:
        decision = evaluate_profile_row_switch(is_dirty=True)

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_confirmation)
