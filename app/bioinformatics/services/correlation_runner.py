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

from app.analysis_runtime.task_bridge import run_analysis_module_task


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
    """Run lite expression correlation through the standard analysis task bridge."""

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
    target_dir = Path(output_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    result_id = f"correlation_{uuid4().hex[:10]}"
    root = Path(project_root).expanduser().resolve() if project_root is not None else target_dir.parent
    bridge_input_path = target_dir / "task_bridge_expression.tsv"
    _write_task_bridge_expression_matrix(bridge_input_path, header, rows)
    dataset = dataset_id or _dataset_id_from_path(source)
    bridge_result = run_analysis_module_task(
        root,
        {
            "schema_version": "biomedpilot.analysis.module_input.v1",
            "module_id": "correlation",
            "mode": "lite",
            "task_id": result_id,
            "project_id": dataset or root.name,
            "inputs": {
                "input_package_id": dataset,
                "source_dataset_id": dataset,
                "expression_matrix_path": str(bridge_input_path),
            },
            "parameters": {
                "analysis_family": "expression_correlation",
                "method": "base_r_pearson_correlation_fixture",
                "target_gene": target,
                "max_results": int(max_results or 200),
                "clinical_conclusion_policy": "not_generated",
            },
            "runtime": {"random_seed": 7, "requested_environment": "r-bio-core-lite"},
        },
        output_dir=target_dir / "standard_result_package",
        worker_backend="rscript",
    )
    standard_package_dir = Path(str(bridge_result["result_package_dir"]))
    result_path = standard_package_dir / "tables" / "lite_correlation_result.tsv"
    result_rows = _read_result_table(result_path) if result_path.is_file() else []
    tested_rows = [
        row
        for row in result_rows
        if not _same_gene(row.get("feature_id", ""), target) and _table_float(row.get("correlation")) is not None
    ]
    result_entry = bridge_result.get("result_entry") if isinstance(bridge_result.get("result_entry"), dict) else {}
    summary_path = standard_package_dir / "logs" / CORRELATION_SUMMARY_FILENAME
    summary = {
        "schema_version": "biomedpilot.correlation_results.v1",
        "result_id": str(result_entry.get("result_id") or f"analysis-package-{result_id}"),
        "task_run_id": result_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset_id": dataset,
        "source_expression_path": str(source),
        "task_bridge_expression_path": str(bridge_input_path),
        "target_gene": target,
        "result_path": str(result_path),
        "summary_path": str(summary_path),
        "standard_result_package_dir": str(standard_package_dir),
        "correlation_executed": bridge_result.get("status") == "passed",
        "network_used": False,
        "method": "pearson",
        "sample_count": sum(1 for value in target_values if value is not None),
        "gene_count_tested": len(tested_rows),
        "row_count_skipped": max(0, len(rows) - len(tested_rows) - 1),
        "returned_result_count": len(result_rows),
        "worker_backend": "rscript",
        "worker_boundary_type": "standard_r_worker",
        "task_system_invocation": "task_center_registered",
        "result_semantics": "testing_level",
        "report_ready_eligible": False,
        "clinical_conclusion_status": "not_generated",
        "blockers": list(bridge_result.get("blockers", [])),
        "warnings": list(bridge_result.get("warnings", [])),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


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


def _write_task_bridge_expression_matrix(path: Path, header: list[str], rows: list[list[str]]) -> None:
    fieldnames = ["feature_id", *header[1:]]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(fieldnames)
        for row in rows:
            writer.writerow([row[0], *[row[index] if index < len(row) else "" for index in range(1, len(header))]])


def _read_result_table(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def _table_float(value: object) -> float | None:
    text = str(value or "").strip()
    if not text or text.upper() == "NA":
        return None
    return _safe_float(text)


def _dataset_id_from_path(path: Path) -> str:
    for part in path.parts:
        if part.upper().startswith("GSE"):
            return part.upper()
    return path.stem


__all__ = ["run_expression_correlation"]
