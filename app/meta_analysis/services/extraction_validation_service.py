from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from app.meta_analysis.extraction.schema_registry import get_extraction_schema_profile
from app.meta_analysis.models.extraction import (
    BinaryOutcomeData,
    ContinuousOutcomeData,
    CorrelationOutcomeData,
    DiagnosticAccuracyOutcomeData,
    ExtractedOutcome,
    ExtractionRecord,
    ExtractionValidationResult,
    ExtractionValidationStatus,
    GenericEffectOutcomeData,
    OutcomeDataType,
    ProportionOutcomeData,
    StudyCharacteristics,
)
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


RATIO_EFFECT_MEASURES = {"OR", "RR", "HR"}


class ExtractionValidationService:
    def __init__(self, *, task_center: TaskCenter | None = None) -> None:
        self._task_center = task_center

    def validate_study_characteristics(
        self,
        study: StudyCharacteristics,
        *,
        profile_type: str = "",
    ) -> ExtractionValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        profile = get_extraction_schema_profile(profile_type) if profile_type else None
        required_fields = profile.required_study_fields if profile is not None else ("first_author", "year", "sample_size")
        for field_name in required_fields:
            value = getattr(study, field_name)
            if value in {"", None}:
                warnings.append(f"missing_required_study_field:{field_name}")
        if study.sample_size is not None and study.sample_size <= 0:
            errors.append("sample_size_must_be_positive")
        return _validation_result(errors, warnings)

    def validate_binary_outcome(
        self,
        outcome: BinaryOutcomeData,
        *,
        profile_type: str,
    ) -> ExtractionValidationResult:
        errors, warnings = self._validate_common_outcome(
            outcome_name=outcome.outcome_name,
            effect_measure=outcome.effect_measure,
            profile_type=profile_type,
            outcome_data_type=OutcomeDataType.BINARY.value,
        )
        for field_name in ("experimental_total", "control_total"):
            if getattr(outcome, field_name) <= 0:
                errors.append(f"{field_name}_must_be_positive")
        if outcome.experimental_events > outcome.experimental_total:
            errors.append("experimental_events_cannot_exceed_total")
        if outcome.control_events > outcome.control_total:
            errors.append("control_events_cannot_exceed_total")
        return _validation_result(errors, warnings)

    def validate_continuous_outcome(
        self,
        outcome: ContinuousOutcomeData,
        *,
        profile_type: str,
    ) -> ExtractionValidationResult:
        errors, warnings = self._validate_common_outcome(
            outcome_name=outcome.outcome_name,
            effect_measure=outcome.effect_measure,
            profile_type=profile_type,
            outcome_data_type=OutcomeDataType.CONTINUOUS.value,
        )
        for field_name in ("experimental_total", "control_total"):
            if getattr(outcome, field_name) <= 0:
                errors.append(f"{field_name}_must_be_positive")
        for field_name in ("experimental_sd", "control_sd"):
            if getattr(outcome, field_name) < 0:
                errors.append(f"{field_name}_cannot_be_negative")
        return _validation_result(errors, warnings)

    def validate_generic_effect_outcome(
        self,
        outcome: GenericEffectOutcomeData,
        *,
        profile_type: str,
    ) -> ExtractionValidationResult:
        errors, warnings = self._validate_common_outcome(
            outcome_name=outcome.outcome_name,
            effect_measure=outcome.effect_measure,
            profile_type=profile_type,
            outcome_data_type=OutcomeDataType.GENERIC_EFFECT.value,
        )
        if outcome.ci_lower is not None and outcome.ci_upper is not None and outcome.ci_lower > outcome.ci_upper:
            errors.append("ci_lower_cannot_exceed_ci_upper")
        if outcome.standard_error is not None and outcome.standard_error < 0:
            errors.append("standard_error_cannot_be_negative")
        if outcome.effect_measure.upper() in RATIO_EFFECT_MEASURES and outcome.effect <= 0:
            errors.append("ratio_effect_must_be_positive")
        return _validation_result(errors, warnings)

    def validate_diagnostic_accuracy_outcome(
        self,
        outcome: DiagnosticAccuracyOutcomeData,
        *,
        profile_type: str,
    ) -> ExtractionValidationResult:
        errors, warnings = self._validate_common_outcome(
            outcome_name=outcome.outcome_name,
            effect_measure=outcome.effect_measure,
            profile_type=profile_type,
            outcome_data_type=OutcomeDataType.DIAGNOSTIC_ACCURACY.value,
        )
        for field_name in ("tp", "fp", "fn", "tn"):
            if getattr(outcome, field_name) < 0:
                errors.append(f"{field_name}_cannot_be_negative")
        if outcome.tp + outcome.fn <= 0:
            errors.append("sensitivity_denominator_must_be_positive")
        if outcome.tn + outcome.fp <= 0:
            errors.append("specificity_denominator_must_be_positive")
        for field_name in ("sensitivity", "specificity"):
            value = getattr(outcome, field_name)
            if value is not None and not 0 <= value <= 1:
                errors.append(f"{field_name}_must_be_between_zero_and_one")
        return _validation_result(errors, warnings)

    def validate_proportion_outcome(
        self,
        outcome: ProportionOutcomeData,
        *,
        profile_type: str,
    ) -> ExtractionValidationResult:
        errors, warnings = self._validate_common_outcome(
            outcome_name=outcome.outcome_name,
            effect_measure=outcome.effect_measure,
            profile_type=profile_type,
            outcome_data_type=OutcomeDataType.PROPORTION.value,
        )
        if outcome.total <= 0:
            errors.append("total_must_be_positive")
        if outcome.events < 0:
            errors.append("events_cannot_be_negative")
        if outcome.events > outcome.total:
            errors.append("events_cannot_exceed_total")
        return _validation_result(errors, warnings)

    def validate_correlation_outcome(
        self,
        outcome: CorrelationOutcomeData,
        *,
        profile_type: str,
    ) -> ExtractionValidationResult:
        errors, warnings = self._validate_common_outcome(
            outcome_name=outcome.outcome_name,
            effect_measure=outcome.effect_measure,
            profile_type=profile_type,
            outcome_data_type=OutcomeDataType.CORRELATION.value,
        )
        if not -1 < outcome.r < 1:
            errors.append("correlation_must_be_between_minus_one_and_one")
        if outcome.sample_size <= 3:
            errors.append("sample_size_must_exceed_three")
        if outcome.p_value is not None and not 0 <= outcome.p_value <= 1:
            errors.append("p_value_must_be_between_zero_and_one")
        return _validation_result(errors, warnings)

    def validate_extraction_record(self, record: ExtractionRecord) -> ExtractionValidationResult:
        profile = get_extraction_schema_profile(record.profile_type)
        errors: list[str] = []
        warnings: list[str] = []
        if profile is None:
            errors.append("unsupported_profile_type")
        study_result = self.validate_study_characteristics(record.study_characteristics, profile_type=record.profile_type)
        errors.extend(study_result.errors)
        warnings.extend(study_result.warnings)
        if not record.outcomes:
            warnings.append("outcomes_missing")
        for outcome in record.outcomes:
            result = self._validate_extracted_outcome(outcome, profile_type=record.profile_type)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        return _validation_result(errors, warnings)

    def validate_extraction_record_task(self, *, project_id: str, record: ExtractionRecord) -> ExtractionValidationResult:
        task = self._start_task(project_id=project_id, record_id=record.record_id)
        result = self.validate_extraction_record(record)
        self._finish_task(task, result)
        return result

    def record_with_validation_status(self, record: ExtractionRecord) -> ExtractionRecord:
        result = self.validate_extraction_record(record)
        now = datetime.now(timezone.utc).isoformat()
        return replace(record, validation_status=result.status, updated_at=now)

    def _validate_extracted_outcome(
        self,
        outcome: ExtractedOutcome,
        *,
        profile_type: str,
    ) -> ExtractionValidationResult:
        if outcome.outcome_data_type == OutcomeDataType.BINARY.value and isinstance(outcome.data, BinaryOutcomeData):
            return self.validate_binary_outcome(outcome.data, profile_type=profile_type)
        if outcome.outcome_data_type == OutcomeDataType.CONTINUOUS.value and isinstance(outcome.data, ContinuousOutcomeData):
            return self.validate_continuous_outcome(outcome.data, profile_type=profile_type)
        if outcome.outcome_data_type == OutcomeDataType.GENERIC_EFFECT.value and isinstance(outcome.data, GenericEffectOutcomeData):
            return self.validate_generic_effect_outcome(outcome.data, profile_type=profile_type)
        if outcome.outcome_data_type == OutcomeDataType.DIAGNOSTIC_ACCURACY.value and isinstance(outcome.data, DiagnosticAccuracyOutcomeData):
            return self.validate_diagnostic_accuracy_outcome(outcome.data, profile_type=profile_type)
        if outcome.outcome_data_type == OutcomeDataType.PROPORTION.value and isinstance(outcome.data, ProportionOutcomeData):
            return self.validate_proportion_outcome(outcome.data, profile_type=profile_type)
        if outcome.outcome_data_type == OutcomeDataType.CORRELATION.value and isinstance(outcome.data, CorrelationOutcomeData):
            return self.validate_correlation_outcome(outcome.data, profile_type=profile_type)
        return ExtractionValidationResult(status=ExtractionValidationStatus.INVALID.value, errors=["outcome_data_type_mismatch"])

    def _validate_common_outcome(
        self,
        *,
        outcome_name: str,
        effect_measure: str,
        profile_type: str,
        outcome_data_type: str,
    ) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        profile = get_extraction_schema_profile(profile_type)
        if profile is None:
            errors.append("unsupported_profile_type")
            return errors, warnings
        if outcome_data_type not in profile.allowed_outcome_data_types:
            errors.append(f"outcome_data_type_not_allowed:{outcome_data_type}")
        if not outcome_name.strip():
            errors.append("outcome_name_required")
        if effect_measure.upper() not in profile.supported_effect_measures:
            errors.append(f"unsupported_effect_measure:{effect_measure}")
        return errors, warnings

    def _start_task(self, *, project_id: str, record_id: str) -> TaskRecord:
        if self._task_center is None:
            now = datetime.now(timezone.utc).isoformat()
            return TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=TaskType.EXTRACTION_RECORD_VALIDATION,
                status=TaskStatus.RUNNING,
                module="meta_analysis",
                title="Extraction Record Validation",
                created_at=now,
                updated_at=now,
                project_id=project_id,
                started_at=now,
                summary=f"Validating extraction record {record_id}",
            )
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.EXTRACTION_RECORD_VALIDATION,
            module="meta_analysis",
            title="Extraction Record Validation",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now(timezone.utc).isoformat(),
            summary=f"Validating extraction record {record_id}",
        )

    def _finish_task(self, task: TaskRecord, result: ExtractionValidationResult) -> None:
        if self._task_center is None:
            return
        now = datetime.now(timezone.utc).isoformat()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if result.is_valid else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=result.status,
                error_message="; ".join(result.errors),
            )
        )


def _validation_result(errors: list[str], warnings: list[str]) -> ExtractionValidationResult:
    if errors:
        status = ExtractionValidationStatus.INVALID.value
    elif warnings:
        status = ExtractionValidationStatus.VALID_WITH_WARNINGS.value
    else:
        status = ExtractionValidationStatus.VALID.value
    return ExtractionValidationResult(status=status, errors=errors, warnings=warnings)
