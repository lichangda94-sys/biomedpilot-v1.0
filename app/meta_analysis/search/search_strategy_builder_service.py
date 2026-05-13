from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.search.strategy_builder import build_meta_search_strategy_draft
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.pico_workspace_service import ConfirmedPICOProtocolV2, PICOProtocolDraftV2, PICOWorkspaceService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


SEARCH_STRATEGY_DRAFT_SCHEMA_VERSION = "meta_search_strategy_draft.v2"
SEARCH_STRATEGY_DRAFT_SET_SCHEMA_VERSION = "meta_search_strategy_draft_set.v2"
CONFIRMED_SEARCH_STRATEGY_SCHEMA_VERSION = "meta_confirmed_search_strategy.v2"
CONFIRMED_SEARCH_STRATEGY_SET_SCHEMA_VERSION = "meta_confirmed_search_strategy_set.v2"
SEARCH_STRATEGY_MANIFEST_SCHEMA_VERSION = "meta_search_strategy_builder_manifest.v2"

DATABASE_PUBMED = "pubmed"
DATABASE_WOS = "web_of_science"
DATABASE_EMBASE = "embase"
DATABASE_COCHRANE = "cochrane"
DATABASE_CNKI = "cnki"
DATABASE_WANFANG = "wanfang"
DATABASE_VIP = "vip"

SEARCH_STRATEGY_DATABASES = (
    DATABASE_PUBMED,
    DATABASE_WOS,
    DATABASE_EMBASE,
    DATABASE_COCHRANE,
    DATABASE_CNKI,
    DATABASE_WANFANG,
    DATABASE_VIP,
)

_DATABASE_FAMILY = {
    DATABASE_PUBMED: "biomedical_bibliographic",
    DATABASE_WOS: "citation_index",
    DATABASE_EMBASE: "biomedical_bibliographic",
    DATABASE_COCHRANE: "evidence_database",
    DATABASE_CNKI: "chinese_literature",
    DATABASE_WANFANG: "chinese_literature",
    DATABASE_VIP: "chinese_literature",
}
_FORBIDDEN_META_TERMS = ("geo", "gse", "tcga", "gtex")


@dataclass(frozen=True)
class SearchStrategyDraftV2:
    search_strategy_id: str
    project_id: str
    source_confirmed_protocol_id: str
    database: str
    database_family: str
    controlled_terms: tuple[str, ...] = ()
    free_text_terms: tuple[str, ...] = ()
    chinese_terms: tuple[str, ...] = ()
    english_terms: tuple[str, ...] = ()
    boolean_query: str = ""
    field_tags: tuple[str, ...] = ()
    date_limits: str = ""
    study_type_filters: tuple[str, ...] = ()
    exclusion_terms: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    draft_source: str = "confirmed_pico_protocol_v2"
    created_at: str = ""
    updated_at: str = ""
    governance_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    version: int = 1
    status: str = "draft"
    search_execution_status: str = "draft_only"
    schema_version: str = SEARCH_STRATEGY_DRAFT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "controlled_terms",
            "free_text_terms",
            "chinese_terms",
            "english_terms",
            "field_tags",
            "study_type_filters",
            "exclusion_terms",
            "warnings",
            "governance_refs",
            "audit_refs",
        ):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True)
class ConfirmedSearchStrategyV2:
    confirmed_search_strategy_id: str
    source_draft_id: str
    database: str
    confirmed_query: str
    confirmed_terms: tuple[str, ...] = ()
    confirmed_at: str = ""
    confirmed_by: str = ""
    version: int = 1
    execution_allowed: bool = False
    execution_status: str = "not_executed"
    governance_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    schema_version: str = CONFIRMED_SEARCH_STRATEGY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confirmed_terms"] = list(self.confirmed_terms)
        payload["governance_refs"] = list(self.governance_refs)
        payload["audit_refs"] = list(self.audit_refs)
        return payload


@dataclass(frozen=True)
class SearchStrategyBuilderResultV2:
    success: bool
    project_id: str
    source_confirmed_protocol_id: str
    draft_count: int
    draft_path: str
    message: str
    drafts: tuple[SearchStrategyDraftV2, ...] = ()
    export_markdown_path: str = ""
    export_text_path: str = ""


class SearchStrategyBuilderService:
    def __init__(
        self,
        *,
        pico_workspace: PICOWorkspaceService | None = None,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
    ) -> None:
        self._pico_workspace = pico_workspace or PICOWorkspaceService()
        self._audit_log = audit_log or MetaAuditLogService()
        self._research_governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)

    def draft_set_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "search_strategy_v2" / "search_strategy_drafts.json"

    def draft_versions_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "search_strategy_v2" / "search_strategy_draft_versions.json"

    def confirmed_set_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "search_strategy_v2" / "search_strategy_confirmed.json"

    def confirmed_versions_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "search_strategy_v2" / "search_strategy_confirmed_versions.json"

    def manifest_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "search_strategy_v2" / "search_strategy_manifest.json"

    def markdown_export_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "search_strategy_v2" / "search_strategy_draft.md"

    def text_export_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "search_strategy_v2" / "search_strategy_draft.txt"

    def generate_from_confirmed_protocol(self, project_dir: Path, *, actor: str = "system") -> SearchStrategyBuilderResultV2:
        project_dir = project_dir.expanduser().resolve()
        confirmed_protocol = self._require_confirmed_protocol(project_dir)
        source_draft = self._pico_workspace.load_draft(project_dir)
        drafts = self._build_drafts(project_dir, confirmed_protocol, source_draft)
        governance = self._research_governance.record_draft_created(
            project_dir,
            project_id=project_dir.name,
            actor=actor,
            target_type="final_search_strategy",
            target_id=confirmed_protocol.confirmed_protocol_id,
            after={"source_confirmed_protocol_id": confirmed_protocol.confirmed_protocol_id, "databases": list(SEARCH_STRATEGY_DATABASES)},
            metadata={"search_execution_status": "draft_only", "confirmed_status": "not_confirmed"},
        )
        audit = self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_dir.name,
            actor=actor,
            target_type="search_strategy_draft_set_v2",
            target_id=confirmed_protocol.confirmed_protocol_id,
            source_path=str(self._pico_workspace.confirmed_path(project_dir).relative_to(project_dir)),
            output_path=str(self.draft_set_path(project_dir).relative_to(project_dir)),
            summary="Search strategy drafts generated from confirmed PICO protocol",
            details={"databases": list(SEARCH_STRATEGY_DATABASES), "search_execution_status": "draft_only"},
        )
        hydrated = tuple(
            SearchStrategyDraftV2(**{**draft.to_dict(), "governance_refs": (*draft.governance_refs, governance.event_id), "audit_refs": (*draft.audit_refs, audit.event_id)})
            for draft in drafts
        )
        self._write_draft_set(project_dir, hydrated, confirmed_protocol)
        for draft in hydrated:
            self._research_governance.record_suggestion_created(
                project_dir,
                project_id=project_dir.name,
                target_type="database_query",
                target_id=draft.search_strategy_id,
                after=draft.to_dict(),
                source_suggestion_id=confirmed_protocol.confirmed_protocol_id,
                metadata={"database": draft.database, "execution_status": draft.search_execution_status},
            )
        markdown_path, text_path = self.export_drafts(project_dir)
        self._write_manifest(project_dir)
        return SearchStrategyBuilderResultV2(
            success=True,
            project_id=project_dir.name,
            source_confirmed_protocol_id=confirmed_protocol.confirmed_protocol_id,
            draft_count=len(hydrated),
            draft_path=str(self.draft_set_path(project_dir)),
            message="Search strategy drafts generated from confirmed protocol. No search executed.",
            drafts=hydrated,
            export_markdown_path=str(markdown_path),
            export_text_path=str(text_path),
        )

    def edit_draft(
        self,
        project_dir: Path,
        *,
        search_strategy_id: str,
        updates: dict[str, Any],
        actor: str,
    ) -> SearchStrategyDraftV2:
        if not actor.strip():
            raise ValueError("actor_required_for_search_strategy_edit")
        project_dir = project_dir.expanduser().resolve()
        drafts = list(self.load_drafts(project_dir))
        if not drafts:
            raise ValueError("search_strategy_draft_set_not_found")
        edited: SearchStrategyDraftV2 | None = None
        next_drafts: list[SearchStrategyDraftV2] = []
        for draft in drafts:
            if draft.search_strategy_id != search_strategy_id:
                next_drafts.append(draft)
                continue
            payload = draft.to_dict()
            for key in (
                "controlled_terms",
                "free_text_terms",
                "chinese_terms",
                "english_terms",
                "boolean_query",
                "field_tags",
                "date_limits",
                "study_type_filters",
                "exclusion_terms",
                "warnings",
            ):
                if key in updates:
                    payload[key] = updates[key]
            payload["version"] = int(draft.version) + 1
            payload["updated_at"] = _now()
            payload["status"] = "draft"
            edited = _draft_from_payload(payload)
            governance = self._research_governance.record_user_confirmation(
                project_dir,
                project_id=edited.project_id,
                action="edit",
                actor=actor,
                target_type="database_query",
                target_id=edited.search_strategy_id,
                before=draft.to_dict(),
                after=edited.to_dict(),
                source_suggestion_id=draft.search_strategy_id,
                metadata={"database": edited.database, "confirmed_status": "not_confirmed"},
            )
            audit = self._audit_log.record_event(
                project_dir,
                event_type="record_saved",
                project_id=edited.project_id,
                actor=actor,
                target_type="search_strategy_draft_v2",
                target_id=edited.search_strategy_id,
                source_path=str(self.draft_set_path(project_dir).relative_to(project_dir)),
                output_path=str(self.draft_set_path(project_dir).relative_to(project_dir)),
                summary=f"Search strategy draft edited for {edited.database}",
                details={"database": edited.database, "version": edited.version, "execution_status": edited.search_execution_status},
            )
            edited = SearchStrategyDraftV2(
                **{
                    **edited.to_dict(),
                    "governance_refs": (*edited.governance_refs, governance.event_id),
                    "audit_refs": (*edited.audit_refs, audit.event_id),
                }
            )
            next_drafts.append(edited)
        if edited is None:
            raise ValueError(f"search_strategy_draft_not_found:{search_strategy_id}")
        confirmed_protocol = self._require_confirmed_protocol(project_dir)
        self._write_draft_set(project_dir, tuple(next_drafts), confirmed_protocol)
        self.export_drafts(project_dir)
        self._write_manifest(project_dir)
        return edited

    def confirm_strategies(
        self,
        project_dir: Path,
        *,
        actor: str,
        database_ids: tuple[str, ...] | None = None,
    ) -> tuple[ConfirmedSearchStrategyV2, ...]:
        if not actor.strip():
            raise ValueError("actor_required_for_search_strategy_confirmation")
        project_dir = project_dir.expanduser().resolve()
        drafts = self.load_drafts(project_dir)
        if not drafts:
            raise ValueError("search_strategy_draft_set_not_found")
        selected_databases = set(database_ids or SEARCH_STRATEGY_DATABASES)
        confirmed_items: list[ConfirmedSearchStrategyV2] = []
        for draft in drafts:
            if draft.database not in selected_databases and draft.search_strategy_id not in selected_databases:
                continue
            execution_allowed = draft.database == DATABASE_PUBMED
            confirmed = ConfirmedSearchStrategyV2(
                confirmed_search_strategy_id=f"search-confirmed-{draft.database}-{uuid4().hex[:10]}",
                source_draft_id=draft.search_strategy_id,
                database=draft.database,
                confirmed_query=draft.boolean_query,
                confirmed_terms=_safe_terms([*draft.controlled_terms, *draft.free_text_terms, *draft.chinese_terms, *draft.english_terms]),
                confirmed_at=_now(),
                confirmed_by=actor,
                version=self._next_confirmed_version(project_dir),
                execution_allowed=execution_allowed,
                execution_status="ready_for_pubmed_execution" if execution_allowed else "draft_only_manual_database_search",
            )
            governance = self._research_governance.record_user_confirmation(
                project_dir,
                project_id=draft.project_id,
                action="confirm",
                actor=actor,
                target_type="final_search_strategy",
                target_id=confirmed.confirmed_search_strategy_id,
                before=draft.to_dict(),
                after=confirmed.to_dict(),
                source_suggestion_id=draft.search_strategy_id,
                metadata={
                    "database": draft.database,
                    "execution_allowed": execution_allowed,
                    "auto_execution": False,
                    "literature_import_status": "not_imported",
                    "screening_status": "not_started",
                    "prisma_status": "not_updated",
                },
            )
            audit = self._audit_log.record_event(
                project_dir,
                event_type="record_saved",
                project_id=draft.project_id,
                actor=actor,
                target_type="confirmed_search_strategy_v2",
                target_id=confirmed.confirmed_search_strategy_id,
                source_path=str(self.draft_set_path(project_dir).relative_to(project_dir)),
                output_path=str(self.confirmed_set_path(project_dir).relative_to(project_dir)),
                summary=f"Search strategy confirmed for {draft.database}",
                details={"database": draft.database, "auto_execution": False, "execution_status": confirmed.execution_status},
            )
            confirmed = ConfirmedSearchStrategyV2(
                **{
                    **confirmed.to_dict(),
                    "governance_refs": (governance.event_id,),
                    "audit_refs": (audit.event_id,),
                }
            )
            confirmed_items.append(confirmed)
        self._write_confirmed_set(project_dir, tuple(confirmed_items))
        self._write_manifest(project_dir)
        return tuple(confirmed_items)

    def load_drafts(self, project_dir: Path) -> tuple[SearchStrategyDraftV2, ...]:
        payload = _load_json(self.draft_set_path(project_dir))
        items = payload.get("strategies", []) if isinstance(payload, dict) else []
        return tuple(_draft_from_payload(item) for item in items if isinstance(item, dict))

    def load_confirmed(self, project_dir: Path) -> tuple[ConfirmedSearchStrategyV2, ...]:
        payload = _load_json(self.confirmed_set_path(project_dir))
        items = payload.get("confirmed_strategies", []) if isinstance(payload, dict) else []
        return tuple(_confirmed_strategy_from_payload(item) for item in items if isinstance(item, dict))

    def export_drafts(self, project_dir: Path) -> tuple[Path, Path]:
        project_dir = project_dir.expanduser().resolve()
        drafts = self.load_drafts(project_dir)
        markdown = _render_markdown(drafts)
        text = _render_text(drafts)
        md_path = self.markdown_export_path(project_dir)
        txt_path = self.text_export_path(project_dir)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
        txt_path.write_text(text, encoding="utf-8")
        return md_path, txt_path

    def _require_confirmed_protocol(self, project_dir: Path) -> ConfirmedPICOProtocolV2:
        confirmed_protocol = self._pico_workspace.load_confirmed(project_dir)
        if confirmed_protocol is None:
            raise ValueError("confirmed_pico_protocol_v2_required")
        return confirmed_protocol

    def _build_drafts(
        self,
        project_dir: Path,
        confirmed: ConfirmedPICOProtocolV2,
        source_draft: PICOProtocolDraftV2 | None,
    ) -> tuple[SearchStrategyDraftV2, ...]:
        question = _source_question(confirmed, source_draft)
        strategy = build_meta_search_strategy_draft(
            question,
            population=confirmed.confirmed_population,
            intervention_or_exposure=confirmed.confirmed_intervention_or_exposure,
            comparator=confirmed.confirmed_comparator,
            outcome="; ".join(confirmed.confirmed_outcomes),
            study_design=confirmed.confirmed_study_design,
        )
        terms = _StrategyTerms(
            controlled_terms=_safe_terms(group_term for group in strategy.concept_groups for group_term in group.mesh_terms),
            english_terms=_safe_terms(group_term for group in strategy.concept_groups for group_term in group.terms_en),
            chinese_terms=_safe_terms([*(source_draft.disease_terms if source_draft else ()), *(source_draft.context_terms if source_draft else ()), *confirmed.confirmed_outcomes]),
            free_text_terms=_safe_terms(
                [
                    confirmed.confirmed_population,
                    confirmed.confirmed_intervention_or_exposure,
                    confirmed.confirmed_comparator,
                    *confirmed.confirmed_outcomes,
                    confirmed.confirmed_study_design,
                ]
            ),
        )
        now = _now()
        drafts = [
            self._draft_for_database(project_dir, confirmed, DATABASE_PUBMED, terms, _pubmed_query(terms, strategy.pubmed_query_draft), now),
            self._draft_for_database(project_dir, confirmed, DATABASE_WOS, terms, _wos_query(terms), now),
            self._draft_for_database(project_dir, confirmed, DATABASE_EMBASE, terms, _embase_query(terms), now),
            self._draft_for_database(project_dir, confirmed, DATABASE_COCHRANE, terms, _cochrane_query(terms), now),
            self._draft_for_database(project_dir, confirmed, DATABASE_CNKI, terms, _chinese_query(terms, field="主题"), now),
            self._draft_for_database(project_dir, confirmed, DATABASE_WANFANG, terms, _chinese_query(terms, field="题名或关键词"), now),
            self._draft_for_database(project_dir, confirmed, DATABASE_VIP, terms, _chinese_query(terms, field="题名/关键词/摘要"), now),
        ]
        return tuple(drafts)

    def _draft_for_database(
        self,
        project_dir: Path,
        confirmed: ConfirmedPICOProtocolV2,
        database: str,
        terms: "_StrategyTerms",
        query: str,
        now: str,
    ) -> SearchStrategyDraftV2:
        return SearchStrategyDraftV2(
            search_strategy_id=f"search-draft-{database}-{uuid4().hex[:10]}",
            project_id=project_dir.name,
            source_confirmed_protocol_id=confirmed.confirmed_protocol_id,
            database=database,
            database_family=_DATABASE_FAMILY[database],
            controlled_terms=terms.controlled_terms if database in {DATABASE_PUBMED, DATABASE_EMBASE} else (),
            free_text_terms=terms.free_text_terms,
            chinese_terms=terms.chinese_terms if database in {DATABASE_CNKI, DATABASE_WANFANG, DATABASE_VIP} else (),
            english_terms=terms.english_terms if database not in {DATABASE_CNKI, DATABASE_WANFANG, DATABASE_VIP} else (),
            boolean_query=query,
            field_tags=_field_tags(database),
            date_limits="reviewer_to_define",
            study_type_filters=_study_filters(confirmed.confirmed_study_design),
            exclusion_terms=("animals", "case report", "editorial", "letter", "review") if database not in {DATABASE_CNKI, DATABASE_WANFANG, DATABASE_VIP} else ("动物实验", "病例报告", "综述", "评论"),
            warnings=_warnings_for_database(database),
            created_at=now,
            updated_at=now,
            search_execution_status="draft_only",
        )

    def _write_draft_set(self, project_dir: Path, drafts: tuple[SearchStrategyDraftV2, ...], confirmed: ConfirmedPICOProtocolV2) -> None:
        payload = {
            "schema_version": SEARCH_STRATEGY_DRAFT_SET_SCHEMA_VERSION,
            "project_id": project_dir.name,
            "source_confirmed_protocol_id": confirmed.confirmed_protocol_id,
            "source_confirmed_protocol_path": str(self._pico_workspace.confirmed_path(project_dir).relative_to(project_dir)),
            "created_at": _now(),
            "search_execution_status": "draft_only",
            "auto_executed": False,
            "auto_imported": False,
            "screening_status": "not_started",
            "prisma_status": "not_updated",
            "databases": list(SEARCH_STRATEGY_DATABASES),
            "strategies": [draft.to_dict() for draft in drafts],
        }
        _write_json(self.draft_set_path(project_dir), payload)
        self._append_version(self.draft_versions_path(project_dir), payload, schema_version="meta_search_strategy_draft_versions.v2")

    def _write_confirmed_set(self, project_dir: Path, confirmed_items: tuple[ConfirmedSearchStrategyV2, ...]) -> None:
        payload = {
            "schema_version": CONFIRMED_SEARCH_STRATEGY_SET_SCHEMA_VERSION,
            "project_id": project_dir.name,
            "created_at": _now(),
            "auto_executed": False,
            "auto_imported": False,
            "screening_status": "not_started",
            "prisma_status": "not_updated",
            "confirmed_strategies": [item.to_dict() for item in confirmed_items],
        }
        _write_json(self.confirmed_set_path(project_dir), payload)
        self._append_version(self.confirmed_versions_path(project_dir), payload, schema_version="meta_confirmed_search_strategy_versions.v2")

    def _append_version(self, path: Path, item: dict[str, Any], *, schema_version: str) -> None:
        payload = _load_json(path) or {"schema_version": schema_version, "versions": []}
        versions = payload.get("versions", [])
        if not isinstance(versions, list):
            versions = []
        versions.append(item)
        _write_json(path, {"schema_version": schema_version, "versions": versions})

    def _next_confirmed_version(self, project_dir: Path) -> int:
        payload = _load_json(self.confirmed_versions_path(project_dir))
        versions = payload.get("versions", []) if isinstance(payload, dict) else []
        return len(versions) + 1 if isinstance(versions, list) else 1

    def _write_manifest(self, project_dir: Path) -> None:
        drafts = self.load_drafts(project_dir)
        confirmed = self.load_confirmed(project_dir)
        payload = {
            "schema_version": SEARCH_STRATEGY_MANIFEST_SCHEMA_VERSION,
            "project_id": project_dir.expanduser().resolve().name,
            "draft_set_path": str(self.draft_set_path(project_dir).relative_to(project_dir.expanduser().resolve())),
            "confirmed_set_path": str(self.confirmed_set_path(project_dir).relative_to(project_dir.expanduser().resolve())),
            "draft_count": len(drafts),
            "confirmed_count": len(confirmed),
            "databases": [draft.database for draft in drafts],
            "search_execution_status": "draft_only",
            "auto_executed": False,
            "auto_imported": False,
            "screening_status": "not_started",
            "prisma_status": "not_updated",
            "updated_at": _now(),
        }
        _write_json(self.manifest_path(project_dir), payload)


@dataclass(frozen=True)
class _StrategyTerms:
    controlled_terms: tuple[str, ...] = ()
    free_text_terms: tuple[str, ...] = ()
    chinese_terms: tuple[str, ...] = ()
    english_terms: tuple[str, ...] = ()


def _source_question(confirmed: ConfirmedPICOProtocolV2, source_draft: PICOProtocolDraftV2 | None) -> str:
    return " ".join(
        _safe_terms(
            [
                source_draft.research_question_original if source_draft else "",
                confirmed.confirmed_population,
                confirmed.confirmed_intervention_or_exposure,
                confirmed.confirmed_comparator,
                *confirmed.confirmed_outcomes,
                confirmed.confirmed_study_design,
                confirmed.confirmed_meta_type,
            ]
        )
    )


def _pubmed_query(terms: _StrategyTerms, fallback: str) -> str:
    return fallback or _and_blocks(
        [
            _or_block([*(f'"{term}"[Mesh]' for term in terms.controlled_terms), *(f'"{term}"[tiab]' for term in terms.english_terms)]),
            _or_block(f'"{term}"[tiab]' for term in terms.free_text_terms),
        ]
    )


def _wos_query(terms: _StrategyTerms) -> str:
    return _and_blocks(_ts_block(values) for values in _concept_blocks(terms, english=True))


def _embase_query(terms: _StrategyTerms) -> str:
    controlled = [f"'{term}'/exp" for term in terms.controlled_terms]
    free = [f'"{term}":ti,ab,kw' for term in [*terms.english_terms, *terms.free_text_terms]]
    return _or_block([*controlled, *free])


def _cochrane_query(terms: _StrategyTerms) -> str:
    blocks = []
    for values in _concept_blocks(terms, english=True):
        block = _or_block(f'"{term}":ti,ab,kw' for term in values)
        if block:
            blocks.append(block)
    return " AND ".join(blocks)


def _chinese_query(terms: _StrategyTerms, *, field: str) -> str:
    values = terms.chinese_terms or terms.free_text_terms
    blocks = [_or_block(values)]
    return " AND ".join(f"{field}=({block})" for block in blocks if block)


def _concept_blocks(terms: _StrategyTerms, *, english: bool) -> tuple[tuple[str, ...], ...]:
    values = terms.english_terms if english else terms.chinese_terms
    if not values:
        values = terms.free_text_terms
    midpoint = max(1, len(values) // 2)
    return (values[:midpoint], values[midpoint:]) if len(values) > 1 else (values,)


def _field_tags(database: str) -> tuple[str, ...]:
    return {
        DATABASE_PUBMED: ("MeSH", "tiab"),
        DATABASE_WOS: ("TS",),
        DATABASE_EMBASE: ("Emtree", "ti", "ab", "kw"),
        DATABASE_COCHRANE: ("title", "abstract", "keyword"),
        DATABASE_CNKI: ("主题", "篇名", "摘要", "关键词"),
        DATABASE_WANFANG: ("题名", "摘要", "关键词"),
        DATABASE_VIP: ("题名", "关键词", "摘要"),
    }[database]


def _study_filters(study_design: str) -> tuple[str, ...]:
    if not study_design:
        return ("reviewer_to_define",)
    return _safe_terms([study_design])


def _warnings_for_database(database: str) -> tuple[str, ...]:
    if database == DATABASE_PUBMED:
        return ("draft_requires_reviewer_confirmation", "pubmed_can_execute_after_explicit_confirmation")
    return ("draft_only", "manual_database_search_required", "no_online_execution_client")


def _render_markdown(drafts: tuple[SearchStrategyDraftV2, ...]) -> str:
    lines = ["# Search Strategy Draft v2", "", "Status: draft-only / requires reviewer confirmation.", ""]
    for draft in drafts:
        lines.extend(
            [
                f"## {draft.database}",
                "",
                f"- Schema: `{draft.schema_version}`",
                f"- Database family: {draft.database_family}",
                f"- Status: {draft.search_execution_status}",
                "",
                "```text",
                draft.boolean_query or "empty",
                "```",
                "",
            ]
        )
    lines.append("No search is executed, no literature is imported, and PRISMA is not updated.")
    return "\n".join(lines) + "\n"


def _render_text(drafts: tuple[SearchStrategyDraftV2, ...]) -> str:
    chunks = ["Search Strategy Draft v2", "draft-only / requires reviewer confirmation", ""]
    for draft in drafts:
        chunks.extend([f"[{draft.database}]", draft.boolean_query or "empty", ""])
    chunks.append("No search is executed. No import, screening, or PRISMA update is performed.")
    return "\n".join(chunks) + "\n"


def _draft_from_payload(payload: dict[str, Any]) -> SearchStrategyDraftV2:
    return SearchStrategyDraftV2(
        search_strategy_id=str(payload.get("search_strategy_id", "")),
        project_id=str(payload.get("project_id", "")),
        source_confirmed_protocol_id=str(payload.get("source_confirmed_protocol_id", "")),
        database=str(payload.get("database", "")),
        database_family=str(payload.get("database_family", "")),
        controlled_terms=tuple(_safe_terms(payload.get("controlled_terms", []))),
        free_text_terms=tuple(_safe_terms(payload.get("free_text_terms", []))),
        chinese_terms=tuple(_safe_terms(payload.get("chinese_terms", []))),
        english_terms=tuple(_safe_terms(payload.get("english_terms", []))),
        boolean_query=str(payload.get("boolean_query", "")),
        field_tags=tuple(_safe_terms(payload.get("field_tags", []))),
        date_limits=str(payload.get("date_limits", "")),
        study_type_filters=tuple(_safe_terms(payload.get("study_type_filters", []))),
        exclusion_terms=tuple(_safe_terms(payload.get("exclusion_terms", []))),
        warnings=tuple(str(item) for item in _as_list(payload.get("warnings", [])) if str(item).strip()),
        draft_source=str(payload.get("draft_source", "confirmed_pico_protocol_v2")),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        governance_refs=tuple(str(item) for item in _as_list(payload.get("governance_refs", []))),
        audit_refs=tuple(str(item) for item in _as_list(payload.get("audit_refs", []))),
        version=int(payload.get("version", 1) or 1),
        status=str(payload.get("status", "draft")),
        search_execution_status=str(payload.get("search_execution_status", "draft_only")),
        schema_version=str(payload.get("schema_version", SEARCH_STRATEGY_DRAFT_SCHEMA_VERSION)),
    )


def _confirmed_strategy_from_payload(payload: dict[str, Any]) -> ConfirmedSearchStrategyV2:
    return ConfirmedSearchStrategyV2(
        confirmed_search_strategy_id=str(payload.get("confirmed_search_strategy_id", "")),
        source_draft_id=str(payload.get("source_draft_id", "")),
        database=str(payload.get("database", "")),
        confirmed_query=str(payload.get("confirmed_query", "")),
        confirmed_terms=tuple(_safe_terms(payload.get("confirmed_terms", []))),
        confirmed_at=str(payload.get("confirmed_at", "")),
        confirmed_by=str(payload.get("confirmed_by", "")),
        version=int(payload.get("version", 1) or 1),
        execution_allowed=bool(payload.get("execution_allowed", False)),
        execution_status=str(payload.get("execution_status", "not_executed")),
        governance_refs=tuple(str(item) for item in _as_list(payload.get("governance_refs", []))),
        audit_refs=tuple(str(item) for item in _as_list(payload.get("audit_refs", []))),
        schema_version=str(payload.get("schema_version", CONFIRMED_SEARCH_STRATEGY_SCHEMA_VERSION)),
    )


def _and_blocks(values: Any) -> str:
    return " AND ".join(block for block in values if str(block).strip())


def _or_block(values: Any) -> str:
    terms = _safe_terms(values)
    if not terms:
        return ""
    if len(terms) == 1:
        return terms[0]
    return "(" + " OR ".join(terms) + ")"


def _ts_block(values: tuple[str, ...]) -> str:
    block = _or_block(f'"{term}"' for term in values)
    return f"TS={block}" if block else ""


def _safe_terms(values: Any) -> tuple[str, ...]:
    seen: set[str] = set()
    items: list[str] = []
    for value in _as_list(values):
        text = str(value or "").strip()
        key = text.lower()
        if text and key not in seen and not any(token in key for token in _FORBIDDEN_META_TERMS):
            seen.add(key)
            items.append(text)
    return tuple(items)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[;,]\s*|\n+", value) if item.strip()]
    if hasattr(value, "__iter__") and not isinstance(value, dict):
        return list(value)
    return [value]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
