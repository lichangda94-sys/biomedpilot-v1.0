from __future__ import annotations

from dataclasses import dataclass

from app.bioinformatics.services.geo_cleaning_service import GeoCleaningPlanResult, GeoCleaningService
from app.shared.feature_availability import get_feature
from app.shared.ui import (
    error_text_qss,
    navigation_button_qss,
    page_title_qss,
    primary_button_qss,
    secondary_button_qss,
    status_badge_qss,
    surface_card_qss,
)


@dataclass(frozen=True)
class GeoCleaningPageState:
    title: str
    description: str
    status_label: str
    last_result: GeoCleaningPlanResult | None = None


def initial_geo_cleaning_state() -> GeoCleaningPageState:
    feature = get_feature("bio-cleaning")
    return GeoCleaningPageState(
        title="数据清洗",
        description="读取资产识别结果并生成清洗预检计划。本阶段不执行矩阵标准化。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class GeoCleaningPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: GeoCleaningService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or GeoCleaningService()
            self._state = initial_geo_cleaning_state()

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

            row = QHBoxLayout()
            self._path_input = QLineEdit()
            self._path_input.setPlaceholderText("选择或粘贴数据资产识别 JSON 文件路径")
            choose_button = QPushButton("选择资产识别结果")
            choose_button.setStyleSheet(secondary_button_qss())
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("生成清洗计划")
            run_button.setStyleSheet(primary_button_qss())
            run_button.clicked.connect(self._create_plan)
            root.addWidget(run_button)

            self._status_label = QLabel("清洗状态：等待资产识别结果")
            self._status_label.setWordWrap(True)
            self._status_label.setStyleSheet(status_badge_qss("pending"))
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet(surface_card_qss())
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("清洗计划摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet(error_text_qss())
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：样本分组")
            next_button.setEnabled(False)
            next_button.setStyleSheet(navigation_button_qss())
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择资产识别结果", "", "Asset detection (*.json)")
            if path:
                self._path_input.setText(path)

        def _create_plan(self) -> None:
            result = self._service.create_cleaning_plan(project_id=self._project_id, asset_detection_path=self._path_input.text())
            if result.success:
                self._status_label.setText("清洗状态：清洗计划已生成")
                self._status_label.setStyleSheet(status_badge_qss("completed"))
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"数据集：{result.dataset_count}\n"
                    f"可清洗：{result.ready_for_cleaning_count}\n"
                    f"实际标准化：未执行\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("清洗状态：失败")
                self._status_label.setStyleSheet(status_badge_qss("error"))
                self._summary_label.setText("没有生成清洗计划。")
                self._error_label.setText(result.message)

else:

    class GeoCleaningPage:  # type: ignore[no-redef]
        pass
