from __future__ import annotations

import json
from pathlib import Path

from app.shared.query_intelligence import build_search_translation_draft
from app.shared.query_intelligence.medical_terms import lookup_medical_terms
from scripts.audit_medical_vocabulary_coverage import build_coverage_audit_report


ROOT = Path(__file__).resolve().parents[2]
ONCOLOGY_CHECKLIST = ROOT / "data" / "medical_terms" / "reference_checklists" / "oncology_core_checklist.json"


def _lookup_text(term: str, *, target_context: str = "bioinformatics") -> str:
    result = lookup_medical_terms(term, target_context=target_context)
    return " ".join(
        [
            *result.disease_terms_en,
            *result.synonyms_en,
            *result.abbreviations,
            *result.mesh_terms,
            *result.tissue_terms,
            *result.tcga_project_candidates,
            *result.gtex_tissue_candidates,
            *result.data_modality_terms,
        ]
    )


def test_oncology_core_checklist_has_systematic_scope() -> None:
    payload = json.loads(ONCOLOGY_CHECKLIST.read_text(encoding="utf-8"))
    tcga_projects = {project for item in payload["items"] for project in item.get("expected_tcga_projects", [])}
    ambiguity_terms = {item["term"] for item in payload["ambiguity_terms"]}

    assert payload["coverage_type"] == "oncology_core"
    assert len(payload["items"]) >= 65
    assert len(tcga_projects) == 33
    assert {"SCC", "RCC", "PTC", "CRC", "MM"} <= ambiguity_terms


def test_oncology_core_audit_reports_full_tcga_coverage() -> None:
    report = build_coverage_audit_report()
    oncology = report["sections"]["oncology_core"]
    tcga = oncology["tcga_project_coverage"]

    assert oncology["total_checklist_items"] >= 65
    assert oncology["missing"] == 0
    assert oncology["coverage_rate"] >= 0.95
    assert tcga["expected_count"] == 33
    assert tcga["covered_count"] == 33
    assert tcga["missing_projects"] == []


def test_high_value_chinese_oncology_terms_map_to_tcga_and_gtex() -> None:
    cases = [
        ("滤泡性甲状腺癌", "follicular thyroid carcinoma", "TCGA-THCA", "Thyroid"),
        ("髓样甲状腺癌", "medullary thyroid carcinoma", "TCGA-THCA", "Thyroid"),
        ("肾嫌色细胞癌", "kidney chromophobe carcinoma", "TCGA-KICH", "Kidney"),
        ("膀胱尿路上皮癌", "bladder urothelial carcinoma", "TCGA-BLCA", "Bladder"),
        ("急性淋巴细胞白血病", "acute lymphoblastic leukemia", "", "Whole Blood"),
        ("多发性骨髓瘤", "multiple myeloma", "", "Whole Blood"),
    ]

    for term, expected_disease, expected_tcga, expected_gtex in cases:
        result = lookup_medical_terms(term)
        text = _lookup_text(term).lower()

        assert expected_disease in text
        if expected_tcga:
            assert expected_tcga in result.tcga_project_candidates
        assert expected_gtex in result.gtex_tissue_candidates


def test_oncology_context_outputs_are_isolated_between_bioinformatics_and_meta_analysis() -> None:
    bio = build_search_translation_draft(
        "肺腺癌转录组",
        target_context="bioinformatics",
        target_database="geo",
    )
    meta = build_search_translation_draft(
        "肺腺癌总生存 Meta 分析",
        target_context="meta_analysis",
        target_database="pubmed",
    )

    assert bio.pubmed_query_candidates == []
    assert bio.geo_query_candidates
    assert "TCGA-LUAD" in bio.audit.get("tcga_project_candidates", [])
    assert "Lung" in bio.audit.get("gtex_tissue_candidates", [])
    assert meta.geo_query_candidates == []
    assert meta.pubmed_query_candidates
    assert not meta.audit.get("tcga_project_candidates")
    assert not meta.audit.get("gtex_tissue_candidates")
    assert "tcga" not in " ".join(meta.database_terms).lower()
    assert "gtex" not in " ".join(meta.database_terms).lower()
    assert "geo" not in " ".join(meta.database_terms).lower()


def test_escc_and_ptc_do_not_cross_leak() -> None:
    escc_text = _lookup_text("食管鳞癌").lower()
    ptc_text = _lookup_text("PTC").lower()
    thyroid_text = _lookup_text("甲状腺癌").lower()

    assert "esophageal squamous cell carcinoma" in escc_text
    assert "thyroid" not in escc_text
    assert "tcga-thca" not in escc_text
    assert "papillary thyroid carcinoma" in ptc_text
    assert "tcga-thca" in ptc_text
    assert "escc" not in ptc_text
    assert "esophageal" not in thyroid_text


def test_lung_subtypes_do_not_cross_expand_without_parent_context() -> None:
    luad = lookup_medical_terms("LUAD")
    lusc = lookup_medical_terms("LUSC")
    lung_cancer = lookup_medical_terms("lung cancer")

    assert "TCGA-LUAD" in luad.tcga_project_candidates
    assert "TCGA-LUSC" not in luad.tcga_project_candidates
    assert "Alzheimer Disease" not in luad.disease_terms_en
    assert "TCGA-LUSC" in lusc.tcga_project_candidates
    assert "TCGA-LUAD" not in lusc.tcga_project_candidates
    assert {"TCGA-LUAD", "TCGA-LUSC"} <= set(lung_cancer.tcga_project_candidates)


def test_digestive_and_brain_subtypes_do_not_over_expand() -> None:
    hcc = lookup_medical_terms("HCC")
    colon = lookup_medical_terms("结肠癌")
    rectal = lookup_medical_terms("直肠癌")
    colorectal = lookup_medical_terms("结直肠癌")
    gbm = lookup_medical_terms("GBM")

    assert "TCGA-LIHC" in hcc.tcga_project_candidates
    assert "TCGA-CHOL" not in hcc.tcga_project_candidates
    assert "TCGA-COAD" in colon.tcga_project_candidates
    assert "TCGA-READ" not in colon.tcga_project_candidates
    assert "TCGA-READ" in rectal.tcga_project_candidates
    assert "TCGA-COAD" not in rectal.tcga_project_candidates
    assert {"TCGA-COAD", "TCGA-READ"} <= set(colorectal.tcga_project_candidates)
    assert "TCGA-GBM" in gbm.tcga_project_candidates
    assert "TCGA-LGG" not in gbm.tcga_project_candidates


def test_rcc_subtypes_and_scc_ambiguity_are_guarded() -> None:
    rcc = lookup_medical_terms("RCC")
    clear_cell = lookup_medical_terms("clear cell RCC")
    papillary = lookup_medical_terms("papillary RCC")
    chromophobe = lookup_medical_terms("chromophobe RCC")
    scc = lookup_medical_terms("SCC")
    read_count = lookup_medical_terms("read count")

    assert not rcc.tcga_project_candidates
    assert any("歧义" in warning for warning in rcc.warnings)
    assert "TCGA-KIRC" in clear_cell.tcga_project_candidates
    assert "TCGA-KIRP" not in clear_cell.tcga_project_candidates
    assert "TCGA-KICH" not in clear_cell.tcga_project_candidates
    assert "TCGA-KIRP" in papillary.tcga_project_candidates
    assert "TCGA-KICH" in chromophobe.tcga_project_candidates
    assert not scc.disease_terms_en
    assert not scc.tcga_project_candidates
    assert any("歧义" in warning for warning in scc.warnings)
    assert "TCGA-READ" not in read_count.tcga_project_candidates
