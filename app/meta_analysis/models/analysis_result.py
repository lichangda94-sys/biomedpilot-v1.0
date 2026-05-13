from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.meta_analysis.models.statistical_result_state import (
    STATISTICAL_RESULT_STATE_TESTING_LEVEL,
    testing_level_result_metadata,
    validate_statistical_result_state,
)


@dataclass(frozen=True)
class StudyMetaAnalysisResult:
    study_id: str
    record_id: str
    first_author: str
    year: int | None
    effect: float
    ci_lower: float
    ci_upper: float
    standard_error: float
    variance: float
    weight: float
    transformed_effect: float
    adjusted: bool = False
    covariates: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisResult:
    result_id: str
    dataset_id: str
    project_id: str
    profile_type: str
    outcome_name: str
    effect_measure: str
    model: str
    pooled_effect: float
    ci_lower: float
    ci_upper: float
    p_value: float
    q_statistic: float
    i_squared: float
    tau_squared: float
    study_results: list[StudyMetaAnalysisResult]
    warnings: list[str]
    created_at: str
    result_state: str = STATISTICAL_RESULT_STATE_TESTING_LEVEL
    testing_level: bool = True
    production_grade: bool = False
    formal_computed: bool = False
    user_reviewed: bool = False
    report_ready: bool = False
    medical_conclusion_status: str = "not_generated"
    testing_level_notice: str = "Developer Preview / testing-level statistical output; not a formal computed result."
    result_state_warnings: list[str] = field(default_factory=lambda: ["testing_level_result_blocks_formal_report_claim"])
    validation_errors: list[str] = field(default_factory=list)


def new_analysis_result_id() -> str:
    return f"ares-{uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def analysis_result_to_dict(result: AnalysisResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["study_results"] = [asdict(item) for item in result.study_results]
    return payload


def analysis_result_from_dict(payload: dict[str, Any]) -> AnalysisResult:
    metadata = testing_level_result_metadata()
    state = validate_statistical_result_state(str(payload.get("result_state") or metadata["result_state"]))
    return AnalysisResult(
        result_id=str(payload["result_id"]),
        dataset_id=str(payload["dataset_id"]),
        project_id=str(payload["project_id"]),
        profile_type=str(payload["profile_type"]),
        outcome_name=str(payload["outcome_name"]),
        effect_measure=str(payload["effect_measure"]),
        model=str(payload["model"]),
        pooled_effect=float(payload["pooled_effect"]),
        ci_lower=float(payload["ci_lower"]),
        ci_upper=float(payload["ci_upper"]),
        p_value=float(payload["p_value"]),
        q_statistic=float(payload["q_statistic"]),
        i_squared=float(payload["i_squared"]),
        tau_squared=float(payload["tau_squared"]),
        study_results=[StudyMetaAnalysisResult(**dict(item)) for item in payload.get("study_results", [])],
        warnings=[str(item) for item in payload.get("warnings", [])],
        created_at=str(payload.get("created_at", "")),
        result_state=state,
        testing_level=bool(payload.get("testing_level", metadata["testing_level"])),
        production_grade=bool(payload.get("production_grade", metadata["production_grade"])),
        formal_computed=bool(payload.get("formal_computed", metadata["formal_computed"])),
        user_reviewed=bool(payload.get("user_reviewed", metadata["user_reviewed"])),
        report_ready=bool(payload.get("report_ready", metadata["report_ready"])),
        medical_conclusion_status=str(payload.get("medical_conclusion_status", metadata["medical_conclusion_status"])),
        testing_level_notice=str(payload.get("testing_level_notice", metadata["testing_level_notice"])),
        result_state_warnings=[str(item) for item in payload.get("result_state_warnings", metadata["result_state_warnings"])],
        validation_errors=[str(item) for item in payload.get("validation_errors", [])],
    )
