"""Legacy duplicate compatibility surface; not part of the current GEO mainline."""

from .download import (
    DownloadConfig,
    DownloadModuleError,
    GeoDownloadError,
    download_full_family_soft,
    load_existing_full_family_soft,
    parse_existing_full_family_soft,
)
from .process import (
    AnnotationError,
    CleaningError,
    MatrixBuildError,
    MetadataParseError,
    ProcessConfig,
    ProcessModuleError,
    process_from_gse_object,
    process_from_local_family_soft,
    run_processing_pipeline,
)

__all__ = [
    "AnnotationError",
    "CleaningError",
    "DownloadConfig",
    "DownloadModuleError",
    "GeoDownloadError",
    "MatrixBuildError",
    "MetadataParseError",
    "ProcessConfig",
    "ProcessModuleError",
    "download_full_family_soft",
    "load_existing_full_family_soft",
    "parse_existing_full_family_soft",
    "process_from_gse_object",
    "process_from_local_family_soft",
    "run_processing_pipeline",
]
