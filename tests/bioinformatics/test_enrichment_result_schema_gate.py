from __future__ import annotations

from pathlib import Path

from app.bioinformatics.enrichment_execution_gate import build_enrichment_parameter_manifest
from app.bioinformatics.enrichment_result_schema import build_enrichment_statistical_policy, validate_enrichment_result_schema_gate
from app.bioinformatics.gene_set_resources import import_gmt_file, select_gene_set
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


def test_enrichment_statistical_policy_blocks_invalid_thresholds() -> None:
    policy = build_enrichment_statistical_policy(analysis_type="ora", p_value_cutoff=1.5, fdr_cutoff=-0.1, min_gene_set_size=0, max_gene_set_size=0, p_adjust_method="none")

    assert policy["status"] == "blocked"
    assert "invalid_enrichment_p_value_cutoff" in policy["blockers"]
    assert "invalid_enrichment_fdr_cutoff" in policy["blockers"]
    assert "invalid_min_gene_set_size" in policy["blockers"]
    assert "unsupported_multiple_testing_method:none" in policy["blockers"]


def test_enrichment_result_schema_gate_passes_for_complete_ora_result(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "ora.tsv"
    table.parent.mkdir(parents=True)
    table.write_text(
        "ID\tDescription\tGeneRatio\tBgRatio\tpvalue\tp.adjust\tqvalue\tgeneID\tCount\n"
        "DNA_DAMAGE\tDNA damage response\t2/3\t2/4\t0.01\t0.02\t0.02\tTP53/BAX\t2\n",
        encoding="utf-8",
    )
    register_result(tmp_path, _entry("ora-1", "ora", table, "ora_result_table"))

    gate = validate_enrichment_result_schema_gate(tmp_path, result_id="ora-1")

    assert gate["schema_version"] == "biomedpilot.enrichment_result_schema_gate.v1"
    assert gate["status"] == "passed"
    assert gate["table_validation"]["status"] == "passed"
    assert gate["statistical_policy"]["status"] == "passed"
    assert gate["semantic_boundary"] == "result_schema_gate_only_not_interpretation_or_report_ready"


def test_enrichment_result_schema_gate_passes_for_complete_gsea_result(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "gsea.tsv"
    table.parent.mkdir(parents=True)
    table.write_text(
        "pathway\tES\tNES\tpval\tpadj\tleadingEdge\tsize\n"
        "DNA_DAMAGE\t0.8\t1.7\t0.01\t0.03\tTP53/BAX\t3\n",
        encoding="utf-8",
    )
    register_result(tmp_path, _entry("gsea-1", "gsea_preranked", table, "gsea_preranked_result_table"))

    gate = validate_enrichment_result_schema_gate(tmp_path, result_id="gsea-1")

    assert gate["status"] == "passed"
    assert gate["table_validation"]["row_count"] == 1


def test_enrichment_result_schema_gate_blocks_missing_policy_and_bad_probabilities(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "bad.tsv"
    table.parent.mkdir(parents=True)
    table.write_text(
        "ID\tDescription\tGeneRatio\tBgRatio\tpvalue\tp.adjust\tqvalue\tgeneID\tCount\n"
        "DNA_DAMAGE\tDNA damage response\t2/3\t2/4\t1.2\tbad\t0.02\tTP53/BAX\t2\n",
        encoding="utf-8",
    )
    entry = _entry("bad-ora", "ora", table, "ora_result_table")
    entry["parameters_manifest"].pop("statistical_policy")
    register_result(tmp_path, entry)

    gate = validate_enrichment_result_schema_gate(tmp_path, result_id="bad-ora")

    assert gate["status"] == "blocked"
    assert "enrichment_statistical_policy_missing" in gate["blockers"]
    assert "enrichment_result_invalid_probability:pvalue:row_1" in gate["blockers"]
    assert "enrichment_result_invalid_probability:p.adjust:row_1" in gate["blockers"]


def test_enrichment_result_schema_gate_blocks_non_formal_or_imported_result(tmp_path: Path) -> None:
    table = tmp_path / "results" / "tables" / "ora.tsv"
    table.parent.mkdir(parents=True)
    table.write_text(
        "ID\tDescription\tGeneRatio\tBgRatio\tpvalue\tp.adjust\tqvalue\tgeneID\tCount\n"
        "DNA_DAMAGE\tDNA damage response\t2/3\t2/4\t0.01\t0.02\t0.02\tTP53/BAX\t2\n",
        encoding="utf-8",
    )
    entry = _entry("imported-ora", "ora", table, "ora_result_table")
    entry["result_semantics"] = "imported_external_result"
    register_result(tmp_path, entry)

    gate = validate_enrichment_result_schema_gate(tmp_path, result_id="imported-ora")

    assert gate["status"] == "blocked"
    assert "enrichment_result_not_formal:imported_external_result" in gate["blockers"]


def test_enrichment_parameter_manifest_embeds_statistical_policy(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path)
    select_gene_set(tmp_path, str(resource["resource_id"]))
    _register_deg_source(tmp_path, "deg-1")
    detection = _write_detection(tmp_path)

    manifest = build_enrichment_parameter_manifest(tmp_path, analysis_type="ora", source_result_id="deg-1", resource_id=str(resource["resource_id"]), backend_detection_path=detection)

    assert manifest["status"] == "passed"
    assert manifest["statistical_policy"]["schema_version"] == "biomedpilot.enrichment_statistical_policy.v1"
    assert manifest["statistical_policy"]["status"] == "passed"


def _entry(result_id: str, task_type: str, table: Path, artifact_type: str) -> dict[str, object]:
    return ResultIndexEntry(
        result_id=result_id,
        task_run_id=f"{result_id}-task",
        task_type=task_type,
        result_semantics="formal_computed_result",
        input_package_id="enrichment-input",
        parameters_manifest={
            "analysis_type": task_type,
            "statistical_policy": build_enrichment_statistical_policy(analysis_type=task_type),
            "input_contract_gate": {"status": "passed"},
            "background_universe": {"status": "passed"},
            "identifier_compatibility_gate": {"status": "passed"},
            "resource_lock": {"status": "passed"},
        },
        engine_name="test_enrichment",
        engine_version="1",
        dependency_snapshot={"status": "passed"},
        output_artifacts=({"artifact_type": artifact_type, "path": str(table), "schema": f"biomedpilot.{artifact_type}.v1"},),
        validation_status="passed",
    ).to_dict()


def _import_resource(tmp_path: Path) -> dict[str, object]:
    gmt = tmp_path / "resource.gmt"
    gmt.write_text("DNA_DAMAGE\tcurated\tTP53\tBAX\tCDKN1A\n", encoding="utf-8")
    return import_gmt_file(
        tmp_path,
        gmt,
        {
            "name": "Curated pathways",
            "collection_type": "Custom",
            "species": "human",
            "gene_id_type": "symbol",
            "source_name": "unit-test-curation",
            "source_url": "https://example.test/gmt",
            "license_note": "test-only user supplied resource",
            "version": "2026-test",
        },
    )["resource"]


def _register_deg_source(tmp_path: Path, result_id: str) -> None:
    table = tmp_path / "results" / "tables" / f"{result_id}.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    table.write_text(
        "feature_id\tgene_symbol\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tsignificance_label\n"
        "f1\tTP53\t1.5\t3.0\t0.01\t0.02\tup\n"
        "f2\tBAX\t-1.3\t-2.2\t0.02\t0.04\tdown\n",
        encoding="utf-8",
    )
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id=result_id,
            task_run_id=f"{result_id}-task",
            task_type="deg",
            result_semantics="formal_computed_result",
            input_package_id="deg-ready",
            parameters_manifest={"gene_id_type": "symbol"},
            engine_name="test_deg",
            engine_version="1",
            dependency_snapshot={"status": "passed"},
            output_artifacts=({"artifact_type": "deg_result_table", "path": str(table.relative_to(tmp_path)), "schema": "biomedpilot.deg_result_table.v1"},),
            validation_status="passed",
        ),
    )


def _write_detection(tmp_path: Path) -> Path:
    path = tmp_path / "r_enrichment_backend_detection.json"
    path.write_text(
        """{
  "schema_version": "biomedpilot.external_enrichment_r_backend_detection.v1",
  "status": "blocked",
  "rscript": {"available": true, "path": "/fake/Rscript", "version": "R 4.4.2", "architecture": "arm64"},
  "packages": {
    "clusterProfiler": {"available": true, "version": "4.14.6", "importable": true, "missing_reason": ""},
    "fgsea": {"available": true, "version": "1.32.4", "importable": true, "missing_reason": ""},
    "DOSE": {"available": true, "version": "4.0.1", "importable": true, "missing_reason": ""},
    "enrichplot": {"available": true, "version": "1.26.6", "importable": true, "missing_reason": ""},
    "ggplot2": {"available": true, "version": "3.5.2", "importable": true, "missing_reason": ""},
    "AnnotationDbi": {"available": true, "version": "1.68.0", "importable": true, "missing_reason": ""},
    "org.Hs.eg.db": {"available": true, "version": "3.20.0", "importable": true, "missing_reason": ""}
  },
  "optional_packages": {},
  "capabilities": {"ora_enricher": true, "gsea_preranked_fgsea": true},
  "blockers": [],
  "warnings": [],
  "install_action": "none_detect_first_only",
  "packaging_policy": "external_runtime_not_bundled"
}""",
        encoding="utf-8",
    )
    return path
