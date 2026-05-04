from __future__ import annotations

import ast
from pathlib import Path

from app.shared.search_context import BIOINFORMATICS_SEARCH_CONTEXT, META_ANALYSIS_SEARCH_CONTEXT


REPO_ROOT = Path(__file__).resolve().parents[2]


def _runtime_python_files(root: str) -> list[Path]:
    base = REPO_ROOT / root
    return sorted(
        path
        for path in base.rglob("*.py")
        if "__pycache__" not in path.parts and "legacy" not in path.parts
    )


def _python_files(root: str) -> list[Path]:
    base = REPO_ROOT / root
    return sorted(path for path in base.rglob("*.py") if "__pycache__" not in path.parts)


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _imported_modules(path: Path) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(_parse(path)):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append("." * node.level + (node.module or ""))
    return modules


def _called_or_referenced_names(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(_parse(path)):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Call):
            names.add(_call_name(node.func))
    return {name for name in names if name}


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _relative(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _module_starts_with(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(f"{prefix}.")


def test_shared_runtime_does_not_depend_on_product_modules() -> None:
    violations: list[str] = []
    forbidden_prefixes = ("app.bioinformatics", "app.meta_analysis")

    for path in _runtime_python_files("app/shared"):
        for module in _imported_modules(path):
            if any(_module_starts_with(module, prefix) for prefix in forbidden_prefixes):
                violations.append(f"{_relative(path)} imports {module}")

    assert violations == []


def test_bioinformatics_runtime_does_not_call_literature_retrieval_services() -> None:
    violations: list[str] = []
    forbidden_import_fragments = (
        "literature_search",
        "pubmed_search_service",
        "PubMedSearchService",
    )
    forbidden_runtime_names = {
        "PubMedSearchService",
        "pubmed_search_service",
        "search_pubmed",
        "search_pubmed_articles",
        "literature_search",
        "WebOfScienceSearchService",
        "EmbaseSearchService",
        "CNKISearchService",
        "RISImportService",
        "NBIBImportService",
        "ZoteroImportService",
        "EndNoteImportService",
    }

    for path in _runtime_python_files("app/bioinformatics"):
        for module in _imported_modules(path):
            if any(fragment in module for fragment in forbidden_import_fragments):
                violations.append(f"{_relative(path)} imports {module}")
        names = _called_or_referenced_names(path)
        for name in sorted(forbidden_runtime_names.intersection(names)):
            violations.append(f"{_relative(path)} references {name}")

    assert violations == []


def test_meta_runtime_does_not_call_bioinformatics_retrieval_services() -> None:
    violations: list[str] = []
    forbidden_modules = (
        "app.bioinformatics",
        "geo_search_service",
        "tcga_search_service",
        "gtex_search_service",
    )
    forbidden_runtime_names = {
        "GeoSearchService",
        "BioinformaticsSourceRouter",
        "GeoSearchAdapter",
        "TcgaGdcSearchAdapter",
        "GtexSearchAdapter",
        "geo_search_service",
        "tcga_search_service",
        "gtex_search_service",
        "search_geo",
        "search_gse",
        "search_tcga",
        "search_gdc",
        "search_gtex",
    }

    for path in _runtime_python_files("app/meta_analysis"):
        for module in _imported_modules(path):
            if any(_module_starts_with(module, forbidden) or forbidden in module for forbidden in forbidden_modules):
                violations.append(f"{_relative(path)} imports {module}")
        names = _called_or_referenced_names(path)
        for name in sorted(forbidden_runtime_names.intersection(names)):
            violations.append(f"{_relative(path)} references {name}")

    assert violations == []


def test_legacy_literature_and_geo_readiness_modules_are_not_imported_by_mainline() -> None:
    violations: list[str] = []
    forbidden_prefixes = (
        "app.bioinformatics.legacy.literature_cli",
        "app.bioinformatics.legacy.literature_gui",
        "app.meta_analysis.legacy.geo_readiness",
    )

    for path in _python_files("app"):
        if "legacy" in path.parts:
            continue
        for module in _imported_modules(path):
            if any(_module_starts_with(module, prefix) for prefix in forbidden_prefixes):
                violations.append(f"{_relative(path)} imports {module}")

    assert violations == []


def test_search_context_database_boundaries() -> None:
    bio_allowed = {value.lower() for value in BIOINFORMATICS_SEARCH_CONTEXT.allowed_databases}
    bio_forbidden = {value.lower() for value in BIOINFORMATICS_SEARCH_CONTEXT.forbidden_databases}
    meta_allowed = {value.lower() for value in META_ANALYSIS_SEARCH_CONTEXT.allowed_databases}
    meta_forbidden = {value.lower() for value in META_ANALYSIS_SEARCH_CONTEXT.forbidden_databases}

    assert {"geo", "gse", "tcga", "gtex", "local"} <= bio_allowed
    assert {"pubmed", "wos", "embase", "cnki", "zotero", "endnote"} <= bio_forbidden
    assert {"pubmed", "wos", "embase", "cnki", "zotero", "endnote", "ris", "nbib", "csv"} <= meta_allowed
    assert {"geo", "gse", "tcga", "gtex"} <= meta_forbidden
