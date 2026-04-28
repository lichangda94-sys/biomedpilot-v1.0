from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from literature.models import (
    ExclusionReason,
    ScreeningDecision,
    ScreeningRecord,
    ScreeningStage,
)
from literature.store import LiteratureStore


DEFAULT_EXCLUSION_REASONS = [
    ExclusionReason(
        reason_code="wrong_population",
        label="Wrong Population",
        description="Population does not match review criteria.",
        applies_to_stage=ScreeningStage.TITLE_ABSTRACT_SCREENING,
    ),
    ExclusionReason(
        reason_code="wrong_intervention",
        label="Wrong Intervention",
        description="Intervention or exposure does not match review criteria.",
        applies_to_stage=ScreeningStage.TITLE_ABSTRACT_SCREENING,
    ),
    ExclusionReason(
        reason_code="wrong_study_design",
        label="Wrong Study Design",
        description="Study design is outside the target criteria.",
        applies_to_stage=ScreeningStage.TITLE_ABSTRACT_SCREENING,
    ),
    ExclusionReason(
        reason_code="no_full_text",
        label="No Full Text",
        description="Full text could not be retrieved.",
        applies_to_stage=ScreeningStage.FULL_TEXT_SCREENING,
    ),
    ExclusionReason(
        reason_code="full_text_ineligible",
        label="Full Text Ineligible",
        description="Full text review found ineligible criteria match.",
        applies_to_stage=ScreeningStage.FULL_TEXT_SCREENING,
    ),
]


class ScreeningService:
    def __init__(self, store: LiteratureStore) -> None:
        self._store = store

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "ScreeningService":
        return cls(LiteratureStore(root_dir))

    def ensure_default_exclusion_reasons(self) -> list[ExclusionReason]:
        existing = self._store.list_exclusion_reasons()
        if existing:
            return existing
        return self._store.replace_exclusion_reasons(list(DEFAULT_EXCLUSION_REASONS))

    def list_exclusion_reasons(
        self,
        *,
        stage: ScreeningStage | None = None,
    ) -> list[ExclusionReason]:
        self.ensure_default_exclusion_reasons()
        return self._store.list_exclusion_reasons(stage=stage)

    def list_screening_records(
        self,
        project_id: str,
        *,
        stage: ScreeningStage | None = None,
        decision: ScreeningDecision | None = None,
    ) -> list[ScreeningRecord]:
        return self._store.list_screening_records(
            project_id=project_id,
            stage=stage,
            decision=decision,
        )

    def generate_screening_pool(
        self,
        project_id: str,
        *,
        stage: ScreeningStage = ScreeningStage.TITLE_ABSTRACT_SCREENING,
    ) -> list[ScreeningRecord]:
        self.ensure_default_exclusion_reasons()
        if stage == ScreeningStage.TITLE_ABSTRACT_SCREENING:
            eligible_records = self._eligible_title_abstract_records(project_id)
        else:
            eligible_records = self._eligible_full_text_records(project_id)

        existing = {
            record.normalized_record_id: record
            for record in self._store.list_screening_records(
                project_id=project_id,
                stage=stage,
            )
        }
        generated: list[ScreeningRecord] = []
        for record in eligible_records:
            current = existing.get(record.record_id)
            if current is not None:
                generated.append(current)
                continue
            generated.append(
                ScreeningRecord(
                    screening_record_id=f"screen-{uuid4().hex[:12]}",
                    project_id=project_id,
                    source_record_id=record.source_record_id or record.record_id,
                    normalized_record_id=record.record_id,
                    stage=stage,
                    decision=ScreeningDecision.PENDING,
                )
            )

        return self._store.replace_screening_records(project_id, stage, generated)

    def list_pending_records(
        self,
        project_id: str,
        *,
        stage: ScreeningStage = ScreeningStage.TITLE_ABSTRACT_SCREENING,
    ) -> list[ScreeningRecord]:
        return self._store.list_screening_records(
            project_id=project_id,
            stage=stage,
            decision=ScreeningDecision.PENDING,
        )

    def submit_decision(
        self,
        screening_record_id: str,
        *,
        decision: ScreeningDecision,
        exclusion_reason_code: str = "",
        exclusion_reason_text: str = "",
        reviewer_id: str | None = None,
        notes: str = "",
    ) -> ScreeningRecord:
        record = self._store.get_screening_record(screening_record_id)
        if record is None:
            raise ValueError(f"Screening record does not exist: {screening_record_id}")
        self._validate_decision(
            stage=record.stage,
            decision=decision,
            exclusion_reason_code=exclusion_reason_code,
        )

        record.decision = decision
        record.exclusion_reason_code = (
            exclusion_reason_code if decision == ScreeningDecision.EXCLUDED else ""
        )
        record.exclusion_reason_text = (
            exclusion_reason_text if decision == ScreeningDecision.EXCLUDED else ""
        )
        record.reviewer_id = reviewer_id
        record.notes = notes
        record.decided_at = self._decision_time(decision)
        return self._store.save_screening_record(record)

    def update_decision(
        self,
        screening_record_id: str,
        *,
        decision: ScreeningDecision,
        exclusion_reason_code: str = "",
        exclusion_reason_text: str = "",
        reviewer_id: str | None = None,
        notes: str = "",
    ) -> ScreeningRecord:
        return self.submit_decision(
            screening_record_id,
            decision=decision,
            exclusion_reason_code=exclusion_reason_code,
            exclusion_reason_text=exclusion_reason_text,
            reviewer_id=reviewer_id,
            notes=notes,
        )

    def get_stage_statistics(
        self,
        project_id: str,
        *,
        stage: ScreeningStage,
    ) -> dict[str, int]:
        records = self._store.list_screening_records(project_id=project_id, stage=stage)
        counts = Counter(record.decision.value for record in records)
        return {
            "included": counts.get(ScreeningDecision.INCLUDED.value, 0),
            "excluded": counts.get(ScreeningDecision.EXCLUDED.value, 0),
            "pending": counts.get(ScreeningDecision.PENDING.value, 0),
            "maybe": counts.get(ScreeningDecision.MAYBE.value, 0),
            "total": len(records),
        }

    def generate_prisma_counts(self, project_id: str) -> dict[str, int]:
        normalized_records = self._store.list_normalized_records(project_id=project_id)
        duplicate_groups = self._store.list_duplicate_groups(project_id=project_id)
        title_stats = self.get_stage_statistics(
            project_id,
            stage=ScreeningStage.TITLE_ABSTRACT_SCREENING,
        )
        full_text_stats = self.get_stage_statistics(
            project_id,
            stage=ScreeningStage.FULL_TEXT_SCREENING,
        )
        duplicates_removed = sum(
            max(len(group.candidate_record_ids) - 1, 0)
            for group in duplicate_groups
        )
        return {
            "records_after_normalization": len(normalized_records),
            "duplicate_groups": len(duplicate_groups),
            "duplicates_removed_from_screening": duplicates_removed,
            "title_abstract_screened": title_stats["total"],
            "title_abstract_included": title_stats["included"],
            "title_abstract_excluded": title_stats["excluded"],
            "title_abstract_pending": title_stats["pending"],
            "title_abstract_maybe": title_stats["maybe"],
            "full_text_screened": full_text_stats["total"],
            "full_text_included": full_text_stats["included"],
            "full_text_excluded": full_text_stats["excluded"],
            "full_text_pending": full_text_stats["pending"],
            "full_text_maybe": full_text_stats["maybe"],
        }

    def _eligible_title_abstract_records(self, project_id: str):
        normalized_records = self._store.list_normalized_records(project_id=project_id)
        duplicate_groups = self._store.list_duplicate_groups(project_id=project_id)
        candidate_ids = {
            record_id
            for group in duplicate_groups
            for record_id in group.candidate_record_ids
        }
        allowed_group_primaries = {
            group.suggested_primary_record_id
            for group in duplicate_groups
        }
        return [
            record
            for record in normalized_records
            if record.record_id not in candidate_ids or record.record_id in allowed_group_primaries
        ]

    def _eligible_full_text_records(self, project_id: str):
        included_records = self._store.list_screening_records(
            project_id=project_id,
            stage=ScreeningStage.TITLE_ABSTRACT_SCREENING,
            decision=ScreeningDecision.INCLUDED,
        )
        normalized_by_id = {
            record.record_id: record
            for record in self._store.list_normalized_records(project_id=project_id)
        }
        return [
            normalized_by_id[record.normalized_record_id]
            for record in included_records
            if record.normalized_record_id in normalized_by_id
        ]

    def _validate_decision(
        self,
        *,
        stage: ScreeningStage,
        decision: ScreeningDecision,
        exclusion_reason_code: str,
    ) -> None:
        reasons = {
            reason.reason_code: reason
            for reason in self.ensure_default_exclusion_reasons()
        }
        if decision == ScreeningDecision.EXCLUDED:
            if not exclusion_reason_code:
                raise ValueError("Excluded screening decision requires an exclusion reason code.")
            reason = reasons.get(exclusion_reason_code)
            if reason is None:
                raise ValueError(f"Unknown exclusion reason code: {exclusion_reason_code}")
            if reason.applies_to_stage != stage:
                raise ValueError(
                    f"Exclusion reason {exclusion_reason_code} does not apply to stage {stage.value}."
                )
            return

        if exclusion_reason_code:
            raise ValueError("Only excluded decisions may carry an exclusion reason code.")

    def _decision_time(self, decision: ScreeningDecision) -> datetime | None:
        if decision == ScreeningDecision.PENDING:
            return None
        from literature.models import utc_now

        return utc_now()
