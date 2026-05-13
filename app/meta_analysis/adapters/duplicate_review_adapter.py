from __future__ import annotations

from dataclasses import dataclass
from app.meta_analysis.literature_import_core import duplicate_groups_for_records


@dataclass(frozen=True)
class DuplicateCandidateGroupResult:
    duplicate_group_id: str
    candidate_record_ids: list[str]
    match_reason: str
    confidence: float
    suggested_primary_record_id: str
    status: str = "pending"


class DuplicateReviewAdapter:
    def identify_duplicate_groups(self, *, project_id: str, records: list[dict[str, object]]) -> list[DuplicateCandidateGroupResult]:
        return [
            DuplicateCandidateGroupResult(
                duplicate_group_id=str(group.get("duplicate_group_id", "")),
                candidate_record_ids=list(group.get("candidate_record_ids", [])),
                match_reason=str(group.get("match_reason", "")),
                confidence=float(group.get("confidence", 0.0)),
                suggested_primary_record_id=str(group.get("suggested_primary_record_id", "")),
                status=str(group.get("status", "pending")),
            )
            for group in duplicate_groups_for_records(project_id, records)
        ]
