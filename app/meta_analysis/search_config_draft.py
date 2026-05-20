from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.meta_analysis.project_workspace import META_PROJECT_CONFIG, open_meta_analysis_project
from app.shared.query_intelligence.meta_seed_terms import (
    SeedTerm,
    build_pubmed_query_blocks,
    load_seed_terms,
    match_chinese_question_to_pico,
)


META_SEED_SEARCH_CONFIG_DRAFT = "meta_seed_search_config_draft.json"


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
    draft_status: str
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
        draft_status="draft_needs_user_confirmation",
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


def save_meta_seed_search_config_draft(
    project_root: str | Path,
    draft: MetaSeedSearchConfigDraft,
) -> Path:
    validation = open_meta_analysis_project(project_root)
    if not validation.is_valid or validation.summary is None:
        raise ValueError("Cannot save Meta search config draft into an invalid Meta project.")

    root = validation.summary.project_root
    draft_path = root / "search_strategy" / META_SEED_SEARCH_CONFIG_DRAFT
    _atomic_write_json(draft_path, draft.to_dict())
    _update_project_config(root, draft_path, draft)
    return draft_path


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


def _update_project_config(root: Path, draft_path: Path, draft: MetaSeedSearchConfigDraft) -> None:
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
        "draft_status": draft.draft_status,
        "user_confirmation_required": draft.user_confirmation_required,
        "search_execution_status": draft.search_execution_status,
        "online_retrieval_executed": draft.online_retrieval_executed,
        "formal_search_completed": draft.formal_search_completed,
    }
    _atomic_write_json(config_path, payload)


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
