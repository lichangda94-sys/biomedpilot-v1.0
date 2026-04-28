from __future__ import annotations

import csv
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from local_data.models import (
    DeliveryFileType,
    DeliveryScanReport,
    LocalDatasetManifest,
    LocalDatasetValidationReport,
    SelectedImportPlan,
)


SUPPORTED_EXPRESSION_DATA_TYPES = {
    DeliveryFileType.RAW_COUNT_MATRIX.value,
    DeliveryFileType.TPM_MATRIX.value,
    DeliveryFileType.FPKM_MATRIX.value,
    DeliveryFileType.NORMALIZED_EXPRESSION_MATRIX.value,
}


def build_selected_import_plan(
    *,
    dataset_slug: str,
    selected_expression_matrix: str | None,
    expression_data_type: str | DeliveryFileType | None,
    selected_sample_metadata: str | None = None,
    selected_gene_annotation: str | None = None,
    selected_qc_reports: list[str] | None = None,
) -> SelectedImportPlan:
    """Build a user-confirmed import plan without reading or modifying files."""
    normalized_expression_type = _normalize_expression_data_type(expression_data_type)
    warnings: list[str] = []
    errors: list[str] = []

    if not dataset_slug.strip():
        errors.append("dataset_slug_missing")

    if not selected_expression_matrix:
        errors.append("expression_matrix_missing")

    if not normalized_expression_type:
        errors.append("expression_data_type_missing")
    elif normalized_expression_type not in SUPPORTED_EXPRESSION_DATA_TYPES:
        errors.append("unsupported_expression_data_type")

    if not selected_sample_metadata:
        warnings.append("sample_metadata_missing")

    if not selected_gene_annotation:
        warnings.append("gene_annotation_missing")

    return SelectedImportPlan(
        dataset_slug=dataset_slug,
        selected_expression_matrix=selected_expression_matrix,
        expression_data_type=normalized_expression_type,
        selected_sample_metadata=selected_sample_metadata,
        selected_gene_annotation=selected_gene_annotation,
        selected_qc_reports=list(selected_qc_reports or []),
        warnings=warnings,
        errors=errors,
        valid=not errors,
    )


def _normalize_expression_data_type(
    expression_data_type: str | DeliveryFileType | None,
) -> str | None:
    if expression_data_type is None:
        return None
    if isinstance(expression_data_type, DeliveryFileType):
        return expression_data_type.value
    return expression_data_type


def standardize_local_dataset(
    *,
    project_dir: str | Path,
    scan_report: DeliveryScanReport,
    import_plan: SelectedImportPlan,
) -> LocalDatasetManifest:
    """Copy selected processed files into a standard local dataset directory."""
    if not import_plan.valid:
        raise ValueError("selected_import_plan_invalid")
    if not import_plan.selected_expression_matrix:
        raise ValueError("expression_matrix_missing")
    if not import_plan.expression_data_type:
        raise ValueError("expression_data_type_missing")

    dataset_dir = Path(project_dir) / "local_datasets" / import_plan.dataset_slug
    standardized_dir = dataset_dir / "standardized"
    standardized_dir.mkdir(parents=True, exist_ok=True)

    expression_source = Path(import_plan.selected_expression_matrix)
    expression_target = standardized_dir / "expression_matrix.csv"
    _copy_processed_file(expression_source, expression_target)

    sample_metadata_target: Path | None = None
    if import_plan.selected_sample_metadata:
        sample_metadata_target = standardized_dir / "sample_metadata.csv"
        _copy_processed_file(Path(import_plan.selected_sample_metadata), sample_metadata_target)

    gene_annotation_target: Path | None = None
    if import_plan.selected_gene_annotation:
        gene_annotation_target = standardized_dir / "gene_annotation.csv"
        _copy_processed_file(Path(import_plan.selected_gene_annotation), gene_annotation_target)

    manifest = LocalDatasetManifest(
        dataset_slug=import_plan.dataset_slug,
        source_type="local_delivery",
        detected_files=[candidate.file_path for candidate in scan_report.candidates],
        selected_expression_matrix=str(expression_target),
        selected_sample_metadata=str(sample_metadata_target) if sample_metadata_target else None,
        selected_gene_annotation=str(gene_annotation_target) if gene_annotation_target else None,
        expression_data_type=import_plan.expression_data_type,
        sample_count=_count_matrix_samples(expression_target),
        gene_count=_count_matrix_genes(expression_target),
        created_at=datetime.now(UTC).isoformat(),
        warnings=list(import_plan.warnings),
    )

    _write_json(dataset_dir / "delivery_scan_report.json", scan_report.to_dict())
    _write_json(dataset_dir / "selected_import_plan.json", import_plan.to_dict())
    _write_json(standardized_dir / "local_dataset_manifest.json", manifest.to_dict())
    validation_report = build_local_dataset_validation_report(
        expression_matrix_path=expression_target,
        sample_metadata_path=sample_metadata_target,
        expression_data_type=import_plan.expression_data_type,
    )
    _write_json(standardized_dir / "validation_report.json", validation_report.to_dict())
    return manifest


def build_local_dataset_validation_report(
    *,
    expression_matrix_path: str | Path,
    sample_metadata_path: str | Path | None,
    expression_data_type: str,
) -> LocalDatasetValidationReport:
    expression_path = Path(expression_matrix_path)
    metadata_path = Path(sample_metadata_path) if sample_metadata_path else None
    header, rows = _read_table(expression_path)
    warnings: list[str] = []
    errors: list[str] = []

    gene_column = header[0] if header else ""
    if gene_column not in {"gene_id", "gene_symbol"}:
        errors.append("expression_gene_identifier_missing")

    matrix_samples = header[1:] if len(header) > 1 else []
    metadata_samples, group_size_summary = _read_metadata(metadata_path, warnings, errors)
    sample_id_match_status = _sample_match_status(matrix_samples, metadata_samples)
    if sample_id_match_status == "mismatch":
        errors.append("sample_id_mismatch")
    elif sample_id_match_status == "metadata_missing":
        warnings.append("sample_metadata_missing")

    gene_values = [row[0] for row in rows if row]
    duplicated_gene_count = len(gene_values) - len(set(gene_values))
    if duplicated_gene_count:
        warnings.append("duplicated_gene_ids")

    missing_value_count = 0
    negative_value_count = 0
    numeric_value_count = 0
    integer_value_count = 0
    for row in rows:
        for value in row[1:]:
            stripped = value.strip()
            if stripped == "":
                missing_value_count += 1
                continue
            try:
                numeric = float(stripped)
            except ValueError:
                errors.append("non_numeric_expression_value")
                continue
            numeric_value_count += 1
            if numeric < 0:
                negative_value_count += 1
            if numeric.is_integer():
                integer_value_count += 1

    if missing_value_count:
        warnings.append("missing_expression_values")
    if negative_value_count:
        errors.append("negative_expression_values")

    group_count = len(group_size_summary)
    for group_name, group_size in group_size_summary.items():
        if group_size < 3:
            warnings.append(f"small_group_size:{group_name}")

    expression_value_type = expression_data_type
    count_based_compatible = _is_count_based_compatible(
        expression_data_type=expression_data_type,
        numeric_value_count=numeric_value_count,
        integer_value_count=integer_value_count,
    )
    if expression_data_type in {
        DeliveryFileType.TPM_MATRIX.value,
        DeliveryFileType.FPKM_MATRIX.value,
        DeliveryFileType.NORMALIZED_EXPRESSION_MATRIX.value,
    }:
        warnings.append("not_count_based_compatible")

    return LocalDatasetValidationReport(
        sample_id_match_status=sample_id_match_status,
        missing_value_count=missing_value_count,
        duplicated_gene_count=duplicated_gene_count,
        group_count=group_count,
        group_size_summary=group_size_summary,
        expression_value_type=expression_value_type,
        count_based_compatible=count_based_compatible,
        warnings=_dedupe_preserve_order(warnings),
        errors=_dedupe_preserve_order(errors),
    )


def _copy_processed_file(source: Path, target: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(str(source))
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _count_matrix_samples(path: Path) -> int:
    header = _read_header(path)
    if not header:
        return 0
    return max(len(header) - 1, 0)


def _count_matrix_genes(path: Path) -> int:
    delimiter = _delimiter_for(path)
    count = 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        next(reader, None)
        for row in reader:
            if row:
                count += 1
    return count


def _read_header(path: Path) -> list[str]:
    delimiter = _delimiter_for(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        return next(reader, [])


def _delimiter_for(path: Path) -> str:
    return "\t" if path.suffix.lower() == ".tsv" else ","


def _read_table(path: Path) -> tuple[list[str], list[list[str]]]:
    delimiter = _delimiter_for(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter=delimiter)
        header = next(reader, [])
        rows = [row for row in reader if row]
    return header, rows


def _read_metadata(
    path: Path | None,
    warnings: list[str],
    errors: list[str],
) -> tuple[list[str], dict[str, int]]:
    if path is None:
        return [], {}
    header, rows = _read_table(path)
    if "sample_id" not in header:
        errors.append("metadata_sample_id_column_missing")
        return [], {}

    sample_index = header.index("sample_id")
    group_index = header.index("group") if "group" in header else None
    if group_index is None:
        warnings.append("metadata_group_column_missing")

    samples: list[str] = []
    group_size_summary: dict[str, int] = {}
    for row in rows:
        if sample_index >= len(row):
            continue
        sample_id = row[sample_index].strip()
        if sample_id:
            samples.append(sample_id)
        if group_index is not None and group_index < len(row):
            group_name = row[group_index].strip()
            if group_name:
                group_size_summary[group_name] = group_size_summary.get(group_name, 0) + 1
    return samples, group_size_summary


def _sample_match_status(matrix_samples: list[str], metadata_samples: list[str]) -> str:
    if not metadata_samples:
        return "metadata_missing"
    matrix_set = set(matrix_samples)
    metadata_set = set(metadata_samples)
    return "matched" if matrix_set == metadata_set else "mismatch"


def _is_count_based_compatible(
    *,
    expression_data_type: str,
    numeric_value_count: int,
    integer_value_count: int,
) -> bool:
    if expression_data_type != DeliveryFileType.RAW_COUNT_MATRIX.value:
        return False
    if numeric_value_count == 0:
        return False
    return integer_value_count / numeric_value_count >= 0.95


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
