from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.services.literature_import_service import ImportResult, LiteratureImportService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class ImportDiagnosticsCard:
    key: str
    label: str
    value: int


@dataclass(frozen=True)
class ImportDiagnosticsWarningRow:
    key: str
    label: str
    count: int
    message: str


@dataclass(frozen=True)
class ImportDiagnosticsVisualSummary:
    diagnostics_path: str
    warnings_csv_path: str
    missing_diagnostics: bool
    total_warning_count: int
    summary_cards: tuple[ImportDiagnosticsCard, ...]
    warning_rows: tuple[ImportDiagnosticsWarningRow, ...]
    failed_record_examples: tuple[str, ...]
    warning_examples: tuple[str, ...]


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
    diagnostics_cards: tuple[ImportDiagnosticsCard, ...] = ()
    warning_table: tuple[ImportDiagnosticsWarningRow, ...] = ()
    missing_diagnostics: bool = False
    total_warning_count: int = 0
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
    visual_summary = import_diagnostics_visual_summary(diagnostics_path, warnings_path=warnings_path)
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
        diagnostics_cards=visual_summary.summary_cards,
        warning_table=visual_summary.warning_rows,
        missing_diagnostics=visual_summary.missing_diagnostics,
        total_warning_count=visual_summary.total_warning_count,
        warning_list=visual_summary.warning_examples,
        failed_records_preview=visual_summary.failed_record_examples,
        diagnostics_export_path=diagnostics_path,
        warnings_export_path=visual_summary.warnings_csv_path,
        recent_import_batches=tuple(recent_import_batches or ()),
    )


def import_diagnostics_visual_summary(diagnostics_path: str, *, warnings_path: str = "") -> ImportDiagnosticsVisualSummary:
    diagnostics = _load_diagnostics_summary(diagnostics_path)
    missing_diagnostics = bool(diagnostics_path and diagnostics.get("warning") == "diagnostics_file_missing")
    normalized_path = str(Path(diagnostics_path).expanduser()) if diagnostics_path else ""
    warnings_csv_path = warnings_path or _infer_warnings_csv_path(normalized_path)
    cards = tuple(
        ImportDiagnosticsCard(key=key, label=label, value=_int_value(diagnostics.get(key, 0)))
        for key, label in _DIAGNOSTICS_CARD_FIELDS
    )
    warning_rows = _diagnostics_warning_rows(diagnostics)
    failed_examples = _string_tuple(diagnostics.get("failed_record_examples", ()), limit=5)
    warning_examples = _string_tuple(diagnostics.get("parse_warning_examples", ()), limit=10)
    total_warning_count = _int_value(diagnostics.get("warning_count", 0))
    if total_warning_count == 0:
        total_warning_count = sum(row.count for row in warning_rows)
    return ImportDiagnosticsVisualSummary(
        diagnostics_path=normalized_path,
        warnings_csv_path=warnings_csv_path,
        missing_diagnostics=missing_diagnostics,
        total_warning_count=total_warning_count,
        summary_cards=cards,
        warning_rows=warning_rows,
        failed_record_examples=failed_examples,
        warning_examples=warning_examples,
    )


def _load_diagnostics_summary(diagnostics_path: str) -> dict[str, object]:
    if not diagnostics_path:
        return {key: [] if key.endswith("examples") else 0 for key in _DIAGNOSTICS_SUMMARY_KEYS}
    path = Path(diagnostics_path).expanduser()
    if not path.exists():
        payload: dict[str, object] = {key: [] if key.endswith("examples") else 0 for key in _DIAGNOSTICS_SUMMARY_KEYS}
        payload.update({"warning": "diagnostics_file_missing", "path": str(path)})
        return payload
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {key: payload.get(key, [] if key.endswith("examples") else 0) for key in _DIAGNOSTICS_SUMMARY_KEYS}


_DIAGNOSTICS_SUMMARY_KEYS = (
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

_DIAGNOSTICS_CARD_FIELDS = (
    ("missing_title_count", "Missing title"),
    ("missing_author_count", "Missing author"),
    ("missing_year_count", "Missing year"),
    ("missing_doi_count", "Missing DOI"),
    ("missing_pmid_count", "Missing PMID"),
    ("empty_abstract_count", "Empty abstract"),
    ("invalid_doi_count", "Invalid DOI"),
    ("invalid_year_count", "Invalid year"),
)

_WARNING_MESSAGES = {
    "missing_title_count": "Records without a title need review before screening.",
    "missing_author_count": "Author metadata is missing for some records.",
    "missing_year_count": "Publication year is missing for some records.",
    "missing_doi_count": "DOI is missing; import continues but matching may be weaker.",
    "missing_pmid_count": "PMID is missing; import continues but PubMed matching may be weaker.",
    "empty_abstract_count": "Abstract text is empty for some records.",
    "invalid_doi_count": "Some DOI values could not be normalized.",
    "invalid_year_count": "Some year values could not be parsed.",
    "duplicate_identifier_count": "Repeated DOI/PMID identifiers were detected in the import batch.",
    "failed_record_count": "Some records failed parsing or validation.",
}


def _diagnostics_warning_rows(diagnostics: dict[str, object]) -> tuple[ImportDiagnosticsWarningRow, ...]:
    rows: list[ImportDiagnosticsWarningRow] = []
    for key, label in (*_DIAGNOSTICS_CARD_FIELDS, ("duplicate_identifier_count", "Duplicate identifier"), ("failed_record_count", "Failed record")):
        count = _int_value(diagnostics.get(key, 0))
        if count <= 0:
            continue
        rows.append(
            ImportDiagnosticsWarningRow(
                key=key,
                label=label,
                count=count,
                message=_WARNING_MESSAGES.get(key, "Import diagnostics warning needs review."),
            )
        )
    return tuple(rows)


def _infer_warnings_csv_path(diagnostics_path: str) -> str:
    if not diagnostics_path:
        return ""
    if diagnostics_path.endswith("_import_diagnostics.json"):
        return diagnostics_path.replace("_import_diagnostics.json", "_import_warnings.csv")
    return str(Path(diagnostics_path).with_name("import_warnings.csv"))


def _int_value(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _string_tuple(value: object, *, limit: int) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(str(item) for item in value[:limit])


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
                cards = "\n".join(f"- {card.label}: {card.value}" for card in self._state.diagnostics_cards) or "无"
                warning_rows = (
                    "\n".join(f"- {row.label}: {row.count} ({row.message})" for row in self._state.warning_table) or "无"
                )
                warnings = "\n".join(f"- {item}" for item in self._state.warning_list) or "无"
                failed = "\n".join(f"- {item}" for item in self._state.failed_records_preview) or "无"
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"格式：{result.source_type.upper()}\n"
                    f"总记录：{result.total_records}\n"
                    f"成功导入：{result.imported_records}\n"
                    f"warning_count：{self._state.total_warning_count or diagnostics.get('warning_count', result.details.get('warning_count', 0))}\n"
                    f"failed_record_count：{diagnostics.get('failed_record_count', 0)}\n"
                    f"Diagnostics summary cards：\n{cards}\n"
                    f"Warning table：\n{warning_rows}\n"
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
