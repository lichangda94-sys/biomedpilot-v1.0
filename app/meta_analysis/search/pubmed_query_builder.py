from __future__ import annotations

from app.meta_analysis.search.search_strategy_models import MetaConceptGroupDraft


def build_pubmed_query_draft(concept_groups: tuple[MetaConceptGroupDraft, ...]) -> str:
    blocks: list[str] = []
    for group in concept_groups:
        terms = [*_mesh_terms(group.mesh_terms), *_tiab_terms(group.terms_en)]
        block = _or_block(terms)
        if block:
            blocks.append(block)
    return " AND ".join(blocks)


def _mesh_terms(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f'{_quote(value)}[Mesh]' for value in values if value)


def _tiab_terms(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f'{_quote(value)}[tiab]' for value in values if value)


def _or_block(values: object) -> str:
    terms = _unique(values)
    if not terms:
        return ""
    if len(terms) == 1:
        return terms[0]
    return "(" + " OR ".join(terms) + ")"


def _quote(value: str) -> str:
    text = value.strip().strip('"')
    return f'"{text}"'


def _unique(values: object) -> tuple[str, ...]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:  # type: ignore[union-attr]
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            items.append(text)
    return tuple(items)
