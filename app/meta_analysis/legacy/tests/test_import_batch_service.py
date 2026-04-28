import tempfile
import unittest
from pathlib import Path

from literature.batch_service import ImportBatchService
from literature.models import (
    ImportBatchStatus,
    ImportFormatHint,
    ImportSourceKind,
    ParsedLiteratureRecord,
)
from literature.parser import ImportParseContext, UnsupportedParserError
from literature.service import LiteratureProjectService
from literature.store import LiteratureStore


class SuccessfulStubParser:
    supported_format = ImportFormatHint.RIS

    def parse(
        self,
        file_path: Path,
        context: ImportParseContext,
    ) -> list[ParsedLiteratureRecord]:
        return [
            ParsedLiteratureRecord(
                batch_id=context.batch_id,
                project_id=context.project_id,
                source="stub",
                source_record_id="r-001",
                title="Example Title",
                authors=["Alice", "Bob"],
                raw_payload={"path": str(file_path)},
            )
        ]


class FailingStubParser:
    supported_format = ImportFormatHint.NBIB

    def parse(
        self,
        file_path: Path,
        context: ImportParseContext,
    ) -> list[ParsedLiteratureRecord]:
        raise RuntimeError("parser exploded")


class ImportBatchServiceTests(unittest.TestCase):
    def test_create_batch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            project_service = LiteratureProjectService.from_root_dir(root_dir)
            project = project_service.create_project("Batch Demo")
            batch_service = ImportBatchService.from_root_dir(root_dir)

            batch = batch_service.create_batch(
                project.project_id,
                "/tmp/demo.ris",
                source_type=ImportSourceKind.FILE,
                format_hint=ImportFormatHint.RIS,
            )

        self.assertEqual(batch.project_id, project.project_id)
        self.assertEqual(batch.status, ImportBatchStatus.PENDING)
        self.assertEqual(batch.input_path, "/tmp/demo.ris")

    def test_status_flow_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            project_service = LiteratureProjectService.from_root_dir(root_dir)
            project = project_service.create_project("Batch Status")
            batch_service = ImportBatchService(
                LiteratureStore(root_dir),
                parsers={ImportFormatHint.RIS: SuccessfulStubParser()},
            )
            batch = batch_service.create_batch(
                project.project_id,
                "/tmp/demo.ris",
                format_hint=ImportFormatHint.RIS,
            )

            executed = batch_service.execute_batch(batch.batch_id)
            stored_batch = LiteratureStore(root_dir).get_import_batch(batch.batch_id)

        self.assertEqual(executed.status, ImportBatchStatus.COMPLETED)
        self.assertEqual(executed.total_records, 1)
        self.assertEqual(executed.imported_records, 1)
        self.assertIsNotNone(executed.started_at)
        self.assertIsNotNone(executed.finished_at)
        self.assertIsNotNone(stored_batch)
        assert stored_batch is not None
        self.assertEqual(stored_batch.status, ImportBatchStatus.COMPLETED)

    def test_empty_parse_result_import(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            project_service = LiteratureProjectService.from_root_dir(root_dir)
            project = project_service.create_project("Empty Import")
            batch_service = ImportBatchService.from_root_dir(root_dir)
            empty_csv = Path(__file__).parent / "fixtures" / "empty.csv"
            batch = batch_service.create_batch(
                project.project_id,
                str(empty_csv),
                format_hint=ImportFormatHint.CSV,
            )

            executed = batch_service.execute_batch(batch.batch_id)
            parsed_records = LiteratureStore(root_dir).list_parsed_records(
                batch_id=batch.batch_id
            )

        self.assertEqual(executed.status, ImportBatchStatus.COMPLETED)
        self.assertEqual(executed.total_records, 0)
        self.assertEqual(executed.imported_records, 0)
        self.assertEqual(parsed_records, [])

    def test_failed_status_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            project_service = LiteratureProjectService.from_root_dir(root_dir)
            project = project_service.create_project("Broken Parser")
            batch_service = ImportBatchService(
                LiteratureStore(root_dir),
                parsers={ImportFormatHint.NBIB: FailingStubParser()},
            )
            batch = batch_service.create_batch(
                project.project_id,
                "/tmp/input.nbib",
                format_hint=ImportFormatHint.NBIB,
            )

            with self.assertRaisesRegex(RuntimeError, "parser exploded"):
                batch_service.execute_batch(batch.batch_id)

            stored_batch = LiteratureStore(root_dir).get_import_batch(batch.batch_id)

        self.assertIsNotNone(stored_batch)
        assert stored_batch is not None
        self.assertEqual(stored_batch.status, ImportBatchStatus.FAILED)
        self.assertEqual(stored_batch.error_message, "parser exploded")

    def test_unsupported_format_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            project_service = LiteratureProjectService.from_root_dir(root_dir)
            project = project_service.create_project("Unsupported Format")
            batch_service = ImportBatchService(
                LiteratureStore(root_dir),
                parsers={ImportFormatHint.RIS: SuccessfulStubParser()},
            )
            batch = batch_service.create_batch(
                project.project_id,
                "/tmp/demo.bib",
                format_hint=ImportFormatHint.BIBTEX,
            )

            with self.assertRaisesRegex(
                UnsupportedParserError,
                "Unsupported import format: bibtex",
            ):
                batch_service.execute_batch(batch.batch_id)

            stored_batch = LiteratureStore(root_dir).get_import_batch(batch.batch_id)

        self.assertIsNotNone(stored_batch)
        assert stored_batch is not None
        self.assertEqual(stored_batch.status, ImportBatchStatus.FAILED)
        self.assertEqual(stored_batch.error_message, "Unsupported import format: bibtex")
