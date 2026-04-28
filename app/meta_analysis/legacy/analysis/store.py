from __future__ import annotations

import json
from pathlib import Path

from analysis.models import AnalysisInput, MetaResult, StudyEffectResult


class AnalysisStore:
    def __init__(self, root_dir: Path) -> None:
        self._module_dir = root_dir / "analysis"
        self._analysis_inputs_file = self._module_dir / "analysis_inputs.json"
        self._study_effects_file = self._module_dir / "study_effects.json"
        self._meta_results_file = self._module_dir / "meta_results.json"

    def ensure_exists(self) -> None:
        self._module_dir.mkdir(parents=True, exist_ok=True)

    def list_analysis_inputs(
        self,
        *,
        project_id: str | None = None,
    ) -> list[AnalysisInput]:
        payload = self._read_json(self._analysis_inputs_file)
        records = [AnalysisInput.from_dict(item) for item in payload]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        return records

    def get_analysis_input(self, analysis_id: str) -> AnalysisInput | None:
        for record in self.list_analysis_inputs():
            if record.analysis_id == analysis_id:
                return record
        return None

    def save_analysis_input(self, record: AnalysisInput) -> AnalysisInput:
        records = self.list_analysis_inputs()
        self._write_records(
            self._analysis_inputs_file,
            self._upsert_by_key(records, record, "analysis_id"),
        )
        return record

    def list_study_effects(
        self,
        *,
        analysis_id: str | None = None,
    ) -> list[StudyEffectResult]:
        payload = self._read_json(self._study_effects_file)
        records = [StudyEffectResult.from_dict(item) for item in payload]
        if analysis_id is not None:
            records = [record for record in records if record.analysis_id == analysis_id]
        return records

    def replace_study_effects(
        self,
        analysis_id: str,
        records: list[StudyEffectResult],
    ) -> list[StudyEffectResult]:
        existing = self.list_study_effects()
        retained = [record for record in existing if record.analysis_id != analysis_id]
        updated = retained + list(records)
        self._write_records(self._study_effects_file, updated)
        return records

    def list_meta_results(
        self,
        *,
        analysis_id: str | None = None,
    ) -> list[MetaResult]:
        payload = self._read_json(self._meta_results_file)
        records = [MetaResult.from_dict(item) for item in payload]
        if analysis_id is not None:
            records = [record for record in records if record.analysis_id == analysis_id]
        return records

    def save_meta_result(self, record: MetaResult) -> MetaResult:
        records = self.list_meta_results()
        self._write_records(
            self._meta_results_file,
            self._upsert_by_key(records, record, "meta_result_id"),
        )
        return record

    def _read_json(self, file_path: Path) -> list[dict]:
        if not file_path.exists():
            return []
        return json.loads(file_path.read_text(encoding="utf-8"))

    def _write_records(
        self,
        file_path: Path,
        records: list[AnalysisInput] | list[StudyEffectResult] | list[MetaResult],
    ) -> None:
        self.ensure_exists()
        payload = [record.to_dict() for record in records]
        file_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _upsert_by_key(
        self,
        records: list[AnalysisInput] | list[MetaResult],
        record: AnalysisInput | MetaResult,
        key: str,
    ) -> list[AnalysisInput] | list[MetaResult]:
        record_key = getattr(record, key)
        updated: list[AnalysisInput] | list[MetaResult] = []
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
