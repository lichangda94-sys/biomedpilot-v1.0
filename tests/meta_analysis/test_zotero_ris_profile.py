from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.services.literature_import_service import LiteratureImportService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "literature"


def _import_fixture(tmp_path: Path, fixture_name: str):
    service = LiteratureImportService(
        task_center=TaskCenter(tmp_path / "tasks" / "tasks.json"),
        data_center=DataCenter(tmp_path / "data" / "data_assets.json"),
        storage_root=tmp_path,
    )
    result = service.import_file(project_id="meta-zotero", source_path=str(FIXTURES / fixture_name))
    assert result.success, result.message
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    diagnostics = json.loads(Path(str(result.details["diagnostics_path"])).read_text(encoding="utf-8"))
    return result, payload, diagnostics


def test_zotero_ris_profile_imports_core_fields_tags_notes_and_external_key(tmp_path: Path) -> None:
    result, payload, diagnostics = _import_fixture(tmp_path, "zotero_export.ris")

    assert result.source_type == "ris"
    assert result.imported_records == 1
    record = payload["records"][0]
    assert record["title"] == "Zotero Exported Trial of Tea Therapy"
    assert record["authors"] == ["Smith, John", "Wang, Mei"]
    assert record["authors_text"] == "Smith, John; Wang, Mei"
    assert [creator["raw"] for creator in record["creators"]] == ["Smith, John", "Wang, Mei"]
    assert record["first_author"] == "John Smith"
    assert record["journal"] == "Journal of Testing Medicine"
    assert record["publication_title"] == "Journal of Testing Medicine"
    assert record["year"] == 2024
    assert record["date"] == "2024/04/12"
    assert record["doi"] == "10.1000/zotero.001"
    assert record["pmid"] == "11111111"
    assert record["abstract"] == "Zotero abstract first sentence. Zotero abstract continuation."
    assert record["keywords"] == ["randomized trial", "tea therapy"]
    assert record["external_key"] == "smith2024tea"
    assert record["raw_payload"]["N1"] == "Zotero note: imported with Better BibTeX key."
    assert record["raw_payload"]["C7"] == "smith2024tea-bbt"
    assert diagnostics["missing_title_count"] == 0
    assert diagnostics["missing_author_count"] == 0
    assert diagnostics["invalid_doi_count"] == 0
    assert diagnostics["warning_count"] == 0


def test_abnormal_ris_fixture_imports_with_explainable_diagnostics(tmp_path: Path) -> None:
    result, payload, diagnostics = _import_fixture(tmp_path, "abnormal_missing_fields.ris")

    assert result.imported_records == 2
    assert len(payload["records"]) == 2
    assert diagnostics["missing_title_count"] == 1
    assert diagnostics["missing_author_count"] == 1
    assert diagnostics["missing_doi_count"] == 1
    assert diagnostics["invalid_doi_count"] == 1
    assert diagnostics["missing_year_count"] == 1
    assert diagnostics["failed_record_count"] == 1
    assert "record_1:missing_title" in diagnostics["failed_record_examples"]
    warnings_path = Path(str(result.details["warnings_path"]))
    assert warnings_path.exists()
    assert "record_1:missing_title" in warnings_path.read_text(encoding="utf-8")
