from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.meta_analysis.models.ai_suggestion import AISuggestion, AISuggestionStatus, ai_suggestion_to_dict
from app.meta_analysis.services.ai_suggestion_service import AISuggestionService
from app.meta_analysis.services.extraction_schema_registry_v1_service import (
    BINARY_OUTCOME_META,
    CONTINUOUS_OUTCOME_META,
    DIAGNOSTIC_ACCURACY_META_V1,
    SURVIVAL_OUTCOME_META,
)
from app.meta_analysis.services.fulltext_parsing_service import FullTextParsingService
from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService
from app.shared.query_intelligence.query_intelligence_service import build_search_translation_draft


AI_EXTRACTION_QUEUE_SCHEMA_VERSION = "meta_ai_extraction_suggestion_queue.v1"
AI_EXTRACTION_VALIDATION_SCHEMA_VERSION = "meta_ai_extraction_suggestion_validation.v1"
AI_EXTRACTION_APPLICATION_SCHEMA_VERSION = "meta_ai_extraction_suggestion_application.v1"


@dataclass(frozen=True)
class AIExtractionSuggestionResult:
    success: bool
    project_id: str
    suggestion_id: str
    output_path: str
    validation_path: str
    queue_path: str
    message: str
    suggestion: AISuggestion | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIExtractionApplyResult:
    success: bool
    project_id: str
    suggestion_id: str
    effect_row_id: str
    study_unit_id: str
    output_path: str
    message: str
    diagnostics: dict[str, Any] = field(default_factory=dict)


class AIAssistedExtractionQueueService:
    def __init__(
        self,
        *,
        ai_suggestions: AISuggestionService | None = None,
        manual_extraction: ManualExtractionEffectRowService | None = None,
        fulltext_parsing: FullTextParsingService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
    ) -> None:
        self._governance = research_governance or MetaResearchGovernanceService()
        self._ai_suggestions = ai_suggestions or AISuggestionService(research_governance=self._governance)
        self._manual_extraction = manual_extraction or ManualExtractionEffectRowService(research_governance=self._governance)
        self._fulltext_parsing = fulltext_parsing or FullTextParsingService(research_governance=self._governance)

    def queue_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "extraction" / "extraction_ai_suggestion_queue.json"

    def validation_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "extraction" / "extraction_ai_suggestion_validation.json"

    def application_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "extraction" / "extraction_ai_suggestion_applications.json"

    def create_suggestion_from_text(
        self,
        project_dir: Path,
        *,
        record_id: str,
        text: str,
        project_id: str | None = None,
        schema_meta_type: str = BINARY_OUTCOME_META,
        research_question: str = "",
        actor: str = "model",
    ) -> AIExtractionSuggestionResult:
        project_dir = project_dir.expanduser().resolve()
        project_id = project_id or project_dir.name
        extraction_payload = _suggest_effect_row_payload(text, record_id=record_id, schema_meta_type=schema_meta_type)
        disease_guard = _disease_guard(text=text, research_question=research_question)
        validation = self._validate_suggestion_payload(extraction_payload, schema_meta_type=schema_meta_type, disease_guard=disease_guard)
        suggestion = self._ai_suggestions.create_ai_suggestion(
            project_dir,
            project_id=project_id,
            target_type="extraction_effect_row",
            target_id=record_id,
            suggestion_type="extraction_effect_row_suggestion",
            suggested_value={
                "schema_version": "meta_ai_extraction_effect_row_suggestion.v1",
                "record_id": record_id,
                "schema_meta_type": schema_meta_type,
                "effect_row_draft": extraction_payload,
                "schema_validation": validation,
                "disease_guard": disease_guard,
                "source": {
                    "source_type": "text",
                    "source_text_preview": text[:500],
                    "actor": actor,
                },
                "safety_note": "AI extraction output is a suggestion only and cannot write final extraction values without reviewer action.",
            },
            rationale=_rationale(schema_meta_type, extraction_payload, validation, disease_guard),
            confidence=_confidence(validation, disease_guard),
        )
        self._write_queue(project_dir)
        self._write_validation(project_dir, suggestion_id=suggestion.suggestion_id, validation=validation, disease_guard=disease_guard)
        return AIExtractionSuggestionResult(
            success=True,
            project_id=project_id,
            suggestion_id=suggestion.suggestion_id,
            output_path=str(self._suggestions_path(project_dir)),
            validation_path=str(self.validation_path(project_dir)),
            queue_path=str(self.queue_path(project_dir)),
            message="AI extraction suggestion created as pending reviewer queue item.",
            suggestion=suggestion,
            diagnostics={"schema_validation": validation, "disease_guard": disease_guard},
        )

    def create_suggestion_from_parsed_fulltext(
        self,
        project_dir: Path,
        *,
        record_id: str,
        project_id: str | None = None,
        schema_meta_type: str = BINARY_OUTCOME_META,
        research_question: str = "",
    ) -> AIExtractionSuggestionResult:
        project_dir = project_dir.expanduser().resolve()
        text = _load_parsed_text(project_dir, self._fulltext_parsing, record_id)
        if not text.strip():
            return AIExtractionSuggestionResult(
                success=False,
                project_id=project_id or project_dir.name,
                suggestion_id="",
                output_path="",
                validation_path=str(self.validation_path(project_dir)),
                queue_path=str(self.queue_path(project_dir)),
                message="No parsed full-text text is available for extraction suggestion.",
                diagnostics={"error_code": "parsed_fulltext_text_missing"},
            )
        return self.create_suggestion_from_text(
            project_dir,
            record_id=record_id,
            text=text,
            project_id=project_id,
            schema_meta_type=schema_meta_type,
            research_question=research_question,
        )

    def accept_suggestion(self, project_dir: Path, suggestion_id: str, *, actor: str = "reviewer"):
        result = self._ai_suggestions.accept_ai_suggestion(project_dir, suggestion_id, reviewer_action="accepted_for_extraction_draft")
        self._write_queue(project_dir)
        return result

    def reject_suggestion(self, project_dir: Path, suggestion_id: str, *, actor: str = "reviewer"):
        result = self._ai_suggestions.reject_ai_suggestion(project_dir, suggestion_id, reviewer_action="rejected_for_extraction_draft")
        self._write_queue(project_dir)
        return result

    def edit_suggestion(self, project_dir: Path, suggestion_id: str, *, edited_effect_row_draft: dict[str, Any], actor: str = "reviewer"):
        suggestion = self._require(project_dir, suggestion_id)
        value = dict(suggestion.suggested_value if isinstance(suggestion.suggested_value, dict) else {})
        before = dict(value.get("effect_row_draft", {}) if isinstance(value.get("effect_row_draft"), dict) else {})
        value["effect_row_draft"] = edited_effect_row_draft
        value["reviewer_edit"] = {"edited_by": actor, "before": before, "after": edited_effect_row_draft}
        result = self._ai_suggestions.edit_ai_suggestion(
            project_dir,
            suggestion_id,
            suggested_value=value,
            reviewer_action="edited_for_extraction_draft",
        )
        self._write_queue(project_dir)
        return result

    def apply_accepted_suggestion_as_draft(
        self,
        project_dir: Path,
        *,
        suggestion_id: str,
        actor: str = "reviewer",
    ) -> AIExtractionApplyResult:
        project_dir = project_dir.expanduser().resolve()
        suggestion = self._require(project_dir, suggestion_id)
        if suggestion.status != AISuggestionStatus.ACCEPTED.value:
            return AIExtractionApplyResult(
                success=False,
                project_id=suggestion.project_id,
                suggestion_id=suggestion_id,
                effect_row_id="",
                study_unit_id="",
                output_path="",
                message="Only accepted extraction suggestions can be applied as manual extraction drafts.",
                diagnostics={"status": suggestion.status},
            )
        value = dict(suggestion.suggested_value if isinstance(suggestion.suggested_value, dict) else {})
        draft = dict(value.get("effect_row_draft", {}) if isinstance(value.get("effect_row_draft"), dict) else {})
        schema_meta_type = str(value.get("schema_meta_type") or draft.get("schema_meta_type") or BINARY_OUTCOME_META)
        record_id = str(value.get("record_id") or draft.get("record_id") or suggestion.target_id)
        study_unit = self._manual_extraction.create_study_unit(
            project_dir,
            record_id=record_id,
            study_unit_label=str(draft.get("study_unit_label") or f"AI suggestion study unit {record_id}"),
            cohort_name=str(draft.get("cohort_name", "")),
            country_or_region=str(draft.get("country_or_region", "")),
            study_design=str(draft.get("study_design", "")),
            sample_size=draft.get("sample_size"),
            population_description=str(draft.get("population_description", "")),
            actor=actor,
        )
        effect_row = self._manual_extraction.create_effect_row(
            project_dir,
            study_unit_id=study_unit.payload["study_unit_id"],
            actor=actor,
            schema_meta_type=schema_meta_type,
            data_input_mode=str(draft.get("data_input_mode") or "manual_note_only"),
            comparison_label=str(draft.get("comparison_label", "")),
            group_1_label=str(draft.get("group_1_label", "")),
            group_2_label=str(draft.get("group_2_label", "")),
            outcome_name=str(draft.get("outcome_name", "")),
            outcome_domain=str(draft.get("outcome_domain", "")),
            timepoint=str(draft.get("timepoint", "")),
            subgroup_label=str(draft.get("subgroup_label", "")),
            data_fields=dict(draft.get("data_fields", {}) if isinstance(draft.get("data_fields"), dict) else {}),
            source_page=str(draft.get("source_page", "")),
            source_table=str(draft.get("source_table", "")),
            source_figure=str(draft.get("source_figure", "")),
            source_quote=str(draft.get("source_quote", "")),
            evidence_note=f"AI suggestion accepted by reviewer; source_suggestion_id={suggestion_id}. {draft.get('evidence_note', '')}",
            analysis_role=str(draft.get("analysis_role") or "secondary_effect_candidate"),
            extraction_status="draft",
            analysis_eligibility="not_assessed",
        )
        effect_row = self._manual_extraction.save_effect_row_draft(
            project_dir,
            effect_row_id=effect_row.payload["effect_row_id"],
            updates={
                "source_suggestion_id": suggestion_id,
                "ai_suggestion_status": "accepted",
                "ai_suggestion_application_mode": "manual_extraction_draft_only",
            },
            actor=actor,
        )
        self._ai_suggestions.apply_accepted_suggestion(project_dir, suggestion_id)
        application = {
            "schema_version": AI_EXTRACTION_APPLICATION_SCHEMA_VERSION,
            "project_id": suggestion.project_id,
            "suggestion_id": suggestion_id,
            "study_unit_id": study_unit.payload["study_unit_id"],
            "effect_row_id": effect_row.payload["effect_row_id"],
            "status": "applied_as_manual_extraction_draft",
            "analysis_ready_dataset_created": False,
            "statistics_run": False,
            "prisma_advanced": False,
            "safety_note": "Accepted AI suggestion was applied only as a manual extraction draft effect row.",
        }
        _append_json_item(self.application_path(project_dir), "applications", application, schema_version=AI_EXTRACTION_APPLICATION_SCHEMA_VERSION)
        self._governance.record_user_confirmation(
            project_dir,
            project_id=suggestion.project_id,
            action="confirm",
            actor=actor,
            target_type="extraction_effect_row",
            target_id=effect_row.payload["effect_row_id"],
            before=ai_suggestion_to_dict(suggestion),
            after=application,
            source_suggestion_id=suggestion_id,
            metadata={
                "workflow_action": "accepted_ai_extraction_suggestion_applied_as_draft",
                "analysis_ready_dataset_created": False,
                "statistics_run": False,
                "prisma_advanced": False,
            },
        )
        self._write_queue(project_dir)
        return AIExtractionApplyResult(
            success=True,
            project_id=suggestion.project_id,
            suggestion_id=suggestion_id,
            effect_row_id=effect_row.payload["effect_row_id"],
            study_unit_id=study_unit.payload["study_unit_id"],
            output_path=effect_row.output_path,
            message="Accepted AI extraction suggestion applied as manual extraction draft only.",
            diagnostics={"application": application},
        )

    def list_extraction_suggestions(self, project_dir: Path) -> list[AISuggestion]:
        return [
            suggestion
            for suggestion in self._ai_suggestions.list_ai_suggestions(project_dir)
            if suggestion.target_type == "extraction_effect_row"
            or suggestion.suggestion_type == "extraction_effect_row_suggestion"
        ]

    def _validate_suggestion_payload(
        self,
        payload: dict[str, Any],
        *,
        schema_meta_type: str,
        disease_guard: dict[str, Any],
    ) -> dict[str, Any]:
        data_fields = dict(payload.get("data_fields", {}) if isinstance(payload.get("data_fields"), dict) else {})
        missing = [field for field in _required_fields(schema_meta_type, str(payload.get("data_input_mode", ""))) if data_fields.get(field) in ("", None)]
        diagnostics = [f"缺少建议字段：{field}" for field in missing]
        if disease_guard.get("status") == "blocked":
            diagnostics.append("disease guard 阻止：suggestion 与研究问题病种不一致。")
        return {
            "schema_version": AI_EXTRACTION_VALIDATION_SCHEMA_VERSION,
            "schema_meta_type": schema_meta_type,
            "status": "invalid" if diagnostics else "valid",
            "missing_fields": missing,
            "diagnostics": diagnostics,
            "writes_final_extraction": False,
            "analysis_ready_dataset_created": False,
        }

    def _write_queue(self, project_dir: Path) -> Path:
        suggestions = self.list_extraction_suggestions(project_dir)
        payload = {
            "schema_version": AI_EXTRACTION_QUEUE_SCHEMA_VERSION,
            "project_id": project_dir.expanduser().resolve().name,
            "suggestion_count": len(suggestions),
            "pending_count": len([item for item in suggestions if item.status == AISuggestionStatus.PENDING.value]),
            "accepted_count": len([item for item in suggestions if item.status == AISuggestionStatus.ACCEPTED.value]),
            "rejected_count": len([item for item in suggestions if item.status == AISuggestionStatus.REJECTED.value]),
            "edited_count": len([item for item in suggestions if item.status == AISuggestionStatus.EDITED.value]),
            "suggestions": [ai_suggestion_to_dict(item) for item in suggestions],
            "safety_note": "AI extraction suggestions never write final extraction values without reviewer action.",
        }
        _write_json(self.queue_path(project_dir), payload)
        return self.queue_path(project_dir)

    def _write_validation(self, project_dir: Path, *, suggestion_id: str, validation: dict[str, Any], disease_guard: dict[str, Any]) -> Path:
        item = {
            "suggestion_id": suggestion_id,
            "validation": validation,
            "disease_guard": disease_guard,
        }
        _append_json_item(self.validation_path(project_dir), "validations", item, schema_version=AI_EXTRACTION_VALIDATION_SCHEMA_VERSION)
        return self.validation_path(project_dir)

    def _require(self, project_dir: Path, suggestion_id: str) -> AISuggestion:
        for suggestion in self.list_extraction_suggestions(project_dir):
            if suggestion.suggestion_id == suggestion_id:
                return suggestion
        raise ValueError(f"ai_extraction_suggestion_not_found:{suggestion_id}")

    def _suggestions_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "ai" / "ai_suggestions.json"


def _suggest_effect_row_payload(text: str, *, record_id: str, schema_meta_type: str) -> dict[str, Any]:
    numbers = [float(item) for item in re.findall(r"\b\d+(?:\.\d+)?\b", text)[:12]]
    outcome = _outcome_name(text)
    payload: dict[str, Any] = {
        "record_id": record_id,
        "study_unit_label": f"Suggested unit for {record_id}",
        "outcome_name": outcome,
        "comparison_label": "AI suggested comparison",
        "group_1_label": "Group 1",
        "group_2_label": "Group 2",
        "timepoint": "",
        "analysis_role": "secondary_effect_candidate",
        "source_quote": text[:300],
        "evidence_note": "Generated from parsed text / abstract; requires reviewer verification.",
    }
    if schema_meta_type == CONTINUOUS_OUTCOME_META:
        payload.update(
            {
                "data_input_mode": "raw_group_data",
                "data_fields": {
                    "group_1_n": _num(numbers, 0),
                    "group_1_mean": _num(numbers, 1),
                    "group_1_sd": _num(numbers, 2),
                    "group_2_n": _num(numbers, 3),
                    "group_2_mean": _num(numbers, 4),
                    "group_2_sd": _num(numbers, 5),
                },
            }
        )
    elif schema_meta_type == SURVIVAL_OUTCOME_META:
        payload.update(
            {
                "data_input_mode": "reported_effect_size",
                "data_fields": {
                    "effect_measure": "HR",
                    "effect_value": _num(numbers, 0),
                    "ci_low": _num(numbers, 1),
                    "ci_high": _num(numbers, 2),
                    "adjusted_or_unadjusted": "not_assessed",
                },
            }
        )
    elif schema_meta_type == DIAGNOSTIC_ACCURACY_META_V1:
        payload.update(
            {
                "data_input_mode": "raw_group_data",
                "data_fields": {
                    "tp": _num(numbers, 0),
                    "fp": _num(numbers, 1),
                    "fn": _num(numbers, 2),
                    "tn": _num(numbers, 3),
                },
            }
        )
    else:
        payload.update(
            {
                "data_input_mode": "raw_group_data",
                "data_fields": {
                    "group_1_n": _num(numbers, 0),
                    "group_1_events": _num(numbers, 1),
                    "group_2_n": _num(numbers, 2),
                    "group_2_events": _num(numbers, 3),
                },
            }
        )
    return payload


def _required_fields(schema_meta_type: str, data_input_mode: str) -> tuple[str, ...]:
    if schema_meta_type == CONTINUOUS_OUTCOME_META:
        return ("group_1_n", "group_1_mean", "group_1_sd", "group_2_n", "group_2_mean", "group_2_sd")
    if schema_meta_type == SURVIVAL_OUTCOME_META:
        return ("effect_measure", "effect_value", "ci_low", "ci_high")
    if schema_meta_type == DIAGNOSTIC_ACCURACY_META_V1:
        return ("tp", "fp", "fn", "tn")
    if data_input_mode == "reported_effect_size":
        return ("effect_measure", "effect_value", "ci_low", "ci_high")
    return ("group_1_n", "group_1_events", "group_2_n", "group_2_events")


def _disease_guard(*, text: str, research_question: str) -> dict[str, Any]:
    if not research_question.strip():
        return {"status": "not_assessed", "matched_terms": [], "rejected_terms": [], "confidence": 0.0}
    question_draft = build_search_translation_draft(research_question, target_context="meta_analysis")
    question_terms = {item.lower() for item in [*question_draft.disease_terms_en, *question_draft.disease_terms_zh] if item}
    text_lower = text.lower()
    matched = sorted(term for term in question_terms if term and term.lower() in text_lower)
    status = "passed" if matched or not question_terms else "needs_review"
    return {
        "status": status,
        "matched_terms": matched,
        "rejected_terms": [],
        "confidence": 0.8 if matched else 0.3,
        "target_context": "meta_analysis",
    }


def _confidence(validation: dict[str, Any], disease_guard: dict[str, Any]) -> float:
    base = 0.65 if validation.get("status") == "valid" else 0.35
    guard = float(disease_guard.get("confidence", 0.0) or 0.0)
    return max(0.0, min(1.0, (base + guard) / 2 if guard else base))


def _rationale(schema_meta_type: str, payload: dict[str, Any], validation: dict[str, Any], disease_guard: dict[str, Any]) -> str:
    return (
        f"Testing extraction suggestion for {schema_meta_type}; "
        f"outcome={payload.get('outcome_name', '')}; "
        f"validation={validation.get('status')}; disease_guard={disease_guard.get('status')}."
    )


def _load_parsed_text(project_dir: Path, parser: FullTextParsingService, record_id: str) -> str:
    result = _load_json(parser.result_path(project_dir, record_id))
    text_path = str(result.get("extracted_text_path", ""))
    if not text_path:
        return ""
    path = project_dir.expanduser().resolve() / text_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _append_json_item(path: Path, key: str, item: dict[str, Any], *, schema_version: str) -> None:
    payload = _load_json(path)
    items = [dict(existing) for existing in payload.get(key, []) if isinstance(existing, dict)]
    items.append(item)
    _write_json(
        path,
        {
            "schema_version": payload.get("schema_version") or schema_version,
            "count": len(items),
            key: items,
        },
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _load_json(path: Path) -> dict[str, Any]:
    path = path.expanduser().resolve()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _num(values: list[float], index: int) -> float | str:
    if index >= len(values):
        return ""
    value = values[index]
    return int(value) if value.is_integer() else value


def _outcome_name(text: str) -> str:
    lowered = text.lower()
    for token in ("mortality", "survival", "response", "recurrence", "sensitivity", "specificity"):
        if token in lowered:
            return token
    return "AI suggested outcome"
