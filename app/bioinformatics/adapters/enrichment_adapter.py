from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EnrichmentPreflightItem:
    accession: str
    deg_result_files: list[str]
    upregulated_gene_count: int
    downregulated_gene_count: int
    status: str
    next_action: str


class EnrichmentAdapter:
    def build_preflight(self, deg_payload: dict[str, object]) -> list[EnrichmentPreflightItem]:
        source_items = list(deg_payload.get("preflight_items", []))
        items: list[EnrichmentPreflightItem] = []
        for item in source_items:
            item_payload = item if isinstance(item, dict) else {}
            deg_result_files = _string_list(item_payload.get("deg_result_files", []))
            up_count = _safe_int(item_payload.get("upregulated_gene_count", 0))
            down_count = _safe_int(item_payload.get("downregulated_gene_count", 0))
            status, next_action = _status_and_action(
                deg_result_files=deg_result_files,
                upregulated_gene_count=up_count,
                downregulated_gene_count=down_count,
            )
            items.append(
                EnrichmentPreflightItem(
                    accession=str(item_payload.get("accession", "")),
                    deg_result_files=deg_result_files,
                    upregulated_gene_count=up_count,
                    downregulated_gene_count=down_count,
                    status=status,
                    next_action=next_action,
                )
            )
        return items


def _status_and_action(
    *,
    deg_result_files: list[str],
    upregulated_gene_count: int,
    downregulated_gene_count: int,
) -> tuple[str, str]:
    if not deg_result_files and upregulated_gene_count == 0 and downregulated_gene_count == 0:
        return "blocked_no_deg_results", "Run or import a confirmed DEG result before enrichment analysis."
    if upregulated_gene_count + downregulated_gene_count == 0:
        return "blocked_no_gene_lists", "Provide up/down gene lists before enrichment analysis."
    return "ready_for_enrichment_runner", "Review ontology/database settings before running enrichment."


def _safe_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []
