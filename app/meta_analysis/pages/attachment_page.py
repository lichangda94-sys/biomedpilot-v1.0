from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.models.attachments import ATTACHMENT_MODES
from app.meta_analysis.services.attachment_service import AttachmentService


@dataclass(frozen=True)
class AttachmentPageState:
    title: str
    description: str
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    warning_summary: str
    mode_options: tuple[str, ...]
    attachment_registry_path: str = ""
    missing_fulltext_report_path: str = ""
    attachment_count: int = 0
    missing_fulltext_count: int = 0
    file_status_summary: tuple[str, ...] = ()


def initial_attachment_state() -> AttachmentPageState:
    return AttachmentPageState(
        title="Full-text / Attachment",
        description="testing 附件登记视图，显示 attachment_registry、missing_fulltext_report，并明确 link / copy / ignore 文件处理状态；不自动下载 PDF。",
        status_label="测试中",
        input_summary="输入：项目目录、本地附件文件路径和 record_id。",
        output_summary="输出：attachment_registry、missing_fulltext_report、fulltext_registry 兼容记录和 Task Center 任务。",
        next_step="下一步：Full-text screening / Quality Assessment。",
        empty_state="没有附件时显示空状态，可继续手动记录 full-text availability。",
        warning_summary="路径失效、缺少 full-text 或 unsupported attachment mode 会显示用户可读 warning；不执行自动 PDF 下载。",
        mode_options=ATTACHMENT_MODES,
    )


def attachment_state_from_project(project_dir: Path, *, service: AttachmentService | None = None) -> AttachmentPageState:
    service = service or AttachmentService()
    base = initial_attachment_state()
    project_dir = project_dir.expanduser().resolve()
    attachments = service.list_attachments(project_dir)
    registry_path = project_dir / "attachments" / "attachment_registry.json"
    missing_path = project_dir / "reports" / "missing_fulltext_report.csv"
    file_status = tuple(
        f"{record.record_id}:{record.attachment_type}:{'available' if record.file_exists else 'missing'}:{record.file_name}"
        for record in attachments[:10]
    )
    missing_count = 0
    if missing_path.exists():
        missing_count = sum(1 for line in missing_path.read_text(encoding="utf-8").splitlines()[1:] if line.endswith(",true"))
    return AttachmentPageState(
        title=base.title,
        description=base.description,
        status_label=base.status_label,
        input_summary=base.input_summary,
        output_summary=base.output_summary,
        next_step=base.next_step,
        empty_state=base.empty_state,
        warning_summary=base.warning_summary,
        mode_options=base.mode_options,
        attachment_registry_path=str(registry_path),
        missing_fulltext_report_path=str(missing_path),
        attachment_count=len(attachments),
        missing_fulltext_count=missing_count,
        file_status_summary=file_status,
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class AttachmentPage(QWidget):
        def __init__(self, *, service: AttachmentService | None = None) -> None:
            super().__init__()
            self._service = service or AttachmentService()
            self._state = initial_attachment_state()

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

            self._record_id_input = QLineEdit()
            self._record_id_input.setPlaceholderText("record_id")
            root.addWidget(self._record_id_input)

            row = QHBoxLayout()
            self._file_input = QLineEdit()
            self._file_input.setPlaceholderText("选择或粘贴本地附件文件路径")
            choose = QPushButton("选择附件")
            choose.clicked.connect(self._choose_file)
            row.addWidget(self._file_input, 1)
            row.addWidget(choose)
            root.addLayout(row)

            buttons = QHBoxLayout()
            for label, mode in (("Link existing", "link_existing_files"), ("Copy to project", "copy_to_project_library"), ("Ignore", "ignore_attachments")):
                button = QPushButton(label)
                button.clicked.connect(lambda _checked=False, value=mode: self._apply_mode(value))
                buttons.addWidget(button)
            root.addLayout(buttons)

            refresh = QPushButton("刷新附件摘要")
            refresh.clicked.connect(self._refresh)
            root.addWidget(refresh)

            card = QFrame()
            card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            layout = QVBoxLayout(card)
            self._summary_label = QLabel("附件摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            layout.addWidget(self._summary_label)
            root.addWidget(card)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择附件", "", "All files (*)")
            if path:
                self._file_input.setText(path)

        def _apply_mode(self, mode: str) -> None:
            if mode != "ignore_attachments":
                self._service.add_attachment(
                    Path(self._project_dir_input.text()).expanduser(),
                    record_id=self._record_id_input.text(),
                    source_file_path=self._file_input.text(),
                    attachment_type="pdf",
                    mode=mode,
                )
            self._refresh()

        def _refresh(self) -> None:
            state = attachment_state_from_project(Path(self._project_dir_input.text()).expanduser(), service=self._service)
            self._summary_label.setText(
                f"attachment_registry：{state.attachment_registry_path}\n"
                f"missing_fulltext_report：{state.missing_fulltext_report_path}\n"
                f"附件数量：{state.attachment_count}\n"
                f"缺失 full-text：{state.missing_fulltext_count}\n"
                f"文件状态：\n" + "\n".join(state.file_status_summary)
            )

else:

    class AttachmentPage:  # type: ignore[no-redef]
        pass

