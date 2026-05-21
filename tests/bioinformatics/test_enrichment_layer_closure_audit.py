from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.enrichment import audit_enrichment_layer_closure
from app.bioinformatics.plots import create_gsea_plot_artifact, create_ora_plot_artifact
from app.bioinformatics.reports.gsea import create_gsea_report_ready_package
from app.bioinformatics.reports.ora import create_ora_report_ready_package
from app.bioinformatics.results.models import RESULT_INDEX_SCHEMA_VERSION, ResultIndexEntry


def test_enrichment_layer_closure_passes_complete_formal_deg_ora_gsea_chain(tmp_path: Path) -> None:
    _complete_layer_fixture(tmp_path, semantics="formal_computed_result")
    assert create_ora_plot_artifact(tmp_path, result_id="ora-formal")["status"] == "passed"
    assert create_gsea_plot_artifact(tmp_path, result_id="gsea-formal")["status"] == "passed"
    assert create_ora_report_ready_package(tmp_path, result_id="ora-formal")["status"] == "ora_report_ready_package_created"
    assert create_gsea_report_ready_package(tmp_path, result_id="gsea-formal")["status"] == "gsea_report_ready_package_created"

    audit = audit_enrichment_layer_closure(tmp_path, require_complete_layer=True)

    assert audit["status"] == "passed"
    assert audit["blockers"] == []
    assert audit["result_semantics_check"]["status"] == "passed"
    assert audit["gene_set_resource_check"]["status"] == "passed"
    matrix = {row["capability"]: row for row in audit["capability_matrix"]}
    assert matrix["Controlled ORA from formal DEG"]["result_present_in_current_project"] is True
    assert matrix["Controlled preranked GSEA from formal DEG"]["result_present_in_current_project"] is True
    assert matrix["Full integrated report"]["current_status"] == "disabled_not_implemented"
    assert matrix["Survival / KM / Cox"]["current_status"] == "disabled_not_implemented"


def test_enrichment_layer_closure_allows_imported_derived_without_formal_upgrade(tmp_path: Path) -> None:
    _complete_layer_fixture(tmp_path, semantics="imported_external_result", source_semantics="imported_external_result", imported_warning=True)
    assert create_ora_plot_artifact(tmp_path, result_id="ora-formal")["status"] == "passed"
    assert create_gsea_plot_artifact(tmp_path, result_id="gsea-formal")["status"] == "passed"
    assert create_ora_report_ready_package(tmp_path, result_id="ora-formal")["status"] == "imported_derived_ora_report_package_created"
    assert create_gsea_report_ready_package(tmp_path, result_id="gsea-formal")["status"] == "imported_derived_gsea_report_package_created"

    audit = audit_enrichment_layer_closure(tmp_path)

    assert audit["status"] == "passed"
    entries = _load_entries(tmp_path)
    assert next(item for item in entries if item["result_id"] == "ora-formal")["report_ready_eligible"] is False
    assert next(item for item in entries if item["result_id"] == "gsea-formal")["report_ready_eligible"] is False


def test_enrichment_layer_closure_blocks_raw_expression_source_and_preflight_report_ready(tmp_path: Path) -> None:
    _complete_layer_fixture(tmp_path)
    entries = _load_entries(tmp_path)
    entries[0]["task_type"] = "expression_matrix"
    entries[1]["result_semantics"] = "preflight_only"
    entries[1]["report_ready_eligible"] = True
    entries[1]["report_artifacts"] = [{"artifact_type": "ora_report_ready_package", "path": "missing.json"}]
    _write_result_index(tmp_path, entries)

    audit = audit_enrichment_layer_closure(tmp_path)

    assert audit["status"] == "blocked"
    assert "ora_enrichment_source_not_deg:ora-formal:expression_matrix" in audit["blockers"]
    assert "non_formal_result_report_ready:ora-formal:preflight_only" in audit["blockers"]


def test_enrichment_layer_closure_blocks_missing_gene_set_and_dependency_snapshot(tmp_path: Path) -> None:
    _complete_layer_fixture(tmp_path)
    entries = _load_entries(tmp_path)
    entries[1]["gene_set_resource_id"] = "missing-sets"
    entries[1]["parameters_manifest"]["gene_set_resource_id"] = "missing-sets"
    entries[2]["dependency_snapshot"]["status"] = "blocked"
    entries[2]["dependency_snapshot"]["packages"].pop("statsmodels")
    _write_result_index(tmp_path, entries)

    audit = audit_enrichment_layer_closure(tmp_path)

    assert audit["status"] == "blocked"
    assert "gene_set_resource_manifest_missing:ora-formal:missing-sets" in audit["blockers"]
    assert "gsea_preranked_dependency_snapshot_not_passed:gsea-formal" in audit["blockers"]
    assert "gsea_dependency_missing_package_status:gsea-formal:statsmodels" in audit["blockers"]


def _complete_layer_fixture(
    root: Path,
    *,
    semantics: str = "formal_computed_result",
    source_semantics: str = "formal_computed_result",
    imported_warning: bool = False,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    deg_table = _write_deg_table(root)
    ora_table = _write_ora_table(root)
    gsea_table = _write_gsea_table(root)
    _write_gene_set_registry(root)
    _write_task_log(root, "ora", "run-ora")
    _write_task_log(root, "gsea", "run-gsea")
    warnings = ["imported_derived_result_not_biomedpilot_formal_recomputed_result"] if imported_warning else []
    _write_result_index(
        root,
        [
            _deg_entry(deg_table, semantics=source_semantics),
            _ora_entry(ora_table, semantics=semantics, source_semantics=source_semantics, warnings=warnings),
            _gsea_entry(gsea_table, semantics=semantics, source_semantics=source_semantics, warnings=warnings),
        ],
    )


def _write_deg_table(root: Path) -> Path:
    path = root / "results" / "tables" / "deg.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [f"GENE{i}\tGENE{i}\t{2.0 if i <= 6 else -1.5}\t0.01\t0.02" for i in range(1, 13)]
    path.write_text("feature_id\tgene_symbol\tlog2_fold_change\tp_value\tadjusted_p_value\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def _write_ora_table(root: Path) -> Path:
    path = root / "results" / "tables" / "ora.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "term_id\tterm_name\tgene_set_size\toverlap_count\toverlap_genes\tbackground_size\tselected_gene_count\tp_value\tadjusted_p_value\tenrichment_ratio\tsource_gene_list\twarnings\n"
        "TERM_POS\tPositive\t4\t2\tGENE1;GENE2\t12\t6\t0.001\t0.003\t6\tselected\t\n",
        encoding="utf-8",
    )
    return path


def _write_gsea_table(root: Path) -> Path:
    path = root / "results" / "tables" / "gsea.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "term_id\tterm_name\tset_size\toverlap_size\tenrichment_score\tnormalized_enrichment_score\tp_value\tadjusted_p_value\tleading_edge_genes\trank_metric\twarnings\n"
        "TERM_POS\tPositive\t4\t4\t0.8\t1.6\t0.01\t0.02\tGENE1;GENE2\tsigned_log10_fdr_by_log2fc\t\n"
        "TERM_NEG\tNegative\t4\t4\t-0.7\t-1.4\t0.03\t0.2\tGENE8;GENE9\tsigned_log10_fdr_by_log2fc\t\n",
        encoding="utf-8",
    )
    return path


def _write_gene_set_registry(root: Path) -> None:
    gmt = root / "user_data" / "bioinformatics" / "gene_sets" / "custom" / "sets.gmt"
    gmt.parent.mkdir(parents=True, exist_ok=True)
    gmt.write_text("TERM_POS\tPositive\tGENE1\tGENE2\tGENE3\tGENE4\nTERM_NEG\tNegative\tGENE8\tGENE9\tGENE10\tGENE11\n", encoding="utf-8")
    registry = root / "user_data" / "bioinformatics" / "gene_sets" / "gene_set_registry.json"
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.gene_set_registry.v1",
                "resources": [
                    {
                        "resource_id": "sets",
                        "name": "sets",
                        "collection_type": "Custom",
                        "species": "unknown",
                        "gene_id_type": "symbol",
                        "status": "available",
                        "local_path": str(gmt.relative_to(root)),
                        "source": "user_import",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_task_log(root: Path, task: str, run_id: str) -> None:
    task_log = root / "analysis_runs" / task / run_id / "task_run.json"
    task_log.parent.mkdir(parents=True, exist_ok=True)
    task_log.write_text(json.dumps({"task_run_id": run_id, "status": "completed"}), encoding="utf-8")


def _deg_entry(table: Path, *, semantics: str) -> dict[str, object]:
    return ResultIndexEntry(
        result_id="deg-source",
        task_run_id="run-deg",
        task_type="deg",
        result_semantics=semantics,
        input_package_id="deg-input-1",
        source_dataset_id="dataset-1",
        source_repository_manifest="standardized_data/repositories/repository_manifest.json",
        parameters_manifest={"gene_id_type": "symbol"},
        engine_name="controlled_deg_mvp",
        engine_version="0.1.0",
        dependency_snapshot={"status": "passed", "packages": {"numpy": {"version": "n"}, "pandas": {"version": "p"}, "scipy": {"version": "s"}, "statsmodels": {"version": "sm"}}},
        output_artifacts=({"artifact_type": "deg_result_table", "path": _relative(table)},),
        validation_status="passed",
    ).to_dict()


def _ora_entry(table: Path, *, semantics: str, source_semantics: str, warnings: list[str]) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "result_id": "ora-formal",
        "task_run_id": "run-ora",
        "task_type": "ora_enrichment",
        "result_semantics": semantics,
        "input_package_id": "ora-input-1",
        "ora_input_id": "ora-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
        "source_deg_result_id": "deg-source",
        "source_result_semantics": source_semantics,
        "gene_set_resource_id": "sets",
        "parameters_manifest": {"ora_parameter_id": "ora-params", "gene_set_resource_id": "sets", "test_method": "hypergeometric", "multiple_testing_policy": "benjamini_hochberg", "selected_gene_rule": "adjusted_p_value_and_abs_log2fc", "background_universe_rule": "source_deg_detected_genes", "fdr_threshold": 0.05},
        "engine_name": "python_scipy_statsmodels_ora_mvp",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": "passed", "packages": {"scipy": {"version": "s"}, "statsmodels": {"version": "sm"}}, "blockers": []},
        "output_artifacts": [{"artifact_type": "ora_result_table", "path": _relative(table)}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": warnings,
        "blockers": [],
        "log_artifacts": [{"artifact_type": "controlled_ora_task_run_log", "path": "analysis_runs/ora/run-ora/task_run.json"}],
        "failure_reason": "",
        "created_at": now,
        "updated_at": now,
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }


def _gsea_entry(table: Path, *, semantics: str, source_semantics: str, warnings: list[str]) -> dict[str, object]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "result_id": "gsea-formal",
        "task_run_id": "run-gsea",
        "task_type": "gsea_preranked",
        "result_semantics": semantics,
        "input_package_id": "gsea-input-1",
        "gsea_input_id": "gsea-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "standardized_data/repositories/repository_manifest.json",
        "source_deg_result_id": "deg-source",
        "source_result_semantics": source_semantics,
        "gene_set_resource_id": "sets",
        "parameters_manifest": {"gsea_parameter_id": "gsea-params", "gene_set_resource_id": "sets", "rank_metric": "signed_log10_fdr_by_log2fc", "permutation_type": "gene_set", "permutation_count": 100, "random_seed": 1, "fdr_threshold": 0.25},
        "engine_name": "python_preranked_gsea_mvp",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": "passed", "packages": {"numpy": {"version": "n"}, "pandas": {"version": "p"}, "scipy": {"version": "s"}, "statsmodels": {"version": "sm"}}, "blockers": []},
        "output_artifacts": [{"artifact_type": "gsea_result_table", "path": _relative(table)}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": warnings,
        "blockers": [],
        "log_artifacts": [{"artifact_type": "controlled_gsea_task_run_log", "path": "analysis_runs/gsea/run-gsea/task_run.json"}],
        "failure_reason": "",
        "created_at": now,
        "updated_at": now,
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }


def _relative(path: Path) -> str:
    return str(path.relative_to(path.parents[2]))


def _load_entries(root: Path) -> list[dict[str, object]]:
    payload = json.loads((root / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8"))
    return [entry for entry in payload["results"] if isinstance(entry, dict)]


def _write_result_index(root: Path, entries: list[dict[str, object]]) -> None:
    path = root / "results" / "summaries" / "result_index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": RESULT_INDEX_SCHEMA_VERSION, "results": entries}), encoding="utf-8")
