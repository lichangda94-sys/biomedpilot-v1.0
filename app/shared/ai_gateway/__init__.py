from __future__ import annotations

from app.shared.ai_gateway.config import DEFAULT_LOCAL_OLLAMA_ROLE_MODEL_MAPPING, desktop_local_ollama_config, load_ai_gateway_config, save_ai_gateway_config
from app.shared.ai_gateway.drafts import AIDraftRecord, create_ai_draft_record, mark_ai_draft_status, save_ai_draft_record
from app.shared.ai_gateway.gateway import AIGateway
from app.shared.ai_gateway.models import AIGatewayConfig, AIGatewayRequest, AIGatewayResponse, AIProviderStatus
from app.shared.ai_gateway.provider_registry import AIProviderRegistry
from app.shared.ai_gateway.role_routing import (
    AI_ROLE_GENERAL_3B,
    AI_ROLE_MEDICAL,
    AI_ROLE_TRANSLATOR,
    BIO_GENERATE_DATASET_QUERY_DRAFT,
    BIO_REFINE_MEDICAL_QUERY_TERMS,
    BIO_SUMMARIZE_DATASET_DETAIL,
    BIO_TRANSLATE_DATASET_DETAIL,
    BIOINFORMATICS_TASK_ROLE_MAPPING,
    AITaskRoleResolution,
    ai_role_for_task,
    resolve_task_role_model,
)

__all__ = [
    "AIGateway",
    "AIGatewayConfig",
    "AIGatewayRequest",
    "AIGatewayResponse",
    "AIProviderRegistry",
    "AIProviderStatus",
    "AI_ROLE_GENERAL_3B",
    "AI_ROLE_MEDICAL",
    "AI_ROLE_TRANSLATOR",
    "AIDraftRecord",
    "AITaskRoleResolution",
    "BIO_GENERATE_DATASET_QUERY_DRAFT",
    "BIO_REFINE_MEDICAL_QUERY_TERMS",
    "BIO_SUMMARIZE_DATASET_DETAIL",
    "BIO_TRANSLATE_DATASET_DETAIL",
    "BIOINFORMATICS_TASK_ROLE_MAPPING",
    "DEFAULT_LOCAL_OLLAMA_ROLE_MODEL_MAPPING",
    "ai_role_for_task",
    "create_ai_draft_record",
    "desktop_local_ollama_config",
    "load_ai_gateway_config",
    "mark_ai_draft_status",
    "resolve_task_role_model",
    "save_ai_draft_record",
    "save_ai_gateway_config",
]
