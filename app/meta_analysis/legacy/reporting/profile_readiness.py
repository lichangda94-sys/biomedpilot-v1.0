from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


PROFILE_READINESS_FILENAME = "profile_readiness.json"
READINESS_DISCLAIMER = (
    "Policy readiness summaries describe structural analysis readiness. "
    "They do not mean pooled statistical analysis has been run. "
    "Advanced statistics such as NMA, HSROC, metaprop, and GLMM are not implemented here."
)


@dataclass(frozen=True)
class ProfileReadinessRow:
    profile: str
    support_status: str
    supported_now: bool
    policy_ready: bool
    unsupported: str = ""
    unimplemented: str = ""
    warnings: str = ""
    recommended_next_action: str = ""


@dataclass(frozen=True)
class ProfileReadinessDashboard:
    rows: list[ProfileReadinessRow] = field(default_factory=list)
    source_path: Path | None = None
    warning: str = ""

    @property
    def has_rows(self) -> bool:
        return bool(self.rows)


def load_project_profile_readiness(project_dir: Path) -> ProfileReadinessDashboard:
    source_path = project_dir / PROFILE_READINESS_FILENAME
    if not source_path.exists():
        return ProfileReadinessDashboard(
            source_path=source_path,
            warning="No profile policy readiness summaries available yet.",
        )
    data = json.loads(source_path.read_text(encoding="utf-8"))
    raw_rows = data.get("rows", []) if isinstance(data, dict) else []
    rows = [_row_from_mapping(row) for row in raw_rows if isinstance(row, dict)]
    return ProfileReadinessDashboard(rows=rows, source_path=source_path)


def _row_from_mapping(data: dict[str, Any]) -> ProfileReadinessRow:
    return ProfileReadinessRow(
        profile=str(data.get("profile") or data.get("method_profile") or ""),
        support_status=str(data.get("support_status") or ""),
        supported_now=bool(data.get("supported_now", False)),
        policy_ready=bool(data.get("policy_ready", False)),
        unsupported=_join_text(data.get("unsupported") or data.get("unsupported_features")),
        unimplemented=_join_text(data.get("unimplemented") or data.get("unimplemented_features")),
        warnings=_join_text(data.get("warnings")),
        recommended_next_action=str(data.get("recommended_next_action") or ""),
    )


def _join_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value)
