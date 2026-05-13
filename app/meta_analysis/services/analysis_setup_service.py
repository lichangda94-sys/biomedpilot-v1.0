from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.models.analysis_dataset import (
    AnalysisReadyDataset,
    analysis_ready_dataset_to_dict,
    now_utc,
)
from app.meta_analysis.models.analysis_result import AnalysisResult, analysis_result_to_dict
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
from app.meta_analysis.services.statistical_applicability_service import StatisticalApplicabilityService
from app.shared.data_center.service import DataCenter


BLOCKED_ADVANCED_METHODS = {
    "network_meta": "network_meta_analysis_not_implemented",
    "network_meta_analysis": "network_meta_analysis_not_implemented",
    "hsroc": "diagnostic_hsroc_not_implemented",
    "diagnostic_hsroc": "diagnostic_hsroc_not_implemented",
    "meta_regression": "meta_regression_not_implemented",
    "meta-regression": "meta_regression_not_implemented",
}


@dataclass(frozen=True)
class AnalysisPlan:
    plan_id: str
    project_id: str
    profile_type: str
    outcome_name: str
    effect_measure: str
    model: str = "random"
    zero_event_correction: str = "continuity_0.5"
    subgroup_variable: str = ""
    requested_method: str = "meta_analysis"
    developer_preview: bool = True
    created_at: str = ""
    updated_at: str = ""
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisSetupRunSummary:
    success: bool
    message: str
    plan: AnalysisPlan
    dataset: AnalysisReadyDataset | None = None
    result: AnalysisResult | None = None
    output_paths: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class AnalysisSetupService:
    def __init__(
        self,
        *,
        dataset_service: AnalysisDatasetService | None = None,
        run_service: AnalysisRunService | None = None,
        applicability_service: StatisticalApplicabilityService | None = None,
        audit_log: MetaAuditLogService | None = None,
        data_center: DataCenter | None = None,
        project_contract: MetaProjectContractService | None = None,
    ) -> None:
        self._dataset_service = dataset_service or AnalysisDatasetService(data_center=data_center)
        self._run_service = run_service or AnalysisRunService(dataset_service=self._dataset_service, data_center=data_center, audit_log=audit_log)
        self._applicability_service = applicability_service or StatisticalApplicabilityService()
        self._audit_log = audit_log or MetaAuditLogService()
        self._data_center = data_center
        self._project_contract = project_contract or MetaProjectContractService(data_center=data_center)

    def create_plan(
        self,
        project_dir: Path,
        *,
        profile_type: str,
        outcome_name: str,
        effect_measure: str,
        model: str = "random",
        zero_event_correction: str = "continuity_0.5",
        subgroup_variable: str = "",
        requested_method: str = "meta_analysis",
    ) -> AnalysisPlan:
        project_dir = project_dir.expanduser().resolve()
        warnings: list[str] = ["developer_preview_analysis_plan"]
        errors: list[str] = []
        if not profile_type:
            errors.append("profile_type_missing")
        if not outcome_name:
            errors.append("outcome_name_missing")
        if not effect_measure:
            errors.append("effect_measure_missing")
        normalized_method = requested_method.strip().lower()
        if normalized_method in BLOCKED_ADVANCED_METHODS:
            errors.append(BLOCKED_ADVANCED_METHODS[normalized_method])
        if model.strip().lower() not in {"fixed", "random"}:
            errors.append("analysis_model_must_be_fixed_or_random")
        now = now_utc()
        return AnalysisPlan(
            plan_id=f"aplan-{uuid4().hex[:12]}",
            project_id=project_dir.name,
            profile_type=profile_type,
            outcome_name=outcome_name,
            effect_measure=effect_measure,
            model=model.strip().lower() or "random",
            zero_event_correction=zero_event_correction,
            subgroup_variable=subgroup_variable,
            requested_method=requested_method,
            created_at=now,
            updated_at=now,
            warnings=_dedupe(warnings),
            errors=_dedupe(errors),
        )

    def save_analysis_plan(self, project_dir: Path, plan: AnalysisPlan) -> Path:
        project_dir = project_dir.expanduser().resolve()
        output_path = self._plan_path(project_dir)
        payload = {
            "project_id": plan.project_id,
            "data_type": "analysis_plan",
            "software_status": "testing",
            "plan": asdict(plan),
        }
        _write_json(output_path, payload)
        self._register_asset(
            project_id=plan.project_id,
            data_type="analysis_plan",
            source_path=str(project_dir / "extraction" / "extraction_records.json"),
            output_path=str(output_path),
            status="needs_attention" if plan.errors else "available",
        )
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=plan.project_id,
            target_type="analysis_plan",
            target_id=plan.plan_id,
            source_path=str(project_dir / "extraction" / "extraction_records.json"),
            output_path=str(output_path),
            summary="Analysis setup plan saved.",
            details={"requested_method": plan.requested_method, "model": plan.model, "errors": plan.errors},
        )
        self._project_contract.write_project_manifests(project_dir)
        return output_path

    def load_analysis_plan(self, project_dir: Path) -> AnalysisPlan | None:
        path = self._plan_path(project_dir.expanduser().resolve())
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        plan_payload = payload.get("plan", payload)
        if not isinstance(plan_payload, dict):
            return None
        return AnalysisPlan(
            plan_id=str(plan_payload.get("plan_id", "")),
            project_id=str(plan_payload.get("project_id", "")),
            profile_type=str(plan_payload.get("profile_type", "")),
            outcome_name=str(plan_payload.get("outcome_name", "")),
            effect_measure=str(plan_payload.get("effect_measure", "")),
            model=str(plan_payload.get("model", "random")),
            zero_event_correction=str(plan_payload.get("zero_event_correction", "continuity_0.5")),
            subgroup_variable=str(plan_payload.get("subgroup_variable", "")),
            requested_method=str(plan_payload.get("requested_method", "meta_analysis")),
            developer_preview=bool(plan_payload.get("developer_preview", True)),
            created_at=str(plan_payload.get("created_at", "")),
            updated_at=str(plan_payload.get("updated_at", "")),
            warnings=[str(item) for item in plan_payload.get("warnings", [])],
            errors=[str(item) for item in plan_payload.get("errors", [])],
        )

    def run_preflight(self, project_dir: Path, plan: AnalysisPlan) -> AnalysisSetupRunSummary:
        project_dir = project_dir.expanduser().resolve()
        if plan.errors:
            self.save_analysis_plan(project_dir, plan)
            warnings_path = self._write_applicability_warnings(project_dir, plan=plan, errors=plan.errors, warnings=plan.warnings)
            return AnalysisSetupRunSummary(
                success=False,
                message="Analysis setup is blocked by plan errors.",
                plan=plan,
                output_paths={"analysis_plan": str(self._plan_path(project_dir)), "applicability_warnings": str(warnings_path)},
                warnings=plan.warnings,
                errors=plan.errors,
            )
        self.save_analysis_plan(project_dir, plan)
        dataset = self._dataset_service.build_analysis_ready_dataset(project_dir, plan.profile_type, plan.outcome_name, plan.effect_measure)
        dataset_path = self._dataset_service.save_analysis_ready_dataset(project_dir, dataset)
        dataset_alias_path = self._write_dataset_alias(project_dir, dataset)
        applicability = self._applicability_service.evaluate_dataset_for_meta_analysis(dataset, plan.model)
        warnings_path = self._write_applicability_warnings(
            project_dir,
            plan=plan,
            dataset=dataset,
            warnings=[*plan.warnings, *applicability.warnings],
            errors=[*plan.errors, *applicability.errors],
        )
        self._project_contract.write_project_manifests(project_dir)
        return AnalysisSetupRunSummary(
            success=not applicability.errors,
            message="Analysis-ready dataset preflight completed." if not applicability.errors else "Analysis preflight found blocking applicability errors.",
            plan=plan,
            dataset=dataset,
            output_paths={
                "analysis_plan": str(self._plan_path(project_dir)),
                "analysis_ready_datasets": str(dataset_path),
                "analysis_ready_dataset": str(dataset_alias_path),
                "applicability_warnings": str(warnings_path),
            },
            warnings=_dedupe([*plan.warnings, *applicability.warnings]),
            errors=_dedupe([*plan.errors, *applicability.errors]),
        )

    def run_analysis_from_plan(self, project_dir: Path, plan: AnalysisPlan) -> AnalysisSetupRunSummary:
        project_dir = project_dir.expanduser().resolve()
        preflight = self.run_preflight(project_dir, plan)
        if not preflight.success or preflight.dataset is None:
            return preflight
        result = self._run_service.run_meta_analysis(project_dir, preflight.dataset.dataset_id, plan.model)
        result_path = self._run_service.save_analysis_result(project_dir, result)
        result_alias_path = self._write_result_alias(project_dir, result)
        applicability = self._applicability_service.evaluate_analysis_result(result)
        warnings_path = self._write_applicability_warnings(
            project_dir,
            plan=plan,
            dataset=preflight.dataset,
            result=result,
            warnings=[*preflight.warnings, *applicability.warnings, *result.warnings],
            errors=[*preflight.errors, *applicability.errors],
        )
        self._project_contract.write_project_manifests(project_dir)
        return AnalysisSetupRunSummary(
            success=True,
            message="Testing meta-analysis run completed.",
            plan=plan,
            dataset=preflight.dataset,
            result=result,
            output_paths={
                **preflight.output_paths,
                "analysis_results": str(result_path),
                "analysis_result": str(result_alias_path),
                "applicability_warnings": str(warnings_path),
            },
            warnings=_dedupe([*preflight.warnings, *applicability.warnings, *result.warnings]),
            errors=_dedupe([*preflight.errors, *applicability.errors]),
        )

    def list_available_outcomes(self, project_dir: Path) -> list[dict[str, object]]:
        return self._dataset_service.list_available_outcomes(project_dir)

    def _write_dataset_alias(self, project_dir: Path, dataset: AnalysisReadyDataset) -> Path:
        output_path = project_dir / "analysis" / "analysis_ready_dataset.json"
        _write_json(
            output_path,
            {
                "project_id": dataset.project_id,
                "data_type": "analysis_ready_dataset",
                "schema_version": "analysis_ready_dataset_alias.v1",
                "dataset": analysis_ready_dataset_to_dict(dataset),
            },
        )
        self._register_asset(
            project_id=dataset.project_id,
            data_type="analysis_ready_dataset_alias",
            source_path=str(project_dir / "analysis" / "analysis_ready_datasets.json"),
            output_path=str(output_path),
            status="available" if not dataset.validation_errors else "needs_attention",
        )
        return output_path

    def _write_result_alias(self, project_dir: Path, result: AnalysisResult) -> Path:
        output_path = project_dir / "analysis" / "analysis_result.json"
        _write_json(
            output_path,
            {
                "project_id": result.project_id,
                "data_type": "analysis_result",
                "schema_version": "analysis_result_alias.v1",
                "result": analysis_result_to_dict(result),
            },
        )
        self._register_asset(
            project_id=result.project_id,
            data_type="analysis_result_alias",
            source_path=str(project_dir / "analysis" / "analysis_results.json"),
            output_path=str(output_path),
            status="available",
        )
        return output_path

    def _write_applicability_warnings(
        self,
        project_dir: Path,
        *,
        plan: AnalysisPlan,
        dataset: AnalysisReadyDataset | None = None,
        result: AnalysisResult | None = None,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> Path:
        output_path = project_dir / "analysis" / "applicability_warnings.json"
        _write_json(
            output_path,
            {
                "project_id": plan.project_id,
                "data_type": "applicability_warnings",
                "schema_version": "analysis_applicability_warnings.v1",
                "plan_id": plan.plan_id,
                "dataset_id": dataset.dataset_id if dataset is not None else "",
                "result_id": result.result_id if result is not None else "",
                "warnings": _dedupe(list(warnings or [])),
                "errors": _dedupe(list(errors or [])),
                "blocked_methods": BLOCKED_ADVANCED_METHODS,
                "developer_preview": True,
            },
        )
        self._register_asset(
            project_id=plan.project_id,
            data_type="applicability_warnings",
            source_path=str(project_dir / "analysis" / "analysis_plan.json"),
            output_path=str(output_path),
            status="needs_attention" if errors else "available",
        )
        return output_path

    def _register_asset(self, *, project_id: str, data_type: str, source_path: str, output_path: str, status: str = "available") -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type=data_type,
            source_path=source_path,
            output_path=output_path,
            status=status,
        )

    def _plan_path(self, project_dir: Path) -> Path:
        return project_dir / "analysis" / "analysis_plan.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
