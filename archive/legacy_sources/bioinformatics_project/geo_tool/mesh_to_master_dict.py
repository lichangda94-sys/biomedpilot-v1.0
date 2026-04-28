import argparse
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict, field
from typing import List


@dataclass
class MeshTerm:
    canonical_id: str
    canonical_name: str
    entry_terms: List[str] = field(default_factory=list)
    tree_numbers: List[str] = field(default_factory=list)
    category: str = ""
    source: str = "MeSH"
    scope_note: str = ""


def infer_category(name: str, tree_numbers: List[str]) -> str:
    lower_name = name.lower()
    joined_tree = " ".join(tree_numbers)

    endocrine_keywords = [
        "thyroid", "parathyroid", "pituitary", "adrenal",
        "pheochromocytoma", "paraganglioma", "neuroendocrine",
        "pancreatic neuroendocrine", "multiple endocrine neoplasia",
    ]
    exposure_keywords = [
        "obesity", "overweight", "alcohol", "smoking", "tobacco",
        "cholesterol", "hypercholesterolemia", "hyperlipidemia",
        "diabetes", "metabolic syndrome", "radiation", "pesticides",
        "endocrine disruptor", "air pollution",
    ]

    if any(k in lower_name for k in endocrine_keywords):
        return "endocrine_tumor"
    if any(k in lower_name for k in exposure_keywords):
        return "exposure"

    if joined_tree.startswith("C"):
        return "disease"
    if joined_tree.startswith("F"):
        return "phenomenon_or_process"
    return "other"


def parse_mesh_desc_xml(xml_path: str) -> List[MeshTerm]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    results: List[MeshTerm] = []

    for record in root.findall("DescriptorRecord"):
        ui = record.findtext("DescriptorUI", default="").strip()
        name = record.findtext("DescriptorName/String", default="").strip()
        scope_note = record.findtext("ScopeNote", default="").strip()

        tree_numbers = []
        tree_list = record.find("TreeNumberList")
        if tree_list is not None:
            for node in tree_list.findall("TreeNumber"):
                if node.text:
                    tree_numbers.append(node.text.strip())

        entry_terms = []
        concept_list = record.find("ConceptList")
        if concept_list is not None:
            for concept in concept_list.findall("Concept"):
                term_list = concept.find("TermList")
                if term_list is not None:
                    for term in term_list.findall("Term"):
                        t = term.findtext("String", default="").strip()
                        if t:
                            entry_terms.append(t)

        entry_terms = list(dict.fromkeys(entry_terms))
        if name and name in entry_terms:
            entry_terms.remove(name)

        category = infer_category(name, tree_numbers)

        results.append(
            MeshTerm(
                canonical_id=ui,
                canonical_name=name,
                entry_terms=entry_terms,
                tree_numbers=tree_numbers,
                category=category,
                source="MeSH",
                scope_note=scope_note,
            )
        )

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--desc", required=True, help="Path to MeSH descriptor XML")
    parser.add_argument("--out", required=True, help="Output JSON file")
    args = parser.parse_args()

    terms = parse_mesh_desc_xml(args.desc)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump([asdict(x) for x in terms], f, ensure_ascii=False, indent=2)

    print(f"Saved {len(terms)} records to {args.out}")


if __name__ == "__main__":
    main()
