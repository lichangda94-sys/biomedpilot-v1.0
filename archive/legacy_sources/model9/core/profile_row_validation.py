from __future__ import annotations

from dataclasses import dataclass

from core.profile_row_templates import ProfileTemplateType


@dataclass(frozen=True)
class ProfileRowValidationIssue:
    row_index: int
    field: str
    message: str
    severity: str = "error"


REQUIRED_PROFILE_ROW_FIELDS: dict[ProfileTemplateType, tuple[str, ...]] = {
    "TREATMENT_EFFECT_META": (
        "row_id",
        "outcome_name",
        "effect_measure",
    ),
    "DIAGNOSTIC_ACCURACY_META": (
        "row_id",
        "index_test_name",
        "target_condition",
        "reference_standard",
    ),
    "BIOMARKER_PREVALENCE_ASSOCIATION_META": (
        "row_id",
        "row_subtype",
        "biomarker_name",
        "effect_measure",
    ),
}


def validate_profile_rows(
    profile_type: ProfileTemplateType,
    rows: list[dict[str, str]],
) -> list[ProfileRowValidationIssue]:
    required_fields = REQUIRED_PROFILE_ROW_FIELDS.get(profile_type)
    if required_fields is None:
        raise ValueError(f"Unsupported profile validation type: {profile_type}")
    issues: list[ProfileRowValidationIssue] = []
    for row_index, row in enumerate(rows):
        if _row_is_blank(row):
            continue
        for field in required_fields:
            if not row.get(field, "").strip():
                issues.append(
                    ProfileRowValidationIssue(
                        row_index=row_index,
                        field=field,
                        message=f"Required field is missing: {field}",
                    )
                )
        if profile_type == "DIAGNOSTIC_ACCURACY_META":
            issues.extend(_validate_diagnostic_metric_shape(row_index, row))
        elif profile_type == "BIOMARKER_PREVALENCE_ASSOCIATION_META":
            issues.extend(_validate_biomarker_shape(row_index, row))
    return issues


def _validate_diagnostic_metric_shape(
    row_index: int,
    row: dict[str, str],
) -> list[ProfileRowValidationIssue]:
    has_table = all(row.get(field, "").strip() for field in ("tp", "fp", "fn", "tn"))
    has_reported_metrics = bool(
        row.get("sensitivity", "").strip() and row.get("specificity", "").strip()
    )
    reported_metric_only = row.get("reported_metric_only", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }
    if has_table or (has_reported_metrics and reported_metric_only):
        return []
    return [
        ProfileRowValidationIssue(
            row_index=row_index,
            field="tp/fp/fn/tn",
            message=(
                "Diagnostic rows need TP/FP/FN/TN or sensitivity/specificity "
                "marked as reported_metric_only."
            ),
        )
    ]


def _validate_biomarker_shape(
    row_index: int,
    row: dict[str, str],
) -> list[ProfileRowValidationIssue]:
    row_subtype = row.get("row_subtype", "").strip()
    effect_measure = row.get("effect_measure", "").strip().lower()
    if row_subtype == "BIOMARKER_PREVALENCE" or effect_measure == "prevalence":
        missing = [
            field
            for field in ("positive_events", "total_n")
            if not row.get(field, "").strip()
        ]
        return [
            ProfileRowValidationIssue(
                row_index=row_index,
                field=field,
                message=f"Prevalence row is missing {field}.",
            )
            for field in missing
        ]
    return []


def _row_is_blank(row: dict[str, str]) -> bool:
    return not any(value.strip() for value in row.values())
