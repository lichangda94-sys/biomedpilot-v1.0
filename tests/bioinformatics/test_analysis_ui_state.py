from __future__ import annotations

import json
from pathlib import Path

from app.bioinformatics.analysis_ui.state import build_analysis_center_state, build_dependency_rows
from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result


def test_analysis_center_state_comes_from_b8_contracts_and_has_no_side_effects(tmp_path: Path) -> None:
    matrix = tmp_path / "expr.tsv"
    matrix.write_text("gene_id\tS1\tS2\nTP53\t10\t20\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nS1\tcase\nS2\tcontrol\n", encoding="utf-8")
    assets = [
        _asset("expr", "raw_count_matrix", "expression_repository", matrix, value_type="count", gene_id_type="symbol"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", tmp_path / "group.json"),
    ]
    _write_standardized_state(tmp_path, assets, default_expression="expr")
    before = _file_set(tmp_path)

    state = build_analysis_center_state(tmp_path)

    assert state["resolver_source"]["source_policy"] == "standardized repository / registry / analysis_input_repository only"
    assert "recognition_report.json" not in json.dumps(state["resolver_source"], ensure_ascii=False)
    assert state["package_rows"]
    assert state["action_rows"]
    assert state["dependency_rows"]
    assert state["gate_rows"]
    assert state["survival_clinical_rows"]
    assert _file_set(tmp_path) == before

    formal_deg = _action(state, "formal_deg")
    assert formal_deg["enabled"] is False
    assert "b9_1_activation_required" in formal_deg["disabled_reason"]
    assert _action(state, "formal_gsea")["enabled"] is False
    assert _action(state, "km_cox_logrank")["enabled"] is False
    assert _action(state, "report_ready_export")["state"] == "blocked_report_ready_gate"


def test_analysis_center_state_shows_package_repair_guidance_for_deg_blockers(tmp_path: Path) -> None:
    matrix = tmp_path / "expr.tsv"
    matrix.write_text("ID_REF\tS1\tS2\n1007_s_at\t1.1\t2.2\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tgroup\nS1\tcase\nS2\tcontrol\n", encoding="utf-8")
    feature = _asset("feature", "feature_annotation", "feature_annotation_repository", tmp_path / "feature.tsv", gene_id_type="ID_REF")
    feature["validation_status"] = "blocked"
    assets = [
        _asset("expr", "expression_matrix", "expression_repository", matrix, value_type="TPM", gene_id_type="ID_REF"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("group", "group_design", "group_design_repository", tmp_path / "group.json"),
        feature,
    ]
    _write_standardized_state(tmp_path, assets, default_expression="expr")

    state = build_analysis_center_state(tmp_path)
    deg_row = next(row for row in state["package_rows"] if row["package_type"] == "deg_recompute")

    assert "geo_probe_or_id_ref_requires_platform_mapping" in deg_row["blockers"]
    assert "display_value_type_not_allowed_for_count_model_deg" in deg_row["blockers"]
    assert "platform probe-to-gene mapping" in deg_row["repair_action"]
    assert "raw count matrix" in deg_row["repair_action"]
    assert _action(state, "formal_deg")["enabled"] is False


def test_result_plot_and_report_gate_preview_preserves_non_formal_semantics(tmp_path: Path) -> None:
    register_result(
        tmp_path,
        ResultIndexEntry(
            result_id="testing",
            task_run_id="task",
            task_type="deg",
            result_semantics="testing_level",
            validation_status="passed",
        ),
    )

    state = build_analysis_center_state(tmp_path)
    result_row = next(row for row in state["result_rows"] if row["result_id"] == "testing")

    assert result_row["semantics"] == "testing level"
    assert result_row["report_status"] == "draft only / not report-ready"
    assert _action(state, "report_ready_export")["enabled"] is False
    assert "unverified_testing_exploratory_or_imported_results_present" in _action(state, "report_ready_export")["disabled_reason"]


def test_dependency_rows_are_detect_only_and_include_formal_blockers() -> None:
    rows = build_dependency_rows(
        deg_dependency={
            "status": "blocked",
            "packages": {
                "numpy": {"available": True, "version": "1"},
                "pandas": {"available": True, "version": "2"},
                "scipy": {"available": False, "version": ""},
                "statsmodels": {"available": False, "version": ""},
            },
            "r_backend": {"packages": {"R": "not_checked", "limma": "not_checked", "DESeq2": "not_checked", "edgeR": "not_checked"}},
        },
        survival_dependency={"status": "preflight_only", "python_lifelines": {"available": False, "version": ""}, "blockers": ["lifelines_missing_formal_survival_disabled"]},
    )

    text = "\n".join(str(row) for row in rows)
    assert "missing_python_package:scipy" in text
    assert "missing_python_package:statsmodels" in text
    assert "lifelines_missing_formal_survival_disabled" in text
    assert "no install action" in text


def _action(state: dict[str, object], action_id: str) -> dict[str, object]:
    return next(row for row in state["action_rows"] if row["action_id"] == action_id)  # type: ignore[index]


def _file_set(root: Path) -> set[str]:
    return {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}


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
    payload = {
        "schema_version": "biomedpilot.repository_manifest.v1",
        "assets": assets,
        "default_asset_selection": selection,
        "source_state": {"source_state_hash": "source-1"},
    }
    registry = {"schema_version": "biomedpilot.standardized_assets_registry.v2", "assets": assets, "default_asset_selection": selection}
    repo_path = root / "standardized_data" / "repositories" / "repository_manifest.json"
    registry_path = root / "manifests" / "standardized_assets_registry.json"
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    repo_path.write_text(json.dumps(payload), encoding="utf-8")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
