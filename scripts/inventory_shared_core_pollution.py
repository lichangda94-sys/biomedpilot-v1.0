from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TERMS = ROOT / "data" / "medical_terms"
MINI_INDEX = TERMS / "mini_medical_terms_index.json"
META_SEED = TERMS / "meta_analysis" / "meta_seed_terms.json"
REPORT_DIR = TERMS / "review_reports"
INVENTORY_PATH = REPORT_DIR / "shared_core_pollution_inventory.json"
MANUAL_REVIEW_PATH = REPORT_DIR / "shared_core_pollution_manual_review.jsonl"

META_OUTCOME_TERMS = {
    "overall survival",
    "progression-free survival",
    "disease-free survival",
    "recurrence-free survival",
    "objective response rate",
    "mortality",
    "recurrence",
}
META_EFFECT_TERMS = {
    "hazard ratio",
    "odds ratio",
    "risk ratio",
    "relative risk",
    "mean difference",
    "standardized mean difference",
    "weighted mean difference",
}
META_STAT_TERMS = {"confidence interval", "p value", "p-value", "sample size", "standard error"}
META_STUDY_TERMS = {
    "cohort study",
    "case-control study",
    "randomized controlled trial",
    "cross-sectional study",
    "clinical trial",
    "observational study",
    "diagnostic accuracy study",
    "prognostic study",
}
META_INTENT_TERMS = {"risk factor", "diagnostic value", "prognostic value", "safety", "efficacy"}
QUALITY_TERMS = {"rob2", "rob 2", "newcastle-ottawa scale", "nos", "grade"}
REPORTING_TERMS = {"prisma", "mosem", "consort"}
BIO_TECH_TERMS = {
    "gse",
    "gsm",
    "gpl",
    "tcga",
    "gtex",
    "rna-seq",
    "single-cell",
    "scrna-seq",
    "tpm",
    "fpkm",
    "rpkm",
    "cpm",
    "raw counts",
    "count matrix",
    "probe id",
    "series matrix",
    "sample metadata",
}
AMBIGUOUS_TERMS = {"risk", "recurrence", "expression", "positive", "negative", "score", "response", "level"}


def main() -> None:
    rows = json.loads(MINI_INDEX.read_text(encoding="utf-8"))
    meta_seed_terms = _load_meta_seed_terms()
    inventory: list[dict[str, object]] = []
    manual_review: list[dict[str, object]] = []
    legacy_reference_index = _legacy_reference_index()

    for row in rows:
        category = _classify(row)
        if category == "valid_shared_core":
            continue
        item = _inventory_item(row, category, meta_seed_terms, legacy_reference_index)
        inventory.append(item)
        if item["manual_review_required"]:
            manual_review.append(_manual_review_item(item))

    summary = Counter(str(item["pollution_category"]) for item in inventory)
    payload = {
        "inventory_name": "shared_core_pollution_inventory",
        "inventory_date": "2026-05-20",
        "source": str(MINI_INDEX.relative_to(ROOT)),
        "runtime_modified": False,
        "total_suspected_pollution_terms": len(inventory),
        "category_counts": dict(sorted(summary.items())),
        "items": sorted(inventory, key=lambda item: (str(item["pollution_category"]), str(item["concept_id"]))),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    INVENTORY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    MANUAL_REVIEW_PATH.write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in manual_review),
        encoding="utf-8",
    )
    print(f"Wrote {INVENTORY_PATH}")
    print(f"Wrote {MANUAL_REVIEW_PATH}")
    print(f"Inventory items: {len(inventory)}; manual review: {len(manual_review)}")


def _classify(row: dict[str, object]) -> str:
    concept_id = str(row.get("concept_id") or "").lower()
    concept_type = str(row.get("concept_type") or "").lower()
    term_source = str(row.get("term_source") or "").lower()
    terms = _row_terms(row)
    joined = " | ".join(sorted(terms))

    if concept_id.startswith("mini:meta_analysis_") or "meta_analysis_terms_core" in term_source:
        if concept_type == "study_design" or terms & META_STUDY_TERMS:
            return "meta_study_design"
        if concept_type == "effect_measure" or terms & META_EFFECT_TERMS:
            return "meta_effect_measure"
        if concept_type == "outcome" or terms & META_OUTCOME_TERMS:
            return "meta_outcome"
        if concept_type == "pico_term":
            return "meta_research_intent" if terms & META_INTENT_TERMS else "needs_manual_review"
        return "needs_manual_review"
    if concept_id in {"mini:meta_outcomes_core"} or concept_type == "outcome" and terms & META_OUTCOME_TERMS:
        return "meta_outcome"
    if concept_id in {"mini:effect_size_core"} or terms & META_EFFECT_TERMS:
        return "meta_effect_measure"
    if concept_id in {"mini:study_design_core"} or concept_type == "study_design" or terms & META_STUDY_TERMS:
        return "meta_study_design"
    if terms & META_STAT_TERMS:
        return "meta_statistical_term"
    if terms & QUALITY_TERMS and ("quality" in joined or "bias" in joined or concept_type in {"quality_tool", "scale"}):
        return "meta_quality_assessment_tool"
    if terms & REPORTING_TERMS:
        return "meta_reporting_guideline"
    if terms & BIO_TECH_TERMS or concept_type == "data_modality":
        if "survival" in joined:
            return "ambiguous_or_qualified_term"
        return "bioinformatics_technical_term"
    if terms & AMBIGUOUS_TERMS and concept_type not in {"disease", "tissue", "organ", "species"}:
        return "ambiguous_or_qualified_term"
    return "valid_shared_core"


def _inventory_item(
    row: dict[str, object],
    category: str,
    meta_seed_terms: dict[str, dict[str, object]],
    legacy_reference_index: dict[str, list[str]],
) -> dict[str, object]:
    concept_id = str(row.get("concept_id") or "")
    preferred = str(row.get("preferred_label_en") or "")
    concept_type = str(row.get("concept_type") or "")
    legacy_refs = legacy_reference_index.get(concept_id, [])
    exists_in_meta_seed = _exists_in_meta_seed(row, meta_seed_terms)
    manual_review_required = category in {"needs_manual_review", "ambiguous_or_qualified_term"} or bool(legacy_refs)
    return {
        "concept_id": concept_id,
        "preferred_label_en": preferred,
        "zh_terms": _strings(row.get("zh_terms")),
        "concept_type": concept_type,
        "pollution_category": category,
        "current_location": "mini_medical_terms_index.json",
        "recommended_target": _recommended_target(category),
        "migration_risk": _migration_risk(category, legacy_refs),
        "exists_in_meta_seed": exists_in_meta_seed,
        "legacy_reference_detected": bool(legacy_refs),
        "legacy_reference_paths": legacy_refs[:10],
        "recommended_action": _recommended_action(category),
        "manual_review_required": manual_review_required,
    }


def _manual_review_item(item: dict[str, object]) -> dict[str, object]:
    issue_type = "legacy_reference_detected" if item["legacy_reference_detected"] else str(item["pollution_category"])
    return {
        "term": item["preferred_label_en"],
        "concept_id": item["concept_id"],
        "phase": "S1_shared_core_pollution_inventory",
        "issue_type": issue_type,
        "details": "Inventory item requires manual review before migration or deprecation.",
        "recommended_action": "manual_review",
        "auto_fix_applied": False,
    }


def _recommended_target(category: str) -> str:
    if category.startswith("meta_") or category == "ambiguous_or_qualified_term":
        return "data/medical_terms/meta_analysis/meta_migrated_from_shared_terms.json"
    if category == "bioinformatics_technical_term":
        return "data/medical_terms/bioinformatics/"
    return "manual_review"


def _recommended_action(category: str) -> str:
    if category == "needs_manual_review":
        return "manual_review_before_migration"
    if category == "ambiguous_or_qualified_term":
        return "qualified_term_only_manual_review"
    return "mirror_to_scoped_then_deprecate_shared"


def _migration_risk(category: str, legacy_refs: list[str]) -> str:
    if legacy_refs or category in {"needs_manual_review", "ambiguous_or_qualified_term"}:
        return "high"
    if category.startswith("meta_"):
        return "medium"
    return "medium"


def _exists_in_meta_seed(row: dict[str, object], meta_seed_terms: dict[str, dict[str, object]]) -> bool:
    terms = _row_terms(row)
    return any(term in meta_seed_terms for term in terms)


def _load_meta_seed_terms() -> dict[str, dict[str, object]]:
    rows = json.loads(META_SEED.read_text(encoding="utf-8"))
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        for term in _row_terms(row):
            result[term] = row
    return result


def _legacy_reference_index() -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    roots = [ROOT / "app", ROOT / "tests", ROOT / "docs"]
    files = [path for root in roots for path in root.rglob("*") if path.is_file() and path.suffix in {".py", ".md", ".json"}]
    concepts = [str(row.get("concept_id") or "") for row in json.loads(MINI_INDEX.read_text(encoding="utf-8"))]
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = str(path.relative_to(ROOT))
        for concept_id in concepts:
            if concept_id and concept_id in text:
                index.setdefault(concept_id, []).append(rel)
    return index


def _row_terms(row: dict[str, object]) -> set[str]:
    keys = (
        "concept_id",
        "preferred_label_en",
        "zh_terms",
        "synonyms_en",
        "exact_synonyms_en",
        "related_synonyms_en",
        "abbreviations",
        "mesh_terms",
        "normalized_terms",
    )
    return {value.lower() for value in _values(row, keys)}


def _values(row: dict[str, object], keys: tuple[str, ...]) -> list[str]:
    values: list[str] = []
    for key in keys:
        value = row.get(key)
        values.extend(_strings(value))
    return values


def _strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if isinstance(item, (str, int, float))]
    return []


if __name__ == "__main__":
    main()
