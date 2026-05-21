from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.analysis_inputs import resolve_analysis_inputs


def test_resolver_builds_standard_package_types_and_blocks_formal_gtex_control(tmp_path: Path) -> None:
    matrix = tmp_path / "expr.tsv"
    matrix.write_text("gene_id\tS1\tS2\nTP53\t1\t2\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nS1\tcase\nS2\tcontrol\n", encoding="utf-8")
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\tOS_event\nC1\t10\t1\n", encoding="utf-8")
    assets = [
        _asset("expr", "tcga_expression_matrix", "expression_repository", matrix, value_type="count", gene_id_type="symbol"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", tmp_path / "group.json"),
        _asset("clinical", "tcga_clinical_metadata", "clinical_repository", clinical),
        _asset("imported", "differential_result_table", "imported_result_repository", tmp_path / "deg.tsv"),
    ]
    _write_standardized_state(tmp_path, assets, default_expression="expr")

    result = resolve_analysis_inputs(tmp_path).to_dict()

    assert {package["package_type"] for package in result["packages"]} == {
        "deg_recompute",
        "deg_imported_result",
        "enrichment_from_deg",
        "gsea_preranked",
        "correlation_expression",
        "immune_score_linkage",
        "tcga_clinical_survival_preflight",
    }
    deg = next(package for package in result["packages"] if package["package_type"] == "deg_recompute")
    assert deg["input_package_id"].startswith("deg_recompute-")
    assert "deg_preflight" in deg["allowed_downstream_tasks"]
    imported = next(package for package in result["packages"] if package["package_type"] == "deg_imported_result")
    assert imported["task_semantics"] == "exploratory"
    assert any("external" in warning for warning in imported["warnings"])


def test_resolver_blocks_multiple_candidate_matrices_without_default(tmp_path: Path) -> None:
    assets = [
        _asset("expr-a", "raw_count_matrix", "expression_repository", tmp_path / "a.tsv", value_type="count", gene_id_type="symbol"),
        _asset("expr-b", "normalized_expression_matrix", "expression_repository", tmp_path / "b.tsv", value_type="TPM", gene_id_type="symbol"),
    ]
    _write_standardized_state(tmp_path, assets, default_expression="")

    result = resolve_analysis_inputs(tmp_path).to_dict()

    assert "multiple_candidate_matrices_without_default_selection" in result["blockers"]
    deg = next(package for package in result["packages"] if package["package_type"] == "deg_recompute")
    assert "multiple_candidate_matrices_without_default_selection" in deg["blockers"]


def test_resolver_blocks_geo_id_ref_without_platform_mapping(tmp_path: Path) -> None:
    matrix = tmp_path / "expr.tsv"
    matrix.write_text("ID_REF\tS1\tS2\n1007_s_at\t1\t2\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nS1\tcase\nS2\tcontrol\n", encoding="utf-8")
    feature = _asset("feature", "feature_annotation", "feature_annotation_repository", tmp_path / "feature.json", gene_id_type="ID_REF")
    feature["validation_status"] = "blocked"
    assets = [
        _asset("expr", "expression_matrix", "expression_repository", matrix, value_type="count", gene_id_type="ID_REF"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", tmp_path / "group.json"),
        feature,
    ]
    _write_standardized_state(tmp_path, assets, default_expression="expr")

    deg = next(package for package in resolve_analysis_inputs(tmp_path).to_dict()["packages"] if package["package_type"] == "deg_recompute")

    assert "geo_probe_or_id_ref_requires_platform_mapping" in deg["blockers"]


def _asset(asset_id: str, asset_type: str, repository: str, path: Path, *, value_type: str = "", gene_id_type: str = "symbol") -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_role": "expression_matrix" if "expression" in asset_type or "count" in asset_type else asset_type,
        "repository": repository,
        "path": str(path),
        "file_path": str(path),
        "validation_status": "passed",
        "analysis_ready": True,
        "expression_value_type": value_type,
        "gene_id_type": gene_id_type,
    }


def _write_standardized_state(root: Path, assets: list[dict[str, object]], *, default_expression: str) -> None:
    selection = {"expression": {"asset_id": default_expression, "selection_state": "user_confirmed"}}
    payload = {
        "schema_version": "biomedpilot.repository_manifest.v1",
        "assets": assets,
        "default_asset_selection": selection,
        "source_state": {"source_state_hash": "source-1"},
    }
    registry = {"schema_version": "biomedpilot.standardized_assets_registry.v2", "assets": assets, "default_asset_selection": selection}
    repo_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.write_text(json.dumps(payload), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
