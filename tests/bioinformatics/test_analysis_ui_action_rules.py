from __future__ import annotations

from app.bioinformatics.analysis_ui.action_rules import build_action_rows


def test_can_run_task_does_not_enable_formal_deg() -> None:
    rows = build_action_rows(
        packages=[
            {
                "package_type": "deg_recompute",
                "status": "config_only",
                "blockers": [],
                "warnings": [],
                "allowed_downstream_tasks": ["deg_preflight"],
            }
        ],
        tasks=[{"task_type": "differential_expression", "can_run": True}],
        results=[],
        deg_dependency={"status": "passed", "blockers": []},
        deg_ready_gate={"status": "passed", "blockers": []},
        parameter_gate={"status": "passed", "blockers": []},
        confirmation_gate={"status": "blocked", "blockers": ["formal_deg_parameter_confirmation_missing"]},
        result_schema_gate={"status": "passed", "blockers": []},
        survival_dependency={"status": "preflight_only", "blockers": ["lifelines_missing_formal_survival_disabled"]},
        report_gate={"status": "blocked", "blockers": ["result_index_missing_or_empty"]},
    )

    formal_deg = _row(rows, "formal_deg")
    assert formal_deg["enabled"] is False
    assert formal_deg["state"] == "blocked_missing_user_confirmation"
    assert "formal_deg_parameter_confirmation_missing" in formal_deg["disabled_reason"]
    confirmation = _row(rows, "formal_deg_parameter_confirmation")
    assert confirmation["enabled"] is True
    assert confirmation["state"] == "requires_user_confirmation"

    preflight = _row(rows, "deg_preflight")
    assert preflight["enabled"] is True
    assert preflight["state"] == "config_only"


def test_formal_gsea_survival_and_km_actions_are_disabled_or_hidden() -> None:
    rows = build_action_rows(packages=[], deg_dependency={"status": "blocked"}, survival_dependency={"status": "preflight_only"}, report_gate={"status": "blocked"})

    legacy = _row(rows, "legacy_asset_pipeline_review")
    assert legacy["enabled"] is False
    assert legacy["state"] == "not_started"
    assert _row(rows, "formal_gsea")["enabled"] is False
    assert _row(rows, "formal_gsea")["state"] == "disabled_gsea_gate_not_passed"
    assert "gsea_input_gate_not_passed" in _row(rows, "formal_gsea")["disabled_reason"]
    assert _row(rows, "survival_formal")["enabled"] is False
    assert _row(rows, "km_cox_logrank")["enabled"] is False
    assert "KM/log-rank" in _row(rows, "km_cox_logrank")["label"]
    assert _row(rows, "run_ora_enrichment")["enabled"] is False
    assert _row(rows, "ora_plot")["enabled"] is False
    assert _row(rows, "ora_report_ready")["enabled"] is False


def test_survival_report_ready_action_enables_section_only_when_km_or_cox_gate_passes() -> None:
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "passed"},
        km_report_gate={"status": "eligible_for_km_logrank_report_ready", "warnings": []},
        cox_report_gate={"status": "blocked", "blockers": ["missing_cox_univariate_result"]},
        report_gate={"status": "blocked"},
    )

    report = _row(rows, "survival_report_ready")
    assert report["enabled"] is True
    assert report["state"] == "available_section_only"
    assert "section-only" in report["next_action"]
    assert "full integrated report" in report["next_action"]


def test_full_integrated_docx_rendered_export_action_is_package_artifact_only() -> None:
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        full_integrated_docx_gate={"status": "passed", "blockers": [], "warnings": []},
    )

    action = _row(rows, "full_integrated_docx_rendered_export")
    assert action["enabled"] is True
    assert action["button_behavior"] == "enabled_docx_rendered_export_package_artifact_only"
    assert "do not write result_index_v2" in action["next_action"]
    assert "formal_computed_result" in action["next_action"]

    blocked = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        full_integrated_docx_gate={"status": "blocked", "blockers": ["renderer_dependency_missing:pandoc"]},
    )
    assert _row(blocked, "full_integrated_docx_rendered_export")["enabled"] is False
    assert "renderer_dependency_missing:pandoc" in _row(blocked, "full_integrated_docx_rendered_export")["disabled_reason"]


def test_full_integrated_pdf_rendered_export_action_is_package_artifact_only() -> None:
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        full_integrated_pdf_gate={"status": "passed", "blockers": [], "warnings": []},
    )

    action = _row(rows, "full_integrated_pdf_rendered_export")
    assert action["enabled"] is True
    assert action["button_behavior"] == "enabled_pdf_rendered_export_package_artifact_only"
    assert "Pandoc + XeLaTeX" in action["next_action"]
    assert "do not write result_index_v2" in action["next_action"]
    assert "formal_computed_result" in action["next_action"]

    blocked = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        full_integrated_pdf_gate={"status": "blocked", "blockers": ["renderer_dependency_missing:xelatex"]},
    )
    blocked_action = _row(blocked, "full_integrated_pdf_rendered_export")
    assert blocked_action["enabled"] is False
    assert blocked_action["state"] == "blocked_pdf_rendered_export_gate"
    assert "renderer_dependency_missing:xelatex" in blocked_action["disabled_reason"]
    assert "wkhtmltopdf remains detect-only" in blocked_action["next_action"]


def test_cox_multivariate_action_is_enabled_only_after_b20_gates_pass() -> None:
    rows = build_action_rows(
        packages=[{"package_type": "tcga_clinical_survival_preflight", "blockers": []}],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "passed", "blockers": []},
        cox_multivariate_parameter_gate={"status": "passed", "blockers": []},
        cox_multivariate_confirmation_gate={"status": "passed", "blockers": []},
        report_gate={"status": "blocked"},
    )

    run = _row(rows, "cox_multivariate")
    assert run["enabled"] is True
    assert run["button_behavior"] == "enabled_multivariate_cox_mvp"
    assert "no risk score" in run["next_action"]

    blocked = build_action_rows(
        packages=[{"package_type": "tcga_clinical_survival_preflight", "blockers": []}],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only", "blockers": ["lifelines_missing_formal_survival_disabled"]},
        cox_multivariate_parameter_gate={"status": "passed", "blockers": []},
        cox_multivariate_confirmation_gate={"status": "blocked", "blockers": ["cox_multivariate_parameter_confirmation_missing"]},
        report_gate={"status": "blocked"},
    )
    assert _row(blocked, "cox_multivariate")["enabled"] is False
    assert "cox_multivariate_parameter_confirmation_missing" in _row(blocked, "cox_multivariate")["disabled_reason"]
    assert "lifelines_missing_formal_survival_disabled" in _row(blocked, "cox_multivariate")["disabled_reason"]


def test_risk_score_action_remains_design_audit_only() -> None:
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "passed"},
        risk_score_design={"schema_version": "biomedpilot.risk_score_nomogram_contract_gate.v1", "status": "ready_for_parameter_confirmation", "blockers": [], "warnings": ["risk_score_contract_gate_only"]},
        report_gate={"status": "blocked"},
    )

    risk = _row(rows, "risk_score")
    assert risk["enabled"] is False
    assert risk["state"] == "contract_gate_only"
    assert "no risk score result" in risk["disabled_reason"]
    assert "formal Cox multivariate source" in risk["next_action"]

    b33_rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "passed"},
        risk_score_design={"schema_version": "biomedpilot.risk_score_nomogram_contract_gate.v1", "status": "ready_for_parameter_confirmation", "blockers": [], "warnings": ["risk_score_contract_gate_only"]},
        risk_score_confirmation_gate={"status": "passed", "blockers": []},
        risk_score_result_schema_gate={"status": "blocked", "blockers": ["risk_score_result_bundle_missing"]},
        report_gate={"status": "blocked"},
    )
    b33_risk = _row(b33_rows, "risk_score")
    assert b33_risk["enabled"] is True
    assert b33_risk["state"] == "enabled_controlled_risk_score_mvp"
    assert b33_risk["button_behavior"] == "enabled_controlled_risk_score_table_only"
    assert "no risk groups" in b33_risk["next_action"]

    plot_rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "passed"},
        risk_score_plot_nomogram_gate={"status": "blocked_planning_only", "blockers": ["b37_risk_score_renderer_activation_required"]},
        report_gate={"status": "blocked"},
    )
    plot_action = _row(plot_rows, "risk_score_plot_nomogram")
    assert plot_action["enabled"] is False
    assert plot_action["state"] == "blocked_planning_only"
    assert "b37_risk_score_renderer_activation_required" in plot_action["disabled_reason"]
    assert "no risk score plot" in plot_action["disabled_reason"]


def test_controlled_preranked_gsea_enabled_only_when_b11_2_gates_pass() -> None:
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        gsea_input_gate={"status": "passed", "source_result_id": "deg-1", "source_result_semantics": "formal_computed_result", "blockers": []},
        gsea_rank_metric_gate={"status": "passed", "blockers": []},
        gsea_gene_set_gate={"status": "passed", "blockers": []},
        gsea_parameter_gate={"status": "passed", "blockers": []},
        gsea_result_schema_gate={"status": "passed", "blockers": []},
        gsea_dependency={"status": "passed", "blockers": []},
    )

    run = _row(rows, "formal_gsea")
    assert run["enabled"] is True
    assert run["button_behavior"] == "enabled_controlled_preranked_gsea_mvp"

    blocked = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        gsea_input_gate={"status": "passed", "source_result_id": "deg-1", "source_result_semantics": "formal_computed_result", "blockers": []},
        gsea_rank_metric_gate={"status": "passed", "blockers": []},
        gsea_gene_set_gate={"status": "passed", "blockers": []},
        gsea_parameter_gate={"status": "passed", "blockers": []},
        gsea_result_schema_gate={"status": "passed", "blockers": []},
        gsea_dependency={"status": "blocked", "blockers": ["missing_python_package:statsmodels"]},
    )
    assert _row(blocked, "formal_gsea")["enabled"] is False
    assert "missing_python_package:statsmodels" in _row(blocked, "formal_gsea")["disabled_reason"]


def test_legacy_asset_pipeline_action_is_review_only() -> None:
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        legacy_asset_pipeline={
            "status": "available_for_review",
            "artifact_count": 4,
            "boundary_message": "Legacy assets still require B8 resolver and downstream task gates.",
            "operations": [
                {
                    "operation_id": "legacy_build_candidates",
                    "label": "Build legacy asset candidates",
                    "enabled": True,
                    "state": "available",
                    "button_behavior": "controlled_standardization_artifact_write_no_formal_execution",
                    "next_action": "Write candidate-only bundle.",
                },
                {
                    "operation_id": "legacy_materialize_candidates",
                    "label": "Materialize legacy candidates",
                    "enabled": False,
                    "state": "blocked",
                    "disabled_reason": "legacy_asset_candidates_missing",
                    "button_behavior": "controlled_standardization_artifact_write_no_formal_execution",
                    "next_action": "Write materialization manifest.",
                },
            ],
        },
    )

    legacy = _row(rows, "legacy_asset_pipeline_review")
    assert legacy["enabled"] is True
    assert legacy["button_behavior"] == "enabled_review_only_no_formal_execution"
    assert "B8 resolver" in legacy["next_action"]
    build = _row(rows, "legacy_build_candidates")
    assert build["enabled"] is True
    assert build["button_behavior"] == "controlled_standardization_artifact_write_no_formal_execution"
    materialize = _row(rows, "legacy_materialize_candidates")
    assert materialize["enabled"] is False
    assert materialize["disabled_reason"] == "legacy_asset_candidates_missing"
    assert _row(rows, "formal_deg")["enabled"] is False


def test_formal_deg_enabled_only_after_user_parameter_confirmation() -> None:
    rows = build_action_rows(
        packages=[{"package_type": "deg_recompute", "status": "config_only", "blockers": [], "warnings": []}],
        deg_dependency={"status": "passed", "blockers": []},
        deg_ready_gate={"status": "passed", "blockers": []},
        parameter_gate={"status": "passed", "blockers": []},
        confirmation_gate={"status": "passed", "blockers": []},
        result_schema_gate={"status": "passed", "blockers": []},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
    )

    formal_deg = _row(rows, "formal_deg")
    assert formal_deg["enabled"] is True
    assert formal_deg["state"] == "enabled_formal_deg"
    assert formal_deg["button_behavior"] == "enabled_controlled_two_group_mvp"
    assert _row(rows, "formal_deg_parameter_confirmation")["state"] == "confirmed"


def test_limma_rscript_action_requires_all_gates_and_confirmation() -> None:
    blocked = build_action_rows(
        packages=[],
        deg_dependency={"status": "passed", "blockers": []},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        limma_rscript_gate={
            "status": "blocked",
            "multi_factor_preflight": {"status": "blocked", "blockers": ["multi_factor_design_config_missing"]},
            "runtime_detection": {"status": "passed", "blockers": []},
            "runtime_gate": {"status": "ready_for_external_runtime_execution", "blockers": []},
            "parameter_manifest": {"status": "blocked", "blockers": ["multi_factor_design_config_missing"]},
            "confirmation_gate": {"status": "blocked", "blockers": ["r_limma_parameter_confirmation_missing"]},
            "result_schema_gate": {"status": "blocked", "blockers": ["parameter_gate_not_passed"]},
            "blockers": ["multi_factor_design_config_missing", "r_limma_parameter_confirmation_missing"],
        },
    )

    assert _row(blocked, "r_limma_design_config")["enabled"] is False
    assert _row(blocked, "r_limma_parameter_confirmation")["enabled"] is False
    assert "multi_factor_design_config_missing" in _row(blocked, "r_limma_parameter_confirmation")["disabled_reason"]
    assert _row(blocked, "formal_deg_limma_rscript")["enabled"] is False
    assert "r_limma_parameter_confirmation_missing" in _row(blocked, "formal_deg_limma_rscript")["disabled_reason"]

    enabled = build_action_rows(
        packages=[],
        deg_dependency={"status": "passed", "blockers": []},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        limma_rscript_gate={
            "status": "passed",
            "multi_factor_preflight": {"status": "design_ready", "blockers": []},
            "runtime_detection": {"status": "passed", "blockers": []},
            "runtime_gate": {"status": "ready_for_external_runtime_execution", "blockers": []},
            "parameter_manifest": {"status": "passed", "blockers": []},
            "confirmation_gate": {"status": "passed", "blockers": []},
            "result_schema_gate": {"status": "passed", "blockers": []},
            "blockers": [],
        },
    )

    assert _row(enabled, "r_limma_design_config")["enabled"] is False
    assert _row(enabled, "r_limma_parameter_confirmation")["state"] == "confirmed"
    limma = _row(enabled, "formal_deg_limma_rscript")
    assert limma["enabled"] is True
    assert limma["button_behavior"] == "enabled_b25_2_audited_limma_rscript_only"


def test_count_model_actions_gate_deseq2_and_edger_confirmation() -> None:
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "passed", "blockers": []},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        r_count_model_plans={
            "plans": {
                "deseq2": {"blockers": ["r_deseq2_parameter_confirmation_missing"]},
                "edger": {"blockers": ["r_edger_parameter_confirmation_missing"]},
            }
        },
    )

    deseq2 = _row(rows, "formal_deg_deseq2_rscript")
    edger = _row(rows, "formal_deg_edger_rscript")
    assert deseq2["enabled"] is False
    assert edger["enabled"] is False
    assert deseq2["state"] == "blocked_deseq2_rscript_gate"
    assert edger["state"] == "blocked_edger_rscript_gate"
    assert "r_deseq2_parameter_confirmation_missing" in deseq2["disabled_reason"]
    assert "r_edger_parameter_confirmation_missing" in edger["disabled_reason"]
    assert _row(rows, "r_deseq2_parameter_confirmation")["enabled"] is False
    assert "r_deseq2_design_preflight_not_ready" in _row(rows, "r_deseq2_parameter_confirmation")["disabled_reason"]
    assert _row(rows, "r_edger_parameter_confirmation")["enabled"] is False
    assert "r_edger_design_preflight_not_ready" in _row(rows, "r_edger_parameter_confirmation")["disabled_reason"]


def test_deseq2_actions_enable_confirmation_then_execution_when_gates_pass() -> None:
    preflight = {"status": "design_ready", "blockers": []}
    runtime_gate = {"status": "ready_for_external_runtime_execution", "blockers": []}
    parameter_manifest = {"status": "passed", "blockers": []}
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "passed", "blockers": []},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        r_count_model_plans={
            "plans": {
                "deseq2": {
                    "formal_execution_enabled": False,
                    "blockers": ["r_deseq2_parameter_confirmation_missing"],
                    "preflight": preflight,
                    "runtime_gate": runtime_gate,
                    "parameter_manifest": parameter_manifest,
                    "parameter_confirmation_gate": {"status": "blocked", "blockers": ["r_deseq2_parameter_confirmation_missing"]},
                },
            }
        },
    )
    confirm = _row(rows, "r_deseq2_parameter_confirmation")
    assert confirm["enabled"] is True
    assert confirm["state"] == "requires_user_confirmation"
    assert confirm["button_behavior"] == "enabled_deseq2_parameter_confirmation_only"
    assert _row(rows, "formal_deg_deseq2_rscript")["enabled"] is False

    enabled = build_action_rows(
        packages=[],
        deg_dependency={"status": "passed", "blockers": []},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        r_count_model_plans={
            "plans": {
                "deseq2": {
                    "formal_execution_enabled": True,
                    "blockers": [],
                    "preflight": preflight,
                    "runtime_gate": runtime_gate,
                    "parameter_manifest": parameter_manifest,
                    "parameter_confirmation_gate": {"status": "passed", "blockers": []},
                },
            }
        },
    )
    assert _row(enabled, "r_deseq2_parameter_confirmation")["state"] == "confirmed"
    deseq2 = _row(enabled, "formal_deg_deseq2_rscript")
    assert deseq2["enabled"] is True
    assert deseq2["state"] == "enabled_formal_deseq2_rscript"
    assert deseq2["button_behavior"] == "enabled_b25_11_audited_deseq2_rscript_only"


def test_edger_actions_enable_confirmation_then_execution_when_gates_pass() -> None:
    preflight = {"status": "design_ready", "blockers": []}
    runtime_gate = {"status": "ready_for_external_runtime_execution", "blockers": []}
    parameter_manifest = {"status": "passed", "blockers": []}
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "passed", "blockers": []},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        r_count_model_plans={
            "plans": {
                "edger": {
                    "formal_execution_enabled": False,
                    "blockers": ["r_edger_parameter_confirmation_missing"],
                    "preflight": preflight,
                    "runtime_gate": runtime_gate,
                    "parameter_manifest": parameter_manifest,
                    "parameter_confirmation_gate": {"status": "blocked", "blockers": ["r_edger_parameter_confirmation_missing"]},
                },
            }
        },
    )
    confirm = _row(rows, "r_edger_parameter_confirmation")
    assert confirm["enabled"] is True
    assert confirm["state"] == "requires_user_confirmation"
    assert confirm["button_behavior"] == "enabled_edger_parameter_confirmation_only"
    assert _row(rows, "formal_deg_edger_rscript")["enabled"] is False

    enabled = build_action_rows(
        packages=[],
        deg_dependency={"status": "passed", "blockers": []},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        r_count_model_plans={
            "plans": {
                "edger": {
                    "formal_execution_enabled": True,
                    "blockers": [],
                    "preflight": preflight,
                    "runtime_gate": runtime_gate,
                    "parameter_manifest": parameter_manifest,
                    "parameter_confirmation_gate": {"status": "passed", "blockers": []},
                },
            }
        },
    )
    assert _row(enabled, "r_edger_parameter_confirmation")["state"] == "confirmed"
    edger = _row(enabled, "formal_deg_edger_rscript")
    assert edger["enabled"] is True
    assert edger["state"] == "enabled_formal_edger_rscript"
    assert edger["button_behavior"] == "enabled_b25_14_audited_edger_rscript_only"


def test_preflight_only_plot_source_is_blocked_and_report_gate_controls_export() -> None:
    rows = build_action_rows(
        packages=[],
        results=[{"result_id": "preflight-1", "result_semantics": "preflight_only"}],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked", "blockers": ["unverified_testing_exploratory_or_imported_results_present"]},
    )

    plot = _row(rows, "plot_spec")
    assert plot["enabled"] is False
    assert "preflight_only_source_cannot_generate_formal_plot" in plot["disabled_reason"]

    report = _row(rows, "report_ready_export")
    assert report["enabled"] is False
    assert report["state"] == "blocked_report_ready_gate"
    assert "unverified_testing_exploratory_or_imported_results_present" in report["disabled_reason"]


def test_formal_deg_plot_action_requires_formal_result_with_deg_table() -> None:
    rows = build_action_rows(
        packages=[],
        results=[
            {
                "result_id": "formal",
                "task_type": "deg",
                "result_semantics": "formal_computed_result",
                "output_artifacts": [{"artifact_type": "deg_result_table", "path": "results/tables/formal.tsv"}],
            }
        ],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
    )

    plot = _row(rows, "plot_spec")
    assert plot["enabled"] is True
    assert plot["button_behavior"] == "enabled_formal_deg_plot_artifact_only"
    assert "does not create report-ready output" in plot["next_action"]


def test_imported_deg_review_is_review_only_not_formal() -> None:
    rows = build_action_rows(
        packages=[{"package_type": "deg_imported_result", "blockers": [], "warnings": ["imported_deg_is_external_result_not_biomedpilot_recomputed"]}],
        results=[{"result_id": "imported", "result_semantics": "imported_external_result"}],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
    )

    imported = _row(rows, "imported_deg_review")
    assert imported["enabled"] is True
    assert imported["button_behavior"] == "enabled_review_only"
    assert "imported_external_result" in imported["next_action"]
    formal_plot = _row(rows, "plot_spec")
    assert formal_plot["enabled"] is False
    assert "formal_deg_plot_requires_formal_computed_result_source" in formal_plot["disabled_reason"]


def test_ora_readiness_can_be_reviewed_but_execution_stays_disabled() -> None:
    rows = build_action_rows(
        packages=[],
        results=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        ora_input_gate={"status": "passed", "source_result_id": "deg-1", "source_result_semantics": "formal_computed_result", "blockers": []},
        ora_gene_set_gate={"status": "passed", "validation_status": "passed", "blockers": []},
        ora_parameter_gate={"status": "passed", "blockers": []},
        ora_result_schema_gate={"status": "passed", "blockers": []},
        ora_dependency={"status": "passed", "blockers": []},
    )

    readiness = _row(rows, "ora_readiness_review")
    assert readiness["enabled"] is True
    assert readiness["button_behavior"] == "enabled_gate_review_only"
    run = _row(rows, "run_ora_enrichment")
    assert run["enabled"] is True
    assert run["button_behavior"] == "enabled_controlled_ora_mvp"


def test_ora_plot_action_is_enabled_only_when_plot_gate_passes() -> None:
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        ora_plot_gate={"status": "passed", "warnings": ["imported_ora_derived_plot_not_biomedpilot_recomputed_formal_plot"]},
    )

    plot = _row(rows, "ora_plot")
    assert plot["enabled"] is True
    assert plot["button_behavior"] == "enabled_ora_real_svg_plot"
    assert "SVG plot artifact" in plot["next_action"]

    blocked = build_action_rows(packages=[], deg_dependency={"status": "blocked"}, survival_dependency={"status": "preflight_only"}, report_gate={"status": "blocked"}, ora_plot_gate={"status": "blocked", "blockers": ["ora_result_not_found"]})
    assert _row(blocked, "ora_plot")["enabled"] is False
    assert "ora_result_not_found" in _row(blocked, "ora_plot")["disabled_reason"]


def test_ora_report_ready_action_is_gate_controlled() -> None:
    rows = build_action_rows(
        packages=[],
        deg_dependency={"status": "blocked"},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
        ora_report_gate={"status": "eligible_for_ora_report_ready", "warnings": []},
    )

    report = _row(rows, "ora_report_ready")
    assert report["enabled"] is True
    assert report["button_behavior"] == "enabled_ora_report_ready_package"
    assert "no GSEA, survival" in report["next_action"]

    imported = build_action_rows(packages=[], deg_dependency={"status": "blocked"}, survival_dependency={"status": "preflight_only"}, report_gate={"status": "blocked"}, ora_report_gate={"status": "eligible_for_imported_derived_ora_report_package", "warnings": ["imported_derived_ora_report_not_biomedpilot_formal_recomputed_ora"]})
    assert _row(imported, "ora_report_ready")["button_behavior"] == "enabled_imported_derived_ora_report_package"
    assert "imported-derived" in _row(imported, "ora_report_ready")["next_action"]

    blocked = build_action_rows(packages=[], deg_dependency={"status": "blocked"}, survival_dependency={"status": "preflight_only"}, report_gate={"status": "blocked"}, ora_report_gate={"status": "blocked", "blockers": ["ora_report_task_run_log_missing"]})
    assert _row(blocked, "ora_report_ready")["enabled"] is False
    assert "ora_report_task_run_log_missing" in _row(blocked, "ora_report_ready")["disabled_reason"]


def test_formal_deg_disabled_reason_lists_all_failed_b9_1_gates() -> None:
    rows = build_action_rows(
        packages=[{"package_type": "deg_recompute", "blockers": ["display_value_type_not_allowed_for_count_model_deg"]}],
        deg_dependency={"status": "blocked", "blockers": ["missing_python_package:statsmodels"]},
        deg_ready_gate={"status": "blocked", "blockers": ["sample_group_mismatch"]},
        parameter_gate={"status": "blocked", "blockers": ["missing_fdr_policy"]},
        confirmation_gate={"status": "blocked", "blockers": ["formal_deg_parameter_confirmation_missing"]},
        result_schema_gate={"status": "blocked", "blockers": ["missing_output_artifact"]},
        survival_dependency={"status": "preflight_only"},
        report_gate={"status": "blocked"},
    )

    reason = str(_row(rows, "formal_deg")["disabled_reason"])
    assert "display_value_type_not_allowed_for_count_model_deg" in reason
    assert "missing_python_package:statsmodels" in reason
    assert "sample_group_mismatch" in reason
    assert "missing_fdr_policy" in reason
    assert "formal_deg_parameter_confirmation_missing" in reason
    assert "missing_output_artifact" in reason
    assert "controlled DEG MVP" in reason


def _row(rows: list[dict[str, object]], action_id: str) -> dict[str, object]:
    return next(row for row in rows if row["action_id"] == action_id)
