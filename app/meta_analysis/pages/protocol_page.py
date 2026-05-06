from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.meta_analysis.models.protocol import ProjectProtocol
from app.meta_analysis.search import (
    MetaSearchStrategyDraft,
    PubMedCandidateHandoffResult,
    PubMedCandidatesHandoffService,
    PubMedSearchExecution,
    PubMedSearchService,
    build_meta_search_strategy_draft,
)
from app.meta_analysis.services.protocol_service import PROTOCOL_RELATIVE_PATHS, ProjectProtocolService
from app.meta_analysis.services.pico_workspace_service import (
    CONFIRMED_PROTOCOL_SCHEMA_VERSION,
    PICO_PROTOCOL_DRAFT_SCHEMA_VERSION,
    ConfirmedPICOProtocolV2,
    PICOProtocolDraftV2,
    PICOWorkspaceService,
)
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


SEARCH_STRATEGY_DRAFT_RELATIVE_PATH = "protocol/search_strategy_draft.json"
SEARCH_STRATEGY_AUDIT_RELATIVE_PATH = "protocol/search_strategy_audit.json"
SEARCH_STRATEGY_CONFIRMED_RELATIVE_PATH = "protocol/search_strategy_user_confirmed.json"
SEARCH_EXECUTION_REPORT_RELATIVE_PATH = "protocol/search_execution_report.json"


@dataclass(frozen=True)
class ProtocolPageState:
    title: str
    status_label: str
    description: str
    project_dir: str
    empty_state: str
    input_summary: str
    output_summary: str
    next_step: str
    testing_limitations: tuple[str, ...]
    protocol: ProjectProtocol | None
    readiness_status: str
    completeness_summary: str
    warnings: tuple[str, ...]
    output_paths: dict[str, str]
    search_strategy_preview: str
    search_strategy_summary: str
    search_execution_status: str
    local_model_status: str
    pico_workspace_schema_version: str = PICO_PROTOCOL_DRAFT_SCHEMA_VERSION
    pico_workspace_status: str = "not_started"
    pico_mode: str = ""
    pico_workspace_draft: PICOProtocolDraftV2 | None = None
    confirmed_protocol: ConfirmedPICOProtocolV2 | None = None
    confirmed_protocol_schema_version: str = CONFIRMED_PROTOCOL_SCHEMA_VERSION
    confirmed_protocol_summary: str = ""
    draft_protocol_path: str = ""
    confirmed_protocol_path: str = ""


def initial_protocol_page_state(project_dir: Path | None = None) -> ProtocolPageState:
    return ProtocolPageState(
        title="Protocol / Research Question",
        status_label="Testing / Developer Preview",
        description="记录 Meta 分析研究题目、研究问题、PICO/PICOS、目标方法类型和可复制的检索式草稿。",
        project_dir=str(project_dir.expanduser().resolve()) if project_dir else "",
        empty_state="尚未保存 review_protocol.json。请先填写核心 PICO/PICOS 字段并保存 draft。",
        input_summary="研究题目、review question、PICO/PICOS、primary outcome、planned databases。",
        output_summary="protocol/review_protocol.json、protocol/search_terms_draft.json、protocol/search_strategy_preview.md、protocol/protocol_summary.md。",
        next_step="保存并人工复核检索式草稿后，进入 Literature Import。",
        testing_limitations=(
            "本模块只生成 draft search strategy，不执行真实数据库检索。",
            "PubMed / Web of Science / Embase / CNKI 检索式必须由 reviewer 人工复核。",
        ),
        protocol=None,
        readiness_status="not_started",
        completeness_summary="No protocol artifact found.",
        warnings=("missing_protocol_artifact",),
        output_paths={},
        search_strategy_preview="",
        search_strategy_summary="",
        search_execution_status="draft_only",
        local_model_status="not_available",
        pico_workspace_status="not_started",
    )


def protocol_page_state_from_project(project_dir: Path, *, service: ProjectProtocolService | None = None) -> ProtocolPageState:
    service = service or ProjectProtocolService()
    project_dir = project_dir.expanduser().resolve()
    protocol = service.load_protocol(project_dir)
    paths = service.protocol_paths(project_dir)
    output_paths = {
        "review_protocol": paths.review_protocol,
        "search_terms_draft": paths.search_terms_draft,
        "search_strategy_preview": paths.search_strategy_preview,
        "protocol_summary": paths.protocol_summary,
        "search_strategy_draft": str(project_dir / SEARCH_STRATEGY_DRAFT_RELATIVE_PATH),
        "search_strategy_audit": str(project_dir / SEARCH_STRATEGY_AUDIT_RELATIVE_PATH),
        "search_strategy_user_confirmed": str(project_dir / SEARCH_STRATEGY_CONFIRMED_RELATIVE_PATH),
        "search_execution_report": str(project_dir / SEARCH_EXECUTION_REPORT_RELATIVE_PATH),
    }
    pico_workspace = PICOWorkspaceService()
    pico_draft = pico_workspace.load_draft(project_dir)
    confirmed_protocol = pico_workspace.load_confirmed(project_dir)
    output_paths.update(
        {
            "pico_workspace_draft": str(pico_workspace.draft_path(project_dir)),
            "pico_workspace_draft_versions": str(pico_workspace.draft_versions_path(project_dir)),
            "pico_workspace_confirmed": str(pico_workspace.confirmed_path(project_dir)),
            "pico_workspace_confirmed_versions": str(pico_workspace.confirmed_versions_path(project_dir)),
            "pico_workspace_manifest": str(pico_workspace.manifest_path(project_dir)),
        }
    )
    if protocol is None:
        state = initial_protocol_page_state(project_dir)
        return ProtocolPageState(
            **{
                **state.__dict__,
                "output_paths": output_paths,
                "pico_workspace_status": "confirmed" if confirmed_protocol else ("draft" if pico_draft else "not_started"),
                "pico_mode": pico_draft.pico_mode if pico_draft else "",
                "pico_workspace_draft": pico_draft,
                "confirmed_protocol": confirmed_protocol,
                "confirmed_protocol_summary": _confirmed_protocol_summary(confirmed_protocol),
                "draft_protocol_path": output_paths["pico_workspace_draft"],
                "confirmed_protocol_path": output_paths["pico_workspace_confirmed"],
            }
        )
    preview_path = Path(paths.search_strategy_preview)
    preview = preview_path.read_text(encoding="utf-8") if preview_path.exists() else ""
    search_draft_path = project_dir / SEARCH_STRATEGY_DRAFT_RELATIVE_PATH
    search_payload = _load_json_object(search_draft_path)
    search_summary = _search_strategy_summary_from_payload(search_payload)
    missing_core = [warning for warning in protocol.warnings if warning.startswith("missing_")]
    completeness = "Core protocol fields complete." if not missing_core else f"Missing core fields: {', '.join(missing_core)}."
    return ProtocolPageState(
        title="Protocol / Research Question",
        status_label="Testing / Developer Preview",
        description="当前页面显示本地 protocol artifact、PICO/PICOS 完整性、检索式草稿路径和 reviewer warning。",
        project_dir=str(project_dir),
        empty_state="",
        input_summary="读取 protocol/review_protocol.json 中的研究问题、PICO/PICOS、方法类型和数据库计划。",
        output_summary="写入 protocol/review_protocol.json、search_terms_draft.json、search_strategy_preview.md 和 protocol_summary.md。",
        next_step="如果 readiness 为 ready/completed，请进入 Literature Import；如果有 warnings，请先人工补全 protocol。",
        testing_limitations=(
            "Developer Preview：检索式是 draft，不是投稿级最终检索式。",
            "当前仅生成检索式草稿，尚未执行在线检索。",
        ),
        protocol=protocol,
        readiness_status=protocol.readiness_status,
        completeness_summary=completeness,
        warnings=protocol.warnings,
        output_paths=output_paths,
        search_strategy_preview=preview,
        search_strategy_summary=search_summary,
        search_execution_status=str(search_payload.get("search_execution_status") or "draft_only"),
        local_model_status=str(search_payload.get("local_model_status") or "not_available"),
        pico_workspace_status="confirmed" if confirmed_protocol else ("draft" if pico_draft else "not_started"),
        pico_mode=pico_draft.pico_mode if pico_draft else "",
        pico_workspace_draft=pico_draft,
        confirmed_protocol=confirmed_protocol,
        confirmed_protocol_summary=_confirmed_protocol_summary(confirmed_protocol),
        draft_protocol_path=output_paths["pico_workspace_draft"],
        confirmed_protocol_path=output_paths["pico_workspace_confirmed"],
    )


def build_pico_workspace_draft(
    project_dir: Path,
    research_question: str,
    *,
    pico_mode: str = "auto",
    service: PICOWorkspaceService | None = None,
) -> PICOProtocolDraftV2:
    service = service or PICOWorkspaceService()
    return service.generate_draft(project_dir, research_question, pico_mode=pico_mode)


def confirm_pico_workspace_protocol(
    project_dir: Path,
    *,
    actor: str,
    confirmed_meta_type: str,
    service: PICOWorkspaceService | None = None,
    user_notes: str = "",
) -> ConfirmedPICOProtocolV2:
    service = service or PICOWorkspaceService()
    return service.confirm_protocol(project_dir, actor=actor, confirmed_meta_type=confirmed_meta_type, user_notes=user_notes)


def build_protocol_search_strategy_draft(values: dict[str, object]) -> MetaSearchStrategyDraft:
    question = _search_question_from_values(values)
    return build_meta_search_strategy_draft(
        question,
        population=str(values.get("population") or ""),
        intervention_or_exposure=str(values.get("intervention_or_exposure") or ""),
        comparator=str(values.get("comparator") or ""),
        outcome=str(values.get("primary_outcome") or values.get("outcomes") or ""),
        study_design=str(values.get("study_design") or ""),
    )


def write_protocol_search_strategy_artifacts(project_dir: Path, draft: MetaSearchStrategyDraft) -> dict[str, str]:
    project_dir = project_dir.expanduser().resolve()
    draft_path = project_dir / SEARCH_STRATEGY_DRAFT_RELATIVE_PATH
    audit_path = project_dir / SEARCH_STRATEGY_AUDIT_RELATIVE_PATH
    _write_json(draft_path, draft.to_dict())
    MetaResearchGovernanceService().record_draft_created(
        project_dir,
        target_type="final_search_strategy",
        target_id="multi_database_search_strategy",
        after=draft.to_dict(),
        metadata={
            "search_execution_status": draft.search_execution_status,
            "databases": [item.database for item in draft.query_drafts],
        },
    )
    _write_json(
        audit_path,
        {
            "schema_version": "meta_search_strategy_audit.v1",
            "target_context": draft.target_context,
            "local_model_status": draft.local_model_status,
            "search_execution_status": draft.search_execution_status,
            "query_draft_count": len(draft.query_drafts),
            "concept_group_count": len(draft.concept_groups),
            "audit": draft.audit,
            "warning_count": len(draft.warnings),
        },
    )
    return {
        "search_strategy_draft": str(draft_path),
        "search_strategy_audit": str(audit_path),
    }


def execute_protocol_pubmed_search(
    project_dir: Path,
    query: str,
    *,
    service: PubMedSearchService | None = None,
    max_results: int = 20,
) -> dict[str, str]:
    project_dir = project_dir.expanduser().resolve()
    service = service or PubMedSearchService()
    execution = service.search_pubmed(query, max_results=max_results)
    return write_pubmed_search_execution_artifacts(project_dir, query, execution)


def write_pubmed_search_execution_artifacts(
    project_dir: Path,
    query: str,
    execution: PubMedSearchExecution,
) -> dict[str, str]:
    project_dir = project_dir.expanduser().resolve()
    confirmed_path = project_dir / SEARCH_STRATEGY_CONFIRMED_RELATIVE_PATH
    report_path = project_dir / SEARCH_EXECUTION_REPORT_RELATIVE_PATH
    confirmation_payload = {
        "schema_version": "meta_search_strategy_user_confirmed.v1",
        "database": "PubMed",
        "query_used": query.strip(),
        "confirmed_at": execution.executed_at,
        "user_action": "confirm_and_search_pubmed",
        "wos_status": "draft_only",
        "embase_status": "draft_only",
        "cnki_status": "draft_only",
    }
    _write_json(
        confirmed_path,
        confirmation_payload,
    )
    _write_json(report_path, execution.to_report())
    preview = PubMedCandidatesHandoffService().create_candidates_preview(
        project_dir,
        execution=execution,
        execution_report_path=str(report_path.relative_to(project_dir)),
        search_strategy_snapshot_path=str(confirmed_path.relative_to(project_dir)),
    )
    MetaResearchGovernanceService().record_user_confirmation(
        project_dir,
        action="confirm",
        actor="reviewer",
        target_type="final_search_strategy",
        target_id="pubmed_query",
        before={"query": query.strip(), "status": "draft"},
        after=confirmation_payload,
        metadata={
            "search_execution_status": "confirmed_pubmed_execution",
            "literature_import_status": "not_imported",
            "screening_status": "not_started",
            "wos_status": "draft_only",
            "embase_status": "draft_only",
            "cnki_status": "draft_only",
        },
    )
    return {
        "search_strategy_user_confirmed": str(confirmed_path),
        "search_execution_report": str(report_path),
        "pubmed_candidates_preview": str(PubMedCandidatesHandoffService().preview_path(project_dir, preview.preview_id)),
    }


def render_pubmed_search_execution_summary(execution: PubMedSearchExecution) -> str:
    record_lines = [
        f"- candidate_id=pcand-{record.pmid} | PMID {record.pmid}: {record.title} | {record.journal} | {record.year} | query_used={record.query_used}"
        for record in execution.records
    ]
    return "\n".join(
        [
            "PubMed search execution:",
            f"success={execution.success}",
            f"result_count={execution.result_count}",
            f"returned_count={execution.returned_count}",
            f"query_used={execution.query_used}",
            "",
            "Literature candidates:",
            *(record_lines or ["none"]),
            "",
            "WOS/Embase/CNKI remain draft-only.",
            "No literature is auto-imported or auto-screened. Use explicit candidate selection before import.",
        ]
    )


def render_pubmed_candidate_handoff_summary(result: PubMedCandidateHandoffResult) -> str:
    record_lines = [
        f"- {record.get('record_id', '')}: PMID {record.get('pmid', '')} | {record.get('title', '')} | screening_status={record.get('screening_status', '')} | dedup_status={record.get('dedup_status', '')}"
        for record in result.imported_records
    ]
    return "\n".join(
        [
            "PubMed candidate handoff:",
            f"success={result.success}",
            f"import_batch_id={result.import_batch_id}",
            f"selected_count={result.selected_count}",
            f"rejected_count={result.rejected_count}",
            f"imported_count={result.imported_count}",
            f"literature_records_path={result.literature_records_path}",
            f"dedup_queue_path={result.dedup_queue_path}",
            "",
            "Imported records:",
            *(record_lines or ["none"]),
            "",
            "No title/abstract screening is created. PRISMA included/screened/full-text numbers are not advanced.",
        ]
    )


def render_search_strategy_summary(draft: MetaSearchStrategyDraft) -> str:
    concept_lines = [
        f"- {group.label}: " + (", ".join(group.all_terms) or "empty")
        for group in draft.concept_groups
    ]
    return "\n".join(
        [
            f"PICO/PECO mode: {draft.review_framework}",
            f"target_context: {draft.target_context}",
            f"local_model_status: {draft.local_model_status}",
            f"search_execution_status={draft.search_execution_status}",
            "",
            "Concept blocks:",
            *concept_lines,
            "",
            "PubMed query draft (MeSH + tiab):",
            draft.pubmed_query_draft or "empty",
            "",
            "WOS query draft (draft-only):",
            draft.web_of_science_query_draft or "empty",
            "",
            "Embase query draft (draft-only):",
            draft.embase_query_draft or "empty",
            "",
            "CNKI query draft (draft-only):",
            draft.cnki_query_draft or "empty",
            "",
            "Warnings:",
            ", ".join(draft.warnings) if draft.warnings else "none",
            "",
            "No live literature search is executed. search_execution_report.json is not written.",
            "当前仅生成检索式草稿，尚未执行在线检索。",
        ]
    )


def render_pico_workspace_draft_summary(draft: PICOProtocolDraftV2) -> str:
    meta_types = [str(item.get("meta_type", "")) for item in draft.meta_type_candidates[:3]]
    return "\n".join(
        [
            "PICO/PICOS/PECO draft",
            f"schema_version={draft.schema_version}",
            f"status={draft.status}",
            f"mode={draft.pico_mode}",
            f"population={draft.population}",
            f"intervention={draft.intervention}",
            f"exposure={draft.exposure}",
            f"comparator={draft.comparator}",
            f"outcome={draft.outcome}",
            f"study_design={draft.study_design}",
            f"meta_type_candidates={', '.join(meta_types)}",
            f"warnings={', '.join(draft.warnings) if draft.warnings else 'none'}",
            "需要人工确认",
            "不会自动执行检索、筛选或 PRISMA。",
        ]
    )


def _search_question_from_values(values: dict[str, object]) -> str:
    fields = (
        values.get("review_question"),
        values.get("project_title"),
        values.get("population"),
        values.get("intervention_or_exposure"),
        values.get("comparator"),
        values.get("outcomes"),
        values.get("primary_outcome"),
        values.get("study_design"),
    )
    return " ".join(str(value).strip() for value in fields if str(value).strip())


def _first_meta_type_candidate(draft: PICOProtocolDraftV2) -> str:
    for item in draft.meta_type_candidates:
        meta_type = str(item.get("meta_type", ""))
        if meta_type and meta_type != "network_meta_coming_soon":
            return meta_type
    return "treatment_comparative_meta"


def _search_strategy_summary_from_payload(payload: dict[str, object]) -> str:
    if not payload:
        return ""
    concept_groups = [
        f"- {item.get('label')}: "
        + ", ".join(
            [
                *[str(value) for value in item.get("terms_zh", []) if str(value).strip()],
                *[str(value) for value in item.get("terms_en", []) if str(value).strip()],
                *[str(value) for value in item.get("mesh_terms", []) if str(value).strip()],
            ]
        )
        for item in payload.get("concept_groups", [])
        if isinstance(item, dict)
    ]
    query_by_database = {
        str(item.get("database")): str(item.get("query") or "")
        for item in payload.get("query_drafts", [])
        if isinstance(item, dict)
    }
    return "\n".join(
        [
            f"PICO/PECO mode: {payload.get('review_framework', '')}",
            f"target_context: {payload.get('target_context', '')}",
            f"local_model_status: {payload.get('local_model_status', '')}",
            f"search_execution_status={payload.get('search_execution_status', '')}",
            "",
            "Concept blocks:",
            *concept_groups,
            "",
            "PubMed query draft (MeSH + tiab):",
            query_by_database.get("pubmed", ""),
            "",
            "WOS query draft (draft-only):",
            query_by_database.get("web_of_science", ""),
            "",
            "Embase query draft (draft-only):",
            query_by_database.get("embase", ""),
            "",
            "CNKI query draft (draft-only):",
            query_by_database.get("cnki", ""),
        ]
    )


def _confirmed_protocol_summary(protocol: ConfirmedPICOProtocolV2 | None) -> str:
    if protocol is None:
        return "需要人工确认"
    return "\n".join(
        [
            "已确认",
            f"mode={protocol.confirmed_pico_mode}",
            f"meta_type={protocol.confirmed_meta_type}",
            f"locked_for_search_strategy={protocol.locked_for_search_strategy}",
            "不会自动执行检索、筛选或 PRISMA。",
        ]
    )


def _load_json_object(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _pubmed_query_from_project(project_dir: Path) -> str:
    payload = _load_json_object(project_dir / SEARCH_STRATEGY_DRAFT_RELATIVE_PATH)
    for item in payload.get("query_drafts", []):
        if isinstance(item, dict) and item.get("database") == "pubmed":
            return str(item.get("query") or "")
    return ""


def _latest_pubmed_candidate_preview_id(project_dir: Path) -> str:
    preview_dir = project_dir.expanduser().resolve() / "protocol" / "pubmed_candidates"
    previews = sorted(preview_dir.glob("*_candidates_preview.json"), key=lambda path: path.stat().st_mtime)
    if not previews:
        return ""
    return previews[-1].name.replace("_candidates_preview.json", "")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


try:
    from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout, QWidget
except Exception:  # pragma: no cover
    QLabel = QLineEdit = QPushButton = QTextEdit = QVBoxLayout = QWidget = None


if QWidget is not None:

    class ProtocolPage(QWidget):
        def __init__(self) -> None:
            super().__init__()
            self._service = ProjectProtocolService()
            self._pico_workspace = PICOWorkspaceService()
            self._state = initial_protocol_page_state()
            root = QVBoxLayout(self)
            title = QLabel(f"{self._state.title} · {self._state.status_label}")
            title.setStyleSheet("font-size: 18px; font-weight: 700;")
            root.addWidget(title)
            description = QLabel(self._state.description)
            description.setWordWrap(True)
            root.addWidget(description)
            self._project_dir = QLineEdit()
            self._project_dir.setPlaceholderText("Meta project directory")
            root.addWidget(self._project_dir)
            self._project_title = QLineEdit()
            self._project_title.setPlaceholderText("研究题目")
            root.addWidget(self._project_title)
            self._review_question = QTextEdit()
            self._review_question.setPlaceholderText("研究问题 / review question")
            self._review_question.setMaximumHeight(90)
            root.addWidget(self._review_question)
            self._pico = QTextEdit()
            self._pico.setPlaceholderText("PICO/PICOS：population; intervention/exposure; comparator; outcomes; study design")
            self._pico.setMaximumHeight(100)
            root.addWidget(self._pico)
            self._method_profile = QLineEdit()
            self._method_profile.setPlaceholderText("Method profile, e.g. TREATMENT_EFFECT_META")
            root.addWidget(self._method_profile)
            self._pico_mode = QLineEdit()
            self._pico_mode.setPlaceholderText("PICO / PICOS / PECO，留空自动判断")
            root.addWidget(self._pico_mode)
            save = QPushButton("生成 PICO 草稿")
            save.clicked.connect(self._save)
            root.addWidget(save)
            confirm_protocol = QPushButton("确认研究问题")
            confirm_protocol.clicked.connect(self._confirm_research_question)
            root.addWidget(confirm_protocol)
            self._summary = QLabel(self._state.empty_state)
            self._summary.setWordWrap(True)
            root.addWidget(self._summary)
            self._pico_workspace_summary = QTextEdit()
            self._pico_workspace_summary.setObjectName("metaPicoWorkspaceDraftPreview")
            self._pico_workspace_summary.setReadOnly(True)
            self._pico_workspace_summary.setPlaceholderText("PICO/PICOS/PECO draft will appear here. 需要人工确认。")
            root.addWidget(self._pico_workspace_summary)
            self._search_strategy_summary = QTextEdit()
            self._search_strategy_summary.setObjectName("metaSearchStrategyDraftPreview")
            self._search_strategy_summary.setReadOnly(True)
            self._search_strategy_summary.setPlaceholderText("Search strategy draft will appear after saving the protocol.")
            root.addWidget(self._search_strategy_summary)
            execute_pubmed = QPushButton("确认并检索 PubMed")
            execute_pubmed.clicked.connect(self._execute_pubmed)
            root.addWidget(execute_pubmed)
            self._pubmed_execution_summary = QTextEdit()
            self._pubmed_execution_summary.setObjectName("metaPubMedSearchExecutionPreview")
            self._pubmed_execution_summary.setReadOnly(True)
            self._pubmed_execution_summary.setPlaceholderText("Confirmed PubMed search results will appear here.")
            root.addWidget(self._pubmed_execution_summary)
            self._selected_pubmed_candidates = QLineEdit()
            self._selected_pubmed_candidates.setObjectName("metaSelectedPubMedCandidateIds")
            self._selected_pubmed_candidates.setPlaceholderText("选中文献 candidate_id 或 PMID，逗号分隔")
            root.addWidget(self._selected_pubmed_candidates)
            import_pubmed = QPushButton("导入选中文献")
            import_pubmed.clicked.connect(self._import_selected_pubmed_candidates)
            root.addWidget(import_pubmed)
            self._pubmed_handoff_summary = QTextEdit()
            self._pubmed_handoff_summary.setObjectName("metaPubMedCandidateHandoffPreview")
            self._pubmed_handoff_summary.setReadOnly(True)
            self._pubmed_handoff_summary.setPlaceholderText("Selected PubMed candidates will be imported into the literature library only after explicit reviewer selection.")
            root.addWidget(self._pubmed_handoff_summary)
            self._last_pubmed_query = ""
            self._last_candidate_preview_id = ""

        def _save(self) -> None:
            self.generate_pico_workspace_draft()
            self.save_protocol_draft()

        def _execute_pubmed(self) -> None:
            self.execute_confirmed_pubmed_search()

        def _import_selected_pubmed_candidates(self) -> None:
            self.import_selected_pubmed_candidates()

        def _confirm_research_question(self) -> None:
            self.confirm_research_question()

        def generate_pico_workspace_draft(self) -> PICOProtocolDraftV2:
            project_dir = Path(self._project_dir.text()).expanduser()
            draft = self._pico_workspace.generate_draft(
                project_dir,
                self._review_question.toPlainText(),
                pico_mode=self._pico_mode.text() or "auto",
            )
            self._pico_workspace_summary.setPlainText(render_pico_workspace_draft_summary(draft))
            return draft

        def confirm_research_question(
            self,
            *,
            confirmed_meta_type: str = "",
            actor: str = "reviewer",
        ) -> ConfirmedPICOProtocolV2:
            project_dir = Path(self._project_dir.text()).expanduser()
            draft = self._pico_workspace.load_draft(project_dir) or self.generate_pico_workspace_draft()
            meta_type = confirmed_meta_type or _first_meta_type_candidate(draft)
            confirmed = self._pico_workspace.confirm_protocol(
                project_dir,
                actor=actor,
                confirmed_meta_type=meta_type,
                user_notes="Confirmed from Protocol page.",
            )
            self._pico_workspace_summary.setPlainText(_confirmed_protocol_summary(confirmed))
            self._summary.setText(
                "已确认研究问题\n"
                f"confirmed_protocol: {self._pico_workspace.confirmed_path(project_dir)}\n"
                f"mode={confirmed.confirmed_pico_mode}\n"
                f"meta_type={confirmed.confirmed_meta_type}\n"
                "下一步：生成检索策略\n"
                "不会自动执行检索、筛选或 PRISMA。"
            )
            return confirmed

        def save_protocol_draft(self) -> MetaSearchStrategyDraft:
            project_dir = Path(self._project_dir.text()).expanduser()
            pico_parts = [part.strip() for part in self._pico.toPlainText().split(";")]
            values = {
                "project_title": self._project_title.text(),
                "review_question": self._review_question.toPlainText(),
                "population": pico_parts[0] if len(pico_parts) > 0 else "",
                "intervention_or_exposure": pico_parts[1] if len(pico_parts) > 1 else "",
                "comparator": pico_parts[2] if len(pico_parts) > 2 else "",
                "outcomes": pico_parts[3] if len(pico_parts) > 3 else "",
                "study_design": pico_parts[4] if len(pico_parts) > 4 else "",
                "primary_outcome": pico_parts[3] if len(pico_parts) > 3 else "",
                "meta_analysis_type": self._method_profile.text(),
                "method_profile_id": self._method_profile.text(),
            }
            result = self._service.save_protocol(project_dir, values)
            search_strategy = build_protocol_search_strategy_draft(values)
            search_paths = write_protocol_search_strategy_artifacts(project_dir, search_strategy)
            summary_text = render_search_strategy_summary(search_strategy)
            self._search_strategy_summary.setPlainText(summary_text)
            self._last_pubmed_query = search_strategy.pubmed_query_draft
            self._summary.setText(
                f"{result.message}\n"
                f"readiness: {result.protocol.readiness_status}\n"
                f"warnings: {', '.join(result.warnings) if result.warnings else 'none'}\n"
                f"preview: {result.artifact_paths.search_strategy_preview}\n"
                f"search_strategy_draft: {search_paths['search_strategy_draft']}\n"
                f"search_strategy_audit: {search_paths['search_strategy_audit']}\n"
                f"local_model_status: {search_strategy.local_model_status}\n"
                f"search_execution_status={search_strategy.search_execution_status}"
            )
            return search_strategy

        def execute_confirmed_pubmed_search(
            self,
            *,
            service: PubMedSearchService | None = None,
            max_results: int = 20,
        ) -> PubMedSearchExecution:
            project_dir = Path(self._project_dir.text()).expanduser()
            query = self._last_pubmed_query or _pubmed_query_from_project(project_dir)
            service = service or PubMedSearchService()
            execution = service.search_pubmed(query, max_results=max_results)
            paths = write_pubmed_search_execution_artifacts(project_dir, query, execution)
            summary = render_pubmed_search_execution_summary(execution)
            self._pubmed_execution_summary.setPlainText(summary)
            preview_path = Path(paths["pubmed_candidates_preview"])
            self._last_candidate_preview_id = preview_path.name.replace("_candidates_preview.json", "")
            self._summary.setText(
                f"PubMed search_execution_report: {paths['search_execution_report']}\n"
                f"search_strategy_user_confirmed: {paths['search_strategy_user_confirmed']}\n"
                f"pubmed_candidates_preview: {paths['pubmed_candidates_preview']}\n"
                f"result_count={execution.result_count}\n"
                f"returned_count={execution.returned_count}\n"
                "WOS/Embase/CNKI remain draft-only.\n"
                "PubMed candidates are preview-only until selected and imported by reviewer."
            )
            return execution

        def import_selected_pubmed_candidates(
            self,
            *,
            selected_candidate_ids: tuple[str, ...] | None = None,
            rejected_candidate_ids: tuple[str, ...] = (),
            service: PubMedCandidatesHandoffService | None = None,
        ) -> PubMedCandidateHandoffResult:
            project_dir = Path(self._project_dir.text()).expanduser()
            service = service or PubMedCandidatesHandoffService()
            selected_ids = selected_candidate_ids or tuple(
                item.strip()
                for item in self._selected_pubmed_candidates.text().replace("\n", ",").split(",")
                if item.strip()
            )
            preview_id = self._last_candidate_preview_id or _latest_pubmed_candidate_preview_id(project_dir)
            result = service.import_selected_candidates(
                project_dir,
                preview_id=preview_id,
                selected_candidate_ids=selected_ids,
                rejected_candidate_ids=rejected_candidate_ids,
                actor="reviewer",
            )
            self._pubmed_handoff_summary.setPlainText(render_pubmed_candidate_handoff_summary(result))
            self._summary.setText(
                f"PubMed candidate handoff: {result.message}\n"
                f"literature_records: {result.literature_records_path or 'not_written'}\n"
                f"dedup_queue: {result.dedup_queue_path or 'not_written'}\n"
                "screening_status=not_started\n"
                "PRISMA included/screened/full-text numbers are not advanced."
            )
            return result

        def set_protocol_inputs(
            self,
            *,
            project_dir: Path,
            project_title: str,
            review_question: str,
            pico: str,
            method_profile: str,
            pico_mode: str = "",
        ) -> None:
            self._project_dir.setText(str(project_dir))
            self._project_title.setText(project_title)
            self._review_question.setPlainText(review_question)
            self._pico.setPlainText(pico)
            self._method_profile.setText(method_profile)
            self._pico_mode.setText(pico_mode)

        def search_strategy_summary_text(self) -> str:
            return self._search_strategy_summary.toPlainText()

        def pubmed_execution_summary_text(self) -> str:
            return self._pubmed_execution_summary.toPlainText()

        def pubmed_handoff_summary_text(self) -> str:
            return self._pubmed_handoff_summary.toPlainText()

        def pico_workspace_summary_text(self) -> str:
            return self._pico_workspace_summary.toPlainText()

else:

    class ProtocolPage:  # type: ignore[no-redef]
        pass
