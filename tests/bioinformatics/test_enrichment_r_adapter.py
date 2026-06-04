from __future__ import annotations

import json
import subprocess
from pathlib import Path

from app.bioinformatics.enrichment_r_adapter import run_controlled_gsea_preranked_r_fixture, run_controlled_ora_r_fixture
from app.bioinformatics.results.registry import load_registry
from app.analysis_runtime import build_standard_analysis_package_catalog, validate_standard_result_package


def test_controlled_ora_r_fixture_registers_formal_result_without_plot_or_report(tmp_path: Path) -> None:
    detection = _write_detection(tmp_path)

    result = run_controlled_ora_r_fixture(tmp_path, detection_path=detection, runner=_fake_successful_r_runner)

    assert result["status"] == "passed"
    assert result["analysis_type"] == "ora"
    assert result["plot_artifacts"] == []
    assert result["report_artifacts"] == []
    assert result["report_ready_eligible"] is False
    result_path = Path(result["result_table_path"])
    standard_package_dir = Path(result["standard_result_package_dir"])
    assert result_path.is_file()
    assert standard_package_dir.is_dir()
    assert "DNA_DAMAGE" in result_path.read_text(encoding="utf-8")
    validation = validate_standard_result_package(
        standard_package_dir,
        expected_module_id="enrichment",
        expected_task_id=str(result["task_run_id"]),
        expected_mode="full",
    )
    assert validation["status"] == "passed"
    provenance = json.loads((standard_package_dir / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["worker_boundary"] == {
        "boundary_type": "legacy_service_adapter_sidecar",
        "standard_worker_entrypoint": "not_used",
        "subprocess_owner": "app.bioinformatics.enrichment_r_adapter",
        "migration_status": "sidecar_only_not_isolated_standard_worker",
        "task_system_invocation": "not_yet_migrated",
    }
    registry = load_registry(tmp_path)
    entry = registry["results"][0]
    assert entry["task_type"] == "ora"
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["engine_name"] == "r_clusterProfiler_enricher"
    assert entry["engine_version"] == "4.14.6"
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []
    assert entry["report_ready_eligible"] is False
    assert entry["validation_status"] == "passed"
    assert any(item["artifact_type"] == "standard_result_package" for item in entry["output_artifacts"])
    catalog = build_standard_analysis_package_catalog(tmp_path)
    assert catalog["status"] == "passed"
    assert catalog["package_count"] == 1
    assert catalog["rows"][0]["module_id"] == "enrichment"
    assert catalog["rows"][0]["mode"] == "full"
    assert catalog["rows"][0]["result_semantics"] == "formal_computed_result"
    assert catalog["rows"][0]["worker_boundary_type"] == "legacy_service_adapter_sidecar"
    assert catalog["rows"][0]["worker_migration_status"] == "sidecar_only_not_isolated_standard_worker"
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1
    assert catalog["rows"][0]["artifact_counts"]["plots"] == 0


def test_controlled_gsea_r_fixture_registers_formal_result_without_plot_or_report(tmp_path: Path) -> None:
    detection = _write_detection(tmp_path)

    result = run_controlled_gsea_preranked_r_fixture(tmp_path, detection_path=detection, runner=_fake_successful_r_runner)

    assert result["status"] == "passed"
    assert result["analysis_type"] == "gsea_preranked"
    result_path = Path(result["result_table_path"])
    standard_package_dir = Path(result["standard_result_package_dir"])
    assert result_path.is_file()
    assert standard_package_dir.is_dir()
    assert "NES" in result_path.read_text(encoding="utf-8")
    registry = load_registry(tmp_path)
    entry = registry["results"][0]
    assert entry["task_type"] == "gsea_preranked"
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["engine_name"] == "r_fgsea_preranked"
    assert entry["engine_version"] == "1.32.4"
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []
    assert entry["report_ready_eligible"] is False
    assert any(item["artifact_type"] == "standard_result_package" for item in entry["output_artifacts"])
    catalog = build_standard_analysis_package_catalog(tmp_path)
    assert catalog["package_count"] == 1
    assert catalog["rows"][0]["artifact_counts"]["tables"] == 1
    assert catalog["rows"][0]["artifact_counts"]["reports"] == 1


def test_controlled_enrichment_r_fixture_blocks_when_backend_gate_fails(tmp_path: Path) -> None:
    result = run_controlled_ora_r_fixture(tmp_path, detection_path=tmp_path / "missing.json", runner=_fake_successful_r_runner)

    assert result["status"] == "blocked"
    assert "external_enrichment_backend_detection_missing" in result["blockers"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_controlled_enrichment_r_fixture_blocks_when_rscript_fails(tmp_path: Path) -> None:
    detection = _write_detection(tmp_path)

    result = run_controlled_gsea_preranked_r_fixture(tmp_path, detection_path=detection, runner=_fake_failing_r_runner)

    assert result["status"] == "blocked"
    assert "r_enrichment_rscript_execution_failed" in result["blockers"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def _fake_successful_r_runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
    output = Path(command[-1])
    script = command[command.index("-e") + 1]
    if "clusterProfiler::enricher" in script:
        output.write_text(
            "ID\tDescription\tGeneRatio\tBgRatio\tpvalue\tp.adjust\tqvalue\tgeneID\tCount\n"
            "DNA_DAMAGE\tDNA damage response\t3/3\t3/5\t0.01\t0.02\t0.02\tTP53/CDKN1A/EGFR\t3\n",
            encoding="utf-8",
        )
    else:
        output.write_text(
            "pathway\tES\tNES\tpval\tpadj\tleadingEdge\tsize\n"
            "DNA_DAMAGE\t0.8\t1.7\t0.01\t0.03\tTP53/CDKN1A\t3\n",
            encoding="utf-8",
        )
    return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")


def _fake_failing_r_runner(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 1, stdout="", stderr="R package error")


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
                    {"code": "missing_required_r_package", "package": "ReactomePA", "required_by": ["ora_reactome"]},
                    {"code": "missing_required_r_package", "package": "msigdbr", "required_by": []},
                ],
                "warnings": [],
                "install_action": "none_detect_first_only",
                "packaging_policy": "external_runtime_not_bundled",
            }
        ),
        encoding="utf-8",
    )
    return path
