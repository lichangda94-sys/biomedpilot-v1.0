"""Chinese term matcher and GEO query builder."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

from disease_terms import DISEASE_TERMS
from exposure_terms import EXPOSURE_TERMS
from molecular_terms import MOLECULAR_TERMS
from population_terms import POPULATION_TERMS
from treatment_terms import TREATMENT_TERMS


DEFAULT_ORGANISM_FILTER = (
    "(Homo sapiens[Organism] OR Mus musculus[Organism] OR Rattus norvegicus[Organism])"
)


@dataclass(frozen=True)
class TermMatch:
    category: str
    canonical: str
    matched_alias: str
    english_terms: tuple[str, ...]


@dataclass(frozen=True)
class QueryBundle:
    raw_query_zh: str
    search_query_en: str
    full_geo_query: str
    disease_matches: tuple[TermMatch, ...]
    exposure_matches: tuple[TermMatch, ...]
    treatment_matches: tuple[TermMatch, ...]
    molecular_matches: tuple[TermMatch, ...]
    population_matches: tuple[TermMatch, ...]


class MeshQueryBuilder:
    """Build GEO-friendly English queries from modular Chinese vocabularies."""

    def __init__(self) -> None:
        self.term_sources = {
            "disease": DISEASE_TERMS,
            "exposure": EXPOSURE_TERMS,
            "treatment": TREATMENT_TERMS,
            "molecular": MOLECULAR_TERMS,
            "population": POPULATION_TERMS,
        }

    def build_query_bundle(self, chinese_query: str) -> QueryBundle:
        normalized = chinese_query.strip()
        if not normalized:
            return QueryBundle(
                raw_query_zh="",
                search_query_en="",
                full_geo_query="",
                disease_matches=(),
                exposure_matches=(),
                treatment_matches=(),
                molecular_matches=(),
                population_matches=(),
            )

        matches = self._extract_grouped_matches(normalized)
        group_queries = []
        for category in ("disease", "exposure", "treatment", "molecular", "population"):
            category_matches = matches[category]
            if category_matches:
                group_queries.append(self._group_to_query(category_matches))

        search_query_en = " AND ".join(group_queries)
        if not search_query_en:
            fallback_tokens = self._fallback_tokens(normalized)
            search_query_en = " AND ".join(f'"{token}"' for token in fallback_tokens)

        if search_query_en:
            full_geo_query = (
                f"({search_query_en}) AND GSE[ETYP] AND {DEFAULT_ORGANISM_FILTER}"
            )
        else:
            full_geo_query = f"GSE[ETYP] AND {DEFAULT_ORGANISM_FILTER}"

        return QueryBundle(
            raw_query_zh=normalized,
            search_query_en=search_query_en,
            full_geo_query=full_geo_query,
            disease_matches=tuple(matches["disease"]),
            exposure_matches=tuple(matches["exposure"]),
            treatment_matches=tuple(matches["treatment"]),
            molecular_matches=tuple(matches["molecular"]),
            population_matches=tuple(matches["population"]),
        )

    def build_query(self, chinese_query: str) -> str:
        return self.build_query_bundle(chinese_query).search_query_en

    def extract_canonical_terms(self, chinese_query: str) -> List[str]:
        bundle = self.build_query_bundle(chinese_query)
        ordered = [
            match.canonical
            for match in (
                list(bundle.disease_matches)
                + list(bundle.exposure_matches)
                + list(bundle.treatment_matches)
                + list(bundle.molecular_matches)
                + list(bundle.population_matches)
            )
        ]
        return ordered

    def debug_groups(self, chinese_query: str) -> Dict[str, List[dict]]:
        bundle = self.build_query_bundle(chinese_query)
        return {
            "disease": [self._match_to_debug_dict(match) for match in bundle.disease_matches],
            "exposure": [self._match_to_debug_dict(match) for match in bundle.exposure_matches],
            "treatment": [self._match_to_debug_dict(match) for match in bundle.treatment_matches],
            "molecular": [self._match_to_debug_dict(match) for match in bundle.molecular_matches],
            "population": [self._match_to_debug_dict(match) for match in bundle.population_matches],
        }

    def _extract_grouped_matches(self, text: str) -> Dict[str, List[TermMatch]]:
        grouped: Dict[str, List[TermMatch]] = {
            "disease": [],
            "exposure": [],
            "treatment": [],
            "molecular": [],
            "population": [],
        }

        for category in ("disease", "exposure", "treatment", "molecular", "population"):
            occupied_ranges: list[tuple[int, int]] = []
            candidates = self._collect_candidates(text, category)
            for candidate in candidates:
                start, end = candidate["start"], candidate["end"]
                if any(not (end <= left or start >= right) for left, right in occupied_ranges):
                    continue
                occupied_ranges.append((start, end))
                grouped[category].append(
                    TermMatch(
                        category=category,
                        canonical=candidate["canonical"],
                        matched_alias=candidate["alias"],
                        english_terms=tuple(candidate["english_terms"]),
                    )
                )

        return grouped

    def _collect_candidates(self, text: str, category: str) -> List[dict]:
        lowered_text = text.lower()
        candidates = []
        for entry in self.term_sources[category]:
            for alias in sorted(set(entry["aliases"]), key=len, reverse=True):
                alias_lower = alias.lower()
                start = lowered_text.find(alias_lower)
                if start < 0:
                    continue
                candidates.append(
                    {
                        "canonical": entry["canonical"],
                        "alias": alias,
                        "english_terms": entry["english_terms"],
                        "start": start,
                        "end": start + len(alias),
                    }
                )
                break

        candidates.sort(key=lambda item: (-(item["end"] - item["start"]), item["start"]))
        return candidates

    @staticmethod
    def _group_to_query(matches: List[TermMatch]) -> str:
        group_blocks = []
        for match in matches:
            joined = " OR ".join(f'"{term}"' for term in match.english_terms)
            group_blocks.append(f"({joined})")
        return " AND ".join(group_blocks)

    @staticmethod
    def _fallback_tokens(chinese_query: str) -> List[str]:
        normalized = re.sub(r"[()（）]", " ", chinese_query)
        normalized = re.sub(r"\b(and|or)\b", " ", normalized, flags=re.I)
        normalized = re.sub(r"[与和及并且还有]+", " ", normalized)
        tokens = re.split(r"[，,、；;：:\s]+", normalized)
        return [token for token in tokens if token]

    @staticmethod
    def _match_to_debug_dict(match: TermMatch) -> dict:
        return {
            "canonical": match.canonical,
            "matched_alias": match.matched_alias,
            "english_terms": list(match.english_terms),
        }
