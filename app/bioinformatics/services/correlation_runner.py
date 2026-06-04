"""Local expression correlation runner."""

from __future__ import annotations

import csv
import gzip
import json
import math
from datetime import datetime, timezone
from itertools import chain
from pathlib import Path
from uuid import uuid4

from app.bioinformatics.results.models import ResultIndexEntry
from app.bioinformatics.results.registry import register_result

from .correlation_standard_package import write_correlation_standard_result_package


CORRELATION_RESULTS_FILENAME = "correlation_results.csv"
CORRELATION_SUMMARY_FILENAME = "correlation_summary.json"


def run_expression_correlation(
    expression_path: str | Path,
    *,
    target_gene: str,
    output_dir: str | Path,
    dataset_id: str = "",
    max_results: int = 200,
    project_root: str | Path | None = None,
) -> dict[str, object]:
    """Compute Pearson correlation against a target gene across sample columns."""

    source = Path(expression_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(str(source))
    target = target_gene.strip()
    if not target:
        raise ValueError("请先填写目标基因。")
    header, rows = _read_matrix(source)
    if len(header) < 3 or not rows:
        raise ValueError("表达矩阵为空或样本列不足。")
    sample_indices = list(range(1, len(header)))
    target_row = next((row for row in rows if _same_gene(row[0], target)), None)
    if target_row is None:
        raise ValueError(f"未在表达矩阵中找到目标基因：{target}")
    target_values = [_safe_float(target_row[index]) if index < len(target_row) else None for index in sample_indices]
    results: list[dict[str, object]] = []
    skipped = 0
    for row in rows:
        gene = str(row[0]).strip()
        if not gene or _same_gene(gene, target):
            continue
        values = [_safe_float(row[index]) if index < len(row) else None for index in sample_indices]
        paired = [(x, y) for x, y in zip(target_values, values, strict=False) if x is not None and y is not None]
        if len(paired) < 3:
            skipped += 1
            continue
        x_values = [item[0] for item in paired]
        y_values = [item[1] for item in paired]
        coefficient = _pearson(x_values, y_values)
        if coefficient is None:
            skipped += 1
            continue
        results.append(
            {
                "gene_id": gene,
                "target_gene": target,
                "pearson_r": coefficient,
                "absolute_r": abs(coefficient),
                "sample_count": len(paired),
            }
        )
    results.sort(key=lambda row: (-float(row["absolute_r"]), str(row["gene_id"])))
    limited = results[: max(1, int(max_results or 200))]
    target_dir = Path(output_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    result_id = f"correlation_{uuid4().hex[:10]}"
    result_path = target_dir / CORRELATION_RESULTS_FILENAME
    summary_path = target_dir / CORRELATION_SUMMARY_FILENAME
    _write_rows(result_path, limited)
    summary = {
        "schema_version": "biomedpilot.correlation_results.v1",
        "result_id": result_id,
        "task_run_id": result_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset_id": dataset_id or _dataset_id_from_path(source),
        "source_expression_path": str(source),
        "target_gene": target,
        "result_path": str(result_path),
        "summary_path": str(summary_path),
        "correlation_executed": True,
        "network_used": False,
        "method": "pearson",
        "sample_count": sum(1 for value in target_values if value is not None),
        "gene_count_tested": len(results),
        "row_count_skipped": skipped,
        "returned_result_count": len(limited),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    root = Path(project_root).expanduser().resolve() if project_root is not None else target_dir.parent
    standard_package_dir = write_correlation_standard_result_package(
        root,
        result_id=result_id,
        result_path=result_path,
        summary_path=summary_path,
        summary=summary,
    )
    summary["standard_result_package_dir"] = str(standard_package_dir)
    _register_standard_correlation_result(root, summary, result_path, summary_path, standard_package_dir)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _register_standard_correlation_result(root: Path, summary: dict[str, object], result_path: Path, summary_path: Path, standard_package_dir: Path) -> None:
    result_id = str(summary.get("result_id") or "")
    now = str(summary.get("generated_at") or datetime.now(timezone.utc).isoformat(timespec="seconds"))
    entry = ResultIndexEntry(
        result_id=result_id,
        task_run_id=str(summary.get("task_run_id") or result_id),
        task_type="analysis:correlation",
        result_semantics="testing_level",
        input_package_id=str(summary.get("dataset_id") or ""),
        source_dataset_id=str(summary.get("dataset_id") or ""),
        source_repository_manifest=str(summary.get("source_expression_path") or ""),
        parameters_manifest={
            "schema_version": "biomedpilot.correlation_parameter_manifest.v1",
            "dataset_id": summary.get("dataset_id") or "",
            "target_gene": summary.get("target_gene") or "",
            "method": summary.get("method") or "pearson",
            "max_results_returned": summary.get("returned_result_count") or 0,
        },
        engine_name="biomedpilot_local_pearson_correlation",
        engine_version="1",
        dependency_snapshot={"mode": "lite", "runtime": "python_standard_library", "heavy_r_dependencies": "not_used"},
        output_artifacts=(
            {"artifact_type": "correlation_result_table", "path": _relative_or_absolute(root, result_path), "schema": "biomedpilot.correlation_result_table.v1"},
            {"artifact_type": "correlation_summary", "path": _relative_or_absolute(root, summary_path), "schema": "biomedpilot.correlation_results.v1"},
            {"artifact_type": "standard_result_package", "path": _relative_or_absolute(root, standard_package_dir), "schema": "biomedpilot.analysis.result_package.v1"},
        ),
        plot_artifacts=(),
        report_artifacts=(),
        validation_status="passed",
        warnings=("testing_level_local_pearson_correlation", "clinical_conclusion_not_generated"),
        blockers=(),
        log_artifacts=(
            {"artifact_type": "correlation_summary", "path": _relative_or_absolute(root, summary_path)},
            {
                "artifact_type": "analysis_worker_invocation_manifest",
                "path": _relative_or_absolute(root, standard_package_dir / "logs" / "worker_invocation.json"),
                "schema": "biomedpilot.analysis.worker_invocation.v1",
            },
        ),
        failure_reason="",
        created_at=now,
        updated_at=now,
        report_ready_eligible=False,
        migration_status="legacy_service_adapter_sidecar",
    )
    register_result(root, entry)


def _read_matrix(path: Path) -> tuple[list[str], list[list[str]]]:
    if "series_matrix" in path.name.lower():
        rows = _geo_series_matrix_rows(path)
        rows = [[str(cell).strip().strip('"') for cell in row] for row in rows if any(str(cell).strip() for cell in row)]
        if not rows:
            return [], []
        return rows[0], [row for row in rows[1:] if len(row) >= 2 and str(row[0]).strip()]
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as handle:
        first = handle.readline()
        if not first:
            return [], []
        delimiter = "\t" if first.count("\t") >= first.count(",") else ","
        reader = csv.reader(chain([first], handle), delimiter=delimiter)
        rows = [[str(cell).strip().strip('"') for cell in row] for row in reader if any(str(cell).strip() for cell in row)]
    if not rows:
        return [], []
    return rows[0], [row for row in rows[1:] if len(row) >= 2 and str(row[0]).strip()]


def _geo_series_matrix_rows(path: Path) -> list[list[str]]:
    rows: list[list[str]] = []
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as handle:
        in_table = False
        for line in handle:
            stripped = line.rstrip("\n")
            if stripped.startswith("!series_matrix_table_begin"):
                in_table = True
                continue
            if stripped.startswith("!series_matrix_table_end"):
                break
            if not in_table or not stripped:
                continue
            rows.append(next(csv.reader([stripped], delimiter="\t")))
    return rows


def _same_gene(value: object, target: str) -> bool:
    return _normalize_gene(value) == _normalize_gene(target)


def _normalize_gene(value: object) -> str:
    text = str(value).strip().upper()
    return text.split(".", 1)[0]


def _safe_float(value: object) -> float | None:
    try:
        numeric = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return None if math.isnan(numeric) else numeric


def _pearson(x_values: list[float], y_values: list[float]) -> float | None:
    if len(x_values) != len(y_values) or len(x_values) < 3:
        return None
    x_mean = sum(x_values) / len(x_values)
    y_mean = sum(y_values) / len(y_values)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=False))
    x_den = math.sqrt(sum((x - x_mean) ** 2 for x in x_values))
    y_den = math.sqrt(sum((y - y_mean) ** 2 for y in y_values))
    denominator = x_den * y_den
    if denominator == 0:
        return None
    return numerator / denominator


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = ["gene_id", "target_gene", "pearson_r", "absolute_r", "sample_count"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _format(row.get(field)) for field in fieldnames})


def _format(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def _dataset_id_from_path(path: Path) -> str:
    for part in path.parts:
        if part.upper().startswith("GSE"):
            return part.upper()
    return path.stem


def _relative_or_absolute(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


__all__ = ["run_expression_correlation"]
