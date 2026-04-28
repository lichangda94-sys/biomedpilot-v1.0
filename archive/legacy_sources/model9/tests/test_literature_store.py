import tempfile
import unittest
from pathlib import Path

from literature.models import ImportFormatHint, ImportSourceKind
from literature.service import LiteratureProjectService
from literature.store import LiteratureStore


class LiteratureStoreTests(unittest.TestCase):
    def test_service_creates_project_and_import_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = LiteratureProjectService.from_root_dir(root_dir)

            project = service.create_project(
                "Oncology Intake",
                description="Module 2-A skeleton",
                tags=["oncology", "pilot"],
                metadata={"created_by": "tests"},
            )
            record = service.register_import(
                project.project_id,
                "/data/intake/batch-001.ris",
                source_kind=ImportSourceKind.FILE,
                format_hint=ImportFormatHint.RIS,
                note="first batch",
            )

            store = LiteratureStore(root_dir)
            projects = store.list_projects()
            imports = store.list_import_records(project.project_id)

        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].name, "Oncology Intake")
        self.assertEqual(projects[0].metadata["created_by"], "tests")
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].import_id, record.import_id)
        self.assertEqual(imports[0].format_hint, ImportFormatHint.RIS)

    def test_store_returns_none_for_unknown_project(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = LiteratureStore(Path(temp_dir))
            project = store.get_project("missing")

        self.assertIsNone(project)
