"""Analysis input adapters for prepared TCGA packages."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .prepared_package import (
    load_tcga_clinical_table,
    load_tcga_expression_matrix,
    load_tcga_sample_metadata,
)


DEFAULT_TUMOR_LABELS = ("Primary Tumor", "Metastatic")
DEFAULT_NORMAL_LABELS = ("Solid Tissue Normal", "Blood Derived Normal")
_ENSEMBL_VERSION_RE = re.compile(r"^(ENSG[0-9]+)\.[0-9]+$", re.IGNORECASE)


def _clean_gene_id(value: str) -> str:
    text = str(value or "").strip()
    match = _ENSEMBL_VERSION_RE.match(text)
    if match:
        return match.group(1).upper()
    return text


def _gene_key(value: str) -> str:
    return _clean_gene_id(value).upper()


def _as_float(value: str) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _sample_barcode(row: dict[str, str]) -> str:
    return row.get("tcga_barcode") or row.get("sample_id") or row.get("barcode") or ""


def _patient_barcode(row: dict[str, str]) -> str:
    return row.get("participant_barcode") or row.get("patient_barcode") or ""


def _expression_sample_columns(expression_matrix: list[dict[str, str]]) -> list[str]:
    if not expression_matrix:
        return []
    return [key for key in expression_matrix[0] if key != "gene_id"]


def _find_gene_row(expression_matrix: list[dict[str, str]], gene_id: str) -> tuple[str, dict[str, str] | None]:
    target_key = _gene_key(gene_id)
    for row in expression_matrix:
        current_gene_id = row.get("gene_id", "")
        if _gene_key(current_gene_id) == target_key:
            return current_gene_id, row
    return "", None


def build_tcga_deg_input(
    manifest_or_path: dict[str, Any] | str | Path,
    tumor_labels: list[str] | tuple[str, ...] | None = None,
    normal_labels: list[str] | tuple[str, ...] | None = None,
    paired: bool = False,
) -> dict[str, Any]:
    """Build DEG-ready grouping inputs without running differential analysis."""
    expression_matrix = load_tcga_expression_matrix(manifest_or_path)
    sample_metadata = load_tcga_sample_metadata(manifest_or_path)
    tumor_set = set(tumor_labels or DEFAULT_TUMOR_LABELS)
    normal_set = set(normal_labels or DEFAULT_NORMAL_LABELS)
    warnings: list[str] = []

    sample_groups: list[dict[str, str]] = []
    tumor_samples: list[str] = []
    normal_samples: list[str] = []
    samples_by_patient: dict[str, dict[str, list[str]]] = {}

    for row in sample_metadata:
        barcode = _sample_barcode(row)
        patient = _patient_barcode(row)
        label = row.get("sample_type_label", "")
        if label in tumor_set:
            group = "tumor"
            tumor_samples.append(barcode)
        elif label in normal_set:
            group = "normal"
            normal_samples.append(barcode)
        else:
            group = "other"
        sample_groups.append({"barcode": barcode, "patient_barcode": patient, "group": group})
        patient_groups = samples_by_patient.setdefault(patient, {"tumor": [], "normal": []})
        if group in patient_groups:
            patient_groups[group].append(barcode)

    if not tumor_samples:
        warnings.append("no_tumor_samples")
    if not normal_samples:
        warnings.append("no_normal_samples")

    paired_patients: list[str] = []
    paired_samples: list[dict[str, str]] = []
    if paired:
        for patient, groups in sorted(samples_by_patient.items()):
            if patient and groups["tumor"] and groups["normal"]:
                paired_patients.append(patient)
                paired_samples.append(
                    {
                        "patient_barcode": patient,
                        "tumor_sample": groups["tumor"][0],
                        "normal_sample": groups["normal"][0],
                    }
                )
        if not paired_patients:
            warnings.append("no_paired_patients")

    return {
        "expression_matrix": expression_matrix,
        "sample_groups": sample_groups,
        "tumor_samples": tumor_samples,
        "normal_samples": normal_samples,
        "paired_patients": paired_patients,
        "paired_samples": paired_samples,
        "sample_count": len(sample_metadata),
        "tumor_count": len(tumor_samples),
        "normal_count": len(normal_samples),
        "warnings": warnings,
    }


def _aggregate_patient_expression(
    expression_matrix: list[dict[str, str]],
    sample_metadata: list[dict[str, str]],
    gene_id: str,
    aggregation: str,
    warnings: list[str],
) -> tuple[str, dict[str, str]]:
    if aggregation not in {"first", "mean"}:
        raise ValueError(f"Unsupported TCGA survival expression aggregation: {aggregation}")
    matched_gene_id, gene_row = _find_gene_row(expression_matrix, gene_id)
    if gene_row is None:
        warnings.append(f"gene_not_found:{gene_id}")
        return "", {}

    values_by_patient: dict[str, list[float | str]] = {}
    for sample in sample_metadata:
        barcode = _sample_barcode(sample)
        patient = _patient_barcode(sample)
        if not barcode or not patient or barcode not in gene_row:
            continue
        value = gene_row.get(barcode, "")
        if aggregation == "mean":
            numeric = _as_float(value)
            if numeric is not None:
                values_by_patient.setdefault(patient, []).append(numeric)
        else:
            values_by_patient.setdefault(patient, []).append(value)

    expression_by_patient: dict[str, str] = {}
    for patient, values in values_by_patient.items():
        if not values:
            continue
        if aggregation == "mean":
            numeric_values = [float(value) for value in values]
            expression_by_patient[patient] = str(sum(numeric_values) / len(numeric_values))
        else:
            expression_by_patient[patient] = str(values[0])
    return matched_gene_id, expression_by_patient


def build_tcga_survival_input(
    manifest_or_path: dict[str, Any] | str | Path,
    gene_id: str | None = None,
    aggregation: str = "first",
) -> dict[str, Any]:
    """Build patient-level survival inputs without running KM or Cox models."""
    expression_matrix = load_tcga_expression_matrix(manifest_or_path)
    sample_metadata = load_tcga_sample_metadata(manifest_or_path)
    clinical_table = load_tcga_clinical_table(manifest_or_path)
    warnings: list[str] = []

    sample_patients = sorted({patient for patient in (_patient_barcode(row) for row in sample_metadata) if patient})
    clinical_by_patient = {row.get("patient_barcode", ""): row for row in clinical_table if row.get("patient_barcode")}
    matched_gene_id = ""
    expression_by_patient: dict[str, str] = {}
    if gene_id is not None:
        matched_gene_id, expression_by_patient = _aggregate_patient_expression(
            expression_matrix,
            sample_metadata,
            gene_id,
            aggregation,
            warnings,
        )

    survival_table: list[dict[str, str]] = []
    missing_expression_patients: list[str] = []
    missing_survival_patients: list[str] = []
    for patient in sample_patients:
        clinical = clinical_by_patient.get(patient)
        if clinical is None:
            missing_survival_patients.append(patient)
            continue
        os_time = clinical.get("os_time_days", "")
        os_event = clinical.get("os_event", "")
        if not os_time or os_event == "":
            missing_survival_patients.append(patient)
            warnings.append(f"missing_survival_fields:{patient}")
            continue
        row = {
            "patient_barcode": patient,
            "os_time_days": os_time,
            "os_event": os_event,
        }
        if gene_id is not None:
            if patient in expression_by_patient:
                row["gene_expression"] = expression_by_patient[patient]
            else:
                missing_expression_patients.append(patient)
                row["gene_expression"] = ""
        survival_table.append(row)

    if gene_id is not None and not matched_gene_id:
        for patient in sample_patients:
            if patient not in missing_expression_patients:
                missing_expression_patients.append(patient)

    return {
        "survival_table": survival_table,
        "expression_by_patient": expression_by_patient,
        "clinical_table": clinical_table,
        "available_patient_count": len(survival_table),
        "missing_expression_patients": sorted(set(missing_expression_patients)),
        "missing_survival_patients": sorted(set(missing_survival_patients)),
        "warnings": warnings,
        "matched_gene_id": matched_gene_id,
    }


def build_tcga_correlation_input(
    manifest_or_path: dict[str, Any] | str | Path,
    target_gene: str,
) -> dict[str, Any]:
    """Build target-gene correlation inputs without calculating correlation."""
    expression_matrix = load_tcga_expression_matrix(manifest_or_path)
    warnings: list[str] = []
    matched_gene_id, gene_row = _find_gene_row(expression_matrix, target_gene)
    if gene_row is None:
        warnings.append(f"target_gene_not_found:{target_gene}")
        return {
            "target_gene": target_gene,
            "matched_gene_id": "",
            "target_expression": {},
            "expression_matrix": expression_matrix,
            "sample_count": len(_expression_sample_columns(expression_matrix)),
            "warnings": warnings,
        }

    target_expression = {
        sample: value for sample, value in gene_row.items() if sample != "gene_id"
    }
    return {
        "target_gene": target_gene,
        "matched_gene_id": matched_gene_id,
        "target_expression": target_expression,
        "expression_matrix": expression_matrix,
        "sample_count": len(target_expression),
        "warnings": warnings,
    }


__all__ = [
    "build_tcga_deg_input",
    "build_tcga_survival_input",
    "build_tcga_correlation_input",
]

