#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from medical_terms_stage_pipeline import (
    MEDICAL_TERMS,
    classification_for_term,
    normalize_zh_candidate,
    read_jsonl,
    split_parenthetical_alias,
    write_jsonl,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize and partition Meta Chinese term candidates.")
    parser.add_argument("--input", default=str(MEDICAL_TERMS / "external_candidates" / "meta" / "raw_meta_zh_candidates.jsonl"))
    parser.add_argument("--output-dir", default=str(MEDICAL_TERMS / "external_candidates" / "meta"))
    args = parser.parse_args()

    normalized_rows: list[dict[str, object]] = []
    rejected_rows: list[dict[str, object]] = []
    evidence_rows: list[dict[str, object]] = []
    future_rows: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in read_jsonl(Path(args.input)):
        base, aliases = split_parenthetical_alias(str(row["raw_zh_term"]))
        for index, term in enumerate([base, *aliases]):
            normalized, actions = normalize_zh_candidate(term)
            status, reason = classification_for_term(normalized, str(row["source_type"]), str(row["initial_source_label"]))
            candidate = {
                **row,
                "candidate_id": row["candidate_id"] if index == 0 else f"{row['candidate_id']}:alias{index}",
                "raw_zh_term": term,
                "normalized_zh_term": normalized,
                "normalization_actions": actions + (["split_parenthetical_alias"] if aliases else []),
                "review_status": "pending",
                "partition_reason": reason,
            }
            key = (normalized, str(row["source_type"]))
            if status == "normalized":
                if key in seen:
                    continue
                seen.add(key)
                normalized_rows.append(candidate)
            elif status == "rejected":
                rejected_rows.append({**candidate, "review_status": "rejected"})
            elif status == "evidence_only":
                evidence_rows.append({**candidate, "review_status": "evidence_only"})
            else:
                future_rows.append({**candidate, "review_status": "future_scope"})

    output_dir = Path(args.output_dir)
    write_jsonl(output_dir / "normalized_meta_zh_candidates.jsonl", sorted(normalized_rows, key=lambda item: str(item["normalized_zh_term"])))
    write_jsonl(output_dir / "rejected_meta_zh_candidates.jsonl", sorted(rejected_rows, key=lambda item: str(item["normalized_zh_term"])))
    write_jsonl(output_dir / "evidence_only_meta_zh_candidates.jsonl", sorted(evidence_rows, key=lambda item: str(item["normalized_zh_term"])))
    write_jsonl(output_dir / "future_scope_meta_zh_candidates.jsonl", sorted(future_rows, key=lambda item: str(item["normalized_zh_term"])))
    print(f"wrote {len(normalized_rows)} normalized Meta Chinese candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
