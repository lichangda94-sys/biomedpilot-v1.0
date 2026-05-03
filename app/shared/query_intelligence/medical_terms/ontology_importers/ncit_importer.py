from __future__ import annotations

from app.shared.query_intelligence.medical_terms.ontology_importers.index_builder import OntologyImporter


class NcitImporter(OntologyImporter):
    def __init__(self, version: str = "") -> None:
        super().__init__(source_name="NCIt", license="CC BY 4.0", version=version)
