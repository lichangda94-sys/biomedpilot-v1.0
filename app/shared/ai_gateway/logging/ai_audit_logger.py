from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from app.shared.ai_gateway.models import AIGatewayConfig, AIGatewayRequest, AIGatewayResponse


class AIAuditLogger:
    def __init__(self, log_path: str | Path) -> None:
        self.log_path = Path(log_path)

    @classmethod
    def from_config(cls, config: AIGatewayConfig) -> "AIAuditLogger":
        return cls(config.audit_log_path)

    def write(self, request: AIGatewayRequest, response: AIGatewayResponse, config: AIGatewayConfig) -> None:
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            entry = self._entry(request, response, config)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        except Exception:
            return

    def _entry(
        self,
        request: AIGatewayRequest,
        response: AIGatewayResponse,
        config: AIGatewayConfig,
    ) -> dict[str, object]:
        entry: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request.request_id,
            "module": request.module,
            "task_type": request.task_type,
            "status": response.status,
            "provider_name": response.provider_name,
            "model_name": response.model_name,
            "fallback_used": response.fallback_used,
            "error_present": bool(response.error_message),
            "privacy": {
                "allow_network": config.allow_network,
                "allow_external_model": config.allow_external_model,
                "allow_sensitive_upload": config.allow_sensitive_upload,
                "store_raw_prompts": config.store_raw_prompts,
                "store_raw_responses": config.store_raw_responses,
            },
            "request_summary": {
                "prompt_length": len(request.prompt),
                "prompt_sha256": _sha256_text(request.prompt),
                "context_keys": sorted(str(key) for key in request.context),
                "contains_sensitive_content": request.contains_sensitive_content,
                "requires_network": request.requires_network,
                "requests_external_model": request.requests_external_model,
            },
            "response_summary": {
                "content_length": len(response.content),
                "content_sha256": _sha256_text(response.content),
            },
        }
        if response.error_message:
            entry["error_message"] = response.error_message
        if config.store_raw_prompts:
            entry["raw_prompt"] = request.prompt
            entry["raw_context"] = asdict(request).get("context", {})
        if config.store_raw_responses:
            entry["raw_response"] = response.content
        return entry


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else ""
