from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.meta_analysis.extraction.schema_registry import get_extraction_schema_profile
from app.meta_analysis.services.audit_log_service import MetaAuditLogService


@dataclass(frozen=True)
class AnalysisProfileConfig:
    config_id: str
    project_id: str
    profile_type: str
    review_question: str
    pico_mode: str
    population: str = ""
    intervention_or_exposure: str = ""
    comparator: str = ""
    outcomes: tuple[str, ...] = ()
    study_design: str = ""
    extraction_schema_profile: str = ""
    effect_measures: tuple[str, ...] = ()
    analysis_plan_defaults: dict[str, str] = field(default_factory=dict)
    validation_warnings: tuple[str, ...] = ()
    validation_errors: tuple[str, ...] = ()
    created_at: str = ""
    updated_at: str = ""


class AnalysisProfileConfigService:
    def __init__(self, *, audit_log: MetaAuditLogService | None = None) -> None:
        self._audit_log = audit_log or MetaAuditLogService()

    def build_config(
        self,
        project_dir: Path,
        *,
        profile_type: str,
        review_question: str,
        pico_mode: str = "PICO",
        population: str = "",
        intervention_or_exposure: str = "",
        comparator: str = "",
        outcomes: tuple[str, ...] | list[str] = (),
        study_design: str = "",
        analysis_model: str = "random",
        zero_event_correction: str = "continuity_0.5",
    ) -> AnalysisProfileConfig:
        project_dir = project_dir.expanduser().resolve()
        schema = get_extraction_schema_profile(profile_type)
        warnings: list[str] = ["developer_preview_profile_config"]
        errors: list[str] = []
        if schema is None:
            errors.append("profile_type_not_registered")
            effect_measures: tuple[str, ...] = ()
        else:
            effect_measures = tuple(schema.supported_effect_measures)
            if not effect_measures and schema.metadata.get("status") == "not_implemented":
                errors.append("profile_type_not_implemented")
        if not review_question.strip():
            errors.append("review_question_missing")
        if not tuple(item for item in outcomes if str(item).strip()):
            warnings.append("outcome_blocks_empty")
        now = _now()
        return AnalysisProfileConfig(
            config_id=f"apcfg-{uuid4().hex[:12]}",
            project_id=project_dir.name,
            profile_type=profile_type,
            review_question=review_question,
            pico_mode=pico_mode.upper() or "PICO",
            population=population,
            intervention_or_exposure=intervention_or_exposure,
            comparator=comparator,
            outcomes=tuple(str(item).strip() for item in outcomes if str(item).strip()),
            study_design=study_design,
            extraction_schema_profile=schema.profile_type if schema is not None else "",
            effect_measures=effect_measures,
            analysis_plan_defaults={
                "model": analysis_model.strip().lower() or "random",
                "zero_event_correction": zero_event_correction,
            },
            validation_warnings=tuple(_dedupe(warnings)),
            validation_errors=tuple(_dedupe(errors)),
            created_at=now,
            updated_at=now,
        )

    def save_config(self, project_dir: Path, config: AnalysisProfileConfig) -> Path:
        project_dir = project_dir.expanduser().resolve()
        path = project_dir / "profiles" / "analysis_profile_configs.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        configs = [item for item in self.list_configs(project_dir) if item.config_id != config.config_id]
        configs.append(config)
        payload = {
            "project_id": project_dir.name,
            "schema_version": "meta_analysis_profile_configs.v1",
            "software_status": "developer_preview_testing",
            "configs": [asdict(item) for item in configs],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._audit_log.record_event(
            project_dir,
            event_type="analysis_profile_config_saved",
            project_id=config.project_id,
            target_type="analysis_profile_config",
            target_id=config.config_id,
            output_path=str(path),
            summary="Analysis profile config snapshot saved.",
            details={"profile_type": config.profile_type, "pico_mode": config.pico_mode, "errors": list(config.validation_errors)},
        )
        return path

    def list_configs(self, project_dir: Path) -> list[AnalysisProfileConfig]:
        path = project_dir.expanduser().resolve() / "profiles" / "analysis_profile_configs.json"
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        configs: list[AnalysisProfileConfig] = []
        for item in payload.get("configs", []):
            configs.append(
                AnalysisProfileConfig(
                    config_id=str(item.get("config_id", "")),
                    project_id=str(item.get("project_id", "")),
                    profile_type=str(item.get("profile_type", "")),
                    review_question=str(item.get("review_question", "")),
                    pico_mode=str(item.get("pico_mode", "PICO")),
                    population=str(item.get("population", "")),
                    intervention_or_exposure=str(item.get("intervention_or_exposure", "")),
                    comparator=str(item.get("comparator", "")),
                    outcomes=tuple(str(value) for value in item.get("outcomes", [])),
                    study_design=str(item.get("study_design", "")),
                    extraction_schema_profile=str(item.get("extraction_schema_profile", "")),
                    effect_measures=tuple(str(value) for value in item.get("effect_measures", [])),
                    analysis_plan_defaults={str(key): str(value) for key, value in dict(item.get("analysis_plan_defaults", {})).items()},
                    validation_warnings=tuple(str(value) for value in item.get("validation_warnings", [])),
                    validation_errors=tuple(str(value) for value in item.get("validation_errors", [])),
                    created_at=str(item.get("created_at", "")),
                    updated_at=str(item.get("updated_at", "")),
                )
            )
        return configs


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result

