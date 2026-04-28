"""Unified TCGA/GTEx module facade exports."""

from .facade import (
    build_tcga_gtex_bundle,
    download_tcga_gtex_dataset,
    get_tcga_gtex_summary,
    resolve_tcga_gtex_files,
    search_tcga_gtex,
)

__all__ = [
    "search_tcga_gtex",
    "resolve_tcga_gtex_files",
    "download_tcga_gtex_dataset",
    "build_tcga_gtex_bundle",
    "get_tcga_gtex_summary",
]
