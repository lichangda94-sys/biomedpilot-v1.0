from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.services.literature_import_service import LiteratureImportService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "literature"


def test_endnote_ris_profile_imports_endnote_aliases_and_notes(tmp_path: Path) -> None:
    service = LiteratureImportService(
        task_center=TaskCenter(tmp_path / "tasks" / "tasks.json"),
        data_center=DataCenter(tmp_path / "data" / "data_assets.json"),
        storage_root=tmp_path,
    )

    result = service.import_file(project_id="meta-endnote", source_path=str(FIXTURES / "endnote_export.ris"))

    assert result.success, result.message
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    diagnostics = json.loads(Path(str(result.details["diagnostics_path"])).read_text(encoding="utf-8"))
    record = payload["records"][0]
    assert record["source_record_id"] == "ENW-001"
    assert record["title"] == "EndNote Exported Placebo Controlled Trial"
    assert record["authors"] == ["Garcia, Maria", "Patel, Arun"]
    assert record["first_author"] == "Maria Garcia"
    assert record["journal"] == "EndNote Clinical Journal"
    assert record["year"] == 2023
    assert record["doi"] == "10.1000/endnote.001"
    assert record["pmid"] == "22222222"
    assert record["abstract"] == "EndNote abstract line one. EndNote abstract line two."
    assert record["keywords"] == ["placebo", "treatment effect"]
    assert record["raw_payload"]["N1"] == "EndNote research notes should remain in raw payload."
    assert diagnostics["missing_title_count"] == 0
    assert diagnostics["missing_author_count"] == 0
    assert diagnostics["empty_abstract_count"] == 0
    assert diagnostics["invalid_doi_count"] == 0
