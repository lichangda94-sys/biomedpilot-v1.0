from __future__ import annotations

import json
from types import SimpleNamespace

from app.shared.query_intelligence import (
    LocalModelConfig,
    QueryIntelligenceInput,
    analyze_medical_question,
    build_search_translation_draft,
)
from app.shared.query_intelligence import local_model_bridge


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


def test_ollama_unavailable_falls_back_to_registry(monkeypatch) -> None:
    monkeypatch.setattr(local_model_bridge.shutil, "which", lambda _name: None)

    result = analyze_medical_question(
        QueryIntelligenceInput("肥胖与甲状腺癌发病的关系", target_context="meta_analysis")
    )

    assert result.local_model_status == "fallback_registry_only"
    assert "obesity" in result.en_terms
    assert "thyroid cancer" in result.en_terms


def test_ollama_unavailable_fallback_registry(monkeypatch) -> None:
    monkeypatch.setattr(local_model_bridge.shutil, "which", lambda _name: None)

    draft = build_search_translation_draft(
        "低分化食管鳞癌相关数据集",
        config=LocalModelConfig(enabled=True),
        use_local_model=True,
    )

    assert draft.local_model_status == "fallback_registry_only"
    assert any(term in draft.main_concepts_en for term in ["esophageal squamous cell carcinoma", "ESCC"])
    assert draft.geo_query_candidates


def test_ollama_available_not_called_by_default(monkeypatch) -> None:
    monkeypatch.setattr(local_model_bridge.shutil, "which", lambda _name: "/usr/local/bin/ollama")

    def fail_run(*_args, **_kwargs):  # pragma: no cover - should never run
        raise AssertionError("subprocess.run should not be called when config disables local model")

    monkeypatch.setattr(local_model_bridge.subprocess, "run", fail_run)

    draft = build_search_translation_draft(
        "低分化食管鳞癌相关数据集",
        config=LocalModelConfig(enabled=False),
    )

    assert draft.local_model_status in {"available_not_called", "disabled_by_config"}
    assert draft.local_model_used is False
    assert "esophageal squamous cell carcinoma" in draft.main_concepts_en


def test_ollama_called_success_json(monkeypatch) -> None:
    monkeypatch.setattr(local_model_bridge.shutil, "which", lambda _name: "/usr/local/bin/ollama")
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
    monkeypatch.setattr(
        local_model_bridge.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""),
    )

    draft = build_search_translation_draft(
        "低分化食管鳞癌相关数据集",
        config=LocalModelConfig(enabled=True),
        use_local_model=True,
    )

    assert draft.local_model_status == "called_success"
    assert "esophageal squamous cell carcinoma" in draft.main_concepts_en or "ESCC" in draft.main_concepts_en
    assert "poorly differentiated" in draft.modifier_terms_en
    assert draft.geo_query_candidates


def test_ollama_invalid_json_fallback(monkeypatch) -> None:
    monkeypatch.setattr(local_model_bridge.shutil, "which", lambda _name: "/usr/local/bin/ollama")
    monkeypatch.setattr(
        local_model_bridge.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="not json", stderr=""),
    )

    draft = build_search_translation_draft(
        "低分化食管鳞癌相关数据集",
        config=LocalModelConfig(enabled=True),
        use_local_model=True,
    )

    assert draft.local_model_status == "invalid_model_output_fallback_registry"
    assert "esophageal squamous cell carcinoma" in draft.main_concepts_en
    assert draft.geo_query_candidates


def test_disease_guard_filters_thyroid_from_escc(monkeypatch) -> None:
    monkeypatch.setattr(local_model_bridge.shutil, "which", lambda _name: "/usr/local/bin/ollama")
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
    monkeypatch.setattr(
        local_model_bridge.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""),
    )

    draft = build_search_translation_draft(
        "低分化食管鳞癌相关数据集",
        config=LocalModelConfig(enabled=True),
        use_local_model=True,
    )
    final_text = " ".join([*draft.main_concepts_en, *draft.pubmed_query_candidates, *draft.geo_query_candidates])

    assert "thyroid cancer" in draft.rejected_terms
    assert "PTC" in draft.rejected_terms
    assert "TCGA-THCA" in draft.rejected_terms
    assert "thyroid" not in final_text.lower()
    assert "PTC" not in final_text
    assert "TCGA-THCA" not in final_text


def test_disease_guard_filters_escc_from_thyroid(monkeypatch) -> None:
    monkeypatch.setattr(local_model_bridge.shutil, "which", lambda _name: "/usr/local/bin/ollama")
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
    monkeypatch.setattr(
        local_model_bridge.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr=""),
    )

    draft = build_search_translation_draft(
        "低分化甲状腺癌相关数据集",
        config=LocalModelConfig(enabled=True),
        use_local_model=True,
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


def test_registry_fallback_generates_geo_queries(monkeypatch) -> None:
    monkeypatch.setattr(local_model_bridge.shutil, "which", lambda _name: None)

    draft = build_search_translation_draft("低分化食管鳞癌相关数据集")
    text = " ".join([*draft.main_concepts_en, *draft.geo_query_candidates])

    assert "esophageal squamous cell carcinoma" in text or "ESCC" in text
    assert any(term in text for term in ["RNA-seq", "microarray", "expression profiling"])
