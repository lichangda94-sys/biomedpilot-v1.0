from __future__ import annotations

import json
from pathlib import Path

from app.meta_analysis.adapters.literature_import_adapter import _legacy_path
from app.meta_analysis.services.attachment_service import AttachmentService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.dedup_decision_service import DedupDecisionService
from app.meta_analysis.services.formal_report_service import PRISMAService
from app.meta_analysis.services.fulltext_service import FullTextService
from app.meta_analysis.services.literature_import_service import LiteratureImportService
from app.meta_analysis.services.reporting_service import ReportingService
from app.meta_analysis.services.screening_service import ScreeningService
from app.meta_analysis.workspace import recent_import_batch_summaries
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter, TaskType


def test_literature_schema_sanitizer_and_normalizer_contract() -> None:
    with _legacy_path():
        from literature.field_sanitizer import LiteratureFieldSanitizer
        from literature.models import ParsedLiteratureRecord
        from literature.normalize import RecordNormalizationService
        from literature.schema import CREATOR_TYPES, IMPORTABLE_FIELDS, PUBLICATION_TYPES, SYSTEM_CONTROLLED_FIELDS

        assert "author" in CREATOR_TYPES
        assert "journal_article" in PUBLICATION_TYPES
        assert "title" in IMPORTABLE_FIELDS
        assert "record_id" in SYSTEM_CONTROLLED_FIELDS

        sanitized = LiteratureFieldSanitizer().sanitize_import_payload(
            {
                "title": " Trial title ",
                "doi": "https://doi.org/10.1000/ABC",
                "record_id": "external-id",
                "project_id": "external-project",
                "screening_status": "included",
                "attachment_id": "att-external",
            }
        )
        assert sanitized.sanitized["title"] == " Trial title "
        assert {"record_id", "project_id", "screening_status", "attachment_id"} <= set(sanitized.removed_fields)

        normalized = RecordNormalizationService().normalize_record(
            ParsedLiteratureRecord(
                batch_id="batch-1",
                project_id="proj-1",
                source="csv",
                title="A Trial of Treatment.\n",
                authors=["Smith, John", "Wang Mei"],
                date="2024 Jan",
                doi="doi: 10.1000/ABC. ",
                pmid="PMID: 123456",
                journal="Journal of Tests",
                publication_type="Randomized Controlled Trial",
            )
        )
        assert normalized.doi_normalized == "10.1000/abc"
        assert normalized.pmid_normalized == "123456"
        assert normalized.year == 2024
        assert normalized.first_author == "John Smith"
        assert normalized.authors_text == "John Smith; Wang Mei"
        assert normalized.publication_type == "randomized_trial"


def test_import_service_generates_diagnostics_audit_and_recent_batch_summary(tmp_path: Path) -> None:
    source = tmp_path / "records.csv"
    source.write_text(
        "title,authors,year,doi,pmid,abstract,publication_type\n"
        "Trial A,\"Smith, John\",2024,10.1000/a,111,Abstract,journal_article\n"
        ",No Title,2024,,222,,journal_article\n",
        encoding="utf-8",
    )
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    audit = MetaAuditLogService()
    service = LiteratureImportService(task_center=task_center, data_center=data_center, storage_root=tmp_path, audit_log=audit)

    result = service.import_file(project_id="meta-test", source_path=str(source))

    assert result.success
    diagnostics_path = Path(str(result.details["diagnostics_path"]))
    warnings_path = Path(str(result.details["warnings_path"]))
    assert diagnostics_path.exists()
    assert warnings_path.exists()
    diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    assert diagnostics["missing_title_count"] == 1
    project_dir = tmp_path / "projects" / "meta-test" / "meta_analysis"
    event_types = {event.event_type for event in audit.list_events(project_dir)}
    assert {"import_batch_created", "record_parsed", "record_normalized", "record_saved", "diagnostics_generated"} <= event_types
    summaries = recent_import_batch_summaries(tmp_path)
    assert summaries[0]["parsed_count"] == 2


def test_duplicate_detection_decisions_and_merge_preview_contract(tmp_path: Path) -> None:
    review_path = tmp_path / "batch_duplicate_groups.json"
    source_path = tmp_path / "screening_ready.json"
    source_payload = {
        "records": [
            {
                "record_id": "rec-1",
                "source": "nbib",
                "title": "Short title",
                "abstract": "",
                "authors": ["Smith J"],
                "journal": "Journal",
                "year": 2024,
                "pmid": "123",
                "doi": "",
                "publication_type": "journal_article",
                "source_trace": ["pubmed"],
            },
            {
                "record_id": "rec-2",
                "source": "ris",
                "title": "Longer and more complete title",
                "abstract": "Long informative abstract",
                "authors": ["Smith J", "Wang M"],
                "journal": "Journal of Tests",
                "year": 2024,
                "pmid": "",
                "doi": "10.1000/abc",
                "publication_type": "clinical_trial",
                "source_trace": ["zotero"],
            },
        ]
    }
    source_path.write_text(json.dumps(source_payload), encoding="utf-8")
    review_path.write_text(
        json.dumps(
            {
                "project_id": "meta-test",
                "batch_id": "batch",
                "source_path": str(source_path),
                "duplicate_groups": [
                    {
                        "group_id": "dup-1",
                        "record_ids": ["rec-1", "rec-2"],
                        "reason": "pmid_exact,title_author_year_journal_suspected",
                        "confidence": 0.98,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    audit = MetaAuditLogService()
    service = DedupDecisionService(storage_root=tmp_path, audit_log=audit)

    group = service.load_groups(duplicate_review_path=str(review_path))[0]
    preview = service.preview_merge(duplicate_review_path=str(review_path), group_id=group.group_id)
    decision = service.save_decision(duplicate_review_path=str(review_path), group_id=group.group_id, decision="merge")

    assert group.record_ids == ["rec-1", "rec-2"]
    assert preview.merged_record["pmid"] == "123"
    assert preview.merged_record["doi"] == "10.1000/abc"
    assert preview.merged_record["title"] == "Longer and more complete title"
    assert preview.merged_record["authors"] == ["Smith J", "Wang M"]
    assert set(preview.provenance_sources) >= {"pubmed", "zotero"}
    assert decision.decision == "merge"
    assert any(event.event_type == "duplicate_decision" for event in audit.list_events(tmp_path))


def test_attachment_fulltext_audit_and_missing_report(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    source_pdf = tmp_path / "paper.pdf"
    source_pdf.write_bytes(b"%PDF-1.4 test")
    task_center = TaskCenter(tmp_path / "tasks" / "tasks.json")
    data_center = DataCenter(tmp_path / "data" / "data_assets.json")
    audit = MetaAuditLogService()
    attachment_service = AttachmentService(task_center=task_center, data_center=data_center, audit_log=audit)

    linked = attachment_service.add_attachment(project_dir, record_id="rec-1", source_file_path=str(source_pdf), attachment_type="pdf", mode="link_existing_files")
    copied_fulltext = FullTextService(task_center=task_center, data_center=data_center, attachment_service=attachment_service, audit_log=audit).attach_fulltext(project_dir, "rec-2", str(source_pdf))
    missing_report = attachment_service.export_missing_fulltext_report(project_dir, record_ids=["rec-1", "rec-2", "rec-3"])

    assert linked is not None and linked.file_path == str(source_pdf.resolve())
    assert Path(copied_fulltext.pdf_path).exists()
    assert (project_dir / "attachments" / "attachment_registry.json").exists()
    assert "rec-3,true" in missing_report.read_text(encoding="utf-8")
    task_types = {task.task_type for task in task_center.list_tasks()}
    assert {TaskType.ATTACHMENT_LINK, TaskType.ATTACHMENT_COPY, TaskType.MISSING_FULLTEXT_REPORT_EXPORT} <= task_types
    data_types = {asset.data_type for asset in data_center.list_assets(project_dir.name)}
    assert {"attachment_registry", "missing_fulltext_report", "fulltext_registry"} <= data_types


def test_prisma_sources_and_report_audit_events(tmp_path: Path) -> None:
    project_dir = tmp_path / "meta-project"
    (project_dir / "literature").mkdir(parents=True)
    (project_dir / "screening").mkdir(parents=True)
    (project_dir / "fulltext").mkdir(parents=True)
    (project_dir / "extraction").mkdir(parents=True)
    (project_dir / "analysis").mkdir(parents=True)
    (project_dir / "reporting").mkdir(parents=True)
    (project_dir / "literature" / "batch_records.json").write_text(json.dumps({"records": [{"record_id": "rec-1"}], "batch_id": "batch"}), encoding="utf-8")
    (project_dir / "screening" / "screening_decisions.json").write_text(json.dumps({"screening_records": [{"record_id": "rec-1", "decision": "included"}]}), encoding="utf-8")
    (project_dir / "fulltext" / "fulltext_registry.json").write_text(json.dumps({"fulltext_files": [{"record_id": "rec-1", "availability_status": "available"}]}), encoding="utf-8")
    (project_dir / "extraction" / "extraction_records.json").write_text(json.dumps({"records": [{"record_id": "rec-1"}]}), encoding="utf-8")
    (project_dir / "analysis" / "analysis_ready_datasets.json").write_text(json.dumps({"datasets": [{"dataset_id": "ds-1"}]}), encoding="utf-8")
    audit = MetaAuditLogService()
    audit.record_event(project_dir, event_type="analysis_run_completed", target_type="analysis_result", target_id="res-1", summary="done")
    prisma = PRISMAService(audit_log=audit).collect_prisma_numbers(project_dir)

    assert any(ref["source_type"] == "ImportBatch" and ref["status"] == "available" for ref in prisma.source_references)
    assert any(source.startswith("audit:AnalysisInput:") for source in prisma.data_sources)

    preflight = tmp_path / "preflight.json"
    preflight.write_text(json.dumps({"batch_id": "batch", "preflight": {"runnable": False}}), encoding="utf-8")
    report = ReportingService(storage_root=tmp_path, audit_log=audit).export_preflight_report(project_id="meta-project", analysis_preflight_path=str(preflight))
    assert report.success
    report_project_dir = tmp_path / "projects" / "meta-project" / "meta_analysis"
    assert any(event.event_type == "report_exported" for event in audit.list_events(report_project_dir))

