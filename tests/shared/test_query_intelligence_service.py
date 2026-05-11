from __future__ import annotations

import json

from app.shared.ai_gateway import AIGateway, AIGatewayConfig
from app.shared.ai_gateway.models import AIGatewayRequest, AIGatewayResponse, AIProviderStatus
from app.shared.ai_gateway.provider_registry import AIProviderRegistry
from app.shared.ai_gateway.providers.base import AIProvider
from app.shared.query_intelligence import (
    LocalModelConfig,
    QueryIntelligenceInput,
    analyze_medical_question,
    build_search_translation_draft,
)
from app.shared.query_intelligence.medical_terms import active_index_status, lookup_medical_terms


def test_registry_fallback_maps_shared_concepts_without_bundled_vocabulary_assets() -> None:
    result = analyze_medical_question(
        QueryIntelligenceInput(
            "肥胖与甲状腺癌发病的关系",
            language_hint="zh",
            target_context="meta_analysis",
        )
    )

    assert "肥胖" in result.zh_terms
    assert "甲状腺癌" in result.zh_terms
    assert "obesity" in result.en_terms
    assert "thyroid cancer" in result.en_terms
    assert "Obesity" in result.mesh_terms
    assert "Thyroid Neoplasms" in result.mesh_terms


def test_lookup_uses_registry_when_external_medical_terms_assets_are_absent() -> None:
    status = active_index_status()
    result = lookup_medical_terms("甲状腺癌", target_context="bioinformatics")

    assert status["full_index_available"] is False
    assert status["mini_index_available"] is False
    assert "biomedical_term_registry" in result.term_sources
    assert "thyroid cancer" in result.disease_terms_en
    assert "TCGA-THCA" in result.tcga_project_candidates


def test_build_search_translation_draft_keeps_context_boundaries() -> None:
    bio = build_search_translation_draft(
        "甲状腺癌相关数据集",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "甲状腺癌 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert bio.pubmed_query_candidates == []
    assert bio.geo_query_candidates
    assert "TCGA-THCA" in bio.audit.get("tcga_project_candidates", [])
    assert meta.geo_query_candidates == []
    assert meta.pubmed_query_candidates
    assert not meta.audit.get("tcga_project_candidates")
    assert not meta.audit.get("gtex_tissue_candidates")


def test_local_model_not_called_by_default() -> None:
    provider = _GatewayJSONProvider({})
    draft = build_search_translation_draft(
        "低分化食管鳞癌相关数据集",
        config=LocalModelConfig(enabled=False),
        ai_gateway=_gateway_with_provider(provider),
    )

    assert draft.local_model_status in {"fallback_registry_only", "disabled_by_config"}
    assert draft.local_model_used is False
    assert "esophageal squamous cell carcinoma" in draft.main_concepts_en
    assert provider.requests == []


def test_local_model_success_keeps_audit_without_raw_output() -> None:
    payload = {
        "main_concepts_zh": ["食管鳞癌"],
        "main_concepts_en": ["esophageal squamous cell carcinoma", "ESCC"],
        "modifier_terms_zh": ["低分化"],
        "modifier_terms_en": ["poorly differentiated"],
        "data_type_terms_en": ["RNA-seq"],
        "pubmed_query_candidates": ['"esophageal squamous cell carcinoma" AND "poorly differentiated"'],
        "geo_query_candidates": ["ESCC AND RNA-seq"],
        "uncertainty": [],
        "notes": [],
        "private_raw": "SECRET_MODEL_OUTPUT_SHOULD_NOT_BE_STORED",
    }
    provider = _GatewayJSONProvider(payload)

    draft = build_search_translation_draft(
        "低分化食管鳞癌相关数据集",
        config=LocalModelConfig(enabled=True, provider="test_gateway"),
        use_local_model=True,
        gateway_module="bioinformatics",
        gateway_task_type="bio_zh_topic_to_dataset_queries",
        ai_gateway=_gateway_with_provider(provider),
    )

    audit_text = json.dumps(draft.audit, ensure_ascii=False)
    assert draft.local_model_status == "called_success"
    assert provider.requests[0].module == "bioinformatics"
    assert provider.requests[0].task_type == "bio_zh_topic_to_dataset_queries"
    assert "raw_output" not in draft.audit["local_model"]
    assert "SECRET_MODEL_OUTPUT_SHOULD_NOT_BE_STORED" not in audit_text
    assert draft.audit["local_model"]["output_sha256"]


def test_disease_guard_filters_cross_disease_terms() -> None:
    payload = {
        "main_concepts_zh": ["甲状腺癌"],
        "main_concepts_en": ["thyroid cancer", "ESCC", "esophageal cancer"],
        "modifier_terms_zh": ["低分化"],
        "modifier_terms_en": ["poorly differentiated"],
        "data_type_terms_en": ["microarray"],
        "pubmed_query_candidates": ["ESCC AND poorly differentiated"],
        "geo_query_candidates": ["esophageal cancer AND microarray", '"thyroid cancer" AND microarray'],
        "uncertainty": [],
        "notes": [],
    }
    provider = _GatewayJSONProvider(payload)

    draft = build_search_translation_draft(
        "低分化甲状腺癌相关数据集",
        config=LocalModelConfig(enabled=True, provider="test_gateway"),
        use_local_model=True,
        gateway_module="bioinformatics",
        gateway_task_type="bio_zh_topic_to_dataset_queries",
        ai_gateway=_gateway_with_provider(provider),
    )
    final_text = " ".join([*draft.main_concepts_en, *draft.pubmed_query_candidates, *draft.geo_query_candidates])

    assert "ESCC" in draft.rejected_terms
    assert "esophageal cancer" in draft.rejected_terms
    assert "escc" not in final_text.lower()
    assert "esophageal" not in final_text.lower()


def test_unknown_term_local_model_candidates_do_not_enter_final_query_without_authoritative_vocab() -> None:
    payload = {
        "main_concepts_zh": ["未知中文疾病"],
        "main_concepts_en": ["imaginary disease"],
        "modifier_terms_zh": [],
        "modifier_terms_en": [],
        "data_type_terms_en": ["RNA-seq"],
        "pubmed_query_candidates": ['"imaginary disease"[tiab]'],
        "geo_query_candidates": ['"imaginary disease" AND "RNA-seq"'],
        "candidate_terms": ["imaginary disease"],
        "uncertainty": [],
        "notes": [],
    }
    provider = _GatewayJSONProvider(payload)

    draft = build_search_translation_draft(
        "未知中文疾病",
        target_context="bioinformatics",
        target_database="geo",
        config=LocalModelConfig(enabled=True, provider="test_gateway"),
        use_local_model=True,
        gateway_module="bioinformatics",
        gateway_task_type="bio_zh_topic_to_dataset_queries",
        ai_gateway=_gateway_with_provider(provider),
    )

    assert draft.local_model_status == "called_success"
    assert draft.candidate_terms == []
    assert draft.main_concepts_en == []
    assert draft.geo_query_candidates == []
    assert draft.audit["local_model"]["candidate_policy"] == "unknown_term_candidates_only_not_final_query"


class _GatewayJSONProvider(AIProvider):
    name = "test_gateway"
    model_name = "mock-local-model"
    status = AIProviderStatus.AVAILABLE
    uses_network = False
    external_model = False

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.requests: list[AIGatewayRequest] = []

    def generate(self, request: AIGatewayRequest) -> AIGatewayResponse:
        self.requests.append(request)
        return AIGatewayResponse(
            request_id=request.request_id,
            module=request.module,
            task_type=request.task_type,
            status="success",
            content=json.dumps(self.payload, ensure_ascii=False),
            provider_name=self.name,
            model_name=self.model_name,
        )


def _gateway_with_provider(provider: AIProvider) -> AIGateway:
    registry = AIProviderRegistry()
    registry.register(provider)
    return AIGateway(
        config=AIGatewayConfig(default_provider=provider.name),
        provider_registry=registry,
        audit_logger=_NoopAuditLogger(),
    )


class _NoopAuditLogger:
    def write(self, *_args, **_kwargs) -> None:
        return None
