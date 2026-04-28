from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from geo_readiness.models import PlatformAnnotationMappingReport, SeriesMatrixExpressionReport


@dataclass(slots=True)
class DegReadyMatrixReport:
    feature_count: int = 0
    mapped_feature_count: int = 0
    unmapped_feature_count: int = 0
    gene_count: int = 0
    gene_count_after_collapse: int = 0
    sample_count: int = 0
    case_count: int = 0
    control_count: int = 0
    duplicated_gene_count: int = 0
    collapse_strategy: str = "mean"
    ready: bool = False
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_count": self.feature_count,
            "mapped_feature_count": self.mapped_feature_count,
            "unmapped_feature_count": self.unmapped_feature_count,
            "gene_count": self.gene_count,
            "gene_count_after_collapse": self.gene_count_after_collapse,
            "sample_count": self.sample_count,
            "case_count": self.case_count,
            "control_count": self.control_count,
            "duplicated_gene_count": self.duplicated_gene_count,
            "collapse_strategy": self.collapse_strategy,
            "ready": self.ready,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


def build_deg_ready_matrix_report(
    expression_rows: list[dict[str, Any]],
    sample_groups: dict[str, str],
    probe_to_symbol: dict[str, str | None] | None,
    *,
    case_group: str = "ptc",
    control_group: str = "normal",
    collapse_strategy: str = "mean",
) -> DegReadyMatrixReport:
    warnings: list[str] = []
    errors: list[str] = []
    mapping = probe_to_symbol or {}
    if not expression_rows:
        errors.append("expression_rows_missing")
    if not mapping:
        errors.append("probe_symbol_mapping_missing")
    if collapse_strategy != "mean":
        errors.append("unsupported_collapse_strategy")

    sample_ids = _sample_ids(expression_rows)
    case_samples = [sample for sample in sample_ids if sample_groups.get(sample) == case_group]
    control_samples = [sample for sample in sample_ids if sample_groups.get(sample) == control_group]
    if not case_samples:
        errors.append("case_group_has_no_samples")
    if not control_samples:
        errors.append("control_group_has_no_samples")

    mapped_values: dict[str, list[float]] = {}
    mapped_feature_count = 0
    unmapped_feature_count = 0
    for row in expression_rows:
        probe_id = str(row.get("probe_id") or row.get("ID_REF") or "").strip()
        if not probe_id:
            continue
        symbol = str(mapping.get(probe_id) or "").strip()
        if not symbol:
            unmapped_feature_count += 1
            continue
        values = _numeric_values(row, sample_ids)
        if len(values) != len(sample_ids):
            errors.append("non_numeric_expression_values")
            continue
        mapped_feature_count += 1
        mapped_values.setdefault(symbol, []).append(mean(values))

    duplicated_gene_count = sum(len(values) - 1 for values in mapped_values.values() if len(values) > 1)
    if duplicated_gene_count:
        warnings.append("duplicated_genes_collapsed")
    if unmapped_feature_count:
        warnings.append("unmapped_probes_excluded")
    if mapped_feature_count == 0 and expression_rows:
        errors.append("mapped_features_missing")

    return DegReadyMatrixReport(
        feature_count=len(expression_rows),
        mapped_feature_count=mapped_feature_count,
        unmapped_feature_count=unmapped_feature_count,
        gene_count=len(mapped_values),
        gene_count_after_collapse=len(mapped_values),
        sample_count=len(sample_ids),
        case_count=len(case_samples),
        control_count=len(control_samples),
        duplicated_gene_count=duplicated_gene_count,
        collapse_strategy=collapse_strategy,
        ready=not errors,
        warnings=warnings,
        errors=_dedupe(errors),
    )


def build_deg_ready_matrix_report_from_reports(
    expression_report: SeriesMatrixExpressionReport | None,
    platform_mapping_report: PlatformAnnotationMappingReport | None,
    sample_groups: dict[str, str],
    *,
    case_group: str = "ptc",
    control_group: str = "normal",
    collapse_strategy: str = "mean",
) -> DegReadyMatrixReport:
    warnings: list[str] = []
    errors: list[str] = []

    if expression_report is None:
        errors.append("expression_report_missing")
        expression_report = SeriesMatrixExpressionReport()
    if platform_mapping_report is None:
        errors.append("platform_mapping_report_missing")
        platform_mapping_report = PlatformAnnotationMappingReport()
    if collapse_strategy != "mean":
        errors.append("unsupported_collapse_strategy")

    warnings.extend(expression_report.warnings)
    warnings.extend(platform_mapping_report.warnings)
    errors.extend(expression_report.errors)
    errors.extend(platform_mapping_report.errors)

    if expression_report.feature_count <= 0:
        errors.append("expression_features_missing")
    if expression_report.sample_count <= 0:
        errors.append("expression_samples_missing")
    if expression_report.numeric_value_status not in {"numeric", "numeric_with_missing"}:
        errors.append("expression_values_not_numeric")
    if expression_report.sample_id_match_status not in {"match", "not_checked"}:
        errors.append("matrix_metadata_sample_id_mismatch")

    if not platform_mapping_report.acceptable:
        errors.append("platform_mapping_not_acceptable")
    if platform_mapping_report.mapped_probe_count <= 0:
        errors.append("mapped_features_missing")

    sample_ids = list(expression_report.matrix_sample_ids)
    case_count = sum(1 for sample_id in sample_ids if sample_groups.get(sample_id) == case_group)
    control_count = sum(1 for sample_id in sample_ids if sample_groups.get(sample_id) == control_group)
    if not case_count:
        errors.append("case_group_has_no_samples")
    if not control_count:
        errors.append("control_group_has_no_samples")

    mapped_feature_count = min(
        expression_report.feature_count,
        platform_mapping_report.mapped_probe_count,
    )
    unmapped_feature_count = max(expression_report.feature_count - mapped_feature_count, 0)
    duplicated_gene_count = min(platform_mapping_report.duplicated_symbol_count, mapped_feature_count)
    gene_count_after_collapse = max(mapped_feature_count - duplicated_gene_count, 0)

    if duplicated_gene_count:
        warnings.append("duplicated_genes_collapsed")
    if unmapped_feature_count:
        warnings.append("unmapped_probes_excluded")

    return DegReadyMatrixReport(
        feature_count=expression_report.feature_count,
        mapped_feature_count=mapped_feature_count,
        unmapped_feature_count=unmapped_feature_count,
        gene_count=gene_count_after_collapse,
        gene_count_after_collapse=gene_count_after_collapse,
        sample_count=expression_report.sample_count,
        case_count=case_count,
        control_count=control_count,
        duplicated_gene_count=duplicated_gene_count,
        collapse_strategy=collapse_strategy,
        ready=not errors,
        warnings=_dedupe(warnings),
        errors=_dedupe(errors),
    )


def _sample_ids(expression_rows: list[dict[str, Any]]) -> list[str]:
    if not expression_rows:
        return []
    excluded = {"probe_id", "ID_REF", "gene_symbol"}
    return [key for key in expression_rows[0].keys() if key not in excluded]


def _numeric_values(row: dict[str, Any], sample_ids: list[str]) -> list[float]:
    values: list[float] = []
    for sample_id in sample_ids:
        try:
            values.append(float(row[sample_id]))
        except (KeyError, TypeError, ValueError):
            return []
    return values


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
