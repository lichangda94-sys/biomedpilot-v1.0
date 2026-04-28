from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.shared.feature_availability import FeatureAvailability, FeatureAvailabilityStatus


class FeatureStatus(StrEnum):
    OPEN = "已开放"
    TESTING = "测试中"
    PENDING = "待接入"
    UNAVAILABLE = "暂未开放"


@dataclass(frozen=True)
class FeatureItem:
    module: str
    name: str
    status: FeatureStatus
    description: str

    def label(self) -> str:
        return f"{self.name} · {self.status.value}"


def feature_item_from_availability(feature: FeatureAvailability) -> FeatureItem:
    status_map = {
        FeatureAvailabilityStatus.OPEN: FeatureStatus.OPEN,
        FeatureAvailabilityStatus.TESTING: FeatureStatus.TESTING,
        FeatureAvailabilityStatus.PLACEHOLDER: FeatureStatus.PENDING,
        FeatureAvailabilityStatus.UNAVAILABLE: FeatureStatus.UNAVAILABLE,
    }
    return FeatureItem(
        module=feature.module,
        name=feature.feature_name,
        status=status_map[feature.status],
        description=feature.description,
    )
