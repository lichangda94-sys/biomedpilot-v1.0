"""Module 2: process GEO full family SOFT or an already parsed GSE object."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import GEOparse
import numpy as np
import pandas as pd

from .common import (
    is_gse_like,
    normalize_accession,
    save_json,
    standardize_column_name,
)


LOGGER = logging.getLogger("geo_process")


class ProcessModuleError(Exception):
    """Base exception for the processing module."""


class MetadataParseError(ProcessModuleError):
    """Raised when phenotype metadata cannot be built or summarized."""


class MatrixBuildError(ProcessModuleError):
    """Raised when an expression matrix cannot be built."""


class AnnotationError(ProcessModuleError):
    """Raised when GPL annotation fails."""


class CleaningError(ProcessModuleError):
    """Raised when expression cleaning fails."""


@dataclass
class ProcessConfig:
    accession: str
    outdir: str
    geo_dir: str
    values_column: str = "VALUE"
    gsm_index_col: str = "ID_REF"
    gpl_probe_col: str = "ID"
    gpl_gene_col: Optional[str] = None
    merge_probe_to_gene: bool = True
    gene_agg_method: str = "mean"
    log2_transform: Optional[bool] = None
    drop_na_gene: bool = True
    drop_duplicate_gene: bool = False


@dataclass
class DatasetStructure:
    accession: str
    experiment_type: str
    sample_count: int
    platform_ids: list[str]
    has_sample_table: bool
    sample_table_column_names: list[str]
    has_id_ref: bool
    has_value: bool
    candidate_expression_columns: list[str]
    has_platform_annotation: bool
    supplementary_files: list[str]
    matrix_strategy: str
    matrix_skip_reason: Optional[str] = None


def load_full_family_soft(filepath: str) -> Any:
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        raise ProcessModuleError(f"Family SOFT file does not exist: {path}")
    if path.suffix == ".txt":
        raise ProcessModuleError(
            f"Quick text file is not allowed as processing input: {path}"
        )

    try:
        gse = GEOparse.get_GEO(filepath=str(path), silent=False)
    except Exception as exc:
        raise ProcessModuleError(f"Failed to parse family SOFT from {path}") from exc

    if not is_gse_like(gse):
        raise ProcessModuleError(f"Input file did not parse into a GSE object: {path}")
    if not getattr(gse, "gsms", None):
        raise ProcessModuleError(f"GSE object has no GSM samples: {path}")
    return gse


def build_phenotype_table(gse: Any) -> pd.DataFrame:
    try:
        pheno = gse.phenotype_data.copy()
    except Exception as exc:
        raise MetadataParseError("Failed to access gse.phenotype_data") from exc

    if pheno is None or pheno.empty:
        raise MetadataParseError("Phenotype table is empty")

    index_name = pheno.index.name or "sample_id"
    pheno = pheno.copy()
    pheno.index = pheno.index.map(str)
    pheno.index.name = standardize_column_name(index_name)
    pheno = pheno.reset_index()
    pheno.columns = [standardize_column_name(col) for col in pheno.columns]

    if "sample_id" not in pheno.columns:
        first_col = pheno.columns[0]
        pheno = pheno.rename(columns={first_col: "sample_id"})

    return pheno


def infer_group_column(pheno: pd.DataFrame) -> Optional[str]:
    if pheno.empty:
        return None

    priorities = ["group", "condition", "treatment", "source_name", "title", "characteristics"]
    columns = list(pheno.columns)
    for keyword in priorities:
        for col in columns:
            if keyword in col and pheno[col].notna().sum() > 0:
                return col
    return None


def summarize_groups(pheno: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if group_col not in pheno.columns:
        raise MetadataParseError(f"Group column not found in phenotype table: {group_col}")
    return (
        pheno[group_col]
        .fillna("NA")
        .astype(str)
        .value_counts(dropna=False)
        .rename_axis("group")
        .reset_index(name="sample_count")
    )


def build_expression_matrix(gse: Any, values_column: str, gsm_index_col: str) -> pd.DataFrame:
    try:
        expr = gse.pivot_samples(values=values_column, index=gsm_index_col)
    except Exception as exc:
        raise MatrixBuildError(
            f"Failed to build expression matrix from pivot_samples(values={values_column}, index={gsm_index_col})"
        ) from exc

    if expr is None or expr.empty:
        raise MatrixBuildError("Expression matrix is empty")
    if expr.shape[0] < 1 or expr.shape[1] < 1:
        raise MatrixBuildError(f"Expression matrix has unreasonable shape: {expr.shape}")

    expr = expr.copy()
    expr.index = expr.index.map(str)
    expr.columns = expr.columns.map(str)
    expr.index.name = gsm_index_col
    return expr


def inspect_gse_tables(gse: Any, values_column: str, gsm_index_col: str) -> dict[str, Any]:
    sample_columns: dict[str, list[str]] = {}
    union_columns: list[str] = []
    has_id_ref = False
    has_value = False
    for gsm_name, gsm in (getattr(gse, "gsms", {}) or {}).items():
        table = getattr(gsm, "table", None)
        if table is None:
            continue
        columns = [str(col) for col in table.columns]
        sample_columns[str(gsm_name)] = columns
        for col in columns:
            if col not in union_columns:
                union_columns.append(col)
        has_id_ref = has_id_ref or gsm_index_col in columns
        has_value = has_value or values_column in columns
    return {
        "sample_table_columns_by_gsm": sample_columns,
        "sample_table_columns_union": union_columns,
        "has_sample_table": any(bool(cols) for cols in sample_columns.values()),
        "has_id_ref": has_id_ref,
        "has_value": has_value,
    }


def infer_experiment_type(gse: Any) -> str:
    metadata = getattr(gse, "metadata", {}) or {}
    values = metadata.get("type") or []
    if isinstance(values, list) and values:
        return "; ".join(str(v) for v in values if v)
    return ""


def collect_supplementary_files(gse: Any) -> list[str]:
    files: list[str] = []
    metadata = getattr(gse, "metadata", {}) or {}
    for value in metadata.get("supplementary_file", []) or []:
        text = str(value).strip()
        if text and text != "NONE" and text not in files:
            files.append(text)
    for gsm in (getattr(gse, "gsms", {}) or {}).values():
        gsm_meta = getattr(gsm, "metadata", {}) or {}
        for value in gsm_meta.get("supplementary_file", []) or []:
            text = str(value).strip()
            if text and text != "NONE" and text not in files:
                files.append(text)
    return files


def identify_dataset_structure(gse: Any, accession: str, values_column: str, gsm_index_col: str) -> DatasetStructure:
    table_info = inspect_gse_tables(gse, values_column, gsm_index_col)
    experiment_type = infer_experiment_type(gse)
    platform_ids = list((getattr(gse, "gpls", {}) or {}).keys())
    supplementary_files = collect_supplementary_files(gse)

    candidate_expression_columns = []
    for col in table_info["sample_table_columns_union"]:
        upper = str(col).upper()
        if upper in {gsm_index_col.upper(), values_column.upper()}:
            continue
        if any(token in upper for token in ["VALUE", "COUNT", "SIGNAL", "INTENSITY", "EXPR", "FPKM", "TPM", "CPM"]):
            candidate_expression_columns.append(col)

    if table_info["has_id_ref"] and table_info["has_value"]:
        strategy = "standard_id_ref_value"
        skip_reason = None
    elif table_info["has_sample_table"] and candidate_expression_columns:
        strategy = "candidate_expression_columns"
        skip_reason = None
    else:
        strategy = "skip_matrix_build"
        if not table_info["has_sample_table"]:
            skip_reason = "sample table 缺失或为空"
        elif not table_info["sample_table_columns_union"]:
            skip_reason = "sample table 没有可用列"
        else:
            skip_reason = "缺少标准列 ID_REF/VALUE，且未识别到可替代表达列"

    return DatasetStructure(
        accession=accession,
        experiment_type=experiment_type,
        sample_count=len(getattr(gse, "gsms", {}) or {}),
        platform_ids=platform_ids,
        has_sample_table=table_info["has_sample_table"],
        sample_table_column_names=table_info["sample_table_columns_union"],
        has_id_ref=table_info["has_id_ref"],
        has_value=table_info["has_value"],
        candidate_expression_columns=candidate_expression_columns,
        has_platform_annotation=bool(platform_ids),
        supplementary_files=supplementary_files,
        matrix_strategy=strategy,
        matrix_skip_reason=skip_reason,
    )


def build_basic_metadata_summary(gse: Any, accession: str, filepath: Optional[str] = None) -> dict[str, Any]:
    gpls = getattr(gse, "gpls", {}) or {}
    return {
        "accession": accession,
        "input_source": filepath,
        "series_name": getattr(gse, "name", None),
        "n_samples": len(getattr(gse, "gsms", {}) or {}),
        "platform_ids": list(gpls.keys()),
        "n_platforms": len(gpls),
    }


def ensure_numeric_matrix(df: pd.DataFrame) -> pd.DataFrame:
    try:
        return df.apply(pd.to_numeric, errors="coerce")
    except Exception as exc:
        raise CleaningError("Failed to convert expression matrix to numeric values") from exc


def auto_detect_log2_needed(df: pd.DataFrame) -> bool:
    values = df.to_numpy(dtype=float, copy=False)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return False
    max_value = float(np.nanmax(finite_values))
    q1 = float(np.nanquantile(finite_values, 0.25))
    return max_value > 100 or q1 > 16


def log2_transform(df: pd.DataFrame) -> pd.DataFrame:
    try:
        return np.log2(df + 1)
    except Exception as exc:
        raise CleaningError("Failed to apply log2 transform") from exc


def drop_all_na_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(axis=0, how="all")


def drop_duplicate_genes(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df.index.duplicated(keep="first")]


def basic_clean_expression(
    expr: pd.DataFrame,
    log2_transform_flag: Optional[bool],
    drop_duplicate_gene_rows: bool,
) -> tuple[pd.DataFrame, bool]:
    try:
        clean_expr = ensure_numeric_matrix(expr)
        clean_expr = drop_all_na_rows(clean_expr)
        applied_log2 = False

        if log2_transform_flag is None:
            applied_log2 = auto_detect_log2_needed(clean_expr)
            if applied_log2:
                clean_expr = log2_transform(clean_expr)
        elif log2_transform_flag:
            clean_expr = log2_transform(clean_expr)
            applied_log2 = True

        clean_expr = drop_all_na_rows(clean_expr)
        if drop_duplicate_gene_rows:
            clean_expr = drop_duplicate_genes(clean_expr)
        if clean_expr.empty:
            raise CleaningError("Expression matrix became empty after cleaning")
    except ProcessModuleError:
        raise
    except Exception as exc:
        raise CleaningError("Failed during basic expression cleaning") from exc

    return clean_expr, applied_log2


def get_single_gpl(gse: Any) -> Any:
    gpls = getattr(gse, "gpls", {}) or {}
    if not gpls:
        raise AnnotationError("No GPL objects found in GSE")
    first_key = next(iter(gpls))
    return gpls[first_key]


def detect_gene_symbol_column(gpl: Any, fallback_column: Optional[str] = None) -> tuple[Optional[str], str]:
    if not hasattr(gpl, "table") or gpl.table is None or gpl.table.empty:
        return None, "GPL table is missing or empty"

    columns = [str(col) for col in gpl.table.columns]
    if fallback_column:
        for col in columns:
            if col == fallback_column:
                return col, "manual_override"
        return None, f"Manual GPL gene column not found: {fallback_column}"

    preferred_names = {
        "gene symbol",
        "genesymbol",
        "gene_symbol",
        "symbol",
        "official gene symbol",
    }
    normalized_map = {re.sub(r"[^a-z0-9]+", "", col.lower()): col for col in columns}
    for normalized, original in normalized_map.items():
        if normalized in {re.sub(r"[^a-z0-9]+", "", name) for name in preferred_names}:
            return original, "header_match"

    best_col: Optional[str] = None
    best_score = 0.0
    for col in columns:
        series = gpl.table[col].dropna().astype(str).str.strip()
        if series.empty:
            continue
        sample = series.head(200)
        valid = sample[
            sample.str.len().between(2, 15)
            & sample.str.match(r"^[A-Za-z0-9._-]+$", na=False)
            & ~sample.str.contains(r"\s", na=False)
        ]
        upperish = valid[valid.str.match(r"^[A-Z0-9._-]+$", na=False)]
        score = float(len(upperish)) / float(len(sample)) if len(sample) else 0.0
        if score > best_score and score >= 0.45:
            best_score = score
            best_col = col

    if best_col:
        return best_col, f"content_inference(score={best_score:.2f})"
    return None, "No suitable gene symbol column detected"


def annotate_expression_matrix(
    expr: pd.DataFrame,
    gpl: Any,
    probe_col: str,
    gene_col: str,
    expr_index_col: str,
) -> pd.DataFrame:
    if not hasattr(gpl, "table") or gpl.table is None or gpl.table.empty:
        raise AnnotationError("GPL table is missing or empty")
    if probe_col not in gpl.table.columns:
        raise AnnotationError(f"Probe column not found in GPL table: {probe_col}")
    if gene_col not in gpl.table.columns:
        raise AnnotationError(f"Gene column not found in GPL table: {gene_col}")

    try:
        expr_reset = expr.reset_index()
        annotation = gpl.table[[probe_col, gene_col]].copy()
        annotated = expr_reset.merge(
            annotation,
            how="left",
            left_on=expr_index_col,
            right_on=probe_col,
        )
        if probe_col in annotated.columns:
            annotated = annotated.drop(columns=[probe_col])
    except Exception as exc:
        raise AnnotationError("Failed to merge expression matrix with GPL annotation") from exc

    return annotated


def aggregate_to_gene(
    annotated_expr: pd.DataFrame,
    gene_col: str,
    sample_columns: list[str],
    method: str,
    drop_na_gene: bool,
) -> pd.DataFrame:
    method = method.lower()
    if method not in {"mean", "median", "max"}:
        raise AnnotationError(f"Unsupported gene aggregation method: {method}")

    try:
        work = annotated_expr.copy()
        gene_series = work[gene_col].astype(str).str.strip()
        if drop_na_gene:
            mask = gene_series.notna() & (gene_series != "") & (gene_series.str.lower() != "nan")
            work = work.loc[mask].copy()
            gene_series = gene_series.loc[mask]
        if work.empty:
            raise AnnotationError("No rows left for gene aggregation after filtering gene symbols")

        work[gene_col] = gene_series
        numeric_expr = work[sample_columns].apply(pd.to_numeric, errors="coerce")
        grouped = numeric_expr.groupby(work[gene_col])
        if method == "mean":
            gene_df = grouped.mean()
        elif method == "median":
            gene_df = grouped.median()
        else:
            gene_df = grouped.max()
        gene_df.index.name = "gene_symbol"
    except ProcessModuleError:
        raise
    except Exception as exc:
        raise AnnotationError("Failed during probe-to-gene aggregation") from exc

    if gene_df.empty:
        raise AnnotationError("Gene-level expression matrix is empty after aggregation")
    return gene_df


def build_run_summary(
    accession: str,
    input_source: str,
    outdir: Path,
    gse: Any,
    expr_probe_clean: pd.DataFrame,
    group_column_guess: Optional[str],
    expr_gene_level: Optional[pd.DataFrame],
    status: str,
) -> dict[str, Any]:
    return {
        "accession": accession,
        "input_source": input_source,
        "outdir": str(outdir),
        "geo_type": getattr(gse, "__class__", type(None)).__name__,
        "n_samples": len(getattr(gse, "gsms", {}) or {}),
        "n_probe_rows": int(expr_probe_clean.shape[0]),
        "n_probe_cols": int(expr_probe_clean.shape[1]),
        "group_column_guess": group_column_guess,
        "n_gene_rows": int(expr_gene_level.shape[0]) if expr_gene_level is not None else None,
        "n_gene_cols": int(expr_gene_level.shape[1]) if expr_gene_level is not None else None,
        "status": status,
    }


def process_from_gse_object(gse: Any, config: ProcessConfig) -> dict[str, Any]:
    if not is_gse_like(gse):
        raise ProcessModuleError(f"Input object is not a GSE-like object: {type(gse)!r}")
    if not getattr(gse, "gsms", None):
        raise ProcessModuleError("GSE object has no GSM samples")

    try:
        accession = normalize_accession(config.accession)
    except ValueError as exc:
        raise ProcessModuleError(str(exc)) from exc

    outdir = Path(config.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("[PROCESS] accession=%s start processing", accession)

    pheno = build_phenotype_table(gse)
    pheno.to_csv(outdir / "phenotype_table.csv", index=False)
    LOGGER.info("[PROCESS] accession=%s metadata parsed, n_samples=%s", accession, len(pheno))

    group_col = infer_group_column(pheno)
    if group_col:
        summarize_groups(pheno, group_col).to_csv(outdir / "group_summary.csv", index=False)

    structure = identify_dataset_structure(gse, accession, config.values_column, config.gsm_index_col)
    metadata_summary = build_basic_metadata_summary(gse, accession)
    metadata_summary.update(
        {
            "experiment_type": structure.experiment_type,
            "sample_table_columns_union": structure.sample_table_column_names,
            "has_sample_table": structure.has_sample_table,
            "has_id_ref": structure.has_id_ref,
            "has_value": structure.has_value,
            "candidate_expression_columns": structure.candidate_expression_columns,
            "has_platform_annotation": structure.has_platform_annotation,
            "supplementary_files": structure.supplementary_files,
            "matrix_strategy": structure.matrix_strategy,
            "matrix_skip_reason": structure.matrix_skip_reason,
        }
    )
    save_json(metadata_summary, outdir / "metadata_summary.json")
    LOGGER.info(
        "[PROCESS] accession=%s experiment_type=%s sample_count=%s platform=%s sample_table_columns=%s has_id_ref=%s has_value=%s strategy=%s",
        accession,
        structure.experiment_type,
        structure.sample_count,
        structure.platform_ids,
        structure.sample_table_column_names,
        structure.has_id_ref,
        structure.has_value,
        structure.matrix_strategy,
    )

    expr_probe_raw: Optional[pd.DataFrame] = None
    expr_probe_clean: Optional[pd.DataFrame] = None
    probe_log2_applied = False
    expr_annotated: Optional[pd.DataFrame] = None
    expr_gene_level: Optional[pd.DataFrame] = None
    resolved_gpl_gene_col: Optional[str] = None
    gpl_gene_col_detection: Optional[str] = None
    matrix_build_success = False
    matrix_build_skipped = False
    matrix_build_failed = False
    matrix_build_error: Optional[str] = None
    status = "metadata_parse_success"
    matrix_strategy = structure.matrix_strategy
    if structure.matrix_strategy == "skip_matrix_build":
        matrix_build_skipped = True
        matrix_build_error = structure.matrix_skip_reason
        status = "matrix_build_skipped"
        LOGGER.warning("[PROCESS] accession=%s matrix skipped: %s", accession, matrix_build_error)
    else:
        try:
            values_column = config.values_column
            if structure.matrix_strategy == "candidate_expression_columns":
                values_column = structure.candidate_expression_columns[0]
                LOGGER.info(
                    "[PROCESS] accession=%s using candidate expression column=%s",
                    accession,
                    values_column,
                )
            expr_probe_raw = build_expression_matrix(
                gse=gse,
                values_column=values_column,
                gsm_index_col=config.gsm_index_col,
            )
            expr_probe_raw.to_csv(outdir / "expression_probe_raw.csv")
            expr_probe_clean, probe_log2_applied = basic_clean_expression(
                expr=expr_probe_raw,
                log2_transform_flag=config.log2_transform,
                drop_duplicate_gene_rows=False,
            )
            expr_probe_clean.to_csv(outdir / "expression_probe_clean.csv")
            matrix_build_success = True
            status = "expression_matrix_success"
            LOGGER.info(
                "[PROCESS] accession=%s matrix built successfully shape=%s",
                accession,
                expr_probe_clean.shape,
            )
        except MatrixBuildError as exc:
            matrix_build_error = str(exc)
            matrix_build_failed = True
            status = "matrix_build_failed"
            LOGGER.warning("[PROCESS] accession=%s matrix build failed: %s", accession, exc)
        except Exception as exc:
            matrix_build_error = f"Unexpected matrix build error: {exc}"
            matrix_build_failed = True
            status = "matrix_build_failed"
            LOGGER.warning("[PROCESS] accession=%s matrix build failed: %s", accession, exc)

    if matrix_build_success and expr_probe_clean is not None:
        try:
            gpl = get_single_gpl(gse)
            resolved_gpl_gene_col, gpl_gene_col_detection = detect_gene_symbol_column(gpl, config.gpl_gene_col)
            LOGGER.info(
                "[PROCESS] accession=%s GPL gene column resolved=%s via %s",
                accession,
                resolved_gpl_gene_col,
                gpl_gene_col_detection,
            )
            if resolved_gpl_gene_col:
                expr_annotated = annotate_expression_matrix(
                    expr=expr_probe_clean,
                    gpl=gpl,
                    probe_col=config.gpl_probe_col,
                    gene_col=resolved_gpl_gene_col,
                    expr_index_col=config.gsm_index_col,
                )
                expr_annotated.to_csv(outdir / "expression_annotated.csv", index=False)
                if config.merge_probe_to_gene:
                    expr_gene_level = aggregate_to_gene(
                        annotated_expr=expr_annotated,
                        gene_col=resolved_gpl_gene_col,
                        sample_columns=list(expr_probe_clean.columns),
                        method=config.gene_agg_method,
                        drop_na_gene=config.drop_na_gene,
                    )
                    expr_gene_level, _ = basic_clean_expression(
                        expr=expr_gene_level,
                        log2_transform_flag=False if probe_log2_applied else config.log2_transform,
                        drop_duplicate_gene_rows=config.drop_duplicate_gene,
                    )
                    expr_gene_level.to_csv(outdir / "expression_gene_level.csv")
            else:
                LOGGER.warning(
                    "[PROCESS] accession=%s GPL gene column auto-detect failed: %s",
                    accession,
                    gpl_gene_col_detection,
                )
        except AnnotationError as exc:
            gpl_gene_col_detection = f"annotation_failed: {exc}"
            LOGGER.warning("[PROCESS] accession=%s annotation skipped: %s", accession, exc)
        except Exception as exc:
            gpl_gene_col_detection = f"annotation_failed: {exc}"
            LOGGER.warning("[PROCESS] accession=%s annotation skipped: %s", accession, exc)

    run_summary = build_run_summary(
        accession=accession,
        input_source="gse_object",
        outdir=outdir,
        gse=gse,
        expr_probe_clean=expr_probe_clean if expr_probe_clean is not None else pd.DataFrame(),
        group_column_guess=group_col,
        expr_gene_level=expr_gene_level,
        status=status,
    )
    run_summary["download_success"] = True
    run_summary["metadata_parse_success"] = True
    run_summary["expression_matrix_success"] = matrix_build_success
    run_summary["matrix_build_success"] = matrix_build_success
    run_summary["matrix_build_skipped"] = matrix_build_skipped
    run_summary["matrix_build_failed"] = matrix_build_failed
    run_summary["expression_matrix_error"] = matrix_build_error
    run_summary["files_preserved"] = True
    run_summary["platform_ids"] = structure.platform_ids
    run_summary["experiment_type"] = structure.experiment_type
    run_summary["sample_table_columns_union"] = structure.sample_table_column_names
    run_summary["has_sample_table"] = structure.has_sample_table
    run_summary["has_id_ref"] = structure.has_id_ref
    run_summary["has_value"] = structure.has_value
    run_summary["candidate_expression_columns"] = structure.candidate_expression_columns
    run_summary["supplementary_files"] = structure.supplementary_files
    run_summary["matrix_build_strategy"] = matrix_strategy
    run_summary["matrix_skip_reason"] = structure.matrix_skip_reason
    run_summary["probe_log2_applied"] = probe_log2_applied
    run_summary["annotation_performed"] = expr_annotated is not None
    run_summary["gene_level_generated"] = expr_gene_level is not None
    run_summary["resolved_gpl_gene_col"] = resolved_gpl_gene_col
    run_summary["gpl_gene_col_detection"] = gpl_gene_col_detection
    run_summary["manual_gpl_gene_col"] = config.gpl_gene_col
    save_json(run_summary, outdir / "run_summary.json")
    return run_summary


def process_from_local_family_soft(filepath: str, config: ProcessConfig) -> dict[str, Any]:
    gse = load_full_family_soft(filepath)
    summary = process_from_gse_object(gse, config)
    summary["input_source"] = str(Path(filepath).expanduser().resolve())
    save_json(summary, Path(config.outdir).expanduser().resolve() / "run_summary.json")
    return summary


def run_processing_pipeline(input_source: Any, config: ProcessConfig) -> dict[str, Any]:
    if isinstance(input_source, (str, Path)):
        return process_from_local_family_soft(str(input_source), config)
    return process_from_gse_object(input_source, config)
