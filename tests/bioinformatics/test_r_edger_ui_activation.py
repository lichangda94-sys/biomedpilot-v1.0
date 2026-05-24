from __future__ import annotations

import json
import os
from pathlib import Path

from app.bioinformatics.analysis_ui.state import build_analysis_center_state
from app.bioinformatics.deg_engine.r_edger_planning import save_r_edger_parameter_confirmation
from app.bioinformatics.deg_engine.r_edger_runtime import run_r_edger_rscript_execution
from app.bioinformatics.deg_engine.r_limma_design import save_r_limma_design_config


def test_edger_design_confirmation_flow_enables_gated_rscript_execution(tmp_path: Path, monkeypatch) -> None:
    _write_standardized_state(tmp_path)
    monkeypatch.setattr(
        "app.bioinformatics.analysis_ui.state.detect_r_edger_runtime_capabilities",
        lambda timeout_seconds=5: _runtime_detection(),
    )

    initial = build_analysis_center_state(tmp_path)
    assert _action(initial, "r_edger_parameter_confirmation")["enabled"] is False
    assert _action(initial, "formal_deg_edger_rscript")["enabled"] is False
    assert "multi_factor_design_config_missing" in _action(initial, "formal_deg_edger_rscript")["disabled_reason"]

    formal_state = initial["developer_diagnostics"]["formal_deg_gate_state"]
    design = save_r_limma_design_config(tmp_path, formal_state["deg_ready_package"])
    assert design["status"] == "confirmed"

    with_design = build_analysis_center_state(tmp_path)
    assert _action(with_design, "r_edger_parameter_confirmation")["enabled"] is True
    assert _action(with_design, "r_edger_parameter_confirmation")["state"] == "requires_user_confirmation"
    assert _action(with_design, "formal_deg_edger_rscript")["enabled"] is False
    assert "r_edger_parameter_confirmation_missing" in _action(with_design, "formal_deg_edger_rscript")["disabled_reason"]

    edger_plan = with_design["r_count_model_plans"]["plans"]["edger"]
    confirmation = save_r_edger_parameter_confirmation(
        tmp_path,
        deg_ready_package=with_design["developer_diagnostics"]["formal_deg_gate_state"]["deg_ready_package"],
        multi_factor_preflight=edger_plan["preflight"],
        dependency_snapshot=edger_plan["runtime_gate"]["dependency_snapshot"],
    )
    assert confirmation["status"] == "confirmed"

    confirmed = build_analysis_center_state(tmp_path)
    assert _action(confirmed, "r_edger_parameter_confirmation")["state"] == "confirmed"
    action = _action(confirmed, "formal_deg_edger_rscript")
    assert action["enabled"] is True
    assert action["button_behavior"] == "enabled_b25_14_audited_edger_rscript_only"
    capability = next(row for row in confirmed["analysis_capability_map"]["rows"] if row["capability_id"] == "deg_edger")
    assert capability["formal_execution_enabled"] is True
    assert capability["can_display_as_completed"] is False

    fake_rscript = _fake_rscript(tmp_path)
    current_plan = confirmed["r_count_model_plans"]["plans"]["edger"]
    parameter_manifest = confirmation["parameter_manifest"]
    output_plan = confirmation["output_plan"]
    result = run_r_edger_rscript_execution(
        tmp_path,
        count_table_path=parameter_manifest["expression_table_path"],
        sample_group_map=parameter_manifest["sample_group_map"],
        case_group=parameter_manifest["case_group"],
        control_group=parameter_manifest["control_group"],
        multi_factor_preflight=current_plan["preflight"],
        parameters_manifest=parameter_manifest,
        rscript_path=str(fake_rscript),
        external_capabilities=current_plan["runtime_gate"]["external_capabilities"],
        dependency_snapshot=current_plan["runtime_gate"]["dependency_snapshot"],
        result_id=output_plan["result_id"],
        task_run_id=output_plan["task_run_id"],
        input_package_id=parameter_manifest["input_package_id"],
        source_dataset_id="edger-ui-activation-fixture",
        source_repository_manifest="standardized_data/repositories/repository_manifest.json",
    )

    assert result["status"] == "passed"
    assert result["result_semantics"] == "formal_computed_result"
    assert result["result_index_entry"]["engine_name"] == "r_edger_rscript_adapter"
    assert {artifact["artifact_type"] for artifact in result["result_index_entry"]["output_artifacts"]} == {"deg_result_table", "edger_result_table"}
    assert result["plot_artifacts"] == []
    assert result["report_artifacts"] == []
    assert result["report_ready_eligible"] is False


def test_edger_rscript_execution_writes_multifactor_design_table(tmp_path: Path) -> None:
    count_table = _write_multifactor_count_table(tmp_path)
    fake_rscript = _fake_rscript_with_design_assertion(tmp_path)
    preflight = _preflight_with_covariates()
    parameter_manifest = {
        "input_package_id": "input-edger-multifactor",
        "deg_ready_package_id": "deg-ready-edger-multifactor",
        "method": "edger",
        "method_family": "edger_count_model",
        "log2fc_threshold": 1.0,
        "fdr_threshold": 0.05,
        "normalization_method": "TMM",
        "test_method": "glm_lrt",
    }
    sample_map = {f"case_{i}": "case" for i in range(1, 4)} | {f"control_{i}": "control" for i in range(1, 4)}

    result = run_r_edger_rscript_execution(
        tmp_path,
        count_table_path=count_table,
        sample_group_map=sample_map,
        case_group="case",
        control_group="control",
        multi_factor_preflight=preflight,
        parameters_manifest=parameter_manifest,
        rscript_path=str(fake_rscript),
        external_capabilities=_runtime_detection()["external_capabilities"],
        dependency_snapshot=_runtime_detection()["dependency_snapshot"],
        result_id="r-edger-multifactor-test",
        task_run_id="task-r-edger-multifactor-test",
        input_package_id="input-edger-multifactor",
    )

    assert result["status"] == "passed"
    manifest_path = tmp_path / "analysis" / "r_deg" / "edger_rscript" / "task-r-edger-multifactor-test" / "command_manifest.json"
    command_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert command_manifest["design_formula"] == "~ batch + age + group"
    assert command_manifest["covariates"] == ["batch", "age"]
    assert command_manifest["test_method"] == "glm_lrt"
    assert result["plot_artifacts"] == []
    assert result["report_artifacts"] == []
    assert result["report_ready_eligible"] is False


def _action(state: dict[str, object], action_id: str) -> dict[str, object]:
    return next(row for row in state["action_rows"] if row["action_id"] == action_id)  # type: ignore[index]


def _runtime_detection() -> dict[str, object]:
    capabilities = {
        "runtime.r.available": {"available": True, "path": "/usr/local/bin/Rscript", "version": "R version 4.4.2"},
        "runtime.bioconductor.available": {"available": True, "version": "1.30.25"},
        "package.r.edger.available": {"available": True, "version": "4.4.2"},
    }
    dependency_snapshot = {
        "status": "passed",
        "runtime": "system_rscript",
        "rscript_path": "/usr/local/bin/Rscript",
        "dependencies": {
            "R": {"installed": True, "path": "/usr/local/bin/Rscript", "version": "R version 4.4.2"},
            "BiocManager": {"installed": True, "version": "1.30.25"},
            "edgeR": {"installed": True, "version": "4.4.2"},
        },
        "blockers": [],
    }
    return {
        "schema_version": "biomedpilot.r_edger_runtime_detection.v1",
        "status": "passed",
        "rscript_path": "/usr/local/bin/Rscript",
        "external_capabilities": capabilities,
        "dependency_snapshot": dependency_snapshot,
        "warnings": [],
        "blockers": [],
    }


def _fake_rscript(tmp_path: Path) -> Path:
    path = tmp_path / "fake_rscript.py"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import pathlib\n"
        "import sys\n"
        "output = pathlib.Path(sys.argv[4])\n"
        "output.write_text(\n"
        "    'feature_id\\tgene_symbol\\tlogFC\\tlogCPM\\tPValue\\tFDR\\tLR\\n'\n"
        "    'ENSG000001\\tGENE1\\t2.1\\t8.4\\t0.001\\t0.01\\t5.2\\n'\n"
        "    'ENSG000002\\tGENE2\\t-1.8\\t7.2\\t0.004\\t0.02\\t4.6\\n',\n"
        "    encoding='utf-8',\n"
        ")\n",
        encoding="utf-8",
    )
    os.chmod(path, 0o755)
    return path


def _fake_rscript_with_design_assertion(tmp_path: Path) -> Path:
    path = tmp_path / "fake_rscript_multifactor.py"
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import csv\n"
        "import pathlib\n"
        "import sys\n"
        "design = pathlib.Path(sys.argv[3])\n"
        "output = pathlib.Path(sys.argv[4])\n"
        "rows = list(csv.DictReader(design.open(encoding='utf-8'), delimiter='\\t'))\n"
        "assert {'sample', 'group', 'batch', 'age'}.issubset(rows[0])\n"
        "output.write_text(\n"
        "    'feature_id\\tgene_symbol\\tlogFC\\tlogCPM\\tPValue\\tFDR\\tLR\\n'\n"
        "    'ENSG000001\\tGENE1\\t2.1\\t8.4\\t0.001\\t0.01\\t5.2\\n',\n"
        "    encoding='utf-8',\n"
        ")\n",
        encoding="utf-8",
    )
    os.chmod(path, 0o755)
    return path


def _write_standardized_state(root: Path) -> None:
    matrix = root / "counts.tsv"
    matrix.write_text(
        "feature_id\tgene_symbol\tcase_1\tcase_2\tcontrol_1\tcontrol_2\n"
        "ENSG000001\tGENE1\t120\t115\t24\t31\n"
        "ENSG000002\tGENE2\t20\t23\t80\t77\n",
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
        _asset("counts", "raw_count_matrix", "expression_repository", matrix, value_type="count"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", group),
    ]
    selection = {"expression": {"asset_id": "counts", "selection_state": "user_confirmed"}}
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


def _write_multifactor_count_table(root: Path) -> Path:
    path = root / "counts_multifactor.tsv"
    path.write_text(
        "feature_id\tgene_symbol\tcase_1\tcase_2\tcase_3\tcontrol_1\tcontrol_2\tcontrol_3\n"
        "ENSG000001\tGENE1\t120\t115\t118\t24\t31\t28\n"
        "ENSG000002\tGENE2\t20\t23\t21\t80\t77\t81\n",
        encoding="utf-8",
    )
    return path


def _preflight_with_covariates() -> dict[str, object]:
    return {
        "status": "design_ready",
        "method": "edger",
        "method_family": "edger_count_model",
        "value_type": "count",
        "value_type_policy": "edger_requires_raw_integer_counts",
        "input_package_id": "input-edger-multifactor",
        "deg_ready_package_id": "deg-ready-edger-multifactor",
        "gene_id_type": "symbol",
        "contrast": {
            "contrast_id": "case_vs_control",
            "factor": "group",
            "case_level": "case",
            "control_level": "control",
            "case_samples": ["case_1", "case_2", "case_3"],
            "control_samples": ["control_1", "control_2", "control_3"],
        },
        "design_config": {
            "primary_factor": "group",
            "case_group": "case",
            "control_group": "control",
            "sample_table": [
                {"sample_id": "case_1", "group": "case", "batch": "b1", "age": 50},
                {"sample_id": "case_2", "group": "case", "batch": "b2", "age": 55},
                {"sample_id": "case_3", "group": "case", "batch": "b1", "age": 65},
                {"sample_id": "control_1", "group": "control", "batch": "b2", "age": 52},
                {"sample_id": "control_2", "group": "control", "batch": "b1", "age": 59},
                {"sample_id": "control_3", "group": "control", "batch": "b2", "age": 70},
            ],
            "covariates": [{"name": "batch", "variable_type": "categorical"}, {"name": "age", "variable_type": "continuous"}],
        },
        "blockers": [],
        "warnings": [],
    }


def _asset(asset_id: str, asset_type: str, repository: str, path: Path, *, value_type: str = "", gene_id_type: str = "symbol") -> dict[str, object]:
    return {
        "asset_id": asset_id,
        "asset_type": asset_type,
        "asset_role": "expression_matrix" if "expression" in asset_type or "count" in asset_type else asset_type,
        "repository": repository,
        "path": str(path),
        "file_path": str(path),
        "validation_status": "passed",
        "analysis_ready": True,
        "expression_value_type": value_type,
        "gene_id_type": gene_id_type,
    }
