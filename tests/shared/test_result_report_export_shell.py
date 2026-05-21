from __future__ import annotations

import os

import pytest

from app.shared.result_report_export_shell import (
    DEFAULT_DISCLAIMER,
    ExportGateState,
    ResultPreviewState,
    empty_result_preview_state,
    export_actions,
    make_result_report_export_adoption_panel,
    report_ready_future_state,
    testing_summary_state as build_testing_summary_state,
)
from app.shared.semantic_keys import ReportStatusKey, ResultSemanticKey

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


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


def test_adoption_panel_uses_empty_state_by_default() -> None:
    try:
        from PySide6.QtWidgets import QApplication, QPushButton, QFrame
    except Exception as exc:  # pragma: no cover - optional GUI runtime.
        pytest.skip(f"PySide6 UI runtime unavailable: {exc}")

    QApplication.instance() or QApplication([])
    panel = make_result_report_export_adoption_panel(module="meta_analysis")
    buttons = panel.findChildren(QPushButton, "exportGatedButton")
    empty_state = panel.findChild(QFrame, "resultPreviewEmptyState")

    assert panel.property("adoptionModule") == "meta_analysis"
    assert panel.property("exportGate") == ExportGateState.DISABLED_EMPTY_RESULT.value
    assert panel.property("reportReadyPackageAllowed") is False
    assert panel.minimumHeight() >= 260
    assert empty_state is not None
    assert empty_state.minimumHeight() >= 128
    assert all(button.minimumHeight() >= 36 for button in buttons)
    assert all(button.property("formalActionEnabled") is False for button in buttons)
    assert all(not button.isEnabled() for button in buttons)
