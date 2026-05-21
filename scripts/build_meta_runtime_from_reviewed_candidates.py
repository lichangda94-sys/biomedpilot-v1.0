#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from medical_terms_stage_pipeline import MEDICAL_TERMS, meta_runtime_entry, read_jsonl, write_json


RUNTIME_FILES = {
    "all": "meta_zh_to_en_concept_terms.json",
    "pico": "meta_en_pico_terms.json",
    "outcome": "meta_en_outcome_terms.json",
    "effect_measure": "meta_en_effect_measure_terms.json",
    "study_design": "meta_en_study_design_terms.json",
    "research_intent": "meta_research_intent_terms.json",
    "pdf_extraction": "meta_en_pdf_extraction_terms.json",
    "stop": "meta_stop_terms.json",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Meta-specific runtime JSON from approved review queue rows.")
    parser.add_argument("--input", default=str(MEDICAL_TERMS / "review_queue" / "meta" / "meta_zh_to_en_review_queue.jsonl"))
    parser.add_argument("--output-dir", default=str(MEDICAL_TERMS / "meta_analysis"))
    args = parser.parse_args()

    entries = []
    for row in read_jsonl(Path(args.input)):
        if row.get("review_status") != "approved":
            continue
        mapping = {
            "concept_id": _concept_id(row),
            "preferred_label_en": row["suggested_preferred_label_en"],
            "synonyms_en": row.get("suggested_synonyms_en", []),
            "mesh_terms": row.get("suggested_mesh_terms", []),
            "concept_type": row["suggested_concept_type"],
            "pico_roles": row["suggested_pico_roles"],
            "standalone_search_allowed": row["standalone_search_allowed"],
            "requires_pairing_with": row.get("requires_pairing_with", []),
            "query_expansion_allowed": row.get("query_expansion_allowed", True),
        }
        entries.append(meta_runtime_entry(str(row["normalized_zh_term"]), mapping, list(row.get("source_evidence", []))))

    entries.sort(key=lambda item: item["concept_id"])
    output_dir = Path(args.output_dir)
    write_json(output_dir / RUNTIME_FILES["all"], entries)
    by_type: dict[str, list[dict[str, object]]] = defaultdict(list)
    for entry in entries:
        by_type[str(entry["concept_type"])].append(entry)
    pico_entries = [entry for entry in entries if entry["concept_type"] in {"disease", "exposure", "risk_factor", "intervention"}]
    write_json(output_dir / RUNTIME_FILES["pico"], pico_entries)
    write_json(output_dir / RUNTIME_FILES["outcome"], by_type.get("outcome", []))
    write_json(output_dir / RUNTIME_FILES["effect_measure"], by_type.get("effect_measure", []))
    write_json(output_dir / RUNTIME_FILES["study_design"], by_type.get("study_design", []))
    write_json(output_dir / RUNTIME_FILES["research_intent"], by_type.get("research_intent", []))
    write_json(output_dir / RUNTIME_FILES["pdf_extraction"], [entry for entry in entries if entry["query_usage"]["english_pdf_extraction"]])
    write_json(output_dir / RUNTIME_FILES["stop"], [])
    print(f"wrote {len(entries)} approved Meta runtime entries")
    return 0


def _concept_id(row: dict[str, object]) -> str:
    preferred = str(row["suggested_preferred_label_en"]).lower().replace(" ", "_").replace("-", "_")
    prefix = str(row["suggested_concept_type"])
    if prefix == "risk_factor":
        prefix = "exposure"
    return f"meta_{prefix}:{preferred}"


if __name__ == "__main__":
    raise SystemExit(main())
