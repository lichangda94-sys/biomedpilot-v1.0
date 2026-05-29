from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.pages.analysis_page import meta_statistics_engine_state_from_project
from app.meta_analysis.services.meta_result_contract_adapter import (
    META_RESULT_CONTRACT_SCHEMA_VERSION,
    MetaResultContractAdapter,
)
from app.meta_analysis.services.meta_statistics_engine_service import MetaStatisticsEngineService
from tests.meta_analysis.test_meta_statistics_engine_v2 import seed_binary_plan


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v2_statistics_run_drives_canonical_table_plot_and_report(tmp_path: Path) -> None:
    seed_binary_plan(tmp_path, effect_measure="OR")
    statistics = MetaStatisticsEngineService()
    run_result = statistics.run_statistics(tmp_path, actor="reviewer")
    adapter = MetaResultContractAdapter(statistics_service=statistics)

    contract = adapter.build_contract(tmp_path, run_result.analysis_run_id)
    table = adapter.export_result_table(tmp_path, run_result.analysis_run_id)
    plot = adapter.generate_forest_plot(tmp_path, run_result.analysis_run_id)
    report = adapter.export_report_artifact(tmp_path, run_result.analysis_run_id)
    refreshed = read_json(tmp_path / "analysis" / "meta_result_contracts" / run_result.analysis_run_id / "meta_result_contract.json")

    assert contract["schema_version"] == META_RESULT_CONTRACT_SCHEMA_VERSION
    assert refreshed["analysis_run_id"] == run_result.analysis_run_id
    assert refreshed["statistics_result_path"] == f"analysis/results/{run_result.analysis_run_id}_result.json"
    assert refreshed["statistics_result_hash"]
    assert refreshed["source_statistics_result_hash"] == refreshed["statistics_result_hash"]
    assert {item["artifact_type"] for item in refreshed["artifacts"]} == {
        "forest_plot",
        "report_export",
        "result_table",
    }

    for artifact in (table, plot, report):
        assert artifact["source_analysis_run_id"] == run_result.analysis_run_id
        assert artifact["source_statistics_result_hash"] == refreshed["statistics_result_hash"]
        assert artifact["testing_level"] is True
        assert artifact["production_grade"] is False
        assert artifact["medical_conclusion_status"] == "not_generated"
        assert (tmp_path / str(artifact["path"])).exists()

    table_text = (tmp_path / str(table["path"])).read_text(encoding="utf-8")
    report_text = (tmp_path / str(report["path"])).read_text(encoding="utf-8")
    assert run_result.analysis_run_id in table_text
    assert run_result.analysis_run_id in report_text
    assert "not production-grade" in report_text
    assert (tmp_path / str(plot["path"])).read_bytes().startswith(b"\x89PNG")


def test_current_meta_statistics_ui_state_discovers_canonical_contract(tmp_path: Path) -> None:
    seed_binary_plan(tmp_path, effect_measure="OR")
    statistics = MetaStatisticsEngineService()
    run_result = statistics.run_statistics(tmp_path, actor="reviewer")
    adapter = MetaResultContractAdapter(statistics_service=statistics)
    adapter.export_result_table(tmp_path, run_result.analysis_run_id)
    adapter.generate_forest_plot(tmp_path, run_result.analysis_run_id)
    adapter.export_report_artifact(tmp_path, run_result.analysis_run_id)

    state = meta_statistics_engine_state_from_project(tmp_path, service=statistics)

    assert state.latest_run_id == run_result.analysis_run_id
    assert state.canonical_contract_path.endswith("meta_result_contract.json")
    assert state.canonical_statistics_result_hash
    assert state.canonical_artifact_count == 3
    assert {item["artifact_type"] for item in state.canonical_artifacts} == {
        "forest_plot",
        "report_export",
        "result_table",
    }
    assert {item["source_analysis_run_id"] for item in state.canonical_artifacts} == {run_result.analysis_run_id}
