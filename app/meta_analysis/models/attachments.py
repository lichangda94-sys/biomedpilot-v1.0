from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


ATTACHMENT_MODES = ("ignore_attachments", "link_existing_files", "copy_to_project_library")
ATTACHMENT_TYPES = ("pdf", "supplement", "extraction_sheet", "figure", "other")


@dataclass(frozen=True)
class AttachmentRecord:
    attachment_id: str
    record_id: str
    attachment_type: str
    file_path: str
    file_name: str
    file_exists: bool
    file_size: int
    checksum: str
    added_at: str
    added_by: str = "system"
    notes: str = ""


def new_attachment_id() -> str:
    return f"att-{uuid4().hex[:12]}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def attachment_to_dict(record: AttachmentRecord) -> dict[str, Any]:
    return asdict(record)


def attachment_from_dict(payload: dict[str, Any]) -> AttachmentRecord:
    return AttachmentRecord(
        attachment_id=str(payload["attachment_id"]),
        record_id=str(payload["record_id"]),
        attachment_type=str(payload.get("attachment_type", "other")),
        file_path=str(payload.get("file_path", "")),
        file_name=str(payload.get("file_name", "")),
        file_exists=bool(payload.get("file_exists", False)),
        file_size=int(payload.get("file_size", 0)),
        checksum=str(payload.get("checksum", "")),
        added_at=str(payload.get("added_at", "")),
        added_by=str(payload.get("added_by", "system")),
        notes=str(payload.get("notes", "")),
    )

