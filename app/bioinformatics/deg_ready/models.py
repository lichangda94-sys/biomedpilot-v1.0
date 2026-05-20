from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


DEG_READY_SCHEMA_VERSION = "biomedpilot.deg_ready_package.v1"
DEG_PREFLIGHT_SCHEMA_VERSION = "biomedpilot.deg_formal_preflight.v1"


@dataclass(frozen=True)
class DegReadyPackage:
    deg_ready_package_id: str
    source_input_package_id: str
    matrix_asset: dict[str, Any] | None
    sample_metadata_asset: dict[str, Any] | None
    group_design_asset: dict[str, Any] | None
    feature_annotation_asset: dict[str, Any] | None
    value_type: str
    gene_id_type: str
    sample_alignment_status: dict[str, Any]
    gene_mapping_status: dict[str, Any]
    allowed_deg_methods: tuple[str, ...]
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    schema_version: str = DEG_READY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["allowed_deg_methods"] = list(self.allowed_deg_methods)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        return payload
