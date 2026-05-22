from pathlib import Path

from app.bioinformatics.acquisition_adapters import adapt_geo_detection_manifest, validate_legacy_acquisition_manifest


def test_geo_adapter_blocks_metadata_only_legacy_detection(tmp_path: Path) -> None:
    manifest = adapt_geo_detection_manifest(
        accession="GSE_METADATA",
        scan_root=tmp_path,
        detection_result={
            "accession_type": "GSE",
            "has_expression_payload": False,
            "payload_type": "metadata_only",
            "candidate_metadata_files": ["GSE_METADATA_family.soft.gz"],
            "warnings": [],
        },
    )

    assert manifest["status"] == "blocked"
    assert "geo_legacy_detection_missing_expression_payload" in manifest["blockers"]
    assert manifest["downstream_contract"]["forbidden_next_layers"] == [
        "formal_result_index",
        "formal_plot",
        "report_ready_package",
    ]

    validation = validate_legacy_acquisition_manifest(manifest)
    assert validation["status"] == "passed"


def test_geo_adapter_uses_deterministic_adapter_id(tmp_path: Path) -> None:
    first = adapt_geo_detection_manifest(
        accession="GSE_DET",
        scan_root=tmp_path,
        detection_result={"has_expression_payload": True, "matrix_level": "gene"},
    )
    second = adapt_geo_detection_manifest(
        accession="GSE_DET",
        scan_root=tmp_path,
        detection_result={"has_expression_payload": True, "matrix_level": "gene"},
    )

    assert first["adapter_id"] == second["adapter_id"]
    assert first["checksum"].startswith("sha256:")
