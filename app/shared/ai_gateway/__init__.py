from __future__ import annotations

from app.shared.ai_gateway.config import desktop_local_ollama_config, load_ai_gateway_config, save_ai_gateway_config
from app.shared.ai_gateway.drafts import AIDraftRecord, create_ai_draft_record, mark_ai_draft_status, save_ai_draft_record
from app.shared.ai_gateway.gateway import AIGateway
from app.shared.ai_gateway.models import AIGatewayConfig, AIGatewayRequest, AIGatewayResponse, AIProviderStatus
from app.shared.ai_gateway.provider_registry import AIProviderRegistry

__all__ = [
    "AIGateway",
    "AIGatewayConfig",
    "AIGatewayRequest",
    "AIGatewayResponse",
    "AIProviderRegistry",
    "AIProviderStatus",
    "AIDraftRecord",
    "create_ai_draft_record",
    "desktop_local_ollama_config",
    "load_ai_gateway_config",
    "mark_ai_draft_status",
    "save_ai_draft_record",
    "save_ai_gateway_config",
]
