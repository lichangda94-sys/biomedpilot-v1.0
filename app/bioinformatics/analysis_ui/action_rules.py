from __future__ import annotations

from typing import Any

from app.bioinformatics.results.models import normalize_result_semantics


FORMAL_DISABLED_REASON = "Formal DEG is limited to audited two-group controlled DEG MVP."


def build_action_rows(
    *,
    packages: list[dict[str, Any]],
    tasks: list[dict[str, Any]] | None = None,
    results: list[dict[str, Any]] | None = None,
    deg_dependency: dict[str, Any] | None = None,
    deg_ready_gate: dict[str, Any] | None = None,
    parameter_gate: dict[str, Any] | None = None,
    confirmation_gate: dict[str, Any] | None = None,
    result_schema_gate: dict[str, Any] | None = None,
    survival_dependency: dict[str, Any] | None = None,
    report_gate: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    package_by_type = {str(item.get("package_type") or ""): item for item in packages if isinstance(item, dict)}
    tasks = tasks or []
    results = results or []
    deg_dependency = deg_dependency or {}
    deg_ready_gate = deg_ready_gate or {}
    parameter_gate = parameter_gate or {}
    confirmation_gate = confirmation_gate or {}
    result_schema_gate = result_schema_gate or {}
    survival_dependency = survival_dependency or {}
    report_gate = report_gate or {}

    deg_package = package_by_type.get("deg_recompute")
    imported_package = package_by_type.get("deg_imported_result")
    immune_package = package_by_type.get("immune_score_linkage")
    survival_package = package_by_type.get("tcga_clinical_survival_preflight")

    rows: list[dict[str, Any]] = []
    rows.append(_deg_preflight_action(deg_package))
    rows.append(_formal_deg_confirmation_action(deg_package, deg_dependency, deg_ready_gate, parameter_gate, result_schema_gate, confirmation_gate))
    rows.append(_formal_deg_action(deg_package, deg_dependency, deg_ready_gate, parameter_gate, confirmation_gate, result_schema_gate))
    rows.append(_constant_disabled_action("formal_gsea", "Run formal GSEA", "hidden_until_ready", "GSEA formal executor is not implemented in B8.9."))
    rows.append(_imported_deg_action(imported_package, results))
    rows.append(_immune_action(immune_package, tasks))
    rows.append(_survival_preflight_action(survival_package, survival_dependency))
    rows.append(_constant_disabled_action("survival_formal", "Run formal survival analysis", "hidden_until_ready", "Survival remains design/preflight only; no KM/Cox/log-rank/HR output."))
    rows.append(_constant_disabled_action("km_cox_logrank", "KM/Cox/log-rank", "hidden_until_ready", "KM plot, Cox model and log-rank p-value are disabled until a later audited stage."))
    rows.append(_plot_action(results))
    rows.append(_markdown_draft_action(results, tasks))
    rows.append(_report_ready_action(report_gate))
    rows.append(
        {
            "action_id": "developer_geo_deg_runner",
            "label": "Developer testing GEO DEG runner",
            "state": "developer_preview",
            "button_behavior": "developer_diagnostics_only",
            "enabled": True,
            "normal_user_visible": False,
            "disabled_reason": "",
            "next_action": "Use only from developer diagnostics; output remains testing_level.",
        }
    )
    return rows


def _deg_preflight_action(package: dict[str, Any] | None) -> dict[str, Any]:
    if not package:
        return _disabled("deg_preflight", "Configure DEG / Run DEG preflight", "blocked_missing_resolver", "No resolver package exists.", "Return to standardization.")
    blockers = _list(package.get("blockers"))
    missing_minimum = [item for item in blockers if item in {"missing_expression_asset", "missing_sample_metadata_asset", "missing_group_design_asset", "multiple_candidate_matrices_without_default_selection"}]
    if missing_minimum:
        return _disabled("deg_preflight", "Configure DEG / Run DEG preflight", "blocked_missing_input_package", "; ".join(missing_minimum), "Repair standardized package inputs.")
    return {
        "action_id": "deg_preflight",
        "label": "Configure DEG / Run DEG preflight",
        "state": "preflight_only" if blockers else "config_only",
        "button_behavior": "enabled_preflight_only",
        "enabled": True,
        "normal_user_visible": True,
        "disabled_reason": "",
        "next_action": "Open DEG config; this does not execute formal DEG.",
    }


def _formal_deg_action(
    package: dict[str, Any] | None,
    dependency: dict[str, Any],
    deg_ready_gate: dict[str, Any],
    parameter_gate: dict[str, Any],
    confirmation_gate: dict[str, Any],
    result_schema_gate: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    state = "hidden_until_ready"
    if not package:
        blockers.append("missing_deg_recompute_input_package")
        state = "blocked_missing_resolver"
    else:
        package_blockers = _list(package.get("blockers"))
        blockers.extend(package_blockers)
        if any("mapping" in item or "probe" in item or "ID_REF" in item for item in package_blockers):
            state = "blocked_missing_mapping"
        elif any("value_type" in item or "TPM" in item or "FPKM" in item for item in package_blockers):
            state = "blocked_value_type"
        elif package_blockers:
            state = "blocked_missing_input_package"
    dependency_blockers = _list(dependency.get("blockers"))
    if dependency.get("status") != "passed":
        blockers.extend(dependency_blockers or ["deg_backend_dependency_not_passed"])
        state = "blocked_missing_backend"
    if deg_ready_gate.get("status") != "passed":
        blockers.extend(_list(deg_ready_gate.get("blockers")) or ["deg_ready_gate_not_passed"])
        if state == "hidden_until_ready":
            state = "blocked_missing_input_package"
    if parameter_gate.get("status") != "passed":
        blockers.extend(_list(parameter_gate.get("blockers")) or ["parameter_gate_not_passed"])
        if state == "hidden_until_ready":
            state = "blocked_missing_parameters"
    if result_schema_gate.get("status") != "passed":
        blockers.extend(_list(result_schema_gate.get("blockers")) or ["result_schema_gate_not_passed"])
        if state == "hidden_until_ready":
            state = "blocked_missing_result_schema"
    if confirmation_gate.get("status") != "passed":
        blockers.extend(_list(confirmation_gate.get("blockers")) or ["formal_deg_parameter_confirmation_missing"])
        if state == "hidden_until_ready":
            state = "blocked_missing_user_confirmation"
    if state == "hidden_until_ready":
        return {
            "action_id": "formal_deg",
            "label": "Run controlled two-group DEG",
            "state": "enabled_formal_deg",
            "button_behavior": "enabled_controlled_two_group_mvp",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Run audited two-group controlled DEG MVP with confirmed parameters and register result index v2 output.",
        }
    return _disabled("formal_deg", "Run controlled two-group DEG", state, "; ".join(dict.fromkeys(blockers + [FORMAL_DISABLED_REASON])), "Resolve resolver, DEG-ready, dependency, parameter, user confirmation and result schema gates.")


def _formal_deg_confirmation_action(
    package: dict[str, Any] | None,
    dependency: dict[str, Any],
    deg_ready_gate: dict[str, Any],
    parameter_gate: dict[str, Any],
    result_schema_gate: dict[str, Any],
    confirmation_gate: dict[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    if not package:
        blockers.append("missing_deg_recompute_input_package")
    else:
        blockers.extend(_list(package.get("blockers")))
    if dependency.get("status") != "passed":
        blockers.extend(_list(dependency.get("blockers")) or ["deg_backend_dependency_not_passed"])
    if deg_ready_gate.get("status") != "passed":
        blockers.extend(_list(deg_ready_gate.get("blockers")) or ["deg_ready_gate_not_passed"])
    if parameter_gate.get("status") != "passed":
        blockers.extend(_list(parameter_gate.get("blockers")) or ["parameter_gate_not_passed"])
    if result_schema_gate.get("status") != "passed":
        blockers.extend(_list(result_schema_gate.get("blockers")) or ["result_schema_gate_not_passed"])
    if blockers:
        return _disabled("formal_deg_parameter_confirmation", "Confirm formal DEG parameters", "blocked_missing_parameters", "; ".join(dict.fromkeys(blockers)), "Resolve formal DEG gates before confirmation.")
    if confirmation_gate.get("status") == "passed":
        return {
            "action_id": "formal_deg_parameter_confirmation",
            "label": "Confirm formal DEG parameters",
            "state": "confirmed",
            "button_behavior": "enabled_reconfirm_parameters_only",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Parameters are confirmed; re-confirm only if comparison, method, thresholds or dependencies changed.",
        }
    return {
        "action_id": "formal_deg_parameter_confirmation",
        "label": "Confirm formal DEG parameters",
        "state": "requires_user_confirmation",
        "button_behavior": "enabled_parameter_confirmation_only",
        "enabled": True,
        "normal_user_visible": True,
        "disabled_reason": "",
        "next_action": "Review comparison, method, thresholds, value type policy, dependencies and output plan before formal DEG.",
    }


def _imported_deg_action(package: dict[str, Any] | None, results: list[dict[str, Any]]) -> dict[str, Any]:
    has_imported_result = any(normalize_result_semantics(item.get("canonical_result_semantics") or item.get("result_semantics")) == "imported_external_result" for item in results)
    if package and not _list(package.get("blockers")) or has_imported_result:
        return {
            "action_id": "imported_deg_review",
            "label": "Review imported DEG",
            "state": "available",
            "button_behavior": "enabled_review_only",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Review external result with imported_external_result semantics.",
        }
    return _disabled("imported_deg_review", "Review imported DEG", "blocked_missing_input_package", "missing imported DEG package/result", "Import an external DEG result if needed.")


def _immune_action(package: dict[str, Any] | None, tasks: list[dict[str, Any]]) -> dict[str, Any]:
    if package and not _list(package.get("blockers")):
        return {
            "action_id": "immune_tme_scoring",
            "label": "Immune / TME scoring",
            "state": "exploratory",
            "button_behavior": "enabled_exploratory_only",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Open exploratory scoring; do not present as clinical conclusion.",
        }
    task_ready = any(str(item.get("analysis_type") or "") == "immune_infiltration" and item.get("can_run") for item in tasks)
    if task_ready:
        return {
            "action_id": "immune_tme_scoring",
            "label": "Immune / TME scoring",
            "state": "exploratory",
            "button_behavior": "enabled_exploratory_only",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Open exploratory scoring; readiness can_run is not formal execution readiness.",
        }
    return _disabled("immune_tme_scoring", "Immune / TME scoring", "blocked_missing_input_package", "missing exploratory expression package", "Repair expression package first.")


def _survival_preflight_action(package: dict[str, Any] | None, dependency: dict[str, Any]) -> dict[str, Any]:
    if not package:
        return _disabled("survival_preflight", "Survival / clinical preflight", "blocked_missing_input_package", "missing survival preflight package", "Build clinical metadata first.")
    blockers = _list(package.get("blockers"))
    dep_blockers = _list(dependency.get("blockers"))
    if blockers:
        return _disabled("survival_preflight", "Survival / clinical preflight", "blocked_missing_input_package", "; ".join(blockers), "Repair clinical/expression assets.")
    return {
        "action_id": "survival_preflight",
        "label": "Survival / clinical preflight",
        "state": "preflight_only",
        "button_behavior": "enabled_preflight_only",
        "enabled": True,
        "normal_user_visible": True,
        "disabled_reason": "; ".join(dep_blockers),
        "next_action": "Preflight/design only; formal survival remains disabled.",
    }


def _plot_action(results: list[dict[str, Any]]) -> dict[str, Any]:
    eligible: list[str] = []
    blocked_sources: list[str] = []
    for entry in results:
        semantics = normalize_result_semantics(entry.get("canonical_result_semantics") or entry.get("result_semantics"))
        result_id = str(entry.get("result_id") or entry.get("result_name") or "")
        task_type = str(entry.get("task_type") or "").lower()
        has_deg_table = any(isinstance(item, dict) and item.get("artifact_type") == "deg_result_table" for item in entry.get("output_artifacts", []) or [])
        if semantics == "formal_computed_result" and task_type == "deg" and has_deg_table:
            eligible.append(result_id or "result")
        elif semantics == "preflight_only":
            blocked_sources.append(f"{result_id}:preflight_only_source_cannot_generate_formal_plot")
        elif semantics in {"testing_level", "exploratory", "imported_external_result"}:
            blocked_sources.append(f"{result_id}:formal_deg_plot_requires_formal_computed_result_source")
    if eligible:
        return {
            "action_id": "plot_spec",
            "label": "Generate formal DEG plot artifact",
            "state": "available",
            "button_behavior": "enabled_formal_deg_plot_artifact_only",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Use formal_computed_result DEG source only; plot artifact inherits source semantics and does not create report-ready output.",
        }
    reason = "; ".join(blocked_sources) if blocked_sources else "No plot-eligible source result in result index."
    return _disabled("plot_spec", "Generate formal DEG plot artifact", "blocked_missing_result_schema", reason, "Register a formal_computed_result DEG result with a DEG result table.")


def _markdown_draft_action(results: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> dict[str, Any]:
    if results or tasks:
        return {
            "action_id": "markdown_draft",
            "label": "Generate Markdown draft",
            "state": "draft_only",
            "button_behavior": "enabled_draft_only",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Generate report draft with semantic labels preserved.",
        }
    return _disabled("markdown_draft", "Generate Markdown draft", "blocked_missing_result_schema", "No result or task record exists.", "Create a configuration record or import a result first.")


def _report_ready_action(gate: dict[str, Any]) -> dict[str, Any]:
    if gate.get("status") == "eligible_for_internal_report":
        return {
            "action_id": "report_ready_export",
            "label": "Export report-ready package",
            "state": "available",
            "button_behavior": "enabled_b8_6_gate_passed",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Export package through B8.6 gate.",
        }
    blockers = _list(gate.get("blockers")) or ["blocked_report_ready_gate"]
    return _disabled("report_ready_export", "Export report-ready package", "blocked_report_ready_gate", "; ".join(blockers), "Resolve B8.6 report-ready gate first.")


def _constant_disabled_action(action_id: str, label: str, state: str, reason: str) -> dict[str, Any]:
    return _disabled(action_id, label, state, reason, "No formal execution in B8.9.")


def _disabled(action_id: str, label: str, state: str, reason: str, next_action: str) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "label": label,
        "state": state,
        "button_behavior": "disabled",
        "enabled": False,
        "normal_user_visible": state != "hidden_until_ready",
        "disabled_reason": reason,
        "next_action": next_action,
    }


def _list(value: object) -> list[str]:
    if isinstance(value, list | tuple):
        return [str(item) for item in value if str(item)]
    return []
