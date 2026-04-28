#!/usr/bin/env python3
"""Compatibility-only legacy processing entrypoint; not part of the frozen GEO mainline.

Process GEO full family SOFT or an already parsed GSE object.

Design notes:
- Reuse GEOparse object abilities instead of rebuilding GEO object logic.
- Treat GEOparse GSE/GPL/GSM objects as the object model layer.
- Add a thin wrapper and table-validation layer inspired by GEOTypes.BaseGEO
  and GEOTypes.SimpleGEO.
- Processing never downloads data. Only local full family SOFT or an existing
  GSE object is accepted.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import GEOparse
import numpy as np
import pandas as pd


LOGGER = logging.getLogger("process_geo_family_soft")


class ProcessModuleError(Exception):
    """Base exception for processing failures."""


class MetadataParseError(ProcessModuleError):
    """Raised when phenotype metadata cannot be parsed."""


class MatrixBuildError(ProcessModuleError):
    """Raised when expression matrix construction fails."""


class AnnotationError(ProcessModuleError):
    """Raised when GPL annotation or gene aggregation fails."""


class CleaningError(ProcessModuleError):
    """Raised when matrix cleaning fails."""


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


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def save_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def normalize_accession(accession: str) -> str:
    accession = accession.strip().upper()
    if not accession.startswith("GSE"):
        raise ProcessModuleError(f"Only GSE accessions are supported, got: {accession}")
    return accession


def is_gse_like(obj: Any) -> bool:
    return (
        obj is not None
        and getattr(obj, "__class__", type(None)).__name__ == "GSE"
        and hasattr(obj, "gsms")
    )


def standardize_column_name(name: Any) -> str:
    text = str(name).strip().lower()
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unnamed"


def deduplicate_names(names: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    fixed: list[str] = []
    for name in names:
        if name not in counts:
            counts[name] = 0
            fixed.append(name)
        else:
            counts[name] += 1
            fixed.append(f"{name}.{counts[name]}")
    return fixed


class GeoObjectView:
    """Thin BaseGEO-like interface over a GEOparse object."""

    def __init__(self, geo_object: Any):
        self.geo_object = geo_object
        self.name = getattr(geo_object, "name", None)
        self.metadata = getattr(geo_object, "metadata", {}) or {}
        self.relations = getattr(geo_object, "relations", {}) or {}

    def get_accession(self) -> Optional[str]:
        if hasattr(self.geo_object, "get_accession"):
            return self.geo_object.get_accession()
        value = self.metadata.get("geo_accession")
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def get_type(self) -> Optional[str]:
        if hasattr(self.geo_object, "get_type"):
            return self.geo_object.get_type()
        value = self.metadata.get("type")
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def get_metadata_attribute(self, metaname: str) -> Any:
        value = self.metadata.get(metaname)
        if value is None:
            raise MetadataParseError(f"No metadata attribute named {metaname}")
        if isinstance(value, list):
            return value if len(value) > 1 else value[0]
        return value


class GeoTableFrame:
    """SimpleGEO-like DataFrame validator and normalizer."""

    def __init__(self, name: str, frame: pd.DataFrame):
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{name} must be a pandas.DataFrame, got: {type(frame)!r}")
        self.name = name
        self.frame = frame.copy()

    def ensure_unique_columns(self) -> "GeoTableFrame":
        original = [str(col) for col in self.frame.columns]
        if len(set(original)) != len(original):
            LOGGER.warning("Detected duplicated columns in %s. Correcting.", self.name)
            self.frame.columns = deduplicate_names(original)
        return self

    def standardize_columns(self) -> "GeoTableFrame":
        standardized = [standardize_column_name(col) for col in self.frame.columns]
        if len(set(standardized)) != len(standardized):
            LOGGER.warning(
                "Standardized columns became duplicated in %s. Applying suffix correction.",
                self.name,
            )
            standardized = deduplicate_names(standardized)
        self.frame.columns = standardized
        return self

    def reorder_or_raise(self, expected_columns: list[str]) -> "GeoTableFrame":
        actual = [str(col) for col in self.frame.columns]
        if actual == expected_columns:
            return self
        if sorted(actual) == sorted(expected_columns):
            LOGGER.warning("Columns in %s are out of order. Reordering.", self.name)
            self.frame = self.frame.loc[:, expected_columns]
            return self
        raise MatrixBuildError(
            f"Columns in {self.name} do not match expectation. "
            f"actual={actual}, expected={expected_columns}"
        )

    def require_columns(self, required: list[str]) -> "GeoTableFrame":
        missing = [col for col in required if col not in self.frame.columns]
        if missing:
            raise MatrixBuildError(f"Missing required columns in {self.name}: {missing}")
        return self

    def require_non_empty(self) -> "GeoTableFrame":
        if self.frame.empty:
            raise MatrixBuildError(f"{self.name} is empty")
        return self


def load_full_family_soft(filepath: str) -> Any:
    path = Path(filepath).expanduser().resolve()
    LOGGER.info("Loading local full family SOFT: %s", path)
    if not path.exists():
        raise ProcessModuleError(f"Full family SOFT file does not exist: {path}")
    if path.name.endswith(".txt"):
        raise ProcessModuleError(
            f"Quick text file is not allowed as formal processing input: {path}"
        )

    try:
        gse = GEOparse.get_GEO(filepath=str(path), silent=False)
    except Exception as exc:
        raise ProcessModuleError(f"Failed to parse family SOFT from {path}") from exc

    if not is_gse_like(gse):
        raise ProcessModuleError(f"Parsed object is not a GSE-like object: {type(gse)!r}")
    return gse


def build_phenotype_table(gse: Any) -> pd.DataFrame:
    LOGGER.info("Building phenotype table from gse.phenotype_data")
    try:
        pheno = gse.phenotype_data.copy()
    except Exception as exc:
        raise MetadataParseError("Failed to read gse.phenotype_data") from exc

    if pheno is None or pheno.empty:
        raise MetadataParseError("Phenotype table is empty")

    pheno.index = pheno.index.map(str)
    pheno.index.name = standardize_column_name(pheno.index.name or "sample_id")
    pheno = pheno.reset_index()
    pheno = (
        GeoTableFrame("phenotype_table", pheno)
        .ensure_unique_columns()
        .standardize_columns()
        .require_non_empty()
        .frame
    )
    if "sample_id" not in pheno.columns:
        pheno = pheno.rename(columns={pheno.columns[0]: "sample_id"})
    return pheno


def infer_group_column(pheno: pd.DataFrame) -> Optional[str]:
    LOGGER.info("Inferring group column from phenotype table")
    if pheno.empty:
        return None

    keyword_priority = [
        "group",
        "condition",
        "phenotype",
        "disease",
        "status",
        "treatment",
        "source_name",
        "characteristics",
        "title",
    ]
    candidate_scores: list[tuple[int, str]] = []

    for col in pheno.columns:
        if col == "sample_id":
            continue
        series = pheno[col].fillna("").astype(str).str.strip()
        non_empty = series[series != ""]
        if non_empty.empty:
            continue
        nunique = non_empty.nunique(dropna=True)
        if nunique <= 1:
            continue
        if nunique > max(20, len(pheno) // 2):
            continue

        score = 0
        for idx, keyword in enumerate(keyword_priority):
            if keyword in col:
                score += 100 - idx
        score += max(0, 20 - nunique)
        candidate_scores.append((score, col))

    if not candidate_scores:
        return None
    candidate_scores.sort(reverse=True)
    return candidate_scores[0][1]


def summarize_groups(pheno: pd.DataFrame, group_col: str) -> pd.DataFrame:
    LOGGER.info("Summarizing groups using column: %s", group_col)
    if group_col not in pheno.columns:
        raise MetadataParseError(f"Group column not found: {group_col}")

    summary = (
        pheno[group_col]
        .fillna("NA")
        .astype(str)
        .str.strip()
        .replace("", "NA")
        .value_counts(dropna=False)
        .rename_axis("group")
        .reset_index(name="sample_count")
    )
    return GeoTableFrame("group_summary", summary).require_non_empty().frame


def get_expected_sample_names(gse: Any) -> list[str]:
    return [str(gsm_name) for gsm_name in (getattr(gse, "gsms", {}) or {}).keys()]


def build_probe_expression_matrix(
    gse: Any,
    values_column: str,
    gsm_index_col: str,
) -> pd.DataFrame:
    LOGGER.info(
        "Building probe-level expression matrix with pivot_samples(values=%s, index=%s)",
        values_column,
        gsm_index_col,
    )
    try:
        expr = gse.pivot_samples(values=values_column, index=gsm_index_col)
    except Exception as exc:
        raise MatrixBuildError(
            f"Failed to build expression matrix using values={values_column}, index={gsm_index_col}"
        ) from exc

    if expr is None or expr.empty:
        raise MatrixBuildError("Probe-level expression matrix is empty")

    expr = expr.copy()
    expr.index = expr.index.map(str)
    expr.columns = expr.columns.map(str)
    expr.index.name = gsm_index_col
    expr_wrapper = GeoTableFrame("expression_probe_matrix", expr).ensure_unique_columns()
    expr_wrapper.reorder_or_raise(get_expected_sample_names(gse))
    return expr_wrapper.frame


def get_single_gpl(gse: Any) -> Any:
    LOGGER.info("Selecting a single GPL object")
    gpls = getattr(gse, "gpls", {}) or {}
    if not gpls:
        raise AnnotationError("No GPL object found in GSE")
    if len(gpls) > 1:
        LOGGER.warning(
            "Multiple GPL objects detected. Using the first GPL only. TODO: implement multi-GPL handling."
        )
    first_key = next(iter(gpls))
    return gpls[first_key]


def ensure_numeric_matrix(df: pd.DataFrame) -> pd.DataFrame:
    LOGGER.info("Converting matrix to numeric values")
    try:
        return df.apply(pd.to_numeric, errors="coerce")
    except Exception as exc:
        raise CleaningError("Failed to convert matrix to numeric values") from exc


def auto_detect_log2_needed(df: pd.DataFrame) -> bool:
    LOGGER.info("Auto-detecting whether log2(x+1) is needed")
    values = df.to_numpy(dtype=float, copy=False)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        return False
    max_value = float(np.nanmax(finite_values))
    q75 = float(np.nanquantile(finite_values, 0.75))
    return max_value > 100 or q75 > 16


def apply_log2_transform(df: pd.DataFrame) -> pd.DataFrame:
    LOGGER.info("Applying log2(x + 1) transform")
    try:
        return np.log2(df + 1)
    except Exception as exc:
        raise CleaningError("Failed to apply log2(x + 1) transform") from exc


def drop_all_na_rows(df: pd.DataFrame) -> pd.DataFrame:
    LOGGER.info("Dropping rows with all values missing")
    return df.dropna(axis=0, how="all")


def drop_duplicate_genes(df: pd.DataFrame) -> pd.DataFrame:
    LOGGER.info("Dropping duplicated gene rows by index")
    return df[~df.index.duplicated(keep="first")]


def basic_clean_expression(
    expr: pd.DataFrame,
    log2_transform_flag: Optional[bool],
    drop_duplicate_gene_rows: bool = False,
) -> tuple[pd.DataFrame, bool]:
    LOGGER.info("Running basic expression cleaning")
    cleaned = ensure_numeric_matrix(expr)
    cleaned = drop_all_na_rows(cleaned)

    applied_log2 = False
    if log2_transform_flag is None:
        if auto_detect_log2_needed(cleaned):
            cleaned = apply_log2_transform(cleaned)
            applied_log2 = True
    elif log2_transform_flag:
        cleaned = apply_log2_transform(cleaned)
        applied_log2 = True

    cleaned = drop_all_na_rows(cleaned)
    if drop_duplicate_gene_rows:
        cleaned = drop_duplicate_genes(cleaned)

    if cleaned.empty:
        raise CleaningError("Expression matrix became empty after cleaning")
    return cleaned, applied_log2


def annotate_expression_matrix(
    expr: pd.DataFrame,
    gpl: Any,
    probe_col: str,
    gene_col: str,
    expr_index_col: str,
) -> pd.DataFrame:
    LOGGER.info(
        "Annotating expression matrix using GPL columns probe=%s gene=%s",
        probe_col,
        gene_col,
    )
    if gene_col is None:
        raise AnnotationError("gene_col cannot be None in annotate_expression_matrix")
    if not hasattr(gpl, "table") or gpl.table is None or gpl.table.empty:
        raise AnnotationError("GPL table is missing or empty")
    if probe_col not in gpl.table.columns:
        raise AnnotationError(f"GPL probe column not found: {probe_col}")
    if gene_col not in gpl.table.columns:
        raise AnnotationError(f"GPL gene column not found: {gene_col}")

    annotation_table = (
        gpl.table[[probe_col, gene_col]]
        .copy()
        .drop_duplicates(subset=[probe_col], keep="first")
    )
    annotation_table = GeoTableFrame("gpl_annotation_table", annotation_table).require_non_empty().frame

    expr_reset = expr.reset_index()
    if expr_index_col not in expr_reset.columns:
        raise AnnotationError(f"Expression index column not found after reset_index: {expr_index_col}")

    try:
        annotated = expr_reset.merge(
            annotation_table,
            how="left",
            left_on=expr_index_col,
            right_on=probe_col,
        )
    except Exception as exc:
        raise AnnotationError("Failed to merge expression matrix with GPL annotation") from exc

    if probe_col in annotated.columns:
        annotated = annotated.drop(columns=[probe_col])
    return GeoTableFrame("expression_annotated", annotated).require_non_empty().frame


def annotate_expression_matrix_from_gse(
    gse: Any,
    values_column: str,
    gpl: Any,
    probe_col: str,
    gene_col: str,
    expr_index_col: str,
) -> pd.DataFrame:
    LOGGER.info("Annotating expression matrix using GSE.pivot_and_annotate")
    try:
        annotated = gse.pivot_and_annotate(
            values=values_column,
            gpl=gpl,
            annotation_column=gene_col,
            gpl_on=probe_col,
            gsm_on=expr_index_col,
        )
    except Exception as exc:
        LOGGER.warning(
            "GSE.pivot_and_annotate failed; falling back to explicit merge annotation."
        )
        expr = build_probe_expression_matrix(
            gse=gse,
            values_column=values_column,
            gsm_index_col=expr_index_col,
        )
        return annotate_expression_matrix(
            expr=expr,
            gpl=gpl,
            probe_col=probe_col,
            gene_col=gene_col,
            expr_index_col=expr_index_col,
        )

    annotated = annotated.reset_index()
    return GeoTableFrame("expression_annotated", annotated).require_non_empty().frame


def normalize_gene_symbol(value: Any) -> Optional[str]:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    text = re.split(r"\s*///\s*|\s*//\s*|\s*;\s*|\s*,\s*", text)[0].strip()
    return text or None


def aggregate_to_gene(
    annotated_expr: pd.DataFrame,
    gene_col: str,
    sample_columns: list[str],
    method: str,
    drop_na_gene: bool,
) -> pd.DataFrame:
    LOGGER.info("Aggregating probes to gene level using method=%s", method)
    if gene_col not in annotated_expr.columns:
        raise AnnotationError(f"Gene column not found in annotated matrix: {gene_col}")
    method = method.lower()
    if method not in {"mean", "median", "max"}:
        raise AnnotationError(f"Unsupported gene aggregation method: {method}")

    work = annotated_expr.copy()
    work[gene_col] = work[gene_col].map(normalize_gene_symbol)
    if drop_na_gene:
        work = work[work[gene_col].notna()].copy()

    if work.empty:
        raise AnnotationError("No rows left after filtering missing gene annotations")

    missing_sample_columns = [col for col in sample_columns if col not in work.columns]
    if missing_sample_columns:
        raise AnnotationError(
            f"Annotated matrix missing sample columns: {missing_sample_columns}"
        )

    numeric = work[sample_columns].apply(pd.to_numeric, errors="coerce")
    grouped = numeric.groupby(work[gene_col])
    if method == "mean":
        gene_df = grouped.mean()
    elif method == "median":
        gene_df = grouped.median()
    else:
        gene_df = grouped.max()

    gene_df.index.name = "gene_symbol"
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
    annotation_performed: bool,
    status: str,
) -> dict[str, Any]:
    geo_view = GeoObjectView(gse)
    return {
        "accession": accession,
        "input_source": input_source,
        "outdir": str(outdir),
        "geo_type": getattr(gse, "__class__", type(None)).__name__,
        "series_name": geo_view.name,
        "series_type": geo_view.get_type(),
        "n_samples": len(getattr(gse, "gsms", {}) or {}),
        "n_probe_rows": int(expr_probe_clean.shape[0]),
        "n_probe_cols": int(expr_probe_clean.shape[1]),
        "group_column_guess": group_column_guess,
        "n_gene_rows": int(expr_gene_level.shape[0]) if expr_gene_level is not None else None,
        "n_gene_cols": int(expr_gene_level.shape[1]) if expr_gene_level is not None else None,
        "data_sources": ["SOFT"] + (["GPL"] if annotation_performed else []),
        "status": status,
    }


class GeoSeriesProcessor:
    """Series-level processing layer built on top of GEOparse GSE methods."""

    def __init__(self, gse: Any, config: ProcessConfig):
        if not is_gse_like(gse):
            raise ProcessModuleError(f"Input object is not a GSE-like object: {type(gse)!r}")
        self.gse = gse
        self.config = config
        self.geo = GeoObjectView(gse)
        self.outdir = Path(config.outdir).expanduser().resolve()
        self.outdir.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict[str, Any]:
        pheno = build_phenotype_table(self.gse)
        pheno.to_csv(self.outdir / "phenotype_table.csv", index=False)

        group_col = infer_group_column(pheno)
        if group_col:
            summarize_groups(pheno, group_col).to_csv(
                self.outdir / "group_summary.csv",
                index=False,
            )
        else:
            LOGGER.warning("Could not infer a group column from phenotype table")

        expr_probe = build_probe_expression_matrix(
            gse=self.gse,
            values_column=self.config.values_column,
            gsm_index_col=self.config.gsm_index_col,
        )
        expr_probe_clean, probe_log2_applied = basic_clean_expression(
            expr=expr_probe,
            log2_transform_flag=self.config.log2_transform,
            drop_duplicate_gene_rows=False,
        )
        expr_probe_clean.to_csv(self.outdir / "expression_probe_clean.csv")

        expr_annotated: Optional[pd.DataFrame] = None
        expr_gene_level: Optional[pd.DataFrame] = None

        if self.config.gpl_gene_col:
            gpl = get_single_gpl(self.gse)
            expr_annotated = annotate_expression_matrix_from_gse(
                gse=self.gse,
                values_column=self.config.values_column,
                gpl=gpl,
                probe_col=self.config.gpl_probe_col,
                gene_col=self.config.gpl_gene_col,
                expr_index_col=self.config.gsm_index_col,
            )
            expr_annotated.to_csv(self.outdir / "expression_annotated.csv", index=False)

            if self.config.merge_probe_to_gene:
                expr_gene_level = aggregate_to_gene(
                    annotated_expr=expr_annotated,
                    gene_col=self.config.gpl_gene_col,
                    sample_columns=list(expr_probe_clean.columns),
                    method=self.config.gene_agg_method,
                    drop_na_gene=self.config.drop_na_gene,
                )
                expr_gene_level, _ = basic_clean_expression(
                    expr=expr_gene_level,
                    log2_transform_flag=False if probe_log2_applied else self.config.log2_transform,
                    drop_duplicate_gene_rows=self.config.drop_duplicate_gene,
                )
                expr_gene_level.to_csv(self.outdir / "expression_gene_level.csv")
        else:
            LOGGER.info("gpl_gene_col is None, skipping GPL annotation and gene-level aggregation")

        run_summary = build_run_summary(
            accession=normalize_accession(self.config.accession),
            input_source="gse_object",
            outdir=self.outdir,
            gse=self.gse,
            expr_probe_clean=expr_probe_clean,
            group_column_guess=group_col,
            expr_gene_level=expr_gene_level,
            annotation_performed=expr_annotated is not None,
            status="success",
        )
        run_summary["probe_log2_applied"] = probe_log2_applied
        run_summary["annotation_performed"] = expr_annotated is not None
        run_summary["gene_level_generated"] = expr_gene_level is not None
        save_json(run_summary, self.outdir / "run_summary.json")
        return run_summary


def process_from_gse_object(gse: Any, config: ProcessConfig) -> dict[str, Any]:
    LOGGER.info("Processing from already parsed GSE object")
    return GeoSeriesProcessor(gse, config).run()


def process_from_local_family_soft(filepath: str, config: ProcessConfig) -> dict[str, Any]:
    LOGGER.info("Processing from local full family SOFT")
    gse = load_full_family_soft(filepath)
    result = process_from_gse_object(gse, config)
    result["input_source"] = str(Path(filepath).expanduser().resolve())
    save_json(result, Path(config.outdir).expanduser().resolve() / "run_summary.json")
    return result


def parse_log2_flag(raw: str) -> Optional[bool]:
    if raw == "auto":
        return None
    return raw == "true"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process GEO full family SOFT or an already parsed GSE object."
    )
    parser.add_argument("accession", help="GSE accession, for example GSE12345")
    parser.add_argument(
        "--input-file",
        required=True,
        help="Local full family SOFT file path. Quick txt files are not allowed.",
    )
    parser.add_argument("--outdir", default="processed_geo", help="Output directory")
    parser.add_argument("--geo-dir", default="geo_downloads", help="Reserved GEO directory argument")
    parser.add_argument("--values-column", default="VALUE", help="Column passed to pivot_samples(values=...)")
    parser.add_argument("--gsm-index-col", default="ID_REF", help="Column passed to pivot_samples(index=...)")
    parser.add_argument("--gpl-probe-col", default="ID", help="GPL probe ID column")
    parser.add_argument("--gpl-gene-col", default=None, help="GPL gene symbol column")
    parser.add_argument(
        "--disable-gene-aggregation",
        action="store_true",
        help="Skip probe-to-gene aggregation even if GPL gene column is provided",
    )
    parser.add_argument(
        "--gene-agg-method",
        default="mean",
        choices=["mean", "median", "max"],
        help="Probe-to-gene aggregation method",
    )
    parser.add_argument(
        "--log2-transform",
        default="auto",
        choices=["auto", "true", "false"],
        help="Whether to apply log2(x+1) to the matrix",
    )
    parser.add_argument(
        "--keep-na-gene",
        action="store_true",
        help="Keep rows with empty gene annotation during aggregation",
    )
    parser.add_argument(
        "--drop-duplicate-gene",
        action="store_true",
        help="Drop duplicated gene rows after gene aggregation",
    )
    return parser.parse_args()


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
        drop_duplicate_gene=args.drop_duplicate_gene,
    )
    LOGGER.info("Process config: %s", json.dumps(asdict(config), ensure_ascii=False))

    try:
        result = process_from_local_family_soft(args.input_file, config)
    except ProcessModuleError as exc:
        LOGGER.error("Processing failed: %s", exc, exc_info=True)
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
