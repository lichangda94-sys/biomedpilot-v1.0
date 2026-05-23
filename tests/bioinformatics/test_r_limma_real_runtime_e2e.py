from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from app.bioinformatics.analysis_ui.state import build_analysis_center_state
from app.bioinformatics.deg_engine.r_limma_confirmation import save_r_limma_parameter_confirmation
from app.bioinformatics.deg_engine.r_limma_design import save_r_limma_design_config
from app.bioinformatics.deg_engine.rscript_adapter import detect_r_limma_runtime_capabilities, run_r_limma_rscript_execution


def test_real_rscript_limma_ui_gated_e2e_registers_formal_result(tmp_path: Path) -> None:
    runtime = detect_r_limma_runtime_capabilities(timeout_seconds=10)
    if runtime["status"] != "passed":
        pytest.skip(f"Rscript/limma runtime unavailable: {runtime.get('blockers')}")

    _write_standardized_state(tmp_path)
    initial = build_analysis_center_state(tmp_path)
    assert _action(initial, "formal_deg_limma_rscript")["enabled"] is False
    assert "multi_factor_design_config_missing" in _action(initial, "formal_deg_limma_rscript")["disabled_reason"]

    design = save_r_limma_design_config(tmp_path, initial["limma_rscript_gate"]["deg_ready_package"])
    assert design["status"] == "confirmed"

    with_design = build_analysis_center_state(tmp_path)
    assert _action(with_design, "r_limma_parameter_confirmation")["enabled"] is True
    assert _action(with_design, "formal_deg_limma_rscript")["enabled"] is False
    assert "r_limma_parameter_confirmation_missing" in _action(with_design, "formal_deg_limma_rscript")["disabled_reason"]

    limma_gate = with_design["limma_rscript_gate"]
    confirmation = save_r_limma_parameter_confirmation(
        tmp_path,
        deg_ready_package=limma_gate["deg_ready_package"],
        multi_factor_preflight=limma_gate["multi_factor_preflight"],
        dependency_snapshot=limma_gate["dependency_snapshot"],
        log2fc_threshold=0.5,
        fdr_threshold=0.5,
    )
    assert confirmation["status"] == "confirmed"

    confirmed = build_analysis_center_state(tmp_path)
    assert _action(confirmed, "formal_deg_limma_rscript")["enabled"] is True

    parameter_manifest = confirmation["parameter_manifest"]
    output_plan = confirmation["output_plan"]
    result = run_r_limma_rscript_execution(
        tmp_path,
        expression_table_path=parameter_manifest["expression_table_path"],
        sample_group_map=parameter_manifest["sample_group_map"],
        case_group=parameter_manifest["case_group"],
        control_group=parameter_manifest["control_group"],
        multi_factor_preflight=confirmed["limma_rscript_gate"]["multi_factor_preflight"],
        parameters_manifest=parameter_manifest,
        rscript_path=str(runtime["rscript_path"]),
        external_capabilities=confirmed["limma_rscript_gate"]["external_capabilities"],
        dependency_snapshot=confirmed["limma_rscript_gate"]["dependency_snapshot"],
        result_id=output_plan["result_id"],
        task_run_id=output_plan["task_run_id"],
        input_package_id=parameter_manifest["input_package_id"],
        source_dataset_id="real-rscript-fixture",
        source_repository_manifest="standardized_data/repositories/repository_manifest.json",
    )

    assert result["status"] == "passed"
    entry = result["result_index_entry"]
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["engine_name"] == "r_limma_rscript_adapter"
    assert entry["report_ready_eligible"] is False
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []
    assert {artifact["artifact_type"] for artifact in entry["output_artifacts"]} == {"deg_result_table", "limma_result_table"}
    assert {artifact["artifact_type"] for artifact in entry["log_artifacts"]} >= {
        "r_limma_external_handoff_log",
        "r_limma_rscript_command_manifest",
        "r_limma_rscript_command_log",
    }

    canonical_rows = list(csv.DictReader(Path(result["handoff"]["canonical_table_path"]).open(encoding="utf-8"), delimiter="\t"))
    assert len(canonical_rows) == 4
    assert all(row["p_value"] for row in canonical_rows)
    assert all(row["adjusted_p_value"] for row in canonical_rows)

    index_payload = json.loads((tmp_path / "results" / "summaries" / "result_index.json").read_text(encoding="utf-8"))
    assert index_payload["results"][0]["result_id"] == output_plan["result_id"]
    capability_rows = {row["capability_id"]: row for row in build_analysis_center_state(tmp_path)["analysis_capability_map"]["rows"]}
    assert capability_rows["deg_deseq2"]["formal_execution_enabled"] is False
    assert capability_rows["deg_edger"]["formal_execution_enabled"] is False


def _action(state: dict[str, object], action_id: str) -> dict[str, object]:
    return next(row for row in state["action_rows"] if row["action_id"] == action_id)  # type: ignore[index]


def _write_standardized_state(root: Path) -> None:
    matrix = root / "expr.tsv"
    matrix.write_text(
        "feature_id\tgene_symbol\tcase_1\tcase_2\tcontrol_1\tcontrol_2\n"
        "ENSG000001\tGENE1\t9.2\t9.0\t5.0\t5.2\n"
        "ENSG000002\tGENE2\t4.1\t4.0\t4.3\t4.1\n"
        "ENSG000003\tGENE3\t2.1\t2.3\t7.0\t7.2\n"
        "ENSG000004\tGENE4\t6.2\t6.4\t6.1\t6.3\n",
        encoding="utf-8",
    )
    sample = root / "sample.tsv"
    sample.write_text(
        "sample_id\tgroup\n"
        "case_1\tcase\n"
        "case_2\tcase\n"
        "control_1\tcontrol\n"
        "control_2\tcontrol\n",
        encoding="utf-8",
    )
    group = root / "group.json"
    group.write_text(
        json.dumps(
            {
                "group_design": {
                    "sample_group_assignments": {
                        "case_1": "case",
                        "case_2": "case",
                        "control_1": "control",
                        "control_2": "control",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    assets = [
        _asset("expr", "normalized_expression_matrix", "expression_repository", matrix, value_type="TPM"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", group),
    ]
    selection = {"expression": {"asset_id": "expr", "selection_state": "user_confirmed"}}
    repository_manifest = {
        "schema_version": "biomedpilot.repository_manifest.v1",
        "assets": assets,
        "default_asset_selection": selection,
        "source_state": {"source_state_hash": "source-1"},
    }
    registry = {
        "schema_version": "biomedpilot.standardized_assets_registry.v2",
        "assets": assets,
        "default_asset_selection": selection,
    }
    repo_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.write_text(json.dumps(repository_manifest), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")


def _asset(asset_id: str, asset_type: str, repository: str, path: Path, *, value_type: str = "", gene_id_type: str = "symbol") -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_role": "expression_matrix" if "expression" in asset_type else asset_type,
        "repository": repository,
        "path": str(path),
        "file_path": str(path),
        "validation_status": "passed",
        "analysis_ready": True,
        "expression_value_type": value_type,
        "gene_id_type": gene_id_type,
    }
