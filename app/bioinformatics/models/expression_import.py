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
