from __future__ import annotations

import app.shared.query_intelligence.medical_terms.term_lookup as term_lookup
from app.shared.query_intelligence.medical_terms import (
    MedicalVocabularyProvider,
    TermLookupResult,
    VocabularyProviderMatch,
    default_vocabulary_providers,
    lookup_medical_terms,
)


class _InjectedProvider:
    provider_id = "test_injected_vocabulary"
    provider_kind = "test_plugin"

    def lookup(self, query: str, normalized_query: str, target_context: str) -> VocabularyProviderMatch:
        if normalized_query != "插件病种":
            return VocabularyProviderMatch(source=self.provider_id, provider_kind=self.provider_kind)
        return VocabularyProviderMatch(
            source=self.provider_id,
            provider_kind=self.provider_kind,
            result=TermLookupResult(
                original_term=query,
                normalized_term=normalized_query,
                matched=True,
                disease_terms_en=["plugin disease"],
                concept_ids=["plugin:plugin_disease"],
                term_sources=[self.provider_id],
                confidence=0.99,
            ),
        )


def test_medical_vocabulary_provider_contract_is_exported_and_injectable() -> None:
    providers = default_vocabulary_providers()
    result = lookup_medical_terms("插件病种", providers=[_InjectedProvider()])

    assert providers
    assert isinstance(_InjectedProvider(), MedicalVocabularyProvider)
    assert result.disease_terms_en == ["plugin disease"]
    assert "plugin:plugin_disease" in result.concept_ids
    assert "test_injected_vocabulary" in result.term_sources
    assert result.confidence == 0.99


def test_zh_override_glioma_lookup() -> None:
    result = lookup_medical_terms("脑胶质瘤")

    assert "glioma" in result.disease_terms_en or "glioblastoma" in result.disease_terms_en
    assert any(term.lower() == "brain" for term in result.tissue_terms)
    assert {"TCGA-GBM", "TCGA-LGG"} <= set(result.tcga_project_candidates)
    assert "Brain" in result.gtex_tissue_candidates


def test_zh_override_escc_lookup() -> None:
    result = lookup_medical_terms("食管鳞癌")
    text = " ".join([*result.disease_terms_en, *result.abbreviations])

    assert "esophageal squamous cell carcinoma" in text or "ESCC" in text
    assert "thyroid cancer" not in text
    assert "PTC" not in text


def test_zh_override_thyroid_lookup() -> None:
    result = lookup_medical_terms("乳头状甲状腺癌")
    text = " ".join([*result.disease_terms_en, *result.abbreviations])

    assert "papillary thyroid carcinoma" in text or "thyroid cancer" in text
    assert "PTC" in result.abbreviations
    assert "ESCC" not in text


def test_term_lookup_prefers_longest_chinese_match() -> None:
    result = lookup_medical_terms("脑胶质瘤")

    assert "脑胶质瘤" in result.matched_zh_terms or "胶质瘤" in result.matched_zh_terms
    assert result.matched_zh_terms != ["脑"]
    assert "glioma" in result.disease_terms_en


def test_term_lookup_fallback_when_index_missing(monkeypatch) -> None:
    monkeypatch.setattr(term_lookup, "load_mini_term_index", lambda: ())

    result = term_lookup.lookup_medical_terms("脑胶质瘤")

    assert result.matched is True
    assert "glioma" in result.disease_terms_en
    assert "zh_term_overrides" in result.term_sources
