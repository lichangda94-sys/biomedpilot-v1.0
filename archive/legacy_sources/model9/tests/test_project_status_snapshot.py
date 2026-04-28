import tempfile
import unittest
from pathlib import Path
from typing import Sequence

from scripts.project_status_snapshot import (
    CommandResult,
    KEY_DIRECTORIES,
    KEY_SCRIPTS,
    build_project_status_summary,
    inspect_project_status,
    main,
)


class ProjectStatusSnapshotTests(unittest.TestCase):
    def test_reports_git_status_tags_directories_and_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for path in KEY_DIRECTORIES:
                (root / path).mkdir(parents=True, exist_ok=True)
            for path in KEY_SCRIPTS:
                file_path = root / path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text("placeholder\n", encoding="utf-8")

            def runner(command: Sequence[str], cwd: Path) -> CommandResult:
                self.assertEqual(cwd, root)
                if command == ("git", "rev-parse", "--is-inside-work-tree"):
                    return CommandResult(0, "true\n")
                if command == ("git", "branch", "--show-current"):
                    return CommandResult(0, "main\n")
                if command == ("git", "rev-parse", "--short", "HEAD"):
                    return CommandResult(0, "abc1234\n")
                if command == ("git", "status", "--short"):
                    return CommandResult(0, "")
                if command == ("git", "tag", "--list", "v0.*"):
                    return CommandResult(0, "v0.16-ui-mock-runner-diagnostics\n")
                return CommandResult(1, "")

            snapshot = inspect_project_status(root, runner=runner)
            lines = build_project_status_summary(root, runner=runner)

        self.assertTrue(snapshot.git_available)
        self.assertTrue(snapshot.git_repo)
        self.assertEqual(snapshot.branch, "main")
        self.assertEqual(snapshot.head, "abc1234")
        self.assertTrue(snapshot.working_tree_clean)
        self.assertEqual(snapshot.tags, ("v0.16-ui-mock-runner-diagnostics",))
        self.assertIn("- branch: main", lines)
        self.assertIn("- head: abc1234", lines)
        self.assertIn("- working tree clean: yes", lines)
        self.assertIn("- v0.16-ui-mock-runner-diagnostics", lines)
        self.assertIn("- scripts/run_dev_checks.py: present", lines)

    def test_reports_dirty_working_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            def runner(command: Sequence[str], cwd: Path) -> CommandResult:
                if command == ("git", "rev-parse", "--is-inside-work-tree"):
                    return CommandResult(0, "true\n")
                if command == ("git", "branch", "--show-current"):
                    return CommandResult(0, "main\n")
                if command == ("git", "rev-parse", "--short", "HEAD"):
                    return CommandResult(0, "abc1234\n")
                if command == ("git", "status", "--short"):
                    return CommandResult(0, " M README.md\n")
                if command == ("git", "tag", "--list", "v0.*"):
                    return CommandResult(0, "")
                return CommandResult(1, "")

            lines = build_project_status_summary(root, runner=runner)

        self.assertIn("- working tree clean: no", lines)

    def test_reports_non_git_repo_with_stable_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            def runner(command: Sequence[str], cwd: Path) -> CommandResult:
                return CommandResult(128, "", "not a git repository")

            snapshot = inspect_project_status(root, runner=runner)
            lines = build_project_status_summary(root, runner=runner)

        self.assertTrue(snapshot.git_available)
        self.assertFalse(snapshot.git_repo)
        self.assertIsNone(snapshot.working_tree_clean)
        self.assertIn("- git repo: no", lines)
        self.assertIn("- branch: unavailable", lines)
        self.assertIn("- working tree clean: unknown", lines)
        self.assertIn("- none", lines)

    def test_reports_git_unavailable_with_stable_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            def runner(command: Sequence[str], cwd: Path) -> CommandResult:
                return CommandResult(127, "", "git not found")

            snapshot = inspect_project_status(root, runner=runner)
            lines = build_project_status_summary(root, runner=runner)

        self.assertFalse(snapshot.git_available)
        self.assertFalse(snapshot.git_repo)
        self.assertIn("- git available: no", lines)
        self.assertIn("- git repo: no", lines)

    def test_main_returns_success_for_read_only_snapshot(self) -> None:
        self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
