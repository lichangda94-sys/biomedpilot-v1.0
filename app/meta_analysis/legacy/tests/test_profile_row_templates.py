from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.profile_row_templates import (
    PROFILE_ROW_TEMPLATE_FIELDS,
    PROFILE_ROWS_DIRNAME,
    export_profile_row_template,
    export_profile_rows_csv,
    import_profile_rows_csv,
    load_project_profile_rows,
    project_profile_rows_path,
    save_project_profile_rows,
    supported_profile_row_template_types,
)


class ProfileRowTemplateTests(unittest.TestCase):
    def test_export_template_writes_headers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "diagnostic_template.csv"

            export_profile_row_template("DIAGNOSTIC_ACCURACY_META", output_path)

            header = output_path.read_text(encoding="utf-8").splitlines()[0]
            self.assertIn("row_id", header)
            self.assertIn("reference_standard", header)
            self.assertIn("reported_metric_only", header)

    def test_export_and_import_profile_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "biomarker_rows.csv"

            export_profile_rows_csv(
                "BIOMARKER_PREVALENCE_ASSOCIATION_META",
                [
                    {
                        "row_id": "HER2_ESCC_PREVALENCE_001",
                        "row_subtype": "BIOMARKER_PREVALENCE",
                        "biomarker_name": "HER2",
                        "positive_events": 12,
                        "total_n": 80,
                        "effect_measure": "prevalence",
                        "assay_method": "IHC",
                        "threshold": "IHC 3+",
                    }
                ],
                output_path,
            )

            rows = import_profile_rows_csv(
                "BIOMARKER_PREVALENCE_ASSOCIATION_META",
                output_path,
            )

            self.assertEqual(rows[0]["row_id"], "HER2_ESCC_PREVALENCE_001")
            self.assertEqual(rows[0]["assay_method"], "IHC")

    def test_import_rejects_missing_template_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "bad.csv"
            input_path.write_text("row_id\nrow-1\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                import_profile_rows_csv("TREATMENT_EFFECT_META", input_path)

    def test_all_templates_include_row_id(self) -> None:
        for fields in PROFILE_ROW_TEMPLATE_FIELDS.values():
            self.assertIn("row_id", fields)

    def test_supported_templates_are_limited_to_current_demo_profiles(self) -> None:
        self.assertEqual(
            supported_profile_row_template_types(),
            (
                "TREATMENT_EFFECT_META",
                "DIAGNOSTIC_ACCURACY_META",
                "BIOMARKER_PREVALENCE_ASSOCIATION_META",
            ),
        )

    def test_project_profile_rows_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)

            output_path = save_project_profile_rows(
                project_dir,
                "DIAGNOSTIC_ACCURACY_META",
                [
                    {
                        "row_id": "DTA_001",
                        "index_test_name": "Afirma GSC",
                        "target_condition": "Thyroid malignancy",
                        "reference_standard": "Histopathology",
                        "tp": "10",
                        "fp": "2",
                        "fn": "1",
                        "tn": "20",
                    }
                ],
            )

            self.assertEqual(
                output_path,
                project_dir / PROFILE_ROWS_DIRNAME / "DIAGNOSTIC_ACCURACY_META.csv",
            )
            self.assertEqual(
                project_profile_rows_path(project_dir, "DIAGNOSTIC_ACCURACY_META"),
                output_path,
            )
            rows = load_project_profile_rows(project_dir, "DIAGNOSTIC_ACCURACY_META")
            self.assertEqual(rows[0]["row_id"], "DTA_001")
            self.assertEqual(rows[0]["reference_standard"], "Histopathology")

    def test_load_project_profile_rows_returns_empty_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(
                load_project_profile_rows(Path(temp_dir), "TREATMENT_EFFECT_META"),
                [],
            )
