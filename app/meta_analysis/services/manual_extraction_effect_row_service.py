from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.extraction_schema_registry_v1_service import (
    BINARY_OUTCOME_META,
    CONTINUOUS_OUTCOME_META,
    DIAGNOSTIC_ACCURACY_META_V1,
    SURVIVAL_OUTCOME_META,
    ExtractionSchemaRegistryV1Service,
)
from app.meta_analysis.services.fulltext_management_service import (
    FULLTEXT_STATUS_FULL_TEXT_CONFIRMED,
    FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE,
    FullTextManagementService,
)
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


MANUAL_EXTRACTION_MANIFEST_SCHEMA_VERSION = "meta_manual_extraction_manifest.v1"
EXTRACTION_STUDY_UNIT_SCHEMA_VERSION = "meta_extraction_study_unit.v1"
EXTRACTION_EFFECT_ROW_SCHEMA_VERSION = "meta_extraction_effect_row.v1"
EXTRACTION_EVIDENCE_REF_SCHEMA_VERSION = "meta_extraction_evidence_ref.v1"
EXTRACTION_VALIDATION_REPORT_SCHEMA_VERSION = "meta_extraction_validation_report.v1"
EXTRACTION_AUDIT_SCHEMA_VERSION = "meta_extraction_audit_event.v1"
STRUCTURED_EXTRACTION_TABLE_SCHEMA_VERSION = "meta_structured_extraction_table.v1"

STRUCTURED_EXTRACTION_STUDY_FIELDS = (
    "study_id",
    "title",
    "first_author",
    "year",
    "country_or_region",
    "study_design",
    "population",
    "sample_size_total",
    "sample_size_case",
    "sample_size_control",
    "intervention_or_exposure",
    "comparator",
    "outcome",
    "follow_up_duration",
    "notes",
)
STRUCTURED_EXTRACTION_EFFECT_FIELDS = (
    "effect_measure_type",
    "effect_estimate",
    "ci_lower",
    "ci_upper",
    "standard_error",
    "p_value",
    "events_case",
    "total_case",
    "events_control",
    "total_control",
    "mean_case",
    "sd_case",
    "mean_control",
    "sd_control",
    "correlation_coefficient",
    "diagnostic_tp",
    "diagnostic_fp",
    "diagnostic_fn",
    "diagnostic_tn",
)
STRUCTURED_EXTRACTION_FIELDS = (*STRUCTURED_EXTRACTION_STUDY_FIELDS, *STRUCTURED_EXTRACTION_EFFECT_FIELDS)
STRUCTURED_EXTRACTION_EFFECT_MEASURES = (
    "OR",
    "RR",
    "HR",
    "MD",
    "SMD",
    "proportion",
    "correlation",
    "diagnostic_accuracy",
    "other",
)
STRUCTURED_EXTRACTION_EVIDENCE_STATES = (
    "empty",
    "draft",
    "suggested",
    "user_accepted",
    "user_edited",
    "confirmed",
    "rejected",
)
STRUCTURED_EXTRACTION_NUMERIC_FIELDS = (
    "year",
    "sample_size_total",
    "sample_size_case",
    "sample_size_control",
    "effect_estimate",
    "ci_lower",
    "ci_upper",
    "standard_error",
    "p_value",
    "events_case",
    "total_case",
    "events_control",
    "total_control",
    "mean_case",
    "sd_case",
    "mean_control",
    "sd_control",
    "correlation_coefficient",
    "diagnostic_tp",
    "diagnostic_fp",
    "diagnostic_fn",
    "diagnostic_tn",
)
STRUCTURED_EXTRACTION_NON_NEGATIVE_FIELDS = (
    "sample_size_total",
    "sample_size_case",
    "sample_size_control",
    "events_case",
    "total_case",
    "events_control",
    "total_control",
    "diagnostic_tp",
    "diagnostic_fp",
    "diagnostic_fn",
    "diagnostic_tn",
)

STRUCTURED_EXTRACTION_FIELD_LABELS_ZH = {
    "study_id": "研究 ID",
    "title": "题名",
    "first_author": "第一作者",
    "year": "年份",
    "country_or_region": "国家/地区",
    "study_design": "研究设计",
    "population": "研究对象",
    "sample_size_total": "总样本量",
    "sample_size_case": "病例/干预组样本量",
    "sample_size_control": "对照组样本量",
    "intervention_or_exposure": "干预/暴露",
    "comparator": "对照",
    "outcome": "结局",
    "follow_up_duration": "随访时间",
    "notes": "备注",
    "effect_measure_type": "效应量类型",
    "effect_estimate": "效应值",
    "ci_lower": "CI 下限",
    "ci_upper": "CI 上限",
    "standard_error": "标准误",
    "p_value": "P 值",
    "events_case": "病例/干预组事件数",
    "total_case": "病例/干预组总数",
    "events_control": "对照组事件数",
    "total_control": "对照组总数",
    "mean_case": "病例/干预组均值",
    "sd_case": "病例/干预组 SD",
    "mean_control": "对照组均值",
    "sd_control": "对照组 SD",
    "correlation_coefficient": "相关系数",
    "diagnostic_tp": "诊断 TP",
    "diagnostic_fp": "诊断 FP",
    "diagnostic_fn": "诊断 FN",
    "diagnostic_tn": "诊断 TN",
}

DATA_INPUT_MODES = (
    "raw_group_data",
    "reported_effect_size",
    "reconstructed_from_text",
    "manual_note_only",
)
ANALYSIS_ROLES = (
    "primary_effect_candidate",
    "secondary_effect_candidate",
    "subgroup_only",
    "sensitivity_only",
    "not_for_quantitative_analysis",
)
EXTRACTION_STATUSES = (
    "not_started",
    "draft",
    "completed_by_user",
    "needs_review",
    "missing_data",
)
VALIDATION_STATUSES = (
    "not_validated",
    "valid",
    "valid_with_warnings",
    "invalid_missing_required_fields",
    "invalid_conflicting_values",
)
ANALYSIS_ELIGIBILITIES = (
    "not_assessed",
    "candidate",
    "blocked",
    "excluded_by_user",
)

RAW_GROUP_FIELDS = (
    "group_1_n",
    "group_1_events",
    "group_2_n",
    "group_2_events",
    "group_1_mean",
    "group_1_sd",
    "group_2_mean",
    "group_2_sd",
    "unit",
    "tp",
    "fp",
    "fn",
    "tn",
)
REPORTED_EFFECT_FIELDS = (
    "effect_measure",
    "effect_value",
    "ci_low",
    "ci_high",
    "p_value",
    "adjusted_or_unadjusted",
    "adjusted_variables",
)
COMMON_CSV_FIELDS = (
    "record_id",
    "study_unit_id",
    "study_unit_label",
    "comparison_label",
    "group_1_label",
    "group_2_label",
    "outcome_name",
    "outcome_domain",
    "timepoint",
    "subgroup_label",
    "data_input_mode",
    "effect_measure",
    "analysis_role",
    "source_page",
    "source_table",
    "source_figure",
    "source_quote",
    "evidence_note",
)
CSV_TEMPLATE_FIELDS = (*COMMON_CSV_FIELDS, *RAW_GROUP_FIELDS, *REPORTED_EFFECT_FIELDS)


@dataclass(frozen=True)
class ManualExtractionWriteResult:
    success: bool
    project_id: str
    target_id: str
    target_type: str
    output_path: str
    manifest_path: str
    validation_report_path: str
    audit_path: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ManualExtractionCsvResult:
    success: bool
    project_id: str
    output_path: str
    row_count: int
    diagnostics: dict[str, Any] = field(default_factory=dict)
    message: str = ""


class ManualExtractionEffectRowService:
    def __init__(
        self,
        *,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
        literature_library: LiteratureLibraryService | None = None,
        schema_registry: ExtractionSchemaRegistryV1Service | None = None,
        fulltext_management: FullTextManagementService | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)
        self._literature_library = literature_library or LiteratureLibraryService(audit_log=self._audit_log)
        self._fulltext_management = fulltext_management or FullTextManagementService(
            audit_log=self._audit_log,
            research_governance=self._governance,
        )
        self._schema_registry = schema_registry or ExtractionSchemaRegistryV1Service(
            audit_log=self._audit_log,
            research_governance=self._governance,
        )

    def extraction_dir(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "extraction"

    def manifest_path(self, project_dir: Path) -> Path:
        return self.extraction_dir(project_dir) / "extraction_manifest.json"

    def study_units_path(self, project_dir: Path) -> Path:
        return self.extraction_dir(project_dir) / "extraction_study_units.json"

    def effect_rows_path(self, project_dir: Path) -> Path:
        return self.extraction_dir(project_dir) / "extraction_effect_rows.json"

    def evidence_refs_path(self, project_dir: Path) -> Path:
        return self.extraction_dir(project_dir) / "extraction_evidence_refs.json"

    def validation_report_path(self, project_dir: Path) -> Path:
        return self.extraction_dir(project_dir) / "extraction_validation_report.json"

    def extraction_audit_path(self, project_dir: Path) -> Path:
        return self.extraction_dir(project_dir) / "extraction_audit.jsonl"

    def create_study_unit(
        self,
        project_dir: Path,
        *,
        record_id: str,
        study_unit_label: str,
        actor: str = "reviewer",
        cohort_name: str = "",
        country_or_region: str = "",
        study_design: str = "",
        sample_size: int | str | None = None,
        population_description: str = "",
        is_independent: bool = True,
        project_id: str | None = None,
    ) -> ManualExtractionWriteResult:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        now = _now()
        study_unit = {
            "schema_version": EXTRACTION_STUDY_UNIT_SCHEMA_VERSION,
            "study_unit_id": f"studyunit-{uuid4().hex[:12]}",
            "project_id": project_id,
            "record_id": record_id,
            "study_unit_label": study_unit_label,
            "cohort_name": cohort_name,
            "country_or_region": country_or_region,
            "study_design": study_design,
            "sample_size": _optional_int(sample_size),
            "population_description": population_description,
            "is_independent": bool(is_independent),
            "created_at": now,
            "updated_at": now,
            "governance_refs": [],
            "audit_refs": [],
        }
        units = self.load_study_units(project_dir)
        units.append(study_unit)
        _write_json(self.study_units_path(project_dir), _collection_payload("study_units", units, EXTRACTION_STUDY_UNIT_SCHEMA_VERSION, project_id))
        audit_ref = self._record_extraction_audit(
            project_dir,
            action="study_unit draft_created",
            actor=actor,
            target_type="study_unit",
            target_id=study_unit["study_unit_id"],
            after=study_unit,
        )
        gov = self._governance.record_draft_created(
            project_dir,
            project_id=project_id,
            actor=actor,
            target_type="study_unit",
            target_id=study_unit["study_unit_id"],
            after=study_unit,
            metadata={"workflow": "manual_extraction_effect_rows"},
        )
        study_unit["governance_refs"].append(gov.event_id)
        study_unit["audit_refs"].append(audit_ref)
        _write_json(self.study_units_path(project_dir), _collection_payload("study_units", units, EXTRACTION_STUDY_UNIT_SCHEMA_VERSION, project_id))
        self._write_manifest(project_dir, project_id=project_id)
        self.validate_effect_rows(project_dir, project_id=project_id)
        return self._result(project_dir, "study_unit", study_unit["study_unit_id"], self.study_units_path(project_dir), "Study unit draft created.", study_unit)

    def create_effect_row(
        self,
        project_dir: Path,
        *,
        study_unit_id: str,
        actor: str = "reviewer",
        project_id: str | None = None,
        schema_meta_type: str = "",
        data_input_mode: str = "raw_group_data",
        comparison_label: str = "",
        group_1_label: str = "",
        group_2_label: str = "",
        outcome_name: str = "",
        outcome_domain: str = "",
        timepoint: str = "",
        subgroup_label: str = "",
        data_fields: dict[str, Any] | None = None,
        source_page: str = "",
        source_table: str = "",
        source_figure: str = "",
        source_quote: str = "",
        evidence_note: str = "",
        analysis_role: str = "primary_effect_candidate",
        extraction_status: str = "draft",
        analysis_eligibility: str = "not_assessed",
    ) -> ManualExtractionWriteResult:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        units = self.load_study_units(project_dir)
        study_unit = _find_by_id(units, "study_unit_id", study_unit_id)
        if study_unit is None:
            raise ValueError(f"study_unit_not_found:{study_unit_id}")
        data_input_mode = _validate_choice(data_input_mode, DATA_INPUT_MODES, "data_input_mode")
        analysis_role = _validate_choice(analysis_role, ANALYSIS_ROLES, "analysis_role")
        extraction_status = _validate_choice(extraction_status, EXTRACTION_STATUSES, "extraction_status")
        analysis_eligibility = _validate_choice(analysis_eligibility, ANALYSIS_ELIGIBILITIES, "analysis_eligibility")
        data_fields = dict(data_fields or {})
        now = _now()
        evidence = self._build_evidence_ref(
            project_id=project_id,
            effect_row_id="",
            source_page=source_page,
            source_table=source_table,
            source_figure=source_figure,
            source_quote=source_quote,
            evidence_note=evidence_note,
            actor=actor,
            created_at=now,
        )
        effect_row_id = f"effectrow-{uuid4().hex[:12]}"
        evidence["effect_row_id"] = effect_row_id
        validation = self._validate_row_payload(
            {
                "data_input_mode": data_input_mode,
                "schema_meta_type": schema_meta_type,
                "outcome_name": outcome_name,
                "raw_group_data": _pick(data_fields, RAW_GROUP_FIELDS),
                "reported_effect_size": _pick(data_fields, REPORTED_EFFECT_FIELDS),
                "analysis_role": analysis_role,
            }
        )
        row = {
            "schema_version": EXTRACTION_EFFECT_ROW_SCHEMA_VERSION,
            "effect_row_id": effect_row_id,
            "project_id": project_id,
            "record_id": str(study_unit.get("record_id", "")),
            "study_unit_id": study_unit_id,
            "study_unit_label": str(study_unit.get("study_unit_label", "")),
            "schema_meta_type": schema_meta_type or self._selected_schema_meta_type(project_dir),
            "comparison_label": comparison_label,
            "group_1_label": group_1_label,
            "group_2_label": group_2_label,
            "outcome_name": outcome_name,
            "outcome_domain": outcome_domain,
            "timepoint": timepoint,
            "subgroup_label": subgroup_label,
            "data_input_mode": data_input_mode,
            "raw_group_data": _pick(data_fields, RAW_GROUP_FIELDS),
            "reported_effect_size": _pick(data_fields, REPORTED_EFFECT_FIELDS),
            "reconstructed_from_text": _pick(data_fields, ("reconstruction_note", "reconstruction_method")),
            "manual_note": str(data_fields.get("manual_note", "")),
            "source_evidence_id": evidence["evidence_ref_id"],
            "analysis_role": analysis_role,
            "extraction_status": extraction_status,
            "validation_status": validation["validation_status"],
            "analysis_eligibility": analysis_eligibility,
            "analysis_ready": False,
            "created_at": now,
            "updated_at": now,
            "governance_refs": [],
            "audit_refs": [],
            "diagnostics": validation["diagnostics"],
            "warnings": validation["warnings"],
        }
        rows = self.load_effect_rows(project_dir)
        evidence_refs = self.load_evidence_refs(project_dir)
        rows.append(row)
        evidence_refs.append(evidence)
        audit_ref = self._record_extraction_audit(
            project_dir,
            action="extraction_row draft_created",
            actor=actor,
            target_type="extraction_row",
            target_id=effect_row_id,
            after=row,
        )
        gov = self._governance.record_draft_created(
            project_dir,
            project_id=project_id,
            actor=actor,
            target_type="extraction_row",
            target_id=effect_row_id,
            after=row,
            metadata={"analysis_ready": False, "statistics_run": False, "prisma_advanced": False},
        )
        row["governance_refs"].append(gov.event_id)
        row["audit_refs"].append(audit_ref)
        _write_json(self.effect_rows_path(project_dir), _collection_payload("effect_rows", rows, EXTRACTION_EFFECT_ROW_SCHEMA_VERSION, project_id))
        _write_json(self.evidence_refs_path(project_dir), _collection_payload("evidence_refs", evidence_refs, EXTRACTION_EVIDENCE_REF_SCHEMA_VERSION, project_id))
        self._write_manifest(project_dir, project_id=project_id)
        report = self.validate_effect_rows(project_dir, project_id=project_id)
        return self._result(project_dir, "extraction_row", effect_row_id, self.effect_rows_path(project_dir), "Extraction effect row draft created.", row, report)

    def save_effect_row_draft(
        self,
        project_dir: Path,
        *,
        effect_row_id: str,
        updates: dict[str, Any],
        actor: str = "reviewer",
    ) -> ManualExtractionWriteResult:
        return self._update_effect_row(
            project_dir,
            effect_row_id=effect_row_id,
            updates=updates,
            actor=actor,
            workflow_action="user_edited",
            status_override=None,
            governance_action="edit",
            summary="Extraction effect row draft edited.",
        )

    def mark_missing_data(
        self,
        project_dir: Path,
        *,
        effect_row_id: str,
        actor: str = "reviewer",
        missing_reason: str = "",
    ) -> ManualExtractionWriteResult:
        return self._update_effect_row(
            project_dir,
            effect_row_id=effect_row_id,
            updates={"missing_reason": missing_reason},
            actor=actor,
            workflow_action="marked_missing",
            status_override="missing_data",
            governance_action="edit",
            summary="Extraction effect row marked as missing data.",
        )

    def complete_effect_row(
        self,
        project_dir: Path,
        *,
        effect_row_id: str,
        actor: str = "reviewer",
    ) -> ManualExtractionWriteResult:
        return self._update_effect_row(
            project_dir,
            effect_row_id=effect_row_id,
            updates={"completed_by_user": True},
            actor=actor,
            workflow_action="completed_by_user",
            status_override="completed_by_user",
            governance_action="confirm",
            summary="Extraction effect row completed by user.",
        )

    def copy_effect_row(
        self,
        project_dir: Path,
        *,
        effect_row_id: str,
        actor: str = "reviewer",
    ) -> ManualExtractionWriteResult:
        rows = self.load_effect_rows(project_dir)
        row = _find_by_id(rows, "effect_row_id", effect_row_id)
        if row is None:
            raise ValueError(f"effect_row_not_found:{effect_row_id}")
        copied = dict(row)
        copied["effect_row_id"] = f"effectrow-{uuid4().hex[:12]}"
        copied["extraction_status"] = "draft"
        copied["validation_status"] = "not_validated"
        copied["analysis_ready"] = False
        copied["created_at"] = _now()
        copied["updated_at"] = copied["created_at"]
        copied["governance_refs"] = []
        copied["audit_refs"] = []
        rows.append(copied)
        _write_json(self.effect_rows_path(project_dir), _collection_payload("effect_rows", rows, EXTRACTION_EFFECT_ROW_SCHEMA_VERSION, project_dir.name))
        audit_ref = self._record_extraction_audit(
            project_dir,
            action="extraction_row draft_created",
            actor=actor,
            target_type="extraction_row",
            target_id=copied["effect_row_id"],
            before=row,
            after=copied,
        )
        gov = self._governance.record_draft_created(
            project_dir,
            actor=actor,
            target_type="extraction_row",
            target_id=copied["effect_row_id"],
            after=copied,
            metadata={"copied_from": effect_row_id, "analysis_ready": False},
        )
        copied["audit_refs"].append(audit_ref)
        copied["governance_refs"].append(gov.event_id)
        _write_json(self.effect_rows_path(project_dir), _collection_payload("effect_rows", rows, EXTRACTION_EFFECT_ROW_SCHEMA_VERSION, project_dir.name))
        self._write_manifest(project_dir, project_id=project_dir.name)
        report = self.validate_effect_rows(project_dir, project_id=project_dir.name)
        return self._result(project_dir, "extraction_row", copied["effect_row_id"], self.effect_rows_path(project_dir), "Extraction effect row copied as draft.", copied, report)

    def validate_effect_rows(self, project_dir: Path, *, project_id: str | None = None) -> dict[str, Any]:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        rows = self.load_effect_rows(project_dir)
        row_reports: list[dict[str, Any]] = []
        missing_required_count = 0
        warnings: list[str] = []
        for row in rows:
            validation = self._validate_row_payload(row)
            row_reports.append({"effect_row_id": row.get("effect_row_id", ""), **validation})
            missing_required_count += len(validation["missing_required_fields"])
            warnings.extend(validation["warnings"])
        warnings.extend(_multiple_primary_warnings(rows))
        report = {
            "schema_version": EXTRACTION_VALIDATION_REPORT_SCHEMA_VERSION,
            "project_id": project_id,
            "created_at": _now(),
            "effect_row_count": len(rows),
            "missing_required_fields_count": missing_required_count,
            "warnings": warnings,
            "row_reports": row_reports,
            "analysis_ready_dataset_created": False,
            "statistics_run": False,
            "prisma_advanced": False,
        }
        _write_json(self.validation_report_path(project_dir), report)
        self._write_manifest(project_dir, project_id=project_id, validation_report=report)
        return report

    def export_empty_template_csv(self, project_dir: Path, *, actor: str = "reviewer", meta_type: str = "") -> ManualExtractionCsvResult:
        project_dir = project_dir.expanduser().resolve()
        meta_type = meta_type or self._selected_schema_meta_type(project_dir)
        path = self.extraction_dir(project_dir) / "manual_extraction_template.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(CSV_TEMPLATE_FIELDS))
            writer.writeheader()
        self._record_extraction_audit(
            project_dir,
            action="extraction_csv exported",
            actor=actor,
            target_type="extraction_csv",
            target_id="manual_extraction_template",
            after={"meta_type": meta_type, "path": str(path), "row_count": 0},
        )
        self._governance.record_draft_created(
            project_dir,
            actor=actor,
            target_type="extraction_csv",
            target_id="manual_extraction_template",
            after={"meta_type": meta_type, "path": str(path), "row_count": 0},
            metadata={"workflow_action": "exported", "analysis_ready": False},
        )
        self._write_manifest(project_dir, project_id=project_dir.name)
        return ManualExtractionCsvResult(True, project_dir.name, str(path), 0, {"meta_type": meta_type}, "CSV template exported.")

    def export_current_csv(self, project_dir: Path, *, actor: str = "reviewer") -> ManualExtractionCsvResult:
        project_dir = project_dir.expanduser().resolve()
        rows = self.load_effect_rows(project_dir)
        path = self.extraction_dir(project_dir) / "manual_extraction_current.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(CSV_TEMPLATE_FIELDS))
            writer.writeheader()
            for row in rows:
                writer.writerow(_flatten_row_for_csv(row))
        self._record_extraction_audit(
            project_dir,
            action="extraction_csv exported",
            actor=actor,
            target_type="extraction_csv",
            target_id="manual_extraction_current",
            after={"path": str(path), "row_count": len(rows)},
        )
        self._governance.record_draft_created(
            project_dir,
            actor=actor,
            target_type="extraction_csv",
            target_id="manual_extraction_current",
            after={"path": str(path), "row_count": len(rows)},
            metadata={"workflow_action": "exported", "analysis_ready": False},
        )
        return ManualExtractionCsvResult(True, project_dir.name, str(path), len(rows), {}, "Current extraction rows exported.")

    def import_csv_as_draft(self, project_dir: Path, *, csv_path: Path, actor: str = "reviewer") -> ManualExtractionCsvResult:
        project_dir = project_dir.expanduser().resolve()
        csv_path = csv_path.expanduser().resolve()
        existing_rows = self.load_effect_rows(project_dir)
        existing_ids = {str(row.get("effect_row_id", "")) for row in existing_rows}
        imported_count = 0
        conflicts: list[dict[str, Any]] = []
        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for index, raw in enumerate(reader, start=1):
                incoming_id = str(raw.get("effect_row_id", "")).strip()
                if incoming_id and incoming_id in existing_ids:
                    conflicts.append({"row_number": index, "effect_row_id": incoming_id, "diagnostic": "CSV 与现有提取行冲突，已保留现有记录，未静默覆盖。"})
                    continue
                record_id = str(raw.get("record_id", "")).strip()
                study_unit_id = str(raw.get("study_unit_id", "")).strip()
                if not study_unit_id or _find_by_id(self.load_study_units(project_dir), "study_unit_id", study_unit_id) is None:
                    unit_result = self.create_study_unit(
                        project_dir,
                        record_id=record_id,
                        study_unit_label=str(raw.get("study_unit_label") or f"CSV study unit {index}"),
                        actor=actor,
                    )
                    study_unit_id = unit_result.payload["study_unit_id"]
                fields = {field: raw.get(field, "") for field in (*RAW_GROUP_FIELDS, *REPORTED_EFFECT_FIELDS)}
                self.create_effect_row(
                    project_dir,
                    study_unit_id=study_unit_id,
                    actor=actor,
                    data_input_mode=str(raw.get("data_input_mode") or "manual_note_only"),
                    comparison_label=str(raw.get("comparison_label", "")),
                    group_1_label=str(raw.get("group_1_label", "")),
                    group_2_label=str(raw.get("group_2_label", "")),
                    outcome_name=str(raw.get("outcome_name", "")),
                    outcome_domain=str(raw.get("outcome_domain", "")),
                    timepoint=str(raw.get("timepoint", "")),
                    subgroup_label=str(raw.get("subgroup_label", "")),
                    data_fields=fields,
                    source_page=str(raw.get("source_page", "")),
                    source_table=str(raw.get("source_table", "")),
                    source_figure=str(raw.get("source_figure", "")),
                    source_quote=str(raw.get("source_quote", "")),
                    evidence_note=str(raw.get("evidence_note", "")),
                    analysis_role=str(raw.get("analysis_role") or "secondary_effect_candidate"),
                )
                imported_count += 1
        diagnostics = {"conflict_count": len(conflicts), "conflicts": conflicts, "import_mode": "draft_only_no_overwrite"}
        self._record_extraction_audit(
            project_dir,
            action="extraction_csv imported_as_draft",
            actor=actor,
            target_type="extraction_csv",
            target_id=csv_path.name,
            source_path=str(csv_path),
            after={"imported_count": imported_count, "diagnostics": diagnostics},
        )
        self._governance.record_draft_created(
            project_dir,
            actor=actor,
            target_type="extraction_csv",
            target_id=csv_path.name,
            after={"imported_count": imported_count, "diagnostics": diagnostics},
            metadata={"workflow_action": "imported_as_draft", "overwrites_existing_records": False, "analysis_ready": False},
        )
        self.validate_effect_rows(project_dir, project_id=project_dir.name)
        return ManualExtractionCsvResult(True, project_dir.name, str(csv_path), imported_count, diagnostics, "CSV imported as extraction drafts.")

    def create_structured_extraction_row(
        self,
        project_dir: Path,
        *,
        fields: dict[str, Any],
        actor: str = "reviewer",
        field_states: dict[str, str] | None = None,
        evidence_state: str = "draft",
        record_id: str = "",
    ) -> ManualExtractionWriteResult:
        project_dir = project_dir.expanduser().resolve()
        normalized = _structured_fields(fields)
        field_states = _structured_field_states(normalized, field_states)
        evidence_state = _validate_choice(evidence_state, STRUCTURED_EXTRACTION_EVIDENCE_STATES, "structured_extraction_evidence_state")
        validation = self.validate_structured_extraction_fields(normalized, evidence_state=evidence_state)
        record_id = record_id or str(normalized.get("record_id") or normalized.get("study_id") or f"structured-{uuid4().hex[:8]}")
        unit_result = self.create_study_unit(
            project_dir,
            record_id=record_id,
            study_unit_label=str(normalized.get("study_id") or normalized.get("title") or "结构化提取研究"),
            actor=actor,
            country_or_region=str(normalized.get("country_or_region", "")),
            study_design=str(normalized.get("study_design", "")),
            sample_size=normalized.get("sample_size_total"),
            population_description=str(normalized.get("population", "")),
        )
        data_input_mode = _structured_data_input_mode(normalized)
        effect_result = self.create_effect_row(
            project_dir,
            study_unit_id=str(unit_result.payload["study_unit_id"]),
            actor=actor,
            schema_meta_type=_structured_schema_meta_type(normalized),
            data_input_mode=data_input_mode,
            comparison_label=_comparison_label(normalized),
            group_1_label="case/intervention",
            group_2_label="control/comparator",
            outcome_name=str(normalized.get("outcome", "")),
            data_fields=_structured_data_fields(normalized),
            evidence_note=str(normalized.get("notes", "")),
            analysis_role="primary_effect_candidate",
            extraction_status="draft",
            analysis_eligibility="not_assessed",
        )
        updates = {
            "m5_schema_version": STRUCTURED_EXTRACTION_TABLE_SCHEMA_VERSION,
            "m5_structured_fields": normalized,
            "m5_field_states": field_states,
            "evidence_state": evidence_state,
            "diagnostics": validation["diagnostics"],
            "warnings": validation["warnings"],
        }
        result = self._update_effect_row(
            project_dir,
            effect_row_id=str(effect_result.payload["effect_row_id"]),
            updates=updates,
            actor=actor,
            workflow_action=evidence_state if evidence_state != "draft" else "draft_saved",
            status_override=None,
            governance_action="edit",
            summary="Structured extraction row saved.",
        )
        payload = dict(result.payload)
        payload["m5_validation"] = validation
        return self._result(project_dir, "structured_extraction_row", str(payload["effect_row_id"]), self.effect_rows_path(project_dir), "Structured extraction row saved.", payload, validation)

    def update_structured_extraction_row(
        self,
        project_dir: Path,
        *,
        effect_row_id: str,
        fields: dict[str, Any],
        actor: str = "reviewer",
        field_states: dict[str, str] | None = None,
        evidence_state: str = "user_edited",
    ) -> ManualExtractionWriteResult:
        current = _find_by_id(self.load_effect_rows(project_dir), "effect_row_id", effect_row_id)
        if current is None:
            raise ValueError(f"effect_row_not_found:{effect_row_id}")
        previous_fields = dict(current.get("m5_structured_fields", {}) if isinstance(current.get("m5_structured_fields"), dict) else {})
        previous_fields.update(_structured_fields(fields))
        previous_states = dict(current.get("m5_field_states", {}) if isinstance(current.get("m5_field_states"), dict) else {})
        merged_states = _structured_field_states(previous_fields, {**previous_states, **dict(field_states or {})}, default_state=evidence_state)
        evidence_state = _validate_choice(evidence_state, STRUCTURED_EXTRACTION_EVIDENCE_STATES, "structured_extraction_evidence_state")
        validation = self.validate_structured_extraction_fields(previous_fields, evidence_state=evidence_state)
        result = self._update_effect_row(
            project_dir,
            effect_row_id=effect_row_id,
            updates={
                "m5_schema_version": STRUCTURED_EXTRACTION_TABLE_SCHEMA_VERSION,
                "m5_structured_fields": previous_fields,
                "m5_field_states": merged_states,
                "evidence_state": evidence_state,
                "outcome_name": str(previous_fields.get("outcome", current.get("outcome_name", ""))),
                **_structured_data_updates(previous_fields),
            },
            actor=actor,
            workflow_action=evidence_state,
            status_override=None,
            governance_action="edit",
            summary="Structured extraction row edited.",
        )
        payload = dict(result.payload)
        payload["m5_validation"] = validation
        return self._result(project_dir, "structured_extraction_row", effect_row_id, self.effect_rows_path(project_dir), "Structured extraction row edited.", payload, validation)

    def confirm_structured_extraction_row(
        self,
        project_dir: Path,
        *,
        effect_row_id: str,
        actor: str = "reviewer",
    ) -> ManualExtractionWriteResult:
        row = _find_by_id(self.load_effect_rows(project_dir), "effect_row_id", effect_row_id)
        if row is None:
            raise ValueError(f"effect_row_not_found:{effect_row_id}")
        fields = dict(row.get("m5_structured_fields", {}) if isinstance(row.get("m5_structured_fields"), dict) else {})
        validation = self.validate_structured_extraction_fields(fields, evidence_state="confirmed")
        if validation["errors"]:
            return self._failure_result(project_dir, "structured_extraction_row", effect_row_id, "Structured extraction row cannot be confirmed.", validation)
        field_states = _structured_field_states(fields, dict(row.get("m5_field_states", {}) if isinstance(row.get("m5_field_states"), dict) else {}), default_state="confirmed")
        field_states = {**field_states, **{field: ("empty" if not _has_value(fields.get(field)) else "confirmed") for field in STRUCTURED_EXTRACTION_FIELDS}}
        result = self._update_effect_row(
            project_dir,
            effect_row_id=effect_row_id,
            updates={"evidence_state": "confirmed", "m5_field_states": field_states, "m5_validation": validation, "completed_by_user": True},
            actor=actor,
            workflow_action="confirmed",
            status_override="completed_by_user",
            governance_action="confirm",
            summary="Structured extraction row confirmed by user.",
        )
        payload = dict(result.payload)
        payload["m5_validation"] = validation
        return self._result(project_dir, "structured_extraction_row", effect_row_id, self.effect_rows_path(project_dir), "Structured extraction row confirmed by user.", payload, validation)

    def load_structured_extraction_table(self, project_dir: Path) -> list[dict[str, Any]]:
        rows = []
        for row in self.load_effect_rows(project_dir):
            if row.get("m5_schema_version") == STRUCTURED_EXTRACTION_TABLE_SCHEMA_VERSION:
                rows.append(dict(row))
        return rows

    def validate_structured_extraction_fields(self, fields: dict[str, Any], *, evidence_state: str = "draft") -> dict[str, Any]:
        normalized = _structured_fields(fields)
        diagnostics: list[str] = []
        errors: list[str] = []
        warnings: list[str] = []
        for field in STRUCTURED_EXTRACTION_NUMERIC_FIELDS:
            if _has_value(normalized.get(field)) and _optional_float(normalized.get(field)) is None:
                errors.append(f"数值无效：{field}")
        for field in STRUCTURED_EXTRACTION_NON_NEGATIVE_FIELDS:
            value = _optional_float(normalized.get(field))
            if value is not None and value < 0:
                errors.append(f"数值不能为负：{field}")
        low = _optional_float(normalized.get("ci_lower"))
        high = _optional_float(normalized.get("ci_upper"))
        if low is not None and high is not None and low > high:
            errors.append("数值无效：ci_lower 不能大于 ci_upper")
        effect_type = str(normalized.get("effect_measure_type", "")).strip()
        if effect_type and effect_type not in STRUCTURED_EXTRACTION_EFFECT_MEASURES:
            errors.append("效应量类型不支持：effect_measure_type")
        if evidence_state == "confirmed":
            if not _has_study_identity(normalized):
                errors.append("确认提取行需要 study identity。")
            if not _has_meaningful_effect(normalized):
                errors.append("确认提取行需要至少一个结局或效应量字段。")
        diagnostics.extend(errors)
        return {
            "schema_version": STRUCTURED_EXTRACTION_TABLE_SCHEMA_VERSION,
            "validation_status": "invalid" if errors else "valid_with_warnings" if warnings else "valid",
            "errors": errors,
            "diagnostics": diagnostics,
            "warnings": warnings,
            "evidence_state": evidence_state,
        }

    def load_study_units(self, project_dir: Path) -> list[dict[str, Any]]:
        return _items_from_payload(_load_json(self.study_units_path(project_dir)), "study_units")

    def load_effect_rows(self, project_dir: Path) -> list[dict[str, Any]]:
        return _items_from_payload(_load_json(self.effect_rows_path(project_dir)), "effect_rows")

    def load_evidence_refs(self, project_dir: Path) -> list[dict[str, Any]]:
        return _items_from_payload(_load_json(self.evidence_refs_path(project_dir)), "evidence_refs")

    def read_manifest(self, project_dir: Path) -> dict[str, Any]:
        project_dir = project_dir.expanduser().resolve()
        payload = _load_json(self.manifest_path(project_dir))
        if payload:
            return payload
        return {
            "schema_version": MANUAL_EXTRACTION_MANIFEST_SCHEMA_VERSION,
            "project_id": project_dir.name,
            "updated_at": "",
            "paths": {
                "study_units": str(self.study_units_path(project_dir).relative_to(project_dir)),
                "effect_rows": str(self.effect_rows_path(project_dir).relative_to(project_dir)),
                "evidence_refs": str(self.evidence_refs_path(project_dir).relative_to(project_dir)),
                "validation_report": str(self.validation_report_path(project_dir).relative_to(project_dir)),
                "audit": str(self.extraction_audit_path(project_dir).relative_to(project_dir)),
            },
            "study_unit_count": 0,
            "effect_row_count": 0,
            "missing_required_fields_count": 0,
            "analysis_candidate_row_count": 0,
            "completed_by_user_count": 0,
            "analysis_ready_dataset_created": False,
            "statistics_run": False,
            "prisma_advanced": False,
            "safety_note": "Manual extraction rows are candidate effect rows only; completed_by_user does not create an analysis-ready dataset.",
        }

    def literature_records_for_extraction(self, project_dir: Path) -> list[dict[str, Any]]:
        project_dir = project_dir.expanduser().resolve()
        confirmed_fulltext = [
            {
                "record_id": record.record_id,
                "title": record.title,
                "authors": record.authors,
                "first_author": _first_author_text(record.authors),
                "year": record.year,
                "journal": record.journal,
                "fulltext_status": record.fulltext_status,
                "extraction_source": "full_text_confirmed",
            }
            for record in self._fulltext_management.list_records(project_dir)
            if record.fulltext_status == FULLTEXT_STATUS_FULL_TEXT_CONFIRMED
        ]
        if confirmed_fulltext:
            return confirmed_fulltext
        final_included = _load_json(project_dir / "fulltext" / "final_included_studies.json")
        rows = final_included.get("included_studies", []) if isinstance(final_included, dict) else []
        if isinstance(rows, list) and rows:
            return [{**dict(item), "extraction_source": "final_included_studies"} for item in rows if isinstance(item, dict)]
        unavailable = [
            {
                "record_id": record.record_id,
                "title": record.title,
                "authors": record.authors,
                "first_author": _first_author_text(record.authors),
                "year": record.year,
                "journal": record.journal,
                "fulltext_status": record.fulltext_status,
                "extraction_source": "manual_full_text_unavailable",
            }
            for record in self._fulltext_management.list_records(project_dir)
            if record.fulltext_status == FULLTEXT_STATUS_FULL_TEXT_UNAVAILABLE
        ]
        if unavailable:
            return unavailable
        return [{**record, "extraction_source": "manual_library_fallback"} for record in self._literature_library.list_records(project_dir)]

    def _update_effect_row(
        self,
        project_dir: Path,
        *,
        effect_row_id: str,
        updates: dict[str, Any],
        actor: str,
        workflow_action: str,
        status_override: str | None,
        governance_action: str,
        summary: str,
    ) -> ManualExtractionWriteResult:
        project_dir = project_dir.expanduser().resolve()
        rows = self.load_effect_rows(project_dir)
        index = _find_index(rows, "effect_row_id", effect_row_id)
        if index < 0:
            raise ValueError(f"effect_row_not_found:{effect_row_id}")
        before = dict(rows[index])
        after = _merge_effect_row_updates(before, updates)
        if status_override is not None:
            after["extraction_status"] = status_override
        after["updated_at"] = _now()
        validation = self._validate_row_payload(after)
        after["validation_status"] = validation["validation_status"]
        after["diagnostics"] = validation["diagnostics"]
        after["warnings"] = validation["warnings"]
        after["analysis_ready"] = False
        rows[index] = after
        _write_json(self.effect_rows_path(project_dir), _collection_payload("effect_rows", rows, EXTRACTION_EFFECT_ROW_SCHEMA_VERSION, project_dir.name))
        audit_ref = self._record_extraction_audit(
            project_dir,
            action=f"extraction_row {workflow_action}",
            actor=actor,
            target_type="extraction_row",
            target_id=effect_row_id,
            before=before,
            after=after,
        )
        gov = self._governance.record_user_confirmation(
            project_dir,
            action=governance_action,
            actor=actor,
            target_type="extraction_row",
            target_id=effect_row_id,
            before=before,
            after=after,
            metadata={
                "workflow_action": workflow_action,
                "analysis_ready": False,
                "analysis_ready_dataset_created": False,
                "statistics_run": False,
                "prisma_advanced": False,
            },
        )
        after.setdefault("audit_refs", [])
        after.setdefault("governance_refs", [])
        after["audit_refs"].append(audit_ref)
        after["governance_refs"].append(gov.event_id)
        rows[index] = after
        _write_json(self.effect_rows_path(project_dir), _collection_payload("effect_rows", rows, EXTRACTION_EFFECT_ROW_SCHEMA_VERSION, project_dir.name))
        report = self.validate_effect_rows(project_dir, project_id=project_dir.name)
        self._write_manifest(project_dir, project_id=project_dir.name, validation_report=report)
        return self._result(project_dir, "extraction_row", effect_row_id, self.effect_rows_path(project_dir), summary, after, report)

    def _validate_row_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        mode = str(row.get("data_input_mode", ""))
        schema_meta_type = str(row.get("schema_meta_type", ""))
        raw = dict(row.get("raw_group_data", {}) if isinstance(row.get("raw_group_data"), dict) else {})
        reported = dict(row.get("reported_effect_size", {}) if isinstance(row.get("reported_effect_size"), dict) else {})
        required = self._required_fields(mode, schema_meta_type, reported)
        missing = [field for field in required if not _has_value(raw.get(field)) and not _has_value(reported.get(field)) and not _has_value(row.get(field))]
        diagnostics = [f"缺少必填字段：{field}" for field in missing]
        warnings: list[str] = []
        conflicting: list[str] = []
        if mode == "raw_group_data" and any(_has_value(reported.get(field)) for field in ("effect_value", "ci_low", "ci_high", "p_value")):
            conflicting.append("raw_group_data 模式不应混入 reported effect size 字段。")
        if mode == "reported_effect_size" and any(_has_value(raw.get(field)) for field in RAW_GROUP_FIELDS if field != "unit"):
            conflicting.append("reported_effect_size 模式不应混入 raw group data 字段。")
        diagnostics.extend(conflicting)
        diagnostics.extend(_numeric_diagnostics(mode, raw, reported))
        if not _has_value(row.get("outcome_name")) and mode != "manual_note_only":
            diagnostics.append("缺少必填字段：outcome_name")
            missing.append("outcome_name")
        if conflicting:
            status = "invalid_conflicting_values"
        elif missing or any(item.startswith("数值无效") or item.startswith("事件数不能") for item in diagnostics):
            status = "invalid_missing_required_fields"
        elif warnings:
            status = "valid_with_warnings"
        elif mode == "manual_note_only":
            status = "not_validated"
        else:
            status = "valid"
        return {
            "validation_status": status,
            "missing_required_fields": missing,
            "diagnostics": diagnostics,
            "warnings": warnings,
        }

    def _required_fields(self, mode: str, schema_meta_type: str, reported: dict[str, Any]) -> tuple[str, ...]:
        effect_measure = str(reported.get("effect_measure", "")).upper()
        if schema_meta_type == DIAGNOSTIC_ACCURACY_META_V1 or {"tp", "fp", "fn", "tn"} & set(reported):
            return ("tp", "fp", "fn", "tn") if mode == "raw_group_data" else ("effect_measure", "effect_value", "ci_low", "ci_high")
        if schema_meta_type == CONTINUOUS_OUTCOME_META:
            return ("group_1_n", "group_1_mean", "group_1_sd", "group_2_n", "group_2_mean", "group_2_sd") if mode == "raw_group_data" else ("effect_measure", "effect_value", "ci_low", "ci_high")
        if schema_meta_type == SURVIVAL_OUTCOME_META or effect_measure == "HR":
            return ("effect_measure", "effect_value", "ci_low", "ci_high")
        if mode == "reported_effect_size":
            return ("effect_measure", "effect_value", "ci_low", "ci_high")
        if mode == "manual_note_only":
            return ()
        return ("group_1_n", "group_1_events", "group_2_n", "group_2_events")

    def _build_evidence_ref(
        self,
        *,
        project_id: str,
        effect_row_id: str,
        source_page: str,
        source_table: str,
        source_figure: str,
        source_quote: str,
        evidence_note: str,
        actor: str,
        created_at: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": EXTRACTION_EVIDENCE_REF_SCHEMA_VERSION,
            "evidence_ref_id": f"evidence-{uuid4().hex[:12]}",
            "project_id": project_id,
            "effect_row_id": effect_row_id,
            "source_page": source_page,
            "source_table": source_table,
            "source_figure": source_figure,
            "source_quote": source_quote,
            "evidence_note": evidence_note,
            "created_by": actor,
            "created_at": created_at,
        }

    def _selected_schema_meta_type(self, project_dir: Path) -> str:
        selection = _load_json(self._schema_registry.selection_path(project_dir))
        selected = str(selection.get("selected_meta_type", "")).strip()
        if selected:
            return selected
        return BINARY_OUTCOME_META

    def _write_manifest(
        self,
        project_dir: Path,
        *,
        project_id: str,
        validation_report: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        project_dir = project_dir.expanduser().resolve()
        units = self.load_study_units(project_dir)
        rows = self.load_effect_rows(project_dir)
        validation_report = validation_report or _load_json(self.validation_report_path(project_dir))
        missing_required_count = int(validation_report.get("missing_required_fields_count", 0)) if isinstance(validation_report, dict) else 0
        candidate_rows = [
            row
            for row in rows
            if row.get("analysis_role") in {"primary_effect_candidate", "secondary_effect_candidate"}
            and row.get("validation_status") in {"valid", "valid_with_warnings"}
            and row.get("analysis_eligibility") != "excluded_by_user"
        ]
        manifest = {
            "schema_version": MANUAL_EXTRACTION_MANIFEST_SCHEMA_VERSION,
            "project_id": project_id,
            "updated_at": _now(),
            "paths": {
                "study_units": str(self.study_units_path(project_dir).relative_to(project_dir)),
                "effect_rows": str(self.effect_rows_path(project_dir).relative_to(project_dir)),
                "evidence_refs": str(self.evidence_refs_path(project_dir).relative_to(project_dir)),
                "validation_report": str(self.validation_report_path(project_dir).relative_to(project_dir)),
                "audit": str(self.extraction_audit_path(project_dir).relative_to(project_dir)),
            },
            "study_unit_count": len(units),
            "effect_row_count": len(rows),
            "missing_required_fields_count": missing_required_count,
            "analysis_candidate_row_count": len(candidate_rows),
            "completed_by_user_count": sum(1 for row in rows if row.get("extraction_status") == "completed_by_user"),
            "analysis_ready_dataset_created": False,
            "statistics_run": False,
            "prisma_advanced": False,
            "safety_note": "Manual extraction rows are candidate effect rows only; completed_by_user does not create an analysis-ready dataset.",
        }
        _write_json(self.manifest_path(project_dir), manifest)
        return manifest

    def _record_extraction_audit(
        self,
        project_dir: Path,
        *,
        action: str,
        actor: str,
        target_type: str,
        target_id: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        source_path: str = "",
    ) -> str:
        project_dir = project_dir.expanduser().resolve()
        path = self.extraction_audit_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        event_id = f"extractaudit-{uuid4().hex[:12]}"
        payload = {
            "schema_version": EXTRACTION_AUDIT_SCHEMA_VERSION,
            "event_id": event_id,
            "project_id": project_dir.name,
            "actor": actor,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "before": before or {},
            "after": after or {},
            "created_at": _now(),
            "analysis_ready_dataset_created": False,
            "statistics_run": False,
            "prisma_advanced": False,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        self._audit_log.record_event(
            project_dir,
            event_type="extraction_updated",
            project_id=project_dir.name,
            actor=actor,
            target_type=target_type,
            target_id=target_id,
            source_path=source_path,
            output_path=str(path.relative_to(project_dir)),
            summary=action,
            details={
                "extraction_audit_event_id": event_id,
                "analysis_ready_dataset_created": False,
                "statistics_run": False,
                "prisma_advanced": False,
            },
        )
        return event_id

    def _result(
        self,
        project_dir: Path,
        target_type: str,
        target_id: str,
        output_path: Path,
        message: str,
        payload: dict[str, Any],
        diagnostics: dict[str, Any] | None = None,
    ) -> ManualExtractionWriteResult:
        return ManualExtractionWriteResult(
            success=True,
            project_id=project_dir.expanduser().resolve().name,
            target_id=target_id,
            target_type=target_type,
            output_path=str(output_path),
            manifest_path=str(self.manifest_path(project_dir)),
            validation_report_path=str(self.validation_report_path(project_dir)),
            audit_path=str(self.extraction_audit_path(project_dir)),
            message=message,
            payload=payload,
            diagnostics=diagnostics or {},
        )

    def _failure_result(
        self,
        project_dir: Path,
        target_type: str,
        target_id: str,
        message: str,
        diagnostics: dict[str, Any],
    ) -> ManualExtractionWriteResult:
        return ManualExtractionWriteResult(
            success=False,
            project_id=project_dir.expanduser().resolve().name,
            target_id=target_id,
            target_type=target_type,
            output_path=str(self.effect_rows_path(project_dir)),
            manifest_path=str(self.manifest_path(project_dir)),
            validation_report_path=str(self.validation_report_path(project_dir)),
            audit_path=str(self.extraction_audit_path(project_dir)),
            message=message,
            payload={},
            diagnostics=diagnostics,
        )


def _merge_effect_row_updates(row: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(row)
    for key, value in updates.items():
        if key in RAW_GROUP_FIELDS:
            raw = dict(merged.get("raw_group_data", {}))
            raw[key] = value
            merged["raw_group_data"] = raw
        elif key in REPORTED_EFFECT_FIELDS:
            reported = dict(merged.get("reported_effect_size", {}))
            reported[key] = value
            merged["reported_effect_size"] = reported
        else:
            merged[key] = value
    return merged


def _structured_fields(fields: dict[str, Any]) -> dict[str, Any]:
    return {field: fields.get(field, "") for field in STRUCTURED_EXTRACTION_FIELDS if _has_value(fields.get(field))}


def _structured_field_states(
    fields: dict[str, Any],
    field_states: dict[str, str] | None,
    *,
    default_state: str = "draft",
) -> dict[str, str]:
    default_state = _validate_choice(default_state, STRUCTURED_EXTRACTION_EVIDENCE_STATES, "structured_extraction_evidence_state")
    states = dict(field_states or {})
    normalized: dict[str, str] = {}
    for field in STRUCTURED_EXTRACTION_FIELDS:
        state = str(states.get(field) or ("empty" if not _has_value(fields.get(field)) else default_state)).strip()
        normalized[field] = state if state in STRUCTURED_EXTRACTION_EVIDENCE_STATES else default_state
    return normalized


def _structured_data_input_mode(fields: dict[str, Any]) -> str:
    if any(_has_value(fields.get(field)) for field in ("effect_estimate", "ci_lower", "ci_upper", "standard_error", "p_value", "correlation_coefficient")):
        return "reported_effect_size"
    if any(_has_value(fields.get(field)) for field in ("events_case", "total_case", "events_control", "total_control", "mean_case", "sd_case", "mean_control", "sd_control", "diagnostic_tp", "diagnostic_fp", "diagnostic_fn", "diagnostic_tn")):
        return "raw_group_data"
    return "manual_note_only"


def _structured_schema_meta_type(fields: dict[str, Any]) -> str:
    effect_type = str(fields.get("effect_measure_type", "")).strip()
    if effect_type == "diagnostic_accuracy" or any(_has_value(fields.get(field)) for field in ("diagnostic_tp", "diagnostic_fp", "diagnostic_fn", "diagnostic_tn")):
        return DIAGNOSTIC_ACCURACY_META_V1
    if effect_type in {"MD", "SMD"} or any(_has_value(fields.get(field)) for field in ("mean_case", "sd_case", "mean_control", "sd_control")):
        return CONTINUOUS_OUTCOME_META
    if effect_type == "HR":
        return SURVIVAL_OUTCOME_META
    return BINARY_OUTCOME_META


def _structured_data_fields(fields: dict[str, Any]) -> dict[str, Any]:
    data = {
        "effect_measure": fields.get("effect_measure_type", ""),
        "effect_value": fields.get("effect_estimate", ""),
        "ci_low": fields.get("ci_lower", ""),
        "ci_high": fields.get("ci_upper", ""),
        "p_value": fields.get("p_value", ""),
        "group_1_n": fields.get("total_case", fields.get("sample_size_case", "")),
        "group_1_events": fields.get("events_case", ""),
        "group_2_n": fields.get("total_control", fields.get("sample_size_control", "")),
        "group_2_events": fields.get("events_control", ""),
        "group_1_mean": fields.get("mean_case", ""),
        "group_1_sd": fields.get("sd_case", ""),
        "group_2_mean": fields.get("mean_control", ""),
        "group_2_sd": fields.get("sd_control", ""),
        "tp": fields.get("diagnostic_tp", ""),
        "fp": fields.get("diagnostic_fp", ""),
        "fn": fields.get("diagnostic_fn", ""),
        "tn": fields.get("diagnostic_tn", ""),
        "manual_note": fields.get("notes", ""),
    }
    return {key: value for key, value in data.items() if _has_value(value)}


def _structured_data_updates(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_meta_type": _structured_schema_meta_type(fields),
        "data_input_mode": _structured_data_input_mode(fields),
        "comparison_label": _comparison_label(fields),
        "raw_group_data": _pick(_structured_data_fields(fields), RAW_GROUP_FIELDS),
        "reported_effect_size": _pick(_structured_data_fields(fields), REPORTED_EFFECT_FIELDS),
        "manual_note": str(fields.get("notes", "")),
    }


def _comparison_label(fields: dict[str, Any]) -> str:
    left = str(fields.get("intervention_or_exposure", "")).strip()
    right = str(fields.get("comparator", "")).strip()
    if left and right:
        return f"{left} vs {right}"
    return left or right


def _has_study_identity(fields: dict[str, Any]) -> bool:
    if _has_value(fields.get("study_id")):
        return True
    return _has_value(fields.get("title")) or (_has_value(fields.get("first_author")) and _has_value(fields.get("year")))


def _has_meaningful_effect(fields: dict[str, Any]) -> bool:
    if _has_value(fields.get("outcome")) and any(_has_value(fields.get(field)) for field in STRUCTURED_EXTRACTION_EFFECT_FIELDS):
        return True
    return any(_has_value(fields.get(field)) for field in ("events_case", "events_control", "mean_case", "mean_control", "diagnostic_tp", "diagnostic_tn", "effect_estimate", "correlation_coefficient"))


def _first_author_text(authors: object) -> str:
    if isinstance(authors, (list, tuple)):
        return str(authors[0]) if authors else ""
    text = str(authors or "").strip()
    if "," in text:
        return text.split(",", 1)[0].strip()
    if "；" in text:
        return text.split("；", 1)[0].strip()
    return text


def _numeric_diagnostics(mode: str, raw: dict[str, Any], reported: dict[str, Any]) -> list[str]:
    diagnostics: list[str] = []
    if mode == "raw_group_data":
        for field in ("group_1_n", "group_1_events", "group_2_n", "group_2_events", "tp", "fp", "fn", "tn"):
            if _has_value(raw.get(field)) and _optional_float(raw.get(field)) is None:
                diagnostics.append(f"数值无效：{field}")
        for events_field, total_field in (("group_1_events", "group_1_n"), ("group_2_events", "group_2_n")):
            events = _optional_float(raw.get(events_field))
            total = _optional_float(raw.get(total_field))
            if events is not None and total is not None and events > total:
                diagnostics.append(f"事件数不能大于总人数：{events_field}")
    if mode == "reported_effect_size":
        for field in ("effect_value", "ci_low", "ci_high"):
            if _has_value(reported.get(field)) and _optional_float(reported.get(field)) is None:
                diagnostics.append(f"数值无效：{field}")
        low = _optional_float(reported.get("ci_low"))
        high = _optional_float(reported.get("ci_high"))
        if low is not None and high is not None and low > high:
            diagnostics.append("数值无效：ci_low 不能大于 ci_high")
    return diagnostics


def _multiple_primary_warnings(rows: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        if row.get("analysis_role") == "primary_effect_candidate":
            key = str(row.get("study_unit_id", ""))
            counts[key] = counts.get(key, 0) + 1
    return [f"同一 study_unit 下存在多个 primary_effect_candidate：{study_unit_id}" for study_unit_id, count in counts.items() if study_unit_id and count > 1]


def _collection_payload(key: str, items: list[dict[str, Any]], item_schema_version: str, project_id: str) -> dict[str, Any]:
    return {
        "schema_version": f"{item_schema_version}_collection",
        "item_schema_version": item_schema_version,
        "project_id": project_id,
        "updated_at": _now(),
        "count": len(items),
        key: items,
    }


def _items_from_payload(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    items = payload.get(key, []) if isinstance(payload, dict) else []
    return [dict(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _load_json(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _find_by_id(items: list[dict[str, Any]], id_key: str, value: str) -> dict[str, Any] | None:
    for item in items:
        if str(item.get(id_key, "")) == value:
            return item
    return None


def _find_index(items: list[dict[str, Any]], id_key: str, value: str) -> int:
    for index, item in enumerate(items):
        if str(item.get(id_key, "")) == value:
            return index
    return -1


def _pick(payload: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: payload.get(key, "") for key in keys if _has_value(payload.get(key))}


def _flatten_row_for_csv(row: dict[str, Any]) -> dict[str, Any]:
    raw = dict(row.get("raw_group_data", {}) if isinstance(row.get("raw_group_data"), dict) else {})
    reported = dict(row.get("reported_effect_size", {}) if isinstance(row.get("reported_effect_size"), dict) else {})
    flat = {key: "" for key in CSV_TEMPLATE_FIELDS}
    for key in COMMON_CSV_FIELDS:
        flat[key] = row.get(key, "")
    flat.update(raw)
    flat.update(reported)
    return flat


def _validate_choice(value: str, choices: tuple[str, ...], field_name: str) -> str:
    normalized = value.strip()
    if normalized not in choices:
        raise ValueError(f"unsupported_{field_name}:{value}")
    return normalized


def _optional_int(value: int | str | None) -> int | None:
    if value in ("", None):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _has_value(value: Any) -> bool:
    return value not in ("", None, [], {})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
