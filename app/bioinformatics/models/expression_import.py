from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExpressionImportResult:
    success: bool
    source_path: str
    source_type: str
    row_count: int
    column_count: int
    candidate_gene_columns: list[str]
    candidate_sample_columns: list[str]
    numeric_sample_column_count: int
    missing_value_rate: float
    output_path: str
    warnings: list[str]
    message: str
    details: dict[str, object] = field(default_factory=dict)
    asset_id: str = ""
    summary_path: str = ""
    manifest_path: str = ""
    gene_id_column_candidates: list[str] = field(default_factory=list)
    selected_gene_id_column: str | None = None
    sample_expression_column_candidates: list[str] = field(default_factory=list)
    numeric_column_count: int = 0
    numeric_column_ratio: float = 0.0
    missing_value_summary: dict[str, object] = field(default_factory=dict)
    duplicate_gene_id_count: int = 0
    non_numeric_columns: list[str] = field(default_factory=list)
    is_expression_matrix_suitable: bool = False
    errors: list[str] = field(default_factory=list)
