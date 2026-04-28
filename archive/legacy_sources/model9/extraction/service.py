from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from extraction.models import ExtractionRecord, FieldSourceTrace, OutcomeRecord, OutcomeType
from extraction.store import ExtractionStore
from literature.models import NormalizedLiteratureRecord, ScreeningDecision, ScreeningStage
from literature.store import LiteratureStore


class ExtractionService:
    def __init__(
        self,
        literature_store: LiteratureStore,
        extraction_store: ExtractionStore,
    ) -> None:
        self._literature_store = literature_store
        self._extraction_store = extraction_store

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "ExtractionService":
        return cls(LiteratureStore(root_dir), ExtractionStore(root_dir))

    def generate_extraction_pool(
        self,
        project_id: str,
        *,
        source_stage: ScreeningStage | None = None,
    ) -> list[ExtractionRecord]:
        stage = self._resolve_source_stage(project_id, source_stage=source_stage)
        included_records = self._literature_store.list_screening_records(
            project_id=project_id,
            stage=stage,
            decision=ScreeningDecision.INCLUDED,
        )
        normalized_map = {
            record.record_id: record
            for record in self._literature_store.list_normalized_records(project_id=project_id)
        }
        existing = {
            record.normalized_record_id: record
            for record in self._extraction_store.list_extraction_records(project_id=project_id)
        }
        generated: list[ExtractionRecord] = []
        for screening_record in included_records:
            normalized_record = normalized_map.get(screening_record.normalized_record_id)
            if normalized_record is None:
                continue
            current = existing.get(screening_record.normalized_record_id)
            if current is not None:
                generated.append(current)
                continue
            generated.append(
                ExtractionRecord(
                    extraction_record_id=f"extr-{uuid4().hex[:12]}",
                    project_id=project_id,
                    screening_record_id=screening_record.screening_record_id,
                    normalized_record_id=normalized_record.record_id,
                    study_title=normalized_record.title,
                )
            )
        for record in generated:
            self._extraction_store.save_extraction_record(record)
        return generated

    def create_extraction_record(
        self,
        project_id: str,
        screening_record_id: str,
        normalized_record_id: str,
        **fields: object,
    ) -> ExtractionRecord:
        record = ExtractionRecord(
            extraction_record_id=f"extr-{uuid4().hex[:12]}",
            project_id=project_id,
            screening_record_id=screening_record_id,
            normalized_record_id=normalized_record_id,
            **fields,
        )
        return self._extraction_store.save_extraction_record(record)

    def update_extraction_record(
        self,
        extraction_record_id: str,
        **fields: object,
    ) -> ExtractionRecord:
        record = self._extraction_store.get_extraction_record(extraction_record_id)
        if record is None:
            raise ValueError(f"Extraction record does not exist: {extraction_record_id}")
        for key, value in fields.items():
            setattr(record, key, value)
        record.touch()
        return self._extraction_store.save_extraction_record(record)

    def create_outcome_record(
        self,
        extraction_record_id: str,
        outcome_name: str,
        outcome_type: OutcomeType,
        **fields: object,
    ) -> OutcomeRecord:
        if self._extraction_store.get_extraction_record(extraction_record_id) is None:
            raise ValueError(f"Extraction record does not exist: {extraction_record_id}")
        record = OutcomeRecord(
            outcome_record_id=f"outc-{uuid4().hex[:12]}",
            extraction_record_id=extraction_record_id,
            outcome_name=outcome_name,
            outcome_type=outcome_type,
            **fields,
        )
        self._validate_outcome_record(record)
        return self._extraction_store.save_outcome_record(record)

    def update_outcome_record(
        self,
        outcome_record_id: str,
        **fields: object,
    ) -> OutcomeRecord:
        record = self._extraction_store.get_outcome_record(outcome_record_id)
        if record is None:
            raise ValueError(f"Outcome record does not exist: {outcome_record_id}")
        for key, value in fields.items():
            setattr(record, key, value)
        self._validate_outcome_record(record)
        record.touch()
        return self._extraction_store.save_outcome_record(record)

    def replace_field_sources(
        self,
        linked_object_id: str,
        records: list[FieldSourceTrace],
    ) -> list[FieldSourceTrace]:
        return self._extraction_store.replace_field_source_traces(linked_object_id, records)

    def list_field_source_traces(
        self,
        linked_object_id: str,
    ) -> list[FieldSourceTrace]:
        return self._extraction_store.list_field_source_traces(
            linked_object_id=linked_object_id
        )

    def list_extraction_records(self, project_id: str) -> list[ExtractionRecord]:
        return self._extraction_store.list_extraction_records(project_id=project_id)

    def list_outcome_records(self, extraction_record_id: str) -> list[OutcomeRecord]:
        return self._extraction_store.list_outcome_records(
            extraction_record_id=extraction_record_id
        )

    def _resolve_source_stage(
        self,
        project_id: str,
        *,
        source_stage: ScreeningStage | None,
    ) -> ScreeningStage:
        if source_stage is not None:
            return source_stage
        full_text_included = self._literature_store.list_screening_records(
            project_id=project_id,
            stage=ScreeningStage.FULL_TEXT_SCREENING,
            decision=ScreeningDecision.INCLUDED,
        )
        if full_text_included:
            return ScreeningStage.FULL_TEXT_SCREENING
        raise ValueError(
            "No full_text_screening included records found; pass source_stage=title_abstract_screening for development flow."
        )

    def _validate_outcome_record(self, record: OutcomeRecord) -> None:
        if record.outcome_type == OutcomeType.BINARY:
            has_ns = record.group_a_n is not None and record.group_b_n is not None
            has_events = record.events_a is not None and record.events_b is not None
            if not (has_ns or has_events):
                raise ValueError(
                    "Binary outcome requires group sample sizes or event counts for both groups."
                )
            return

        if record.outcome_type == OutcomeType.CONTINUOUS:
            required = (
                record.group_a_n is not None
                and record.group_b_n is not None
                and record.mean_a is not None
                and record.mean_b is not None
                and record.sd_a is not None
                and record.sd_b is not None
            )
            if not required:
                raise ValueError(
                    "Continuous outcome requires n, mean, and sd for both groups."
                )
            return

        if record.outcome_type == OutcomeType.TIME_TO_EVENT:
            required = (
                record.hr is not None
                and record.ci_lower is not None
                and record.ci_upper is not None
            )
            if not required:
                raise ValueError(
                    "Time-to-event outcome requires hr and confidence interval bounds."
                )

    def seed_study_title_from_normalized(
        self,
        normalized_record: NormalizedLiteratureRecord,
    ) -> str:
        return normalized_record.title
