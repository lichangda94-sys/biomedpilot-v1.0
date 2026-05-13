from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


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


def new_analysis_result_id() -> str:
    return f"ares-{uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def analysis_result_to_dict(result: AnalysisResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["study_results"] = [asdict(item) for item in result.study_results]
    return payload


def analysis_result_from_dict(payload: dict[str, Any]) -> AnalysisResult:
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
    )
