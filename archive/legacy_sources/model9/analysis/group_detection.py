from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


@dataclass(slots=True)
class GroupDetectionReport:
    group_column_candidates: list[str] = field(default_factory=list)
    detected_groups: list[str] = field(default_factory=list)
    sample_to_group: dict[str, str] = field(default_factory=dict)
    ambiguous_samples: list[str] = field(default_factory=list)
    excluded_group_candidates: list[str] = field(default_factory=list)
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "group_column_candidates": list(self.group_column_candidates),
            "detected_groups": list(self.detected_groups),
            "sample_to_group": dict(self.sample_to_group),
            "ambiguous_samples": list(self.ambiguous_samples),
            "excluded_group_candidates": list(self.excluded_group_candidates),
            "confidence": self.confidence,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


def detect_geo_sample_groups(
    sample_metadata_rows: list[dict[str, str]],
) -> GroupDetectionReport:
    if not sample_metadata_rows:
        return GroupDetectionReport(
            warnings=["sample_metadata_missing"],
            errors=["sample_metadata_missing"],
        )

    group_column_candidates = _group_column_candidates(sample_metadata_rows)
    sample_to_group: dict[str, str] = {}
    ambiguous_samples: list[str] = []
    excluded_group_candidates: list[str] = []
    detected_groups: list[str] = []

    for index, row in enumerate(sample_metadata_rows):
        sample_id = row.get("sample_id") or f"sample_{index + 1}"
        groups = _classify_row(row)
        if "atc" in groups:
            sample_to_group[sample_id] = "excluded_atc"
            excluded_group_candidates.append(sample_id)
            continue
        if _is_excluded_non_target_row(row):
            sample_to_group[sample_id] = "excluded_non_target"
            excluded_group_candidates.append(sample_id)
            continue
        if len(groups) == 1:
            group = groups[0]
            sample_to_group[sample_id] = group
            detected_groups.append(group)
        elif len(groups) > 1:
            ambiguous_samples.append(sample_id)
        else:
            ambiguous_samples.append(sample_id)

    detected_groups = _dedupe(detected_groups)
    excluded_group_candidates = _dedupe(excluded_group_candidates)
    warnings: list[str] = []
    if ambiguous_samples:
        warnings.append("ambiguous_samples")
    if "excluded_atc" in sample_to_group.values():
        warnings.append("excluded_atc_samples")
    if "excluded_non_target" in sample_to_group.values():
        warnings.append("excluded_non_target_samples")
    if not detected_groups:
        warnings.append("no_groups_detected")

    classified = len(sample_to_group)
    confidence = classified / len(sample_metadata_rows)
    return GroupDetectionReport(
        group_column_candidates=group_column_candidates,
        detected_groups=detected_groups,
        sample_to_group=sample_to_group,
        ambiguous_samples=ambiguous_samples,
        excluded_group_candidates=excluded_group_candidates,
        confidence=round(confidence, 3),
        warnings=warnings,
    )


def _group_column_candidates(rows: list[dict[str, str]]) -> list[str]:
    candidates: list[str] = []
    for row in rows:
        for column, value in row.items():
            if column == "sample_id" or not value:
                continue
            if _classify_text(value):
                candidates.append(column)
    return _dedupe(candidates)


def _classify_row(row: dict[str, str]) -> list[str]:
    groups: list[str] = []
    for column, value in row.items():
        if column == "sample_id":
            continue
        if column == "characteristics_ch1":
            groups.extend(_classify_characteristics(value))
        else:
            groups.extend(_classify_text(value))
    return _dedupe(groups)


def _classify_text(value: str) -> list[str]:
    text = value.lower()
    groups: list[str] = []
    if (
        "papillary thyroid carcinoma" in text
        or "papillary carcinoma" in text
        or re.search(r"\bptc\b", text)
    ):
        groups.append("ptc")
    if "anaplastic thyroid carcinoma" in text or re.search(r"\batc\b", text):
        groups.append("atc")
    if _is_normal_control_text(text):
        groups.append("normal")
    return groups


def _classify_characteristics(value: str) -> list[str]:
    groups: list[str] = []
    for part in value.split(";"):
        text = part.strip().lower()
        if not text:
            continue
        if ":" in text:
            key, raw_value = text.split(":", 1)
            text = raw_value.strip()
            if key.strip() == "morphology of papillary carcinomas" and text in {
                "",
                "na",
                "n/a",
                "not applicable",
            }:
                continue
        groups.extend(_classify_text(text))
    return _dedupe(groups)


def _is_normal_control_text(text: str) -> bool:
    return (
        "normal thyroid" in text
        or "non-tumor control" in text
        or "non tumor control" in text
        or "patient-matched non-tumor control" in text
        or "matched non-tumor" in text
        or "non-tumoral" in text
        or "adjacent non-tumor" in text
        or "adjacent normal" in text
        or "normal control" in text
        or re.search(r"\bnormal\b", text) is not None
    )


def _is_excluded_non_target_row(row: dict[str, str]) -> bool:
    # Restrict non-target exclusions to sample label fields. Clinical
    # characteristics often contain generic field names such as
    # "ln.metastasis..cm." that should not classify the sample itself.
    label_text = " ".join(
        row.get(column, "")
        for column in ("title", "source_name_ch1")
    ).lower()
    return (
        "lymph node metastasis" in label_text
        or re.search(r"\blnm\b", label_text) is not None
        or "recurrence" in label_text
        or re.search(r"\brec\b", label_text) is not None
        or "follicular thyroid carcinoma" in label_text
        or "follicular thyroid adenoma" in label_text
        or "oncocytic thyroid carcinoma" in label_text
        or "oncocytic thyroid adenoma" in label_text
        or "medullary thyroid carcinoma" in label_text
    )


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
