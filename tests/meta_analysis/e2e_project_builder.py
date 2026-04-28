from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from app.meta_analysis.models.extraction import (
    BinaryOutcomeData,
    ExtractedOutcome,
    ExtractionRecord,
    ExtractionValidationStatus,
    OutcomeDataType,
    StudyCharacteristics,
    new_extraction_id,
    now_utc,
)
from app.meta_analysis.services.advanced_analysis_service import AdvancedAnalysisService
from app.meta_analysis.services.analysis_dataset_service import AnalysisDatasetService
from app.meta_analysis.services.analysis_run_service import AnalysisRunService
from app.meta_analysis.services.dedup_decision_service import DedupDecisionService
from app.meta_analysis.services.duplicate_review_service import DuplicateReviewService
from app.meta_analysis.services.extraction_record_storage_service import ExtractionRecordStorageService
from app.meta_analysis.services.figure_result_service import FigureResultService
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder, PRISMAService
from app.meta_analysis.services.fulltext_service import FullTextService
from app.meta_analysis.services.literature_import_service import LiteratureImportService
from app.meta_analysis.services.prepare_screening_service import PrepareScreeningService
from app.meta_analysis.services.publication_export_service import PublicationExportService
from app.meta_analysis.services.quality_service import QualityAssessmentService
from app.meta_analysis.services.screening_service import ScreeningService
from app.shared.data_center.service import DataCenter
from app.shared.task_center.service import TaskCenter


EXAMPLE_INPUT = Path("examples/meta_analysis_e2e_project/inputs/mock_literature.csv")
DEFAULT_OUTCOME_DATA = [
    (10, 100, 20, 100, "A"),
    (12, 110, 22, 115, "A"),
    (16, 120, 24, 118, "B"),
]


def build_meta_analysis_e2e_project(
    tmp_path: Path,
    *,
    project_id: str = "meta-e2e-project",
    input_path: Path = EXAMPLE_INPUT,
    outcome_data: list[tuple[int, int, int, int, str]] | None = None,
    intervention_or_exposure: str = "Statin exposure",
    comparator: str = "Control",
    outcome_name: str = "Mortality",
    source_location: str = "mock source",
    seeded_note: str = "Seeded by Stage M E2E validation.",
) -> dict[str, Any]:
    project_dir = tmp_path / project_id
    project_dir.mkdir(parents=True)
    (project_dir / "project.json").write_text(
        json.dumps({"project_id": project_id, "software_status": "Developer Preview / testing"}),
        encoding="utf-8",
    )
    task_center = TaskCenter(tmp_path / "registry" / "tasks.json")
    data_center = DataCenter(tmp_path / "registry" / "data_assets.json")

    import_service = LiteratureImportService(task_center=task_center, data_center=data_center, storage_root=tmp_path)
    prepare_service = PrepareScreeningService(task_center=task_center, data_center=data_center, storage_root=tmp_path)
    duplicate_service = DuplicateReviewService(task_center=task_center, data_center=data_center, storage_root=tmp_path)
    dedup_service = DedupDecisionService(task_center=task_center, data_center=data_center, storage_root=tmp_path)
    screening_service = ScreeningService(task_center=task_center, data_center=data_center, storage_root=tmp_path)

    import_result = import_service.import_file(project_id=project_id, source_path=str(input_path.resolve()))
    assert import_result.success, import_result.message
    copied_literature = _copy_to_project(Path(import_result.output_path), project_dir / "literature" / "literature_records.json")

    prepare_result = prepare_service.prepare(project_id=project_id, import_output_path=import_result.output_path)
    assert prepare_result.success, prepare_result.message
    copied_prepare = _copy_to_project(Path(prepare_result.output_path), project_dir / "screening" / "screening_ready_records.json")

    duplicate_result = duplicate_service.review(project_id=project_id, screening_ready_path=prepare_result.output_path)
    assert duplicate_result.success, duplicate_result.message
    copied_duplicates = _copy_to_project(Path(duplicate_result.output_path), project_dir / "deduplication" / "duplicate_candidate_groups.json")

    dedup_result = dedup_service.generate_deduplicated_literature(project_id=project_id, duplicate_review_path=duplicate_result.output_path)
    assert dedup_result.success, dedup_result.message
    copied_dedup = _copy_to_project(Path(dedup_result.output_path), project_dir / "deduplication" / "deduplicated_literature.json")

    queue_result = screening_service.create_queue(project_id=project_id, source_path=duplicate_result.output_path)
    assert queue_result.success, queue_result.message
    queue_path = Path(queue_result.output_path)
    queue_payload = json.loads(queue_path.read_text(encoding="utf-8"))
    screening_records = list(queue_payload["screening_records"])
    for index, item in enumerate(screening_records):
        decision = "included" if index < 3 else "excluded"
        update = screening_service.update_decision(
            project_id=project_id,
            queue_path=str(queue_path),
            screening_record_id=str(item["screening_record_id"]),
            decision=decision,
            exclusion_reason_text="wrong outcome" if decision == "excluded" else "",
            reviewer_id="reviewer-a",
            notes=seeded_note,
        )
        assert update.success, update.message
    copied_screening = _copy_to_project(queue_path, project_dir / "screening" / "screening_decisions.json")
    screening_records = list(json.loads(copied_screening.read_text(encoding="utf-8"))["screening_records"])
    included_records = [record for record in screening_records if record["decision"] == "included"]

    fulltext_service = FullTextService(task_center=task_center, data_center=data_center)
    for record in included_records:
        record_id = _screening_record_source_id(record)
        fulltext_service.update_fulltext_availability(project_dir, record_id, "available")
        fulltext_service.save_fulltext_decision(
            project_dir,
            record_id=record_id,
            reviewer_id="reviewer-a",
            decision="include",
            notes="Seeded full-text include decision.",
        )
    data_center.register_asset(
        project_id=project_id,
        module="meta_analysis",
        data_type="fulltext_registry",
        source_path=str(project_dir),
        output_path=str(project_dir / "fulltext" / "fulltext_registry.json"),
        status="available",
    )
    fulltext_service.export_full_text_exclusion_report(project_dir)

    extraction_storage = ExtractionRecordStorageService(task_center=task_center, data_center=data_center)
    extraction_records = _extraction_records(
        project_id,
        included_records,
        outcome_data=outcome_data or DEFAULT_OUTCOME_DATA,
        intervention_or_exposure=intervention_or_exposure,
        comparator=comparator,
        outcome_name=outcome_name,
        source_location=source_location,
        seeded_note=seeded_note,
    )
    extraction_storage.save_extraction_records(project_dir, extraction_records)

    quality_service = QualityAssessmentService(task_center=task_center, data_center=data_center)
    for record in extraction_records:
        assessment = quality_service.create_quality_assessment(
            project_id=project_id,
            study_id=record.study_id,
            record_id=record.record_id,
            tool_name="NOS",
            domains={"selection": "low risk", "comparability": "some concerns", "outcome": "low risk"},
            overall_judgement="low risk",
            reviewer_id="reviewer-a",
            notes="Seeded quality assessment for Stage M.",
        )
        quality_service.save_quality_assessment(project_dir, assessment)
    quality_table = quality_service.export_quality_table_csv(project_dir)

    dataset_service = AnalysisDatasetService(
        extraction_storage=extraction_storage,
        task_center=task_center,
        data_center=data_center,
    )
    dataset = dataset_service.build_analysis_ready_dataset(project_dir, "TREATMENT_EFFECT_META", "Mortality", "OR")
    assert not dataset.validation_errors, dataset.validation_errors
    dataset_path = dataset_service.save_analysis_ready_dataset(project_dir, dataset)

    run_service = AnalysisRunService(dataset_service=dataset_service, task_center=task_center, data_center=data_center)
    analysis_result = run_service.run_meta_analysis(project_dir, dataset.dataset_id, "random")
    analysis_path = run_service.save_analysis_result(project_dir, analysis_result)

    figure_service = FigureResultService(analysis_run_service=run_service, task_center=task_center, data_center=data_center)
    forest_artifact = figure_service.generate_forest_plot(project_dir, analysis_result.result_id)
    result_table = figure_service.export_result_table_csv(project_dir, analysis_result.result_id)

    advanced_service = AdvancedAnalysisService(
        dataset_service=dataset_service,
        analysis_run_service=run_service,
        figure_service=figure_service,
        task_center=task_center,
        data_center=data_center,
    )
    funnel_artifact = advanced_service.generate_funnel_plot(project_dir, analysis_result.result_id)
    bias_result = advanced_service.run_publication_bias_test(project_dir, analysis_result.result_id)
    bias_path = advanced_service.save_publication_bias_result(project_dir, bias_result)

    prisma_service = PRISMAService(task_center=task_center, data_center=data_center)
    prisma_summary = prisma_service.collect_prisma_numbers(project_dir)
    prisma_json = prisma_service.save_prisma_flow_summary(project_dir, prisma_summary)
    prisma_md = prisma_service.export_prisma_flow_markdown(project_dir, prisma_summary)

    report_builder = FormalMarkdownReportBuilder(
        prisma_service=prisma_service,
        task_center=task_center,
        data_center=data_center,
    )
    formal_report = report_builder.build_formal_markdown_report(project_dir)

    export_service = PublicationExportService(
        formal_report_builder=report_builder,
        task_center=task_center,
        data_center=data_center,
    )
    supplementary = export_service.export_supplementary_exports(project_dir)
    html_report = export_service.export_html_report(project_dir)
    word_report = export_service.export_word_report(project_dir)
    figure_package = export_service.export_figure_package(project_dir)
    snapshot = export_service.create_project_snapshot(project_dir)
    snapshot_path = export_service.save_project_snapshot(project_dir, snapshot)
    reproducibility = export_service.export_reproducibility_package(project_dir)

    return {
        "project_dir": project_dir,
        "task_center": task_center,
        "data_center": data_center,
        "paths": {
            "literature_records": copied_literature,
            "screening_ready_records": copied_prepare,
            "duplicate_candidate_groups": copied_duplicates,
            "deduplicated_literature": copied_dedup,
            "screening_decisions": copied_screening,
            "fulltext_registry": project_dir / "fulltext" / "fulltext_registry.json",
            "fulltext_exclusion_report": project_dir / "reports" / "full_text_exclusion_report.csv",
            "extraction_records": project_dir / "extraction" / "extraction_records.json",
            "quality_assessment_table": quality_table,
            "analysis_ready_dataset": dataset_path,
            "analysis_result": analysis_path,
            "forest_plot": Path(forest_artifact.file_path),
            "result_table": result_table,
            "funnel_plot": Path(funnel_artifact.file_path),
            "publication_bias_result": bias_path,
            "prisma_summary_json": prisma_json,
            "prisma_summary_md": prisma_md,
            "formal_report": formal_report,
            "html_report": Path(html_report.output_path),
            "word_report": Path(word_report.output_path),
            "supplementary_exports": Path(supplementary.output_path),
            "figure_package": Path(figure_package.output_path),
            "snapshot": snapshot_path,
            "reproducibility_package": Path(reproducibility.output_path),
        },
        "warnings": {
            "publication_bias": bias_result.warnings,
            "prisma": prisma_summary.notes,
            "seeded_note": seeded_note,
        },
    }


def _copy_to_project(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def _screening_record_source_id(record: dict[str, Any]) -> str:
    return str(record.get("record_id") or record.get("normalized_record_id") or record.get("source_record_id") or record["screening_record_id"])


def _extraction_records(
    project_id: str,
    included_records: list[dict[str, Any]],
    *,
    outcome_data: list[tuple[int, int, int, int, str]],
    intervention_or_exposure: str,
    comparator: str,
    outcome_name: str,
    source_location: str,
    seeded_note: str,
) -> list[ExtractionRecord]:
    records: list[ExtractionRecord] = []
    for index, (record, data) in enumerate(zip(included_records, outcome_data, strict=True), start=1):
        exp_events, exp_total, ctrl_events, ctrl_total, subgroup = data
        now = now_utc()
        authors = record.get("authors")
        first_author = str(authors[0]) if isinstance(authors, list) and authors else f"Study {index}"
        records.append(
            ExtractionRecord(
                extraction_id=new_extraction_id(),
                project_id=project_id,
                record_id=_screening_record_source_id(record),
                study_id=f"study-{index}",
                reviewer_id="reviewer-a",
                profile_type="TREATMENT_EFFECT_META",
                study_characteristics=StudyCharacteristics(
                    first_author=first_author,
                    year=int(record.get("year") or 2020),
                    country="United States",
                    study_design="randomized controlled trial",
                    population="Adults with eligible clinical outcome data",
                    sample_size=exp_total + ctrl_total,
                    intervention_or_exposure=intervention_or_exposure,
                    comparator=comparator,
                    follow_up="12 months",
                    notes=seeded_note,
                ),
                outcomes=[
                    ExtractedOutcome(
                        outcome_id=f"outcome-{index}",
                        outcome_data_type=OutcomeDataType.BINARY.value,
                        data=BinaryOutcomeData(
                            outcome_name=outcome_name,
                            effect_measure="OR",
                            experimental_events=exp_events,
                            experimental_total=exp_total,
                            control_events=ctrl_events,
                            control_total=ctrl_total,
                            timepoint="12 months",
                            subgroup=subgroup,
                            notes=seeded_note,
                        ),
                    )
                ],
                notes=seeded_note,
                source_location=source_location,
                validation_status=ExtractionValidationStatus.VALID.value,
                created_at=now,
                updated_at=now,
            )
        )
    return records
