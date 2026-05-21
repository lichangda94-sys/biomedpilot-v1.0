from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

from .censoring import derive_os_event, derive_os_time, event_coding
from .models import EVENT_FIELD_CANDIDATES, SURVIVAL_OUTCOME_GATE_SCHEMA_VERSION, TIME_FIELD_CANDIDATES, utc_now


DEFAULT_MINIMUM_EVENT_COUNT = 5
DEFAULT_MISSING_WARNING_RATE = 0.3
DEFAULT_MISSING_BLOCKER_RATE = 0.5


def build_survival_outcome_gate(
    project_root: str | Path,
    survival_input: dict[str, Any],
    *,
    time_field: str | None = None,
    event_field: str | None = None,
    time_unit: str = "days",
    minimum_event_count: int = DEFAULT_MINIMUM_EVENT_COUNT,
    maximum_missing_rate_warning: float = DEFAULT_MISSING_WARNING_RATE,
    maximum_missing_rate_blocker: float = DEFAULT_MISSING_BLOCKER_RATE,
) -> dict[str, Any]:
    root = Path(project_root).expanduser().resolve()
    rows = _read_table(_clinical_path(root, survival_input))
    fields = list(rows[0].keys()) if rows else []
    selected_time = time_field or _first_field(fields, TIME_FIELD_CANDIDATES)
    selected_event = event_field or _first_field(fields, EVENT_FIELD_CANDIDATES)
    derived_time = False
    derived_event = False
    time_sources: list[str] = []
    event_sources: list[str] = []
    time_values: list[str] = []
    event_values: list[str] = []
    for row in rows:
        time_value = str(row.get(selected_time) or "").strip() if selected_time else ""
        if selected_time and selected_time.lower() not in {"os_time", "overall_survival_time", "time"}:
            derived_time = True
            time_sources.append(selected_time)
        if not time_value:
            time_value, used = derive_os_time(row)
            if used:
                derived_time = True
                time_sources.extend(used)
        event_value = str(row.get(selected_event) or "").strip() if selected_event else ""
        if selected_event and selected_event.lower() in {"vital_status", "death_status"}:
            derived_event = True
            event_sources.append(selected_event)
        if not event_value:
            event_value, used = derive_os_event(row)
            if used:
                derived_event = True
                event_sources.extend(used)
        time_values.append(time_value)
        event_values.append(event_value)
    coding = event_coding(event_values)
    numeric_times = [_number(value) for value in time_values if str(value).strip()]
    numeric_present = [value for value in numeric_times if value is not None]
    blockers = [str(item) for item in survival_input.get("blockers", []) or [] if str(item) == "case_sample_mapping_failed"]
    warnings: list[str] = []
    missing_time_count = sum(1 for value in time_values if str(value).strip() == "")
    missing_event_count = sum(1 for value in event_values if str(value).strip() == "")
    sample_count = len(rows)
    if not rows:
        blockers.append("missing_clinical_rows")
    if not selected_time and not derived_time:
        blockers.append("missing_time_field")
    if not selected_event and not derived_event:
        blockers.append("missing_event_field")
    if not time_unit:
        blockers.append("missing_time_unit")
    if coding["status"] in {"missing", "ambiguous"}:
        blockers.append("ambiguous_event_coding" if coding["status"] == "ambiguous" else "all_event_missing")
    if missing_time_count == sample_count and sample_count:
        blockers.append("all_time_missing")
    if missing_event_count == sample_count and sample_count:
        blockers.append("all_event_missing")
    if any((value or 0) < 0 for value in numeric_present):
        blockers.append("negative_survival_time")
    if int(coding.get("event_count") or 0) == 0 and sample_count:
        blockers.append("no_events")
    if 0 < int(coding.get("event_count") or 0) < minimum_event_count:
        warnings.append("low_event_count")
    for name, count in (("time", missing_time_count), ("event", missing_event_count)):
        rate = count / sample_count if sample_count else 0.0
        if rate > maximum_missing_rate_blocker:
            blockers.append(f"high_missing_{name}_rate")
        elif rate > maximum_missing_rate_warning:
            warnings.append(f"high_missing_{name}_rate")
    zero_time_count = sum(1 for value in numeric_present if value == 0)
    if sample_count and zero_time_count / sample_count > 0.2:
        warnings.append("many_zero_survival_times")
    if derived_time:
        warnings.append("derived_os_time_requires_user_review")
    if derived_event:
        warnings.append("derived_os_event_requires_user_review")
    return {
        "schema_version": SURVIVAL_OUTCOME_GATE_SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": "passed" if not blockers else "blocked",
        "survival_outcome_gate_id": _gate_id(survival_input.get("survival_clinical_input_id"), selected_time, selected_event),
        "survival_clinical_input_id": str(survival_input.get("survival_clinical_input_id") or ""),
        "time_field": selected_time,
        "event_field": selected_event,
        "time_unit": time_unit,
        "event_coding": coding,
        "censoring_policy": "event=1 means observed event/death; event=0 means censored/alive; ambiguous coding blocks",
        "derived_os_time_policy": {"derived": derived_time, "source_fields": sorted(set(time_sources)), "rule": "days_to_death else days_to_last_follow_up"},
        "derived_os_event_policy": {"derived": derived_event, "source_fields": sorted(set(event_sources)), "rule": "dead/deceased/event -> 1; alive/living/censored -> 0"},
        "sample_count": sample_count,
        "event_count": int(coding.get("event_count") or 0),
        "censored_count": int(coding.get("censored_count") or 0),
        "missing_time_count": missing_time_count,
        "missing_event_count": missing_event_count,
        "negative_time_count": sum(1 for value in numeric_present if value < 0),
        "zero_time_count": zero_time_count,
        "time_summary": _numeric_summary(numeric_present),
        "event_summary": {"observed_values": coding.get("observed_values", []), "status": coding.get("status", "")},
        "warnings": list(dict.fromkeys([*warnings, *[str(item) for item in survival_input.get("warnings", []) or []]])),
        "blockers": list(dict.fromkeys(blockers)),
        "provenance": {"clinical_asset": survival_input.get("clinical_asset", {}), "no_formal_statistics": True},
    }


def _clinical_path(root: Path, survival_input: dict[str, Any]) -> Path | None:
    asset = survival_input.get("clinical_asset") if isinstance(survival_input.get("clinical_asset"), dict) else {}
    value = str(asset.get("path") or "")
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


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


def _first_field(fields: list[str], candidates: tuple[str, ...]) -> str:
    lowered = {field.lower(): field for field in fields}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return ""


def _number(value: object) -> float | None:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None


def _numeric_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    return {"count": len(values), "min": ordered[0], "max": ordered[-1], "median": ordered[len(ordered) // 2]}


def _gate_id(*values: object) -> str:
    raw = "|".join(str(value or "") for value in values)
    return f"survival-outcome-{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:12]}"
