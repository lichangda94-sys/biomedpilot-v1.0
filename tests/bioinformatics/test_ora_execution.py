from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.bioinformatics.enrichment.executor import run_controlled_ora
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry
from app.bioinformatics.results.registry import load_registry


def test_formal_deg_valid_gmt_runs_ora_and_registers_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_ora_dependencies(monkeypatch)
    deg = _write_deg_table(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt")
    _write_result_index(tmp_path, [_formal_deg_entry(deg)])

    result = run_controlled_ora(tmp_path, gene_set_resource_path=gmt, dependency_snapshot=_passed_dependency())

    assert result["status"] == "passed"
    table = Path(str(result["result_table_path"]))
    assert table.is_file()
    text = table.read_text(encoding="utf-8")
    assert "p_value" in text
    assert "adjusted_p_value" in text
    registry = load_registry(tmp_path)
    entry = next(item for item in registry["results"] if item["result_id"] == result["result_id"])
    assert entry["task_type"] == "ora_enrichment"
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["source_result_semantics"] == "formal_computed_result"
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []
    assert entry["report_ready_eligible"] is False
    assert Path(str(result["task_run_path"])).is_file()


def test_imported_deg_runs_as_imported_derived_ora_with_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_ora_dependencies(monkeypatch)
    deg = _write_deg_table(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt")
    entry = _formal_deg_entry(deg)
    entry["result_id"] = "imported-deg"
    entry["result_semantics"] = "imported_external_result"
    entry["parameters_manifest"] = {"column_mapping_confirmed": True, "column_mapping": {"gene": "gene_symbol"}, "source_file": str(deg)}
    entry["source"] = "external_import"
    _write_result_index(tmp_path, [entry])

    result = run_controlled_ora(tmp_path, gene_set_resource_path=gmt, dependency_snapshot=_passed_dependency())

    assert result["status"] == "passed"
    registered = next(item for item in load_registry(tmp_path)["results"] if item["result_id"] == result["result_id"])
    assert registered["result_semantics"] == "imported_external_result"
    assert registered["source_result_semantics"] == "imported_external_result"
    assert "imported_deg_derived_ora_not_biomedpilot_recomputed_deg_formal_ora" in registered["warnings"]


def test_missing_stats_dependencies_block_without_result_or_pvalues(tmp_path: Path) -> None:
    deg = _write_deg_table(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt")
    _write_result_index(tmp_path, [_formal_deg_entry(deg)])

    result = run_controlled_ora(tmp_path, gene_set_resource_path=gmt, dependency_snapshot={"status": "blocked", "blockers": ["missing_python_package:statsmodels"]})

    assert result["status"] == "blocked_missing_dependency"
    assert "missing_python_package:statsmodels" in result["blockers"]
    assert not (tmp_path / "results" / "tables").exists()
    assert load_registry(tmp_path)["results"][0]["result_id"] == "formal-deg"
    assert Path(str(result["task_run_path"])).is_file()


def test_invalid_gene_set_and_empty_selected_gene_list_are_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_ora_dependencies(monkeypatch)
    deg = _write_deg_table(tmp_path, selected=False)
    bad_gmt = tmp_path / "bad.gmt"
    bad_gmt.write_text("bad\tdesc\n", encoding="utf-8")
    _write_result_index(tmp_path, [_formal_deg_entry(deg)])

    invalid = run_controlled_ora(tmp_path, gene_set_resource_path=bad_gmt, dependency_snapshot=_passed_dependency())
    assert invalid["status"] == "blocked"
    assert any("gmt:" in item or "ora_gene_set" in item for item in invalid["blockers"])

    valid_gmt = _write_gmt(tmp_path / "sets.gmt")
    empty = run_controlled_ora(tmp_path, gene_set_resource_path=valid_gmt, dependency_snapshot=_passed_dependency())
    assert empty["status"] == "blocked"
    assert "ora_selected_gene_list_empty" in empty["blockers"]


def test_no_overlap_produces_valid_table_with_warning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_ora_dependencies(monkeypatch)
    deg = _write_deg_table(tmp_path)
    gmt = tmp_path / "no_overlap.gmt"
    gmt.write_text("TERM_X\tNo overlap\tZZZ1\tZZZ2\n", encoding="utf-8")
    _write_result_index(tmp_path, [_formal_deg_entry(deg)])

    result = run_controlled_ora(tmp_path, gene_set_resource_path=gmt, dependency_snapshot=_passed_dependency())

    assert result["status"] == "passed"
    assert "ora_no_gene_sets_tested_after_size_filter" in result["warnings"]


def test_raw_expression_and_testing_sources_are_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_ora_dependencies(monkeypatch)
    deg = _write_deg_table(tmp_path)
    gmt = _write_gmt(tmp_path / "sets.gmt")
    raw = _formal_deg_entry(deg)
    raw["task_type"] = "expression_matrix"
    _write_result_index(tmp_path / "raw", [raw])
    assert "ora_input_requires_deg_result:expression_matrix" in run_controlled_ora(tmp_path / "raw", gene_set_resource_path=gmt, dependency_snapshot=_passed_dependency())["blockers"]

    testing = _formal_deg_entry(deg)
    testing["result_semantics"] = "testing_level"
    _write_result_index(tmp_path / "testing", [testing])
    assert "ora_input_semantics_not_allowed:testing_level" in run_controlled_ora(tmp_path / "testing", gene_set_resource_path=gmt, dependency_snapshot=_passed_dependency())["blockers"]


def _install_fake_ora_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    scipy = types.ModuleType("scipy")
    scipy_stats = types.ModuleType("scipy.stats")

    class _Hypergeom:
        @staticmethod
        def sf(k: int, _population: int, _success: int, _draws: int) -> float:
            return 0.01 if k >= 0 else 1.0

    def _fisher_exact(_table: object, alternative: str = "greater") -> object:
        return types.SimpleNamespace(pvalue=0.02 if alternative == "greater" else 1.0)

    scipy_stats.hypergeom = _Hypergeom()
    scipy_stats.fisher_exact = _fisher_exact
    statsmodels = types.ModuleType("statsmodels")
    statsmodels_stats = types.ModuleType("statsmodels.stats")
    statsmodels_multitest = types.ModuleType("statsmodels.stats.multitest")

    def _multipletests(values: list[float], method: str = "fdr_bh") -> tuple[list[bool], list[float], float, float]:
        adjusted = [min(1.0, value * len(values)) for value in values]
        return [value <= 0.05 for value in adjusted], adjusted, 0.0, 0.0

    statsmodels_multitest.multipletests = _multipletests
    monkeypatch.setitem(sys.modules, "scipy", scipy)
    monkeypatch.setitem(sys.modules, "scipy.stats", scipy_stats)
    monkeypatch.setitem(sys.modules, "statsmodels", statsmodels)
    monkeypatch.setitem(sys.modules, "statsmodels.stats", statsmodels_stats)
    monkeypatch.setitem(sys.modules, "statsmodels.stats.multitest", statsmodels_multitest)


def _write_deg_table(root: Path, *, selected: bool = True) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    rows = [
        "ENSG1\tTP53\t1.5\t0.01\tupregulated" if selected else "ENSG1\tTP53\t0.2\t0.9\tnot_significant",
        "ENSG2\tBRCA1\t-1.4\t0.02\tdownregulated" if selected else "ENSG2\tBRCA1\t0.1\t0.8\tnot_significant",
        "ENSG3\tEGFR\t0.1\t0.8\tnot_significant",
    ]
    table = root / "deg.tsv"
    table.write_text("feature_id\tgene_symbol\tlog2_fold_change\tadjusted_p_value\tsignificance_label\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return table


def _write_gmt(path: Path) -> Path:
    path.write_text("TERM_A\tApoptosis\tTP53\tBRCA1\nTERM_B\tGrowth\tEGFR\n", encoding="utf-8")
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
            "scipy": {"available": True, "version": "fake-scipy"},
            "statsmodels": {"available": True, "version": "fake-statsmodels"},
        },
        "blockers": [],
        "install_action": "none_detect_first_only",
    }
