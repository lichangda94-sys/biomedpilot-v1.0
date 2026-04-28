from __future__ import annotations

import hashlib
from difflib import SequenceMatcher

from literature.models import DuplicateCandidateGroup, NormalizedLiteratureRecord


REASON_CONFIDENCE = {
    "doi_exact": 0.99,
    "pmid_exact": 0.98,
    "title_same_first_author": 0.9,
    "title_similar_year_close": 0.82,
}


def choose_primary_record(records: list[NormalizedLiteratureRecord]) -> NormalizedLiteratureRecord:
    if not records:
        raise ValueError("No records available to select a primary record.")

    return max(
        records,
        key=lambda record: (
            completeness_score(record),
            len(record.abstract),
            len(record.keywords),
            -len(record.source_trace),
            record.record_id,
        ),
    )


def completeness_score(record: NormalizedLiteratureRecord) -> int:
    score = 0
    score += 4 if record.title else 0
    score += 3 if record.authors else 0
    score += 3 if record.journal else 0
    score += 3 if record.year is not None else 0
    score += 4 if record.doi else 0
    score += 4 if record.pmid else 0
    score += 2 if record.abstract else 0
    score += 1 if record.keywords else 0
    score += 1 if record.language else 0
    return score


class DuplicateDetectionService:
    def identify_groups(
        self,
        project_id: str,
        records: list[NormalizedLiteratureRecord],
    ) -> list[DuplicateCandidateGroup]:
        group_state: dict[frozenset[str], dict[str, object]] = {}
        by_id = {record.record_id: record for record in records}

        self._register_exact_key_groups(
            project_id,
            records,
            key_fn=lambda record: record.doi_normalized,
            reason="doi_exact",
            state=group_state,
            by_id=by_id,
        )
        self._register_exact_key_groups(
            project_id,
            records,
            key_fn=lambda record: record.pmid_normalized,
            reason="pmid_exact",
            state=group_state,
            by_id=by_id,
        )
        self._register_exact_key_groups(
            project_id,
            records,
            key_fn=lambda record: self._title_author_key(record),
            reason="title_same_first_author",
            state=group_state,
            by_id=by_id,
        )
        self._register_similar_title_groups(project_id, records, group_state, by_id)

        groups: list[DuplicateCandidateGroup] = []
        for candidate_ids, payload in group_state.items():
            candidate_records = [by_id[record_id] for record_id in sorted(candidate_ids)]
            primary = choose_primary_record(candidate_records)
            reasons = sorted(payload["reasons"])
            confidence = max(REASON_CONFIDENCE[reason] for reason in reasons)
            digest = hashlib.sha1(
                "|".join(sorted(candidate_ids) + reasons).encode("utf-8")
            ).hexdigest()[:12]
            groups.append(
                DuplicateCandidateGroup(
                    duplicate_group_id=f"dup-{digest}",
                    project_id=project_id,
                    candidate_record_ids=sorted(candidate_ids),
                    match_reason=",".join(reasons),
                    confidence=confidence,
                    suggested_primary_record_id=primary.record_id,
                )
            )

        return sorted(groups, key=lambda group: group.duplicate_group_id)

    def _register_exact_key_groups(
        self,
        project_id: str,
        records: list[NormalizedLiteratureRecord],
        *,
        key_fn,
        reason: str,
        state: dict[frozenset[str], dict[str, object]],
        by_id: dict[str, NormalizedLiteratureRecord],
    ) -> None:
        buckets: dict[str, list[NormalizedLiteratureRecord]] = {}
        for record in records:
            key = key_fn(record)
            if not key:
                continue
            buckets.setdefault(key, []).append(record)

        for bucket in buckets.values():
            if len(bucket) < 2:
                continue
            candidate_ids = frozenset(record.record_id for record in bucket)
            self._add_group(candidate_ids, reason, state)

    def _register_similar_title_groups(
        self,
        project_id: str,
        records: list[NormalizedLiteratureRecord],
        state: dict[frozenset[str], dict[str, object]],
        by_id: dict[str, NormalizedLiteratureRecord],
    ) -> None:
        for index, left in enumerate(records):
            if not left.title_normalized or left.year_normalized is None:
                continue
            for right in records[index + 1 :]:
                if not right.title_normalized or right.year_normalized is None:
                    continue
                if abs(left.year_normalized - right.year_normalized) > 1:
                    continue
                similarity = SequenceMatcher(
                    None,
                    left.title_normalized,
                    right.title_normalized,
                ).ratio()
                if similarity >= 0.92:
                    candidate_ids = frozenset({left.record_id, right.record_id})
                    self._add_group(candidate_ids, "title_similar_year_close", state)

    def _title_author_key(self, record: NormalizedLiteratureRecord) -> str:
        if not record.title_normalized or not record.authors_normalized:
            return ""
        return f"{record.title_normalized}|{record.authors_normalized[0]}"

    def _add_group(
        self,
        candidate_ids: frozenset[str],
        reason: str,
        state: dict[frozenset[str], dict[str, object]],
    ) -> None:
        payload = state.setdefault(candidate_ids, {"reasons": set()})
        reasons: set[str] = payload["reasons"]  # type: ignore[assignment]
        reasons.add(reason)
