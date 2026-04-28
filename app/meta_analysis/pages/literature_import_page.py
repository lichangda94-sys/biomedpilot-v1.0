from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.services.literature_import_service import ImportResult, LiteratureImportService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class LiteratureImportPageState:
    title: str
    description: str
    supported_formats: tuple[str, ...]
    status_label: str
    last_result: ImportResult | None = None


def initial_literature_import_state() -> LiteratureImportPageState:
    feature = get_feature("meta-literature-import")
    return LiteratureImportPageState(
        title="文献导入",
        description="支持 NBIB / RIS / CSV 文件导入，用于后续去重和筛选。",
        supported_formats=("NBIB", "RIS", "CSV"),
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


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
                self._status_label.setText("导入状态：完成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"格式：{result.source_type.upper()}\n"
                    f"总记录：{result.total_records}\n"
                    f"成功导入：{result.imported_records}\n"
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

