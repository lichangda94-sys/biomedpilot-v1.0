from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleGroupingPlanItem:
    accession: str
    expression_files: list[str]
    metadata_files: list[str]
    status: str
    next_action: str


class SampleGroupingAdapter:
    def build_grouping_plan(self, cleaning_payload: dict[str, object]) -> list[SampleGroupingPlanItem]:
        cleaning_items = list(cleaning_payload.get("cleaning_items", []))
        items: list[SampleGroupingPlanItem] = []
        for item in cleaning_items:
            item_payload = item if isinstance(item, dict) else {}
            expression_files = _string_list(item_payload.get("expression_files", []))
            metadata_files = _string_list(item_payload.get("metadata_files", []))
            status = "ready_for_manual_grouping" if metadata_files else "blocked_no_sample_annotation"
            next_action = (
                "Review sample annotation columns and assign case/control groups."
                if metadata_files
                else "Provide sample annotation metadata before grouping; do not run differential analysis yet."
            )
            items.append(
                SampleGroupingPlanItem(
                    accession=str(item_payload.get("accession", "")),
                    expression_files=expression_files,
                    metadata_files=metadata_files,
                    status=status,
                    next_action=next_action,
                )
            )
        return items


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []
