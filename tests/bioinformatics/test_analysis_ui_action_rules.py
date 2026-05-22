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
    assert _row(rows, "formal_gsea")["state"] == "hidden_until_ready"
    assert _row(rows, "survival_formal")["enabled"] is False
    assert _row(rows, "km_cox_logrank")["enabled"] is False
    assert "KM/log-rank" in _row(rows, "km_cox_logrank")["label"]


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
