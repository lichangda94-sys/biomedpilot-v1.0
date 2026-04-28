from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.extraction.schema_registry import list_extraction_schema_profiles
from app.meta_analysis.models.analysis_dataset import AnalysisReadyDataset
from app.meta_analysis.models.analysis_result import AnalysisResult
from app.meta_analysis.models.extraction import OutcomeDataType
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.services.analysis_service import AnalysisPreflightResult, AnalysisPreflightService
from app.shared.feature_availability import get_feature
from app.shared.storage import default_storage_root


@dataclass(frozen=True)
class AnalysisPageState:
    title: str
    description: str
    status_label: str
    last_result: AnalysisPreflightResult | None = None
    last_dataset: AnalysisReadyDataset | None = None
    last_analysis_result: AnalysisResult | None = None
    project_dir_placeholder: str = "选择或粘贴项目目录路径"
    profile_options: tuple[str, ...] = ()
    outcome_type_options: tuple[str, ...] = ()
    model_options: tuple[str, ...] = ("fixed", "random")
    available_outcome_columns: tuple[str, ...] = (
        "profile_type",
        "outcome_name",
        "effect_measure",
        "outcome_data_type",
        "record_count",
    )
    dataset_summary_fields: tuple[str, ...] = (
        "dataset_id",
        "profile_type",
        "outcome_name",
        "effect_measure",
        "included_study_count",
        "excluded_study_count",
        "validation_errors",
        "validation_warnings",
    )
    study_row_preview_fields: tuple[str, ...] = (
        "study_id",
        "first_author",
        "year",
        "outcome_name",
        "effect_measure",
        "analysis_status",
        "exclusion_reason",
    )
    result_summary_fields: tuple[str, ...] = (
        "result_id",
        "dataset_id",
        "model",
        "pooled_effect",
        "ci_lower",
        "ci_upper",
        "p_value",
        "q_statistic",
        "i_squared",
        "tau_squared",
    )


def initial_analysis_state() -> AnalysisPageState:
    feature = get_feature("meta-analysis")
    return AnalysisPageState(
        title="Analysis / Meta 统计分析预检",
        description="读取 Extraction 输出并检查是否具备最小统计运行条件；可基于结构化 extraction_records 构建 testing analysis-ready dataset，并运行基础 testing pooled effect。当前不生成森林图或敏感性分析。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        profile_options=tuple(profile.profile_type for profile in list_extraction_schema_profiles()),
        outcome_type_options=tuple(item.value for item in OutcomeDataType),
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class AnalysisPage(QWidget):
        def __init__(
            self,
            *,
            project_id: str = "manual-testing-project",
            service: AnalysisPreflightService | None = None,
            dataset_service: AnalysisDatasetService | None = None,
            run_service: AnalysisRunService | None = None,
        ) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or AnalysisPreflightService()
            self._dataset_service = dataset_service or AnalysisDatasetService()
            self._run_service = run_service or AnalysisRunService(dataset_service=self._dataset_service)
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

            dataset_title = QLabel("Analysis-ready Dataset（测试中）")
            dataset_title.setStyleSheet("font-size: 16px; font-weight: 700;")
            root.addWidget(dataset_title)

            self._project_dir_input = QLineEdit()
            self._project_dir_input.setPlaceholderText(self._state.project_dir_placeholder)
            self._project_dir_input.setText(str(default_storage_root() / "projects" / self._project_id))
            root.addWidget(self._project_dir_input)

            self._profile_input = QLineEdit()
            self._profile_input.setPlaceholderText("profile_type，例如 TREATMENT_EFFECT_META")
            if self._state.profile_options:
                self._profile_input.setText(self._state.profile_options[0])
            root.addWidget(self._profile_input)

            self._outcome_name_input = QLineEdit()
            self._outcome_name_input.setPlaceholderText("outcome_name，例如 Mortality")
            root.addWidget(self._outcome_name_input)

            self._effect_measure_input = QLineEdit()
            self._effect_measure_input.setPlaceholderText("effect_measure，例如 OR / RR / MD / SMD / HR")
            root.addWidget(self._effect_measure_input)

            build_button = QPushButton("构建 analysis-ready dataset")
            build_button.clicked.connect(self._build_dataset)
            root.addWidget(build_button)

            self._dataset_summary_label = QLabel("analysis-ready dataset 摘要会显示在这里。")
            self._dataset_summary_label.setWordWrap(True)
            root.addWidget(self._dataset_summary_label)

            run_title = QLabel("Meta Analysis Run（测试中）")
            run_title.setStyleSheet("font-size: 16px; font-weight: 700;")
            root.addWidget(run_title)

            self._dataset_id_input = QLineEdit()
            self._dataset_id_input.setPlaceholderText("analysis_ready_dataset ID")
            root.addWidget(self._dataset_id_input)

            self._model_input = QLineEdit()
            self._model_input.setPlaceholderText("fixed 或 random")
            self._model_input.setText("fixed")
            root.addWidget(self._model_input)

            run_analysis_button = QPushButton("运行基础 Meta 分析")
            run_analysis_button.clicked.connect(self._run_meta_analysis)
            root.addWidget(run_analysis_button)

            self._analysis_result_label = QLabel("pooled result 摘要会显示在这里。")
            self._analysis_result_label.setWordWrap(True)
            root.addWidget(self._analysis_result_label)

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

        def _build_dataset(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            dataset = self._dataset_service.build_analysis_ready_dataset(
                project_dir,
                self._profile_input.text().strip(),
                self._outcome_name_input.text().strip(),
                self._effect_measure_input.text().strip(),
            )
            output_path = self._dataset_service.save_analysis_ready_dataset(project_dir, dataset)
            self._dataset_id_input.setText(dataset.dataset_id)
            self._dataset_summary_label.setText(
                f"Dataset ID：{dataset.dataset_id}\n"
                f"Profile：{dataset.profile_type}\n"
                f"Outcome：{dataset.outcome_name}\n"
                f"Effect measure：{dataset.effect_measure}\n"
                f"Outcome type：{dataset.outcome_data_type or '未匹配'}\n"
                f"Included：{len(dataset.included_extraction_ids)}\n"
                f"Excluded：{len(dataset.excluded_extraction_ids)}\n"
                f"Errors：{', '.join(dataset.validation_errors) or '无'}\n"
                f"Warnings：{', '.join(dataset.validation_warnings) or '无'}\n"
                f"输出：{output_path}"
            )

        def _run_meta_analysis(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            try:
                result = self._run_service.run_meta_analysis(
                    project_dir,
                    self._dataset_id_input.text().strip(),
                    self._model_input.text().strip(),
                )
                output_path = self._run_service.save_analysis_result(project_dir, result)
                self._analysis_result_label.setText(
                    f"Result ID：{result.result_id}\n"
                    f"Dataset ID：{result.dataset_id}\n"
                    f"Model：{result.model}\n"
                    f"Pooled effect：{result.pooled_effect:.6g}\n"
                    f"95% CI：{result.ci_lower:.6g} - {result.ci_upper:.6g}\n"
                    f"P value：{result.p_value:.6g}\n"
                    f"Q：{result.q_statistic:.6g}\n"
                    f"I²：{result.i_squared:.6g}\n"
                    f"tau²：{result.tau_squared:.6g}\n"
                    f"Warnings：{', '.join(result.warnings) or '无'}\n"
                    f"输出：{output_path}"
                )
                self._error_label.setText("")
            except Exception as exc:
                self._analysis_result_label.setText("没有生成 pooled result。")
                self._error_label.setText(f"Meta 分析运行失败：{exc}")

else:

    class AnalysisPage:  # type: ignore[no-redef]
        pass
