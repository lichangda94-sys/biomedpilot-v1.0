from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.meta_analysis.project_workspace import open_meta_analysis_project
from app.meta_analysis.search.pubmed_candidates_handoff_service import PubMedCandidatesHandoffService
from app.meta_analysis.search.pubmed_search_service import PubMedSearchExecution, PubMedSearchResult
from app.meta_analysis.search.search_strategy_builder_service import SearchStrategyBuilderService
from app.meta_analysis.services.analysis_setup_service import AnalysisSetupService
from app.meta_analysis.services.dedup_review_v2_service import DECISION_KEEP_BOTH, DedupReviewV2Service
from app.meta_analysis.services.extraction_form_service import ExtractionFormService
from app.meta_analysis.services.formal_report_service import FormalMarkdownReportBuilder, PRISMAService
from app.meta_analysis.services.literature_library_service import LiteratureLibraryService
from app.meta_analysis.services.multisource_literature_import_service import MultiSourceLiteratureImportService
from app.meta_analysis.services.online_retrieval_validation_service import OnlineRetrievalValidationService
from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
from app.meta_analysis.services.report_manifest_service import ReportManifestService
from app.meta_analysis.services.title_abstract_screening_v2_service import DECISION_INCLUDE, TitleAbstractScreeningV2Service


MATRIX_SCHEMA_VERSION = "biomedpilot.meta_release_connection_matrix.v1"
ACTION_RESULT_SCHEMA_VERSION = "biomedpilot.meta_release_action_result.v1"


@dataclass(frozen=True)
class MetaConnectionRow:
    action_id: str
    ui_page: str
    backend_capability: str
    branch_source: str
    expected_test: str
    button_label: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


CONNECTION_ROWS: tuple[MetaConnectionRow, ...] = (
    MetaConnectionRow(
        "question_type_gate",
        "Question & Meta Type / 研究问题与 Meta 类型",
        "PICOWorkspaceService.generate_draft + confirm_protocol",
        "codex/meta-workflow-ui + current Integration active runtime",
        "点击后生成/读取 PICO draft、confirmed protocol 和 manifest；无有效项目时写 disabled reason。",
        "Run gate",
    ),
    MetaConnectionRow(
        "search_strategy_gate",
        "Search Strategy / 检索策略",
        "SearchStrategyBuilderService.generate_from_confirmed_protocol + confirm_strategies",
        "codex/meta-search-ui-main + current Integration active runtime",
        "点击后生成多数据库检索草稿并确认 PubMed execution gate；缺 confirmed protocol 时写 disabled reason。",
        "Build search",
    ),
    MetaConnectionRow(
        "pubmed_retrieval_gate",
        "Search Strategy / PubMed 联网检索",
        "OnlineRetrievalValidationService.validate_pubmed_retrieval with release fixture fetcher",
        "codex/meta-search-ui-main",
        "点击后调用检索 service，使用本地 fixture fetcher 生成 PubMed retrieval artifact，不触发真实网络。",
        "Validate retrieval",
    ),
    MetaConnectionRow(
        "multisource_import_recognition",
        "Import & Deduplication / 文献导入与识别",
        "MultiSourceLiteratureImportService.detect_format + parse_file + LiteratureLibraryService.import_records",
        "codex/meta-workflow-ui + current Integration active runtime",
        "点击后导入 release fixture CSV，生成 diagnostics、normalized library 和 import batch。",
        "Import fixture",
    ),
    MetaConnectionRow(
        "candidate_handoff_bridge",
        "Import & Deduplication / PubMed candidate handoff",
        "PubMedCandidatesHandoffService.create_candidates_preview + import_selected_candidates",
        "codex/meta-search-ui-main",
        "点击后生成 candidate preview、selection、library handoff 和 dedup preparation artifact。",
        "Handoff",
    ),
    MetaConnectionRow(
        "dedup_screening_queue",
        "Screening / 去重与标题摘要筛选",
        "DedupReviewV2Service.build_review_queue + generate_deduplicated_set + TitleAbstractScreeningV2Service.build_queue",
        "codex/meta-workflow-ui + current Integration active runtime",
        "点击后调用去重和筛选队列 service，生成 duplicate queue、deduplicated set、screening queue 或明确 blocker。",
        "Prepare screening",
    ),
    MetaConnectionRow(
        "extraction_quality_gate",
        "Full-text & Extraction / 数据提取质控",
        "TitleAbstractScreeningV2Service.save_decision + ExtractionFormService.save_draft + pre_export_completeness_check",
        "codex/meta-workflow-ui + current Integration active runtime",
        "点击后把首条 screening queue 记录纳入 release probe，生成 extraction draft 和 completeness gate artifact。",
        "Check extraction",
    ),
    MetaConnectionRow(
        "statistics_report_gate",
        "Meta Analysis Tasks -> Result & Report / 统计与报告 gate",
        "AnalysisSetupService.create_plan/run_preflight + PRISMAService + ReportManifestService + FormalMarkdownReportBuilder",
        "codex/meta-workflow-ui + current Integration active runtime",
        "点击后生成 analysis plan/preflight、PRISMA/report manifest，并在未达 report-ready 时写 blocker。",
        "Report gate",
    ),
)


def build_meta_connection_matrix() -> dict[str, Any]:
    return {
        "schema_version": MATRIX_SCHEMA_VERSION,
        "created_at": _now(),
        "module": "meta_analysis",
        "rows": [row.to_dict() for row in CONNECTION_ROWS],
    }


def write_meta_connection_matrix(project_root: Path) -> Path:
    path = project_root.expanduser().resolve() / "manifests" / "meta_release_connection_matrix.json"
    _write_json(path, build_meta_connection_matrix())
    return path


def execute_meta_release_action(project_root: Path, action_id: str) -> dict[str, Any]:
    project_root = project_root.expanduser().resolve()
    row = _row(action_id)
    validation = open_meta_analysis_project(project_root)
    if not validation.is_valid:
        return _write_result(
            project_root,
            action_id=action_id,
            status="blocked",
            services_called=("open_meta_analysis_project",),
            artifact_paths=(),
            backend_results={"validation_errors": list(validation.errors)},
            disabled_reason="meta_project_manifest_missing_or_invalid",
        )
    actions: dict[str, Callable[[Path], dict[str, Any]]] = {
        "question_type_gate": _run_question_type_gate,
        "search_strategy_gate": _run_search_strategy_gate,
        "pubmed_retrieval_gate": _run_pubmed_retrieval_gate,
        "multisource_import_recognition": _run_multisource_import_recognition,
        "candidate_handoff_bridge": _run_candidate_handoff_bridge,
        "dedup_screening_queue": _run_dedup_screening_queue,
        "extraction_quality_gate": _run_extraction_quality_gate,
        "statistics_report_gate": _run_statistics_report_gate,
    }
    payload = actions[action_id](project_root)
    payload.setdefault("ui_page", row.ui_page)
    payload.setdefault("backend_capability", row.backend_capability)
    payload.setdefault("branch_source", row.branch_source)
    payload.setdefault("expected_test", row.expected_test)
    return _write_result(project_root, action_id=action_id, **payload)


def _run_question_type_gate(project_root: Path) -> dict[str, Any]:
    service = PICOWorkspaceService()
    draft = service.load_draft(project_root)
    if draft is None:
        draft = service.generate_draft(
            project_root,
            "Does release connection validation identify treatment effect meta-analysis readiness?",
            pico_mode="pico",
            actor="release_connection_probe",
        )
    confirmed = service.load_confirmed(project_root)
    if confirmed is None:
        confirmed = service.confirm_protocol(
            project_root,
            actor="release_connection_probe",
            confirmed_meta_type="treatment_comparative_meta",
            user_notes="Release connection probe; reviewer confirmation is still required for production use.",
            overrides={
                "confirmed_population": draft.population or "adult patients",
                "confirmed_intervention_or_exposure": draft.intervention or "intervention",
                "confirmed_comparator": draft.comparator or "control",
                "confirmed_outcomes": (draft.outcome or "clinical outcome",),
                "confirmed_study_design": draft.study_design or "randomized controlled trial",
            },
        )
    artifacts = (
        service.draft_path(project_root),
        service.confirmed_path(project_root),
        service.manifest_path(project_root),
    )
    return {
        "status": "passed",
        "services_called": ("PICOWorkspaceService.generate_draft", "PICOWorkspaceService.confirm_protocol"),
        "artifact_paths": _paths(artifacts),
        "backend_results": {
            "draft_protocol_id": draft.protocol_id,
            "confirmed_protocol_id": confirmed.confirmed_protocol_id,
            "confirmed_meta_type": confirmed.confirmed_meta_type,
            "production_note": "release_probe_created_or_loaded; reviewer confirmation remains the production gate",
        },
    }


def _run_search_strategy_gate(project_root: Path) -> dict[str, Any]:
    _run_question_type_gate(project_root)
    service = SearchStrategyBuilderService()
    try:
        result = service.generate_from_confirmed_protocol(project_root, actor="release_connection_probe")
        confirmed = service.confirm_strategies(project_root, actor="release_connection_probe", database_ids=("pubmed",))
    except Exception as exc:
        return {
            "status": "blocked",
            "services_called": ("SearchStrategyBuilderService.generate_from_confirmed_protocol",),
            "artifact_paths": (),
            "backend_results": {"error": str(exc)},
            "disabled_reason": "confirmed_protocol_required_for_search_strategy",
        }
    return {
        "status": "passed",
        "services_called": (
            "SearchStrategyBuilderService.generate_from_confirmed_protocol",
            "SearchStrategyBuilderService.confirm_strategies",
        ),
        "artifact_paths": _paths((result.draft_path, result.export_markdown_path, result.export_text_path, service.confirmed_set_path(project_root), service.manifest_path(project_root))),
        "backend_results": {
            "draft_count": result.draft_count,
            "confirmed_databases": [item.database for item in confirmed],
            "pubmed_execution_allowed": any(item.database == "pubmed" and item.execution_allowed for item in confirmed),
        },
    }


def _run_pubmed_retrieval_gate(project_root: Path) -> dict[str, Any]:
    service = OnlineRetrievalValidationService(fetcher=_fixture_pubmed_fetcher)
    result = service.validate_pubmed_retrieval(project_root, query="release connection validation meta analysis", retmax=1, timeout_seconds=0.2)
    status = "passed" if result.success and result.output_path else "blocked"
    return {
        "status": status,
        "services_called": ("OnlineRetrievalValidationService.validate_pubmed_retrieval",),
        "artifact_paths": _paths((result.output_path, result.history_path)),
        "backend_results": {
            "fetched_count": result.fetched_count,
            "message": result.message,
            "warnings": result.warnings,
            "network_mode": "fixture_fetcher_no_live_network",
        },
        "disabled_reason": "" if status == "passed" else "pubmed_retrieval_validation_failed",
    }


def _run_multisource_import_recognition(project_root: Path) -> dict[str, Any]:
    source_path = _write_fixture_csv(project_root)
    service = MultiSourceLiteratureImportService()
    detected = service.detect_format(source_path, requested_format="auto")
    result = service.import_file(
        project_root,
        project_id=project_root.name,
        source_path=source_path,
        source_format="auto",
        source_database="Release fixture CSV",
        search_strategy="release connection validation",
        search_date="2026-05-28",
    )
    status = "passed" if result.success else "blocked"
    return {
        "status": status,
        "services_called": (
            "MultiSourceLiteratureImportService.detect_format",
            "MultiSourceLiteratureImportService.parse_file",
            "LiteratureLibraryService.import_records",
        ),
        "artifact_paths": _paths((source_path, result.diagnostics_path, result.library_records_path)),
        "backend_results": {
            "detected_format": detected,
            "parsed_record_count": result.parsed_record_count,
            "imported_count": result.imported_count,
            "skipped_count": result.skipped_count,
            "message": result.message,
            "error_message": result.error_message,
        },
        "disabled_reason": "" if status == "passed" else "multisource_import_failed",
    }


def _run_candidate_handoff_bridge(project_root: Path) -> dict[str, Any]:
    _run_search_strategy_gate(project_root)
    execution = _fixture_pubmed_execution()
    report_path = project_root / "protocol" / "pubmed_candidates" / "release_pubmed_execution_report.json"
    _write_json(report_path, execution.to_report())
    service = PubMedCandidatesHandoffService()
    preview = service.create_candidates_preview(
        project_root,
        execution=execution,
        execution_report_path=str(report_path),
        search_strategy_snapshot_path="protocol/search_strategy_v2/search_strategy_confirmed.json",
        project_id=project_root.name,
    )
    selected = tuple(candidate.candidate_id for candidate in preview.candidates[:1])
    handoff = service.import_selected_candidates(project_root, preview_id=preview.preview_id, selected_candidate_ids=selected, actor="release_connection_probe")
    status = "passed" if handoff.success else "blocked"
    return {
        "status": status,
        "services_called": (
            "PubMedCandidatesHandoffService.create_candidates_preview",
            "PubMedCandidatesHandoffService.import_selected_candidates",
            "LiteratureLibraryService.import_records",
        ),
        "artifact_paths": _paths((report_path, service.preview_path(project_root, preview.preview_id), service.selection_path(project_root, preview.preview_id), handoff.literature_records_path, handoff.import_batch_path, handoff.dedup_queue_path, handoff.handoff_audit_path)),
        "backend_results": {
            "preview_id": preview.preview_id,
            "candidate_count": len(preview.candidates),
            "selected_count": handoff.selected_count,
            "imported_count": handoff.imported_count,
            "message": handoff.message,
        },
        "disabled_reason": "" if status == "passed" else "pubmed_candidate_handoff_failed",
    }


def _run_dedup_screening_queue(project_root: Path) -> dict[str, Any]:
    _ensure_literature_pair(project_root)
    dedup = DedupReviewV2Service()
    queue = dedup.build_review_queue(project_root, project_id=project_root.name)
    for group in queue.groups:
        dedup.save_decision(project_root, group_id=group.group_id, decision=DECISION_KEEP_BOTH, actor="release_connection_probe")
    deduplicated = dedup.generate_deduplicated_set(project_root, project_id=project_root.name)
    screening = TitleAbstractScreeningV2Service()
    screening_result = screening.build_queue(project_root, project_id=project_root.name)
    status = "passed" if screening_result.record_count > 0 else "blocked"
    return {
        "status": status,
        "services_called": (
            "DedupReviewV2Service.build_review_queue",
            "DedupReviewV2Service.save_decision",
            "DedupReviewV2Service.generate_deduplicated_set",
            "TitleAbstractScreeningV2Service.build_queue",
        ),
        "artifact_paths": _paths((dedup.review_queue_path(project_root), dedup.decisions_path(project_root), dedup.deduplicated_set_path(project_root), screening.queue_path(project_root))),
        "backend_results": {
            "duplicate_group_count": queue.group_count,
            "deduplicated_count": deduplicated.get("deduplicated_count", 0),
            "screening_record_count": screening_result.record_count,
            "screening_warnings": list(screening_result.warnings),
        },
        "disabled_reason": "" if status == "passed" else "no_literature_records_available_for_screening",
    }


def _run_extraction_quality_gate(project_root: Path) -> dict[str, Any]:
    _run_dedup_screening_queue(project_root)
    screening = TitleAbstractScreeningV2Service()
    queue = screening.load_queue(project_root)
    records = [item for item in queue.get("queue_records", []) if isinstance(item, dict)]
    if not records:
        return {
            "status": "blocked",
            "services_called": ("TitleAbstractScreeningV2Service.load_queue",),
            "artifact_paths": (),
            "backend_results": {"queue_record_count": 0},
            "disabled_reason": "screening_queue_empty",
        }
    first = records[0]
    decision = screening.save_decision(project_root, record_id=str(first.get("record_id", "")), decision=DECISION_INCLUDE, actor="release_connection_probe", notes="Release connection probe include decision.")
    extraction = ExtractionFormService()
    draft_path = extraction.save_draft(
        project_root,
        project_id=project_root.name,
        record_id=str(first.get("record_id", "")),
        form_data={
            "record_id": str(first.get("record_id", "")),
            "study_id": "release-probe-study",
            "reviewer_id": "release_connection_probe",
            "profile_type": "treatment_effect_meta",
            "outcome_name": "release_probe_outcome",
            "effect_measure": "OR",
        },
        draft_id="release_connection_extraction_draft",
    )
    completeness = extraction.pre_export_completeness_check(project_root)
    quality_path = project_root / "extraction" / "release_connection_quality_gate.json"
    _write_json(quality_path, {"decision": decision.__dict__, "completeness": completeness})
    return {
        "status": "blocked",
        "services_called": (
            "TitleAbstractScreeningV2Service.save_decision",
            "ExtractionFormService.save_draft",
            "ExtractionFormService.pre_export_completeness_check",
        ),
        "artifact_paths": _paths((screening.decisions_path(project_root), screening.compatible_decisions_path(project_root), draft_path, quality_path)),
        "backend_results": {
            "screening_decision_success": decision.success,
            "extraction_draft_path": str(draft_path),
            "ready_for_export": completeness.get("ready_for_export", False),
            "record_count": completeness.get("record_count", 0),
        },
        "disabled_reason": "validated_extraction_records_required_for_formal_analysis",
    }


def _run_statistics_report_gate(project_root: Path) -> dict[str, Any]:
    analysis = AnalysisSetupService()
    plan = analysis.create_plan(
        project_root,
        profile_type="treatment_effect_meta",
        outcome_name="release_probe_outcome",
        effect_measure="OR",
        model="random",
    )
    preflight = analysis.run_preflight(project_root, plan)
    prisma = PRISMAService()
    prisma_summary = prisma.collect_prisma_numbers(project_root)
    prisma_path = prisma.save_prisma_flow_summary(project_root, prisma_summary)
    prisma_md = prisma.export_prisma_flow_markdown(project_root, prisma_summary)
    manifest_path = ReportManifestService().save_report_manifest(project_root)
    report_path = FormalMarkdownReportBuilder().build_draft_markdown_report(project_root)
    status = "passed" if preflight.success and not preflight.errors else "blocked"
    blockers = list(preflight.errors)
    if not preflight.success and not blockers:
        blockers.append("analysis_preflight_not_ready")
    return {
        "status": status,
        "services_called": (
            "AnalysisSetupService.create_plan",
            "AnalysisSetupService.run_preflight",
            "PRISMAService.collect_prisma_numbers",
            "PRISMAService.save_prisma_flow_summary",
            "ReportManifestService.save_report_manifest",
            "FormalMarkdownReportBuilder.build_draft_markdown_report",
        ),
        "artifact_paths": _paths((*preflight.output_paths.values(), prisma_path, prisma_md, manifest_path, report_path)),
        "backend_results": {
            "preflight_success": preflight.success,
            "warnings": preflight.warnings,
            "errors": preflight.errors,
            "report_ready": status == "passed",
            "draft_report_path": str(report_path),
        },
        "disabled_reason": "" if status == "passed" else ";".join(blockers),
    }


def _ensure_literature_pair(project_root: Path) -> None:
    records = LiteratureLibraryService().list_records(project_root)
    pmids = {str(record.get("pmid", "")) for record in records}
    if "99999901" not in pmids or len(records) < 2:
        _run_candidate_handoff_bridge(project_root)
        _run_multisource_import_recognition(project_root)


def _write_fixture_csv(project_root: Path) -> Path:
    path = project_root / "literature" / "connection_fixtures" / "release_import.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("title", "abstract", "authors", "journal", "year", "doi", "pmid"))
        writer.writeheader()
        writer.writerow(
            {
                "title": "Release connection validation study",
                "abstract": "A local fixture record used to validate Meta literature import recognition.",
                "authors": "Release Probe",
                "journal": "BioMedPilot Fixture Journal",
                "year": "2026",
                "doi": "10.5555/release-connection",
                "pmid": "99999901",
            }
        )
    return path


def _fixture_pubmed_execution() -> PubMedSearchExecution:
    record = PubMedSearchResult(
        pmid="99999901",
        doi="10.5555/release-connection",
        title="Release connection validation study",
        journal="BioMedPilot Fixture Journal",
        year="2026",
        publication_date="2026-05-28",
        authors=("Release Probe",),
        abstract="A local fixture record used to validate Meta PubMed candidate handoff.",
        snippet="Release connection validation study",
        url="https://pubmed.ncbi.nlm.nih.gov/99999901/",
        query_used="release connection validation meta analysis",
    )
    return PubMedSearchExecution(
        success=True,
        query_used=record.query_used,
        executed_at=_now(),
        result_count=1,
        returned_count=1,
        records=(record,),
        dedup_summary={"unique_pmids": 1, "duplicate_pmids": 0},
        warnings=("fixture_fetcher_no_live_network",),
        search_execution_id="pubmedexec-release-connection",
    )


def _fixture_pubmed_fetcher(url: str, _timeout: float) -> bytes:
    if "esearch.fcgi" in url:
        return json.dumps({"esearchresult": {"idlist": ["99999901"]}}).encode("utf-8")
    xml = """
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>99999901</PMID>
          <Article>
            <ArticleTitle>Release connection validation study</ArticleTitle>
            <Journal><Title>BioMedPilot Fixture Journal</Title><JournalIssue><PubDate><Year>2026</Year></PubDate></JournalIssue></Journal>
            <Abstract><AbstractText>A local fixture record used to validate Meta PubMed retrieval.</AbstractText></Abstract>
            <AuthorList><Author><LastName>Probe</LastName><ForeName>Release</ForeName></Author></AuthorList>
          </Article>
        </MedlineCitation>
        <PubmedData><ArticleIdList><ArticleId IdType="doi">10.5555/release-connection</ArticleId></ArticleIdList></PubmedData>
      </PubmedArticle>
    </PubmedArticleSet>
    """
    return xml.encode("utf-8")


def _row(action_id: str) -> MetaConnectionRow:
    for row in CONNECTION_ROWS:
        if row.action_id == action_id:
            return row
    raise KeyError(f"unknown_meta_release_action:{action_id}")


def _write_result(
    project_root: Path,
    *,
    action_id: str,
    status: str,
    services_called: tuple[str, ...],
    artifact_paths: tuple[str, ...],
    backend_results: dict[str, Any],
    disabled_reason: str = "",
    ui_page: str = "",
    backend_capability: str = "",
    branch_source: str = "",
    expected_test: str = "",
) -> dict[str, Any]:
    run_dir = project_root / "meta_analysis" / "connection_runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _safe_timestamp()
    run_path = run_dir / f"{action_id}_{timestamp}.json"
    latest_path = run_dir / f"{action_id}_latest.json"
    payload = {
        "schema_version": ACTION_RESULT_SCHEMA_VERSION,
        "action_id": action_id,
        "created_at": _now(),
        "status": status,
        "ui_page": ui_page or _row(action_id).ui_page,
        "backend_capability": backend_capability or _row(action_id).backend_capability,
        "branch_source": branch_source or _row(action_id).branch_source,
        "expected_test": expected_test or _row(action_id).expected_test,
        "services_called": list(services_called),
        "artifact_paths": list(artifact_paths),
        "backend_results": backend_results,
        "disabled_reason": disabled_reason,
        "action_artifact_path": str(run_path),
    }
    _write_json(run_path, payload)
    _write_json(latest_path, payload)
    return payload


def _paths(values: tuple[str | Path, ...]) -> tuple[str, ...]:
    paths: list[str] = []
    for value in values:
        if not value:
            continue
        path = Path(value).expanduser()
        if path.exists():
            paths.append(str(path))
    return tuple(paths)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
