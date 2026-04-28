from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from literature.models import utc_now


class OutcomeType(StrEnum):
    BINARY = "binary"
    CONTINUOUS = "continuous"
    TIME_TO_EVENT = "time_to_event"


@dataclass(slots=True)
class ExtractionRecord:
    extraction_record_id: str
    project_id: str
    screening_record_id: str
    normalized_record_id: str
    study_title: str = ""
    study_design: str = ""
    population: str = ""
    condition: str = ""
    intervention: str = ""
    comparator: str = ""
    sample_size_total: int | None = None
    follow_up: str = ""
    country: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, object]:
        return {
            "extraction_record_id": self.extraction_record_id,
            "project_id": self.project_id,
            "screening_record_id": self.screening_record_id,
            "normalized_record_id": self.normalized_record_id,
            "study_title": self.study_title,
            "study_design": self.study_design,
            "population": self.population,
            "condition": self.condition,
            "intervention": self.intervention,
            "comparator": self.comparator,
            "sample_size_total": self.sample_size_total,
            "follow_up": self.follow_up,
            "country": self.country,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ExtractionRecord":
        return cls(
            extraction_record_id=str(payload["extraction_record_id"]),
            project_id=str(payload["project_id"]),
            screening_record_id=str(payload["screening_record_id"]),
            normalized_record_id=str(payload["normalized_record_id"]),
            study_title=str(payload.get("study_title", "")),
            study_design=str(payload.get("study_design", "")),
            population=str(payload.get("population", "")),
            condition=str(payload.get("condition", "")),
            intervention=str(payload.get("intervention", "")),
            comparator=str(payload.get("comparator", "")),
            sample_size_total=payload.get("sample_size_total"),  # type: ignore[arg-type]
            follow_up=str(payload.get("follow_up", "")),
            country=str(payload.get("country", "")),
            notes=str(payload.get("notes", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(slots=True)
class OutcomeRecord:
    outcome_record_id: str
    extraction_record_id: str
    outcome_name: str
    outcome_type: OutcomeType
    metric_hint: str = ""
    timepoint: str = ""
    group_a_label: str = ""
    group_b_label: str = ""
    group_a_n: int | None = None
    group_b_n: int | None = None
    events_a: int | None = None
    events_b: int | None = None
    mean_a: float | None = None
    mean_b: float | None = None
    sd_a: float | None = None
    sd_b: float | None = None
    hr: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    p_value: float | None = None
    notes: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, object]:
        return {
            "outcome_record_id": self.outcome_record_id,
            "extraction_record_id": self.extraction_record_id,
            "outcome_name": self.outcome_name,
            "outcome_type": self.outcome_type.value,
            "metric_hint": self.metric_hint,
            "timepoint": self.timepoint,
            "group_a_label": self.group_a_label,
            "group_b_label": self.group_b_label,
            "group_a_n": self.group_a_n,
            "group_b_n": self.group_b_n,
            "events_a": self.events_a,
            "events_b": self.events_b,
            "mean_a": self.mean_a,
            "mean_b": self.mean_b,
            "sd_a": self.sd_a,
            "sd_b": self.sd_b,
            "hr": self.hr,
            "ci_lower": self.ci_lower,
            "ci_upper": self.ci_upper,
            "p_value": self.p_value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "OutcomeRecord":
        return cls(
            outcome_record_id=str(payload["outcome_record_id"]),
            extraction_record_id=str(payload["extraction_record_id"]),
            outcome_name=str(payload["outcome_name"]),
            outcome_type=OutcomeType(str(payload["outcome_type"])),
            metric_hint=str(payload.get("metric_hint", "")),
            timepoint=str(payload.get("timepoint", "")),
            group_a_label=str(payload.get("group_a_label", "")),
            group_b_label=str(payload.get("group_b_label", "")),
            group_a_n=payload.get("group_a_n"),  # type: ignore[arg-type]
            group_b_n=payload.get("group_b_n"),  # type: ignore[arg-type]
            events_a=payload.get("events_a"),  # type: ignore[arg-type]
            events_b=payload.get("events_b"),  # type: ignore[arg-type]
            mean_a=payload.get("mean_a"),  # type: ignore[arg-type]
            mean_b=payload.get("mean_b"),  # type: ignore[arg-type]
            sd_a=payload.get("sd_a"),  # type: ignore[arg-type]
            sd_b=payload.get("sd_b"),  # type: ignore[arg-type]
            hr=payload.get("hr"),  # type: ignore[arg-type]
            ci_lower=payload.get("ci_lower"),  # type: ignore[arg-type]
            ci_upper=payload.get("ci_upper"),  # type: ignore[arg-type]
            p_value=payload.get("p_value"),  # type: ignore[arg-type]
            notes=str(payload.get("notes", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(slots=True)
class FieldSourceTrace:
    source_field_name: str
    source_page: int | None
    source_text_snippet: str
    linked_object_type: str
    linked_object_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_field_name": self.source_field_name,
            "source_page": self.source_page,
            "source_text_snippet": self.source_text_snippet,
            "linked_object_type": self.linked_object_type,
            "linked_object_id": self.linked_object_id,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "FieldSourceTrace":
        return cls(
            source_field_name=str(payload["source_field_name"]),
            source_page=payload.get("source_page"),  # type: ignore[arg-type]
            source_text_snippet=str(payload.get("source_text_snippet", "")),
            linked_object_type=str(payload["linked_object_type"]),
            linked_object_id=str(payload["linked_object_id"]),
        )
