from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from app.bioinformatics.acquisition_file_records import build_file_record
from app.bioinformatics.data_sources.tcga_preview import DEFAULT_PAGE_SIZE, GDCFetcher, _fetch_gdc_json
from app.bioinformatics.project_workspace_binding import AcquisitionSummary, LATEST_RECORD, register_acquisition
from app.bioinformatics.tcga.barcode import parse_tcga_barcode


TCGA_CLINICAL_BUILD_MANIFEST_SCHEMA_VERSION = "biomedpilot.tcga_clinical_build_manifest.v1"
TCGA_CLINICAL_ARTIFACT_MANIFEST_SCHEMA_VERSION = "biomedpilot.tcga_clinical_artifact_manifest.v1"
TCGA_CLINICAL_RECEIPT_SCHEMA_VERSION = "biomedpilot.tcga_clinical_receipt.v1"

CLINICAL_CASE_FIELDS = ",".join(
    (
        "case_id",
        "submitter_id",
        "project.project_id",
        "primary_site",
        "disease_type",
        "consent_type",
        "days_to_index",
        "index_date",
        "demographic.gender",
        "demographic.race",
        "demographic.ethnicity",
        "demographic.vital_status",
        "demographic.days_to_birth",
        "demographic.age_at_index",
        "demographic.days_to_death",
        "demographic.year_of_birth",
        "demographic.year_of_death",
        "diagnoses.diagnosis_id",
        "diagnoses.primary_diagnosis",
        "diagnoses.tumor_stage",
        "diagnoses.tumor_grade",
        "diagnoses.ajcc_pathologic_stage",
        "diagnoses.ajcc_pathologic_t",
        "diagnoses.ajcc_pathologic_n",
        "diagnoses.ajcc_pathologic_m",
        "diagnoses.ajcc_clinical_stage",
        "diagnoses.ajcc_clinical_t",
        "diagnoses.ajcc_clinical_n",
        "diagnoses.ajcc_clinical_m",
        "diagnoses.days_to_diagnosis",
        "diagnoses.age_at_diagnosis",
        "diagnoses.classification_of_tumor",
        "diagnoses.last_known_disease_status",
        "diagnoses.prior_malignancy",
        "diagnoses.prior_treatment",
        "diagnoses.vital_status",
        "diagnoses.days_to_death",
        "diagnoses.days_to_last_follow_up",
        "follow_ups.follow_up_id",
        "follow_ups.days_to_follow_up",
        "follow_ups.days_to_last_follow_up",
        "follow_ups.days_to_death",
        "follow_ups.vital_status",
        "follow_ups.progression_or_recurrence",
        "follow_ups.treatment_or_therapy",
        "follow_ups.days_to_recurrence",
        "follow_ups.days_to_progression",
    )
)


@dataclass(frozen=True)
class TCGAClinicalBuildResult:
    success: bool
    status: str
    message: str
    project_id: str
    clinical_build_id: str
    mode: str
    case_count: int
    matched_case_count: int
    matched_sample_count: int
    survival_case_count: int
    death_event_count: int
    raw_cases_path: Path
    case_table_path: Path
    diagnosis_table_path: Path
    followup_table_path: Path
    survival_table_path: Path
    mapping_table_path: Path
    clinical_manifest_path: Path
    clinical_receipt_path: Path
    warnings: tuple[str, ...]
    acquisition_summary: AcquisitionSummary | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        for key in (
            "raw_cases_path",
            "case_table_path",
            "diagnosis_table_path",
            "followup_table_path",
            "survival_table_path",
            "mapping_table_path",
            "clinical_manifest_path",
            "clinical_receipt_path",
        ):
            payload[key] = str(payload[key])
        if self.acquisition_summary is not None:
            payload["acquisition_summary"] = {
                "acquisition_id": self.acquisition_summary.acquisition_id,
                "source_files": list(self.acquisition_summary.source_files),
                "record_path": str(self.acquisition_summary.record_path),
            }
        return payload


class TCGAClinicalMetadataBuilder:
    def __init__(self, fetcher: GDCFetcher | None = None, *, page_size: int = DEFAULT_PAGE_SIZE) -> None:
        self._fetcher = fetcher or _fetch_gdc_json
        self._page_size = max(1, int(page_size))

    def build_for_latest_expression_build(
        self,
        project_root: str | Path,
        *,
        timeout: int = 10,
        project_id: str | None = None,
    ) -> TCGAClinicalBuildResult:
        root = Path(project_root).expanduser().resolve()
        manifest_path = latest_tcga_expression_build_manifest_path(root, project_id=project_id)
        if manifest_path is None:
            raise FileNotFoundError("未找到 B6.4 TCGA expression build manifest；只能按项目执行 clinical 概况预览。")
        return self.build_for_expression_build(root, manifest_path=manifest_path, timeout=timeout)

    def build_for_expression_build(
        self,
        project_root: str | Path,
        *,
        manifest_path: str | Path,
        timeout: int = 10,
    ) -> TCGAClinicalBuildResult:
        root = Path(project_root).expanduser().resolve()
        manifest_path = Path(manifest_path).expanduser().resolve()
        manifest = _read_json(manifest_path)
        project_id = str(manifest.get("project_id") or "").strip().upper()
        sample_mapping_path = Path(str(manifest.get("sample_mapping_path") or ""))
        if not project_id:
            raise ValueError("TCGA B6.4 build manifest 缺少 project_id。")
        sample_rows = _read_sample_mapping(sample_mapping_path)
        case_ids = sorted({str(row.get("case_id") or "").strip() for row in sample_rows if str(row.get("case_id") or "").strip()})
        case_submitter_ids = sorted({_case_submitter_from_sample_row(row) for row in sample_rows if _case_submitter_from_sample_row(row)})
        filters = build_gdc_clinical_case_filters(project_id=project_id, case_ids=case_ids, case_submitter_ids=case_submitter_ids)
        cases = self._fetch_all_cases(filters, timeout=timeout)
        return self._build_from_cases(
            root=root,
            project_id=project_id,
            mode="expression_matched_cases",
            cases=cases,
            filters=filters,
            source_expression_manifest_path=manifest_path,
            source_sample_mapping_path=sample_mapping_path,
            sample_rows=sample_rows,
            timeout=timeout,
        )

    def build_for_project(self, project_root: str | Path, project_id: str, *, timeout: int = 10) -> TCGAClinicalBuildResult:
        root = Path(project_root).expanduser().resolve()
        normalized_project = str(project_id or "").strip().upper()
        if not normalized_project:
            raise ValueError("必须提供 TCGA project_id。")
        filters = build_gdc_clinical_case_filters(project_id=normalized_project)
        cases = self._fetch_all_cases(filters, timeout=timeout)
        return self._build_from_cases(
            root=root,
            project_id=normalized_project,
            mode="project_clinical_preview_only",
            cases=cases,
            filters=filters,
            source_expression_manifest_path=None,
            source_sample_mapping_path=None,
            sample_rows=[],
            timeout=timeout,
        )

    def _fetch_all_cases(self, filters: dict[str, object], *, timeout: int) -> list[dict[str, Any]]:
        offset = 0
        total: int | None = None
        hits: list[dict[str, Any]] = []
        while total is None or offset < total:
            payload = self._fetcher(
                "/cases",
                {
                    "filters": filters,
                    "fields": CLINICAL_CASE_FIELDS,
                    "format": "JSON",
                    "size": self._page_size,
                    "from": offset,
                    "sort": "submitter_id:asc",
                },
                timeout,
            )
            page_hits, pagination_total = _payload_hits_and_total(payload)
            hits.extend(page_hits)
            total = pagination_total if pagination_total is not None else len(hits)
            if not page_hits or pagination_total is None:
                break
            offset += len(page_hits)
        return hits

    def _build_from_cases(
        self,
        *,
        root: Path,
        project_id: str,
        mode: str,
        cases: list[dict[str, Any]],
        filters: dict[str, object],
        source_expression_manifest_path: Path | None,
        source_sample_mapping_path: Path | None,
        sample_rows: list[dict[str, str]],
        timeout: int,
    ) -> TCGAClinicalBuildResult:
        clinical_build_id = f"tcga-b66-{uuid4().hex[:10]}"
        clinical_dir = _clinical_output_dir(root, project_id, clinical_build_id, source_expression_manifest_path)
        raw_cases_path = clinical_dir / "tcga_clinical_raw_cases.json"
        case_table_path = clinical_dir / "tcga_clinical_case_table.tsv"
        diagnosis_table_path = clinical_dir / "tcga_clinical_diagnosis_table.tsv"
        followup_table_path = clinical_dir / "tcga_clinical_followup_table.tsv"
        survival_table_path = clinical_dir / "tcga_clinical_survival_table.tsv"
        mapping_table_path = clinical_dir / "tcga_clinical_mapping_table.tsv"
        build_manifest_path = clinical_dir / "tcga_clinical_build_manifest.json"
        receipt_path = root / "acquisition" / "clinical_receipts" / f"{clinical_build_id}.json"
        clinical_artifact_manifest_path = root / "acquisition" / "clinical_manifests" / f"{clinical_build_id}.json"

        raw_payload = {
            "schema_version": "biomedpilot.gdc_cases_raw_payload.v1",
            "created_at": _now(),
            "project_id": project_id,
            "mode": mode,
            "endpoint": "/cases",
            "filters": filters,
            "fields": CLINICAL_CASE_FIELDS,
            "cases": cases,
        }
        _write_json(raw_cases_path, raw_payload)

        warnings: list[str] = []
        case_rows, diagnosis_rows, followup_rows, survival_rows = _standardize_cases(cases, warnings)
        mapping_rows = _build_mapping_rows(sample_rows, case_rows, survival_rows) if sample_rows else []
        summary = _clinical_gate_summary(mode=mode, case_rows=case_rows, mapping_rows=mapping_rows, survival_rows=survival_rows, warnings=warnings)
        _write_tsv(case_table_path, case_rows, _CASE_TABLE_FIELDS)
        _write_tsv(diagnosis_table_path, diagnosis_rows, _DIAGNOSIS_TABLE_FIELDS)
        _write_tsv(followup_table_path, followup_rows, _FOLLOWUP_TABLE_FIELDS)
        _write_tsv(survival_table_path, survival_rows, _SURVIVAL_TABLE_FIELDS)
        _write_tsv(mapping_table_path, mapping_rows, _MAPPING_TABLE_FIELDS)

        clinical_manifest = {
            "schema_version": TCGA_CLINICAL_ARTIFACT_MANIFEST_SCHEMA_VERSION,
            "clinical_build_id": clinical_build_id,
            "created_at": _now(),
            "project_id": project_id,
            "mode": mode,
            "source_expression_build_manifest_path": str(source_expression_manifest_path or ""),
            "source_sample_mapping_path": str(source_sample_mapping_path or ""),
            "raw_source_files": [{"path": str(raw_cases_path), "role": "tcga_gdc_raw_cases_json"}],
            "derived_artifacts": {
                "case_table": str(case_table_path),
                "diagnosis_table": str(diagnosis_table_path),
                "followup_table": str(followup_table_path),
                "survival_table": str(survival_table_path),
                "mapping_table": str(mapping_table_path),
                "build_manifest": str(build_manifest_path),
            },
            "summary": summary,
            "warnings": list(dict.fromkeys(warnings)),
            "not_expression_source_files": True,
        }
        _write_json(clinical_artifact_manifest_path, clinical_manifest)

        build_manifest = {
            "schema_version": TCGA_CLINICAL_BUILD_MANIFEST_SCHEMA_VERSION,
            "clinical_build_id": clinical_build_id,
            "created_at": _now(),
            "project_id": project_id,
            "mode": mode,
            "status": "tcga_clinical_metadata_built",
            "message": _clinical_message(mode, summary),
            "source_expression_build_manifest_path": str(source_expression_manifest_path or ""),
            "source_sample_mapping_path": str(source_sample_mapping_path or ""),
            "query": {
                "endpoint": "/cases",
                "filters": filters,
                "fields": CLINICAL_CASE_FIELDS,
                "timeout": timeout,
            },
            "raw_cases_path": str(raw_cases_path),
            "case_table_path": str(case_table_path),
            "diagnosis_table_path": str(diagnosis_table_path),
            "followup_table_path": str(followup_table_path),
            "survival_table_path": str(survival_table_path),
            "mapping_table_path": str(mapping_table_path),
            "clinical_artifact_manifest_path": str(clinical_artifact_manifest_path),
            "summary": summary,
            "warnings": list(dict.fromkeys(warnings)),
            "ready_for_recognition": "pending_data_check",
            "analysis_gate_status": "pending_data_check",
            "clinical_gate_status": summary["clinical_gate_status"],
            "survival_gate_status": summary["survival_gate_status"],
            "survival_execution_status": "not_executed",
        }
        _write_json(build_manifest_path, build_manifest)

        receipt = {
            "schema_version": TCGA_CLINICAL_RECEIPT_SCHEMA_VERSION,
            "clinical_build_id": clinical_build_id,
            "created_at": _now(),
            "project_id": project_id,
            "mode": mode,
            "status": "tcga_clinical_metadata_built",
            "endpoint": "/cases",
            "filters": filters,
            "raw_cases_path": str(raw_cases_path),
            "clinical_build_manifest_path": str(build_manifest_path),
            "clinical_artifact_manifest_path": str(clinical_artifact_manifest_path),
            "summary": summary,
            "events": [
                {
                    "status": "success" if cases else "empty",
                    "case_count": len(cases),
                    "message": f"GDC /cases returned {len(cases)} cases.",
                }
            ],
            "warnings": list(dict.fromkeys(warnings)),
        }
        _write_json(receipt_path, receipt)

        acquisition = _register_clinical_build(
            root=root,
            project_id=project_id,
            clinical_build_id=clinical_build_id,
            raw_cases_path=raw_cases_path,
            build_manifest_path=build_manifest_path,
            clinical_artifact_manifest_path=clinical_artifact_manifest_path,
            receipt_path=receipt_path,
            summary=summary,
            warnings=warnings,
            mode=mode,
        )
        return TCGAClinicalBuildResult(
            success=True,
            status="tcga_clinical_metadata_built",
            message=str(build_manifest["message"]),
            project_id=project_id,
            clinical_build_id=clinical_build_id,
            mode=mode,
            case_count=int(summary["case_count"]),
            matched_case_count=int(summary["matched_case_count"]),
            matched_sample_count=int(summary["matched_sample_count"]),
            survival_case_count=int(summary["survival_case_count"]),
            death_event_count=int(summary["death_event_count"]),
            raw_cases_path=raw_cases_path,
            case_table_path=case_table_path,
            diagnosis_table_path=diagnosis_table_path,
            followup_table_path=followup_table_path,
            survival_table_path=survival_table_path,
            mapping_table_path=mapping_table_path,
            clinical_manifest_path=clinical_artifact_manifest_path,
            clinical_receipt_path=receipt_path,
            warnings=tuple(dict.fromkeys(warnings)),
            acquisition_summary=acquisition,
        )


_CASE_TABLE_FIELDS = [
    "case_id",
    "case_submitter_id",
    "project_id",
    "primary_site",
    "disease_type",
    "consent_type",
    "days_to_index",
    "index_date",
    "gender",
    "race",
    "ethnicity",
    "vital_status",
    "days_to_birth",
    "age_at_index",
    "days_to_death",
    "year_of_birth",
    "year_of_death",
    "primary_diagnosis",
    "tumor_stage",
    "tumor_grade",
    "ajcc_pathologic_stage",
    "ajcc_pathologic_t",
    "ajcc_pathologic_n",
    "ajcc_pathologic_m",
    "diagnosis_count",
    "followup_count",
]

_DIAGNOSIS_TABLE_FIELDS = [
    "case_id",
    "case_submitter_id",
    "diagnosis_index",
    "diagnosis_id",
    "primary_diagnosis",
    "tumor_stage",
    "tumor_grade",
    "ajcc_pathologic_stage",
    "ajcc_pathologic_t",
    "ajcc_pathologic_n",
    "ajcc_pathologic_m",
    "ajcc_clinical_stage",
    "ajcc_clinical_t",
    "ajcc_clinical_n",
    "ajcc_clinical_m",
    "days_to_diagnosis",
    "age_at_diagnosis",
    "classification_of_tumor",
    "last_known_disease_status",
    "prior_malignancy",
    "prior_treatment",
    "vital_status",
    "days_to_death",
    "days_to_last_follow_up",
]

_FOLLOWUP_TABLE_FIELDS = [
    "case_id",
    "case_submitter_id",
    "followup_index",
    "follow_up_id",
    "days_to_follow_up",
    "days_to_last_follow_up",
    "days_to_death",
    "vital_status",
    "progression_or_recurrence",
    "treatment_or_therapy",
    "days_to_recurrence",
    "days_to_progression",
]

_SURVIVAL_TABLE_FIELDS = [
    "case_id",
    "case_submitter_id",
    "OS_time",
    "OS_event",
    "OS_time_source",
    "OS_event_source",
    "survival_warning",
]

_MAPPING_TABLE_FIELDS = [
    "sample_barcode",
    "sample_submitter_id",
    "sample_type",
    "case_id",
    "case_submitter_id",
    "has_expression",
    "has_clinical",
    "has_survival",
    "mapping_status",
]


def latest_tcga_expression_build_manifest_path(project_root: str | Path, *, project_id: str | None = None) -> Path | None:
    root = Path(project_root).expanduser().resolve()
    selected_project = str(project_id or "").strip().upper()
    records_dir = root / "acquisition" / "records"
    if not records_dir.exists():
        return None
    candidates: list[Path] = []
    for path in sorted(records_dir.glob("*.json"), key=lambda item: item.stat().st_mtime):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            continue
        record_project = str(metadata.get("project_id") or payload.get("source_label") or "").strip().upper()
        if selected_project and record_project and record_project != selected_project:
            continue
        if str(metadata.get("download_status") or "") != "tcga_expression_matrix_built":
            continue
        manifest_path = Path(str(metadata.get("tcga_expression_build_manifest_path") or ""))
        if manifest_path.is_file():
            candidates.append(manifest_path)
    return candidates[-1] if candidates else None


def latest_tcga_clinical_build_manifest_path(project_root: str | Path, *, project_id: str | None = None) -> Path | None:
    root = Path(project_root).expanduser().resolve()
    selected_project = str(project_id or "").strip().upper()
    records_dir = root / "acquisition" / "records"
    if not records_dir.exists():
        return None
    candidates: list[Path] = []
    for path in sorted(records_dir.glob("*.json"), key=lambda item: item.stat().st_mtime):
        if path.name == LATEST_RECORD:
            continue
        try:
            payload = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        if not isinstance(metadata, dict):
            continue
        record_project = str(metadata.get("project_id") or payload.get("source_label") or "").strip().upper()
        if selected_project and record_project and record_project != selected_project:
            continue
        if str(metadata.get("download_status") or "") != "tcga_clinical_metadata_built":
            continue
        manifest_path = Path(str(metadata.get("tcga_clinical_build_manifest_path") or ""))
        if manifest_path.is_file():
            candidates.append(manifest_path)
    return candidates[-1] if candidates else None


def build_gdc_clinical_case_filters(
    *,
    project_id: str,
    case_ids: Iterable[str] | None = None,
    case_submitter_ids: Iterable[str] | None = None,
) -> dict[str, object]:
    operands: list[dict[str, object]] = [_in_filter("project.project_id", [project_id])]
    case_operands: list[dict[str, object]] = []
    case_id_values = _unique_nonempty(case_ids or [])
    submitter_values = _unique_nonempty(case_submitter_ids or [])
    if case_id_values:
        case_operands.append(_in_filter("case_id", case_id_values))
    if submitter_values:
        case_operands.append(_in_filter("submitter_id", submitter_values))
    if len(case_operands) == 1:
        operands.append(case_operands[0])
    elif case_operands:
        operands.append({"op": "or", "content": case_operands})
    return {"op": "and", "content": operands}


def _standardize_cases(
    cases: list[dict[str, Any]],
    warnings: list[str],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    case_rows: list[dict[str, str]] = []
    diagnosis_rows: list[dict[str, str]] = []
    followup_rows: list[dict[str, str]] = []
    survival_rows: list[dict[str, str]] = []
    for case in cases:
        case_id = _text(case.get("case_id"))
        case_submitter_id = _text(case.get("submitter_id"))
        project = case.get("project") if isinstance(case.get("project"), dict) else {}
        demographic = case.get("demographic") if isinstance(case.get("demographic"), dict) else {}
        diagnoses = [item for item in case.get("diagnoses", []) or [] if isinstance(item, dict)]
        follow_ups = [item for item in case.get("follow_ups", []) or [] if isinstance(item, dict)]
        for diagnosis in diagnoses:
            follow_ups.extend(item for item in diagnosis.get("follow_ups", []) or [] if isinstance(item, dict))
        if not demographic:
            warnings.append(f"missing_demographic:{case_submitter_id or case_id}")
        primary_diagnosis = diagnoses[0] if diagnoses else {}
        if not diagnoses:
            warnings.append(f"missing_diagnosis:{case_submitter_id or case_id}")
        case_rows.append(
            {
                "case_id": case_id,
                "case_submitter_id": case_submitter_id,
                "project_id": _text(project.get("project_id") if isinstance(project, dict) else ""),
                "primary_site": _text(case.get("primary_site")),
                "disease_type": _text(case.get("disease_type")),
                "consent_type": _text(case.get("consent_type")),
                "days_to_index": _text(case.get("days_to_index")),
                "index_date": _text(case.get("index_date")),
                "gender": _text(demographic.get("gender")),
                "race": _text(demographic.get("race")),
                "ethnicity": _text(demographic.get("ethnicity")),
                "vital_status": _first_text(demographic.get("vital_status"), primary_diagnosis.get("vital_status")),
                "days_to_birth": _text(demographic.get("days_to_birth")),
                "age_at_index": _text(demographic.get("age_at_index")),
                "days_to_death": _first_text(demographic.get("days_to_death"), primary_diagnosis.get("days_to_death")),
                "year_of_birth": _text(demographic.get("year_of_birth")),
                "year_of_death": _text(demographic.get("year_of_death")),
                "primary_diagnosis": _text(primary_diagnosis.get("primary_diagnosis")),
                "tumor_stage": _text(primary_diagnosis.get("tumor_stage")),
                "tumor_grade": _text(primary_diagnosis.get("tumor_grade")),
                "ajcc_pathologic_stage": _text(primary_diagnosis.get("ajcc_pathologic_stage")),
                "ajcc_pathologic_t": _text(primary_diagnosis.get("ajcc_pathologic_t")),
                "ajcc_pathologic_n": _text(primary_diagnosis.get("ajcc_pathologic_n")),
                "ajcc_pathologic_m": _text(primary_diagnosis.get("ajcc_pathologic_m")),
                "diagnosis_count": str(len(diagnoses)),
                "followup_count": str(len(follow_ups)),
            }
        )
        for index, diagnosis in enumerate(diagnoses, start=1):
            diagnosis_rows.append(
                {
                    "case_id": case_id,
                    "case_submitter_id": case_submitter_id,
                    "diagnosis_index": str(index),
                    **{field: _text(diagnosis.get(field)) for field in _DIAGNOSIS_TABLE_FIELDS if field not in {"case_id", "case_submitter_id", "diagnosis_index"}},
                }
            )
        for index, follow_up in enumerate(follow_ups, start=1):
            followup_rows.append(
                {
                    "case_id": case_id,
                    "case_submitter_id": case_submitter_id,
                    "followup_index": str(index),
                    **{field: _text(follow_up.get(field)) for field in _FOLLOWUP_TABLE_FIELDS if field not in {"case_id", "case_submitter_id", "followup_index"}},
                }
            )
        survival_rows.append(_derive_basic_os_row(case_id, case_submitter_id, demographic, diagnoses, follow_ups, warnings))
    return case_rows, diagnosis_rows, followup_rows, survival_rows


def _derive_basic_os_row(
    case_id: str,
    case_submitter_id: str,
    demographic: dict[str, Any],
    diagnoses: list[dict[str, Any]],
    follow_ups: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, str]:
    label = case_submitter_id or case_id
    vital_status, event_source = _first_field_with_source(
        [("demographic.vital_status", demographic), *[(f"diagnoses[{index}].vital_status", item) for index, item in enumerate(diagnoses)]],
        "vital_status",
    )
    if not vital_status:
        vital_status, event_source = _first_field_with_source(
            [(f"follow_ups[{index}].vital_status", item) for index, item in enumerate(follow_ups)],
            "vital_status",
        )
    normalized_status = vital_status.strip().lower()
    if normalized_status == "dead":
        event = "1"
        os_time, time_source = _first_field_with_source(
            [("demographic.days_to_death", demographic), *[(f"diagnoses[{index}].days_to_death", item) for index, item in enumerate(diagnoses)], *[(f"follow_ups[{index}].days_to_death", item) for index, item in enumerate(follow_ups)]],
            "days_to_death",
        )
    elif normalized_status == "alive":
        event = "0"
        os_time, time_source = _first_field_with_source(
            [*[(f"diagnoses[{index}].days_to_last_follow_up", item) for index, item in enumerate(diagnoses)], *[(f"follow_ups[{index}].days_to_last_follow_up", item) for index, item in enumerate(follow_ups)]],
            "days_to_last_follow_up",
        )
    else:
        event = ""
        event_source = ""
        os_time = ""
        time_source = ""
    warning = ""
    if not os_time:
        os_time, time_source = _max_followup_time(follow_ups)
    if not event:
        warning = "OS_event_unavailable"
        warnings.append(f"missing_vital_status:{label}")
    if not os_time:
        warning = ";".join([value for value in (warning, "OS_time_unavailable") if value])
        warnings.append(f"missing_os_time:{label}")
    return {
        "case_id": case_id,
        "case_submitter_id": case_submitter_id,
        "OS_time": os_time,
        "OS_event": event,
        "OS_time_source": time_source,
        "OS_event_source": event_source,
        "survival_warning": warning,
    }


def _build_mapping_rows(
    sample_rows: list[dict[str, str]],
    case_rows: list[dict[str, str]],
    survival_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    clinical_by_case_id = {str(row.get("case_id") or ""): row for row in case_rows if str(row.get("case_id") or "")}
    clinical_by_submitter = {str(row.get("case_submitter_id") or ""): row for row in case_rows if str(row.get("case_submitter_id") or "")}
    survival_case_ids = {str(row.get("case_id") or "") for row in survival_rows if str(row.get("OS_time") or "") and str(row.get("OS_event") or "")}
    survival_submitters = {str(row.get("case_submitter_id") or "") for row in survival_rows if str(row.get("OS_time") or "") and str(row.get("OS_event") or "")}
    mapping: list[dict[str, str]] = []
    for sample in sample_rows:
        sample_barcode = _first_text(sample.get("sample_barcode"), sample.get("sample_submitter_id"), sample.get("sample_id"))
        case_id = _text(sample.get("case_id"))
        case_submitter_id = _case_submitter_from_sample_row(sample)
        clinical = clinical_by_case_id.get(case_id)
        status = "matched_by_case_id" if clinical is not None else ""
        if clinical is None and case_submitter_id:
            clinical = clinical_by_submitter.get(case_submitter_id)
            status = "matched_by_case_submitter_id" if clinical is not None else ""
        if clinical is None and sample_barcode:
            patient_barcode = _patient_barcode_from_sample(sample_barcode)
            if patient_barcode:
                clinical = clinical_by_submitter.get(patient_barcode)
                status = "matched_by_sample_barcode_patient_prefix" if clinical is not None else ""
                case_submitter_id = case_submitter_id or patient_barcode
        if clinical is not None:
            case_id = str(clinical.get("case_id") or case_id)
            case_submitter_id = str(clinical.get("case_submitter_id") or case_submitter_id)
        has_survival = case_id in survival_case_ids or case_submitter_id in survival_submitters
        mapping.append(
            {
                "sample_barcode": sample_barcode,
                "sample_submitter_id": _first_text(sample.get("sample_submitter_id"), sample.get("sample_id"), sample_barcode),
                "sample_type": _text(sample.get("sample_type")),
                "case_id": case_id,
                "case_submitter_id": case_submitter_id,
                "has_expression": "true",
                "has_clinical": "true" if clinical is not None else "false",
                "has_survival": "true" if has_survival else "false",
                "mapping_status": status or "unmatched",
            }
        )
    return mapping


def _clinical_gate_summary(
    *,
    mode: str,
    case_rows: list[dict[str, str]],
    mapping_rows: list[dict[str, str]],
    survival_rows: list[dict[str, str]],
    warnings: list[str],
) -> dict[str, object]:
    matched_samples = [row for row in mapping_rows if row.get("has_clinical") == "true"]
    matched_case_keys = {
        str(row.get("case_id") or row.get("case_submitter_id") or "")
        for row in matched_samples
        if str(row.get("case_id") or row.get("case_submitter_id") or "")
    }
    expression_case_keys = {
        str(row.get("case_id") or row.get("case_submitter_id") or "")
        for row in mapping_rows
        if str(row.get("case_id") or row.get("case_submitter_id") or "")
    }
    survival_available = [row for row in survival_rows if str(row.get("OS_time") or "") and str(row.get("OS_event") or "")]
    death_events = [row for row in survival_available if str(row.get("OS_event") or "") == "1"]
    match_ratio = (len(matched_case_keys) / len(expression_case_keys)) if expression_case_keys else 0.0
    if not case_rows:
        clinical_gate_status = "clinical_unavailable"
    elif mode == "project_clinical_preview_only":
        clinical_gate_status = "clinical_partial"
        warnings.append("project_clinical_preview_only_no_expression_mapping")
    elif match_ratio >= 0.8:
        clinical_gate_status = "clinical_ready"
    else:
        clinical_gate_status = "clinical_partial"
        warnings.append("tcga_expression_clinical_case_match_ratio_below_0_8")
    if survival_available and death_events:
        survival_gate_status = "survival_ready_basic"
        if len(death_events) < 5:
            warnings.append("death_event_count_below_warning_threshold_5")
    elif survival_available:
        survival_gate_status = "survival_partial"
    else:
        survival_gate_status = "survival_unavailable"
    demographic_available = sum(1 for row in case_rows if row.get("gender") or row.get("race") or row.get("ethnicity") or row.get("age_at_index"))
    diagnosis_available = sum(1 for row in case_rows if row.get("primary_diagnosis") or row.get("tumor_stage") or row.get("ajcc_pathologic_stage"))
    return {
        "case_count": len(case_rows),
        "expression_case_count": len(expression_case_keys),
        "matched_case_count": len(matched_case_keys),
        "matched_sample_count": len(matched_samples),
        "sample_count": len(mapping_rows),
        "sample_case_match_ratio": round(match_ratio, 4),
        "survival_case_count": len(survival_available),
        "death_event_count": len(death_events),
        "demographic_available_case_count": demographic_available,
        "diagnosis_available_case_count": diagnosis_available,
        "clinical_gate_status": clinical_gate_status,
        "survival_gate_status": survival_gate_status,
        "survival_execution_status": "not_executed",
        "auto_run_survival": False,
        "auto_run_deg_gsea": False,
    }


def _register_clinical_build(
    *,
    root: Path,
    project_id: str,
    clinical_build_id: str,
    raw_cases_path: Path,
    build_manifest_path: Path,
    clinical_artifact_manifest_path: Path,
    receipt_path: Path,
    summary: dict[str, object],
    warnings: list[str],
    mode: str,
) -> AcquisitionSummary:
    file_records = [
        build_file_record(
            raw_cases_path,
            source="tcga_gdc",
            role="tcga_gdc_raw_cases_json",
            status="available",
            message="B6.6 GDC /cases raw clinical JSON trace file.",
        )
    ]
    return register_acquisition(
        root,
        source_type="tcga_project",
        source_label=project_id,
        strategy="reference",
        selected_paths=[raw_cases_path],
        metadata={
            "source": "tcga_gdc",
            "ui_source": "tcga_database_page",
            "registration_status": "registered_tcga_clinical_artifacts_waiting_data_check",
            "download_status": "tcga_clinical_metadata_built",
            "ready_for_recognition": "pending_data_check",
            "recognition_scope": "tcga_clinical_metadata_waiting_data_check",
            "analysis_gate_status": "pending_data_check",
            "clinical_gate_status": summary.get("clinical_gate_status"),
            "survival_gate_status": summary.get("survival_gate_status"),
            "survival_execution_status": "not_executed",
            "analysis_gate_message": "TCGA clinical metadata 已获取并完成表达-临床映射，等待统一数据检查与准备；不自动执行 survival/DEG/GSEA。",
            "project_id": project_id,
            "clinical_build_id": clinical_build_id,
            "mode": mode,
            "display_title_zh": f"TCGA {project_id} clinical metadata",
            "download_receipt_path": str(receipt_path),
            "clinical_receipt_path": str(receipt_path),
            "tcga_clinical_build_manifest_path": str(build_manifest_path),
            "tcga_clinical_artifact_manifest_path": str(clinical_artifact_manifest_path),
            "tcga_clinical_summary": summary,
            "expected_assets": ["clinical_metadata", "case_sample_mapping", "basic_survival_metadata"],
            "warnings": list(dict.fromkeys(warnings)),
        },
        file_records=file_records,
    )


def _clinical_message(mode: str, summary: dict[str, object]) -> str:
    if mode == "project_clinical_preview_only":
        return f"TCGA clinical 概况已获取：{summary.get('case_count') or 0} 个 case；无 B6.4 表达矩阵，不能做表达-临床映射。"
    return (
        f"TCGA clinical metadata 已获取：{summary.get('case_count') or 0} 个 case；"
        f"匹配表达 case {summary.get('matched_case_count') or 0} 个，"
        f"基础 OS 可用 {summary.get('survival_case_count') or 0} 个 case；等待数据检查与准备。"
    )


def _clinical_output_dir(root: Path, project_id: str, clinical_build_id: str, source_expression_manifest_path: Path | None) -> Path:
    if source_expression_manifest_path is not None and source_expression_manifest_path.is_file():
        return source_expression_manifest_path.parent / "clinical"
    return root / "standardized_data" / "tcga" / _slug(project_id) / _slug(clinical_build_id) / "data_prepared" / "tcga" / "clinical"


def _read_sample_mapping(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"TCGA sample mapping file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{str(key or "").strip(): str(value or "").strip() for key, value in row.items()} for row in reader]


def _write_tsv(path: Path, rows: Iterable[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _payload_hits_and_total(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], int | None]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    hits = [item for item in data.get("hits", []) or [] if isinstance(item, dict)]
    pagination = data.get("pagination") if isinstance(data.get("pagination"), dict) else {}
    total = pagination.get("total")
    try:
        return hits, int(total) if total is not None else None
    except (TypeError, ValueError):
        return hits, None


def _first_field_with_source(sources: Iterable[tuple[str, dict[str, Any]]], field: str) -> tuple[str, str]:
    for source, payload in sources:
        value = _text(payload.get(field))
        if value:
            return value, source
    return "", ""


def _max_followup_time(follow_ups: list[dict[str, Any]]) -> tuple[str, str]:
    candidates: list[tuple[int, str]] = []
    for index, follow_up in enumerate(follow_ups):
        for field in ("days_to_follow_up", "days_to_last_follow_up"):
            value = _text(follow_up.get(field))
            if value:
                try:
                    candidates.append((int(float(value)), f"follow_ups[{index}].{field}"))
                except ValueError:
                    continue
    if not candidates:
        return "", ""
    value, source = max(candidates, key=lambda item: item[0])
    return str(value), source


def _case_submitter_from_sample_row(row: dict[str, str]) -> str:
    value = _text(row.get("case_submitter_id"))
    if value:
        return value
    barcode = _first_text(row.get("sample_barcode"), row.get("sample_submitter_id"), row.get("sample_id"))
    return _patient_barcode_from_sample(barcode)


def _patient_barcode_from_sample(sample_barcode: str) -> str:
    text = str(sample_barcode or "").strip()
    if not text:
        return ""
    try:
        parsed = parse_tcga_barcode(text)
    except ValueError:
        match = re.match(r"^(TCGA-[A-Z0-9]{2}-[A-Z0-9]{4})", text, flags=re.IGNORECASE)
        return match.group(1).upper() if match else ""
    return str(parsed.get("patient_barcode") or "").strip().upper()


def _in_filter(field: str, values: Iterable[str]) -> dict[str, object]:
    return {"op": "in", "content": {"field": field, "value": _unique_nonempty(values)}}


def _unique_nonempty(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def _first_text(*values: object) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "").strip()).strip("-").lower() or "tcga"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


__all__ = [
    "CLINICAL_CASE_FIELDS",
    "TCGA_CLINICAL_ARTIFACT_MANIFEST_SCHEMA_VERSION",
    "TCGA_CLINICAL_BUILD_MANIFEST_SCHEMA_VERSION",
    "TCGA_CLINICAL_RECEIPT_SCHEMA_VERSION",
    "TCGAClinicalBuildResult",
    "TCGAClinicalMetadataBuilder",
    "build_gdc_clinical_case_filters",
    "latest_tcga_clinical_build_manifest_path",
    "latest_tcga_expression_build_manifest_path",
]
