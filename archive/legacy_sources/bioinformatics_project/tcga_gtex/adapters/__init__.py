"""Source-specific adapters for TCGA/GDC, GTEx, and future GEO integration."""

from .gtex_adapter import search as search_gtex
from .gtex_adapter import resolve_files as resolve_gtex_files
from .tcga_adapter import search as search_tcga
from .tcga_adapter import resolve_files as resolve_tcga_files

__all__ = ["search_tcga", "search_gtex", "resolve_tcga_files", "resolve_gtex_files"]
