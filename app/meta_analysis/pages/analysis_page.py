from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.extraction.schema_registry import list_extraction_schema_profiles
from app.meta_analysis.models.analysis_dataset import AnalysisReadyDataset
from app.meta_analysis.models.analysis_result import AnalysisResult
from app.meta_analysis.models.statistical_result_state import (
    STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN,
    STATISTICAL_RESULT_STATE_NOT_RUN,
    blocks_formal_report_claim,
    statistical_result_state_label_zh,
)
from app.meta_analysis.services.effect_size_normalization_service import EffectSizeNormalizationService
from app.meta_analysis.models.extraction import OutcomeDataType
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.analysis_plan_service import (
    ANALYSIS_PLAN_DRAFT_SCHEMA_VERSION,
    ANALYSIS_PLAN_M7_SCHEMA_VERSION,
    CONFIRMED_ANALYSIS_PLAN_SCHEMA_VERSION,
    AnalysisPlanService,
)
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.services.analysis_setup_service import BLOCKED_ADVANCED_METHODS, AnalysisSetupService
from app.meta_analysis.services.analysis_service import AnalysisPreflightResult, AnalysisPreflightService
from app.meta_analysis.services.figure_result_service import FigureResultService
from app.meta_analysis.services.meta_statistics_engine_service import (
    META_STATISTICS_ANALYSIS_MANIFEST_SCHEMA_VERSION,
    META_STATISTICS_ANALYSIS_RUN_SCHEMA_VERSION,
    META_STATISTICS_STANDARDIZED_RESULT_SCHEMA_VERSION,
    MetaStatisticsEngineService,
)
from app.meta_analysis.services.pairwise_meta_executor_service import PairwiseMetaExecutorService
from app.meta_analysis.ui_text import (
    ANALYSIS_BLOCKED_METHOD_ZH,
    ANALYSIS_DESCRIPTION_ZH,
    ANALYSIS_MODEL_ZH,
    ANALYSIS_SECTION_ZH,
    ANALYSIS_TITLE_ZH,
    DEVELOPER_INFO_TITLE_ZH,
    INTERNAL_BETA_STATUS_ZH,
)
from app.shared.feature_availability import get_feature
from app.shared.storage import default_storage_root
from app.ui_style_tokens import meta_card_stylesheet, meta_error_text_style, meta_title_style
from app.version import APP_VERSION


@dataclass(frozen=True)
class AnalysisPageState:
    title: str
    description: str
    status_label: str
    input_summary: str
    output_summary: str
    next_step: str
    empty_state: str
    warning_summary: str
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
    figure_artifact_fields: tuple[str, ...] = (
        "analysis_result_id",
        "forest_plot_path",
        "result_table_path",
        "artifact_status",
    )
    advanced_analysis_fields: tuple[str, ...] = (
        "subgroup_variable",
        "subgroup_result_id",
        "leave_one_out_result_id",
        "publication_bias_result_id",
        "egger_test",
        "begg_test_placeholder",
        "funnel_plot_path",
        "small_study_warning",
    )
    title_zh: str = ANALYSIS_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = ANALYSIS_DESCRIPTION_ZH
    input_summary_zh: str = "输入：extraction_records、analysis-ready dataset、模型设置和适用性规则。"
    output_summary_zh: str = "输出：analysis_plan、analysis_ready_dataset、analysis_result、applicability_warnings、图表和结果表。"
    next_step_zh: str = "下一步：生成图表、PRISMA 和 testing 报告。"
    empty_state_zh: str = "没有 extraction_records 或匹配 outcome 时显示 warning，不静默运行统计。"
    warning_summary_zh: str = "不满足适用条件时显示 warning 或 blocking error；Network Meta / HSROC / Meta 回归保持未实现。"
    section_labels_zh: dict[str, str] | None = None
    model_option_labels_zh: tuple[str, ...] = ()
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


@dataclass(frozen=True)
class AnalysisSetupPageState:
    title: str
    status_label: str
    description: str
    setup_inputs: tuple[str, ...]
    model_options: tuple[str, ...]
    zero_event_correction_options: tuple[str, ...]
    subgroup_options: tuple[str, ...]
    available_outcomes: tuple[dict[str, object], ...]
    selected_plan_path: str
    analysis_ready_dataset_path: str
    analysis_result_path: str
    applicability_warnings_path: str
    preflight_summary: dict[str, object]
    run_result_summary: dict[str, object]
    result_state_summary: dict[str, object]
    effect_size_normalization_summary: dict[str, object]
    pairwise_executor_summary: dict[str, object]
    advanced_method_status: dict[str, str]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    empty_state: str
    next_step: str
    testing_limitations: tuple[str, ...]
    title_zh: str = ANALYSIS_TITLE_ZH
    status_label_zh: str = "内部测试"
    description_zh: str = ANALYSIS_DESCRIPTION_ZH
    input_summary_zh: str = "输入：profile、outcome、effect measure、模型、零事件校正和 subgroup。"
    output_summary_zh: str = "输出：analysis_plan、analysis_ready_dataset、analysis_result 和 applicability_warnings。"
    next_step_zh: str = "下一步：无 blocking error 时生成图表与结果表。"
    empty_state_zh: str = "没有可用 outcome 时，请回到数据提取检查。"
    section_labels_zh: dict[str, str] | None = None
    model_option_labels_zh: tuple[str, ...] = ()
    advanced_method_status_zh: dict[str, str] | None = None
    effect_size_normalization_labels_zh: tuple[str, ...] = (
        "效应量标准化预检查",
        "可用于后续统计的研究数",
        "需要用户检查",
        "字段不完整",
        "不支持的效应量类型",
    )
    pairwise_executor_labels_zh: tuple[str, ...] = (
        "统计执行状态",
        "模型",
        "纳入研究数",
        "合并效应量",
        "95% CI",
        "异质性 I²",
        "测试阶段提示",
        "需要用户审核后才能进入报告",
    )
    developer_info_title_zh: str = DEVELOPER_INFO_TITLE_ZH


@dataclass(frozen=True)
class AnalysisPlanBuilderPageState:
    title: str
    status_label: str
    description: str
    project_dir: str
    draft_schema_version: str
    confirmed_schema_version: str
    draft_path: str
    confirmed_path: str
    manifest_path: str
    confirmed_protocol_status: str
    draft_status: str
    confirmed_status: str
    m7_schema_version: str
    plan_state: str
    meta_type: str
    effect_measure: str
    effect_measure_type: str
    model_default: str
    model_preference: str
    included_study_count: int
    included_candidate_count: int
    excluded_candidate_count: int
    warnings: tuple[str, ...]
    readiness_warnings_zh: tuple[str, ...]
    primary_actions: tuple[str, ...]
    safety_flags: dict[str, bool]
    title_zh: str = "分析计划"
    status_label_zh: str = "内部测试"
    description_zh: str = "确认研究类型、效应量、模型、异质性、亚组/敏感性/发表偏倚计划；确认后仍不运行统计。"


@dataclass(frozen=True)
class MetaStatisticsEnginePageState:
    title: str
    status_label: str
    description: str
    project_dir: str
    run_schema_version: str
    result_schema_version: str
    manifest_schema_version: str
    confirmed_plan_status: str
    latest_run_id: str
    latest_result_id: str
    run_count: int
    run_path: str
    result_path: str
    manifest_path: str
    input_validation_status: str
    result_status: str
    result_state: str
    result_state_label_zh: str
    warnings: tuple[str, ...]
    primary_actions: tuple[str, ...]
    safety_flags: dict[str, bool]
    testing_level_notice: str = "testing-level statistics only; not production-grade."
    title_zh: str = "统计引擎"
    status_label_zh: str = "内部测试"
    description_zh: str = "必须基于已确认分析计划运行；输出 testing-level 标准结果，不生成医学结论。"


def initial_analysis_state() -> AnalysisPageState:
    feature = get_feature("meta-analysis")
    return AnalysisPageState(
        title="Analysis / Meta 统计分析预检",
        description="读取 Extraction 输出并检查是否具备最小统计运行条件；可基于结构化 extraction_records 构建 testing analysis-ready dataset，并运行基础 testing pooled effect。新增 prevalence、correlation、diagnostic basic、subgroup、leave-one-out、publication bias basic 和 funnel plot 支持；network meta 显示 not implemented。",
        status_label=feature.status.display_label() if feature is not None else "测试中",
        input_summary="输入：extraction_pool preflight/预检文件或 extraction_records / analysis_ready_dataset。",
        output_summary="输出：analysis_preflight、analysis_ready_dataset、analysis_result、forest/funnel plot 和 result table。",
        next_step="下一步：Reporting / PRISMA / formal Markdown testing report。",
        empty_state="没有 extraction_records 或匹配 outcome 时显示明确错误，不运行正式统计。",
        warning_summary="区分 preflight、dataset、run result 和 advanced analysis；network meta 明确 not implemented。",
        profile_options=tuple(profile.profile_type for profile in list_extraction_schema_profiles()),
        outcome_type_options=tuple(item.value for item in OutcomeDataType),
        title_zh=ANALYSIS_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=ANALYSIS_DESCRIPTION_ZH,
        section_labels_zh=ANALYSIS_SECTION_ZH,
        model_option_labels_zh=tuple(ANALYSIS_MODEL_ZH[item] for item in ("fixed", "random")),
    )


def analysis_setup_state_from_project(
    project_dir: Path,
    *,
    service: AnalysisSetupService | None = None,
) -> AnalysisSetupPageState:
    project_dir = project_dir.expanduser().resolve()
    setup_service = service or AnalysisSetupService()
    warnings: list[str] = ["analysis_setup_developer_preview"]
    errors: list[str] = []
    try:
        available_outcomes = tuple(setup_service.list_available_outcomes(project_dir))
    except Exception as exc:
        available_outcomes = ()
        warnings.append(f"available_outcomes_unavailable:{exc}")
    plan_path = project_dir / "analysis" / "analysis_plan.json"
    dataset_path = project_dir / "analysis" / "analysis_ready_dataset.json"
    result_path = project_dir / "analysis" / "analysis_result.json"
    warnings_path = project_dir / "analysis" / "applicability_warnings.json"
    preflight_summary = _analysis_alias_summary(dataset_path, "dataset")
    run_result_summary = _analysis_alias_summary(result_path, "result")
    normalization_summary = _effect_size_normalization_summary(project_dir)
    pairwise_summary = _pairwise_executor_summary(project_dir)
    if not plan_path.exists():
        warnings.append("analysis_plan_missing")
    if not dataset_path.exists():
        warnings.append("analysis_ready_dataset_alias_missing")
    if not result_path.exists():
        warnings.append("analysis_result_alias_missing")
    if warnings_path.exists():
        payload = _load_json(warnings_path)
        warnings.extend(str(item) for item in payload.get("warnings", []) if item)
        errors.extend(str(item) for item in payload.get("errors", []) if item)
    return AnalysisSetupPageState(
        title="Analysis Setup / 统计设置与适用性解释",
        status_label="测试中 / Developer Preview",
        description="用于把 Analysis-ready dataset、基础 Meta 统计运行和 applicability warnings 串成 setup → run → explain 流程。",
        setup_inputs=("profile_type", "outcome_name", "effect_measure", "model", "zero_event_correction", "subgroup_variable"),
        model_options=("fixed", "random"),
        zero_event_correction_options=("continuity_0.5", "none"),
        subgroup_options=_available_subgroup_options(available_outcomes),
        available_outcomes=available_outcomes,
        selected_plan_path=str(plan_path),
        analysis_ready_dataset_path=str(dataset_path),
        analysis_result_path=str(result_path),
        applicability_warnings_path=str(warnings_path),
        preflight_summary=preflight_summary,
        run_result_summary=run_result_summary,
        result_state_summary={
            "state": run_result_summary.get("result_state", STATISTICAL_RESULT_STATE_NOT_RUN),
            "label_zh": run_result_summary.get("result_state_label_zh", statistical_result_state_label_zh(STATISTICAL_RESULT_STATE_NOT_RUN)),
            "blocks_formal_report_claim": run_result_summary.get("blocks_formal_report_claim", True),
        },
        effect_size_normalization_summary=normalization_summary,
        pairwise_executor_summary=pairwise_summary,
        advanced_method_status={
            "network_meta": BLOCKED_ADVANCED_METHODS["network_meta"],
            "hsroc": BLOCKED_ADVANCED_METHODS["hsroc"],
            "meta_regression": BLOCKED_ADVANCED_METHODS["meta_regression"],
        },
        warnings=tuple(_dedupe(warnings)),
        errors=tuple(_dedupe(errors)),
        empty_state="没有 extraction_records 或可匹配 outcome 时显示 warning，不静默运行统计。",
        next_step="运行通过后进入 Figures / Tables；若存在 blocking errors，先回到 Extraction 或 Analysis Setup 修正。",
        testing_limitations=(
            "Network Meta not implemented.",
            "Diagnostic HSROC not implemented.",
            "Meta-regression not implemented.",
            "Developer Preview 统计结果需要人工复核后才能用于正式研究。",
        ),
        title_zh=ANALYSIS_TITLE_ZH,
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
        description_zh=ANALYSIS_DESCRIPTION_ZH,
        section_labels_zh=ANALYSIS_SECTION_ZH,
        model_option_labels_zh=tuple(ANALYSIS_MODEL_ZH[item] for item in ("fixed", "random")),
        advanced_method_status_zh={key: ANALYSIS_BLOCKED_METHOD_ZH.get(key, value) for key, value in {
            "network_meta": BLOCKED_ADVANCED_METHODS["network_meta"],
            "hsroc": BLOCKED_ADVANCED_METHODS["hsroc"],
            "meta_regression": BLOCKED_ADVANCED_METHODS["meta_regression"],
        }.items()},
    )


def analysis_plan_builder_state_from_project(
    project_dir: Path,
    *,
    service: AnalysisPlanService | None = None,
) -> AnalysisPlanBuilderPageState:
    project_dir = project_dir.expanduser().resolve()
    plan_service = service or AnalysisPlanService()
    draft = plan_service.load_draft(project_dir)
    confirmed = plan_service.load_confirmed(project_dir)
    confirmed_protocol_path = project_dir / "protocol" / "pico_workspace_confirmed.json"
    warnings: list[str] = []
    if not confirmed_protocol_path.exists():
        warnings.append("confirmed_protocol_missing")
    if not draft:
        warnings.append("analysis_plan_draft_missing")
    return AnalysisPlanBuilderPageState(
        title="Analysis Plan Builder v1",
        status_label="Draft-first / Developer Preview",
        description="根据 confirmed protocol、extraction effect rows 和 quality summary 生成分析计划草稿；用户确认前不能用于运行统计。",
        project_dir=str(project_dir),
        draft_schema_version=ANALYSIS_PLAN_DRAFT_SCHEMA_VERSION,
        confirmed_schema_version=CONFIRMED_ANALYSIS_PLAN_SCHEMA_VERSION,
        draft_path=str(plan_service.draft_path(project_dir)),
        confirmed_path=str(plan_service.confirmed_path(project_dir)),
        manifest_path=str(plan_service.manifest_path(project_dir)),
        confirmed_protocol_status="confirmed" if confirmed_protocol_path.exists() else "missing",
        draft_status=str(draft.get("status", "missing")) if draft else "missing",
        confirmed_status="confirmed" if confirmed else "not_confirmed",
        m7_schema_version=ANALYSIS_PLAN_M7_SCHEMA_VERSION,
        plan_state=str((confirmed or draft).get("plan_state", "missing")) if (confirmed or draft) else "missing",
        meta_type=str(draft.get("meta_type", "")) if draft else "",
        effect_measure=str(draft.get("effect_measure", "")) if draft else "",
        effect_measure_type=str((confirmed or draft).get("effect_measure_type", "")) if (confirmed or draft) else "",
        model_default=str(draft.get("model_default", "")) if draft else "",
        model_preference=str((confirmed or draft).get("model_preference", "")) if (confirmed or draft) else "",
        included_study_count=int((confirmed or draft).get("included_study_count", 0) or 0) if (confirmed or draft) else 0,
        included_candidate_count=len(draft.get("included_effect_row_candidates", [])) if isinstance(draft.get("included_effect_row_candidates"), list) else 0,
        excluded_candidate_count=len(draft.get("excluded_effect_row_candidates", [])) if isinstance(draft.get("excluded_effect_row_candidates"), list) else 0,
        warnings=tuple(_dedupe([*warnings, *(str(item) for item in draft.get("warnings", []) if item)])) if draft else tuple(warnings),
        readiness_warnings_zh=tuple(
            dict((confirmed or draft).get("m7_warning_labels_zh", {})).values()
        )
        if isinstance((confirmed or draft).get("m7_warning_labels_zh", {}) if (confirmed or draft) else {}, dict)
        else (),
        primary_actions=("生成分析计划草稿", "查看候选效应量", "确认分析计划", "暂不运行统计"),
        safety_flags={
            "auto_confirms_analysis_plan": False,
            "creates_analysis_ready_dataset": False,
            "runs_statistics": False,
            "creates_final_analysis_result": False,
            "advances_prisma": False,
            "generates_medical_interpretation": False,
            "future_statistical_execution_requires_confirmed_plan": True,
        },
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
    )


def meta_statistics_engine_state_from_project(
    project_dir: Path,
    *,
    service: MetaStatisticsEngineService | None = None,
) -> MetaStatisticsEnginePageState:
    project_dir = project_dir.expanduser().resolve()
    stats_service = service or MetaStatisticsEngineService()
    manifest = _load_json(stats_service.manifest_path(project_dir))
    confirmed_plan_path = project_dir / "analysis" / "analysis_plan_confirmed_v1.json"
    latest_run_id = str(manifest.get("latest_analysis_run_id", ""))
    latest_result_id = str(manifest.get("latest_result_id", ""))
    result = stats_service.load_standardized_result(project_dir, latest_run_id) if latest_run_id else {}
    diagnostics = dict(result.get("diagnostics", {})) if isinstance(result.get("diagnostics"), dict) else {}
    warnings: list[str] = []
    if not confirmed_plan_path.exists():
        warnings.append("confirmed_analysis_plan_missing")
    warnings.extend(str(item) for item in diagnostics.get("warnings", []) if item)
    return MetaStatisticsEnginePageState(
        title="Meta Statistics Engine v2",
        status_label="Confirmed-plan only / Developer Preview",
        description="只允许从 confirmed_analysis_plan.v1 运行 testing-level 统计；不会生成 final conclusion。",
        project_dir=str(project_dir),
        run_schema_version=META_STATISTICS_ANALYSIS_RUN_SCHEMA_VERSION,
        result_schema_version=META_STATISTICS_STANDARDIZED_RESULT_SCHEMA_VERSION,
        manifest_schema_version=META_STATISTICS_ANALYSIS_MANIFEST_SCHEMA_VERSION,
        confirmed_plan_status="confirmed" if confirmed_plan_path.exists() else "missing",
        latest_run_id=latest_run_id,
        latest_result_id=latest_result_id,
        run_count=int(manifest.get("run_count", 0) or 0),
        run_path=str(stats_service.runs_dir(project_dir) / f"{latest_run_id}.json") if latest_run_id else "",
        result_path=str(stats_service.results_dir(project_dir) / f"{latest_run_id}_result.json") if latest_run_id else "",
        manifest_path=str(stats_service.manifest_path(project_dir)),
        input_validation_status=str(diagnostics.get("input_validation_status", "")),
        result_status=str(result.get("result_status", "testing_result_generated" if result else "not_started")),
        result_state=str(result.get("result_state", "testing_level" if result else STATISTICAL_RESULT_STATE_NOT_RUN)),
        result_state_label_zh=statistical_result_state_label_zh(str(result.get("result_state", "testing_level" if result else STATISTICAL_RESULT_STATE_NOT_RUN))),
        warnings=tuple(_dedupe(warnings)),
        primary_actions=("运行统计分析", "查看分析计划", "查看输入校验", "查看统计结果"),
        safety_flags={
            "requires_confirmed_analysis_plan": True,
            "modifies_extraction_records": False,
            "modifies_quality_assessment": False,
            "advances_prisma": False,
            "generates_medical_conclusion": False,
            "production_grade": False,
        },
        status_label_zh=f"{APP_VERSION} · {INTERNAL_BETA_STATUS_ZH}",
    )


def _analysis_alias_summary(path: Path, payload_key: str) -> dict[str, object]:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    payload = _load_json(path)
    inner = payload.get(payload_key, {}) if isinstance(payload, dict) else {}
    if not isinstance(inner, dict):
        inner = {}
    return {
        "status": "available",
        "id": str(inner.get("dataset_id") or inner.get("result_id") or ""),
        "outcome_name": str(inner.get("outcome_name", "")),
        "effect_measure": str(inner.get("effect_measure", "")),
        "model": str(inner.get("model", "")),
        "result_state": str(inner.get("result_state") or payload.get("result_state") or STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN),
        "result_state_label_zh": statistical_result_state_label_zh(str(inner.get("result_state") or payload.get("result_state") or STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN)),
        "blocks_formal_report_claim": blocks_formal_report_claim(inner) if payload_key == "result" else True,
        "warnings": inner.get("warnings", []),
        "errors": inner.get("validation_errors", []),
    }


def _effect_size_normalization_summary(project_dir: Path) -> dict[str, object]:
    try:
        effects = EffectSizeNormalizationService().normalize_extraction_rows(project_dir)
        summary = EffectSizeNormalizationService().summarize_normalization(effects).to_dict()
    except Exception:
        summary = {
            "total_rows": 0,
            "confirmed_rows": 0,
            "normalized_ready": 0,
            "incomplete": 0,
            "invalid": 0,
            "needs_user_review": 0,
            "unsupported_effect_type": 0,
            "warnings": [],
            "result_state": STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN,
        }
    return {
        "title_zh": "效应量标准化预检查",
        "ready_label_zh": "可用于后续统计的研究数",
        "needs_review_label_zh": "需要用户检查",
        "incomplete_label_zh": "字段不完整",
        "unsupported_label_zh": "不支持的效应量类型",
        "normalized_ready": int(summary.get("normalized_ready", 0) or 0),
        "needs_user_review": int(summary.get("needs_user_review", 0) or 0),
        "incomplete": int(summary.get("incomplete", 0) or 0),
        "unsupported_effect_type": int(summary.get("unsupported_effect_type", 0) or 0),
        "creates_computed_result": False,
        "result_state": STATISTICAL_RESULT_STATE_CONFIGURED_NOT_RUN,
    }


def _pairwise_executor_summary(project_dir: Path) -> dict[str, object]:
    result = PairwiseMetaExecutorService().load_latest_result(project_dir)
    if result is None:
        return {
            "title_zh": "统计执行状态",
            "state_label_zh": statistical_result_state_label_zh(STATISTICAL_RESULT_STATE_NOT_RUN),
            "result_state": STATISTICAL_RESULT_STATE_NOT_RUN,
            "model_label_zh": "模型",
            "model_used": "未运行",
            "included_label_zh": "纳入研究数",
            "included_count": 0,
            "pooled_label_zh": "合并效应量",
            "pooled_effect": "缺失",
            "ci_label_zh": "95% CI",
            "confidence_interval": "缺失",
            "i2_label_zh": "异质性 I²",
            "i_squared": "缺失",
            "testing_notice_zh": "测试阶段提示：尚未运行 M12 pairwise executor。",
            "review_notice_zh": "需要用户审核后才能进入报告。",
            "blocks_formal_report_claim": True,
        }
    payload = result.to_dict()
    ci = "缺失"
    if payload.get("pooled_ci_lower") is not None and payload.get("pooled_ci_upper") is not None:
        ci = f"{_format_optional_float(payload.get('pooled_ci_lower'))} - {_format_optional_float(payload.get('pooled_ci_upper'))}"
    heterogeneity = payload.get("heterogeneity_summary", {})
    i2 = heterogeneity.get("i_squared") if isinstance(heterogeneity, dict) else None
    return {
        "title_zh": "统计执行状态",
        "state_label_zh": statistical_result_state_label_zh(str(payload.get("result_state", STATISTICAL_RESULT_STATE_NOT_RUN))),
        "result_state": str(payload.get("result_state", STATISTICAL_RESULT_STATE_NOT_RUN)),
        "model_label_zh": "模型",
        "model_used": str(payload.get("model_used", "")) or "未运行",
        "included_label_zh": "纳入研究数",
        "included_count": len(payload.get("included_studies", [])) if isinstance(payload.get("included_studies"), list) else 0,
        "pooled_label_zh": "合并效应量",
        "pooled_effect": _format_optional_float(payload.get("pooled_effect")),
        "ci_label_zh": "95% CI",
        "confidence_interval": ci,
        "i2_label_zh": "异质性 I²",
        "i_squared": _format_optional_float(i2),
        "testing_notice_zh": "测试阶段提示：M12 为 Developer Preview / testing MVP，不生成正式医学结论。",
        "review_notice_zh": "需要用户审核后才能进入报告。",
        "blocks_formal_report_claim": blocks_formal_report_claim(payload),
    }


def _format_optional_float(value: object) -> str:
    if value is None:
        return "缺失"
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return "缺失"


def _available_subgroup_options(available_outcomes: tuple[dict[str, object], ...]) -> tuple[str, ...]:
    if not available_outcomes:
        return ("subgroup", "country", "study_design")
    return ("subgroup", "country", "study_design", "none")


def _load_json(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


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
            figure_service: FigureResultService | None = None,
        ) -> None:
            super().__init__()
            self._project_id = project_id
            self._service = service or AnalysisPreflightService()
            self._dataset_service = dataset_service or AnalysisDatasetService()
            self._run_service = run_service or AnalysisRunService(dataset_service=self._dataset_service)
            self._figure_service = figure_service or FigureResultService(analysis_run_service=self._run_service)
            self._analysis_plan_service = AnalysisPlanService()
            self._statistics_engine_service = MetaStatisticsEngineService()
            self._pairwise_executor_service = PairwiseMetaExecutorService()
            self._state = initial_analysis_state()

            root = QVBoxLayout(self)
            title = QLabel(f"{self._state.title_zh} · {self._state.status_label_zh}")
            title.setStyleSheet(meta_title_style())
            root.addWidget(title)
            description = QLabel(self._state.description_zh)
            description.setWordWrap(True)
            root.addWidget(description)
            root.addWidget(QLabel(f"功能状态：{self._state.status_label_zh} / {self._state.status_label}"))

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

            plan_title = QLabel("Analysis Plan Builder v1（草稿优先）")
            plan_title.setStyleSheet("font-size: 16px; font-weight: 700;")
            root.addWidget(plan_title)
            plan_hint = QLabel("从 confirmed protocol、extraction effect rows 和 quality summary 生成分析计划；确认计划也不会运行统计。")
            plan_hint.setWordWrap(True)
            root.addWidget(plan_hint)
            plan_buttons = QHBoxLayout()
            draft_plan_button = QPushButton("生成分析计划草稿")
            draft_plan_button.clicked.connect(self._build_analysis_plan_draft)
            confirm_plan_button = QPushButton("确认分析计划")
            confirm_plan_button.clicked.connect(self._confirm_analysis_plan)
            hold_button = QPushButton("暂不运行统计")
            hold_button.setEnabled(False)
            plan_buttons.addWidget(draft_plan_button)
            plan_buttons.addWidget(confirm_plan_button)
            plan_buttons.addWidget(hold_button)
            root.addLayout(plan_buttons)
            self._analysis_plan_label = QLabel("分析计划草稿和候选效应量会显示在这里。")
            self._analysis_plan_label.setWordWrap(True)
            root.addWidget(self._analysis_plan_label)

            stats_title = QLabel("Meta Statistics Engine v2（需已确认分析计划）")
            stats_title.setStyleSheet("font-size: 16px; font-weight: 700;")
            root.addWidget(stats_title)
            stats_hint = QLabel("运行统计分析只读取 confirmed_analysis_plan.v1；输出 testing-level standardized result，不推进 PRISMA，不生成医学结论。")
            stats_hint.setWordWrap(True)
            root.addWidget(stats_hint)
            stats_buttons = QHBoxLayout()
            run_stats_button = QPushButton("运行统计分析")
            run_stats_button.clicked.connect(self._run_statistics_v2)
            view_plan_button = QPushButton("查看分析计划")
            view_plan_button.clicked.connect(self._view_confirmed_analysis_plan)
            view_validation_button = QPushButton("查看输入校验")
            view_validation_button.clicked.connect(self._view_statistics_validation)
            view_result_button = QPushButton("查看统计结果")
            view_result_button.clicked.connect(self._view_statistics_result)
            view_pairwise_button = QPushButton("查看 M12 执行状态")
            view_pairwise_button.clicked.connect(self._view_pairwise_executor_result)
            stats_buttons.addWidget(run_stats_button)
            stats_buttons.addWidget(view_plan_button)
            stats_buttons.addWidget(view_validation_button)
            stats_buttons.addWidget(view_result_button)
            stats_buttons.addWidget(view_pairwise_button)
            root.addLayout(stats_buttons)
            self._statistics_engine_label = QLabel("请先确认分析计划。")
            self._statistics_engine_label.setWordWrap(True)
            root.addWidget(self._statistics_engine_label)

            normalization_title = QLabel("效应量标准化预检查")
            normalization_title.setStyleSheet("font-size: 16px; font-weight: 700;")
            root.addWidget(normalization_title)
            self._normalization_summary_label = QLabel("可用于后续统计的研究数、需要用户检查、字段不完整和不支持的效应量类型会显示在这里。")
            self._normalization_summary_label.setWordWrap(True)
            root.addWidget(self._normalization_summary_label)
            self._pairwise_executor_label = QLabel("统计执行状态、模型、纳入研究数、合并效应量、95% CI、异质性 I² 和测试阶段提示会显示在这里。")
            self._pairwise_executor_label.setWordWrap(True)
            root.addWidget(self._pairwise_executor_label)

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

            figure_title = QLabel("Figures / Result Table（测试中）")
            figure_title.setStyleSheet("font-size: 16px; font-weight: 700;")
            root.addWidget(figure_title)

            self._analysis_result_id_input = QLineEdit()
            self._analysis_result_id_input.setPlaceholderText("analysis_result ID")
            root.addWidget(self._analysis_result_id_input)

            forest_button = QPushButton("生成 forest plot PNG")
            forest_button.clicked.connect(self._generate_forest_plot)
            root.addWidget(forest_button)

            table_button = QPushButton("导出 result table CSV")
            table_button.clicked.connect(self._export_result_table)
            root.addWidget(table_button)

            self._artifact_label = QLabel("figure artifact 和 result table 路径会显示在这里。")
            self._artifact_label.setWordWrap(True)
            root.addWidget(self._artifact_label)

            self._status_label = QLabel("分析状态：等待 Extraction 输出")
            self._status_label.setWordWrap(True)
            root.addWidget(self._status_label)
            summary_card = QFrame()
            summary_card.setStyleSheet(meta_card_stylesheet())
            summary_layout = QVBoxLayout(summary_card)
            self._summary_label = QLabel("Analysis 预检摘要会显示在这里。")
            self._summary_label.setWordWrap(True)
            summary_layout.addWidget(self._summary_label)
            root.addWidget(summary_card)
            self._error_label = QLabel("")
            self._error_label.setWordWrap(True)
            self._error_label.setStyleSheet(meta_error_text_style())
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

        def _build_analysis_plan_draft(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            try:
                result = self._analysis_plan_service.generate_draft(project_dir, actor="reviewer")
                self._analysis_plan_label.setText(
                    f"Draft ID：{result.plan_id}\n"
                    f"Meta type：{result.payload.get('meta_type', '')}\n"
                    f"Effect measure：{result.payload.get('effect_measure', '')}\n"
                    f"Model default：{result.payload.get('model_default', '')}\n"
                    f"Included candidates：{len(result.payload.get('included_effect_row_candidates', []))}\n"
                    f"Excluded candidates：{len(result.payload.get('excluded_effect_row_candidates', []))}\n"
                    f"Warnings：{', '.join(result.warnings) or '无'}\n"
                    f"输出：{result.output_path}\n"
                    "暂不运行统计。"
                )
                self._error_label.setText("")
            except Exception as exc:
                self._analysis_plan_label.setText("没有生成分析计划草稿。")
                self._error_label.setText(f"分析计划草稿生成失败：{exc}")

        def _confirm_analysis_plan(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            try:
                result = self._analysis_plan_service.confirm_plan(project_dir, actor="reviewer")
                self._analysis_plan_label.setText(
                    f"Confirmed plan ID：{result.plan_id}\n"
                    f"Effect measure：{result.payload.get('confirmed_effect_measure', '')}\n"
                    f"Model：{result.payload.get('confirmed_model', '')}\n"
                    f"Primary rows：{len(result.payload.get('confirmed_primary_effect_rows', []))}\n"
                    f"Secondary rows：{len(result.payload.get('confirmed_secondary_effect_rows', []))}\n"
                    f"输出：{result.output_path}\n"
                    "确认完成；仍未运行统计。"
                )
                self._error_label.setText("")
            except Exception as exc:
                self._analysis_plan_label.setText("没有确认分析计划。")
                self._error_label.setText(f"分析计划确认失败：{exc}")

        def _run_statistics_v2(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            try:
                result = self._statistics_engine_service.run_statistics(project_dir, actor="reviewer")
                output = result.standardized_result
                self._statistics_engine_label.setText(
                    f"Run ID：{result.analysis_run_id}\n"
                    f"Result ID：{result.result_id}\n"
                    f"结果状态：{statistical_result_state_label_zh(str(output.get('result_state', 'testing_level')))}\n"
                    f"Effect measure：{output.get('effect_measure', '')}\n"
                    f"Model：{output.get('model', '')}\n"
                    f"Pooled effect：{output.get('pooled_effect', '')}\n"
                    f"95% CI：{output.get('ci_low', '')} - {output.get('ci_high', '')}\n"
                    f"I²：{output.get('i_squared', '')}\n"
                    "testing-level；未生成医学结论。"
                )
                self._refresh_normalization_summary(project_dir)
                self._error_label.setText("")
            except Exception as exc:
                self._statistics_engine_label.setText("请先确认分析计划。")
                self._error_label.setText(f"统计分析未运行：{exc}")

        def _view_confirmed_analysis_plan(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            path = project_dir / "analysis" / "analysis_plan_confirmed_v1.json"
            payload = _load_json(path)
            self._statistics_engine_label.setText(
                f"分析计划状态：{'已确认' if payload else '缺失'}\n"
                f"Effect measure：{payload.get('confirmed_effect_measure', '')}\n"
                f"Model：{payload.get('confirmed_model', '')}\n"
                f"Locked：{payload.get('locked_for_analysis_run', False)}"
            )

        def _view_statistics_validation(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            state = meta_statistics_engine_state_from_project(project_dir, service=self._statistics_engine_service)
            self._statistics_engine_label.setText(
                f"Input validation：{state.input_validation_status or 'not_started'}\n"
                f"Warnings：{', '.join(state.warnings) or '无'}\n"
                f"结果状态：{state.result_state_label_zh}"
            )

        def _view_statistics_result(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            state = meta_statistics_engine_state_from_project(project_dir, service=self._statistics_engine_service)
            result = self._statistics_engine_service.load_standardized_result(project_dir, state.latest_run_id) if state.latest_run_id else {}
            self._statistics_engine_label.setText(
                f"Status：{state.result_status}\n"
                f"结果状态：{state.result_state_label_zh}\n"
                f"Pooled effect：{result.get('pooled_effect', '')}\n"
                f"Testing：{result.get('testing_level_notice', '')}"
            )
            self._refresh_normalization_summary(project_dir)
            self._refresh_pairwise_executor_summary(project_dir)

        def _view_pairwise_executor_result(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            self._refresh_pairwise_executor_summary(project_dir)

        def _refresh_normalization_summary(self, project_dir: Path) -> None:
            summary = _effect_size_normalization_summary(project_dir)
            self._normalization_summary_label.setText(
                f"{summary['title_zh']}\n"
                f"{summary['ready_label_zh']}：{summary['normalized_ready']}\n"
                f"{summary['needs_review_label_zh']}：{summary['needs_user_review']}\n"
                f"{summary['incomplete_label_zh']}：{summary['incomplete']}\n"
                f"{summary['unsupported_label_zh']}：{summary['unsupported_effect_type']}\n"
                "标准化输入仅用于后续执行器预检查，不生成 computed 或 report_ready 结果。"
            )

        def _refresh_pairwise_executor_summary(self, project_dir: Path) -> None:
            summary = _pairwise_executor_summary(project_dir)
            self._pairwise_executor_label.setText(
                f"{summary['title_zh']}：{summary['state_label_zh']}\n"
                f"{summary['model_label_zh']}：{summary['model_used']}\n"
                f"{summary['included_label_zh']}：{summary['included_count']}\n"
                f"{summary['pooled_label_zh']}：{summary['pooled_effect']}\n"
                f"{summary['ci_label_zh']}：{summary['confidence_interval']}\n"
                f"{summary['i2_label_zh']}：{summary['i_squared']}\n"
                f"{summary['testing_notice_zh']}\n"
                f"{summary['review_notice_zh']}"
            )

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
                self._analysis_result_id_input.setText(result.result_id)
                self._analysis_result_label.setText(
                    f"Result ID：{result.result_id}\n"
                    f"Dataset ID：{result.dataset_id}\n"
                    f"结果状态：{statistical_result_state_label_zh(result.result_state)}\n"
                    f"Model：{result.model}\n"
                    f"Pooled effect：{result.pooled_effect:.6g}\n"
                    f"95% CI：{result.ci_lower:.6g} - {result.ci_upper:.6g}\n"
                    f"P value：{result.p_value:.6g}\n"
                    f"Q：{result.q_statistic:.6g}\n"
                    f"I²：{result.i_squared:.6g}\n"
                    f"tau²：{result.tau_squared:.6g}\n"
                    f"Warnings：{', '.join(result.warnings) or '无'}\n"
                    "测试级结果，不可作为正式统计结论。"
                )
                self._error_label.setText("")
            except Exception as exc:
                self._analysis_result_label.setText("没有生成 pooled result。")
                self._error_label.setText(f"Meta 分析运行失败：{exc}")

        def _generate_forest_plot(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            try:
                artifact = self._figure_service.generate_forest_plot(project_dir, self._analysis_result_id_input.text().strip())
                self._artifact_label.setText(f"Forest plot：已生成 testing-level artifact；类型 {artifact.figure_type}")
                self._error_label.setText("")
            except Exception as exc:
                self._artifact_label.setText("没有生成 forest plot。")
                self._error_label.setText(f"Forest plot 生成失败：{exc}")

        def _export_result_table(self) -> None:
            project_dir = Path(self._project_dir_input.text()).expanduser()
            try:
                output_path = self._figure_service.export_result_table_csv(project_dir, self._analysis_result_id_input.text().strip())
                self._artifact_label.setText("Result table：已导出 testing-level 结果表，不代表正式统计结论。")
                self._error_label.setText("")
            except Exception as exc:
                self._artifact_label.setText("没有导出 result table。")
                self._error_label.setText(f"Result table 导出失败：{exc}")

else:

    class AnalysisPage:  # type: ignore[no-redef]
        pass
