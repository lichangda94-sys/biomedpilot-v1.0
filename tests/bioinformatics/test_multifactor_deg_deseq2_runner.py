from __future__ import annotations

from pathlib import Path

from app.analysis_runtime import build_standard_analysis_package_catalog, validate_standard_result_package
from app.bioinformatics.deg_engine import check_multifactor_r_backend, run_controlled_multifactor_deseq2_fixture
from app.bioinformatics.deg_engine.multifactor_schema import validate_multifactor_deg_result_index_entry
from app.bioinformatics.results.registry import load_registry


def test_multifactor_deseq2_backend_detects_external_r_runtime() -> None:
    snapshot = check_multifactor_r_backend("DESeq2")

    assert snapshot["schema_version"] == "biomedpilot.multifactor_deg_r_dependency_snapshot.v1"
    assert snapshot["install_action"] == "none_detect_first_only"
    if snapshot["status"] == "passed":
        assert snapshot["r_backend"]["packages"]["DESeq2"]["available"] is True
    else:
        assert snapshot["blockers"]


def test_controlled_multifactor_deseq2_fixture_registers_formal_result(tmp_path: Path) -> None:
    result = run_controlled_multifactor_deseq2_fixture(tmp_path, allow_legacy_sidecar_execution=True)

    assert result["status"] == "passed", result.get("blockers")
    assert result["parameter_manifest"]["backend_method"] == "DESeq2"
    assert result["parameter_manifest"]["value_type_policy"] == "passed_count_model_requires_raw_counts"

    table = Path(result["result_table_path"])
    standard_package_dir = Path(result["standard_result_package_dir"])
    assert table.is_file()
    assert standard_package_dir.is_dir()
    text = table.read_text(encoding="utf-8")
    assert "p_value" in text
    assert "adjusted_p_value" in text
    assert validate_standard_result_package(
        standard_package_dir,
        expected_module_id="deg",
        expected_task_id=str(result["task_run_id"]),
        expected_mode="full",
    )["status"] == "passed"

    entry = next(item for item in load_registry(tmp_path)["results"] if item["result_id"] == result["result_id"])
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["engine_name"] == "r_deseq2_multifactor"
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []
    assert entry["report_ready_eligible"] is False
    assert any(item["artifact_type"] == "standard_result_package" for item in entry["output_artifacts"])
    assert validate_multifactor_deg_result_index_entry(entry)["status"] == "passed"
    catalog = build_standard_analysis_package_catalog(tmp_path)
    assert catalog["package_count"] == 1
    assert catalog["rows"][0]["module_id"] == "deg"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1


def test_multifactor_deseq2_blocks_non_count_value_type(tmp_path: Path) -> None:
    result = run_controlled_multifactor_deseq2_fixture(tmp_path, value_type="TPM")

    assert result["status"] == "blocked"
    assert "blocked_count_model_requires_raw_counts" in result["blockers"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()
