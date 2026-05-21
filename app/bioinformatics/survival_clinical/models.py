from __future__ import annotations

from datetime import datetime, timezone


SURVIVAL_CLINICAL_INPUT_SCHEMA_VERSION = "biomedpilot.survival_clinical_input.v1"
SURVIVAL_OUTCOME_GATE_SCHEMA_VERSION = "biomedpilot.survival_outcome_gate.v1"
CLINICAL_VARIABLE_AUDIT_SCHEMA_VERSION = "biomedpilot.clinical_variable_audit.v1"

SURVIVAL_CLINICAL_TASK_TYPE = "survival_clinical_preflight"
SURVIVAL_CLINICAL_RESULT_SEMANTICS = "preflight_only"

CLINICAL_ASSET_TYPES = {"clinical_metadata", "survival_metadata", "tcga_clinical_metadata"}
SAMPLE_METADATA_ASSET_TYPES = {"sample_metadata", "phenotype_metadata", "tcga_sample_metadata", "gtex_sample_metadata"}
EXPRESSION_ASSET_TYPES = {"raw_count_matrix", "count_matrix", "expression_matrix", "normalized_expression_matrix", "tcga_expression_matrix", "gtex_expression_matrix"}

CASE_ID_COLUMNS = ("case_id", "case", "submitter_id", "patient", "patient_id", "patient_barcode", "participant_barcode", "bcr_patient_barcode")
SAMPLE_ID_COLUMNS = ("sample_id", "sample", "geo_accession", "gsm", "barcode", "tcga_barcode", "sample_barcode")
PATIENT_ID_COLUMNS = ("patient_id", "patient", "patient_barcode", "participant_barcode", "bcr_patient_barcode", "case_id")

TIME_FIELD_CANDIDATES = (
    "OS_time",
    "overall_survival_time",
    "days_to_death",
    "days_to_last_follow_up",
    "last_follow_up",
    "follow_up_time",
    "time",
)
EVENT_FIELD_CANDIDATES = (
    "OS_event",
    "overall_survival_event",
    "vital_status",
    "death_status",
    "event",
)

IDENTIFIER_HINTS = ("case_id", "sample_id", "patient_id", "barcode", "submitter_id", "geo_accession", "gsm")
ORDINAL_HINTS = ("stage", "grade", "ajcc", "tnm", "pathologic_stage", "clinical_stage")
DATE_HINTS = ("date", "diagnosis_date", "birth_date", "death_date")
TEXT_HINTS = ("comment", "note", "description", "free_text")

FORBIDDEN_SURVIVAL_OUTPUTS = [
    "KM plot",
    "log-rank p-value",
    "Cox hazard ratio",
    "HR",
    "survival p-value",
    "clinical advice",
    "treatment recommendation",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
