import tempfile
import unittest
from pathlib import Path

from extraction.models import FieldSourceTrace, OutcomeType
from extraction.service import ExtractionService
from literature.models import (
    NormalizedLiteratureRecord,
    ScreeningDecision,
    ScreeningRecord,
    ScreeningStage,
)
from literature.store import LiteratureStore


class ExtractionServiceTests(unittest.TestCase):
    def test_generate_extraction_pool_defaults_to_full_text_included(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            literature_store = LiteratureStore(root_dir)
            project_id = "proj-fulltext"
            literature_store.replace_normalized_records(
                project_id,
                [
                    self._normalized_record("n1", project_id, "Study One"),
                    self._normalized_record("n2", project_id, "Study Two"),
                ],
            )
            literature_store.replace_screening_records(
                project_id,
                ScreeningStage.FULL_TEXT_SCREENING,
                [
                    self._screening_record(
                        "s1",
                        project_id,
                        "src1",
                        "n1",
                        ScreeningDecision.INCLUDED,
                        stage=ScreeningStage.FULL_TEXT_SCREENING,
                    ),
                    self._screening_record(
                        "s2",
                        project_id,
                        "src2",
                        "n2",
                        ScreeningDecision.EXCLUDED,
                        stage=ScreeningStage.FULL_TEXT_SCREENING,
                    ),
                ],
            )

            records = ExtractionService.from_root_dir(root_dir).generate_extraction_pool(
                project_id
            )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].normalized_record_id, "n1")

    def test_generate_extraction_pool_from_included_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            literature_store = LiteratureStore(root_dir)
            project_id = "proj-extraction"
            literature_store.replace_normalized_records(
                project_id,
                [
                    self._normalized_record("n1", project_id, "Study One"),
                    self._normalized_record("n2", project_id, "Study Two"),
                ],
            )
            literature_store.replace_screening_records(
                project_id,
                ScreeningStage.TITLE_ABSTRACT_SCREENING,
                [
                    self._screening_record("s1", project_id, "src1", "n1", ScreeningDecision.INCLUDED),
                    self._screening_record("s2", project_id, "src2", "n2", ScreeningDecision.MAYBE),
                ],
            )

            records = ExtractionService.from_root_dir(root_dir).generate_extraction_pool(
                project_id,
                source_stage=ScreeningStage.TITLE_ABSTRACT_SCREENING,
            )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].screening_record_id, "s1")
        self.assertEqual(records[0].study_title, "Study One")

    def test_create_and_update_extraction_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = ExtractionService.from_root_dir(root_dir)
            record = service.create_extraction_record(
                "proj-1",
                "screen-1",
                "norm-1",
                study_title="Initial",
                population="Adults",
            )
            updated = service.update_extraction_record(
                record.extraction_record_id,
                study_design="RCT",
                country="China",
            )

        self.assertEqual(updated.study_title, "Initial")
        self.assertEqual(updated.population, "Adults")
        self.assertEqual(updated.study_design, "RCT")
        self.assertEqual(updated.country, "China")

    def test_create_and_update_outcome_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = ExtractionService.from_root_dir(root_dir)
            extraction = service.create_extraction_record(
                "proj-2",
                "screen-2",
                "norm-2",
                study_title="Outcome Study",
            )
            outcome = service.create_outcome_record(
                extraction.extraction_record_id,
                "Mortality",
                OutcomeType.BINARY,
                group_a_n=100,
                group_b_n=98,
                events_a=5,
                events_b=8,
            )
            updated = service.update_outcome_record(
                outcome.outcome_record_id,
                metric_hint="RR",
                p_value=0.04,
            )

        self.assertEqual(updated.metric_hint, "RR")
        self.assertEqual(updated.p_value, 0.04)

    def test_basic_validation_triggers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = ExtractionService.from_root_dir(root_dir)
            extraction = service.create_extraction_record(
                "proj-3",
                "screen-3",
                "norm-3",
                study_title="Validation Study",
            )

            with self.assertRaisesRegex(
                ValueError,
                "Binary outcome requires group sample sizes or event counts",
            ):
                service.create_outcome_record(
                    extraction.extraction_record_id,
                    "Binary Fail",
                    OutcomeType.BINARY,
                )

            with self.assertRaisesRegex(
                ValueError,
                "Continuous outcome requires n, mean, and sd",
            ):
                service.create_outcome_record(
                    extraction.extraction_record_id,
                    "Continuous Fail",
                    OutcomeType.CONTINUOUS,
                    group_a_n=10,
                    group_b_n=10,
                    mean_a=1.2,
                    mean_b=1.0,
                )

            with self.assertRaisesRegex(
                ValueError,
                "Time-to-event outcome requires hr and confidence interval bounds",
            ):
                service.create_outcome_record(
                    extraction.extraction_record_id,
                    "Time Fail",
                    OutcomeType.TIME_TO_EVENT,
                    hr=0.8,
                )

    def test_results_can_be_queried(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = ExtractionService.from_root_dir(root_dir)
            extraction = service.create_extraction_record(
                "proj-4",
                "screen-4",
                "norm-4",
                study_title="Query Study",
            )
            service.create_outcome_record(
                extraction.extraction_record_id,
                "Progression-free survival",
                OutcomeType.TIME_TO_EVENT,
                hr=0.72,
                ci_lower=0.55,
                ci_upper=0.95,
            )
            service.replace_field_sources(
                extraction.extraction_record_id,
                [
                    FieldSourceTrace(
                        source_field_name="study_design",
                        source_page=5,
                        source_text_snippet="Randomized controlled trial",
                        linked_object_type="extraction_record",
                        linked_object_id=extraction.extraction_record_id,
                    )
                ],
            )

            extraction_records = service.list_extraction_records("proj-4")
            outcome_records = service.list_outcome_records(extraction.extraction_record_id)
            field_sources = service.list_field_source_traces(extraction.extraction_record_id)

        self.assertEqual(len(extraction_records), 1)
        self.assertEqual(len(outcome_records), 1)
        self.assertEqual(len(field_sources), 1)
        self.assertEqual(outcome_records[0].outcome_name, "Progression-free survival")

    def _normalized_record(
        self,
        record_id: str,
        project_id: str,
        title: str,
    ) -> NormalizedLiteratureRecord:
        return NormalizedLiteratureRecord(
            record_id=record_id,
            batch_id="batch-1",
            project_id=project_id,
            source="ris",
            source_record_id=f"src-{record_id}",
            title=title,
            title_normalized=title.lower(),
            source_trace=[record_id],
        )

    def _screening_record(
        self,
        screening_record_id: str,
        project_id: str,
        source_record_id: str,
        normalized_record_id: str,
        decision: ScreeningDecision,
        *,
        stage: ScreeningStage = ScreeningStage.TITLE_ABSTRACT_SCREENING,
    ) -> ScreeningRecord:
        return ScreeningRecord(
            screening_record_id=screening_record_id,
            project_id=project_id,
            source_record_id=source_record_id,
            normalized_record_id=normalized_record_id,
            stage=stage,
            decision=decision,
        )
