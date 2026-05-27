from __future__ import annotations

from pathlib import Path

from app.bioinformatics.deg_engine import build_deg_input_adaptation_gate
from app.bioinformatics.deg_ready import build_deg_ready_package


def test_input_adaptation_passes_raw_count_gene_level_package(tmp_path: Path) -> None:
    package = _package(tmp_path, value_type="count", gene_id_type="symbol")
    ready = build_deg_ready_package(package).to_dict()

    gate = build_deg_input_adaptation_gate(package, ready)

    assert gate["status"] == "passed"
    assert gate["value_type"] == "count"
    assert "deseq2" in gate["allowed_methods"]
    assert "edger" in gate["allowed_methods"]
    assert not gate["blockers"]


def test_input_adaptation_blocks_display_value_for_count_model(tmp_path: Path) -> None:
    package = _package(tmp_path, value_type="TPM", gene_id_type="symbol")
    ready = build_deg_ready_package(package).to_dict()

    gate = build_deg_input_adaptation_gate(package, ready, requested_method_family="deseq2")

    assert gate["status"] == "blocked"
    assert "tpm_fpkm_or_log_expression_not_allowed_for_count_model_deg" in gate["blockers"]
    assert "display_value_type_requires_non_count_model_method" in gate["warnings"]


def test_input_adaptation_blocks_geo_probe_without_mapping(tmp_path: Path) -> None:
    package = _package(tmp_path, value_type="TPM", gene_id_type="ID_REF", feature_validation="blocked")
    ready = build_deg_ready_package(package).to_dict()

    gate = build_deg_input_adaptation_gate(package, ready)

    assert gate["status"] == "blocked"
    assert "geo_probe_or_id_ref_requires_platform_mapping" in gate["blockers"]
    assert any("platform probe-to-gene mapping" in item for item in gate["repair_guidance"])


def test_input_adaptation_blocks_missing_package() -> None:
    gate = build_deg_input_adaptation_gate(None, None)

    assert gate["status"] == "blocked"
    assert "missing_deg_recompute_input_package" in gate["blockers"]


def _package(tmp_path: Path, *, value_type: str, gene_id_type: str, feature_validation: str = "passed") -> dict[str, object]:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tS1\tS2\nTP53\t10\t5\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nS1\tcase\nS2\tcontrol\n", encoding="utf-8")
    return {
        "input_package_id": "pkg-1",
        "package_type": "deg_recompute",
        "value_type": value_type,
        "gene_id_type": gene_id_type,
        "expression_asset": {"asset_id": "expr", "path": str(matrix), "asset_type": "raw_count_matrix"},
        "sample_metadata_asset": {"asset_id": "sample", "path": str(sample), "asset_type": "sample_metadata"},
        "group_design_asset": {"asset_id": "group", "asset_type": "group_design"},
        "feature_annotation_asset": {"asset_id": "feature", "validation_status": feature_validation, "asset_type": "feature_annotation"},
        "blockers": [],
        "warnings": [],
    }
