from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from ._io import asset_path, event_observed, parse_float, read_table, sample_id
from .cox_multivariate_design import audit_cox_multivariate_design


COX_MULTIVARIATE_PARAMETER_SCHEMA_VERSION = "biomedpilot.cox_multivariate_parameter_manifest.v1"


def build_cox_multivariate_parameter_manifest(
    survival_package: dict[str, Any] | Any | None,
    *,
    outcome_gate: dict[str, Any] | None = None,
    clinical_variable_audit: dict[str, Any] | None = None,
    selected_covariates: list[str] | None = None,
    minimum_sample_count: int = 12,
    minimum_event_count: int = 10,
    minimum_events_per_variable: int = 10,
    maximum_missing_fraction: float = 0.4,
    dependency_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    package = survival_package.to_dict() if hasattr(survival_package, "to_dict") else dict(survival_package or {})
    outcome = dict(outcome_gate or {})
    dependency = dict(dependency_snapshot or {})
    audit = clinical_variable_audit if isinstance(clinical_variable_audit, dict) else {}
    variable_mapping = audit.get("variable_mapping") if isinstance(audit.get("variable_mapping"), dict) else {}
    selected = [str(item) for item in selected_covariates or [] if str(item)]
    design_audit = audit_cox_multivariate_design(package, audit, selected_covariates=selected, user_confirmed=True)
    rows = read_table(asset_path(package.get("clinical_asset") if isinstance(package.get("clinical_asset"), dict) else None))
    time_field = str(package.get("time_field") or "")
    event_field = str(package.get("event_field") or "")
    event_coding = package.get("event_coding") if isinstance(package.get("event_coding"), dict) else {}
    encoded = _complete_case_rows(rows, selected, variable_mapping, time_field, event_field, event_coding)
    blockers: list[str] = []
    warnings: list[str] = ["multivariate_cox_statistical_result_only", "no_clinical_prognosis_or_treatment_advice", "proportional_hazards_diagnostic_planned_not_executed"]

    if not package:
        blockers.append("missing_survival_input")
    if package.get("blockers"):
        blockers.extend(str(item) for item in package.get("blockers", []) or [])
    if not outcome:
        blockers.append("missing_outcome_gate")
    if outcome.get("blockers"):
        blockers.append("outcome_gate_has_blockers")
    if not selected:
        blockers.append("missing_selected_covariates")
    if len(selected) < 2:
        blockers.append("multivariate_cox_requires_at_least_two_covariates")
    if not time_field:
        blockers.append("missing_time_field")
    if not event_field:
        blockers.append("missing_event_field")
    if event_coding.get("status") == "ambiguous":
        blockers.append("ambiguous_event_coding")
    if encoded["sample_count"] < minimum_sample_count:
        blockers.append("minimum_sample_count_not_met")
    if encoded["event_count"] < minimum_event_count:
        blockers.append("minimum_event_count_not_met")
    events_per_variable = encoded["event_count"] / len(selected) if selected else 0.0
    if selected and events_per_variable < minimum_events_per_variable:
        blockers.append("events_per_variable_not_met")
    if dependency.get("status") != "passed":
        blockers.append("dependency_snapshot_missing" if not dependency else "dependency_snapshot_not_passed")

    for name in selected:
        spec = variable_mapping.get(name) if isinstance(variable_mapping, dict) else {}
        variable_type = str((spec or {}).get("variable_type") or "unknown_variable")
        missing_fraction = _missing_fraction(spec or {}, encoded["raw_total_count"])
        if not spec:
            blockers.append(f"covariate_not_in_clinical_variable_audit:{name}")
        if variable_type == "unknown_variable":
            blockers.append(f"unknown_covariate_type:{name}")
        if variable_type == "time_to_event_variable":
            blockers.append(f"time_to_event_variable_not_allowed_as_covariate:{name}")
        if _identifier_like(name):
            blockers.append(f"identifier_not_allowed_as_covariate:{name}")
        if variable_type in {"categorical_variable", "ordinal_variable"} and int((spec or {}).get("unique_count") or 0) > 2:
            blockers.append(f"categorical_covariate_requires_dummy_expansion_not_enabled:{name}")
        if missing_fraction > maximum_missing_fraction:
            blockers.append(f"missingness_too_high:{name}")
        elif missing_fraction > 0.25:
            warnings.append(f"high_missingness:{name}")

    collinearity = _collinearity_report(encoded["matrix"], selected)
    if collinearity["status"] == "blocked":
        blockers.append("collinearity_unresolved")
    elif collinearity["warnings"]:
        warnings.extend(collinearity["warnings"])

    blockers.extend(str(item) for item in design_audit.get("blockers", []) or [] if str(item) not in {"user_confirmation_missing", "collinearity_unresolved"})

    return {
        "schema_version": COX_MULTIVARIATE_PARAMETER_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "passed",
        "survival_clinical_input_id": str(package.get("survival_package_id") or package.get("survival_clinical_input_id") or ""),
        "survival_outcome_gate_id": str(outcome.get("survival_outcome_gate_id") or outcome.get("survival_package_id") or ""),
        "cox_multivariate_parameter_id": _parameter_id(package, selected),
        "time_field": time_field,
        "event_field": event_field,
        "time_unit": str(package.get("time_unit") or ""),
        "event_coding": event_coding,
        "censoring_policy": str(package.get("censoring_policy") or ""),
        "selected_covariates": selected,
        "covariate_specs": {name: variable_mapping.get(name, {}) for name in selected},
        "covariate_encoding_policy": "continuous numeric as-is; binary categorical uses lexicographic reference; multi-level categorical blocks until dummy expansion contract",
        "model_formula_manifest": {
            "formula": "Surv(time, event) ~ " + " + ".join(selected) if selected else "",
            "time_field": time_field,
            "event_field": event_field,
            "covariates": selected,
            "automatic_variable_selection": False,
            "ph_assumption_diagnostic": "planned_not_executed",
        },
        "included_cases": encoded["included_cases"],
        "excluded_cases": encoded["excluded_cases"],
        "sample_count": encoded["sample_count"],
        "event_count": encoded["event_count"],
        "non_missing_count": encoded["sample_count"],
        "missing_count": len(encoded["excluded_cases"]),
        "events_per_variable": events_per_variable,
        "minimum_sample_count": minimum_sample_count,
        "minimum_event_count": minimum_event_count,
        "minimum_events_per_variable": minimum_events_per_variable,
        "missingness_policy": f"block if covariate missing fraction > {maximum_missing_fraction}",
        "collinearity_report": collinearity,
        "design_audit": design_audit,
        "dependency_snapshot": dependency,
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
        "provenance": {
            "source": "B12 survival input package / outcome gate / clinical variable audit",
            "clinical_asset_path": str(asset_path(package.get("clinical_asset") if isinstance(package.get("clinical_asset"), dict) else None) or ""),
            "raw_recognition_report_used": False,
            "ui_temp_table_used": False,
            "automatic_variable_selection": False,
            "risk_score_generated": False,
            "clinical_conclusion_generated": False,
        },
    }


def _complete_case_rows(
    rows: list[dict[str, str]],
    covariates: list[str],
    variable_mapping: dict[str, Any],
    time_field: str,
    event_field: str,
    event_coding: dict[str, Any],
) -> dict[str, Any]:
    included: list[str] = []
    excluded: list[str] = []
    matrix: list[list[float]] = []
    events = 0
    references = _category_references(rows, covariates)
    for row in rows:
        sid = sample_id(row)
        time = parse_float(row.get(time_field))
        event = event_observed(row.get(event_field), event_coding)
        values: list[float] = []
        valid = bool(sid) and time is not None and event is not None
        for name in covariates:
            raw = str(row.get(name) or "").strip()
            spec = variable_mapping.get(name) if isinstance(variable_mapping, dict) else {}
            variable_type = str((spec or {}).get("variable_type") or "")
            if raw == "":
                valid = False
                break
            if variable_type in {"binary_variable", "categorical_variable", "ordinal_variable"}:
                values.append(0.0 if raw == references.get(name, raw) else 1.0)
            else:
                parsed = parse_float(raw)
                if parsed is None:
                    valid = False
                    break
                values.append(parsed)
        if not valid:
            if sid:
                excluded.append(sid)
            continue
        included.append(sid)
        matrix.append(values)
        events += int(bool(event))
    return {
        "included_cases": included,
        "excluded_cases": excluded,
        "sample_count": len(included),
        "event_count": events,
        "matrix": matrix,
        "raw_total_count": len(rows),
        "category_references": references,
    }


def _category_references(rows: list[dict[str, str]], covariates: list[str]) -> dict[str, str]:
    references: dict[str, str] = {}
    for name in covariates:
        values = sorted({str(row.get(name) or "").strip() for row in rows if str(row.get(name) or "").strip()})
        if values:
            references[name] = values[0]
    return references


def _collinearity_report(matrix: list[list[float]], covariates: list[str]) -> dict[str, Any]:
    warnings: list[str] = []
    high_pairs: list[dict[str, Any]] = []
    if not matrix or len(covariates) < 2:
        return {"status": "passed", "high_correlation_pairs": [], "warnings": []}
    columns = [[row[index] for row in matrix] for index in range(len(covariates))]
    for i, left in enumerate(columns):
        for j, right in enumerate(columns):
            if j <= i:
                continue
            corr = _pearson(left, right)
            if abs(corr) >= 0.95:
                high_pairs.append({"left": covariates[i], "right": covariates[j], "correlation": corr})
            elif abs(corr) >= 0.85:
                warnings.append(f"collinearity_warning:{covariates[i]}:{covariates[j]}")
    return {"status": "blocked" if high_pairs else "warning" if warnings else "passed", "high_correlation_pairs": high_pairs, "warnings": warnings}


def _pearson(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=False))
    left_var = sum((a - left_mean) ** 2 for a in left)
    right_var = sum((b - right_mean) ** 2 for b in right)
    denominator = (left_var * right_var) ** 0.5
    return numerator / denominator if denominator else 0.0


def _missing_fraction(spec: dict[str, Any], fallback_total: int) -> float:
    if "missing_fraction" in spec:
        return float(spec.get("missing_fraction") or 0.0)
    total = int(spec.get("total_count") or fallback_total or 0)
    return (float(spec.get("missing_count") or 0) / total) if total else 0.0


def _identifier_like(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("id", "barcode", "uuid", "case", "sample", "participant"))


def _parameter_id(package: dict[str, Any], covariates: list[str]) -> str:
    seed = "|".join([str(package.get("survival_package_id") or ""), str(package.get("time_field") or ""), str(package.get("event_field") or ""), *covariates])
    return f"cox-mv-param-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
