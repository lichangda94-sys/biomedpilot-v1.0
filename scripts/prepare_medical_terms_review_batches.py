#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"
REVIEW_BATCHES = MEDICAL_TERMS / "review_batches"
TODAY = date.today().isoformat()

HIGH_VALUE_TYPES = {
    "disease",
    "population",
    "exposure",
    "risk_factor",
    "intervention",
    "drug",
    "surgery",
    "radiotherapy",
    "diagnostic_test",
    "comparator",
    "outcome",
    "survival_outcome",
    "event_outcome",
    "risk_outcome",
    "diagnostic_outcome",
    "safety_outcome",
    "effect_measure",
    "statistical_term",
    "study_design",
    "research_intent",
}
GENERIC_TERMS = {
    "患者",
    "疾病",
    "症状",
    "治疗",
    "研究",
    "分析",
    "结果",
    "方法",
    "观察",
    "影响",
    "因素",
    "关系",
    "情况",
    "表现",
    "检查",
    "诊断",
    "临床",
    "医学",
    "资料",
    "对象",
}
COLLOQUIAL_TERMS = {"不舒服", "难受", "身体不好", "有问题", "毛病", "状态差"}
PDF_SECTION_TERMS = {"表1", "观察指标", "资料与方法", "纳入标准", "排除标准", "统计学方法", "参考文献"}
TCM_TERMS = {"气虚", "血瘀", "痰湿", "湿热", "肾虚", "脾虚", "上火", "体寒"}
META_RELEVANT_HINTS = ("甲状腺", "糖尿病", "肥胖", "高脂", "肿瘤", "癌", "暴露", "干预", "结局", "风险", "疗效", "预后")
CONFLICT_FOCUS_TERMS = {"转移", "阳性", "阴性", "表达", "风险", "预后", "疗效", "安全性", "结节", "病变", "反应", "水平", "评分", "综合征"}
GROUP_ONLY_TERMS = {
    "tumor",
    "normal",
    "case",
    "control",
    "treated",
    "untreated",
    "vehicle",
    "sham",
    "knockdown",
    "overexpression",
    "resistant",
    "sensitive",
    "primary",
    "metastatic",
    "recurrent",
    "adjacent normal",
    "wild type",
    "mutant",
}


def main() -> int:
    _require_inputs()
    bio_summary = _prepare_bioinformatics_batches()
    meta_summary = _prepare_meta_batches()
    _write_discussion_report(bio_summary, meta_summary)
    _write_meta_optimization_report(meta_summary)
    print("wrote medical terms review batches")
    return 0


def _prepare_bioinformatics_batches() -> dict[str, Any]:
    geo = _read_json(MEDICAL_TERMS / "bioinformatics" / "audits" / "geo_core_terms_coverage_audit.json")
    gtex = _read_json(MEDICAL_TERMS / "bioinformatics" / "audits" / "gtex_terms_coverage_audit.json")
    tcga = _read_json(MEDICAL_TERMS / "bioinformatics" / "audits" / "tcga_terms_coverage_audit.json")

    geo_rows = [_geo_missing_row(item) for item in geo["items"] if item["status"] == "missing"]
    gtex_rows = [_gtex_review_row(item) for item in gtex["items"] if item["status"] == "needs_review"]
    bio_dir = REVIEW_BATCHES / "bioinformatics"
    _write_jsonl(bio_dir / "geo_core_missing_review_batch.jsonl", geo_rows)
    _write_jsonl(bio_dir / "gtex_needs_review_batch.jsonl", gtex_rows)

    summary = {
        "generated_at": TODAY,
        "geo_missing_total": len(geo_rows),
        "geo_must_add": sum(1 for row in geo_rows if row["priority"] == "must_add"),
        "geo_should_add": sum(1 for row in geo_rows if row["priority"] == "should_add"),
        "geo_candidate_only": sum(1 for row in geo_rows if row["priority"] == "candidate_only"),
        "geo_manual_review": sum(1 for row in geo_rows if row["manual_review_required"]),
        "gtex_needs_review_total": len(gtex_rows),
        "tcga_status": "complete" if tcga["summary"]["missing"] == 0 and tcga["summary"]["needs_review"] == 0 else "review_required",
        "notes": [
            "GEO missing terms are classified for Bioinformatics-specific review, not shared-core promotion.",
            "GTEx broad body terms retain manual review markers.",
        ],
    }
    _write_json(bio_dir / "bioinformatics_review_batch_summary.json", summary)
    return summary


def _prepare_meta_batches() -> dict[str, Any]:
    meta_dir = REVIEW_BATCHES / "meta"
    runtime_entries = _read_json(MEDICAL_TERMS / "meta_analysis" / "meta_zh_to_en_concept_terms.json")
    promotion_rows = _read_jsonl(MEDICAL_TERMS / "review_queue" / "shared" / "shared_promotion_candidates_from_meta.jsonl")
    review_rows = _read_jsonl(MEDICAL_TERMS / "review_queue" / "meta" / "meta_zh_to_en_review_queue.jsonl")
    conflicts = _read_jsonl(MEDICAL_TERMS / "review_queue" / "meta" / "meta_mapping_conflicts.jsonl")
    disambiguation = _read_jsonl(MEDICAL_TERMS / "review_queue" / "meta" / "meta_needs_disambiguation.jsonl")
    english_mapping = _read_jsonl(MEDICAL_TERMS / "review_queue" / "meta" / "meta_needs_english_mapping.jsonl")
    rejected = _read_jsonl(MEDICAL_TERMS / "external_candidates" / "meta" / "rejected_meta_zh_candidates.jsonl")
    evidence_only = _read_jsonl(MEDICAL_TERMS / "external_candidates" / "meta" / "evidence_only_meta_zh_candidates.jsonl")
    future_scope = _read_jsonl(MEDICAL_TERMS / "external_candidates" / "meta" / "future_scope_meta_zh_candidates.jsonl")

    approved_batch = [_runtime_review_row(entry) for entry in runtime_entries if entry.get("review_status") == "approved"]
    promotion_batch = [_promotion_review_row(row) for row in promotion_rows]
    priority_batch = sorted((_priority_review_row(row) for row in review_rows), key=lambda item: (-item["priority_score"], item["normalized_zh_term"]))[:300]
    conflict_batch = sorted((_conflict_row(row) for row in conflicts), key=lambda item: (_risk_order(item["risk_level"]), -item["priority_score"], item["normalized_zh_term"]))[:200]
    disambiguation_batch = sorted((_disambiguation_row(row) for row in disambiguation), key=lambda item: (-item["priority_score"], item["normalized_zh_term"]))[:200]
    english_mapping_batch = sorted((_english_mapping_row(row) for row in english_mapping), key=lambda item: (-item["priority_score"], item["normalized_zh_term"]))[:300]
    auto_reject_batch = _auto_reject_rows(rejected, review_rows)
    evidence_batch = _aggregate_evidence_only(evidence_only)
    future_batch = _aggregate_future_scope(future_scope)

    _write_jsonl(meta_dir / "meta_approved_runtime_review_batch.jsonl", approved_batch)
    _write_jsonl(meta_dir / "meta_shared_promotion_review_batch.jsonl", promotion_batch)
    _write_jsonl(meta_dir / "meta_priority_review_batch_top_300.jsonl", priority_batch)
    _write_jsonl(meta_dir / "meta_mapping_conflicts_top_200.jsonl", conflict_batch)
    _write_jsonl(meta_dir / "meta_disambiguation_top_200.jsonl", disambiguation_batch)
    _write_jsonl(meta_dir / "meta_english_mapping_top_300.jsonl", english_mapping_batch)
    _write_jsonl(meta_dir / "meta_auto_reject_candidates.jsonl", auto_reject_batch)
    _write_jsonl(meta_dir / "meta_evidence_only_candidates_optimized.jsonl", evidence_batch)
    _write_jsonl(meta_dir / "meta_future_scope_candidates_optimized.jsonl", future_batch)

    summary = {
        "generated_at": TODAY,
        "raw_candidates_total": _jsonl_count(MEDICAL_TERMS / "external_candidates" / "meta" / "raw_meta_zh_candidates.jsonl"),
        "normalized_candidates_total": _jsonl_count(MEDICAL_TERMS / "external_candidates" / "meta" / "normalized_meta_zh_candidates.jsonl"),
        "review_queue_total": len(review_rows),
        "approved_runtime_total": len(approved_batch),
        "shared_promotion_total": len(promotion_batch),
        "priority_review_top_n": len(priority_batch),
        "mapping_conflicts_top_n": len(conflict_batch),
        "disambiguation_top_n": len(disambiguation_batch),
        "english_mapping_top_n": len(english_mapping_batch),
        "auto_reject_total": len(auto_reject_batch),
        "evidence_only_optimized_total": len(evidence_batch),
        "future_scope_optimized_total": len(future_batch),
        "manual_review_recommended_order": [
            "geo_core_missing_review_batch",
            "gtex_needs_review_batch",
            "meta_approved_runtime_review_batch",
            "meta_shared_promotion_review_batch",
            "meta_mapping_conflicts_top_200",
            "meta_disambiguation_top_200",
            "meta_english_mapping_top_300",
            "meta_priority_review_batch_top_300",
        ],
    }
    _write_json(meta_dir / "meta_review_batch_summary.json", summary)
    return summary


def _geo_missing_row(item: dict[str, Any]) -> dict[str, Any]:
    category = item["category"]
    concept_type = "grouping_term" if category == "grouping_modifier" else category
    target_files = {
        "omics_assay": "data/medical_terms/bioinformatics/bioinformatics_data_type_terms.json",
        "data_format": "data/medical_terms/bioinformatics/bioinformatics_data_type_terms.json",
        "sample_status": "data/medical_terms/bioinformatics/bioinformatics_grouping_terms.json",
        "treatment_status": "data/medical_terms/bioinformatics/bioinformatics_grouping_terms.json",
        "grouping_term": "data/medical_terms/bioinformatics/bioinformatics_grouping_terms.json",
        "platform_term": "data/medical_terms/bioinformatics/bioinformatics_dataset_registry_terms.json",
        "database_id": "data/medical_terms/bioinformatics/bioinformatics_dataset_registry_terms.json",
        "species": "data/medical_terms/bioinformatics/bioinformatics_species_terms.json",
        "stop_term": "data/medical_terms/bioinformatics/bioinformatics_stop_terms.json",
    }
    priority = _geo_priority(concept_type)
    standalone = str(item["term"]).lower() not in GROUP_ONLY_TERMS and concept_type not in {"data_format", "stop_term", "platform_term"}
    return {
        "term": item["term"],
        "audit_status": item["status"],
        "suggested_concept_type": concept_type,
        "suggested_target_file": target_files.get(concept_type, "data/medical_terms/bioinformatics/bioinformatics_terms.json"),
        "priority": priority,
        "standalone_search_allowed": standalone,
        "bioinformatics_usage": _geo_usage(concept_type),
        "shared_core_allowed": False,
        "manual_review_required": concept_type in {"species", "needs_review"},
        "reason": f"Core GEO {concept_type} term missing from Bioinformatics runtime.",
    }


def _geo_priority(concept_type: str) -> str:
    if concept_type in {"data_format", "species"}:
        return "must_add"
    if concept_type in {"sample_status", "treatment_status", "grouping_term", "platform_term"}:
        return "should_add"
    if concept_type == "stop_term":
        return "candidate_only"
    return "candidate_only"


def _geo_usage(concept_type: str) -> list[str]:
    if concept_type in {"data_format", "omics_assay"}:
        return ["dataset_filter", "data_type_detection", "analysis_readiness_check"]
    if concept_type in {"sample_status", "treatment_status", "grouping_term"}:
        return ["group_detection", "sample_annotation", "comparison_suggestion"]
    if concept_type == "species":
        return ["dataset_filter", "species_detection", "metadata_normalization"]
    if concept_type == "platform_term":
        return ["dataset_registry", "platform_metadata_detection"]
    return ["stop_word_filtering"]


def _gtex_review_row(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "term": item["gtex_tissue"],
        "audit_status": item["status"],
        "suggested_zh_terms": [item["zh_term"]],
        "suggested_concept_type": "tissue",
        "suggested_target": "GTEx tissue mapping",
        "review_reason": item.get("review_notes") or "Chinese tissue mapping or subtype needs confirmation.",
        "manual_review_required": True,
        "recommended_action": "Confirm standard Chinese name and whether subtype-specific mappings are needed.",
    }


def _runtime_review_row(entry: dict[str, Any]) -> dict[str, Any]:
    issues = []
    if not entry.get("preferred_label_en"):
        issues.append("missing preferred_label_en")
    if not entry.get("concept_type"):
        issues.append("missing concept_type")
    query_usage = entry.get("query_usage") or {}
    if query_usage.get("chinese_database_search") is True:
        issues.append("chinese_database_search=true")
    if query_usage.get("chinese_pdf_extraction") is True:
        issues.append("chinese_pdf_extraction=true")
    if entry.get("concept_type") in {"effect_measure", "research_intent"} and entry.get("query_expansion_allowed") is True:
        issues.append("query_expansion_allowed unreasonable")
    if entry.get("concept_type") == "outcome" and entry.get("standalone_search_allowed") not in {False, "conditional"}:
        issues.append("standalone_search_allowed unreasonable")
    return {
        "concept_id": entry.get("concept_id"),
        "zh_terms": entry.get("zh_terms", []),
        "preferred_label_en": entry.get("preferred_label_en"),
        "concept_type": entry.get("concept_type"),
        "pico_roles": entry.get("pico_roles", []),
        "query_expansion_allowed": entry.get("query_expansion_allowed"),
        "standalone_search_allowed": entry.get("standalone_search_allowed"),
        "query_usage": query_usage,
        "review_focus": ["Check English mapping", "Check PICO role", "Check query usage"],
        "quality_flags": issues,
    }


def _promotion_review_row(row: dict[str, Any]) -> dict[str, Any]:
    concept_type = str(row.get("suggested_concept_type", ""))
    allowed = concept_type in {"disease", "phenotype", "tissue"}
    return {
        "term": row.get("normalized_zh_term"),
        "suggested_preferred_label_en": row.get("suggested_preferred_label_en"),
        "suggested_concept_type": concept_type,
        "suggested_action": "eligible_for_discussion" if allowed else "reject_promotion_keep_meta_only",
        "promotion_allowed": "manual_review_only",
        "reason": "Disease concept likely useful to both Bioinformatics and Meta." if allowed else "Meta-specific concept should remain Meta-only.",
    }


def _priority_review_row(row: dict[str, Any]) -> dict[str, Any]:
    score, reasons = _priority_score(row)
    return {
        "normalized_zh_term": row.get("normalized_zh_term"),
        "suggested_concept_type": row.get("suggested_concept_type"),
        "suggested_pico_roles": row.get("suggested_pico_roles", []),
        "suggested_preferred_label_en": row.get("suggested_preferred_label_en", ""),
        "priority_score": score,
        "priority_reason": reasons,
        "recommended_manual_action": "confirm_mapping_and_runtime_entry" if row.get("suggested_preferred_label_en") else "manual_confirm_english_mapping",
    }


def _priority_score(row: dict[str, Any]) -> tuple[int, list[str]]:
    term = str(row.get("normalized_zh_term", ""))
    concept_type = str(row.get("suggested_concept_type", ""))
    reasons: list[str] = []
    score = 0
    if row.get("suggested_preferred_label_en"):
        score += 5
        reasons.append("has_english_mapping")
    if row.get("suggested_mesh_terms"):
        score += 5
        reasons.append("has_mesh_terms")
    if concept_type in HIGH_VALUE_TYPES:
        score += 4
        reasons.append("high_value_concept_type")
    evidence = row.get("source_evidence") or []
    if isinstance(evidence, list) and len({item.get("source_file") for item in evidence if isinstance(item, dict)}) > 1:
        score += 3
        reasons.append("multiple_sources")
    if 2 <= len(term) <= 12:
        score += 3
        reasons.append("stable_short_phrase")
    if re.search(r"[A-Z]{2,}[0-9]*", term):
        score += 2
        reasons.append("contains_abbreviation")
    if any(hint in term for hint in META_RELEVANT_HINTS):
        score += 2
        reasons.append("meta_relevant")
    reject_reason = _auto_reject_reason(term)
    if reject_reason:
        score -= 5
        reasons.append(reject_reason)
    return score, reasons


def _conflict_row(row: dict[str, Any]) -> dict[str, Any]:
    term = str(row.get("normalized_zh_term", ""))
    labels = list(row.get("source_labels", []))
    risk = "high" if term in CONFLICT_FOCUS_TERMS or len(term) <= 2 else "medium"
    return {
        "normalized_zh_term": term,
        "conflict_types": labels,
        "candidate_mappings": [],
        "risk_level": risk,
        "priority_score": 20 if risk == "high" else 10,
        "recommended_action": "manual_disambiguation_required",
        "reason": "Term may mean different roles across Meta and Bioinformatics contexts.",
    }


def _disambiguation_row(row: dict[str, Any]) -> dict[str, Any]:
    score, reasons = _priority_score(row)
    term = str(row.get("normalized_zh_term", ""))
    if term in CONFLICT_FOCUS_TERMS:
        score += 5
        reasons.append("known_ambiguous_focus_term")
    return {
        "normalized_zh_term": term,
        "possible_roles": row.get("suggested_pico_roles", []),
        "recommended_action": "manual_define_context_rule",
        "priority_score": score,
        "priority_reason": reasons,
    }


def _english_mapping_row(row: dict[str, Any]) -> dict[str, Any]:
    score, reasons = _priority_score(row)
    term = str(row.get("normalized_zh_term", ""))
    return {
        "normalized_zh_term": term,
        "suggested_concept_type": row.get("suggested_concept_type"),
        "suggested_pico_roles": row.get("suggested_pico_roles", []),
        "english_mapping_status": "missing",
        "recommended_lookup": _recommended_lookup(term),
        "priority_score": score,
        "priority_reason": reasons,
        "recommended_action": "manual_confirm_english_mapping",
    }


def _recommended_lookup(term: str) -> list[str]:
    lookup = {
        "碘131治疗": ["radioiodine therapy", "iodine-131 therapy", "I-131 therapy"],
        "复发": ["recurrence", "relapse", "disease recurrence"],
        "预后": ["prognosis", "prognostic factor", "survival outcome"],
        "转移": ["metastasis", "metastatic disease", "distant metastasis"],
    }
    return lookup.get(term, [])


def _auto_reject_rows(rejected: list[dict[str, Any]], review_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for row in rejected:
        term = str(row.get("normalized_zh_term") or row.get("raw_zh_term") or "")
        reason = str(row.get("partition_reason") or _auto_reject_reason(term) or "previously_rejected_candidate")
        if term:
            rows[term] = {"normalized_zh_term": term, "reject_reason": reason, "recommended_status": "rejected"}
    for row in review_rows:
        term = str(row.get("normalized_zh_term", ""))
        reason = _auto_reject_reason(term)
        if reason and term:
            rows[term] = {"normalized_zh_term": term, "reject_reason": reason, "recommended_status": "rejected"}
    return sorted(rows.values(), key=lambda item: item["normalized_zh_term"])


def _auto_reject_reason(term: str) -> str:
    if len(term) == 1 and not re.fullmatch(r"[A-Z]{2,}", term):
        return "single_character_non_abbreviation"
    if term in GENERIC_TERMS:
        return "generic_medical_word"
    if term in COLLOQUIAL_TERMS:
        return "colloquial_term"
    if term in PDF_SECTION_TERMS:
        return "chinese_pdf_section_term"
    if term in TCM_TERMS:
        return "future_tcm_scope"
    if len(term) > 40 or re.search(r"[。；;]", term):
        return "long_or_sentence_like_candidate"
    if re.search(r"\b[BIOS]-[A-Z]+\b", term):
        return "ner_bio_label"
    return ""


def _aggregate_evidence_only(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        term = str(row.get("normalized_zh_term") or row.get("raw_zh_term") or "")
        if term:
            grouped[term].append(row)
    result = []
    for term, items in grouped.items():
        result.append(
            {
                "normalized_zh_term": term,
                "source_count": len(items),
                "source_files": sorted({str(item.get("source_file", "")) for item in items if item.get("source_file")}),
                "reason": "description_or_evidence_only",
                "recommended_status": "evidence_only",
            }
        )
    return sorted(result, key=lambda item: (-item["source_count"], item["normalized_zh_term"]))


def _aggregate_future_scope(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        term = str(row.get("normalized_zh_term") or row.get("raw_zh_term") or "")
        if term:
            grouped[term].append(row)
    result = []
    for term, items in grouped.items():
        result.append(
            {
                "normalized_zh_term": term,
                "future_scope_type": _future_scope_type(term),
                "source_count": len(items),
                "reason": "Out of current Meta English-search and English-extraction scope.",
                "recommended_status": "future_scope",
            }
        )
    return sorted(result, key=lambda item: item["normalized_zh_term"])


def _future_scope_type(term: str) -> str:
    if term in TCM_TERMS:
        return "tcm_meta_specific_term"
    if term in PDF_SECTION_TERMS:
        return "chinese_pdf_section_term"
    return "future_chinese_corpus_scope"


def _risk_order(risk: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(risk, 3)


def _write_discussion_report(bio: dict[str, Any], meta: dict[str, Any]) -> None:
    report_dir = REVIEW_BATCHES / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "# Vocabulary Review Batches For Discussion",
            "",
            f"Generated: {TODAY}",
            "",
            "## Purpose",
            "",
            "This stage turns the previous 47,000+ Meta candidates and Bioinformatics audits into bounded review batches for human discussion.",
            "",
            "## Bioinformatics",
            "",
            f"- GEO missing: {bio['geo_missing_total']} -> data/medical_terms/review_batches/bioinformatics/geo_core_missing_review_batch.jsonl",
            f"- GTEx needs_review: {bio['gtex_needs_review_total']} -> data/medical_terms/review_batches/bioinformatics/gtex_needs_review_batch.jsonl",
            f"- TCGA status: {bio['tcga_status']}",
            "",
            "## Meta",
            "",
            f"- Approved runtime review entries: {meta['approved_runtime_total']} -> data/medical_terms/review_batches/meta/meta_approved_runtime_review_batch.jsonl",
            f"- Shared promotion candidates: {meta['shared_promotion_total']} -> data/medical_terms/review_batches/meta/meta_shared_promotion_review_batch.jsonl",
            f"- Priority review top batch: {meta['priority_review_top_n']} -> data/medical_terms/review_batches/meta/meta_priority_review_batch_top_300.jsonl",
            f"- Mapping conflicts top batch: {meta['mapping_conflicts_top_n']} -> data/medical_terms/review_batches/meta/meta_mapping_conflicts_top_200.jsonl",
            f"- Disambiguation top batch: {meta['disambiguation_top_n']} -> data/medical_terms/review_batches/meta/meta_disambiguation_top_200.jsonl",
            f"- English mapping top batch: {meta['english_mapping_top_n']} -> data/medical_terms/review_batches/meta/meta_english_mapping_top_300.jsonl",
            f"- Auto reject candidates: {meta['auto_reject_total']}",
            f"- Evidence-only optimized candidates: {meta['evidence_only_optimized_total']}",
            f"- Future-scope optimized candidates: {meta['future_scope_optimized_total']}",
            "",
            "## Recommended Discussion Order",
            "",
            "1. GEO core missing 28",
            "2. GTEx needs_review 5",
            "3. Meta approved runtime 11",
            "4. Shared promotion candidates 4",
            "5. Meta mapping conflicts top 200",
            "6. Meta disambiguation top 200",
            "7. Meta English mapping top 300",
            "8. Meta priority review top 300",
            "",
            "## Scope Guard",
            "",
            "This stage does not modify shared core, Bioinformatics runtime, Meta runtime, desktop entry points, packaging, or business workflows.",
            "",
        ]
    )
    (report_dir / "vocabulary_review_batches_for_discussion.md").write_text(text, encoding="utf-8")


def _write_meta_optimization_report(meta: dict[str, Any]) -> None:
    report_dir = REVIEW_BATCHES / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "# Meta Candidate Optimization Report",
            "",
            f"Generated: {TODAY}",
            "",
            f"- raw_candidates_total: {meta['raw_candidates_total']}",
            f"- normalized_candidates_total: {meta['normalized_candidates_total']}",
            f"- review_queue_total: {meta['review_queue_total']}",
            f"- auto_reject_total: {meta['auto_reject_total']}",
            "",
            "## Rules",
            "",
            "High-value batches prioritize mapped disease, exposure, intervention, outcome, effect measure, study design, and research intent terms, then short stable phrases and multi-source terms.",
            "",
            "Conflict batches prioritize cross-label terms, known ambiguous review terms, and short broad terms.",
            "",
            "Disambiguation and English-mapping batches prioritize terms likely to become runtime candidates after human review.",
            "",
            "Auto-reject candidates include single-character non-abbreviations, generic medical words, colloquial terms, long sentence-like strings, Chinese PDF section terms, and out-of-scope TCM terms.",
            "",
            "## Top Batch Files",
            "",
            "- data/medical_terms/review_batches/meta/meta_priority_review_batch_top_300.jsonl",
            "- data/medical_terms/review_batches/meta/meta_mapping_conflicts_top_200.jsonl",
            "- data/medical_terms/review_batches/meta/meta_disambiguation_top_200.jsonl",
            "- data/medical_terms/review_batches/meta/meta_english_mapping_top_300.jsonl",
            "",
            "## Remaining Manual Review Reason",
            "",
            "Most external corpus rows still lack reliable English preferred labels, MeSH/Emtree candidates, and unambiguous PICO/PECO roles.",
            "",
        ]
    )
    (report_dir / "meta_candidate_optimization_report.md").write_text(text, encoding="utf-8")


def _require_inputs() -> None:
    required = [
        MEDICAL_TERMS / "bioinformatics" / "audits" / "tcga_terms_coverage_audit.json",
        MEDICAL_TERMS / "bioinformatics" / "audits" / "gtex_terms_coverage_audit.json",
        MEDICAL_TERMS / "bioinformatics" / "audits" / "geo_core_terms_coverage_audit.json",
        MEDICAL_TERMS / "review_queue" / "meta" / "meta_zh_to_en_review_queue.jsonl",
        MEDICAL_TERMS / "meta_analysis" / "meta_zh_to_en_concept_terms.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required review-batch input files: " + ", ".join(missing))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _jsonl_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()) if path.exists() else 0


if __name__ == "__main__":
    raise SystemExit(main())
