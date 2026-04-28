from __future__ import annotations

from dataclasses import dataclass

from app.bioinformatics.services.enrichment_service import EnrichmentPreflightResult, EnrichmentService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class EnrichmentPageState:
    title: str
    description: str
    status_label: str
    last_result: EnrichmentPreflightResult | None = None


def initial_enrichment_state() -> EnrichmentPageState:
    feature = get_feature("bio-enrichment")
    return EnrichmentPageState(
        title="富集分析",
        description="读取差异表达分析预检并检查富集分析前置条件。本阶段不下载数据库、不运行 GO / KEGG / GSEA。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class EnrichmentPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: EnrichmentService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or EnrichmentService()
            self._state = initial_enrichment_state()

            root = QVBoxLayout(self)
            title = QLabel(self._state.title)
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label}"))

            row = QHBoxLayout()
            self._path_input = QLineEdit()
            self._path_input.setPlaceholderText("选择或粘贴差异表达分析预检 JSON 文件路径")
            choose_button = QPushButton("选择差异分析预检")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("运行富集分析预检")
            run_button.clicked.connect(self._create_preflight)
            root.addWidget(run_button)

            self._status_label = QLabel("富集状态：等待差异表达分析预检")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("富集分析预检摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：相关性分析")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择差异表达分析预检", "", "Differential expression preflight (*.json)")
            if path:
                self._path_input.setText(path)

        def _create_preflight(self) -> None:
            result = self._service.create_preflight(project_id=self._project_id, differential_expression_path=self._path_input.text())
            if result.success:
                self._status_label.setText("富集状态：预检已生成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"数据集：{result.dataset_count}\n"
                    f"具备前置条件：{result.ready_for_enrichment_count}\n"
                    f"富集分析：未执行\n"
                    f"数据库下载：未执行\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("富集状态：失败")
                self._summary_label.setText("没有生成富集分析预检。")
                self._error_label.setText(result.message)

else:

    class EnrichmentPage:  # type: ignore[no-redef]
        pass
