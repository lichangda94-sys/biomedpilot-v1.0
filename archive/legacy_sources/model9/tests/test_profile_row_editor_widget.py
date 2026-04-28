from __future__ import annotations

import unittest

from tests.qt_test_utils import get_qapplication


class ProfileRowEditorWidgetTests(unittest.TestCase):
    def test_editor_uses_template_columns_and_round_trips_rows(self) -> None:
        get_qapplication()
        from app.profile_row_editor_widget import ProfileRowEditorWidget

        widget = ProfileRowEditorWidget("BIOMARKER_PREVALENCE_ASSOCIATION_META")

        widget.set_rows(
            [
                {
                    "row_id": "HER2_ESCC_PREVALENCE_001",
                    "row_subtype": "BIOMARKER_PREVALENCE",
                    "biomarker_name": "HER2",
                    "effect_measure": "prevalence",
                    "positive_events": "12",
                    "total_n": "80",
                }
            ]
        )

        self.assertEqual(widget.profile_type(), "BIOMARKER_PREVALENCE_ASSOCIATION_META")
        self.assertEqual(widget.cell_text(0, 0), "HER2_ESCC_PREVALENCE_001")
        self.assertEqual(widget.rows()[0]["biomarker_name"], "HER2")
        self.assertFalse(widget.is_dirty())
        self.assertIn("No validation issues", widget.state_text())

    def test_editor_can_add_empty_row_without_running_analysis(self) -> None:
        get_qapplication()
        from app.profile_row_editor_widget import ProfileRowEditorWidget

        widget = ProfileRowEditorWidget("DIAGNOSTIC_ACCURACY_META")

        widget.add_empty_row()

        self.assertEqual(len(widget.rows()), 1)
        self.assertIn("does not run meta-analysis", widget.note_text())
        self.assertIn("does not generate reports", widget.note_text())
        self.assertIn("not auto-saved", widget.note_text())
        self.assertIn("Save rows only saves CSV", widget.note_text())
        self.assertIn("Load rows only loads CSV", widget.note_text())
        self.assertIn("TREATMENT_EFFECT_META", widget.note_text())
        self.assertIn("BIOMARKER_PREVALENCE_ASSOCIATION_META", widget.note_text())
        self.assertTrue(widget.is_dirty())
        self.assertFalse(widget.save_rows_button_enabled())
        self.assertFalse(widget.load_rows_button_enabled())

    def test_meta_workspace_exposes_minimal_row_editor(self) -> None:
        get_qapplication()
        from app.meta_analysis_workspace_widget import MetaAnalysisWorkspaceWidget

        widget = MetaAnalysisWorkspaceWidget()

        editor = widget.row_editor()
        self.assertEqual(editor.profile_type(), "BIOMARKER_PREVALENCE_ASSOCIATION_META")
        self.assertIn("does not run meta-analysis", editor.note_text())
        self.assertIn("does not generate reports", editor.note_text())

    def test_editor_tracks_dirty_state_after_cell_edit(self) -> None:
        get_qapplication()
        from app.profile_row_editor_widget import ProfileRowEditorWidget

        widget = ProfileRowEditorWidget("TREATMENT_EFFECT_META")
        widget.set_rows(
            [
                {
                    "row_id": "te-1",
                    "outcome_name": "Mortality",
                    "effect_measure": "OR",
                }
            ]
        )

        self.assertFalse(widget.is_dirty())
        item = widget._table.item(0, 1)
        item.setText("binary")

        self.assertTrue(widget.is_dirty())
        self.assertIn("Unsaved changes", widget.state_text())

    def test_editor_reports_validation_issues(self) -> None:
        get_qapplication()
        from app.profile_row_editor_widget import ProfileRowEditorWidget

        widget = ProfileRowEditorWidget("BIOMARKER_PREVALENCE_ASSOCIATION_META")
        widget.set_rows(
            [
                {
                    "row_id": "bio-1",
                    "row_subtype": "BIOMARKER_PREVALENCE",
                    "biomarker_name": "HER2",
                    "effect_measure": "prevalence",
                }
            ]
        )

        issues = widget.validation_issues()

        self.assertEqual([issue.field for issue in issues], ["positive_events", "total_n"])
        self.assertIn("2 validation issue", widget.state_text())

    def test_editor_exposes_save_and_load_decisions(self) -> None:
        get_qapplication()
        from app.profile_row_editor_widget import ProfileRowEditorWidget

        widget = ProfileRowEditorWidget("TREATMENT_EFFECT_META")
        widget.set_rows(
            [
                {
                    "row_id": "te-1",
                    "outcome_name": "Mortality",
                    "effect_measure": "OR",
                }
            ]
        )

        self.assertTrue(widget.save_decision().allowed)
        self.assertTrue(widget.load_decision().allowed)

        item = widget._table.item(0, 1)
        item.setText("binary")

        self.assertFalse(widget.load_decision().allowed)
        self.assertTrue(widget.load_decision().requires_confirmation)
        self.assertFalse(widget.switch_profile_decision().allowed)

    def test_editor_save_button_uses_policy_before_handler(self) -> None:
        get_qapplication()
        from pathlib import Path
        from app.profile_row_editor_widget import ProfileRowEditorWidget

        calls: list[str] = []
        widget = ProfileRowEditorWidget("BIOMARKER_PREVALENCE_ASSOCIATION_META")
        widget.set_profile_io_handlers(
            save_handler=lambda: calls.append("save") or Path("/tmp/rows.csv"),
            load_handler=lambda _profile_type: [],
        )
        widget.set_rows(
            [
                {
                    "row_id": "bio-1",
                    "row_subtype": "BIOMARKER_PREVALENCE",
                    "biomarker_name": "HER2",
                    "effect_measure": "prevalence",
                }
            ]
        )

        widget.trigger_save_rows()

        self.assertEqual(calls, [])
        self.assertIn("Save blocked", widget.action_status_text())

    def test_editor_load_button_blocks_dirty_table(self) -> None:
        get_qapplication()
        from pathlib import Path
        from app.profile_row_editor_widget import ProfileRowEditorWidget

        calls: list[str] = []
        widget = ProfileRowEditorWidget("TREATMENT_EFFECT_META")
        widget.set_profile_io_handlers(
            save_handler=lambda: Path("/tmp/rows.csv"),
            load_handler=lambda _profile_type: calls.append("load") or [],
        )
        widget.set_rows(
            [
                {
                    "row_id": "te-1",
                    "outcome_name": "Mortality",
                    "effect_measure": "OR",
                }
            ]
        )
        widget._table.item(0, 1).setText("binary")

        widget.trigger_load_rows()

        self.assertEqual(calls, [])
        self.assertIn("Load requires confirmation", widget.action_status_text())
