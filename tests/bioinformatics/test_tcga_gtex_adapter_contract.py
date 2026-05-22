from app.bioinformatics.acquisition_adapters import (
    adapt_gtex_preview_manifest,
    adapt_tcga_preview_manifest,
    validate_legacy_acquisition_manifest,
)


def test_tcga_preview_adapter_preserves_acquisition_boundary() -> None:
    summary = {
        "request": {"project_id": "TCGA-LUAD", "analysis_purpose": "differential_expression", "sample_scope": "tumor_normal"},
        "status": "ready",
        "file_count": 2,
        "case_count": 2,
        "sample_count": 2,
        "gdc_filters": {"op": "and"},
        "case_filters": {"op": "and"},
        "file_manifest_entries": [{"file_id": "file-1", "file_name": "counts.tsv", "data_type": "Gene Expression Quantification"}],
        "warnings": ["preview only"],
    }

    manifest = adapt_tcga_preview_manifest(preview_summary=summary)

    assert manifest["source"] == "tcga_gdc"
    assert manifest["output_asset_type"] == "tcga_gdc_acquisition_manifest_candidate"
    assert manifest["provenance"]["project_id"] == "TCGA-LUAD"
    assert manifest["provenance"]["file_count"] == 2
    assert manifest["downstream_contract"]["writes_formal_result"] is False
    assert manifest["downstream_contract"]["ready_for_formal_analysis"] is False
    assert manifest["downstream_contract"]["must_pass_b8_resolver"] is True
    assert validate_legacy_acquisition_manifest(manifest)["status"] == "passed"


def test_gtex_preview_adapter_cannot_be_tcga_normal_control() -> None:
    summary = {
        "request": {"tissue_id": "lung", "tissue_site_detail": "Lung", "use_purpose": "normal_reference"},
        "status": "ready",
        "donor_count": 10,
        "sample_count": 11,
        "file_count": 1,
        "file_manifest_entries": [{"file_name": "gtex_lung.gct.gz"}],
        "tissue_metadata": {"tissueSiteDetail": "Lung"},
        "warnings": [],
    }

    manifest = adapt_gtex_preview_manifest(preview_summary=summary)

    assert manifest["source"] == "gtex"
    assert manifest["output_asset_type"] == "gtex_acquisition_manifest_candidate"
    assert manifest["downstream_contract"]["can_fill_tcga_normal_control"] is False
    assert "gtex_must_remain_independent_not_tcga_normal_control" in manifest["warnings"]
    assert validate_legacy_acquisition_manifest(manifest)["status"] == "passed"


def test_gtex_contract_validation_blocks_tcga_normal_control_override() -> None:
    manifest = adapt_gtex_preview_manifest(
        preview_summary={
            "request": {"tissue_id": "lung", "tissue_site_detail": "Lung"},
            "status": "ready",
            "file_manifest_entries": [{"file_name": "gtex_lung.gct.gz"}],
        }
    )
    forged = {**manifest, "downstream_contract": {**manifest["downstream_contract"], "can_fill_tcga_normal_control": True}}

    validation = validate_legacy_acquisition_manifest(forged)

    assert validation["status"] == "blocked"
    assert "gtex_adapter_must_not_fill_tcga_normal_control" in validation["blockers"]
