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
        description="检索范围：GEO/GSE、TCGA/GDC、GTEx、本地数据。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
    )


try:
    from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFrame = QLabel = QLineEdit = QPushButton = QTableWidget = QTableWidgetItem = QVBoxLayout = QWidget = None


if QWidget is not None:

    class GeoImportPage(QWidget):
        def __init__(self, *, project_id: str = "manual-testing-project", service: GeoImportService | None = None) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or GeoImportService()
            self._state = initial_geo_import_state()
            self._last_result: GeoImportPlanResult | None = None

            root = QVBoxLayout(self)
            title = QLabel(self._state.title)
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label}"))

            self._query_input = QLineEdit()
            self._query_input.setPlaceholderText("输入疾病或主题，例如 脑胶质瘤、肺腺癌、糖尿病相关转录组")
            self._accession_input = QLineEdit()
            self._accession_input.setPlaceholderText("可选 GSE accession，例如 GSE33630, GSE27155")
            self._max_results_input = QLineEdit()
            self._max_results_input.setPlaceholderText("max_results，默认 20")
            root.addWidget(self._query_input)
            root.addWidget(self._accession_input)
            root.addWidget(self._max_results_input)

            draft_button = QPushButton("生成检索草稿")
            draft_button.clicked.connect(self._create_plan)
            root.addWidget(draft_button)
            search_button = QPushButton("检索 GEO/GSE")
            search_button.clicked.connect(self._search_geo)
            root.addWidget(search_button)

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
            self._geo_query_table = QTableWidget(0, 2)
            self._geo_query_table.setHorizontalHeaderLabels(["GEO query 草稿", "类型"])
            root.addWidget(self._geo_query_table)
            self._tcga_table = QTableWidget(0, 5)
            self._tcga_table.setHorizontalHeaderLabels(["project_id", "project_name", "primary_site", "disease_type", "mapping_status"])
            root.addWidget(self._tcga_table)
            self._gtex_table = QTableWidget(0, 3)
            self._gtex_table.setHorizontalHeaderLabels(["tissue", "role", "mapping_status"])
            root.addWidget(self._gtex_table)
            self._geo_result_table = QTableWidget(0, 6)
            self._geo_result_table.setHorizontalHeaderLabels(["GSE", "标题", "query_used", "相关性", "原因", "操作"])
            root.addWidget(self._geo_result_table)
            self._source_candidate_table = QTableWidget(0, 7)
            self._source_candidate_table.setHorizontalHeaderLabels(["来源", "ID", "标题", "数据类型", "样本数", "可登记/下载", "提示"])
            root.addWidget(self._source_candidate_table)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            self._register_first_button = QPushButton("登记首条结果为数据来源")
            self._register_first_button.setEnabled(False)
            self._register_first_button.clicked.connect(self._register_first_result)
            root.addWidget(self._register_first_button)
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
            self._last_result = result
            self._render_result(result)

        def _search_geo(self) -> None:
            try:
                max_results = int(self._max_results_input.text() or "20")
            except ValueError:
                max_results = 20
            result = self._service.create_geo_import_plan(
                project_id=self._project_id,
                query_text=self._query_input.text(),
                accession_text=self._accession_input.text(),
                max_results=max_results,
                execute_online=True,
            )
            self._last_result = result
            self._render_result(result)

        def _render_result(self, result: GeoImportPlanResult) -> None:
            if result.success:
                self._status_label.setText("检索状态：" + ("GEO/GSE 检索完成" if result.search_status == "completed" else "检索草稿已生成"))
                self._summary_label.setText(
                    f"识别疾病：{', '.join(result.recognized_diseases_zh) or '未识别到明确疾病'}\n"
                    f"英文疾病词：{', '.join(result.disease_terms_en[:6]) or '无'}\n"
                    f"结果数量：{len(result.geo_results)}\n"
                    f"宽泛检索保护：{'已触发' if result.broad_query_guard_triggered else '未触发'}\n"
                    f"max_results：{result.max_results}\n"
                    f"输出：{result.output_path}"
                )
                self._fill_query_table(result)
                self._fill_tcga_table(result)
                self._fill_gtex_table(result)
                self._fill_geo_result_table(result)
                self._fill_source_candidate_table(result)
                self._register_first_button.setEnabled(bool(result.geo_results))
                self._error_label.setText("")
            else:
                self._status_label.setText("导入状态：失败")
                self._summary_label.setText("没有生成 GEO 查询计划。")
                self._clear_tables()
                self._register_first_button.setEnabled(False)
                self._error_label.setText(result.message)

        def _fill_query_table(self, result: GeoImportPlanResult) -> None:
            rows = [(query, "首选疾病 query") for query in result.confirmed_geo_queries]
            rows.extend((query, "补充 query，需确认") for query in result.supplemental_geo_queries[:8])
            self._geo_query_table.setRowCount(len(rows))
            for row, (query, kind) in enumerate(rows):
                self._geo_query_table.setItem(row, 0, QTableWidgetItem(query))
                self._geo_query_table.setItem(row, 1, QTableWidgetItem(kind))

        def _fill_tcga_table(self, result: GeoImportPlanResult) -> None:
            self._tcga_table.setRowCount(len(result.tcga_project_candidates))
            for row, item in enumerate(result.tcga_project_candidates):
                for col, key in enumerate(("project_id", "project_name", "primary_site", "disease_type", "mapping_status")):
                    self._tcga_table.setItem(row, col, QTableWidgetItem(str(item.get(key, ""))))

        def _fill_gtex_table(self, result: GeoImportPlanResult) -> None:
            self._gtex_table.setRowCount(len(result.gtex_tissue_candidates))
            for row, item in enumerate(result.gtex_tissue_candidates):
                for col, key in enumerate(("tissue", "role", "mapping_status")):
                    self._gtex_table.setItem(row, col, QTableWidgetItem(str(item.get(key, ""))))

        def _fill_geo_result_table(self, result: GeoImportPlanResult) -> None:
            self._geo_result_table.setRowCount(len(result.geo_results))
            for row, item in enumerate(result.geo_results):
                self._geo_result_table.setItem(row, 0, QTableWidgetItem(str(item.get("accession", ""))))
                self._geo_result_table.setItem(row, 1, QTableWidgetItem(str(item.get("title", ""))))
                self._geo_result_table.setItem(row, 2, QTableWidgetItem(str(item.get("query_used", ""))))
                self._geo_result_table.setItem(row, 3, QTableWidgetItem(str(item.get("rank_score", ""))))
                self._geo_result_table.setItem(row, 4, QTableWidgetItem(str(item.get("disease_relevance_reason", ""))))
                self._geo_result_table.setItem(row, 5, QTableWidgetItem("可登记"))

        def _fill_source_candidate_table(self, result: GeoImportPlanResult) -> None:
            self._source_candidate_table.setRowCount(len(result.unified_dataset_candidates))
            for row, item in enumerate(result.unified_dataset_candidates):
                warnings = item.get("warnings", ())
                if isinstance(warnings, (list, tuple)):
                    warning_text = "；".join(str(value) for value in warnings[:2])
                else:
                    warning_text = str(warnings)
                available = "可下载" if item.get("download_plan_available") else "候选"
                if item.get("source") == "geo":
                    available = "可登记" if item.get("accession_or_project") else "候选"
                values = [
                    item.get("source", ""),
                    item.get("accession_or_project", ""),
                    item.get("display_title", ""),
                    item.get("data_modality", ""),
                    item.get("sample_count", ""),
                    available,
                    warning_text,
                ]
                for col, value in enumerate(values):
                    self._source_candidate_table.setItem(row, col, QTableWidgetItem(str(value)))

        def _clear_tables(self) -> None:
            for table in (self._geo_query_table, self._tcga_table, self._gtex_table, self._geo_result_table, self._source_candidate_table):
                table.setRowCount(0)

        def _register_first_result(self) -> None:
            if not self._last_result or not self._last_result.geo_results:
                return
            output_path = self._service.register_geo_result_as_source(
                project_id=self._project_id,
                result=self._last_result.geo_results[0],
            )
            self._status_label.setText(f"登记状态：已登记为数据来源 {output_path}")

else:

    class GeoImportPage:  # type: ignore[no-redef]
        pass
