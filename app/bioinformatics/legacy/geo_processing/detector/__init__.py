"""Dataset detection package for GEO inputs."""

from .dataset_detector import detect_accession_type, detect_dataset
from .models import (
    AccessionType,
    ContainerType,
    DataRole,
    DatasetDetectionResult,
    MatrixLevel,
    RecommendedStrategy,
    TechnologyType,
    ValueSemantic,
)
from .utils import scan_dataset_files

__all__ = [
    "AccessionType",
    "ContainerType",
    "DataRole",
    "DatasetDetectionResult",
    "MatrixLevel",
    "RecommendedStrategy",
    "TechnologyType",
    "ValueSemantic",
    "detect_accession_type",
    "detect_dataset",
    "scan_dataset_files",
]
