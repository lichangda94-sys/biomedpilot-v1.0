from __future__ import annotations

from .models import UnifiedDatasetCandidate


class AcquisitionHandoffBuilder:
    def build_metadata(self, candidate: UnifiedDatasetCandidate, *, source_query: str = "") -> dict[str, object]:
        return {
            "source": candidate.source,
            "accession_or_project": candidate.accession_or_project,
            "display_title": candidate.display_title,
            "source_query": source_query,
            "download_plan_available": candidate.download_plan_available,
            "recommended_analyses": list(candidate.recommended_analyses),
            "warnings": list(candidate.warnings),
            "source_specific_metadata": candidate.source_specific_metadata,
            "acquisition_status": "pending_download" if candidate.download_plan_available else "requires_manual_review",
            "next_recommended_stage": "acquisition_download" if candidate.download_plan_available else "manual_source_review",
        }
