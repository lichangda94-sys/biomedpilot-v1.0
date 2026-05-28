from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.enrichment_execution_gate import (
    build_enrichment_execution_gate,
    build_enrichment_parameter_manifest,
    save_enrichment_parameter_confirmation,
    validate_enrichment_parameter_confirmation,
)
from app.bioinformatics.gene_set_resources import import_gmt_file, select_gene_set


def test_enrichment_execution_gate_requires_confirmation_after_resource_and_backend_pass(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path)
    select_gene_set(tmp_path, str(resource["resource_id"]))
    detection = _write_detection(tmp_path)

    gate = build_enrichment_execution_gate(tmp_path, analysis_type="ora", source_result_id="deg-1", resource_id=str(resource["resource_id"]), backend_detection_path=detection)

    assert gate["status"] == "blocked"
    assert gate["parameter_manifest"]["status"] == "passed"
    assert "enrichment_parameter_confirmation_missing" in gate["blockers"]
    assert gate["formal_ui_button_enabled"] is False
    assert gate["boundary"] == "execution_gate_only_formal_ui_activation_requires_later_stage"


def test_enrichment_confirmation_passes_and_detects_stale_manifest(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path)
    select_gene_set(tmp_path, str(resource["resource_id"]))
    detection = _write_detection(tmp_path)
    manifest = build_enrichment_parameter_manifest(tmp_path, analysis_type="gsea_preranked", source_result_id="deg-1", resource_id=str(resource["resource_id"]), backend_detection_path=detection)

    confirmation = save_enrichment_parameter_confirmation(tmp_path, manifest)
    gate = validate_enrichment_parameter_confirmation(confirmation, parameter_manifest=manifest)

    assert gate["status"] == "passed"
    changed = dict(manifest)
    changed["fdr_cutoff"] = 0.1
    changed["manifest_hash"] = "changed"
    stale = validate_enrichment_parameter_confirmation(confirmation, parameter_manifest=changed)
    assert stale["status"] == "blocked"
    assert "enrichment_parameter_confirmation_stale" in stale["blockers"]


def test_enrichment_parameter_manifest_blocks_non_formal_source_and_missing_resource(tmp_path: Path) -> None:
    detection = _write_detection(tmp_path)

    manifest = build_enrichment_parameter_manifest(tmp_path, analysis_type="ora", source_result_id="imported", source_result_semantics="imported_external_result", backend_detection_path=detection)

    assert manifest["status"] == "blocked"
    assert "enrichment_source_result_not_formal:imported_external_result" in manifest["blockers"]
    assert "enrichment_resource_not_selected" in manifest["blockers"]


def test_enrichment_parameter_manifest_blocks_reactome_until_package_available(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path, collection_type="Reactome")
    select_gene_set(tmp_path, str(resource["resource_id"]))
    detection = _write_detection(tmp_path)

    manifest = build_enrichment_parameter_manifest(tmp_path, analysis_type="ora_reactome", source_result_id="deg-1", resource_id=str(resource["resource_id"]), backend_detection_path=detection)

    assert manifest["status"] == "blocked"
    assert "unsupported_enrichment_analysis_type:ora_reactome" in manifest["blockers"]
    assert any(str(item).startswith("missing_required_r_package:ReactomePA") for item in manifest["blockers"])


def _import_resource(tmp_path: Path, *, collection_type: str = "Custom") -> dict[str, object]:
    gmt = tmp_path / f"{collection_type}.gmt"
    gmt.write_text("DNA_DAMAGE\tcurated\tTP53\tCDKN1A\tEGFR\nHOUSEKEEPING\tcurated\tGAPDH\tACTB\n", encoding="utf-8")
    return import_gmt_file(
        tmp_path,
        gmt,
        {
            "name": f"{collection_type} resource",
            "collection_type": collection_type,
            "species": "human",
            "gene_id_type": "symbol",
            "source_name": "unit-test-curation",
            "source_url": "https://example.test/resource.gmt",
            "license_note": "test-only user supplied resource",
            "version": "2026-test",
        },
    )["resource"]


def _write_detection(tmp_path: Path) -> Path:
    path = tmp_path / "r_enrichment_backend_detection.json"
    packages = {
        "clusterProfiler": {"available": True, "version": "4.14.6", "importable": True, "missing_reason": ""},
        "fgsea": {"available": True, "version": "1.32.4", "importable": True, "missing_reason": ""},
        "DOSE": {"available": True, "version": "4.0.1", "importable": True, "missing_reason": ""},
        "enrichplot": {"available": True, "version": "1.26.6", "importable": True, "missing_reason": ""},
        "ggplot2": {"available": True, "version": "3.5.2", "importable": True, "missing_reason": ""},
        "AnnotationDbi": {"available": True, "version": "1.68.0", "importable": True, "missing_reason": ""},
        "org.Hs.eg.db": {"available": True, "version": "3.20.0", "importable": True, "missing_reason": ""},
        "ReactomePA": {"available": False, "version": "", "importable": False, "missing_reason": "package_not_installed_or_not_on_libpaths:ReactomePA"},
        "msigdbr": {"available": False, "version": "", "importable": False, "missing_reason": "package_not_installed_or_not_on_libpaths:msigdbr"},
    }
    optional = {
        "KEGGREST": {"available": True, "version": "1.46.0", "importable": True, "missing_reason": ""},
        "GO.db": {"available": True, "version": "3.20.0", "importable": True, "missing_reason": ""},
    }
    path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.external_enrichment_r_backend_detection.v1",
                "status": "blocked",
                "rscript": {"available": True, "path": "/fake/Rscript", "version": "R 4.4.2", "architecture": "arm64"},
                "packages": packages,
                "optional_packages": optional,
                "capabilities": {
                    "ora_enricher": True,
                    "gsea_preranked_fgsea": True,
                    "ora_reactome": False,
                },
                "blockers": [{"code": "missing_required_r_package", "package": "ReactomePA", "required_by": ["ora_reactome"]}],
                "warnings": [],
                "install_action": "none_detect_first_only",
                "packaging_policy": "external_runtime_not_bundled",
            }
        ),
        encoding="utf-8",
    )
    return path
