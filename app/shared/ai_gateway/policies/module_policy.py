from __future__ import annotations

from dataclasses import dataclass

from app.shared.ai_gateway.models import AIGatewayConfig, AIGatewayRequest


STRICT_MODULE_PREFIXES: dict[str, tuple[str, ...]] = {
    "bioinformatics": ("bio_",),
    "meta_analysis": ("meta_",),
}


@dataclass(frozen=True)
class ModulePolicyDecision:
    allowed: bool
    reason: str = ""


def check_module_policy(request: AIGatewayRequest, config: AIGatewayConfig) -> ModulePolicyDecision:
    module = request.module.strip()
    task_type = request.task_type.strip()
    if not module:
        return ModulePolicyDecision(False, "module is required")
    if not task_type:
        return ModulePolicyDecision(False, "task_type is required")

    strict_prefixes = STRICT_MODULE_PREFIXES.get(module)
    if strict_prefixes is not None:
        if task_type.startswith(strict_prefixes):
            return ModulePolicyDecision(True)
        return ModulePolicyDecision(False, f"{module} can only call tasks with prefixes: {', '.join(strict_prefixes)}")

    configured_prefixes = tuple(config.allowed_task_prefixes.get(module, []))
    if configured_prefixes and task_type.startswith(configured_prefixes):
        return ModulePolicyDecision(True)
    if configured_prefixes:
        return ModulePolicyDecision(False, f"{module} is configured but task_type is outside its allowed prefixes")
    return ModulePolicyDecision(False, f"{module} is not allowed to use AI Gateway")
