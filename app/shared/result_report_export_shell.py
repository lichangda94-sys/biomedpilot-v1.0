from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.shared.semantic_keys import ExportKey, ReportStatusKey, ResultSemanticKey


class ResultPreviewState(StrEnum):
    EMPTY = "empty"
    IMPORTED_EXTERNAL = "imported_external"
    TESTING_SUMMARY = "testing_summary"
    REPORT_READY_FUTURE = "report_ready_future"


class ExportGateState(StrEnum):
    DISABLED_EMPTY_RESULT = "disabled_empty_result"
    ENABLED_TESTING_EXPORT = "enabled_testing_export"
    BLOCKED_FORMAL_REPORT_READY = "blocked_formal_report_ready"


@dataclass(frozen=True)
class ResultReportExportState:
    result_state: ResultPreviewState
    result_semantic_key: str
    report_status_key: str
    export_gate: ExportGateState
    export_enabled: bool
    gate_reason: str
    disclaimer: str
    generated_artifact_paths: tuple[str, ...] = ()

    @property
    def report_ready_package_allowed(self) -> bool:
        return False


@dataclass(frozen=True)
class ExportAction:
    format_key: str
    label: str
    enabled: bool
    gate_reason: str


DEFAULT_DISCLAIMER = (
    "当前 Result / Report / Export 壳层仅用于测试摘要、结果预览和报告草稿边界展示；"
    "不构成正式统计结果、正式图表、临床建议或 report-ready 交付包。"
)


def empty_result_preview_state(*, module: str = "shared") -> ResultReportExportState:
    return ResultReportExportState(
        result_state=ResultPreviewState.EMPTY,
        result_semantic_key=ResultSemanticKey.TESTING_SUMMARY_ONLY.value,
        report_status_key=ReportStatusKey.DRAFT.value,
        export_gate=ExportGateState.DISABLED_EMPTY_RESULT,
        export_enabled=False,
        gate_reason=f"{module}: 尚无可预览结果；请先完成受控 preflight 或导入外部结果。",
        disclaimer=DEFAULT_DISCLAIMER,
    )


def testing_summary_state(*, module: str = "shared") -> ResultReportExportState:
    return ResultReportExportState(
        result_state=ResultPreviewState.TESTING_SUMMARY,
        result_semantic_key=ResultSemanticKey.TESTING_SUMMARY_ONLY.value,
        report_status_key=ReportStatusKey.TESTING_SUMMARY.value,
        export_gate=ExportGateState.ENABLED_TESTING_EXPORT,
        export_enabled=True,
        gate_reason=f"{module}: 仅允许导出 testing summary / draft，不允许 report-ready 包。",
        disclaimer=DEFAULT_DISCLAIMER,
    )


def report_ready_future_state(*, module: str = "shared") -> ResultReportExportState:
    return ResultReportExportState(
        result_state=ResultPreviewState.REPORT_READY_FUTURE,
        result_semantic_key=ResultSemanticKey.FORMAL_COMPUTED_RESULT.value,
        report_status_key=ReportStatusKey.REPORT_READY_FUTURE.value,
        export_gate=ExportGateState.BLOCKED_FORMAL_REPORT_READY,
        export_enabled=False,
        gate_reason=f"{module}: report-ready 包是未来能力，当前壳层禁止生成。",
        disclaimer=DEFAULT_DISCLAIMER,
    )


def export_actions(
    state: ResultReportExportState,
    formats: tuple[ExportKey, ...] = (ExportKey.MARKDOWN, ExportKey.HTML, ExportKey.DOCX, ExportKey.CSV, ExportKey.XLSX),
) -> tuple[ExportAction, ...]:
    return tuple(
        ExportAction(
            format_key=format_key.value,
            label=format_key.value.replace("export.format.", "").upper(),
            enabled=state.export_enabled,
            gate_reason=state.gate_reason,
        )
        for format_key in formats
    )


def make_result_preview_empty_state(state: ResultReportExportState | None = None):
    from app.shared.ui_components.primitives import make_empty_state

    shell_state = state or empty_result_preview_state()
    empty = make_empty_state(
        "No result preview / 暂无结果预览",
        f"{shell_state.gate_reason} {shell_state.disclaimer}",
    )
    empty.setObjectName("resultPreviewEmptyState")
    empty.setProperty("resultSemanticKey", shell_state.result_semantic_key)
    empty.setProperty("reportStatusKey", shell_state.report_status_key)
    empty.setProperty("exportGate", shell_state.export_gate.value)
    return empty


def make_report_draft_boundary(state: ResultReportExportState | None = None):
    from PySide6.QtWidgets import QLabel, QVBoxLayout

    from app.shared.ui_components.primitives import make_card, make_status_chip

    shell_state = state or empty_result_preview_state()
    card = make_card(object_name="reportDraftBoundaryCard")
    card.setProperty("reportStatusKey", shell_state.report_status_key)
    layout = QVBoxLayout(card)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(8)
    layout.addWidget(make_status_chip(status_key=_visual_status_for_report(shell_state.report_status_key)))
    title = QLabel("Report draft boundary / 报告草稿边界")
    title.setObjectName("reportDraftBoundaryTitle")
    body = QLabel(shell_state.disclaimer)
    body.setObjectName("reportDraftBoundaryDisclaimer")
    body.setWordWrap(True)
    layout.addWidget(title)
    layout.addWidget(body)
    return card


def make_export_buttons(state: ResultReportExportState, formats: tuple[ExportKey, ...] = (ExportKey.MARKDOWN, ExportKey.HTML, ExportKey.DOCX)):
    from app.shared.ui_components.primitives import make_button

    buttons = []
    for action in export_actions(state, formats):
        button = make_button(f"导出 {action.label}", role="secondary")
        button.setObjectName("exportGatedButton")
        button.setProperty("formatKey", action.format_key)
        button.setProperty("exportGate", state.export_gate.value)
        button.setToolTip(action.gate_reason)
        button.setEnabled(action.enabled)
        buttons.append(button)
    return tuple(buttons)


def _visual_status_for_report(report_status_key: str) -> str:
    if report_status_key == ReportStatusKey.DRAFT.value:
        return "draft"
    if report_status_key == ReportStatusKey.TESTING_SUMMARY.value:
        return "testing"
    return "planned"
