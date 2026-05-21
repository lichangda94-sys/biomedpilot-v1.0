from __future__ import annotations

from typing import Any


def event_coding(values: list[object]) -> dict[str, Any]:
    observed = [str(value).strip() for value in values if str(value).strip() != ""]
    unique = sorted(set(observed))
    if not observed:
        return {"status": "missing", "event_count": 0, "censored_count": 0, "observed_values": []}
    if set(unique) <= {"0", "1"}:
        return {"status": "binary_0_censored_1_event", "event_count": observed.count("1"), "censored_count": observed.count("0"), "observed_values": unique, "event_1_meaning": "event/death", "event_0_meaning": "censored/alive"}
    lowered = [value.lower() for value in observed]
    lowered_set = set(lowered)
    if lowered_set <= {"alive", "dead", "censored", "event", "deceased", "living"}:
        event_count = sum(1 for value in lowered if value in {"dead", "event", "deceased"})
        censored_count = sum(1 for value in lowered if value in {"alive", "censored", "living"})
        return {"status": "categorical_alive_dead", "event_count": event_count, "censored_count": censored_count, "observed_values": unique, "event_1_meaning": "dead/event/deceased", "event_0_meaning": "alive/censored/living"}
    return {"status": "ambiguous", "event_count": 0, "censored_count": 0, "observed_values": unique}


def derive_os_time(row: dict[str, str]) -> tuple[str, list[str]]:
    death = _number(row.get("days_to_death"))
    follow = _number(row.get("days_to_last_follow_up") or row.get("last_follow_up") or row.get("follow_up_time"))
    if death is not None:
        return str(death).rstrip("0").rstrip(".") if "." in str(death) else str(int(death)), ["days_to_death"]
    if follow is not None:
        return str(follow).rstrip("0").rstrip(".") if "." in str(follow) else str(int(follow)), ["days_to_last_follow_up"]
    return "", []


def derive_os_event(row: dict[str, str]) -> tuple[str, list[str]]:
    for field in ("vital_status", "death_status"):
        value = str(row.get(field) or "").strip().lower()
        if value in {"dead", "deceased", "event"}:
            return "1", [field]
        if value in {"alive", "living", "censored"}:
            return "0", [field]
    return "", []


def _number(value: object) -> float | None:
    try:
        text = str(value or "").strip()
        if not text:
            return None
        return float(text)
    except (TypeError, ValueError):
        return None
