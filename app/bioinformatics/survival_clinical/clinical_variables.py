from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from .missingness import missingness
from .models import (
    CLINICAL_VARIABLE_AUDIT_SCHEMA_VERSION,
    DATE_HINTS,
    IDENTIFIER_HINTS,
    ORDINAL_HINTS,
    TEXT_HINTS,
    TIME_FIELD_CANDIDATES,
    utc_now,
)


def audit_clinical_variables(project_root: str | Path, survival_input: dict[str, Any]) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    rows = _read_table(_clinical_path(root, survival_input))
    fields = list(rows[0].keys()) if rows else []
    variables = [_audit_variable(field, [row.get(field, "") for row in rows]) for field in fields]
    blockers = ["missing_clinical_rows"] if not rows else []
    return {
        "schema_version": CLINICAL_VARIABLE_AUDIT_SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": "blocked" if blockers else "preflight_only",
        "survival_clinical_input_id": str(survival_input.get("survival_clinical_input_id") or ""),
        "variable_count": len(variables),
        "variables": variables,
        "summary": {
            "candidate_km_grouping": sum(1 for item in variables if "km_grouping_candidate" in item["allowed_analysis_candidates"]),
            "candidate_cox_covariate": sum(1 for item in variables if "cox_covariate_candidate" in item["allowed_analysis_candidates"]),
            "blocked_variables": sum(1 for item in variables if item["blockers"]),
        },
        "warnings": list(dict.fromkeys([warning for item in variables for warning in item["warnings"]])),
        "blockers": blockers,
        "forbidden_outputs": ["formal clinical association p-value", "Cox HR", "clinical conclusion", "treatment recommendation"],
    }


def _audit_variable(name: str, values: list[object]) -> dict[str, Any]:
    miss = missingness(values)
    non_missing_values = [str(value).strip() for value in values if str(value or "").strip() != ""]
    unique = sorted(set(non_missing_values))
    variable_type = _variable_type(name, non_missing_values)
    warnings: list[str] = []
    blockers: list[str] = []
    if miss["non_missing_count"] == 0:
        blockers.append("all_missing")
    if miss["missing_rate"] > 0.5:
        blockers.append("high_missing_rate")
    elif miss["missing_rate"] > 0.3:
        warnings.append("high_missing_rate")
    if len(unique) <= 1 and miss["non_missing_count"] > 0:
        blockers.append("constant_variable")
    if variable_type == "identifier":
        blockers.append("identifier_not_allowed_for_statistics")
    if variable_type == "unknown":
        blockers.append("unknown_variable_type")
    if miss["non_missing_count"] < 3 and miss["non_missing_count"] > 0:
        blockers.append("too_few_non_missing_values")
    if variable_type == "categorical" and len(unique) > 20:
        warnings.append("too_many_categories_for_cox")
    if variable_type in {"binary", "categorical", "ordinal"}:
        counts = {value: non_missing_values.count(value) for value in unique}
        if any(count < 2 for count in counts.values()):
            warnings.append("rare_category_detected")
    if variable_type == "ordinal":
        warnings.append("ordinal_order_needs_confirmation")
    if variable_type == "date":
        warnings.append("date_requires_transformation")
    return {
        "variable_name": name,
        "variable_type": variable_type,
        "semantic_hint": _semantic_hint(name),
        "unique_count": len(unique),
        "missing_count": miss["missing_count"],
        "missing_rate": miss["missing_rate"],
        "non_missing_count": miss["non_missing_count"],
        "example_values": unique[:5],
        "numeric_summary": _numeric_summary(non_missing_values) if variable_type in {"continuous", "time_to_event"} else {},
        "category_summary": {value: non_missing_values.count(value) for value in unique[:12]} if variable_type in {"binary", "categorical", "ordinal"} else {},
        "allowed_analysis_candidates": _candidates(variable_type, blockers),
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
    }


def _variable_type(name: str, values: list[str]) -> str:
    lowered = name.lower()
    if any(hint in lowered for hint in IDENTIFIER_HINTS):
        return "identifier"
    if any(hint in lowered for hint in DATE_HINTS) or all(_looks_like_date(value) for value in values[:5] if value):
        return "date"
    if any(hint in lowered for hint in TIME_FIELD_CANDIDATES):
        return "time_to_event"
    if any(hint in lowered for hint in ORDINAL_HINTS):
        return "ordinal"
    if any(hint in lowered for hint in TEXT_HINTS) or any(len(value.split()) > 3 for value in values):
        return "text"
    unique = sorted(set(values))
    if unique and set(value.lower() for value in unique) <= {"0", "1", "yes", "no", "true", "false", "male", "female", "m", "f", "alive", "dead"}:
        return "binary"
    numeric_count = sum(1 for value in values if _is_number(value))
    if values and numeric_count / len(values) >= 0.9:
        return "continuous"
    if 1 < len(unique) <= 20:
        return "categorical"
    if len(unique) > 20:
        return "text"
    return "unknown"


def _semantic_hint(name: str) -> str:
    lowered = name.lower()
    if any(hint in lowered for hint in IDENTIFIER_HINTS):
        return "identifier"
    if "stage" in lowered:
        return "stage"
    if "grade" in lowered:
        return "grade"
    if "time" in lowered or "follow" in lowered:
        return "survival_time"
    if "event" in lowered or "vital" in lowered or "death" in lowered:
        return "survival_event"
    return ""


def _candidates(variable_type: str, blockers: list[str]) -> list[str]:
    if "all_missing" in blockers or "constant_variable" in blockers or variable_type in {"identifier", "unknown", "text", "date"}:
        return ["identifier_only" if variable_type == "identifier" else "not_for_formal_statistics"]
    if variable_type in {"binary", "categorical", "ordinal"}:
        return ["km_grouping_candidate", "logrank_grouping_candidate", "cox_covariate_candidate", "clinical_association_candidate"]
    if variable_type == "continuous":
        return ["cox_covariate_candidate", "clinical_association_candidate"]
    if variable_type == "time_to_event":
        return ["not_for_formal_statistics"]
    return ["not_for_formal_statistics"]


def _numeric_summary(values: list[str]) -> dict[str, Any]:
    numeric = sorted(float(value) for value in values if _is_number(value))
    if not numeric:
        return {}
    return {"min": numeric[0], "max": numeric[-1], "median": numeric[len(numeric) // 2]}


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _looks_like_date(value: str) -> bool:
    return bool(re.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$", value.strip()))


def _clinical_path(root: Path, survival_input: dict[str, Any]) -> Path | None:
    asset = survival_input.get("clinical_asset") if isinstance(survival_input.get("clinical_asset"), dict) else {}
    value = str(asset.get("path") or "")
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def _read_table(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.is_file():
        return []
    try:
        first = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return []
    delimiter = "," if first.count(",") > first.count("\t") else "\t"
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter=delimiter)]
