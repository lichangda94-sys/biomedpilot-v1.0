from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from ._io import asset_path, event_observed, parse_float, read_table, sample_id


COX_PARAMETER_SCHEMA_VERSION = "biomedpilot.cox_univariate_parameter_manifest.v1"


def build_cox_univariate_parameter_manifest(
    survival_package: dict[str, Any] | Any | None,
    *,
    outcome_gate: dict[str, Any] | None = None,
    clinical_variable_audit: dict[str, Any] | None = None,
    covariate: str = "",
    covariate_label: str = "",
    minimum_sample_count: int = 4,
    minimum_event_count: int = 3,
    minimum_non_missing_count: int = 4,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    package = survival_package.to_dict() if hasattr(survival_package, "to_dict") else dict(survival_package or {})
    outcome = dict(outcome_gate or {})
    dependency = dict(dependency_snapshot or {})
    rows = read_table(asset_path(package.get("clinical_asset") if isinstance(package.get("clinical_asset"), dict) else None))
    time_field = str(package.get("time_field") or "")
    event_field = str(package.get("event_field") or "")
    event_coding = package.get("event_coding") if isinstance(package.get("event_coding"), dict) else {}
    covariate_type = _covariate_type(clinical_variable_audit, covariate, rows)
    stats = _covariate_stats(rows, covariate, time_field, event_field, event_coding)
    blockers: list[str] = []
    warnings: list[str] = ["proportional_hazards_not_tested", "single_variable_model_only", "not_clinical_conclusion"]

    if not package:
        blockers.append("missing_survival_input")
    if not outcome:
        blockers.append("missing_outcome_gate")
    if outcome.get("blockers"):
        blockers.append("outcome_gate_has_blockers")
    if not time_field:
        blockers.append("missing_time_field")
    if not event_field:
        blockers.append("missing_event_field")
    if event_coding.get("status") == "ambiguous":
        blockers.append("ambiguous_event_coding")
    if not covariate:
        blockers.append("missing_covariate")
    if covariate_type == "unknown_variable":
        blockers.append("unknown_covariate_type")
    if _identifier_like(covariate):
        blockers.append("identifier_not_allowed_as_covariate")
    if _date_like(covariate) and covariate_type != "continuous_variable":
        blockers.append("date_not_transformed")
    if stats["non_missing_count"] == 0:
        blockers.append("all_missing_covariate")
    if stats["unique_count"] <= 1 and stats["non_missing_count"] > 0:
        blockers.append("constant_covariate")
    if stats["non_missing_count"] < minimum_non_missing_count:
        blockers.append("too_few_non_missing_values")
    if stats["event_count"] < minimum_event_count:
        blockers.append("minimum_event_count_not_met")
    if stats["sample_count"] < minimum_sample_count:
        blockers.append("minimum_sample_count_not_met")
    if covariate_type == "categorical_variable" and stats["unique_count"] > 2:
        blockers.append("too_many_categories")
    if stats["mapping_failures"]:
        blockers.append("case_sample_mapping_failed")
    if dependency.get("status") != "passed":
        blockers.append("dependency_snapshot_missing" if not dependency else "dependency_snapshot_not_passed")

    if stats["missing_rate"] > 0.25:
        warnings.append("high_missingness")
    if covariate_type in {"binary_variable", "categorical_variable"} and stats["non_missing_count"]:
        min_count = min(stats["category_counts"].values()) if stats["category_counts"] else 0
        if min_count and max(stats["category_counts"].values()) / min_count >= 3:
            warnings.append("unbalanced_binary_groups")
        if min_count and min_count < 3:
            warnings.append("rare_category_detected")
    if covariate_type == "ordinal_variable":
        warnings.append("ordinal_order_needs_confirmation")
    if stats["continuous_outlier"]:
        warnings.append("continuous_variable_outlier_warning")

    return {
        "schema_version": COX_PARAMETER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "survival_clinical_input_id": str(package.get("survival_package_id") or package.get("survival_clinical_input_id") or ""),
        "survival_outcome_gate_id": str(outcome.get("survival_outcome_gate_id") or outcome.get("survival_package_id") or ""),
        "cox_parameter_id": _parameter_id(package, covariate),
        "time_field": time_field,
        "event_field": event_field,
        "time_unit": str(package.get("time_unit") or ""),
        "event_coding": event_coding,
        "censoring_policy": str(package.get("censoring_policy") or ""),
        "covariate": covariate,
        "covariate_label": covariate_label or covariate,
        "covariate_type": covariate_type,
        "covariate_source": "B12 clinical variable audit",
        "covariate_transform_policy": "none_for_binary_or_numeric_mvp",
        "category_reference_policy": "lexicographic_first_category_reference_for_binary",
        "included_cases": stats["included_cases"],
        "excluded_cases": stats["excluded_cases"],
        "sample_count": stats["sample_count"],
        "event_count": stats["event_count"],
        "non_missing_count": stats["non_missing_count"],
        "missing_count": stats["missing_count"],
        "missing_rate": stats["missing_rate"],
        "category_counts": stats["category_counts"],
        "minimum_sample_count": minimum_sample_count,
        "minimum_event_count": minimum_event_count,
        "minimum_non_missing_count": minimum_non_missing_count,
        "dependency_snapshot": dependency,
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
        "provenance": {
            "source": "B12 survival input package / outcome gate / clinical variable audit",
            "clinical_asset_path": str(asset_path(package.get("clinical_asset") if isinstance(package.get("clinical_asset"), dict) else None) or ""),
            "raw_recognition_report_used": False,
            "ui_temp_table_used": False,
            "automatic_variable_selection": False,
        },
    }


def _covariate_stats(rows: list[dict[str, str]], covariate: str, time_field: str, event_field: str, event_coding: dict[str, Any]) -> dict[str, Any]:
    included: list[str] = []
    excluded: list[str] = []
    values: list[str] = []
    events = 0
    mapping_failures = 0
    numeric_values: list[float] = []
    for row in rows:
        sid = sample_id(row)
        value = str(row.get(covariate) or "").strip()
        time_value = parse_float(row.get(time_field))
        event_value = event_observed(row.get(event_field), event_coding)
        if not sid or time_value is None or event_value is None:
            mapping_failures += 1
            if sid:
                excluded.append(sid)
            continue
        if value == "":
            excluded.append(sid)
            continue
        included.append(sid)
        values.append(value)
        events += int(event_value)
        parsed = parse_float(value)
        if parsed is not None:
            numeric_values.append(parsed)
    total = len(included) + len(excluded)
    category_counts = {value: values.count(value) for value in sorted(set(values))}
    continuous_outlier = False
    if len(numeric_values) >= 4:
        mean = sum(numeric_values) / len(numeric_values)
        variance = sum((value - mean) ** 2 for value in numeric_values) / len(numeric_values)
        sd = variance ** 0.5
        continuous_outlier = sd > 0 and any(abs(value - mean) > 4 * sd for value in numeric_values)
    return {
        "included_cases": included,
        "excluded_cases": excluded,
        "sample_count": len(included),
        "event_count": events,
        "non_missing_count": len(values),
        "missing_count": len(excluded),
        "missing_rate": (len(excluded) / total) if total else 0.0,
        "unique_count": len(set(values)),
        "category_counts": category_counts,
        "mapping_failures": mapping_failures,
        "continuous_outlier": continuous_outlier,
    }


def _covariate_type(audit: dict[str, Any] | None, covariate: str, rows: list[dict[str, str]]) -> str:
    mapping = audit.get("variable_mapping") if isinstance(audit, dict) else {}
    spec = mapping.get(covariate) if isinstance(mapping, dict) else {}
    typed = str(spec.get("variable_type") or "") if isinstance(spec, dict) else ""
    if typed:
        return typed
    values = [str(row.get(covariate) or "").strip() for row in rows if str(row.get(covariate) or "").strip()]
    unique = set(values)
    if not values:
        return "unknown_variable"
    if unique <= {"0", "1"}:
        return "binary_variable"
    numeric = sum(1 for value in values if parse_float(value) is not None)
    if numeric / len(values) >= 0.9:
        return "continuous_variable"
    if 1 < len(unique) <= 12:
        return "categorical_variable"
    return "unknown_variable"


def _identifier_like(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("id", "barcode", "uuid", "case", "sample", "participant"))


def _date_like(name: str) -> bool:
    lowered = name.lower()
    return "date" in lowered or lowered.endswith("_dt")


def _parameter_id(package: dict[str, Any], covariate: str) -> str:
    seed = "|".join([str(package.get("survival_package_id") or ""), str(package.get("time_field") or ""), str(package.get("event_field") or ""), covariate])
    return f"cox-param-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
