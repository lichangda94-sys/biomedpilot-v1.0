from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.models.effect_size_normalization import (
    EFFECT_SIZE_RATIO_MEASURES,
    NORMALIZATION_STATUS_READY,
    NormalizedEffectSizeInput,
)
from app.meta_analysis.models.pairwise_meta_executor import (
    PAIRWISE_META_EXECUTOR_SCHEMA_VERSION,
    PAIRWISE_META_EXECUTOR_VERSION,
    PAIRWISE_MODEL_FIXED_EFFECT,
    PAIRWISE_SUPPORTED_MODELS,
    PairwiseMetaExecutorConfig,
    PairwiseMetaExecutorResult,
    PairwiseStudyResult,
)
from app.meta_analysis.models.result_review import REVIEW_STATE_ACCEPTED_FOR_REPORT
from app.meta_analysis.models.statistical_result_state import (
    STATISTICAL_RESULT_STATE_COMPUTED,
    STATISTICAL_RESULT_STATE_FAILED_VALIDATION,
    STATISTICAL_RESULT_STATE_REPORT_READY,
    STATISTICAL_RESULT_STATE_USER_REVIEWED,
    can_enter_computed_state,
    can_enter_report_ready_state,
)
from app.meta_analysis.services.analysis_plan_service import AnalysisPlanService
from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.effect_size_normalization_service import EffectSizeNormalizationService


class PairwiseMetaExecutorService:
    def __init__(
        self,
        *,
        analysis_plan_service: AnalysisPlanService | None = None,
        normalization_service: EffectSizeNormalizationService | None = None,
        audit_log: MetaAuditLogService | None = None,
    ) -> None:
        self._plan_service = analysis_plan_service or AnalysisPlanService()
        self._normalization_service = normalization_service or EffectSizeNormalizationService()
        self._audit_log = audit_log or MetaAuditLogService()

    def results_dir(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "analysis" / "pairwise_executor"

    def latest_result_path(self, project_dir: Path) -> Path:
        return self.results_dir(project_dir) / "latest_pairwise_meta_result.json"

    def execute(
        self,
        project_dir: Path,
        *,
        config: PairwiseMetaExecutorConfig | None = None,
        actor: str = "reviewer",
    ) -> PairwiseMetaExecutorResult:
        project_dir = project_dir.expanduser().resolve()
        config = config or PairwiseMetaExecutorConfig()
        confirmed_plan = self._plan_service.load_confirmed(project_dir)
        normalized = self._normalization_service.normalize_extraction_rows(project_dir)
        result = self.execute_from_inputs(
            confirmed_plan=confirmed_plan,
            normalized_records=normalized,
            config=config,
            project_name=project_dir.name,
        )
        self.save_result(project_dir, result)
        self._audit_log.record_event(
            project_dir,
            event_type="analysis_run_completed" if result.result_state == STATISTICAL_RESULT_STATE_COMPUTED else "analysis_run_failed_validation",
            project_id=project_dir.name,
            actor=actor,
            target_type="pairwise_meta_executor_result",
            target_id=result.result_id,
            source_path="analysis/analysis_plan_confirmed_v1.json",
            output_path=str(self.latest_result_path(project_dir).relative_to(project_dir)),
            summary="Pairwise fixed-effect executor MVP completed." if result.result_state == STATISTICAL_RESULT_STATE_COMPUTED else "Pairwise fixed-effect executor MVP failed validation.",
            details={
                "result_state": result.result_state,
                "model_used": result.model_used,
                "included_count": len(result.included_studies),
                "excluded_count": len(result.excluded_studies),
                "developer_preview_testing": result.developer_preview_testing,
            },
        )
        return result

    def execute_from_inputs(
        self,
        *,
        confirmed_plan: dict[str, Any] | None,
        normalized_records: list[NormalizedEffectSizeInput],
        config: PairwiseMetaExecutorConfig | None = None,
        project_name: str = "",
    ) -> PairwiseMetaExecutorResult:
        config = config or PairwiseMetaExecutorConfig()
        run_id = f"pairwise-run-{uuid4().hex[:12]}"
        result_id = f"pairwise-result-{uuid4().hex[:12]}"
        now = _now()
        warnings: list[str] = ["developer_preview_testing_only", "fixed_effect_inverse_variance_mvp"]
        validation_errors: list[str] = []
        if not confirmed_plan or str(confirmed_plan.get("plan_state", "")) != "confirmed":
            validation_errors.append("confirmed_analysis_plan_required")
        model = _normalize_model(config.model or str((confirmed_plan or {}).get("confirmed_model") or (confirmed_plan or {}).get("model_preference") or PAIRWISE_MODEL_FIXED_EFFECT))
        if model not in PAIRWISE_SUPPORTED_MODELS:
            validation_errors.append("random_effects_not_supported_in_m12" if "random" in model else "unsupported_pairwise_model")
        plan_effect = _normalize_effect_type(str((confirmed_plan or {}).get("confirmed_effect_measure") or (confirmed_plan or {}).get("effect_measure_type") or ""))
        ready_records, excluded_studies = _split_records(normalized_records, plan_effect=plan_effect)
        effect_types = sorted({record.effect_measure_type for record in ready_records if record.effect_measure_type})
        if len(ready_records) < 2:
            validation_errors.append("at_least_two_ready_normalized_studies_required")
        if any(item.get("reason") == "effect_measure_type_mismatch" for item in excluded_studies):
            validation_errors.append("normalized_effect_type_must_match_confirmed_plan")
        if not effect_types:
            validation_errors.append("effect_measure_type_required")
        elif len(effect_types) > 1:
            validation_errors.append("consistent_effect_measure_type_required")
        elif plan_effect and effect_types[0] != plan_effect:
            validation_errors.append("normalized_effect_type_must_match_confirmed_plan")
        numeric_errors = _numeric_validation_errors(ready_records)
        validation_errors.extend(numeric_errors)
        reproducibility_metadata = _reproducibility_metadata(
            project_name=project_name,
            timestamp=now,
            input_count=len(normalized_records),
            included_count=len(ready_records),
            excluded_count=len(excluded_studies),
            model=model,
            effect_measure_type=effect_types[0] if len(effect_types) == 1 else plan_effect,
        )
        gate = can_enter_computed_state(
            {
                "confirmed_analysis_plan": bool(confirmed_plan and str(confirmed_plan.get("plan_state", "")) == "confirmed"),
                "confirmed_extraction_rows": bool(ready_records),
                "effect_measure_consistent": bool(effect_types and len(effect_types) == 1 and (not plan_effect or effect_types[0] == plan_effect)),
                "numeric_fields_valid": not numeric_errors,
                "enough_included_studies": len(ready_records) >= 2,
                "reproducibility_metadata_present": bool(reproducibility_metadata),
            },
            warnings=warnings,
        )
        if not gate.allowed:
            validation_errors.extend(list(gate.errors))
        validation_errors = _dedupe(validation_errors)
        if validation_errors:
            return PairwiseMetaExecutorResult(
                result_state=STATISTICAL_RESULT_STATE_FAILED_VALIDATION,
                result_id=result_id,
                analysis_run_id=run_id,
                model_used=model,
                effect_measure_type=effect_types[0] if len(effect_types) == 1 else plan_effect,
                effect_scale=_effect_scale(effect_types[0] if len(effect_types) == 1 else plan_effect),
                included_studies=[],
                excluded_studies=excluded_studies,
                warnings=_dedupe([*warnings, *[warning for record in normalized_records for warning in record.warnings]]),
                validation_errors=validation_errors,
                reproducibility_metadata=reproducibility_metadata,
                result_manifest=_result_manifest(
                    result_id=result_id,
                    run_id=run_id,
                    timestamp=now,
                    state=STATISTICAL_RESULT_STATE_FAILED_VALIDATION,
                    model=model,
                    effect_measure_type=effect_types[0] if len(effect_types) == 1 else plan_effect,
                    included_count=0,
                    excluded_count=len(excluded_studies),
                    validation_errors=validation_errors,
                    warnings=warnings,
                ),
            )
        effect_measure = effect_types[0]
        study_results = [_study_result(record, effect_measure=effect_measure) for record in ready_records]
        pooled = _fixed_effect_pool(study_results)
        heterogeneity = _heterogeneity_summary(study_results, pooled["pooled_effect"])
        back_transformed = _back_transform_ratio(effect_measure, pooled["pooled_effect"], pooled["ci_lower"], pooled["ci_upper"])
        return PairwiseMetaExecutorResult(
            result_state=STATISTICAL_RESULT_STATE_COMPUTED,
            result_id=result_id,
            analysis_run_id=run_id,
            model_used=model,
            effect_measure_type=effect_measure,
            effect_scale=_effect_scale(effect_measure),
            included_studies=[item.to_dict() for item in study_results],
            excluded_studies=excluded_studies,
            pooled_effect=pooled["pooled_effect"],
            pooled_ci_lower=pooled["ci_lower"],
            pooled_ci_upper=pooled["ci_upper"],
            pooled_standard_error=pooled["standard_error"],
            z_value=pooled["z_value"],
            p_value=pooled["p_value"],
            back_transformed_effect=back_transformed.get("effect"),
            back_transformed_ci_lower=back_transformed.get("ci_lower"),
            back_transformed_ci_upper=back_transformed.get("ci_upper"),
            heterogeneity_summary=heterogeneity,
            warnings=warnings,
            validation_errors=[],
            reproducibility_metadata=reproducibility_metadata,
            result_manifest=_result_manifest(
                result_id=result_id,
                run_id=run_id,
                timestamp=now,
                state=STATISTICAL_RESULT_STATE_COMPUTED,
                model=model,
                effect_measure_type=effect_measure,
                included_count=len(study_results),
                excluded_count=len(excluded_studies),
                validation_errors=[],
                warnings=warnings,
            ),
            formal_computed=True,
            testing_level=False,
            user_reviewed=False,
            report_ready=False,
        )

    def mark_user_reviewed(self, result: PairwiseMetaExecutorResult | dict[str, Any], *, actor: str = "reviewer") -> PairwiseMetaExecutorResult:
        payload = result.to_dict() if isinstance(result, PairwiseMetaExecutorResult) else dict(result)
        if str(payload.get("result_state", "")) != STATISTICAL_RESULT_STATE_COMPUTED:
            raise ValueError("computed_result_required_for_user_review")
        if not actor.strip():
            raise ValueError("actor_required_for_user_review")
        if payload.get("warnings") and not bool(payload.get("review_warnings_acknowledged", False)):
            raise ValueError("warnings_must_be_acknowledged")
        if str(payload.get("review_decision", "")) != REVIEW_STATE_ACCEPTED_FOR_REPORT:
            raise ValueError("accepted_for_report_review_required")
        if _critical_warnings(payload):
            raise ValueError("critical_warnings_block_report_ready")
        payload["result_state"] = STATISTICAL_RESULT_STATE_USER_REVIEWED
        payload["user_reviewed"] = True
        payload["report_ready"] = False
        payload.setdefault("warnings", []).append("user_review_required_before_report_ready")
        return PairwiseMetaExecutorResult(**_known_result_fields(payload))

    def mark_report_ready(self, result: PairwiseMetaExecutorResult | dict[str, Any], *, actor: str = "reviewer") -> PairwiseMetaExecutorResult:
        payload = result.to_dict() if isinstance(result, PairwiseMetaExecutorResult) else dict(result)
        if not actor.strip():
            raise ValueError("actor_required_for_report_ready")
        if str(payload.get("review_decision", "")) != REVIEW_STATE_ACCEPTED_FOR_REPORT:
            raise ValueError("accepted_for_report_review_required")
        if not bool(payload.get("report_ready_requested", False)):
            raise ValueError("report_ready_request_required")
        if payload.get("validation_errors"):
            raise ValueError("validation_errors_must_be_resolved")
        if _critical_warnings(payload):
            raise ValueError("critical_warnings_block_report_ready")
        gate = can_enter_report_ready_state(payload)
        if not gate.allowed:
            raise ValueError(";".join(gate.errors))
        payload["result_state"] = STATISTICAL_RESULT_STATE_REPORT_READY
        payload["user_reviewed"] = True
        payload["report_ready"] = True
        payload["report_ready_granted"] = True
        return PairwiseMetaExecutorResult(**_known_result_fields(payload))

    def save_result(self, project_dir: Path, result: PairwiseMetaExecutorResult) -> Path:
        path = self.latest_result_path(project_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load_latest_result(self, project_dir: Path) -> PairwiseMetaExecutorResult | None:
        path = self.latest_result_path(project_dir)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None
        return PairwiseMetaExecutorResult(**_known_result_fields(payload))


def _split_records(records: list[NormalizedEffectSizeInput], *, plan_effect: str) -> tuple[list[NormalizedEffectSizeInput], list[dict[str, Any]]]:
    ready: list[NormalizedEffectSizeInput] = []
    excluded: list[dict[str, Any]] = []
    for record in records:
        reason = ""
        if record.normalization_status != NORMALIZATION_STATUS_READY:
            reason = f"normalization_status:{record.normalization_status}"
        elif record.source_state != "confirmed":
            reason = "source_row_not_confirmed"
        elif plan_effect and record.effect_measure_type != plan_effect:
            reason = "effect_measure_type_mismatch"
        if reason:
            excluded.append({"study_label": record.study_label, "effect_measure_type": record.effect_measure_type, "reason": reason, "warnings": list(record.warnings)})
        else:
            ready.append(record)
    return ready, excluded


def _study_result(record: NormalizedEffectSizeInput, *, effect_measure: str) -> PairwiseStudyResult:
    estimate = record.log_estimate if effect_measure in EFFECT_SIZE_RATIO_MEASURES else record.estimate
    if estimate is None or record.standard_error is None or record.variance is None:
        raise ValueError("ready_normalized_record_missing_numeric_fields")
    return PairwiseStudyResult(
        study_label=record.study_label,
        effect_measure_type=record.effect_measure_type,
        estimate=float(estimate),
        standard_error=float(record.standard_error),
        variance=float(record.variance),
        weight=1.0 / float(record.variance),
        effect_scale=_effect_scale(effect_measure),
        warnings=list(record.warnings),
    )


def _fixed_effect_pool(studies: list[PairwiseStudyResult]) -> dict[str, float]:
    weight_sum = sum(study.weight for study in studies)
    pooled = sum(study.weight * study.estimate for study in studies) / weight_sum
    se = math.sqrt(1.0 / weight_sum)
    ci_lower = pooled - 1.96 * se
    ci_upper = pooled + 1.96 * se
    z_value = pooled / se if se > 0 else 0.0
    p_value = math.erfc(abs(z_value) / math.sqrt(2.0))
    return {
        "pooled_effect": pooled,
        "standard_error": se,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "z_value": z_value,
        "p_value": p_value,
    }


def _heterogeneity_summary(studies: list[PairwiseStudyResult], pooled_effect: float) -> dict[str, Any]:
    q = sum(study.weight * ((study.estimate - pooled_effect) ** 2) for study in studies)
    df = max(len(studies) - 1, 0)
    i2 = max(0.0, ((q - df) / q) * 100.0) if q > 0 else 0.0
    return {
        "q": q,
        "df": df,
        "i_squared": i2,
        "testing_level_diagnostic": True,
        "notice": "Developer Preview heterogeneity diagnostic; external validation pending.",
    }


def _numeric_validation_errors(records: list[NormalizedEffectSizeInput]) -> list[str]:
    errors: list[str] = []
    for record in records:
        values = [record.standard_error, record.variance]
        estimate = record.log_estimate if record.effect_measure_type in EFFECT_SIZE_RATIO_MEASURES else record.estimate
        values.append(estimate)
        if any(value is None or not math.isfinite(float(value)) for value in values):
            errors.append("finite_numeric_estimate_se_variance_required")
        if record.standard_error is not None and float(record.standard_error) <= 0:
            errors.append("positive_standard_error_required")
        if record.variance is not None and float(record.variance) <= 0:
            errors.append("positive_variance_required")
    return _dedupe(errors)


def _normalize_model(model: str) -> str:
    value = str(model or PAIRWISE_MODEL_FIXED_EFFECT).strip().lower().replace("-", "_")
    aliases = {
        "fixed": PAIRWISE_MODEL_FIXED_EFFECT,
        "fixed_effects": PAIRWISE_MODEL_FIXED_EFFECT,
        "fixed_effect": PAIRWISE_MODEL_FIXED_EFFECT,
        "random": "random_effect",
        "random_effects": "random_effect",
        "random_effect": "random_effect",
    }
    return aliases.get(value, value)


def _normalize_effect_type(value: str) -> str:
    text = str(value or "").strip()
    upper = text.upper()
    if upper in {"OR", "RR", "HR", "MD", "SMD"}:
        return upper
    lower = text.lower()
    aliases = {"prevalence": "proportion", "diagnostic": "diagnostic_accuracy"}
    return aliases.get(lower, text)


def _effect_scale(effect_measure: str) -> str:
    return "log" if effect_measure in EFFECT_SIZE_RATIO_MEASURES else "original"


def _back_transform_ratio(effect_measure: str, pooled: float, ci_lower: float, ci_upper: float) -> dict[str, float]:
    if effect_measure not in EFFECT_SIZE_RATIO_MEASURES:
        return {}
    return {"effect": math.exp(pooled), "ci_lower": math.exp(ci_lower), "ci_upper": math.exp(ci_upper)}


def _reproducibility_metadata(
    *,
    project_name: str,
    timestamp: str,
    input_count: int,
    included_count: int,
    excluded_count: int,
    model: str,
    effect_measure_type: str,
) -> dict[str, Any]:
    return {
        "executor_schema_version": PAIRWISE_META_EXECUTOR_SCHEMA_VERSION,
        "executor_version": PAIRWISE_META_EXECUTOR_VERSION,
        "created_at": timestamp,
        "project_label": project_name,
        "input_record_count": input_count,
        "included_count": included_count,
        "excluded_count": excluded_count,
        "model_used": model,
        "effect_measure_type": effect_measure_type,
        "developer_preview_testing": True,
    }


def _result_manifest(
    *,
    result_id: str,
    run_id: str,
    timestamp: str,
    state: str,
    model: str,
    effect_measure_type: str,
    included_count: int,
    excluded_count: int,
    validation_errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "meta_pairwise_executor_manifest.m12",
        "result_id": result_id,
        "analysis_run_id": run_id,
        "result_state": state,
        "created_at": timestamp,
        "model_used": model,
        "effect_measure_type": effect_measure_type,
        "included_count": included_count,
        "excluded_count": excluded_count,
        "validation_errors": list(validation_errors),
        "warnings": list(warnings),
        "developer_preview_testing": True,
    }


def _known_result_fields(payload: dict[str, Any]) -> dict[str, Any]:
    names = set(PairwiseMetaExecutorResult.__dataclass_fields__.keys())
    return {name: payload[name] for name in names if name in payload}


def _critical_warnings(payload: dict[str, Any]) -> list[str]:
    warnings = payload.get("warnings", [])
    if not isinstance(warnings, list):
        return []
    result: list[str] = []
    for warning in warnings:
        text = str(warning).lower()
        if text.startswith("critical") or "critical_warning" in text or "unresolved_critical" in text:
            result.append(str(warning))
    return result


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result
