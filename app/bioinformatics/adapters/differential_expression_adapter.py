from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DifferentialExpressionPreflightItem:
    accession: str
    expression_files: list[str]
    metadata_files: list[str]
    has_group_assignment: bool
    has_case_group: bool
    has_control_group: bool
    status: str
    next_action: str


class DifferentialExpressionAdapter:
    def build_preflight(self, grouping_payload: dict[str, object]) -> list[DifferentialExpressionPreflightItem]:
        grouping_items = list(grouping_payload.get("grouping_items", []))
        items: list[DifferentialExpressionPreflightItem] = []
        for item in grouping_items:
            item_payload = item if isinstance(item, dict) else {}
            expression_files = _string_list(item_payload.get("expression_files", []))
            metadata_files = _string_list(item_payload.get("metadata_files", []))
            group_labels = _group_labels(item_payload)
            has_group_assignment = bool(group_labels)
            has_case_group = _has_label(group_labels, ("case", "tumor", "disease", "ptc", "treated"))
            has_control_group = _has_label(group_labels, ("control", "normal", "healthy", "untreated"))
            status, next_action = _status_and_action(
                expression_files=expression_files,
                metadata_files=metadata_files,
                has_group_assignment=has_group_assignment,
                has_case_group=has_case_group,
                has_control_group=has_control_group,
            )
            items.append(
                DifferentialExpressionPreflightItem(
                    accession=str(item_payload.get("accession", "")),
                    expression_files=expression_files,
                    metadata_files=metadata_files,
                    has_group_assignment=has_group_assignment,
                    has_case_group=has_case_group,
                    has_control_group=has_control_group,
                    status=status,
                    next_action=next_action,
                )
            )
        return items


def _status_and_action(
    *,
    expression_files: list[str],
    metadata_files: list[str],
    has_group_assignment: bool,
    has_case_group: bool,
    has_control_group: bool,
) -> tuple[str, str]:
    if not expression_files:
        return "blocked_no_expression_matrix", "Provide a cleaned expression matrix before differential analysis."
    if not metadata_files:
        return "blocked_no_sample_annotation", "Provide sample annotation before differential analysis."
    if not has_group_assignment:
        return "blocked_no_group_assignment", "Assign case/control groups in the sample grouping step."
    if not has_case_group or not has_control_group:
        return "blocked_no_case_control_groups", "Confirm both case and control groups before running statistics."
    return "ready_for_deg_runner", "Review parameters and choose a statistical engine before running formal DEG."


def _group_labels(item_payload: dict[str, object]) -> list[str]:
    labels: list[str] = []
    group_assignments = item_payload.get("group_assignments")
    if isinstance(group_assignments, dict):
        labels.extend(str(value) for value in group_assignments.values())
    sample_groups = item_payload.get("sample_groups")
    if isinstance(sample_groups, list):
        for sample_group in sample_groups:
            if isinstance(sample_group, dict):
                labels.append(str(sample_group.get("group", "")))
            else:
                labels.append(str(sample_group))
    comparison_groups = item_payload.get("comparison_groups")
    if isinstance(comparison_groups, dict):
        labels.extend(str(value) for value in comparison_groups.values())
    for key in ("case_group", "control_group"):
        if item_payload.get(key):
            labels.append(str(item_payload[key]))
    return [label.strip().lower() for label in labels if label and str(label).strip()]


def _has_label(labels: list[str], candidates: tuple[str, ...]) -> bool:
    return any(any(candidate in label for candidate in candidates) for label in labels)


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []
