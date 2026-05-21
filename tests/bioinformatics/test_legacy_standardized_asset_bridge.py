from pathlib import Path

from app.bioinformatics.acquisition_adapters import (
    adapt_geo_detection_manifest,
    adapt_gtex_preview_manifest,
    adapt_tcga_preview_manifest,
    validate_legacy_standardized_asset_candidate,
    write_legacy_acquisition_manifest,
    write_legacy_standardized_asset_candidates,
)


def test_bridge_writes_geo_standardized_asset_candidates_without_analysis_inputs(tmp_path: Path) -> None:
    manifest = adapt_geo_detection_manifest(
        accession="GSE_BRIDGE",
        scan_root=tmp_path,
        detection_result={
            "accession_type": "GSE",
            "has_expression_payload": True,
            "matrix_level": "gene",
            "candidate_expression_files": ["GSE_BRIDGE_series_matrix.txt.gz"],
            "candidate_metadata_files": ["GSE_BRIDGE_family.soft.gz"],
            "candidate_annotation_files": ["GPL_BRIDGE.annot.txt"],
        },
    )
    write_legacy_acquisition_manifest(tmp_path, manifest)

    bundle = write_legacy_standardized_asset_candidates(tmp_path)

    assert bundle["status"] == "candidate_only"
    assert bundle["candidate_count"] == 3
    assert bundle["downstream_contract"]["writes_repository_manifest"] is False
    assert bundle["downstream_contract"]["writes_analysis_input_repository"] is False
    assert bundle["downstream_contract"]["writes_result_index"] is False
    assert (tmp_path / "standardized_data/asset_candidates/legacy_acquisition_asset_candidates.json").exists()
    assert not (tmp_path / "standardized_data/repositories/repository_manifest.json").exists()
    assert not (tmp_path / "standardized_data/repositories/analysis_input_repository").exists()
    roles = {candidate["asset_role"] for candidate in bundle["candidates"]}
    assert roles == {"expression_matrix", "sample_metadata", "feature_annotation"}
    assert all(candidate["formal_analysis_ready"] is False for candidate in bundle["candidates"])
    assert all(candidate["result_semantics"] == "not_a_result" for candidate in bundle["candidates"])


def test_bridge_maps_tcga_and_gtex_preview_candidates(tmp_path: Path) -> None:
    tcga = adapt_tcga_preview_manifest(
        preview_summary={
            "request": {"project_id": "TCGA-LUAD", "analysis_purpose": "differential_expression"},
            "status": "ready",
            "file_count": 1,
            "file_manifest_entries": [{"file_id": "file-1", "file_name": "TCGA-LUAD.star_counts.tsv", "data_type": "Gene Expression Quantification"}],
        }
    )
    gtex = adapt_gtex_preview_manifest(
        preview_summary={
            "request": {"tissue_id": "lung", "tissue_site_detail": "Lung"},
            "status": "ready",
            "file_manifest_entries": [{"file_name": "GTEx_lung_expression.gct.gz", "resource_name": "expression"}],
        }
    )
    write_legacy_acquisition_manifest(tmp_path, tcga)
    write_legacy_acquisition_manifest(tmp_path, gtex)

    bundle = write_legacy_standardized_asset_candidates(tmp_path)

    asset_types = {candidate["asset_type"] for candidate in bundle["candidates"]}
    assert "tcga_expression_matrix_candidate" in asset_types
    assert "gtex_expression_matrix_candidate" in asset_types
    gtex_candidates = [candidate for candidate in bundle["candidates"] if candidate["source"] == "gtex"]
    assert gtex_candidates
    assert all(candidate["can_fill_tcga_normal_control"] is False for candidate in gtex_candidates)
    assert all("standardization_validation" in candidate["next_required_gates"] for candidate in bundle["candidates"])
    assert all("b8_analysis_input_resolver" in candidate["next_required_gates"] for candidate in bundle["candidates"])


def test_candidate_validation_blocks_formal_promotion(tmp_path: Path) -> None:
    manifest = adapt_geo_detection_manifest(
        accession="GSE_FORMAL",
        scan_root=tmp_path,
        detection_result={"has_expression_payload": True, "matrix_level": "gene", "candidate_expression_files": ["matrix.tsv"]},
    )
    write_legacy_acquisition_manifest(tmp_path, manifest)
    bundle = write_legacy_standardized_asset_candidates(tmp_path)
    candidate = dict(bundle["candidates"][0])
    candidate.update(
        {
            "formal_analysis_ready": True,
            "result_semantics": "formal_computed_result",
            "report_ready_eligible": True,
        }
    )

    validation = validate_legacy_standardized_asset_candidate(candidate)

    assert validation["status"] == "blocked"
    assert "legacy_asset_candidate_must_not_be_formal_ready" in validation["blockers"]
    assert "legacy_asset_candidate_must_not_set_formal_result_semantics" in validation["blockers"]
    assert "legacy_asset_candidate_report_ready_forbidden" in validation["blockers"]


def test_blocked_legacy_manifest_stays_blocked_candidate(tmp_path: Path) -> None:
    manifest = adapt_geo_detection_manifest(
        accession="GSE_METADATA_ONLY",
        scan_root=tmp_path,
        detection_result={"has_expression_payload": False, "matrix_level": "unknown", "candidate_metadata_files": ["family.soft.gz"]},
    )
    write_legacy_acquisition_manifest(tmp_path, manifest)

    bundle = write_legacy_standardized_asset_candidates(tmp_path)

    assert bundle["candidate_count"] == 1
    candidate = bundle["candidates"][0]
    assert candidate["validation_status"] == "blocked"
    assert "geo_legacy_detection_missing_expression_payload" in candidate["blockers"]
    assert candidate["formal_analysis_ready"] is False
