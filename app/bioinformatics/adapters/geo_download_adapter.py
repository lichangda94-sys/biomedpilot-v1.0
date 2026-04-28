from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.bioinformatics.adapters.legacy_geo import LegacyGeoAdapter


@dataclass(frozen=True)
class GeoDownloadPlanItem:
    accession: str
    target_dir: str
    status: str
    note: str


class GeoDownloadAdapter:
    def build_download_plan(self, *, project_id: str, query_plan_payload: dict[str, object], download_root: Path) -> list[GeoDownloadPlanItem]:
        plan = query_plan_payload.get("plan")
        plan_payload = plan if isinstance(plan, dict) else {}
        accessions = list(plan_payload.get("accessions", []))
        if not accessions:
            query_text = str(plan_payload.get("query_text", ""))
            accessions = LegacyGeoAdapter().parse_accessions(query_text)
        items: list[GeoDownloadPlanItem] = []
        for accession in accessions:
            normalized = str(accession).strip().upper()
            if not normalized:
                continue
            target_dir = download_root / normalized
            items.append(
                GeoDownloadPlanItem(
                    accession=normalized,
                    target_dir=str(target_dir),
                    status="planned",
                    note="Download not executed. Requires explicit user confirmation.",
                )
            )
        return items
