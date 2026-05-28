from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from ._io import asset_path, event_observed, parse_float, read_table, sample_id


KM_PARAMETER_SCHEMA_VERSION = "biomedpilot.km_logrank_parameter_manifest.v1"


def build_km_logrank_parameter_manifest(
    survival_package: dict[str, Any] | Any | None,
    *,
    outcome_gate: dict[str, Any] | None = None,
    clinical_variable_audit: dict[str, Any] | None = None,
    grouping_variable: str = "",
    group_a: str = "",
    group_b: str = "",
    grouping_source: str = "clinical_variable",
    grouping_method: str = "clinical_binary_or_categorical",
    minimum_group_size: int = 2,
    minimum_event_count: int = 1,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    package = survival_package.to_dict() if hasattr(survival_package, "to_dict") else dict(survival_package or {})
    outcome = dict(outcome_gate or {})
    dependency = dict(dependency_snapshot or {})
    rows = read_table(asset_path(package.get("clinical_asset") if isinstance(package.get("clinical_asset"), dict) else None))
    time_field = str(package.get("time_field") or "")
    event_field = str(package.get("event_field") or "")
    event_coding = package.get("event_coding") if isinstance(package.get("event_coding"), dict) else {}
    blockers: list[str] = []
    warnings: list[str] = []

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
    if not package.get("time_unit"):
        blockers.append("missing_time_unit")
    if event_coding.get("status") == "ambiguous":
        blockers.append("ambiguous_event_coding")
    if not grouping_variable:
        blockers.append("missing_grouping_variable")
    if not group_a or not group_b:
        blockers.append("missing_group_a_or_group_b")
    if group_a and group_b and group_a == group_b:
        blockers.append("same_group_labels")
    if dependency.get("status") != "passed":
        blockers.append("dependency_snapshot_missing" if not dependency else "dependency_snapshot_not_passed")

    grouped = _group_samples(rows, grouping_variable, group_a, group_b, time_field, event_field, event_coding)
    group_a_samples = grouped["group_a_samples"]
    group_b_samples = grouped["group_b_samples"]
    if set(group_a_samples) & set(group_b_samples):
        blockers.append("group_samples_overlap")
    if len(group_a_samples) < minimum_group_size or len(group_b_samples) < minimum_group_size:
        blockers.append("minimum_group_size_not_met")
    if grouped["mapping_failures"]:
        blockers.append("case_sample_mapping_failed")
    if grouped["group_a_event_count"] < minimum_event_count or grouped["group_b_event_count"] < minimum_event_count:
        blockers.append("minimum_event_count_not_met")
    if grouped["group_a_event_count"] == 0 or grouped["group_b_event_count"] == 0:
        blockers.append("grouping_contains_no_events")

    if 0 < grouped["group_a_event_count"] < 3 or 0 < grouped["group_b_event_count"] < 3:
        warnings.append("low_event_count")
    if group_a_samples and group_b_samples:
        larger = max(len(group_a_samples), len(group_b_samples))
        smaller = min(len(group_a_samples), len(group_b_samples))
        if smaller and larger / smaller >= 3:
            warnings.append("unbalanced_groups")
    missingness = package.get("missingness_report") if isinstance(package.get("missingness_report"), dict) else {}
    if any(_missing_fraction(item) > 0.25 for item in missingness.values() if isinstance(item, dict)):
        warnings.append("high_missingness")
    if _censored_fraction(grouped) > 0.75:
        warnings.append("many_censored_samples")
    if grouping_method in {"median_split", "upper_lower_quantile", "custom_cutoff", "expression_high_low"}:
        warnings.append("expression_cutoff_requires_confirmation")
    if _variable_type(clinical_variable_audit, grouping_variable) == "continuous_variable":
        warnings.append("ordinal_grouping_requires_confirmation")

    manifest = {
        "schema_version": KM_PARAMETER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "survival_clinical_input_id": str(package.get("survival_package_id") or package.get("survival_clinical_input_id") or ""),
        "survival_outcome_gate_id": str(outcome.get("survival_outcome_gate_id") or outcome.get("survival_package_id") or ""),
        "km_parameter_id": _parameter_id(package, grouping_variable, group_a, group_b),
        "time_field": time_field,
        "event_field": event_field,
        "time_unit": str(package.get("time_unit") or ""),
        "event_coding": event_coding,
        "censoring_policy": str(package.get("censoring_policy") or ""),
        "grouping_source": grouping_source,
        "grouping_variable": grouping_variable,
        "grouping_method": grouping_method,
        "group_a": group_a,
        "group_b": group_b,
        "group_a_samples": group_a_samples,
        "group_b_samples": group_b_samples,
        "group_a_case_count": len(group_a_samples),
        "group_b_case_count": len(group_b_samples),
        "group_a_event_count": grouped["group_a_event_count"],
        "group_b_event_count": grouped["group_b_event_count"],
        "minimum_group_size": minimum_group_size,
        "minimum_event_count": minimum_event_count,
        "missingness_policy": "exclude_missing_time_event_or_group",
        "logrank_method": "two_group_logrank_chi_square_df1",
        "dependency_snapshot": dependency,
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
        "provenance": {
            "source": "B12 survival input package / outcome gate / clinical variable audit",
            "clinical_asset_path": str(asset_path(package.get("clinical_asset") if isinstance(package.get("clinical_asset"), dict) else None) or ""),
            "raw_recognition_report_used": False,
            "ui_temp_table_used": False,
        },
    }
    return manifest


def _group_samples(
    rows: list[dict[str, str]],
    grouping_variable: str,
    group_a: str,
    group_b: str,
    time_field: str,
    event_field: str,
    event_coding: dict[str, Any],
) -> dict[str, Any]:
    group_a_samples: list[str] = []
    group_b_samples: list[str] = []
    group_a_events = 0
    group_b_events = 0
    mapping_failures = 0
    included = 0
    censored = 0
    for row in rows:
        sid = sample_id(row)
        time_value = parse_float(row.get(time_field))
        event_value = event_observed(row.get(event_field), event_coding)
        group_value = str(row.get(grouping_variable) or "").strip()
        if not sid or time_value is None or event_value is None or group_value not in {group_a, group_b}:
            if group_value in {group_a, group_b}:
                mapping_failures += 1
            continue
        included += 1
        if not event_value:
            censored += 1
        if group_value == group_a:
            group_a_samples.append(sid)
            group_a_events += int(event_value)
        elif group_value == group_b:
            group_b_samples.append(sid)
            group_b_events += int(event_value)
    return {
        "group_a_samples": group_a_samples,
        "group_b_samples": group_b_samples,
        "group_a_event_count": group_a_events,
        "group_b_event_count": group_b_events,
        "mapping_failures": mapping_failures,
        "included_count": included,
        "censored_count": censored,
    }


def _missing_fraction(item: dict[str, Any]) -> float:
    total = int(item.get("total_count") or 0)
    if total <= 0:
        return 0.0
    return float(item.get("missing_count") or 0) / total


def _censored_fraction(grouped: dict[str, Any]) -> float:
    total = int(grouped.get("included_count") or 0)
    if total <= 0:
        return 0.0
    return float(grouped.get("censored_count") or 0) / total


def _variable_type(clinical_variable_audit: dict[str, Any] | None, variable: str) -> str:
    mapping = clinical_variable_audit.get("variable_mapping") if isinstance(clinical_variable_audit, dict) else {}
    spec = mapping.get(variable) if isinstance(mapping, dict) else {}
    return str(spec.get("variable_type") or "") if isinstance(spec, dict) else ""


def _parameter_id(package: dict[str, Any], grouping_variable: str, group_a: str, group_b: str) -> str:
    seed = "|".join(
        [
            str(package.get("survival_package_id") or ""),
            str(package.get("time_field") or ""),
            str(package.get("event_field") or ""),
            grouping_variable,
            group_a,
            group_b,
        ]
    )
    return f"km-param-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
