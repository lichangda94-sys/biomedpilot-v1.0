from __future__ import annotations

import csv
import gzip
from pathlib import Path
from typing import Any


def read_expression_matrix(path: str | Path, *, gene_id_column: str | None = None) -> tuple[list[dict[str, str]], str, list[str]]:
    matrix_path = Path(path).expanduser().resolve()
    opener = gzip.open if matrix_path.name.lower().endswith(".gz") else open
    with opener(matrix_path, "rt", encoding="utf-8-sig", newline="") as handle:  # type: ignore[arg-type]
        sample = handle.readline()
        delimiter = "," if sample.count(",") > sample.count("\t") else "\t"
        handle.seek(0)
        reader = csv.DictReader(handle, delimiter=delimiter)
        fieldnames = [str(item or "").strip() for item in reader.fieldnames or []]
        gene_col = gene_id_column or _guess_gene_column(fieldnames)
        sample_columns = [field for field in fieldnames if field and field != gene_col]
        rows = [{str(key or "").strip(): str(value or "").strip() for key, value in row.items()} for row in reader]
    return rows, gene_col, sample_columns


def matrix_profile(path: str | Path) -> dict[str, Any]:
    try:
        rows, gene_col, sample_columns = read_expression_matrix(path)
    except Exception as exc:
        return {"status": "failed", "error": str(exc), "gene_id_column": "", "sample_columns": [], "gene_count": 0, "sample_count": 0}
    genes = [str(row.get(gene_col) or "").strip() for row in rows if str(row.get(gene_col) or "").strip()]
    return {
        "status": "ok" if genes and sample_columns else "blocked",
        "gene_id_column": gene_col,
        "sample_columns": sample_columns,
        "gene_count": len(genes),
        "sample_count": len(sample_columns),
        "gene_id_type": guess_gene_id_type(genes[:50]),
    }


def guess_gene_id_type(values: list[str]) -> str:
    normalized = [value.strip().upper() for value in values if value.strip()]
    if not normalized:
        return "unknown"
    if sum(1 for value in normalized if value.startswith("ENSG")) >= max(1, len(normalized) // 2):
        return "ensembl"
    if sum(1 for value in normalized if value.isdigit()) >= max(1, len(normalized) // 2):
        return "entrez"
    return "symbol"


def normalize_value_type(value: object, *, asset_type: str = "") -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if asset_type == "raw_count_matrix":
        return "raw_counts"
    if text in {"tpm"}:
        return "TPM"
    if text in {"fpkm"}:
        return "FPKM"
    if text in {"fpkm_uq", "fpkm_uq_unstranded", "fpkm-uq"}:
        return "FPKM-UQ"
    if text in {"normalized", "normalized_expression", "normalized_or_log_expression"}:
        return "normalized_expression"
    if text in {"log2", "log2_expression", "log2_transformed", "log_expression"}:
        return "log2_expression"
    if text in {"microarray", "microarray_normalized"}:
        return "microarray_normalized"
    if text in {"count", "counts", "raw_count", "raw_counts", "count_like_candidate"}:
        return "raw_counts"
    return "unknown"


def value_type_policy(value_type: str) -> dict[str, object]:
    normalized = normalize_value_type(value_type)
    if normalized in {"TPM", "normalized_expression", "log2_expression"}:
        return {"value_type": normalized, "status": "recommended", "can_run": True, "message": "推荐用于 bulk immune / TME signature scoring。"}
    if normalized in {"FPKM", "FPKM-UQ", "microarray_normalized"}:
        return {"value_type": normalized, "status": "usable", "can_run": True, "message": "可用于探索性 bulk immune / TME signature scoring。"}
    if normalized == "raw_counts":
        return {"value_type": normalized, "status": "blocked", "can_run": False, "message": "raw counts 默认不用于 B7 scoring；请使用 TPM/FPKM/标准化或 log 表达矩阵。"}
    return {"value_type": "unknown", "status": "blocked", "can_run": False, "message": "表达值类型未知，当前无 override，不默认运行 B7 scoring。"}


def _guess_gene_column(fieldnames: list[str]) -> str:
    for candidate in ("gene_id", "gene", "gene_name", "symbol", "id", "ID_REF"):
        for field in fieldnames:
            if field.lower() == candidate.lower():
                return field
    return fieldnames[0] if fieldnames else "gene_id"


__all__ = ["guess_gene_id_type", "matrix_profile", "normalize_value_type", "read_expression_matrix", "value_type_policy"]
