from pathlib import Path

from app.bioinformatics.acquisition_adapters import (
    adapt_geo_detection_manifest,
    validate_legacy_acquisition_manifest,
    write_legacy_acquisition_manifest,
)


def test_geo_legacy_detection_manifest_stays_acquisition_only(tmp_path: Path) -> None:
    detection = {
        "accession": "GSE1",
        "accession_type": "GSE",
        "has_expression_payload": True,
        "matrix_level": "probe",
        "technology_type": "microarray",
        "value_semantic": "log2_expression",
        "recommended_strategy": "SERIES_MATRIX_FIRST",
        "candidate_expression_files": ["GSE1_series_matrix.txt.gz"],
        "candidate_metadata_files": ["GSE1_family.soft.gz"],
        "candidate_annotation_files": ["GPL1.annot.txt"],
        "warnings": ["legacy_detector_warning"],
    }

    manifest = adapt_geo_detection_manifest(accession="GSE1", scan_root=tmp_path, detection_result=detection)

    assert manifest["source"] == "geo"
    assert manifest["output_asset_type"] == "geo_detection_acquisition_candidate"
    assert manifest["status"] == "manifest_only"
    assert manifest["downstream_contract"]["writes_formal_result"] is False
    assert manifest["downstream_contract"]["ready_for_formal_analysis"] is False
    assert manifest["downstream_contract"]["must_pass_standardization"] is True
    assert manifest["downstream_contract"]["must_pass_b8_resolver"] is True
    assert "geo_probe_or_unknown_mapping_requires_later_standardization_gate" in manifest["warnings"]
    assert "result_semantics" not in manifest
    assert manifest.get("report_ready_eligible") is not True

    validation = validate_legacy_acquisition_manifest(manifest)
    assert validation["status"] == "passed"
    assert validation["blockers"] == []

    written = write_legacy_acquisition_manifest(tmp_path, manifest)
    assert written["status"] == "passed"
    assert Path(written["manifest_path"]).exists()


def test_legacy_manifest_validation_blocks_formal_promotion(tmp_path: Path) -> None:
    manifest = adapt_geo_detection_manifest(
        accession="GSE2",
        scan_root=tmp_path,
        detection_result={"has_expression_payload": True, "matrix_level": "gene"},
    )
    forged = {
        **manifest,
        "result_semantics": "formal_computed_result",
        "report_ready_eligible": True,
        "output_asset_type": "formal_deg_result",
    }

    validation = validate_legacy_acquisition_manifest(forged)

    assert validation["status"] == "blocked"
    assert "legacy_adapter_output_must_not_be_formal_result" in validation["blockers"]
    assert "legacy_adapter_must_not_set_formal_result_semantics" in validation["blockers"]
    assert "legacy_adapter_report_ready_forbidden" in validation["blockers"]
