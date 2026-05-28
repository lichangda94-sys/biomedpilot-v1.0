from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.bioinformatics.enrichment import (
    build_enrichment_background_identifier_gate,
    build_enrichment_production_preview,
    build_enrichment_production_result_schema_gate,
    build_enrichment_resource_lock,
    build_enrichment_statistical_policy,
    build_ora_gene_set_resource_gate,
    create_enrichment_production_audit_package,
)
from app.bioinformatics.enrichment.input_gate import build_ora_input_gate
from app.bioinformatics.enrichment.models import ORA_RESULT_TASK_TYPE
from app.bioinformatics.enrichment.parameter_gate import build_ora_parameter_manifest
from app.bioinformatics.gene_set_resources import import_gmt_file, select_gene_set
from app.bioinformatics.gsea.models import GSEA_TASK_TYPE
from app.bioinformatics.gsea.result_schema import build_gsea_result_schema_gate
from app.bioinformatics.results.registry import register_result


def test_enrichment_resource_lock_background_and_statistical_policy_pass_for_releasebuild_ora(tmp_path: Path) -> None:
    deg_table = _write_deg_table(tmp_path)
    _register_deg_result(tmp_path, deg_table)
    resource = _import_resource(tmp_path)
    select_gene_set(tmp_path, str(resource["resource_id"]))

    input_gate = build_ora_input_gate(tmp_path, result_id="deg-1")
    gene_set_gate = build_ora_gene_set_resource_gate(tmp_path, resource_id=str(resource["resource_id"]), expected_gene_id_type="symbol")
    parameter_gate = build_ora_parameter_manifest(input_gate, gene_set_gate, min_gene_set_size=1)

    lock = build_enrichment_resource_lock(ORA_RESULT_TASK_TYPE, gene_set_gate)
    background = build_enrichment_background_identifier_gate(ORA_RESULT_TASK_TYPE, input_gate, gene_set_gate)
    policy = build_enrichment_statistical_policy(ORA_RESULT_TASK_TYPE, parameter_gate)

    assert lock["status"] == "passed"
    assert lock["checksum"]
    assert lock["file_size"] > 0
    assert background["status"] == "passed"
    assert background["background_count"] == 4
    assert policy["status"] == "passed"
    assert policy["statistical_boundary"] == "statistical_research_only_no_pathway_activation_or_clinical_conclusion"


def test_enrichment_production_result_schema_and_audit_package_require_formal_result(tmp_path: Path) -> None:
    resource = _import_resource(tmp_path)
    table = _write_ora_table(tmp_path)
    log = tmp_path / "analysis_runs" / "ora" / "ora-run-1" / "task_run.json"
    log.parent.mkdir(parents=True)
    log.write_text('{"status":"completed"}\n', encoding="utf-8")
    register_result(tmp_path, _ora_entry(table, log, resource_id=str(resource["resource_id"])))

    schema = build_enrichment_production_result_schema_gate(tmp_path, analysis_type=ORA_RESULT_TASK_TYPE, result_id="ora-1")
    package = create_enrichment_production_audit_package(tmp_path, analysis_type=ORA_RESULT_TASK_TYPE, result_id="ora-1")

    assert schema["status"] == "passed"
    assert schema["table_validation"]["status"] == "passed"
    assert package["status"] == "enrichment_production_audit_package_created"
    package_path = Path(package["package_path"])
    assert (package_path / "enrichment_production_audit_package_manifest.json").is_file()
    assert (package_path / "tables" / table.name).is_file()
    assert (package_path / "manifests" / "result_index_snapshot.json").is_file()
    assert package["report_ready_eligible"] is False

    imported = _ora_entry(table, log, result_id="ora-imported", resource_id=str(resource["resource_id"]))
    imported["result_semantics"] = "imported_external_result"
    imported["source_result_semantics"] = "imported_external_result"
    register_result(tmp_path, imported)
    blocked = build_enrichment_production_result_schema_gate(tmp_path, analysis_type=ORA_RESULT_TASK_TYPE, result_id="ora-imported")
    assert blocked["status"] == "blocked"
    assert "enrichment_production_requires_formal_result:imported_external_result" in blocked["blockers"]


def test_enrichment_production_preview_surfaces_ora_and_gsea_blockers(tmp_path: Path) -> None:
    ora_state = {
        "input_gate": {"status": "blocked", "source_gene_id_type": "symbol", "blockers": ["ora_source_deg_result_missing"], "warnings": []},
        "gene_set_gate": {"status": "blocked", "blockers": ["ora_gene_set_resource_missing"], "warnings": []},
        "parameter_gate": {"status": "blocked", "blockers": ["ora_parameter_missing_source_result"], "warnings": []},
        "result_schema_gate": {"status": "blocked", "blockers": ["ora_parameter_gate_not_passed"], "warnings": []},
    }
    gsea_state = {
        "input_gate": {"status": "blocked", "source_gene_id_type": "symbol", "ranked_gene_count": 0, "blockers": ["gsea_source_result_missing"], "warnings": []},
        "gene_set_gate": {"status": "blocked", "blockers": ["gsea_gene_set_resource_missing"], "warnings": []},
        "parameter_gate": {"status": "blocked", "blockers": ["gsea_parameter_missing_source_result"], "warnings": []},
        "result_schema_gate": build_gsea_result_schema_gate(parameter_manifest={}),
    }

    preview = build_enrichment_production_preview(tmp_path, ora_state=ora_state, gsea_state=gsea_state)

    assert preview["status"] == "blocked"
    assert preview["action_boundary"] == "preview_only_no_package_write_no_report_ready_upgrade"
    gate_text = "\n".join(str(row) for row in preview["gate_rows"])
    assert "ORA resource lock" in gate_text
    assert "GSEA production result schema" in gate_text
    assert "ora_source_deg_result_missing" in preview["blockers"]
    assert "gsea_source_result_missing" in preview["blockers"]


def _write_deg_table(root: Path) -> Path:
    path = root / "results" / "tables" / "deg.tsv"
    path.parent.mkdir(parents=True)
    path.write_text(
        "feature_id\tgene_symbol\tlog2_fold_change\tp_value\tadjusted_p_value\tsignificance_label\n"
        "TP53\tTP53\t2.0\t0.001\t0.01\tup\n"
        "BAX\tBAX\t1.5\t0.002\t0.02\tup\n"
        "BRCA1\tBRCA1\t0.1\t0.4\t0.5\tnot_significant\n"
        "STAT1\tSTAT1\t-1.8\t0.003\t0.03\tdown\n",
        encoding="utf-8",
    )
    return path


def _write_ora_table(root: Path) -> Path:
    path = root / "results" / "tables" / "ora.tsv"
    path.parent.mkdir(parents=True)
    path.write_text(
        "term_id\tterm_name\tgene_set_size\toverlap_count\toverlap_genes\tbackground_size\tselected_gene_count\tp_value\tadjusted_p_value\tenrichment_ratio\tsource_gene_list\twarnings\n"
        "DNA_DAMAGE\tDNA damage\t3\t2\tBAX;TP53\t4\t3\t0.01\t0.02\t2.6\tadjusted_p_value_and_abs_log2fc\t\n",
        encoding="utf-8",
    )
    return path


def _import_resource(root: Path) -> dict[str, object]:
    gmt = root / "fixture.gmt"
    gmt.write_text("DNA_DAMAGE\tcurated\tTP53\tBAX\tBRCA1\nINTERFERON\tcurated\tSTAT1\tIRF1\n", encoding="utf-8")
    return import_gmt_file(
        root,
        gmt,
        {
            "name": "Fixture GMT",
            "collection_type": "Custom",
            "species": "human",
            "gene_id_type": "symbol",
            "source_name": "B100a fixture",
            "source_url": "https://example.test/fixture.gmt",
            "license_note": "test-only fixture",
            "version": "2026-b100a",
        },
    )["resource"]


def _register_deg_result(root: Path, table: Path) -> None:
    register_result(
        root,
        {
            "result_id": "deg-1",
            "task_run_id": "deg-run-1",
            "task_type": "deg",
            "result_semantics": "formal_computed_result",
            "input_package_id": "deg-input-1",
            "source_dataset_id": "dataset-1",
            "source_repository_manifest": "manifest.json",
            "parameters_manifest": {"gene_id_type": "symbol"},
            "engine_name": "fixture",
            "engine_version": "1",
            "dependency_snapshot": {"status": "passed"},
            "output_artifacts": [{"artifact_type": "deg_result_table", "path": str(table.relative_to(root))}],
            "plot_artifacts": [],
            "report_artifacts": [],
            "validation_status": "passed",
            "warnings": [],
            "blockers": [],
            "log_artifacts": [],
            "failure_reason": "",
            "created_at": _now(),
            "updated_at": _now(),
            "schema_version": "biomedpilot.result_index_entry.v1",
            "report_ready_eligible": False,
            "migration_status": "native_v2",
        },
    )


def _ora_entry(table: Path, log: Path, *, result_id: str = "ora-1", resource_id: str = "fixture") -> dict[str, object]:
    root = table.parents[2]
    return {
        "result_id": result_id,
        "task_run_id": "ora-run-1",
        "task_type": ORA_RESULT_TASK_TYPE,
        "result_semantics": "formal_computed_result",
        "input_package_id": "ora-input-1",
        "ora_input_id": "ora-input-1",
        "source_dataset_id": "dataset-1",
        "source_repository_manifest": "manifest.json",
        "source_deg_result_id": "deg-1",
        "source_result_semantics": "formal_computed_result",
        "gene_set_resource_id": resource_id,
        "parameters_manifest": {"ora_parameter_id": "params-1", "multiple_testing_policy": "BH"},
        "engine_name": "python_scipy_statsmodels_ora_mvp",
        "engine_version": "0.1.0",
        "dependency_snapshot": {"status": "passed"},
        "output_artifacts": [{"artifact_type": "ora_result_table", "path": str(table.relative_to(root))}],
        "plot_artifacts": [],
        "report_artifacts": [],
        "validation_status": "passed",
        "warnings": [],
        "blockers": [],
        "log_artifacts": [{"artifact_type": "controlled_ora_task_run_log", "path": str(log.relative_to(root))}],
        "failure_reason": "",
        "created_at": _now(),
        "updated_at": _now(),
        "schema_version": "biomedpilot.result_index_entry.v1",
        "report_ready_eligible": False,
        "migration_status": "native_v2",
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
