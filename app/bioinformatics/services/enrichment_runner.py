"""Local over-representation enrichment runner for confirmed DEG results."""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ENRICHMENT_RESULTS_FILENAME = "enrichment_results.csv"
ENRICHMENT_SUMMARY_FILENAME = "enrichment_summary.json"


def run_over_representation_enrichment(
    deg_result_path: str | Path,
    gmt_path: str | Path,
    *,
    output_dir: str | Path,
    dataset_id: str = "",
    adjusted_p_value_cutoff: float = 0.05,
    log2_fold_change_cutoff: float = 1.0,
) -> dict[str, object]:
    """Run a small local ORA against a user-supplied GMT file.

    This runner intentionally does not download GO/KEGG/MSigDB. It consumes a
    confirmed differential expression result table and an explicit GMT file.
    """

    deg_path = Path(deg_result_path).expanduser().resolve()
    gene_set_path = Path(gmt_path).expanduser().resolve()
    if not deg_path.is_file():
        raise FileNotFoundError(str(deg_path))
    if not gene_set_path.is_file():
        raise FileNotFoundError(str(gene_set_path))

    deg_rows = _read_deg_rows(deg_path)
    all_genes = {row["gene_id"] for row in deg_rows if row.get("gene_id")}
    significant_genes = {
        row["gene_id"]
        for row in deg_rows
        if row.get("gene_id")
        and _safe_float(row.get("adjusted_p_value", "")) is not None
        and _safe_float(row.get("adjusted_p_value", "")) <= adjusted_p_value_cutoff  # type: ignore[operator]
        and abs(_safe_float(row.get("log2_fold_change", "")) or 0.0) >= log2_fold_change_cutoff
    }
    if not all_genes:
        raise ValueError("差异表达结果中没有可用 gene_id。")
    gene_sets = _read_gmt(gene_set_path)
    rows: list[dict[str, object]] = []
    for term_name, description, genes in gene_sets:
        term_genes = set(genes)
        overlap = significant_genes & term_genes
        if not overlap:
            continue
        background_hits = len(all_genes & term_genes)
        if background_hits == 0:
            continue
        p_value = _hypergeom_tail(
            population_size=len(all_genes),
            success_in_population=background_hits,
            draw_count=len(significant_genes),
            observed_success=len(overlap),
        )
        rows.append(
            {
                "term_name": term_name,
                "description": description,
                "overlap_count": len(overlap),
                "term_gene_count_in_background": background_hits,
                "significant_gene_count": len(significant_genes),
                "background_gene_count": len(all_genes),
                "p_value": p_value,
                "overlap_genes": ";".join(sorted(overlap)),
            }
        )
    adjusted = _benjamini_hochberg([row["p_value"] for row in rows])
    for row, value in zip(rows, adjusted, strict=False):
        row["adjusted_p_value"] = value
    rows.sort(key=lambda row: (float(row.get("adjusted_p_value") or 1.0), float(row.get("p_value") or 1.0), str(row.get("term_name") or "")))

    target = Path(output_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    result_path = target / ENRICHMENT_RESULTS_FILENAME
    summary_path = target / ENRICHMENT_SUMMARY_FILENAME
    _write_rows(result_path, rows)
    summary = {
        "schema_version": "biomedpilot.enrichment_results.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset_id": dataset_id or _dataset_id_from_path(deg_path),
        "deg_result_path": str(deg_path),
        "gmt_path": str(gene_set_path),
        "result_path": str(result_path),
        "summary_path": str(summary_path),
        "enrichment_executed": True,
        "network_used": False,
        "database_download_executed": False,
        "background_gene_count": len(all_genes),
        "significant_gene_count": len(significant_genes),
        "tested_gene_set_count": len(gene_sets),
        "enriched_term_count": len(rows),
        "parameters": {
            "adjusted_p_value_cutoff": adjusted_p_value_cutoff,
            "log2_fold_change_cutoff": log2_fold_change_cutoff,
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _read_deg_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            gene = str(row.get("gene_id") or row.get("gene") or row.get("symbol") or "").strip()
            if not gene:
                continue
            normalized = {str(key): str(value).strip() for key, value in row.items() if key is not None}
            normalized["gene_id"] = gene
            rows.append(normalized)
        return rows


def _read_gmt(path: Path) -> list[tuple[str, str, list[str]]]:
    gene_sets: list[tuple[str, str, list[str]]] = []
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = [part.strip() for part in line.rstrip("\n").split("\t")]
            if len(parts) < 3:
                continue
            genes = [gene for gene in parts[2:] if gene]
            if genes:
                gene_sets.append((parts[0], parts[1], genes))
    return gene_sets


def _hypergeom_tail(*, population_size: int, success_in_population: int, draw_count: int, observed_success: int) -> float:
    if observed_success <= 0 or population_size <= 0 or draw_count <= 0 or success_in_population <= 0:
        return 1.0
    denominator = math.comb(population_size, draw_count)
    if denominator == 0:
        return 1.0
    max_success = min(success_in_population, draw_count)
    total = 0
    for successes in range(observed_success, max_success + 1):
        failures = draw_count - successes
        if failures > population_size - success_in_population:
            continue
        total += math.comb(success_in_population, successes) * math.comb(population_size - success_in_population, failures)
    return min(1.0, total / denominator)


def _benjamini_hochberg(values: list[object]) -> list[float | None]:
    indexed = [(index, float(value)) for index, value in enumerate(values) if value is not None]
    adjusted: list[float | None] = [None] * len(values)
    if not indexed:
        return adjusted
    indexed.sort(key=lambda item: item[1], reverse=True)
    total = len(indexed)
    running = 1.0
    for rank_from_end, (index, p_value) in enumerate(indexed, start=1):
        rank = total - rank_from_end + 1
        running = min(running, p_value * total / rank)
        adjusted[index] = min(running, 1.0)
    return adjusted


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "term_name",
        "description",
        "overlap_count",
        "term_gene_count_in_background",
        "significant_gene_count",
        "background_gene_count",
        "p_value",
        "adjusted_p_value",
        "overlap_genes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _format(row.get(field)) for field in fieldnames})


def _safe_float(value: object) -> float | None:
    try:
        numeric = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return None if math.isnan(numeric) else numeric


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


__all__ = ["run_over_representation_enrichment"]
