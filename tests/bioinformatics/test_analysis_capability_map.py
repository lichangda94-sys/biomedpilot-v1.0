from __future__ import annotations

from app.bioinformatics.analysis_ui.capability_map import build_analysis_capability_map


def test_b17_capability_map_keeps_unimplemented_methods_blocked() -> None:
    capability_map = build_analysis_capability_map(
        action_rows=[
            {"action_id": "formal_deg", "enabled": True, "state": "enabled_formal_deg", "next_action": "Run audited DEG."},
            {"action_id": "run_ora_enrichment", "enabled": False, "state": "blocked", "disabled_reason": "ora_source_deg_result_missing"},
            {"action_id": "formal_gsea", "enabled": False, "state": "blocked", "disabled_reason": "gsea_input_gate_not_passed"},
            {"action_id": "km_cox_logrank", "enabled": False, "state": "blocked", "disabled_reason": "dependency_snapshot_not_passed"},
            {"action_id": "cox_univariate", "enabled": False, "state": "blocked", "disabled_reason": "dependency_snapshot_not_passed"},
        ],
        survival_clinical_rows=[
            {"row_id": "cox_multivariate_design", "status": "design_only"},
            {"row_id": "risk_score", "status": "disabled"},
        ],
        multi_factor_deg_gate={"status": "blocked", "blockers": ["multi_factor_design_config_missing"], "result_semantics": "preflight_only"},
    )
    rows = {row["capability_id"]: row for row in capability_map["rows"]}

    assert rows["deg_two_group_controlled_mvp"]["formal_execution_enabled"] is True
    for capability_id in ("deg_limma", "deg_deseq2", "deg_edger", "deg_multifactor", "cox_multivariate", "risk_score", "km_cox_real_plot", "full_integrated_report", "legacy_formal_execution"):
        row = rows[capability_id]
        assert row["formal_execution_enabled"] is False
        assert row["can_display_as_completed"] is False
        assert row["disabled_reason"]

    assert rows["deg_limma"]["ui_state"] == "blocked_by_dependency"
    assert rows["deg_multifactor"]["implementation_status"] == "contract_preflight_available"
    assert rows["deg_multifactor"]["ui_state"] == "blocked_preflight"
    assert "preflight" in rows["deg_multifactor"]["result_semantics_policy"]
    assert "package.r.limma.available" in rows["deg_limma"]["dependency_capability_keys"]
    assert "runtime.r.available" in rows["deg_deseq2"]["dependency_capability_keys"]
    assert "package.r.edger.available" in rows["deg_edger"]["dependency_capability_keys"]
    assert rows["cox_multivariate"]["implementation_status"] == "b20_gated_execution_contract"
    assert rows["risk_score"]["ui_state"] == "disabled"
    assert rows["full_integrated_report"]["implementation_status"] == "planned"
    assert rows["legacy_formal_execution"]["implementation_status"] == "disabled"
    assert capability_map["summary"]["completed_claim_count"] == 0


def test_dependency_available_does_not_upgrade_r_method_to_completed() -> None:
    capability_map = build_analysis_capability_map(
        external_capabilities={
            "runtime.r.available": {"available": True, "version": "4.4"},
            "runtime.bioconductor.available": {"available": True, "version": "3.20"},
            "package.r.limma.available": {"available": True, "version": "3.x"},
        }
    )
    limma = next(row for row in capability_map["rows"] if row["capability_id"] == "deg_limma")

    assert limma["ui_state"] == "planned_adapter_contract"
    assert limma["formal_execution_enabled"] is False
    assert limma["can_display_as_completed"] is False
    assert "B19 adapter" in limma["reason"]
