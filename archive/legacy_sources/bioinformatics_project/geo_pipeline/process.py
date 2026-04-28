"""Module 2: process GEO full family SOFT or an already parsed GSE object."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import GEOparse
import numpy as np
import pandas as pd

from .common import (
    configure_logging,
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
    recommended_strategy: Optional[str] = None
    value_type_hint: Optional[str] = None
    values_column: str = "VALUE"
    gsm_index_col: str = "ID_REF"
    gpl_probe_col: str = "ID"
    gpl_gene_col: Optional[str] = None
    merge_probe_to_gene: bool = True
    gene_agg_method: str = "mean"
    log2_transform: Optional[bool] = None
    drop_na_gene: bool = True
    drop_duplicate_gene: bool = False


def load_full_family_soft(filepath: str) -> Any:
    path = Path(filepath).expanduser().resolve()
    LOGGER.info("Loading full family SOFT from %s", path)
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
    LOGGER.info("Building phenotype table")
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
    LOGGER.info("Inferring group column")
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
    LOGGER.info("Summarizing groups using column: %s", group_col)
    if group_col not in pheno.columns:
        raise MetadataParseError(f"Group column not found in phenotype table: {group_col}")

    summary = (
        pheno[group_col]
        .fillna("NA")
        .astype(str)
        .value_counts(dropna=False)
        .rename_axis("group")
        .reset_index(name="sample_count")
    )
    return summary


def build_expression_matrix(gse: Any, values_column: str, gsm_index_col: str) -> pd.DataFrame:
    LOGGER.info(
        "Building probe-level expression matrix with values=%s index=%s",
        values_column,
        gsm_index_col,
    )
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


def _resolve_dataset_root(config: ProcessConfig) -> Path:
    geo_dir = Path(config.geo_dir).expanduser().resolve()
    outdir = Path(config.outdir).expanduser().resolve()
    if geo_dir.name == "geo_downloads" and geo_dir.parent.name == "raw_downloads":
        return geo_dir.parent.parent
    if geo_dir.name == "raw_downloads":
        return geo_dir.parent
    return outdir


def _pick_column(pheno: pd.DataFrame, *, exact: tuple[str, ...] = (), contains: tuple[str, ...] = ()) -> Optional[str]:
    columns = [str(col) for col in pheno.columns]
    for name in exact:
        if name in pheno.columns:
            return name
    for keyword in contains:
        for column in columns:
            if keyword in column:
                return column
    return None


def _text_series(pheno: pd.DataFrame, column: Optional[str], *, default: str) -> pd.Series:
    if column is None or column not in pheno.columns:
        return pd.Series([default] * len(pheno), index=pheno.index, dtype="object")
    series = pheno[column].fillna("").astype(str).str.strip()
    return series.where(series != "", default)


def _metadata_first_text(gse: Any, *keys: str, default: str = "unknown") -> str:
    metadata = getattr(gse, "metadata", {}) or {}
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, list) and value:
            text = str(value[0]).strip()
            if text:
                return text
        elif value is not None:
            text = str(value).strip()
            if text:
                return text
    return default


def _single_platform_id(gse: Any) -> str:
    gpls = getattr(gse, "gpls", {}) or {}
    if len(gpls) == 1:
        return str(next(iter(gpls))).strip() or "unknown"
    return "unknown"


def build_sample_annotation(
    pheno: pd.DataFrame,
    *,
    accession: str,
    gse: Any,
    group_column_guess: Optional[str],
) -> pd.DataFrame:
    sample_id_series = _text_series(
        pheno,
        "sample_id" if "sample_id" in pheno.columns else pheno.columns[0],
        default="unknown_sample",
    )
    subject_column = _pick_column(pheno, exact=("subject_id",), contains=("subject", "patient", "donor"))
    sample_type_column = _pick_column(pheno, exact=("sample_type",), contains=("sample_type", "cell_type"))
    condition_column = _pick_column(pheno, exact=("condition",), contains=("condition", "status", "phenotype"))
    tissue_column = _pick_column(pheno, exact=("tissue",), contains=("tissue", "source_name", "organ"))
    disease_column = _pick_column(pheno, exact=("disease",), contains=("disease", "diagnosis", "subtype"))
    organism_column = _pick_column(pheno, exact=("organism",), contains=("organism", "species"))
    platform_column = _pick_column(pheno, exact=("platform_id", "platform"), contains=("platform", "gpl"))
    batch_column = _pick_column(pheno, exact=("batch_id", "batch"), contains=("batch",))
    source_name_column = _pick_column(pheno, exact=("source_name",), contains=("source_name", "title"))
    characteristics_columns = [str(column) for column in pheno.columns if "characteristics" in str(column)]

    platform_default = _single_platform_id(gse)
    organism_default = _metadata_first_text(gse, "organism", "organism_ch1")
    source_name_series = _text_series(pheno, source_name_column, default="unknown")
    raw_characteristics = pd.Series([""] * len(pheno), index=pheno.index, dtype="object")
    if characteristics_columns:
        raw_characteristics = pheno[characteristics_columns].fillna("").astype(str).agg(
            lambda row: " | ".join(value.strip() for value in row if value.strip()),
            axis=1,
        )

    sample_annotation = pd.DataFrame(
        {
            "sample_id": sample_id_series,
            "source_sample_id": sample_id_series,
            "subject_id": _text_series(pheno, subject_column, default="unknown"),
            "sample_type": _text_series(pheno, sample_type_column, default="unknown"),
            "group": _text_series(pheno, group_column_guess, default="unknown"),
            "condition": _text_series(pheno, condition_column or group_column_guess, default="unknown"),
            "tissue": _text_series(pheno, tissue_column, default="unknown"),
            "disease": _text_series(pheno, disease_column, default="unknown"),
            "organism": _text_series(pheno, organism_column, default=organism_default),
            "platform_id": _text_series(pheno, platform_column, default=platform_default),
            "batch_id": _text_series(pheno, batch_column, default="unknown"),
            "source_dataset": accession,
            "source_name": source_name_series,
            "raw_characteristics": raw_characteristics.fillna("").astype(str),
        }
    )
    return sample_annotation


def _map_value_semantic(value_type_hint: Optional[str], probe_log2_applied: bool) -> str:
    hint = str(value_type_hint or "").strip().lower()
    if probe_log2_applied or hint in {"log2", "log2_expression"}:
        return "log2_expression"
    if hint in {"count", "counts", "raw_counts"}:
        return "raw_counts"
    if hint in {"normalized", "normalized_counts"}:
        return "normalized_counts"
    return "unknown"


def _infer_technology_type(gse: Any, config: ProcessConfig) -> str:
    gpls = getattr(gse, "gpls", {}) or {}
    if gpls:
        return "microarray"
    values_column = str(config.values_column).strip().lower()
    if values_column in {"count", "counts", "raw_count", "raw_counts"}:
        return "bulk_rnaseq"
    return "unknown"


def build_dataset_manifest(
    *,
    accession: str,
    input_source: str,
    dataset_root: Path,
    gse: Any,
    config: ProcessConfig,
    sample_annotation: Optional[pd.DataFrame],
    expr_probe_clean: Optional[pd.DataFrame],
    result: dict[str, Any],
) -> dict[str, Any]:
    parsed_root = dataset_root / "parsed"
    organized_root = dataset_root / "organized"
    sample_id_order: list[str]
    if sample_annotation is not None and not sample_annotation.empty:
        sample_id_order = [str(value) for value in sample_annotation["sample_id"].tolist()]
    elif expr_probe_clean is not None:
        sample_id_order = [str(value) for value in expr_probe_clean.columns.tolist()]
    else:
        sample_id_order = []

    written_assets = dict(result.get("standard_assets_written") or {})
    warnings: list[str] = []
    if not written_assets.get("expression_gene"):
        warnings.append("organized/expression_gene.tsv.gz not generated in phase-1 writer")
    if not written_assets.get("feature_annotation"):
        warnings.append("organized/feature_annotation.tsv not generated in phase-1 writer")

    build_status = "failed"
    if written_assets.get("sample_annotation") or result.get("parsed_outputs", {}).get("expression_matrix"):
        build_status = "partial_success"
    if written_assets.get("sample_annotation") and written_assets.get("expression_gene"):
        build_status = "success"

    return {
        "contract_version": "v1",
        "dataset_id": accession,
        "source_db": "GEO",
        "source_accession": accession,
        "dataset_root": str(dataset_root),
        "raw_root": str(dataset_root / "raw_downloads"),
        "parsed_root": str(parsed_root),
        "organized_root": str(organized_root),
        "technology_type": _infer_technology_type(gse, config),
        "matrix_level": "probe" if expr_probe_clean is not None else "unknown",
        "value_semantic": _map_value_semantic(config.value_type_hint, bool(result.get("probe_log2_applied"))),
        "is_log_scale": bool(result.get("probe_log2_applied")),
        "expression_unit": "unknown",
        "sample_count": len(sample_id_order),
        "feature_count": int(expr_probe_clean.shape[0]) if expr_probe_clean is not None else 0,
        "sample_id_order": sample_id_order,
        "asset_paths": written_assets,
        "build_status": build_status,
        "recommended_strategy": str(config.recommended_strategy or "MANUAL_REVIEW_REQUIRED"),
        "title": _metadata_first_text(gse, "title", default=accession),
        "organism": (
            str(sample_annotation["organism"].iloc[0]).strip()
            if sample_annotation is not None and not sample_annotation.empty
            else _metadata_first_text(gse, "organism", "organism_ch1")
        ),
        "platform_ids": sorted(
            {
                str(value).strip()
                for value in (
                    sample_annotation["platform_id"].tolist()
                    if sample_annotation is not None and "platform_id" in sample_annotation.columns
                    else [_single_platform_id(gse)]
                )
                if str(value).strip() and str(value).strip() != "unknown"
            }
        ),
        "has_clinical_outcome": False,
        "has_feature_annotation": bool(written_assets.get("feature_annotation")),
        "has_comparison_config": False,
        "warnings": warnings,
        "provenance": {
            "input_source": input_source,
            "metadata_parse_success": bool(result.get("metadata_parse_success")),
            "expression_matrix_success": bool(result.get("expression_matrix_success")),
            "annotation_performed": bool(result.get("annotation_performed")),
            "gene_level_generated": bool(result.get("gene_level_generated")),
        },
    }


def write_phase1_processing_assets(
    *,
    accession: str,
    input_source: str,
    gse: Any,
    config: ProcessConfig,
    pheno: Optional[pd.DataFrame],
    expr_probe_clean: Optional[pd.DataFrame],
    group_column_guess: Optional[str],
    result: dict[str, Any],
) -> dict[str, Any]:
    dataset_root = _resolve_dataset_root(config)
    parsed_root = dataset_root / "parsed"
    organized_root = dataset_root / "organized"
    parsed_root.mkdir(parents=True, exist_ok=True)
    organized_root.mkdir(parents=True, exist_ok=True)

    parsed_outputs: dict[str, str] = {}
    standard_assets_written: dict[str, str] = {}
    sample_annotation: Optional[pd.DataFrame] = None

    if pheno is not None and not pheno.empty:
        parsed_metadata_path = parsed_root / "metadata" / "sample_metadata.tsv"
        parsed_metadata_path.parent.mkdir(parents=True, exist_ok=True)
        pheno.to_csv(parsed_metadata_path, sep="\t", index=False)
        parsed_outputs["sample_metadata"] = "parsed/metadata/sample_metadata.tsv"

        sample_annotation = build_sample_annotation(
            pheno,
            accession=accession,
            gse=gse,
            group_column_guess=group_column_guess,
        )
        sample_annotation_path = organized_root / "sample_annotation.tsv"
        sample_annotation.to_csv(sample_annotation_path, sep="\t", index=False)
        standard_assets_written["sample_annotation"] = "organized/sample_annotation.tsv"

    if expr_probe_clean is not None and not expr_probe_clean.empty:
        parsed_expression_path = parsed_root / "expression" / "expression_matrix.tsv.gz"
        parsed_expression_path.parent.mkdir(parents=True, exist_ok=True)
        expr_probe_clean.to_csv(parsed_expression_path, sep="\t", compression="gzip")
        parsed_outputs["expression_matrix"] = "parsed/expression/expression_matrix.tsv.gz"

    result["dataset_root"] = str(dataset_root)
    result["parsed_root"] = str(parsed_root)
    result["organized_root"] = str(organized_root)
    result["parsed_outputs"] = parsed_outputs
    result["standard_assets_written"] = standard_assets_written

    standard_assets_written["dataset_manifest"] = "organized/dataset_manifest.json"
    dataset_manifest = build_dataset_manifest(
        accession=accession,
        input_source=input_source,
        dataset_root=dataset_root,
        gse=gse,
        config=config,
        sample_annotation=sample_annotation,
        expr_probe_clean=expr_probe_clean,
        result=result,
    )
    dataset_manifest_path = organized_root / "dataset_manifest.json"
    save_json(dataset_manifest, dataset_manifest_path)

    parse_report = {
        "accession": accession,
        "input_source": input_source,
        "status": result.get("status"),
        "metadata_parse_success": bool(result.get("metadata_parse_success")),
        "expression_matrix_success": bool(result.get("expression_matrix_success")),
        "group_column_guess": group_column_guess,
        "parsed_outputs": parsed_outputs,
        "standard_assets_written": standard_assets_written,
    }
    parse_report_path = parsed_root / "reports" / "parse_report.json"
    save_json(parse_report, parse_report_path)
    parsed_outputs["parse_report"] = "parsed/reports/parse_report.json"

    result["standard_assets_written"] = standard_assets_written
    result["dataset_manifest_path"] = str(dataset_manifest_path)
    return result


def ensure_numeric_matrix(df: pd.DataFrame) -> pd.DataFrame:
    LOGGER.info("Converting expression matrix to numeric values")
    try:
        numeric_df = df.apply(pd.to_numeric, errors="coerce")
    except Exception as exc:
        raise CleaningError("Failed to convert expression matrix to numeric values") from exc
    return numeric_df


def auto_detect_log2_needed(df: pd.DataFrame) -> bool:
    LOGGER.info("Auto-detecting whether log2 transform is needed")
    values = df.to_numpy(dtype=float, copy=False)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return False
    max_value = float(np.nanmax(finite_values))
    q1 = float(np.nanquantile(finite_values, 0.25))
    return max_value > 100 or q1 > 16


def log2_transform(df: pd.DataFrame) -> pd.DataFrame:
    LOGGER.info("Applying log2(x + 1) transform")
    try:
        return np.log2(df + 1)
    except Exception as exc:
        raise CleaningError("Failed to apply log2 transform") from exc


def drop_all_na_rows(df: pd.DataFrame) -> pd.DataFrame:
    LOGGER.info("Dropping rows that are all-NA")
    return df.dropna(axis=0, how="all")


def drop_duplicate_genes(df: pd.DataFrame) -> pd.DataFrame:
    LOGGER.info("Dropping duplicated gene rows by index")
    return df[~df.index.duplicated(keep="first")]


def basic_clean_expression(
    expr: pd.DataFrame,
    log2_transform_flag: Optional[bool],
    drop_duplicate_gene_rows: bool,
) -> tuple[pd.DataFrame, bool]:
    LOGGER.info("Cleaning expression matrix")
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
    LOGGER.info("Selecting GPL object")
    gpls = getattr(gse, "gpls", {}) or {}
    if not gpls:
        raise AnnotationError("No GPL objects found in GSE")
    if len(gpls) > 1:
        LOGGER.warning(
            "Multiple GPLs detected (%s). Using the first GPL as a simplified strategy. TODO: extend multi-GPL support.",
            len(gpls),
        )
    first_key = next(iter(gpls))
    return gpls[first_key]


def annotate_expression_matrix(
    expr: pd.DataFrame,
    gpl: Any,
    probe_col: str,
    gene_col: str,
    expr_index_col: str,
) -> pd.DataFrame:
    LOGGER.info("Annotating expression matrix using GPL columns %s -> %s", probe_col, gene_col)
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
    LOGGER.info("Aggregating probe-level matrix to gene level with method=%s", method)
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


def _base_processing_result(accession: str, outdir: Path, input_source: str) -> dict[str, Any]:
    """Return a stable result skeleton for partial-success processing."""
    return {
        "accession": accession,
        "input_source": input_source,
        "outdir": str(outdir),
        "status": "failed",
        "metadata_parse_success": False,
        "expression_matrix_success": False,
        "matrix_build_success": False,
        "matrix_build_skipped": False,
        "matrix_build_failed": False,
        "expression_matrix_error": None,
        "metadata_error": None,
        "group_column_guess": None,
        "probe_log2_applied": False,
        "annotation_performed": False,
        "gene_level_generated": False,
    }


def process_from_gse_object(gse: Any, config: ProcessConfig, *, input_source: str = "gse_object") -> dict[str, Any]:
    LOGGER.info("Starting processing from an existing GSE object")
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
    result = _base_processing_result(
        accession=accession,
        outdir=outdir,
        input_source=input_source,
    )

    pheno: Optional[pd.DataFrame] = None
    expr_probe_clean: Optional[pd.DataFrame] = None
    group_col: Optional[str] = None
    probe_log2_applied = False

    try:
        pheno = build_phenotype_table(gse)
        pheno.to_csv(outdir / "phenotype_table.csv", index=False)
        group_col = infer_group_column(pheno)
        if group_col:
            group_summary = summarize_groups(pheno, group_col)
            group_summary.to_csv(outdir / "group_summary.csv", index=False)
        result["metadata_parse_success"] = True
        result["group_column_guess"] = group_col
    except MetadataParseError as exc:
        LOGGER.warning("Metadata parsing failed for %s: %s", accession, exc)
        result["metadata_error"] = str(exc)

    try:
        expr_probe_raw = build_expression_matrix(
            gse=gse,
            values_column=config.values_column,
            gsm_index_col=config.gsm_index_col,
        )
        expr_probe_raw.to_csv(outdir / "expression_probe_raw.csv")

        expr_probe_clean, probe_log2_applied = basic_clean_expression(
            expr=expr_probe_raw,
            log2_transform_flag=config.log2_transform,
            drop_duplicate_gene_rows=False,
        )
        expr_probe_clean.to_csv(outdir / "expression_probe_clean.csv")
        result["expression_matrix_success"] = True
        result["matrix_build_success"] = True
        result["probe_log2_applied"] = probe_log2_applied
    except (MatrixBuildError, CleaningError) as exc:
        LOGGER.warning("Expression matrix processing failed for %s: %s", accession, exc)
        result["matrix_build_failed"] = True
        result["expression_matrix_error"] = str(exc)

    expr_annotated: Optional[pd.DataFrame] = None
    expr_gene_level: Optional[pd.DataFrame] = None

    if expr_probe_clean is not None and config.gpl_gene_col:
        LOGGER.info("Annotating expression matrix with GPL metadata")
        try:
            gpl = get_single_gpl(gse)
            expr_annotated = annotate_expression_matrix(
                expr=expr_probe_clean,
                gpl=gpl,
                probe_col=config.gpl_probe_col,
                gene_col=config.gpl_gene_col,
                expr_index_col=config.gsm_index_col,
            )
            expr_annotated.to_csv(outdir / "expression_annotated.csv", index=False)
            result["annotation_performed"] = True

            if config.merge_probe_to_gene:
                expr_gene_level = aggregate_to_gene(
                    annotated_expr=expr_annotated,
                    gene_col=config.gpl_gene_col,
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
                result["gene_level_generated"] = True
        except AnnotationError as exc:
            LOGGER.warning("GPL annotation failed for %s: %s", accession, exc)
            result["annotation_error"] = str(exc)

    if result["metadata_parse_success"] and expr_probe_clean is None:
        result["status"] = "partial_success"
        result["matrix_build_skipped"] = not result["matrix_build_failed"]
    elif result["metadata_parse_success"] and expr_probe_clean is not None:
        result["status"] = "success"
    elif expr_probe_clean is not None:
        result["status"] = "partial_success"
    else:
        raise ProcessModuleError(
            result["metadata_error"]
            or result["expression_matrix_error"]
            or "Both metadata parsing and expression matrix processing failed"
        )

    if expr_probe_clean is not None:
        run_summary = build_run_summary(
            accession=accession,
            input_source=input_source,
            outdir=outdir,
            gse=gse,
            expr_probe_clean=expr_probe_clean,
            group_column_guess=group_col,
            expr_gene_level=expr_gene_level,
            status=result["status"],
        )
    else:
        run_summary = {
            "accession": accession,
            "input_source": input_source,
            "outdir": str(outdir),
            "geo_type": getattr(gse, "__class__", type(None)).__name__,
            "n_samples": len(getattr(gse, "gsms", {}) or {}),
            "n_probe_rows": None,
            "n_probe_cols": None,
            "group_column_guess": group_col,
            "n_gene_rows": None,
            "n_gene_cols": None,
            "status": result["status"],
        }

    run_summary.update(result)
    run_summary = write_phase1_processing_assets(
        accession=accession,
        input_source=input_source,
        gse=gse,
        config=config,
        pheno=pheno,
        expr_probe_clean=expr_probe_clean,
        group_column_guess=group_col,
        result=run_summary,
    )
    save_json(run_summary, outdir / "run_summary.json")
    return run_summary


def process_from_local_family_soft(filepath: str, config: ProcessConfig) -> dict[str, Any]:
    LOGGER.info("Starting processing from local full family SOFT")
    gse = load_full_family_soft(filepath)
    resolved_input = str(Path(filepath).expanduser().resolve())
    summary = process_from_gse_object(gse, config, input_source=resolved_input)
    save_json(summary, Path(config.outdir).expanduser().resolve() / "run_summary.json")
    return summary


def run_processing_pipeline(input_source: Any, config: ProcessConfig) -> dict[str, Any]:
    if isinstance(input_source, (str, Path)):
        return process_from_local_family_soft(str(input_source), config)
    return process_from_gse_object(input_source, config)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process a downloaded GEO full family SOFT into phenotype and expression tables."
    )
    parser.add_argument("accession", help="GSE accession, for example GSE12345")
    parser.add_argument("--input-file", required=True, help="Local full family SOFT filepath. Quick txt files are not allowed.")
    parser.add_argument("--outdir", default="geo_processed", help="Directory for processing outputs")
    parser.add_argument("--geo-dir", default="geo_downloads", help="Directory for GEO local storage metadata")
    parser.add_argument("--values-column", default="VALUE", help="Column passed to GSE.pivot_samples(values=...)")
    parser.add_argument("--gsm-index-col", default="ID_REF", help="Index column passed to GSE.pivot_samples(index=...)")
    parser.add_argument("--gpl-probe-col", default="ID", help="GPL probe identifier column")
    parser.add_argument("--gpl-gene-col", default=None, help="GPL gene symbol column. If omitted, annotation and gene aggregation are skipped.")
    parser.add_argument("--disable-gene-aggregation", action="store_true", help="Skip probe-to-gene aggregation even if GPL gene column is provided")
    parser.add_argument("--gene-agg-method", default="mean", choices=["mean", "median", "max"], help="Aggregation method for probe-to-gene summarization")
    parser.add_argument("--log2-transform", choices=["auto", "true", "false"], default="auto", help="Control probe-level log2 transform")
    parser.add_argument("--keep-duplicate-genes", action="store_true", help="Keep duplicated genes after gene aggregation")
    parser.add_argument("--keep-na-gene", action="store_true", help="Keep empty/NA gene annotations during aggregation")
    return parser.parse_args()


def parse_log2_flag(raw: str) -> Optional[bool]:
    if raw == "auto":
        return None
    return raw == "true"


def main() -> int:
    configure_logging()
    args = parse_args()

    config = ProcessConfig(
        accession=args.accession,
        outdir=args.outdir,
        geo_dir=args.geo_dir,
        values_column=args.values_column,
        gsm_index_col=args.gsm_index_col,
        gpl_probe_col=args.gpl_probe_col,
        gpl_gene_col=args.gpl_gene_col,
        merge_probe_to_gene=not args.disable_gene_aggregation,
        gene_agg_method=args.gene_agg_method,
        log2_transform=parse_log2_flag(args.log2_transform),
        drop_na_gene=not args.keep_na_gene,
        drop_duplicate_gene=not args.keep_duplicate_genes,
    )

    LOGGER.info("Process config: %s", json.dumps(asdict(config), ensure_ascii=False))

    try:
        result = process_from_local_family_soft(args.input_file, config)
    except ProcessModuleError as exc:
        LOGGER.exception("Processing pipeline failed")
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
