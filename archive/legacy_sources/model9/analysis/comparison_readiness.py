from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ComparisonReadinessReport:
    comparison_id: str
    group_column: str
    case_group: str
    control_group: str
    case_count: int
    control_count: int
    missing_group_samples: list[str]
    total_samples: int
    runnable: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "group_column": self.group_column,
            "case_group": self.case_group,
            "control_group": self.control_group,
            "case_count": self.case_count,
            "control_count": self.control_count,
            "missing_group_samples": list(self.missing_group_samples),
            "total_samples": self.total_samples,
            "runnable": self.runnable,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


def build_comparison_readiness_report(
    sample_metadata: list[dict[str, Any]],
    comparison_rule: dict[str, Any] | Any,
    *,
    minimum_group_size: int = 2,
) -> ComparisonReadinessReport:
    comparison_id = str(_rule_value(comparison_rule, "comparison_id", "comparison"))
    group_column = str(_rule_value(comparison_rule, "group_column", ""))
    case_group = str(_rule_value(comparison_rule, "case_group", ""))
    control_group = str(_rule_value(comparison_rule, "control_group", ""))

    errors: list[str] = []
    warnings: list[str] = []
    case_count = 0
    control_count = 0
    missing_group_samples: list[str] = []

    if not group_column:
        errors.append("group_column_missing")
    if not case_group:
        errors.append("case_group_missing")
    if not control_group:
        errors.append("control_group_missing")

    if group_column:
        for index, sample in enumerate(sample_metadata):
            value = sample.get(group_column)
            sample_id = str(sample.get("sample_id") or sample.get("id") or f"sample_{index + 1}")
            if value is None or str(value).strip() == "":
                missing_group_samples.append(sample_id)
                continue
            normalized_value = str(value)
            if normalized_value == case_group:
                case_count += 1
            elif normalized_value == control_group:
                control_count += 1
    if group_column and sample_metadata and case_count == 0:
        errors.append("case_group_has_no_samples")
    if group_column and sample_metadata and control_count == 0:
        errors.append("control_group_has_no_samples")
    if case_count and case_count < minimum_group_size:
        warnings.append("case_group_below_minimum_size")
    if control_count and control_count < minimum_group_size:
        warnings.append("control_group_below_minimum_size")
    if missing_group_samples:
        warnings.append("samples_missing_group_assignment")

    return ComparisonReadinessReport(
        comparison_id=comparison_id,
        group_column=group_column,
        case_group=case_group,
        control_group=control_group,
        case_count=case_count,
        control_count=control_count,
        missing_group_samples=missing_group_samples,
        total_samples=len(sample_metadata),
        runnable=not errors,
        warnings=warnings,
        errors=errors,
    )


def _rule_value(rule: dict[str, Any] | Any, key: str, default: Any) -> Any:
    if isinstance(rule, dict):
        return rule.get(key, default)
    return getattr(rule, key, default)
