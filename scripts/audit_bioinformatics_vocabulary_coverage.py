#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from medical_terms_stage_pipeline import (
    DOCS_MEDICAL_TERMS,
    GEO_CORE_TERMS,
    GTEX_TISSUES,
    MEDICAL_TERMS,
    TCGA_PROJECTS,
    TODAY,
    markdown_table,
    status_from_covered,
    write_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.shared.query_intelligence.medical_terms import load_terms  # noqa: E402
from app.shared.query_intelligence.medical_terms.term_index_loader import load_mini_term_index  # noqa: E402
from app.shared.query_intelligence.medical_terms.zh_overrides_loader import load_zh_overrides  # noqa: E402


def main() -> int:
    mini, haystack = _load_audit_corpus()

    tcga = _audit_tcga(mini, haystack)
    gtex = _audit_gtex(mini, haystack)
    geo = _audit_geo(haystack)
    audit_dir = MEDICAL_TERMS / "bioinformatics" / "audits"
    write_json(audit_dir / "tcga_terms_coverage_audit.json", tcga)
    write_json(audit_dir / "gtex_terms_coverage_audit.json", gtex)
    write_json(audit_dir / "geo_core_terms_coverage_audit.json", geo)
    _write_markdown_reports(tcga, gtex, geo)
    print("wrote Bioinformatics vocabulary coverage audits")
    return 0


def _load_audit_corpus() -> tuple[list[dict[str, object]], str]:
    """Use approved loaders so this script does not bypass scope routing."""
    mini = [asdict(term) for term in load_mini_term_index()]
    zh = [asdict(override) for override in load_zh_overrides()]
    scoped = [
        {
            "concept_id": term.concept_id,
            "preferred_label_en": term.preferred_label_en,
            "concept_type": term.concept_type,
            "source": term.source,
            "terms": list(term.terms),
        }
        for term in load_terms("bioinformatics")
    ]
    haystack = json.dumps({"bioinformatics_scope": scoped, "mini_cross_refs": mini, "zh_overrides": zh}, ensure_ascii=False).lower()
    return mini, haystack


def _audit_tcga(mini: list[dict[str, object]], haystack: str) -> dict[str, object]:
    rows = []
    for code, english_name, zh_name in TCGA_PROJECTS:
        mapped = [
            str(item.get("concept_id"))
            for item in mini
            if code in item.get("cross_refs", {}).get("tcga", [])  # type: ignore[union-attr]
        ]
        covered = bool(mapped)
        rows.append(
            {
                "project_code": code,
                "cancer_name_en": english_name,
                "cancer_name_zh": zh_name,
                "mapped_concept_ids": sorted(mapped),
                "project_code_covered": code.lower() in haystack,
                "zh_name_covered": zh_name.lower() in haystack,
                "status": status_from_covered(covered),
                "review_notes": "" if covered else "TCGA project code is not mapped to a runtime disease concept.",
            }
        )
    return _audit_payload("tcga_terms_coverage_audit.v1", rows)


def _audit_gtex(mini: list[dict[str, object]], haystack: str) -> dict[str, object]:
    broad = {"Skin", "Blood", "Artery", "Nerve", "Muscle", "Heart"}
    rows = []
    for tissue, zh_name, tissue_type in GTEX_TISSUES:
        mapped = [
            str(item.get("concept_id"))
            for item in mini
            if tissue in item.get("cross_refs", {}).get("gtex", [])  # type: ignore[union-attr]
            or tissue.lower() == str(item.get("preferred_label_en", "")).lower()
        ]
        covered = bool(mapped) or tissue.lower() in haystack
        needs_review = tissue in broad and covered
        rows.append(
            {
                "gtex_tissue": tissue,
                "zh_term": zh_name,
                "tissue_type": tissue_type,
                "mapped_concept_ids": sorted(set(mapped)),
                "tissue_covered": covered,
                "zh_mapping_covered": zh_name.lower() in haystack,
                "body_generic_conflict": tissue in broad,
                "status": status_from_covered(covered, needs_review=needs_review),
                "review_notes": "Broad body term requires context-aware matching." if needs_review else ("" if covered else "Missing or approximate GTEx tissue coverage."),
            }
        )
    return _audit_payload("gtex_terms_coverage_audit.v1", rows)


def _audit_geo(haystack: str) -> dict[str, object]:
    rows = []
    for category, terms in GEO_CORE_TERMS.items():
        for term in terms:
            covered = term.lower() in haystack
            rows.append(
                {
                    "term": term,
                    "category": category,
                    "status": "complete" if covered else "missing",
                    "covered": covered,
                    "review_notes": "" if covered else "Keep as GEO core future candidate; do not claim full GEO coverage.",
                }
            )
    payload = _audit_payload("geo_core_terms_coverage_audit.v1", rows)
    payload["scope_note"] = "Core GEO term audit only; long-tail GEO vocabulary is future scope."
    payload["future_candidates"] = [row for row in rows if row["status"] == "missing"]
    return payload


def _audit_payload(schema_version: str, rows: list[dict[str, object]]) -> dict[str, object]:
    statuses = {status: sum(1 for row in rows if row["status"] == status) for status in ("complete", "partial", "missing", "needs_review")}
    return {
        "schema_version": schema_version,
        "generated_at": TODAY,
        "summary": {
            "total": len(rows),
            "complete": statuses["complete"],
            "partial": statuses["partial"],
            "missing": statuses["missing"],
            "needs_review": statuses["needs_review"],
        },
        "items": rows,
    }


def _write_markdown_reports(tcga: dict[str, object], gtex: dict[str, object], geo: dict[str, object]) -> None:
    DOCS_MEDICAL_TERMS.mkdir(parents=True, exist_ok=True)
    reports = (
        ("tcga_terms_coverage_audit.md", "TCGA Terms Coverage Audit", tcga, ["project_code", "status", "mapped_concept_ids", "review_notes"]),
        ("gtex_terms_coverage_audit.md", "GTEx Terms Coverage Audit", gtex, ["gtex_tissue", "status", "zh_mapping_covered", "body_generic_conflict", "review_notes"]),
        ("geo_core_terms_coverage_audit.md", "GEO Core Terms Coverage Audit", geo, ["term", "category", "status", "review_notes"]),
    )
    for filename, title, payload, columns in reports:
        items = payload["items"]  # type: ignore[index]
        rows = [[str(item.get(column, "")) for column in columns] for item in items]  # type: ignore[union-attr]
        text = f"# {title}\n\nGenerated: {TODAY}\n\n## Summary\n\n```json\n{json.dumps(payload['summary'], ensure_ascii=False, indent=2)}\n```\n\n## Items\n\n{markdown_table(columns, rows)}\n"
        (DOCS_MEDICAL_TERMS / filename).write_text(text, encoding="utf-8")
    summary = _summary_report(tcga, gtex, geo)
    (DOCS_MEDICAL_TERMS / "bioinformatics_vocabulary_coverage_audit_summary.md").write_text(summary, encoding="utf-8")


def _summary_report(tcga: dict[str, object], gtex: dict[str, object], geo: dict[str, object]) -> str:
    missing = []
    review = []
    for source, payload in (("TCGA", tcga), ("GTEx", gtex), ("GEO", geo)):
        for item in payload["items"]:  # type: ignore[index]
            if item["status"] == "missing":
                missing.append([source, str(item.get("project_code") or item.get("gtex_tissue") or item.get("term")), str(item.get("review_notes", ""))])
            if item["status"] == "needs_review":
                review.append([source, str(item.get("project_code") or item.get("gtex_tissue") or item.get("term")), str(item.get("review_notes", ""))])
    return "\n".join(
        [
            "# Bioinformatics Vocabulary Coverage Audit Summary",
            "",
            f"Generated: {TODAY}",
            "",
            "## Conclusions",
            "",
            f"- TCGA: {tcga['summary']}",
            f"- GTEx: {gtex['summary']}",
            f"- GEO core: {geo['summary']}",
            "",
            "GEO is reported as core coverage only; this stage does not claim long-tail GEO vocabulary completeness.",
            "",
            "## Missing Items",
            "",
            markdown_table(["source", "term", "reason"], missing) if missing else "No missing items.",
            "",
            "## Needs Manual Review",
            "",
            markdown_table(["source", "term", "reason"], review) if review else "No manual review items.",
            "",
            "## Suggested Later Patch",
            "",
            "Add reviewed missing GEO species, sample-state, and data-format terms to Bioinformatics-specific vocabulary files before any runtime exposure.",
            "",
            "## Why Nothing Was Auto-Merged",
            "",
            "This stage is an audit stage. It does not automatically promote Bioinformatics terms into shared core or Meta runtime.",
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
