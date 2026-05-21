from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_ready import build_deg_ready_package


def test_deg_ready_builder_passes_gene_symbol_matrix_with_aligned_groups(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tS1\tS2\nTP53\t10\t5\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nS1\tcase\nS2\tcontrol\n", encoding="utf-8")
    package = _package(matrix, sample, value_type="count", gene_id_type="symbol")

    ready = build_deg_ready_package(package).to_dict()

    assert ready["sample_alignment_status"]["status"] == "passed"
    assert ready["gene_mapping_status"]["status"] == "passed"
    assert "count_model_preflight" in ready["allowed_deg_methods"]


def test_deg_ready_builder_blocks_imported_deg_and_duplicate_samples(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tS1\tS1\nTP53\t10\t5\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nS1\tcase\n", encoding="utf-8")
    package = _package(matrix, sample, package_type="deg_imported_result")

    ready = build_deg_ready_package(package).to_dict()

    assert "input_package_is_not_deg_recompute" in ready["blockers"]
    assert "duplicate_expression_sample_ids" in ready["blockers"]


def _package(matrix: Path, sample: Path, *, package_type: str = "deg_recompute", value_type: str = "count", gene_id_type: str = "symbol") -> dict[str, object]:
    return {
        "input_package_id": "pkg-1",
        "package_type": package_type,
        "value_type": value_type,
        "gene_id_type": gene_id_type,
        "expression_asset": {"asset_id": "expr", "path": str(matrix), "asset_type": "raw_count_matrix"},
        "sample_metadata_asset": {"asset_id": "sample", "path": str(sample), "asset_type": "sample_metadata"},
        "group_design_asset": {"asset_id": "group", "asset_type": "group_design"},
        "feature_annotation_asset": {"asset_id": "feature", "validation_status": "passed", "asset_type": "feature_annotation"},
        "blockers": [],
        "warnings": [],
    }
