from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from extraction.models import ExtractionRecord, OutcomeRecord
from extraction.rule_models import (
    ExtractionRule,
    RuleCheckType,
    RuleEvaluationResult,
    RuleEvaluationStatus,
    RuleSeverity,
    RuleTargetType,
)
from extraction.rule_store import RuleStore
from extraction.store import ExtractionStore


class RuleService:
    def __init__(self, extraction_store: ExtractionStore, rule_store: RuleStore) -> None:
        self._extraction_store = extraction_store
        self._rule_store = rule_store

    @classmethod
    def from_root_dir(cls, root_dir: Path) -> "RuleService":
        return cls(ExtractionStore(root_dir), RuleStore(root_dir))

    def create_rule(
        self,
        project_id: str,
        target_type: RuleTargetType,
        check_type: RuleCheckType,
        field_name: str,
        *,
        label: str = "",
        severity: RuleSeverity = RuleSeverity.ERROR,
        enabled: bool = True,
        parameters: dict[str, object] | None = None,
        notes: str = "",
    ) -> ExtractionRule:
        self._require(project_id.strip(), "project_id is required.")
        self._require(field_name.strip(), "field_name is required.")
        rule = ExtractionRule(
            rule_id=f"rule-{uuid4().hex[:12]}",
            project_id=project_id.strip(),
            target_type=target_type,
            check_type=check_type,
            field_name=field_name.strip(),
            label=label.strip(),
            severity=severity,
            enabled=enabled,
            parameters=dict(parameters or {}),
            notes=notes.strip(),
        )
        return self._rule_store.save_rule(rule)

    def update_rule(
        self,
        rule_id: str,
        **fields: object,
    ) -> ExtractionRule:
        rule = self._require_rule(rule_id)
        for key, value in fields.items():
            if key == "parameters":
                setattr(rule, key, dict(value or {}))  # type: ignore[arg-type]
            else:
                setattr(rule, key, value)
        rule.touch()
        return self._rule_store.save_rule(rule)

    def list_rules(
        self,
        project_id: str,
        *,
        target_type: RuleTargetType | None = None,
        enabled_only: bool = False,
    ) -> list[ExtractionRule]:
        return self._rule_store.list_rules(
            project_id=project_id,
            target_type=target_type,
            enabled_only=enabled_only,
        )

    def evaluate_extraction_record(self, extraction_record_id: str) -> list[RuleEvaluationResult]:
        record = self._extraction_store.get_extraction_record(extraction_record_id)
        if record is None:
            raise ValueError(f"Extraction record does not exist: {extraction_record_id}")
        rules = self._rule_store.list_rules(
            project_id=record.project_id,
            target_type=RuleTargetType.EXTRACTION_RECORD,
            enabled_only=True,
        )
        results = [
            self._evaluate_rule(rule, target=record, target_id=record.extraction_record_id)
            for rule in rules
        ]
        return self._rule_store.replace_results(target_id=record.extraction_record_id, results=results)

    def evaluate_outcome_record(self, outcome_record_id: str) -> list[RuleEvaluationResult]:
        record = self._extraction_store.get_outcome_record(outcome_record_id)
        if record is None:
            raise ValueError(f"Outcome record does not exist: {outcome_record_id}")
        extraction = self._extraction_store.get_extraction_record(record.extraction_record_id)
        if extraction is None:
            raise ValueError(f"Extraction record does not exist: {record.extraction_record_id}")
        rules = self._rule_store.list_rules(
            project_id=extraction.project_id,
            target_type=RuleTargetType.OUTCOME_RECORD,
            enabled_only=True,
        )
        results = [
            self._evaluate_rule(rule, target=record, target_id=record.outcome_record_id)
            for rule in rules
        ]
        return self._rule_store.replace_results(target_id=record.outcome_record_id, results=results)

    def list_results(self, *, project_id: str | None = None, target_id: str | None = None) -> list[RuleEvaluationResult]:
        return self._rule_store.list_results(project_id=project_id, target_id=target_id)

    def _evaluate_rule(
        self,
        rule: ExtractionRule,
        *,
        target: ExtractionRecord | OutcomeRecord,
        target_id: str,
    ) -> RuleEvaluationResult:
        value = getattr(target, rule.field_name, None)
        status, message = self._check_value(rule, value)
        return RuleEvaluationResult(
            result_id=f"rres-{uuid4().hex[:12]}",
            rule_id=rule.rule_id,
            project_id=rule.project_id,
            target_type=rule.target_type,
            target_id=target_id,
            status=status,
            message=message,
            severity=rule.severity,
        )

    def _check_value(
        self,
        rule: ExtractionRule,
        value: object,
    ) -> tuple[RuleEvaluationStatus, str]:
        if rule.check_type == RuleCheckType.REQUIRED_FIELD:
            if value is None or value == "":
                return RuleEvaluationStatus.FAILED, f"{rule.field_name} is required."
            return RuleEvaluationStatus.PASSED, f"{rule.field_name} is present."

        if rule.check_type == RuleCheckType.NUMERIC_RANGE:
            if value is None or value == "":
                return RuleEvaluationStatus.SKIPPED, f"{rule.field_name} has no value."
            try:
                numeric_value = float(value)
            except (TypeError, ValueError):
                return RuleEvaluationStatus.FAILED, f"{rule.field_name} is not numeric."
            min_value = rule.parameters.get("min")
            max_value = rule.parameters.get("max")
            if min_value is not None and numeric_value < float(min_value):
                return RuleEvaluationStatus.FAILED, f"{rule.field_name} is below minimum {min_value}."
            if max_value is not None and numeric_value > float(max_value):
                return RuleEvaluationStatus.FAILED, f"{rule.field_name} is above maximum {max_value}."
            return RuleEvaluationStatus.PASSED, f"{rule.field_name} is within range."

        if rule.check_type == RuleCheckType.ALLOWED_VALUES:
            allowed = [str(item) for item in rule.parameters.get("allowed_values", [])]
            if not allowed:
                return RuleEvaluationStatus.SKIPPED, "No allowed values configured."
            if str(value) in allowed:
                return RuleEvaluationStatus.PASSED, f"{rule.field_name} is allowed."
            return RuleEvaluationStatus.FAILED, f"{rule.field_name} is not an allowed value."

        return RuleEvaluationStatus.SKIPPED, f"Unsupported rule type: {rule.check_type.value}"

    def _require_rule(self, rule_id: str) -> ExtractionRule:
        rule = self._rule_store.get_rule(rule_id)
        if rule is None:
            raise ValueError(f"Extraction rule does not exist: {rule_id}")
        return rule

    def _require(self, condition: object, message: str) -> None:
        if not condition:
            raise ValueError(message)
