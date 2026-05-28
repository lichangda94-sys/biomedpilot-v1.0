from __future__ import annotations

GSEA_INPUT_SCHEMA_VERSION = "biomedpilot.gsea_preranked_input_gate.v1"
GSEA_RANK_METRIC_SCHEMA_VERSION = "biomedpilot.gsea_rank_metric_gate.v1"
GSEA_GENE_SET_SCHEMA_VERSION = "biomedpilot.gsea_gene_set_resource_gate.v1"
GSEA_PARAMETER_SCHEMA_VERSION = "biomedpilot.gsea_parameter_gate.v1"
GSEA_RESULT_SCHEMA_GATE_VERSION = "biomedpilot.gsea_result_schema_gate.v1"

GSEA_TASK_TYPE = "gsea_preranked"
GSEA_ENGINE_NAME = "biomedpilot_gsea_preranked_gate_only"
GSEA_ENGINE_VERSION = "0.0.0-gate"
CONTROLLED_GSEA_ENGINE_NAME = "python_preranked_gsea_mvp"
CONTROLLED_GSEA_ENGINE_VERSION = "0.1.0"

ALLOWED_GSEA_SOURCE_SEMANTICS = {"formal_computed_result", "imported_external_result"}
ALLOWED_RANK_METRICS = {
    "signed_log10_fdr_by_log2fc",
    "signed_log10_pvalue_by_log2fc",
    "log2_fold_change",
    "statistic",
    "custom_rank_column",
}
ALLOWED_DUPLICATE_GENE_POLICIES = {"keep_max_abs_rank", "first", "fail"}
ALLOWED_PERMUTATION_TYPES = {"gene_set"}
ALLOWED_SCORING_SCHEMES = {"classic", "weighted"}

GENE_COLUMN_ALIASES = ("feature_id", "gene_symbol", "gene_id", "gene", "symbol")
LOG2FC_COLUMN_ALIASES = ("log2_fold_change", "log2FC", "log2fc", "logFC")
P_VALUE_COLUMN_ALIASES = ("p_value", "P.Value", "pvalue", "p")
ADJUSTED_P_COLUMN_ALIASES = ("adjusted_p_value", "padj", "adj_p_value", "FDR", "q_value")
STATISTIC_COLUMN_ALIASES = ("statistic", "t", "t_stat", "score", "wald_statistic")

REQUIRED_GSEA_RESULT_INDEX_FIELDS = (
    "result_id",
    "task_run_id",
    "task_type",
    "result_semantics",
    "input_package_id",
    "gsea_input_id",
    "source_deg_result_id",
    "source_result_semantics",
    "gene_set_resource_id",
    "parameters_manifest",
    "engine_name",
    "engine_version",
    "dependency_snapshot",
    "output_artifacts",
    "plot_artifacts",
    "report_artifacts",
    "validation_status",
    "warnings",
    "blockers",
    "log_artifacts",
    "failure_reason",
    "created_at",
    "updated_at",
    "schema_version",
    "report_ready_eligible",
    "migration_status",
)

REQUIRED_GSEA_RESULT_TABLE_COLUMNS = (
    "term_id",
    "term_name",
    "set_size",
    "overlap_size",
    "enrichment_score",
    "normalized_enrichment_score",
    "p_value",
    "adjusted_p_value",
    "leading_edge_genes",
    "rank_metric",
    "warnings",
)
