import json
from pathlib import Path

from app.bioinformatics.acquisition_adapters import (
    adapt_geo_detection_manifest,
    adapt_gtex_preview_manifest,
    apply_legacy_asset_selection_to_repository_manifest,
    build_legacy_asset_selection_manifest,
    materialize_legacy_standardized_asset_candidates,
    merge_legacy_materialized_assets_into_repository_manifest,
    validate_legacy_asset_selection_manifest,
    write_legacy_acquisition_manifest,
    write_legacy_standardized_asset_candidates,
)
from app.bioinformatics.analysis_inputs import resolve_analysis_inputs


def _write_source(path: Path, text: str = "gene_symbol\ts1\ts2\nTP53\t1\t2\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _prepare_merged_geo_assets(tmp_path: Path) -> dict[str, object]:
    expression_a = _write_source(tmp_path / "inputs" / "gene_symbol_counts_a.tsv")
    expression_b = _write_source(tmp_path / "inputs" / "gene_symbol_counts_b.tsv")
    sample = _write_source(tmp_path / "inputs" / "sample_metadata.tsv", "sample_id\tgroup\ns1\tcase\ns2\tcontrol\n")
    manifest = adapt_geo_detection_manifest(
        accession="GSE_SELECT",
        scan_root=tmp_path,
        detection_result={
            "accession_type": "GSE",
            "has_expression_payload": True,
            "matrix_level": "gene",
            "candidate_expression_files": [str(expression_a), str(expression_b)],
            "candidate_metadata_files": [str(sample)],
        },
    )
    write_legacy_acquisition_manifest(tmp_path, manifest)
    write_legacy_standardized_asset_candidates(tmp_path)
    materialize_legacy_standardized_asset_candidates(tmp_path)
    return merge_legacy_materialized_assets_into_repository_manifest(tmp_path)


def _assets_by_role(merge: dict[str, object], role: str) -> list[dict[str, object]]:
    return [asset for asset in merge["merged_assets"] if isinstance(asset, dict) and asset.get("asset_role") == role]  # type: ignore[index]


def test_selection_updates_repository_default_but_keeps_formal_analysis_blocked(tmp_path: Path) -> None:
    merge = _prepare_merged_geo_assets(tmp_path)
    expression_assets = _assets_by_role(merge, "expression_matrix")
    sample_assets = _assets_by_role(merge, "sample_metadata")
    assert len(expression_assets) == 2

    before = resolve_analysis_inputs(tmp_path).to_dict()
    before_deg = next(package for package in before["packages"] if package["package_type"] == "deg_recompute")
    assert "multiple_candidate_matrices_without_default_selection" in before_deg["blockers"]

    selection = build_legacy_asset_selection_manifest(
        tmp_path,
        expression_asset_id=str(expression_assets[0]["asset_id"]),
        sample_metadata_asset_id=str(sample_assets[0]["asset_id"]),
        confirmed_by_user=True,
    )
    result = apply_legacy_asset_selection_to_repository_manifest(tmp_path, selection)

    assert result["status"] == "selection_recorded_preflight_only"
    assert result["repository_manifest_updated"] is True
    assert "missing_group_design_selection" in result["validation"]["downstream_blockers"]
    repository_manifest = json.loads((tmp_path / "standardized_data/repositories/repository_manifest.json").read_text(encoding="utf-8"))
    assert repository_manifest["default_asset_selection"]["expression"]["asset_id"] == expression_assets[0]["asset_id"]
    assert repository_manifest["default_asset_selection"]["sample_metadata"]["asset_id"] == sample_assets[0]["asset_id"]
    assert not (tmp_path / "standardized_data/repositories/analysis_input_repository").exists()
    assert not (tmp_path / "results/summaries/result_index.json").exists()

    after = resolve_analysis_inputs(tmp_path).to_dict()
    after_deg = next(package for package in after["packages"] if package["package_type"] == "deg_recompute")
    assert "multiple_candidate_matrices_without_default_selection" not in after_deg["blockers"]
    assert "missing_group_design_asset" in after_deg["blockers"]
    assert after_deg["expression_asset"]["asset_id"] == expression_assets[0]["asset_id"]


def test_selection_requires_user_confirmation_and_does_not_update_repository(tmp_path: Path) -> None:
    merge = _prepare_merged_geo_assets(tmp_path)
    expression = _assets_by_role(merge, "expression_matrix")[0]
    selection = build_legacy_asset_selection_manifest(tmp_path, expression_asset_id=str(expression["asset_id"]), confirmed_by_user=False)

    result = apply_legacy_asset_selection_to_repository_manifest(tmp_path, selection)

    assert result["status"] == "blocked"
    assert result["repository_manifest_updated"] is False
    assert "legacy_asset_selection_requires_user_confirmation" in result["validation"]["selection_blockers"]
    repository_manifest = json.loads((tmp_path / "standardized_data/repositories/repository_manifest.json").read_text(encoding="utf-8"))
    assert repository_manifest.get("default_asset_selection", {}) == {}


def test_selection_validation_blocks_formalish_asset(tmp_path: Path) -> None:
    merge = _prepare_merged_geo_assets(tmp_path)
    expression = _assets_by_role(merge, "expression_matrix")[0]
    repository_path = tmp_path / "standardized_data/repositories/repository_manifest.json"
    repository_manifest = json.loads(repository_path.read_text(encoding="utf-8"))
    for asset in repository_manifest["assets"]:
        if asset["asset_id"] == expression["asset_id"]:
            asset["formal_analysis_ready"] = True
            asset["result_semantics"] = "formal_computed_result"
    repository_path.write_text(json.dumps(repository_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    selection = build_legacy_asset_selection_manifest(tmp_path, expression_asset_id=str(expression["asset_id"]), confirmed_by_user=True)
    validation = validate_legacy_asset_selection_manifest(selection)

    assert validation["status"] == "blocked"
    assert "expression_selection_formalish_asset_forbidden" in validation["selection_blockers"]


def test_gtex_selection_is_recorded_but_resolver_keeps_normal_control_blockers(tmp_path: Path) -> None:
    gtex = adapt_gtex_preview_manifest(
        preview_summary={
            "request": {"tissue_id": "lung", "tissue_site_detail": "Lung"},
            "status": "ready",
            "file_manifest_entries": [{"file_name": "gtex_lung_expression.gct.gz", "resource_name": "expression"}],
        }
    )
    write_legacy_acquisition_manifest(tmp_path, gtex)
    write_legacy_standardized_asset_candidates(tmp_path)
    materialize_legacy_standardized_asset_candidates(tmp_path)
    merge = merge_legacy_materialized_assets_into_repository_manifest(tmp_path)
    expression = _assets_by_role(merge, "expression_matrix")[0]

    selection = build_legacy_asset_selection_manifest(tmp_path, expression_asset_id=str(expression["asset_id"]), confirmed_by_user=True)
    result = apply_legacy_asset_selection_to_repository_manifest(tmp_path, selection)

    assert result["status"] == "selection_recorded_preflight_only"
    assert "gtex_expression_cannot_be_selected_as_tcga_normal_control" in result["validation"]["downstream_blockers"]
    resolved = resolve_analysis_inputs(tmp_path).to_dict()
    deg_package = next(package for package in resolved["packages"] if package["package_type"] == "deg_recompute")
    assert "gtex_must_not_auto_fill_tcga_normal_control" in deg_package["blockers"]
    survival_package = next(package for package in resolved["packages"] if package["package_type"] == "tcga_clinical_survival_preflight")
    assert "gtex_expression_cannot_be_auto_used_as_tcga_survival_normal_control" in survival_package["blockers"]
