from pathlib import Path

from app.bioinformatics.acquisition_adapters import (
    adapt_geo_detection_manifest,
    adapt_gtex_preview_manifest,
    materialize_legacy_standardized_asset_candidates,
    merge_legacy_materialized_assets_into_repository_manifest,
    plan_legacy_repository_manifest_merge,
    validate_legacy_repository_manifest_merge_plan,
    write_legacy_acquisition_manifest,
    write_legacy_standardized_asset_candidates,
)
from app.bioinformatics.analysis_inputs import resolve_analysis_inputs


def _write_geo_expression_source(tmp_path: Path, name: str = "gene_symbol_matrix.tsv") -> Path:
    source = tmp_path / "inputs" / name
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("gene_symbol\ts1\ts2\nTP53\t1\t2\n", encoding="utf-8")
    return source


def _prepare_materialized_geo_expression(tmp_path: Path) -> dict[str, object]:
    source = _write_geo_expression_source(tmp_path)
    manifest = adapt_geo_detection_manifest(
        accession="GSE_MERGE",
        scan_root=tmp_path,
        detection_result={
            "accession_type": "GSE",
            "has_expression_payload": True,
            "matrix_level": "gene",
            "candidate_expression_files": [str(source)],
        },
    )
    write_legacy_acquisition_manifest(tmp_path, manifest)
    write_legacy_standardized_asset_candidates(tmp_path)
    return materialize_legacy_standardized_asset_candidates(tmp_path)


def test_repository_merge_writes_manifest_but_not_analysis_inputs_or_results(tmp_path: Path) -> None:
    _prepare_materialized_geo_expression(tmp_path)

    merge = merge_legacy_materialized_assets_into_repository_manifest(tmp_path)

    assert merge["status"] == "merged_repository_manifest_only"
    assert merge["merged_asset_count"] == 1
    repository_manifest = tmp_path / "standardized_data/repositories/repository_manifest.json"
    validation_report = tmp_path / "standardized_data/repositories/validation_report.json"
    lineage = tmp_path / "standardized_data/repositories/asset_lineage.jsonl"
    assert repository_manifest.exists()
    assert validation_report.exists()
    assert lineage.exists()
    assert not (tmp_path / "standardized_data/repositories/analysis_input_repository").exists()
    assert not (tmp_path / "results/summaries/result_index.json").exists()

    asset = merge["merged_assets"][0]
    assert asset["asset_type"] == "expression_matrix"
    assert asset["legacy_asset_type"] == "geo_expression_matrix"
    assert asset["analysis_ready"] is False
    assert asset["formal_analysis_ready"] is False
    assert asset["result_semantics"] == "not_a_result"
    assert asset["report_ready_eligible"] is False
    assert asset["default_selected"] is False
    assert merge["downstream_contract"]["writes_analysis_input_repository"] is False
    assert merge["downstream_contract"]["writes_result_index"] is False


def test_repository_merge_makes_asset_visible_to_resolver_but_formal_deg_stays_blocked(tmp_path: Path) -> None:
    _prepare_materialized_geo_expression(tmp_path)
    merge_legacy_materialized_assets_into_repository_manifest(tmp_path)

    resolved = resolve_analysis_inputs(tmp_path).to_dict()

    assert resolved["packages"]
    deg_package = next(package for package in resolved["packages"] if package["package_type"] == "deg_recompute")
    assert deg_package["expression_asset"]["asset_type"] == "expression_matrix"
    assert deg_package["status"] == "blocked"
    assert "missing_sample_metadata_asset" in deg_package["blockers"]
    assert "missing_group_design_asset" in deg_package["blockers"]
    assert not (tmp_path / "standardized_data/repositories/analysis_input_repository").exists()


def test_repository_merge_preserves_gtex_normal_control_boundary(tmp_path: Path) -> None:
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
    resolved = resolve_analysis_inputs(tmp_path).to_dict()

    assert merge["merged_assets"][0]["asset_type"] == "gtex_expression_matrix"
    deg_package = next(package for package in resolved["packages"] if package["package_type"] == "deg_recompute")
    assert "gtex_must_not_auto_fill_tcga_normal_control" in deg_package["blockers"]
    survival_package = next(package for package in resolved["packages"] if package["package_type"] == "tcga_clinical_survival_preflight")
    assert "gtex_expression_cannot_be_auto_used_as_tcga_survival_normal_control" in survival_package["blockers"]


def test_repository_merge_plan_validation_blocks_formal_promotion(tmp_path: Path) -> None:
    _prepare_materialized_geo_expression(tmp_path)
    plan = plan_legacy_repository_manifest_merge(tmp_path)
    plan["downstream_contract"] = {
        **plan["downstream_contract"],
        "writes_analysis_input_repository": True,
        "writes_result_index": True,
        "ready_for_formal_analysis": True,
    }
    plan["merge_assets"][0] = {
        **plan["merge_assets"][0],
        "analysis_ready": True,
        "formal_analysis_ready": True,
        "result_semantics": "formal_computed_result",
        "report_ready_eligible": True,
    }

    validation = validate_legacy_repository_manifest_merge_plan(plan)

    assert validation["status"] == "blocked"
    assert "repository_merge_must_not_write_analysis_input_repository" in validation["blockers"]
    assert "repository_merge_must_not_write_result_index" in validation["blockers"]
    assert "repository_merge_must_not_be_formal_ready" in validation["blockers"]
    assert "merge_asset_0:analysis_ready_forbidden_in_b16_3" in validation["blockers"]
    assert "merge_asset_0:formal_analysis_ready_forbidden" in validation["blockers"]
    assert "merge_asset_0:formal_result_semantics_forbidden" in validation["blockers"]
    assert "merge_asset_0:report_ready_forbidden" in validation["blockers"]


def test_repository_merge_blocks_blocked_materialization(tmp_path: Path) -> None:
    manifest = adapt_geo_detection_manifest(
        accession="GSE_BLOCKED_MERGE",
        scan_root=tmp_path,
        detection_result={"has_expression_payload": False, "matrix_level": "unknown", "candidate_metadata_files": ["missing.soft"]},
    )
    write_legacy_acquisition_manifest(tmp_path, manifest)
    write_legacy_standardized_asset_candidates(tmp_path)
    materialize_legacy_standardized_asset_candidates(tmp_path)

    merge = merge_legacy_materialized_assets_into_repository_manifest(tmp_path)

    assert merge["status"] == "merged_repository_manifest_only"
    assert merge["merged_asset_count"] == 0
