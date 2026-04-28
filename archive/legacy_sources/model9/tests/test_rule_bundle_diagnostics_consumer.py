import json
import tempfile
import unittest
from pathlib import Path

from extraction.rule_models import RuleCheckType, RuleSeverity, RuleTargetType
from extraction.rule_service import RuleService
from extraction.rule_store import (
    format_rule_bundle_diagnostics_summary,
    inspect_rule_bundles,
)


class RuleBundleDiagnosticsConsumerTests(unittest.TestCase):
    def test_summary_reports_valid_bundle_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = RuleService.from_root_dir(root_dir)
            service.create_rule(
                "proj-rule",
                RuleTargetType.EXTRACTION_RECORD,
                RuleCheckType.REQUIRED_FIELD,
                "study_design",
                severity=RuleSeverity.WARNING,
            )
            service.create_rule(
                "proj-rule",
                RuleTargetType.OUTCOME_RECORD,
                RuleCheckType.NUMERIC_RANGE,
                "group_a_n",
                enabled=False,
            )

            diagnostics = inspect_rule_bundles(root_dir)
            lines = format_rule_bundle_diagnostics_summary(diagnostics)

            self.assertEqual(diagnostics["total_bundles"], 1)
            self.assertEqual(diagnostics["valid_bundles"], 1)
            self.assertEqual(diagnostics["invalid_bundles"], 0)
            self.assertEqual(diagnostics["disabled_rules"], 1)
            self.assertEqual(diagnostics["warnings"], 0)
            self.assertEqual(diagnostics["errors"], 0)
            self.assertIn("- disabled rules: 1", lines)

    def test_summary_handles_missing_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            diagnostics = inspect_rule_bundles(Path(temp_dir))
            lines = format_rule_bundle_diagnostics_summary(diagnostics)

            self.assertEqual(diagnostics["total_bundles"], 0)
            self.assertEqual(diagnostics["missing_files"], 1)
            self.assertIn("- missing files: 1", lines)

    def test_summary_handles_empty_diagnostics(self) -> None:
        lines = format_rule_bundle_diagnostics_summary(None)

        self.assertEqual(lines[0], "Rule bundle diagnostics:")
        self.assertIn("- total bundles: 0", lines)
        self.assertIn("- errors: 0", lines)

    def test_summary_reports_malformed_bundle_without_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            module_dir = root_dir / "extraction"
            module_dir.mkdir()
            (module_dir / "extraction_rules.json").write_text("{bad json", encoding="utf-8")

            diagnostics = inspect_rule_bundles(root_dir)
            lines = format_rule_bundle_diagnostics_summary(diagnostics)

            self.assertEqual(diagnostics["total_bundles"], 1)
            self.assertEqual(diagnostics["invalid_bundles"], 1)
            self.assertEqual(diagnostics["malformed_json"], 1)
            self.assertEqual(diagnostics["errors"], 1)
            self.assertIn("- malformed json: 1", lines)

    def test_summary_reports_invalid_rule_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            module_dir = root_dir / "extraction"
            module_dir.mkdir()
            (module_dir / "extraction_rules.json").write_text(
                json.dumps([{"rule_id": "rule-incomplete"}]),
                encoding="utf-8",
            )

            diagnostics = inspect_rule_bundles(root_dir)

            self.assertEqual(diagnostics["invalid_bundles"], 1)
            self.assertEqual(diagnostics["errors"], 1)


if __name__ == "__main__":
    unittest.main()
