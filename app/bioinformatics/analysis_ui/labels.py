from __future__ import annotations

from typing import Iterable


PACKAGE_LABELS = {
    "deg_recompute": "DEG recompute input",
    "deg_imported_result": "Imported DEG result",
    "enrichment_from_deg": "Enrichment from DEG",
    "gsea_preranked": "GSEA prerank preflight",
    "correlation_expression": "Expression correlation",
    "immune_score_linkage": "Immune / TME exploratory",
    "tcga_clinical_survival_preflight": "Survival / clinical preflight",
}

SEMANTICS_LABELS = {
    "formal_computed_result": "formal computed result",
    "imported_external_result": "imported external result",
    "testing_level": "testing level",
    "exploratory": "exploratory",
    "preflight_only": "preflight only",
    "configured_not_run": "configured only",
    "blocked": "blocked",
    "failed": "failed",
    "config_only": "config only",
}

STATUS_LABELS = {
    "available": "available",
    "config_only": "config only",
    "preflight_only": "preflight only",
    "exploratory": "exploratory",
    "developer_preview": "developer preview",
    "blocked": "blocked",
    "blocked_missing_resolver": "blocked: missing resolver",
    "blocked_missing_input_package": "blocked: missing input package",
    "blocked_missing_mapping": "blocked: missing mapping",
    "blocked_value_type": "blocked: incompatible value type",
    "blocked_missing_backend": "blocked: missing backend",
    "blocked_missing_parameters": "blocked: missing parameters",
    "blocked_missing_result_schema": "blocked: missing result schema",
    "blocked_missing_user_confirmation": "blocked: missing user confirmation",
    "blocked_report_ready_gate": "blocked: report-ready gate",
    "hidden_until_ready": "hidden until ready",
    "formal_ready_but_not_activated": "formal-ready gates passed; activation still blocked",
    "draft_only": "draft only",
}

REPAIR_GUIDANCE = {
    "missing_repository_manifest": "Return to data standardization and generate repository_manifest.json.",
    "missing_standardized_assets_registry": "Return to data standardization and generate the standardized asset registry.",
    "multiple_candidate_matrices_without_default_selection": "Return to standardization and select one default expression matrix.",
    "missing_expression_asset": "Add or rebuild a standardized expression/count matrix.",
    "missing_sample_metadata_asset": "Add or rebuild sample metadata before DEG preflight.",
    "missing_group_design_asset": "Confirm group/comparison design before DEG preflight.",
    "geo_probe_or_id_ref_requires_platform_mapping": "Import or confirm platform probe-to-gene mapping before formal DEG.",
    "display_value_type_not_allowed_for_count_model_deg": "Use display/correlation/immune routes or provide a raw count matrix.",
    "tpm_fpkm_or_log_expression_not_allowed_for_count_model_deg": "Use a display route or provide raw counts for count-model DEG.",
    "unknown_or_unsupported_value_type_for_deg": "Annotate the expression value type before DEG preflight.",
    "unknown_value_type_blocks_formal_deg": "Annotate the expression value type before formal DEG.",
    "gtex_must_not_auto_fill_tcga_normal_control": "Use TCGA normal samples or a later explicit batch-aware design.",
    "missing_imported_deg_result_asset": "Import an external DEG result table if you want to review imported results.",
    "missing_deg_result_for_enrichment": "Provide a validated DEG result before enrichment preflight.",
    "missing_deg_result_for_preranked_gsea": "Provide a validated ranked DEG result before GSEA preflight.",
    "gsea_preranked_requires_rank_metric_validation_in_later_stage": "GSEA remains disabled until rank metric validation is implemented.",
    "missing_clinical_asset": "Build or import TCGA clinical metadata before survival preflight.",
    "gtex_expression_cannot_be_auto_used_as_tcga_survival_normal_control": "Do not auto-use GTEx as TCGA survival control.",
    "missing_python_package:scipy": "Detect scipy first; do not run formal DEG or fake p-values while missing.",
    "missing_python_package:statsmodels": "Detect statsmodels first; do not run formal DEG or fake FDR while missing.",
    "dependency_snapshot_not_passed": "Formal DEG requires a passed dependency snapshot.",
    "missing_case_or_control_group": "Confirm a case/control comparison before formal DEG.",
    "same_case_control_group": "Case and control groups must be different.",
    "missing_case_samples": "Confirm case samples before formal DEG.",
    "missing_control_samples": "Confirm control samples before formal DEG.",
    "sample_group_mismatch": "Repair sample/group alignment before formal DEG.",
    "count_model_requested_for_display_value_type": "Do not route TPM/FPKM/log expression into count-model DEG.",
    "method_incompatible_with_count_value_type": "Use a count-model method for raw count matrices.",
    "invalid_pseudocount": "Set a non-negative pseudocount policy.",
    "missing_fdr_policy": "Select an FDR/multiple testing policy.",
    "b9_2_activation_required": "B9.1 only hardens gates; formal execution requires a later B9.2 audit.",
    "lifelines_missing_formal_survival_disabled": "Detect lifelines first; B13 KM/log-rank remains blocked while missing.",
    "km_logrank_parameter_confirmation_missing": "Confirm KM/log-rank parameters before running the controlled two-group MVP.",
    "km_parameter_gate_not_passed": "Resolve time/event/group/dependency blockers before KM/log-rank.",
    "cox_univariate_parameter_confirmation_missing": "Confirm single-variable Cox parameters before running the controlled MVP.",
    "cox_parameter_gate_not_passed": "Resolve time/event/covariate/dependency blockers before Cox.",
    "identifier_not_allowed_as_covariate": "Do not use sample/case identifiers as Cox covariates.",
    "too_many_categories": "Reduce or explicitly recode categories before Cox.",
    "too_few_events_for_multivariate": "Multivariate Cox design needs more events.",
    "user_confirmation_missing": "User confirmation is required before Cox design can advance.",
    "dependency_snapshot_missing": "A passed dependency snapshot is required before formal execution.",
    "dependency_snapshot_not_passed": "Dependency detection must pass before formal execution.",
    "preflight_only_source_cannot_generate_formal_plot": "Select a result-index source with plot-eligible semantics.",
    "result_index_missing_or_empty": "Register a validated result before report-ready export.",
    "unverified_testing_exploratory_or_imported_results_present": "Keep draft labels or promote only through audited formal result contracts.",
    "input_package_provenance_present": "Result must include input_package_id before report-ready export.",
    "parameters_manifest_present": "Result must include parameters before report-ready export.",
    "dependency_snapshot_present": "Result must include dependency_snapshot before report-ready export.",
    "validation_status_pass_or_warn_only": "Result validation must pass or warn before report-ready export.",
}


def label_package_type(value: object) -> str:
    text = str(value or "")
    return PACKAGE_LABELS.get(text, text or "unknown package")


def label_semantics(value: object) -> str:
    text = str(value or "")
    return SEMANTICS_LABELS.get(text, text or "unknown semantics")


def label_status(value: object) -> str:
    text = str(value or "")
    return STATUS_LABELS.get(text, text or "unknown")


def compact_list(values: Iterable[object], *, empty: str = "None") -> str:
    items = [str(item) for item in values if str(item)]
    return "；".join(items) if items else empty


def repair_guidance(blockers: Iterable[object], warnings: Iterable[object] = ()) -> str:
    keys = [str(item) for item in [*list(blockers), *list(warnings)] if str(item)]
    guidance = [REPAIR_GUIDANCE[item] for item in keys if item in REPAIR_GUIDANCE]
    if guidance:
        return "；".join(dict.fromkeys(guidance))
    if keys:
        return "Review blocker/warning in developer diagnostics."
    return "No repair needed."
