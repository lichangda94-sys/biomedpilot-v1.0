from __future__ import annotations

import json
from pathlib import Path

from app.analysis_runtime import build_standard_analysis_package_catalog, validate_standard_result_package
from app.bioinformatics.deg_engine import check_multifactor_r_backend, run_controlled_multifactor_limma_fixture
from app.bioinformatics.deg_engine.multifactor_schema import validate_multifactor_deg_result_index_entry
from app.bioinformatics.results.registry import load_registry


def test_multifactor_limma_backend_detects_external_r_runtime() -> None:
    snapshot = check_multifactor_r_backend("limma")

    assert snapshot["schema_version"] == "biomedpilot.multifactor_deg_r_dependency_snapshot.v1"
    assert snapshot["install_action"] == "none_detect_first_only"
    assert "r_backend_detect_first_no_auto_install" in snapshot["warnings"]
    if snapshot["status"] == "passed":
        assert snapshot["rscript"]["available"] is True
        assert snapshot["r_backend"]["packages"]["limma"]["available"] is True
    else:
        assert snapshot["blockers"]


def test_controlled_multifactor_limma_fixture_registers_formal_result(tmp_path: Path) -> None:
    result = run_controlled_multifactor_limma_fixture(tmp_path)

    assert result["status"] == "passed", result.get("blockers")
    assert result["parameter_manifest"]["design_formula"] == "~ batch + group"
    assert result["parameter_manifest"]["contrast"]["coefficient"] == "groupcase"
    assert result["dependency_snapshot"]["status"] == "passed"

    table = Path(result["result_table_path"])
    standard_package_dir = Path(result["standard_result_package_dir"])
    assert table.is_file()
    assert standard_package_dir.is_dir()
    text = table.read_text(encoding="utf-8")
    assert "p_value" in text
    assert "adjusted_p_value" in text
    validation = validate_standard_result_package(
        standard_package_dir,
        expected_module_id="deg",
        expected_task_id=str(result["task_run_id"]),
        expected_mode="full",
    )
    assert validation["status"] == "passed"

    registry = load_registry(tmp_path)
    entry = next(item for item in registry["results"] if item["result_id"] == result["result_id"])
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["engine_name"] == "r_limma_multifactor"
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []
    assert entry["report_ready_eligible"] is False
    assert any(item["artifact_type"] == "standard_result_package" for item in entry["output_artifacts"])
    assert validate_multifactor_deg_result_index_entry(entry)["status"] == "passed"
    catalog = build_standard_analysis_package_catalog(tmp_path)
    assert catalog["status"] == "passed"
    assert catalog["package_count"] == 1
    assert catalog["rows"][0]["module_id"] == "deg"
    assert catalog["rows"][0]["mode"] == "full"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1
    assert catalog["rows"][0]["artifact_counts"]["plots"] == 0

    log_path = tmp_path / entry["log_artifacts"][0]["path"]
    log = json.loads(log_path.read_text(encoding="utf-8"))
    assert log["task_run_id"] == result["task_run_id"]
    assert log["dependency_snapshot"]["status"] == "passed"
