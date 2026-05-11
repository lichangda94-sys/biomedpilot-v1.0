from __future__ import annotations

import json
from pathlib import Path

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report


ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_PATH = ROOT / "data" / "medical_terms" / "reference_checklists" / "anatomy_tissue_core_checklist.json"


def _lookup_text(term: str) -> str:
    result = lookup_medical_terms(term)
    return " ".join(
        [
            *result.disease_terms_en,
            *result.synonyms_en,
            *result.abbreviations,
            *result.mesh_terms,
            *result.tissue_terms,
            *result.gtex_tissue_candidates,
            *result.tcga_primary_site_candidates,
            *result.tcga_project_candidates,
        ]
    )


def test_anatomy_tissue_checklist_has_gtex_and_tcga_primary_site_scope() -> None:
    payload = json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))
    gtex = {candidate for item in payload["items"] for candidate in item.get("gtex_tissue_candidates", [])}
    primary_sites = {candidate for item in payload["items"] for candidate in item.get("tcga_primary_site_candidates", [])}
    ambiguity_terms = {item["term"] for item in payload["ambiguity_terms"]}

    assert payload["coverage_type"] == "anatomy_tissue_core"
    assert len(payload["items"]) >= 65
    assert len(gtex) >= 50
    assert len(primary_sites) >= 25
    assert {"Thyroid", "Liver", "Lung", "Whole Blood", "Adipose - Subcutaneous", "Adipose - Visceral"} <= gtex
    assert {"breast", "lung", "liver", "thyroid", "colon", "rectum", "bone marrow", "lymph node", "soft tissue"} <= primary_sites
    assert {"thyroid", "liver", "lung", "colon", "rectum", "blood", "bone marrow", "lymph node", "adipose tissue"} <= ambiguity_terms


def test_anatomy_tissue_coverage_audit_is_complete() -> None:
    report = build_coverage_audit_report()
    section = report["sections"]["anatomy_tissue_core"]
    gates = {gate["gate_id"]: gate for gate in report["quality_gates"]["gates"]}

    assert section["covered"] == section["total_checklist_items"]
    assert section["missing"] == 0
    assert section["coverage_rate"] == 1.0
    assert section["gtex_tissue_coverage"]["missing_tissues"] == []
    assert section["tcga_primary_site_coverage"]["missing_sites"] == []
    assert gates["anatomy_tissue_core_coverage"]["status"] == "pass"
    assert gates["anatomy_tissue_missing_gtex_tissues"]["observed"] == 0
    assert gates["anatomy_tissue_missing_tcga_primary_sites"]["observed"] == 0


def test_gtex_tissue_and_chinese_organ_positive_lookup() -> None:
    cases = [
        ("皮下脂肪", "subcutaneous adipose tissue", "Adipose - Subcutaneous", "adipose tissue"),
        ("内脏脂肪", "visceral adipose tissue", "Adipose - Visceral", "adipose tissue"),
        ("肾上腺", "adrenal gland", "Adrenal Gland", "adrenal gland"),
        ("食管黏膜", "esophagus mucosa", "Esophagus - Mucosa", "esophagus"),
        ("左心室", "heart left ventricle", "Heart - Left Ventricle", "heart"),
        ("肾皮质", "kidney cortex", "Kidney - Cortex", "kidney"),
        ("回肠末端", "small intestine terminal ileum", "Small Intestine - Terminal Ileum", "small intestine"),
        ("黑质", "brain substantia nigra", "Brain - Substantia nigra", "brain"),
    ]

    for term, tissue, gtex, primary in cases:
        result = lookup_medical_terms(term)
        text = " ".join(result.tissue_terms).lower()

        assert tissue in text
        assert gtex in result.gtex_tissue_candidates
        assert primary in result.tcga_primary_site_candidates
        assert result.disease_terms_en == []


def test_tcga_primary_site_candidates_are_exposed_for_bioinformatics_only() -> None:
    bio = build_search_translation_draft(
        "甲状腺 RNA-seq",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "甲状腺疾病 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert bio.pubmed_query_candidates == []
    assert "Thyroid" in bio.audit.get("gtex_tissue_candidates", [])
    assert "thyroid" in bio.audit.get("tcga_primary_site_candidates", [])
    assert meta.geo_query_candidates == []
    assert meta.pubmed_query_candidates
    assert not meta.audit.get("gtex_tissue_candidates")
    assert not meta.audit.get("tcga_primary_site_candidates")


def test_tissue_terms_do_not_become_cancer_or_disease_concepts() -> None:
    forbidden_by_term = {
        "甲状腺": ["thyroid cancer", "ptc", "tcga-thca"],
        "thyroid": ["thyroid cancer", "ptc", "tcga-thca"],
        "肝脏": ["hepatocellular carcinoma", "hcc", "tcga-lihc"],
        "liver": ["hepatocellular carcinoma", "hcc", "tcga-lihc"],
        "肺": ["lung adenocarcinoma", "luad", "lung squamous cell carcinoma", "lusc", "tcga-luad", "tcga-lusc"],
        "lung": ["lung adenocarcinoma", "luad", "lung squamous cell carcinoma", "lusc", "tcga-luad", "tcga-lusc"],
        "脂肪组织": ["obesity"],
    }

    for term, forbidden_terms in forbidden_by_term.items():
        result = lookup_medical_terms(term)
        text = _lookup_text(term).lower()

        assert result.disease_terms_en == []
        for forbidden in forbidden_terms:
            assert forbidden not in text


def test_colon_rectum_and_colorectal_boundaries() -> None:
    colon = lookup_medical_terms("结肠")
    rectum = lookup_medical_terms("直肠")
    colorectal = lookup_medical_terms("结直肠")

    assert "colon" in colon.tcga_primary_site_candidates
    assert "rectum" not in colon.tcga_primary_site_candidates
    assert "rectum" in rectum.tcga_primary_site_candidates
    assert "colon" not in rectum.tcga_primary_site_candidates
    assert {"colon", "rectum"} <= set(colorectal.tcga_primary_site_candidates)
    assert colon.disease_terms_en == []
    assert rectum.disease_terms_en == []
    assert colorectal.disease_terms_en == []


def test_blood_bone_marrow_and_lymph_node_boundaries() -> None:
    blood = lookup_medical_terms("血液")
    marrow = lookup_medical_terms("骨髓")
    lymph_node = lookup_medical_terms("淋巴结")

    assert "blood" in blood.tcga_primary_site_candidates
    assert "bone marrow" not in blood.tcga_primary_site_candidates
    assert "lymph node" not in blood.tcga_primary_site_candidates
    assert "bone marrow" in marrow.tcga_primary_site_candidates
    assert "leukemia" not in _lookup_text("骨髓").lower()
    assert "lymph node" in lymph_node.tcga_primary_site_candidates
    assert "lymphoma" not in _lookup_text("淋巴结").lower()
    assert blood.disease_terms_en == []
    assert marrow.disease_terms_en == []
    assert lymph_node.disease_terms_en == []


def test_endocrine_short_tokens_do_not_match_tissue_core_terms() -> None:
    t3 = lookup_medical_terms("T3")
    stat3 = lookup_medical_terms("STAT3")
    t4 = lookup_medical_terms("T4")
    tsh = lookup_medical_terms("TSH")

    assert "triiodothyronine" in " ".join(t3.exposure_terms).lower()
    assert stat3.tissue_terms == []
    assert stat3.gtex_tissue_candidates == []
    assert "thyroxine" in " ".join(t4.exposure_terms).lower()
    assert "thyroid-stimulating hormone" in " ".join(tsh.exposure_terms)
