"""Controlled GEO expression matrix differential analysis runner."""

from __future__ import annotations

import csv
import gzip
import json
import math
import re
import zipfile
from datetime import datetime, timezone
from itertools import chain, combinations
from pathlib import Path
from statistics import NormalDist
from xml.etree import ElementTree


RESULT_FILENAME = "geo_differential_expression_results.csv"
SUMMARY_FILENAME = "geo_differential_expression_summary.json"

DEFAULT_CASE_TERMS = (
    "case",
    "tumor",
    "tumour",
    "cancer",
    "treated",
    "cuet",
    "disease",
    "ptc",
)
DEFAULT_CONTROL_TERMS = (
    "control",
    "normal",
    "healthy",
    "untreated",
    "ut",
    "mock",
    "wildtype",
    "wild_type",
    "wt",
)
ANNOTATION_TOKENS = (
    "chr",
    "chromosome",
    "start",
    "end",
    "strand",
    "gene_name",
    "gene_symbol",
    "symbol",
    "entrez",
    "transcript",
    "description",
    "go",
    "kegg",
    "reactome",
    "do",
    "ko_entry",
    "tf_family",
    "ec",
    "gene_assignment",
    "type",
)
DERIVED_STAT_TOKENS = (
    "fc",
    "fold_change",
    "logfc",
    "log2fc",
    "p_value",
    "pvalue",
    "p_val",
    "adj_p_val",
    "padj",
    "fdr",
    "qvalue",
    "stat",
)


def run_geo_differential_expression(
    expression_path: str | Path,
    *,
    output_dir: str | Path,
    dataset_id: str = "",
    case_terms: tuple[str, ...] | list[str] | None = None,
    control_terms: tuple[str, ...] | list[str] | None = None,
    case_label: str = "case",
    control_label: str = "control",
    min_samples_per_group: int = 1,
    pseudocount: float = 1e-9,
    max_rows: int | None = None,
) -> dict[str, object]:
    """Run a minimal case-vs-control differential expression analysis.

    The runner expects a user-confirmed expression matrix. It infers case/control
    sample columns from column names by default and never downloads external data.
    """

    source = Path(expression_path).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(str(source))
    header, data_rows = _read_matrix(source, max_rows=max_rows)
    if len(header) < 3 or not data_rows:
        raise ValueError("expression matrix is empty or missing sample columns")

    numeric_columns = _numeric_columns(header, data_rows)
    sample_columns = _sample_columns(header, numeric_columns)
    case_indices, control_indices = _infer_group_columns(
        header,
        sample_columns,
        case_terms=tuple(case_terms or DEFAULT_CASE_TERMS),
        control_terms=tuple(control_terms or DEFAULT_CONTROL_TERMS),
    )
    if len(case_indices) < min_samples_per_group or len(control_indices) < min_samples_per_group:
        raise ValueError("case/control sample columns could not be inferred from expression matrix")

    statistical_engine = (
        "scipy_welch_t_test"
        if _try_ttest([1.0, 2.0], [1.0, 2.0]) is not None
        else "standard_library_permutation_or_welch_approx"
    )
    result_rows: list[dict[str, object]] = []
    skipped = 0
    for row in data_rows:
        gene_id = str(row[0]).strip()
        if not gene_id:
            skipped += 1
            continue
        case_values = [_as_float(row[index]) for index in case_indices if index < len(row)]
        control_values = [_as_float(row[index]) for index in control_indices if index < len(row)]
        case_numeric = [value for value in case_values if value is not None]
        control_numeric = [value for value in control_values if value is not None]
        if len(case_numeric) < min_samples_per_group or len(control_numeric) < min_samples_per_group:
            skipped += 1
            continue
        case_mean = _mean(case_numeric)
        control_mean = _mean(control_numeric)
        ratio = (case_mean + pseudocount) / (control_mean + pseudocount)
        log2fc = math.log2(ratio) if ratio > 0 else None
        p_value = _compute_p_value(case_numeric, control_numeric, statistical_engine)
        result_rows.append(
            {
                "gene_id": gene_id,
                "case_mean": case_mean,
                "control_mean": control_mean,
                "log2_fold_change": log2fc,
                "mean_difference": case_mean - control_mean,
                "case_sample_count": len(case_numeric),
                "control_sample_count": len(control_numeric),
                "p_value": p_value,
            }
        )
    adjusted = _benjamini_hochberg([row["p_value"] for row in result_rows])
    for row, adj in zip(result_rows, adjusted, strict=False):
        row["adjusted_p_value"] = adj
    result_rows.sort(
        key=lambda row: (
            row["p_value"] is None,
            row["p_value"] if row["p_value"] is not None else float("inf"),
            -abs(float(row["log2_fold_change"] or 0.0)),
        )
    )

    target = Path(output_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    result_path = target / RESULT_FILENAME
    summary_path = target / SUMMARY_FILENAME
    _write_results(result_path, result_rows)
    summary = {
        "schema_version": "biomedpilot.geo_differential_expression.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset_id": dataset_id or _dataset_id_from_path(source),
        "source_expression_path": str(source),
        "result_path": str(result_path),
        "summary_path": str(summary_path),
        "formal_deg_executed": True,
        "network_used": False,
        "statistical_engine": statistical_engine,
        "case_label": case_label,
        "control_label": control_label,
        "case_samples": [header[index] for index in case_indices],
        "control_samples": [header[index] for index in control_indices],
        "gene_count_tested": len(result_rows),
        "row_count_skipped": skipped,
        "warnings": (
            []
            if statistical_engine == "scipy_welch_t_test"
            else ["scipy_unavailable_used_standard_library_statistics"]
        ),
        "parameters": {
            "case_terms": list(case_terms or DEFAULT_CASE_TERMS),
            "control_terms": list(control_terms or DEFAULT_CONTROL_TERMS),
            "min_samples_per_group": min_samples_per_group,
            "pseudocount": pseudocount,
        },
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def _read_matrix(path: Path, *, max_rows: int | None = None) -> tuple[list[str], list[list[str]]]:
    if path.suffix.lower() == ".xlsx":
        rows = _xlsx_rows(path, max_rows=max_rows)
    else:
        rows = _delimited_rows(path, max_rows=max_rows)
    rows = [[str(cell).strip().strip('"') for cell in row] for row in rows if any(str(cell).strip() for cell in row)]
    if not rows:
        return [], []
    return rows[0], [row for row in rows[1:] if len(row) >= 2 and str(row[0]).strip()]


def _delimited_rows(path: Path, *, max_rows: int | None = None) -> list[list[str]]:
    opener = gzip.open if path.name.lower().endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="ignore", newline="") as handle:
        first = handle.readline()
        if not first:
            return []
        delimiter = "\t" if first.count("\t") >= first.count(",") else ","
        reader = csv.reader(chain([first], handle), delimiter=delimiter)
        rows: list[list[str]] = []
        for row in reader:
            rows.append(row)
            if max_rows is not None and len(rows) >= max_rows + 1:
                break
    return rows


def _xlsx_rows(path: Path, *, max_rows: int | None = None, max_cells: int = 10000) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        worksheet_name = "xl/worksheets/sheet1.xml"
        if worksheet_name not in names:
            return []
        shared_strings = _xlsx_shared_strings(archive, names)
        worksheet = ElementTree.fromstring(archive.read(worksheet_name))
        parsed_rows: list[list[str]] = []
        for row in worksheet.findall(".//{*}sheetData/{*}row"):
            values_by_column: dict[int, str] = {}
            for cell in list(row.findall("{*}c"))[:max_cells]:
                column_index = _xlsx_column_index(str(cell.attrib.get("r", "")))
                values_by_column[column_index] = _xlsx_cell_value(cell, shared_strings)
            if values_by_column:
                parsed_rows.append([values_by_column.get(index, "") for index in range(max(values_by_column) + 1)])
            if max_rows is not None and len(parsed_rows) >= max_rows + 1:
                break
        return parsed_rows


def _xlsx_shared_strings(archive: zipfile.ZipFile, names: set[str]) -> list[str]:
    if "xl/sharedStrings.xml" not in names:
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall(".//{*}si"):
        values.append("".join(text.text or "" for text in item.findall(".//{*}t")))
    return values


def _xlsx_cell_value(cell: ElementTree.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//{*}t"))
    raw = cell.find("{*}v")
    value = raw.text if raw is not None and raw.text is not None else ""
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (ValueError, IndexError):
            return value
    return value


def _xlsx_column_index(reference: str) -> int:
    letters = "".join(character for character in reference if character.isalpha())
    index = 0
    for character in letters.upper():
        index = index * 26 + (ord(character) - ord("A") + 1)
    return max(index - 1, 0)


def _numeric_columns(header: list[str], rows: list[list[str]]) -> set[int]:
    numeric_columns: set[int] = set()
    for index in range(1, len(header)):
        values = [row[index] for row in rows[:250] if index < len(row)]
        if not values:
            continue
        numeric = sum(1 for value in values if _as_float(value) is not None)
        if numeric / max(len(values), 1) >= 0.7:
            numeric_columns.add(index)
    return numeric_columns


def _sample_columns(header: list[str], numeric_columns: set[int]) -> list[int]:
    candidates = [index for index in sorted(numeric_columns) if not _is_non_sample_column(header[index])]
    fpkm_columns = [index for index in candidates if "fpkm" in _normalize(header[index])]
    if fpkm_columns:
        return fpkm_columns
    tpm_columns = [index for index in candidates if "tpm" in _normalize(header[index])]
    if tpm_columns:
        return tpm_columns
    return candidates


def _is_non_sample_column(column_name: str) -> bool:
    normalized = _normalize(column_name)
    if normalized in {"", "id", "id_ref", "gene", "genes", "gene_id", "geneid", "rowname"}:
        return True
    if normalized in DERIVED_STAT_TOKENS:
        return True
    if any(token == normalized or normalized.startswith(f"{token}_") for token in DERIVED_STAT_TOKENS):
        return True
    if any(token == normalized or normalized.startswith(f"{token}_") or normalized.endswith(f"_{token}") for token in ANNOTATION_TOKENS):
        return True
    return False


def _infer_group_columns(
    header: list[str],
    sample_columns: list[int],
    *,
    case_terms: tuple[str, ...],
    control_terms: tuple[str, ...],
) -> tuple[list[int], list[int]]:
    case_indices: list[int] = []
    control_indices: list[int] = []
    for index in sample_columns:
        normalized = _normalize(header[index])
        if _matches_any(normalized, control_terms):
            control_indices.append(index)
        elif _matches_any(normalized, case_terms):
            case_indices.append(index)
    return case_indices, control_indices


def _matches_any(normalized: str, terms: tuple[str, ...]) -> bool:
    tokens = [token for token in re.split(r"[_:.\-\s+]+", normalized) if token]
    for term in terms:
        candidate = _normalize(term)
        if not candidate:
            continue
        if candidate in tokens:
            return True
        if len(candidate) >= 4 and candidate in normalized:
            return True
    return False


def _normalize(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in str(value)).strip("_")


def _as_float(value: object) -> float | None:
    try:
        numeric = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if math.isnan(numeric):
        return None
    return numeric


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _try_ttest(case_values: list[float], control_values: list[float]) -> float | None:
    try:
        from scipy import stats  # type: ignore
    except Exception:
        return None
    try:
        result = stats.ttest_ind(case_values, control_values, equal_var=False, nan_policy="omit")
    except Exception:
        return None
    try:
        value = float(result.pvalue)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(value) else value


def _compute_p_value(case_values: list[float], control_values: list[float], statistical_engine: str) -> float | None:
    if statistical_engine == "scipy_welch_t_test":
        return _try_ttest(case_values, control_values)
    total = len(case_values) + len(control_values)
    if total <= 12:
        return _permutation_p_value(case_values, control_values)
    return _welch_normal_approx_p_value(case_values, control_values)


def _permutation_p_value(case_values: list[float], control_values: list[float]) -> float | None:
    case_count = len(case_values)
    all_values = [*case_values, *control_values]
    if case_count == 0 or case_count == len(all_values):
        return None
    observed = abs(_mean(case_values) - _mean(control_values))
    total = 0
    extreme = 0
    all_indices = tuple(range(len(all_values)))
    for case_indices in combinations(all_indices, case_count):
        case_set = set(case_indices)
        perm_case = [all_values[index] for index in case_indices]
        perm_control = [all_values[index] for index in all_indices if index not in case_set]
        diff = abs(_mean(perm_case) - _mean(perm_control))
        total += 1
        if diff >= observed - 1e-12:
            extreme += 1
    return extreme / total if total else None


def _welch_normal_approx_p_value(case_values: list[float], control_values: list[float]) -> float | None:
    if len(case_values) < 2 or len(control_values) < 2:
        return None
    case_var = _sample_variance(case_values)
    control_var = _sample_variance(control_values)
    standard_error = math.sqrt(case_var / len(case_values) + control_var / len(control_values))
    if standard_error == 0:
        return None
    z_value = abs(_mean(case_values) - _mean(control_values)) / standard_error
    return 2 * (1 - NormalDist().cdf(z_value))


def _sample_variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    return sum((value - mean) ** 2 for value in values) / (len(values) - 1)


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


def _write_results(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "gene_id",
        "case_mean",
        "control_mean",
        "log2_fold_change",
        "mean_difference",
        "case_sample_count",
        "control_sample_count",
        "p_value",
        "adjusted_p_value",
    ]
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
        if re.fullmatch(r"GSE\d+", part, flags=re.IGNORECASE):
            return part.upper()
    match = re.search(r"GSE\d+", path.name, flags=re.IGNORECASE)
    return match.group(0).upper() if match else path.stem


__all__ = ["run_geo_differential_expression"]
