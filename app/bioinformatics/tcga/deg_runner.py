"""Minimal TCGA tumor-vs-normal DEG runner."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from .analysis_inputs import build_tcga_deg_input
from .prepared_package import load_tcga_prepared_manifest


RESULT_FILENAME = "tcga_deg_results.csv"
SUMMARY_FILENAME = "tcga_deg_summary.json"


def _as_float(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _try_ttest(tumor_values: list[float], normal_values: list[float]) -> float | None:
    try:
        from scipy import stats  # type: ignore
    except Exception:
        return None
    try:
        result = stats.ttest_ind(tumor_values, normal_values, equal_var=False, nan_policy="omit")
    except Exception:
        return None
    p_value = getattr(result, "pvalue", None)
    try:
        numeric = float(p_value)
    except (TypeError, ValueError):
        return None
    if math.isnan(numeric):
        return None
    return numeric


def _manifest_payload(manifest_or_path: dict[str, Any] | str | Path) -> tuple[dict[str, Any], Path | None]:
    if isinstance(manifest_or_path, dict):
        return manifest_or_path, None
    path = Path(manifest_or_path).expanduser().resolve()
    return load_tcga_prepared_manifest(path), path


def _deg_output_dir(output_dir: str | Path | None, manifest_path: Path | None) -> Path:
    if output_dir is not None:
        return Path(output_dir).expanduser().resolve() / "analysis" / "tcga" / "deg"
    if manifest_path is not None and len(manifest_path.parents) >= 3:
        return manifest_path.parents[2] / "analysis" / "tcga" / "deg"
    return Path.cwd().resolve() / "analysis" / "tcga" / "deg"


def _format_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.12g}"


def _write_results(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "gene_id",
        "tumor_mean",
        "normal_mean",
        "log2_fold_change",
        "mean_difference",
        "tumor_sample_count",
        "normal_sample_count",
        "p_value",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def run_tcga_deg_analysis(
    manifest_or_path: dict[str, Any] | str | Path,
    output_dir: str | Path | None = None,
    tumor_labels: list[str] | tuple[str, ...] | None = None,
    normal_labels: list[str] | tuple[str, ...] | None = None,
    min_samples_per_group: int = 1,
    pseudocount: float = 1e-9,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run a minimal tumor-vs-normal DEG summary without enrichment/reporting."""
    manifest, manifest_path = _manifest_payload(manifest_or_path)
    deg_input = build_tcga_deg_input(
        manifest,
        tumor_labels=tumor_labels,
        normal_labels=normal_labels,
        paired=False,
    )
    warnings = list(deg_input.get("warnings", []))
    expression_matrix = deg_input["expression_matrix"]
    tumor_samples = deg_input["tumor_samples"]
    normal_samples = deg_input["normal_samples"]
    scipy_available = _try_ttest([1.0, 2.0], [1.0, 2.0]) is not None
    if not scipy_available:
        warnings.append("statistical_test_unavailable")

    result_rows: list[dict[str, Any]] = []
    for row in expression_matrix:
        gene_id = row.get("gene_id", "")
        tumor_values = [_as_float(row.get(sample, "")) for sample in tumor_samples]
        normal_values = [_as_float(row.get(sample, "")) for sample in normal_samples]
        tumor_numeric = [value for value in tumor_values if value is not None]
        normal_numeric = [value for value in normal_values if value is not None]

        if len(tumor_numeric) < min_samples_per_group or len(normal_numeric) < min_samples_per_group:
            warnings.append(
                "gene_skipped_insufficient_samples:"
                f"{gene_id}:tumor={len(tumor_numeric)}:normal={len(normal_numeric)}"
            )
            continue

        tumor_mean = _mean(tumor_numeric)
        normal_mean = _mean(normal_numeric)
        mean_difference = tumor_mean - normal_mean
        ratio = (tumor_mean + pseudocount) / (normal_mean + pseudocount)
        log2_fold_change = math.log2(ratio) if ratio > 0 else None
        if log2_fold_change is None:
            warnings.append(f"log2_fold_change_unavailable:{gene_id}")

        p_value = _try_ttest(tumor_numeric, normal_numeric) if scipy_available else None
        result_rows.append(
            {
                "gene_id": gene_id,
                "tumor_mean": _format_number(tumor_mean),
                "normal_mean": _format_number(normal_mean),
                "log2_fold_change": _format_number(log2_fold_change),
                "mean_difference": _format_number(mean_difference),
                "tumor_sample_count": len(tumor_numeric),
                "normal_sample_count": len(normal_numeric),
                "p_value": _format_number(p_value),
                "_sort_p_value": p_value,
                "_sort_abs_log2fc": abs(log2_fold_change) if log2_fold_change is not None else -1.0,
            }
        )

    if any(row["_sort_p_value"] is not None for row in result_rows):
        result_rows.sort(
            key=lambda row: (
                row["_sort_p_value"] is None,
                row["_sort_p_value"] if row["_sort_p_value"] is not None else float("inf"),
                -row["_sort_abs_log2fc"],
            )
        )
    else:
        result_rows.sort(key=lambda row: row["_sort_abs_log2fc"], reverse=True)

    output_path = _deg_output_dir(output_dir, manifest_path)
    result_path = output_path / RESULT_FILENAME
    summary_path = output_path / SUMMARY_FILENAME
    public_rows = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in result_rows
    ]
    _write_results(result_path, public_rows)

    summary_parameters = {
        "tumor_labels": list(tumor_labels) if tumor_labels is not None else None,
        "normal_labels": list(normal_labels) if normal_labels is not None else None,
        "min_samples_per_group": min_samples_per_group,
        "pseudocount": pseudocount,
        **dict(parameters or {}),
    }
    summary = {
        "project_id": manifest.get("project_id", ""),
        "batch_id": manifest.get("batch_id", ""),
        "gene_count_tested": len(public_rows),
        "tumor_sample_count": len(tumor_samples),
        "normal_sample_count": len(normal_samples),
        "result_path": str(result_path),
        "summary_path": str(summary_path),
        "warnings": list(dict.fromkeys(warnings)),
        "parameters": summary_parameters,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


__all__ = ["run_tcga_deg_analysis"]

