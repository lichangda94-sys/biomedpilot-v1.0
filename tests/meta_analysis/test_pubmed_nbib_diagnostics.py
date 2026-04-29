from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.services.dedup_decision_service import DedupDecisionService
from app.meta_analysis.services.duplicate_review_service import DuplicateReviewService
from app.meta_analysis.services.literature_import_service import LiteratureImportService
from app.meta_analysis.services.prepare_screening_service import PrepareScreeningService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "literature"


def test_pubmed_nbib_profile_imports_fields_and_duplicate_diagnostics(tmp_path: Path) -> None:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    import_service = LiteratureImportService(task_center=task_center, data_center=data_center, storage_root=tmp_path)

    result = import_service.import_file(project_id="meta-pubmed", source_path=str(FIXTURES / "pubmed_export.nbib"))

    assert result.success, result.message
    payload = json.loads(Path(result.output_path).read_text(encoding="utf-8"))
    diagnostics = json.loads(Path(str(result.details["diagnostics_path"])).read_text(encoding="utf-8"))
    records = payload["records"]
    assert result.source_type == "nbib"
    assert result.imported_records == 2
    assert records[0]["title"] == "PubMed randomized placebo treatment trial"
    assert records[0]["authors"] == ["Brown, Alice", "Chen, David"]
    assert records[0]["first_author"] == "Alice Brown"
    assert records[0]["journal"] == "PubMed Trial Journal"
    assert records[0]["year"] == 2022
    assert records[0]["doi"] == "10.1000/pubmed.001"
    assert records[0]["pmid"] == "33333333"
    assert records[0]["publication_type"] == "randomized_trial"
    assert records[0]["keywords"] == ["randomized", "placebo"]
    assert diagnostics["missing_title_count"] == 0
    assert diagnostics["missing_author_count"] == 0
    assert diagnostics["duplicate_identifier_count"] == 1
    assert diagnostics["duplicate_candidate_count"] == 1
    assert diagnostics["records_after_dedup_count"] == 1


def test_pubmed_nbib_duplicate_candidate_matches_expected_exact_reason(tmp_path: Path) -> None:
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    import_service = LiteratureImportService(task_center=task_center, data_center=data_center, storage_root=tmp_path)
    prepare_service = PrepareScreeningService(task_center=task_center, data_center=data_center, storage_root=tmp_path)
    review_service = DuplicateReviewService(task_center=task_center, data_center=data_center, storage_root=tmp_path)
    dedup_service = DedupDecisionService(task_center=task_center, data_center=data_center, storage_root=tmp_path)

    import_result = import_service.import_file(project_id="meta-pubmed", source_path=str(FIXTURES / "pubmed_export.nbib"))
    prepare_result = prepare_service.prepare(project_id="meta-pubmed", import_output_path=import_result.output_path)
    review_result = review_service.review(project_id="meta-pubmed", screening_ready_path=prepare_result.output_path)
    groups = dedup_service.load_groups(duplicate_review_path=review_result.output_path)

    assert import_result.success
    assert prepare_result.success
    assert review_result.success
    assert review_result.duplicate_group_count == 1
    assert len(groups) == 1
    group = groups[0]
    assert set(group.record_ids) == {
        str(record["record_id"])
        for record in json.loads(Path(prepare_result.output_path).read_text(encoding="utf-8"))["records"]
    }
    assert "doi_exact" in group.match_reason
    assert "pmid_exact" in group.match_reason
    assert group.confidence >= 0.98
