from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.bioinformatics.gsea import run_controlled_preranked_gsea
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry
from app.bioinformatics.results.registry import load_registry


def test_formal_deg_valid_gmt_runs_preranked_gsea_and_registers_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_gsea_dependencies(monkeypatch)
    deg = _write_deg_table(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt")
    _write_result_index(tmp_path, [_formal_deg_entry(deg)])

    result = run_controlled_preranked_gsea(tmp_path, gene_set_resource_path=gmt, min_gene_set_size=2, max_gene_set_size=20, minimum_ranked_gene_count=10, permutation_count=25, dependency_snapshot=_passed_dependency())

    assert result["status"] == "passed"
    table = Path(str(result["result_table_path"]))
    assert table.is_file()
    text = table.read_text(encoding="utf-8")
    assert "p_value" in text
    assert "adjusted_p_value" in text
    registry = load_registry(tmp_path)
    entry = next(item for item in registry["results"] if item["result_id"] == result["result_id"])
    assert entry["task_type"] == "gsea_preranked"
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["source_result_semantics"] == "formal_computed_result"
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []
    assert entry["report_ready_eligible"] is False
    assert entry["parameters_manifest"]["permutation_count"] == 25
    assert Path(str(result["task_run_path"])).is_file()


def test_imported_deg_runs_as_imported_derived_gsea_with_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_gsea_dependencies(monkeypatch)
    deg = _write_deg_table(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt")
    entry = _formal_deg_entry(deg)
    entry["result_id"] = "imported-deg"
    entry["result_semantics"] = "imported_external_result"
    entry["parameters_manifest"] = {"gene_id_type": "symbol", "column_mapping_confirmed": True, "source_file": str(deg)}
    entry["source"] = "external_import"
    _write_result_index(tmp_path, [entry])

    result = run_controlled_preranked_gsea(tmp_path, gene_set_resource_path=gmt, min_gene_set_size=2, max_gene_set_size=20, permutation_count=10, dependency_snapshot=_passed_dependency())

    assert result["status"] == "passed"
    registered = next(item for item in load_registry(tmp_path)["results"] if item["result_id"] == result["result_id"])
    assert registered["result_semantics"] == "imported_external_result"
    assert registered["source_result_semantics"] == "imported_external_result"
    assert "imported_deg_derived_gsea_not_biomedpilot_recomputed_deg_formal_gsea" in registered["warnings"]


def test_missing_statsmodels_blocks_without_result_or_fake_fdr(tmp_path: Path) -> None:
    deg = _write_deg_table(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt")
    _write_result_index(tmp_path, [_formal_deg_entry(deg)])

    result = run_controlled_preranked_gsea(tmp_path, gene_set_resource_path=gmt, min_gene_set_size=2, max_gene_set_size=20, dependency_snapshot={"status": "blocked", "blockers": ["missing_python_package:statsmodels"]})

    assert result["status"] == "blocked_missing_dependency"
    assert "missing_python_package:statsmodels" in result["blockers"]
    assert not (tmp_path / "results" / "tables").exists()
    assert load_registry(tmp_path)["results"][0]["result_id"] == "formal-deg"


def test_raw_expression_testing_and_bad_rank_sources_are_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_gsea_dependencies(monkeypatch)
    deg = _write_deg_table(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt")
    raw = _formal_deg_entry(deg)
    raw["task_type"] = "expression_matrix"
    _write_result_index(tmp_path / "raw", [raw])
    assert "gsea_input_requires_deg_result:expression_matrix" in run_controlled_preranked_gsea(tmp_path / "raw", result_id="formal-deg", gene_set_resource_path=gmt, min_gene_set_size=2, max_gene_set_size=20, dependency_snapshot=_passed_dependency())["blockers"]

    testing = _formal_deg_entry(deg)
    testing["result_semantics"] = "testing_level"
    _write_result_index(tmp_path / "testing", [testing])
    assert "gsea_input_semantics_not_allowed:testing_level" in run_controlled_preranked_gsea(tmp_path / "testing", result_id="formal-deg", gene_set_resource_path=gmt, min_gene_set_size=2, max_gene_set_size=20, dependency_snapshot=_passed_dependency())["blockers"]

    _write_result_index(tmp_path, [_formal_deg_entry(deg)])
    bad_metric = run_controlled_preranked_gsea(tmp_path, gene_set_resource_path=gmt, rank_metric="not_a_metric", min_gene_set_size=2, max_gene_set_size=20, dependency_snapshot=_passed_dependency())
    assert "gsea_rank_metric_not_allowed:not_a_metric" in bad_metric["blockers"]


def _install_fake_gsea_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "numpy", types.ModuleType("numpy"))
    monkeypatch.setitem(sys.modules, "pandas", types.ModuleType("pandas"))
    monkeypatch.setitem(sys.modules, "scipy", types.ModuleType("scipy"))
    statsmodels = types.ModuleType("statsmodels")
    statsmodels_stats = types.ModuleType("statsmodels.stats")
    statsmodels_multitest = types.ModuleType("statsmodels.stats.multitest")

    def _multipletests(values: list[float], method: str = "fdr_bh") -> tuple[list[bool], list[float], float, float]:
        adjusted = [min(1.0, value * len(values)) for value in values]
        return [value <= 0.25 for value in adjusted], adjusted, 0.0, 0.0

    statsmodels_multitest.multipletests = _multipletests
    monkeypatch.setitem(sys.modules, "statsmodels", statsmodels)
    monkeypatch.setitem(sys.modules, "statsmodels.stats", statsmodels_stats)
    monkeypatch.setitem(sys.modules, "statsmodels.stats.multitest", statsmodels_multitest)


def _write_deg_table(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for index in range(1, 13):
        gene = f"GENE{index}"
        log2fc = 2.0 if index <= 6 else -1.5
        fdr = 0.001 * index if index <= 6 else 0.02 + index / 100
        rows.append(f"{gene}\t{gene}\t{log2fc}\t{fdr}\t0.01")
    table = root / "deg.tsv"
    table.write_text("feature_id\tgene_symbol\tlog2_fold_change\tadjusted_p_value\tp_value\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return table


def _write_gmt(path: Path) -> Path:
    path.write_text(
        "TERM_POS\tPositive genes\tGENE1\tGENE2\tGENE3\tGENE4\n"
        "TERM_NEG\tNegative genes\tGENE8\tGENE9\tGENE10\tGENE11\n",
        encoding="utf-8",
    )
    return path


def _formal_deg_entry(table: Path) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return ResultIndexEntry(
        result_id="formal-deg",
        task_run_id="run-1",
        task_type="deg",
        result_semantics="formal_computed_result",
        input_package_id="input-1",
        source_dataset_id="dataset-1",
        source_repository_manifest="standardized_data/repositories/repository_manifest.json",
        parameters_manifest={"gene_id_type": "symbol"},
        engine_name="python_scipy_statsmodels_deg_mvp",
        engine_version="0.1.0",
        dependency_snapshot={"status": "passed", "packages": {"scipy": {"available": True}, "statsmodels": {"available": True}}},
        output_artifacts=({"artifact_type": "deg_result_table", "path": str(table)},),
        validation_status="passed",
        log_artifacts=({"artifact_type": "task_run_log", "path": "logs/task.json"},),
        created_at=now,
        updated_at=now,
    ).to_dict()


def _write_result_index(root: Path, entries: list[dict[str, object]]) -> None:
    path = root / "results" / "summaries" / "result_index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": RESULT_INDEX_SCHEMA_VERSION, "results": entries}), encoding="utf-8")


def _passed_dependency() -> dict[str, object]:
    return {
        "status": "passed",
        "packages": {
            "numpy": {"available": True, "version": "fake-numpy"},
            "pandas": {"available": True, "version": "fake-pandas"},
            "scipy": {"available": True, "version": "fake-scipy"},
            "statsmodels": {"available": True, "version": "fake-statsmodels"},
        },
        "blockers": [],
        "install_action": "none_detect_first_only",
    }
