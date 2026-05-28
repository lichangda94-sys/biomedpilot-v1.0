from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.enrichment_audit_package import create_enrichment_production_audit_package
from app.bioinformatics.enrichment_result_schema import build_enrichment_statistical_policy
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import load_registry, register_result


def test_enrichment_audit_package_requires_formal_enrichment_result(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    entry = _entry("imported", "ora", table, "ora_result_table")
    entry["result_semantics"] = "imported_external_result"
    register_result(tmp_path, entry)

    manifest = create_enrichment_production_audit_package(tmp_path, result_id="imported")

    assert manifest["status"] == "blocked"
    assert "enrichment_audit_package_requires_formal_computed_result" in manifest["blockers"]


def test_enrichment_audit_package_blocks_when_result_schema_gate_fails(tmp_path: Path) -> None:
    table = _write_ora_table(tmp_path)
    entry = _entry("ora-missing-policy", "ora", table, "ora_result_table")
    entry["parameters_manifest"].pop("statistical_policy")
    register_result(tmp_path, entry)

    manifest = create_enrichment_production_audit_package(tmp_path, result_id="ora-missing-policy")

    assert manifest["status"] == "blocked"
    assert "enrichment_statistical_policy_missing" in manifest["blockers"]


def test_enrichment_audit_package_copies_tables_plots_logs_and_manifests(tmp_path: Path) -> None:
    table = _write_gsea_table(tmp_path)
    plot = tmp_path / "plots" / "gsea.svg"
    plot.parent.mkdir(parents=True)
    plot.write_text("<svg><text>No clinical conclusion</text></svg>", encoding="utf-8")
    log = tmp_path / "analysis" / "enrichment" / "gsea_run_log.json"
    log.parent.mkdir(parents=True)
    log.write_text(json.dumps({"task_run_id": "task-gsea"}), encoding="utf-8")
    entry = _entry("gsea-formal", "gsea_preranked", table, "gsea_preranked_result_table")
    entry["plot_artifacts"] = [
        {
            "plot_id": "gsea-formal-gsea_preranked_plot",
            "plot_artifact_scope": "formal_enrichment_plot",
            "image_artifacts": [{"artifact_type": "svg", "path": str(plot.relative_to(tmp_path)), "mime_type": "image/svg+xml"}],
            "table_artifacts": [{"artifact_type": "source_enrichment_table", "path": str(table.relative_to(tmp_path))}],
        }
    ]
    entry["log_artifacts"] = [{"artifact_type": "controlled_enrichment_r_run_log", "path": str(log.relative_to(tmp_path))}]
    register_result(tmp_path, entry)

    manifest = create_enrichment_production_audit_package(tmp_path, result_id="gsea-formal")

    assert manifest["status"] == "enrichment_production_audit_package_created"
    assert manifest["report_ready_eligible_changed"] is False
    assert manifest["section_report_created"] is False
    assert manifest["clinical_interpretation_enabled"] is False
    package = Path(str(manifest["package_path"]))
    assert (package / "enrichment_audit_package_manifest.json").is_file()
    assert (package / "tables" / table.name).is_file()
    assert (package / "plots" / plot.name).is_file()
    assert (package / "logs" / log.name).is_file()
    assert (package / "manifests" / "resource_lock.json").is_file()
    assert (package / "manifests" / "background_universe.json").is_file()
    assert (package / "manifests" / "identifier_compatibility.json").is_file()
    assert (package / "manifests" / "statistical_policy.json").is_file()
    assert (package / "manifests" / "result_schema_gate.json").is_file()
    checksums = json.loads((package / "manifests" / "checksums.json").read_text(encoding="utf-8"))
    checksum_paths = {item["path"] for item in checksums["files"]}
    assert "tables/gsea.tsv" in checksum_paths
    assert "plots/gsea.svg" in checksum_paths
    assert "manifests/statistical_policy.json" in checksum_paths
    entry_after = load_registry(tmp_path)["results"][0]
    assert entry_after["report_ready_eligible"] is False


def _write_ora_table(tmp_path: Path) -> Path:
    path = tmp_path / "results" / "tables" / "ora.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "ID\tDescription\tGeneRatio\tBgRatio\tpvalue\tp.adjust\tqvalue\tgeneID\tCount\n"
        "DNA_DAMAGE\tDNA damage response\t2/3\t2/4\t0.01\t0.02\t0.02\tTP53/BAX\t2\n",
        encoding="utf-8",
    )
    return path


def _write_gsea_table(tmp_path: Path) -> Path:
    path = tmp_path / "results" / "tables" / "gsea.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "pathway\tES\tNES\tpval\tpadj\tleadingEdge\tsize\n"
        "DNA_DAMAGE\t0.8\t1.7\t0.01\t0.03\tTP53/BAX\t3\n",
        encoding="utf-8",
    )
    return path


def _entry(result_id: str, task_type: str, table: Path, artifact_type: str) -> dict[str, object]:
    return ResultIndexEntry(
        result_id=result_id,
        task_run_id=f"task-{result_id}",
        task_type=task_type,
        result_semantics="formal_computed_result",
        input_package_id="enrichment-input",
        source_dataset_id="controlled_enrichment_fixture",
        source_repository_manifest="controlled_fixture://enrichment/test",
        parameters_manifest={
            "analysis_type": task_type,
            "source_result_id": "deg-source",
            "resource_id": "resource-1",
            "statistical_policy": build_enrichment_statistical_policy(analysis_type=task_type),
            "input_contract_gate": {"status": "passed"},
            "background_universe": {"status": "passed", "gene_count": 3},
            "identifier_compatibility_gate": {"status": "passed"},
            "resource_lock": {"status": "passed", "resource_id": "resource-1"},
            "parameter_confirmation": {"status": "passed"},
        },
        engine_name="r_fgsea_preranked" if task_type == "gsea_preranked" else "r_clusterProfiler_enricher",
        engine_version="1",
        dependency_snapshot={"status": "passed"},
        output_artifacts=({"artifact_type": artifact_type, "path": str(table.relative_to(table.parents[2])), "schema": f"biomedpilot.{artifact_type}.v1"},),
        validation_status="passed",
        report_ready_eligible=False,
    ).to_dict()
