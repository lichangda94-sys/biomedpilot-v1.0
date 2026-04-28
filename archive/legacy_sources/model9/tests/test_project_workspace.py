from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.project_workspace import (
    PROJECT_MANIFEST_FILENAME,
    ProjectWorkspaceStore,
)


class ProjectWorkspaceStoreTests(unittest.TestCase):
    def test_create_project_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProjectWorkspaceStore(Path(temp_dir))

            state = store.create_project(
                project_type="bioinformatics",
                name="Lung Cancer Study",
            )

            self.assertEqual(state.project_id, "lung-cancer-study")
            self.assertEqual(state.project_type, "bioinformatics")
            self.assertTrue((state.project_dir / PROJECT_MANIFEST_FILENAME).exists())

    def test_open_project_reads_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProjectWorkspaceStore(Path(temp_dir))
            created = store.create_project(
                project_type="meta_analysis",
                name="Cardiology Review",
                project_id="meta-cardio",
            )

            opened = store.open_project(created.project_dir)

            self.assertEqual(opened.project_id, "meta-cardio")
            self.assertEqual(opened.name, "Cardiology Review")
            self.assertEqual(opened.project_type, "meta_analysis")

    def test_save_project_updates_manifest_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProjectWorkspaceStore(Path(temp_dir))
            created = store.create_project(
                project_type="bioinformatics",
                name="Demo",
            )

            saved = store.save_project(created)

            self.assertEqual(saved.status, "saved")
            self.assertEqual(store.open_project(saved.project_dir).status, "saved")
