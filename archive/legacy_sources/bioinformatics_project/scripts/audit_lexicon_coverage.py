"""Audit concept and lexicon coverage for the TCGA/GDC, GTEx, and GEO-ready stack."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tcga_gtex.config_rules import get_default_rule_service

LEXICON_DIR = REPO_ROOT / "tcga_gtex" / "lexicon"

CONCEPTS_PATH = LEXICON_DIR / "concept_catalog.csv"
MAPPINGS_PATH = LEXICON_DIR / "concept_source_mappings.csv"
FULL_PATH = LEXICON_DIR / "english_core_terms_full.csv"
CURATED_PATH = LEXICON_DIR / "english_ui_terms_curated.csv"
ALIASES_PATH = LEXICON_DIR / "english_term_aliases.csv"
CHINESE_TERMS_PATH = LEXICON_DIR / "chinese_concept_terms.csv"
REPORT_JSON_PATH = LEXICON_DIR / "coverage_audit_report.json"
REPORT_MD_PATH = LEXICON_DIR / "coverage_audit_report.md"

AUDIT_SOURCES = ["tcga_gdc", "gtex", "geo", "shared"]
CATEGORY_GROUPS = [
    "disease_or_project_terms",
    "sample_terms",
    "data_terms",
    "access_terms",
    "tissue_terms",
    "display_terms",
    "source_entities",
]

FULL_BUCKET_NORMALIZATION = {
    "disease_or_project_terms": "disease_or_project_terms",
    "sample_terms": "sample_terms",
    "data_terms": "data_terms",
    "display_terms": "display_terms",
    "source_entities": "source_entities",
    "access_and_mode_terms": "access_terms",
}


_RULE_SERVICE = get_default_rule_service()
_AUDIT_RULES = _RULE_SERVICE.load_coverage_audit_rules()

HIGH_FREQUENCY_CANCERS = _AUDIT_RULES["high_frequency_cancers"]
HIGH_FREQUENCY_TISSUES = _AUDIT_RULES["high_frequency_tissues"]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_full_category(row: dict[str, str]) -> str | None:
    bucket = FULL_BUCKET_NORMALIZATION.get(row["bucket"])
    if bucket == "disease_or_project_terms" and row["field_name"] == "cases.primary_site":
        return "tissue_terms"
    if bucket == "sample_terms" and row["field_name"] in {"tissue", "subregion"}:
        return "tissue_terms"
    return bucket


def concept_category_to_report_group(concept: dict[str, str]) -> str | None:
    mapping = {
        "disease": "disease_or_project_terms",
        "sample_type": "sample_terms",
        "analysis_resource": "data_terms",
        "access": "access_terms",
        "tissue": "tissue_terms",
        "database_entity": "source_entities",
    }
    return mapping.get(concept["concept_category"])


def mapping_category_for_row(mapping: dict[str, str], concept_lookup: dict[str, dict[str, str]]) -> str | None:
    concept = concept_lookup.get(mapping["concept_id"])
    if concept is None:
        return None
    return concept_category_to_report_group(concept)


def representative_items(rows: list[dict[str, str]], key: str, limit: int = 5) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for row in rows:
        value = row.get(key, "")
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
        if len(values) >= limit:
            break
    return values


def detect_category_bias(full_rows: list[dict[str, str]], chinese_rows: list[dict[str, str]], term: str) -> dict[str, Any]:
    full_mentions = [row for row in full_rows if term in row["display_label_en"].lower() or term in row["term_en"].lower()]
    chinese_mentions = [row for row in chinese_rows if term in row["term_zh"]]
    return {
        "full_mentions": len(full_mentions),
        "chinese_mentions": len(chinese_mentions),
        "full_ratio": round(len(full_mentions) / max(len(full_rows), 1), 4),
        "chinese_ratio": round(len(chinese_mentions) / max(len(chinese_rows), 1), 4),
    }


def coverage_state(layers: dict[str, bool]) -> str:
    if all(layers.values()):
        return "fully_covered"
    if any(layers.values()):
        return "partially_covered"
    return "missing"


def build_category_coverage(
    full_rows: list[dict[str, str]],
    concepts: list[dict[str, str]],
    mappings: list[dict[str, str]],
) -> dict[str, Any]:
    concept_lookup = {row["concept_id"]: row for row in concepts}
    report: dict[str, Any] = {}

    for category in CATEGORY_GROUPS:
        full_by_source = defaultdict(list)
        for row in full_rows:
            normalized = normalize_full_category(row)
            if normalized == category:
                full_by_source[row["source"]].append(row)

        concept_rows = [row for row in concepts if concept_category_to_report_group(row) == category]
        mapping_by_source = defaultdict(list)
        for row in mappings:
            normalized = mapping_category_for_row(row, concept_lookup)
            if normalized == category:
                mapping_by_source[row["source"]].append(row)

        source_stats = {}
        for source in AUDIT_SOURCES:
            source_stats[source] = {
                "full_term_count": len(full_by_source[source]),
                "mapping_count": len(mapping_by_source[source]),
                "representative_terms": representative_items(full_by_source[source], "display_label_en"),
                "representative_concepts": representative_items(concept_rows, "concept_id"),
                "representative_mapping_targets": representative_items(mapping_by_source[source], "target_value"),
            }

        source_stats["database_agnostic_concepts"] = {
            "concept_count": len(concept_rows),
            "representative_concepts": representative_items(concept_rows, "concept_id"),
        }

        missing_layers = []
        if concept_rows and not any(full_by_source.values()):
            missing_layers.append("concept_present_but_full_missing")
        if concept_rows and not any(mapping_by_source.values()):
            missing_layers.append("concept_present_but_mapping_missing")

        full_rep_values = " ".join(representative_items([row for group in full_by_source.values() for row in group], "display_label_en", limit=20)).lower()
        bias_note = "thyroid_skewed" if "thyroid" in full_rep_values and full_rep_values.count("thyroid") >= 2 else "not_obvious"

        report[category] = {
            "by_source": source_stats,
            "missing_layer_flags": missing_layers,
            "bias_note": bias_note,
        }

    return report


def build_disease_coverage(
    concepts: list[dict[str, str]],
    mappings: list[dict[str, str]],
    full_rows: list[dict[str, str]],
    chinese_rows: list[dict[str, str]],
) -> dict[str, Any]:
    disease_concepts = [row for row in concepts if row["concept_category"] == "disease"]
    chinese_by_concept = defaultdict(list)
    for row in chinese_rows:
        chinese_by_concept[row["concept_id"]].append(row)

    mappings_by_concept_source = defaultdict(list)
    for row in mappings:
        mappings_by_concept_source[(row["concept_id"], row["source"])].append(row)

    tcga_project_ids = sorted(
        {
            row["field_value"]
            for row in full_rows
            if row["field_name"] == "project.project_id" and row["term_type"] == "value" and row["field_value"].startswith("TCGA-")
        }
    )
    gtex_tissues = {
        row["field_value"]
        for row in full_rows
        if row["source"] == "gtex" and row["field_name"] == "tissue" and row["term_type"] == "value"
    }

    concept_entries = []
    for concept in disease_concepts:
        concept_id = concept["concept_id"]
        tcga_rows = mappings_by_concept_source[(concept_id, "tcga_gdc")]
        gtex_rows = mappings_by_concept_source[(concept_id, "gtex")]
        geo_rows = mappings_by_concept_source[(concept_id, "geo")]

        has_tcga_project_mapping = any(row["target_field"] == "project.project_id" for row in tcga_rows)
        has_gtex_tissue_reference = any(row["target_value"] in gtex_tissues for row in gtex_rows)

        concept_entries.append(
            {
                "concept_id": concept_id,
                "concept_en": concept["concept_en"],
                "has_chinese_entry": bool(chinese_by_concept[concept_id]),
                "has_tcga_mapping": bool(tcga_rows),
                "has_tcga_project_mapping": has_tcga_project_mapping,
                "has_gtex_tissue_reference": has_gtex_tissue_reference,
                "has_geo_preview_terms": bool(geo_rows),
                "representative_chinese_terms": representative_items(chinese_by_concept[concept_id], "term_zh"),
            }
        )

    high_frequency = []
    missing_items: list[dict[str, Any]] = []
    concept_ids_present = {row["concept_id"] for row in disease_concepts}
    full_project_ids = set(tcga_project_ids)
    for item in HIGH_FREQUENCY_CANCERS:
        matched_concepts = [concept_id for concept_id in item["concept_ids"] if concept_id in concept_ids_present]
        chinese_present = any(chinese_by_concept[concept_id] for concept_id in matched_concepts)
        tcga_mapping_present = any(mappings_by_concept_source[(concept_id, "tcga_gdc")] for concept_id in matched_concepts)
        geo_present = any(mappings_by_concept_source[(concept_id, "geo")] for concept_id in matched_concepts)
        tcga_project_present = any(project_id in full_project_ids for project_id in item["tcga_project_ids"])
        gtex_reference_present = any(tissue in gtex_tissues for tissue in item["gtex_tissues"])
        english_full_present = tcga_project_present or any(
            row["display_label_en"].lower() == item["label"] or row["term_en"].lower() == item["label"]
            for row in full_rows
        )

        layer_flags = {
            "concept": bool(matched_concepts),
            "english_full": english_full_present,
            "chinese_concept": chinese_present,
            "source_mapping": tcga_mapping_present or geo_present,
            "tcga_project_mapping": tcga_project_present,
            "gtex_tissue_reference": gtex_reference_present,
            "geo_preview_terms": geo_present,
        }
        state = coverage_state(layer_flags)
        missing_layers = [name for name, present in layer_flags.items() if not present]
        if state != "fully_covered":
            missing_items.append({"kind": "disease", "label": item["label"], "missing_layers": missing_layers})

        high_frequency.append(
            {
                "label": item["label"],
                "status": state,
                "matched_concepts": matched_concepts,
                "missing_layers": missing_layers,
            }
        )

    return {
        "tcga_project_ids": tcga_project_ids,
        "disease_concepts": concept_entries,
        "high_frequency_status": high_frequency,
        "missing_items": missing_items,
    }


def build_tissue_coverage(
    concepts: list[dict[str, str]],
    mappings: list[dict[str, str]],
    full_rows: list[dict[str, str]],
    chinese_rows: list[dict[str, str]],
) -> dict[str, Any]:
    tissue_concepts = [row for row in concepts if row["concept_category"] == "tissue"]
    chinese_by_concept = defaultdict(list)
    for row in chinese_rows:
        chinese_by_concept[row["concept_id"]].append(row)

    mappings_by_concept_source = defaultdict(list)
    for row in mappings:
        mappings_by_concept_source[(row["concept_id"], row["source"])].append(row)

    gtex_tissues = sorted(
        {
            row["field_value"]
            for row in full_rows
            if row["source"] == "gtex" and row["field_name"] == "tissue" and row["term_type"] == "value"
        }
    )
    tcga_sites = {
        row["field_value"]
        for row in full_rows
        if row["source"] == "tcga_gdc" and row["field_name"] == "cases.primary_site" and row["term_type"] == "value"
    }

    concept_entries = []
    for concept in tissue_concepts:
        concept_id = concept["concept_id"]
        gtex_rows = mappings_by_concept_source[(concept_id, "gtex")]
        tcga_rows = mappings_by_concept_source[(concept_id, "tcga_gdc")]
        geo_rows = mappings_by_concept_source[(concept_id, "geo")]
        concept_entries.append(
            {
                "concept_id": concept_id,
                "concept_en": concept["concept_en"],
                "has_chinese_entry": bool(chinese_by_concept[concept_id]),
                "has_gtex_mapping": bool(gtex_rows),
                "has_tcga_primary_site_mapping": any(row["target_field"] == "cases.primary_site" for row in tcga_rows),
                "has_geo_preview_terms": bool(geo_rows),
                "representative_chinese_terms": representative_items(chinese_by_concept[concept_id], "term_zh"),
            }
        )

    high_frequency = []
    missing_items: list[dict[str, Any]] = []
    concept_ids_present = {row["concept_id"] for row in tissue_concepts}
    for item in HIGH_FREQUENCY_TISSUES:
        matched_concepts = [concept_id for concept_id in item["concept_ids"] if concept_id in concept_ids_present]
        chinese_present = any(chinese_by_concept[concept_id] for concept_id in matched_concepts)
        gtex_mapping_present = any(mappings_by_concept_source[(concept_id, "gtex")] for concept_id in matched_concepts)
        tcga_mapping_present = any(mappings_by_concept_source[(concept_id, "tcga_gdc")] for concept_id in matched_concepts)
        geo_present = any(mappings_by_concept_source[(concept_id, "geo")] for concept_id in matched_concepts)
        full_present = any(tissue in gtex_tissues for tissue in item["gtex_tissues"]) or any(site in tcga_sites for site in item["tcga_sites"])

        layer_flags = {
            "concept": bool(matched_concepts),
            "english_full": full_present,
            "chinese_concept": chinese_present,
            "source_mapping": gtex_mapping_present or tcga_mapping_present or geo_present,
            "gtex_mapping": gtex_mapping_present,
            "tcga_primary_site_mapping": tcga_mapping_present,
            "geo_preview_terms": geo_present,
        }
        state = coverage_state(layer_flags)
        missing_layers = [name for name, present in layer_flags.items() if not present]
        if state != "fully_covered":
            missing_items.append({"kind": "tissue", "label": item["label"], "missing_layers": missing_layers})
        high_frequency.append(
            {
                "label": item["label"],
                "status": state,
                "matched_concepts": matched_concepts,
                "missing_layers": missing_layers,
            }
        )

    return {
        "gtex_tissues": gtex_tissues,
        "tissue_concepts": concept_entries,
        "high_frequency_status": high_frequency,
        "missing_items": missing_items,
    }


def build_bias_flags(
    full_rows: list[dict[str, str]],
    concepts: list[dict[str, str]],
    mappings: list[dict[str, str]],
    chinese_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    disease_chinese = [row for row in chinese_rows if row["category_zh"] == "疾病"]
    tissue_chinese = [row for row in chinese_rows if row["category_zh"] == "组织"]
    tissue_concepts = [row for row in concepts if row["concept_category"] == "tissue"]
    disease_concepts = [row for row in concepts if row["concept_category"] == "disease"]
    thyroid_mapping_rows = [row for row in mappings if "thyroid" in row["concept_id"] or "thyroid" in row["target_value"].lower()]

    flags = []

    thyroid_disease_ratio = round(
        sum(1 for row in disease_chinese if "甲状腺" in row["term_zh"]) / max(len(disease_chinese), 1),
        4,
    )
    if thyroid_disease_ratio >= 0.5:
        flags.append(
            {
                "flag": "chinese_disease_skewed_to_thyroid",
                "severity": "high",
                "details": {"thyroid_ratio": thyroid_disease_ratio, "disease_term_count": len(disease_chinese)},
            }
        )

    thyroid_tissue_ratio = round(
        sum(1 for row in tissue_chinese if "甲状腺" in row["term_zh"]) / max(len(tissue_chinese), 1),
        4,
    )
    if thyroid_tissue_ratio >= 0.5:
        flags.append(
            {
                "flag": "chinese_tissue_skewed_to_thyroid",
                "severity": "high",
                "details": {"thyroid_ratio": thyroid_tissue_ratio, "tissue_term_count": len(tissue_chinese)},
            }
        )

    thyroid_mapping_ratio = round(len(thyroid_mapping_rows) / max(len(mappings), 1), 4)
    if thyroid_mapping_ratio >= 0.05:
        flags.append(
            {
                "flag": "preview_mapping_default_bias_to_thyroid_or_thca",
                "severity": "medium",
                "details": {"thyroid_mapping_ratio": thyroid_mapping_ratio, "thyroid_mapping_count": len(thyroid_mapping_rows)},
            }
        )

    if len(tissue_concepts) < 12:
        flags.append(
            {
                "flag": "tissue_concept_layer_still_sparse",
                "severity": "high",
                "details": {"tissue_concept_count": len(tissue_concepts)},
            }
        )
    if len([row for row in concepts if row["concept_category"] == "analysis_resource"]) < 8:
        flags.append(
            {
                "flag": "analysis_resource_layer_thin",
                "severity": "medium",
                "details": {"analysis_resource_concept_count": len([row for row in concepts if row["concept_category"] == "analysis_resource"])},
            }
        )
    if len([row for row in chinese_rows if row["category_zh"] == "疾病"]) <= 5:
        flags.append(
            {
                "flag": "chinese_disease_layer_very_sparse",
                "severity": "high",
                "details": {"chinese_disease_count": len(disease_chinese)},
            }
        )
    if len(disease_concepts) > 20 and len(disease_chinese) <= 5:
        flags.append(
            {
                "flag": "disease_concepts_exist_but_chinese_bridge_is_thin",
                "severity": "high",
                "details": {"disease_concept_count": len(disease_concepts), "chinese_disease_count": len(disease_chinese)},
            }
        )

    return flags


def build_next_recommended_expansions(
    disease_coverage: dict[str, Any],
    tissue_coverage: dict[str, Any],
    bias_flags: list[dict[str, Any]],
) -> list[str]:
    recommendations: list[str] = []

    missing_diseases = [row["label"] for row in disease_coverage["high_frequency_status"] if row["status"] != "fully_covered"][:5]
    if missing_diseases:
        recommendations.append(
            "Expand Chinese disease entry points beyond thyroid-first coverage, starting with: "
            + ", ".join(missing_diseases)
            + "."
        )

    missing_tissues = [row["label"] for row in tissue_coverage["high_frequency_status"] if row["status"] != "fully_covered"][:5]
    if missing_tissues:
        recommendations.append(
            "Add shared tissue concepts and Chinese bridges for: "
            + ", ".join(missing_tissues)
            + "."
        )

    if any(flag["flag"] == "preview_mapping_default_bias_to_thyroid_or_thca" for flag in bias_flags):
        recommendations.append(
            "Reduce THCA/thyroid default bias by adding disease and tissue preview paths for BRCA, LUAD, LIHC, COAD/READ, and STAD."
        )

    recommendations.append(
        "Add umbrella concepts that are currently missing but important for navigation, such as colorectal cancer, gastric cancer, prostate cancer, pancreatic cancer, ovarian cancer, melanoma, leukemia, lymphoma, and lymphoid tissue."
    )
    recommendations.append(
        "Keep GEO in the concept-to-query-expansion layer only, but broaden GEO preview terms once non-thyroid Chinese concepts are added."
    )
    return recommendations


def build_markdown_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Lexicon Coverage Audit")
    lines.append("")
    lines.append("## Category Coverage")
    lines.append("")
    for category, details in report["category_coverage"].items():
        lines.append(f"### {category}")
        lines.append("")
        for source, stats in details["by_source"].items():
            if source == "database_agnostic_concepts":
                lines.append(
                    f"- concept layer: {stats['concept_count']} concepts; examples: {', '.join(stats['representative_concepts']) or 'none'}"
                )
            else:
                lines.append(
                    f"- {source}: full={stats['full_term_count']}, mappings={stats['mapping_count']}, terms={', '.join(stats['representative_terms']) or 'none'}, mapping targets={', '.join(stats['representative_mapping_targets']) or 'none'}"
                )
        lines.append(f"- bias note: {details['bias_note']}")
        if details["missing_layer_flags"]:
            lines.append(f"- missing layer flags: {', '.join(details['missing_layer_flags'])}")
        lines.append("")

    lines.append("## Disease Coverage")
    lines.append("")
    lines.append("### TCGA project IDs")
    lines.append("")
    lines.append(", ".join(report["disease_coverage"]["tcga_project_ids"]))
    lines.append("")
    lines.append("### High-frequency cancer status")
    lines.append("")
    for item in report["disease_coverage"]["high_frequency_status"]:
        lines.append(
            f"- {item['label']}: {item['status']} (missing: {', '.join(item['missing_layers']) or 'none'})"
        )
    lines.append("")
    lines.append("## Tissue Coverage")
    lines.append("")
    lines.append("### GTEx tissues")
    lines.append("")
    lines.append(", ".join(report["tissue_coverage"]["gtex_tissues"]))
    lines.append("")
    lines.append("### High-frequency tissue status")
    lines.append("")
    for item in report["tissue_coverage"]["high_frequency_status"]:
        lines.append(
            f"- {item['label']}: {item['status']} (missing: {', '.join(item['missing_layers']) or 'none'})"
        )
    lines.append("")
    lines.append("## Bias Flags")
    lines.append("")
    for flag in report["bias_flags"]:
        lines.append(f"- {flag['flag']} [{flag['severity']}]: {json.dumps(flag['details'], ensure_ascii=False)}")
    lines.append("")
    lines.append("## Recommended Next Expansions")
    lines.append("")
    for item in report["next_recommended_expansions"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def build_coverage_audit_report() -> dict[str, Any]:
    concepts = load_csv(CONCEPTS_PATH)
    mappings = load_csv(MAPPINGS_PATH)
    full_rows = load_csv(FULL_PATH)
    curated_rows = load_csv(CURATED_PATH)
    alias_rows = load_csv(ALIASES_PATH)
    chinese_rows = load_csv(CHINESE_TERMS_PATH)

    category_coverage = build_category_coverage(full_rows, concepts, mappings)
    disease_coverage = build_disease_coverage(concepts, mappings, full_rows, chinese_rows)
    tissue_coverage = build_tissue_coverage(concepts, mappings, full_rows, chinese_rows)
    bias_flags = build_bias_flags(full_rows, concepts, mappings, chinese_rows)

    report = {
        "summary": {
            "concept_count": len(concepts),
            "mapping_count": len(mappings),
            "full_term_count": len(full_rows),
            "curated_term_count": len(curated_rows),
            "alias_count": len(alias_rows),
            "chinese_term_count": len(chinese_rows),
        },
        "category_coverage": category_coverage,
        "disease_coverage": disease_coverage,
        "tissue_coverage": tissue_coverage,
        "missing_items": disease_coverage["missing_items"] + tissue_coverage["missing_items"],
        "bias_flags": bias_flags,
        "next_recommended_expansions": build_next_recommended_expansions(disease_coverage, tissue_coverage, bias_flags),
    }
    return report


def write_report_files(report: dict[str, Any]) -> tuple[Path, Path]:
    REPORT_JSON_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(build_markdown_report(report), encoding="utf-8")
    return REPORT_JSON_PATH, REPORT_MD_PATH


def main() -> None:
    report = build_coverage_audit_report()
    json_path, md_path = write_report_files(report)
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
