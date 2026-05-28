from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.enrichment_backend import build_enrichment_backend_gate


def test_core_ora_passes_when_reactomepa_and_msigdbr_are_missing(tmp_path: Path) -> None:
    detection_path = _write_detection(tmp_path)

    gate = build_enrichment_backend_gate(tmp_path, analysis_type="ora", detection_path=detection_path)

    assert gate["schema_version"] == "biomedpilot.enrichment_backend_gate.v1"
    assert gate["status"] == "passed"
    assert gate["required_capabilities"] == ["ora_enricher"]
    assert gate["rscript"]["architecture"] == "arm64"
    assert gate["packages"]["clusterProfiler"]["version"] == "4.14.6"
    assert gate["install_action"] == "none_detect_first_only"
    assert gate["packaging_policy"] == "external_runtime_not_bundled"
    assert gate["semantic_boundary"] == "backend_gate_only_not_enrichment_execution"
    assert "external_detection_global_status_blocked_by_unselected_capabilities" in gate["warnings"]
    assert "external_detection_blocker_outside_selected_capabilities:ReactomePA" in gate["warnings"]
    assert "external_detection_package_not_required_for_selected_capability:msigdbr" in gate["warnings"]


def test_go_kegg_gsea_and_plot_capabilities_pass_independently(tmp_path: Path) -> None:
    detection_path = _write_detection(tmp_path)

    go = build_enrichment_backend_gate(tmp_path, analysis_type="ora_go", detection_path=detection_path)
    kegg = build_enrichment_backend_gate(tmp_path, analysis_type="ora_kegg", detection_path=detection_path)
    gsea = build_enrichment_backend_gate(tmp_path, analysis_type="gsea_preranked", detection_path=detection_path)
    plot = build_enrichment_backend_gate(tmp_path, analysis_type="enrichment_plot", detection_path=detection_path)

    assert go["status"] == "passed"
    assert kegg["status"] == "passed"
    assert gsea["status"] == "passed"
    assert plot["status"] == "passed"
    assert gsea["capability_rows"][0]["package_versions"]["fgsea"] == "1.32.4"
    assert plot["capability_rows"][0]["package_versions"]["enrichplot"] == "1.26.6"


def test_reactome_and_msigdbr_capabilities_remain_blocked(tmp_path: Path) -> None:
    detection_path = _write_detection(tmp_path)

    reactome = build_enrichment_backend_gate(tmp_path, analysis_type="ora_reactome", detection_path=detection_path)
    msigdbr = build_enrichment_backend_gate(tmp_path, analysis_type="msigdbr_resource", detection_path=detection_path)

    assert reactome["status"] == "blocked"
    assert any(str(item).startswith("missing_required_r_package:ReactomePA") for item in reactome["blockers"])
    assert msigdbr["status"] == "blocked"
    assert any(str(item).startswith("missing_required_r_package:msigdbr") for item in msigdbr["blockers"])


def test_missing_and_bad_detection_payloads_block_gracefully(tmp_path: Path) -> None:
    missing = build_enrichment_backend_gate(tmp_path, analysis_type="ora", detection_path=tmp_path / "missing.json")
    assert missing["status"] == "blocked"
    assert "external_enrichment_backend_detection_missing" in missing["blockers"]

    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{", encoding="utf-8")
    bad = build_enrichment_backend_gate(tmp_path, analysis_type="ora", detection_path=bad_json)
    assert bad["status"] == "blocked"
    assert "external_enrichment_backend_detection_invalid_json" in bad["blockers"]

    schema = tmp_path / "schema.json"
    payload = _detection_payload()
    payload["schema_version"] = "wrong"
    schema.write_text(json.dumps(payload), encoding="utf-8")
    mismatch = build_enrichment_backend_gate(tmp_path, analysis_type="ora", detection_path=schema)
    assert mismatch["status"] == "blocked"
    assert "external_enrichment_backend_schema_mismatch:wrong" in mismatch["blockers"]


def test_unknown_capability_blocks_without_traceback(tmp_path: Path) -> None:
    detection_path = _write_detection(tmp_path)

    gate = build_enrichment_backend_gate(tmp_path, required_capabilities=["unknown_capability"], detection_path=detection_path)

    assert gate["status"] == "blocked"
    assert "unknown_enrichment_backend_capability:unknown_capability" in gate["blockers"]


def _write_detection(tmp_path: Path) -> Path:
    path = tmp_path / "r_enrichment_backend_detection.json"
    path.write_text(json.dumps(_detection_payload()), encoding="utf-8")
    return path


def _detection_payload() -> dict[str, object]:
    available = {
        "clusterProfiler": "4.14.6",
        "fgsea": "1.32.4",
        "DOSE": "4.0.1",
        "enrichplot": "1.26.6",
        "ggplot2": "3.5.2",
        "AnnotationDbi": "1.68.0",
        "org.Hs.eg.db": "3.20.0",
    }
    packages = {name: {"available": True, "version": version, "importable": True, "missing_reason": ""} for name, version in available.items()}
    packages["ReactomePA"] = {
        "available": False,
        "version": "",
        "importable": False,
        "missing_reason": "package_not_installed_or_not_on_libpaths:ReactomePA",
    }
    packages["msigdbr"] = {
        "available": False,
        "version": "",
        "importable": False,
        "missing_reason": "package_not_installed_or_not_on_libpaths:msigdbr",
    }
    optional = {
        "KEGGREST": {"available": True, "version": "1.46.0", "importable": True, "missing_reason": ""},
        "GO.db": {"available": True, "version": "3.20.0", "importable": True, "missing_reason": ""},
        "pathview": {
            "available": False,
            "version": "",
            "importable": False,
            "missing_reason": "package_not_installed_or_not_on_libpaths:pathview",
        },
    }
    return {
        "schema_version": "biomedpilot.external_enrichment_r_backend_detection.v1",
        "created_at": "2026-05-28T00:00:00+00:00",
        "status": "blocked",
        "rscript": {
            "available": True,
            "path": "/usr/local/bin/Rscript",
            "version": "R version 4.4.2 (2024-10-31)",
            "architecture": "arm64",
            "library_paths": ["/Library/Frameworks/R.framework/Versions/4.4-arm64/Resources/library"],
        },
        "packages": packages,
        "optional_packages": optional,
        "capabilities": {
            "ora_enricher": True,
            "ora_go": True,
            "ora_kegg": True,
            "ora_reactome": False,
            "gsea_preranked_fgsea": True,
            "gsea_preranked_clusterprofiler": True,
            "enrichment_plot_dotplot": True,
            "enrichment_plot_barplot": True,
            "gsea_plot_curve": True,
        },
        "blockers": [
            {
                "code": "missing_required_r_package",
                "message": "package_not_installed_or_not_on_libpaths:ReactomePA",
                "package": "ReactomePA",
                "required_by": ["ora_reactome"],
            },
            {
                "code": "missing_required_r_package",
                "message": "package_not_installed_or_not_on_libpaths:msigdbr",
                "package": "msigdbr",
                "required_by": [],
            },
        ],
        "warnings": ["optional_r_package_missing:pathview:package_not_installed_or_not_on_libpaths:pathview"],
        "install_action": "none_detect_first_only",
        "packaging_policy": "external_runtime_not_bundled",
    }
