from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.shared.query_intelligence.medical_terms.term_index_models import TermConcept


@dataclass(frozen=True)
class OntologyImporter:
    source_name: str
    license: str
    version: str = ""

    def load(self, source_path: Path) -> tuple[TermConcept, ...]:
        raise NotImplementedError("Ontology import is reserved for a later stage.")


def build_term_index_from_sources(_sources: list[Path] | None = None) -> tuple[TermConcept, ...]:
    return ()
