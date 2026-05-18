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

    assert all(row["promotion_allowed"] == "manual_review_only" for row in promotion)
    assert all("priority_score" in row for row in priority)
    assert all(row["recommended_status"] == "rejected" for row in auto_reject)


def test_discussion_reports_exist() -> None:
    discussion = REVIEW_BATCHES / "reports" / "vocabulary_review_batches_for_discussion.md"
    optimization = REVIEW_BATCHES / "reports" / "meta_candidate_optimization_report.md"

    assert "GEO core missing" in discussion.read_text(encoding="utf-8")
    assert "Meta approved runtime 11" in discussion.read_text(encoding="utf-8")
    assert "Top Batch Files" in optimization.read_text(encoding="utf-8")
