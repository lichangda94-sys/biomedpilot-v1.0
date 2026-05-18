from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"
REVIEW_BATCHES = MEDICAL_TERMS / "review_batches"


def _json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_review_batch_outputs_do_not_touch_shared_core() -> None:
    mini = MEDICAL_TERMS / "mini_medical_terms_index.json"
    zh = MEDICAL_TERMS / "zh_term_overrides.json"
    before = (_sha256(mini), _sha256(zh))

    assert (_sha256(mini), _sha256(zh)) == before


def test_bioinformatics_review_batches_are_loadable() -> None:
    geo = _jsonl(REVIEW_BATCHES / "bioinformatics" / "geo_core_missing_review_batch.jsonl")
    gtex = _jsonl(REVIEW_BATCHES / "bioinformatics" / "gtex_needs_review_batch.jsonl")
    summary = _json(REVIEW_BATCHES / "bioinformatics" / "bioinformatics_review_batch_summary.json")

    assert len(gtex) == 5
    assert len(geo) == summary["geo_missing_total"]  # type: ignore[index]
    assert summary["gtex_needs_review_total"] == 5  # type: ignore[index]
    assert {row["audit_status"] for row in geo} <= {"missing"}
    assert {row["audit_status"] for row in gtex} == {"needs_review"}
    assert all(row["shared_core_allowed"] is False for row in geo)
    assert all(row["manual_review_required"] is True for row in gtex)


def test_meta_review_batches_are_loadable_and_scoped() -> None:
    approved = _jsonl(REVIEW_BATCHES / "meta" / "meta_approved_runtime_review_batch.jsonl")
    promotion = _jsonl(REVIEW_BATCHES / "meta" / "meta_shared_promotion_review_batch.jsonl")
    priority = _jsonl(REVIEW_BATCHES / "meta" / "meta_priority_review_batch_top_300.jsonl")
    conflicts = _jsonl(REVIEW_BATCHES / "meta" / "meta_mapping_conflicts_top_200.jsonl")
    disambiguation = _jsonl(REVIEW_BATCHES / "meta" / "meta_disambiguation_top_200.jsonl")
    english = _jsonl(REVIEW_BATCHES / "meta" / "meta_english_mapping_top_300.jsonl")
    auto_reject = _jsonl(REVIEW_BATCHES / "meta" / "meta_auto_reject_candidates.jsonl")
    evidence = _jsonl(REVIEW_BATCHES / "meta" / "meta_evidence_only_candidates_optimized.jsonl")
    future = _jsonl(REVIEW_BATCHES / "meta" / "meta_future_scope_candidates_optimized.jsonl")
    summary = _json(REVIEW_BATCHES / "meta" / "meta_review_batch_summary.json")

    assert len(approved) == 11
    assert len(promotion) == 4
    assert len(priority) == 300
    assert len(conflicts) == 200
    assert len(disambiguation) == 200
    assert len(english) == 300
    assert summary["approved_runtime_total"] == 11  # type: ignore[index]
    assert summary["shared_promotion_total"] == 4  # type: ignore[index]
    assert summary["auto_reject_total"] == len(auto_reject)  # type: ignore[index]
    assert summary["evidence_only_optimized_total"] == len(evidence)  # type: ignore[index]
    assert summary["future_scope_optimized_total"] == len(future)  # type: ignore[index]

    for row in approved:
        usage = row["query_usage"]
        assert usage["chinese_database_search"] is False  # type: ignore[index]
        assert usage["chinese_pdf_extraction"] is False  # type: ignore[index]
        assert "Check English mapping" in row["review_focus"]
        assert row["synonyms_en"] is not None
        assert row["mesh_terms"] is not None
        assert row["emtree_terms"] is not None
        assert "query_expansion_guard" in row

    by_zh = {row["zh_terms"][0]: row for row in approved}  # type: ignore[index]
    for term in ["乳腺癌", "甲状腺癌", "2型糖尿病"]:
        assert by_zh[term]["review_status"] == "approved_runtime_ok"
        assert by_zh[term]["shared_promotion_decision"] == "align_existing_shared_concept"
        assert str(by_zh[term]["existing_shared_concept_id"]).startswith("mini:")
    assert by_zh["肥胖"]["review_status"] == "needs_type_fix"
    assert by_zh["肥胖"]["shared_promotion_decision"] == "blocked_from_shared_promotion"
    assert "BMI" not in by_zh["肥胖"]["synonyms_en"]
    assert "body mass index" not in by_zh["肥胖"]["synonyms_en"]
    assert "overweight" not in by_zh["肥胖"]["synonyms_en"]
    assert by_zh["糖尿病前期"]["concept_type"] == "phenotype_risk_state"
    assert by_zh["糖尿病前期"]["pico_roles"] == ["exposure"]
    assert by_zh["复发"]["review_status"] == "needs_expansion_guard"
    assert by_zh["复发"]["query_expansion_allowed"] == "conditional"
    assert by_zh["复发"]["standalone_search_allowed"] is False
    assert by_zh["风险"]["query_expansion_allowed"] is False
    assert by_zh["危险因素"]["query_expansion_allowed"] is False
    assert by_zh["Meta分析"]["query_expansion_guard"]["mode"] == "filter_only"
    assert by_zh["Meta分析"]["query_expansion_allowed"] is False

    promotion_by_term = {row["term"]: row for row in promotion}
    for term in ["2型糖尿病", "乳腺癌", "甲状腺癌"]:
        assert promotion_by_term[term]["promotion_allowed"] == "align_existing_shared_concept"
        assert promotion_by_term[term]["shared_core_write_allowed"] is False
        assert str(promotion_by_term[term]["target_shared_concept_id"]).startswith("mini:")
    assert promotion_by_term["肥胖"]["promotion_allowed"] == "blocked_from_shared_promotion"
    assert promotion_by_term["肥胖"]["shared_core_write_allowed"] is False
    assert all("priority_score" in row for row in priority)
    assert all(row["recommended_status"] == "rejected" for row in auto_reject)


def test_discussion_reports_exist() -> None:
    discussion = REVIEW_BATCHES / "reports" / "vocabulary_review_batches_for_discussion.md"
    optimization = REVIEW_BATCHES / "reports" / "meta_candidate_optimization_report.md"
    correction = REVIEW_BATCHES / "reports" / "meta_runtime_seed_correction_report.md"

    assert "GEO core missing" in discussion.read_text(encoding="utf-8")
    assert "Meta approved runtime 11" in discussion.read_text(encoding="utf-8")
    assert "Top Batch Files" in optimization.read_text(encoding="utf-8")
    assert "blocked_from_shared_promotion" in correction.read_text(encoding="utf-8")
