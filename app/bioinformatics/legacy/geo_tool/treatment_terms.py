"""Treatment and intervention term dictionary for Chinese-driven GEO search."""

from __future__ import annotations


def _entry(canonical: str, aliases: list[str], english_terms: list[str]) -> dict:
    return {
        "canonical": canonical,
        "aliases": aliases,
        "english_terms": english_terms,
    }


TREATMENT_TERMS = [
    _entry("免疫治疗", ["免疫治疗", "免疫", "iccr", "car-t", "t细胞治疗"], ["immunotherapy", "engineered T cell", "T cell", "ICCR", "CAR-T"]),
    _entry("化疗", ["化疗", "化学治疗"], ["chemotherapy", "cytotoxic therapy"]),
    _entry("放疗", ["放疗", "放射治疗"], ["radiotherapy", "radiation therapy"]),
    _entry("靶向治疗", ["靶向治疗", "靶向药"], ["targeted therapy", "molecular targeted therapy"]),
    _entry("药物处理", ["药物", "药物处理", "药物干预", "治疗", "抑制剂"], ["treatment", "drug response", "inhibitor", "therapy"]),
    _entry("激酶抑制剂", ["激酶抑制剂", "tkis", "tki"], ["kinase inhibitor", "TKI", "tyrosine kinase inhibitor"]),
    _entry("braf抑制剂", ["braf抑制剂", "vemurafenib", "dabrafenib"], ["BRAF inhibitor", "vemurafenib", "dabrafenib"]),
    _entry("mek抑制剂", ["mek抑制剂", "trametinib"], ["MEK inhibitor", "trametinib"]),
    _entry("egfr抑制剂", ["egfr抑制剂", "gefitinib", "erlotinib", "osimertinib"], ["EGFR inhibitor", "gefitinib", "erlotinib", "osimertinib"]),
    _entry("免疫检查点抑制剂", ["pd1", "pdl1", "ctla4", "免疫检查点抑制剂"], ["immune checkpoint inhibitor", "PD-1", "PD-L1", "CTLA-4"]),
    _entry("敲低", ["敲低", "干扰", "sirna", "shrna"], ["knockdown", "siRNA", "shRNA"]),
    _entry("过表达", ["过表达", "转染", "过表达模型"], ["overexpression", "transfection"]),
    _entry("敲除", ["敲除", "crisper", "crispr", "基因敲除"], ["knockout", "CRISPR", "gene knockout"]),
]
