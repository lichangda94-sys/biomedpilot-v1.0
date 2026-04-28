import tempfile
import unittest
from pathlib import Path

from literature.adapters import CsvImportAdapter, NbibImportAdapter, RisImportAdapter
from literature.batch_service import ImportBatchService
from literature.models import ImportBatchStatus, ImportFormatHint, ImportSourceKind
from literature.parser import ImportParseContext
from literature.service import LiteratureProjectService
from literature.store import LiteratureStore


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def make_context(format_hint: ImportFormatHint, input_path: Path) -> ImportParseContext:
    return ImportParseContext(
        batch_id="batch-fixture",
        project_id="proj-fixture",
        input_path=str(input_path),
        format_hint=format_hint,
        source_type=ImportSourceKind.FILE,
    )


class RealParserTests(unittest.TestCase):
    def test_ris_parser_extracts_records_and_authors(self) -> None:
        file_path = FIXTURES_DIR / "sample.ris"

        records = RisImportAdapter().parse(file_path, make_context(ImportFormatHint.RIS, file_path))

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].source_record_id, "RIS-001")
        self.assertEqual(records[0].title, "Effects of Tea on Sleep")
        self.assertEqual(records[0].authors, ["Zhang, Wei", "Smith, Jane"])
        self.assertEqual(records[0].journal, "Journal of Sleep Studies")
        self.assertEqual(records[0].year, 2024)
        self.assertEqual(records[0].doi, "10.1000/tea.001")
        self.assertEqual(records[0].keywords, ["sleep", "tea"])
        self.assertEqual(records[1].abstract, "")
        self.assertEqual(records[1].journal, "")

    def test_nbib_parser_extracts_records_and_multiauthors(self) -> None:
        file_path = FIXTURES_DIR / "sample.nbib"

        records = NbibImportAdapter().parse(file_path, make_context(ImportFormatHint.NBIB, file_path))

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].pmid, "12345678")
        self.assertEqual(records[0].authors, ["Doe, Jane", "Roe, John"])
        self.assertEqual(records[0].abstract, "Example abstract continued abstract line.")
        self.assertEqual(records[0].doi, "10.2000/nbib.001")
        self.assertEqual(records[1].journal, "")
        self.assertEqual(records[1].year, 2022)

    def test_csv_parser_extracts_records_and_tolerates_missing_fields(self) -> None:
        file_path = FIXTURES_DIR / "sample.csv"

        records = CsvImportAdapter().parse(file_path, make_context(ImportFormatHint.CSV, file_path))

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].source_record_id, "csv-001")
        self.assertEqual(records[0].authors, ["Alice", "Bob"])
        self.assertEqual(records[0].keywords, ["screening", "analysis"])
        self.assertEqual(records[1].title, "Sparse CSV Record")
        self.assertEqual(records[1].doi, "")
        self.assertEqual(records[1].language, "")

    def test_invalid_ris_file_raises_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid.ris"
            file_path.write_text("this is not a RIS file\n", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "Could not parse RIS file: no records found",
            ):
                RisImportAdapter().parse(file_path, make_context(ImportFormatHint.RIS, file_path))

    def test_batch_execution_with_real_parser_updates_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            project = LiteratureProjectService.from_root_dir(root_dir).create_project("RIS Batch")
            batch_service = ImportBatchService.from_root_dir(root_dir)
            file_path = FIXTURES_DIR / "sample.ris"
            batch = batch_service.create_batch(
                project.project_id,
                str(file_path),
                format_hint=ImportFormatHint.RIS,
            )

            executed = batch_service.execute_batch(batch.batch_id)
            parsed_records = LiteratureStore(root_dir).list_parsed_records(batch_id=batch.batch_id)

        self.assertEqual(executed.status, ImportBatchStatus.COMPLETED)
        self.assertEqual(executed.total_records, 2)
        self.assertEqual(executed.imported_records, 2)
        self.assertEqual(len(parsed_records), 2)

    def test_invalid_file_marks_batch_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            invalid_file = root_dir / "broken.ris"
            invalid_file.write_text("not a valid ris payload\n", encoding="utf-8")
            project = LiteratureProjectService.from_root_dir(root_dir).create_project("Broken RIS")
            batch_service = ImportBatchService.from_root_dir(root_dir)
            batch = batch_service.create_batch(
                project.project_id,
                str(invalid_file),
                format_hint=ImportFormatHint.RIS,
            )

            with self.assertRaisesRegex(
                ValueError,
                "Could not parse RIS file: no records found",
            ):
                batch_service.execute_batch(batch.batch_id)

            stored_batch = LiteratureStore(root_dir).get_import_batch(batch.batch_id)

        self.assertIsNotNone(stored_batch)
        assert stored_batch is not None
        self.assertEqual(stored_batch.status, ImportBatchStatus.FAILED)
