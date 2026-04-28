from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class DedupDecisionType(StrEnum):
    KEEP_FIRST = "keep_first"
    KEEP_SECOND = "keep_second"
    MERGE = "merge"
    MARK_NOT_DUPLICATE = "mark_not_duplicate"
    SKIP = "skip"


class DuplicateGroupStatus(StrEnum):
    PENDING = "pending"
    RESOLVED = "resolved"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class DuplicateGroup:
    group_id: str
    records: list[dict[str, object]]
    match_reason: str
    confidence: float
    status: str = DuplicateGroupStatus.PENDING.value


@dataclass(frozen=True)
class DedupDecision:
    decision_id: str
    group_id: str
    decision: str
    selected_record_id: str = ""
    merged_record: dict[str, object] = field(default_factory=dict)
    note: str = ""
    created_at: str = ""


@dataclass(frozen=True)
class DedupResult:
    project_id: str
    original_count: int
    duplicate_group_count: int
    resolved_group_count: int
    unique_count: int
    output_path: str
    decisions_path: str
    message: str
    success: bool = True
    error_count: int = 0
    details: dict[str, object] = field(default_factory=dict)
