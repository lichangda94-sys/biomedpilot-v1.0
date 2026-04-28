"""Exposure and intervention term dictionary for Chinese-driven GEO search."""

from __future__ import annotations


def _entry(canonical: str, aliases: list[str], english_terms: list[str]) -> dict:
    return {
        "canonical": canonical,
        "aliases": aliases,
        "english_terms": english_terms,
    }


EXPOSURE_TERMS = [
    _entry("肥胖", ["肥胖", "超重", "obesity"], ["obesity", "obese", "overweight"]),
    _entry("高脂饮食", ["高脂饮食", "高脂", "高脂膳食", "hfd"], ["high fat diet", "HFD", "high fat feeding"]),
    _entry("糖尿病", ["糖尿病", "2型糖尿病", "t2dm"], ["diabetes", "type 2 diabetes", "T2DM"]),
    _entry("胰岛素抵抗", ["胰岛素抵抗"], ["insulin resistance"]),
    _entry("吸烟", ["吸烟", "烟草", "香烟", "抽烟"], ["smoking", "tobacco", "cigarette smoke"]),
    _entry("饮酒", ["饮酒", "酒精", "乙醇", "酗酒"], ["alcohol", "ethanol", "alcohol drinking"]),
    _entry("辐射", ["辐射", "电离辐射", "放射线"], ["radiation", "ionizing radiation", "irradiation"]),
    _entry("碘缺乏", ["碘缺乏", "缺碘"], ["iodine deficiency", "low iodine"]),
    _entry("碘过量", ["碘过量", "高碘"], ["iodine excess", "high iodine"]),
    _entry("重金属", ["重金属", "重金属暴露", "镉", "砷", "铅", "汞", "铬", "镍"], ["heavy metal", "heavy metals", "metal exposure", "cadmium", "arsenic", "lead", "mercury", "chromium", "nickel"]),
    _entry("空气污染", ["空气污染", "pm2.5", "pm10", "颗粒物"], ["air pollution", "PM2.5", "PM10", "particulate matter"]),
    _entry("石棉", ["石棉"], ["asbestos"]),
    _entry("农药", ["农药", "杀虫剂"], ["pesticide", "pesticides", "insecticide"]),
    _entry("除草剂", ["除草剂"], ["herbicide", "herbicides"]),
    _entry("内分泌干扰物", ["内分泌干扰物", "环境雌激素", "双酚a", "bpa", "邻苯二甲酸酯"], ["endocrine disruptor", "endocrine disrupting chemical", "bisphenol A", "BPA", "phthalate"]),
    _entry("雌激素", ["雌激素", "estrogen", "雌二醇"], ["estrogen", "estradiol", "E2"]),
    _entry("雄激素", ["雄激素", "androgen"], ["androgen", "testosterone"]),
    _entry("甲状腺激素", ["甲状腺激素", "t3", "t4", "促甲状腺激素", "tsh"], ["thyroid hormone", "T3", "T4", "TSH"]),
    _entry("缺氧", ["缺氧", "低氧"], ["hypoxia", "hypoxic"]),
    _entry("炎症", ["炎症", "慢性炎症"], ["inflammation", "chronic inflammation", "inflammatory"]),
    _entry("氧化应激", ["氧化应激"], ["oxidative stress", "ROS", "reactive oxygen species"]),
    _entry("感染", ["感染", "病毒感染", "细菌感染"], ["infection", "viral infection", "bacterial infection"]),
    _entry("hpv感染", ["hpv", "hpv感染", "人乳头瘤病毒"], ["HPV", "human papillomavirus"]),
    _entry("hbv感染", ["hbv", "乙肝病毒", "hbv感染"], ["HBV", "hepatitis B virus"]),
    _entry("hcv感染", ["hcv", "丙肝病毒", "hcv感染"], ["HCV", "hepatitis C virus"]),
    _entry("ebv感染", ["ebv", "eb病毒", "ebv感染"], ["EBV", "Epstein Barr virus"]),
    _entry("幽门螺杆菌感染", ["幽门螺杆菌", "hp感染"], ["Helicobacter pylori", "H. pylori"]),
    _entry("转录组", ["转录组", "表达谱", "芯片", "微阵列"], ["transcriptome", "gene expression", "microarray", "expression profiling"]),
    _entry("单细胞", ["单细胞", "单细胞测序", "scrna"], ["single cell", "single cell RNA sequencing", "scRNA-seq"]),
    _entry("甲基化", ["甲基化", "dna甲基化"], ["methylation", "DNA methylation"]),
    _entry("ferroptosis", ["铁死亡", "ferroptosis"], ["ferroptosis"]),
    _entry("自噬", ["自噬", "autophagy"], ["autophagy"]),
    _entry("凋亡", ["凋亡", "apoptosis"], ["apoptosis"]),
]
