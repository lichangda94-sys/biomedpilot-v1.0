from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CorrelationPreflightItem:
    accession: str
    expression_files: list[str]
    metadata_files: list[str]
    status: str
    next_action: str


class CorrelationAdapter:
    def build_preflight(self, cleaning_payload: dict[str, object]) -> list[CorrelationPreflightItem]:
        cleaning_items = list(cleaning_payload.get("cleaning_items", []))
        items: list[CorrelationPreflightItem] = []
        for item in cleaning_items:
            item_payload = item if isinstance(item, dict) else {}
            expression_files = _string_list(item_payload.get("expression_files", []))
            metadata_files = _string_list(item_payload.get("metadata_files", []))
            status, next_action = _status_and_action(expression_files=expression_files, metadata_files=metadata_files)
            items.append(
                CorrelationPreflightItem(
                    accession=str(item_payload.get("accession", "")),
                    expression_files=expression_files,
                    metadata_files=metadata_files,
                    status=status,
                    next_action=next_action,
                )
            )
        return items


def _status_and_action(*, expression_files: list[str], metadata_files: list[str]) -> tuple[str, str]:
    if not expression_files:
        return "blocked_no_expression_matrix", "Provide a cleaned expression matrix before correlation analysis."
    if not metadata_files:
        return "blocked_no_sample_annotation", "Provide sample annotation or phenotype variables before correlation analysis."
    return "ready_for_correlation_setup", "Choose target genes, phenotype variables, and correlation method before running analysis."


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []
