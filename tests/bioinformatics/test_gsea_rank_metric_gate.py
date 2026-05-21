from __future__ import annotations

from pathlib import Path

import pytest

from app.bioinformatics.gsea import build_gsea_rank_metric_gate


@pytest.mark.parametrize("metric", ["signed_log10_fdr_by_log2fc", "signed_log10_pvalue_by_log2fc", "log2_fold_change", "statistic"])
def test_valid_rank_metrics_pass(tmp_path: Path, metric: str) -> None:
    table = _write_table(tmp_path)

    gate = build_gsea_rank_metric_gate(tmp_path, source_result_id="deg", source_deg_table=table, source_gene_id_type="symbol", rank_metric=metric)

    assert gate["status"] == "passed"
    assert gate["ranked_gene_count"] == 12
    assert (tmp_path / gate["ranked_gene_list_path"]).is_file()


def test_custom_rank_column_passes_when_column_exists(tmp_path: Path) -> None:
    table = _write_table(tmp_path)

    gate = build_gsea_rank_metric_gate(tmp_path, source_result_id="deg", source_deg_table=table, source_gene_id_type="symbol", rank_metric="custom_rank_column", custom_rank_column="custom_score")

    assert gate["status"] == "passed"


def test_missing_rank_metric_column_blocks(tmp_path: Path) -> None:
    table = tmp_path / "deg.tsv"
    table.write_text("gene_symbol\tlog2_fold_change\nGENE1\t1\n", encoding="utf-8")

    gate = build_gsea_rank_metric_gate(tmp_path, source_result_id="deg", source_deg_table=table, source_gene_id_type="symbol", rank_metric="signed_log10_fdr_by_log2fc")

    assert "gsea_rank_metric_column_missing:adjusted_p_value" in gate["blockers"]


def test_all_zero_and_all_na_rank_block(tmp_path: Path) -> None:
    zero = tmp_path / "zero.tsv"
    zero.write_text("gene_symbol\tlog2_fold_change\n" + "\n".join(f"GENE{i}\t0" for i in range(12)) + "\n", encoding="utf-8")
    zero_gate = build_gsea_rank_metric_gate(tmp_path, source_result_id="zero", source_deg_table=zero, source_gene_id_type="symbol", rank_metric="log2_fold_change")
    assert "gsea_rank_metric_all_zero" in zero_gate["blockers"]

    na = tmp_path / "na.tsv"
    na.write_text("gene_symbol\tlog2_fold_change\n" + "\n".join(f"GENE{i}\tNA" for i in range(12)) + "\n", encoding="utf-8")
    na_gate = build_gsea_rank_metric_gate(tmp_path, source_result_id="na", source_deg_table=na, source_gene_id_type="symbol", rank_metric="log2_fold_change")
    assert any("gsea_rank_non_numeric_values" in item for item in na_gate["blockers"])


def test_duplicate_genes_are_handled_by_explicit_policy(tmp_path: Path) -> None:
    table = _write_table(tmp_path, duplicate=True)

    gate = build_gsea_rank_metric_gate(tmp_path, source_result_id="deg", source_deg_table=table, source_gene_id_type="symbol", rank_metric="log2_fold_change", duplicate_gene_policy="keep_max_abs_rank")
    failed = build_gsea_rank_metric_gate(tmp_path, source_result_id="deg", source_deg_table=table, source_gene_id_type="symbol", rank_metric="log2_fold_change", duplicate_gene_policy="fail")

    assert gate["status"] == "passed"
    assert "gsea_rank_duplicate_genes_handled:keep_max_abs_rank:1" in gate["warnings"]
    assert "gsea_rank_duplicate_genes_not_allowed" in failed["blockers"]


def test_unknown_gene_id_type_blocks(tmp_path: Path) -> None:
    table = _write_table(tmp_path)
    gate = build_gsea_rank_metric_gate(tmp_path, source_result_id="deg", source_deg_table=table, source_gene_id_type="unknown", rank_metric="log2_fold_change")
    assert "gsea_rank_gene_id_type_unknown_or_unmapped" in gate["blockers"]


def _write_table(root: Path, *, duplicate: bool = False) -> Path:
    table = root / "deg.tsv"
    rows = []
    for i in range(1, 13):
        gene = "GENE1" if duplicate and i == 2 else f"GENE{i}"
        feature = "g1" if duplicate and i == 2 else f"g{i}"
        rows.append(f"{feature}\t{gene}\t{(-1) ** i * (1 + i / 10):.2f}\t{2 + i / 10:.2f}\t{0.001 * i:.4f}\t{0.002 * i:.4f}\t{5 - i / 10:.2f}")
    table.write_text("feature_id\tgene_symbol\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tcustom_score\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return table
