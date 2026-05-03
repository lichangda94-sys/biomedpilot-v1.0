from __future__ import annotations

from .models import UnifiedDatasetCandidate


class DatasetCandidateNormalizer:
    def normalize(self, candidates: tuple[UnifiedDatasetCandidate, ...] | list[UnifiedDatasetCandidate]) -> tuple[UnifiedDatasetCandidate, ...]:
        return tuple(candidates)
