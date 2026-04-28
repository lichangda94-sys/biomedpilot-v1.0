import tempfile
import unittest
from pathlib import Path

from extraction.models import ExtractionRecord, OutcomeRecord, OutcomeType
from extraction.rule_models import (
    RuleCheckType,
    RuleEvaluationStatus,
    RuleSeverity,
    RuleTargetType,
)
from extraction.rule_service import RuleService
from extraction.rule_store import RuleStore
from extraction.store import ExtractionStore


class RuleServiceTests(unittest.TestCase):
    def test_create_rule_and_persist_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = RuleService.from_root_dir(root_dir)

            rule = service.create_rule(
                "proj-rule",
                RuleTargetType.EXTRACTION_RECORD,
                RuleCheckType.REQUIRED_FIELD,
                "study_design",
                label="Study design is required",
                severity=RuleSeverity.WARNING,
            )
            reloaded = RuleService(ExtractionStore(root_dir), RuleStore(root_dir))

            rules = reloaded.list_rules("proj-rule")

            self.assertEqual([item.rule_id for item in rules], [rule.rule_id])
            self.assertEqual(rules[0].field_name, "study_design")
            self.assertEqual(rules[0].severity, RuleSeverity.WARNING)

    def test_required_field_rule_evaluates_extraction_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            extraction_store = ExtractionStore(root_dir)
            record = self._save_extraction(extraction_store, study_design="")
            service = RuleService(extraction_store, RuleStore(root_dir))
            service.create_rule(
                record.project_id,
                RuleTargetType.EXTRACTION_RECORD,
                RuleCheckType.REQUIRED_FIELD,
                "study_design",
            )

            failed = service.evaluate_extraction_record(record.extraction_record_id)
            record.study_design = "RCT"
            extraction_store.save_extraction_record(record)
            passed = service.evaluate_extraction_record(record.extraction_record_id)

            self.assertEqual(failed[0].status, RuleEvaluationStatus.FAILED)
            self.assertIn("required", failed[0].message)
            self.assertEqual(passed[0].status, RuleEvaluationStatus.PASSED)
            self.assertEqual(
                [item.result_id for item in service.list_results(target_id=record.extraction_record_id)],
                [passed[0].result_id],
            )

    def test_numeric_range_rule_evaluates_outcome_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            extraction_store = ExtractionStore(root_dir)
            extraction = self._save_extraction(extraction_store)
            outcome = extraction_store.save_outcome_record(
                OutcomeRecord(
                    outcome_record_id="outcome-1",
                    extraction_record_id=extraction.extraction_record_id,
                    outcome_name="Mortality",
                    outcome_type=OutcomeType.BINARY,
                    group_a_n=120,
                    group_b_n=100,
                    events_a=10,
                    events_b=20,
                )
            )
            service = RuleService(extraction_store, RuleStore(root_dir))
            service.create_rule(
                extraction.project_id,
                RuleTargetType.OUTCOME_RECORD,
                RuleCheckType.NUMERIC_RANGE,
                "group_a_n",
                parameters={"min": 1, "max": 100},
            )

            results = service.evaluate_outcome_record(outcome.outcome_record_id)

            self.assertEqual(results[0].status, RuleEvaluationStatus.FAILED)
            self.assertIn("above maximum", results[0].message)

    def test_allowed_values_rule_can_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            extraction_store = ExtractionStore(root_dir)
            extraction = self._save_extraction(extraction_store, study_design="cohort")
            service = RuleService(extraction_store, RuleStore(root_dir))
            service.create_rule(
                extraction.project_id,
                RuleTargetType.EXTRACTION_RECORD,
                RuleCheckType.ALLOWED_VALUES,
                "study_design",
                parameters={"allowed_values": ["rct", "cohort"]},
            )

            results = service.evaluate_extraction_record(extraction.extraction_record_id)

            self.assertEqual(results[0].status, RuleEvaluationStatus.PASSED)

    def _save_extraction(
        self,
        store: ExtractionStore,
        *,
        study_design: str = "RCT",
    ) -> ExtractionRecord:
        return store.save_extraction_record(
            ExtractionRecord(
                extraction_record_id="extr-1",
                project_id="proj-rule",
                screening_record_id="screen-1",
                normalized_record_id="norm-1",
                study_title="Study One",
                study_design=study_design,
            )
        )


if __name__ == "__main__":
    unittest.main()
