from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.services.audit_log_service import MetaAuditLogService


@dataclass(frozen=True)
class AuditLogPageState:
    title: str
    description: str
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    warning_summary: str
    audit_log_path: str = ""
    event_count: int = 0
    event_type_counts: dict[str, int] | None = None
    recent_events: tuple[str, ...] = ()


def initial_audit_log_state() -> AuditLogPageState:
    return AuditLogPageState(
        title="Audit Log / 审计日志",
        description="只读 testing 视图，汇总 import、sanitize、normalize、duplicate、screening、fulltext、extraction、analysis 和 report 事件。",
        status_label="测试中",
        input_summary="输入：Meta Analysis 项目目录。",
        output_summary="输出：audit/audit_log.jsonl 只读摘要，不替代 Task Center。",
        next_step="下一步：用于 PRISMA source references、traceability audit 和 reproducibility package 检查。",
        empty_state="没有 audit log 时显示空状态，不阻塞本地流程。",
        warning_summary="缺少 audit log 或缺少某类事件时只显示 warning，不崩溃。",
        event_type_counts={},
    )


def audit_log_state_from_project(project_dir: Path, *, service: MetaAuditLogService | None = None) -> AuditLogPageState:
    service = service or MetaAuditLogService()
    base = initial_audit_log_state()
    project_dir = project_dir.expanduser().resolve()
    events = service.list_events(project_dir)
    counts: dict[str, int] = {}
    for event in events:
        counts[event.event_type] = counts.get(event.event_type, 0) + 1
    recent = tuple(f"{event.created_at} | {event.event_type} | {event.target_type}:{event.target_id} | {event.summary}" for event in events[-10:])
    return AuditLogPageState(
        title=base.title,
        description=base.description,
        status_label=base.status_label,
        input_summary=base.input_summary,
        output_summary=base.output_summary,
        next_step=base.next_step,
        empty_state=base.empty_state,
        warning_summary=base.warning_summary,
        audit_log_path=str(service.audit_path(project_dir)),
        event_count=len(events),
        event_type_counts=counts,
        recent_events=recent,
    )


try:
    from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFrame = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class AuditLogPage(QWidget):
        def __init__(self, *, service: MetaAuditLogService | None = None) -> None:
            super().__init__()
            self._service = service or MetaAuditLogService()
            self._state = initial_audit_log_state()

            root = QVBoxLayout(self)
            title = QLabel(self._state.title)
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label}"))

            self._project_dir_input = QLineEdit()
            self._project_dir_input.setPlaceholderText("选择或粘贴项目目录路径")
            root.addWidget(self._project_dir_input)
            refresh = QPushButton("刷新 audit log 摘要")
            refresh.clicked.connect(self._refresh)
            root.addWidget(refresh)

            card = QFrame()
            card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(card)
            self._summary_label = QLabel("audit log 摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            layout.addWidget(self._summary_label)
            root.addWidget(card)
            root.addStretch(1)

        def _refresh(self) -> None:
            state = audit_log_state_from_project(Path(self._project_dir_input.text()).expanduser(), service=self._service)
            counts = "\n".join(f"- {key}: {value}" for key, value in sorted((state.event_type_counts or {}).items())) or "无"
            recent = "\n".join(state.recent_events) or "无"
            self._summary_label.setText(
                f"audit_log：{state.audit_log_path}\n"
                f"event_count：{state.event_count}\n"
                f"event_type_counts：\n{counts}\n"
                f"recent_events：\n{recent}"
            )

else:

    class AuditLogPage:  # type: ignore[no-redef]
        pass

