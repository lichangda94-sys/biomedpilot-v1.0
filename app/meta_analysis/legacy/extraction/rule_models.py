from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from literature.models import utc_now


class RuleTargetType(StrEnum):
    EXTRACTION_RECORD = "extraction_record"
    OUTCOME_RECORD = "outcome_record"


class RuleCheckType(StrEnum):
    REQUIRED_FIELD = "required_field"
    NUMERIC_RANGE = "numeric_range"
    ALLOWED_VALUES = "allowed_values"


class RuleSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class RuleEvaluationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class ExtractionRule:
    rule_id: str
    project_id: str
    target_type: RuleTargetType
    check_type: RuleCheckType
    field_name: str
    label: str = ""
    severity: RuleSeverity = RuleSeverity.ERROR
    enabled: bool = True
    parameters: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "project_id": self.project_id,
            "target_type": self.target_type.value,
            "check_type": self.check_type.value,
            "field_name": self.field_name,
            "label": self.label,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "parameters": dict(self.parameters),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExtractionRule":
        return cls(
            rule_id=str(payload["rule_id"]),
            project_id=str(payload["project_id"]),
            target_type=RuleTargetType(str(payload["target_type"])),
            check_type=RuleCheckType(str(payload["check_type"])),
            field_name=str(payload["field_name"]),
            label=str(payload.get("label", "")),
            severity=RuleSeverity(str(payload.get("severity", RuleSeverity.ERROR.value))),
            enabled=bool(payload.get("enabled", True)),
            parameters=dict(payload.get("parameters", {})),
            notes=str(payload.get("notes", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )


@dataclass(slots=True)
class RuleEvaluationResult:
    result_id: str
    rule_id: str
    project_id: str
    target_type: RuleTargetType
    target_id: str
    status: RuleEvaluationStatus
    message: str = ""
    severity: RuleSeverity = RuleSeverity.ERROR
    checked_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "rule_id": self.rule_id,
            "project_id": self.project_id,
            "target_type": self.target_type.value,
            "target_id": self.target_id,
            "status": self.status.value,
            "message": self.message,
            "severity": self.severity.value,
            "checked_at": self.checked_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RuleEvaluationResult":
        return cls(
            result_id=str(payload["result_id"]),
            rule_id=str(payload["rule_id"]),
            project_id=str(payload["project_id"]),
            target_type=RuleTargetType(str(payload["target_type"])),
            target_id=str(payload["target_id"]),
            status=RuleEvaluationStatus(str(payload["status"])),
            message=str(payload.get("message", "")),
            severity=RuleSeverity(str(payload.get("severity", RuleSeverity.ERROR.value))),
            checked_at=datetime.fromisoformat(str(payload["checked_at"])),
        )
