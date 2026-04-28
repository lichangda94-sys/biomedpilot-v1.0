from __future__ import annotations

import csv
from dataclasses import dataclass, field
import math
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass(slots=True)
class DegSummaryRow:
    gene_symbol: str
    case_mean: float
    control_mean: float
    log2fc: float
    status: str = "computed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "gene_symbol": self.gene_symbol,
            "case_mean": self.case_mean,
            "control_mean": self.control_mean,
            "log2fc": self.log2fc,
            "status": self.status,
        }


@dataclass(slots=True)
class DegSummaryReport:
    comparison_id: str
    case_group: str
    control_group: str
    gene_count: int = 0
    case_count: int = 0
    control_count: int = 0
    computed_gene_count: int = 0
    skipped_gene_count: int = 0
    log2fc_available: bool = True
    pvalue_available: bool = False
    fdr_available: bool = False
    method: str = "mean_log2fc_summary"
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    rows: list[DegSummaryRow] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "case_group": self.case_group,
            "control_group": self.control_group,
            "gene_count": self.gene_count,
            "case_count": self.case_count,
            "control_count": self.control_count,
            "computed_gene_count": self.computed_gene_count,
            "skipped_gene_count": self.skipped_gene_count,
            "log2fc_available": self.log2fc_available,
            "pvalue_available": self.pvalue_available,
            "fdr_available": self.fdr_available,
            "method": self.method,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "rows": [row.to_dict() for row in self.rows],
        }


def build_deg_summary_report(
    gene_matrix_rows: list[dict[str, Any]],
    sample_groups: dict[str, str],
    *,
    comparison_id: str = "ptc_vs_normal_control",
    case_group: str = "ptc",
    control_group: str = "normal",
    pseudocount: float = 1e-9,
) -> DegSummaryReport:
    warnings: list[str] = []
    errors: list[str] = []
    if not gene_matrix_rows:
        errors.append("gene_matrix_missing")
    if pseudocount <= 0:
        errors.append("invalid_pseudocount")

    sample_ids = _sample_ids(gene_matrix_rows)
    case_samples = [sample for sample in sample_ids if sample_groups.get(sample) == case_group]
    control_samples = [sample for sample in sample_ids if sample_groups.get(sample) == control_group]
    if not case_samples:
        errors.append("case_group_has_no_samples")
    if not control_samples:
        errors.append("control_group_has_no_samples")

    rows: list[DegSummaryRow] = []
    skipped_gene_count = 0
    if case_samples and control_samples:
        for row in gene_matrix_rows:
            gene_symbol = str(row.get("gene_symbol") or "").strip()
            if not gene_symbol:
                skipped_gene_count += 1
                warnings.append("gene_symbol_missing")
                continue
            case_values = _numeric_values(row, case_samples)
            control_values = _numeric_values(row, control_samples)
            if len(case_values) != len(case_samples) or len(control_values) != len(control_samples):
                skipped_gene_count += 1
                warnings.append("gene_values_missing_or_non_numeric")
                continue
            case_mean = mean(case_values)
            control_mean = mean(control_values)
            log2fc = math.log2((case_mean + pseudocount) / (control_mean + pseudocount))
            rows.append(
                DegSummaryRow(
                    gene_symbol=gene_symbol,
                    case_mean=case_mean,
                    control_mean=control_mean,
                    log2fc=log2fc,
                )
            )
    elif gene_matrix_rows:
        skipped_gene_count = len(gene_matrix_rows)

    if gene_matrix_rows and not rows:
        errors.append("computed_genes_missing")

    return DegSummaryReport(
        comparison_id=comparison_id,
        case_group=case_group,
        control_group=control_group,
        gene_count=len(gene_matrix_rows),
        case_count=len(case_samples),
        control_count=len(control_samples),
        computed_gene_count=len(rows),
        skipped_gene_count=skipped_gene_count,
        log2fc_available=not errors,
        pvalue_available=False,
        fdr_available=False,
        method="mean_log2fc_summary",
        warnings=_dedupe(warnings),
        errors=_dedupe(errors),
        rows=rows,
    )


def write_deg_summary_table(report: DegSummaryReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["gene_symbol", "case_mean", "control_mean", "log2fc", "status"],
        )
        writer.writeheader()
        for row in report.rows:
            writer.writerow(row.to_dict())
    return path


def write_volcano_ready_descriptive_table(report: DegSummaryReport, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "gene_symbol",
        "case_mean",
        "control_mean",
        "log2fc",
        "abs_log2fc",
        "status",
        "pvalue",
        "padj",
        "pvalue_available",
        "fdr_available",
        "method",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in report.rows:
            writer.writerow(
                {
                    "gene_symbol": row.gene_symbol,
                    "case_mean": row.case_mean,
                    "control_mean": row.control_mean,
                    "log2fc": row.log2fc,
                    "abs_log2fc": abs(row.log2fc),
                    "status": "descriptive_only" if row.status == "computed" else row.status,
                    "pvalue": "",
                    "padj": "",
                    "pvalue_available": "false",
                    "fdr_available": "false",
                    "method": "descriptive_mean_log2fc",
                }
            )
    return path


def _sample_ids(gene_matrix_rows: list[dict[str, Any]]) -> list[str]:
    if not gene_matrix_rows:
        return []
    excluded = {"gene_symbol"}
    return [key for key in gene_matrix_rows[0].keys() if key not in excluded]


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
