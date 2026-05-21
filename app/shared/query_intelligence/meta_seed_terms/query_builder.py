from __future__ import annotations

from app.shared.query_intelligence.meta_seed_terms.loader import load_seed_terms
from app.shared.query_intelligence.meta_seed_terms.models import SeedTerm


def build_pubmed_query_blocks(seed_ids: list[str] | None = None) -> list[str]:
    seeds = _selected_seeds(seed_ids)
    blocks: list[str] = []
    for seed in seeds:
        if seed.concept_type in {"research_intent", "effect_measure"}:
            continue
        if seed.filter_only and seed.concept_type != "study_design":
            continue
        if seed.query_expansion_allowed is False:
            continue
        terms = []
        terms.extend(f'"{term}"[MeSH Terms]' for term in seed.mesh_terms)
        terms.extend(f'"{term}"[Title/Abstract]' for term in seed.pubmed_free_text_terms)
        terms = _unique(terms)
        if terms:
            blocks.append("(" + " OR ".join(terms) + ")")
    return blocks


def _selected_seeds(seed_ids: list[str] | None) -> list[SeedTerm]:
    seeds = list(load_seed_terms())
    if seed_ids is None:
        return seeds
    wanted = set(seed_ids)
    return [seed for seed in seeds if seed.concept_id in wanted]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result
