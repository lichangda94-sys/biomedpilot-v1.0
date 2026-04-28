from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from extraction.rule_models import ExtractionRule, RuleEvaluationResult, RuleTargetType


RULE_BUNDLE_DIAGNOSTIC_KEYS = (
    "total_bundles",
    "valid_bundles",
    "invalid_bundles",
    "missing_files",
    "malformed_json",
    "disabled_rules",
    "warnings",
    "errors",
)


def inspect_rule_bundles(root_dir: Path) -> dict[str, Any]:
    rules_file = root_dir / "extraction" / "extraction_rules.json"
    diagnostics: dict[str, Any] = {
        "total_bundles": 0,
        "valid_bundles": 0,
        "invalid_bundles": 0,
        "missing_files": 0,
        "malformed_json": 0,
        "disabled_rules": 0,
        "warnings": 0,
        "errors": 0,
        "warning_messages": [],
        "error_messages": [],
    }

    if not rules_file.exists():
        diagnostics["missing_files"] = 1
        return diagnostics

    diagnostics["total_bundles"] = 1
    try:
        payload = json.loads(rules_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        diagnostics["invalid_bundles"] = 1
        diagnostics["malformed_json"] = 1
        diagnostics["errors"] = 1
        diagnostics["error_messages"].append(f"{rules_file.name}: malformed json ({exc.msg})")
        return diagnostics

    if not isinstance(payload, list):
        diagnostics["invalid_bundles"] = 1
        diagnostics["errors"] = 1
        diagnostics["error_messages"].append(f"{rules_file.name}: expected a list of rules")
        return diagnostics

    invalid_rules = 0
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            invalid_rules += 1
            diagnostics["error_messages"].append(f"{rules_file.name}[{index}]: expected an object")
            continue
        try:
            rule = ExtractionRule.from_dict(item)
        except (KeyError, TypeError, ValueError) as exc:
            invalid_rules += 1
            diagnostics["error_messages"].append(f"{rules_file.name}[{index}]: {exc}")
            continue
        if not rule.enabled:
            diagnostics["disabled_rules"] += 1

    if invalid_rules:
        diagnostics["invalid_bundles"] = 1
        diagnostics["errors"] += invalid_rules
    else:
        diagnostics["valid_bundles"] = 1

    return diagnostics


def format_rule_bundle_diagnostics_summary(diagnostics: dict[str, Any] | None) -> list[str]:
    values = diagnostics or {}
    lines = ["Rule bundle diagnostics:"]
    for key in RULE_BUNDLE_DIAGNOSTIC_KEYS:
        value = values.get(key, 0)
        if not isinstance(value, int):
            value = 0
        lines.append(f"- {key.replace('_', ' ')}: {value}")
    return lines


class RuleStore:
    def __init__(self, root_dir: Path) -> None:
        self._module_dir = root_dir / "extraction"
        self._rules_file = self._module_dir / "extraction_rules.json"
        self._results_file = self._module_dir / "rule_evaluation_results.json"

    @property
    def module_dir(self) -> Path:
        return self._module_dir

    def ensure_exists(self) -> None:
        self._module_dir.mkdir(parents=True, exist_ok=True)

    def list_rules(
        self,
        *,
        project_id: str | None = None,
        target_type: RuleTargetType | None = None,
        enabled_only: bool = False,
    ) -> list[ExtractionRule]:
        records = [ExtractionRule.from_dict(item) for item in self._read_json(self._rules_file)]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        if target_type is not None:
            records = [record for record in records if record.target_type == target_type]
        if enabled_only:
            records = [record for record in records if record.enabled]
        return records

    def get_rule(self, rule_id: str) -> ExtractionRule | None:
        for rule in self.list_rules():
            if rule.rule_id == rule_id:
                return rule
        return None

    def save_rule(self, rule: ExtractionRule) -> ExtractionRule:
        records = self.list_rules()
        self._write_records(
            self._rules_file,
            self._upsert_by_key(records, rule, "rule_id"),
        )
        return rule

    def list_results(
        self,
        *,
        project_id: str | None = None,
        target_id: str | None = None,
    ) -> list[RuleEvaluationResult]:
        records = [RuleEvaluationResult.from_dict(item) for item in self._read_json(self._results_file)]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        if target_id is not None:
            records = [record for record in records if record.target_id == target_id]
        return records

    def replace_results(
        self,
        *,
        target_id: str,
        results: list[RuleEvaluationResult],
    ) -> list[RuleEvaluationResult]:
        existing = self.list_results()
        retained = [record for record in existing if record.target_id != target_id]
        self._write_records(self._results_file, retained + list(results))
        return results

    def _read_json(self, file_path: Path) -> list[dict]:
        if not file_path.exists():
            return []
        return json.loads(file_path.read_text(encoding="utf-8"))

    def _write_records(
        self,
        file_path: Path,
        records: list[ExtractionRule] | list[RuleEvaluationResult],
    ) -> None:
        self.ensure_exists()
        payload = [record.to_dict() for record in records]
        file_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _upsert_by_key(
        self,
        records: list[ExtractionRule],
        record: ExtractionRule,
        key: str,
    ) -> list[ExtractionRule]:
        record_key = getattr(record, key)
        updated: list[ExtractionRule] = []
        replaced = False
        for item in records:
            if getattr(item, key) == record_key:
                updated.append(record)
                replaced = True
            else:
                updated.append(item)
        if not replaced:
            updated.append(record)
        return updated
