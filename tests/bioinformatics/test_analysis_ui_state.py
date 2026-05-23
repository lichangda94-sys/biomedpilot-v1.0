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
    assert state["ora_gate_rows"]
    assert state["survival_clinical_rows"]
    assert state["survival_clinical_report_gate_rows"]
    assert state["analysis_capability_map"]["schema_version"] == "biomedpilot.deep_analysis_capability_map.v1"
    assert state["multi_factor_deg_gate"]["result_semantics"] == "preflight_only"
    assert state["multi_factor_deg_gate"]["formal_execution_enabled"] is False
    assert state["r_deg_adapter_gates"]["status"] == "blocked"
    assert state["limma_rscript_gate"]["schema_version"] == "biomedpilot.r_limma_rscript_ui_execution_gate.v1"
    assert state["limma_rscript_gate"]["formal_execution_enabled"] is False
    assert state["developer_diagnostics"]["survival_clinical_state"]["risk_score_design"]["result_semantics"] == "design_audit_only"
    assert state["developer_diagnostics"]["survival_clinical_state"]["risk_score_design"]["writes_result_index"] is False
    assert _file_set(tmp_path) == before

    formal_deg = _action(state, "formal_deg")
    assert formal_deg["enabled"] is False
    assert _action(state, "formal_deg_limma_rscript")["enabled"] is False
    assert "multi_factor_design_config_missing" in _action(state, "formal_deg_limma_rscript")["disabled_reason"]
    assert formal_deg["disabled_reason"]
    assert any(
        blocker in formal_deg["disabled_reason"]
        for blocker in ("missing_python_package:scipy", "formal_deg_parameter_confirmation_missing")
    )
    assert _action(state, "formal_gsea")["enabled"] is False
    assert _action(state, "run_ora_enrichment")["enabled"] is False
    assert "ora_source_deg_result_missing" in _action(state, "run_ora_enrichment")["disabled_reason"]
    assert _action(state, "km_cox_logrank")["enabled"] is False
    assert _action(state, "report_ready_export")["state"] == "blocked_report_ready_gate"
    assert _action(state, "full_integrated_docx_rendered_export")["enabled"] is False
    assert "full_integrated_markdown_package_missing" in _action(state, "full_integrated_docx_rendered_export")["disabled_reason"]
    formal_gate_text = "\n".join(str(row) for row in state["formal_deg_gate_rows"])
    assert "Parameter manifest" in formal_gate_text
    assert "Result schema gate" in formal_gate_text
    assert "B9.2 controlled activation" in formal_gate_text
    assert "Multi-factor DEG preflight" in formal_gate_text
    assert "multi_factor_design_config_missing" in formal_gate_text
    assert "R adapter contract: limma" in formal_gate_text
    assert "limma Rscript runtime detection" in formal_gate_text
    assert "limma Rscript user confirmation" in formal_gate_text
    assert "external_engine_capability_registry_missing" in formal_gate_text
    assert "B25.6 count-model activation plan: deseq2" in formal_gate_text
    assert "multi_factor_design_config_missing" in formal_gate_text
    assert _action(state, "r_deseq2_parameter_confirmation")["enabled"] is False
    assert _action(state, "formal_deg_deseq2_rscript")["enabled"] is False
    assert _action(state, "formal_deg_edger_rscript")["enabled"] is False
    assert _action(state, "formal_deg_deseq2_rscript")["disabled_reason"]
    assert state["r_count_model_plans"]["formal_execution_enabled"] is False
    ora_gate_text = "\n".join(str(row) for row in state["ora_gate_rows"])
    assert "ORA source DEG result" in ora_gate_text
    assert "B10.2 controlled ORA execution" in ora_gate_text
    survival_gate_text = "\n".join(str(row) for row in state["survival_clinical_report_gate_rows"])
    assert "KM/log-rank section report-ready" in survival_gate_text
    assert "missing_km_logrank_result" in survival_gate_text
    gate_text = "\n".join(str(row) for row in state["gate_rows"])
    assert "DOCX rendered export" in gate_text
    assert "no result_index_v2 write" in gate_text
    assert state["developer_diagnostics"]["full_integrated_docx_rendered_export_gate"]["checks"]["writes_result_index_v2"] is False
    assert state["legacy_asset_pipeline"]["formal_analysis_enabled"] is False
    assert state["legacy_asset_pipeline"]["writes_result_index"] is False
    assert _action(state, "legacy_asset_pipeline_review")["enabled"] is False
    capabilities = {row["capability_id"]: row for row in state["analysis_capability_map"]["rows"]}
    for capability_id in ("deg_limma", "deg_limma_rscript_execution", "deg_deseq2", "deg_edger", "deg_multifactor", "cox_multivariate", "risk_score", "full_integrated_report"):
        assert capabilities[capability_id]["formal_execution_enabled"] is False
        assert capabilities[capability_id]["can_display_as_completed"] is False
        assert capabilities[capability_id]["disabled_reason"]
    assert "package.r.deseq2.available" in capabilities["deg_deseq2"]["dependency_capability_keys"]


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
    assert "display_value_type_requires_controlled_two_group_method_not_count_model" in deg_row["warnings"]
    assert "platform probe-to-gene mapping" in deg_row["repair_action"]
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
        renderer_snapshot={
            "capabilities": {
                "pandoc": {"available": False, "version": "", "packaging_impact": "external_binary_required_for_docx_and_pdf_activation_not_bundled"},
                "xelatex": {"available": False, "version": "", "packaging_impact": "external_binary_required_for_pandoc_pdf_backend_not_bundled"},
                "wkhtmltopdf": {"available": False, "version": "", "packaging_impact": "external_binary_alternative_pdf_backend_not_bundled"},
                "quarto": {"available": False, "version": "", "packaging_impact": "future_renderer_detect_only_not_enabled"},
            }
        },
    )

    text = "\n".join(str(row) for row in rows)
    assert "missing_python_package:scipy" in text
    assert "missing_python_package:statsmodels" in text
    assert "lifelines_missing_formal_survival_disabled" in text
    assert "Pandoc report renderer" in text
    assert "renderer_dependency_missing:pandoc" in text
    assert "PDF/DOCX export remains disabled" in text
    assert "no install action" in text
    assert "required_in_packaged_app_for_formal_deg" in text


def test_analysis_center_state_shows_b12_survival_clinical_input_hardening(tmp_path: Path) -> None:
    matrix = tmp_path / "expr.tsv"
    matrix.write_text("gene_id\tS1\tS2\nTP53\t10\t20\n", encoding="utf-8")
    sample = tmp_path / "sample.tsv"
    sample.write_text("sample_id\tcase_id\tgroup\nS1\tC1\tcase\nS2\tC2\tcontrol\n", encoding="utf-8")
    clinical = tmp_path / "clinical.tsv"
    clinical.write_text("case_id\tOS_time\tOS_event\tstage\tage\nC1\t10\t1\tII\t50\nC2\t20\t0\tIII\t60\n", encoding="utf-8")
    assets = [
        _asset("expr", "normalized_expression_matrix", "expression_repository", matrix, value_type="TPM", gene_id_type="symbol"),
        _asset("sample", "sample_metadata", "sample_metadata_repository", sample),
        _asset("clinical", "clinical_metadata", "clinical_repository", clinical),
    ]
    _write_standardized_state(tmp_path, assets, default_expression="expr")

    state = build_analysis_center_state(tmp_path)

    diagnostics = state["developer_diagnostics"]["survival_clinical_state"]
    assert diagnostics["input_resolver"]["case_sample_mapping_status"] == "passed"
    row_text = "\n".join(str(row) for row in state["survival_clinical_rows"])
    assert "Survival / clinical input resolver" in row_text
    assert "OS_time / OS_event / censoring gate" in row_text
    assert "Clinical variable typing / missingness" in row_text
    assert "mapped cases=2" in row_text
    assert "KM/log-rank section package" in row_text
    assert "Cox section package" in row_text
    assert _action(state, "survival_clinical_input_readiness")["enabled"] is True
    assert _action(state, "km_cox_logrank")["enabled"] is False
    assert _action(state, "cox_univariate")["enabled"] is False
    assert _action(state, "generate_km_plot")["enabled"] is False
    assert _action(state, "survival_report_ready")["enabled"] is False


def test_legacy_asset_pipeline_state_is_review_only_and_does_not_upgrade_inputs(tmp_path: Path) -> None:
    adapter_dir = tmp_path / "acquisition" / "legacy_adapter_manifests"
    adapter_dir.mkdir(parents=True)
    (adapter_dir / "geo.json").write_text(json.dumps({"adapter_id": "geo", "source": "geo"}), encoding="utf-8")
    candidate_path = tmp_path / "standardized_data" / "asset_candidates" / "legacy_acquisition_asset_candidates.json"
    candidate_path.parent.mkdir(parents=True)
    candidate_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.legacy_standardized_asset_candidate_bundle.v1",
                "status": "candidate_only",
                "candidate_count": 1,
                "warnings": ["candidate_only_not_repository_asset"],
                "blockers": [],
                "downstream_contract": {
                    "writes_analysis_input_repository": False,
                    "writes_result_index": False,
                    "ready_for_formal_analysis": False,
                },
            }
        ),
        encoding="utf-8",
    )
    selection_path = tmp_path / "standardized_data" / "asset_candidates" / "legacy_asset_selection_manifest.json"
    selection_path.write_text(
        json.dumps(
            {
                "schema_version": "biomedpilot.legacy_asset_selection_manifest.v1",
                "status": "selection_recorded_preflight_only",
                "confirmed_by_user": True,
                "selected_assets": {"expression": {"asset_id": "expr"}},
                "validation": {
                    "status": "passed_with_downstream_blockers",
                    "selection_blockers": [],
                    "downstream_blockers": ["missing_group_design_selection"],
                    "warnings": ["selected_legacy_asset_is_not_analysis_ready_until_downstream_gates_pass"],
                },
                "formal_analysis_ready": False,
                "result_semantics": "not_a_result",
                "report_ready_eligible": False,
            }
        ),
        encoding="utf-8",
    )
    before = _file_set(tmp_path)

    state = build_analysis_center_state(tmp_path)

    pipeline = state["legacy_asset_pipeline"]
    assert pipeline["status"] == "blocked"
    assert pipeline["artifact_count"] == 3
    assert pipeline["formal_analysis_enabled"] is False
    assert pipeline["writes_analysis_input_repository"] is False
    assert pipeline["writes_result_index"] is False
    assert pipeline["report_ready_eligible"] is False
    assert "missing_group_design_selection" in pipeline["blockers"]
    assert "B8 resolver" in pipeline["boundary_message"]
    operations = {item["operation_id"]: item for item in pipeline["operations"]}
    assert operations["legacy_build_candidates"]["enabled"] is True
    assert operations["legacy_materialize_candidates"]["enabled"] is True
    assert operations["legacy_merge_repository_manifest"]["enabled"] is False
    assert operations["legacy_confirm_asset_selection"]["enabled"] is False
    review = _action(state, "legacy_asset_pipeline_review")
    assert review["enabled"] is True
    assert review["button_behavior"] == "enabled_review_only_no_formal_execution"
    assert _action(state, "legacy_build_candidates")["button_behavior"] == "controlled_standardization_artifact_write_no_formal_execution"
    assert _file_set(tmp_path) == before


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
