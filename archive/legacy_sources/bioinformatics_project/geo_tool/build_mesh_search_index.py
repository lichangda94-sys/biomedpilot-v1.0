import argparse
import json
from typing import Dict, List


DISEASE_KEYWORDS = [
    "neoplasm", "tumor", "tumour", "carcinoma", "adenoma",
    "pheochromocytoma", "paraganglioma", "prolactinoma",
    "insulinoma", "gastrinoma", "glucagonoma",
    "somatostatinoma", "vipoma",
]

METADATA_WHITELIST = {
    "Obesity",
    "Overweight",
    "Alcohol Drinking",
    "Smoking",
    "Tobacco Use Disorder",
    "Air Pollution",
    "Radiation Exposure",
    "Hypercholesterolemia",
    "Cholesterol",
    "Hyperlipidemias",
    "Diabetes Mellitus",
    "Metabolic Syndrome",
    "Pesticides",
    "Endocrine Disruptors",

    "Child",
    "Adolescent",
    "Adult",
    "Aged",
    "Female",
    "Male",

    "China",
    "United States",
    "Japan",
    "South Korea",
    "Asia",
    "Europe",
}


def normalize_terms(terms: List[str]) -> List[str]:
    cleaned = []
    for t in terms:
        t = t.strip()
        if t:
            cleaned.append(t)
    return list(dict.fromkeys(cleaned))


def infer_search_bucket(name: str, category: str) -> str:
    lower_name = name.lower()

    if category == "endocrine_tumor":
        if any(k in lower_name for k in DISEASE_KEYWORDS):
            return "disease"

    if name in METADATA_WHITELIST:
        return "metadata"

    return ""


def build_search_index(records: List[dict]) -> Dict[str, dict]:
    index = {}

    for rec in records:
        canonical_name = rec.get("canonical_name", "").strip()
        if not canonical_name:
            continue

        category = rec.get("category", "")
        bucket = infer_search_bucket(canonical_name, category)
        if not bucket:
            continue

        entry_terms = rec.get("entry_terms", [])
        all_terms = normalize_terms([canonical_name] + entry_terms)

        index[canonical_name] = {
            "canonical_id": rec.get("canonical_id", ""),
            "canonical_name": canonical_name,
            "english_terms": all_terms,
            "tree_numbers": rec.get("tree_numbers", []),
            "category": bucket,
            "source": rec.get("source", "MeSH"),
            "scope_note": rec.get("scope_note", ""),
        }

    return index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="mesh_master_dict.json")
    parser.add_argument("--out", required=True, help="mesh_search_index.json")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        records = json.load(f)

    index = build_search_index(records)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(index)} searchable entries to {args.out}")


if __name__ == "__main__":
    main()
