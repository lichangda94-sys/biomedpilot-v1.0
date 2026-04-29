from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.models.attachments import ATTACHMENT_MODES
from app.meta_analysis.pages.warning_severity import WarningSeverityItem, classify_warning_severity, warning_severity_counts
from app.meta_analysis.services.attachment_service import AttachmentService
from app.meta_analysis.services.criteria_service import CriteriaBuilderService
from app.meta_analysis.services.fulltext_service import FullTextService


@dataclass(frozen=True)
class AttachmentFileRow:
    record_id: str
    file_name: str
    attachment_type: str
    file_exists: bool
    storage_mode: str
    file_path: str


@dataclass(frozen=True)
class MissingFullTextRow:
    record_id: str
    missing_fulltext: bool


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
    attachment_registry_missing: bool = False
    attachment_registry_warning: str = ""
    missing_fulltext_report_path: str = ""
    attachment_count: int = 0
    pdf_attachment_count: int = 0
    link_attachment_count: int = 0
    copy_attachment_count: int = 0
    ignore_attachment_count: int = 0
    missing_attachment_count: int = 0
    broken_path_count: int = 0
    missing_fulltext_report_status: str = "not_generated"
    missing_fulltext_count: int = 0
    missing_fulltext_rows: tuple[MissingFullTextRow, ...] = ()
    fulltext_registry_path: str = ""
    fulltext_record_count: int = 0
    attachment_validation_status: str = "not_run"
    attachment_validation_message: str = "没有附件时显示空状态。"
    attachment_rows: tuple[AttachmentFileRow, ...] = ()
    file_status_summary: tuple[str, ...] = ()
    panel_help: tuple[str, ...] = ()
    testing_limitations: tuple[str, ...] = ()
    warning_severity_items: tuple[WarningSeverityItem, ...] = ()
    warning_severity_counts: dict[str, int] | None = None
    criteria_summary_path: str = ""
    criteria_hints: tuple[str, ...] = ()


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
        panel_help=(
            "当前面板显示 attachment_registry.json、missing_fulltext_report.csv 和附件路径验证状态。",
            "输入来自项目目录和用户手动 link/copy 的本地文件；输出写入 attachments、fulltext 和 reports 目录。",
            "warning 表示附件缺失、路径失效或 full-text 尚未绑定。",
            "下一步建议：导出 missing full-text report，并在 Full-text screening / Quality 前补齐必要 PDF。",
        ),
        testing_limitations=(
            "Developer Preview / testing：不自动下载 PDF。",
            "不执行 OCR、网页抓取、机构代理登录或版权受限下载。",
        ),
    )


def attachment_state_from_project(
    project_dir: Path,
    *,
    service: AttachmentService | None = None,
    criteria_service: CriteriaBuilderService | None = None,
) -> AttachmentPageState:
    service = service or AttachmentService()
    criteria_service = criteria_service or CriteriaBuilderService()
    base = initial_attachment_state()
    project_dir = project_dir.expanduser().resolve()
    attachments = service.list_attachments(project_dir)
    registry_path = project_dir / "attachments" / "attachment_registry.json"
    raw_registry = _load_attachment_registry(registry_path)
    fulltext_registry_path = project_dir / "fulltext" / "fulltext_registry.json"
    missing_path = project_dir / "reports" / "missing_fulltext_report.csv"
    attachment_rows = tuple(
        AttachmentFileRow(
            record_id=record.record_id,
            file_name=record.file_name,
            attachment_type=record.attachment_type,
            file_exists=_file_exists(record.file_path),
            storage_mode=_storage_mode(project_dir, record.file_path),
            file_path=record.file_path,
        )
        for record in attachments
    )
    file_status = tuple(
        f"{row.record_id}:{row.attachment_type}:{'available' if row.file_exists else 'missing'}:{row.file_name}"
        for row in attachment_rows[:10]
    )
    missing_report_status, missing_rows = _missing_fulltext_report_rows(missing_path)
    broken_path_count = len([row for row in attachment_rows if not row.file_exists])
    severity_items = _attachment_warning_severity_items(
        registry_missing=not registry_path.exists(),
        broken_path_count=broken_path_count,
        missing_fulltext_count=len([row for row in missing_rows if row.missing_fulltext]),
    )
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
        attachment_registry_missing=not registry_path.exists(),
        attachment_registry_warning="" if registry_path.exists() else "attachment_registry.json 尚未生成；当前仅显示空状态，不影响后续手动 link/copy 附件。",
        missing_fulltext_report_path=str(missing_path),
        attachment_count=len(attachments),
        pdf_attachment_count=len([row for row in attachment_rows if row.attachment_type == "pdf"]),
        link_attachment_count=len([row for row in attachment_rows if row.storage_mode == "link_existing_files"]),
        copy_attachment_count=len([row for row in attachment_rows if row.storage_mode == "copy_to_project_library"]),
        ignore_attachment_count=_ignored_attachment_count(raw_registry),
        missing_attachment_count=len([row for row in attachment_rows if not row.file_exists]),
        broken_path_count=broken_path_count,
        missing_fulltext_report_status=missing_report_status,
        missing_fulltext_count=len([row for row in missing_rows if row.missing_fulltext]),
        missing_fulltext_rows=missing_rows,
        fulltext_registry_path=str(fulltext_registry_path),
        fulltext_record_count=_fulltext_record_count(fulltext_registry_path),
        attachment_validation_status=_validation_status(len(attachment_rows), broken_path_count),
        attachment_validation_message=_validation_message(len(attachment_rows), broken_path_count),
        attachment_rows=attachment_rows,
        file_status_summary=file_status,
        panel_help=base.panel_help,
        testing_limitations=base.testing_limitations,
        warning_severity_items=severity_items,
        warning_severity_counts=warning_severity_counts(severity_items),
        criteria_summary_path=str(project_dir / "criteria" / "criteria_summary.md"),
        criteria_hints=criteria_service.criteria_hints(project_dir, stage="full_text"),
    )


def _file_exists(file_path: str) -> bool:
    try:
        path = Path(file_path).expanduser()
        return path.exists() and path.is_file()
    except (OSError, RuntimeError, ValueError):
        return False


def _storage_mode(project_dir: Path, file_path: str) -> str:
    try:
        path = Path(file_path).expanduser().resolve()
        path.relative_to(project_dir)
        return "copy_to_project_library"
    except (OSError, RuntimeError, ValueError):
        return "link_existing_files"


def _missing_fulltext_report_rows(missing_path: Path) -> tuple[str, tuple[MissingFullTextRow, ...]]:
    if not missing_path.exists():
        return "not_generated", ()
    try:
        with missing_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except (OSError, csv.Error, UnicodeDecodeError):
        return "unreadable", ()
    return "available", tuple(
        MissingFullTextRow(
            record_id=str(row.get("record_id", "")),
            missing_fulltext=str(row.get("missing_fulltext", "")).strip().lower() == "true",
        )
        for row in rows
    )


def _fulltext_record_count(fulltext_registry_path: Path) -> int:
    if not fulltext_registry_path.exists():
        return 0
    try:
        import json

        payload = json.loads(fulltext_registry_path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    records = payload.get("fulltext_files")
    return len(records) if isinstance(records, list) else 0


def _load_attachment_registry(registry_path: Path) -> dict[str, object]:
    if not registry_path.exists():
        return {}
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _ignored_attachment_count(registry_payload: dict[str, object]) -> int:
    ignored = registry_payload.get("ignored_attachments")
    if isinstance(ignored, list):
        return len(ignored)
    attachments = registry_payload.get("attachments")
    if not isinstance(attachments, list):
        return 0
    return len(
        [
            item
            for item in attachments
            if isinstance(item, dict)
            and str(item.get("storage_mode") or item.get("mode") or "").strip() == "ignore_attachments"
        ]
    )


def _validation_status(attachment_count: int, broken_path_count: int) -> str:
    if attachment_count == 0:
        return "empty"
    if broken_path_count:
        return "broken_paths_detected"
    return "valid"


def _validation_message(attachment_count: int, broken_path_count: int) -> str:
    if attachment_count == 0:
        return "没有附件登记；可手动 link/copy PDF 或导出 missing full-text report。"
    if broken_path_count:
        return f"发现 {broken_path_count} 个附件路径失效，请检查本地文件位置。"
    return "附件路径验证通过。"


def _attachment_warning_severity_items(
    *,
    registry_missing: bool,
    broken_path_count: int,
    missing_fulltext_count: int,
) -> tuple[WarningSeverityItem, ...]:
    items: list[WarningSeverityItem] = []
    if registry_missing:
        items.append(
            WarningSeverityItem(
                key="attachment_registry_missing",
                severity=classify_warning_severity(context="attachment", key="attachment_registry_missing"),
                message="attachment_registry.json 尚未生成。",
            )
        )
    if broken_path_count:
        items.append(
            WarningSeverityItem(
                key="broken_path_count",
                severity=classify_warning_severity(context="attachment", key="broken_path_count", count=broken_path_count),
                message=f"{broken_path_count} 个附件路径失效。",
            )
        )
    if missing_fulltext_count:
        items.append(
            WarningSeverityItem(
                key="missing_fulltext_count",
                severity=classify_warning_severity(context="attachment", key="missing_fulltext_count", count=missing_fulltext_count),
                message=f"{missing_fulltext_count} 条记录缺少 full-text PDF。",
            )
        )
    return tuple(items)


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class AttachmentPage(QWidget):
        def __init__(self, *, service: AttachmentService | None = None, fulltext_service: FullTextService | None = None) -> None:
            super().__init__()
            self._service = service or AttachmentService()
            self._fulltext_service = fulltext_service or FullTextService(attachment_service=self._service)
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

            self._missing_record_ids_input = QLineEdit()
            self._missing_record_ids_input.setPlaceholderText("missing report record_ids，用逗号分隔；为空时使用已有附件记录")
            root.addWidget(self._missing_record_ids_input)

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

            validate = QPushButton("验证附件路径")
            validate.clicked.connect(self._validate_attachments)
            root.addWidget(validate)

            export_missing = QPushButton("导出 missing_fulltext_report.csv")
            export_missing.clicked.connect(self._export_missing_report)
            root.addWidget(export_missing)

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
            if mode in {"link_existing_files", "copy_to_project_library"}:
                self._fulltext_service.attach_pdf(
                    Path(self._project_dir_input.text()).expanduser(),
                    record_id=self._record_id_input.text(),
                    source_file_path=self._file_input.text(),
                    mode=mode,
                )
            elif mode == "ignore_attachments":
                self._fulltext_service.attach_pdf(
                    Path(self._project_dir_input.text()).expanduser(),
                    record_id=self._record_id_input.text(),
                    source_file_path=self._file_input.text(),
                    mode=mode,
                )
            self._refresh()

        def _validate_attachments(self) -> None:
            self._service.validate_attachments(Path(self._project_dir_input.text()).expanduser())
            self._refresh()

        def _export_missing_report(self) -> None:
            record_ids = [
                item.strip()
                for item in self._missing_record_ids_input.text().split(",")
                if item.strip()
            ]
            self._service.export_missing_fulltext_report(
                Path(self._project_dir_input.text()).expanduser(),
                record_ids=record_ids or None,
            )
            self._refresh()

        def _refresh(self) -> None:
            state = attachment_state_from_project(Path(self._project_dir_input.text()).expanduser(), service=self._service)
            attachment_rows = "\n".join(
                f"- {row.record_id}: {row.file_name} · {row.attachment_type} · {'exists' if row.file_exists else 'missing'} · {row.storage_mode}"
                for row in state.attachment_rows[:20]
            ) or "无"
            self._summary_label.setText(
                f"attachment_registry：{state.attachment_registry_path}\n"
                f"attachment_registry_warning：{state.attachment_registry_warning or '无'}\n"
                f"fulltext_registry：{state.fulltext_registry_path}\n"
                f"missing_fulltext_report：{state.missing_fulltext_report_path}\n"
                f"missing_fulltext_report_status：{state.missing_fulltext_report_status}\n"
                f"attachment_validation：{state.attachment_validation_status} · {state.attachment_validation_message}\n"
                f"附件数量：{state.attachment_count}\n"
                f"Full-text 记录：{state.fulltext_record_count}\n"
                f"PDF 附件：{state.pdf_attachment_count}\n"
                f"link / copy / ignore / missing：{state.link_attachment_count} / {state.copy_attachment_count} / {state.ignore_attachment_count} / {state.missing_attachment_count}\n"
                f"broken path：{state.broken_path_count}\n"
                f"缺失 full-text：{state.missing_fulltext_count}\n"
                f"文件状态：\n" + attachment_rows
            )

else:

    class AttachmentPage:  # type: ignore[no-redef]
        pass
