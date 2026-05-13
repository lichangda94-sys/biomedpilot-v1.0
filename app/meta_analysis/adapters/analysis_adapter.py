from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AnalysisReadinessResult:
    extraction_records: int
    outcome_records: int
    valid_outcome_records: int
    outcome_type_counts: dict[str, int]
    runnable: bool
    blocking_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommended_action: str = ""


class AnalysisAdapter:
    def evaluate_extraction_pool(self, payload: dict[str, object]) -> AnalysisReadinessResult:
        extraction_records = list(payload.get("extraction_records", []))
        outcome_records = list(payload.get("outcome_records", []))
        supported_outcome_types = self.supported_outcome_types()

        blocking_errors: list[str] = []
        warnings: list[str] = []
        outcome_type_counts: dict[str, int] = {}
        valid_outcome_records = 0

        if not extraction_records:
            blocking_errors.append("extraction_records_missing")
        if not outcome_records:
            blocking_errors.append("outcome_records_missing")
        if payload.get("manual_data_entry_enabled") is False:
            warnings.append("manual_extraction_form_not_open")

        for index, outcome in enumerate(outcome_records, start=1):
            outcome_record = outcome if isinstance(outcome, dict) else {}
            outcome_type = str(outcome_record.get("outcome_type", "")).strip().lower()
            outcome_id = str(outcome_record.get("outcome_record_id", f"outcome_{index}"))
            outcome_type_counts[outcome_type or "unknown"] = outcome_type_counts.get(outcome_type or "unknown", 0) + 1
            if outcome_type not in supported_outcome_types:
                blocking_errors.append(f"{outcome_id}:unsupported_outcome_type")
                continue
            missing_fields = self._missing_required_fields(outcome_record, outcome_type)
            if missing_fields:
                blocking_errors.append(f"{outcome_id}:missing_{','.join(missing_fields)}")
                continue
            valid_outcome_records += 1

        if outcome_records and valid_outcome_records < 2:
            blocking_errors.append("at_least_two_valid_outcomes_required")
        if len([key for key, count in outcome_type_counts.items() if key != "unknown" and count > 0]) > 1:
            warnings.append("mixed_outcome_types_require_separate_analyses")

        runnable = not blocking_errors
        return AnalysisReadinessResult(
            extraction_records=len(extraction_records),
            outcome_records=len(outcome_records),
            valid_outcome_records=valid_outcome_records,
            outcome_type_counts=outcome_type_counts,
            runnable=runnable,
            blocking_errors=blocking_errors,
            warnings=warnings,
            recommended_action=self._recommended_action(runnable, blocking_errors, warnings),
        )

    def supported_outcome_types(self) -> set[str]:
        return {
            "binary",
            "continuous",
            "time_to_event",
            "prevalence",
            "incidence",
            "correlation",
            "diagnostic_2x2",
        }

    def _missing_required_fields(self, outcome_record: dict[str, object], outcome_type: str) -> list[str]:
        required_by_type = {
            "binary": ["group_a_n", "group_b_n", "events_a", "events_b"],
            "continuous": ["group_a_n", "group_b_n", "mean_a", "mean_b", "sd_a", "sd_b"],
            "time_to_event": ["hr", "ci_lower", "ci_upper"],
        }
        return [
            field_name
            for field_name in required_by_type.get(outcome_type, [])
            if outcome_record.get(field_name) is None
        ]

    def _recommended_action(self, runnable: bool, blocking_errors: list[str], warnings: list[str]) -> str:
        if runnable and warnings:
            return "review_warnings_before_analysis"
        if runnable:
            return "ready_for_statistical_analysis"
        if "extraction_records_missing" in blocking_errors:
            return "complete_screening_and_extraction_pool"
        if "outcome_records_missing" in blocking_errors:
            return "enter_outcome_data"
        if "at_least_two_valid_outcomes_required" in blocking_errors:
            return "add_more_valid_outcomes"
        return "resolve_analysis_preflight_errors"
