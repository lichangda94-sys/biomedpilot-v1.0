from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACTIVE_APP_TARGETS = (
    PROJECT_ROOT / "app" / "meta_analysis" / "adapters",
    PROJECT_ROOT / "app" / "meta_analysis" / "services",
    PROJECT_ROOT / "app" / "meta_analysis" / "pages",
    PROJECT_ROOT / "app" / "meta_analysis" / "workspace.py",
)
ACTIVE_TEST_TARGETS = (
    PROJECT_ROOT / "tests" / "meta_analysis" / "test_stage_6_literature_import_panel.py",
    PROJECT_ROOT / "tests" / "meta_analysis" / "test_literature_contract_hardening.py",
)


def test_active_meta_runtime_does_not_use_legacy_bridge() -> None:
    forbidden_runtime_tokens = (
        "_legacy_path",
        "LEGACY_ROOT",
        "app.meta_analysis.legacy",
        "app/meta_analysis/legacy",
        "from literature.",
        "from extraction.models",
        "from analysis.",
    )

    for path in _python_files(ACTIVE_APP_TARGETS):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_runtime_tokens:
            assert token not in text, f"{path} still contains active legacy bridge token {token}"


def test_active_literature_tests_do_not_depend_on_legacy_batch_service() -> None:
    forbidden_test_tokens = (
        "_legacy_path",
        "literature.batch_service",
        "executes_legacy_batch_service",
        "before_legacy_execution",
    )

    for path in _python_files(ACTIVE_TEST_TARGETS):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_test_tokens:
            assert token not in text, f"{path} still depends on legacy batch import token {token}"


def _python_files(targets: tuple[Path, ...]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        if target.is_file():
            files.append(target)
        else:
            files.extend(sorted(path for path in target.rglob("*.py") if "legacy" not in path.parts))
    return files
