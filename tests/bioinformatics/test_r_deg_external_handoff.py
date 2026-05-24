from __future__ import annotations

import csv
import json
from pathlib import Path

from app.bioinformatics.deg_engine.r_backend_handoff import (
    build_r_deg_external_handoff_plan,
    register_r_limma_external_handoff_result,
)


def test_limma_external_handoff_registers_formal_deg_result(tmp_path: Path) -> None:
    result = register_r_limma_external_handoff_result(
        tmp_path,
        multi_factor_preflight=_preflight(),
        external_capabilities=_capabilities(),
        dependency_snapshot=_dependency_snapshot(),
        output_rows=_limma_rows(),
        parameters_manifest={
            "schema_version": "test.r_limma.params.v1",
            "comparison_id": "case-v-control",
            "log2fc_threshold": 1.0,
            "fdr_threshold": 0.05,
        },
        input_package_id="input-r-limma-1",
        source_dataset_id="dataset-r-limma-1",
        source_repository_manifest="manifests/source.json",
        result_id="r-limma-test-1",
        task_run_id="task-r-limma-test-1",
    )

    assert result["status"] == "passed"
    assert result["result_semantics"] == "formal_computed_result"
    assert result["report_ready_eligible"] is False
    assert result["plot_artifacts"] == []
    assert result["report_artifacts"] == []
    assert result["result_index_gate"]["status"] == "passed"

    canonical_table = Path(result["canonical_table_path"])
    limma_table = Path(result["limma_table_path"])
    log_path = Path(result["log_path"])
    result_index = tmp_path / "results" / "summaries" / "result_index.json"
    assert canonical_table.is_file()
    assert limma_table.is_file()
    assert log_path.is_file()
    assert result_index.is_file()

    rows = list(csv.DictReader(canonical_table.open(encoding="utf-8"), delimiter="\t"))
    assert rows[0]["feature_id"] == "ENSG000001"
    assert rows[0]["p_value"] == "0.001"
    assert rows[0]["adjusted_p_value"] == "0.01"
    assert rows[0]["significance_label"] == "upregulated"

    index_payload = json.loads(result_index.read_text(encoding="utf-8"))
    entry = index_payload["results"][0]
    assert entry["result_id"] == "r-limma-test-1"
    assert entry["engine_name"] == "r_limma_external_handoff"
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["report_ready_eligible"] is False
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []
    assert {artifact["artifact_type"] for artifact in entry["output_artifacts"]} == {
        "deg_result_table",
        "limma_result_table",
    }
    assert entry["dependency_snapshot"]["status"] == "passed"
    assert entry["parameters_manifest"]["external_runtime_handoff"] is True


def test_limma_external_handoff_blocks_missing_runtime_without_result_index(tmp_path: Path) -> None:
    result = register_r_limma_external_handoff_result(
        tmp_path,
        multi_factor_preflight=_preflight(),
        external_capabilities={
            "runtime.r.available": {"available": False},
            "runtime.bioconductor.available": {"available": True},
            "package.r.limma.available": {"available": True},
        },
        dependency_snapshot={"status": "blocked", "blockers": ["runtime.r.missing"]},
        output_rows=_limma_rows(),
        input_package_id="input-r-limma-1",
    )

    assert result["status"] == "blocked"
    assert "external_capability_not_available:runtime.r.available" in result["blockers"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_limma_external_handoff_blocks_bad_output_schema_without_formal_result(tmp_path: Path) -> None:
    rows = [
        {
            "feature_id": "ENSG000001",
            "gene_symbol": "GENE1",
            "logFC": 1.2,
            "AveExpr": 8.4,
            "t": 4.2,
            "P.Value": 0.001,
        }
    ]

    result = register_r_limma_external_handoff_result(
        tmp_path,
        multi_factor_preflight=_preflight(),
        external_capabilities=_capabilities(),
        dependency_snapshot=_dependency_snapshot(),
        output_rows=rows,
        input_package_id="input-r-limma-1",
    )

    assert result["status"] == "blocked"
    assert "missing_output_column:adj.P.Val" in result["blockers"]
    assert not (tmp_path / "results" / "summaries" / "result_index.json").exists()


def test_deseq2_and_edger_external_handoff_remain_deferred() -> None:
    deseq2_plan = build_r_deg_external_handoff_plan("DESeq2")
    edger_plan = build_r_deg_external_handoff_plan("edgeR")

    assert deseq2_plan["status"] == "planned_not_enabled"
    assert edger_plan["status"] == "planned_not_enabled"
    assert deseq2_plan["can_register_formal_result"] is False
    assert edger_plan["can_register_formal_result"] is False
    assert "r_deseq2_generic_external_handoff_disabled_use_controlled_rscript_adapter" in deseq2_plan["blockers"]
    assert "r_edger_generic_external_handoff_disabled_use_controlled_rscript_adapter" in edger_plan["blockers"]
    assert "deseq2_rscript_execution_adapter_not_implemented" not in deseq2_plan["blockers"]
    assert "edger_rscript_execution_adapter_not_implemented" not in edger_plan["blockers"]


def _preflight() -> dict[str, object]:
    return {
        "status": "design_ready",
        "method": "limma",
        "method_family": "limma_normalized_expression",
        "input_package_id": "input-r-limma-1",
        "result_semantics": "preflight_only",
        "blockers": [],
        "warnings": [],
    }


def _capabilities() -> dict[str, object]:
    return {
        "runtime.r.available": {"available": True, "version": "4.4.0"},
        "runtime.bioconductor.available": {"available": True, "version": "3.20"},
        "package.r.limma.available": {"available": True, "version": "3.62.0"},
    }


def _dependency_snapshot() -> dict[str, object]:
    return {
        "status": "passed",
        "runtime": "external_r",
        "dependencies": {
            "R": {"installed": True, "version": "4.4.0"},
            "Bioconductor": {"installed": True, "version": "3.20"},
            "limma": {"installed": True, "version": "3.62.0"},
        },
        "blockers": [],
    }


def _limma_rows() -> list[dict[str, object]]:
    return [
        {
            "feature_id": "ENSG000001",
            "gene_symbol": "GENE1",
            "logFC": 1.5,
            "AveExpr": 8.4,
            "t": 4.2,
            "P.Value": 0.001,
            "adj.P.Val": 0.01,
            "B": 5.0,
        },
        {
            "feature_id": "ENSG000002",
            "gene_symbol": "GENE2",
            "logFC": -0.4,
            "AveExpr": 7.1,
            "t": -1.1,
            "P.Value": 0.2,
            "adj.P.Val": 0.5,
            "B": -2.0,
        },
    ]
