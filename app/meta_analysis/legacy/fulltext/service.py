from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fulltext.models import AvailabilityStatus, FullTextRecord
from fulltext.store import FullTextStore
from literature.store import LiteratureStore


class FullTextService:
    def __init__(
        self,
        literature_store: LiteratureStore,
        fulltext_store: FullTextStore,
    ) -> None:
        self._literature_store = literature_store
        self._fulltext_store = fulltext_store

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "FullTextService":
        return cls(LiteratureStore(root_dir), FullTextStore(root_dir))

    def attach_file(
        self,
        screening_record_id: str,
        *,
        file_name: str,
        file_path: str,
        file_type: str = "",
        import_method: str = "",
        notes: str = "",
    ) -> FullTextRecord:
        screening_record = self._require_screening_record(screening_record_id)
        record = self._fulltext_store.get_by_screening_record(screening_record_id)
        if record is None:
            record = FullTextRecord(
                fulltext_record_id=f"ftxt-{uuid4().hex[:12]}",
                project_id=screening_record.project_id,
                screening_record_id=screening_record.screening_record_id,
                normalized_record_id=screening_record.normalized_record_id,
            )
        record.file_name = file_name
        record.file_path = file_path
        record.file_type = file_type or Path(file_name).suffix.lstrip(".").lower()
        record.import_method = import_method
        record.notes = notes
        record.availability_status = AvailabilityStatus.AVAILABLE
        record.touch()
        return self._fulltext_store.save_record(record)

    def list_fulltext_records(self, project_id: str) -> list[FullTextRecord]:
        return self._fulltext_store.list_records(project_id=project_id)

    def update_status(
        self,
        fulltext_record_id: str,
        *,
        availability_status: AvailabilityStatus,
        notes: str = "",
    ) -> FullTextRecord:
        record = self._fulltext_store.get_record(fulltext_record_id)
        if record is None:
            raise ValueError(f"Full-text record does not exist: {fulltext_record_id}")
        record.availability_status = availability_status
        record.notes = notes
        record.touch()
        return self._fulltext_store.save_record(record)

    def get_by_screening_record(self, screening_record_id: str) -> FullTextRecord | None:
        return self._fulltext_store.get_by_screening_record(screening_record_id)

    def _require_screening_record(self, screening_record_id: str):
        record = self._literature_store.get_screening_record(screening_record_id)
        if record is None:
            raise ValueError(f"Screening record does not exist: {screening_record_id}")
        return record
