from __future__ import annotations

from pathlib import Path

from local_data.models import (
    DeliveryFileCandidate,
    DeliveryFileType,
    DeliveryScanReport,
)


_TABULAR_EXTENSIONS = {".csv", ".tsv", ".txt", ".xls", ".xlsx"}
_REPORT_EXTENSIONS = {".html", ".htm", ".pdf", ".txt", ".csv", ".tsv", ".xlsx", ".xls"}


def scan_delivery_folder(root_dir: str | Path) -> DeliveryScanReport:
    """Classify local delivery files using path/name hints only.

    The scanner does not open file contents. It records candidate types for later
    user confirmation and never mutates source files.
    """
    root = Path(root_dir)
    warnings: list[str] = []
    if not root.exists():
        return DeliveryScanReport(
            root_dir=str(root),
            candidates=[],
            warnings=["root_dir_missing"],
        )
    if not root.is_dir():
        return DeliveryScanReport(
            root_dir=str(root),
            candidates=[],
            warnings=["root_dir_not_directory"],
        )

    candidates: list[DeliveryFileCandidate] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        file_type, confidence, reasons, candidate_warnings = _classify_file(path, root)
        candidates.append(
            DeliveryFileCandidate(
                file_path=str(path),
                file_name=path.name,
                file_size=path.stat().st_size,
                detected_type=file_type,
                confidence=confidence,
                reasons=reasons,
                warnings=candidate_warnings,
            )
        )

    return DeliveryScanReport(root_dir=str(root), candidates=candidates, warnings=warnings)


def _classify_file(
    path: Path,
    root: Path,
) -> tuple[DeliveryFileType, float, list[str], list[str]]:
    normalized = _normalized_relative_path(path, root)
    name = path.name.lower()
    suffixes = [suffix.lower() for suffix in path.suffixes]
    suffix = path.suffix.lower()
    reasons: list[str] = []
    warnings: list[str] = []

    if _is_fastq(name, suffixes):
        reasons.append("fastq_extension")
        warnings.append("raw_sequence_file_detected_but_not_parsed")
        return DeliveryFileType.RAW_FASTQ, 0.98, reasons, warnings

    if "multiqc" in normalized or "fastqc" in normalized:
        reasons.append("qc_tool_name")
        return DeliveryFileType.QC_REPORT, 0.94, reasons, warnings

    if _has_any(normalized, ["differential", "deg", "de_result", "diffexp"]):
        if _is_tabular_or_report(suffix):
            reasons.append("differential_expression_path_hint")
            return DeliveryFileType.DIFFERENTIAL_EXPRESSION_RESULT, 0.86, reasons, warnings

    if _has_any(normalized, ["sample_metadata", "metadata", "phenotype", "clinical", "sample_info"]):
        if _is_tabular(suffix):
            reasons.append("sample_metadata_name_hint")
            return DeliveryFileType.SAMPLE_METADATA, 0.88, reasons, warnings

    if _has_any(normalized, ["gene_annotation", "gene_annot", "gene_info", "gene_map", "platform_annotation"]):
        if _is_tabular(suffix):
            reasons.append("gene_annotation_name_hint")
            return DeliveryFileType.GENE_ANNOTATION, 0.88, reasons, warnings

    if _has_any(normalized, ["tpm"]):
        if _is_tabular(suffix):
            reasons.append("tpm_name_hint")
            return DeliveryFileType.TPM_MATRIX, 0.9, reasons, warnings

    if _has_any(normalized, ["fpkm"]):
        if _is_tabular(suffix):
            reasons.append("fpkm_name_hint")
            return DeliveryFileType.FPKM_MATRIX, 0.9, reasons, warnings

    if _has_count_hint(normalized):
        if _is_tabular(suffix):
            reasons.append("count_matrix_name_hint")
            return DeliveryFileType.RAW_COUNT_MATRIX, 0.88, reasons, warnings

    if _has_any(normalized, ["normalized", "normalised", "norm_expression", "expression_matrix"]):
        if _is_tabular(suffix):
            reasons.append("normalized_expression_name_hint")
            return DeliveryFileType.NORMALIZED_EXPRESSION_MATRIX, 0.82, reasons, warnings

    if "qc" in normalized and suffix in _REPORT_EXTENSIONS:
        reasons.append("qc_path_hint")
        return DeliveryFileType.QC_REPORT, 0.78, reasons, warnings

    reasons.append("no_supported_delivery_hint")
    warnings.append("unclassified_file")
    return DeliveryFileType.UNKNOWN, 0.0, reasons, warnings


def _normalized_relative_path(path: Path, root: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    return "/".join(part.lower() for part in relative.parts)


def _is_fastq(name: str, suffixes: list[str]) -> bool:
    return (
        name.endswith(".fastq")
        or name.endswith(".fq")
        or name.endswith(".fastq.gz")
        or name.endswith(".fq.gz")
        or suffixes[-2:] in [[".fastq", ".gz"], [".fq", ".gz"]]
    )


def _is_tabular(suffix: str) -> bool:
    return suffix in _TABULAR_EXTENSIONS


def _is_tabular_or_report(suffix: str) -> bool:
    return suffix in (_TABULAR_EXTENSIONS | _REPORT_EXTENSIONS)


def _has_any(value: str, needles: list[str]) -> bool:
    return any(needle in value for needle in needles)


def _has_count_hint(value: str) -> bool:
    return any(
        hint in value
        for hint in [
            "raw_count",
            "raw_counts",
            "counts_matrix",
            "count_matrix",
            "gene_counts",
            "read_counts",
        ]
    )
