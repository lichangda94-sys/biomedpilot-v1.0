from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DOC = REPO_ROOT / "docs" / "ai_gateway_ollama_existing_call_audit.md"

DIRECT_OLLAMA_PATTERNS = (
    '["ollama", "run"',
    "/api/generate",
    "/api/tags",
    'shutil.which("ollama")',
    "command -v ollama",
    "localhost:11434",
    "127.0.0.1:11434",
)

EXPECTED_DIRECT_OLLAMA_FILES = {
    "app/shared/ai_gateway/providers/ollama_provider.py",
    "app/shared/local_engines/ollama_llm_engine.py",
    "app/shared/local_engines/ollama_llm_registry.py",
    "app/bioinformatics/legacy/geo_tool/geo_text_processor.py",
    "app/bioinformatics/legacy/geo_tool/bootstrap_geo_tool.sh",
    "archive/legacy_sources/bioinformatics_project/geo_tool/geo_text_processor.py",
    "archive/legacy_sources/bioinformatics_project/geo_tool/bootstrap_geo_tool.sh",
}

ACTIVE_APP_DIRECT_OLLAMA_FILES = {
    "app/shared/ai_gateway/providers/ollama_provider.py",
    "app/shared/local_engines/ollama_llm_engine.py",
    "app/shared/local_engines/ollama_llm_registry.py",
}

LEGACY_APP_DIRECT_OLLAMA_FILES = {
    "app/bioinformatics/legacy/geo_tool/geo_text_processor.py",
    "app/bioinformatics/legacy/geo_tool/bootstrap_geo_tool.sh",
}


def test_ollama_existing_call_audit_records_all_direct_call_files() -> None:
    documented = AUDIT_DOC.read_text(encoding="utf-8")

    for path in EXPECTED_DIRECT_OLLAMA_FILES:
        assert path in documented

    discovered = _direct_ollama_files()
    assert discovered == EXPECTED_DIRECT_OLLAMA_FILES


def test_active_direct_ollama_calls_remain_isolated_from_meta_analysis_and_gateway() -> None:
    active_app_direct_calls = _direct_ollama_files(REPO_ROOT / "app") - LEGACY_APP_DIRECT_OLLAMA_FILES

    assert active_app_direct_calls == ACTIVE_APP_DIRECT_OLLAMA_FILES
    assert _direct_ollama_files(REPO_ROOT / "app" / "bioinformatics") == LEGACY_APP_DIRECT_OLLAMA_FILES
    assert _direct_ollama_files(REPO_ROOT / "app" / "meta_analysis") == set()
    assert _direct_ollama_files(REPO_ROOT / "app" / "shared" / "ai_gateway") == {
        "app/shared/ai_gateway/providers/ollama_provider.py"
    }
    assert _direct_ollama_files(REPO_ROOT / "app" / "shared" / "local_engines") == {
        "app/shared/local_engines/ollama_llm_engine.py",
        "app/shared/local_engines/ollama_llm_registry.py",
    }


def test_ollama_existing_call_audit_includes_required_sections() -> None:
    documented = AUDIT_DOC.read_text(encoding="utf-8")

    for heading in (
        "## Existing Call Inventory",
        "## Current Behavior",
        "## Safety Assessment",
        "## Reuse Candidates",
        "## Migration Plan",
        "## Risks",
        "## Recommended Next Stage",
    ):
        assert heading in documented


def test_no_ollama_chat_integration_exists_and_qwen_stays_in_role_registry() -> None:
    scanned_roots = [REPO_ROOT / "app", REPO_ROOT / "scripts", REPO_ROOT / "config"]
    text = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for root in scanned_roots if root.exists() for path in _text_files(root))

    assert "/api/chat" not in text
    qwen_files = {
        path.relative_to(REPO_ROOT).as_posix()
        for root in scanned_roots
        if root.exists()
        for path in _text_files(root)
        if "qwen" in path.read_text(encoding="utf-8", errors="ignore").lower()
    }
    assert qwen_files <= {
        "app/shared/ai_gateway/config.py",
        "app/shared/local_engines/ollama_llm_engine.py",
        "app/shared/local_engines/ollama_llm_registry.py",
    }


def _direct_ollama_files(*roots: Path) -> set[str]:
    scan_roots = roots or (REPO_ROOT / "app", REPO_ROOT / "archive")
    return _direct_ollama_files_in_roots(tuple(scan_roots))


def _direct_ollama_files_in_roots(roots: tuple[Path, ...]) -> set[str]:
    found: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in _text_files(root):
            content = path.read_text(encoding="utf-8", errors="ignore")
            if any(pattern in content for pattern in DIRECT_OLLAMA_PATTERNS):
                found.add(path.relative_to(REPO_ROOT).as_posix())
    return found


def _text_files(root: Path) -> list[Path]:
    excluded_parts = {"__pycache__", ".pytest_cache"}
    suffixes = {".py", ".sh", ".md", ".txt", ".json", ".yaml", ".yml", ".toml"}
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in suffixes
        and not any(part in excluded_parts for part in path.parts)
    ]
