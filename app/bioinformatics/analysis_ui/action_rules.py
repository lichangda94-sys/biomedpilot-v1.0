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
    formal_deg_report_gate: dict[str, Any] | None = None,
    ora_input_gate: dict[str, Any] | None = None,
    ora_gene_set_gate: dict[str, Any] | None = None,
    ora_parameter_gate: dict[str, Any] | None = None,
    ora_result_schema_gate: dict[str, Any] | None = None,
    ora_dependency: dict[str, Any] | None = None,
    ora_plot_gate: dict[str, Any] | None = None,
    ora_report_gate: dict[str, Any] | None = None,
    gsea_plot_gate: dict[str, Any] | None = None,
    gsea_report_gate: dict[str, Any] | None = None,
    gsea_input_gate: dict[str, Any] | None = None,
    gsea_rank_metric_gate: dict[str, Any] | None = None,
    gsea_gene_set_gate: dict[str, Any] | None = None,
    gsea_parameter_gate: dict[str, Any] | None = None,
    gsea_result_schema_gate: dict[str, Any] | None = None,
    gsea_dependency: dict[str, Any] | None = None,
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
    formal_deg_report_gate = formal_deg_report_gate or {}
    ora_input_gate = ora_input_gate or {}
    ora_gene_set_gate = ora_gene_set_gate or {}
    ora_parameter_gate = ora_parameter_gate or {}
    ora_result_schema_gate = ora_result_schema_gate or {}
    ora_dependency = ora_dependency or {}
    ora_plot_gate = ora_plot_gate or {}
    ora_report_gate = ora_report_gate or {}
    gsea_plot_gate = gsea_plot_gate or {}
    gsea_report_gate = gsea_report_gate or {}
    gsea_input_gate = gsea_input_gate or {}
    gsea_rank_metric_gate = gsea_rank_metric_gate or {}
    gsea_gene_set_gate = gsea_gene_set_gate or {}
    gsea_parameter_gate = gsea_parameter_gate or {}
    gsea_result_schema_gate = gsea_result_schema_gate or {}
    gsea_dependency = gsea_dependency or {}

    deg_package = package_by_type.get("deg_recompute")
    imported_package = package_by_type.get("deg_imported_result")
    immune_package = package_by_type.get("immune_score_linkage")
    survival_package = package_by_type.get("tcga_clinical_survival_preflight")

    rows: list[dict[str, Any]] = []
    rows.append(_deg_preflight_action(deg_package))
    rows.append(_formal_deg_confirmation_action(deg_package, deg_dependency, deg_ready_gate, parameter_gate, result_schema_gate, confirmation_gate))
    rows.append(_formal_deg_action(deg_package, deg_dependency, deg_ready_gate, parameter_gate, confirmation_gate, result_schema_gate))
    rows.append(_gsea_readiness_action(gsea_input_gate, gsea_rank_metric_gate, gsea_gene_set_gate, gsea_parameter_gate, gsea_result_schema_gate, gsea_dependency))
    rows.append(_gsea_run_action(gsea_input_gate, gsea_rank_metric_gate, gsea_gene_set_gate, gsea_parameter_gate, gsea_result_schema_gate, gsea_dependency))
    rows.append(_imported_deg_action(imported_package, results))
    rows.append(_ora_readiness_action(ora_input_gate, ora_gene_set_gate, ora_parameter_gate, ora_result_schema_gate, ora_dependency))
    rows.append(_ora_run_action(ora_input_gate, ora_gene_set_gate, ora_parameter_gate, ora_result_schema_gate, ora_dependency))
    rows.append(_ora_plot_action(ora_plot_gate))
    rows.append(_ora_report_ready_action(ora_report_gate))
    rows.append(_gsea_plot_action(gsea_plot_gate))
    rows.append(_gsea_report_ready_action(gsea_report_gate))
    rows.append(_immune_action(immune_package, tasks))
    rows.append(_survival_preflight_action(survival_package, survival_dependency))
    rows.append(_constant_disabled_action("survival_formal", "Run formal survival analysis", "hidden_until_ready", "Survival remains design/preflight only; no KM/Cox/log-rank/HR output."))
    rows.append(_constant_disabled_action("km_cox_logrank", "KM/Cox/log-rank", "hidden_until_ready", "KM plot, Cox model and log-rank p-value are disabled until a later audited stage."))
    rows.append(_plot_action(results))
    rows.append(_markdown_draft_action(results, tasks))
    rows.append(_report_ready_action(report_gate, formal_deg_report_gate))
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


def _gsea_readiness_action(
    input_gate: dict[str, Any],
    rank_metric_gate: dict[str, Any],
    gene_set_gate: dict[str, Any],
    parameter_gate: dict[str, Any],
    result_schema_gate: dict[str, Any],
    dependency: dict[str, Any],
) -> dict[str, Any]:
    blockers = _gsea_blockers(input_gate, rank_metric_gate, gene_set_gate, parameter_gate, result_schema_gate, dependency)
    if input_gate.get("source_result_id") or blockers:
        return {
            "action_id": "gsea_preranked_readiness_review",
            "label": "Review GSEA preranked readiness",
            "state": "gate_review_available" if blockers else "ready_for_controlled_execution",
            "button_behavior": "enabled_gate_review_only",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Review source DEG, rank metric, ranked gene count, local GMT overlap, parameters, dependencies and result schema.",
        }
    return _disabled("gsea_preranked_readiness_review", "Review GSEA preranked readiness", "blocked_missing_result_schema", "gsea_source_result_missing", "Register a formal or imported DEG result before GSEA readiness review.")


def _gsea_run_action(
    input_gate: dict[str, Any],
    rank_metric_gate: dict[str, Any],
    gene_set_gate: dict[str, Any],
    parameter_gate: dict[str, Any],
    result_schema_gate: dict[str, Any],
    dependency: dict[str, Any],
) -> dict[str, Any]:
    blockers = _gsea_blockers(input_gate, rank_metric_gate, gene_set_gate, parameter_gate, result_schema_gate, dependency)
    if not blockers:
        return {
            "action_id": "formal_gsea",
            "label": "Run controlled preranked GSEA",
            "state": "enabled_controlled_preranked_gsea",
            "button_behavior": "enabled_controlled_preranked_gsea_mvp",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Run controlled preranked GSEA MVP with gene-set permutations only; no plot, report-ready, survival or clinical interpretation.",
        }
    reason = "; ".join(dict.fromkeys(blockers)) or "gsea_gate_not_passed"
    return _disabled("formal_gsea", "Run controlled preranked GSEA", "disabled_gsea_gate_not_passed", reason, "Resolve GSEA source, rank metric, gene set, parameters, dependencies and result schema gates.")


def _gsea_blockers(
    input_gate: dict[str, Any],
    rank_metric_gate: dict[str, Any],
    gene_set_gate: dict[str, Any],
    parameter_gate: dict[str, Any],
    result_schema_gate: dict[str, Any],
    dependency: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    for gate, fallback in (
        (input_gate, "gsea_input_gate_not_passed"),
        (rank_metric_gate, "gsea_rank_metric_gate_not_passed"),
        (gene_set_gate, "gsea_gene_set_gate_not_passed"),
        (parameter_gate, "gsea_parameter_gate_not_passed"),
        (result_schema_gate, "gsea_result_schema_gate_not_passed"),
        (dependency, "gsea_dependency_snapshot_not_passed"),
    ):
        if gate.get("status") != "passed":
            blockers.extend(_list(gate.get("blockers")) or [fallback])
    return list(dict.fromkeys(blockers))


def _ora_readiness_action(
    ora_input_gate: dict[str, Any],
    gene_set_gate: dict[str, Any],
    parameter_gate: dict[str, Any],
    result_schema_gate: dict[str, Any],
    dependency: dict[str, Any],
) -> dict[str, Any]:
    blockers = _ora_blockers(ora_input_gate, gene_set_gate, parameter_gate, result_schema_gate, dependency)
    source_id = str(ora_input_gate.get("source_result_id") or "")
    if source_id:
        return {
            "action_id": "ora_readiness_review",
            "label": "Review ORA readiness / Configure ORA",
            "state": "gate_review_available" if blockers else "ready_for_future_execution",
            "button_behavior": "enabled_gate_review_only",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Review source DEG semantics, selected gene policy, gene set resource, parameters and B10.1 disabled execution reasons.",
        }
    return _disabled(
        "ora_readiness_review",
        "Review ORA readiness / Configure ORA",
        "blocked_missing_result_schema",
        "; ".join(blockers or ["ora_source_deg_result_missing"]),
        "Register or import a DEG result before ORA readiness review.",
    )


def _ora_run_action(
    ora_input_gate: dict[str, Any],
    gene_set_gate: dict[str, Any],
    parameter_gate: dict[str, Any],
    result_schema_gate: dict[str, Any],
    dependency: dict[str, Any],
) -> dict[str, Any]:
    blockers = _ora_blockers(ora_input_gate, gene_set_gate, parameter_gate, result_schema_gate, dependency)
    if not blockers:
        return {
            "action_id": "run_ora_enrichment",
            "label": "Run controlled ORA enrichment",
            "state": "enabled_controlled_ora",
            "button_behavior": "enabled_controlled_ora_mvp",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Run controlled ORA from eligible DEG result and validated local GMT; register result index v2 table only.",
        }
    return _disabled(
        "run_ora_enrichment",
        "Run controlled ORA enrichment",
        "blocked_controlled_ora_gate",
        "; ".join(dict.fromkeys(blockers)),
        "Resolve ORA source, local GMT resource, parameters, result schema and dependency gates.",
    )


def _ora_blockers(
    ora_input_gate: dict[str, Any],
    gene_set_gate: dict[str, Any],
    parameter_gate: dict[str, Any],
    result_schema_gate: dict[str, Any],
    dependency: dict[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if ora_input_gate.get("status") != "passed":
        blockers.extend(_list(ora_input_gate.get("blockers")) or ["ora_input_gate_not_passed"])
    if gene_set_gate.get("status") != "passed" and gene_set_gate.get("validation_status") != "passed":
        blockers.extend(_list(gene_set_gate.get("blockers")) or ["ora_gene_set_gate_not_passed"])
    if parameter_gate.get("status") != "passed":
        blockers.extend(_list(parameter_gate.get("blockers")) or ["ora_parameter_gate_not_passed"])
    if result_schema_gate.get("status") != "passed":
        blockers.extend(_list(result_schema_gate.get("blockers")) or ["ora_result_schema_gate_not_passed"])
    if dependency.get("status") != "passed":
        blockers.extend(_list(dependency.get("blockers")) or ["ora_dependency_snapshot_not_passed"])
    return list(dict.fromkeys(blockers))


def _ora_plot_action(gate: dict[str, Any]) -> dict[str, Any]:
    if gate.get("status") == "passed":
        warnings = _list(gate.get("warnings"))
        return {
            "action_id": "ora_plot",
            "label": "Generate ORA plot artifact/spec",
            "state": "available",
            "button_behavior": "enabled_ora_plot_spec_only",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Create ORA plot artifact/spec only; no PNG/SVG/PDF rendering and no report-ready output." + (f" Warnings: {'; '.join(warnings)}" if warnings else ""),
        }
    blockers = _list(gate.get("blockers")) or ["ora_plot_gate_not_passed"]
    return _disabled(
        "ora_plot",
        "Generate ORA plot artifact/spec",
        "blocked_ora_plot_gate",
        "; ".join(blockers),
        "Register a valid ORA enrichment result before creating a spec-only ORA plot artifact.",
    )


def _ora_report_ready_action(gate: dict[str, Any]) -> dict[str, Any]:
    if gate.get("status") in {"eligible_for_ora_report_ready", "eligible_for_imported_derived_ora_report_package"}:
        warnings = _list(gate.get("warnings"))
        imported = gate.get("status") == "eligible_for_imported_derived_ora_report_package"
        return {
            "action_id": "ora_report_ready",
            "label": "Export ORA report-ready package" if not imported else "Export imported-derived ORA package",
            "state": "available_imported_derived" if imported else "available",
            "button_behavior": "enabled_imported_derived_ora_report_package" if imported else "enabled_ora_report_ready_package",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": (
                "Export ORA-only package with explicit imported-derived warning; no formal recomputed ORA label, GSEA, survival or clinical conclusions."
                if imported
                else "Export ORA-only report-ready package; no GSEA, survival, full integrated report or clinical conclusions."
            ) + (f" Warnings: {'; '.join(warnings)}" if warnings else ""),
        }
    blockers = _list(gate.get("blockers")) or ["ora_report_ready_gate_not_passed"]
    return _disabled(
        "ora_report_ready",
        "Export ORA report-ready package",
        "blocked_ora_report_ready_gate",
        "; ".join(blockers),
        "Resolve ORA result index, table, gene set, dependency, task log, plot/table-only and provenance gates.",
    )


def _gsea_plot_action(gate: dict[str, Any]) -> dict[str, Any]:
    if gate.get("status") == "passed":
        warnings = _list(gate.get("warnings"))
        return {
            "action_id": "gsea_plot",
            "label": "Generate GSEA plot artifact/spec",
            "state": "available",
            "button_behavior": "enabled_gsea_plot_spec_only",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Create GSEA plot artifact/spec only; no PNG/SVG/PDF rendering and no report-ready output." + (f" Warnings: {'; '.join(warnings)}" if warnings else ""),
        }
    blockers = _list(gate.get("blockers")) or ["gsea_plot_gate_not_passed"]
    return _disabled("gsea_plot", "Generate GSEA plot artifact/spec", "blocked_gsea_plot_gate", "; ".join(blockers), "Register a valid GSEA preranked result before creating a spec-only GSEA plot artifact.")


def _gsea_report_ready_action(gate: dict[str, Any]) -> dict[str, Any]:
    if gate.get("status") in {"eligible_for_gsea_report_ready", "eligible_for_imported_derived_gsea_report_package"}:
        warnings = _list(gate.get("warnings"))
        imported = gate.get("status") == "eligible_for_imported_derived_gsea_report_package"
        return {
            "action_id": "gsea_report_ready",
            "label": "Export GSEA report-ready package" if not imported else "Export imported-derived GSEA package",
            "state": "available_imported_derived" if imported else "available",
            "button_behavior": "enabled_imported_derived_gsea_report_package" if imported else "enabled_gsea_report_ready_package",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": (
                "Export GSEA-only package with explicit imported-derived warning; no formal recomputed GSEA label, survival or clinical conclusions."
                if imported
                else "Export GSEA-only report-ready package; no survival, full integrated report or clinical conclusions."
            ) + (f" Warnings: {'; '.join(warnings)}" if warnings else ""),
        }
    blockers = _list(gate.get("blockers")) or ["gsea_report_ready_gate_not_passed"]
    return _disabled("gsea_report_ready", "Export GSEA report-ready package", "blocked_gsea_report_ready_gate", "; ".join(blockers), "Resolve GSEA result index, table, gene set, dependency, task log, plot/table-only and provenance gates.")


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


def _report_ready_action(gate: dict[str, Any], formal_deg_gate: dict[str, Any] | None = None) -> dict[str, Any]:
    formal_deg_gate = formal_deg_gate or {}
    if formal_deg_gate.get("status") == "eligible_for_formal_deg_report_ready":
        return {
            "action_id": "report_ready_export",
            "label": "Export formal DEG report-ready package",
            "state": "available",
            "button_behavior": "enabled_b9_7_formal_deg_gate_passed",
            "enabled": True,
            "normal_user_visible": True,
            "disabled_reason": "",
            "next_action": "Export formal DEG section only; GSEA, survival and clinical conclusions remain disabled.",
        }
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
    formal_blockers = _list(formal_deg_gate.get("blockers")) if formal_deg_gate.get("selected_result_id") else []
    blockers = formal_blockers or _list(gate.get("blockers")) or ["blocked_report_ready_gate"]
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
