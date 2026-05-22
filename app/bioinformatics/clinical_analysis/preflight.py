from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.shared.local_engines import ExternalEngineRegistry

from .dependency_check import check_survival_backend_dependencies
from .models import CLINICAL_PREFLIGHT_SCHEMA_VERSION, SURVIVAL_PREFLIGHT_SCHEMA_VERSION, SurvivalInputPackage


def build_survival_preflight(
    survival_package: SurvivalInputPackage | dict[str, Any],
    *,
    external_registry: ExternalEngineRegistry | None = None,
    storage_root: str | Path | None = None,
) -> dict[str, Any]:
    package = survival_package.to_dict() if isinstance(survival_package, SurvivalInputPackage) else dict(survival_package)
    dependency = check_survival_backend_dependencies(external_registry=external_registry, storage_root=storage_root)
    blockers = [str(item) for item in package.get("blockers", []) or []]
    warnings = [str(item) for item in package.get("warnings", []) or []]
    blockers.extend(str(item) for item in dependency.get("blockers", []) or [])
    if int(package.get("event_count") or 0) <= 0:
        blockers.append("no_events_available")
    if not package.get("sample_case_mapping"):
        blockers.append("missing_sample_case_mapping")
    return {
        "schema_version": SURVIVAL_PREFLIGHT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "preflight_passed_formal_execution_still_disabled",
        "survival_package_id": package.get("survival_package_id") or "",
        "allowed_next_steps": [] if blockers else ["backend_decision", "user_confirm_grouping_policy"],
        "dependency_snapshot": dependency,
        "blockers": list(dict.fromkeys(blockers)),
        "warnings": list(dict.fromkeys(warnings + list(dependency.get("warnings", []) or []))),
        "forbidden_outputs": ["KM plot", "Cox hazard ratio", "log-rank p-value", "clinical advice"],
    }


def build_clinical_association_preflight(clinical_rows: list[dict[str, Any]]) -> dict[str, Any]:
    variables = _variable_mapping(clinical_rows)
    warnings: list[str] = []
    blockers: list[str] = []
    if not clinical_rows:
        blockers.append("missing_clinical_rows")
    for name, spec in variables.items():
        if spec["missing_fraction"] > 0.5:
            warnings.append(f"high_missingness:{name}")
        if spec["variable_type"] == "unknown_variable":
            warnings.append(f"unknown_variable_type:{name}")
    if len([name for name, spec in variables.items() if spec["variable_type"] != "unknown_variable"]) > 12:
        warnings.append("multivariable_model_too_many_candidate_variables")
    return {
        "schema_version": CLINICAL_PREFLIGHT_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "blocked" if blockers else "design_preflight_only",
        "variable_mapping": variables,
        "allowed_tests_candidate": _allowed_tests(variables),
        "blockers": blockers,
        "warnings": warnings,
        "forbidden_outputs": ["formal clinical association p-value", "clinical advice"],
    }


def _variable_mapping(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not rows:
        return {}
    fields = list(rows[0].keys())
    mapping: dict[str, dict[str, Any]] = {}
    for field in fields:
        values = [row.get(field) for row in rows]
        non_missing = [value for value in values if str(value or "").strip() != ""]
        mapping[field] = {
            "variable_type": _variable_type(field, non_missing),
            "missing_count": len(values) - len(non_missing),
            "missing_fraction": (len(values) - len(non_missing)) / len(values) if values else 0.0,
            "unique_count": len({str(value) for value in non_missing}),
        }
    return mapping


def _variable_type(field: str, values: list[Any]) -> str:
    lowered = field.lower()
    if "time" in lowered or lowered.endswith("_days"):
        return "time_to_event_variable"
    unique = {str(value).strip() for value in values}
    if unique and unique <= {"0", "1"}:
        return "binary_variable"
    numeric = 0
    for value in values:
        try:
            float(value)
            numeric += 1
        except (TypeError, ValueError):
            pass
    if values and numeric / len(values) >= 0.9:
        return "continuous_variable"
    if 1 < len(unique) <= 12:
        return "categorical_variable"
    if len(unique) > 12:
        return "unknown_variable"
    return "unknown_variable"


def _allowed_tests(variables: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    tests: dict[str, list[str]] = {}
    for name, spec in variables.items():
        variable_type = spec["variable_type"]
        if variable_type == "continuous_variable":
            tests[name] = ["correlation_candidate", "group_comparison_candidate"]
        elif variable_type in {"categorical_variable", "binary_variable", "ordinal_variable"}:
            tests[name] = ["chi_square_or_fisher_candidate", "group_comparison_candidate"]
        elif variable_type == "time_to_event_variable":
            tests[name] = ["survival_preflight_candidate"]
        else:
            tests[name] = []
    return tests
