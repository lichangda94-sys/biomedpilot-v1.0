from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .models import CASE_ID_COLUMNS, PATIENT_ID_COLUMNS, SAMPLE_ID_COLUMNS


def select_column(fields: list[str], candidates: tuple[str, ...]) -> str:
    lower_to_original = {field.lower(): field for field in fields}
    for candidate in candidates:
        if candidate.lower() in lower_to_original:
            return lower_to_original[candidate.lower()]
    for field in fields:
        lowered = field.lower()
        if any(candidate.lower() in lowered for candidate in candidates):
            return field
    return ""


def tcga_case_id(value: object) -> tuple[str, bool]:
    text = str(value or "").strip()
    parts = text.split("-")
    if len(parts) >= 3 and parts[0].upper() == "TCGA":
        case = "-".join(parts[:3]).upper()
        return case, case != text
    return text, False


def build_case_sample_mapping(
    *,
    clinical_rows: list[dict[str, str]],
    sample_rows: list[dict[str, str]],
    expression_sample_ids: list[str],
) -> dict[str, Any]:
    clinical_fields = list(clinical_rows[0].keys()) if clinical_rows else []
    sample_fields = list(sample_rows[0].keys()) if sample_rows else []
    clinical_case_col = select_column(clinical_fields, CASE_ID_COLUMNS)
    clinical_sample_col = select_column(clinical_fields, SAMPLE_ID_COLUMNS)
    clinical_patient_col = select_column(clinical_fields, PATIENT_ID_COLUMNS)
    sample_case_col = select_column(sample_fields, CASE_ID_COLUMNS)
    sample_sample_col = select_column(sample_fields, SAMPLE_ID_COLUMNS)
    blockers: list[str] = []
    warnings: list[str] = []
    provenance: list[str] = []

    if not (clinical_case_col or clinical_sample_col or clinical_patient_col):
        blockers.append("missing_case_or_sample_identifier")

    clinical_case_ids: list[str] = []
    clinical_sample_ids: list[str] = []
    truncated = 0
    for row in clinical_rows:
        raw_case = row.get(clinical_case_col) or row.get(clinical_patient_col) or row.get(clinical_sample_col) or ""
        case, was_truncated = tcga_case_id(raw_case)
        if was_truncated:
            truncated += 1
        if case:
            clinical_case_ids.append(case)
        raw_sample = row.get(clinical_sample_col) or raw_case
        sample, sample_truncated = tcga_case_id(raw_sample)
        if sample_truncated:
            truncated += 1
        if raw_sample:
            clinical_sample_ids.append(str(raw_sample).strip())
    if truncated:
        warnings.append("tcga_barcode_truncated_to_case_id")
        provenance.append("tcga_barcode_policy: first 12 characters / TCGA-XX-YYYY case id")

    duplicate_case_ids = sorted([case for case, count in Counter(clinical_case_ids).items() if count > 1])
    duplicate_sample_ids = sorted([sample for sample, count in Counter(clinical_sample_ids).items() if count > 1])
    if duplicate_case_ids:
        blockers.append("duplicate_case_id_unresolved")
    if duplicate_sample_ids:
        blockers.append("duplicate_sample_id_unresolved")

    expression_to_case: dict[str, str] = {}
    if sample_rows and sample_sample_col:
        case_to_samples: dict[str, set[str]] = defaultdict(set)
        sample_to_cases: dict[str, set[str]] = defaultdict(set)
        for row in sample_rows:
            sample = str(row.get(sample_sample_col) or "").strip()
            raw_case = row.get(sample_case_col) or sample
            case, was_truncated = tcga_case_id(raw_case)
            if was_truncated:
                warnings.append("tcga_barcode_truncated_to_case_id")
            if sample and case:
                expression_to_case[sample] = case
                case_to_samples[case].add(sample)
                sample_to_cases[sample].add(case)
        if any(len(samples) > 1 for samples in case_to_samples.values()):
            warnings.append("one_case_multiple_samples_detected")
        if any(len(cases) > 1 for cases in sample_to_cases.values()):
            blockers.append("ambiguous_many_to_many_mapping")
    else:
        for sample in expression_sample_ids:
            case, was_truncated = tcga_case_id(sample)
            if was_truncated:
                warnings.append("tcga_barcode_truncated_to_case_id")
            expression_to_case[sample] = case

    clinical_cases = set(clinical_case_ids)
    expression_samples = set(expression_sample_ids)
    mapped_samples = sorted(sample for sample, case in expression_to_case.items() if sample in expression_samples and case in clinical_cases)
    mapped_cases = sorted({expression_to_case[sample] for sample in mapped_samples})
    unmapped_cases = sorted(clinical_cases - set(mapped_cases))
    unmapped_samples = sorted(expression_samples - set(mapped_samples))
    if clinical_cases and expression_samples and not mapped_samples:
        blockers.append("no_overlap_between_clinical_and_expression")
        blockers.append("case_sample_mapping_failed")
    elif unmapped_cases or unmapped_samples:
        warnings.append("partial_case_sample_mapping")
    if unmapped_cases:
        warnings.append("clinical_only_cases_present")
    if unmapped_samples:
        warnings.append("expression_only_samples_present")

    status = "passed" if not blockers else "blocked"
    if not blockers and warnings:
        status = "passed_with_warnings"
    return {
        "case_id_column": clinical_case_col,
        "sample_id_column": clinical_sample_col or sample_sample_col,
        "patient_id_column": clinical_patient_col,
        "case_sample_mapping_status": status,
        "case_sample_mapping_table": [{"sample_id": sample, "case_id": expression_to_case.get(sample, "")} for sample in sorted(expression_to_case)],
        "sample_count": len(expression_sample_ids),
        "case_count": len(clinical_cases),
        "mapped_case_count": len(mapped_cases),
        "mapped_sample_count": len(mapped_samples),
        "duplicate_case_ids": duplicate_case_ids,
        "duplicate_sample_ids": duplicate_sample_ids,
        "unmapped_cases": unmapped_cases,
        "unmapped_samples": unmapped_samples,
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
        "provenance": list(dict.fromkeys(provenance)),
    }
