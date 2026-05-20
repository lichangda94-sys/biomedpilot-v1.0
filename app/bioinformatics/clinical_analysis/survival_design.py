from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

from .models import SurvivalInputPackage


def build_survival_package(
    input_package: dict[str, Any],
    *,
    time_field: str = "OS_time",
    event_field: str = "OS_event",
    time_unit: str = "days",
    grouping_policy: str = "user_confirmed_required",
) -> SurvivalInputPackage:
    clinical_asset = input_package.get("clinical_asset") if isinstance(input_package.get("clinical_asset"), dict) else None
    expression_asset = input_package.get("expression_asset") if isinstance(input_package.get("expression_asset"), dict) else None
    clinical_rows = _read_table(_asset_path(clinical_asset))
    blockers: list[str] = []
    warnings: list[str] = []
    if clinical_asset is None:
        blockers.append("missing_clinical_asset")
    if expression_asset is None:
        warnings.append("missing_expression_asset_survival_expression_grouping_unavailable")
    fields = set(clinical_rows[0].keys()) if clinical_rows else set()
    if time_field not in fields:
        blockers.append("missing_time_field")
    if event_field not in fields:
        blockers.append("missing_event_field")
    sample_case_mapping = _sample_case_mapping(clinical_rows)
    event_values = [str(row.get(event_field) or "").strip() for row in clinical_rows]
    event_coding = _event_coding(event_values)
    if event_coding["status"] == "ambiguous":
        blockers.append("ambiguous_event_coding")
    event_count = int(event_coding.get("event_count") or 0)
    if 0 < event_count < 10:
        warnings.append("low_event_count_for_formal_survival")
    if grouping_policy in {"", "auto_median_split"}:
        blockers.append("expression_grouping_policy_must_be_user_confirmed")
    missingness = _missingness_report(clinical_rows, [time_field, event_field])
    return SurvivalInputPackage(
        survival_package_id=_survival_id(str(input_package.get("input_package_id") or "")),
        input_package_id=str(input_package.get("input_package_id") or ""),
        clinical_asset=clinical_asset,
        expression_asset=expression_asset,
        sample_case_mapping=sample_case_mapping,
        time_field=time_field,
        event_field=event_field,
        time_unit=time_unit,
        event_coding=event_coding,
        censoring_policy="event=1 observed, event=0 censored; ambiguous coding blocks",
        grouping_policy=grouping_policy,
        missingness_report=missingness,
        event_count=event_count,
        sample_count=len(clinical_rows),
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def _asset_path(asset: dict[str, Any] | None) -> Path | None:
    if not isinstance(asset, dict):
        return None
    path = str(asset.get("path") or asset.get("file_path") or "")
    return Path(path).expanduser() if path else None


def _read_table(path: Path | None) -> list[dict[str, str]]:
    if path is None or not path.is_file():
        return []
    try:
        first = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    except (OSError, IndexError):
        return []
    delimiter = "," if first.count(",") > first.count("\t") else "\t"
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter=delimiter)]


def _sample_case_mapping(rows: list[dict[str, str]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in rows:
        sample = row.get("sample_id") or row.get("barcode") or row.get("tcga_barcode") or row.get("patient_barcode") or row.get("case_id") or ""
        case = row.get("case_id") or row.get("patient_barcode") or row.get("participant_barcode") or sample
        if sample:
            mapping[str(sample)] = str(case)
    return mapping


def _event_coding(values: list[str]) -> dict[str, Any]:
    observed = {value for value in values if value != ""}
    if not observed:
        return {"status": "ambiguous", "event_count": 0, "observed_values": []}
    if observed <= {"0", "1"}:
        return {"status": "binary_0_censored_1_event", "event_count": values.count("1"), "observed_values": sorted(observed)}
    lowered = {value.lower() for value in observed}
    if lowered <= {"alive", "dead", "censored", "event"}:
        event_count = sum(1 for value in values if value.lower() in {"dead", "event"})
        return {"status": "categorical_alive_dead", "event_count": event_count, "observed_values": sorted(observed)}
    return {"status": "ambiguous", "event_count": 0, "observed_values": sorted(observed)}


def _missingness_report(rows: list[dict[str, str]], fields: list[str]) -> dict[str, Any]:
    return {
        field: {
            "missing_count": sum(1 for row in rows if str(row.get(field) or "").strip() == ""),
            "total_count": len(rows),
        }
        for field in fields
    }


def _survival_id(input_package_id: str) -> str:
    return f"survival-{hashlib.sha1(input_package_id.encode('utf-8')).hexdigest()[:12]}"
