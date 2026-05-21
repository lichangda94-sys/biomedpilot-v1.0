from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


PLOT_ARTIFACT_SCHEMA_VERSION = "biomedpilot.plot_artifact.v1"
PLOT_TYPES = {"volcano_plot", "deg_heatmap", "ora_barplot", "ora_dotplot", "correlation_scatter", "km_plot", "km_curve"}


@dataclass(frozen=True)
class PlotArtifact:
    plot_id: str
    plot_type: str
    source_result_id: str
    source_result_semantics: str
    plot_semantics: str = ""
    plot_artifact_scope: str = "inherited_semantics_plot"
    input_package_id: str = ""
    task_run_id: str = ""
    parameters_manifest: dict[str, Any] = field(default_factory=dict)
    plot_spec_artifact: dict[str, Any] = field(default_factory=dict)
    image_artifacts: tuple[dict[str, Any], ...] = ()
    table_artifacts: tuple[dict[str, Any], ...] = ()
    engine_name: str = "biomedpilot_plot_spec"
    engine_version: str = "0.1.0"
    dependency_snapshot: dict[str, Any] = field(default_factory=lambda: {"matplotlib": {"available": False, "reason": "not_required_for_spec_only"}})
    warnings: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    schema_version: str = PLOT_ARTIFACT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["image_artifacts"] = [dict(item) for item in self.image_artifacts]
        payload["table_artifacts"] = [dict(item) for item in self.table_artifacts]
        payload["warnings"] = list(self.warnings)
        payload["blockers"] = list(self.blockers)
        return payload
