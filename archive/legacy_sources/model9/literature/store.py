from __future__ import annotations

import json
from pathlib import Path

from literature.models import (
    DedupMergeResult,
    DuplicateCandidateGroup,
    ExclusionReason,
    ImportBatch,
    ImportRecord,
    LiteratureProject,
    NormalizedLiteratureRecord,
    ParsedLiteratureRecord,
    ScreeningDecision,
    ScreeningRecord,
    ScreeningStage,
)


class LiteratureStore:
    def __init__(self, root_dir: Path) -> None:
        self._module_dir = root_dir / "literature"
        self._projects_file = self._module_dir / "projects.json"
        self._imports_file = self._module_dir / "import_records.json"
        self._batches_file = self._module_dir / "import_batches.json"
        self._parsed_records_file = self._module_dir / "parsed_records.json"
        self._normalized_records_file = self._module_dir / "normalized_records.json"
        self._duplicate_groups_file = self._module_dir / "duplicate_groups.json"
        self._merge_results_file = self._module_dir / "merge_results.json"
        self._screening_records_file = self._module_dir / "screening_records.json"
        self._exclusion_reasons_file = self._module_dir / "exclusion_reasons.json"

    @property
    def module_dir(self) -> Path:
        return self._module_dir

    def ensure_exists(self) -> None:
        self._module_dir.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> list[LiteratureProject]:
        payload = self._read_json(self._projects_file)
        return [LiteratureProject.from_dict(item) for item in payload]

    def get_project(self, project_id: str) -> LiteratureProject | None:
        for project in self.list_projects():
            if project.project_id == project_id:
                return project
        return None

    def save_project(self, project: LiteratureProject) -> LiteratureProject:
        projects = self.list_projects()
        self._write_records(
            self._projects_file,
            self._upsert_by_key(projects, project, "project_id"),
        )
        return project

    def list_import_records(self, project_id: str | None = None) -> list[ImportRecord]:
        payload = self._read_json(self._imports_file)
        records = [ImportRecord.from_dict(item) for item in payload]
        if project_id is None:
            return records
        return [record for record in records if record.project_id == project_id]

    def save_import_record(self, record: ImportRecord) -> ImportRecord:
        records = self.list_import_records()
        self._write_records(
            self._imports_file,
            self._upsert_by_key(records, record, "import_id"),
        )
        return record

    def list_import_batches(self, project_id: str | None = None) -> list[ImportBatch]:
        payload = self._read_json(self._batches_file)
        batches = [ImportBatch.from_dict(item) for item in payload]
        if project_id is None:
            return batches
        return [batch for batch in batches if batch.project_id == project_id]

    def get_import_batch(self, batch_id: str) -> ImportBatch | None:
        for batch in self.list_import_batches():
            if batch.batch_id == batch_id:
                return batch
        return None

    def save_import_batch(self, batch: ImportBatch) -> ImportBatch:
        batches = self.list_import_batches()
        self._write_records(
            self._batches_file,
            self._upsert_by_key(batches, batch, "batch_id"),
        )
        return batch

    def list_parsed_records(
        self,
        *,
        project_id: str | None = None,
        batch_id: str | None = None,
    ) -> list[ParsedLiteratureRecord]:
        payload = self._read_json(self._parsed_records_file)
        records = [ParsedLiteratureRecord.from_dict(item) for item in payload]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        if batch_id is not None:
            records = [record for record in records if record.batch_id == batch_id]
        return records

    def replace_parsed_records(
        self,
        batch_id: str,
        records: list[ParsedLiteratureRecord],
    ) -> list[ParsedLiteratureRecord]:
        existing = self.list_parsed_records()
        retained = [record for record in existing if record.batch_id != batch_id]
        updated = retained + list(records)
        self._write_records(self._parsed_records_file, updated)
        return records

    def list_normalized_records(
        self,
        *,
        project_id: str | None = None,
    ) -> list[NormalizedLiteratureRecord]:
        payload = self._read_json(self._normalized_records_file)
        records = [NormalizedLiteratureRecord.from_dict(item) for item in payload]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        return records

    def get_normalized_record(self, record_id: str) -> NormalizedLiteratureRecord | None:
        for record in self.list_normalized_records():
            if record.record_id == record_id:
                return record
        return None

    def replace_normalized_records(
        self,
        project_id: str,
        records: list[NormalizedLiteratureRecord],
    ) -> list[NormalizedLiteratureRecord]:
        existing = self.list_normalized_records()
        retained = [record for record in existing if record.project_id != project_id]
        updated = retained + list(records)
        self._write_records(self._normalized_records_file, updated)
        return records

    def list_duplicate_groups(
        self,
        *,
        project_id: str | None = None,
    ) -> list[DuplicateCandidateGroup]:
        payload = self._read_json(self._duplicate_groups_file)
        groups = [DuplicateCandidateGroup.from_dict(item) for item in payload]
        if project_id is not None:
            groups = [group for group in groups if group.project_id == project_id]
        return groups

    def get_duplicate_group(self, duplicate_group_id: str) -> DuplicateCandidateGroup | None:
        for group in self.list_duplicate_groups():
            if group.duplicate_group_id == duplicate_group_id:
                return group
        return None

    def replace_duplicate_groups(
        self,
        project_id: str,
        groups: list[DuplicateCandidateGroup],
    ) -> list[DuplicateCandidateGroup]:
        existing = self.list_duplicate_groups()
        retained = [group for group in existing if group.project_id != project_id]
        updated = retained + list(groups)
        self._write_records(self._duplicate_groups_file, updated)
        return groups

    def list_merge_results(
        self,
        *,
        project_id: str | None = None,
    ) -> list[DedupMergeResult]:
        payload = self._read_json(self._merge_results_file)
        results = [DedupMergeResult.from_dict(item) for item in payload]
        if project_id is not None:
            results = [result for result in results if result.project_id == project_id]
        return results

    def save_merge_result(self, result: DedupMergeResult) -> DedupMergeResult:
        results = self.list_merge_results()
        self._write_records(
            self._merge_results_file,
            self._upsert_by_key(results, result, "merge_result_id"),
        )
        return result

    def list_screening_records(
        self,
        *,
        project_id: str | None = None,
        stage: ScreeningStage | None = None,
        decision: ScreeningDecision | None = None,
    ) -> list[ScreeningRecord]:
        payload = self._read_json(self._screening_records_file)
        records = [ScreeningRecord.from_dict(item) for item in payload]
        if project_id is not None:
            records = [record for record in records if record.project_id == project_id]
        if stage is not None:
            records = [record for record in records if record.stage == stage]
        if decision is not None:
            records = [record for record in records if record.decision == decision]
        return records

    def get_screening_record(self, screening_record_id: str) -> ScreeningRecord | None:
        for record in self.list_screening_records():
            if record.screening_record_id == screening_record_id:
                return record
        return None

    def save_screening_record(self, record: ScreeningRecord) -> ScreeningRecord:
        records = self.list_screening_records()
        self._write_records(
            self._screening_records_file,
            self._upsert_by_key(records, record, "screening_record_id"),
        )
        return record

    def replace_screening_records(
        self,
        project_id: str,
        stage: ScreeningStage,
        records: list[ScreeningRecord],
    ) -> list[ScreeningRecord]:
        existing = self.list_screening_records()
        retained = [
            record
            for record in existing
            if not (record.project_id == project_id and record.stage == stage)
        ]
        updated = retained + list(records)
        self._write_records(self._screening_records_file, updated)
        return records

    def list_exclusion_reasons(
        self,
        *,
        stage: ScreeningStage | None = None,
    ) -> list[ExclusionReason]:
        payload = self._read_json(self._exclusion_reasons_file)
        reasons = [ExclusionReason.from_dict(item) for item in payload]
        if stage is not None:
            reasons = [reason for reason in reasons if reason.applies_to_stage == stage]
        return reasons

    def save_exclusion_reason(self, reason: ExclusionReason) -> ExclusionReason:
        reasons = self.list_exclusion_reasons()
        self._write_records(
            self._exclusion_reasons_file,
            self._upsert_by_key(reasons, reason, "reason_code"),
        )
        return reason

    def replace_exclusion_reasons(self, reasons: list[ExclusionReason]) -> list[ExclusionReason]:
        self._write_records(self._exclusion_reasons_file, reasons)
        return reasons

    def _read_json(self, file_path: Path) -> list[dict]:
        if not file_path.exists():
            return []
        return json.loads(file_path.read_text(encoding="utf-8"))

    def _write_records(
        self,
        file_path: Path,
        records: list[LiteratureProject]
        | list[ImportRecord]
        | list[ImportBatch]
        | list[ParsedLiteratureRecord]
        | list[NormalizedLiteratureRecord]
        | list[DuplicateCandidateGroup]
        | list[DedupMergeResult]
        | list[ScreeningRecord]
        | list[ExclusionReason],
    ) -> None:
        self.ensure_exists()
        payload = [record.to_dict() for record in records]
        file_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _upsert_by_key(
        self,
        records: list[LiteratureProject]
        | list[ImportRecord]
        | list[ImportBatch]
        | list[DedupMergeResult]
        | list[ScreeningRecord]
        | list[ExclusionReason],
        record: LiteratureProject
        | ImportRecord
        | ImportBatch
        | DedupMergeResult
        | ScreeningRecord
        | ExclusionReason,
        key: str,
    ) -> list[LiteratureProject] | list[ImportRecord] | list[ImportBatch] | list[DedupMergeResult] | list[ScreeningRecord] | list[ExclusionReason]:
        record_key = getattr(record, key)
        updated: list[LiteratureProject] | list[ImportRecord] | list[ImportBatch] | list[DedupMergeResult] | list[ScreeningRecord] | list[ExclusionReason] = []
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
