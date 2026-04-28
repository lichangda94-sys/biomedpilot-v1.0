import tempfile
import unittest
from pathlib import Path

from literature.models import (
    DuplicateCandidateGroup,
    NormalizedLiteratureRecord,
    ScreeningDecision,
    ScreeningStage,
)
from literature.screening_service import ScreeningService
from literature.store import LiteratureStore


class ScreeningServiceTests(unittest.TestCase):
    def test_generate_title_abstract_screening_pool(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            store = LiteratureStore(root_dir)
            project_id = "proj-screen"
            store.replace_normalized_records(
                project_id,
                [
                    self._normalized_record("n1", project_id, source_record_id="src-1"),
                    self._normalized_record("n2", project_id, source_record_id="src-2"),
                    self._normalized_record("n3", project_id, source_record_id="src-3"),
                ],
            )
            store.replace_duplicate_groups(
                project_id,
                [
                    DuplicateCandidateGroup(
                        duplicate_group_id="dup-1",
                        project_id=project_id,
                        candidate_record_ids=["n2", "n3"],
                        match_reason="doi_exact",
                        confidence=0.99,
                        suggested_primary_record_id="n2",
                    )
                ],
            )

            records = ScreeningService(store).generate_screening_pool(project_id)

        self.assertEqual(len(records), 2)
        self.assertEqual(
            sorted(record.normalized_record_id for record in records),
            ["n1", "n2"],
        )
        self.assertTrue(
            all(record.stage == ScreeningStage.TITLE_ABSTRACT_SCREENING for record in records)
        )

    def test_submit_included_excluded_and_maybe_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            store = LiteratureStore(root_dir)
            project_id = "proj-decisions"
            self._seed_screening_pool(store, project_id, ["n1", "n2", "n3"])
            service = ScreeningService(store)
            records = service.generate_screening_pool(project_id)

            included = service.submit_decision(
                records[0].screening_record_id,
                decision=ScreeningDecision.INCLUDED,
                reviewer_id="rev-1",
                notes="keep",
            )
            excluded = service.submit_decision(
                records[1].screening_record_id,
                decision=ScreeningDecision.EXCLUDED,
                exclusion_reason_code="wrong_population",
                exclusion_reason_text="Adults only",
            )
            maybe = service.submit_decision(
                records[2].screening_record_id,
                decision=ScreeningDecision.MAYBE,
            )

        self.assertEqual(included.decision, ScreeningDecision.INCLUDED)
        self.assertEqual(excluded.exclusion_reason_code, "wrong_population")
        self.assertEqual(excluded.exclusion_reason_text, "Adults only")
        self.assertEqual(maybe.decision, ScreeningDecision.MAYBE)
        self.assertIsNotNone(included.decided_at)
        self.assertIsNotNone(excluded.decided_at)
        self.assertIsNotNone(maybe.decided_at)

    def test_exclusion_reason_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            store = LiteratureStore(root_dir)
            project_id = "proj-validation"
            self._seed_screening_pool(store, project_id, ["n1"])
            service = ScreeningService(store)
            record = service.generate_screening_pool(project_id)[0]

            with self.assertRaisesRegex(
                ValueError,
                "Excluded screening decision requires an exclusion reason code",
            ):
                service.submit_decision(
                    record.screening_record_id,
                    decision=ScreeningDecision.EXCLUDED,
                )

            with self.assertRaisesRegex(
                ValueError,
                "Unknown exclusion reason code: not_a_reason",
            ):
                service.submit_decision(
                    record.screening_record_id,
                    decision=ScreeningDecision.EXCLUDED,
                    exclusion_reason_code="not_a_reason",
                )

    def test_update_screening_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            store = LiteratureStore(root_dir)
            project_id = "proj-update"
            self._seed_screening_pool(store, project_id, ["n1"])
            service = ScreeningService(store)
            record = service.generate_screening_pool(project_id)[0]

            service.submit_decision(
                record.screening_record_id,
                decision=ScreeningDecision.EXCLUDED,
                exclusion_reason_code="wrong_population",
                exclusion_reason_text="initial reason",
            )
            updated = service.update_decision(
                record.screening_record_id,
                decision=ScreeningDecision.INCLUDED,
                notes="restored",
            )

        self.assertEqual(updated.decision, ScreeningDecision.INCLUDED)
        self.assertEqual(updated.exclusion_reason_code, "")
        self.assertEqual(updated.exclusion_reason_text, "")
        self.assertEqual(updated.notes, "restored")

    def test_prisma_counts_are_correct(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            store = LiteratureStore(root_dir)
            project_id = "proj-prisma"
            store.replace_normalized_records(
                project_id,
                [
                    self._normalized_record("n1", project_id, source_record_id="src-1"),
                    self._normalized_record("n2", project_id, source_record_id="src-2"),
                    self._normalized_record("n3", project_id, source_record_id="src-3"),
                    self._normalized_record("n4", project_id, source_record_id="src-4"),
                ],
            )
            store.replace_duplicate_groups(
                project_id,
                [
                    DuplicateCandidateGroup(
                        duplicate_group_id="dup-2",
                        project_id=project_id,
                        candidate_record_ids=["n3", "n4"],
                        match_reason="doi_exact",
                        confidence=0.99,
                        suggested_primary_record_id="n3",
                    )
                ],
            )
            service = ScreeningService(store)
            title_records = service.generate_screening_pool(project_id)
            service.submit_decision(
                title_records[0].screening_record_id,
                decision=ScreeningDecision.INCLUDED,
            )
            service.submit_decision(
                title_records[1].screening_record_id,
                decision=ScreeningDecision.EXCLUDED,
                exclusion_reason_code="wrong_population",
            )
            service.submit_decision(
                title_records[2].screening_record_id,
                decision=ScreeningDecision.MAYBE,
            )
            full_text_records = service.generate_screening_pool(
                project_id,
                stage=ScreeningStage.FULL_TEXT_SCREENING,
            )

            prisma = service.generate_prisma_counts(project_id)

        self.assertEqual(len(full_text_records), 1)
        self.assertEqual(prisma["records_after_normalization"], 4)
        self.assertEqual(prisma["duplicate_groups"], 1)
        self.assertEqual(prisma["duplicates_removed_from_screening"], 1)
        self.assertEqual(prisma["title_abstract_screened"], 3)
        self.assertEqual(prisma["title_abstract_included"], 1)
        self.assertEqual(prisma["title_abstract_excluded"], 1)
        self.assertEqual(prisma["title_abstract_maybe"], 1)
        self.assertEqual(prisma["title_abstract_pending"], 0)
        self.assertEqual(prisma["full_text_screened"], 1)
        self.assertEqual(prisma["full_text_pending"], 1)

    def _seed_screening_pool(
        self,
        store: LiteratureStore,
        project_id: str,
        normalized_ids: list[str],
    ) -> None:
        store.replace_normalized_records(
            project_id,
            [
                self._normalized_record(record_id, project_id, source_record_id=f"src-{record_id}")
                for record_id in normalized_ids
            ],
        )

    def _normalized_record(
        self,
        record_id: str,
        project_id: str,
        *,
        source_record_id: str,
    ) -> NormalizedLiteratureRecord:
        return NormalizedLiteratureRecord(
            record_id=record_id,
            batch_id="batch-1",
            project_id=project_id,
            source="ris",
            source_record_id=source_record_id,
            title=f"Title {record_id}",
            title_normalized=f"title {record_id}",
            source_trace=[record_id],
        )
