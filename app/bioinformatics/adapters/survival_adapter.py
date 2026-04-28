from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SurvivalPreflightItem:
    accession: str
    metadata_files: list[str]
    survival_fields: list[str]
    has_time_field: bool
    has_event_field: bool
    status: str
    next_action: str


class SurvivalAdapter:
    def build_preflight(self, cleaning_payload: dict[str, object]) -> list[SurvivalPreflightItem]:
        cleaning_items = list(cleaning_payload.get("cleaning_items", []))
        items: list[SurvivalPreflightItem] = []
        for item in cleaning_items:
            item_payload = item if isinstance(item, dict) else {}
            metadata_files = _string_list(item_payload.get("metadata_files", []))
            survival_fields = _string_list(item_payload.get("survival_fields", []))
            has_time_field = _has_field(survival_fields, ("time", "days", "os_time", "followup", "follow_up"))
            has_event_field = _has_field(survival_fields, ("event", "status", "death", "vital"))
            status, next_action = _status_and_action(
                metadata_files=metadata_files,
                has_time_field=has_time_field,
                has_event_field=has_event_field,
            )
            items.append(
                SurvivalPreflightItem(
                    accession=str(item_payload.get("accession", "")),
                    metadata_files=metadata_files,
                    survival_fields=survival_fields,
                    has_time_field=has_time_field,
                    has_event_field=has_event_field,
                    status=status,
                    next_action=next_action,
                )
            )
        return items


def _status_and_action(*, metadata_files: list[str], has_time_field: bool, has_event_field: bool) -> tuple[str, str]:
    if not metadata_files:
        return "blocked_no_clinical_metadata", "Provide clinical metadata before survival analysis."
    if not has_time_field or not has_event_field:
        return "blocked_no_survival_fields", "Map survival time and event/status fields before running survival analysis."
    return "ready_for_survival_setup", "Review endpoint definitions and censoring rules before running survival analysis."


def _has_field(fields: list[str], candidates: tuple[str, ...]) -> bool:
    normalized = [field.lower() for field in fields]
    return any(any(candidate in field for candidate in candidates) for field in normalized)


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []
