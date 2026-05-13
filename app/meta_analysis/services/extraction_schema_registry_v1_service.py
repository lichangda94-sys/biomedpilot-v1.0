from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.meta_analysis.services.audit_log_service import MetaAuditLogService
from app.meta_analysis.services.research_governance_service import MetaResearchGovernanceService


EXTRACTION_SCHEMA_REGISTRY_V1_SCHEMA_VERSION = "meta_extraction_schema_registry.v1"
EXTRACTION_SCHEMA_V1_SCHEMA_VERSION = "meta_extraction_schema.v1"
EXTRACTION_SCHEMA_SELECTION_SCHEMA_VERSION = "meta_extraction_schema_selection.v1"

BINARY_OUTCOME_META = "binary_outcome_meta"
CONTINUOUS_OUTCOME_META = "continuous_outcome_meta"
SURVIVAL_OUTCOME_META = "survival_outcome_meta"
PREVALENCE_INCIDENCE_META_V1 = "prevalence_incidence_meta"
DIAGNOSTIC_ACCURACY_META_V1 = "diagnostic_accuracy_meta"
EXPOSURE_DISEASE_RISK_META_V1 = "exposure_disease_risk_meta"
BIOMARKER_EXPRESSION_DIFFERENCE_META = "biomarker_expression_difference_meta"
CORRELATION_META_V1 = "correlation_meta"
PROGNOSTIC_FACTOR_META_V1 = "prognostic_factor_meta"
DOSE_RESPONSE_META = "dose_response_meta"


@dataclass(frozen=True)
class ExtractionSchemaV1:
    meta_type: str
    display_name: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    validation_rules: tuple[str, ...]
    effect_size_mapping: dict[str, Any]
    analysis_defaults: dict[str, Any]
    quality_tool_recommendation: tuple[str, ...]
    report_template_mapping: dict[str, Any]
    coming_soon: bool = False
    notes: str = ""
    schema_version: str = EXTRACTION_SCHEMA_V1_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["required_fields"] = list(self.required_fields)
        payload["optional_fields"] = list(self.optional_fields)
        payload["validation_rules"] = list(self.validation_rules)
        payload["quality_tool_recommendation"] = list(self.quality_tool_recommendation)
        return payload


@dataclass(frozen=True)
class ExtractionSchemaRegistryV1:
    project_id: str
    schemas: tuple[ExtractionSchemaV1, ...]
    created_at: str
    updated_at: str
    schema_version: str = EXTRACTION_SCHEMA_REGISTRY_V1_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "schema_count": len(self.schemas),
            "schemas": [schema.to_dict() for schema in self.schemas],
            "safety_note": "Extraction schemas generate table templates and validation rules only; they do not write final extracted values.",
        }


class ExtractionSchemaRegistryV1Service:
    def __init__(
        self,
        *,
        audit_log: MetaAuditLogService | None = None,
        research_governance: MetaResearchGovernanceService | None = None,
    ) -> None:
        self._audit_log = audit_log or MetaAuditLogService()
        self._governance = research_governance or MetaResearchGovernanceService(audit_log=self._audit_log)

    def registry_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "extraction" / "schema_registry_v1.json"

    def selection_path(self, project_dir: Path) -> Path:
        return project_dir.expanduser().resolve() / "extraction" / "selected_extraction_schema_v1.json"

    def default_schemas(self) -> tuple[ExtractionSchemaV1, ...]:
        return DEFAULT_SCHEMAS

    def save_default_registry(self, project_dir: Path, *, project_id: str | None = None) -> ExtractionSchemaRegistryV1:
        project_dir = project_dir.expanduser().resolve()
        now = _now()
        registry = ExtractionSchemaRegistryV1(project_id=project_id or project_dir.name, schemas=self.default_schemas(), created_at=now, updated_at=now)
        _write_json(self.registry_path(project_dir), registry.to_dict())
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=registry.project_id,
            target_type="extraction_schema_registry_v1",
            target_id="schema_registry_v1",
            output_path=str(self.registry_path(project_dir).relative_to(project_dir)),
            summary="Extraction schema registry v1 saved.",
            details={"schema_count": len(registry.schemas), "writes_final_extraction": False},
        )
        self._governance.record_draft_created(
            project_dir,
            project_id=registry.project_id,
            target_type="extraction_schema_registry",
            target_id="schema_registry_v1",
            after={"schema_count": len(registry.schemas), "schema_version": registry.schema_version},
            metadata={"writes_final_extraction": False},
        )
        return registry

    def load_registry(self, project_dir: Path) -> ExtractionSchemaRegistryV1:
        payload = _load_json(self.registry_path(project_dir))
        if not payload:
            return ExtractionSchemaRegistryV1(project_id=project_dir.expanduser().resolve().name, schemas=self.default_schemas(), created_at="", updated_at="")
        return _registry_from_payload(payload)

    def get_schema(self, project_dir: Path, meta_type: str) -> ExtractionSchemaV1 | None:
        normalized = _normalize_meta_type(meta_type)
        for schema in self.load_registry(project_dir).schemas:
            if schema.meta_type == normalized:
                return schema
        return None

    def build_form_template(self, project_dir: Path, meta_type: str) -> dict[str, Any]:
        schema = self.get_schema(project_dir, meta_type)
        if schema is None:
            raise ValueError(f"unsupported_extraction_schema_meta_type:{meta_type}")
        return {
            "schema_version": "meta_extraction_form_template.v1",
            "meta_type": schema.meta_type,
            "display_name": schema.display_name,
            "required_fields": list(schema.required_fields),
            "optional_fields": list(schema.optional_fields),
            "field_order": [*schema.required_fields, *schema.optional_fields],
            "validation_rules": list(schema.validation_rules),
            "effect_size_mapping": schema.effect_size_mapping,
            "analysis_defaults": schema.analysis_defaults,
            "quality_tool_recommendation": list(schema.quality_tool_recommendation),
            "report_template_mapping": schema.report_template_mapping,
            "coming_soon": schema.coming_soon,
            "safety_note": "Template fields require manual reviewer entry and confirmation before analysis.",
        }

    def save_schema_selection(
        self,
        project_dir: Path,
        *,
        meta_type: str,
        actor: str = "system",
        confirm: bool = False,
    ) -> dict[str, Any]:
        project_dir = project_dir.expanduser().resolve()
        schema = self.get_schema(project_dir, meta_type)
        if schema is None:
            raise ValueError(f"unsupported_extraction_schema_meta_type:{meta_type}")
        payload = {
            "schema_version": EXTRACTION_SCHEMA_SELECTION_SCHEMA_VERSION,
            "selection_id": f"exschema-{uuid4().hex[:12]}",
            "project_id": project_dir.name,
            "selected_meta_type": schema.meta_type,
            "selected_display_name": schema.display_name,
            "selected_at": _now(),
            "selected_by": actor,
            "status": "confirmed" if confirm else "draft_needs_review",
            "form_template": self.build_form_template(project_dir, schema.meta_type),
            "writes_final_extraction": False,
            "writes_analysis_input": False,
        }
        _write_json(self.selection_path(project_dir), payload)
        self._audit_log.record_event(
            project_dir,
            event_type="record_saved",
            project_id=project_dir.name,
            actor=actor,
            target_type="extraction_schema_selection",
            target_id=payload["selection_id"],
            output_path=str(self.selection_path(project_dir).relative_to(project_dir)),
            summary=f"Extraction schema selected: {schema.meta_type}.",
            details={"status": payload["status"], "writes_final_extraction": False},
        )
        if confirm:
            self._governance.record_user_confirmation(
                project_dir,
                project_id=project_dir.name,
                action="confirm",
                actor=actor,
                target_type="extraction_schema_selection",
                target_id=payload["selection_id"],
                before={},
                after=payload,
                metadata={"meta_type": schema.meta_type, "writes_final_extraction": False},
            )
        else:
            self._governance.record_draft_created(
                project_dir,
                project_id=project_dir.name,
                actor=actor,
                target_type="extraction_schema_selection",
                target_id=payload["selection_id"],
                after=payload,
                metadata={"meta_type": schema.meta_type, "writes_final_extraction": False},
            )
        return payload


COMMON_STUDY_FIELDS = ("study_id", "record_id", "first_author", "year", "study_design", "population", "sample_size")
SOURCE_FIELDS = ("source_page", "source_table", "source_sentence", "reviewer_notes")


DEFAULT_SCHEMAS = (
    ExtractionSchemaV1(
        meta_type=BINARY_OUTCOME_META,
        display_name="二分类结局 Meta",
        required_fields=(*COMMON_STUDY_FIELDS, "effect_measure", "experimental_events", "experimental_total", "control_events", "control_total"),
        optional_fields=("outcome_name", "timepoint", "subgroup", *SOURCE_FIELDS),
        validation_rules=("events_cannot_exceed_total", "totals_must_be_positive", "effect_measure_must_be_or_rr_rd"),
        effect_size_mapping={"supported": ("OR", "RR", "RD"), "input_type": "2x2_counts"},
        analysis_defaults={"model": "random_effects", "continuity_correction": 0.5, "zero_cell_handling": "add_half"},
        quality_tool_recommendation=("ROB2", "ROBINS-I", "Newcastle-Ottawa Scale"),
        report_template_mapping={"methods": "binary_outcome_methods", "results": "binary_forest_summary"},
    ),
    ExtractionSchemaV1(
        meta_type=CONTINUOUS_OUTCOME_META,
        display_name="连续结局 Meta",
        required_fields=(*COMMON_STUDY_FIELDS, "effect_measure", "experimental_mean", "experimental_sd", "experimental_total", "control_mean", "control_sd", "control_total"),
        optional_fields=("outcome_name", "unit", "timepoint", "subgroup", *SOURCE_FIELDS),
        validation_rules=("sd_must_be_non_negative", "totals_must_be_positive", "effect_measure_must_be_md_smd_wmd"),
        effect_size_mapping={"supported": ("MD", "SMD", "WMD"), "input_type": "mean_sd_n"},
        analysis_defaults={"model": "random_effects", "smd_method": "hedges_g"},
        quality_tool_recommendation=("ROB2", "ROBINS-I", "Newcastle-Ottawa Scale"),
        report_template_mapping={"methods": "continuous_outcome_methods", "results": "continuous_forest_summary"},
    ),
    ExtractionSchemaV1(
        meta_type=SURVIVAL_OUTCOME_META,
        display_name="生存结局 Meta",
        required_fields=(*COMMON_STUDY_FIELDS, "outcome_name", "hr", "ci_lower", "ci_upper"),
        optional_fields=("log_hr", "standard_error", "adjusted", "covariates", "follow_up", *SOURCE_FIELDS),
        validation_rules=("hr_must_be_positive", "ci_lower_cannot_exceed_ci_upper", "derive_log_hr_and_se_when_possible"),
        effect_size_mapping={"supported": ("HR",), "input_type": "hr_95ci_or_loghr_se"},
        analysis_defaults={"model": "random_effects", "scale": "log"},
        quality_tool_recommendation=("Newcastle-Ottawa Scale", "ROBINS-I"),
        report_template_mapping={"methods": "survival_methods", "results": "survival_forest_summary"},
    ),
    ExtractionSchemaV1(
        meta_type=PREVALENCE_INCIDENCE_META_V1,
        display_name="患病率 / 发生率 Meta",
        required_fields=(*COMMON_STUDY_FIELDS, "outcome_name", "events", "total"),
        optional_fields=("person_time", "case_definition", "sampling_frame", "subgroup", *SOURCE_FIELDS),
        validation_rules=("events_cannot_exceed_total", "total_must_be_positive", "person_time_must_be_positive_when_present"),
        effect_size_mapping={"supported": ("prevalence", "incidence"), "input_type": "single_arm_events_total"},
        analysis_defaults={"model": "random_effects", "transformation": "logit"},
        quality_tool_recommendation=("JBI prevalence checklist", "AHRQ cross-sectional"),
        report_template_mapping={"methods": "prevalence_methods", "results": "prevalence_forest_summary"},
    ),
    ExtractionSchemaV1(
        meta_type=DIAGNOSTIC_ACCURACY_META_V1,
        display_name="诊断准确性 Meta",
        required_fields=(*COMMON_STUDY_FIELDS, "index_test", "reference_standard", "tp", "fp", "fn", "tn"),
        optional_fields=("cutoff", "sensitivity", "specificity", "auc", *SOURCE_FIELDS),
        validation_rules=("diagnostic_counts_must_be_non_negative", "sensitivity_denominator_must_be_positive", "specificity_denominator_must_be_positive"),
        effect_size_mapping={"supported": ("sensitivity", "specificity", "PLR", "NLR", "DOR"), "input_type": "diagnostic_2x2"},
        analysis_defaults={"model": "diagnostic_basic_2x2", "advanced_model": "bivariate_hsroc_not_implemented"},
        quality_tool_recommendation=("QUADAS-2",),
        report_template_mapping={"methods": "diagnostic_methods", "results": "diagnostic_summary"},
    ),
    ExtractionSchemaV1(
        meta_type=EXPOSURE_DISEASE_RISK_META_V1,
        display_name="暴露-疾病风险 Meta",
        required_fields=(*COMMON_STUDY_FIELDS, "exposure", "outcome_name", "effect_measure", "effect", "ci_lower", "ci_upper"),
        optional_fields=("adjusted", "covariates", "exposure_definition", "comparison_group", *SOURCE_FIELDS),
        validation_rules=("ratio_effect_must_be_positive", "ci_lower_cannot_exceed_ci_upper", "effect_measure_must_be_or_rr_hr"),
        effect_size_mapping={"supported": ("OR", "RR", "HR"), "input_type": "reported_association_effect"},
        analysis_defaults={"model": "random_effects", "scale": "log"},
        quality_tool_recommendation=("Newcastle-Ottawa Scale", "ROBINS-I"),
        report_template_mapping={"methods": "exposure_risk_methods", "results": "risk_forest_summary"},
    ),
    ExtractionSchemaV1(
        meta_type=BIOMARKER_EXPRESSION_DIFFERENCE_META,
        display_name="生物标志物表达差异 Meta",
        required_fields=(*COMMON_STUDY_FIELDS, "biomarker", "case_mean", "case_sd", "case_n", "control_mean", "control_sd", "control_n"),
        optional_fields=("platform", "unit", "tissue", "cutoff", *SOURCE_FIELDS),
        validation_rules=("sd_must_be_non_negative", "sample_sizes_must_be_positive", "biomarker_required"),
        effect_size_mapping={"supported": ("SMD", "MD"), "input_type": "mean_sd_n"},
        analysis_defaults={"model": "random_effects", "smd_method": "hedges_g"},
        quality_tool_recommendation=("Newcastle-Ottawa Scale", "AHRQ cross-sectional"),
        report_template_mapping={"methods": "biomarker_difference_methods", "results": "biomarker_forest_summary"},
    ),
    ExtractionSchemaV1(
        meta_type=CORRELATION_META_V1,
        display_name="相关性 Meta",
        required_fields=(*COMMON_STUDY_FIELDS, "variable_x", "variable_y", "r", "sample_size"),
        optional_fields=("correlation_type", "adjusted", "covariates", *SOURCE_FIELDS),
        validation_rules=("r_must_be_between_minus_one_and_one", "sample_size_must_exceed_three"),
        effect_size_mapping={"supported": ("Fisher z", "r"), "input_type": "correlation_r_n"},
        analysis_defaults={"model": "random_effects", "transformation": "fisher_z"},
        quality_tool_recommendation=("Newcastle-Ottawa Scale", "JBI checklist"),
        report_template_mapping={"methods": "correlation_methods", "results": "correlation_forest_summary"},
    ),
    ExtractionSchemaV1(
        meta_type=PROGNOSTIC_FACTOR_META_V1,
        display_name="预后因素 Meta",
        required_fields=(*COMMON_STUDY_FIELDS, "prognostic_factor", "outcome_name", "effect_measure", "effect", "ci_lower", "ci_upper"),
        optional_fields=("adjusted", "covariates", "follow_up", *SOURCE_FIELDS),
        validation_rules=("ratio_effect_must_be_positive", "ci_lower_cannot_exceed_ci_upper", "effect_measure_must_be_hr_or"),
        effect_size_mapping={"supported": ("HR", "OR"), "input_type": "reported_prognostic_effect"},
        analysis_defaults={"model": "random_effects", "scale": "log"},
        quality_tool_recommendation=("Newcastle-Ottawa Scale", "ROBINS-I"),
        report_template_mapping={"methods": "prognostic_methods", "results": "prognostic_forest_summary"},
    ),
    ExtractionSchemaV1(
        meta_type=DOSE_RESPONSE_META,
        display_name="剂量反应 Meta",
        required_fields=(*COMMON_STUDY_FIELDS, "dose", "cases", "non_cases", "person_years"),
        optional_fields=("dose_unit", "reference_dose", "effect", "ci_lower", "ci_upper", "trend_p_value", *SOURCE_FIELDS),
        validation_rules=("dose_required", "counts_must_be_non_negative", "person_years_must_be_positive_when_present"),
        effect_size_mapping={"supported": ("dose_response_slope", "OR", "RR"), "input_type": "dose_cases_noncases_personyears"},
        analysis_defaults={"model": "dose_response_placeholder", "status": "testing_schema_only"},
        quality_tool_recommendation=("Newcastle-Ottawa Scale", "ROBINS-I"),
        report_template_mapping={"methods": "dose_response_methods", "results": "dose_response_table"},
    ),
)


META_TYPE_ALIASES = {
    "treatment_comparative_meta": BINARY_OUTCOME_META,
    "exposure_disease_risk_meta": EXPOSURE_DISEASE_RISK_META_V1,
    "diagnostic_accuracy_meta": DIAGNOSTIC_ACCURACY_META_V1,
    "prognostic_factor_meta": PROGNOSTIC_FACTOR_META_V1,
    "prevalence_incidence_meta": PREVALENCE_INCIDENCE_META_V1,
    "biomarker_expression_difference_meta": BIOMARKER_EXPRESSION_DIFFERENCE_META,
    "correlation_meta": CORRELATION_META_V1,
    "survival_outcome_meta": SURVIVAL_OUTCOME_META,
    "dose_response_meta": DOSE_RESPONSE_META,
    "continuous_outcome_meta": CONTINUOUS_OUTCOME_META,
    "binary_outcome_meta": BINARY_OUTCOME_META,
}


def _normalize_meta_type(meta_type: str) -> str:
    return META_TYPE_ALIASES.get(meta_type.strip(), meta_type.strip())


def _registry_from_payload(payload: dict[str, Any]) -> ExtractionSchemaRegistryV1:
    return ExtractionSchemaRegistryV1(
        project_id=str(payload.get("project_id", "")),
        schemas=tuple(_schema_from_payload(item) for item in payload.get("schemas", []) if isinstance(item, dict)),
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        schema_version=str(payload.get("schema_version", EXTRACTION_SCHEMA_REGISTRY_V1_SCHEMA_VERSION)),
    )


def _schema_from_payload(payload: dict[str, Any]) -> ExtractionSchemaV1:
    return ExtractionSchemaV1(
        meta_type=str(payload.get("meta_type", "")),
        display_name=str(payload.get("display_name", "")),
        required_fields=tuple(str(item) for item in payload.get("required_fields", []) if str(item)),
        optional_fields=tuple(str(item) for item in payload.get("optional_fields", []) if str(item)),
        validation_rules=tuple(str(item) for item in payload.get("validation_rules", []) if str(item)),
        effect_size_mapping=dict(payload.get("effect_size_mapping", {})),
        analysis_defaults=dict(payload.get("analysis_defaults", {})),
        quality_tool_recommendation=tuple(str(item) for item in payload.get("quality_tool_recommendation", []) if str(item)),
        report_template_mapping=dict(payload.get("report_template_mapping", {})),
        coming_soon=bool(payload.get("coming_soon", False)),
        notes=str(payload.get("notes", "")),
        schema_version=str(payload.get("schema_version", EXTRACTION_SCHEMA_V1_SCHEMA_VERSION)),
    )


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
