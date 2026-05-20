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
        survival_dependency={"status": "preflight_only", "blockers": ["lifelines_missing_formal_survival_disabled"]},
        report_gate={"status": "blocked", "blockers": ["result_index_missing_or_empty"]},
    )

    formal_deg = _row(rows, "formal_deg")
    assert formal_deg["enabled"] is False
    assert "b9_1_activation_required" in formal_deg["disabled_reason"]
    assert "Formal executor is not activated" in formal_deg["disabled_reason"]

    preflight = _row(rows, "deg_preflight")
    assert preflight["enabled"] is True
    assert preflight["state"] == "config_only"


def test_formal_gsea_survival_and_km_actions_are_disabled_or_hidden() -> None:
    rows = build_action_rows(packages=[], deg_dependency={"status": "blocked"}, survival_dependency={"status": "preflight_only"}, report_gate={"status": "blocked"})

    assert _row(rows, "formal_gsea")["enabled"] is False
    assert _row(rows, "formal_gsea")["state"] == "hidden_until_ready"
    assert _row(rows, "survival_formal")["enabled"] is False
    assert _row(rows, "km_cox_logrank")["enabled"] is False
    assert "KM/Cox/log-rank" in _row(rows, "km_cox_logrank")["label"]


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


def _row(rows: list[dict[str, object]], action_id: str) -> dict[str, object]:
    return next(row for row in rows if row["action_id"] == action_id)
