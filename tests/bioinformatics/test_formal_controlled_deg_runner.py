from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from app.bioinformatics.deg_engine import run_formal_controlled_deg, save_deg_parameter_confirmation
from app.bioinformatics.results.registry import load_registry


def test_formal_controlled_deg_runner_registers_result_index_v2(tmp_path: Path, monkeypatch) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tcase1\tcase2\tctrl1\tctrl2\nTP53\t10\t12\t5\t6\nEGFR\t2\t2\t8\t9\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\ncase1\tcase\ncase2\tcase\nctrl1\tcontrol\nctrl2\tcontrol\n", encoding="utf-8")
    group = tmp_path / "group.json"
    group.write_text(json.dumps({"group_design": {"sample_group_assignments": {"case1": "case", "case2": "case", "ctrl1": "control", "ctrl2": "control"}}}), encoding="utf-8")
    _write_standardized_state(
        tmp_path,
        [
            _asset("expr", "raw_count_matrix", "expression_repository", matrix, value_type="count", gene_id_type="symbol"),
            _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
            _asset("group", "group_design", "group_design_repository", group),
        ],
        default_expression="expr",
    )
    _patch_backend(monkeypatch)
    dependency = {"status": "passed", "engine_candidate": "python_scipy_statsmodels", "blockers": [], "packages": {}}
    confirmation = save_deg_parameter_confirmation(tmp_path, dependency_snapshot=dependency)
    assert confirmation["status"] == "confirmed"

    result = run_formal_controlled_deg(
        tmp_path,
        dependency_snapshot=dependency,
    )

    assert result["status"] == "passed"
    registry = load_registry(tmp_path)
    entry = registry["results"][0]
    assert entry["result_semantics"] == "formal_computed_result"
    assert entry["input_package_id"]
    assert entry["parameters_manifest"]["method"] == "welch_t_test"
    assert entry["dependency_snapshot"]["status"] == "passed"
    assert entry["validation_status"] == "passed"
    assert entry["report_ready_eligible"] is False
    assert entry["plot_artifacts"] == []
    assert entry["report_artifacts"] == []
    assert (tmp_path / entry["output_artifacts"][0]["path"]).is_file()


def test_formal_controlled_deg_runner_requires_user_parameter_confirmation(tmp_path: Path, monkeypatch) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tcase1\tcase2\tctrl1\tctrl2\nTP53\t10\t12\t5\t6\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\ncase1\tcase\ncase2\tcase\nctrl1\tcontrol\nctrl2\tcontrol\n", encoding="utf-8")
    group = tmp_path / "group.json"
    group.write_text(json.dumps({"group_design": {"sample_group_assignments": {"case1": "case", "case2": "case", "ctrl1": "control", "ctrl2": "control"}}}), encoding="utf-8")
    _write_standardized_state(
        tmp_path,
        [
            _asset("expr", "raw_count_matrix", "expression_repository", matrix, value_type="count", gene_id_type="symbol"),
            _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
            _asset("group", "group_design", "group_design_repository", group),
        ],
        default_expression="expr",
    )
    _patch_backend(monkeypatch)

    result = run_formal_controlled_deg(
        tmp_path,
        dependency_snapshot={"status": "passed", "engine_candidate": "python_scipy_statsmodels", "blockers": [], "packages": {}},
    )

    assert result["status"] == "blocked"
    assert "formal_deg_parameter_confirmation_missing" in result["blockers"]
    assert load_registry(tmp_path)["results"] == []


def test_formal_controlled_deg_runner_blocks_missing_dependencies_without_result(tmp_path: Path) -> None:
    _write_standardized_state(tmp_path, [], default_expression="")

    result = run_formal_controlled_deg(tmp_path, dependency_snapshot={"status": "blocked", "blockers": ["missing_python_package:scipy"]})

    assert result["status"] == "blocked"
    assert "missing_expression_asset" in result["blockers"]
    assert load_registry(tmp_path)["results"] == []


def test_formal_controlled_deg_runner_rejects_count_model_method(tmp_path: Path) -> None:
    matrix = tmp_path / "matrix.tsv"
    matrix.write_text("gene\tcase1\tctrl1\nTP53\t10\t5\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\ncase1\tcase\nctrl1\tcontrol\n", encoding="utf-8")
    group = tmp_path / "group.json"
    group.write_text(json.dumps({"group_design": {"sample_group_assignments": {"case1": "case", "ctrl1": "control"}}}), encoding="utf-8")
    _write_standardized_state(
        tmp_path,
        [
            _asset("expr", "raw_count_matrix", "expression_repository", matrix, value_type="count", gene_id_type="symbol"),
            _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
            _asset("group", "group_design", "group_design_repository", group),
        ],
        default_expression="expr",
    )

    result = run_formal_controlled_deg(tmp_path, method="count_model", dependency_snapshot={"status": "passed", "blockers": []})

    assert result["status"] == "blocked"
    assert "count_model_backend_not_activated_in_b9_2_controlled_mvp" in result["blockers"]


def _patch_backend(monkeypatch) -> None:
    class Stats:
        @staticmethod
        def ttest_ind(case_values, control_values, equal_var=False, nan_policy="omit"):
            return SimpleNamespace(pvalue=0.01, statistic=2.5)

        @staticmethod
        def mannwhitneyu(case_values, control_values, alternative="two-sided"):
            return SimpleNamespace(pvalue=0.02, statistic=3.0)

    def multipletests(p_values, method="fdr_bh"):
        return None, [min(1.0, value * len(p_values)) for value in p_values]

    from app.bioinformatics.deg_engine import python_backend

    monkeypatch.setattr(python_backend, "_import_backends", lambda: (Stats, multipletests))


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


def _write_standardized_state(root: Path, assets: list[dict[str, object]], *, default_expression: str) -> None:
    selection = {"expression": {"asset_id": default_expression, "selection_state": "user_confirmed"}}
    payload = {"schema_version": "biomedpilot.repository_manifest.v1", "assets": assets, "default_asset_selection": selection}
    registry = {"schema_version": "biomedpilot.standardized_assets_registry.v2", "assets": assets, "default_asset_selection": selection}
    repo_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.write_text(json.dumps(payload), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
