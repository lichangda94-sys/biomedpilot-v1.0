from __future__ import annotations

import app.shared.query_intelligence.medical_terms.term_lookup as term_lookup
from app.shared.query_intelligence.medical_terms import lookup_medical_terms


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
