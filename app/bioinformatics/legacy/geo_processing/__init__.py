"""Public entrypoints for GEO processing detection and download validation."""

from .detector import DatasetDetectionResult, detect_dataset
from .download_models import DownloadValidationResult, FileScoreResult
from .module1_readers import (
    handoff_recommended_strategy,
    handoff_value_type_hint,
    load_module1_dataset_context,
    read_dataset_manifest_draft,
    read_download_plan,
    read_download_receipt,
    read_file_inventory,
    read_module1_handoff,
    read_parser_hints,
    read_search_result_item,
    read_selected_results,
)
from .module3_assets import STANDARD_ASSET_PATHS, build_standard_asset_layout, merge_standard_asset_layout
from .download_validator import (
    build_dataset_core_objects,
    classify_file_by_scores,
    compare_expected_vs_actual,
    determine_dataset_status_from_core_objects,
    export_data_asset_index,
    export_download_validation_report,
    organize_dataset_files,
    score_file_candidate,
    validate_downloaded_dataset,
)

__all__ = [
    "DatasetDetectionResult",
    "DownloadValidationResult",
    "FileScoreResult",
    "build_dataset_core_objects",
    "classify_file_by_scores",
    "compare_expected_vs_actual",
    "detect_dataset",
    "determine_dataset_status_from_core_objects",
    "export_data_asset_index",
    "export_download_validation_report",
    "handoff_recommended_strategy",
    "handoff_value_type_hint",
    "load_module1_dataset_context",
    "organize_dataset_files",
    "read_dataset_manifest_draft",
    "read_download_plan",
    "read_download_receipt",
    "read_file_inventory",
    "read_module1_handoff",
    "read_parser_hints",
    "read_search_result_item",
    "read_selected_results",
    "score_file_candidate",
    "STANDARD_ASSET_PATHS",
    "build_standard_asset_layout",
    "merge_standard_asset_layout",
    "validate_downloaded_dataset",
]
