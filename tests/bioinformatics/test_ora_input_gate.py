from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.enrichment.input_gate import build_ora_input_gate
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry


def test_formal_deg_result_builds_ora_input_package(tmp_path: Path) -> None:
    table = _write_deg_table(tmp_path)
    _write_result_index(tmp_path, [_formal_deg_entry(table)])

    gate = build_ora_input_gate(tmp_path)

    assert gate["status"] == "passed"
    assert gate["source"] == "formal_deg"
    assert gate["source_result_semantics"] == "formal_computed_result"
    assert gate["source_task_type"] == "deg"
    assert gate["gene_list_count"] == 2
    assert gate["background_universe_count"] == 3
    assert gate["blockers"] == []


def test_imported_deg_result_passes_with_imported_warning(tmp_path: Path) -> None:
    table = _write_deg_table(tmp_path)
    entry = _formal_deg_entry(table)
    entry["result_id"] = "imported-deg"
    entry["result_semantics"] = "imported_external_result"
    entry["parameters_manifest"] = {"column_mapping_confirmed": True, "column_mapping": {"gene": "gene_symbol"}, "source_file": str(table)}
    entry["source"] = "external_import"
    _write_result_index(tmp_path, [entry])

    gate = build_ora_input_gate(tmp_path)

    assert gate["status"] == "passed"
    assert gate["source"] == "imported_deg"
    assert "imported_deg_source_is_external_not_biomedpilot_recomputed" in gate["warnings"]


def test_testing_preflight_and_dry_run_deg_results_are_blocked(tmp_path: Path) -> None:
    table = _write_deg_table(tmp_path)
    for semantics in ("testing_level", "preflight_only", "configured_not_run", "exploratory"):
        project = tmp_path / semantics
        project.mkdir()
        local_table = project / "deg.tsv"
        local_table.write_text(table.read_text(encoding="utf-8"), encoding="utf-8")
        entry = _formal_deg_entry(local_table)
        entry["result_id"] = semantics
        entry["result_semantics"] = semantics
        _write_result_index(project, [entry])

        gate = build_ora_input_gate(project)

        assert gate["status"] == "blocked"
        assert f"ora_input_semantics_not_allowed:{semantics}" in gate["blockers"]


def test_raw_expression_result_is_blocked_as_ora_source(tmp_path: Path) -> None:
    table = _write_deg_table(tmp_path)
    entry = _formal_deg_entry(table)
    entry["task_type"] = "expression_matrix"
    _write_result_index(tmp_path, [entry])

    gate = build_ora_input_gate(tmp_path)

    assert gate["status"] == "blocked"
    assert "ora_input_requires_deg_result:expression_matrix" in gate["blockers"]


def test_missing_deg_table_and_invalid_columns_are_blocked(tmp_path: Path) -> None:
    missing_entry = _formal_deg_entry(tmp_path / "missing.tsv")
    _write_result_index(tmp_path / "missing", [missing_entry])
    missing_gate = build_ora_input_gate(tmp_path / "missing")
    assert "ora_source_deg_table_file_missing" in missing_gate["blockers"]

    invalid_project = tmp_path / "invalid"
    invalid_project.mkdir()
    invalid_table = invalid_project / "deg.tsv"
    invalid_table.write_text("gene\tp_value\nTP53\t0.01\n", encoding="utf-8")
    _write_result_index(invalid_project, [_formal_deg_entry(invalid_table)])

    gate = build_ora_input_gate(invalid_project)

    assert gate["status"] == "blocked"
    assert "ora_source_deg_table_missing_adjusted_p_value" in gate["blockers"]
    assert "ora_source_deg_table_missing_log2fc" in gate["blockers"]


def _write_deg_table(root: Path) -> Path:
    table = root / "deg.tsv"
    table.write_text(
        "\t".join(["feature_id", "gene_symbol", "log2_fold_change", "adjusted_p_value", "significance_label"]) + "\n"
        "ENSG1\tTP53\t1.5\t0.01\tupregulated\n"
        "ENSG2\tBRCA1\t-1.4\t0.02\tdownregulated\n"
        "ENSG3\tEGFR\t0.1\t0.8\tnot_significant\n",
        encoding="utf-8",
    )
    return table


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
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=(),
        blockers=(),
        log_artifacts=({"artifact_type": "task_run_log", "path": "logs/task.json"},),
        created_at=now,
        updated_at=now,
    ).to_dict()


def _write_result_index(root: Path, entries: list[dict[str, object]]) -> None:
    path = root / "results" / "summaries" / "result_index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": RESULT_INDEX_SCHEMA_VERSION, "results": entries}), encoding="utf-8")
