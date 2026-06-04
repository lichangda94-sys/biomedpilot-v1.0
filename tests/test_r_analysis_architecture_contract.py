from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_MODULES = {
    "survival",
    "univariate",
    "multivariate",
    "enrichment",
    "immune_infiltration",
    "spatial_transcriptomics",
    "docking",
    "molecular_dynamics",
}


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_analysis_registry_declares_standard_modules_modes_and_package_contract() -> None:
    registry = read_json(ROOT / "analysis" / "registry" / "analysis_modules.json")

    assert registry["schema_version"] == "biomedpilot.analysis_modules.v1"
    assert registry["standard_entrypoint"] == "analysis/runners/run_module.R"
    assert registry["standard_result_package"] == {
        "required_files": ["result.json", "provenance.json"],
        "required_directories": ["tables", "plots", "reports", "logs"],
    }
    modules = {item["module_id"]: item for item in registry["modules"]}  # type: ignore[index]
    assert REQUIRED_MODULES <= set(modules)
    for module_id, module in modules.items():
        modes = module["modes"]
        assert modes["mock"]["supported"] is True
        assert "lite" in modes
        assert "full" in modes
        assert module["result_package_contract"] == "analysis/schemas/output/result_package.schema.json"
        assert module["analysis_environment"]


def test_standard_schemas_and_mock_result_package_exist_without_r_dependency() -> None:
    input_schema = read_json(ROOT / "analysis" / "schemas" / "input" / "module_input.schema.json")
    output_schema = read_json(ROOT / "analysis" / "schemas" / "output" / "result_package.schema.json")
    result = read_json(ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / "result.json")
    provenance = read_json(ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / "provenance.json")

    assert "module_id" in input_schema["required"]
    assert "result_json" in output_schema["required"]
    assert "provenance_json" in output_schema["required"]
    assert result["mode"] == "mock"
    assert result["status"] == "passed"
    assert provenance["mode"] == "mock"
    for dirname in ("tables", "plots", "reports", "logs"):
        assert (ROOT / "analysis" / "fixtures" / "outputs" / "mock_result_package" / dirname).exists()


def test_default_source_tree_does_not_install_r_packages_in_request_flow() -> None:
    forbidden = (
        "install.packages",
        "BiocManager::install",
        "pak::pkg_install",
        "remotes::install_github",
    )
    searched_roots = [ROOT / "app", ROOT / "scripts", ROOT / "analysis"]
    offenders: list[str] = []
    for root in searched_roots:
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".r", ".rscript", ".sh"}:
                continue
            if "__pycache__" in path.parts or "legacy" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for needle in forbidden:
                if needle in text:
                    offenders.append(f"{path.relative_to(ROOT)}:{needle}")
    assert offenders == []

