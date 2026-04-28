from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from literature.models import utc_now


class BiasJudgement(StrEnum):
    LOW = "low"
    UNCLEAR = "unclear"
    HIGH = "high"


@dataclass(slots=True)
class BiasDomainTemplate:
    tool_name: str
    domain_name: str
    description: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "tool_name": self.tool_name,
            "domain_name": self.domain_name,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "BiasDomainTemplate":
        return cls(
            tool_name=str(payload["tool_name"]),
            domain_name=str(payload["domain_name"]),
            description=str(payload.get("description", "")),
        )


@dataclass(slots=True)
class BiasRecord:
    bias_record_id: str
    project_id: str
    screening_record_id: str
    extraction_record_id: str | None
    tool_name: str
    domain_name: str
    judgement: BiasJudgement
    support_text: str = ""
    reviewer_id: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, object]:
        return {
            "bias_record_id": self.bias_record_id,
            "project_id": self.project_id,
            "screening_record_id": self.screening_record_id,
            "extraction_record_id": self.extraction_record_id,
            "tool_name": self.tool_name,
            "domain_name": self.domain_name,
            "judgement": self.judgement.value,
            "support_text": self.support_text,
            "reviewer_id": self.reviewer_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "BiasRecord":
        return cls(
            bias_record_id=str(payload["bias_record_id"]),
            project_id=str(payload["project_id"]),
            screening_record_id=str(payload["screening_record_id"]),
            extraction_record_id=(
                str(payload["extraction_record_id"])
                if payload.get("extraction_record_id") is not None
                else None
            ),
            tool_name=str(payload["tool_name"]),
            domain_name=str(payload["domain_name"]),
            judgement=BiasJudgement(str(payload["judgement"])),
            support_text=str(payload.get("support_text", "")),
            reviewer_id=(
                str(payload["reviewer_id"])
                if payload.get("reviewer_id") is not None
                else None
            ),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(slots=True)
class BiasAssessmentRow:
    screening_record_id: str
    extraction_record_id: str | None
    domain_name: str
    judgement: BiasJudgement
    support_text: str

    def to_dict(self) -> dict[str, object]:
        return {
            "screening_record_id": self.screening_record_id,
            "extraction_record_id": self.extraction_record_id,
            "domain_name": self.domain_name,
            "judgement": self.judgement.value,
            "support_text": self.support_text,
        }


@dataclass(slots=True)
class BiasAssessmentTable:
    project_id: str
    tool_name: str
    overall_judgement: BiasJudgement
    rows: list[BiasAssessmentRow] = field(default_factory=list)
