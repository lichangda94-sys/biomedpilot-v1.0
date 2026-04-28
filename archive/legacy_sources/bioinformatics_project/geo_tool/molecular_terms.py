"""Molecular event and biomarker term dictionary for Chinese-driven GEO search."""

from __future__ import annotations


def _entry(canonical: str, aliases: list[str], english_terms: list[str]) -> dict:
    return {
        "canonical": canonical,
        "aliases": aliases,
        "english_terms": english_terms,
    }


MOLECULAR_TERMS = [
    _entry("braf突变", ["braf突变", "braf", "brafv600e"], ["BRAF", "BRAF V600E", "BRAFV600E"]),
    _entry("ret融合", ["ret融合", "ret", "ret/ptc"], ["RET fusion", "RET/PTC", "RET rearrangement"]),
    _entry("ras突变", ["ras", "ras突变", "nras", "hras", "kras"], ["RAS mutation", "NRAS", "HRAS", "KRAS"]),
    _entry("egfr突变", ["egfr", "egfr突变"], ["EGFR", "EGFR mutation"]),
    _entry("alk融合", ["alk", "alk融合"], ["ALK fusion", "ALK rearrangement"]),
    _entry("tp53突变", ["tp53", "p53", "tp53突变"], ["TP53", "p53", "TP53 mutation"]),
    _entry("tert启动子突变", ["tert", "tert启动子", "tert启动子突变"], ["TERT promoter mutation", "TERT"]),
    _entry("pik3ca突变", ["pik3ca", "pik3ca突变"], ["PIK3CA", "PIK3CA mutation"]),
    _entry("idh突变", ["idh", "idh1", "idh2", "idh突变"], ["IDH mutation", "IDH1", "IDH2"]),
    _entry("ntrk融合", ["ntrk", "ntrk融合"], ["NTRK fusion", "TRK fusion"]),
    _entry("myc扩增", ["myc扩增", "myc"], ["MYC amplification", "MYC"]),
    _entry("her2扩增", ["her2", "erbb2", "her2扩增"], ["HER2", "ERBB2", "HER2 amplification"]),
    _entry("msi", ["msi", "微卫星不稳定"], ["microsatellite instability", "MSI"]),
    _entry("tmb", ["tmb", "肿瘤突变负荷"], ["tumor mutation burden", "TMB"]),
    _entry("pdl1", ["pdl1", "pd-l1", "cd274"], ["PD-L1", "CD274"]),
    _entry("pd1", ["pd1", "pd-1", "pdcd1"], ["PD-1", "PDCD1"]),
    _entry("ctla4", ["ctla4", "ctla-4"], ["CTLA-4", "CTLA4"]),
    _entry("肿瘤干性", ["肿瘤干性", "癌症干细胞"], ["cancer stem cell", "stemness"]),
    _entry("上皮间质转化", ["上皮间质转化", "emt"], ["epithelial mesenchymal transition", "EMT"]),
]
