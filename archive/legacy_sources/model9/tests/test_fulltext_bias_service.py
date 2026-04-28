import tempfile
import unittest
from pathlib import Path

from bias.models import BiasJudgement
from bias.service import BiasAssessmentService
from extraction.models import ExtractionRecord
from extraction.store import ExtractionStore
from fulltext.models import AvailabilityStatus
from fulltext.service import FullTextService
from literature.models import ScreeningDecision, ScreeningRecord, ScreeningStage
from literature.store import LiteratureStore


class FullTextBiasServiceTests(unittest.TestCase):
    def test_attach_fulltext_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            self._seed_screening(root_dir, "screen-1", "proj-1", "norm-1")
            service = FullTextService.from_root_dir(root_dir)

            record = service.attach_file(
                "screen-1",
                file_name="study1.pdf",
                file_path="/tmp/study1.pdf",
                import_method="manual_upload",
            )

        self.assertEqual(record.availability_status, AvailabilityStatus.AVAILABLE)
        self.assertEqual(record.file_type, "pdf")
        self.assertEqual(record.import_method, "manual_upload")

    def test_update_fulltext_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            self._seed_screening(root_dir, "screen-2", "proj-1", "norm-2")
            service = FullTextService.from_root_dir(root_dir)
            record = service.attach_file(
                "screen-2",
                file_name="study2.pdf",
                file_path="/tmp/study2.pdf",
            )

            updated = service.update_status(
                record.fulltext_record_id,
                availability_status=AvailabilityStatus.MISSING,
                notes="library request pending",
            )

        self.assertEqual(updated.availability_status, AvailabilityStatus.MISSING)
        self.assertEqual(updated.notes, "library request pending")

    def test_initialize_bias_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = BiasAssessmentService.from_root_dir(root_dir)

            domains = service.initialize_default_domains()

        self.assertEqual(len(domains), 3)
        self.assertEqual(domains[0].tool_name, "nos_cohort_minimal")

    def test_save_and_update_bias_domain_judgement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            self._seed_screening(root_dir, "screen-3", "proj-2", "norm-3")
            self._seed_extraction(root_dir, "extr-3", "proj-2", "screen-3", "norm-3")
            service = BiasAssessmentService.from_root_dir(root_dir)

            created = service.submit_domain_judgement(
                "screen-3",
                extraction_record_id="extr-3",
                domain_name="selection",
                judgement=BiasJudgement.UNCLEAR,
                support_text="sampling not fully described",
            )
            updated = service.submit_domain_judgement(
                "screen-3",
                extraction_record_id="extr-3",
                domain_name="selection",
                judgement=BiasJudgement.LOW,
                support_text="sampling acceptable",
            )

        self.assertEqual(created.domain_name, "selection")
        self.assertEqual(updated.judgement, BiasJudgement.LOW)
        self.assertEqual(updated.support_text, "sampling acceptable")

    def test_overall_bias_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            self._seed_screening(root_dir, "screen-4", "proj-3", "norm-4")
            service = BiasAssessmentService.from_root_dir(root_dir)

            service.submit_domain_judgement(
                "screen-4",
                domain_name="selection",
                judgement=BiasJudgement.LOW,
            )
            service.submit_domain_judgement(
                "screen-4",
                domain_name="comparability",
                judgement=BiasJudgement.HIGH,
            )

            overall = service.summarize_overall_judgement("screen-4")

        self.assertEqual(overall, BiasJudgement.HIGH)

    def test_bias_assessment_table_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            self._seed_screening(root_dir, "screen-5", "proj-4", "norm-5")
            service = BiasAssessmentService.from_root_dir(root_dir)
            service.submit_domain_judgement(
                "screen-5",
                domain_name="selection",
                judgement=BiasJudgement.LOW,
                support_text="cohort clearly defined",
            )
            service.submit_domain_judgement(
                "screen-5",
                domain_name="outcome_assessment",
                judgement=BiasJudgement.UNCLEAR,
                support_text="blinding unclear",
            )

            table = service.generate_bias_assessment_table("screen-5")

        self.assertEqual(table.project_id, "proj-4")
        self.assertEqual(table.tool_name, "nos_cohort_minimal")
        self.assertEqual(len(table.rows), 2)
        self.assertEqual(table.overall_judgement, BiasJudgement.UNCLEAR)

    def _seed_screening(
        self,
        root_dir: Path,
        screening_record_id: str,
        project_id: str,
        normalized_record_id: str,
    ) -> None:
        store = LiteratureStore(root_dir)
        store.replace_screening_records(
            project_id,
            ScreeningStage.FULL_TEXT_SCREENING,
            [
                ScreeningRecord(
                    screening_record_id=screening_record_id,
                    project_id=project_id,
                    source_record_id=f"src-{screening_record_id}",
                    normalized_record_id=normalized_record_id,
                    stage=ScreeningStage.FULL_TEXT_SCREENING,
                    decision=ScreeningDecision.INCLUDED,
                )
            ],
        )

    def _seed_extraction(
        self,
        root_dir: Path,
        extraction_record_id: str,
        project_id: str,
        screening_record_id: str,
        normalized_record_id: str,
    ) -> None:
        store = ExtractionStore(root_dir)
        store.save_extraction_record(
            ExtractionRecord(
                extraction_record_id=extraction_record_id,
                project_id=project_id,
                screening_record_id=screening_record_id,
                normalized_record_id=normalized_record_id,
                study_title="Study",
            )
        )
