from __future__ import annotations

ORA_INPUT_SCHEMA_VERSION = "biomedpilot.ora_input_gate.v1"
ORA_GENE_SET_GATE_SCHEMA_VERSION = "biomedpilot.ora_gene_set_resource_gate.v1"
ORA_PARAMETER_SCHEMA_VERSION = "biomedpilot.ora_parameter_gate.v1"
ORA_RESULT_SCHEMA_GATE_VERSION = "biomedpilot.ora_result_schema_gate.v1"
ORA_RESULT_TASK_TYPE = "ora_enrichment"
ORA_ENGINE_NAME = "biomedpilot_ora_gate_only"
ORA_ENGINE_VERSION = "0.0.0-gate"

ALLOWED_ORA_SOURCE_SEMANTICS = {"formal_computed_result", "imported_external_result"}
ALLOWED_ORA_TEST_METHODS = {"hypergeometric", "fisher_exact"}

GENE_COLUMN_ALIASES = ("feature_id", "gene_symbol", "gene_id", "gene", "symbol")
LOG2FC_COLUMN_ALIASES = ("log2_fold_change", "log2FC", "log2fc", "logFC")
ADJUSTED_P_COLUMN_ALIASES = ("adjusted_p_value", "padj", "adj_p_value", "FDR", "q_value")
SIGNIFICANCE_COLUMN_ALIASES = ("significance_label", "significance")

REQUIRED_ORA_RESULT_INDEX_FIELDS = (
    "result_id",
    "task_run_id",
    "task_type",
    "result_semantics",
    "input_package_id",
    "ora_input_id",
    "source_dataset_id",
    "source_repository_manifest",
    "source_deg_result_id",
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
    "created_at",
    "updated_at",
    "schema_version",
    "report_ready_eligible",
)

REQUIRED_ORA_TABLE_COLUMNS = (
    "term_id",
    "term_name",
    "gene_set_size",
    "overlap_count",
    "overlap_genes",
    "background_size",
    "selected_gene_count",
    "p_value",
    "adjusted_p_value",
    "enrichment_ratio",
    "source_gene_list",
    "warnings",
)
