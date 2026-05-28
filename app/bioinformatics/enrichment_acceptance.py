from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.bioinformatics.enrichment_backend import build_enrichment_backend_gate
from app.bioinformatics.enrichment_execution_gate import build_enrichment_parameter_manifest
from app.bioinformatics.enrichment_input_contract import build_enrichment_input_contract_gate
from app.bioinformatics.enrichment_result_schema import build_enrichment_statistical_policy, validate_enrichment_result_schema_gate
from app.bioinformatics.gene_set_resources import import_gmt_file, select_gene_set
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


ENRICHMENT_CROSS_LIBRARY_ACCEPTANCE_SCHEMA_VERSION = "biomedpilot.enrichment_cross_library_acceptance.v1"


def build_enrichment_cross_library_acceptance_gate(project_root: str | Path | None = None) -> dict[str, Any]:
    scenarios: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="biomedpilot_enrichment_acceptance_") as tmpdir:
        root = Path(tmpdir)
        detection = _write_detection(root, reactome=True, msigdbr=True)
        blocked_detection = root / "missing_detection.json"
        scenarios.extend(
            [
                _positive_resource_contract(root, "go_bp_ora_positive", collection_type="GO_BP", analysis_type="ora", source_gene_id_type="symbol", resource_gene_id_type="symbol", detection_path=detection),
                _positive_resource_contract(root, "kegg_entrez_ora_positive", collection_type="KEGG", analysis_type="ora", source_gene_id_type="entrez", resource_gene_id_type="entrez", detection_path=detection),
                _positive_resource_contract(root, "reactome_ora_positive", collection_type="Reactome", analysis_type="ora", source_gene_id_type="symbol", resource_gene_id_type="symbol", detection_path=detection),
                _positive_resource_contract(root, "msigdb_hallmark_gsea_positive", collection_type="Hallmark", analysis_type="gsea_preranked", source_gene_id_type="symbol", resource_gene_id_type="symbol", detection_path=detection),
                _positive_resource_contract(root, "custom_gmt_ora_positive", collection_type="Custom", analysis_type="ora", source_gene_id_type="symbol", resource_gene_id_type="symbol", detection_path=detection),
                _negative_contract(root, "id_space_mismatch_negative", lambda project: _id_mismatch_gate(project), expected_blocker="source_resource_gene_id_type_mismatch:symbol!=entrez"),
                _negative_contract(root, "missing_background_negative", lambda project: _missing_background_gate(project), expected_blocker="background_universe_empty"),
                _negative_contract(root, "missing_backend_negative", lambda project: _missing_backend_gate(project, blocked_detection), expected_blocker="external_enrichment_backend_detection_missing"),
                _negative_contract(root, "preflight_source_negative", lambda project: _non_formal_source_gate(project, semantics="preflight_only"), expected_blocker="enrichment_source_result_not_formal:preflight_only"),
                _negative_contract(root, "imported_source_negative", lambda project: _non_formal_source_gate(project, semantics="imported_external_result"), expected_blocker="enrichment_source_result_not_formal:imported_external_result"),
                _positive_result_schema(root, "ora_result_schema_positive", task_type="ora"),
                _positive_result_schema(root, "gsea_result_schema_positive", task_type="gsea_preranked"),
            ]
        )
    blockers = [f"scenario_failed:{row['scenario_id']}:{row['failure_reason']}" for row in scenarios if row.get("acceptance_status") != "passed"]
    return {
        "schema_version": ENRICHMENT_CROSS_LIBRARY_ACCEPTANCE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "project_root": str(Path(project_root).expanduser().resolve()) if project_root else "",
        "scenario_count": len(scenarios),
        "passed_scenario_count": sum(1 for row in scenarios if row.get("acceptance_status") == "passed"),
        "scenario_rows": scenarios,
        "acceptance_matrix": {
            "go_bp": _scenario_status(scenarios, "go_bp_ora_positive"),
            "kegg": _scenario_status(scenarios, "kegg_entrez_ora_positive"),
            "reactome": _scenario_status(scenarios, "reactome_ora_positive"),
            "msigdb_hallmark": _scenario_status(scenarios, "msigdb_hallmark_gsea_positive"),
            "custom_gmt": _scenario_status(scenarios, "custom_gmt_ora_positive"),
            "id_mismatch_negative": _scenario_status(scenarios, "id_space_mismatch_negative"),
            "missing_background_negative": _scenario_status(scenarios, "missing_background_negative"),
            "missing_backend_negative": _scenario_status(scenarios, "missing_backend_negative"),
            "non_formal_source_negative": all(_scenario_status(scenarios, item) == "passed" for item in ("preflight_source_negative", "imported_source_negative")),
        },
        "semantic_boundary": "acceptance_gate_only_not_enrichment_execution_or_interpretation",
        "blockers": blockers,
        "warnings": [],
    }


def _positive_resource_contract(
    root: Path,
    scenario_id: str,
    *,
    collection_type: str,
    analysis_type: str,
    source_gene_id_type: str,
    resource_gene_id_type: str,
    detection_path: Path,
) -> dict[str, Any]:
    project = root / scenario_id
    project.mkdir(parents=True)
    resource = _import_resource(project, collection_type=collection_type, gene_id_type=resource_gene_id_type)
    select_gene_set(project, str(resource["resource_id"]))
    _register_deg_source(project, "deg-source", gene_id_type=source_gene_id_type, value_prefix="ENTREZ" if source_gene_id_type == "entrez" else "")
    manifest = build_enrichment_parameter_manifest(
        project,
        analysis_type=analysis_type,
        source_result_id="deg-source",
        resource_id=str(resource["resource_id"]),
        required_gene_id_type=source_gene_id_type,
        backend_detection_path=detection_path,
    )
    return _scenario_row(scenario_id, "positive", manifest, expected_status="passed")


def _positive_result_schema(root: Path, scenario_id: str, *, task_type: str) -> dict[str, Any]:
    project = root / scenario_id
    project.mkdir(parents=True)
    table = _write_enrichment_result_table(project, task_type)
    result_id = f"{task_type}-formal"
    register_result(project, _enrichment_entry(project, result_id, task_type, table))
    gate = validate_enrichment_result_schema_gate(project, result_id=result_id)
    return _scenario_row(scenario_id, "positive", gate, expected_status="passed")


def _negative_contract(root: Path, scenario_id: str, builder: Callable[[Path], dict[str, Any]], *, expected_blocker: str) -> dict[str, Any]:
    project = root / scenario_id
    project.mkdir(parents=True)
    gate = builder(project)
    row = _scenario_row(scenario_id, "negative", gate, expected_status="blocked", expected_blocker=expected_blocker)
    return row


def _id_mismatch_gate(project: Path) -> dict[str, Any]:
    resource = _import_resource(project, collection_type="Custom", gene_id_type="entrez")
    select_gene_set(project, str(resource["resource_id"]))
    _register_deg_source(project, "deg-source", gene_id_type="symbol")
    return build_enrichment_input_contract_gate(project, analysis_type="ora", source_result_id="deg-source", resource_id=str(resource["resource_id"]), required_gene_id_type="symbol")


def _missing_background_gate(project: Path) -> dict[str, Any]:
    resource = _import_resource(project, collection_type="Custom", gene_id_type="symbol")
    select_gene_set(project, str(resource["resource_id"]))
    _register_deg_source(project, "deg-source", gene_id_type="symbol", empty_table=True)
    return build_enrichment_input_contract_gate(project, analysis_type="ora", source_result_id="deg-source", resource_id=str(resource["resource_id"]))


def _missing_backend_gate(project: Path, detection_path: Path) -> dict[str, Any]:
    resource = _import_resource(project, collection_type="Custom", gene_id_type="symbol")
    select_gene_set(project, str(resource["resource_id"]))
    _register_deg_source(project, "deg-source", gene_id_type="symbol")
    return build_enrichment_parameter_manifest(project, analysis_type="ora", source_result_id="deg-source", resource_id=str(resource["resource_id"]), backend_detection_path=detection_path)


def _non_formal_source_gate(project: Path, *, semantics: str) -> dict[str, Any]:
    resource = _import_resource(project, collection_type="Custom", gene_id_type="symbol")
    select_gene_set(project, str(resource["resource_id"]))
    _register_deg_source(project, "deg-source", gene_id_type="symbol", semantics=semantics)
    return build_enrichment_input_contract_gate(project, analysis_type="ora", source_result_id="deg-source", resource_id=str(resource["resource_id"]))


def _scenario_row(scenario_id: str, scenario_type: str, gate: dict[str, Any], *, expected_status: str, expected_blocker: str = "") -> dict[str, Any]:
    blockers = [str(item) for item in gate.get("blockers", []) or []]
    observed_status = str(gate.get("status") or "")
    if expected_status == "passed":
        accepted = observed_status == "passed" and not blockers
    else:
        accepted = observed_status == "blocked" and (not expected_blocker or expected_blocker in blockers)
    failure_reason = "" if accepted else f"expected_{expected_status}_with_{expected_blocker or 'no_blockers'}_observed_{observed_status}:{';'.join(blockers)}"
    return {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "expected_status": expected_status,
        "observed_status": observed_status,
        "expected_blocker": expected_blocker,
        "observed_blockers": blockers,
        "acceptance_status": "passed" if accepted else "failed",
        "failure_reason": failure_reason,
    }


def _import_resource(project: Path, *, collection_type: str, gene_id_type: str) -> dict[str, object]:
    gmt = project / f"{collection_type}_{gene_id_type}.gmt"
    genes = ("1017", "7157", "672") if gene_id_type == "entrez" else ("TP53", "BAX", "CDKN1A")
    gmt.write_text(f"DNA_DAMAGE\tcurated\t{genes[0]}\t{genes[1]}\t{genes[2]}\nINTERFERON\tcurated\tSTAT1\tIRF1\n", encoding="utf-8")
    return import_gmt_file(
        project,
        gmt,
        {
            "name": f"{collection_type} fixture",
            "collection_type": collection_type,
            "species": "human",
            "gene_id_type": gene_id_type,
            "source_name": "B97 fixture",
            "source_url": "https://example.test/enrichment-fixture.gmt",
            "license_note": "test-only fixture resource",
            "version": "2026-b97",
        },
    )["resource"]


def _register_deg_source(project: Path, result_id: str, *, gene_id_type: str, semantics: str = "formal_computed_result", value_prefix: str = "", empty_table: bool = False) -> None:
    table = project / "results" / "tables" / f"{result_id}.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    if empty_table:
        table.write_text("feature_id\tgene_symbol\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tsignificance_label\n", encoding="utf-8")
    elif gene_id_type == "entrez":
        table.write_text(
            "feature_id\tgene_symbol\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tsignificance_label\n"
            "1017\t1017\t1.5\t3.0\t0.01\t0.02\tup\n7157\t7157\t-1.3\t-2.2\t0.02\t0.04\tdown\n672\t672\t0.2\t0.1\t0.8\t0.9\tnot_significant\n",
            encoding="utf-8",
        )
    else:
        table.write_text(
            "feature_id\tgene_symbol\tlog2_fold_change\tstatistic\tp_value\tadjusted_p_value\tsignificance_label\n"
            "f1\tTP53\t1.5\t3.0\t0.01\t0.02\tup\nf2\tBAX\t-1.3\t-2.2\t0.02\t0.04\tdown\nf3\tCDKN1A\t0.2\t0.1\t0.8\t0.9\tnot_significant\n",
            encoding="utf-8",
        )
    register_result(
        project,
        ResultIndexEntry(
            result_id=result_id,
            task_run_id=f"{result_id}-task",
            task_type="deg",
            result_semantics=semantics,
            input_package_id="deg-ready",
            parameters_manifest={"gene_id_type": gene_id_type},
            engine_name="test_deg",
            engine_version="1",
            dependency_snapshot={"status": "passed"},
            output_artifacts=({"artifact_type": "deg_result_table", "path": str(table.relative_to(project)), "schema": "biomedpilot.deg_result_table.v1"},),
            validation_status="passed",
        ),
    )


def _write_enrichment_result_table(project: Path, task_type: str) -> Path:
    table = project / "results" / "tables" / f"{task_type}.tsv"
    table.parent.mkdir(parents=True, exist_ok=True)
    if task_type == "ora":
        table.write_text(
            "ID\tDescription\tGeneRatio\tBgRatio\tpvalue\tp.adjust\tqvalue\tgeneID\tCount\n"
            "DNA_DAMAGE\tDNA damage response\t2/3\t2/4\t0.01\t0.02\t0.02\tTP53/BAX\t2\n",
            encoding="utf-8",
        )
    else:
        table.write_text(
            "pathway\tES\tNES\tpval\tpadj\tleadingEdge\tsize\n"
            "DNA_DAMAGE\t0.8\t1.7\t0.01\t0.03\tTP53/BAX\t3\n",
            encoding="utf-8",
        )
    return table


def _enrichment_entry(project: Path, result_id: str, task_type: str, table: Path) -> dict[str, object]:
    artifact_type = "ora_result_table" if task_type == "ora" else "gsea_preranked_result_table"
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
        output_artifacts=({"artifact_type": artifact_type, "path": str(table.relative_to(project)), "schema": f"biomedpilot.{artifact_type}.v1"},),
        validation_status="passed",
    ).to_dict()


def _write_detection(root: Path, *, reactome: bool, msigdbr: bool) -> Path:
    path = root / "r_enrichment_backend_detection.json"
    packages = {
        "clusterProfiler": {"available": True, "version": "4.14.6", "importable": True, "missing_reason": ""},
        "fgsea": {"available": True, "version": "1.32.4", "importable": True, "missing_reason": ""},
        "DOSE": {"available": True, "version": "4.0.1", "importable": True, "missing_reason": ""},
        "enrichplot": {"available": True, "version": "1.26.6", "importable": True, "missing_reason": ""},
        "ggplot2": {"available": True, "version": "3.5.2", "importable": True, "missing_reason": ""},
        "AnnotationDbi": {"available": True, "version": "1.68.0", "importable": True, "missing_reason": ""},
        "org.Hs.eg.db": {"available": True, "version": "3.20.0", "importable": True, "missing_reason": ""},
        "ReactomePA": {"available": reactome, "version": "1.50.0" if reactome else "", "importable": reactome, "missing_reason": "" if reactome else "missing"},
        "msigdbr": {"available": msigdbr, "version": "7.5.1" if msigdbr else "", "importable": msigdbr, "missing_reason": "" if msigdbr else "missing"},
    }
    payload = {
        "schema_version": "biomedpilot.external_enrichment_r_backend_detection.v1",
        "status": "passed",
        "rscript": {"available": True, "path": "/fake/Rscript", "version": "R 4.4.2", "architecture": "arm64"},
        "packages": packages,
        "optional_packages": {"KEGGREST": {"available": True, "version": "1.46.0", "importable": True, "missing_reason": ""}},
        "capabilities": {
            "ora_enricher": True,
            "ora_go": True,
            "ora_kegg": True,
            "ora_reactome": reactome,
            "gsea_preranked_fgsea": True,
            "gsea_preranked_clusterprofiler": True,
            "msigdbr_gene_set_catalog": msigdbr,
        },
        "blockers": [],
        "warnings": [],
        "install_action": "none_detect_first_only",
        "packaging_policy": "external_runtime_not_bundled",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _scenario_status(scenarios: list[dict[str, Any]], scenario_id: str) -> str:
    row = next((item for item in scenarios if item.get("scenario_id") == scenario_id), {})
    return str(row.get("acceptance_status") or "missing")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
