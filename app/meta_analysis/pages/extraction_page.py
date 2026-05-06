from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.extraction.schema_registry import list_extraction_schema_profiles
from app.meta_analysis.models.extraction import OutcomeDataType
from app.meta_analysis.services.extraction_form_service import ExtractionFormService
from app.meta_analysis.services.extraction_schema_registry_v1_service import (
    EXTRACTION_SCHEMA_REGISTRY_V1_SCHEMA_VERSION,
    ExtractionSchemaRegistryV1Service,
)
from app.meta_analysis.services.extraction_service import ExtractionPoolResult, ExtractionService
from app.meta_analysis.ui_text import (
    DEVELOPER_INFO_TITLE_ZH,
    EXTRACTION_DESCRIPTION_ZH,
    EXTRACTION_FIELD_ZH,
    EXTRACTION_TITLE_ZH,
    INTERNAL_BETA_STATUS_ZH,
)
from app.shared.feature_availability import get_feature
from app.shared.storage import default_storage_root
from app.version import APP_VERSION


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
    field_groups: dict[str, tuple[str, ...]]
    required_fields: dict[str, tuple[str, ...]]
    draft_status_fields: tuple[str, ...]
    outcome_row_controls: tuple[str, ...]
    field_error_targets: tuple[str, ...]
    completeness_summary_fields: tuple[str, ...]
    export_readiness_warning: str
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
    extraction_schema_registry_version: str = EXTRACTION_SCHEMA_REGISTRY_V1_SCHEMA_VERSION
    extraction_schema_registry_path: str = ""
    extraction_schema_count: int = 0
    extraction_schema_options: tuple[str, ...] = ()
    title_zh: str = EXTRACTION_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = EXTRACTION_DESCRIPTION_ZH
    input_summary_zh: str = "输入：最终纳入研究、提取 schema、人工录入字段和来源位置。"
    output_summary_zh: str = "输出：extraction_records、CSV、validation report 和 manual edits log。"
    next_step_zh: str = "下一步：完成数据提取后进入质量评价或分析数据集检查。"
    warning_summary_zh: str = "缺失必填字段、无来源位置或完整性不足时需要 reviewer 复核。"
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


@dataclass(frozen=True)
class ExtractionStudyTableRow:
    record_id: str
    study_id: str
    title: str
    first_author: str
    year: str
    status: str
    completeness_score: float | None = None
    missing_required_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExtractionOutcomeRowTemplate:
    outcome_data_type: str
    fields: tuple[str, ...]
    required_fields: tuple[str, ...]
    help_text: str


@dataclass(frozen=True)
class SimplifiedExtractionPageState:
    title: str
    status_label: str
    description: str
    project_dir: str
    study_rows: tuple[ExtractionStudyTableRow, ...]
    outcome_row_templates: tuple[ExtractionOutcomeRowTemplate, ...]
    field_help_text: dict[str, str]
    required_field_markers: dict[str, bool]
    draft_count: int
    saved_record_count: int
    manual_edits_log_path: str
    extraction_records_path: str
    extraction_records_csv_path: str
    validation_report_path: str
    copy_previous_available: bool
    completeness_summary: dict[str, object]
    export_ready: bool
    warnings: tuple[str, ...]
    testing_limitations: tuple[str, ...]
    extraction_schema_registry_version: str = EXTRACTION_SCHEMA_REGISTRY_V1_SCHEMA_VERSION
    extraction_schema_registry_path: str = ""
    extraction_schema_count: int = 0
    extraction_schema_options: tuple[str, ...] = ()
    selected_extraction_schema_path: str = ""
    title_zh: str = EXTRACTION_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = EXTRACTION_DESCRIPTION_ZH
    input_summary_zh: str = "输入：final_included_studies、drafts 和结构化 extraction 表单。"
    output_summary_zh: str = "输出：extraction_records.json、extraction_records.csv、validation report 和 manual_edits_log。"
    next_step_zh: str = "下一步：完成质量评价，然后构建 analysis-ready dataset。"
    empty_state_zh: str = "没有最终纳入研究时，请先完成全文筛选。"
    field_labels_zh: dict[str, str] | None = None
    outcome_type_labels_zh: dict[str, str] | None = None
    export_ready_zh: str = ""
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


def initial_extraction_state() -> ExtractionPageState:
    feature = get_feature("meta-extraction")
    schema_service = ExtractionSchemaRegistryV1Service()
    schemas = schema_service.default_schemas()
    return ExtractionPageState(
        title="Extraction / 数据提取",
        description="读取 Screening 队列并为 included 文献生成数据提取池；结构化 ExtractionRecord 表单处于 testing 状态，并支持 prevalence、correlation、diagnostic basic 等 advanced method 数据结构。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        input_summary="输入：screening_queue / included records，或人工录入 record_id 与 study characteristics。",
        output_summary="输出：extraction_pool、extraction_records 和 extraction_records.csv testing export。",
        next_step="下一步：Analysis-ready dataset builder。",
        warning_summary="validation error 阻止保存；warning 允许保存但必须显示给用户。",
        project_dir_placeholder="project_dir，例如 /path/to/project",
        field_groups={
            "study_characteristics": (
                "first_author",
                "year",
                "country",
                "study_design",
                "population",
                "sample_size",
                "intervention_or_exposure",
                "comparator",
                "follow_up",
            ),
            "outcomes": ("binary", "continuous", "generic_effect", "diagnostic_accuracy", "proportion", "correlation"),
            "review_metadata": ("record_id", "study_id", "reviewer_id", "profile_type", "source_location", "notes"),
        },
        required_fields={
            "record": ("record_id", "study_id", "reviewer_id", "profile_type"),
            "study_characteristics": ("first_author", "year", "sample_size"),
            "outcome_common": ("outcome_name", "effect_measure"),
        },
        draft_status_fields=("draft_id", "updated_at", "record_id", "reviewer_id"),
        outcome_row_controls=("add_outcome_row", "remove_outcome_row", "duplicate_outcome_row"),
        field_error_targets=("field_name", "message", "severity", "outcome_index"),
        completeness_summary_fields=("completeness_score", "missing_required_fields", "ready_for_export"),
        export_readiness_warning="导出前会检查 ExtractionRecord 完整性；不完整记录会生成 warning。",
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
        extraction_schema_registry_path="extraction/schema_registry_v1.json",
        extraction_schema_count=len(schemas),
        extraction_schema_options=tuple(schema.meta_type for schema in schemas),
        title_zh=EXTRACTION_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=EXTRACTION_DESCRIPTION_ZH,
    )


def simplified_extraction_state_from_project(
    project_dir: Path,
    *,
    service: ExtractionFormService | None = None,
    schema_registry_service: ExtractionSchemaRegistryV1Service | None = None,
) -> SimplifiedExtractionPageState:
    project_dir = project_dir.expanduser().resolve()
    service = service or ExtractionFormService()
    schema_registry_service = schema_registry_service or ExtractionSchemaRegistryV1Service()
    base = initial_extraction_state()
    registry = schema_registry_service.load_registry(project_dir)
    records = service.load_extraction_records(project_dir)
    drafts = service.load_drafts(project_dir)
    completeness = service.pre_export_completeness_check(project_dir)
    final_included_rows = _final_included_rows(project_dir)
    rows = _study_rows_from_records(records, service)
    if not rows:
        rows = _study_rows_from_final_included(final_included_rows)
    warnings: list[str] = []
    if not rows:
        warnings.append("no_included_studies_for_extraction")
    if completeness.get("warnings"):
        warnings.extend(str(item) for item in completeness.get("warnings", []))
    if not (project_dir / "fulltext" / "final_included_studies.json").exists():
        warnings.append("missing_final_included_studies")
    return SimplifiedExtractionPageState(
        title="Simplified Extraction Workspace",
        status_label="Testing / Developer Preview",
        description="简化的人工数据提取 page-state：按 study characteristics 表格和 outcome rows 组织字段，复用现有 ExtractionRecord core、draft、validation 和 completeness score。",
        project_dir=str(project_dir),
        study_rows=tuple(rows),
        outcome_row_templates=_outcome_templates(base),
        field_help_text=_field_help_text(),
        required_field_markers={field_name: True for group in base.required_fields.values() for field_name in group},
        draft_count=len(drafts),
        saved_record_count=len(records),
        manual_edits_log_path=str(project_dir / "extraction" / "manual_edits_log.jsonl"),
        extraction_records_path=str(project_dir / "extraction" / "extraction_records.json"),
        extraction_records_csv_path=str(project_dir / "exports" / "extraction_records.csv"),
        validation_report_path=str(project_dir / "extraction" / "extraction_validation_report.json"),
        copy_previous_available=bool(records),
        completeness_summary=completeness,
        export_ready=bool(completeness.get("ready_for_export", False)),
        warnings=tuple(warnings),
        testing_limitations=(
            "Developer Preview：该视图不改变 extraction schema，只整理人工录入体验。",
            "人工补充必须写入 manual_edits_log.jsonl；不能静默覆盖正式分析数据。",
            "缺失 required fields 会阻止或提示保存，取决于 validation service 的 error/warning 级别。",
            "Extraction Schema Registry v1 只生成表单模板和校验规则，不写最终提取值。",
        ),
        extraction_schema_registry_version=registry.schema_version,
        extraction_schema_registry_path=str(schema_registry_service.registry_path(project_dir)),
        extraction_schema_count=len(registry.schemas),
        extraction_schema_options=tuple(schema.meta_type for schema in registry.schemas),
        selected_extraction_schema_path=str(schema_registry_service.selection_path(project_dir)),
        title_zh=EXTRACTION_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=EXTRACTION_DESCRIPTION_ZH,
        field_labels_zh={field: EXTRACTION_FIELD_ZH.get(field, field) for field in _all_extraction_fields(base)},
        outcome_type_labels_zh={
            "binary": "二分类结局",
            "continuous": "连续变量结局",
            "generic_effect": "已报告效应量",
            "diagnostic_accuracy": "诊断准确性基础数据",
            "proportion": "单臂比例 / 患病率",
            "correlation": "相关性结局",
        },
        export_ready_zh="可以导出" if bool(completeness.get("ready_for_export", False)) else "需要补齐后再导出",
    )


def _outcome_templates(base: ExtractionPageState) -> tuple[ExtractionOutcomeRowTemplate, ...]:
    required = tuple(base.required_fields["outcome_common"])
    return (
        ExtractionOutcomeRowTemplate("binary", base.binary_outcome_fields, required, "二分类结局：事件数和总人数用于 OR/RR/RD。"),
        ExtractionOutcomeRowTemplate("continuous", base.continuous_outcome_fields, required, "连续变量结局：均值、SD 和样本量用于 MD/SMD。"),
        ExtractionOutcomeRowTemplate("generic_effect", base.generic_effect_outcome_fields, required, "已报告效应量：effect + CI 或 SE，用于 HR/OR/RR inverse variance。"),
        ExtractionOutcomeRowTemplate("diagnostic_accuracy", base.diagnostic_accuracy_outcome_fields, ("outcome_name", "tp", "fp", "fn", "tn"), "诊断基础表：当前不是 bivariate/HSROC。"),
        ExtractionOutcomeRowTemplate("proportion", base.proportion_outcome_fields, ("outcome_name", "events", "total"), "单臂比例或患病率：记录 transformation 方法供 Analysis 解释。"),
        ExtractionOutcomeRowTemplate("correlation", base.correlation_outcome_fields, ("outcome_name", "r", "sample_size"), "相关性 Meta：r 会转换为 Fisher z。"),
    )


def _field_help_text() -> dict[str, str]:
    return {
        "record_id": "来自 literature/screening/fulltext 的文献记录 ID。",
        "study_id": "稳定 study 标识；同一研究多篇报告应使用一致 study_id。",
        "source_location": "记录页码、表格编号或补充材料位置。",
        "sample_size": "研究总样本量；必须大于 0。",
        "outcome_name": "结局名称，必须与后续 Analysis 选择一致。",
        "effect_measure": "OR/RR/RD/MD/SMD/HR/PREVALENCE/CORRELATION/DOR 等。",
        "manual_supplement": "人工补充必须记录 before/after、source location、note 和是否用于正式分析。",
    }


def _all_extraction_fields(base: ExtractionPageState) -> tuple[str, ...]:
    fields: list[str] = []
    for group in (
        base.study_characteristics_fields,
        base.binary_outcome_fields,
        base.continuous_outcome_fields,
        base.generic_effect_outcome_fields,
        base.diagnostic_accuracy_outcome_fields,
        base.proportion_outcome_fields,
        base.correlation_outcome_fields,
        ("record_id", "study_id", "reviewer_id", "profile_type", "source_location", "manual_supplement"),
    ):
        fields.extend(group)
    return tuple(dict.fromkeys(fields))


def _final_included_rows(project_dir: Path) -> list[dict[str, object]]:
    path = project_dir / "fulltext" / "final_included_studies.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    rows = payload.get("included_studies", [])
    return [dict(item) for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []


def _study_rows_from_records(records: list[object], service: ExtractionFormService) -> list[ExtractionStudyTableRow]:
    rows: list[ExtractionStudyTableRow] = []
    for record in records:
        summary = service.field_validation_summary(record)
        rows.append(
            ExtractionStudyTableRow(
                record_id=record.record_id,
                study_id=record.study_id,
                title="",
                first_author=record.study_characteristics.first_author,
                year=str(record.study_characteristics.year or ""),
                status=record.validation_status,
                completeness_score=summary.completeness_score,
                missing_required_fields=tuple(summary.missing_required_fields),
            )
        )
    return rows


def _study_rows_from_final_included(rows: list[dict[str, object]]) -> list[ExtractionStudyTableRow]:
    return [
        ExtractionStudyTableRow(
            record_id=str(item.get("record_id", "")),
            study_id=str(item.get("study_id") or item.get("record_id", "")),
            title=str(item.get("title", "")),
            first_author=str(item.get("first_author", "")),
            year=str(item.get("year", "")),
            status="needs_extraction",
        )
        for item in rows
    ]


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
            title = QLabel(f"{self._state.title_zh} · {self._state.status_label_zh}")
            title.setStyleSheet("font-size: 20px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description_zh)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label_zh} / {self._state.status_label}"))

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
