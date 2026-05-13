from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class SubgroupAnalysisResult:
    subgroup_result_id: str
    analysis_result_id: str
    dataset_id: str
    project_id: str
    subgroup_variable: str
    subgroup_results: list[dict[str, Any]]
    between_group_heterogeneity: dict[str, Any]
    warnings: list[str]
    created_at: str


@dataclass(frozen=True)
class LeaveOneOutResult:
    sensitivity_result_id: str
    analysis_result_id: str
    project_id: str
    omitted_study_results: list[dict[str, Any]]
    influential_studies: list[str]
    warnings: list[str]
    created_at: str


@dataclass(frozen=True)
class PublicationBiasResult:
    bias_result_id: str
    analysis_result_id: str
    project_id: str
    egger_test: dict[str, Any]
    begg_test: dict[str, Any]
    funnel_plot_artifact_id: str
    warnings: list[str]
    created_at: str


def new_subgroup_result_id() -> str:
    return f"subgrp-{uuid4().hex[:12]}"


def new_sensitivity_result_id() -> str:
    return f"loo-{uuid4().hex[:12]}"


def new_bias_result_id() -> str:
    return f"bias-{uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def subgroup_result_to_dict(result: SubgroupAnalysisResult) -> dict[str, Any]:
    return asdict(result)


def subgroup_result_from_dict(payload: dict[str, Any]) -> SubgroupAnalysisResult:
    return SubgroupAnalysisResult(
        subgroup_result_id=str(payload["subgroup_result_id"]),
        analysis_result_id=str(payload["analysis_result_id"]),
        dataset_id=str(payload["dataset_id"]),
        project_id=str(payload["project_id"]),
        subgroup_variable=str(payload["subgroup_variable"]),
        subgroup_results=[dict(item) for item in payload.get("subgroup_results", [])],
        between_group_heterogeneity=dict(payload.get("between_group_heterogeneity", {})),
        warnings=[str(item) for item in payload.get("warnings", [])],
        created_at=str(payload.get("created_at", "")),
    )


def leave_one_out_result_to_dict(result: LeaveOneOutResult) -> dict[str, Any]:
    return asdict(result)


def leave_one_out_result_from_dict(payload: dict[str, Any]) -> LeaveOneOutResult:
    return LeaveOneOutResult(
        sensitivity_result_id=str(payload["sensitivity_result_id"]),
        analysis_result_id=str(payload["analysis_result_id"]),
        project_id=str(payload["project_id"]),
        omitted_study_results=[dict(item) for item in payload.get("omitted_study_results", [])],
        influential_studies=[str(item) for item in payload.get("influential_studies", [])],
        warnings=[str(item) for item in payload.get("warnings", [])],
        created_at=str(payload.get("created_at", "")),
    )


def publication_bias_result_to_dict(result: PublicationBiasResult) -> dict[str, Any]:
    return asdict(result)


def publication_bias_result_from_dict(payload: dict[str, Any]) -> PublicationBiasResult:
    return PublicationBiasResult(
        bias_result_id=str(payload["bias_result_id"]),
        analysis_result_id=str(payload["analysis_result_id"]),
        project_id=str(payload["project_id"]),
        egger_test=dict(payload.get("egger_test", {})),
        begg_test=dict(payload.get("begg_test", {})),
        funnel_plot_artifact_id=str(payload.get("funnel_plot_artifact_id", "")),
        warnings=[str(item) for item in payload.get("warnings", [])],
        created_at=str(payload.get("created_at", "")),
    )
