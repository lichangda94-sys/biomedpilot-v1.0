from __future__ import annotations

from .models import UnifiedDatasetCandidate


class DatasetCandidateRanker:
    def rank(self, candidates: tuple[UnifiedDatasetCandidate, ...] | list[UnifiedDatasetCandidate]) -> tuple[UnifiedDatasetCandidate, ...]:
        return tuple(sorted(candidates, key=lambda item: (item.score, _sample_count_value(item.sample_count)), reverse=True))


def _sample_count_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
