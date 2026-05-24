from __future__ import annotations

from typing import Any


R_RUNTIME_KEY = "runtime.r.available"
BIOCONDUCTOR_KEY = "runtime.bioconductor.available"
LIMMA_KEY = "package.r.limma.available"
DESEQ2_KEY = "package.r.deseq2.available"
EDGER_KEY = "package.r.edger.available"
SURVIVAL_KEY = "package.r.survival.available"
GLMNET_KEY = "package.r.glmnet.available"
MATPLOTLIB_KEY = "package.python.matplotlib.available"
PANDOC_KEY = "renderer.pandoc.available"
QUARTO_KEY = "renderer.quarto.available"
LATEX_KEY = "renderer.latex.available"


def build_analysis_capability_map(
    *,
    action_rows: list[dict[str, Any]] | None = None,
    formal_deg_gate_rows: list[dict[str, Any]] | None = None,
    ora_gate_rows: list[dict[str, Any]] | None = None,
    gsea_gate_rows: list[dict[str, Any]] | None = None,
    survival_clinical_rows: list[dict[str, Any]] | None = None,
    dependency_rows: list[dict[str, Any]] | None = None,
    external_capabilities: dict[str, Any] | None = None,
    multi_factor_deg_gate: dict[str, Any] | None = None,
    r_deg_adapter_gates: dict[str, Any] | None = None,
    r_count_model_plans: dict[str, Any] | None = None,
    limma_rscript_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    action_by_id = {str(row.get("action_id") or ""): row for row in action_rows or [] if isinstance(row, dict)}
    dependency_by_id = {str(row.get("dependency_id") or ""): row for row in dependency_rows or [] if isinstance(row, dict)}
    external_capabilities = external_capabilities or {}

    rows = [
        _row_from_action(
            "deg_two_group_controlled_mvp",
            "DEG two-group controlled MVP",
            "DEG",
            "formal_available",
            action_by_id.get("formal_deg"),
            required_contracts=["B8 resolver", "B9 DEG parameter/confirmation/result schema", "result_index_v2"],
            result_semantics="formal_computed_result when all gates pass",
        ),
        _r_method_row("deg_limma", "limma", "limma", [R_RUNTIME_KEY, BIOCONDUCTOR_KEY, LIMMA_KEY], external_capabilities, r_deg_adapter_gates, method_policy="normalized/log expression or limma-voom contract planned"),
        _row_from_action(
            "deg_limma_rscript_execution",
            "limma Rscript controlled execution",
            "DEG",
            "b25_3_gated_execution_control",
            action_by_id.get("formal_deg_limma_rscript"),
            required_contracts=["B8 resolver", "B18 limma design preflight", "B25 Rscript runtime detection", "B25 limma parameter confirmation", "result_index_v2"],
            result_semantics="formal_computed_result only after limma Rscript execution and B25 handoff/result schema gates pass",
        ),
        _r_method_row("deg_deseq2", "DESeq2", "deseq2", [R_RUNTIME_KEY, BIOCONDUCTOR_KEY, DESEQ2_KEY], external_capabilities, r_deg_adapter_gates, r_count_model_plans=r_count_model_plans, method_policy="raw integer count model only; TPM/FPKM blocked"),
        _r_method_row("deg_edger", "edgeR", "edger", [R_RUNTIME_KEY, BIOCONDUCTOR_KEY, EDGER_KEY], external_capabilities, r_deg_adapter_gates, r_count_model_plans=r_count_model_plans, method_policy="raw integer count model only; TPM/FPKM blocked"),
        _multifactor_deg_row(multi_factor_deg_gate),
        _row_from_action(
            "ora_controlled_mvp",
            "ORA controlled enrichment",
            "Enrichment",
            "controlled_mvp_available",
            action_by_id.get("run_ora_enrichment"),
            required_contracts=["B10 ORA input/resource/parameter/result gates"],
            result_semantics="formal_computed_result only from eligible source result; imported-derived ORA remains imported_external_result",
        ),
        _row_from_action(
            "gsea_preranked_controlled_mvp",
            "Preranked GSEA controlled MVP",
            "Enrichment",
            "controlled_mvp_available",
            action_by_id.get("formal_gsea"),
            required_contracts=["B11 GSEA input/rank/gene-set/parameter/result gates"],
            result_semantics="formal_computed_result only from eligible source result; imported-derived GSEA remains imported_external_result",
        ),
        _row_from_action(
            "km_logrank_controlled_mvp",
            "KM/log-rank controlled MVP",
            "Survival",
            "controlled_mvp_available",
            action_by_id.get("km_cox_logrank"),
            required_contracts=["B12/B13 survival input/outcome/parameter/confirmation gates"],
            result_semantics="formal_computed_result when all KM/log-rank gates pass; report_ready_eligible remains false",
        ),
        _row_from_action(
            "cox_univariate_controlled_mvp",
            "Cox univariate controlled MVP",
            "Survival",
            "controlled_mvp_available",
            action_by_id.get("cox_univariate"),
            required_contracts=["B12/B14 Cox input/outcome/covariate/parameter/confirmation gates"],
            result_semantics="formal_computed_result when all Cox univariate gates pass; report_ready_eligible remains false",
        ),
        _static_row(
            "cox_multivariate",
            "Cox multivariate",
            "Survival",
            "b20_gated_execution_contract",
            _status_from_survival_row(survival_clinical_rows, "cox_multivariate_design") or "disabled",
            "B20 adds gated multivariate Cox execution with EPV, covariate, missingness, collinearity, model-formula, dependency and confirmation gates; risk score and clinical conclusions remain disabled.",
            capability_keys=[SURVIVAL_KEY],
        ),
        _static_row(
            "risk_score",
            "Risk score / nomogram",
            "Survival",
            "disabled_design_only",
            _status_from_survival_row(survival_clinical_rows, "risk_score") or "disabled",
            "B21 risk score is design-audit only: training/validation, coefficient source, cutoff, overfitting protection and provenance can be reviewed, but no score, nomogram, risk group or clinical conclusion is generated.",
            capability_keys=[GLMNET_KEY],
        ),
        _static_row(
            "km_cox_real_plot",
            "KM/Cox real plot artifact",
            "Plot",
            "b22_real_renderer_gated",
            _status_from_survival_row(survival_clinical_rows, "km_plot_artifact") or _status_from_survival_row(survival_clinical_rows, "cox_forest_plot") or "blocked",
            "B22 adds gated real SVG plot artifacts for formal KM/Cox results only; plot artifacts inherit source semantics and do not create survival report-ready output.",
            capability_keys=["renderer.python.builtin_svg.available", MATPLOTLIB_KEY, "package.r.ggplot2.available", "package.r.survminer.available"],
        ),
        _static_row(
            "full_integrated_report",
            "Full integrated report",
            "Report",
            "b23_gate_blocked",
            str((action_by_id.get("full_integrated_report_export") or {}).get("state") or "blocked_full_integrated_report_gate"),
            str((action_by_id.get("full_integrated_report_export") or {}).get("disabled_reason") or "B23 full integrated report gate is blocked until all section report-ready gates pass, including survival/clinical."),
            capability_keys=[PANDOC_KEY, QUARTO_KEY, LATEX_KEY, "renderer.wkhtmltopdf.available"],
        ),
        _static_row(
            "legacy_formal_execution",
            "Legacy formal execution",
            "Legacy",
            "disabled",
            "disabled",
            "Legacy GEO/TCGA/GTEx pipeline outputs are acquisition/standardization inputs only and cannot bypass B8 resolver or result semantics gates.",
            capability_keys=[],
        ),
    ]
    return {
        "schema_version": "biomedpilot.deep_analysis_capability_map.v1",
        "source_policy": "B17 UI status map only; no formal execution, no dependency installation, no legacy execution upgrade.",
        "rows": rows,
        "summary": _summary(rows),
        "external_engine_handoff": {
            "required_capability_keys": sorted({key for row in rows for key in row.get("dependency_capability_keys", [])}),
            "query_policy": "Bioinformatics reads capability status/snapshots from external engine handoff only; it does not install or maintain R/Bioconductor/Python plotting tools.",
            "limma_rscript_gate_status": str((limma_rscript_gate or {}).get("status") or "blocked"),
        },
    }


def _row_from_action(
    capability_id: str,
    label: str,
    category: str,
    implementation_status: str,
    action: dict[str, Any] | None,
    *,
    required_contracts: list[str],
    result_semantics: str,
) -> dict[str, Any]:
    action = action or {}
    enabled = bool(action.get("enabled"))
    state = str(action.get("state") or ("available" if enabled else "blocked"))
    reason = str(action.get("disabled_reason") or action.get("next_action") or "No action state is available.")
    return {
        "capability_id": capability_id,
        "label": label,
        "category": category,
        "implementation_status": implementation_status,
        "ui_state": "available" if enabled else state,
        "formal_execution_enabled": enabled,
        "can_display_as_completed": False,
        "reason": reason,
        "disabled_reason": "" if enabled else reason,
        "dependency_capability_keys": [],
        "required_contracts": required_contracts,
        "result_semantics_policy": result_semantics,
        "boundary": "Dependency/input availability does not equal completed analysis; a completed badge requires a validated result entry.",
    }


def _r_method_row(
    capability_id: str,
    label: str,
    method: str,
    keys: list[str],
    external_capabilities: dict[str, Any],
    r_deg_adapter_gates: dict[str, Any] | None,
    *,
    r_count_model_plans: dict[str, Any] | None = None,
    method_policy: str,
) -> dict[str, Any]:
    gate = {}
    if isinstance(r_deg_adapter_gates, dict) and isinstance(r_deg_adapter_gates.get("gates"), dict):
        gate = r_deg_adapter_gates["gates"].get(method, {}) if isinstance(r_deg_adapter_gates["gates"].get(method), dict) else {}
    plan = {}
    if method in {"deseq2", "edger"} and isinstance(r_count_model_plans, dict) and isinstance(r_count_model_plans.get("plans"), dict):
        plan = r_count_model_plans["plans"].get(method, {}) if isinstance(r_count_model_plans["plans"].get(method), dict) else {}
    missing = [key for key in keys if _capability_available(external_capabilities.get(key)) is not True]
    gate_blockers = [str(item) for item in gate.get("blockers", []) or []] if isinstance(gate.get("blockers"), list) else []
    plan_blockers = [str(item) for item in plan.get("blockers", []) or []] if isinstance(plan.get("blockers"), list) else []
    plan_formal_enabled = method == "deseq2" and bool(plan.get("formal_execution_enabled")) and not plan_blockers
    if plan_formal_enabled:
        state = "ready_for_ui_execution"
        reason = f"{label} B25.11 UI execution is available only through the audited DESeq2 Rscript action and result_index_v2 gates."
    elif method == "deseq2" and plan:
        state = "blocked_deseq2_rscript_gate"
        reason = f"{label} B25.11 UI execution is blocked: {', '.join(plan_blockers)}."
    elif plan:
        state = "blocked_count_model_planning_only"
        reason = f"{label} B25.12 count-model parameter/runtime planning remains blocked: {', '.join(plan_blockers)}."
    elif missing or gate_blockers:
        state = "blocked_by_dependency"
        reason = f"{label} B19 adapter gate is blocked: {', '.join(gate_blockers or missing)}."
    elif gate.get("status") == "ready_for_external_runtime_execution":
        state = "ready_for_external_runtime_gate"
        reason = f"{label} external dependencies appear available, but B19 adapter/input/output/result schema gates are still required before formal execution."
    else:
        state = "planned_adapter_contract"
        reason = f"{label} external dependencies appear available, but B19 adapter/input/output/result schema gates are still required before formal execution."
    return {
        "capability_id": capability_id,
        "label": label,
        "category": "DEG",
        "implementation_status": "b25_11_deseq2_gated_ui_execution" if method == "deseq2" and plan else ("b25_12_edger_parameter_runtime_planning" if method == "edger" and plan else ("b25_6_count_model_activation_planning" if plan else "b19_adapter_contract_gate")),
        "ui_state": state,
        "formal_execution_enabled": plan_formal_enabled,
        "can_display_as_completed": False,
        "reason": reason,
        "disabled_reason": reason,
        "dependency_capability_keys": keys,
        "required_contracts": ["B8 resolver", "B18 count-model design preflight", "B25 count-model activation plan", "method-specific parameter confirmation", "method-specific Rscript adapter", "result_index_v2"] if plan else ["B18 multi-factor/preflight policy", "B19 R adapter contract", "external engine dependency snapshot"],
        "method_policy": method_policy,
        "result_semantics_policy": "Never formal_computed_result until B19 adapter execution, output schema validation and result_index registration pass.",
        "boundary": "External dependency availability is not a completed analysis capability.",
    }


def _multifactor_deg_row(gate: dict[str, Any] | None) -> dict[str, Any]:
    gate = gate if isinstance(gate, dict) else {}
    status = str(gate.get("status") or "blocked")
    blockers = [str(item) for item in gate.get("blockers", []) or []] if isinstance(gate.get("blockers"), list) else []
    if status == "design_ready":
        ui_state = "available_preflight_only"
        reason = "Multi-factor DEG design preflight is ready, but formal execution still requires B19 adapter/output/result schema gates."
    elif blockers:
        ui_state = "blocked_preflight"
        reason = f"Multi-factor DEG preflight is blocked: {', '.join(blockers)}."
    else:
        ui_state = "contract_preflight_available"
        reason = "B18 multi-factor DEG contract/preflight is available; provide design matrix, contrast, covariates and value type policy to evaluate readiness."
    return {
        "capability_id": "deg_multifactor",
        "label": "Multi-factor DEG design",
        "category": "DEG",
        "implementation_status": "contract_preflight_available",
        "ui_state": ui_state,
        "formal_execution_enabled": False,
        "can_display_as_completed": False,
        "reason": reason,
        "disabled_reason": reason,
        "dependency_capability_keys": [R_RUNTIME_KEY, BIOCONDUCTOR_KEY, LIMMA_KEY, DESEQ2_KEY, EDGER_KEY],
        "required_contracts": ["B18 design matrix/contrast/value-type preflight", "B19 R adapter contract", "external engine dependency snapshot"],
        "result_semantics_policy": "B18 writes preflight_only manifest only; never formal_computed_result.",
        "boundary": "Design readiness is not execution readiness and cannot be displayed as a completed analysis.",
    }


def _static_row(
    capability_id: str,
    label: str,
    category: str,
    implementation_status: str,
    ui_state: str,
    reason: str,
    *,
    capability_keys: list[str],
) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "label": label,
        "category": category,
        "implementation_status": implementation_status,
        "ui_state": ui_state,
        "formal_execution_enabled": False,
        "can_display_as_completed": False,
        "reason": reason,
        "disabled_reason": reason,
        "dependency_capability_keys": capability_keys,
        "required_contracts": [],
        "result_semantics_policy": "Must not write formal_computed_result in B17.",
        "boundary": "Planned/design/spec-only capability is not a completed formal result.",
    }


def _status_from_survival_row(rows: list[dict[str, Any]] | None, row_id: str) -> str:
    for row in rows or []:
        if isinstance(row, dict) and str(row.get("row_id") or "") == row_id:
            return str(row.get("status") or "")
    return ""


def _capability_available(value: Any) -> bool | None:
    if isinstance(value, dict):
        if "available" in value:
            return bool(value.get("available"))
        status = str(value.get("status") or "").lower()
        if status in {"available", "passed", "ok", "true"}:
            return True
        if status in {"missing", "blocked", "failed", "not_configured", "false"}:
            return False
    if isinstance(value, bool):
        return value
    return None


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_state: dict[str, int] = {}
    for row in rows:
        state = str(row.get("ui_state") or "unknown")
        by_state[state] = by_state.get(state, 0) + 1
    completed_claims = [row["capability_id"] for row in rows if row.get("can_display_as_completed") is True]
    return {
        "row_count": len(rows),
        "by_ui_state": by_state,
        "completed_claim_count": len(completed_claims),
        "completed_claim_capabilities": completed_claims,
    }
