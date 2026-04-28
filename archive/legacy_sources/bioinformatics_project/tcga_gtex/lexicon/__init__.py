"""English lexicon resources for the TCGA/GTEx module."""

from __future__ import annotations

from pathlib import Path

LEXICON_DIR = Path(__file__).resolve().parent
CONCEPT_CATALOG_CSV = LEXICON_DIR / "concept_catalog.csv"
CONCEPT_SOURCE_MAPPINGS_CSV = LEXICON_DIR / "concept_source_mappings.csv"
CHINESE_CONCEPT_TERMS_CSV = LEXICON_DIR / "chinese_concept_terms.csv"
ENGLISH_CORE_TERMS_FULL_CSV = LEXICON_DIR / "english_core_terms_full.csv"
ENGLISH_UI_TERMS_CURATED_CSV = LEXICON_DIR / "english_ui_terms_curated.csv"
ENGLISH_TERM_ALIASES_CSV = LEXICON_DIR / "english_term_aliases.csv"
ENGLISH_CORE_TERMS_CSV = LEXICON_DIR / "english_core_terms.csv"
COLLECTION_NOTES_MD = LEXICON_DIR / "collection_notes.md"

__all__ = [
    "LEXICON_DIR",
    "CONCEPT_CATALOG_CSV",
    "CONCEPT_SOURCE_MAPPINGS_CSV",
    "CHINESE_CONCEPT_TERMS_CSV",
    "ENGLISH_CORE_TERMS_FULL_CSV",
    "ENGLISH_UI_TERMS_CURATED_CSV",
    "ENGLISH_TERM_ALIASES_CSV",
    "ENGLISH_CORE_TERMS_CSV",
    "COLLECTION_NOTES_MD",
]
