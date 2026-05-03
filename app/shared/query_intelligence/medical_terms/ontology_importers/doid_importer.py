from __future__ import annotations

from app.shared.query_intelligence.medical_terms.ontology_importers.index_builder import OntologyImporter


class DoidImporter(OntologyImporter):
    def __init__(self, version: str = "") -> None:
        super().__init__(source_name="DOID", license="CC0", version=version)
