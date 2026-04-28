from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.extraction.schema_registry import NETWORK_META_ANALYSIS, get_extraction_schema_profile
from app.meta_analysis.models.analysis_dataset import (
    AnalysisDatasetValidationResult,
    AnalysisReadyDataset,
    StudyAnalysisRow,
    analysis_ready_dataset_from_dict,
    analysis_ready_dataset_to_dict,
    new_analysis_ready_dataset_id,
    now_utc,
)
from app.meta_analysis.models.extraction import (
    BinaryOutcomeData,
    ContinuousOutcomeData,
    CorrelationOutcomeData,
    DiagnosticAccuracyOutcomeData,
    ExtractedOutcome,
    ExtractionRecord,
    GenericEffectOutcomeData,
    OutcomeDataType,
    ProportionOutcomeData,
)
from app.meta_analysis.services.extraction_record_storage_service import ExtractionRecordStorageService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


class AnalysisDatasetService:
    def __init__(
        self,
        *,
        extraction_storage: ExtractionRecordStorageService | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
    ) -> None:
        self._task_center = task_center
        self._data_center = data_center
        self._extraction_storage = extraction_storage or ExtractionRecordStorageService()

    def list_available_outcomes(self, project_dir: Path) -> list[dict[str, object]]:
        outcome_counts: dict[tuple[str, str, str, str], int] = {}
        for outcome in self._extraction_storage.list_extraction_outcomes(project_dir):
            key = (
                outcome["profile_type"],
                outcome["outcome_name"],
                outcome["effect_measure"],
                outcome["outcome_data_type"],
            )
            outcome_counts[key] = outcome_counts.get(key, 0) + 1
        return [
            {
                "profile_type": profile_type,
                "outcome_name": outcome_name,
                "effect_measure": effect_measure,
                "outcome_data_type": outcome_data_type,
                "record_count": record_count,
            }
            for (profile_type, outcome_name, effect_measure, outcome_data_type), record_count in sorted(outcome_counts.items())
        ]

    def build_analysis_ready_dataset(
        self,
        project_dir: Path,
        profile_type: str,
        outcome_name: str,
        effect_measure: str,
    ) -> AnalysisReadyDataset:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_dir.name
        task = self._start_task(
            project_id=project_id,
            summary=f"Building analysis-ready dataset for {profile_type} / {outcome_name} / {effect_measure}",
        )
        try:
            dataset = self._build_dataset(project_dir, profile_type, outcome_name, effect_measure)
            validation = self.validate_analysis_dataset(dataset)
            dataset = AnalysisReadyDataset(
                dataset_id=dataset.dataset_id,
                project_id=dataset.project_id,
                profile_type=dataset.profile_type,
                outcome_name=dataset.outcome_name,
                effect_measure=dataset.effect_measure,
                outcome_data_type=dataset.outcome_data_type,
                included_extraction_ids=dataset.included_extraction_ids,
                excluded_extraction_ids=dataset.excluded_extraction_ids,
                study_rows=dataset.study_rows,
                validation_errors=_dedupe([*dataset.validation_errors, *validation.errors]),
                validation_warnings=_dedupe([*dataset.validation_warnings, *validation.warnings]),
                created_at=dataset.created_at,
            )
            self._finish_task(task, success=True, summary=_dataset_task_summary(dataset))
            return dataset
        except Exception as exc:
            dataset = AnalysisReadyDataset(
                dataset_id=new_analysis_ready_dataset_id(),
                project_id=project_id,
                profile_type=profile_type,
                outcome_name=outcome_name,
                effect_measure=effect_measure,
                outcome_data_type="",
                included_extraction_ids=[],
                excluded_extraction_ids=[],
                study_rows=[],
                validation_errors=["analysis_dataset_build_failed"],
                validation_warnings=[],
                created_at=now_utc(),
            )
            self._finish_task(task, success=False, summary="Analysis-ready dataset build failed.")
            return AnalysisReadyDataset(
                **{
                    **analysis_ready_dataset_to_dict(dataset),
                    "validation_errors": [*dataset.validation_errors, str(exc)],
                }
            )

    def validate_analysis_dataset(self, dataset: AnalysisReadyDataset) -> AnalysisDatasetValidationResult:
        errors = list(dataset.validation_errors)
        warnings = list(dataset.validation_warnings)
        if not dataset.profile_type:
            errors.append("profile_type_missing")
        if not dataset.outcome_name:
            errors.append("outcome_name_missing")
        if not dataset.effect_measure:
            errors.append("effect_measure_missing")
        if not dataset.included_extraction_ids:
            errors.append("analysis_ready_dataset_has_no_included_studies")
        if len(dataset.included_extraction_ids) < 2 and dataset.included_extraction_ids:
            warnings.append("fewer_than_two_included_studies")
        for row in dataset.study_rows:
            if row.analysis_status == "excluded" and not row.exclusion_reason:
                errors.append(f"excluded_row_missing_reason:{row.record_id}")
        return AnalysisDatasetValidationResult(valid=not errors, errors=_dedupe(errors), warnings=_dedupe(warnings))

    def save_analysis_ready_dataset(self, project_dir: Path, dataset: AnalysisReadyDataset) -> Path:
        project_dir = project_dir.expanduser().resolve()
        output_path = self._datasets_path(project_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        datasets = [existing for existing in self.list_analysis_ready_datasets(project_dir) if existing.dataset_id != dataset.dataset_id]
        datasets.append(dataset)
        payload = {
            "project_id": dataset.project_id,
            "data_type": "analysis_ready_dataset",
            "updated_at": now_utc(),
            "datasets": [analysis_ready_dataset_to_dict(item) for item in datasets],
        }
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._register_asset(
            project_id=dataset.project_id,
            source_path=str(project_dir / "extraction" / "extraction_records.json"),
            output_path=str(output_path),
            status="available" if dataset.included_extraction_ids and not dataset.validation_errors else "needs_attention",
        )
        return output_path

    def load_analysis_ready_dataset(self, project_dir: Path, dataset_id: str) -> AnalysisReadyDataset | None:
        for dataset in self.list_analysis_ready_datasets(project_dir):
            if dataset.dataset_id == dataset_id:
                return dataset
        return None

    def list_analysis_ready_datasets(self, project_dir: Path) -> list[AnalysisReadyDataset]:
        path = self._datasets_path(project_dir.expanduser().resolve())
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [analysis_ready_dataset_from_dict(item) for item in payload.get("datasets", [])]

    def _build_dataset(self, project_dir: Path, profile_type: str, outcome_name: str, effect_measure: str) -> AnalysisReadyDataset:
        records_path = project_dir / "extraction" / "extraction_records.json"
        records = self._extraction_storage.load_extraction_records(project_dir)
        project_id = records[0].project_id if records else project_dir.name
        global_errors: list[str] = []
        global_warnings: list[str] = []
        if not records_path.exists():
            global_errors.append("extraction_records_missing")
        if not records:
            global_errors.append("extraction_records_empty")
        if get_extraction_schema_profile(profile_type) is None:
            global_errors.append("unsupported_profile_type")
        if profile_type == NETWORK_META_ANALYSIS:
            global_errors.append("network_meta_analysis_not_implemented")

        included_extraction_ids: list[str] = []
        excluded_extraction_ids: list[str] = []
        rows: list[StudyAnalysisRow] = []
        matched_outcome_type = ""
        matched_count = 0
        for record in records:
            if record.profile_type != profile_type:
                continue
            for outcome in record.outcomes:
                if outcome.data.outcome_name != outcome_name or outcome.data.effect_measure != effect_measure:
                    continue
                matched_count += 1
                matched_outcome_type = matched_outcome_type or outcome.outcome_data_type
                row_errors, row_warnings, normalized_data = self._validate_and_normalize_outcome(
                    profile_type=profile_type,
                    outcome=outcome,
                    record=record,
                )
                analysis_status = "included" if not row_errors else "excluded"
                if analysis_status == "included":
                    _append_unique(included_extraction_ids, record.extraction_id)
                else:
                    _append_unique(excluded_extraction_ids, record.extraction_id)
                rows.append(
                    StudyAnalysisRow(
                        study_id=record.study_id,
                        record_id=record.record_id,
                        first_author=record.study_characteristics.first_author,
                        year=record.study_characteristics.year,
                        outcome_name=outcome.data.outcome_name,
                        effect_measure=outcome.data.effect_measure,
                        outcome_data_type=outcome.outcome_data_type,
                        raw_data=asdict(outcome.data),
                        normalized_data=normalized_data,
                        analysis_status=analysis_status,
                        exclusion_reason="; ".join(row_errors),
                        warnings=row_warnings,
                    )
                )
        if records and matched_count == 0:
            global_errors.append("matching_outcome_missing")
        return AnalysisReadyDataset(
            dataset_id=new_analysis_ready_dataset_id(),
            project_id=project_id,
            profile_type=profile_type,
            outcome_name=outcome_name,
            effect_measure=effect_measure,
            outcome_data_type=matched_outcome_type,
            included_extraction_ids=included_extraction_ids,
            excluded_extraction_ids=excluded_extraction_ids,
            study_rows=rows,
            validation_errors=_dedupe(global_errors),
            validation_warnings=_dedupe(global_warnings),
            created_at=now_utc(),
        )

    def _validate_and_normalize_outcome(
        self,
        *,
        profile_type: str,
        outcome: ExtractedOutcome,
        record: ExtractionRecord,
    ) -> tuple[list[str], list[str], dict[str, object]]:
        errors: list[str] = []
        warnings: list[str] = []
        profile = get_extraction_schema_profile(profile_type)
        if profile is not None and outcome.data.effect_measure not in profile.supported_effect_measures:
            errors.append("effect_measure_not_supported_by_profile")
        if record.validation_status == "invalid":
            warnings.append("extraction_record_validation_status_invalid")
        if outcome.outcome_data_type == OutcomeDataType.BINARY.value and isinstance(outcome.data, BinaryOutcomeData):
            return self._validate_binary(outcome.data, errors, warnings)
        if outcome.outcome_data_type == OutcomeDataType.CONTINUOUS.value and isinstance(outcome.data, ContinuousOutcomeData):
            return self._validate_continuous(outcome.data, errors, warnings)
        if outcome.outcome_data_type == OutcomeDataType.GENERIC_EFFECT.value and isinstance(outcome.data, GenericEffectOutcomeData):
            return self._validate_generic_effect(outcome.data, errors, warnings)
        if outcome.outcome_data_type == OutcomeDataType.PROPORTION.value and isinstance(outcome.data, ProportionOutcomeData):
            return self._validate_proportion(outcome.data, errors, warnings)
        if outcome.outcome_data_type == OutcomeDataType.CORRELATION.value and isinstance(outcome.data, CorrelationOutcomeData):
            return self._validate_correlation(outcome.data, errors, warnings)
        if outcome.outcome_data_type == OutcomeDataType.DIAGNOSTIC_ACCURACY.value and isinstance(outcome.data, DiagnosticAccuracyOutcomeData):
            return self._validate_diagnostic_accuracy(outcome.data, errors, warnings)
        return [*errors, "unsupported_outcome_data_type"], warnings, {}

    def _validate_binary(
        self,
        data: BinaryOutcomeData,
        errors: list[str],
        warnings: list[str],
    ) -> tuple[list[str], list[str], dict[str, object]]:
        if data.effect_measure not in {"OR", "RR", "RD"}:
            errors.append("binary_effect_measure_not_analysis_supported")
        for label, events, total in (
            ("experimental", data.experimental_events, data.experimental_total),
            ("control", data.control_events, data.control_total),
        ):
            if total <= 0:
                errors.append(f"{label}_total_must_be_positive")
            if events < 0:
                errors.append(f"{label}_events_cannot_be_negative")
            if events > total:
                errors.append(f"{label}_events_cannot_exceed_total")
        normalized = {
            "experimental_events": data.experimental_events,
            "experimental_non_events": data.experimental_total - data.experimental_events,
            "experimental_total": data.experimental_total,
            "control_events": data.control_events,
            "control_non_events": data.control_total - data.control_events,
            "control_total": data.control_total,
            "effect_measure": data.effect_measure,
            "timepoint": data.timepoint,
            "subgroup": data.subgroup,
        }
        return errors, warnings, normalized

    def _validate_continuous(
        self,
        data: ContinuousOutcomeData,
        errors: list[str],
        warnings: list[str],
    ) -> tuple[list[str], list[str], dict[str, object]]:
        if data.effect_measure not in {"MD", "SMD"}:
            errors.append("continuous_effect_measure_not_analysis_supported")
        if data.experimental_total <= 0:
            errors.append("experimental_total_must_be_positive")
        if data.control_total <= 0:
            errors.append("control_total_must_be_positive")
        if data.experimental_sd < 0:
            errors.append("experimental_sd_cannot_be_negative")
        if data.control_sd < 0:
            errors.append("control_sd_cannot_be_negative")
        normalized = {
            "experimental_mean": data.experimental_mean,
            "experimental_sd": data.experimental_sd,
            "experimental_total": data.experimental_total,
            "control_mean": data.control_mean,
            "control_sd": data.control_sd,
            "control_total": data.control_total,
            "effect_measure": data.effect_measure,
            "unit": data.unit,
            "timepoint": data.timepoint,
            "subgroup": data.subgroup,
        }
        return errors, warnings, normalized

    def _validate_generic_effect(
        self,
        data: GenericEffectOutcomeData,
        errors: list[str],
        warnings: list[str],
    ) -> tuple[list[str], list[str], dict[str, object]]:
        if data.effect_measure in {"OR", "RR", "HR"} and data.effect <= 0:
            errors.append("ratio_effect_must_be_positive")
        if data.ci_lower is not None and data.ci_upper is not None and data.ci_lower > data.ci_upper:
            errors.append("ci_lower_cannot_exceed_ci_upper")
        if data.standard_error is not None and data.standard_error <= 0:
            errors.append("standard_error_must_be_positive")
        if data.standard_error is None and (data.ci_lower is None or data.ci_upper is None):
            errors.append("generic_effect_requires_standard_error_or_ci")
        normalized = {
            "effect": data.effect,
            "ci_lower": data.ci_lower,
            "ci_upper": data.ci_upper,
            "standard_error": data.standard_error,
            "p_value": data.p_value,
            "adjusted": data.adjusted,
            "covariates": data.covariates,
            "effect_measure": data.effect_measure,
            "timepoint": data.timepoint,
            "subgroup": data.subgroup,
        }
        return errors, warnings, normalized

    def _validate_proportion(
        self,
        data: ProportionOutcomeData,
        errors: list[str],
        warnings: list[str],
    ) -> tuple[list[str], list[str], dict[str, object]]:
        if data.effect_measure not in {"PREVALENCE", "INCIDENCE", "PROPORTION", "SINGLE_ARM"}:
            errors.append("proportion_effect_measure_not_analysis_supported")
        if data.total <= 0:
            errors.append("total_must_be_positive")
        if data.events < 0:
            errors.append("events_cannot_be_negative")
        if data.events > data.total:
            errors.append("events_cannot_exceed_total")
        normalized = {
            "events": data.events,
            "non_events": data.total - data.events,
            "total": data.total,
            "proportion": data.events / data.total if data.total > 0 else None,
            "effect_measure": data.effect_measure,
            "population_source": data.population_source,
            "diagnostic_criteria": data.diagnostic_criteria,
            "timepoint": data.timepoint,
            "subgroup": data.subgroup,
        }
        return errors, warnings, normalized

    def _validate_correlation(
        self,
        data: CorrelationOutcomeData,
        errors: list[str],
        warnings: list[str],
    ) -> tuple[list[str], list[str], dict[str, object]]:
        if data.effect_measure not in {"CORRELATION", "PEARSON_R", "SPEARMAN_R"}:
            errors.append("correlation_effect_measure_not_analysis_supported")
        if not -1 < data.r < 1:
            errors.append("correlation_must_be_between_minus_one_and_one")
        if data.sample_size <= 3:
            errors.append("sample_size_must_exceed_three")
        if data.p_value is not None and not 0 <= data.p_value <= 1:
            errors.append("p_value_must_be_between_zero_and_one")
        normalized = {
            "r": data.r,
            "sample_size": data.sample_size,
            "correlation_type": data.correlation_type,
            "p_value": data.p_value,
            "variable_x": data.variable_x,
            "variable_y": data.variable_y,
            "effect_measure": data.effect_measure,
        }
        return errors, warnings, normalized

    def _validate_diagnostic_accuracy(
        self,
        data: DiagnosticAccuracyOutcomeData,
        errors: list[str],
        warnings: list[str],
    ) -> tuple[list[str], list[str], dict[str, object]]:
        if data.effect_measure not in {"SENSITIVITY", "SPECIFICITY", "PLR", "NLR", "DOR"}:
            errors.append("diagnostic_effect_measure_not_analysis_supported")
        for field_name in ("tp", "fp", "fn", "tn"):
            if getattr(data, field_name) < 0:
                errors.append(f"{field_name}_cannot_be_negative")
        sensitivity_denominator = data.tp + data.fn
        specificity_denominator = data.tn + data.fp
        if sensitivity_denominator <= 0:
            errors.append("sensitivity_denominator_must_be_positive")
        if specificity_denominator <= 0:
            errors.append("specificity_denominator_must_be_positive")
        sensitivity = data.tp / sensitivity_denominator if sensitivity_denominator > 0 else None
        specificity = data.tn / specificity_denominator if specificity_denominator > 0 else None
        plr = sensitivity / (1 - specificity) if sensitivity is not None and specificity not in {None, 1} else None
        nlr = (1 - sensitivity) / specificity if specificity not in {None, 0} and sensitivity is not None else None
        dor = plr / nlr if plr is not None and nlr not in {None, 0} else None
        normalized = {
            "tp": data.tp,
            "fp": data.fp,
            "fn": data.fn,
            "tn": data.tn,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "plr": plr,
            "nlr": nlr,
            "dor": dor,
            "effect_measure": data.effect_measure,
            "cutoff": data.cutoff,
            "index_test": data.index_test,
            "reference_standard": data.reference_standard,
        }
        return errors, warnings, normalized

    def _datasets_path(self, project_dir: Path) -> Path:
        return project_dir / "analysis" / "analysis_ready_datasets.json"

    def _register_asset(self, *, project_id: str, source_path: str, output_path: str, status: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type="analysis_ready_dataset",
            source_path=source_path,
            output_path=output_path,
            status=status,
        )

    def _start_task(self, *, project_id: str, summary: str) -> TaskRecord:
        now = now_utc()
        if self._task_center is None:
            return TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=TaskType.ANALYSIS_DATASET_BUILD,
                status=TaskStatus.RUNNING,
                module="meta_analysis",
                title="Analysis-ready Dataset Build",
                created_at=now,
                updated_at=now,
                project_id=project_id,
                started_at=now,
                summary=summary,
            )
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.ANALYSIS_DATASET_BUILD,
            module="meta_analysis",
            title="Analysis-ready Dataset Build",
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


def _dataset_task_summary(dataset: AnalysisReadyDataset) -> str:
    return (
        "Analysis-ready dataset built: "
        f"{len(dataset.included_extraction_ids)} included, "
        f"{len(dataset.excluded_extraction_ids)} excluded, "
        f"{len(dataset.validation_errors)} validation errors."
    )


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _dedupe(items: list[str]) -> list[str]:
    deduped: list[str] = []
    for item in items:
        if item and item not in deduped:
            deduped.append(item)
    return deduped
