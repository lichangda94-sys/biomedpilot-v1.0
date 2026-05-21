from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.bioinformatics.gsea import build_gsea_preranked_input_gate
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry


def test_formal_deg_result_builds_gsea_preranked_input(tmp_path: Path) -> None:
    table = _write_deg_table(tmp_path)
    _write_result_index(tmp_path, [_deg_entry(table)])

    gate = build_gsea_preranked_input_gate(tmp_path, result_id="deg-formal")

    assert gate["status"] == "passed"
    assert gate["source_result_semantics"] == "formal_computed_result"
    assert gate["source_task_type"] == "deg"
    assert gate["rank_metric"] == "signed_log10_fdr_by_log2fc"
    assert gate["ranked_gene_count"] == 12
    assert (tmp_path / gate["ranked_gene_list_path"]).is_file()
    assert gate["allowed_downstream_tasks"] == ["gsea_preranked_preflight"]


def test_imported_deg_result_builds_gsea_input_with_imported_warning(tmp_path: Path) -> None:
    table = _write_deg_table(tmp_path)
    entry = _deg_entry(table, result_id="deg-imported", semantics="imported_external_result")
    entry["parameters_manifest"] = {"gene_id_type": "symbol", "column_mapping_confirmed": True, "source_file": str(table)}
    entry["source"] = "external_import"
    _write_result_index(tmp_path, [entry])

    gate = build_gsea_preranked_input_gate(tmp_path, result_id="deg-imported")

    assert gate["status"] == "passed"
    assert gate["source_result_semantics"] == "imported_external_result"
    assert "imported_deg_gsea_preranked_input_requires_external_provenance_label" in gate["warnings"]


@pytest.mark.parametrize("semantics", ["testing_level", "exploratory", "preflight_only"])
def test_gsea_input_blocks_non_formal_non_imported_deg(tmp_path: Path, semantics: str) -> None:
    table = _write_deg_table(tmp_path)
    _write_result_index(tmp_path, [_deg_entry(table, semantics=semantics)])

    gate = build_gsea_preranked_input_gate(tmp_path, result_id="deg-formal")

    assert gate["status"] == "blocked"
    assert f"gsea_input_semantics_not_allowed:{semantics}" in gate["blockers"]


def test_gsea_input_blocks_raw_expression_and_ora_result(tmp_path: Path) -> None:
    table = _write_deg_table(tmp_path)
    raw = _deg_entry(table, result_id="raw", task_type="expression_matrix")
    ora = _deg_entry(table, result_id="ora", task_type="ora_enrichment")
    _write_result_index(tmp_path, [raw, ora])

    raw_gate = build_gsea_preranked_input_gate(tmp_path, result_id="raw")
    ora_gate = build_gsea_preranked_input_gate(tmp_path, result_id="ora")

    assert "gsea_input_requires_deg_result:expression_matrix" in raw_gate["blockers"]
    assert "gsea_input_requires_deg_result:ora_enrichment" in ora_gate["blockers"]


def test_imported_deg_requires_mapping_and_source_provenance(tmp_path: Path) -> None:
    table = _write_deg_table(tmp_path)
    _write_result_index(tmp_path, [_deg_entry(table, semantics="imported_external_result")])

    gate = build_gsea_preranked_input_gate(tmp_path, result_id="deg-formal")

    assert "gsea_imported_deg_column_mapping_not_confirmed" in gate["blockers"]
    assert "gsea_imported_deg_source_provenance_missing" in gate["blockers"]


def _write_deg_table(root: Path) -> Path:
    path = root / "deg.tsv"
    rows = [
        f"g{i}\tGENE{i}\t{(-1) ** i * (1 + i / 10):.2f}\t{2 + i / 10:.2f}\t{0.001 * i:.4f}\t{0.002 * i:.4f}\tup\t"
        for i in range(1, 13)
    ]
    path.write_text("feature_id\tgene_symbol\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tsignificance_label\twarnings\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def _deg_entry(table: Path, *, result_id: str = "deg-formal", semantics: str = "formal_computed_result", task_type: str = "deg") -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return ResultIndexEntry(
        result_id=result_id,
        task_run_id=f"{result_id}-run",
        task_type=task_type,
        result_semantics=semantics,
        input_package_id="input-1",
        parameters_manifest={"gene_id_type": "symbol"},
        dependency_snapshot={"status": "passed"},
        output_artifacts=({"artifact_type": "deg_result_table", "path": str(table)},),
        validation_status="passed",
        created_at=now,
        updated_at=now,
    ).to_dict()


def _write_result_index(root: Path, entries: list[dict[str, object]]) -> None:
    path = root / "results" / "summaries" / "result_index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": RESULT_INDEX_SCHEMA_VERSION, "results": entries}), encoding="utf-8")
