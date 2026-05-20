from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


SURVIVAL_PACKAGE_SCHEMA_VERSION = "biomedpilot.survival_input_package.v1"
SURVIVAL_PREFLIGHT_SCHEMA_VERSION = "biomedpilot.survival_preflight.v1"
CLINICAL_PREFLIGHT_SCHEMA_VERSION = "biomedpilot.clinical_association_preflight.v1"


@dataclass(frozen=True)
class SurvivalInputPackage:
    survival_package_id: str
    input_package_id: str
    clinical_asset: dict[str, Any] | None
    expression_asset: dict[str, Any] | None
    sample_case_mapping: dict[str, str]
    time_field: str
    event_field: str
    time_unit: str
    event_coding: dict[str, Any]
    censoring_policy: str
    grouping_policy: str
    missingness_report: dict[str, Any]
    event_count: int
    sample_count: int
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    schema_version: str = SURVIVAL_PACKAGE_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        return payload
