from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.services.literature_import_service import ImportResult, LiteratureImportService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class LiteratureImportPageState:
    title: str
    description: str
    supported_formats: tuple[str, ...]
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    warning_summary: str
    last_result: ImportResult | None = None
    diagnostics_summary: dict[str, object] | None = None
    warning_list: tuple[str, ...] = ()
    failed_records_preview: tuple[str, ...] = ()
    diagnostics_export_path: str = ""
    warnings_export_path: str = ""
    recent_import_batches: tuple[dict[str, object], ...] = ()


def initial_literature_import_state() -> LiteratureImportPageState:
    feature = get_feature("meta-literature-import")
    return LiteratureImportPageState(
        title="文献导入",
        description="支持 NBIB / RIS / CSV 文件导入，用于后续去重和筛选。",
        supported_formats=("NBIB", "RIS", "CSV"),
        status_label=feature.status.display_label() if feature is not None else "测试中",
        input_summary="输入：本地 NBIB / RIS / CSV 文献文件路径。",
        output_summary="输出：literature_records 数据资产和 literature_import task。",
        next_step="下一步：Prepare Screening / 去重准备。",
        empty_state="未选择文件时不会运行导入，请先选择本地文献文件。",
        warning_summary="错误会显示为用户可读 message；详细解析错误保留在 details。",
    )


def literature_import_state_from_result(
    result: ImportResult,
    *,
    recent_import_batches: list[dict[str, object]] | None = None,
) -> LiteratureImportPageState:
    base = initial_literature_import_state()
    diagnostics_path = str(result.details.get("diagnostics_path", "")) if result.details else ""
    warnings_path = str(result.details.get("warnings_path", "")) if result.details else ""
    diagnostics = _load_diagnostics_summary(diagnostics_path)
    warnings = tuple(diagnostics.get("parse_warning_examples", [])[:10]) if diagnostics else ()
    failed_preview = tuple(diagnostics.get("failed_record_examples", [])[:5]) if diagnostics else ()
    return LiteratureImportPageState(
        title=base.title,
        description=base.description,
        supported_formats=base.supported_formats,
        status_label=base.status_label,
        input_summary=base.input_summary,
        output_summary="输出：literature_records、import diagnostics、warnings CSV、Data Center asset 和 literature_import task。",
        next_step=base.next_step,
        empty_state=base.empty_state,
        warning_summary="显示 diagnostics summary、warning list、failed records preview；详细解析错误保留在 details。",
        last_result=result,
        diagnostics_summary=diagnostics,
        warning_list=warnings,
        failed_records_preview=failed_preview,
        diagnostics_export_path=diagnostics_path,
        warnings_export_path=warnings_path,
        recent_import_batches=tuple(recent_import_batches or ()),
    )


def _load_diagnostics_summary(diagnostics_path: str) -> dict[str, object]:
    if not diagnostics_path:
        return {}
    path = Path(diagnostics_path).expanduser()
    if not path.exists():
        return {"warning": "diagnostics_file_missing", "path": str(path)}
    payload = json.loads(path.read_text(encoding="utf-8"))
    keys = (
        "raw_record_count",
        "parsed_record_count",
        "normalized_record_count",
        "failed_record_count",
        "warning_count",
        "missing_title_count",
        "missing_author_count",
        "missing_year_count",
        "missing_doi_count",
        "missing_pmid_count",
        "empty_abstract_count",
        "invalid_year_count",
        "invalid_doi_count",
        "duplicate_identifier_count",
        "parse_warning_examples",
        "failed_record_examples",
    )
    return {key: payload.get(key, [] if key.endswith("examples") else 0) for key in keys}


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class LiteratureImportPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: LiteratureImportService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or LiteratureImportService()
            self._state = initial_literature_import_state()

            root = QVBoxLayout(self)
            title = QLabel(self._state.title)
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            status = QLabel(f"功能状态：{self._state.status_label}")
            status.setStyleSheet("font-weight: 700;")
            root.addWidget(status)

            row = QHBoxLayout()
            self._path_input = QLineEdit()
            self._path_input.setPlaceholderText("选择或粘贴 .nbib / .ris / .csv 文件路径")
            choose_button = QPushButton("选择文件")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            import_button = QPushButton("导入")
            import_button.clicked.connect(self._run_import)
            root.addWidget(import_button)

            self._status_label = QLabel("导入状态：等待文件")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            self._summary_card = QFrame()
            self._summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(self._summary_card)
            self._summary_label = QLabel("导入结果摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(self._summary_card)

            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：进入文献去重")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择文献文件", "", "Literature files (*.nbib *.ris *.csv)")
            if path:
                self._path_input.setText(path)

        def _run_import(self) -> None:
            result = self._service.import_file(project_id=self._project_id, source_path=self._path_input.text())
            if result.success:
                self._state = literature_import_state_from_result(result)
                self._status_label.setText("导入状态：完成")
                diagnostics = self._state.diagnostics_summary or {}
                warnings = "\n".join(f"- {item}" for item in self._state.warning_list) or "无"
                failed = "\n".join(f"- {item}" for item in self._state.failed_records_preview) or "无"
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"格式：{result.source_type.upper()}\n"
                    f"总记录：{result.total_records}\n"
                    f"成功导入：{result.imported_records}\n"
                    f"warning_count：{diagnostics.get('warning_count', result.details.get('warning_count', 0))}\n"
                    f"failed_record_count：{diagnostics.get('failed_record_count', 0)}\n"
                    f"diagnostics：{self._state.diagnostics_export_path}\n"
                    f"warnings CSV：{self._state.warnings_export_path}\n"
                    f"warning list：\n{warnings}\n"
                    f"failed records preview：\n{failed}\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("导入状态：失败")
                self._summary_label.setText("没有生成导入结果。")
                self._error_label.setText(result.message)

else:

    class LiteratureImportPage:  # type: ignore[no-redef]
        pass
