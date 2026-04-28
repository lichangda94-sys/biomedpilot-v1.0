from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from analysis.comparison_readiness import ComparisonReadinessReport
from analysis.group_detection import GroupDetectionReport
from core.dataset_readiness import (
    DatasetAssetReadinessReport,
    GeneMappingReadinessReport,
    SampleMappingReadinessReport,
    build_dataset_asset_readiness_report,
    build_gene_mapping_readiness_report,
    build_sample_mapping_readiness_report,
)
from analysis.comparison_readiness import build_comparison_readiness_report
from geo_readiness.models import (
    PlatformAnnotationMappingReport,
    SeriesMatrixExpressionReport,
    SeriesMatrixMetadataReport,
)


ANALYSIS_PREFLIGHT_SUMMARY_KEYS = (
    "total_checks",
    "runnable_checks",
    "blocked_checks",
    "warning_count",
    "blocking_error_count",
)


@dataclass(slots=True)
class AnalysisPreflightSummary:
    dataset_id: str
    profile_id: str
    asset_readiness: DatasetAssetReadinessReport
    gene_mapping_readiness: GeneMappingReadinessReport
    sample_mapping_readiness: SampleMappingReadinessReport
    comparison_readiness: ComparisonReadinessReport
    runnable: bool
    blocking_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "profile_id": self.profile_id,
            "asset_readiness": self.asset_readiness.to_dict(),
            "gene_mapping_readiness": self.gene_mapping_readiness.to_dict(),
            "sample_mapping_readiness": self.sample_mapping_readiness.to_dict(),
            "comparison_readiness": self.comparison_readiness.to_dict(),
            "runnable": self.runnable,
            "blocking_errors": list(self.blocking_errors),
            "warnings": list(self.warnings),
            "recommended_action": self.recommended_action,
        }


def build_analysis_preflight_summary(
    *,
    dataset_id: str,
    profile_id: str,
    asset_readiness: DatasetAssetReadinessReport,
    gene_mapping_readiness: GeneMappingReadinessReport,
    sample_mapping_readiness: SampleMappingReadinessReport,
    comparison_readiness: ComparisonReadinessReport,
) -> AnalysisPreflightSummary:
    blocking_errors: list[str] = []
    warnings: list[str] = []

    blocking_errors.extend(
        f"asset:{error}" for error in asset_readiness.errors
    )
    warnings.extend(f"asset:{warning}" for warning in asset_readiness.warnings)

    if not gene_mapping_readiness.acceptable:
        blocking_errors.extend(
            f"gene_mapping:{error}" for error in gene_mapping_readiness.errors
        )
    warnings.extend(
        f"gene_mapping:{warning}" for warning in gene_mapping_readiness.warnings
    )

    if not sample_mapping_readiness.acceptable:
        blocking_errors.extend(
            f"sample_mapping:{error}" for error in sample_mapping_readiness.errors
        )
    warnings.extend(
        f"sample_mapping:{warning}" for warning in sample_mapping_readiness.warnings
    )

    if not comparison_readiness.runnable:
        blocking_errors.extend(
            f"comparison:{error}" for error in comparison_readiness.errors
        )
    warnings.extend(
        f"comparison:{warning}" for warning in comparison_readiness.warnings
    )

    runnable = not blocking_errors
    return AnalysisPreflightSummary(
        dataset_id=dataset_id,
        profile_id=profile_id,
        asset_readiness=asset_readiness,
        gene_mapping_readiness=gene_mapping_readiness,
        sample_mapping_readiness=sample_mapping_readiness,
        comparison_readiness=comparison_readiness,
        runnable=runnable,
        blocking_errors=blocking_errors,
        warnings=warnings,
        recommended_action=_analysis_preflight_recommended_action(
            runnable,
            blocking_errors,
            warnings,
        ),
    )


def summarize_analysis_preflight_summaries(
    summaries: list[AnalysisPreflightSummary] | None,
) -> dict[str, int]:
    records = list(summaries or [])
    return {
        "total_checks": len(records),
        "runnable_checks": sum(1 for item in records if item.runnable),
        "blocked_checks": sum(1 for item in records if not item.runnable),
        "warning_count": sum(len(item.warnings) for item in records),
        "blocking_error_count": sum(len(item.blocking_errors) for item in records),
    }


def format_analysis_preflight_summary(
    summary: dict[str, int] | None,
) -> list[str]:
    values = summary or {}
    lines = ["Analysis preflight readiness summary:"]
    for key in ANALYSIS_PREFLIGHT_SUMMARY_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


def build_fake_analysis_preflight_smoke_fixture() -> list[AnalysisPreflightSummary]:
    runnable = build_analysis_preflight_summary(
        dataset_id="GSE-fake-runnable",
        profile_id="profile-smoke",
        asset_readiness=build_dataset_asset_readiness_report(
            "GSE-fake-runnable",
            {
                "expression_matrix": True,
                "sample_annotation": True,
                "gene_annotation": True,
            },
        ),
        gene_mapping_readiness=build_gene_mapping_readiness_report(
            ["TP53", "EGFR"],
            input_id_type="gene_symbol",
            target_id_type="gene_symbol",
        ),
        sample_mapping_readiness=build_sample_mapping_readiness_report(
            ["S1", "S2"],
            ["S1", "S2"],
        ),
        comparison_readiness=build_comparison_readiness_report(
            [
                {"sample_id": "S1", "group": "case"},
                {"sample_id": "S2", "group": "case"},
                {"sample_id": "S3", "group": "control"},
                {"sample_id": "S4", "group": "control"},
            ],
            {
                "comparison_id": "fake_case_vs_control",
                "group_column": "group",
                "case_group": "case",
                "control_group": "control",
            },
        ),
    )
    blocked = build_analysis_preflight_summary(
        dataset_id="GSE-fake-blocked",
        profile_id="profile-smoke",
        asset_readiness=build_dataset_asset_readiness_report("GSE-fake-blocked", {}),
        gene_mapping_readiness=build_gene_mapping_readiness_report(
            ["TP53"],
            input_id_type="gene_symbol",
            target_id_type="gene_symbol",
        ),
        sample_mapping_readiness=build_sample_mapping_readiness_report(["S1"], ["S1"]),
        comparison_readiness=build_comparison_readiness_report(
            [
                {"sample_id": "S1", "group": "case"},
                {"sample_id": "S2", "group": "control"},
            ],
            {
                "comparison_id": "fake_case_vs_control",
                "group_column": "group",
                "case_group": "case",
                "control_group": "control",
            },
            minimum_group_size=1,
        ),
    )
    return [runnable, blocked]


def build_geo_series_matrix_preflight_summary(
    *,
    series_matrix_metadata: SeriesMatrixMetadataReport,
    group_detection: GroupDetectionReport,
    expression_report: SeriesMatrixExpressionReport | None = None,
    platform_mapping_report: PlatformAnnotationMappingReport | None = None,
    profile_id: str = "geo_series_matrix_metadata_only",
    gene_mapping_readiness: GeneMappingReadinessReport | None = None,
) -> AnalysisPreflightSummary:
    dataset_id = series_matrix_metadata.gse_id or "unknown_geo_series"
    sample_ids = list(series_matrix_metadata.sample_ids)
    matrix_sample_ids = (
        list(expression_report.matrix_sample_ids)
        if expression_report is not None
        else sample_ids
    )
    metadata_sample_ids = [
        row.get("sample_id", "") for row in series_matrix_metadata.sample_metadata_rows
    ]
    comparison_metadata = [
        {"sample_id": sample_id, "group": group}
        for sample_id, group in group_detection.sample_to_group.items()
        if group in {"ptc", "normal"}
    ]

    summary = build_analysis_preflight_summary(
        dataset_id=dataset_id,
        profile_id=profile_id,
        asset_readiness=build_dataset_asset_readiness_report(
            dataset_id,
            {
                "expression_matrix": expression_report is not None,
                "sample_annotation": bool(series_matrix_metadata.sample_metadata_rows),
                "platform_annotation": bool(series_matrix_metadata.platform_ids),
                "gene_annotation": bool(
                    platform_mapping_report and platform_mapping_report.acceptable
                ),
            },
        ),
        gene_mapping_readiness=gene_mapping_readiness
        or _gene_mapping_from_platform_report(platform_mapping_report)
        or build_gene_mapping_readiness_report(
            ["probe_placeholder"],
            {"probe_placeholder": "GENE"},
            input_id_type="probe_id",
        ),
        sample_mapping_readiness=build_sample_mapping_readiness_report(
            matrix_sample_ids,
            metadata_sample_ids,
        ),
        comparison_readiness=build_comparison_readiness_report(
            comparison_metadata,
            {
                "comparison_id": f"{dataset_id}_ptc_vs_normal_candidate",
                "group_column": "group",
                "case_group": "ptc",
                "control_group": "normal",
            },
            minimum_group_size=1,
        ),
    )

    if expression_report is None:
        if "expression_matrix_values_not_parsed" not in summary.blocking_errors:
            summary.blocking_errors.append("expression_matrix_values_not_parsed")
        summary.runnable = False
        summary.recommended_action = "parse_expression_matrix_values_before_analysis"
    else:
        summary.blocking_errors.extend(
            _expression_report_blocking_errors(expression_report)
        )
        summary.warnings.extend(
            f"expression_matrix:{warning}" for warning in expression_report.warnings
        )
        summary.runnable = not summary.blocking_errors
        summary.recommended_action = _analysis_preflight_recommended_action(
            summary.runnable,
            summary.blocking_errors,
            summary.warnings,
        )
    summary.warnings.extend(
        f"series_matrix:{warning}" for warning in series_matrix_metadata.warnings
    )
    summary.warnings.extend(
        f"group_detection:{warning}" for warning in group_detection.warnings
    )
    if "excluded_atc_samples" in group_detection.warnings:
        summary.warnings.append("group_detection:atc_samples_excluded_from_candidate")
    if "excluded_non_target_samples" in group_detection.warnings:
        summary.warnings.append("group_detection:non_target_samples_excluded_from_candidate")
    if {"ptc", "normal"}.issubset(set(group_detection.detected_groups)):
        summary.warnings.append("comparison:ptc_vs_normal_candidate_detected")
    if platform_mapping_report is not None:
        summary.blocking_errors.extend(
            _platform_mapping_blocking_errors(platform_mapping_report)
        )
        summary.warnings.extend(
            f"platform_mapping:{warning}"
            for warning in platform_mapping_report.warnings
        )
        summary.runnable = not summary.blocking_errors
    if expression_report is None:
        summary.recommended_action = "parse_expression_matrix_values_before_analysis"
    else:
        summary.recommended_action = _analysis_preflight_recommended_action(
            summary.runnable,
            summary.blocking_errors,
            summary.warnings,
        )
    return summary


def _gene_mapping_from_platform_report(
    platform_mapping_report: PlatformAnnotationMappingReport | None,
) -> GeneMappingReadinessReport | None:
    if platform_mapping_report is None:
        return None
    return GeneMappingReadinessReport(
        input_id_type="probe_id",
        target_id_type="gene_symbol",
        total_features=platform_mapping_report.probe_count,
        mapped_features=platform_mapping_report.mapped_probe_count,
        unmapped_features=platform_mapping_report.unmapped_probe_count,
        duplicated_targets=platform_mapping_report.duplicated_symbol_count,
        mapping_success_rate=platform_mapping_report.mapping_success_rate,
        collapse_strategy="platform_annotation",
        acceptable=platform_mapping_report.acceptable,
        warnings=list(platform_mapping_report.warnings),
        errors=list(platform_mapping_report.errors),
    )


def _platform_mapping_blocking_errors(
    platform_mapping_report: PlatformAnnotationMappingReport,
) -> list[str]:
    if platform_mapping_report.acceptable:
        return []
    errors = [f"platform_mapping:{error}" for error in platform_mapping_report.errors]
    if not errors:
        errors.append("platform_mapping:platform_mapping_not_acceptable")
    return _dedupe_strings(errors)


def _expression_report_blocking_errors(
    expression_report: SeriesMatrixExpressionReport,
) -> list[str]:
    errors = [f"expression_matrix:{error}" for error in expression_report.errors]
    if expression_report.feature_count <= 0:
        errors.append("expression_matrix:feature_rows_missing")
    if expression_report.sample_count <= 0:
        errors.append("expression_matrix:sample_columns_missing")
    if expression_report.numeric_value_status == "non_numeric":
        if "expression_matrix:non_numeric_expression_values" not in errors:
            errors.append("expression_matrix:non_numeric_expression_values")
    if expression_report.sample_id_match_status == "mismatch":
        if "expression_matrix:matrix_metadata_sample_id_mismatch" not in errors:
            errors.append("expression_matrix:matrix_metadata_sample_id_mismatch")
    return _dedupe_strings(errors)


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _analysis_preflight_recommended_action(
    runnable: bool,
    blocking_errors: list[str],
    warnings: list[str],
) -> str:
    if not runnable:
        if any(error.startswith("asset:expression_matrix_missing") for error in blocking_errors):
            return "provide_expression_matrix"
        if any(error.startswith("sample_mapping:") for error in blocking_errors):
            return "fix_sample_mapping"
        if any(error.startswith("comparison:") for error in blocking_errors):
            return "fix_comparison_definition"
        if any(error.startswith("gene_mapping:") for error in blocking_errors):
            return "fix_gene_mapping"
        return "resolve_blocking_errors"
    if warnings:
        return "review_warnings_before_analysis"
    return "ready_for_analysis"
