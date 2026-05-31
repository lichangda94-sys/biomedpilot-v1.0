from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from app.labtools.image_analysis.image_models import utc_timestamp


@dataclass(frozen=True)
class ImageAnalysisAuditRecord:
    event_type: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_timestamp)
    audit_id: str = field(default_factory=lambda: f"image_audit_{uuid4().hex[:12]}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "event_type": self.event_type,
            "message": self.message,
            "created_at": self.created_at,
            "details": dict(self.details),
        }
