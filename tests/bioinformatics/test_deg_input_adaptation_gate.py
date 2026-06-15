from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_engine.input_adaptation import build_deg_input_adaptation_gate
from app.bioinformatics.deg_ready import build_deg_ready_package


def test_deg_input_adaptation_allows_tcga_like_raw_counts(tmp_path: Path) -> None:
    matrix = tmp_path / "counts.tsv"
    matrix.write_text("gene\tcase_1\tcase_2\tcontrol_1\tcontrol_2\nTP53\t20\t21\t5\t4\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\ncase_1\tcase\ncase_2\tcase\ncontrol_1\tcontrol\ncontrol_2\tcontrol\n", encoding="utf-8")
    package = _package(matrix, sample, value_type="raw_counts", gene_id_type="ensembl")
    ready = build_deg_ready_package(package).to_dict()

    gate = build_deg_input_adaptation_gate(package, ready)

    assert gate["status"] == "passed"
    assert gate["value_type"] == "raw_counts"
    assert "deseq2" in gate["allowed_methods"]
    assert "edger" in gate["allowed_methods"]
    assert gate["sample_alignment_status"] == "passed"


def test_deg_input_adaptation_blocks_geo_id_ref_without_mapping(tmp_path: Path) -> None:
    matrix = tmp_path / "geo.tsv"
    matrix.write_text("ID_REF\tS1\tS2\n1007_s_at\t1.5\t2.2\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nS1\tcase\nS2\tcontrol\n", encoding="utf-8")
    package = _package(matrix, sample, value_type="TPM", gene_id_type="ID_REF", feature_status="blocked")
    ready = build_deg_ready_package(package).to_dict()

    gate = build_deg_input_adaptation_gate(package, ready, requested_method_family="deseq2")

    assert gate["status"] == "blocked"
    assert "geo_probe_or_id_ref_requires_platform_mapping" in gate["blockers"]
    assert "tpm_fpkm_or_log_expression_not_allowed_for_count_model_deg" in gate["blockers"]
    assert "Attach validated platform probe-to-gene mapping before formal DEG." in gate["repair_guidance"]


def test_deg_input_adaptation_blocks_sample_group_mismatch(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tS1\tS2\nTP53\t10\t5\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nX1\tcase\nX2\tcontrol\n", encoding="utf-8")
    package = _package(matrix, sample, value_type="count", gene_id_type="symbol")
    ready = build_deg_ready_package(package).to_dict()

    gate = build_deg_input_adaptation_gate(package, ready)

    assert gate["status"] == "blocked"
    assert "expression_and_metadata_samples_do_not_overlap" in gate["blockers"]
    assert "Repair sample/group alignment before DEG." in gate["repair_guidance"]


def _package(matrix: Path, sample: Path, *, value_type: str, gene_id_type: str, feature_status: str = "passed") -> dict[str, object]:
    return {
        "input_package_id": "pkg-real",
        "package_type": "deg_recompute",
        "value_type": value_type,
        "gene_id_type": gene_id_type,
        "expression_asset": {"asset_id": "expr", "path": str(matrix), "asset_type": "expression_matrix"},
        "sample_metadata_asset": {"asset_id": "sample", "path": str(sample), "asset_type": "sample_metadata"},
        "group_design_asset": {"asset_id": "group", "asset_type": "group_design"},
        "feature_annotation_asset": {"asset_id": "feature", "asset_type": "feature_annotation", "validation_status": feature_status},
        "blockers": [],
        "warnings": [],
    }
