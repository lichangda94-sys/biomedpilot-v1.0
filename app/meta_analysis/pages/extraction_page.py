from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.extraction.schema_registry import list_extraction_schema_profiles
from app.meta_analysis.models.extraction import OutcomeDataType
from app.meta_analysis.services.extraction_form_service import ExtractionFormService
from app.meta_analysis.services.extraction_service import ExtractionPoolResult, ExtractionService
from app.shared.feature_availability import get_feature
from app.shared.storage import default_storage_root


@dataclass(frozen=True)
class ExtractionPageState:
    title: str
    description: str
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    warning_summary: str
    project_dir_placeholder: str
    profile_options: tuple[str, ...]
    outcome_type_options: tuple[str, ...]
    study_characteristics_fields: tuple[str, ...]
    binary_outcome_fields: tuple[str, ...]
    continuous_outcome_fields: tuple[str, ...]
    generic_effect_outcome_fields: tuple[str, ...]
    diagnostic_accuracy_outcome_fields: tuple[str, ...]
    proportion_outcome_fields: tuple[str, ...]
    correlation_outcome_fields: tuple[str, ...]
    empty_state: str
    export_path: str
    last_result: ExtractionPoolResult | None = None


def initial_extraction_state() -> ExtractionPageState:
    feature = get_feature("meta-extraction")
    return ExtractionPageState(
        title="Extraction / 数据提取",
        description="读取 Screening 队列并为 included 文献生成数据提取池；结构化 ExtractionRecord 表单处于 testing 状态，并支持 prevalence、correlation、diagnostic basic 等 advanced method 数据结构。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        input_summary="输入：screening_queue / included records，或人工录入 record_id 与 study characteristics。",
        output_summary="输出：extraction_pool、extraction_records 和 extraction_records.csv testing export。",
        next_step="下一步：Analysis-ready dataset builder。",
        warning_summary="validation error 阻止保存；warning 允许保存但必须显示给用户。",
        project_dir_placeholder="project_dir，例如 /path/to/project",
        profile_options=tuple(profile.profile_type for profile in list_extraction_schema_profiles()),
        outcome_type_options=(
            *tuple(item.value for item in OutcomeDataType),
        ),
        study_characteristics_fields=(
            "first_author",
            "year",
            "country",
            "study_design",
            "population",
            "sample_size",
            "intervention_or_exposure",
            "comparator",
            "follow_up",
            "study_notes",
        ),
        binary_outcome_fields=(
            "outcome_name",
            "effect_measure",
            "experimental_events",
            "experimental_total",
            "control_events",
            "control_total",
            "timepoint",
            "subgroup",
            "outcome_notes",
        ),
        continuous_outcome_fields=(
            "outcome_name",
            "effect_measure",
            "experimental_mean",
            "experimental_sd",
            "experimental_total",
            "control_mean",
            "control_sd",
            "control_total",
            "unit",
            "timepoint",
            "subgroup",
            "outcome_notes",
        ),
        generic_effect_outcome_fields=(
            "outcome_name",
            "effect_measure",
            "effect",
            "ci_lower",
            "ci_upper",
            "standard_error",
            "p_value",
            "adjusted",
            "covariates",
            "timepoint",
            "subgroup",
            "outcome_notes",
        ),
        diagnostic_accuracy_outcome_fields=(
            "outcome_name",
            "effect_measure",
            "tp",
            "fp",
            "fn",
            "tn",
            "sensitivity",
            "specificity",
            "cutoff",
            "index_test",
            "reference_standard",
            "outcome_notes",
        ),
        proportion_outcome_fields=(
            "outcome_name",
            "effect_measure",
            "events",
            "total",
            "population_source",
            "diagnostic_criteria",
            "timepoint",
            "subgroup",
            "outcome_notes",
        ),
        correlation_outcome_fields=(
            "outcome_name",
            "effect_measure",
            "r",
            "sample_size",
            "correlation_type",
            "p_value",
            "variable_x",
            "variable_y",
            "outcome_notes",
        ),
        empty_state="没有 extraction_pool 候选文献时，可以先生成提取池或手动输入 record_id / study_id。",
        export_path="project_dir/exports/extraction_records.csv",
    )


try:
    from PySide6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QFileDialog = QFrame = QHBoxLayout = QLabel = QLineEdit = QPushButton = QVBoxLayout = QWidget = None


if QWidget is not None:

    class ExtractionPage(QWidget):
        def __init__(
            self,
            *,
            project_id: str = "manual-testing-project",
            service: ExtractionService | None = None,
            form_service: ExtractionFormService | None = None,
        ) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or ExtractionService()
            self._form_service = form_service or ExtractionFormService()
            self._state = initial_extraction_state()
            self._form_inputs: dict[str, QLineEdit] = {}

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
            self._path_input.setPlaceholderText("选择或粘贴 Screening 队列 JSON 文件路径")
            choose_button = QPushButton("选择 Screening 队列")
            choose_button.clicked.connect(self._choose_file)
            row.addWidget(self._path_input, 1)
            row.addWidget(choose_button)
            root.addLayout(row)

            run_button = QPushButton("生成数据提取池")
            run_button.clicked.connect(self._create_pool)
            root.addWidget(run_button)

            self._status_label = QLabel("提取状态：等待 Screening 队列")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("提取池摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)

            form_card = QFrame()
            form_card.setStyleSheet("QFrame { border: 1px solid #D8DEE9; border-radius: 8px; background: #FFFFFF; }")
            form_layout = QVBoxLayout(form_card)
            form_title = QLabel("结构化 ExtractionRecord 表单（测试中）")
            form_title.setStyleSheet("font-weight: 700;")
            form_layout.addWidget(form_title)
            form_hint = QLabel("保存时会调用 validation service；error 会阻止保存，warning 会显示但允许保存。")
            form_hint.setWordWrap(True)
            form_layout.addWidget(form_hint)
            self._project_dir_input = QLineEdit()
            self._project_dir_input.setPlaceholderText(self._state.project_dir_placeholder)
            form_layout.addWidget(self._project_dir_input)
            for field_name in (
                "record_id",
                "study_id",
                "reviewer_id",
                "profile_type",
                "outcome_data_type",
                "source_location",
                "notes",
                *self._state.study_characteristics_fields,
                *self._state.generic_effect_outcome_fields,
                *self._state.diagnostic_accuracy_outcome_fields,
                *self._state.proportion_outcome_fields,
                *self._state.correlation_outcome_fields,
                *[
                    field
                    for field in self._state.binary_outcome_fields + self._state.continuous_outcome_fields
                    if field
                    not in (
                        self._state.generic_effect_outcome_fields
                        + self._state.diagnostic_accuracy_outcome_fields
                        + self._state.proportion_outcome_fields
                        + self._state.correlation_outcome_fields
                    )
                ],
            ):
                self._add_form_input(form_layout, field_name)
            self._form_inputs["profile_type"].setPlaceholderText(" / ".join(self._state.profile_options))
            self._form_inputs["outcome_data_type"].setPlaceholderText("binary / continuous / generic_effect / proportion / correlation / diagnostic_accuracy")
            self._form_inputs["effect_measure"].setPlaceholderText("OR / RR / RD / MD / SMD / HR / PREVALENCE / CORRELATION / DOR")
            save_record_button = QPushButton("保存 ExtractionRecord")
            save_record_button.clicked.connect(self._save_structured_record)
            form_layout.addWidget(save_record_button)
            export_records_button = QPushButton("导出 extraction_records.csv")
            export_records_button.clicked.connect(self._export_structured_records)
            form_layout.addWidget(export_records_button)
            self._validation_label = QLabel(self._state.empty_state)
            self._validation_label.setWordWrap(True)
            form_layout.addWidget(self._validation_label)
            root.addWidget(form_card)

            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet("color: #B42318;")
            root.addWidget(self._error_label)
            next_button = QPushButton("下一步：Analysis")
            next_button.setEnabled(False)
            root.addWidget(next_button)
            root.addStretch(1)

        def _choose_file(self) -> None:
            path, _selected_filter = QFileDialog.getOpenFileName(self, "选择 Screening 队列", "", "Screening queue (*.json)")
            if path:
                self._path_input.setText(path)

        def _create_pool(self) -> None:
            result = self._service.create_pool(project_id=self._project_id, screening_queue_path=self._path_input.text())
            if result.success:
                self._status_label.setText("提取状态：提取池已生成")
                self._summary_label.setText(
                    f"来源：{result.source_path}\n"
                    f"筛选记录：{result.total_screening_records}\n"
                    f"Included：{result.included_records}\n"
                    f"提取记录：{result.extraction_records}\n"
                    f"输出：{result.output_path}"
                )
                self._error_label.setText("")
                candidates = self._form_service.load_candidate_records(result.output_path)
                if candidates:
                    first = candidates[0]
                    self._form_inputs["record_id"].setText(first.record_id)
                    self._form_inputs["study_id"].setText(first.study_id)
                    self._validation_label.setText(f"候选文献：{len(candidates)} 条，已载入第一条 record_id。")
                else:
                    self._validation_label.setText(self._state.empty_state)
            else:
                self._status_label.setText("提取状态：失败")
                self._summary_label.setText("没有生成提取池。")
                self._error_label.setText(result.message)

        def _add_form_input(self, layout: QVBoxLayout, field_name: str) -> None:
            if field_name in self._form_inputs:
                return
            field = QLineEdit()
            field.setPlaceholderText(field_name)
            self._form_inputs[field_name] = field
            layout.addWidget(field)

        def _save_structured_record(self) -> None:
            result = self._form_service.save_extraction_record_from_form(
                project_dir=self._project_dir(),
                project_id=self._project_id,
                form_data=self._form_data(),
            )
            if result.success:
                self._validation_label.setText(
                    f"保存完成：{result.output_path}\nWarnings：{', '.join(result.validation.warnings) or '无'}"
                )
                self._error_label.setText("")
            else:
                self._validation_label.setText("保存被阻止。")
                self._error_label.setText("; ".join(result.validation.errors) or result.message)

        def _export_structured_records(self) -> None:
            result = self._form_service.export_extraction_records_csv(
                project_dir=self._project_dir(),
                project_id=self._project_id,
            )
            if result.success:
                self._validation_label.setText(f"导出完成：{result.output_path}")
                self._error_label.setText("")
            else:
                self._validation_label.setText("导出失败。")
                self._error_label.setText(result.message)

        def _form_data(self) -> dict[str, object]:
            data = {key: value.text() for key, value in self._form_inputs.items()}
            data["profile_type"] = data.get("profile_type") or (self._state.profile_options[0] if self._state.profile_options else "")
            data["outcome_data_type"] = data.get("outcome_data_type") or OutcomeDataType.BINARY.value
            return data

        def _project_dir(self) -> Path:
            text = self._project_dir_input.text().strip()
            if text:
                return Path(text)
            return default_storage_root() / "projects" / self._project_id / "meta_analysis"

else:

    class ExtractionPage:  # type: ignore[no-redef]
        pass
