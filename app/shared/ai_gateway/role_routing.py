from __future__ import annotations

from dataclasses import dataclass

from app.shared.ai_gateway.models import AIGatewayConfig


BIO_GENERATE_DATASET_QUERY_DRAFT = "bio_generate_dataset_query_draft"
BIO_REFINE_MEDICAL_QUERY_TERMS = "bio_refine_medical_query_terms"
BIO_TRANSLATE_DATASET_DETAIL = "bio_translate_dataset_detail"
BIO_SUMMARIZE_DATASET_DETAIL = "bio_summarize_dataset_detail"

AI_ROLE_GENERAL_3B = "general_3b"
AI_ROLE_TRANSLATOR = "translator"
AI_ROLE_MEDICAL = "medical"

BIOINFORMATICS_TASK_ROLE_MAPPING: dict[str, str] = {
    BIO_GENERATE_DATASET_QUERY_DRAFT: AI_ROLE_GENERAL_3B,
    BIO_REFINE_MEDICAL_QUERY_TERMS: AI_ROLE_MEDICAL,
    BIO_TRANSLATE_DATASET_DETAIL: AI_ROLE_TRANSLATOR,
    BIO_SUMMARIZE_DATASET_DETAIL: AI_ROLE_MEDICAL,
}


@dataclass(frozen=True)
class AITaskRoleResolution:
    task_type: str
    role_id: str
    model_name: str
    status: str
    warning: str = ""

    @property
    def available(self) -> bool:
        return self.status in {"mapped", "fallback_model"}


def ai_role_for_task(task_type: str) -> str:
    return BIOINFORMATICS_TASK_ROLE_MAPPING.get(task_type.strip(), "")


def resolve_task_role_model(
    config: AIGatewayConfig,
    task_type: str,
    *,
    fallback_model: str = "",
) -> AITaskRoleResolution:
    clean_task = task_type.strip()
    role_id = ai_role_for_task(clean_task)
    if not role_id:
        clean_fallback = fallback_model.strip()
        if config.default_provider != "ollama" and clean_fallback:
            return AITaskRoleResolution(
                clean_task,
                "",
                clean_fallback,
                "fallback_model",
                "Task has no role mapping; using injected test/local fallback model.",
            )
        return AITaskRoleResolution(clean_task, "", clean_fallback, "unmapped_task", "AI task has no role mapping.")

    mapping = dict(config.role_model_mapping or {})
    model_name = str(mapping.get(role_id) or "").strip()
    if model_name:
        return AITaskRoleResolution(clean_task, role_id, model_name, "mapped")

    clean_fallback = fallback_model.strip()
    if config.default_provider == "ollama":
        return AITaskRoleResolution(
            clean_task,
            role_id,
            "",
            "role_mapping_missing",
            f"AI Gateway role_model_mapping 缺少 {role_id}。",
        )
    if clean_fallback:
        return AITaskRoleResolution(
            clean_task,
            role_id,
            clean_fallback,
            "fallback_model",
            "Role mapping missing; using injected test/local fallback model.",
        )
    return AITaskRoleResolution(clean_task, role_id, "", "role_mapping_missing", f"AI Gateway role_model_mapping 缺少 {role_id}。")
