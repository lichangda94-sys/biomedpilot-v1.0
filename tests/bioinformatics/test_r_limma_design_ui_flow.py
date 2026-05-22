from __future__ import annotations

import json
import os
from pathlib import Path

from app.bioinformatics.analysis_ui.state import build_analysis_center_state
from app.bioinformatics.deg_engine.r_limma_confirmation import save_r_limma_parameter_confirmation
from app.bioinformatics.deg_engine.r_limma_design import save_r_limma_design_config
from app.bioinformatics.deg_engine.rscript_adapter import run_r_limma_rscript_execution


def test_limma_design_config_confirmation_flow_enables_rscript_action(tmp_path: Path, monkeypatch) -> None:
    _write_standardized_state(tmp_path)
    monkeypatch.setattr(
        "app.bioinformatics.analysis_ui.state.detect_r_limma_runtime_capabilities",
        lambda timeout_seconds=5: _runtime_detection(),
    )

    initial = build_analysis_center_state(tmp_path)
    assert _action(initial, "r_limma_design_config")["enabled"] is True
    assert _action(initial, "formal_deg_limma_rscript")["enabled"] is False
    assert "multi_factor_design_config_missing" in _action(initial, "formal_deg_limma_rscript")["disabled_reason"]

    design = save_r_limma_design_config(tmp_path, initial["limma_rscript_gate"]["deg_ready_package"])
    assert design["status"] == "confirmed"
    assert design["contrast"]["case_samples"] == ["case_1", "case_2"]
    assert design["contrast"]["control_samples"] == ["control_1", "control_2"]

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
    )
    assert confirmation["status"] == "confirmed"

    confirmed = build_analysis_center_state(tmp_path)
    assert _action(confirmed, "r_limma_parameter_confirmation")["state"] == "confirmed"
    action = _action(confirmed, "formal_deg_limma_rscript")
    assert action["enabled"] is True
    assert action["button_behavior"] == "enabled_b25_2_audited_limma_rscript_only"

    fake_rscript = _fake_rscript(tmp_path)
    current_gate = confirmed["limma_rscript_gate"]
    parameter_manifest = confirmation["parameter_manifest"]
    output_plan = confirmation["output_plan"]
    result = run_r_limma_rscript_execution(
        tmp_path,
        expression_table_path=parameter_manifest["expression_table_path"],
        sample_group_map=parameter_manifest["sample_group_map"],
        case_group=parameter_manifest["case_group"],
        control_group=parameter_manifest["control_group"],
        multi_factor_preflight=current_gate["multi_factor_preflight"],
        parameters_manifest=parameter_manifest,
        rscript_path=str(fake_rscript),
        external_capabilities=current_gate["external_capabilities"],
        dependency_snapshot=current_gate["dependency_snapshot"],
        result_id=output_plan["result_id"],
        task_run_id=output_plan["task_run_id"],
        input_package_id=parameter_manifest["input_package_id"],
    )
    assert result["status"] == "passed"
    assert result["result_index_entry"]["result_semantics"] == "formal_computed_result"
    assert result["result_index_entry"]["engine_name"] == "r_limma_rscript_adapter"
    assert result["report_ready_eligible"] is False
    assert result["plot_artifacts"] == []
    assert result["report_artifacts"] == []


def _action(state: dict[str, object], action_id: str) -> dict[str, object]:
    return next(row for row in state["action_rows"] if row["action_id"] == action_id)  # type: ignore[index]


def _runtime_detection() -> dict[str, object]:
    capabilities = {
        "runtime.r.available": {"available": True, "path": "/usr/local/bin/Rscript", "version": "R version 4.4.2"},
        "runtime.bioconductor.available": {"available": True, "version": "1.30.25"},
        "package.r.limma.available": {"available": True, "version": "3.62.2"},
    }
    dependency_snapshot = {
        "status": "passed",
        "runtime": "system_rscript",
        "rscript_path": "/usr/local/bin/Rscript",
        "dependencies": {
            "R": {"installed": True, "path": "/usr/local/bin/Rscript", "version": "R version 4.4.2"},
            "BiocManager": {"installed": True, "version": "1.30.25"},
            "limma": {"installed": True, "version": "3.62.2"},
        },
        "blockers": [],
    }
    return {
        "schema_version": "biomedpilot.r_limma_runtime_detection.v1",
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
        "    'feature_id\\tgene_symbol\\tlogFC\\tAveExpr\\tt\\tP.Value\\tadj.P.Val\\tB\\n'\n"
        "    'ENSG000001\\tGENE1\\t1.2\\t8.5\\t3.0\\t0.01\\t0.04\\t2.5\\n'\n"
        "    'ENSG000002\\tGENE2\\t-0.2\\t4.1\\t-0.5\\t0.4\\t0.7\\t-1.0\\n',\n"
        "    encoding='utf-8',\n"
        ")\n",
        encoding="utf-8",
    )
    os.chmod(path, 0o755)
    return path


def _write_standardized_state(root: Path) -> None:
    matrix = root / "expr.tsv"
    matrix.write_text(
        "feature_id\tcase_1\tcase_2\tcontrol_1\tcontrol_2\n"
        "ENSG000001\t9.0\t9.2\t5.0\t5.1\n"
        "ENSG000002\t4.1\t4.0\t4.3\t4.2\n",
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
