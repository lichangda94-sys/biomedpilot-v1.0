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


def test_chinese_question_maps_to_shared_medical_concepts() -> None:
    result = analyze_medical_question(
        QueryIntelligenceInput(
            "肥胖与甲状腺癌发病的关系",
            language_hint="zh",
            target_context="meta_analysis",
        )
    )

    assert "肥胖" in result.zh_terms
    assert "甲状腺癌" in result.zh_terms
    assert "发病" in result.zh_terms
    assert "obesity" in result.en_terms
    assert "BMI" in result.en_terms
    assert "thyroid cancer" in result.en_terms
    assert "Obesity" in result.mesh_terms
    assert "Body Mass Index" in result.mesh_terms
    assert "Thyroid Neoplasms" in result.mesh_terms


def test_ollama_unavailable_falls_back_to_registry() -> None:
    result = analyze_medical_question(
        QueryIntelligenceInput("肥胖与甲状腺癌发病的关系", target_context="meta_analysis")
    )

    assert result.local_model_status == "fallback_registry_only"
    assert "obesity" in result.en_terms
    assert "thyroid cancer" in result.en_terms


def test_local_model_missing_gateway_context_fallback_registry() -> None:
    draft = build_search_translation_draft(
        "低分化食管鳞癌相关数据集",
        config=LocalModelConfig(enabled=True),
        use_local_model=True,
    )

    assert draft.local_model_status == "fallback_registry_only"
    assert draft.audit["local_model"]["status"] == "missing_gateway_context_fallback_registry"
    assert any(term in draft.main_concepts_en for term in ["esophageal squamous cell carcinoma", "ESCC"])
    assert draft.geo_query_candidates


def test_ollama_available_not_called_by_default() -> None:
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


def test_local_model_defaults_use_installed_translate_and_medical_names() -> None:
    config = LocalModelConfig()

    assert config.translator_model == "translategemma"
    assert config.medical_model == "medgemma:4b"


def test_ollama_called_success_json() -> None:
    payload = {
        "main_concepts_zh": ["食管鳞癌"],
        "main_concepts_en": ["esophageal squamous cell carcinoma", "ESCC"],
        "modifier_terms_zh": ["低分化"],
        "modifier_terms_en": ["poorly differentiated"],
        "data_type_terms_en": ["RNA-seq", "microarray"],
        "pubmed_query_candidates": ['"esophageal squamous cell carcinoma" AND "poorly differentiated"'],
        "geo_query_candidates": ["ESCC AND RNA-seq"],
        "uncertainty": [],
        "notes": [],
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

    assert draft.local_model_status == "called_success"
    assert provider.requests[0].module == "bioinformatics"
    assert provider.requests[0].task_type == "bio_zh_topic_to_dataset_queries"
    assert "esophageal squamous cell carcinoma" in draft.main_concepts_en or "ESCC" in draft.main_concepts_en
    assert "poorly differentiated" in draft.modifier_terms_en
    assert draft.geo_query_candidates
    assert "raw_output" not in draft.audit["local_model"]
    assert draft.audit["local_model"]["output_char_count"] > 0
    assert draft.audit["local_model"]["output_sha256"]


def test_ollama_invalid_json_fallback() -> None:
    provider = _GatewayTextProvider("not json")

    draft = build_search_translation_draft(
        "低分化食管鳞癌相关数据集",
        config=LocalModelConfig(enabled=True, provider="test_gateway"),
        use_local_model=True,
        gateway_module="bioinformatics",
        gateway_task_type="bio_zh_topic_to_dataset_queries",
        ai_gateway=_gateway_with_provider(provider),
    )

    assert draft.local_model_status == "invalid_model_output_fallback_registry"
    assert "esophageal squamous cell carcinoma" in draft.main_concepts_en
    assert draft.geo_query_candidates


def test_disease_guard_filters_thyroid_from_escc() -> None:
    payload = {
        "main_concepts_zh": ["食管鳞癌"],
        "main_concepts_en": ["esophageal squamous cell carcinoma", "thyroid cancer", "PTC", "TCGA-THCA"],
        "modifier_terms_zh": ["低分化"],
        "modifier_terms_en": ["poorly differentiated"],
        "data_type_terms_en": ["RNA-seq"],
        "pubmed_query_candidates": ['"thyroid cancer" AND "poorly differentiated"'],
        "geo_query_candidates": ["PTC AND RNA-seq", "TCGA-THCA AND microarray", "ESCC AND RNA-seq"],
        "uncertainty": [],
        "notes": [],
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
    final_text = " ".join([*draft.main_concepts_en, *draft.pubmed_query_candidates, *draft.geo_query_candidates])

    assert "thyroid cancer" in draft.rejected_terms
    assert "PTC" in draft.rejected_terms
    assert "TCGA-THCA" in draft.rejected_terms
    assert "thyroid" not in final_text.lower()
    assert "PTC" not in final_text
    assert "TCGA-THCA" not in final_text


def test_disease_guard_filters_escc_from_thyroid() -> None:
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


def test_search_translation_draft_editable_contract() -> None:
    draft = build_search_translation_draft("低分化食管鳞癌相关数据集")

    assert isinstance(draft.pubmed_query_candidates, list)
    assert isinstance(draft.geo_query_candidates, list)
    assert all(isinstance(item, str) for item in draft.pubmed_query_candidates)
    assert all(isinstance(item, str) for item in draft.geo_query_candidates)
    assert draft.search_execution_status == "draft_only"


def test_build_search_translation_draft_uses_zh_override_glioma() -> None:
    draft = build_search_translation_draft("脑胶质瘤")
    text = " ".join([*draft.main_concepts_en, *draft.disease_terms_en, *draft.geo_query_candidates])

    assert draft.main_concepts_en
    assert "glioma" in text or "glioblastoma" in text
    assert "term_lookup" in draft.audit
    assert "zh_term_overrides" in draft.audit.get("term_sources", [])
    assert "TCGA-GBM" in draft.audit.get("tcga_project_candidates", [])
    assert "Brain" in draft.audit.get("gtex_tissue_candidates", [])


def test_disease_guard_still_filters_cross_disease_terms() -> None:
    escc = build_search_translation_draft("食管鳞癌")
    thyroid = build_search_translation_draft("甲状腺癌")
    glioma = build_search_translation_draft("脑胶质瘤")

    escc_text = " ".join([*escc.main_concepts_en, *escc.disease_terms_en, *escc.database_terms])
    thyroid_text = " ".join([*thyroid.main_concepts_en, *thyroid.disease_terms_en, *thyroid.database_terms])
    glioma_text = " ".join([*glioma.main_concepts_en, *glioma.disease_terms_en, *glioma.database_terms])

    assert "thyroid" not in escc_text.lower()
    assert "PTC" not in escc_text
    assert "escc" not in thyroid_text.lower()
    assert "esophageal" not in thyroid_text.lower()
    assert "thyroid" not in glioma_text.lower()
    assert "escc" not in glioma_text.lower()


def test_meta_exposure_risk_intent_uses_peco_terms() -> None:
    draft = build_search_translation_draft(
        "肥胖与甲状腺癌发病风险 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert draft.review_or_analysis_intent == "exposure_disease_risk_meta"
    assert "obesity" in " ".join(draft.exposure_terms_en).lower()
    assert "thyroid cancer" in " ".join(draft.disease_terms_en).lower()
    assert draft.search_execution_status == "draft_only"
    assert draft.pubmed_query_candidates
    assert draft.geo_query_candidates == []
    assert not draft.audit.get("tcga_project_candidates")
    assert not draft.audit.get("gtex_tissue_candidates")


def test_meta_pubmed_query_prefers_mesh_terms() -> None:
    draft = build_search_translation_draft(
        "甲状腺癌 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert draft.mesh_terms
    assert draft.pubmed_query_candidates[0].endswith("[Mesh]")
    assert "TCGA-THCA" not in " ".join(draft.pubmed_query_candidates + draft.database_terms)


def test_sqlite_optional_index_preserves_bio_and_meta_boundaries() -> None:
    bio = build_search_translation_draft(
        "脑胶质瘤肾脏转录组",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "神经退行性疾病 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert "glioma" in " ".join([*bio.main_concepts_en, *bio.disease_terms_en]).lower()
    assert "Brain" in bio.audit.get("gtex_tissue_candidates", [])
    assert bio.geo_query_candidates
    assert meta.geo_query_candidates == []
    assert not meta.audit.get("tcga_project_candidates")
    assert not meta.audit.get("gtex_tissue_candidates")
    assert "neurodegenerative disease" in " ".join([*meta.main_concepts_en, *meta.disease_terms_en]).lower()


def test_unknown_term_local_model_candidates_do_not_enter_final_query() -> None:
    payload = {
        "main_concepts_zh": ["未知中文疾病"],
        "main_concepts_en": ["glioma", "imaginary disease"],
        "modifier_terms_zh": [],
        "modifier_terms_en": [],
        "data_type_terms_en": ["RNA-seq"],
        "pubmed_query_candidates": ['"glioma"[tiab]'],
        "geo_query_candidates": ['"glioma" AND "RNA-seq"'],
        "candidate_terms": ["glioma", "imaginary disease", "TCGA-THCA"],
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
    assert draft.candidate_terms == ["glioma"]
    assert draft.main_concepts_en == []
    assert draft.geo_query_candidates == []
    assert "glioma" not in " ".join([*draft.main_concepts_en, *draft.geo_query_candidates, *draft.database_terms]).lower()
    assert not draft.audit.get("tcga_project_candidates")
    assert not draft.audit.get("gtex_tissue_candidates")
    assert draft.audit["local_model"]["candidate_policy"] == "unknown_term_candidates_only_not_final_query"


def test_unknown_term_meta_candidates_keep_bio_fields_filtered() -> None:
    payload = {
        "main_concepts_zh": ["未知中文疾病"],
        "main_concepts_en": ["thyroid cancer"],
        "modifier_terms_zh": [],
        "modifier_terms_en": [],
        "data_type_terms_en": [],
        "pubmed_query_candidates": ['"thyroid cancer"[tiab]'],
        "geo_query_candidates": ["TCGA-THCA AND RNA-seq"],
        "candidate_terms": ["thyroid cancer", "TCGA-THCA", "GTEx Thyroid"],
        "uncertainty": [],
        "notes": [],
    }
    provider = _GatewayJSONProvider(payload)

    draft = build_search_translation_draft(
        "未知中文疾病",
        target_context="meta_analysis",
        target_database="pubmed",
        config=LocalModelConfig(enabled=True, provider="test_gateway"),
        use_local_model=True,
        gateway_module="meta_analysis",
        gateway_task_type="meta_generate_search_strategy",
        ai_gateway=_gateway_with_provider(provider),
    )

    assert draft.candidate_terms == ["thyroid cancer"]
    assert draft.pubmed_query_candidates == []
    assert draft.geo_query_candidates == []
    assert not draft.audit.get("tcga_project_candidates")
    assert not draft.audit.get("gtex_tissue_candidates")


def test_bioinformatics_context_filters_literature_candidates() -> None:
    draft = build_search_translation_draft(
        "甲状腺癌相关数据集",
        target_context="bioinformatics",
        target_database="geo",
    )

    assert draft.pubmed_query_candidates == []
    assert draft.geo_query_candidates
    assert "TCGA-THCA" in draft.audit.get("tcga_project_candidates", [])
    assert draft.audit["context_output_policy"]["blocks"]


def test_registry_fallback_generates_geo_queries() -> None:
    draft = build_search_translation_draft("低分化食管鳞癌相关数据集")
    text = " ".join([*draft.main_concepts_en, *draft.geo_query_candidates])

    assert "esophageal squamous cell carcinoma" in text or "ESCC" in text
    assert any(term in text for term in ["RNA-seq", "microarray", "expression profiling"])


def test_gateway_module_policy_blocks_cross_context_local_model_call() -> None:
    payload = {
        "main_concepts_zh": ["甲状腺癌"],
        "main_concepts_en": ["thyroid cancer"],
        "modifier_terms_zh": [],
        "modifier_terms_en": [],
        "data_type_terms_en": [],
        "pubmed_query_candidates": ['"thyroid cancer"[tiab]'],
        "geo_query_candidates": [],
        "uncertainty": [],
        "notes": [],
    }
    provider = _GatewayJSONProvider(payload)

    draft = build_search_translation_draft(
        "甲状腺癌 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
        config=LocalModelConfig(enabled=True, provider="test_gateway"),
        use_local_model=True,
        gateway_module="meta_analysis",
        gateway_task_type="bio_zh_topic_to_dataset_queries",
        ai_gateway=_gateway_with_provider(provider),
    )

    assert draft.local_model_status == "called_failed_fallback_registry"
    assert provider.requests == []
    assert draft.pubmed_query_candidates


def test_shared_query_intelligence_audit_does_not_store_raw_model_output() -> None:
    secret = "SECRET_MODEL_OUTPUT_SHOULD_NOT_BE_STORED"
    payload = {
        "main_concepts_zh": ["食管鳞癌"],
        "main_concepts_en": ["esophageal squamous cell carcinoma"],
        "modifier_terms_zh": [],
        "modifier_terms_en": [],
        "data_type_terms_en": ["RNA-seq"],
        "pubmed_query_candidates": [],
        "geo_query_candidates": ["ESCC AND RNA-seq"],
        "uncertainty": [],
        "notes": [],
        "private_raw": secret,
    }
    provider = _GatewayJSONProvider(payload)

    draft = build_search_translation_draft(
        "食管鳞癌相关数据集",
        config=LocalModelConfig(enabled=True, provider="test_gateway"),
        use_local_model=True,
        gateway_module="bioinformatics",
        gateway_task_type="bio_zh_topic_to_dataset_queries",
        ai_gateway=_gateway_with_provider(provider),
    )

    audit_text = json.dumps(draft.audit, ensure_ascii=False)
    assert "raw_output" not in draft.audit["local_model"]
    assert secret not in audit_text
    assert draft.audit["local_model"]["output_char_count"] > 0
    assert draft.audit["local_model"]["output_sha256"]


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


class _GatewayTextProvider(_GatewayJSONProvider):
    def __init__(self, content: str) -> None:
        super().__init__({})
        self.content = content

    def generate(self, request: AIGatewayRequest) -> AIGatewayResponse:
        self.requests.append(request)
        return AIGatewayResponse(
            request_id=request.request_id,
            module=request.module,
            task_type=request.task_type,
            status="success",
            content=self.content,
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
