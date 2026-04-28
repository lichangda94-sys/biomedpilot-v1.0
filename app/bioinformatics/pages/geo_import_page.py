from __future__ import annotations

from dataclasses import dataclass

from app.bioinformatics.services.geo_import_service import GeoImportPlanResult, GeoImportService
from app.shared.feature_availability import get_feature


@dataclass(frozen=True)
class GeoImportPageState:
    title: str
    description: str
    status_label: str
    last_result: GeoImportPlanResult | None = None


def initial_geo_import_state() -> GeoImportPageState:
    feature = get_feature("bio-data-import")
    return GeoImportPageState(
        title="数据检索 / 导入",
        description="生成 GEO 查询计划和 GSE accession 导入记录。本阶段不自动下载 NCBI 数据。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFrame = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class GeoImportPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: GeoImportService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or GeoImportService()
            self._state = initial_geo_import_state()

            root = QVBoxLayout(self)
            title = QLabel(self._state.title)
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label}"))

            self._query_input = QLineEdit()
            self._query_input.setPlaceholderText("GEO 检索词，例如 papillary thyroid carcinoma RNA-seq")
            self._accession_input = QLineEdit()
            self._accession_input.setPlaceholderText("可选 GSE accession，例如 GSE33630, GSE27155")
            self._max_results_input = QLineEdit()
            self._max_results_input.setPlaceholderText("max_results，默认 20")
            root.addWidget(self._query_input)
            root.addWidget(self._accession_input)
            root.addWidget(self._max_results_input)

            run_button = QPushButton("生成 GEO 查询计划")
            run_button.clicked.connect(self._create_plan)
            root.addWidget(run_button)

            self._status_label = QLabel("导入状态：等待检索词或 accession")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("GEO 查询计划摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：数据下载")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _create_plan(self) -> None:
            try:
                max_results = int(self._max_results_input.text() or "20")
            except ValueError:
                max_results = 20
            result = self._service.create_geo_import_plan(
                project_id=self._project_id,
                query_text=self._query_input.text(),
                accession_text=self._accession_input.text(),
                max_results=max_results,
            )
            if result.success:
                self._status_label.setText("导入状态：GEO 查询计划已生成")
                self._summary_label.setText(
                    f"检索词：{result.query_text or '仅 accession 导入'}\n"
                    f"完整 GEO query：{result.full_geo_query}\n"
                    f"Accessions：{', '.join(result.accessions) or '无'}\n"
                    f"max_results：{result.max_results}\n"
                    f"输出：{result.output_path}\n"
                    f"在线检索：未执行"
                )
                self._error_label.setText("")
            else:
                self._status_label.setText("导入状态：失败")
                self._summary_label.setText("没有生成 GEO 查询计划。")
                self._error_label.setText(result.message)

else:

    class GeoImportPage:  # type: ignore[no-redef]
        pass
