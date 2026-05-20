from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Literal

from .term_index_loader import default_mini_index_path


MedicalTermScope = Literal["shared_core", "meta_analysis", "bioinformatics"]


@dataclass(frozen=True)
class ScopedMedicalTerm:
    concept_id: str
    preferred_label_en: str
    concept_type: str
    source: str
    active_scope: str
    terms: tuple[str, ...] = ()
    scope: dict[str, bool] = field(default_factory=dict)
    usage: dict[str, object] = field(default_factory=dict)
    legacy_concept_ids: tuple[str, ...] = ()

    def matches(self, value: str) -> bool:
        lowered = value.lower()
        return lowered == self.preferred_label_en.lower() or lowered in {term.lower() for term in self.terms}


@dataclass(frozen=True)
class LegacyConceptResolution:
    requested_concept_id: str
    resolved_concept_id: str
    scope: str
    active: bool
    source: str
    reason: str = ""


DATA_DIR = Path(__file__).resolve().parents[4] / "data" / "medical_terms"
BIO_DIR = DATA_DIR / "bioinformatics"
META_DIR = DATA_DIR / "meta_analysis"
MIGRATED_META_PATH = META_DIR / "meta_migrated_from_shared_terms.json"
COMPATIBILITY_PATH = META_DIR / "legacy_meta_compatibility_map.json"
META_SEED_PATH = META_DIR / "meta_seed_terms.json"


def load_terms(scope: MedicalTermScope = "shared_core") -> tuple[ScopedMedicalTerm, ...]:
    if scope not in {"shared_core", "meta_analysis", "bioinformatics"}:
        raise ValueError(f"Unsupported medical term scope: {scope}")
    compatibility = _load_compatibility_by_legacy_id()
    shared = _load_shared_terms(active_scope=scope, excluded_legacy_ids=frozenset(compatibility))
    if scope == "shared_core":
        return shared
    if scope == "meta_analysis":
        return _unique_by_concept_id((*shared, *_load_meta_seed_terms(), *_load_meta_migrated_terms()))
    return (*shared, *_load_bioinformatics_terms())


def resolve_legacy_concept_id(concept_id: str, scope: MedicalTermScope = "shared_core") -> LegacyConceptResolution | None:
    if scope not in {"shared_core", "meta_analysis", "bioinformatics"}:
        raise ValueError(f"Unsupported medical term scope: {scope}")
    compatibility = _load_compatibility_by_legacy_id()
    if scope == "meta_analysis" and concept_id in compatibility:
        mapping = compatibility[concept_id]
        return LegacyConceptResolution(
            requested_concept_id=concept_id,
            resolved_concept_id=str(mapping["new_concept_id"]),
            scope=scope,
            active=True,
            source="legacy_meta_compatibility_map",
            reason="legacy mini concept mapped to Meta scoped mirror",
        )
    if concept_id in compatibility:
        return LegacyConceptResolution(
            requested_concept_id=concept_id,
            resolved_concept_id="",
            scope=scope,
            active=False,
            source="legacy_meta_compatibility_map",
            reason="legacy Meta concept is not active in this scope",
        )
    if any(term.concept_id == concept_id for term in load_terms(scope)):
        return LegacyConceptResolution(
            requested_concept_id=concept_id,
            resolved_concept_id=concept_id,
            scope=scope,
            active=True,
            source="scope_terms",
            reason="concept is active in requested scope",
        )
    return None


def find_terms(query: str, scope: MedicalTermScope = "shared_core") -> tuple[ScopedMedicalTerm, ...]:
    return tuple(term for term in load_terms(scope) if term.matches(query))


@lru_cache(maxsize=3)
def _load_shared_terms(active_scope: str, excluded_legacy_ids: frozenset[str]) -> tuple[ScopedMedicalTerm, ...]:
    excluded = set(excluded_legacy_ids)
    rows = _read_json(default_mini_index_path())
    if not isinstance(rows, list):
        return ()
    terms: list[ScopedMedicalTerm] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        concept_id = str(row.get("concept_id") or "")
        if concept_id in excluded:
            continue
        if active_scope in {"meta_analysis", "bioinformatics"} and _is_legacy_meta_scoped_shared_row(row):
            continue
        if active_scope == "meta_analysis" and _is_bioinformatics_scoped_shared_row(row):
            continue
        terms.append(
            ScopedMedicalTerm(
                concept_id=concept_id,
                preferred_label_en=str(row.get("preferred_label_en") or ""),
                concept_type=str(row.get("concept_type") or ""),
                source="mini_medical_terms_index",
                active_scope=active_scope,
                terms=tuple(_row_terms(row)),
                scope={
                    "shared_core_allowed": True,
                    "bioinformatics_allowed": active_scope == "bioinformatics",
                    "meta_analysis_allowed": active_scope == "meta_analysis",
                },
                usage={},
            )
        )
    return tuple(terms)


@lru_cache(maxsize=1)
def _load_meta_seed_terms() -> tuple[ScopedMedicalTerm, ...]:
    payload = _read_json(META_SEED_PATH)
    if not isinstance(payload, list):
        return ()
    result: list[ScopedMedicalTerm] = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        result.append(
            ScopedMedicalTerm(
                concept_id=str(row.get("concept_id") or ""),
                preferred_label_en=str(row.get("preferred_label_en") or ""),
                concept_type=str(row.get("concept_type") or ""),
                source="meta_seed_terms",
                active_scope="meta_analysis",
                terms=tuple(_row_terms(row)),
                scope={
                    "shared_core_allowed": False,
                    "bioinformatics_allowed": False,
                    "meta_analysis_allowed": True,
                },
                usage={
                    "query_expansion_allowed": row.get("query_expansion_allowed"),
                    "standalone_search_allowed": row.get("standalone_search_allowed"),
                    "filter_only": row.get("filter_only"),
                    "pdf_extraction_target": row.get("pdf_extraction_target"),
                },
            )
        )
    return tuple(result)


@lru_cache(maxsize=1)
def _load_meta_migrated_terms() -> tuple[ScopedMedicalTerm, ...]:
    payload = _read_json(MIGRATED_META_PATH)
    if not isinstance(payload, dict):
        return ()
    result: list[ScopedMedicalTerm] = []
    for row in payload.get("terms", []):
        if not isinstance(row, dict):
            continue
        result.append(
            ScopedMedicalTerm(
                concept_id=str(row.get("concept_id") or ""),
                preferred_label_en=str(row.get("preferred_label_en") or ""),
                concept_type=str(row.get("concept_type") or ""),
                source="meta_migrated_from_shared_terms",
                active_scope="meta_analysis",
                terms=tuple(_row_terms(row)),
                scope=dict(row.get("scope") or {}),
                usage=dict(row.get("usage") or {}),
                legacy_concept_ids=tuple(str(item) for item in row.get("legacy_concept_ids", []) if str(item)),
            )
        )
    return tuple(result)


@lru_cache(maxsize=1)
def _load_bioinformatics_terms() -> tuple[ScopedMedicalTerm, ...]:
    terms: list[ScopedMedicalTerm] = []
    for path in sorted(BIO_DIR.glob("bioinformatics_*_terms.json")):
        payload = _read_json(path)
        if not isinstance(payload, dict):
            continue
        for row in payload.get("terms", []):
            if not isinstance(row, dict):
                continue
            preferred = str(row.get("preferred_label") or row.get("term") or "")
            concept_id = str(row.get("concept_id") or f"bio_stop:{preferred}")
            terms.append(
                ScopedMedicalTerm(
                    concept_id=concept_id,
                    preferred_label_en=preferred,
                    concept_type=str(row.get("concept_type") or row.get("term_type") or ""),
                    source=path.name,
                    active_scope="bioinformatics",
                    terms=tuple(_row_terms(row)),
                    scope={
                        "shared_core_allowed": bool(row.get("shared_core_allowed", False)),
                        "bioinformatics_allowed": True,
                        "meta_analysis_allowed": bool(row.get("meta_scope_allowed", False)),
                    },
                    usage={
                        "standalone_search_allowed": row.get("standalone_search_allowed"),
                        "global_stop_word": row.get("global_stop_word"),
                    },
                )
            )
    return tuple(terms)


@lru_cache(maxsize=1)
def _load_compatibility_by_legacy_id() -> dict[str, dict[str, object]]:
    payload = _read_json(COMPATIBILITY_PATH)
    if not isinstance(payload, dict):
        return {}
    result: dict[str, dict[str, object]] = {}
    for row in payload.get("mappings", []):
        if not isinstance(row, dict):
            continue
        for legacy_id in row.get("legacy_concept_ids", []):
            result[str(legacy_id)] = row
    return result


def _read_json(path: Path) -> object:
    if not path.exists():
        return {} if path.suffix == ".json" else []
    return json.loads(path.read_text(encoding="utf-8"))


def _row_terms(row: dict[str, object]) -> list[str]:
    values: list[str] = []
    keys = (
        "term",
        "preferred_label",
        "preferred_label_en",
        "preferred_zh",
        "zh_terms",
        "synonyms",
        "synonyms_en",
        "exact_synonyms_en",
        "related_synonyms_en",
        "abbreviations",
        "mesh_terms",
        "normalized_terms",
        "zh_entry_terms",
        "gtex_subtype_mappings",
    )
    for key in keys:
        value = row.get(key)
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    values.append(item)
                elif isinstance(item, dict):
                    values.extend(str(nested) for nested in item.values() if isinstance(nested, str))
    return _unique(values)


def _is_legacy_meta_scoped_shared_row(row: dict[str, object]) -> bool:
    concept_id = str(row.get("concept_id") or "")
    concept_type = str(row.get("concept_type") or "")
    category = str(row.get("category") or "")
    return (
        concept_id.startswith("mini:meta_analysis_")
        or category == "meta_analysis_term"
        or concept_type
        in {
            "pico_term",
            "effect_measure",
            "outcome",
            "study_design",
            "publication_type",
            "diagnostic_accuracy",
            "exclusion_type",
            "quality_assessment",
        }
    )


def _is_bioinformatics_scoped_shared_row(row: dict[str, object]) -> bool:
    return str(row.get("concept_type") or "") == "data_modality"


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        value = value.strip()
        lowered = value.lower()
        if value and lowered not in seen:
            seen.add(lowered)
            result.append(value)
    return result


def _unique_by_concept_id(terms: tuple[ScopedMedicalTerm, ...]) -> tuple[ScopedMedicalTerm, ...]:
    result: dict[str, ScopedMedicalTerm] = {}
    for term in terms:
        if term.concept_id:
            result[term.concept_id] = term
    return tuple(result.values())
