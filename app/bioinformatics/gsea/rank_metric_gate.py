from __future__ import annotations

import csv
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import (
    ADJUSTED_P_COLUMN_ALIASES,
    ALLOWED_DUPLICATE_GENE_POLICIES,
    ALLOWED_RANK_METRICS,
    GENE_COLUMN_ALIASES,
    GSEA_RANK_METRIC_SCHEMA_VERSION,
    LOG2FC_COLUMN_ALIASES,
    P_VALUE_COLUMN_ALIASES,
    STATISTIC_COLUMN_ALIASES,
)


def build_gsea_rank_metric_gate(
    project_root: str | Path,
    *,
    source_result_id: str = "",
    source_deg_table: str | Path = "",
    source_gene_id_type: str = "unknown",
    rank_metric: str = "signed_log10_fdr_by_log2fc",
    custom_rank_column: str = "",
    duplicate_gene_policy: str = "keep_max_abs_rank",
    missing_gene_policy: str = "drop_missing_gene_id",
    minimum_ranked_gene_count: int = 10,
    direction_sign_policy: str = "positive_rank_upregulated",
    write_ranked_list: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    table = Path(source_deg_table).expanduser() if source_deg_table else Path()
    table = table if table.is_absolute() else root / table
    blockers: list[str] = []
    warnings: list[str] = []
    ranked_rows: list[tuple[str, float]] = []
    duplicate_count = 0
    if rank_metric not in ALLOWED_RANK_METRICS:
        blockers.append(f"gsea_rank_metric_not_allowed:{rank_metric or 'missing'}")
    if duplicate_gene_policy not in ALLOWED_DUPLICATE_GENE_POLICIES:
        blockers.append("gsea_duplicate_gene_policy_invalid")
    if not direction_sign_policy:
        blockers.append("gsea_direction_sign_policy_missing")
    if source_gene_id_type in {"", "unknown"}:
        blockers.append("gsea_rank_gene_id_type_unknown_or_unmapped")
    if minimum_ranked_gene_count <= 0:
        blockers.append("gsea_minimum_ranked_gene_count_invalid")
    rows = _read_table(table)
    if not rows:
        blockers.append("gsea_source_deg_table_missing_or_empty")
    else:
        header = set(rows[0].keys())
        gene_column = _first_present(header, GENE_COLUMN_ALIASES)
        metric_columns = _metric_columns(header, rank_metric, custom_rank_column=custom_rank_column)
        if not gene_column:
            blockers.append("gsea_rank_gene_column_missing")
        for column_name, column_value in metric_columns.items():
            if not column_value:
                blockers.append(f"gsea_rank_metric_column_missing:{column_name}")
        if not blockers:
            raw_ranked: list[tuple[str, float]] = []
            missing_gene_count = 0
            non_numeric_count = 0
            for row in rows:
                gene = str(row.get(gene_column) or "").strip()
                if not gene:
                    missing_gene_count += 1
                    continue
                rank_value = _rank_value(row, rank_metric, metric_columns)
                if rank_value is None:
                    non_numeric_count += 1
                    continue
                raw_ranked.append((gene, rank_value))
            if missing_gene_count:
                warnings.append(f"gsea_rank_rows_dropped_missing_gene:{missing_gene_count}")
            if non_numeric_count:
                blockers.append(f"gsea_rank_non_numeric_values:{non_numeric_count}")
            ranked_rows, duplicate_count = _dedupe(raw_ranked, policy=duplicate_gene_policy)
            if duplicate_count:
                warnings.append(f"gsea_rank_duplicate_genes_handled:{duplicate_gene_policy}:{duplicate_count}")
                if duplicate_gene_policy == "fail":
                    blockers.append("gsea_rank_duplicate_genes_not_allowed")
            if len(ranked_rows) < minimum_ranked_gene_count:
                blockers.append(f"gsea_ranked_gene_count_below_minimum:{len(ranked_rows)}<{minimum_ranked_gene_count}")
            numeric_values = [value for _gene, value in ranked_rows]
            if numeric_values and all(abs(value) == 0 for value in numeric_values):
                blockers.append("gsea_rank_metric_all_zero")
            if not numeric_values:
                blockers.append("gsea_rank_metric_all_na")
    ranked_gene_list_path = ""
    if not blockers and write_ranked_list:
        ranked_gene_list_path = _write_ranked_list(root, source_result_id=source_result_id, rank_metric=rank_metric, ranked_rows=ranked_rows)
    return {
        "schema_version": GSEA_RANK_METRIC_SCHEMA_VERSION,
        "created_at": _now(),
        "status": "blocked" if blockers else "passed",
        "source_result_id": source_result_id,
        "source_deg_table": str(table),
        "rank_metric": rank_metric,
        "rank_metric_policy": "preranked_metric_gate_only_no_gsea_execution",
        "custom_rank_column": custom_rank_column,
        "ranked_gene_list_path": ranked_gene_list_path,
        "ranked_gene_count": len(ranked_rows),
        "duplicate_gene_count": duplicate_count,
        "duplicate_gene_policy": duplicate_gene_policy,
        "missing_gene_policy": missing_gene_policy,
        "minimum_ranked_gene_count": minimum_ranked_gene_count,
        "direction_sign_policy": direction_sign_policy,
        "source_gene_id_type": source_gene_id_type,
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
    }


def _read_table(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        first = handle.readline()
        delimiter = "," if first.count(",") > first.count("\t") else "\t"
        return [dict(row) for row in csv.DictReader([first, *handle.readlines()], delimiter=delimiter)]


def _metric_columns(header: set[str], rank_metric: str, *, custom_rank_column: str) -> dict[str, str]:
    if rank_metric == "signed_log10_fdr_by_log2fc":
        return {"log2_fold_change": _first_present(header, LOG2FC_COLUMN_ALIASES), "adjusted_p_value": _first_present(header, ADJUSTED_P_COLUMN_ALIASES)}
    if rank_metric == "signed_log10_pvalue_by_log2fc":
        return {"log2_fold_change": _first_present(header, LOG2FC_COLUMN_ALIASES), "p_value": _first_present(header, P_VALUE_COLUMN_ALIASES)}
    if rank_metric == "log2_fold_change":
        return {"log2_fold_change": _first_present(header, LOG2FC_COLUMN_ALIASES)}
    if rank_metric == "statistic":
        return {"statistic": _first_present(header, STATISTIC_COLUMN_ALIASES)}
    if rank_metric == "custom_rank_column":
        return {"custom_rank_column": custom_rank_column if custom_rank_column in header else ""}
    return {}


def _rank_value(row: dict[str, str], rank_metric: str, columns: dict[str, str]) -> float | None:
    if rank_metric == "signed_log10_fdr_by_log2fc":
        log2fc = _float(row.get(columns.get("log2_fold_change", "")))
        fdr = _float(row.get(columns.get("adjusted_p_value", "")))
        if log2fc is None or fdr is None:
            return None
        return _sign(log2fc) * -math.log10(max(fdr, 1e-300))
    if rank_metric == "signed_log10_pvalue_by_log2fc":
        log2fc = _float(row.get(columns.get("log2_fold_change", "")))
        p_value = _float(row.get(columns.get("p_value", "")))
        if log2fc is None or p_value is None:
            return None
        return _sign(log2fc) * -math.log10(max(p_value, 1e-300))
    column = next(iter(columns.values()), "")
    return _float(row.get(column))


def _dedupe(rows: list[tuple[str, float]], *, policy: str) -> tuple[list[tuple[str, float]], int]:
    seen: dict[str, float] = {}
    duplicate_count = 0
    for gene, value in rows:
        if gene in seen:
            duplicate_count += 1
            if policy == "fail":
                continue
            if policy == "keep_max_abs_rank" and abs(value) > abs(seen[gene]):
                seen[gene] = value
        else:
            seen[gene] = value
    if policy == "fail" and duplicate_count:
        return [], duplicate_count
    return sorted(seen.items(), key=lambda item: item[1], reverse=True), duplicate_count


def _write_ranked_list(root: Path, *, source_result_id: str, rank_metric: str, ranked_rows: list[tuple[str, float]]) -> str:
    path = root / "analysis" / "gsea" / "preranked" / f"{_safe_name(source_result_id or 'gsea')}_{_safe_name(rank_metric)}.rnk"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        for gene, value in ranked_rows:
            writer.writerow([gene, f"{value:.12g}"])
    return str(path.relative_to(root))


def _first_present(header: set[str], aliases: tuple[str, ...]) -> str:
    lookup = {name.lower(): name for name in header}
    for alias in aliases:
        if alias in header:
            return alias
        if alias.lower() in lookup:
            return lookup[alias.lower()]
    return ""


def _float(value: object) -> float | None:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) else number


def _sign(value: float) -> float:
    return -1.0 if value < 0 else 1.0


def _safe_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in value) or "gsea"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
