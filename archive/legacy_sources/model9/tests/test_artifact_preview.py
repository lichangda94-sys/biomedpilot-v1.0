import tempfile
import unittest
from pathlib import Path

from core.task_management import TaskManagementService


class ArtifactPreviewServiceTests(unittest.TestCase):
    def test_preview_existing_csv_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / "summary.csv"
            artifact.write_text("analysis_id,value\nanalysis-1,42\n", encoding="utf-8")
            service, result = self._record_result(root, artifact)

            preview = service.preview_result_artifact(result.result_id)

        self.assertTrue(preview.exists)
        self.assertTrue(preview.preview_available)
        self.assertEqual(preview.file_name, "summary.csv")
        self.assertEqual(preview.file_extension, ".csv")
        self.assertIn("analysis_id,value", preview.preview_text)
        self.assertEqual(preview.error_code, "")

    def test_preview_existing_json_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / "summary.json"
            artifact.write_text('{"analysis_id": "analysis-1"}', encoding="utf-8")
            service, result = self._record_result(root, artifact)

            preview = service.preview_result_artifact(result.result_id)

        self.assertTrue(preview.exists)
        self.assertTrue(preview.preview_available)
        self.assertEqual(preview.file_extension, ".json")
        self.assertIn("analysis-1", preview.preview_text)

    def test_missing_artifact_returns_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / "missing.csv"
            service, result = self._record_result(root, artifact)

            preview = service.preview_result_artifact(result.result_id)

        self.assertFalse(preview.exists)
        self.assertFalse(preview.preview_available)
        self.assertEqual(preview.error_code, "missing")
        self.assertEqual(preview.artifact_path, str(artifact))

    def test_result_without_artifact_path_returns_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir) / "state")
            task = service.create_task("reporting.summary", "Result without artifact")
            result = service.record_result(task.task_id, "note")

            preview = service.preview_result_artifact(result.result_id)

        self.assertFalse(preview.exists)
        self.assertFalse(preview.preview_available)
        self.assertEqual(preview.error_code, "not_applicable")

    def test_unsupported_extension_returns_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / "plot.png"
            artifact.write_bytes(b"not-a-real-image")
            service, result = self._record_result(root, artifact)

            preview = service.preview_result_artifact(result.result_id)

        self.assertTrue(preview.exists)
        self.assertFalse(preview.preview_available)
        self.assertEqual(preview.file_extension, ".png")
        self.assertEqual(preview.error_code, "unsupported")
        self.assertEqual(preview.preview_text, "")

    def test_max_chars_limits_preview_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / "summary.txt"
            artifact.write_text("abcdef", encoding="utf-8")
            service, result = self._record_result(root, artifact)

            preview = service.preview_result_artifact(result.result_id, max_chars=3)

        self.assertEqual(preview.preview_text, "abc")

    def test_preview_does_not_change_result_or_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact = root / "summary.md"
            artifact.write_text("# Summary\n", encoding="utf-8")
            service, result = self._record_result(root, artifact)
            before_result = result.to_dict()
            before_text = artifact.read_text(encoding="utf-8")

            service.preview_result_artifact(result.result_id)
            after_result = service.list_results()[0].to_dict()
            after_text = artifact.read_text(encoding="utf-8")

        self.assertEqual(after_result, before_result)
        self.assertEqual(after_text, before_text)

    def test_missing_result_returns_result_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = TaskManagementService.from_state_dir(Path(temp_dir) / "state")

            preview = service.preview_result_artifact("missing-result")

        self.assertFalse(preview.exists)
        self.assertFalse(preview.preview_available)
        self.assertEqual(preview.error_code, "result_not_found")

    def _record_result(self, root: Path, artifact: Path):
        service = TaskManagementService.from_state_dir(root / "state")
        task = service.create_task("reporting.summary", "Preview artifact")
        result = service.record_result(
            task.task_id,
            "profile_reporting_summary",
            artifact_path=str(artifact),
        )
        return service, result


if __name__ == "__main__":
    unittest.main()
