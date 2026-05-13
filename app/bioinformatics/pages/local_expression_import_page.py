from __future__ import annotations

from dataclasses import dataclass

from app.bioinformatics.models.expression_import import ExpressionImportResult
from app.bioinformatics.services.local_expression_import_service import LocalExpressionImportService
from app.shared.feature_availability import get_feature
from app.shared.ui import (
    error_text_qss,
    navigation_button_qss,
    page_title_qss,
    primary_button_qss,
    status_badge_qss,
    surface_card_qss,
    warning_text_qss,
)


@dataclass(frozen=True)
class LocalExpressionImportPageState:
    title: str
    description: str
    status_label: str
    file_path_placeholder: str
    import_button_label: str
    next_step: str
    summary_fields: tuple[str, ...] = (
        "row_count",
        "column_count",
        "gene_id_column_candidates",
        "sample_expression_column_candidates",
        "numeric_column_ratio",
        "missing_value_summary",
        "duplicate_gene_id_count",
        "is_expression_matrix_suitable",
    )
    last_result: ExpressionImportResult | None = None


def initial_local_expression_import_state() -> LocalExpressionImportPageState:
    feature = get_feature("bio-local-expression-import")
    return LocalExpressionImportPageState(
        title="本地表达矩阵导入",
        description="支持 CSV / TSV / TXT / XLSX 表达矩阵导入，用于后续数据清洗、分组和差异分析。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        file_path_placeholder="输入本地表达矩阵文件路径，例如 /path/to/expression_matrix.csv",
        import_button_label="导入表达矩阵",
        next_step="下一步：数据资产确认 / 样本注释导入",
    )


try:
    from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFrame = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class LocalExpressionImportPage(QWidget):
        def __init__(
            self,
            *,
            project_id: str = "manual-testing-project",
            service: LocalExpressionImportService | None = None,
        ) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or LocalExpressionImportService()
            self._state = initial_local_expression_import_state()

            root = QVBoxLayout(self)
            title = QLabel(self._state.title)
            title.setStyleSheet(page_title_qss())
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            feature_status = QLabel(f"功能状态：{self._state.status_label}")
            feature_status.setStyleSheet(status_badge_qss("testing"))
            root.addWidget(feature_status)

            self._path_input = QLineEdit()
            self._path_input.setPlaceholderText(self._state.file_path_placeholder)
            root.addWidget(self._path_input)

            import_button = QPushButton(self._state.import_button_label)
            import_button.setStyleSheet(primary_button_qss())
            import_button.clicked.connect(self._import_matrix)
            root.addWidget(import_button)

            self._status_label = QLabel("导入状态：等待本地表达矩阵文件")
            self._status_label.setWordWrap(True)
            self._status_label.setStyleSheet(status_badge_qss("pending"))
            root.addWidget(self._status_label)

            summary_card = QFrame()
            summary_card.setStyleSheet(surface_card_qss())
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("表达矩阵导入摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)

            self._warnings_label = QLabel("")
            self._warnings_label.setWordWrap(True)
            self._warnings_label.setStyleSheet(warning_text_qss())
            root.addWidget(self._warnings_label)

            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet(error_text_qss())
            root.addWidget(self._error_label)

            next_button = QPushButton(self._state.next_step)
            next_button.setEnabled(False)
            next_button.setStyleSheet(navigation_button_qss())
            root.addWidget(next_button)
            root.addStretch(1)

        def _import_matrix(self) -> None:
            result = self._service.import_expression_matrix(
                project_id=self._project_id,
                source_path=self._path_input.text(),
            )
            if result.success:
                self._status_label.setText("导入状态：表达矩阵导入预检已完成")
                self._status_label.setStyleSheet(status_badge_qss("warning" if result.warnings else "completed"))
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"格式：{result.source_type.upper()}\n"
                    f"行数：{result.row_count}\n"
                    f"列数：{result.column_count}\n"
                    f"候选 gene/probe 列：{', '.join(result.candidate_gene_columns) or '未识别'}\n"
                    f"候选表达样本列：{', '.join(result.sample_expression_column_candidates) or '未识别'}\n"
                    f"数值样本列数量：{result.numeric_column_count}\n"
                    f"数值列比例：{result.numeric_column_ratio:.2%}\n"
                    f"缺失比例：{result.missing_value_rate:.2%}\n"
                    f"重复 gene/probe/id 数：{result.duplicate_gene_id_count}\n"
                    f"适合作为表达矩阵：{'是' if result.is_expression_matrix_suitable else '需人工确认'}\n"
                    f"Manifest：{result.manifest_path or result.output_path}\n"
                    f"Summary：{result.summary_path or '未生成'}"
                )
                self._warnings_label.setText("\n".join(result.warnings))
                self._error_label.setText("")
            else:
                self._status_label.setText("导入状态：失败")
                self._status_label.setStyleSheet(status_badge_qss("error"))
                self._summary_label.setText("没有生成表达矩阵数据资产。")
                self._warnings_label.setText("")
                self._error_label.setText(result.message)

else:

    class LocalExpressionImportPage:  # type: ignore[no-redef]
        pass
