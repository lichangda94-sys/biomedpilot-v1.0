#!/usr/bin/env python3
from __future__ import annotations

import argparse

from medical_terms_stage_pipeline import DEFAULT_EXTERNAL_CORPUS, MEDICAL_TERMS, SOURCE_FILES, TODAY, clean_source_line, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description="Import external Chinese medical corpus terms as tracked Meta candidates.")
    parser.add_argument("--corpus-root", default=str(DEFAULT_EXTERNAL_CORPUS))
    parser.add_argument("--output", default=str(MEDICAL_TERMS / "external_candidates" / "meta" / "raw_meta_zh_candidates.jsonl"))
    args = parser.parse_args()

    corpus_root = DEFAULT_EXTERNAL_CORPUS if args.corpus_root == str(DEFAULT_EXTERNAL_CORPUS) else __import__("pathlib").Path(args.corpus_root)
    rows: list[dict[str, object]] = []
    next_id = 1
    for filename, source_type, source_label in SOURCE_FILES:
        path = corpus_root / filename
        if not path.exists():
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            raw = clean_source_line(line, source_type)
            if not raw:
                continue
            rows.append(
                {
                    "candidate_id": f"meta_zh_candidate:{next_id:06d}",
                    "raw_zh_term": raw,
                    "source_file": filename,
                    "source_type": source_type,
                    "initial_source_label": source_label,
                    "line_no": line_no,
                    "source_license_status": "unknown",
                    "created_at": TODAY,
                }
            )
            next_id += 1
    write_jsonl(__import__("pathlib").Path(args.output), rows)
    print(f"wrote {len(rows)} raw Meta Chinese candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
