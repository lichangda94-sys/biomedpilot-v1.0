from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.extraction_schema_registry_v1_service import ExtractionSchemaRegistryV1Service
from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService
from app.meta_analysis.services.pico_workspace_service import PICOWorkspaceService
from app.meta_analysis.services.quality_service import QualityAssessmentService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


ANALYSIS_PLAN_DRAFT_SCHEMA_VERSION = "meta_analysis_plan_draft.v1"
CONFIRMED_ANALYSIS_PLAN_SCHEMA_VERSION = "meta_confirmed_analysis_plan.v1"
ANALYSIS_PLAN_MANIFEST_SCHEMA_VERSION = "meta_analysis_plan_manifest.v1"


@dataclass(frozen=True)
class AnalysisPlanBuilderResult:
    success: bool
    project_id: str
    plan_id: str
    output_path: str
    manifest_path: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


class AnalysisPlanService:
    def __init__(
        self,
        *,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
        pico_workspace: PICOWorkspaceService | None = None,
        manual_extraction: ManualExtractionEffectRowService | None = None,
        schema_registry: ExtractionSchemaRegistryV1Service | None = None,
        quality_service: QualityAssessmentService | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)
        self._pico_workspace = pico_workspace or PICOWorkspaceService(audit_log=self._audit_log, research_governance=self._governance)
        self._manual_extraction = manual_extraction or ManualExtractionEffectRowService(audit_log=self._audit_log, research_governance=self._governance)
        self._schema_registry = schema_registry or ExtractionSchemaRegistryV1Service(audit_log=self._audit_log, research_governance=self._governance)
        self._quality_service = quality_service or QualityAssessmentService(audit_log=self._audit_log, research_governance=self._governance)

    def draft_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "analysis_plan_draft_v1.json"

    def draft_versions_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "analysis_plan_draft_versions_v1.json"

    def confirmed_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "analysis_plan_confirmed_v1.json"

    def confirmed_versions_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "analysis_plan_confirmed_versions_v1.json"

    def manifest_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "analysis_plan_manifest_v1.json"

    def generate_draft(
        self,
        project_dir: Path,
        *,
        actor: str = "system",
        project_id: str | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> AnalysisPlanBuilderResult:
        project_dir = project_dir.expanduser().resolve()
        confirmed_protocol = self._pico_workspace.load_confirmed(project_dir)
        if confirmed_protocol is None:
            raise ValueError("confirmed_protocol_required_for_analysis_plan")
        project_id = project_id or confirmed_protocol.confirmed_protocol_id or project_dir.name
        meta_type = str((overrides or {}).get("meta_type") or confirmed_protocol.confirmed_meta_type)
        schema = self._schema_registry.get_schema(project_dir, meta_type)
        rows = self._manual_extraction.load_effect_rows(project_dir)
        quality_summary = self._quality_service.quality_summary_for_report(project_dir)
        included, excluded = _split_effect_row_candidates(rows)
        warnings = _analysis_plan_warnings(
            rows=rows,
            included=included,
            quality_summary=quality_summary,
            schema_required_fields=tuple(schema.required_fields) if schema is not None else (),
        )
        defaults = _analysis_defaults_for_meta_type(meta_type, included=included, schema_defaults=dict(schema.analysis_defaults) if schema is not None else {})
        plan_id = f"aplan-draft-{uuid4().hex[:12]}"
        now = _now()
        draft = {
            "schema_version": ANALYSIS_PLAN_DRAFT_SCHEMA_VERSION,
            "analysis_plan_id": plan_id,
            "project_id": project_dir.name,
            "source_confirmed_protocol_id": confirmed_protocol.confirmed_protocol_id,
            "meta_type": meta_type,
            "effect_measure": str((overrides or {}).get("effect_measure") or defaults["effect_measure"]),
            "input_data_type": defaults["input_data_type"],
            "model_default": str((overrides or {}).get("model_default") or defaults["model_default"]),
            "fixed_effect_allowed": True,
            "random_effect_allowed": True,
            "heterogeneity_metrics": ["Q", "I2", "tau2"],
            "subgroup_plan": defaults["subgroup_plan"],
            "sensitivity_plan": defaults["sensitivity_plan"],
            "publication_bias_plan": defaults["publication_bias_plan"],
            "transformation_method": defaults["transformation_method"],
            "zero_cell_correction": defaults["zero_cell_correction"],
            "ci_method": defaults["ci_method"],
            "diagnostic_model_options": defaults["diagnostic_model_options"],
            "prevalence_transformation": defaults["prevalence_transformation"],
            "included_effect_row_candidates": included,
            "excluded_effect_row_candidates": excluded,
            "warnings": warnings,
            "quality_assessment_summary": quality_summary,
            "created_at": now,
            "updated_at": now,
            "status": "draft",
            "governance_refs": [],
            "audit_refs": [],
            "analysis_run_status": "not_started",
            "analysis_ready_dataset_created": False,
            "final_analysis_result_created": False,
            "prisma_advanced": False,
            "medical_interpretation_status": "not_generated",
        }
        output_path = self.draft_path(project_dir)
        _write_json(output_path, draft)
        audit = self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_dir.name,
            actor=actor,
            target_type="analysis_plan",
            target_id=plan_id,
            source_path=str(self._pico_workspace.confirmed_path(project_dir).relative_to(project_dir)),
            output_path=str(output_path.relative_to(project_dir)),
            summary="Analysis plan draft created.",
            details={"status": "draft", "analysis_run_status": "not_started", "prisma_advanced": False},
        )
        governance = self._governance.record_draft_created(
            project_dir,
            project_id=project_dir.name,
            actor=actor,
            target_type="analysis_plan",
            target_id=plan_id,
            after=draft,
            metadata={"analysis_run_status": "not_started", "final_result_status": "not_created"},
        )
        draft["audit_refs"].append(audit.event_id)
        draft["governance_refs"].append(governance.event_id)
        _write_json(output_path, draft)
        self._append_version(self.draft_versions_path(project_dir), draft, schema_version="meta_analysis_plan_draft_versions.v1")
        self._record_candidate_suggestions(project_dir, actor=actor, plan_id=plan_id, included=included, excluded=excluded)
        self._write_manifest(project_dir)
        return AnalysisPlanBuilderResult(True, project_dir.name, plan_id, str(output_path), str(self.manifest_path(project_dir)), "Analysis plan draft created.", draft, tuple(warnings))

    def edit_draft(
        self,
        project_dir: Path,
        *,
        updates: dict[str, Any],
        actor: str = "reviewer",
    ) -> AnalysisPlanBuilderResult:
        if not actor.strip():
            raise ValueError("actor_required_for_analysis_plan_edit")
        project_dir = project_dir.expanduser().resolve()
        before = self.load_draft(project_dir)
        if not before:
            raise ValueError("analysis_plan_draft_not_found")
        allowed = {
            "effect_measure",
            "model_default",
            "subgroup_plan",
            "sensitivity_plan",
            "publication_bias_plan",
            "transformation_method",
            "zero_cell_correction",
            "ci_method",
            "diagnostic_model_options",
            "prevalence_transformation",
            "included_effect_row_candidates",
            "excluded_effect_row_candidates",
            "warnings",
        }
        after = dict(before)
        for key, value in updates.items():
            if key in allowed:
                after[key] = value
        after["updated_at"] = _now()
        after["status"] = "draft"
        after["analysis_run_status"] = "not_started"
        after["analysis_ready_dataset_created"] = False
        after["final_analysis_result_created"] = False
        after["prisma_advanced"] = False
        output_path = self.draft_path(project_dir)
        _write_json(output_path, after)
        audit = self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_dir.name,
            actor=actor,
            target_type="analysis_plan",
            target_id=str(after.get("analysis_plan_id", "")),
            source_path=str(output_path.relative_to(project_dir)),
            output_path=str(output_path.relative_to(project_dir)),
            summary="Analysis plan draft edited.",
            details={"status": "draft", "analysis_run_status": "not_started"},
        )
        governance = self._governance.record_user_confirmation(
            project_dir,
            project_id=project_dir.name,
            action="edit",
            actor=actor,
            target_type="analysis_plan",
            target_id=str(after.get("analysis_plan_id", "")),
            before=before,
            after=after,
            metadata={"analysis_run_status": "not_started", "final_result_status": "not_created"},
        )
        after.setdefault("audit_refs", []).append(audit.event_id)
        after.setdefault("governance_refs", []).append(governance.event_id)
        _write_json(output_path, after)
        self._append_version(self.draft_versions_path(project_dir), after, schema_version="meta_analysis_plan_draft_versions.v1")
        self._write_manifest(project_dir)
        return AnalysisPlanBuilderResult(True, project_dir.name, str(after.get("analysis_plan_id", "")), str(output_path), str(self.manifest_path(project_dir)), "Analysis plan draft edited.", after, tuple(str(item) for item in after.get("warnings", [])))

    def confirm_plan(
        self,
        project_dir: Path,
        *,
        actor: str,
        confirmed_model: str = "",
        confirmed_effect_measure: str = "",
        primary_effect_row_ids: tuple[str, ...] | list[str] | None = None,
        secondary_effect_row_ids: tuple[str, ...] | list[str] | None = None,
    ) -> AnalysisPlanBuilderResult:
        if not actor.strip():
            raise ValueError("actor_required_for_analysis_plan_confirmation")
        project_dir = project_dir.expanduser().resolve()
        draft = self.load_draft(project_dir)
        if not draft:
            raise ValueError("analysis_plan_draft_not_found")
        included_candidates = list(draft.get("included_effect_row_candidates", []))
        primary_ids = [str(item) for item in (primary_effect_row_ids or _candidate_ids(included_candidates, "primary_effect_candidate")) if str(item)]
        secondary_ids = [str(item) for item in (secondary_effect_row_ids or _candidate_ids(included_candidates, "secondary_effect_candidate")) if str(item)]
        now = _now()
        confirmed = {
            "schema_version": CONFIRMED_ANALYSIS_PLAN_SCHEMA_VERSION,
            "confirmed_analysis_plan_id": f"aplan-confirmed-{uuid4().hex[:12]}",
            "plan_state": "confirmed",
            "source_draft_id": str(draft.get("analysis_plan_id", "")),
            "confirmed_effect_measure": confirmed_effect_measure or str(draft.get("effect_measure", "")),
            "confirmed_model": (confirmed_model or str(draft.get("model_default", "random_effects"))).strip(),
            "confirmed_primary_effect_rows": primary_ids,
            "confirmed_secondary_effect_rows": secondary_ids,
            "confirmed_subgroup_plan": dict(draft.get("subgroup_plan", {})) if isinstance(draft.get("subgroup_plan"), dict) else {},
            "confirmed_sensitivity_plan": dict(draft.get("sensitivity_plan", {})) if isinstance(draft.get("sensitivity_plan"), dict) else {},
            "confirmed_publication_bias_plan": dict(draft.get("publication_bias_plan", {})) if isinstance(draft.get("publication_bias_plan"), dict) else {},
            "confirmed_at": now,
            "confirmed_by": actor,
            "version": self._next_confirmed_version(project_dir),
            "locked_for_analysis_run": True,
            "analysis_run_status": "not_started",
            "analysis_ready_dataset_created": False,
            "final_analysis_result_created": False,
            "prisma_advanced": False,
            "medical_interpretation_status": "not_generated",
            "governance_refs": [],
            "audit_refs": [],
        }
        output_path = self.confirmed_path(project_dir)
        _write_json(output_path, confirmed)
        audit = self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_dir.name,
            actor=actor,
            target_type="analysis_plan",
            target_id=confirmed["confirmed_analysis_plan_id"],
            source_path=str(self.draft_path(project_dir).relative_to(project_dir)),
            output_path=str(output_path.relative_to(project_dir)),
            summary="Analysis plan confirmed by reviewer.",
            details={"locked_for_analysis_run": True, "analysis_run_status": "not_started", "prisma_advanced": False},
        )
        governance = self._governance.record_user_confirmation(
            project_dir,
            project_id=project_dir.name,
            action="confirm",
            actor=actor,
            target_type="analysis_plan",
            target_id=confirmed["confirmed_analysis_plan_id"],
            before=draft,
            after=confirmed,
            source_suggestion_id=str(draft.get("analysis_plan_id", "")),
            metadata={"locked_for_analysis_run": True, "analysis_run_status": "not_started", "final_result_status": "not_created"},
        )
        confirmed["audit_refs"].append(audit.event_id)
        confirmed["governance_refs"].append(governance.event_id)
        _write_json(output_path, confirmed)
        self._append_version(self.confirmed_versions_path(project_dir), confirmed, schema_version="meta_analysis_plan_confirmed_versions.v1")
        self._record_candidate_confirmations(project_dir, actor=actor, draft=draft, primary_ids=primary_ids, secondary_ids=secondary_ids)
        self._write_manifest(project_dir)
        return AnalysisPlanBuilderResult(True, project_dir.name, confirmed["confirmed_analysis_plan_id"], str(output_path), str(self.manifest_path(project_dir)), "Analysis plan confirmed by reviewer; no statistics were run.", confirmed, ())

    def load_draft(self, project_dir: Path) -> dict[str, Any]:
        return _load_json(self.draft_path(project_dir))

    def load_confirmed(self, project_dir: Path) -> dict[str, Any]:
        return _load_json(self.confirmed_path(project_dir))

    def _record_candidate_suggestions(
        self,
        project_dir: Path,
        *,
        actor: str,
        plan_id: str,
        included: list[dict[str, Any]],
        excluded: list[dict[str, Any]],
    ) -> None:
        for action, candidates in (("candidate_selected", included), ("candidate_excluded", excluded)):
            for candidate in candidates:
                target_id = str(candidate.get("effect_row_id", ""))
                if not target_id:
                    continue
                self._governance.record_suggestion_created(
                    project_dir,
                    project_id=project_dir.name,
                    actor=actor,
                    target_type="effect_row_candidate",
                    target_id=f"{plan_id}:{target_id}",
                    after=candidate,
                    source_suggestion_id=plan_id,
                    metadata={"analysis_plan_candidate_action": action, "analysis_ready_dataset_created": False},
                )
                self._audit_log.record_event(
                    project_dir,
                    event_type="record_saved",
                    project_id=project_dir.name,
                    actor=actor,
                    target_type="analysis_plan_effect_row_candidate",
                    target_id=f"{plan_id}:{target_id}",
                    source_path=str(self._manual_extraction.effect_rows_path(project_dir).relative_to(project_dir)),
                    output_path=str(self.draft_path(project_dir).relative_to(project_dir)),
                    summary=f"Analysis plan effect row {action}.",
                    details={"analysis_plan_candidate_action": action, "effect_row_id": target_id},
                )

    def _record_candidate_confirmations(
        self,
        project_dir: Path,
        *,
        actor: str,
        draft: dict[str, Any],
        primary_ids: list[str],
        secondary_ids: list[str],
    ) -> None:
        confirmed_ids = set(primary_ids + secondary_ids)
        candidates = list(draft.get("included_effect_row_candidates", [])) + list(draft.get("excluded_effect_row_candidates", []))
        for candidate in candidates:
            effect_row_id = str(candidate.get("effect_row_id", ""))
            if not effect_row_id:
                continue
            action = "accept" if effect_row_id in confirmed_ids else "reject"
            self._governance.record_user_confirmation(
                project_dir,
                project_id=project_dir.name,
                action=action,
                actor=actor,
                target_type="effect_row_candidate",
                target_id=f"{draft.get('analysis_plan_id', '')}:{effect_row_id}",
                before=candidate,
                after={**candidate, "confirmed_candidate_status": "selected" if action == "accept" else "excluded"},
                source_suggestion_id=str(draft.get("analysis_plan_id", "")),
                metadata={"analysis_plan_candidate_action": "candidate_selected" if action == "accept" else "candidate_excluded"},
            )

    def _write_manifest(self, project_dir: Path) -> None:
        project_dir = project_dir.expanduser().resolve()
        draft = self.load_draft(project_dir)
        confirmed = self.load_confirmed(project_dir)
        payload = {
            "schema_version": ANALYSIS_PLAN_MANIFEST_SCHEMA_VERSION,
            "project_id": project_dir.name,
            "draft_path": str(self.draft_path(project_dir).relative_to(project_dir)),
            "confirmed_path": str(self.confirmed_path(project_dir).relative_to(project_dir)),
            "draft_status": "draft" if draft else "missing",
            "confirmed_status": "confirmed" if confirmed else "not_confirmed",
            "analysis_run_status": "not_started",
            "analysis_ready_dataset_created": False,
            "final_analysis_result_created": False,
            "prisma_advanced": False,
            "updated_at": _now(),
        }
        _write_json(self.manifest_path(project_dir), payload)

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


def _split_effect_row_candidates(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for row in rows:
        candidate = _candidate_from_row(row)
        validation = str(row.get("validation_status", ""))
        role = str(row.get("analysis_role", ""))
        eligibility = str(row.get("analysis_eligibility", ""))
        if (
            role != "not_for_quantitative_analysis"
            and eligibility not in {"blocked", "excluded_by_user"}
            and validation in {"valid", "valid_with_warnings"}
        ):
            included.append(candidate)
        else:
            excluded.append({**candidate, "exclusion_reason": _candidate_exclusion_reason(row)})
    return included, excluded


def _candidate_from_row(row: dict[str, Any]) -> dict[str, Any]:
    reported = dict(row.get("reported_effect_size", {})) if isinstance(row.get("reported_effect_size"), dict) else {}
    raw = dict(row.get("raw_group_data", {})) if isinstance(row.get("raw_group_data"), dict) else {}
    effect_measure = str(reported.get("effect_measure") or row.get("effect_measure") or "")
    return {
        "effect_row_id": str(row.get("effect_row_id", "")),
        "study_unit_id": str(row.get("study_unit_id", "")),
        "study_unit_label": str(row.get("study_unit_label", "")),
        "record_id": str(row.get("record_id", "")),
        "schema_meta_type": str(row.get("schema_meta_type", "")),
        "comparison_label": str(row.get("comparison_label", "")),
        "outcome_name": str(row.get("outcome_name", "")),
        "timepoint": str(row.get("timepoint", "")),
        "subgroup_label": str(row.get("subgroup_label", "")),
        "data_input_mode": str(row.get("data_input_mode", "")),
        "effect_measure": effect_measure,
        "analysis_role": str(row.get("analysis_role", "")),
        "validation_status": str(row.get("validation_status", "")),
        "analysis_eligibility": str(row.get("analysis_eligibility", "")),
        "adjusted_or_unadjusted": str(reported.get("adjusted_or_unadjusted", "")),
        "has_raw_group_data": any(value not in ("", None) for value in raw.values()),
        "has_reported_effect_size": any(value not in ("", None) for value in reported.values()),
        "diagnostics": dict(row.get("diagnostics", {})) if isinstance(row.get("diagnostics"), dict) else {},
        "warnings": list(row.get("warnings", [])) if isinstance(row.get("warnings"), list) else [],
    }


def _candidate_exclusion_reason(row: dict[str, Any]) -> str:
    if str(row.get("analysis_role", "")) == "not_for_quantitative_analysis":
        return "not_for_quantitative_analysis"
    if str(row.get("analysis_eligibility", "")) in {"blocked", "excluded_by_user"}:
        return f"analysis_eligibility:{row.get('analysis_eligibility')}"
    if str(row.get("validation_status", "")) not in {"valid", "valid_with_warnings"}:
        return f"validation_status:{row.get('validation_status')}"
    return "not_selected"


def _analysis_defaults_for_meta_type(meta_type: str, *, included: list[dict[str, Any]], schema_defaults: dict[str, Any]) -> dict[str, Any]:
    normalized = meta_type.strip()
    row_effects = [str(item.get("effect_measure", "")).upper() for item in included if str(item.get("effect_measure", "")).strip()]
    first_row_effect = row_effects[0] if row_effects else ""
    defaults = {
        "effect_measure": first_row_effect or "OR",
        "input_data_type": _common_value(included, "data_input_mode") or "mixed",
        "model_default": str(schema_defaults.get("model") or "random_effects"),
        "subgroup_plan": {"status": "draft", "variables": _nonempty_values(included, "subgroup_label")},
        "sensitivity_plan": {"leave_one_out": "planned_if_study_count_at_least_3"},
        "publication_bias_plan": {"egger": "planned_if_study_count_at_least_10", "funnel": "planned_if_study_count_at_least_10"},
        "transformation_method": str(schema_defaults.get("transformation") or schema_defaults.get("scale") or "none"),
        "zero_cell_correction": str(schema_defaults.get("zero_cell_handling") or schema_defaults.get("continuity_correction") or "not_applicable"),
        "ci_method": "95_percent_wald_or_inverse_variance",
        "diagnostic_model_options": {"basic_2x2": False, "bivariate_hsroc": "not_implemented"},
        "prevalence_transformation": "",
    }
    if normalized in {"binary_outcome_meta", "treatment_comparative_meta"}:
        defaults.update({"effect_measure": first_row_effect or "OR", "zero_cell_correction": "continuity_0.5"})
    elif normalized == "continuous_outcome_meta":
        defaults.update({"effect_measure": first_row_effect or "MD", "zero_cell_correction": "not_applicable"})
    elif normalized == "survival_outcome_meta":
        defaults.update({"effect_measure": first_row_effect or "HR", "transformation_method": "log"})
    elif normalized == "prevalence_incidence_meta":
        defaults.update({"effect_measure": first_row_effect or "PREVALENCE", "prevalence_transformation": "logit", "transformation_method": "logit"})
    elif normalized == "diagnostic_accuracy_meta":
        defaults.update({"effect_measure": first_row_effect or "DOR", "input_data_type": "diagnostic_2x2", "diagnostic_model_options": {"basic_2x2": True, "bivariate_hsroc": "not_implemented"}})
    elif normalized == "correlation_meta":
        defaults.update({"effect_measure": first_row_effect or "Fisher z", "transformation_method": "fisher_z"})
    elif normalized == "dose_response_meta":
        defaults.update({"effect_measure": first_row_effect or "dose_response_slope", "model_default": "dose_response_placeholder", "sensitivity_plan": {"status": "coming_soon"}})
    return defaults


def _analysis_plan_warnings(
    *,
    rows: list[dict[str, Any]],
    included: list[dict[str, Any]],
    quality_summary: dict[str, Any],
    schema_required_fields: tuple[str, ...],
) -> list[str]:
    warnings: list[str] = []
    if not rows:
        warnings.append("effect_rows_missing")
    if not included:
        warnings.append("no_valid_effect_row_candidates")
    for row in rows:
        missing = list(dict(row.get("diagnostics", {})).get("missing_required_fields", [])) if isinstance(row.get("diagnostics"), dict) else []
        if missing:
            warnings.append(f"effect_row_missing_required_fields:{row.get('effect_row_id')}:{','.join(str(item) for item in missing)}")
        elif str(row.get("validation_status", "")) == "invalid_missing_required_fields":
            warnings.append(f"effect_row_missing_required_fields:{row.get('effect_row_id')}")
    warnings.extend(_multiple_primary_warnings(rows))
    effects = {str(item.get("effect_measure", "")).upper() for item in included if str(item.get("effect_measure", "")).strip()}
    if len(effects) > 1:
        warnings.append("effect_measure_mixed")
    adjusted = {str(item.get("adjusted_or_unadjusted", "")).lower() for item in included if str(item.get("adjusted_or_unadjusted", "")).strip()}
    if len(adjusted) > 1:
        warnings.append("adjusted_unadjusted_mixed")
    outcomes = {str(item.get("outcome_name", "")).lower() for item in included if str(item.get("outcome_name", "")).strip()}
    if len(outcomes) > 1:
        warnings.append("outcome_name_inconsistent")
    timepoints = {str(item.get("timepoint", "")).lower() for item in included if str(item.get("timepoint", "")).strip()}
    if len(timepoints) > 1:
        warnings.append("timepoint_inconsistent")
    assessment_count = int(quality_summary.get("assessment_count", 0) or 0)
    completed_count = int(quality_summary.get("completed_by_user_count", 0) or 0)
    if assessment_count == 0 or completed_count < assessment_count:
        warnings.append("quality_assessment_not_completed")
    study_count = len({str(item.get("study_unit_id", "")) for item in included if str(item.get("study_unit_id", "")).strip()})
    if study_count < 10:
        warnings.append("study_count_less_than_10_publication_bias_not_recommended")
    if schema_required_fields and not included:
        warnings.append("schema_required_fields_not_satisfied")
    return _dedupe(warnings)


def _multiple_primary_warnings(rows: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for row in rows:
        if str(row.get("analysis_role", "")) == "primary_effect_candidate":
            unit_id = str(row.get("study_unit_id", ""))
            counts[unit_id] = counts.get(unit_id, 0) + 1
    return [f"multiple_primary_effect_candidates:{unit_id}" for unit_id, count in counts.items() if unit_id and count > 1]


def _candidate_ids(candidates: list[dict[str, Any]], role: str) -> list[str]:
    return [str(item.get("effect_row_id", "")) for item in candidates if str(item.get("analysis_role", "")) == role and str(item.get("effect_row_id", ""))]


def _common_value(items: list[dict[str, Any]], key: str) -> str:
    values = _nonempty_values(items, key)
    return values[0] if len(values) == 1 else ""


def _nonempty_values(items: list[dict[str, Any]], key: str) -> list[str]:
    return sorted({str(item.get(key, "")).strip() for item in items if str(item.get(key, "")).strip()})


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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
