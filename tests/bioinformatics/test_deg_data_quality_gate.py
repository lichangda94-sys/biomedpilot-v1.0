from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_engine import build_deg_data_quality_gate


def test_data_quality_passes_clean_matrix(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tS1\tS2\nTP53\t10\t5\nBRCA1\t20\t30\n", encoding="utf-8")

    gate = build_deg_data_quality_gate(_ready(matrix))

    assert gate["status"] == "passed"
    assert gate["feature_count"] == 2
    assert not gate["blockers"]


def test_data_quality_blocks_duplicate_gene_without_policy(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tS1\tS2\nTP53\t10\t5\nTP53\t20\t30\n", encoding="utf-8")

    gate = build_deg_data_quality_gate(_ready(matrix))

    assert gate["status"] == "blocked"
    assert "duplicated_gene_id_without_aggregation_policy" in gate["blockers"]
    assert gate["auto_repaired"] is False


def test_data_quality_blocks_non_numeric_missing_and_negative_counts(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tS1\tS2\nTP53\t-1\t5\nBRCA1\tNA\t\n", encoding="utf-8")

    gate = build_deg_data_quality_gate(_ready(matrix, value_type="count"))

    assert "negative_counts_block_count_model" in gate["blockers"]
    assert "non_numeric_expression_values" in gate["blockers"]
    assert "missing_values_in_expression_matrix" in gate["blockers"]


def test_data_quality_warns_all_zero_low_count_mixed_ids(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tS1\tS2\nTP53\t0\t0\nENSG000001\t1\t1\n", encoding="utf-8")

    gate = build_deg_data_quality_gate(_ready(matrix))

    assert gate["status"] == "passed"
    assert "all_zero_features_present" in gate["warnings"]
    assert "low_count_features_present" in gate["warnings"]
    assert "zero_variance_features_present" in gate["warnings"]
    assert "mixed_feature_identifier_patterns_present" in gate["warnings"]


def _ready(matrix: Path, *, value_type: str = "count") -> dict[str, object]:
    return {
        "source_input_package_id": "pkg-1",
        "deg_ready_package_id": "ready-1",
        "value_type": value_type,
        "matrix_asset": {"asset_id": "expr", "path": str(matrix)},
        "blockers": [],
        "warnings": [],
    }
