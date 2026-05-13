from __future__ import annotations

import json
from pathlib import Path

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report


ROOT = Path(__file__).resolve().parents[2]
CHECKLIST_PATH = ROOT / "data" / "medical_terms" / "reference_checklists" / "bioinformatics_modality_core_checklist.json"


def _lookup_text(term: str, *, target_context: str = "bioinformatics") -> str:
    result = lookup_medical_terms(term, target_context=target_context)
    return " ".join(
        [
            *result.disease_terms_en,
            *result.tissue_terms,
            *result.data_modality_terms,
            *result.assay_terms,
            *result.platform_candidates,
            *result.synonyms_en,
            *result.abbreviations,
        ]
    )


def test_bioinformatics_modality_checklist_has_systematic_scope() -> None:
    payload = json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))
    subcategories = {item["subcategory"] for item in payload["items"]}
    ambiguity_terms = {item["term"] for item in payload["ambiguity_terms"]}

    assert payload["coverage_type"] == "bioinformatics_modality_core"
    assert len(payload["items"]) >= 60
    assert {
        "transcriptomics",
        "noncoding_rna",
        "epigenomics",
        "genomics",
        "single_cell_multiomics",
        "proteomics_metabolomics",
        "functional_genomics",
        "clinical_phenotypic_omics",
    } <= subcategories
    assert {"RNA-seq", "scRNA-seq", "ATAC-seq", "ChIP-seq", "WGS", "WES", "proteomics", "metabolomics", "测序"} <= ambiguity_terms


def test_bioinformatics_modality_coverage_audit_is_complete() -> None:
    report = build_coverage_audit_report()
    section = report["sections"]["bioinformatics_modality_core"]
    gates = {gate["gate_id"]: gate for gate in report["quality_gates"]["gates"]}

    assert section["total_checklist_items"] >= 60
    assert section["covered"] == section["total_checklist_items"]
    assert section["missing"] == 0
    assert section["coverage_rate"] == 1.0
    assert section["missing_terms"] == []
    assert gates["bioinformatics_modality_core_coverage"]["status"] == "pass"
    assert gates["bioinformatics_modality_missing_terms"]["observed"] == 0


def test_chinese_modality_aliases_positive_lookup() -> None:
    cases = [
        ("单细胞", "single-cell RNA-seq", "scRNA-seq"),
        ("空间转录组", "spatial transcriptomics", ""),
        ("甲基化", "methylation profiling", ""),
        ("全外显子", "whole exome sequencing", "WES"),
        ("全基因组", "whole genome sequencing", "WGS"),
        ("芯片", "microarray", ""),
        ("表达谱", "expression profiling", ""),
        ("蛋白组", "proteomics", ""),
        ("代谢组", "metabolomics", ""),
    ]

    for query, modality, abbreviation in cases:
        result = lookup_medical_terms(query)
        text = _lookup_text(query).lower()

        assert modality.lower() in text
        assert result.disease_terms_en == []
        assert result.tissue_terms == []
        if abbreviation:
            assert abbreviation in result.abbreviations or abbreviation.lower() in text


def test_abbreviation_positive_lookup_is_data_modality_only() -> None:
    cases = {
        "RNA-seq": "RNA-seq",
        "scRNA-seq": "single-cell RNA-seq",
        "ATAC-seq": "ATAC-seq",
        "ChIP-seq": "ChIP-seq",
        "WGS": "whole genome sequencing",
        "WES": "whole exome sequencing",
        "CNV": "copy number variation",
    }

    for query, expected in cases.items():
        result = lookup_medical_terms(query)
        text = _lookup_text(query).lower()

        assert expected.lower() in text
        assert result.disease_terms_en == []
        assert result.tissue_terms == []
        assert result.data_modality_terms


def test_broad_and_specific_assay_boundaries() -> None:
    sequencing = lookup_medical_terms("测序")
    scrna = _lookup_text("scRNA-seq").lower()
    atac = _lookup_text("ATAC-seq").lower()
    wgs = _lookup_text("WGS").lower()
    proteomics = _lookup_text("proteomics").lower()

    assert sequencing.disease_terms_en == []
    assert "sequencing" in " ".join(sequencing.data_modality_terms).lower()
    assert "rna-seq" not in " ".join(sequencing.data_modality_terms).lower()
    assert "whole genome sequencing" not in " ".join(sequencing.data_modality_terms).lower()
    assert "whole exome sequencing" not in " ".join(sequencing.data_modality_terms).lower()
    assert "bulk rna-seq" not in scrna
    assert "chip-seq" not in atac
    assert "whole exome sequencing" not in wgs
    assert "metabolomics" not in proteomics


def test_bioinformatics_and_meta_context_isolation_for_modalities() -> None:
    bio = build_search_translation_draft(
        "肺腺癌 RNA-seq 数据集",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "RNA-seq 与预后 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert bio.pubmed_query_candidates == []
    assert "RNA-seq" in bio.data_type_terms_en
    assert "RNA-seq" in bio.audit["term_lookup"].get("data_modality_terms", [])
    assert "RNA-seq" in bio.audit.get("assay_terms", [])
    assert {"GEO", "SRA"} & set(bio.audit.get("platform_candidates", []))
    assert meta.geo_query_candidates == []
    assert "tcga" not in " ".join(meta.pubmed_query_candidates).lower()
    assert "gtex" not in " ".join(meta.pubmed_query_candidates).lower()
    assert "geo" not in " ".join(meta.pubmed_query_candidates).lower()
    assert "RNA-seq" in meta.audit["term_lookup"].get("data_modality_terms", [])
    assert not meta.audit.get("platform_candidates")
    assert "platform_candidates" not in meta.audit["term_lookup"]
