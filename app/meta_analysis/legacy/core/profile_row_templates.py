from __future__ import annotations

import csv
from pathlib import Path
from typing import Literal


ProfileTemplateType = Literal[
    "TREATMENT_EFFECT_META",
    "DIAGNOSTIC_ACCURACY_META",
    "BIOMARKER_PREVALENCE_ASSOCIATION_META",
]

PROFILE_ROWS_DIRNAME = "profile_rows"

PROFILE_ROW_TEMPLATE_FIELDS: dict[ProfileTemplateType, tuple[str, ...]] = {
    "TREATMENT_EFFECT_META": (
        "row_id",
        "outcome_type",
        "intervention_name",
        "comparator_name",
        "outcome_name",
        "effect_measure",
        "intervention_events",
        "intervention_total",
        "comparator_events",
        "comparator_total",
        "reported_effect",
        "reported_ci_lower",
        "reported_ci_upper",
        "extractor_note",
    ),
    "DIAGNOSTIC_ACCURACY_META": (
        "row_id",
        "index_test_name",
        "target_condition",
        "reference_standard",
        "tp",
        "fp",
        "fn",
        "tn",
        "sensitivity",
        "specificity",
        "reported_metric_only",
        "extractor_note",
    ),
    "BIOMARKER_PREVALENCE_ASSOCIATION_META": (
        "row_id",
        "row_subtype",
        "biomarker_name",
        "disease_name",
        "positive_events",
        "total_n",
        "effect_measure",
        "reported_effect",
        "assay_method",
        "threshold",
        "extractor_note",
    ),
}


def supported_profile_row_template_types() -> tuple[ProfileTemplateType, ...]:
    return tuple(PROFILE_ROW_TEMPLATE_FIELDS.keys())


def export_profile_row_template(profile_type: ProfileTemplateType, output_path: Path) -> Path:
    fields = _fields_for_profile(profile_type)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields))
        writer.writeheader()
    return output_path


def export_profile_rows_csv(
    profile_type: ProfileTemplateType,
    rows: list[dict[str, object]],
    output_path: Path,
) -> Path:
    fields = _fields_for_profile(profile_type)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    return output_path


def import_profile_rows_csv(profile_type: ProfileTemplateType, input_path: Path) -> list[dict[str, str]]:
    fields = _fields_for_profile(profile_type)
    with input_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        missing = [field for field in fields if field not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV template is missing required fields: {', '.join(missing)}")
        return [{field: (row.get(field) or "") for field in fields} for row in reader]


def project_profile_rows_path(project_dir: Path, profile_type: ProfileTemplateType) -> Path:
    _fields_for_profile(profile_type)
    return project_dir / PROFILE_ROWS_DIRNAME / f"{profile_type}.csv"


def save_project_profile_rows(
    project_dir: Path,
    profile_type: ProfileTemplateType,
    rows: list[dict[str, object]],
) -> Path:
    return export_profile_rows_csv(
        profile_type,
        rows,
        project_profile_rows_path(project_dir, profile_type),
    )


def load_project_profile_rows(
    project_dir: Path,
    profile_type: ProfileTemplateType,
) -> list[dict[str, str]]:
    input_path = project_profile_rows_path(project_dir, profile_type)
    if not input_path.exists():
        return []
    return import_profile_rows_csv(profile_type, input_path)


def _fields_for_profile(profile_type: ProfileTemplateType) -> tuple[str, ...]:
    try:
        return PROFILE_ROW_TEMPLATE_FIELDS[profile_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported profile row template: {profile_type}") from exc
