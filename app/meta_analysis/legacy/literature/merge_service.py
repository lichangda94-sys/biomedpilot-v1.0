from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from literature.dedup import choose_primary_record
from literature.models import DedupMergeResult, DuplicateCandidateGroup, NormalizedLiteratureRecord, ParsedLiteratureRecord
from literature.normalize import RecordNormalizationService
from literature.store import LiteratureStore


MERGE_FIELDS = (
    "title",
    "abstract",
    "authors",
    "journal",
    "year",
    "doi",
    "pmid",
    "keywords",
    "language",
)


class DedupMergeService:
    def __init__(self, store: LiteratureStore) -> None:
        self._store = store
        self._normalizer = RecordNormalizationService()

    def merge_group(self, duplicate_group_id: str) -> DedupMergeResult:
        group = self._store.get_duplicate_group(duplicate_group_id)
        if group is None:
            raise ValueError(f"Duplicate group does not exist: {duplicate_group_id}")

        candidates = [
            self._store.get_normalized_record(record_id)
            for record_id in group.candidate_record_ids
        ]
        records = [record for record in candidates if record is not None]
        if len(records) < 2:
            raise ValueError(
                f"Duplicate group requires at least two candidate records: {duplicate_group_id}"
            )

        primary = choose_primary_record(records)
        field_sources = {
            field_name: primary.record_id
            for field_name in MERGE_FIELDS
            if self._has_value(getattr(primary, field_name))
        }

        merged = replace(primary, source_trace=sorted({*primary.source_trace, primary.record_id}))
        donor_records = [record for record in records if record.record_id != primary.record_id]
        for donor in donor_records:
            for field_name in MERGE_FIELDS:
                current_value = getattr(merged, field_name)
                donor_value = getattr(donor, field_name)
                if self._has_value(current_value) or not self._has_value(donor_value):
                    continue
                merged = replace(merged, **{field_name: donor_value})
                field_sources[field_name] = donor.record_id

        merged = self._renormalize_record(
            merged,
            source_trace=sorted(set(group.candidate_record_ids)),
        )
        result = DedupMergeResult(
            merge_result_id=f"merge-{uuid4().hex[:12]}",
            duplicate_group_id=group.duplicate_group_id,
            project_id=group.project_id,
            primary_record_id=primary.record_id,
            merged_record=merged,
            merged_from_record_ids=[
                record.record_id for record in donor_records
            ],
            field_sources=field_sources,
        )
        return self._store.save_merge_result(result)

    def _renormalize_record(
        self,
        record: NormalizedLiteratureRecord,
        *,
        source_trace: list[str],
    ) -> NormalizedLiteratureRecord:
        parsed = ParsedLiteratureRecord(
            record_id=record.record_id,
            batch_id=record.batch_id,
            project_id=record.project_id,
            source=record.source,
            source_record_id=record.source_record_id,
            title=record.title,
            abstract=record.abstract,
            authors=list(record.authors),
            journal=record.journal,
            year=record.year,
            doi=record.doi,
            pmid=record.pmid,
            keywords=list(record.keywords),
            language=record.language,
            raw_payload=dict(record.raw_payload),
        )
        return replace(
            self._normalizer.normalize_record(parsed),
            source_trace=source_trace,
        )

    def _has_value(self, value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, list):
            return bool(value)
        return True
