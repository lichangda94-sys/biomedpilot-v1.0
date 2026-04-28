from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BioReportSourceSummary:
    source_path: str
    source_kind: str
    dataset_count: int
    completed_execution: bool


class BioReportAdapter:
    def summarize_sources(self, source_paths: list[Path]) -> list[BioReportSourceSummary]:
        summaries: list[BioReportSourceSummary] = []
        for source_path in source_paths:
            payload = json.loads(source_path.read_text(encoding="utf-8"))
            source_kind = _source_kind(payload)
            summaries.append(
                BioReportSourceSummary(
                    source_path=str(source_path),
                    source_kind=source_kind,
                    dataset_count=_dataset_count(payload),
                    completed_execution=_completed_execution(payload),
                )
            )
        return summaries


def _source_kind(payload: dict[str, object]) -> str:
    if "query" in payload or "accessions" in payload:
        return "geo_query_plan"
    if "download_items" in payload:
        return "geo_download_plan"
    if "detections" in payload:
        return "geo_asset_detection"
    if "cleaning_items" in payload:
        return "geo_cleaning_plan"
    if "grouping_items" in payload:
        return "geo_sample_grouping_plan"
    if "preflight_items" in payload:
        if "enrichment_executed" in payload:
            return "geo_enrichment_preflight"
        if "correlation_executed" in payload:
            return "geo_correlation_preflight"
        if "survival_analysis_executed" in payload:
            return "geo_survival_preflight"
        return "geo_differential_expression_preflight"
    return "unknown_bioinformatics_artifact"


def _dataset_count(payload: dict[str, object]) -> int:
    for key in ("download_items", "detections", "cleaning_items", "grouping_items", "preflight_items"):
        value = payload.get(key)
        if isinstance(value, list):
            return len(value)
    accessions = payload.get("accessions")
    if isinstance(accessions, list):
        return len(accessions)
    return 0


def _completed_execution(payload: dict[str, object]) -> bool:
    execution_flags = (
        "download_executed",
        "cleaning_executed",
        "grouping_executed",
        "formal_deg_executed",
        "enrichment_executed",
        "correlation_executed",
        "survival_analysis_executed",
    )
    return any(bool(payload.get(flag)) for flag in execution_flags)
