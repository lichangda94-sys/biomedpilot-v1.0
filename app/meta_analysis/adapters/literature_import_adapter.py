from __future__ import annotations

from pathlib import Path
from app.meta_analysis.literature_import_core import ImportAdapterResult, parse_literature_file


class LiteratureImportAdapter:
    def parse_file(self, source_path: Path, project_id: str, source_type: str) -> ImportAdapterResult:
        return parse_literature_file(source_path, project_id, source_type)
