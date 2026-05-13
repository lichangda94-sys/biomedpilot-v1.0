from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any
from uuid import uuid4

from app.meta_analysis.models.analysis_result import StudyMetaAnalysisResult
from app.meta_analysis.services.analysis_plan_service import AnalysisPlanService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.manual_extraction_effect_row_service import ManualExtractionEffectRowService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService
from app.meta_analysis.stats.heterogeneity import calculate_heterogeneity
from app.meta_analysis.stats.meta_effects import (
    CORRELATION_EFFECT_MEASURES,
    LOG_SCALE_EFFECT_MEASURES,
    StudyEffectEstimate,
    ci_to_standard_error,
    diagnostic_accuracy_metrics,
    diagnostic_ratio_variance,
    fisher_z_effect,
    proportion_effect,
    report_effect_values,
)


META_STATISTICS_ANALYSIS_RUN_SCHEMA_VERSION = "meta_statistics_analysis_run.v2"
META_STATISTICS_STANDARDIZED_RESULT_SCHEMA_VERSION = "meta_statistics_standardized_result.v2"
META_STATISTICS_ANALYSIS_MANIFEST_SCHEMA_VERSION = "meta_statistics_analysis_manifest.v2"
META_STATISTICS_ANALYSIS_AUDIT_SCHEMA_VERSION = "meta_statistics_analysis_audit.v2"


@dataclass(frozen=True)
class MetaStatisticsRunResult:
    success: bool
    project_id: str
    analysis_run_id: str
    result_id: str
    run_path: str
    result_path: str
    manifest_path: str
    message: str
    analysis_run: dict[str, Any] = field(default_factory=dict)
    standardized_result: dict[str, Any] = field(default_factory=dict)


class MetaStatisticsEngineService:
    def __init__(
        self,
        *,
        analysis_plan_service: AnalysisPlanService | None = None,
        manual_extraction: ManualExtractionEffectRowService | None = None,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)
        self._plan_service = analysis_plan_service or AnalysisPlanService(audit_log=self._audit_log, research_governance=self._governance)
        self._manual_extraction = manual_extraction or ManualExtractionEffectRowService(audit_log=self._audit_log, research_governance=self._governance)

    def runs_dir(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "runs"

    def results_dir(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "results"

    def manifest_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "analysis_manifest.json"

    def analysis_audit_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "logs" / "analysis" / "analysis_audit.jsonl"

    def run_statistics(
        self,
        project_dir: Path,
        *,
        actor: str = "reviewer",
        model: str = "",
    ) -> MetaStatisticsRunResult:
        project_dir = project_dir.expanduser().resolve()
        confirmed_plan = self._plan_service.load_confirmed(project_dir)
        if not confirmed_plan:
            raise ValueError("confirmed_analysis_plan_required")
        draft = self._plan_service.load_draft(project_dir)
        run_id = f"arun-{uuid4().hex[:12]}"
        result_id = f"statres-{uuid4().hex[:12]}"
        requested_gov = self._governance.record_draft_created(
            project_dir,
            project_id=project_dir.name,
            actor=actor,
            target_type="analysis_run",
            target_id=run_id,
            after={"source_confirmed_analysis_plan_id": confirmed_plan.get("confirmed_analysis_plan_id", ""), "status": "requested"},
            metadata={"workflow_action": "analysis_run requested", "testing_level": True},
        )
        requested_audit = self._record_analysis_audit(
            project_dir,
            actor=actor,
            action="analysis_run requested",
            target_type="analysis_run",
            target_id=run_id,
            after={"source_confirmed_analysis_plan_id": confirmed_plan.get("confirmed_analysis_plan_id", "")},
        )
        included_rows, excluded_rows = self._resolve_effect_rows(project_dir, confirmed_plan)
        validation = _validate_inputs(confirmed_plan=confirmed_plan, draft=draft, included_rows=included_rows)
        if validation["blocking_errors"]:
            raise ValueError(";".join(validation["blocking_errors"]))
        effects = [
            _effect_from_extraction_row(
                row,
                effect_measure=str(confirmed_plan.get("confirmed_effect_measure") or draft.get("effect_measure") or ""),
            )
            for row in included_rows
        ]
        selected_model = _normalize_model(model or str(confirmed_plan.get("confirmed_model") or draft.get("model_default") or "random"))
        pooled = _pool_effects_v2(effects, effect_measure=str(confirmed_plan.get("confirmed_effect_measure") or draft.get("effect_measure") or effects[0].effect_measure), model=selected_model)
        study_results = [_study_result(effect, pooled["weights"][index], source_row=included_rows[index]) for index, effect in enumerate(effects)]
        warnings = _dedupe([*validation["warnings"], *[warning for effect in effects for warning in effect.warnings]])
        standardized = {
            "schema_version": META_STATISTICS_STANDARDIZED_RESULT_SCHEMA_VERSION,
            "analysis_run_id": run_id,
            "analysis_result_id": result_id,
            "source_confirmed_analysis_plan_id": str(confirmed_plan.get("confirmed_analysis_plan_id", "")),
            "project_id": project_dir.name,
            "meta_type": str(draft.get("meta_type", "")),
            "effect_measure": str(confirmed_plan.get("confirmed_effect_measure") or draft.get("effect_measure") or effects[0].effect_measure),
            "model": selected_model,
            "pooled_effect": pooled["pooled_effect"],
            "ci_low": pooled["ci_low"],
            "ci_high": pooled["ci_high"],
            "p_value": pooled["p_value"],
            "z_value": pooled["z_value"],
            "heterogeneity_q": pooled["heterogeneity_q"],
            "heterogeneity_p": pooled["heterogeneity_p"],
            "i_squared": pooled["i_squared"],
            "tau_squared": pooled["tau_squared"],
            "study_results": study_results,
            "subgroup_results": _subgroup_results(included_rows, effects, selected_model),
            "sensitivity_results": _leave_one_out_results(included_rows, effects, selected_model),
            "publication_bias_results": _publication_bias_results(study_results),
            "diagnostics": {
                "input_validation_status": validation["status"],
                "blocking_errors": validation["blocking_errors"],
                "warnings": warnings,
                "included_effect_row_count": len(included_rows),
                "excluded_effect_row_count": len(excluded_rows),
            },
            "testing_level_notice": "Developer Preview / testing-level statistics only; not production-grade statistical software.",
            "medical_conclusion_status": "not_generated",
            "production_grade": False,
            "created_at": _now(),
        }
        run_payload = {
            "schema_version": META_STATISTICS_ANALYSIS_RUN_SCHEMA_VERSION,
            "analysis_run_id": run_id,
            "source_confirmed_analysis_plan_id": str(confirmed_plan.get("confirmed_analysis_plan_id", "")),
            "project_id": project_dir.name,
            "meta_type": standardized["meta_type"],
            "effect_measure": standardized["effect_measure"],
            "model": selected_model,
            "included_effect_rows": [str(row.get("effect_row_id", "")) for row in included_rows],
            "excluded_effect_rows": [str(row.get("effect_row_id", "")) for row in excluded_rows],
            "input_validation_status": validation["status"],
            "result_status": "testing_result_generated",
            "warnings": warnings,
            "created_at": standardized["created_at"],
            "audit_refs": [requested_audit],
            "governance_refs": [requested_gov.event_id],
            "testing_level": True,
            "prisma_advanced": False,
            "medical_conclusion_status": "not_generated",
        }
        run_path = self.runs_dir(project_dir) / f"{run_id}.json"
        result_path = self.results_dir(project_dir) / f"{run_id}_result.json"
        _write_json(run_path, run_payload)
        _write_json(result_path, standardized)
        completed_audit = self._record_analysis_audit(
            project_dir,
            actor=actor,
            action="analysis_run executed",
            target_type="analysis_run",
            target_id=run_id,
            before={"status": "requested"},
            after={"status": "testing_result_generated", "result_id": result_id},
        )
        result_audit = self._audit_log.record_event(
            project_dir,
            event_type="analysis_run_completed",
            project_id=project_dir.name,
            actor=actor,
            target_type="analysis_result",
            target_id=result_id,
            source_path=str(self._plan_service.confirmed_path(project_dir).relative_to(project_dir)),
            output_path=str(result_path.relative_to(project_dir)),
            summary="Meta statistics engine v2 generated a testing-level standardized result.",
            details={"analysis_run_id": run_id, "testing_level": True, "prisma_advanced": False, "medical_conclusion_status": "not_generated"},
        )
        executed_gov = self._governance.record_suggestion_created(
            project_dir,
            project_id=project_dir.name,
            actor=actor,
            target_type="analysis_run",
            target_id=run_id,
            after=run_payload,
            source_suggestion_id=str(confirmed_plan.get("confirmed_analysis_plan_id", "")),
            metadata={"workflow_action": "analysis_run executed", "testing_level": True},
        )
        result_gov = self._governance.record_suggestion_created(
            project_dir,
            project_id=project_dir.name,
            actor=actor,
            target_type="analysis_result",
            target_id=result_id,
            after=standardized,
            source_suggestion_id=run_id,
            metadata={"workflow_action": "analysis_result generated", "reviewed_status": "placeholder_not_reviewed", "medical_conclusion_status": "not_generated"},
        )
        run_payload["audit_refs"].extend([completed_audit, result_audit.event_id])
        run_payload["governance_refs"].extend([executed_gov.event_id, result_gov.event_id])
        _write_json(run_path, run_payload)
        self._write_manifest(project_dir, latest_run_id=run_id, latest_result_id=result_id)
        return MetaStatisticsRunResult(
            True,
            project_dir.name,
            run_id,
            result_id,
            str(run_path),
            str(result_path),
            str(self.manifest_path(project_dir)),
            "Testing-level meta statistics run completed from confirmed analysis plan.",
            run_payload,
            standardized,
        )

    def load_standardized_result(self, project_dir: Path, analysis_run_id: str) -> dict[str, Any]:
        return _load_json(self.results_dir(project_dir) / f"{analysis_run_id}_result.json")

    def _resolve_effect_rows(self, project_dir: Path, confirmed_plan: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        rows = self._manual_extraction.load_effect_rows(project_dir)
        by_id = {str(row.get("effect_row_id", "")): row for row in rows}
        included_ids = [
            str(item)
            for item in [
                *list(confirmed_plan.get("confirmed_primary_effect_rows", [])),
                *list(confirmed_plan.get("confirmed_secondary_effect_rows", [])),
            ]
            if str(item)
        ]
        included = [by_id[item] for item in included_ids if item in by_id]
        excluded = [row for row in rows if str(row.get("effect_row_id", "")) not in set(included_ids)]
        return included, excluded

    def _record_analysis_audit(
        self,
        project_dir: Path,
        *,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> str:
        path = self.analysis_audit_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        event_id = f"anaudit-{uuid4().hex[:12]}"
        payload = {
            "schema_version": META_STATISTICS_ANALYSIS_AUDIT_SCHEMA_VERSION,
            "event_id": event_id,
            "project_id": project_dir.expanduser().resolve().name,
            "actor": actor,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "before": before or {},
            "after": after or {},
            "created_at": _now(),
            "testing_level": True,
            "prisma_advanced": False,
            "medical_conclusion_status": "not_generated",
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        return event_id

    def _write_manifest(self, project_dir: Path, *, latest_run_id: str, latest_result_id: str) -> None:
        runs = sorted(self.runs_dir(project_dir).glob("*.json")) if self.runs_dir(project_dir).exists() else []
        payload = {
            "schema_version": META_STATISTICS_ANALYSIS_MANIFEST_SCHEMA_VERSION,
            "project_id": project_dir.expanduser().resolve().name,
            "latest_analysis_run_id": latest_run_id,
            "latest_result_id": latest_result_id,
            "run_count": len(runs),
            "runs_path": str(self.runs_dir(project_dir).relative_to(project_dir.expanduser().resolve())),
            "results_path": str(self.results_dir(project_dir).relative_to(project_dir.expanduser().resolve())),
            "analysis_audit_path": str(self.analysis_audit_path(project_dir).relative_to(project_dir.expanduser().resolve())),
            "testing_level": True,
            "production_grade": False,
            "prisma_advanced": False,
            "medical_conclusion_status": "not_generated",
            "updated_at": _now(),
        }
        _write_json(self.manifest_path(project_dir), payload)


def _validate_inputs(*, confirmed_plan: dict[str, Any], draft: dict[str, Any], included_rows: list[dict[str, Any]]) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    if not confirmed_plan.get("confirmed_analysis_plan_id"):
        errors.append("confirmed_analysis_plan_id_missing")
    if not included_rows:
        errors.append("confirmed_analysis_plan_has_no_effect_rows")
    statuses = {str(row.get("validation_status", "")) for row in included_rows}
    if not statuses <= {"valid", "valid_with_warnings"}:
        errors.append("included_effect_rows_have_validation_errors")
    effect_measure = str(confirmed_plan.get("confirmed_effect_measure") or draft.get("effect_measure") or "").upper()
    row_effects = {_row_effect_measure(row, effect_measure).upper() for row in included_rows if _row_effect_measure(row, effect_measure)}
    if len(row_effects) > 1:
        warnings.append("effect_measure_mixed")
    adjusted = {_adjustment_status(row) for row in included_rows if _adjustment_status(row)}
    if len(adjusted) > 1:
        warnings.append("adjusted_unadjusted_mixed")
    outcomes = {str(row.get("outcome_name", "")).lower() for row in included_rows if str(row.get("outcome_name", "")).strip()}
    if len(outcomes) > 1:
        warnings.append("outcome_timepoint_or_outcome_name_inconsistent")
    timepoints = {str(row.get("timepoint", "")).lower() for row in included_rows if str(row.get("timepoint", "")).strip()}
    if len(timepoints) > 1:
        warnings.append("outcome_timepoint_or_outcome_name_inconsistent")
    if len(included_rows) < 10:
        warnings.append("egger_funnel_not_recommended_study_count_less_than_10")
    if any(_needs_zero_cell_correction(row, effect_measure) for row in included_rows):
        warnings.append("zero_cell_correction_required")
    if str(draft.get("meta_type", "")) == "diagnostic_accuracy_meta":
        for row in included_rows:
            raw = _raw(row)
            if not all(_has_value(raw.get(field)) for field in ("tp", "fp", "fn", "tn")):
                errors.append(f"diagnostic_2x2_incomplete:{row.get('effect_row_id')}")
    return {
        "status": "invalid" if errors else ("valid_with_warnings" if warnings else "valid"),
        "blocking_errors": _dedupe(errors),
        "warnings": _dedupe(warnings),
    }


def _effect_from_extraction_row(row: dict[str, Any], *, effect_measure: str) -> StudyEffectEstimate:
    raw = _raw(row)
    reported = _reported(row)
    measure = _row_effect_measure(row, effect_measure)
    meta_type = str(row.get("schema_meta_type", ""))
    warnings = list(row.get("warnings", [])) if isinstance(row.get("warnings"), list) else []
    if meta_type in {"binary_outcome_meta", "treatment_comparative_meta"} or {"group_1_events", "group_2_events"} <= set(raw):
        return _binary_effect(row, measure or "OR", warnings)
    if meta_type == "continuous_outcome_meta" or {"group_1_mean", "group_2_mean"} <= set(raw):
        return _continuous_effect(row, measure or "MD", warnings)
    if meta_type == "survival_outcome_meta" or measure == "HR":
        return _reported_effect(row, measure or "HR", warnings)
    if meta_type == "prevalence_incidence_meta":
        return _prevalence_effect(row, measure or "PREVALENCE", warnings)
    if meta_type == "diagnostic_accuracy_meta":
        return _diagnostic_effect(row, measure or "DOR", warnings)
    if meta_type == "correlation_meta" or measure in {"CORRELATION", "PEARSON_R", "SPEARMAN_R", "FISHER Z", "FISHER_Z"}:
        if _has_value(reported.get("effect_value")) and _has_value(reported.get("ci_low")) and _has_value(reported.get("ci_high")):
            return _reported_effect(row, "CORRELATION" if measure in {"FISHER Z", "FISHER_Z"} else measure, warnings)
        r = float(reported.get("effect_value", raw.get("r", 0)))
        n = float(raw.get("sample_size", raw.get("group_1_n", 0)))
        theta, variance = fisher_z_effect(r, n)
        return _make_effect(row, "CORRELATION", theta, variance, warnings)
    return _reported_effect(row, measure or str(reported.get("effect_measure") or "OR"), warnings)


def _binary_effect(row: dict[str, Any], measure: str, warnings: list[str]) -> StudyEffectEstimate:
    raw = _raw(row)
    a = float(raw["group_1_events"])
    n1 = float(raw["group_1_n"])
    c = float(raw["group_2_events"])
    n0 = float(raw["group_2_n"])
    b = n1 - a
    d = n0 - c
    measure = measure.upper()
    if measure in {"OR", "RR"} and min(a, b, c, d) == 0:
        a += 0.5
        b += 0.5
        c += 0.5
        d += 0.5
        n1 = a + b
        n0 = c + d
        warnings = [*warnings, "zero_event_correction_applied"]
    if measure == "OR":
        theta = math.log((a * d) / (b * c))
        variance = (1 / a) + (1 / b) + (1 / c) + (1 / d)
    elif measure == "RR":
        theta = math.log((a / n1) / (c / n0))
        variance = (1 / a) - (1 / n1) + (1 / c) - (1 / n0)
    elif measure == "RD":
        p1 = a / n1
        p0 = c / n0
        theta = p1 - p0
        variance = (p1 * (1 - p1) / n1) + (p0 * (1 - p0) / n0)
    else:
        raise ValueError(f"unsupported_binary_effect_measure:{measure}")
    return _make_effect(row, measure, theta, variance, warnings)


def _continuous_effect(row: dict[str, Any], measure: str, warnings: list[str]) -> StudyEffectEstimate:
    raw = _raw(row)
    n1 = float(raw["group_1_n"])
    n0 = float(raw["group_2_n"])
    mean1 = float(raw["group_1_mean"])
    mean0 = float(raw["group_2_mean"])
    sd1 = float(raw["group_1_sd"])
    sd0 = float(raw["group_2_sd"])
    measure = measure.upper()
    mean_diff = mean1 - mean0
    if measure == "MD":
        theta = mean_diff
        variance = (sd1**2 / n1) + (sd0**2 / n0)
    elif measure == "SMD":
        pooled_sd = math.sqrt((((n1 - 1) * sd1**2) + ((n0 - 1) * sd0**2)) / (n1 + n0 - 2))
        theta = (1 - (3 / (4 * (n1 + n0) - 9))) * (mean_diff / pooled_sd)
        variance = ((n1 + n0) / (n1 * n0)) + ((theta**2) / (2 * (n1 + n0 - 2)))
    else:
        raise ValueError(f"unsupported_continuous_effect_measure:{measure}")
    return _make_effect(row, measure, theta, variance, warnings)


def _reported_effect(row: dict[str, Any], measure: str, warnings: list[str]) -> StudyEffectEstimate:
    reported = _reported(row)
    measure = measure.upper()
    effect = float(reported["effect_value"])
    low = float(reported["ci_low"])
    high = float(reported["ci_high"])
    if measure in LOG_SCALE_EFFECT_MEASURES:
        theta = math.log(effect)
        se = ci_to_standard_error(low, high, log_scale=True)
    elif measure in CORRELATION_EFFECT_MEASURES:
        theta, _unused = fisher_z_effect(effect, 10_000)
        se = ci_to_standard_error(low, high, log_scale=False)
    else:
        theta = effect
        se = ci_to_standard_error(low, high, log_scale=False)
    return _make_effect(row, measure, theta, se**2, warnings)


def _prevalence_effect(row: dict[str, Any], measure: str, warnings: list[str]) -> StudyEffectEstimate:
    raw = _raw(row)
    events = float(raw.get("events", raw.get("group_1_events", 0)))
    total = float(raw.get("total", raw.get("group_1_n", 0)))
    theta, variance, warnings = proportion_effect(events, total, measure=measure.upper(), warnings=warnings)
    return _make_effect(row, measure.upper(), theta, variance, warnings)


def _diagnostic_effect(row: dict[str, Any], measure: str, warnings: list[str]) -> StudyEffectEstimate:
    raw = _raw(row)
    tp = float(raw["tp"])
    fp = float(raw["fp"])
    fn = float(raw["fn"])
    tn = float(raw["tn"])
    measure = measure.upper()
    metrics = diagnostic_accuracy_metrics(tp=tp, fp=fp, fn=fn, tn=tn)
    if measure == "SENSITIVITY":
        theta, variance, warnings = proportion_effect(tp, tp + fn, measure=measure, warnings=warnings)
    elif measure == "SPECIFICITY":
        theta, variance, warnings = proportion_effect(tn, tn + fp, measure=measure, warnings=warnings)
    elif measure in {"PLR", "NLR", "DOR"}:
        effect = getattr(metrics, measure.lower())
        theta = math.log(effect)
        variance = diagnostic_ratio_variance(tp=tp, fp=fp, fn=fn, tn=tn, measure=measure)
    else:
        raise ValueError(f"unsupported_diagnostic_effect_measure:{measure}")
    return _make_effect(row, measure, theta, variance, [*warnings, "diagnostic_2x2_testing_basic"])


def _pool_effects_v2(effects: list[StudyEffectEstimate], *, effect_measure: str, model: str) -> dict[str, Any]:
    heterogeneity = calculate_heterogeneity(effects)
    if model == "random":
        weights = [1 / (effect.variance + heterogeneity.tau_squared) for effect in effects]
    else:
        weights = [1 / effect.variance for effect in effects]
    pooled_theta = sum(weight * effect.transformed_effect for weight, effect in zip(weights, effects, strict=True)) / sum(weights)
    pooled_variance = 1 / sum(weights)
    pooled_se = math.sqrt(pooled_variance)
    pooled_effect, ci_low, ci_high = report_effect_values(effect_measure, pooled_theta, pooled_se)
    z_value = pooled_theta / pooled_se if pooled_se > 0 else 0.0
    return {
        "model": model,
        "pooled_effect": pooled_effect,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "p_value": math.erfc(abs(z_value) / math.sqrt(2)),
        "z_value": z_value,
        "heterogeneity_q": heterogeneity.q_statistic,
        "heterogeneity_p": _chi_square_survival_approx(heterogeneity.q_statistic, len(effects) - 1),
        "i_squared": heterogeneity.i_squared,
        "tau_squared": heterogeneity.tau_squared,
        "weights": weights,
    }


def _study_result(effect: StudyEffectEstimate, weight: float, *, source_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "effect_row_id": str(source_row.get("effect_row_id", "")),
        "study_unit_id": str(source_row.get("study_unit_id", "")),
        "study_id": effect.study_id,
        "record_id": effect.record_id,
        "first_author": effect.first_author,
        "year": effect.year,
        "outcome_name": str(source_row.get("outcome_name", "")),
        "timepoint": str(source_row.get("timepoint", "")),
        "subgroup_label": str(source_row.get("subgroup_label", "")),
        "effect": effect.effect,
        "ci_low": effect.ci_lower,
        "ci_high": effect.ci_upper,
        "standard_error": effect.standard_error,
        "variance": effect.variance,
        "weight": weight,
        "transformed_effect": effect.transformed_effect,
        "adjusted": effect.adjusted,
        "warnings": list(effect.warnings),
    }


def _subgroup_results(rows: list[dict[str, Any]], effects: list[StudyEffectEstimate], model: str) -> list[dict[str, Any]]:
    groups: dict[str, list[tuple[dict[str, Any], StudyEffectEstimate]]] = {}
    for row, effect in zip(rows, effects, strict=True):
        label = str(row.get("subgroup_label", "") or "overall")
        groups.setdefault(label, []).append((row, effect))
    results = []
    for label, pairs in groups.items():
        pooled = _pool_effects_v2([effect for _row, effect in pairs], effect_measure=pairs[0][1].effect_measure, model=model)
        results.append({"subgroup_label": label, "study_count": len(pairs), "pooled_effect": pooled["pooled_effect"], "ci_low": pooled["ci_low"], "ci_high": pooled["ci_high"], "i_squared": pooled["i_squared"]})
    return results


def _leave_one_out_results(rows: list[dict[str, Any]], effects: list[StudyEffectEstimate], model: str) -> list[dict[str, Any]]:
    if len(effects) < 3:
        return [{"implemented": True, "message": "leave_one_out_requires_at_least_three_studies", "study_count": len(effects)}]
    results = []
    for index, effect in enumerate(effects):
        remaining = [item for idx, item in enumerate(effects) if idx != index]
        pooled = _pool_effects_v2(remaining, effect_measure=effect.effect_measure, model=model)
        results.append({"omitted_effect_row_id": str(rows[index].get("effect_row_id", "")), "pooled_effect": pooled["pooled_effect"], "ci_low": pooled["ci_low"], "ci_high": pooled["ci_high"]})
    return results


def _publication_bias_results(study_results: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [
        StudyMetaAnalysisResult(
            study_id=str(item.get("study_id", "")),
            record_id=str(item.get("record_id", "")),
            first_author=str(item.get("first_author", "")),
            year=int(item["year"]) if item.get("year") not in ("", None) else None,
            effect=float(item["effect"]),
            ci_lower=float(item["ci_low"]),
            ci_upper=float(item["ci_high"]),
            standard_error=float(item["standard_error"]),
            variance=float(item["variance"]),
            weight=float(item["weight"]),
            transformed_effect=float(item["transformed_effect"]),
            warnings=list(item.get("warnings", [])),
        )
        for item in study_results
    ]
    return {"egger": _egger_test(rows), "funnel_data": [{"effect": row.effect, "standard_error": row.standard_error, "effect_row_id": study_results[index]["effect_row_id"]} for index, row in enumerate(rows)]}


def _egger_test(rows: list[StudyMetaAnalysisResult]) -> dict[str, object]:
    if len(rows) < 3:
        return {"implemented": True, "intercept": None, "slope": None, "p_value": None, "message": "egger_test_requires_at_least_three_studies"}
    precision = [1 / row.standard_error for row in rows if row.standard_error > 0]
    standardized = [row.transformed_effect / row.standard_error for row in rows if row.standard_error > 0]
    if len(precision) < 3:
        return {"implemented": True, "intercept": None, "slope": None, "p_value": None, "message": "egger_test_requires_positive_standard_errors"}
    mean_x = sum(precision) / len(precision)
    mean_y = sum(standardized) / len(standardized)
    ss_xx = sum((x - mean_x) ** 2 for x in precision)
    if ss_xx <= 0:
        return {"implemented": True, "intercept": None, "slope": None, "p_value": None, "message": "egger_test_precision_has_no_variation"}
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(precision, standardized, strict=True)) / ss_xx
    intercept = mean_y - (slope * mean_x)
    return {"implemented": True, "intercept": intercept, "slope": slope, "p_value": None, "study_count": len(precision), "message": "testing_egger_linear_regression"}


def _make_effect(row: dict[str, Any], measure: str, theta: float, variance: float, warnings: list[str]) -> StudyEffectEstimate:
    if variance <= 0:
        raise ValueError(f"non_positive_variance:{row.get('effect_row_id')}")
    se = math.sqrt(variance)
    effect, ci_low, ci_high = report_effect_values(measure, theta, se)
    return StudyEffectEstimate(
        study_id=str(row.get("study_unit_id", "")),
        record_id=str(row.get("record_id", "")),
        first_author=str(row.get("study_unit_label", "")),
        year=None,
        effect_measure=measure,
        effect=effect,
        ci_lower=ci_low,
        ci_upper=ci_high,
        standard_error=se,
        variance=variance,
        transformed_effect=theta,
        adjusted=_adjustment_status(row) == "adjusted",
        warnings=warnings,
    )


def _raw(row: dict[str, Any]) -> dict[str, Any]:
    return dict(row.get("raw_group_data", {})) if isinstance(row.get("raw_group_data"), dict) else {}


def _reported(row: dict[str, Any]) -> dict[str, Any]:
    return dict(row.get("reported_effect_size", {})) if isinstance(row.get("reported_effect_size"), dict) else {}


def _row_effect_measure(row: dict[str, Any], fallback: str) -> str:
    reported = _reported(row)
    return str(reported.get("effect_measure") or fallback or "").upper().replace("FISHER Z", "CORRELATION")


def _adjustment_status(row: dict[str, Any]) -> str:
    value = str(_reported(row).get("adjusted_or_unadjusted", "")).strip().lower()
    if value:
        return value
    return ""


def _needs_zero_cell_correction(row: dict[str, Any], effect_measure: str) -> bool:
    raw = _raw(row)
    if effect_measure.upper() not in {"OR", "RR"}:
        return False
    if not {"group_1_n", "group_1_events", "group_2_n", "group_2_events"} <= set(raw):
        return False
    a = float(raw["group_1_events"])
    b = float(raw["group_1_n"]) - a
    c = float(raw["group_2_events"])
    d = float(raw["group_2_n"]) - c
    return min(a, b, c, d) == 0


def _normalize_model(value: str) -> str:
    text = value.strip().lower().replace("_effects", "").replace("_effect", "")
    return "fixed" if text == "fixed" else "random"


def _chi_square_survival_approx(q_statistic: float, df: int) -> float | None:
    if df <= 0:
        return None
    if q_statistic <= 0:
        return 1.0
    z_value = ((q_statistic / df) ** (1 / 3) - (1 - (2 / (9 * df)))) / math.sqrt(2 / (9 * df))
    return max(0.0, min(1.0, 1 - NormalDist().cdf(z_value)))


def _has_value(value: object) -> bool:
    return value not in ("", None)


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
