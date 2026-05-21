from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.deg_engine.confirmation import (
    CONFIRMATION_PATH,
    load_deg_parameter_confirmation,
    save_deg_parameter_confirmation,
    validate_deg_parameter_confirmation,
)


def test_deg_parameter_confirmation_records_user_review_surface(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    dependency = _dependency()

    confirmation = save_deg_parameter_confirmation(
        tmp_path,
        method="mann_whitney",
        log2fc_threshold=0.75,
        p_value_threshold=0.01,
        fdr_threshold=0.1,
        dependency_snapshot=dependency,
    )

    assert confirmation["status"] == "confirmed"
    manifest = confirmation["parameter_manifest"]
    summary = confirmation["user_confirmation_summary"]
    assert manifest["method"] == "mann_whitney"
    assert manifest["log2fc_threshold"] == 0.75
    assert manifest["p_value_threshold"] == 0.01
    assert manifest["fdr_threshold"] == 0.1
    assert summary["comparison"]["case_sample_count"] == 2
    assert summary["comparison"]["control_sample_count"] == 2
    assert summary["value_type_policy"]["value_type"] == "count"
    assert summary["dependency_versions"]["scipy"] == "1.17.1"
    assert confirmation["output_plan"]["task_run_id"].startswith("task-run-")
    assert confirmation["output_plan"]["result_index_registry_path"] == "results/summaries/result_index.json"
    assert (tmp_path / CONFIRMATION_PATH).is_file()
    assert load_deg_parameter_confirmation(tmp_path)["status"] == "confirmed"

    gate = validate_deg_parameter_confirmation(confirmation, parameter_manifest=manifest, dependency_snapshot=dependency)
    assert gate["status"] == "passed"


def test_deg_parameter_confirmation_blocks_stale_method_or_dependency(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    dependency = _dependency()
    confirmation = save_deg_parameter_confirmation(tmp_path, method="welch_t_test", dependency_snapshot=dependency)
    manifest = dict(confirmation["parameter_manifest"])
    manifest["method"] = "mann_whitney"
    changed_dependency = _dependency()
    changed_dependency["packages"]["scipy"]["version"] = "2.0.0"

    gate = validate_deg_parameter_confirmation(confirmation, parameter_manifest=manifest, dependency_snapshot=changed_dependency)

    assert gate["status"] == "blocked"
    assert "formal_deg_confirmation_mismatch:method" in gate["blockers"]
    assert "formal_deg_confirmation_dependency_version_mismatch:scipy" in gate["blockers"]


def _dependency() -> dict[str, object]:
    return {
        "status": "passed",
        "engine_candidate": "python_scipy_statsmodels",
        "blockers": [],
        "packages": {
            "numpy": {"available": True, "version": "2.4.6"},
            "pandas": {"available": True, "version": "3.0.3"},
            "scipy": {"available": True, "version": "1.17.1"},
            "statsmodels": {"available": True, "version": "0.14.6"},
        },
    }


def _write_fixture(root: Path) -> None:
    matrix = root / "matrix.tsv"
    matrix.write_text("gene\tcase1\tcase2\tctrl1\tctrl2\nTP53\t10\t12\t5\t6\nEGFR\t2\t2\t8\t9\n", encoding="utf-8")
    sample = root / "sample.tsv"
    sample.write_text("sample_id\tgroup\ncase1\tcase\ncase2\tcase\nctrl1\tcontrol\nctrl2\tcontrol\n", encoding="utf-8")
    group = root / "group.json"
    group.write_text(json.dumps({"group_design": {"sample_group_assignments": {"case1": "case", "case2": "case", "ctrl1": "control", "ctrl2": "control"}}}), encoding="utf-8")
    assets = [
        _asset("expr", "raw_count_matrix", "expression_repository", matrix, value_type="count"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", group),
    ]
    selection = {"expression": {"asset_id": "expr", "selection_state": "user_confirmed"}}
    payload = {"schema_version": "biomedpilot.repository_manifest.v1", "assets": assets, "default_asset_selection": selection}
    registry = {"schema_version": "biomedpilot.standardized_assets_registry.v2", "assets": assets, "default_asset_selection": selection}
    repo_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.write_text(json.dumps(payload), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")


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
