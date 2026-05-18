from __future__ import annotations

import json
from pathlib import Path

from app.shared.query_intelligence.medical_terms import lookup_medical_terms


ROOT = Path(__file__).resolve().parents[2]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"


def _json(path: str) -> object:
    return json.loads((MEDICAL_TERMS / path).read_text(encoding="utf-8"))


def _jsonl(path: str) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in (MEDICAL_TERMS / path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_bioinformatics_audit_outputs_cover_required_scopes() -> None:
    tcga = _json("bioinformatics/audits/tcga_terms_coverage_audit.json")
    gtex = _json("bioinformatics/audits/gtex_terms_coverage_audit.json")
    geo = _json("bioinformatics/audits/geo_core_terms_coverage_audit.json")

    tcga_codes = {item["project_code"] for item in tcga["items"]}  # type: ignore[index]
    assert len(tcga_codes) == 33
    assert {"TCGA-BRCA", "TCGA-GBM", "TCGA-THCA"} <= tcga_codes
    assert set(item["status"] for item in tcga["items"]) <= {"complete", "partial", "missing", "needs_review"}  # type: ignore[index]

    gtex_tissues = {item["gtex_tissue"] for item in gtex["items"]}  # type: ignore[index]
    assert {"Thyroid", "Whole Blood", "Adipose Tissue", "Adrenal Gland"} <= gtex_tissues
    assert gtex["summary"]["needs_review"] == 0  # type: ignore[index]
    assert gtex["summary"]["approved_with_subtype_mapping"] == 3  # type: ignore[index]
    assert gtex["summary"]["complete_with_note"] == 2  # type: ignore[index]

    geo_categories = {item["category"] for item in geo["items"]}  # type: ignore[index]
    assert {"omics_assay", "species", "sample_status", "data_format", "platform_term", "stop_term"} <= geo_categories
    assert set(item["status"] for item in geo["items"]) <= {"complete", "partial", "missing", "needs_review", "approved-with-note"}  # type: ignore[index]
    assert geo["summary"]["missing"] == 0  # type: ignore[index]
    assert geo["scope_note"].startswith("Core GEO term audit only")  # type: ignore[index]


def test_meta_candidate_pipeline_outputs_are_loadable_and_scoped() -> None:
    raw = _jsonl("external_candidates/meta/raw_meta_zh_candidates.jsonl")
    normalized = _jsonl("external_candidates/meta/normalized_meta_zh_candidates.jsonl")
    rejected = _jsonl("external_candidates/meta/rejected_meta_zh_candidates.jsonl")
    evidence_only = _jsonl("external_candidates/meta/evidence_only_meta_zh_candidates.jsonl")
    future_scope = _jsonl("external_candidates/meta/future_scope_meta_zh_candidates.jsonl")
    review = _jsonl("review_queue/meta/meta_zh_to_en_review_queue.jsonl")

    assert len(raw) > len(normalized) > 0
    assert rejected
    assert evidence_only
    assert future_scope
    assert len(review) >= len(normalized)

    raw_required = {"candidate_id", "raw_zh_term", "source_file", "source_type", "line_no", "source_license_status"}
    normalized_required = raw_required | {"normalized_zh_term", "normalization_actions", "review_status"}
    review_required = {
        "candidate_id",
        "normalized_zh_term",
        "suggested_concept_type",
        "suggested_pico_roles",
        "query_usage",
        "review_status",
    }
    assert raw_required <= raw[0].keys()
    assert normalized_required <= normalized[0].keys()
    assert review_required <= review[0].keys()

    for row in review:
        query_usage = row["query_usage"]
        assert query_usage["chinese_database_search"] is False  # type: ignore[index]
        assert query_usage["chinese_pdf_extraction"] is False  # type: ignore[index]
        assert row["review_status"] in {"approved", "pending", "rejected", "evidence_only", "future_scope"}


def test_meta_runtime_seed_entries_follow_runtime_rules() -> None:
    entries = _json("meta_analysis/meta_zh_to_en_concept_terms.json")
    concept_ids = [entry["concept_id"] for entry in entries]  # type: ignore[index]
    by_zh = {entry["zh_terms"][0]: entry for entry in entries}  # type: ignore[index]

    assert len(concept_ids) == len(set(concept_ids))
    assert {"糖尿病前期", "甲状腺癌", "放射性碘治疗", "二甲双胍", "肥胖", "乳腺癌"} <= set(by_zh)
    for entry in entries:  # type: ignore[assignment]
        assert entry["review_status"] in {"approved", "approved_runtime_ok", "needs_type_fix", "needs_expansion_guard"}
        assert entry["preferred_label_en"]
        assert entry["concept_type"]
        assert entry["query_usage"]["chinese_database_search"] is False
        assert entry["query_usage"]["chinese_pdf_extraction"] is False
        if entry["concept_type"] in {"effect_measure", "research_intent"}:
            assert entry["query_expansion_allowed"] is False
        if entry["concept_type"] == "outcome":
            assert entry["query_expansion_allowed"] != True
            assert entry["standalone_search_allowed"] is False
            assert entry["query_expansion_guard"]["mode"] == "requires_population_or_disease_context"

    assert by_zh["肥胖"]["review_status"] == "needs_type_fix"
    assert by_zh["肥胖"]["shared_promotion_decision"] == "blocked_from_shared_promotion"
    assert "BMI" not in by_zh["肥胖"]["synonyms_en"]
    assert "body mass index" not in by_zh["肥胖"]["synonyms_en"]
    assert "overweight" not in by_zh["肥胖"]["synonyms_en"]
    assert by_zh["肥胖"]["measurement_terms_en"] == ["BMI", "body mass index"]
    assert by_zh["肥胖"]["related_terms_en"] == ["overweight"]
    assert by_zh["糖尿病前期"]["concept_type"] == "phenotype_risk_state"
    assert by_zh["糖尿病前期"]["pico_roles"] == ["exposure"]
    assert by_zh["复发"]["review_status"] == "needs_expansion_guard"
    assert by_zh["复发"]["query_expansion_allowed"] == "conditional"
    assert by_zh["复发"]["standalone_search_allowed"] is False
    assert by_zh["风险"]["query_expansion_allowed"] is False
    assert by_zh["危险因素"]["query_expansion_allowed"] is False
    assert by_zh["Meta分析"]["query_expansion_allowed"] is False
    assert by_zh["Meta分析"]["query_expansion_guard"]["mode"] == "filter_only"


def test_stage_scope_isolation_guards_remain_effective() -> None:
    for term in ["总生存期", "无进展生存期", "HR", "OR", "队列研究", "随机对照试验", "危险因素", "诊断价值"]:
        result = lookup_medical_terms(term, target_context="bioinformatics")
        assert result.outcome_terms == []
        assert result.effect_measures == []
        assert result.study_design_terms == []

    for term in ["GSE", "GSM", "GPL", "TPM", "FPKM", "raw counts", "probe ID", "series matrix", "sample metadata"]:
        result = lookup_medical_terms(term, target_context="meta_analysis")
        assert result.disease_terms_en == []
        assert result.pico_terms == []


def test_chinese_input_examples_have_expected_meta_runtime_terms() -> None:
    entries = _json("meta_analysis/meta_zh_to_en_concept_terms.json")
    term_text = json.dumps(entries, ensure_ascii=False)
    for expected in ["糖尿病前期", "甲状腺癌", "risk", "放射性碘治疗", "recurrence", "二甲双胍", "2型糖尿病", "肥胖", "乳腺癌", "meta-analysis"]:
        assert expected in term_text
