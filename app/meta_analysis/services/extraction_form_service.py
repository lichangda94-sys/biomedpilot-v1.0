from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.extraction.schema_registry import TREATMENT_EFFECT_META, list_extraction_schema_profiles
from app.meta_analysis.models.extraction import (
    BinaryOutcomeData,
    ContinuousOutcomeData,
    CorrelationOutcomeData,
    DiagnosticAccuracyOutcomeData,
    ExtractedOutcome,
    ExtractionRecord,
    ExtractionValidationResult,
    GenericEffectOutcomeData,
    OutcomeDataType,
    ProportionOutcomeData,
    StudyCharacteristics,
    new_extraction_id,
    now_utc,
)
from app.meta_analysis.services.extraction_record_storage_service import ExtractionRecordStorageService
from app.meta_analysis.services.extraction_validation_service import ExtractionValidationService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.project_contract_service import MetaProjectContractService
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


@dataclass(frozen=True)
class ExtractionDraft:
    draft_id: str
    project_id: str
    record_id: str
    form_data: dict[str, object]
    updated_at: str


@dataclass(frozen=True)
class FieldValidationSummary:
    errors_by_field: dict[str, list[str]]
    warnings_by_field: dict[str, list[str]]
    completeness_score: float
    missing_required_fields: list[str]


@dataclass(frozen=True)
class ManualExtractionEdit:
    edit_id: str
    project_id: str
    extraction_id: str
    record_id: str
    field_name: str
    before_value: str
    after_value: str
    reviewer_id: str
    note: str
    source_location: str
    used_for_formal_analysis: bool
    created_at: str


class ExtractionFormService:
    def __init__(
        self,
        *,
        storage_service: ExtractionRecordStorageService | None = None,
        validation_service: ExtractionValidationService | None = None,
        task_center: TaskCenter | None = None,
        data_center: DataCenter | None = None,
        audit_log: MetaAuditLogService | None = None,
        project_contract: MetaProjectContractService | None = None,
    ) -> None:
        self._task_center = task_center
        self._data_center = data_center
        self._audit_log = audit_log or MetaAuditLogService()
        self._project_contract = project_contract
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

    def build_extraction_record_with_outcomes(
        self,
        *,
        project_id: str,
        form_data: dict[str, object],
        outcome_rows: list[dict[str, object]],
    ) -> ExtractionRecord:
        base = self.build_extraction_record(project_id=project_id, form_data={**form_data, **(outcome_rows[0] if outcome_rows else {})})
        outcomes = [
            ExtractedOutcome(
                outcome_id=str(row.get("outcome_id") or f"out-{uuid4().hex[:12]}"),
                outcome_data_type=str(row.get("outcome_data_type") or form_data.get("outcome_data_type") or OutcomeDataType.BINARY.value),
                data=self._outcome_data(
                    outcome_type=str(row.get("outcome_data_type") or form_data.get("outcome_data_type") or OutcomeDataType.BINARY.value),
                    form_data={**form_data, **row},
                ),
            )
            for row in outcome_rows
        ]
        return ExtractionRecord(
            extraction_id=base.extraction_id,
            project_id=base.project_id,
            record_id=base.record_id,
            study_id=base.study_id,
            reviewer_id=base.reviewer_id,
            profile_type=base.profile_type,
            study_characteristics=base.study_characteristics,
            outcomes=outcomes or base.outcomes,
            notes=base.notes,
            source_location=base.source_location,
            validation_status=base.validation_status,
            created_at=base.created_at,
            updated_at=base.updated_at,
        )

    def save_draft(self, project_dir: Path, *, project_id: str, record_id: str, form_data: dict[str, object], draft_id: str | None = None) -> Path:
        project_dir = project_dir.expanduser().resolve()
        output_path = project_dir / "extraction" / "drafts" / f"{draft_id or f'draft-{uuid4().hex[:12]}'}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = ExtractionDraft(
            draft_id=output_path.stem,
            project_id=project_id,
            record_id=record_id,
            form_data=dict(form_data),
            updated_at=now_utc(),
        )
        output_path.write_text(json.dumps(payload.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path

    def load_drafts(self, project_dir: Path) -> list[ExtractionDraft]:
        drafts: list[ExtractionDraft] = []
        for path in sorted((project_dir.expanduser().resolve() / "extraction" / "drafts").glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            drafts.append(ExtractionDraft(**payload))
        return drafts

    def load_extraction_records(self, project_dir: Path) -> list[ExtractionRecord]:
        return self._storage_service.load_extraction_records(project_dir)

    def delete_draft(self, project_dir: Path, draft_id: str) -> bool:
        path = project_dir.expanduser().resolve() / "extraction" / "drafts" / f"{draft_id}.json"
        if not path.exists():
            return False
        path.unlink()
        return True

    def copy_previous_study_characteristics(self, project_dir: Path) -> dict[str, object]:
        records = self._storage_service.load_extraction_records(project_dir)
        if not records:
            return {}
        return {
            key: value
            for key, value in records[-1].study_characteristics.__dict__.items()
            if key != "notes"
        }

    def required_field_metadata(self, profile_type: str = TREATMENT_EFFECT_META) -> dict[str, list[str]]:
        return {
            "study_characteristics": ["first_author", "year", "sample_size"],
            "record": ["record_id", "study_id", "reviewer_id", "profile_type"],
            "outcome_common": ["outcome_name", "effect_measure"],
        }

    def field_validation_summary(self, record: ExtractionRecord) -> FieldValidationSummary:
        validation = self._validation_service.validate_extraction_record(record)
        errors = _field_map(validation.errors)
        warnings = _field_map(validation.warnings)
        required = self.required_field_metadata(record.profile_type)
        missing = _missing_required(record, required)
        return FieldValidationSummary(
            errors_by_field=errors,
            warnings_by_field=warnings,
            completeness_score=self.extraction_completeness_score(record),
            missing_required_fields=missing,
        )

    def extraction_completeness_score(self, record: ExtractionRecord) -> float:
        required = self.required_field_metadata(record.profile_type)
        fields = [
            ("record", field_name, getattr(record, field_name))
            for field_name in required["record"]
        ]
        fields.extend(
            ("study_characteristics", field_name, getattr(record.study_characteristics, field_name))
            for field_name in required["study_characteristics"]
        )
        for outcome in record.outcomes:
            fields.extend(("outcome", field_name, getattr(outcome.data, field_name, "")) for field_name in required["outcome_common"])
        if not fields:
            return 1.0
        filled = [value for _group, _field, value in fields if value not in ("", None, [])]
        return len(filled) / len(fields)

    def pre_export_completeness_check(self, project_dir: Path) -> dict[str, object]:
        records = self._storage_service.load_extraction_records(project_dir)
        incomplete = [
            {"extraction_id": record.extraction_id, "score": self.extraction_completeness_score(record)}
            for record in records
            if self.extraction_completeness_score(record) < 1.0
        ]
        return {
            "record_count": len(records),
            "incomplete_records": incomplete,
            "ready_for_export": not incomplete,
            "warnings": [f"extraction_record_incomplete:{item['extraction_id']}" for item in incomplete],
        }

    def record_manual_edit(
        self,
        project_dir: Path,
        *,
        extraction_id: str,
        record_id: str,
        field_name: str,
        before_value: object,
        after_value: object,
        reviewer_id: str = "",
        note: str = "",
        source_location: str = "",
        used_for_formal_analysis: bool = False,
    ) -> Path:
        project_dir = project_dir.expanduser().resolve()
        path = project_dir / "extraction" / "manual_edits_log.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        edit = ManualExtractionEdit(
            edit_id=f"edit-{uuid4().hex[:12]}",
            project_id=project_dir.name,
            extraction_id=extraction_id,
            record_id=record_id,
            field_name=field_name,
            before_value=str(before_value),
            after_value=str(after_value),
            reviewer_id=reviewer_id,
            note=note,
            source_location=source_location,
            used_for_formal_analysis=used_for_formal_analysis,
            created_at=now_utc(),
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(edit), ensure_ascii=False, sort_keys=True) + "\n")
        if self._data_center is not None:
            self._data_center.register_asset(
                project_id=project_dir.name,
                module="meta_analysis",
                data_type="extraction_manual_edits_log",
                source_path=str(project_dir / "extraction" / "extraction_records.json"),
                output_path=str(path),
                status="testing",
            )
        self._audit_log.record_event(
            project_dir,
            event_type="extraction_updated",
            project_id=project_dir.name,
            target_type="manual_extraction_edit",
            target_id=edit.edit_id,
            source_path=source_location,
            output_path=str(path),
            summary=f"Manual extraction edit recorded for {field_name}.",
            details={
                "extraction_id": extraction_id,
                "record_id": record_id,
                "field_name": field_name,
                "used_for_formal_analysis": used_for_formal_analysis,
            },
        )
        if self._project_contract is not None:
            self._project_contract.write_project_manifests(project_dir)
        return path

    def load_manual_edits(self, project_dir: Path) -> list[ManualExtractionEdit]:
        path = project_dir.expanduser().resolve() / "extraction" / "manual_edits_log.jsonl"
        if not path.exists():
            return []
        edits: list[ManualExtractionEdit] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            edits.append(
                ManualExtractionEdit(
                    edit_id=str(payload.get("edit_id", "")),
                    project_id=str(payload.get("project_id", "")),
                    extraction_id=str(payload.get("extraction_id", "")),
                    record_id=str(payload.get("record_id", "")),
                    field_name=str(payload.get("field_name", "")),
                    before_value=str(payload.get("before_value", "")),
                    after_value=str(payload.get("after_value", "")),
                    reviewer_id=str(payload.get("reviewer_id", "")),
                    note=str(payload.get("note", "")),
                    source_location=str(payload.get("source_location", "")),
                    used_for_formal_analysis=bool(payload.get("used_for_formal_analysis", False)),
                    created_at=str(payload.get("created_at", "")),
                )
            )
        return edits

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

    def _outcome_data(
        self,
        *,
        outcome_type: str,
        form_data: dict[str, object],
    ) -> (
        BinaryOutcomeData
        | ContinuousOutcomeData
        | GenericEffectOutcomeData
        | DiagnosticAccuracyOutcomeData
        | ProportionOutcomeData
        | CorrelationOutcomeData
    ):
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
        if outcome_type == OutcomeDataType.DIAGNOSTIC_ACCURACY.value:
            return DiagnosticAccuracyOutcomeData(
                outcome_name=str(form_data.get("outcome_name", "")),
                effect_measure=str(form_data.get("effect_measure") or "DOR"),
                tp=_required_int(form_data.get("tp"), "tp"),
                fp=_required_int(form_data.get("fp"), "fp"),
                fn=_required_int(form_data.get("fn"), "fn"),
                tn=_required_int(form_data.get("tn"), "tn"),
                sensitivity=_optional_float(form_data.get("sensitivity")),
                specificity=_optional_float(form_data.get("specificity")),
                cutoff=str(form_data.get("cutoff", "")),
                index_test=str(form_data.get("index_test", "")),
                reference_standard=str(form_data.get("reference_standard", "")),
                notes=str(form_data.get("outcome_notes", "")),
            )
        if outcome_type == OutcomeDataType.PROPORTION.value:
            return ProportionOutcomeData(
                outcome_name=str(form_data.get("outcome_name", "")),
                effect_measure=str(form_data.get("effect_measure") or "PREVALENCE"),
                events=_required_int(form_data.get("events"), "events"),
                total=_required_int(form_data.get("total"), "total"),
                population_source=str(form_data.get("population_source", "")),
                diagnostic_criteria=str(form_data.get("diagnostic_criteria", "")),
                timepoint=str(form_data.get("timepoint", "")),
                subgroup=str(form_data.get("subgroup", "")),
                notes=str(form_data.get("outcome_notes", "")),
            )
        if outcome_type == OutcomeDataType.CORRELATION.value:
            return CorrelationOutcomeData(
                outcome_name=str(form_data.get("outcome_name", "")),
                effect_measure=str(form_data.get("effect_measure") or "CORRELATION"),
                r=_required_float(form_data.get("r"), "r"),
                sample_size=_required_int(form_data.get("sample_size"), "sample_size"),
                correlation_type=str(form_data.get("correlation_type", "")),
                p_value=_optional_float(form_data.get("p_value")),
                variable_x=str(form_data.get("variable_x", "")),
                variable_y=str(form_data.get("variable_y", "")),
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


def _field_map(messages: list[str]) -> dict[str, list[str]]:
    mapped: dict[str, list[str]] = {}
    for message in messages:
        if message.startswith("missing_required_study_field:"):
            field = message.split(":", 1)[-1]
        elif message == "outcome_name_required":
            field = "outcome_name"
        elif message.startswith("unsupported_effect_measure"):
            field = "effect_measure"
        elif message.endswith("_must_be_integer"):
            field = message.removesuffix("_must_be_integer")
        elif message.endswith("_must_be_numeric"):
            field = message.removesuffix("_must_be_numeric")
        elif message.endswith("_must_be_positive"):
            field = message.removesuffix("_must_be_positive")
        elif message.endswith("_cannot_be_negative"):
            field = message.removesuffix("_cannot_be_negative")
        else:
            field = message.split(":", 1)[-1] if ":" in message else message
        mapped.setdefault(field, []).append(message)
    return mapped


def _missing_required(record: ExtractionRecord, required: dict[str, list[str]]) -> list[str]:
    missing: list[str] = []
    for field_name in required["record"]:
        if getattr(record, field_name) in ("", None, []):
            missing.append(field_name)
    for field_name in required["study_characteristics"]:
        if getattr(record.study_characteristics, field_name) in ("", None, []):
            missing.append(field_name)
    for outcome in record.outcomes:
        for field_name in required["outcome_common"]:
            if getattr(outcome.data, field_name, "") in ("", None, []):
                missing.append(field_name)
    return missing
