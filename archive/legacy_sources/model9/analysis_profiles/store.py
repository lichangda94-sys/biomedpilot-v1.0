from __future__ import annotations

import json
from pathlib import Path

from analysis_profiles.models import (
    AnalysisProfile,
    ComparisonRule,
    GenePanel,
    KeywordRuleSet,
    ThresholdProfile,
)


class AnalysisProfileStore:
    def __init__(self, root_dir: Path) -> None:
        self._module_dir = root_dir / "analysis_profiles"
        self._gene_panels_file = self._module_dir / "gene_panels.json"
        self._comparison_rules_file = self._module_dir / "comparison_rules.json"
        self._keyword_rule_sets_file = self._module_dir / "keyword_rule_sets.json"
        self._threshold_profiles_file = self._module_dir / "threshold_profiles.json"
        self._analysis_profiles_file = self._module_dir / "analysis_profiles.json"

    @property
    def module_dir(self) -> Path:
        return self._module_dir

    def ensure_exists(self) -> None:
        self._module_dir.mkdir(parents=True, exist_ok=True)

    def list_gene_panels(self, *, project_id: str | None = None) -> list[GenePanel]:
        records = [GenePanel.from_dict(item) for item in self._read_json(self._gene_panels_file)]
        return self._filter_project(records, project_id)

    def get_gene_panel(self, gene_panel_id: str) -> GenePanel | None:
        return self._find_by_key(self.list_gene_panels(), "gene_panel_id", gene_panel_id)

    def save_gene_panel(self, record: GenePanel) -> GenePanel:
        self._write_records(self._gene_panels_file, self._upsert_by_key(self.list_gene_panels(), record, "gene_panel_id"))
        return record

    def list_comparison_rules(self, *, project_id: str | None = None) -> list[ComparisonRule]:
        records = [ComparisonRule.from_dict(item) for item in self._read_json(self._comparison_rules_file)]
        return self._filter_project(records, project_id)

    def get_comparison_rule(self, comparison_rule_id: str) -> ComparisonRule | None:
        return self._find_by_key(self.list_comparison_rules(), "comparison_rule_id", comparison_rule_id)

    def save_comparison_rule(self, record: ComparisonRule) -> ComparisonRule:
        self._write_records(self._comparison_rules_file, self._upsert_by_key(self.list_comparison_rules(), record, "comparison_rule_id"))
        return record

    def list_keyword_rule_sets(self, *, project_id: str | None = None) -> list[KeywordRuleSet]:
        records = [KeywordRuleSet.from_dict(item) for item in self._read_json(self._keyword_rule_sets_file)]
        return self._filter_project(records, project_id)

    def get_keyword_rule_set(self, keyword_rule_set_id: str) -> KeywordRuleSet | None:
        return self._find_by_key(self.list_keyword_rule_sets(), "keyword_rule_set_id", keyword_rule_set_id)

    def save_keyword_rule_set(self, record: KeywordRuleSet) -> KeywordRuleSet:
        self._write_records(self._keyword_rule_sets_file, self._upsert_by_key(self.list_keyword_rule_sets(), record, "keyword_rule_set_id"))
        return record

    def list_threshold_profiles(self, *, project_id: str | None = None) -> list[ThresholdProfile]:
        records = [ThresholdProfile.from_dict(item) for item in self._read_json(self._threshold_profiles_file)]
        return self._filter_project(records, project_id)

    def get_threshold_profile(self, threshold_profile_id: str) -> ThresholdProfile | None:
        return self._find_by_key(self.list_threshold_profiles(), "threshold_profile_id", threshold_profile_id)

    def save_threshold_profile(self, record: ThresholdProfile) -> ThresholdProfile:
        self._write_records(self._threshold_profiles_file, self._upsert_by_key(self.list_threshold_profiles(), record, "threshold_profile_id"))
        return record

    def list_analysis_profiles(self, *, project_id: str | None = None) -> list[AnalysisProfile]:
        records = [AnalysisProfile.from_dict(item) for item in self._read_json(self._analysis_profiles_file)]
        return self._filter_project(records, project_id)

    def get_analysis_profile(self, analysis_profile_id: str) -> AnalysisProfile | None:
        return self._find_by_key(self.list_analysis_profiles(), "analysis_profile_id", analysis_profile_id)

    def save_analysis_profile(self, record: AnalysisProfile) -> AnalysisProfile:
        self._write_records(self._analysis_profiles_file, self._upsert_by_key(self.list_analysis_profiles(), record, "analysis_profile_id"))
        return record

    def _read_json(self, file_path: Path) -> list[dict]:
        if not file_path.exists():
            return []
        return json.loads(file_path.read_text(encoding="utf-8"))

    def _write_records(
        self,
        file_path: Path,
        records: list[GenePanel] | list[ComparisonRule] | list[KeywordRuleSet] | list[ThresholdProfile] | list[AnalysisProfile],
    ) -> None:
        self.ensure_exists()
        payload = [record.to_dict() for record in records]
        file_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _upsert_by_key(
        self,
        records: list,
        record: object,
        key: str,
    ) -> list:
        record_key = getattr(record, key)
        updated = []
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

    def _find_by_key(self, records: list, key: str, value: str):
        for record in records:
            if getattr(record, key) == value:
                return record
        return None

    def _filter_project(self, records: list, project_id: str | None) -> list:
        if project_id is None:
            return records
        return [record for record in records if record.project_id == project_id]
