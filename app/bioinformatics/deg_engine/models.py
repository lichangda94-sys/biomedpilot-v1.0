from __future__ import annotations

DEG_ENGINE_NAME = "python_scipy_statsmodels_deg_mvp"
DEG_ENGINE_VERSION = "0.1.0"
DEG_RESULT_SCHEMA_VERSION = "biomedpilot.deg_result_table.v1"
DEG_RESULT_BUNDLE_SCHEMA_VERSION = "biomedpilot.deg_result_bundle.v1"

REQUIRED_DEG_RESULT_COLUMNS = (
    "feature_id",
    "gene_symbol",
    "base_mean_or_mean_expression",
    "case_mean",
    "control_mean",
    "log2_fold_change",
    "statistic",
    "p_value",
    "adjusted_p_value",
    "significance_label",
    "warnings",
)
