from __future__ import annotations

from app.shared.result_report_export_shell import (
    DEFAULT_DISCLAIMER,
    ExportGateState,
    ResultPreviewState,
    empty_result_preview_state,
    export_actions,
    report_ready_future_state,
    testing_summary_state as build_testing_summary_state,
)
from app.shared.semantic_keys import ReportStatusKey, ResultSemanticKey


def test_empty_result_state_gates_all_exports() -> None:
    state = empty_result_preview_state(module="bioinformatics")
    actions = export_actions(state)

    assert state.result_state is ResultPreviewState.EMPTY
    assert state.result_semantic_key == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert state.report_status_key == ReportStatusKey.DRAFT.value
    assert state.export_gate is ExportGateState.DISABLED_EMPTY_RESULT
    assert state.export_enabled is False
    assert state.report_ready_package_allowed is False
    assert state.generated_artifact_paths == ()
    assert "尚无可预览结果" in state.gate_reason
    assert all(not action.enabled for action in actions)


def test_testing_summary_allows_only_draft_style_exports() -> None:
    state = build_testing_summary_state(module="meta_analysis")
    actions = export_actions(state)

    assert state.result_state is ResultPreviewState.TESTING_SUMMARY
    assert state.result_semantic_key == ResultSemanticKey.TESTING_SUMMARY_ONLY.value
    assert state.report_status_key == ReportStatusKey.TESTING_SUMMARY.value
    assert state.export_gate is ExportGateState.ENABLED_TESTING_EXPORT
    assert state.export_enabled is True
    assert "仅允许导出 testing summary / draft" in state.gate_reason
    assert all(action.enabled for action in actions)
    assert all("report-ready" in action.gate_reason for action in actions)


def test_report_ready_future_is_blocked_in_shell() -> None:
    state = report_ready_future_state(module="shared")

    assert state.result_semantic_key == ResultSemanticKey.FORMAL_COMPUTED_RESULT.value
    assert state.report_status_key == ReportStatusKey.REPORT_READY_FUTURE.value
    assert state.export_gate is ExportGateState.BLOCKED_FORMAL_REPORT_READY
    assert state.export_enabled is False
    assert state.report_ready_package_allowed is False
    assert "未来能力" in state.gate_reason
    assert "禁止生成" in state.gate_reason


def test_disclaimer_blocks_formal_result_claims() -> None:
    assert "不构成正式统计结果" in DEFAULT_DISCLAIMER
    assert "正式图表" in DEFAULT_DISCLAIMER
    assert "report-ready" in DEFAULT_DISCLAIMER
