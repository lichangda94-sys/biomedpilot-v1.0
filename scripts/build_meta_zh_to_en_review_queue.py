#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from medical_terms_stage_pipeline import (
    CURATED_META_MAPPINGS,
    DOCS_MEDICAL_TERMS,
    MEDICAL_TERMS,
    TODAY,
    candidate_sort_key,
    curated_mapping_for,
    duplicate_normalized_terms,
    grouped_source_evidence,
    make_query_usage,
    read_jsonl,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Meta Chinese-to-English review queues.")
    parser.add_argument("--input", default=str(MEDICAL_TERMS / "external_candidates" / "meta" / "normalized_meta_zh_candidates.jsonl"))
    parser.add_argument("--output-dir", default=str(MEDICAL_TERMS / "review_queue"))
    args = parser.parse_args()

    rows = read_jsonl(Path(args.input))
    evidence_by_term = grouped_source_evidence(rows)
    duplicate_labels = duplicate_normalized_terms(rows)
    review_rows: list[dict[str, object]] = []
    needs_mapping: list[dict[str, object]] = []
    needs_disambiguation: list[dict[str, object]] = []
    conflicts: list[dict[str, object]] = []
    promotion: list[dict[str, object]] = []
    reviewed_terms: set[str] = set()

    for row in sorted(rows, key=candidate_sort_key):
        term = str(row["normalized_zh_term"])
        mapping = curated_mapping_for(term)
        if mapping:
            if term in reviewed_terms:
                continue
            reviewed_terms.add(term)
            concept_type = str(mapping["concept_type"])
            review = {
                "candidate_id": row["candidate_id"],
                "normalized_zh_term": term,
                "suggested_concept_type": concept_type,
                "suggested_pico_roles": list(mapping["pico_roles"]),
                "suggested_preferred_label_en": mapping["preferred_label_en"],
                "suggested_synonyms_en": list(mapping.get("synonyms_en", [])),
                "suggested_mesh_terms": list(mapping.get("mesh_terms", [])),
                "query_usage": make_query_usage(concept_type),
                "query_expansion_allowed": bool(mapping.get("query_expansion_allowed", concept_type not in {"effect_measure", "research_intent"})),
                "standalone_search_allowed": mapping.get("standalone_search_allowed", "conditional"),
                "requires_pairing_with": list(mapping.get("requires_pairing_with", [])),
                "review_status": "approved",
                "review_reason": "curated_high_confidence_stage_seed",
                "source_evidence": evidence_by_term.get(term, []),
            }
            review_rows.append(review)
            if concept_type in {"disease", "risk_factor"}:
                promotion.append(_promotion_candidate(term, mapping))
            continue
        suggested = "disease" if row.get("initial_source_label") == "disease" else "outcome"
        review = {
            "candidate_id": row["candidate_id"],
            "normalized_zh_term": term,
            "suggested_concept_type": suggested,
            "suggested_pico_roles": ["population", "disease"] if suggested == "disease" else ["outcome"],
            "suggested_preferred_label_en": "",
            "suggested_synonyms_en": [],
            "suggested_mesh_terms": [],
            "query_usage": make_query_usage(suggested),
            "query_expansion_allowed": False,
            "standalone_search_allowed": "conditional",
            "requires_pairing_with": ["population_or_disease"] if suggested != "disease" else [],
            "review_status": "pending",
            "review_reason": "auto_candidate_requires_human_review",
            "source_evidence": evidence_by_term.get(term, []),
        }
        review_rows.append(review)
        needs_mapping.append({**review, "reason_for_review": "English preferred label is not available from deterministic rules."})
        if row.get("initial_source_label") == "symptom":
            needs_disambiguation.append({**review, "reason_for_review": "Symptom-like term may be outcome, disease, or evidence-only context."})

    for term, labels in sorted(duplicate_labels.items()):
        conflicts.append(
            {
                "normalized_zh_term": term,
                "source_labels": sorted(labels),
                "review_status": "pending",
                "reason_for_review": "Same normalized term appears under multiple external source labels.",
            }
        )

    for term, mapping in sorted(CURATED_META_MAPPINGS.items()):
        if term in reviewed_terms:
            continue
        concept_type = str(mapping["concept_type"])
        review = {
            "candidate_id": f"meta_zh_seed:{term}",
            "normalized_zh_term": term,
            "suggested_concept_type": concept_type,
            "suggested_pico_roles": list(mapping["pico_roles"]),
            "suggested_preferred_label_en": mapping["preferred_label_en"],
            "suggested_synonyms_en": list(mapping.get("synonyms_en", [])),
            "suggested_mesh_terms": list(mapping.get("mesh_terms", [])),
            "query_usage": make_query_usage(concept_type),
            "query_expansion_allowed": bool(mapping.get("query_expansion_allowed", concept_type not in {"effect_measure", "research_intent"})),
            "standalone_search_allowed": mapping.get("standalone_search_allowed", "conditional"),
            "requires_pairing_with": list(mapping.get("requires_pairing_with", [])),
            "review_status": "approved",
            "review_reason": "curated_high_confidence_stage_seed_not_present_in_external_corpus",
            "source_evidence": [
                {
                    "source_file": "medical_terms_development_plan_for_codex.md",
                    "source_type": "stage_plan_rule_seed",
                    "raw_zh_term": term,
                }
            ],
        }
        review_rows.append(review)
        if concept_type in {"disease", "risk_factor"}:
            promotion.append(_promotion_candidate(term, mapping))

    out = Path(args.output_dir)
    write_jsonl(out / "meta" / "meta_zh_to_en_review_queue.jsonl", review_rows)
    write_jsonl(out / "meta" / "meta_needs_english_mapping.jsonl", needs_mapping)
    write_jsonl(out / "meta" / "meta_needs_disambiguation.jsonl", needs_disambiguation)
    write_jsonl(out / "meta" / "meta_mapping_conflicts.jsonl", conflicts)
    write_jsonl(out / "shared" / "shared_promotion_candidates_from_meta.jsonl", promotion)
    _write_reports(len(rows), review_rows, needs_mapping, needs_disambiguation, conflicts, promotion)
    print(f"wrote {len(review_rows)} Meta review queue rows")
    return 0


def _promotion_candidate(term: str, mapping: dict[str, object]) -> dict[str, object]:
    return {
        "normalized_zh_term": term,
        "suggested_preferred_label_en": mapping["preferred_label_en"],
        "suggested_concept_type": mapping["concept_type"],
        "source": "meta_runtime_seed",
        "review_status": "pending",
        "reason_for_review": "Potential shared-core term; requires human approval before promotion.",
    }


def _write_reports(
    normalized_count: int,
    review_rows: list[dict[str, object]],
    needs_mapping: list[dict[str, object]],
    needs_disambiguation: list[dict[str, object]],
    conflicts: list[dict[str, object]],
    promotion: list[dict[str, object]],
) -> None:
    approved_count = sum(1 for row in review_rows if row.get("review_status") == "approved")
    report = "\n".join(
        [
            "# Meta Chinese-To-English Candidate Report",
            "",
            f"Generated: {TODAY}",
            "",
            "## Counts",
            "",
            f"- normalized_candidates: {normalized_count}",
            f"- review_queue_rows: {len(review_rows)}",
            f"- approved_runtime_seed_rows: {approved_count}",
            f"- needs_english_mapping: {len(needs_mapping)}",
            f"- needs_disambiguation: {len(needs_disambiguation)}",
            f"- mapping_conflicts: {len(conflicts)}",
            f"- shared_promotion_candidates: {len(promotion)}",
            "",
            "## Scope",
            "",
            "Chinese corpus terms are used for Chinese input understanding, English database query drafting, and English PDF extraction targets. They are not used for Chinese database retrieval or Chinese full-text extraction.",
            "",
            "## Runtime Policy",
            "",
            "Only curated high-confidence seed rows enter Meta-specific runtime in this stage. External corpus rows without deterministic English mapping remain pending for human review.",
            "",
        ]
    )
    review_dir = MEDICAL_TERMS / "review_reports"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "meta_zh_to_en_candidate_report.md").write_text(report, encoding="utf-8")

    DOCS_MEDICAL_TERMS.mkdir(parents=True, exist_ok=True)
    manual = "\n".join(
        [
            "# Manual Review Required Report",
            "",
            f"Generated: {TODAY}",
            "",
            "## Required Review Counts",
            "",
            f"- needs_english_mapping: {len(needs_mapping)}",
            f"- needs_disambiguation: {len(needs_disambiguation)}",
            f"- mapping_conflicts: {len(conflicts)}",
            f"- shared_promotion_candidates: {len(promotion)}",
            "",
            "## Files",
            "",
            "- data/medical_terms/review_queue/meta/meta_needs_english_mapping.jsonl",
            "- data/medical_terms/review_queue/meta/meta_needs_disambiguation.jsonl",
            "- data/medical_terms/review_queue/meta/meta_mapping_conflicts.jsonl",
            "- data/medical_terms/review_queue/shared/shared_promotion_candidates_from_meta.jsonl",
            "",
            "## Reason",
            "",
            "Most external corpus terms do not carry reliable English preferred labels, MeSH/Emtree candidates, or unambiguous PICO roles. They remain pending and are not written to shared core.",
            "",
        ]
    )
    (DOCS_MEDICAL_TERMS / "manual_review_required_report.md").write_text(manual, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
