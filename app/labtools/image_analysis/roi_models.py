from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ROIRecord:
    roi_type: str
    label: str
    coordinates: tuple[tuple[float, float], ...] = ()
    notes: str = ""
    user_defined: bool = True
    roi_id: str = field(default_factory=lambda: f"roi_{uuid4().hex[:12]}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "roi_id": self.roi_id,
            "roi_type": self.roi_type,
            "label": self.label,
            "coordinates": [list(point) for point in self.coordinates],
            "notes": self.notes,
            "user_defined": self.user_defined,
        }


def empty_roi_placeholder(task_type: str) -> ROIRecord:
    return ROIRecord(
        roi_type="not_configured",
        label="ROI 待配置",
        coordinates=(),
        notes=f"{task_type} 任务尚未配置 ROI，本阶段不会自动识别区域。",
        user_defined=False,
    )
