from __future__ import annotations

import argparse
import json
from pathlib import Path

import scripts.update_medical_term_index as index_builder
from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import (
    VocabularyProviderMatch,
    active_index_status,
    lookup_medical_terms,
)
from app.shared.query_intelligence.medical_terms.term_index_loader import (
    load_full_term_index,
    load_mini_term_index,
)
from app.shared.query_intelligence.medical_terms.zh_overrides_loader import load_zh_overrides


ROOT = Path(__file__).resolve().parents[2]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"


def test_stage_v0_1_required_runtime_resources_exist_and_load() -> None:
    manifest = json.loads((ROOT / "data" / "package_manifest.json").read_text(encoding="utf-8"))
    medical = manifest["medical_terms_index"]
    required = {
        "data/medical_terms/mini_medical_terms_index.json",
        "data/medical_terms/zh_term_overrides.json",
        "data/medical_terms/source_metadata.json",
        "data/medical_terms/license_attribution.md",
    }
    status = active_index_status()

    assert medical["scope"] == "BioMedPilot shared medical vocabulary"
    assert medical["not_bioinformatics_specific"] is True
    assert required <= set(medical["included_in_default_package"])
    for relative_path in required:
        assert (ROOT / relative_path).exists()
    assert status["mini_index_available"] is True
    assert load_mini_term_index()
    assert load_zh_overrides()


def test_stage_v0_1_sqlite_is_optional_and_json_fallback_is_supported(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.shared.query_intelligence.medical_terms.term_lookup.load_full_term_index",
        lambda: (),
    )

    result = lookup_medical_terms("脑胶质瘤", target_context="bioinformatics")

    assert "medical_terms_index.sqlite" not in result.term_sources
    assert "mini_medical_terms_index" in result.term_sources or "zh_term_overrides" in result.term_sources
    assert "glioma" in " ".join(result.disease_terms_en).lower()


def test_stage_v0_1_tracked_sqlite_matches_current_schema_when_present() -> None:
    index_path = MEDICAL_TERMS / "medical_terms_index.sqlite"
    if not index_path.exists():
        return

    load_full_term_index.cache_clear()
    concepts = load_full_term_index(str(index_path))

    assert concepts
    assert {concept.concept_id for concept in concepts} >= {"mini:glioma", "mini:thyroid_cancer"}


def test_stage_v0_1_modality_only_terms_do_not_become_diseases() -> None:
    for term in ("read count", "counts", "TPM", "FPKM", "microarray", "RNA", "DNA", "CNV", "SNP"):
        result = lookup_medical_terms(term, target_context="bioinformatics")

        assert result.disease_terms_en == []
        assert result.outcome_terms == []
        assert result.effect_measures == []
        assert result.pubmed_query_terms == []


def test_stage_v0_1_context_filters_keep_bio_and_meta_search_surfaces_separate() -> None:
    bio = build_search_translation_draft(
        "甲状腺癌 OS HR RNA-seq 数据集",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "甲状腺癌 OS HR Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert bio.pubmed_query_candidates == []
    assert bio.geo_query_candidates
    assert bio.effect_measures == []
    assert bio.pubmed_query_terms == []
    assert "pubmed_query_terms" not in bio.audit["term_lookup"]

    assert meta.geo_query_candidates == []
    assert not meta.audit.get("tcga_project_candidates")
    assert not meta.audit.get("gtex_tissue_candidates")
    assert meta.pubmed_query_candidates
    assert "hazard ratio" in " ".join(meta.effect_measures).lower()


def test_stage_v0_1_ontology_download_requires_explicit_flag(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, Path]] = []

    def fail_if_called(url: str, target: Path) -> None:
        calls.append((url, target))
        raise AssertionError("ontology download must not run without explicit flag")

    monkeypatch.setattr(index_builder, "urlretrieve", fail_if_called)
    args = argparse.Namespace(
        mondo=None,
        doid=None,
        ncit=None,
        mesh=None,
        efo=None,
        download_dir=tmp_path / "raw",
    )

    paths = index_builder._resolve_source_paths(args, download_sources=False)

    assert set(paths) == {"MONDO", "DOID", "NCIt", "MeSH", "EFO"}
    assert calls == []
    assert not (tmp_path / "raw").exists()


def test_stage_v0_1_provider_match_contract_is_unmatched_without_payload() -> None:
    match = VocabularyProviderMatch(source="test_provider", provider_kind="test")

    assert match.matched is False
    assert match.result is None
    assert match.overrides == ()
    assert match.index_concepts == ()
    assert match.registry_concepts == ()
