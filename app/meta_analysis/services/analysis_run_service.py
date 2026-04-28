from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.models.analysis_result import (
    AnalysisResult,
    StudyMetaAnalysisResult,
    analysis_result_from_dict,
    analysis_result_to_dict,
    new_analysis_result_id,
    now_utc,
)
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.stats.meta_effects import study_effect_from_row
from app.meta_analysis.stats.meta_models import pool_effects
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


class AnalysisRunService:
    def __init__(
        self,
        *,
        dataset_service: AnalysisDatasetService | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
    ) -> None:
        self._dataset_service = dataset_service or AnalysisDatasetService()
        self._task_center = task_center
        self._data_center = data_center

    def run_meta_analysis(self, project_dir: Path, dataset_id: str, model: str) -> AnalysisResult:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_task(project_id=project_dir.name, summary=f"Running {model} meta-analysis for {dataset_id}")
        try:
            dataset = self._dataset_service.load_analysis_ready_dataset(project_dir, dataset_id)
            if dataset is None:
                raise ValueError("analysis_ready_dataset_not_found")
            if dataset.validation_errors:
                raise ValueError("analysis_ready_dataset_has_validation_errors")
            rows = [row for row in dataset.study_rows if row.analysis_status == "included"]
            if not rows:
                raise ValueError("analysis_ready_dataset_has_no_included_studies")
            effects = [study_effect_from_row(row) for row in rows]
            pooled = pool_effects(effects, effect_measure=dataset.effect_measure, model=model)
            warnings = list(dataset.validation_warnings)
            if len(effects) < 2:
                warnings.append("insufficient_studies_warning")
            study_results = [
                StudyMetaAnalysisResult(
                    study_id=effect.study_id,
                    record_id=effect.record_id,
                    first_author=effect.first_author,
                    year=effect.year,
                    effect=effect.effect,
                    ci_lower=effect.ci_lower,
                    ci_upper=effect.ci_upper,
                    standard_error=effect.standard_error,
                    variance=effect.variance,
                    weight=pooled.weights[index],
                    transformed_effect=effect.transformed_effect,
                    adjusted=effect.adjusted,
                    covariates=effect.covariates,
                    warnings=effect.warnings,
                )
                for index, effect in enumerate(effects)
            ]
            result = AnalysisResult(
                result_id=new_analysis_result_id(),
                dataset_id=dataset.dataset_id,
                project_id=dataset.project_id,
                profile_type=dataset.profile_type,
                outcome_name=dataset.outcome_name,
                effect_measure=dataset.effect_measure,
                model=pooled.model,
                pooled_effect=pooled.pooled_effect,
                ci_lower=pooled.ci_lower,
                ci_upper=pooled.ci_upper,
                p_value=pooled.p_value,
                q_statistic=pooled.q_statistic,
                i_squared=pooled.i_squared,
                tau_squared=pooled.tau_squared,
                study_results=study_results,
                warnings=_dedupe(warnings),
                created_at=now_utc(),
            )
            self._finish_task(task, success=True, summary=f"Meta-analysis completed for {len(study_results)} studies.")
            return result
        except Exception:
            self._finish_task(task, success=False, summary="Meta-analysis run failed.")
            raise

    def save_analysis_result(self, project_dir: Path, result: AnalysisResult) -> Path:
        project_dir = project_dir.expanduser().resolve()
        output_path = self._results_path(project_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        results = [existing for existing in self.list_analysis_results(project_dir) if existing.result_id != result.result_id]
        results.append(result)
        payload = {
            "project_id": result.project_id,
            "data_type": "analysis_result",
            "updated_at": now_utc(),
            "results": [analysis_result_to_dict(item) for item in results],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._register_asset(
            project_id=result.project_id,
            source_path=str(project_dir / "analysis" / "analysis_ready_datasets.json"),
            output_path=str(output_path),
        )
        return output_path

    def load_analysis_result(self, project_dir: Path, result_id: str) -> AnalysisResult | None:
        for result in self.list_analysis_results(project_dir):
            if result.result_id == result_id:
                return result
        return None

    def list_analysis_results(self, project_dir: Path) -> list[AnalysisResult]:
        path = self._results_path(project_dir.expanduser().resolve())
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [analysis_result_from_dict(item) for item in payload.get("results", [])]

    def _results_path(self, project_dir: Path) -> Path:
        return project_dir / "analysis" / "analysis_results.json"

    def _register_asset(self, *, project_id: str, source_path: str, output_path: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type="analysis_result",
            source_path=source_path,
            output_path=output_path,
            status="available",
        )

    def _start_task(self, *, project_id: str, summary: str) -> TaskRecord:
        now = now_utc()
        if self._task_center is None:
            return TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=TaskType.META_ANALYSIS_RUN,
                status=TaskStatus.RUNNING,
                module="meta_analysis",
                title="Meta-analysis Run",
                created_at=now,
                updated_at=now,
                project_id=project_id,
                started_at=now,
                summary=summary,
            )
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.META_ANALYSIS_RUN,
            module="meta_analysis",
            title="Meta-analysis Run",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=summary,
        )

    def _finish_task(self, task: TaskRecord, *, success: bool, summary: str) -> None:
        if self._task_center is None:
            return
        now = now_utc()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=summary,
                error_message="" if success else summary,
            )
        )


def _dedupe(items: list[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item and item not in deduped:
            deduped.append(item)
    return deduped
