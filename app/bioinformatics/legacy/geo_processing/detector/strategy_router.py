"""Route detection outcomes into explicit processing strategies."""

from __future__ import annotations

from .models import DatasetDetectionResult, MatrixLevel, RecommendedStrategy, TechnologyType, ValueSemantic
from .rules import (
    FAILURE_AMBIGUOUS,
    FAILURE_DIFF_RESULT,
    FAILURE_GPL_MISSING,
    FAILURE_MATRIX_NOT_FOUND,
    FAILURE_RAW_ONLY,
    FAILURE_SAMPLE_TABLE_MISSING,
    FAILURE_UNSUPPORTED,
)


def _add_warning(result: DatasetDetectionResult, message: str) -> None:
    if message not in result.warnings:
        result.warnings.append(message)


def _compute_confidence(result: DatasetDetectionResult) -> float:
    confidence = 0.0
    if result.accession_type != "UNKNOWN":
        confidence += 0.2
    if result.container_types:
        confidence += 0.2
    if result.data_roles:
        confidence += 0.2
    if result.technology_type != TechnologyType.UNKNOWN.value:
        confidence += 0.2
    if result.matrix_level not in {MatrixLevel.UNKNOWN.value, MatrixLevel.NON_MATRIX.value}:
        confidence += 0.1
    if result.value_semantic != ValueSemantic.UNKNOWN.value:
        confidence += 0.1

    if "conflict_detected" in result.extra:
        confidence -= 0.2
    if result.failure_reason in {FAILURE_AMBIGUOUS, FAILURE_UNSUPPORTED}:
        confidence -= 0.15
    return max(0.0, min(1.0, round(confidence, 2)))


def route_processing_strategy(result: DatasetDetectionResult) -> DatasetDetectionResult:
    """Select the next processing route and attach warnings and confidence."""
    strategy = RecommendedStrategy.MANUAL_REVIEW_REQUIRED.value

    if result.technology_type == TechnologyType.SINGLE_CELL.value:
        result.failure_reason = FAILURE_UNSUPPORTED
        result.next_action = "single-cell dataset detected; stop automatic bulk matrix construction"
        strategy = RecommendedStrategy.UNSUPPORTED_SINGLE_CELL.value
    elif result.technology_type == TechnologyType.SPATIAL.value:
        result.failure_reason = FAILURE_UNSUPPORTED
        result.next_action = "spatial dataset detected; stop automatic bulk matrix construction"
        strategy = RecommendedStrategy.UNSUPPORTED_SPATIAL.value
    elif result.has_series_matrix and result.matrix_level in {
        MatrixLevel.PROBE.value,
        MatrixLevel.GENE.value,
        MatrixLevel.TRANSCRIPT.value,
    }:
        strategy = RecommendedStrategy.SERIES_MATRIX_FIRST.value
        result.next_action = "parse metadata and expression from series matrix first"
    elif result.candidate_expression_files and not result.has_series_matrix:
        if result.has_family_soft:
            strategy = RecommendedStrategy.SOFT_METADATA_PLUS_SUPP_MATRIX.value
            result.next_action = "parse metadata from SOFT and expression matrix from supplementary file"
        else:
            strategy = RecommendedStrategy.SUPPLEMENTARY_MATRIX_FIRST.value
            result.next_action = "parse expression from supplementary processed matrix and keep metadata fallback"
    elif result.raw_files and result.technology_type == TechnologyType.MICROARRAY.value:
        result.failure_reason = FAILURE_RAW_ONLY
        result.next_action = "raw CEL files detected; external microarray preprocessing is required"
        strategy = RecommendedStrategy.RAW_MICROARRAY_EXTERNAL_PREPROCESS.value
    elif result.raw_files and result.technology_type in {
        TechnologyType.BULK_RNASEQ.value,
        TechnologyType.BULK_RNASEQ_RAW_LINKED.value,
        TechnologyType.UNKNOWN.value,
    }:
        result.failure_reason = FAILURE_RAW_ONLY
        result.next_action = "raw sequencing files detected; upstream alignment/counting pipeline is required"
        strategy = RecommendedStrategy.RAW_RNASEQ_EXTERNAL_PREPROCESS.value
    elif result.candidate_metadata_files:
        result.failure_reason = FAILURE_MATRIX_NOT_FOUND
        result.next_action = "metadata is available; continue metadata parsing without expression matrix"
        strategy = RecommendedStrategy.METADATA_ONLY.value

    if result.matrix_level == MatrixLevel.DIFF_RESULT.value:
        result.failure_reason = FAILURE_DIFF_RESULT
        _add_warning(result, "differential-result table detected; do not use it as expression matrix")
        if result.candidate_metadata_files:
            strategy = RecommendedStrategy.METADATA_ONLY.value
            result.next_action = "metadata is available; skip DEG table and continue metadata-only processing"

    if result.has_family_soft and "family_soft_sample_table_missing" in result.extra:
        _add_warning(result, "sample_table missing in family soft")
        if result.failure_reason is None:
            result.failure_reason = FAILURE_SAMPLE_TABLE_MISSING

    if result.matrix_level == MatrixLevel.PROBE.value:
        _add_warning(result, "probe-level matrix detected; GPL annotation mapping is recommended")
        if result.has_platform_annotation:
            result.extra.setdefault("probe_mapping", RecommendedStrategy.PROBE_TO_GENE_WITH_GPL.value)
        else:
            result.failure_reason = result.failure_reason or FAILURE_GPL_MISSING

    if len(result.candidate_expression_files) > 1 and "top_expression_candidate" not in result.extra:
        result.failure_reason = FAILURE_AMBIGUOUS
        result.extra["conflict_detected"] = "expression candidates are tied"
        _add_warning(result, "multiple expression candidates detected; manual review may be required")

    if not result.candidate_expression_files and result.candidate_metadata_files and result.failure_reason is None:
        result.failure_reason = FAILURE_MATRIX_NOT_FOUND

    result.recommended_strategy = strategy
    result.confidence = _compute_confidence(result)
    return result
