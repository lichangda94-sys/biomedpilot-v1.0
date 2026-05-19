from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.shared.query_intelligence.meta_seed_terms.models import SeedTerm


DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "medical_terms" / "meta_analysis"
SEED_PATH = DATA_DIR / "meta_seed_terms.json"
SCHEMA_PATH = DATA_DIR / "meta_seed_terms_schema.json"


@lru_cache(maxsize=1)
def load_seed_terms() -> tuple[SeedTerm, ...]:
    payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return tuple(SeedTerm.from_dict(row) for row in payload)


@lru_cache(maxsize=1)
def load_mesh_mappings() -> dict[str, dict[str, object]]:
    return _load_mapping("mesh_mappings.json")


@lru_cache(maxsize=1)
def load_pubmed_free_text_mappings() -> dict[str, dict[str, object]]:
    return _load_mapping("pubmed_free_text_mappings.json")


@lru_cache(maxsize=1)
def load_emtree_mappings() -> dict[str, dict[str, object]]:
    return _load_mapping("emtree_mappings.json")


def validate_seed_terms(
    seeds: tuple[SeedTerm, ...] | None = None,
    *,
    schema_path: Path = SCHEMA_PATH,
) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    required = set(schema["items"]["required"])
    allowed_types = set(schema["items"]["properties"]["concept_type"]["enum"])
    allowed_emtree_status = set(schema["items"]["properties"]["emtree_review_status"]["enum"])
    rows = seeds or load_seed_terms()
    errors: list[str] = []
    seen: set[str] = set()
    for seed in rows:
        payload = seed.__dict__
        missing = sorted(required - set(payload))
        if missing:
            errors.append(f"{seed.concept_id}: missing {missing}")
        if seed.concept_id in seen:
            errors.append(f"{seed.concept_id}: duplicate concept_id")
        seen.add(seed.concept_id)
        if seed.concept_type not in allowed_types:
            errors.append(f"{seed.concept_id}: invalid concept_type={seed.concept_type}")
        if seed.emtree_review_status not in allowed_emtree_status:
            errors.append(f"{seed.concept_id}: invalid emtree_review_status={seed.emtree_review_status}")
        if seed.concept_type == "outcome" and seed.query_expansion_allowed != "conditional":
            errors.append(f"{seed.concept_id}: outcome must use conditional query expansion")
        if seed.concept_type in {"research_intent", "effect_measure"} and seed.query_expansion_allowed is not False:
            errors.append(f"{seed.concept_id}: intent/effect must not expand query")
    return errors


def _load_mapping(filename: str) -> dict[str, dict[str, object]]:
    payload = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
    return {str(row["concept_id"]): row for row in payload}
