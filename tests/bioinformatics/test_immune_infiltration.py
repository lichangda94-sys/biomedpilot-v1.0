from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.bioinformatics.comparison_config import ComparisonSampleAssignment, build_comparison_config_text, comparison_config_path
from app.bioinformatics.immune_infiltration import (
    build_immune_infiltration_readiness,
    build_linkage_preflight,
    generate_immune_tme_report,
    import_gmt_signatures,
    load_builtin_signatures,
    run_immune_scoring,
)
from app.bioinformatics.project_readiness import run_project_readiness


def test_builtin_and_gmt_signature_resources(tmp_path: Path) -> None:
    builtins = load_builtin_signatures()
    assert any(signature.signature_id == "cd8_t_cell" for signature in builtins)
    gmt = tmp_path / "custom.gmt"
    gmt.write_text("CUSTOM_ALPHA\tna\tCD3D\tCD8A\tGZMB\nCUSTOM_ALPHA\tna\tMS4A1\n", encoding="utf-8")
    imported = import_gmt_signatures(gmt)
    signatures = imported["signatures"]
    assert [signature["signature_id"] for signature in signatures] == ["custom_alpha", "custom_alpha_2"]
    assert signatures[0]["genes"] == ["CD3D", "CD8A", "GZMB"]


def test_readiness_allows_tpm_and_blocks_raw_counts(tmp_path: Path) -> None:
    matrix = _write_matrix(tmp_path / "expr.tsv")
    _write_standardized_registry(tmp_path, matrix, value_type="TPM", asset_type="normalized_expression_matrix")
    ready = build_immune_infiltration_readiness(tmp_path)
    assert ready["can_run_scoring"] is True
    assert ready["status"] in {"ready", "warning"}
    _write_standardized_registry(tmp_path, matrix, value_type="raw_counts", asset_type="raw_count_matrix")
    blocked = build_immune_infiltration_readiness(tmp_path)
    assert blocked["can_run_scoring"] is False
    assert any(str(item).startswith("value_type_blocked") for item in blocked["blockers"])


def test_project_readiness_exposes_immune_tme_scoring_row(tmp_path: Path) -> None:
    matrix = _write_matrix(tmp_path / "expr.tsv")
    _write_standardized_registry(tmp_path, matrix, value_type="TPM", asset_type="normalized_expression_matrix")
    result = run_project_readiness(tmp_path)
    rows = result["capability_matrix"]["rows"]
    immune_row = next(row for row in rows if row["analysis_type"] == "immune_tme_scoring")
    assert immune_row["can_run"] is True
    assert "探索性 immune / TME signature score" in " ".join(immune_row["warnings"])
    assert result["readiness_report"]["immune_infiltration_readiness"]["can_run_scoring"] is True


def test_scoring_outputs_manifest_receipt_and_result_index(tmp_path: Path) -> None:
    matrix = _write_matrix(tmp_path / "expr.tsv")
    signatures = [signature for signature in load_builtin_signatures() if signature.signature_id in {"cd8_t_cell", "pdcd1_checkpoint"}]
    result = run_immune_scoring(
        tmp_path,
        expression_matrix_path=matrix,
        selected_signatures=signatures,
        input_value_type="TPM",
        dataset_id="asset:test",
        dataset_label="Test TPM",
        scoring_method="mean_zscore",
    )
    assert Path(result.score_matrix_path).is_file()
    assert Path(result.coverage_path).is_file()
    assert Path(result.sample_summary_path).is_file()
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "biomedpilot.immune_tme_scoring_manifest.v1"
    assert manifest["scored_signature_count"] >= 1
    assert "KM/Cox/log-rank" in " ".join(manifest["blocked_downstream"])
    index = json.loads((tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8"))
    assert any(entry["analysis_type"] == "immune_tme_scoring" for entry in index["results"])


def test_scoring_blocks_unknown_or_raw_value_type(tmp_path: Path) -> None:
    matrix = _write_matrix(tmp_path / "expr.tsv")
    with pytest.raises(ValueError):
        run_immune_scoring(tmp_path, expression_matrix_path=matrix, selected_signatures=load_builtin_signatures()[:1], input_value_type="unknown")
    with pytest.raises(ValueError):
        run_immune_scoring(tmp_path, expression_matrix_path=matrix, selected_signatures=load_builtin_signatures()[:1], input_value_type="raw_counts")


def test_linkage_preflight_and_report_draft(tmp_path: Path) -> None:
    matrix = _write_matrix(tmp_path / "expr.tsv")
    signatures = [signature for signature in load_builtin_signatures() if signature.signature_id == "cd8_t_cell"]
    result = run_immune_scoring(tmp_path, expression_matrix_path=matrix, selected_signatures=signatures, input_value_type="TPM")
    comparison_config_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    comparison_config_path(tmp_path).write_text(
        build_comparison_config_text(
            comparison_id="test",
            group_column="group",
            case_group="tumor",
            control_group="normal",
            assignments=[
                ComparisonSampleAssignment("S1", "tumor"),
                ComparisonSampleAssignment("S2", "normal"),
                ComparisonSampleAssignment("S3", "normal"),
            ],
        ),
        encoding="utf-8",
    )
    preflight = build_linkage_preflight(tmp_path, score_matrix_path=result.score_matrix_path, expression_matrix_path=matrix, target_gene="CD8A")
    assert preflight["group_comparison"]["ready"] is True
    assert preflight["target_gene_correlation"]["ready"] is True
    assert "KM" in preflight["not_supported_in_b7"]
    report = generate_immune_tme_report(tmp_path, manifest_path=result.manifest_path, linkage_preflight=preflight)
    text = Path(report["report_path"]).read_text(encoding="utf-8")
    assert "Immune / TME Signature Scoring Report Draft" in text
    assert "does not run DEG, GSEA, KM, Cox, or log-rank" in text


def _write_matrix(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "gene_id\tS1\tS2\tS3",
                "CD3D\t10\t3\t4",
                "CD8A\t12\t2\t3",
                "GZMB\t15\t1\t2",
                "PRF1\t14\t2\t1",
                "PDCD1\t5\t0\t1",
                "MS4A1\t0\t7\t8",
                "NKG7\t11\t1\t2",
                "HLA-DRA\t9\t9\t8",
                "ACTB\t50\t51\t52",
                "GAPDH\t30\t31\t29",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def _write_standardized_registry(root: Path, matrix_path: Path, *, value_type: str, asset_type: str) -> None:
    path = root / "manifests" / "standardized_assets_registry.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.standardized_assets_registry.v2",
                "assets": [
                    {
                        "asset_id": "expr",
                        "label_zh": "Test expression",
                        "asset_type": asset_type,
                        "file_path": str(matrix_path),
                        "expression_value_type": value_type,
                        "gene_id_type": "symbol",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
