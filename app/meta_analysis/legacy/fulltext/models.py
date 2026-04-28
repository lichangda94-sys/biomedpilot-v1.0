from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from literature.models import utc_now


class AvailabilityStatus(StrEnum):
    NOT_ADDED = "not_added"
    AVAILABLE = "available"
    MISSING = "missing"
    EXCLUDED_UNAVAILABLE = "excluded_unavailable"


@dataclass(slots=True)
class FullTextRecord:
    fulltext_record_id: str
    project_id: str
    screening_record_id: str
    normalized_record_id: str
    file_name: str = ""
    file_path: str = ""
    file_type: str = ""
    availability_status: AvailabilityStatus = AvailabilityStatus.NOT_ADDED
    import_method: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, object]:
        return {
            "fulltext_record_id": self.fulltext_record_id,
            "project_id": self.project_id,
            "screening_record_id": self.screening_record_id,
            "normalized_record_id": self.normalized_record_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "availability_status": self.availability_status.value,
            "import_method": self.import_method,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "FullTextRecord":
        return cls(
            fulltext_record_id=str(payload["fulltext_record_id"]),
            project_id=str(payload["project_id"]),
            screening_record_id=str(payload["screening_record_id"]),
            normalized_record_id=str(payload["normalized_record_id"]),
            file_name=str(payload.get("file_name", "")),
            file_path=str(payload.get("file_path", "")),
            file_type=str(payload.get("file_type", "")),
            availability_status=AvailabilityStatus(
                str(payload.get("availability_status", AvailabilityStatus.NOT_ADDED.value))
            ),
            import_method=str(payload.get("import_method", "")),
            notes=str(payload.get("notes", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
            updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        )
