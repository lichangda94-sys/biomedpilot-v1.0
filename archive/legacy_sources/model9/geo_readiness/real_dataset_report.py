from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


GAP_CATEGORIES = (
    "download_gap",
    "metadata_parse_gap",
    "series_matrix_parse_gap",
    "expression_matrix_gap",
    "sample_mapping_gap",
    "gene_mapping_gap",
    "group_detection_gap",
    "comparison_readiness_gap",
    "preflight_gap",
    "ui_display_gap",
    "manual_confirmation_required",
)


@dataclass(slots=True)
class RealDatasetGap:
    category: str
    code: str
    message: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "code": self.code,
            "message": self.message,
            "source": self.source,
        }


@dataclass(slots=True)
class RealDatasetReadinessReport:
    dataset_id: str
    metadata_parse: dict[str, Any] = field(default_factory=dict)
    series_matrix_metadata: dict[str, Any] = field(default_factory=dict)
    group_detection: dict[str, Any] = field(default_factory=dict)
    expression_report: dict[str, Any] = field(default_factory=dict)
    platform_mapping: dict[str, Any] = field(default_factory=dict)
    preflight: dict[str, Any] = field(default_factory=dict)
    gaps: list[RealDatasetGap] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommended_action: str = "review_report"

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "metadata_parse": dict(self.metadata_parse),
            "series_matrix_metadata": dict(self.series_matrix_metadata),
            "group_detection": dict(self.group_detection),
            "expression_report": dict(self.expression_report),
            "platform_mapping": dict(self.platform_mapping),
            "preflight": dict(self.preflight),
            "gaps": [gap.to_dict() for gap in self.gaps],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "recommended_action": self.recommended_action,
        }


def classify_real_dataset_gaps(
    *,
    metadata_errors: list[str] | None = None,
    series_matrix_errors: list[str] | None = None,
    expression_errors: list[str] | None = None,
    sample_mapping_status: str = "",
    platform_mapping_acceptable: bool | None = None,
    platform_mapping_errors: list[str] | None = None,
    group_errors: list[str] | None = None,
    group_warnings: list[str] | None = None,
    preflight_blocking_errors: list[str] | None = None,
) -> list[RealDatasetGap]:
    gaps: list[RealDatasetGap] = []
    for error in metadata_errors or []:
        gaps.append(_gap("metadata_parse_gap", error, "metadata_parse"))
    for error in series_matrix_errors or []:
        gaps.append(_gap("series_matrix_parse_gap", error, "series_matrix_metadata"))
    for error in expression_errors or []:
        gaps.append(_gap("expression_matrix_gap", error, "expression_report"))
    if sample_mapping_status == "mismatch":
        gaps.append(_gap("sample_mapping_gap", "sample_id_mismatch", "expression_report"))
    if platform_mapping_acceptable is False:
        codes = platform_mapping_errors or ["platform_mapping_not_acceptable"]
        for code in codes:
            gaps.append(_gap("gene_mapping_gap", code, "platform_mapping"))
    for error in group_errors or []:
        gaps.append(_gap("group_detection_gap", error, "group_detection"))
    for warning in group_warnings or []:
        if warning in {"ambiguous_samples", "no_groups_detected"}:
            gaps.append(_gap("group_detection_gap", warning, "group_detection"))
    for error in preflight_blocking_errors or []:
        category = _preflight_gap_category(error)
        gaps.append(_gap(category, error, "preflight"))
    return _dedupe_gaps(gaps)


def build_real_dataset_readiness_report(
    *,
    dataset_id: str,
    metadata_parse: dict[str, Any] | None = None,
    series_matrix_metadata: dict[str, Any] | None = None,
    group_detection: dict[str, Any] | None = None,
    expression_report: dict[str, Any] | None = None,
    platform_mapping: dict[str, Any] | None = None,
    preflight: dict[str, Any] | None = None,
) -> RealDatasetReadinessReport:
    metadata_parse = metadata_parse or {}
    series_matrix_metadata = series_matrix_metadata or {}
    group_detection = group_detection or {}
    expression_report = expression_report or {}
    platform_mapping = platform_mapping or {}
    preflight = preflight or {}

    gaps = classify_real_dataset_gaps(
        metadata_errors=list(metadata_parse.get("errors", [])),
        series_matrix_errors=list(series_matrix_metadata.get("errors", [])),
        expression_errors=list(expression_report.get("errors", [])),
        sample_mapping_status=str(expression_report.get("sample_id_match_status", "")),
        platform_mapping_acceptable=platform_mapping.get("acceptable"),
        platform_mapping_errors=list(platform_mapping.get("errors", [])),
        group_errors=list(group_detection.get("errors", [])),
        group_warnings=list(group_detection.get("warnings", [])),
        preflight_blocking_errors=list(preflight.get("blocking_errors", [])),
    )
    errors = [gap.code for gap in gaps]
    warnings = _collect_warnings(
        metadata_parse,
        series_matrix_metadata,
        group_detection,
        expression_report,
        platform_mapping,
        preflight,
    )
    return RealDatasetReadinessReport(
        dataset_id=dataset_id,
        metadata_parse=metadata_parse,
        series_matrix_metadata=series_matrix_metadata,
        group_detection=group_detection,
        expression_report=expression_report,
        platform_mapping=platform_mapping,
        preflight=preflight,
        gaps=gaps,
        warnings=warnings,
        errors=errors,
        recommended_action=_recommended_action(gaps, preflight),
    )


def _gap(category: str, code: str, source: str) -> RealDatasetGap:
    if category not in GAP_CATEGORIES:
        category = "preflight_gap"
    return RealDatasetGap(category=category, code=code, source=source)


def _preflight_gap_category(error: str) -> str:
    if error.startswith("sample_mapping:"):
        return "sample_mapping_gap"
    if error.startswith("gene_mapping:") or error.startswith("platform_mapping:"):
        return "gene_mapping_gap"
    if error.startswith("comparison:"):
        return "comparison_readiness_gap"
    if error.startswith("expression_matrix:") or error.startswith("asset:expression_matrix"):
        return "expression_matrix_gap"
    return "preflight_gap"


def _dedupe_gaps(gaps: list[RealDatasetGap]) -> list[RealDatasetGap]:
    seen: set[tuple[str, str, str]] = set()
    result: list[RealDatasetGap] = []
    for gap in gaps:
        key = (gap.category, gap.code, gap.source)
        if key not in seen:
            seen.add(key)
            result.append(gap)
    return result


def _collect_warnings(*sections: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for section in sections:
        for warning in section.get("warnings", []):
            if warning not in warnings:
                warnings.append(warning)
    return warnings


def _recommended_action(gaps: list[RealDatasetGap], preflight: dict[str, Any]) -> str:
    if not gaps and preflight.get("runnable") is True:
        return "ready_for_manual_review"
    categories = {gap.category for gap in gaps}
    if "metadata_parse_gap" in categories:
        return "fix_metadata_parser_or_input"
    if "series_matrix_parse_gap" in categories:
        return "fix_series_matrix_parser_or_input"
    if "expression_matrix_gap" in categories:
        return "fix_expression_matrix_readiness"
    if "sample_mapping_gap" in categories:
        return "fix_sample_mapping"
    if "gene_mapping_gap" in categories:
        return "fix_gene_mapping"
    if "group_detection_gap" in categories:
        return "review_group_detection"
    if "comparison_readiness_gap" in categories:
        return "fix_comparison_definition"
    return "review_preflight_gaps"
