from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ANALYSIS_INPUT_SCHEMA_VERSION = "biomedpilot.analysis_input_package.v2"
RESOLVER_SCHEMA_VERSION = "biomedpilot.analysis_input_resolver.v1"

PACKAGE_TYPES = {
    "deg_recompute",
    "deg_imported_result",
    "enrichment_from_deg",
    "gsea_preranked",
    "correlation_expression",
    "immune_score_linkage",
    "tcga_clinical_survival_preflight",
}


@dataclass(frozen=True)
class AnalysisAssetRef:
    asset_id: str = ""
    asset_role: str = ""
    asset_type: str = ""
    repository: str = ""
    path: str = ""
    validation_status: str = ""

    @classmethod
    def from_asset(cls, asset: dict[str, Any] | None, role: str = "") -> "AnalysisAssetRef | None":
        if not isinstance(asset, dict):
            return None
        return cls(
            asset_id=str(asset.get("asset_id") or ""),
            asset_role=role or str(asset.get("asset_role") or ""),
            asset_type=str(asset.get("asset_type") or ""),
            repository=str(asset.get("repository") or ""),
            path=str(asset.get("path") or asset.get("file_path") or ""),
            validation_status=str(asset.get("validation_status") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnalysisInputPackage:
    input_package_id: str
    package_type: str
    source_dataset_id: str = ""
    source_repository_manifest: str = ""
    expression_asset: AnalysisAssetRef | None = None
    sample_metadata_asset: AnalysisAssetRef | None = None
    group_design_asset: AnalysisAssetRef | None = None
    feature_annotation_asset: AnalysisAssetRef | None = None
    clinical_asset: AnalysisAssetRef | None = None
    imported_result_asset: AnalysisAssetRef | None = None
    value_type: str = "unknown"
    gene_id_type: str = "unknown"
    allowed_downstream_tasks: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    schema_version: str = ANALYSIS_INPUT_SCHEMA_VERSION
    status: str = "blocked"
    task_semantics: str = "config_only"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "expression_asset",
            "sample_metadata_asset",
            "group_design_asset",
            "feature_annotation_asset",
            "clinical_asset",
            "imported_result_asset",
        ):
            if payload[key] is None:
                payload[key] = None
        payload["allowed_downstream_tasks"] = list(self.allowed_downstream_tasks)
        payload["blockers"] = list(self.blockers)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True)
class AnalysisInputResolverResult:
    project_root: str
    packages: tuple[AnalysisInputPackage, ...]
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    repository_manifest_path: str = ""
    registry_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    schema_version: str = RESOLVER_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "project_root": self.project_root,
            "repository_manifest_path": self.repository_manifest_path,
            "registry_path": self.registry_path,
            "packages": [package.to_dict() for package in self.packages],
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


def package_status(blockers: list[str], warnings: list[str], *, exploratory: bool = False) -> tuple[str, str]:
    if blockers:
        return "blocked", "blocked"
    if exploratory:
        return "preflight_only", "exploratory"
    if warnings:
        return "preflight_only", "preflight_only"
    return "config_only", "config_only"


def relative_or_absolute(root: Path, value: str) -> str:
    if not value:
        return ""
    path = Path(value).expanduser()
    if path.is_absolute():
        return str(path)
    return str(root / path)
