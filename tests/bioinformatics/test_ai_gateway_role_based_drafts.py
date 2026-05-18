from __future__ import annotations

from pathlib import Path

from app.bioinformatics.download import GeoStudyTextInput, GeoTextSummaryService
from app.shared.ai_gateway import (
    AIGateway,
    AIGatewayConfig,
    AIGatewayRequest,
    AIGatewayResponse,
    AIProviderRegistry,
    BIO_GENERATE_DATASET_QUERY_DRAFT,
    BIO_REFINE_MEDICAL_QUERY_TERMS,
    BIO_SUMMARIZE_DATASET_DETAIL,
    BIO_TRANSLATE_DATASET_DETAIL,
    ai_role_for_task,
    load_ai_gateway_config,
)
from app.shared.ai_gateway.models import AIProviderStatus
from app.shared.ai_gateway.providers.base import AIProvider
from app.shared.query_intelligence import LocalModelConfig, build_search_translation_draft


def test_bioinformatics_ai_task_role_mapping() -> None:
    assert ai_role_for_task(BIO_GENERATE_DATASET_QUERY_DRAFT) == "general_3b"
    assert ai_role_for_task(BIO_REFINE_MEDICAL_QUERY_TERMS) == "medical"
    assert ai_role_for_task(BIO_TRANSLATE_DATASET_DETAIL) == "translator"
    assert ai_role_for_task(BIO_SUMMARIZE_DATASET_DETAIL) == "medical"


def test_disabled_gateway_keeps_rule_based_query_fallback(tmp_path: Path) -> None:
    config_path = tmp_path / "ai_gateway_config.json"
    config = load_ai_gateway_config(config_path)

    draft = build_search_translation_draft(
        "甲状腺癌相关数据集",
        config=LocalModelConfig(enabled=config.default_provider == "ollama"),
        use_local_model=False,
    )

    assert draft.source == "rule_based"
    assert draft.user_confirmation_required is True
    assert draft.accepted_by_user is False
    assert "thyroid cancer" in " ".join([*draft.main_concepts_en, *draft.geo_query_candidates]).lower()
    assert not config_path.exists()


def test_query_draft_requests_general_3b_role_when_mapping_exists() -> None:
    provider = _RoleRecordingProvider(
        {
            "main_concepts_zh": ["甲状腺癌"],
            "main_concepts_en": ["thyroid cancer"],
            "modifier_terms_zh": [],
            "modifier_terms_en": [],
            "data_type_terms_en": ["RNA-seq"],
            "pubmed_query_candidates": [],
            "geo_query_candidates": ['"thyroid cancer" AND "RNA-seq"'],
            "uncertainty": [],
            "notes": [],
        }
    )

    draft = build_search_translation_draft(
        "甲状腺癌相关数据集",
        config=LocalModelConfig(enabled=True, provider=provider.name),
        use_local_model=True,
        gateway_module="bioinformatics",
        gateway_task_type=BIO_GENERATE_DATASET_QUERY_DRAFT,
        ai_gateway=_gateway(provider),
    )

    assert draft.source == "local_model_draft"
    assert draft.ai_role == "general_3b"
    assert draft.model_name == "qwen2.5:3b"
    assert provider.requests[0].metadata["ai_role"] == "general_3b"
    assert provider.requests[0].metadata["model"] == "qwen2.5:3b"
    assert draft.user_confirmation_required is True


def test_medical_query_refine_requests_medical_role() -> None:
    provider = _RoleRecordingProvider(
        {
            "main_concepts_zh": ["胶质瘤"],
            "main_concepts_en": ["glioma"],
            "modifier_terms_zh": [],
            "modifier_terms_en": [],
            "data_type_terms_en": ["microarray"],
            "pubmed_query_candidates": [],
            "geo_query_candidates": ['"glioma" AND "microarray"'],
            "uncertainty": [],
            "notes": [],
        }
    )

    draft = build_search_translation_draft(
        "胶质瘤表达谱",
        config=LocalModelConfig(enabled=True, provider=provider.name),
        use_local_model=True,
        gateway_module="bioinformatics",
        gateway_task_type=BIO_REFINE_MEDICAL_QUERY_TERMS,
        ai_gateway=_gateway(provider),
    )

    assert draft.ai_role == "medical"
    assert draft.model_name == "medgemma:4b"
    assert provider.requests[0].metadata["ai_role"] == "medical"


def test_geo_text_summary_requests_translator_and_medical_roles() -> None:
    provider = _GeoTextProvider()
    service = GeoTextSummaryService(ai_gateway=_gateway(provider))

    summary = service.summarize(
        GeoStudyTextInput(
            accession="GSE33630",
            title_en="Glioma expression profile",
            summary_en="Glioma and normal brain samples.",
            overall_design_en="Tumor versus normal control.",
        )
    )

    assert summary.status == "completed"
    assert summary.source == "local_model_draft"
    assert summary.user_confirmation_required is True
    assert [request.task_type for request in provider.requests] == [BIO_TRANSLATE_DATASET_DETAIL, BIO_SUMMARIZE_DATASET_DETAIL]
    assert [request.metadata["ai_role"] for request in provider.requests] == ["translator", "medical"]
    assert [request.metadata["model"] for request in provider.requests] == ["translategemma:latest", "medgemma:4b"]


def test_gateway_failure_keeps_dataset_summary_fallback() -> None:
    service = GeoTextSummaryService(ai_gateway=_gateway(_FailingProvider()))

    summary = service.summarize(GeoStudyTextInput(accession="GSE33630", title_en="Glioma expression profile"))

    assert summary.status == "failed"
    assert summary.source == "fallback"
    assert summary.user_confirmation_required is True
    assert summary.brief_zh


def _gateway(provider: AIProvider) -> AIGateway:
    registry = AIProviderRegistry()
    registry.register(provider)
    return AIGateway(
        config=AIGatewayConfig(
            default_provider=provider.name,
            allow_network=False,
            role_model_mapping={
                "general_3b": "qwen2.5:3b",
                "translator": "translategemma:latest",
                "medical": "medgemma:4b",
            },
        ),
        provider_registry=registry,
        audit_logger=_NoopAuditLogger(),
    )


class _RoleRecordingProvider(AIProvider):
    name = "test_gateway"
    model_name = "mock-local-model"
    status = AIProviderStatus.AVAILABLE
    uses_network = False
    external_model = False

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.requests: list[AIGatewayRequest] = []

    def generate(self, request: AIGatewayRequest) -> AIGatewayResponse:
        import json

        self.requests.append(request)
        return AIGatewayResponse(
            request_id=request.request_id,
            module=request.module,
            task_type=request.task_type,
            status="success",
            content=json.dumps(self.payload, ensure_ascii=False),
            provider_name=self.name,
            model_name=str(request.metadata["model"]),
        )


class _GeoTextProvider(_RoleRecordingProvider):
    def __init__(self) -> None:
        super().__init__({})

    def generate(self, request: AIGatewayRequest) -> AIGatewayResponse:
        self.requests.append(request)
        if request.task_type == BIO_TRANSLATE_DATASET_DETAIL:
            content = '{"title_zh":"胶质瘤表达谱","summary_zh":"胶质瘤样本摘要。","overall_design_zh":"肿瘤和正常对照。"}'
        else:
            content = '{"brief_zh":"该数据集比较胶质瘤样本和正常脑组织对照。","covered_terms":[],"missing_or_uncertain":[]}'
        return AIGatewayResponse(
            request_id=request.request_id,
            module=request.module,
            task_type=request.task_type,
            status="success",
            content=content,
            provider_name=self.name,
            model_name=str(request.metadata["model"]),
        )


class _FailingProvider(_GeoTextProvider):
    def generate(self, request: AIGatewayRequest) -> AIGatewayResponse:
        self.requests.append(request)
        return AIGatewayResponse(
            request_id=request.request_id,
            module=request.module,
            task_type=request.task_type,
            status="error",
            content="",
            provider_name=self.name,
            model_name=str(request.metadata["model"]),
            fallback_used=True,
            error_message="simulated failure",
        )


class _NoopAuditLogger:
    def write(self, *_args, **_kwargs) -> None:
        return None
