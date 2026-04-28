from __future__ import annotations

from dataclasses import dataclass

from app.meta_analysis.services.analysis_service import AnalysisPreflightResult, AnalysisPreflightService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class AnalysisPageState:
    title: str
    description: str
    status_label: str
    last_result: AnalysisPreflightResult | None = None


def initial_analysis_state() -> AnalysisPageState:
    feature = get_feature("meta-analysis")
    return AnalysisPageState(
        title="Analysis / Meta 统计分析预检",
        description="读取 Extraction 输出并检查是否具备最小统计运行条件。本阶段不执行合并效应量、森林图或敏感性分析。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class AnalysisPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: AnalysisPreflightService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or AnalysisPreflightService()
            self._state = initial_analysis_state()

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
            self._path_input.setPlaceholderText("选择或粘贴 Extraction 输出 JSON 文件路径")
            choose_button = QPushButton("选择 Extraction 输出")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("运行 Analysis 预检")
            run_button.clicked.connect(self._run_preflight)
            root.addWidget(run_button)

            self._status_label = QLabel("分析状态：等待 Extraction 输出")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("Analysis 预检摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：Reporting")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择 Extraction 输出", "", "Extraction output (*.json)")
            if path:
                self._path_input.setText(path)

        def _run_preflight(self) -> None:
            result = self._service.run_preflight(project_id=self._project_id, extraction_pool_path=self._path_input.text())
            if result.success:
                self._status_label.setText("分析状态：预检完成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"提取记录：{result.extraction_records}\n"
                    f"Outcome 记录：{result.outcome_records}\n"
                    f"有效 Outcome：{result.valid_outcome_records}\n"
                    f"可运行统计：{'是' if result.runnable else '否'}\n"
                    f"阻断项：{', '.join(result.blocking_errors) or '无'}\n"
                    f"建议：{result.recommended_action}\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("分析状态：预检失败")
                self._summary_label.setText("没有生成 Analysis 预检结果。")
                self._error_label.setText(result.message)

else:

    class AnalysisPage:  # type: ignore[no-redef]
        pass
