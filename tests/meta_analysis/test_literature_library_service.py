from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.search.pubmed_candidates_handoff_service import PubMedCandidatesHandoffService
from app.meta_analysis.search.pubmed_search_service import PubMedSearchExecution, PubMedSearchResult
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.literature_import_service import LiteratureImportService
from app.meta_analysis.services.literature_library_service import (
    LITERATURE_IMPORT_BATCH_SCHEMA_VERSION,
    LITERATURE_LIBRARY_MANIFEST_SCHEMA_VERSION,
    LITERATURE_LIBRARY_SCHEMA_VERSION,
    NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION,
    LiteratureLibraryService,
)
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "literature"


def test_library_service_imports_normalized_records_manifest_and_queries(tmp_path: Path) -> None:
    service = LiteratureLibraryService()

    result = service.import_records(
        tmp_path,
        project_id="meta-library",
        source_type="manual",
        source_name="Manual",
        source_file="manual-entry",
        raw_records=[
            {
                "title": "Manual Trial",
                "abstract": "Manual abstract",
                "authors": ["Alice Adams", "Ben Baker"],
                "journal": "Manual Journal",
                "year": "2026",
                "doi": "10.1000/manual.001",
                "pmid": "999",
            }
        ],
    )
    record = result.imported_records[0]
    batch = json.loads(Path(result.import_batches_path).read_text(encoding="utf-8"))["import_batches"][0]
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert result.success
    assert json.loads(Path(result.records_path).read_text(encoding="utf-8"))["schema_version"] == LITERATURE_LIBRARY_SCHEMA_VERSION
    assert record["schema_version"] == NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION
    assert record["record_id"] == "lit-pmid-999"
    assert record["screening_status"] == "not_started"
    assert record["dedup_status"] == "pending_review"
    assert record["full_text_status"] == "not_checked"
    assert record["quality_status"] == "not_started"
    assert record["provenance"]["source_type"] == "manual"
    assert batch["schema_version"] == LITERATURE_IMPORT_BATCH_SCHEMA_VERSION
    assert manifest["schema_version"] == LITERATURE_LIBRARY_MANIFEST_SCHEMA_VERSION
    assert manifest["total_records"] == 1
    assert manifest["total_batches"] == 1
    assert manifest["source_counts"] == {"manual": 1}
    assert service.get_record(tmp_path, "lit-pmid-999")["title"] == "Manual Trial"
    assert service.filter_records(tmp_path, pmid="999")[0]["doi"] == "10.1000/manual.001"
    assert service.filter_records(tmp_path, doi="10.1000/manual.001")[0]["pmid"] == "999"
    assert service.filter_records(tmp_path, title_keyword="manual")[0]["record_id"] == "lit-pmid-999"
    assert service.filter_records(tmp_path, import_batch_id=result.import_batch_id)[0]["record_id"] == "lit-pmid-999"


def test_library_service_missing_identifiers_do_not_crash_and_emit_chinese_diagnostics(tmp_path: Path) -> None:
    result = LiteratureLibraryService().import_records(
        tmp_path,
        project_id="meta-library",
        source_type="csv",
        source_name="CSV",
        source_file="sparse.csv",
        raw_records=[{"record_id": "sparse-1", "title": "Sparse record"}],
    )

    assert result.success
    assert result.imported_count == 1
    warnings = result.diagnostics["warning_counts"]
    assert warnings["缺少 DOI"] == 1
    assert warnings["缺少 PMID"] == 1
    assert warnings["缺少摘要"] == 1
    assert warnings["缺少年份"] == 1
    assert warnings["作者字段不完整"] == 1


def test_pubmed_handoff_uses_unified_library_schema_and_manifest(tmp_path: Path) -> None:
    execution = _execution()
    preview = PubMedCandidatesHandoffService().create_candidates_preview(
        tmp_path,
        execution=execution,
        execution_report_path="protocol/search_execution_report.json",
        search_strategy_snapshot_path="protocol/search_strategy_user_confirmed.json",
    )

    result = PubMedCandidatesHandoffService().import_selected_candidates(
        tmp_path,
        preview_id=preview.preview_id,
        selected_candidate_ids=("pcand-111",),
        rejected_candidate_ids=("pcand-222",),
        actor="reviewer",
    )
    library = json.loads(Path(result.literature_records_path).read_text(encoding="utf-8"))
    manifest = json.loads((tmp_path / "literature" / "library_manifest.json").read_text(encoding="utf-8"))
    record = library["records"][0]

    assert library["schema_version"] == LITERATURE_LIBRARY_SCHEMA_VERSION
    assert record["schema_version"] == NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION
    assert record["source_type"] == "pubmed_confirmed_candidates"
    assert record["search_execution_id"] == "pubmedexec-m3"
    assert record["provenance"]["candidate_preview_id"] == preview.preview_id
    assert record["screening_status"] == "not_started"
    assert manifest["source_counts"] == {"pubmed_confirmed_candidates": 1}
    assert "222" not in json.dumps(library)


def test_nbib_ris_csv_import_bridge_writes_unified_library(tmp_path: Path) -> None:
    service = LiteratureImportService(
        task_center=TaskCenter(tmp_path / "tasks" / "tasks.json"),
        data_center=DataCenter(tmp_path / "data" / "assets.json"),
        storage_root=tmp_path,
    )

    for fixture in ("sample.nbib", "sample.ris", "sample.csv"):
        result = service.import_file(project_id="meta-import", source_path=str(FIXTURES / fixture))
        assert result.success
        assert result.details["library_schema_version"] == LITERATURE_LIBRARY_SCHEMA_VERSION
        assert result.details["record_schema_version"] == NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION

    project_dir = tmp_path / "projects" / "meta-import" / "meta_analysis"
    library = json.loads((project_dir / "literature" / "literature_records.json").read_text(encoding="utf-8"))
    manifest = json.loads((project_dir / "literature" / "library_manifest.json").read_text(encoding="utf-8"))
    records = library["records"]

    assert library["schema_version"] == LITERATURE_LIBRARY_SCHEMA_VERSION
    assert len(records) == 6
    assert {record["schema_version"] for record in records} == {NORMALIZED_LITERATURE_RECORD_SCHEMA_VERSION}
    assert {"nbib", "ris", "csv"} <= set(manifest["source_counts"])
    assert manifest["total_batches"] == 3
    assert all(record["provenance"] for record in records)
    assert all(record["screening_status"] == "not_started" for record in records)


def test_library_import_does_not_create_screening_or_advance_prisma_review_counts(tmp_path: Path) -> None:
    LiteratureLibraryService().import_records(
        tmp_path,
        project_id="meta-library",
        source_type="manual",
        source_name="Manual",
        raw_records=[{"title": "Manual Trial", "pmid": "999"}],
    )
    prisma = PRISMAService().collect_prisma_numbers(tmp_path)

    assert not (tmp_path / "screening").exists()
    assert prisma.records_screened == 0
    assert prisma.records_excluded_title_abstract == 0
    assert prisma.full_text_reports_assessed == 0
    assert prisma.studies_included == 0


def _execution() -> PubMedSearchExecution:
    return PubMedSearchExecution(
        success=True,
        query_used='"Obesity"[Mesh]',
        executed_at="2026-05-06T00:00:00+00:00",
        result_count=2,
        returned_count=2,
        search_execution_id="pubmedexec-m3",
        records=(
            PubMedSearchResult(
                pmid="111",
                doi="10.1000/demo111",
                title="Obesity and thyroid cancer risk",
                journal="Meta Trial Journal",
                year="2024",
                publication_date="2024-01-02",
                authors=("Alice Adams",),
                abstract="Candidate abstract for thyroid cancer risk.",
                snippet="Candidate abstract for thyroid cancer risk.",
                url="https://pubmed.ncbi.nlm.nih.gov/111/",
                query_used='"Obesity"[Mesh]',
            ),
            PubMedSearchResult(
                pmid="222",
                doi="10.1000/demo222",
                title="BMI and thyroid neoplasms",
                journal="Meta Review Journal",
                year="2025",
                publication_date="2025",
                authors=("Ben Baker",),
                abstract="Second candidate abstract.",
                snippet="Second candidate abstract.",
                url="https://pubmed.ncbi.nlm.nih.gov/222/",
                query_used='"Obesity"[Mesh]',
            ),
        ),
    )
