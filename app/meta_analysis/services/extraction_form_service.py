from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.extraction.schema_registry import TREATMENT_EFFECT_META, list_extraction_schema_profiles
from app.meta_analysis.models.extraction import (
    BinaryOutcomeData,
    ContinuousOutcomeData,
    ExtractedOutcome,
    ExtractionRecord,
    ExtractionValidationResult,
    GenericEffectOutcomeData,
    OutcomeDataType,
    StudyCharacteristics,
    new_extraction_id,
    now_utc,
)
from app.meta_analysis.services.extraction_record_storage_service import ExtractionRecordStorageService
from app.meta_analysis.services.extraction_validation_service import ExtractionValidationService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskRecord, TaskStatus, TaskType


@dataclass(frozen=True)
class ExtractionCandidateRecord:
    record_id: str
    study_id: str
    study_title: str
    source_path: str


@dataclass(frozen=True)
class ExtractionRecordSaveResult:
    success: bool
    project_id: str
    output_path: str
    validation: ExtractionValidationResult
    message: str
    record: ExtractionRecord | None = None
    details: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ExtractionRecordsExportResult:
    success: bool
    project_id: str
    source_path: str
    output_path: str
    record_count: int
    message: str
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)


class ExtractionFormService:
    def __init__(
        self,
        *,
        storage_service: ExtractionRecordStorageService | None = None,
        validation_service: ExtractionValidationService | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
    ) -> None:
        self._task_center = task_center
        self._data_center = data_center
        self._storage_service = storage_service or ExtractionRecordStorageService(
            task_center=task_center,
            data_center=data_center,
        )
        self._validation_service = validation_service or ExtractionValidationService(task_center=task_center)

    def load_candidate_records(self, extraction_pool_path: str) -> list[ExtractionCandidateRecord]:
        if not extraction_pool_path.strip():
            return []
        path = Path(extraction_pool_path).expanduser()
        if not path.exists() or path.suffix.lower() != ".json":
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        candidates: list[ExtractionCandidateRecord] = []
        for item in payload.get("extraction_records", []):
            record_id = str(item.get("normalized_record_id") or item.get("screening_record_id") or item.get("extraction_record_id", ""))
            candidates.append(
                ExtractionCandidateRecord(
                    record_id=record_id,
                    study_id=str(item.get("extraction_record_id") or record_id),
                    study_title=str(item.get("study_title", "")),
                    source_path=str(path),
                )
            )
        return candidates

    def build_extraction_record(
        self,
        *,
        project_id: str,
        form_data: dict[str, object],
    ) -> ExtractionRecord:
        outcome_type = str(form_data.get("outcome_data_type", OutcomeDataType.BINARY.value))
        profile_type = str(form_data.get("profile_type", TREATMENT_EFFECT_META))
        created_at = str(form_data.get("created_at") or now_utc())
        study = StudyCharacteristics(
            first_author=str(form_data.get("first_author", "")),
            year=_optional_int(form_data.get("year")),
            country=str(form_data.get("country", "")),
            study_design=str(form_data.get("study_design", "")),
            population=str(form_data.get("population", "")),
            sample_size=_optional_int(form_data.get("sample_size")),
            intervention_or_exposure=str(form_data.get("intervention_or_exposure", "")),
            comparator=str(form_data.get("comparator", "")),
            follow_up=str(form_data.get("follow_up", "")),
            notes=str(form_data.get("study_notes", "")),
        )
        outcome = ExtractedOutcome(
            outcome_id=str(form_data.get("outcome_id") or f"out-{uuid4().hex[:12]}"),
            outcome_data_type=outcome_type,
            data=self._outcome_data(outcome_type=outcome_type, form_data=form_data),
        )
        return ExtractionRecord(
            extraction_id=str(form_data.get("extraction_id") or new_extraction_id()),
            project_id=project_id,
            record_id=str(form_data.get("record_id", "")),
            study_id=str(form_data.get("study_id", "")),
            reviewer_id=str(form_data.get("reviewer_id", "")),
            profile_type=profile_type,
            study_characteristics=study,
            outcomes=[outcome],
            notes=str(form_data.get("notes", "")),
            source_location=str(form_data.get("source_location", "")),
            validation_status="invalid",
            created_at=created_at,
            updated_at=str(form_data.get("updated_at") or created_at),
        )

    def save_extraction_record(self, *, project_dir: Path, record: ExtractionRecord) -> ExtractionRecordSaveResult:
        validation = self._validation_service.validate_extraction_record(record)
        if validation.errors:
            return ExtractionRecordSaveResult(
                success=False,
                project_id=record.project_id,
                output_path="",
                validation=validation,
                message="Extraction record contains validation errors and was not saved.",
                record=record,
            )
        validated_record = self._validation_service.record_with_validation_status(record)
        output_path = self._storage_service.append_or_update_extraction_record(project_dir, validated_record)
        return ExtractionRecordSaveResult(
            success=True,
            project_id=record.project_id,
            output_path=str(output_path),
            validation=validation,
            message="Extraction record saved.",
            record=validated_record,
            details={"warnings": validation.warnings},
        )

    def save_extraction_record_from_form(
        self,
        *,
        project_dir: Path,
        project_id: str,
        form_data: dict[str, object],
    ) -> ExtractionRecordSaveResult:
        try:
            record = self.build_extraction_record(project_id=project_id, form_data=form_data)
        except ValueError as exc:
            validation = ExtractionValidationResult(status="invalid", errors=[str(exc)], warnings=[])
            return ExtractionRecordSaveResult(
                success=False,
                project_id=project_id,
                output_path="",
                validation=validation,
                message="Extraction record form contains invalid numeric values.",
            )
        return self.save_extraction_record(project_dir=project_dir, record=record)

    def export_extraction_records_csv(self, *, project_dir: Path, project_id: str | None = None) -> ExtractionRecordsExportResult:
        project_dir = project_dir.expanduser().resolve()
        task = self._start_export_task(project_id=project_id or project_dir.name, project_dir=project_dir)
        try:
            records = self._storage_service.load_extraction_records(project_dir)
            output_path = project_dir / "exports" / "extraction_records.csv"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=_export_fieldnames())
                writer.writeheader()
                for record in records:
                    for outcome in record.outcomes:
                        writer.writerow(_export_row(record, outcome))
            resolved_project_id = project_id or (records[0].project_id if records else project_dir.name)
            self._register_export_asset(
                project_id=resolved_project_id,
                source_path=str(project_dir / "extraction" / "extraction_records.json"),
                output_path=str(output_path),
            )
            result = ExtractionRecordsExportResult(
                success=True,
                project_id=resolved_project_id,
                source_path=str(project_dir / "extraction" / "extraction_records.json"),
                output_path=str(output_path),
                record_count=len(records),
                message=f"Extraction records CSV exported: {len(records)} records.",
            )
            self._finish_export_task(task, result)
            return result
        except Exception as exc:
            result = ExtractionRecordsExportResult(
                success=False,
                project_id=project_id or project_dir.name,
                source_path=str(project_dir / "extraction" / "extraction_records.json"),
                output_path="",
                record_count=0,
                message="Extraction records export failed.",
                error_count=1,
                details={"error": str(exc)},
            )
            self._finish_export_task(task, result)
            return result

    def available_profile_types(self) -> tuple[str, ...]:
        return tuple(profile.profile_type for profile in list_extraction_schema_profiles())

    def _outcome_data(self, *, outcome_type: str, form_data: dict[str, object]) -> BinaryOutcomeData | ContinuousOutcomeData | GenericEffectOutcomeData:
        if outcome_type == OutcomeDataType.BINARY.value:
            return BinaryOutcomeData(
                outcome_name=str(form_data.get("outcome_name", "")),
                effect_measure=str(form_data.get("effect_measure", "")),
                experimental_events=_required_int(form_data.get("experimental_events"), "experimental_events"),
                experimental_total=_required_int(form_data.get("experimental_total"), "experimental_total"),
                control_events=_required_int(form_data.get("control_events"), "control_events"),
                control_total=_required_int(form_data.get("control_total"), "control_total"),
                timepoint=str(form_data.get("timepoint", "")),
                subgroup=str(form_data.get("subgroup", "")),
                notes=str(form_data.get("outcome_notes", "")),
            )
        if outcome_type == OutcomeDataType.CONTINUOUS.value:
            return ContinuousOutcomeData(
                outcome_name=str(form_data.get("outcome_name", "")),
                effect_measure=str(form_data.get("effect_measure", "")),
                experimental_mean=_required_float(form_data.get("experimental_mean"), "experimental_mean"),
                experimental_sd=_required_float(form_data.get("experimental_sd"), "experimental_sd"),
                experimental_total=_required_int(form_data.get("experimental_total"), "experimental_total"),
                control_mean=_required_float(form_data.get("control_mean"), "control_mean"),
                control_sd=_required_float(form_data.get("control_sd"), "control_sd"),
                control_total=_required_int(form_data.get("control_total"), "control_total"),
                unit=str(form_data.get("unit", "")),
                timepoint=str(form_data.get("timepoint", "")),
                subgroup=str(form_data.get("subgroup", "")),
                notes=str(form_data.get("outcome_notes", "")),
            )
        if outcome_type == OutcomeDataType.GENERIC_EFFECT.value:
            covariates = [
                item.strip()
                for item in str(form_data.get("covariates", "")).split(",")
                if item.strip()
            ]
            return GenericEffectOutcomeData(
                outcome_name=str(form_data.get("outcome_name", "")),
                effect_measure=str(form_data.get("effect_measure", "")),
                effect=_required_float(form_data.get("effect"), "effect"),
                ci_lower=_optional_float(form_data.get("ci_lower")),
                ci_upper=_optional_float(form_data.get("ci_upper")),
                standard_error=_optional_float(form_data.get("standard_error")),
                p_value=_optional_float(form_data.get("p_value")),
                adjusted=_truthy(form_data.get("adjusted")),
                covariates=covariates,
                timepoint=str(form_data.get("timepoint", "")),
                subgroup=str(form_data.get("subgroup", "")),
                notes=str(form_data.get("outcome_notes", "")),
            )
        raise ValueError(f"unsupported_outcome_data_type:{outcome_type}")

    def _register_export_asset(self, *, project_id: str, source_path: str, output_path: str) -> None:
        if self._data_center is None:
            return
        self._data_center.register_asset(
            project_id=project_id,
            module="meta_analysis",
            data_type="extraction_records_export",
            source_path=source_path,
            output_path=output_path,
            status="available",
        )

    def _start_export_task(self, *, project_id: str, project_dir: Path) -> TaskRecord:
        now = datetime.now(timezone.utc).isoformat()
        if self._task_center is None:
            return TaskRecord(
                task_id=f"task-{uuid4().hex[:12]}",
                task_type=TaskType.EXTRACTION_EXPORT,
                status=TaskStatus.RUNNING,
                module="meta_analysis",
                title="Extraction Export",
                created_at=now,
                updated_at=now,
                project_id=project_id,
                started_at=now,
                summary=f"Exporting extraction records from {project_dir}",
            )
        return self._task_center.register_task(
            task_id=f"task-{uuid4().hex[:12]}",
            task_type=TaskType.EXTRACTION_EXPORT,
            module="meta_analysis",
            title="Extraction Export",
            project_id=project_id,
            status=TaskStatus.RUNNING,
            started_at=now,
            summary=f"Exporting extraction records from {project_dir}",
        )

    def _finish_export_task(self, task: TaskRecord, result: ExtractionRecordsExportResult) -> None:
        if self._task_center is None:
            return
        now = datetime.now(timezone.utc).isoformat()
        self._task_center.save_task(
            TaskRecord(
                task_id=task.task_id,
                task_type=task.task_type,
                status=TaskStatus.COMPLETED if result.success else TaskStatus.FAILED,
                module=task.module,
                title=task.title,
                created_at=task.created_at,
                updated_at=now,
                project_id=task.project_id,
                started_at=task.started_at,
                finished_at=now,
                summary=result.message,
                error_message="" if result.success else result.message,
            )
        )


def _export_fieldnames() -> list[str]:
    return [
        "extraction_id",
        "record_id",
        "study_id",
        "reviewer_id",
        "profile_type",
        "first_author",
        "year",
        "country",
        "study_design",
        "sample_size",
        "outcome_id",
        "outcome_data_type",
        "outcome_name",
        "effect_measure",
        "validation_status",
        "source_location",
        "notes",
    ]


def _export_row(record: ExtractionRecord, outcome: ExtractedOutcome) -> dict[str, object]:
    study = record.study_characteristics
    return {
        "extraction_id": record.extraction_id,
        "record_id": record.record_id,
        "study_id": record.study_id,
        "reviewer_id": record.reviewer_id,
        "profile_type": record.profile_type,
        "first_author": study.first_author,
        "year": study.year or "",
        "country": study.country,
        "study_design": study.study_design,
        "sample_size": study.sample_size or "",
        "outcome_id": outcome.outcome_id,
        "outcome_data_type": outcome.outcome_data_type,
        "outcome_name": outcome.data.outcome_name,
        "effect_measure": outcome.data.effect_measure,
        "validation_status": record.validation_status,
        "source_location": record.source_location,
        "notes": record.notes,
    }


def _required_int(value: object, field_name: str) -> int:
    parsed = _optional_int(value)
    if parsed is None:
        raise ValueError(f"{field_name}_must_be_integer")
    return parsed


def _optional_int(value: object) -> int | None:
    if value in {None, ""}:
        return None
    return int(str(value).strip())


def _required_float(value: object, field_name: str) -> float:
    parsed = _optional_float(value)
    if parsed is None:
        raise ValueError(f"{field_name}_must_be_numeric")
    return parsed


def _optional_float(value: object) -> float | None:
    if value in {None, ""}:
        return None
    return float(str(value).strip())


def _truthy(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "adjusted"}
