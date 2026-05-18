from __future__ import annotations

from dataclasses import dataclass
from typing import Any


OLLAMA_LLM_PROVIDER = "ollama"
OLLAMA_LLM_ENGINE_FAMILY = "local_llm_ollama"
OLLAMA_LLM_ENGINE_ID = OLLAMA_LLM_ENGINE_FAMILY
OLLAMA_LLM_ENGINE_NAME = "Ollama 本地 LLM 外部引擎"
OLLAMA_LLM_ENGINE_TYPE = "local_llm_backend"
OLLAMA_LLM_HTTP_ENDPOINT = "http://localhost:11434"

OLLAMA_ROLE_GENERAL_3B = "general_3b"
OLLAMA_ROLE_TRANSLATOR = "translator"
OLLAMA_ROLE_MEDICAL = "medical"


@dataclass(frozen=True)
class OllamaModelRole:
    role_id: str
    default_model: str
    display_name: str
    intended_use: str
    required: bool
    provider: str = OLLAMA_LLM_PROVIDER
    privacy_note: str = "local_only: prompt stays on the configured local Ollama endpoint."
    allowed_task_types: tuple[str, ...] = ()

    @property
    def requirement_status(self) -> str:
        return "required" if self.required else "optional"

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "default_model": self.default_model,
            "display_name": self.display_name,
            "intended_use": self.intended_use,
            "requirement_status": self.requirement_status,
            "required": self.required,
            "provider": self.provider,
            "privacy_note": self.privacy_note,
            "allowed_task_types": list(self.allowed_task_types),
        }


OLLAMA_MODEL_ROLES: tuple[OllamaModelRole, ...] = (
    OllamaModelRole(
        role_id=OLLAMA_ROLE_GENERAL_3B,
        default_model="qwen2.5:3b",
        display_name="Ollama 3B 通用轻量模型",
        intended_use="中文主题理解、轻量检索词改写、非结论性草稿辅助。",
        required=True,
        allowed_task_types=(
            "bio_generate_dataset_query_draft",
            "meta_query_refine",
            "meta_pico_draft",
        ),
    ),
    OllamaModelRole(
        role_id=OLLAMA_ROLE_TRANSLATOR,
        default_model="translategemma:latest",
        display_name="Translator 本地翻译模型",
        intended_use="英文医学 metadata 到中文的保守翻译，不写入最终科研结论。",
        required=True,
        allowed_task_types=("bio_translate_dataset_detail",),
    ),
    OllamaModelRole(
        role_id=OLLAMA_ROLE_MEDICAL,
        default_model="medgemma:4b",
        display_name="Medical 本地医学模型",
        intended_use="医学语义提炼、研究问题精炼、检索候选草稿；输出需人工确认。",
        required=True,
        allowed_task_types=(
            "bio_translate_dataset_detail",
            "bio_generate_dataset_query_draft",
            "meta_query_refine",
            "meta_pico_draft",
            "meta_screening_reasoning_draft",
        ),
    ),
)


def ollama_model_role_registry() -> tuple[OllamaModelRole, ...]:
    return OLLAMA_MODEL_ROLES


def ollama_role_model_mapping() -> dict[str, str]:
    return {role.role_id: role.default_model for role in OLLAMA_MODEL_ROLES}


def ollama_model_role_registry_payload() -> list[dict[str, Any]]:
    return [role.to_dict() for role in OLLAMA_MODEL_ROLES]

