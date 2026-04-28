from __future__ import annotations

from dataclasses import dataclass

from app.bioinformatics.services.geo_asset_detection_service import GeoAssetDetectionResult, GeoAssetDetectionService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class GeoAssetDetectionPageState:
    title: str
    description: str
    status_label: str
    last_result: GeoAssetDetectionResult | None = None


def initial_geo_asset_detection_state() -> GeoAssetDetectionPageState:
    feature = get_feature("bio-asset-detection")
    return GeoAssetDetectionPageState(
        title="数据资产识别",
        description="读取 GEO 下载计划并扫描本地目标目录。本阶段不联网、不下载。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class GeoAssetDetectionPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: GeoAssetDetectionService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or GeoAssetDetectionService()
            self._state = initial_geo_asset_detection_state()

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
            self._path_input.setPlaceholderText("选择或粘贴 GEO 下载计划 JSON 文件路径")
            choose_button = QPushButton("选择 GEO 下载计划")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("识别本地数据资产")
            run_button.clicked.connect(self._detect_assets)
            root.addWidget(run_button)

            self._status_label = QLabel("识别状态：等待 GEO 下载计划")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("资产识别摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：数据清洗")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择 GEO 下载计划", "", "GEO download plan (*.json)")
            if path:
                self._path_input.setText(path)

        def _detect_assets(self) -> None:
            result = self._service.detect_assets(project_id=self._project_id, geo_download_plan_path=self._path_input.text())
            if result.success:
                self._status_label.setText("识别状态：完成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"扫描 accession：{result.dataset_count}\n"
                    f"表达矩阵候选：{result.ready_dataset_count}\n"
                    f"联网：未使用\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("识别状态：失败")
                self._summary_label.setText("没有生成资产识别结果。")
                self._error_label.setText(result.message)

else:

    class GeoAssetDetectionPage:  # type: ignore[no-redef]
        pass
