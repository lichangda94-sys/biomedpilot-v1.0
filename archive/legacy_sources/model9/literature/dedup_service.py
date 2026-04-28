from __future__ import annotations

from pathlib import Path

from literature.dedup import DuplicateDetectionService
from literature.models import DuplicateCandidateGroup, NormalizedLiteratureRecord
from literature.normalize import RecordNormalizationService
from literature.store import LiteratureStore


class NormalizationDedupService:
    def __init__(self, store: LiteratureStore) -> None:
        self._store = store
        self._normalizer = RecordNormalizationService()
        self._detector = DuplicateDetectionService()

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "NormalizationDedupService":
        return cls(LiteratureStore(root_dir))

    def normalize_project_records(self, project_id: str) -> list[NormalizedLiteratureRecord]:
        parsed_records = self._store.list_parsed_records(project_id=project_id)
        normalized_records = self._normalizer.normalize_records(parsed_records)
        return self._store.replace_normalized_records(project_id, normalized_records)

    def identify_duplicate_groups(self, project_id: str) -> list[DuplicateCandidateGroup]:
        normalized_records = self._store.list_normalized_records(project_id=project_id)
        groups = self._detector.identify_groups(project_id, normalized_records)
        return self._store.replace_duplicate_groups(project_id, groups)

    def prepare_project(self, project_id: str) -> tuple[list[NormalizedLiteratureRecord], list[DuplicateCandidateGroup]]:
        normalized_records = self.normalize_project_records(project_id)
        groups = self.identify_duplicate_groups(project_id)
        return normalized_records, groups
