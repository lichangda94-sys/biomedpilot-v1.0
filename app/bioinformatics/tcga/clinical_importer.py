"""Local TCGA clinical table import and survival field standardization."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from app.bioinformatics.standard_assets.tcga_assets import (
    CONTRACT_VERSION,
    TCGA_CLINICAL_LINKAGE_SUMMARY,
    TCGA_CLINICAL_TABLE,
    TCGA_PREPARE_MANIFEST,
    build_tcga_asset_paths,
)

from .barcode import parse_tcga_barcode


PATIENT_BARCODE_FIELDS = (
    "patient_barcode",
    "bcr_patient_barcode",
    "submitter_id",
    "case_submitter_id",
    "cases.submitter_id",
)
SAMPLE_BARCODE_FIELDS = (
    "tcga_barcode",
    "sample_barcode",
    "barcode",
    "sample_id",
    "aliquot_barcode",
    "cases.samples.submitter_id",
)
CLINICAL_OUTPUT_FIELDS = [
    "patient_barcode",
    "os_time_days",
    "os_event",
    "vital_status",
    "days_to_death",
    "days_to_last_follow_up",
    "age_at_diagnosis",
    "age_at_diagnosis_years",
    "gender",
    "stage",
]
STAGE_FIELDS = ("ajcc_pathologic_stage", "pathologic_stage", "tumor_stage", "stage")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _detect_delimiter(input_path: Path) -> str:
    first_line = input_path.read_text(encoding="utf-8-sig").splitlines()[0]
    if first_line.count("\t") > first_line.count(","):
        return "\t"
    return ","


def _read_table(input_path: Path) -> list[dict[str, str]]:
    delimiter = _detect_delimiter(input_path)
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append({str(key or "").strip(): str(value or "").strip() for key, value in row.items()})
    return rows


def _write_table(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _emptyish(value: Any) -> bool:
    text = str(value or "").strip()
    return text == "" or text.lower() in {"na", "n/a", "null", "none", "not reported", "not available", "--"}


def _get_value(row: dict[str, str], candidates: tuple[str, ...]) -> str:
    lower_to_key = {key.lower(): key for key in row}
    for candidate in candidates:
        key = lower_to_key.get(candidate.lower())
        if key is not None and not _emptyish(row.get(key, "")):
            return row.get(key, "").strip()
    return ""


def _normalize_patient_barcode(value: str) -> str:
    if _emptyish(value):
        return ""
    try:
        return parse_tcga_barcode(value)["patient_barcode"]
    except ValueError:
        return value.strip().upper()


def _patient_barcode_from_row(row: dict[str, str]) -> str:
    patient_value = _get_value(row, PATIENT_BARCODE_FIELDS)
    if patient_value:
        return _normalize_patient_barcode(patient_value)
    sample_value = _get_value(row, SAMPLE_BARCODE_FIELDS)
    if sample_value:
        return _normalize_patient_barcode(sample_value)
    return ""


def _number_text(value: str) -> str:
    if _emptyish(value):
        return ""
    text = str(value).strip()
    try:
        numeric = float(text)
    except ValueError:
        return text
    if numeric.is_integer():
        return str(int(numeric))
    return str(numeric)


def _numeric(value: str) -> float | None:
    text = _number_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _normalize_vital_status(value: str) -> str:
    text = str(value or "").strip().lower()
    if text in {"dead", "deceased"}:
        return "Dead"
    if text in {"alive", "living"}:
        return "Alive"
    return str(value or "").strip() or "Unknown"


def _vital_event(vital_status: str) -> int | None:
    text = vital_status.strip().lower()
    if text in {"dead", "deceased"}:
        return 1
    if text in {"alive", "living"}:
        return 0
    return None


def _normalize_gender(value: str) -> str:
    text = str(value or "").strip().lower()
    if text in {"male", "m"}:
        return "male"
    if text in {"female", "f"}:
        return "female"
    return "unknown"


def _age_years(age_at_diagnosis: str) -> str:
    value = _numeric(age_at_diagnosis)
    if value is None or value <= 150:
        return ""
    return f"{value / 365.25:.2f}"


def _standardize_clinical_row(row: dict[str, str], warnings: list[str]) -> dict[str, str]:
    patient_barcode = _patient_barcode_from_row(row)
    vital_status = _normalize_vital_status(_get_value(row, ("vital_status",)))
    days_to_death = _number_text(_get_value(row, ("days_to_death",)))
    days_to_last_follow_up = _number_text(
        _get_value(row, ("days_to_last_follow_up", "days_to_last_followup", "days_to_last_contact"))
    )
    death_days = _numeric(days_to_death)
    follow_up_days = _numeric(days_to_last_follow_up)

    os_time_days = ""
    os_event: int | str = ""
    if death_days is not None:
        os_time_days = _number_text(days_to_death)
        os_event = 1
    elif follow_up_days is not None:
        os_time_days = _number_text(days_to_last_follow_up)
        os_event = 0

    vital_event = _vital_event(vital_status)
    if os_event == "" and vital_event is not None:
        os_event = vital_event
    elif os_event != "" and vital_event is not None and os_event != vital_event:
        warnings.append(f"os_event_conflict:{patient_barcode}:time_event={os_event}:vital_event={vital_event}")

    if not os_time_days:
        warnings.append(f"missing_os_time:{patient_barcode or 'unknown_patient'}")

    age_at_diagnosis = _number_text(_get_value(row, ("age_at_diagnosis",)))
    stage = _get_value(row, STAGE_FIELDS)
    return {
        "patient_barcode": patient_barcode,
        "os_time_days": os_time_days,
        "os_event": str(os_event),
        "vital_status": vital_status,
        "days_to_death": days_to_death,
        "days_to_last_follow_up": days_to_last_follow_up,
        "age_at_diagnosis": age_at_diagnosis,
        "age_at_diagnosis_years": _age_years(age_at_diagnosis),
        "gender": _normalize_gender(_get_value(row, ("gender", "sex"))),
        "stage": stage,
    }


def _standardize_clinical_rows(raw_rows: list[dict[str, str]], warnings: list[str]) -> list[dict[str, str]]:
    seen_patients: set[str] = set()
    duplicate_patients: list[str] = []
    output_rows: list[dict[str, str]] = []

    for row in raw_rows:
        standardized = _standardize_clinical_row(row, warnings)
        patient_barcode = standardized["patient_barcode"]
        if not patient_barcode:
            warnings.append("missing_patient_barcode")
            continue
        if patient_barcode in seen_patients:
            duplicate_patients.append(patient_barcode)
            continue
        seen_patients.add(patient_barcode)
        output_rows.append(standardized)

    if duplicate_patients:
        warnings.append(
            f"duplicate_patient_barcode_rows_removed:{len(duplicate_patients)}:{','.join(sorted(set(duplicate_patients)))}"
        )
    return output_rows


def _patient_from_sample_metadata_row(row: dict[str, str]) -> str:
    for field in ("participant_barcode", "patient_barcode"):
        value = row.get(field, "")
        if not _emptyish(value):
            return _normalize_patient_barcode(value)
    for field in ("tcga_barcode", "sample_id", "barcode"):
        value = row.get(field, "")
        if not _emptyish(value):
            return _normalize_patient_barcode(value)
    return ""


def _build_linkage_summary(
    sample_metadata_path: Path,
    clinical_rows: list[dict[str, str]],
) -> dict[str, Any]:
    sample_rows = _read_table(sample_metadata_path)
    sample_patients = sorted(
        {patient for patient in (_patient_from_sample_metadata_row(row) for row in sample_rows) if patient}
    )
    clinical_patients = sorted({row["patient_barcode"] for row in clinical_rows if row.get("patient_barcode")})
    matched = sorted(set(sample_patients) & set(clinical_patients))
    return {
        "sample_count": len(sample_rows),
        "unique_sample_patients": len(sample_patients),
        "clinical_patient_count": len(clinical_patients),
        "matched_patient_count": len(matched),
        "unmatched_sample_patients": sorted(set(sample_patients) - set(clinical_patients)),
        "unmatched_clinical_patients": sorted(set(clinical_patients) - set(sample_patients)),
    }


def _merge_warnings(existing: list[Any], new_warnings: list[str]) -> list[str]:
    merged: list[str] = []
    for warning in [str(value) for value in existing] + new_warnings:
        if warning not in merged:
            merged.append(warning)
    return merged


def _update_prepare_manifest(
    manifest_path: Path,
    *,
    project_id: str,
    batch_id: str,
    source_path: Path,
    asset_paths: dict[str, Path],
    clinical_patient_count: int,
    linkage_summary: dict[str, Any] | None,
    warnings: list[str],
    parameters: dict[str, Any] | None,
) -> dict[str, Any]:
    if manifest_path.exists():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        payload = {
            "contract_version": CONTRACT_VERSION,
            "manifest_role": TCGA_PREPARE_MANIFEST,
            "project_id": project_id,
            "batch_id": batch_id,
            "created_at": _now_iso(),
            "source": str(source_path),
            "asset_paths": {},
            "sample_count": 0,
            "gene_count": 0,
            "normalization": "unknown",
            "warnings": [],
            "parameters": {},
        }

    payload.setdefault("contract_version", CONTRACT_VERSION)
    payload.setdefault("manifest_role", TCGA_PREPARE_MANIFEST)
    payload.setdefault("project_id", project_id)
    payload.setdefault("batch_id", batch_id)
    payload.setdefault("created_at", _now_iso())
    payload.setdefault("source", str(source_path))
    payload.setdefault("parameters", {})

    existing_asset_paths = payload.get("asset_paths") if isinstance(payload.get("asset_paths"), dict) else {}
    payload["asset_paths"] = {**existing_asset_paths, **{key: str(value) for key, value in asset_paths.items()}}
    payload["clinical_source"] = str(source_path)
    payload["clinical_patient_count"] = clinical_patient_count
    payload["matched_patient_count"] = 0 if linkage_summary is None else linkage_summary["matched_patient_count"]
    payload["warnings"] = _merge_warnings(payload.get("warnings", []), warnings)
    payload["parameters"] = {
        **payload.get("parameters", {}),
        "clinical_import": dict(parameters or {}),
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def import_tcga_clinical_table(
    input_path: str | Path,
    output_dir: str | Path,
    project_id: str,
    batch_id: str,
    sample_metadata_path: str | Path | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Import a local TCGA clinical table and standardize survival fields."""
    source_path = Path(input_path).expanduser().resolve()
    raw_rows = _read_table(source_path)
    warnings: list[str] = []
    clinical_rows = _standardize_clinical_rows(raw_rows, warnings)

    asset_paths = build_tcga_asset_paths(output_dir, project_id, batch_id, layout="data_prepared")
    clinical_path = asset_paths[TCGA_CLINICAL_TABLE]
    linkage_summary_path = asset_paths[TCGA_CLINICAL_LINKAGE_SUMMARY]
    manifest_path = asset_paths[TCGA_PREPARE_MANIFEST]

    _write_table(clinical_path, clinical_rows, CLINICAL_OUTPUT_FIELDS)

    linkage_summary = None
    if sample_metadata_path is not None:
        linkage_summary = _build_linkage_summary(Path(sample_metadata_path).expanduser().resolve(), clinical_rows)
        linkage_summary_path.parent.mkdir(parents=True, exist_ok=True)
        linkage_summary_path.write_text(json.dumps(linkage_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest = _update_prepare_manifest(
        manifest_path,
        project_id=project_id,
        batch_id=batch_id,
        source_path=source_path,
        asset_paths=asset_paths,
        clinical_patient_count=len(clinical_rows),
        linkage_summary=linkage_summary,
        warnings=warnings,
        parameters=parameters,
    )

    return {
        "status": "success",
        "project_id": project_id,
        "batch_id": batch_id,
        "clinical_patient_count": len(clinical_rows),
        "matched_patient_count": 0 if linkage_summary is None else linkage_summary["matched_patient_count"],
        "warnings": warnings,
        "asset_paths": {key: str(value) for key, value in asset_paths.items()},
        "linkage_summary": linkage_summary,
        "manifest": manifest,
    }


__all__ = ["import_tcga_clinical_table"]
