from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class AIProviderStatus(str, Enum):
    DISABLED = "disabled"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@dataclass(frozen=True)
class AIGatewayRequest:
    module: str
    task_type: str
    prompt: str = ""
    context: dict[str, object] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: f"ai-{uuid4().hex[:12]}")
    contains_sensitive_content: bool = False
    requires_network: bool = False
    requests_external_model: bool = False
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AIGatewayResponse:
    request_id: str
    module: str
    task_type: str
    status: str
    content: str
    provider_name: str = "disabled"
    model_name: str = ""
    fallback_used: bool = False
    error_message: str = ""
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AIGatewayConfig:
    allow_network: bool = False
    allow_external_model: bool = False
    allow_sensitive_upload: bool = False
    store_raw_prompts: bool = False
    store_raw_responses: bool = False
    default_provider: str = "disabled"
    audit_log_path: str = "logs/ai_gateway/ai_gateway_audit.jsonl"
    allowed_task_prefixes: dict[str, list[str]] = field(
        default_factory=lambda: {
            "bioinformatics": ["bio_"],
            "meta_analysis": ["meta_"],
        }
    )
    provider_configs: dict[str, dict[str, object]] = field(default_factory=dict)
