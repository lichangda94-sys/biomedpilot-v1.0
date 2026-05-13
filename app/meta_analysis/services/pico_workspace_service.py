from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService
from app.shared.query_intelligence import build_search_translation_draft
from app.shared.search_context import META_ANALYSIS_SEARCH_CONTEXT, filter_search_translation_draft_by_context


PICO_PROTOCOL_DRAFT_SCHEMA_VERSION = "meta_pico_protocol_draft.v2"
CONFIRMED_PROTOCOL_SCHEMA_VERSION = "meta_confirmed_protocol.v2"
PICO_WORKSPACE_MANIFEST_SCHEMA_VERSION = "meta_pico_workspace_manifest.v2"

PICO_MODE_PICO = "pico"
PICO_MODE_PICOS = "picos"
PICO_MODE_PECO = "peco"
PICO_MODES = (PICO_MODE_PICO, PICO_MODE_PICOS, PICO_MODE_PECO)

META_TYPE_CANDIDATES = (
    "treatment_comparative_meta",
    "exposure_disease_risk_meta",
    "diagnostic_accuracy_meta",
    "prognostic_factor_meta",
    "prevalence_incidence_meta",
    "biomarker_expression_difference_meta",
    "correlation_meta",
    "survival_outcome_meta",
    "dose_response_meta",
    "network_meta_coming_soon",
)

_FORBIDDEN_META_TERMS = ("geo", "gse", "tcga", "gtex")


@dataclass(frozen=True)
class PICOProtocolDraftV2:
    protocol_id: str
    project_id: str
    research_question_original: str
    research_question_language: str
    pico_mode: str
    population: str = ""
    intervention: str = ""
    exposure: str = ""
    comparator: str = ""
    outcome: str = ""
    study_design: str = ""
    context_terms: tuple[str, ...] = ()
    disease_terms: tuple[str, ...] = ()
    synonym_terms: tuple[str, ...] = ()
    exclusion_scope: tuple[str, ...] = ()
    meta_type_candidates: tuple[dict[str, Any], ...] = ()
    draft_source: str = "shared_query_intelligence"
    confidence: float = 0.0
    warnings: tuple[str, ...] = ()
    version: int = 1
    status: str = "draft"
    created_at: str = ""
    updated_at: str = ""
    governance_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    schema_version: str = PICO_PROTOCOL_DRAFT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["context_terms"] = list(self.context_terms)
        payload["disease_terms"] = list(self.disease_terms)
        payload["synonym_terms"] = list(self.synonym_terms)
        payload["exclusion_scope"] = list(self.exclusion_scope)
        payload["meta_type_candidates"] = [dict(item) for item in self.meta_type_candidates]
        payload["governance_refs"] = list(self.governance_refs)
        payload["audit_refs"] = list(self.audit_refs)
        return payload


@dataclass(frozen=True)
class ConfirmedPICOProtocolV2:
    confirmed_protocol_id: str
    source_draft_id: str
    confirmed_at: str
    confirmed_by: str
    confirmed_pico_mode: str
    confirmed_population: str = ""
    confirmed_intervention_or_exposure: str = ""
    confirmed_comparator: str = ""
    confirmed_outcomes: tuple[str, ...] = ()
    confirmed_study_design: str = ""
    confirmed_meta_type: str = ""
    user_notes: str = ""
    version: int = 1
    locked_for_search_strategy: bool = True
    governance_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    schema_version: str = CONFIRMED_PROTOCOL_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confirmed_outcomes"] = list(self.confirmed_outcomes)
        payload["governance_refs"] = list(self.governance_refs)
        payload["audit_refs"] = list(self.audit_refs)
        return payload


class PICOWorkspaceService:
    def __init__(
        self,
        *,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._research_governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)

    def draft_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "pico_workspace_draft.json"

    def draft_versions_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "pico_workspace_draft_versions.json"

    def confirmed_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "pico_workspace_confirmed.json"

    def confirmed_versions_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "pico_workspace_confirmed_versions.json"

    def manifest_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "protocol" / "pico_workspace_manifest.json"

    def generate_draft(
        self,
        project_dir: Path,
        research_question: str,
        *,
        pico_mode: str = "auto",
        project_id: str | None = None,
        actor: str = "system",
    ) -> PICOProtocolDraftV2:
        project_dir = project_dir.expanduser().resolve()
        question = research_question.strip()
        shared = filter_search_translation_draft_by_context(
            build_search_translation_draft(
                question,
                target_context="meta_analysis",
                target_database="pubmed",
                use_local_model=False,
                allow_network=False,
            ),
            META_ANALYSIS_SEARCH_CONTEXT,
        )
        now = _now()
        mode = _normalize_pico_mode(pico_mode, question=question, shared_intent=shared.review_or_analysis_intent, exposure_terms=shared.exposure_terms_zh + shared.exposure_terms_en)
        warnings = _warnings(question, mode, shared.warnings)
        draft = PICOProtocolDraftV2(
            protocol_id=f"pico-draft-{uuid4().hex[:12]}",
            project_id=project_id or project_dir.name,
            research_question_original=question,
            research_question_language=_language(question, shared.detected_language),
            pico_mode=mode,
            population=_first_term([*shared.disease_terms_zh, *shared.disease_terms_en, *shared.main_concepts_zh, *shared.main_concepts_en]),
            intervention=_first_term(shared.exposure_terms_zh + shared.exposure_terms_en) if mode != PICO_MODE_PECO else "",
            exposure=_first_term(shared.exposure_terms_zh + shared.exposure_terms_en) if mode == PICO_MODE_PECO else "",
            comparator=_extract_comparator(question),
            outcome=_first_term([*shared.outcome_terms_zh, *shared.outcome_terms_en, *shared.disease_terms_zh, *shared.disease_terms_en]),
            study_design=_extract_study_design(question, mode),
            context_terms=_safe_terms([*shared.modifier_terms_zh, *shared.modifier_terms_en]),
            disease_terms=_safe_terms([*shared.disease_terms_zh, *shared.disease_terms_en]),
            synonym_terms=_safe_terms([*shared.candidate_terms, *shared.mesh_terms]),
            exclusion_scope=_default_exclusion_scope(),
            meta_type_candidates=_meta_type_candidates(question, mode, shared.review_or_analysis_intent),
            confidence=float(shared.confidence or 0.0),
            warnings=warnings,
            created_at=now,
            updated_at=now,
        )
        return self._write_draft(project_dir, draft, actor=actor, action="draft_created", before={})

    def edit_draft(
        self,
        project_dir: Path,
        *,
        updates: dict[str, Any],
        actor: str,
    ) -> PICOProtocolDraftV2:
        if not actor.strip():
            raise ValueError("actor_required_for_pico_draft_edit")
        project_dir = project_dir.expanduser().resolve()
        before = self.load_draft(project_dir)
        if before is None:
            raise ValueError("pico_draft_not_found")
        payload = before.to_dict()
        allowed = {
            "research_question_original",
            "research_question_language",
            "pico_mode",
            "population",
            "intervention",
            "exposure",
            "comparator",
            "outcome",
            "study_design",
            "context_terms",
            "disease_terms",
            "synonym_terms",
            "exclusion_scope",
            "meta_type_candidates",
            "confidence",
            "warnings",
        }
        for key, value in updates.items():
            if key in allowed:
                payload[key] = value
        payload["pico_mode"] = _normalize_pico_mode(str(payload.get("pico_mode", before.pico_mode)), question=str(payload.get("research_question_original", "")))
        payload["version"] = int(before.version) + 1
        payload["updated_at"] = _now()
        payload["status"] = "draft"
        edited = _draft_from_payload(payload)
        return self._write_draft(project_dir, edited, actor=actor, action="edit", before=before.to_dict())

    def confirm_protocol(
        self,
        project_dir: Path,
        *,
        actor: str,
        confirmed_meta_type: str,
        user_notes: str = "",
        locked_for_search_strategy: bool = True,
        overrides: dict[str, Any] | None = None,
    ) -> ConfirmedPICOProtocolV2:
        if not actor.strip():
            raise ValueError("actor_required_for_pico_protocol_confirmation")
        project_dir = project_dir.expanduser().resolve()
        draft = self.load_draft(project_dir)
        if draft is None:
            raise ValueError("pico_draft_not_found")
        overrides = dict(overrides or {})
        mode = _normalize_pico_mode(str(overrides.get("confirmed_pico_mode") or draft.pico_mode), question=draft.research_question_original)
        confirmed_type = str(confirmed_meta_type).strip()
        if not confirmed_type:
            raise ValueError("confirmed_meta_type_required")
        confirmed = ConfirmedPICOProtocolV2(
            confirmed_protocol_id=f"pico-confirmed-{uuid4().hex[:12]}",
            source_draft_id=draft.protocol_id,
            confirmed_at=_now(),
            confirmed_by=actor,
            confirmed_pico_mode=mode,
            confirmed_population=str(overrides.get("confirmed_population") or draft.population),
            confirmed_intervention_or_exposure=str(
                overrides.get("confirmed_intervention_or_exposure")
                or (draft.exposure if mode == PICO_MODE_PECO else draft.intervention)
            ),
            confirmed_comparator=str(overrides.get("confirmed_comparator") or draft.comparator),
            confirmed_outcomes=tuple(_safe_terms(_as_list(overrides.get("confirmed_outcomes") or draft.outcome))),
            confirmed_study_design=str(overrides.get("confirmed_study_design") or draft.study_design),
            confirmed_meta_type=confirmed_type,
            user_notes=user_notes.strip(),
            version=self._next_confirmed_version(project_dir),
            locked_for_search_strategy=bool(locked_for_search_strategy),
        )
        governance = self._research_governance.record_user_confirmation(
            project_dir,
            project_id=draft.project_id,
            action="confirm",
            actor=actor,
            target_type=_governance_target(mode),
            target_id=confirmed.confirmed_protocol_id,
            before=draft.to_dict(),
            after=confirmed.to_dict(),
            source_suggestion_id=draft.protocol_id,
            metadata={
                "confirmed_meta_type": confirmed.confirmed_meta_type,
                "locked_for_search_strategy": confirmed.locked_for_search_strategy,
                "screening_status": "not_started",
                "prisma_status": "not_updated",
            },
        )
        audit = self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=draft.project_id,
            actor=actor,
            target_type="pico_workspace_confirmed_protocol_v2",
            target_id=confirmed.confirmed_protocol_id,
            source_path=str(self.draft_path(project_dir).relative_to(project_dir)),
            output_path=str(self.confirmed_path(project_dir).relative_to(project_dir)),
            summary="PICO/PICOS/PECO protocol confirmed by reviewer",
            details={"source_draft_id": draft.protocol_id, "confirmed_meta_type": confirmed.confirmed_meta_type},
        )
        confirmed = ConfirmedPICOProtocolV2(
            **{
                **confirmed.to_dict(),
                "governance_refs": (governance.event_id,),
                "audit_refs": (audit.event_id,),
            }
        )
        self._write_confirmed(project_dir, confirmed)
        self._write_manifest(project_dir)
        return confirmed

    def load_draft(self, project_dir: Path) -> PICOProtocolDraftV2 | None:
        payload = _load_json(self.draft_path(project_dir))
        return _draft_from_payload(payload) if payload else None

    def load_confirmed(self, project_dir: Path) -> ConfirmedPICOProtocolV2 | None:
        payload = _load_json(self.confirmed_path(project_dir))
        return _confirmed_from_payload(payload) if payload else None

    def _write_draft(
        self,
        project_dir: Path,
        draft: PICOProtocolDraftV2,
        *,
        actor: str,
        action: str,
        before: dict[str, Any],
    ) -> PICOProtocolDraftV2:
        target_type = _governance_target(draft.pico_mode)
        if action == "edit":
            governance = self._research_governance.record_user_confirmation(
                project_dir,
                project_id=draft.project_id,
                action="edit",
                actor=actor,
                target_type=target_type,
                target_id=draft.protocol_id,
                before=before,
                after=draft.to_dict(),
                source_suggestion_id=draft.protocol_id,
                metadata={"draft_status": "user_edited", "confirmed_status": "not_confirmed"},
            )
        else:
            governance = self._research_governance.record_draft_created(
                project_dir,
                project_id=draft.project_id,
                actor=actor,
                target_type=target_type,
                target_id=draft.protocol_id,
                after=draft.to_dict(),
                metadata={"draft_status": "draft", "confirmed_status": "not_confirmed"},
            )
            self._research_governance.record_suggestion_created(
                project_dir,
                project_id=draft.project_id,
                target_type="meta_type_candidate",
                target_id=f"{draft.protocol_id}:meta_type_candidates",
                after={"meta_type_candidates": [dict(item) for item in draft.meta_type_candidates]},
                source_suggestion_id=draft.protocol_id,
                metadata={"final_meta_type_status": "not_confirmed"},
            )
        audit = self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=draft.project_id,
            actor=actor,
            target_type="pico_workspace_draft_v2",
            target_id=draft.protocol_id,
            source_path="PICO workspace v2",
            output_path=str(self.draft_path(project_dir).relative_to(project_dir)),
            summary=f"PICO/PICOS/PECO protocol {action}",
            details={
                "pico_mode": draft.pico_mode,
                "version": draft.version,
                "confirmed_status": "not_confirmed",
                "search_execution_status": "not_started",
                "screening_status": "not_started",
                "prisma_status": "not_updated",
            },
        )
        draft = PICOProtocolDraftV2(
            **{
                **draft.to_dict(),
                "governance_refs": (*draft.governance_refs, governance.event_id),
                "audit_refs": (*draft.audit_refs, audit.event_id),
            }
        )
        _write_json(self.draft_path(project_dir), draft.to_dict())
        self._append_version(self.draft_versions_path(project_dir), draft.to_dict(), schema_version="meta_pico_protocol_draft_versions.v2")
        self._write_manifest(project_dir)
        return draft

    def _write_confirmed(self, project_dir: Path, confirmed: ConfirmedPICOProtocolV2) -> None:
        _write_json(self.confirmed_path(project_dir), confirmed.to_dict())
        self._append_version(
            self.confirmed_versions_path(project_dir),
            confirmed.to_dict(),
            schema_version="meta_pico_workspace_confirmed_versions.v2",
        )

    def _append_version(self, path: Path, item: dict[str, Any], *, schema_version: str) -> None:
        payload = _load_json(path) or {"schema_version": schema_version, "versions": []}
        versions = payload.get("versions", [])
        if not isinstance(versions, list):
            versions = []
        versions.append(item)
        payload = {"schema_version": schema_version, "versions": versions}
        _write_json(path, payload)

    def _next_confirmed_version(self, project_dir: Path) -> int:
        payload = _load_json(self.confirmed_versions_path(project_dir))
        versions = payload.get("versions", []) if isinstance(payload, dict) else []
        return len(versions) + 1 if isinstance(versions, list) else 1

    def _write_manifest(self, project_dir: Path) -> None:
        project_dir = project_dir.expanduser().resolve()
        draft = self.load_draft(project_dir)
        confirmed = self.load_confirmed(project_dir)
        payload = {
            "schema_version": PICO_WORKSPACE_MANIFEST_SCHEMA_VERSION,
            "project_id": project_dir.name,
            "draft_path": str(self.draft_path(project_dir).relative_to(project_dir)),
            "draft_versions_path": str(self.draft_versions_path(project_dir).relative_to(project_dir)),
            "confirmed_path": str(self.confirmed_path(project_dir).relative_to(project_dir)),
            "confirmed_versions_path": str(self.confirmed_versions_path(project_dir).relative_to(project_dir)),
            "draft_status": "present" if draft else "missing",
            "confirmed_status": "confirmed" if confirmed else "not_confirmed",
            "locked_for_search_strategy": bool(confirmed.locked_for_search_strategy) if confirmed else False,
            "search_execution_status": "not_started",
            "screening_status": "not_started",
            "prisma_status": "not_updated",
            "updated_at": _now(),
        }
        _write_json(self.manifest_path(project_dir), payload)


def _draft_from_payload(payload: dict[str, Any]) -> PICOProtocolDraftV2:
    return PICOProtocolDraftV2(
        protocol_id=str(payload.get("protocol_id", "")),
        project_id=str(payload.get("project_id", "")),
        research_question_original=str(payload.get("research_question_original", "")),
        research_question_language=str(payload.get("research_question_language", "")),
        pico_mode=_normalize_pico_mode(str(payload.get("pico_mode", PICO_MODE_PICO)), question=str(payload.get("research_question_original", ""))),
        population=str(payload.get("population", "")),
        intervention=str(payload.get("intervention", "")),
        exposure=str(payload.get("exposure", "")),
        comparator=str(payload.get("comparator", "")),
        outcome=str(payload.get("outcome", "")),
        study_design=str(payload.get("study_design", "")),
        context_terms=tuple(_safe_terms(_as_list(payload.get("context_terms", ())))),
        disease_terms=tuple(_safe_terms(_as_list(payload.get("disease_terms", ())))),
        synonym_terms=tuple(_safe_terms(_as_list(payload.get("synonym_terms", ())))),
        exclusion_scope=tuple(_safe_terms(_as_list(payload.get("exclusion_scope", ())))),
        meta_type_candidates=tuple(dict(item) for item in payload.get("meta_type_candidates", []) if isinstance(item, dict)),
        draft_source=str(payload.get("draft_source", "shared_query_intelligence")),
        confidence=float(payload.get("confidence", 0.0) or 0.0),
        warnings=tuple(str(item) for item in _as_list(payload.get("warnings", ())) if str(item).strip()),
        version=int(payload.get("version", 1) or 1),
        status=str(payload.get("status", "draft")),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        governance_refs=tuple(str(item) for item in _as_list(payload.get("governance_refs", ()))),
        audit_refs=tuple(str(item) for item in _as_list(payload.get("audit_refs", ()))),
        schema_version=str(payload.get("schema_version", PICO_PROTOCOL_DRAFT_SCHEMA_VERSION)),
    )


def _confirmed_from_payload(payload: dict[str, Any]) -> ConfirmedPICOProtocolV2:
    return ConfirmedPICOProtocolV2(
        confirmed_protocol_id=str(payload.get("confirmed_protocol_id", "")),
        source_draft_id=str(payload.get("source_draft_id", "")),
        confirmed_at=str(payload.get("confirmed_at", "")),
        confirmed_by=str(payload.get("confirmed_by", "")),
        confirmed_pico_mode=_normalize_pico_mode(str(payload.get("confirmed_pico_mode", PICO_MODE_PICO))),
        confirmed_population=str(payload.get("confirmed_population", "")),
        confirmed_intervention_or_exposure=str(payload.get("confirmed_intervention_or_exposure", "")),
        confirmed_comparator=str(payload.get("confirmed_comparator", "")),
        confirmed_outcomes=tuple(_safe_terms(_as_list(payload.get("confirmed_outcomes", ())))),
        confirmed_study_design=str(payload.get("confirmed_study_design", "")),
        confirmed_meta_type=str(payload.get("confirmed_meta_type", "")),
        user_notes=str(payload.get("user_notes", "")),
        version=int(payload.get("version", 1) or 1),
        locked_for_search_strategy=bool(payload.get("locked_for_search_strategy", True)),
        governance_refs=tuple(str(item) for item in _as_list(payload.get("governance_refs", ()))),
        audit_refs=tuple(str(item) for item in _as_list(payload.get("audit_refs", ()))),
        schema_version=str(payload.get("schema_version", CONFIRMED_PROTOCOL_SCHEMA_VERSION)),
    )


def _normalize_pico_mode(
    value: str,
    *,
    question: str = "",
    shared_intent: str = "",
    exposure_terms: list[str] | None = None,
) -> str:
    normalized = value.strip().lower()
    if normalized in PICO_MODES:
        return normalized
    text = f"{question} {shared_intent} {' '.join(exposure_terms or [])}".lower()
    if any(token in text for token in ("暴露", "风险", "危险因素", "相关", "exposure", "risk", "factor", "association")):
        return PICO_MODE_PECO
    if any(token in text for token in ("picos", "study design", "研究类型", "纳入标准", "系统综述")):
        return PICO_MODE_PICOS
    return PICO_MODE_PICO


def _governance_target(mode: str) -> str:
    return {
        PICO_MODE_PECO: "final_peco",
        PICO_MODE_PICOS: "final_picos",
    }.get(mode, "final_pico")


def _language(question: str, fallback: str) -> str:
    if re.search(r"[\u4e00-\u9fff]", question):
        return "zh"
    return fallback or "en"


def _warnings(question: str, mode: str, shared_warnings: list[str]) -> tuple[str, ...]:
    warnings = list(shared_warnings)
    if not question:
        warnings.append("missing_research_question")
    if mode not in PICO_MODES:
        warnings.append("pico_mode_requires_reviewer_confirmation")
    warnings.append("requires_human_confirmation")
    return tuple(_unique(warnings))


def _meta_type_candidates(question: str, mode: str, shared_intent: str) -> tuple[dict[str, Any], ...]:
    text = f"{question} {shared_intent}".lower()
    preferred = "treatment_comparative_meta"
    if mode == PICO_MODE_PECO or any(token in text for token in ("risk", "association", "暴露", "风险", "相关")):
        preferred = "exposure_disease_risk_meta"
    if any(token in text for token in ("diagnostic", "sensitivity", "specificity", "诊断", "敏感性", "特异性")):
        preferred = "diagnostic_accuracy_meta"
    if any(token in text for token in ("prevalence", "incidence", "患病率", "发生率")):
        preferred = "prevalence_incidence_meta"
    candidates: list[dict[str, Any]] = []
    for name in META_TYPE_CANDIDATES:
        candidates.append(
            {
                "meta_type": name,
                "status": "coming_soon" if name == "network_meta_coming_soon" else "candidate",
                "rank": 1 if name == preferred else 2,
                "source": "rule_based_candidate",
                "requires_user_confirmation": True,
            }
        )
    return tuple(sorted(candidates, key=lambda item: (int(item["rank"]), str(item["meta_type"]))))


def _extract_comparator(question: str) -> str:
    for marker in ("相比", "对照", "versus", "vs", "compared with"):
        if marker in question:
            tail = question.split(marker, 1)[1].strip(" ，,。?")
            return _safe_text(tail[:80])
    return ""


def _extract_study_design(question: str, mode: str) -> str:
    if any(token in question.lower() for token in ("随机", "randomized", "rct")):
        return "randomized controlled trial"
    if mode == PICO_MODE_PICOS:
        return "study design requires reviewer input"
    return ""


def _default_exclusion_scope() -> tuple[str, ...]:
    return ("animal_study", "cell_study", "non_original_article")


def _first_term(values: list[str]) -> str:
    terms = _safe_terms(values)
    return terms[0] if terms else ""


def _safe_terms(values: Any) -> tuple[str, ...]:
    return tuple(_unique(_safe_text(item) for item in values if _safe_text(item)))


def _safe_text(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.lower()
    if any(token in lowered for token in _FORBIDDEN_META_TERMS):
        return ""
    return text


def _unique(values: Any) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        text = str(value).strip()
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            items.append(text)
    return items


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[;,]\s*|\n+", value) if item.strip()]
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
