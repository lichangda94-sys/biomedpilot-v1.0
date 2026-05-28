from __future__ import annotations

from typing import Any

from app.shared.semantic_keys import AnalysisStatusKey, ReportStatusKey, ResultSemanticKey

from .labels import label_action


FORMAL_ACTION_IDS = {
    "formal_deg",
    "formal_ora",
    "formal_gsea",
    "km_logrank",
    "cox_univariate",
    "report_ready_package",
    "export_package",
}


def build_action_rows(*, has_project: bool, result_entries: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Build read-only action rows for the UIShell gate preview.

    This intentionally does not import or call formal executors. It mirrors the
    target action contract at the button/gate level only.
    """

    result_entries = result_entries or []
    has_any_result = bool(result_entries)
    has_imported_or_testing = any(
        str(entry.get("result_semantic_key") or "") in {ResultSemanticKey.IMPORTED_EXTERNAL_RESULT.value, ResultSemanticKey.TESTING_SUMMARY_ONLY.value}
        for entry in result_entries
    )
    return [
        _row(
            "deg_preflight",
            enabled=has_project,
            state="enabled_preflight_only" if has_project else "disabled_missing_project",
            button_behavior="enabled_preflight_only",
            disabled_reason="" if has_project else "open_or_create_project_first",
            result_semantic_key=AnalysisStatusKey.PREFLIGHT_ONLY.value,
            next_action="Open DEG input checks. This does not execute formal DEG.",
        ),
        _row(
            "formal_deg",
            enabled=False,
            state="blocked_until_carryover",
            button_behavior="disabled_formal_executor_not_carried",
            disabled_reason="formal_deg_requires_scoped_carryover_of_state_dependency_parameter_confirmation_result_schema_gates",
            result_semantic_key=ResultSemanticKey.FORMAL_COMPUTED_RESULT.value,
            next_action="Carry over gate contracts first; do not execute formal DEG in UI-C2b.",
        ),
        _row(
            "formal_ora",
            enabled=False,
            state="blocked_until_backend",
            button_behavior="disabled_formal_executor_not_productized",
            disabled_reason="formal_ora_product_gate_not_available_in_uishell",
            result_semantic_key=ResultSemanticKey.FORMAL_COMPUTED_RESULT.value,
            next_action="Keep ORA as preflight/testing until result schema and resource gates exist.",
        ),
        _row(
            "formal_gsea",
            enabled=False,
            state="hidden_until_ready",
            button_behavior="hidden_until_ready",
            disabled_reason="formal_gsea_executor_not_ready",
            result_semantic_key=ResultSemanticKey.FORMAL_COMPUTED_RESULT.value,
            next_action="Do not expose GSEA execution before rank metric validation and formal executor gates.",
        ),
        _row(
            "km_logrank",
            enabled=False,
            state="blocked_until_carryover",
            button_behavior="disabled_survival_executor_not_carried",
            disabled_reason="km_logrank_requires_survival_clinical_scoped_carryover",
            result_semantic_key=ResultSemanticKey.FORMAL_COMPUTED_RESULT.value,
            next_action="Keep survival preflight only until clinical/survival carry-over audit.",
        ),
        _row(
            "cox_univariate",
            enabled=False,
            state="blocked_until_carryover",
            button_behavior="disabled_clinical_executor_not_carried",
            disabled_reason="cox_requires_clinical_scoped_carryover_and_user_confirmation",
            result_semantic_key=ResultSemanticKey.FORMAL_COMPUTED_RESULT.value,
            next_action="Do not expose Cox execution in normal UI.",
        ),
        _row(
            "clinical_variable_audit",
            enabled=has_project,
            state="enabled_preflight_only" if has_project else "disabled_missing_project",
            button_behavior="enabled_preflight_only",
            disabled_reason="" if has_project else "open_or_create_project_first",
            result_semantic_key=AnalysisStatusKey.PREFLIGHT_ONLY.value,
            next_action="Show clinical variable audit/preflight only; no clinical conclusion.",
        ),
        _row(
            "result_review",
            enabled=has_any_result,
            state="enabled_review_only" if has_any_result else "disabled_empty_result",
            button_behavior="enabled_review_only" if has_any_result else "disabled_empty_result",
            disabled_reason="" if has_any_result else "no_result_index_entries",
            result_semantic_key=ResultSemanticKey.TESTING_SUMMARY_ONLY.value if has_imported_or_testing else ResultSemanticKey.TESTING_SUMMARY_ONLY.value,
            next_action="Review existing imported/testing/preflight rows only.",
        ),
        _row(
            "report_draft",
            enabled=has_project,
            state="enabled_review_only" if has_project else "disabled_missing_project",
            button_behavior="enabled_draft_preview_only" if has_project else "disabled_missing_project",
            disabled_reason="" if has_project else "open_or_create_project_first",
            result_semantic_key=ResultSemanticKey.TESTING_SUMMARY_ONLY.value,
            report_status_key=ReportStatusKey.DRAFT.value,
            next_action="Preview draft boundary only; no report-ready package generation.",
        ),
        _row(
            "report_ready_package",
            enabled=False,
            state="disabled_missing_report_ready",
            button_behavior="disabled_report_package_builder",
            disabled_reason="report_ready_gate_not_carried_or_not_passed",
            result_semantic_key=ResultSemanticKey.FORMAL_COMPUTED_RESULT.value,
            report_status_key=ReportStatusKey.REPORT_READY_FUTURE.value,
            next_action="Report-ready package remains future/gated.",
        ),
        _row(
            "export_package",
            enabled=False,
            state="disabled_missing_report_ready",
            button_behavior="disabled_export",
            disabled_reason="export_requires_report_ready_package_and_file_picker",
            result_semantic_key=ResultSemanticKey.TESTING_SUMMARY_ONLY.value,
            report_status_key=ReportStatusKey.DRAFT.value,
            next_action="Keep export disabled in UI-C2b.",
        ),
    ]


def _row(
    action_id: str,
    *,
    enabled: bool,
    state: str,
    button_behavior: str,
    disabled_reason: str,
    result_semantic_key: str,
    next_action: str,
    report_status_key: str = ReportStatusKey.DRAFT.value,
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "label": label_action(action_id),
        "state": state,
        "button_behavior": button_behavior,
        "enabled": enabled,
        "normal_user_visible": state != "hidden_until_ready",
        "disabled_reason": disabled_reason,
        "next_action": next_action,
        "result_semantic_key": result_semantic_key,
        "report_status_key": report_status_key,
        "formal_action": action_id in FORMAL_ACTION_IDS,
        "formal_action_enabled": False,
    }
