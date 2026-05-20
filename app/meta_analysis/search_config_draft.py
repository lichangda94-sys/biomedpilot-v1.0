from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from app.meta_analysis.project_workspace import META_PROJECT_CONFIG, open_meta_analysis_project
from app.shared.query_intelligence.meta_seed_terms import (
    SeedTerm,
    build_pubmed_query_blocks,
    load_seed_terms,
    match_chinese_question_to_pico,
)


META_SEED_SEARCH_CONFIG_DRAFT = "meta_seed_search_config_draft.json"
META_SEED_CONFIRMED_SEARCH_PLAN = "confirmed_search_plan.json"

SearchDraftReviewStatus = Literal["draft_only", "needs_edit", "user_confirmed", "rejected"]


@dataclass(frozen=True)
class MetaSeedConceptGuard:
    concept_id: str
    preferred_label_en: str
    zh_terms: tuple[str, ...]
    concept_type: str
    pico_roles: tuple[str, ...]
    query_expansion_allowed: bool | str
    standalone_search_allowed: bool | str
    requires_pairing_with: tuple[str, ...]
    filter_only: bool
    pdf_extraction_target: bool
    included_in_pubmed_topic_query: bool
    guard_explanation: str


@dataclass(frozen=True)
class MetaSeedSearchConfigDraft:
    original_question: str
    draft_status: SearchDraftReviewStatus
    user_confirmation_required: bool
    search_execution_status: str
    online_retrieval_executed: bool
    formal_search_completed: bool
    detected_intent: str
    population: tuple[MetaSeedConceptGuard, ...]
    exposure_or_intervention: tuple[MetaSeedConceptGuard, ...]
    outcome: tuple[MetaSeedConceptGuard, ...]
    study_design: tuple[MetaSeedConceptGuard, ...]
    effect_measure: tuple[MetaSeedConceptGuard, ...]
    research_intent_terms: tuple[MetaSeedConceptGuard, ...]
    detected_concepts: tuple[MetaSeedConceptGuard, ...]
    pubmed_query_blocks: tuple[str, ...]
    pubmed_query_draft: str
    warnings: tuple[str, ...]
    unsupported_features: tuple[str, ...]
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MetaSearchPlanGuardOverride:
    concept_id: str
    reason: str
    requested_action: str
    warning: str


@dataclass(frozen=True)
class MetaUserEditedSearchPlan:
    review_status: SearchDraftReviewStatus
    selected_concept_ids: tuple[str, ...]
    included_pubmed_query_blocks: tuple[str, ...]
    edited_pubmed_query_draft: str
    user_notes: str
    guard_overrides: tuple[MetaSearchPlanGuardOverride, ...]
    updated_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MetaConfirmedSearchPlan:
    review_status: SearchDraftReviewStatus
    search_execution_status: str
    online_retrieval_executed: bool
    formal_search_completed: bool
    auto_generated_draft: dict[str, object]
    user_edited_plan: dict[str, object]
    confirmed_pubmed_query_draft: str
    warnings: tuple[str, ...]
    created_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_meta_seed_search_config_draft(question: str) -> MetaSeedSearchConfigDraft:
    normalized_question = " ".join(question.strip().split())
    pico = match_chinese_question_to_pico(normalized_question)
    matched_terms = _match_all_seed_terms(normalized_question)
    eligible_query_ids = _pubmed_topic_eligible_ids(pico)
    blocks = tuple(build_pubmed_query_blocks(eligible_query_ids))
    included_ids = set(eligible_query_ids)
    guards = tuple(_guard_from_seed(seed, seed.concept_id in included_ids) for seed in matched_terms)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    return MetaSeedSearchConfigDraft(
        original_question=normalized_question,
        draft_status="draft_only",
        user_confirmation_required=True,
        search_execution_status="not_executed",
        online_retrieval_executed=False,
        formal_search_completed=False,
        detected_intent=pico.research_intent,
        population=_guards_for(pico.population_or_disease, guards),
        exposure_or_intervention=_guards_for([*pico.exposure, *pico.intervention], guards),
        outcome=_guards_for(pico.outcome, guards),
        study_design=_guards_for(pico.study_design, guards),
        effect_measure=tuple(guard for guard in guards if guard.concept_type == "effect_measure"),
        research_intent_terms=tuple(guard for guard in guards if guard.concept_type == "research_intent"),
        detected_concepts=guards,
        pubmed_query_blocks=blocks,
        pubmed_query_draft=" AND ".join(blocks),
        warnings=_warnings(pico, blocks),
        unsupported_features=(
            "no_online_pubmed_embase_wos_retrieval",
            "no_chinese_database_search",
            "no_chinese_pdf_extraction",
            "no_english_pdf_extraction_ui",
            "no_final_extraction_table_write",
        ),
        created_at=now,
    )


def build_user_edited_search_plan(
    draft: MetaSeedSearchConfigDraft,
    *,
    selected_concept_ids: list[str] | tuple[str, ...] | None = None,
    included_pubmed_query_blocks: list[str] | tuple[str, ...] | None = None,
    edited_pubmed_query_draft: str | None = None,
    user_notes: str = "",
    guard_overrides: list[dict[str, str]] | tuple[dict[str, str], ...] | None = None,
) -> MetaUserEditedSearchPlan:
    selected_ids = tuple(selected_concept_ids if selected_concept_ids is not None else _included_concept_ids(draft))
    included_blocks = tuple(included_pubmed_query_blocks if included_pubmed_query_blocks is not None else draft.pubmed_query_blocks)
    edited_query = edited_pubmed_query_draft if edited_pubmed_query_draft is not None else " AND ".join(included_blocks)
    overrides = tuple(_guard_override_from_dict(payload) for payload in (guard_overrides or ()))
    has_edits = (
        selected_ids != _included_concept_ids(draft)
        or included_blocks != draft.pubmed_query_blocks
        or edited_query != draft.pubmed_query_draft
        or bool(user_notes.strip())
        or bool(overrides)
    )
    return MetaUserEditedSearchPlan(
        review_status="needs_edit" if has_edits else "draft_only",
        selected_concept_ids=selected_ids,
        included_pubmed_query_blocks=included_blocks,
        edited_pubmed_query_draft=edited_query,
        user_notes=user_notes.strip(),
        guard_overrides=overrides,
        updated_at=_now(),
    )


def build_confirmed_search_plan(
    draft: MetaSeedSearchConfigDraft,
    user_edited_plan: MetaUserEditedSearchPlan,
    *,
    user_confirmed: bool = False,
) -> MetaConfirmedSearchPlan:
    if draft.draft_status == "rejected" or user_edited_plan.review_status == "rejected":
        raise ValueError("Rejected Meta search config drafts cannot become confirmed search plans.")
    if not user_confirmed:
        raise ValueError("User confirmation is required before creating a confirmed search plan.")
    override_warnings = tuple(override.warning for override in user_edited_plan.guard_overrides)
    warnings = (
        *draft.warnings,
        *override_warnings,
        "Confirmed search plan only: no online retrieval was executed.",
    )
    return MetaConfirmedSearchPlan(
        review_status="user_confirmed",
        search_execution_status="not_executed",
        online_retrieval_executed=False,
        formal_search_completed=False,
        auto_generated_draft=draft.to_dict(),
        user_edited_plan=user_edited_plan.to_dict(),
        confirmed_pubmed_query_draft=user_edited_plan.edited_pubmed_query_draft,
        warnings=warnings,
        created_at=_now(),
    )


def reject_meta_seed_search_config_draft(
    draft: MetaSeedSearchConfigDraft,
    *,
    user_notes: str = "",
) -> dict[str, object]:
    return {
        "review_status": "rejected",
        "search_execution_status": "not_executed",
        "online_retrieval_executed": False,
        "formal_search_completed": False,
        "auto_generated_draft": draft.to_dict(),
        "user_edited_plan": {
            "review_status": "rejected",
            "selected_concept_ids": [],
            "included_pubmed_query_blocks": [],
            "edited_pubmed_query_draft": "",
            "user_notes": user_notes.strip(),
            "guard_overrides": [],
            "updated_at": _now(),
        },
        "confirmed_search_plan": None,
        "warnings": (
            "Rejected draft cannot enter formal retrieval or downstream Meta workflow.",
            "No online retrieval was executed.",
        ),
        "updated_at": _now(),
    }


def save_meta_seed_search_config_draft(
    project_root: str | Path,
    draft: MetaSeedSearchConfigDraft,
    user_edited_plan: MetaUserEditedSearchPlan | None = None,
) -> Path:
    validation = open_meta_analysis_project(project_root)
    if not validation.is_valid or validation.summary is None:
        raise ValueError("Cannot save Meta search config draft into an invalid Meta project.")

    root = validation.summary.project_root
    draft_path = root / "search_strategy" / META_SEED_SEARCH_CONFIG_DRAFT
    edited = user_edited_plan or build_user_edited_search_plan(draft)
    _atomic_write_json(draft_path, _review_payload(draft, edited, None))
    _update_project_config(root, draft_path, draft, edited.review_status, None)
    return draft_path


def save_confirmed_search_plan(
    project_root: str | Path,
    draft: MetaSeedSearchConfigDraft,
    user_edited_plan: MetaUserEditedSearchPlan,
    *,
    user_confirmed: bool = False,
) -> Path:
    validation = open_meta_analysis_project(project_root)
    if not validation.is_valid or validation.summary is None:
        raise ValueError("Cannot save confirmed Meta search plan into an invalid Meta project.")

    root = validation.summary.project_root
    confirmed_plan = build_confirmed_search_plan(draft, user_edited_plan, user_confirmed=user_confirmed)
    draft_path = root / "search_strategy" / META_SEED_SEARCH_CONFIG_DRAFT
    confirmed_path = root / "search_strategy" / META_SEED_CONFIRMED_SEARCH_PLAN
    _atomic_write_json(draft_path, _review_payload(draft, user_edited_plan, confirmed_plan))
    _atomic_write_json(confirmed_path, confirmed_plan.to_dict())
    _update_project_config(root, draft_path, draft, "user_confirmed", confirmed_path)
    return confirmed_path


def save_rejected_search_config_draft(
    project_root: str | Path,
    draft: MetaSeedSearchConfigDraft,
    *,
    user_notes: str = "",
) -> Path:
    validation = open_meta_analysis_project(project_root)
    if not validation.is_valid or validation.summary is None:
        raise ValueError("Cannot save rejected Meta search draft into an invalid Meta project.")

    root = validation.summary.project_root
    rejected_path = root / "search_strategy" / META_SEED_SEARCH_CONFIG_DRAFT
    _atomic_write_json(rejected_path, reject_meta_seed_search_config_draft(draft, user_notes=user_notes))
    _update_project_config(root, rejected_path, draft, "rejected", None)
    return rejected_path


def _match_all_seed_terms(question: str) -> list[SeedTerm]:
    matches: list[SeedTerm] = []
    for seed in load_seed_terms():
        if any(term and term in question for term in seed.zh_terms):
            matches.append(seed)
    return matches


def _pubmed_topic_eligible_ids(pico) -> list[str]:
    paired_with_population = bool(pico.population_or_disease)
    eligible: list[str] = []
    eligible.extend(seed.concept_id for seed in pico.population_or_disease)
    eligible.extend(seed.concept_id for seed in pico.exposure)
    eligible.extend(seed.concept_id for seed in pico.intervention)
    if paired_with_population:
        eligible.extend(seed.concept_id for seed in pico.outcome)
    return _unique(eligible)


def _guard_from_seed(seed: SeedTerm, included: bool) -> MetaSeedConceptGuard:
    return MetaSeedConceptGuard(
        concept_id=seed.concept_id,
        preferred_label_en=seed.preferred_label_en,
        zh_terms=tuple(seed.zh_terms),
        concept_type=seed.concept_type,
        pico_roles=tuple(seed.pico_roles),
        query_expansion_allowed=seed.query_expansion_allowed,
        standalone_search_allowed=seed.standalone_search_allowed,
        requires_pairing_with=tuple(seed.requires_pairing_with),
        filter_only=seed.filter_only,
        pdf_extraction_target=seed.pdf_extraction_target,
        included_in_pubmed_topic_query=included,
        guard_explanation=_guard_explanation(seed, included),
    )


def _guard_explanation(seed: SeedTerm, included: bool) -> str:
    if included:
        return "included in PubMed topic draft from curated MeSH/free-text mapping"
    if seed.concept_type == "outcome":
        return "conditional outcome term; requires population/disease pairing before topic expansion"
    if seed.concept_type == "study_design":
        return "filter-only study design marker; not used as topic expansion"
    if seed.concept_type in {"effect_measure", "research_intent"}:
        return "guarded analysis marker; not used as PubMed topic expansion"
    if seed.filter_only:
        return "filter-only seed; not used as topic expansion"
    if seed.query_expansion_allowed is False:
        return "query expansion disabled by seed guard"
    return "detected but not selected for PubMed topic draft"


def _guards_for(seeds: list[SeedTerm], guards: tuple[MetaSeedConceptGuard, ...]) -> tuple[MetaSeedConceptGuard, ...]:
    wanted = {seed.concept_id for seed in seeds}
    return tuple(guard for guard in guards if guard.concept_id in wanted)


def _warnings(pico, blocks: tuple[str, ...]) -> tuple[str, ...]:
    warnings = [
        "Draft only: user confirmation is required before any formal search step.",
        "No online PubMed, Embase, Web of Science, or Chinese database retrieval was executed.",
        "Query guards exclude research intent, effect measures, and study design markers from topic expansion.",
    ]
    if pico.outcome and not pico.population_or_disease:
        warnings.append("Outcome terms were detected without a disease/population pair and were not expanded.")
    if not blocks:
        warnings.append("No PubMed topic query blocks were generated from the detected curated seed terms.")
    return tuple(warnings)


def _review_payload(
    draft: MetaSeedSearchConfigDraft,
    user_edited_plan: MetaUserEditedSearchPlan,
    confirmed_plan: MetaConfirmedSearchPlan | None,
) -> dict[str, object]:
    review_status: SearchDraftReviewStatus = "user_confirmed" if confirmed_plan else user_edited_plan.review_status
    return {
        "review_status": review_status,
        "search_execution_status": "not_executed",
        "online_retrieval_executed": False,
        "formal_search_completed": False,
        "auto_generated_draft": draft.to_dict(),
        "user_edited_plan": user_edited_plan.to_dict(),
        "confirmed_search_plan": confirmed_plan.to_dict() if confirmed_plan else None,
        "warnings": (*draft.warnings, *_override_warnings(user_edited_plan)),
        "updated_at": _now(),
    }


def _update_project_config(
    root: Path,
    draft_path: Path,
    draft: MetaSeedSearchConfigDraft,
    review_status: SearchDraftReviewStatus,
    confirmed_path: Path | None,
) -> None:
    config_path = root / META_PROJECT_CONFIG
    payload: dict[str, object]
    if config_path.exists():
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        payload = loaded if isinstance(loaded, dict) else {}
    else:
        payload = {}
    payload["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload["workflow_stage"] = "search_config_draft"
    payload["search_config_draft"] = {
        "type": "meta_seed_search_config_draft",
        "path": str(draft_path),
        "review_status": review_status,
        "draft_status": review_status,
        "user_confirmation_required": review_status != "user_confirmed",
        "search_execution_status": draft.search_execution_status,
        "online_retrieval_executed": draft.online_retrieval_executed,
        "formal_search_completed": draft.formal_search_completed,
        "confirmed_search_plan_path": str(confirmed_path) if confirmed_path else "",
    }
    _atomic_write_json(config_path, payload)


def _guard_override_from_dict(payload: dict[str, str]) -> MetaSearchPlanGuardOverride:
    concept_id = str(payload.get("concept_id") or "").strip()
    requested_action = str(payload.get("requested_action") or "manual_query_override").strip()
    reason = str(payload.get("reason") or "").strip()
    return MetaSearchPlanGuardOverride(
        concept_id=concept_id,
        reason=reason,
        requested_action=requested_action,
        warning=(
            f"Guard override requested for {concept_id or 'unknown concept'}; "
            "manual override is recorded but not automatically considered safe."
        ),
    )


def _included_concept_ids(draft: MetaSeedSearchConfigDraft) -> tuple[str, ...]:
    return tuple(guard.concept_id for guard in draft.detected_concepts if guard.included_in_pubmed_topic_query)


def _override_warnings(user_edited_plan: MetaUserEditedSearchPlan) -> tuple[str, ...]:
    return tuple(override.warning for override in user_edited_plan.guard_overrides)


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
