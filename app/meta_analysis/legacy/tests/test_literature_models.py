import unittest

from literature.models import (
    ImportBatch,
    ImportBatchStatus,
    ImportFormatHint,
    ImportRecord,
    ImportRecordStatus,
    ImportSourceKind,
    LiteratureProject,
    LiteratureProjectStatus,
    ParsedLiteratureRecord,
)


class LiteratureModelTests(unittest.TestCase):
    def test_project_round_trip(self) -> None:
        project = LiteratureProject(
            project_id="proj-001",
            name="Cardiology Review",
            description="Seed project",
            status=LiteratureProjectStatus.ACTIVE,
            tags=["cardiology"],
            metadata={"owner": "team-a"},
        )

        restored = LiteratureProject.from_dict(project.to_dict())

        self.assertEqual(restored.project_id, "proj-001")
        self.assertEqual(restored.name, "Cardiology Review")
        self.assertEqual(restored.tags, ["cardiology"])
        self.assertEqual(restored.metadata["owner"], "team-a")

    def test_import_record_transition_and_round_trip(self) -> None:
        record = ImportRecord(
            import_id="imp-001",
            project_id="proj-001",
            source_path="/tmp/source.ris",
            source_kind=ImportSourceKind.FILE,
            format_hint=ImportFormatHint.RIS,
        )
        record.transition(
            ImportRecordStatus.COMPLETED,
            "imported",
            discovered_count=10,
            imported_count=8,
        )

        restored = ImportRecord.from_dict(record.to_dict())

        self.assertEqual(restored.status, ImportRecordStatus.COMPLETED)
        self.assertEqual(restored.discovered_count, 10)
        self.assertEqual(restored.imported_count, 8)
        self.assertEqual(restored.note, "imported")

    def test_import_batch_and_parsed_record_round_trip(self) -> None:
        batch = ImportBatch(
            batch_id="batch-001",
            project_id="proj-001",
            source_type=ImportSourceKind.FILE,
            input_path="/tmp/source.ris",
            format_hint=ImportFormatHint.RIS,
        )
        batch.mark_running()
        batch.mark_completed(total_records=2, imported_records=2, warning_count=1)

        restored_batch = ImportBatch.from_dict(batch.to_dict())
        parsed = ParsedLiteratureRecord(
            batch_id="batch-001",
            project_id="proj-001",
            source="ris",
            source_record_id="r-1",
            title="A title",
            authors=["Alice"],
            keywords=["x"],
            raw_payload={"id": "r-1"},
        )
        restored_record = ParsedLiteratureRecord.from_dict(parsed.to_dict())

        self.assertEqual(restored_batch.status, ImportBatchStatus.COMPLETED)
        self.assertEqual(restored_batch.total_records, 2)
        self.assertEqual(restored_batch.warning_count, 1)
        self.assertEqual(restored_record.title, "A title")
        self.assertEqual(restored_record.authors, ["Alice"])
