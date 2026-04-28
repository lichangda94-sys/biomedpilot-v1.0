import tempfile
import unittest
from pathlib import Path

from scripts.export_requirements import (
    build_requirements_content,
    build_requirements_summary,
    check_requirements,
    export_requirements,
    main,
    read_project_dependencies,
    write_requirements,
)


class RequirementsExportTests(unittest.TestCase):
    def test_exports_project_dependencies_from_pyproject(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text(
                """
[project]
dependencies = [
    "PySide6>=6.7,<7",
    "requests>=2",
]
""".strip()
                + "\n",
                encoding="utf-8",
            )

            export = export_requirements(pyproject)

        self.assertEqual(
            export.dependencies,
            ("PySide6>=6.7,<7", "requests>=2"),
        )
        self.assertIn("PySide6>=6.7,<7", export.content)
        self.assertIn("requests>=2", export.content)

    def test_no_declared_dependencies_has_stable_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text("[project]\nname = \"example\"\n", encoding="utf-8")

            dependencies = read_project_dependencies(pyproject)
            content = build_requirements_content(
                dependencies,
                source_name="pyproject.toml",
            )

        self.assertEqual(dependencies, ())
        self.assertIn("# No project dependencies declared.", content)

    def test_check_mode_reports_in_sync_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pyproject = root / "pyproject.toml"
            requirements = root / "requirements.txt"
            pyproject.write_text(
                "[project]\ndependencies = [\"PySide6>=6.7,<7\"]\n",
                encoding="utf-8",
            )
            export = export_requirements(pyproject)
            write_requirements(requirements, export)

            result = main(
                [
                    "--check",
                    "--pyproject",
                    str(pyproject),
                    "--requirements",
                    str(requirements),
                ]
            )

        self.assertEqual(result, 0)

    def test_check_mode_reports_out_of_sync_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            pyproject = root / "pyproject.toml"
            requirements = root / "requirements.txt"
            pyproject.write_text(
                "[project]\ndependencies = [\"PySide6>=6.7,<7\"]\n",
                encoding="utf-8",
            )
            requirements.write_text("stale\n", encoding="utf-8")
            export = export_requirements(pyproject)
            lines = build_requirements_summary(
                requirements,
                export,
                check=True,
                in_sync=check_requirements(requirements, export),
            )

            result = main(
                [
                    "--check",
                    "--pyproject",
                    str(pyproject),
                    "--requirements",
                    str(requirements),
                ]
            )

        self.assertEqual(result, 1)
        self.assertIn("- check: out of sync", lines)


if __name__ == "__main__":
    unittest.main()
