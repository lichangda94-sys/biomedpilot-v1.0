from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


def audit_cox_multivariate_design(survival_package: dict[str, Any] | Any, clinical_variable_audit: dict[str, Any], *, selected_covariates: list[str] | None = None, user_confirmed: bool = False) -> dict[str, Any]:
    package = survival_package.to_dict() if hasattr(survival_package, "to_dict") else dict(survival_package or {})
    selected = list(selected_covariates or [])
    variable_mapping = clinical_variable_audit.get("variable_mapping") if isinstance(clinical_variable_audit, dict) else {}
    candidates = [name for name, spec in variable_mapping.items() if isinstance(spec, dict) and spec.get("variable_type") not in {"unknown_variable", "time_to_event_variable"} and not _identifier_like(name)]
    event_count = int(package.get("event_count") or 0)
    sample_count = int(package.get("sample_count") or 0)
    model_covariates = selected or candidates
    event_per_variable = (event_count / len(model_covariates)) if model_covariates else 0.0
    blockers: list[str] = []
    warnings: list[str] = []
    if event_count < 10:
        blockers.append("too_few_events_for_multivariate")
    if model_covariates and event_per_variable < 10:
        blockers.append("too_many_covariates_for_events")
    if not candidates:
        blockers.append("no_valid_covariates")
    if any(_missing_fraction(variable_mapping.get(name, {})) > 0.4 for name in model_covariates):
        blockers.append("missingness_too_high")
    if any((variable_mapping.get(name, {}) or {}).get("variable_type") == "unknown_variable" for name in model_covariates):
        blockers.append("unknown_variable_type_present")
    if _basic_collinearity_warning(model_covariates):
        blockers.append("collinearity_unresolved")
    if not user_confirmed:
        blockers.append("user_confirmation_missing")
    for name in model_covariates:
        spec = variable_mapping.get(name, {}) if isinstance(variable_mapping, dict) else {}
        if int(spec.get("unique_count") or 0) > 8:
            warnings.append(f"too_many_categories:{name}")
        if spec.get("variable_type") == "ordinal_variable":
            warnings.append(f"ordinal_order_confirmation_required:{name}")
    return {
        "schema_version": "biomedpilot.cox_multivariate_design_audit.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cox_multivariate_design_id": _design_id(package, model_covariates),
        "survival_clinical_input_id": package.get("survival_package_id", ""),
        "survival_outcome_gate_id": package.get("survival_package_id", ""),
        "candidate_covariates": candidates,
        "selected_covariates": selected,
        "event_count": event_count,
        "sample_count": sample_count,
        "event_per_variable": event_per_variable,
        "missingness_summary": {name: variable_mapping.get(name, {}) for name in model_covariates},
        "collinearity_warning": "basic_name_overlap_only" if _basic_collinearity_warning(model_covariates) else "",
        "category_count_warnings": [item for item in warnings if item.startswith("too_many_categories")],
        "variable_type_warnings": [item for item in warnings if item.startswith("ordinal_order")],
        "model_formula_preview": "Surv(time, event) ~ " + " + ".join(model_covariates) if model_covariates else "",
        "warnings": list(dict.fromkeys(warnings)),
        "blockers": list(dict.fromkeys(blockers)),
        "provenance": {"design_audit_only": True, "multivariate_execution": False, "automatic_variable_selection": False},
    }


def _missing_fraction(spec: dict[str, Any]) -> float:
    if "missing_fraction" in spec:
        return float(spec.get("missing_fraction") or 0.0)
    total = int(spec.get("total_count") or 0)
    return (float(spec.get("missing_count") or 0) / total) if total else 0.0


def _identifier_like(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in ("id", "barcode", "uuid", "case", "sample", "participant"))


def _basic_collinearity_warning(names: list[str]) -> bool:
    lowered = [name.lower() for name in names]
    return len(lowered) != len(set(lowered))


def _design_id(package: dict[str, Any], covariates: list[str]) -> str:
    seed = "|".join([str(package.get("survival_package_id") or ""), *covariates])
    return f"cox-mv-design-{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:12]}"
