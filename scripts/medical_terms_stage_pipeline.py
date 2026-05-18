from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
MEDICAL_TERMS = ROOT / "data" / "medical_terms"
DOCS_MEDICAL_TERMS = ROOT / "docs" / "medical_terms"
DEFAULT_EXTERNAL_CORPUS = Path("/Users/changdali/Desktop/vocabularypool/LSTM-CRF-medical-master/datasets")
TODAY = date.today().isoformat()

TCGA_PROJECTS: tuple[tuple[str, str, str], ...] = (
    ("TCGA-ACC", "adrenocortical carcinoma", "肾上腺皮质癌"),
    ("TCGA-BLCA", "bladder urothelial carcinoma", "膀胱尿路上皮癌"),
    ("TCGA-BRCA", "breast invasive carcinoma", "乳腺癌"),
    ("TCGA-CESC", "cervical squamous cell carcinoma and endocervical adenocarcinoma", "宫颈癌"),
    ("TCGA-CHOL", "cholangiocarcinoma", "胆管癌"),
    ("TCGA-COAD", "colon adenocarcinoma", "结肠癌"),
    ("TCGA-DLBC", "diffuse large B-cell lymphoma", "弥漫大B细胞淋巴瘤"),
    ("TCGA-ESCA", "esophageal carcinoma", "食管癌"),
    ("TCGA-GBM", "glioblastoma", "胶质母细胞瘤"),
    ("TCGA-HNSC", "head and neck squamous cell carcinoma", "头颈鳞癌"),
    ("TCGA-KICH", "kidney chromophobe", "肾嫌色细胞癌"),
    ("TCGA-KIRC", "kidney renal clear cell carcinoma", "肾透明细胞癌"),
    ("TCGA-KIRP", "kidney renal papillary cell carcinoma", "肾乳头状细胞癌"),
    ("TCGA-LAML", "acute myeloid leukemia", "急性髓系白血病"),
    ("TCGA-LGG", "lower grade glioma", "低级别胶质瘤"),
    ("TCGA-LIHC", "liver hepatocellular carcinoma", "肝细胞癌"),
    ("TCGA-LUAD", "lung adenocarcinoma", "肺腺癌"),
    ("TCGA-LUSC", "lung squamous cell carcinoma", "肺鳞癌"),
    ("TCGA-MESO", "mesothelioma", "间皮瘤"),
    ("TCGA-OV", "ovarian serous cystadenocarcinoma", "卵巢浆液性囊腺癌"),
    ("TCGA-PAAD", "pancreatic adenocarcinoma", "胰腺癌"),
    ("TCGA-PCPG", "pheochromocytoma and paraganglioma", "嗜铬细胞瘤和副神经节瘤"),
    ("TCGA-PRAD", "prostate adenocarcinoma", "前列腺癌"),
    ("TCGA-READ", "rectum adenocarcinoma", "直肠癌"),
    ("TCGA-SARC", "sarcoma", "肉瘤"),
    ("TCGA-SKCM", "skin cutaneous melanoma", "皮肤黑色素瘤"),
    ("TCGA-STAD", "stomach adenocarcinoma", "胃癌"),
    ("TCGA-TGCT", "testicular germ cell tumor", "睾丸生殖细胞肿瘤"),
    ("TCGA-THCA", "thyroid carcinoma", "甲状腺癌"),
    ("TCGA-THYM", "thymoma", "胸腺瘤"),
    ("TCGA-UCEC", "uterine corpus endometrial carcinoma", "子宫内膜癌"),
    ("TCGA-UCS", "uterine carcinosarcoma", "子宫癌肉瘤"),
    ("TCGA-UVM", "uveal melanoma", "葡萄膜黑色素瘤"),
)

GTEX_TISSUES: tuple[tuple[str, str, str], ...] = (
    ("Thyroid", "甲状腺", "organ"),
    ("Breast - Mammary Tissue", "乳腺", "tissue"),
    ("Lung", "肺", "organ"),
    ("Liver", "肝脏", "organ"),
    ("Pancreas", "胰腺", "organ"),
    ("Prostate", "前列腺", "organ"),
    ("Colon - Sigmoid", "乙状结肠", "tissue"),
    ("Colon - Transverse", "横结肠", "tissue"),
    ("Whole Blood", "全血", "body_fluid"),
    ("Skin", "皮肤", "tissue"),
    ("Stomach", "胃", "organ"),
    ("Esophagus", "食管", "organ"),
    ("Heart", "心脏", "organ"),
    ("Adipose Tissue", "脂肪组织", "tissue"),
    ("Muscle", "肌肉", "tissue"),
    ("Brain", "脑", "organ"),
    ("Kidney", "肾脏", "organ"),
    ("Spleen", "脾脏", "organ"),
    ("Small Intestine", "小肠", "organ"),
    ("Artery", "动脉", "tissue"),
    ("Nerve", "神经", "tissue"),
    ("Pituitary", "垂体", "organ"),
    ("Adrenal Gland", "肾上腺", "organ"),
)

GEO_CORE_TERMS: dict[str, tuple[str, ...]] = {
    "omics_assay": (
        "RNA-seq",
        "bulk RNA-seq",
        "single-cell RNA-seq",
        "scRNA-seq",
        "microarray",
        "expression profiling",
        "transcriptome profiling",
        "methylation profiling",
        "miRNA profiling",
        "proteomics",
    ),
    "species": ("Homo sapiens", "human", "Mus musculus", "mouse", "Rattus norvegicus", "rat"),
    "sample_status": (
        "tumor",
        "normal",
        "adjacent normal",
        "case",
        "control",
        "primary",
        "metastatic",
        "recurrent",
        "cell line",
        "tissue",
        "blood",
        "serum",
        "plasma",
    ),
    "treatment_status": ("treated", "untreated", "vehicle", "sham", "resistant", "sensitive"),
    "grouping_modifier": ("wild type", "mutant", "knockdown", "overexpression"),
    "data_format": (
        "count matrix",
        "raw counts",
        "TPM",
        "FPKM",
        "RPKM",
        "CPM",
        "gene symbol",
        "Ensembl ID",
        "probe ID",
        "series matrix",
        "sample metadata",
    ),
    "platform_term": ("platform annotation",),
    "stop_term": ("dataset", "sample", "series"),
}

SOURCE_FILES: tuple[tuple[str, str, str], ...] = (
    ("disease_new2.dic", "disease_dictionary", "disease"),
    ("disease_new.dic", "disease_dictionary", "disease"),
    ("symptom_new2.dic", "symptom_dictionary", "symptom"),
    ("body中文身体部位名称.txt", "anatomy_dictionary", "anatomy_or_tissue"),
)

DEFAULT_STOP_TERMS = {
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
    "不舒服",
    "难受",
    "身体不好",
    "有问题",
    "毛病",
    "状态差",
    "表1",
    "观察指标",
    "资料与方法",
    "纳入标准",
    "排除标准",
    "统计学方法",
    "参考文献",
}

FUTURE_SCOPE_TERMS = {"气虚", "血瘀", "痰湿", "湿热", "肾虚", "脾虚", "上火", "体寒"}

CURATED_META_MAPPINGS: dict[str, dict[str, Any]] = {
    "糖尿病前期": {
        "concept_id": "meta_exposure:prediabetes",
        "preferred_label_en": "prediabetes",
        "synonyms_en": ["pre-diabetes", "prediabetic state", "impaired fasting glucose", "impaired glucose tolerance", "IFG", "IGT"],
        "mesh_terms": ["Prediabetic State"],
        "concept_type": "exposure",
        "pico_roles": ["exposure"],
        "meta_profiles": ["exposure_disease_risk_meta"],
        "standalone_search_allowed": "conditional",
        "requires_pairing_with": ["population_or_disease"],
    },
    "甲状腺癌": {
        "concept_id": "meta_disease:thyroid_cancer",
        "preferred_label_en": "thyroid cancer",
        "synonyms_en": ["thyroid neoplasm", "thyroid carcinoma"],
        "mesh_terms": ["Thyroid Neoplasms"],
        "concept_type": "disease",
        "pico_roles": ["population", "disease"],
        "meta_profiles": ["disease_meta", "exposure_disease_risk_meta"],
        "standalone_search_allowed": "conditional",
        "requires_pairing_with": [],
    },
    "乳腺癌": {
        "concept_id": "meta_disease:breast_cancer",
        "preferred_label_en": "breast cancer",
        "synonyms_en": ["breast neoplasm", "mammary carcinoma"],
        "mesh_terms": ["Breast Neoplasms"],
        "concept_type": "disease",
        "pico_roles": ["population", "disease"],
        "meta_profiles": ["disease_meta", "exposure_disease_risk_meta"],
        "standalone_search_allowed": "conditional",
        "requires_pairing_with": [],
    },
    "2型糖尿病": {
        "concept_id": "meta_disease:type_2_diabetes",
        "preferred_label_en": "type 2 diabetes mellitus",
        "synonyms_en": ["type 2 diabetes", "T2DM", "non-insulin-dependent diabetes mellitus"],
        "mesh_terms": ["Diabetes Mellitus, Type 2"],
        "concept_type": "disease",
        "pico_roles": ["population", "disease"],
        "meta_profiles": ["disease_meta", "intervention_effect_meta"],
        "standalone_search_allowed": "conditional",
        "requires_pairing_with": [],
    },
    "肥胖": {
        "concept_id": "meta_exposure:obesity",
        "preferred_label_en": "obesity",
        "synonyms_en": ["overweight", "body mass index", "BMI"],
        "mesh_terms": ["Obesity", "Body Mass Index"],
        "concept_type": "risk_factor",
        "pico_roles": ["exposure"],
        "meta_profiles": ["exposure_disease_risk_meta"],
        "standalone_search_allowed": "conditional",
        "requires_pairing_with": ["population_or_disease"],
    },
    "放射性碘治疗": {
        "concept_id": "meta_intervention:radioactive_iodine_therapy",
        "preferred_label_en": "radioactive iodine therapy",
        "synonyms_en": ["radioiodine therapy", "I-131 therapy", "radioactive iodine ablation", "RAI"],
        "mesh_terms": ["Radioisotopes", "Iodine Radioisotopes"],
        "concept_type": "intervention",
        "pico_roles": ["intervention"],
        "meta_profiles": ["intervention_effect_meta"],
        "standalone_search_allowed": "conditional",
        "requires_pairing_with": ["population_or_disease"],
    },
    "二甲双胍": {
        "concept_id": "meta_intervention:metformin",
        "preferred_label_en": "metformin",
        "synonyms_en": ["metformin hydrochloride"],
        "mesh_terms": ["Metformin"],
        "concept_type": "intervention",
        "pico_roles": ["intervention"],
        "meta_profiles": ["intervention_effect_meta"],
        "standalone_search_allowed": "conditional",
        "requires_pairing_with": ["population_or_disease"],
    },
    "复发": {
        "concept_id": "meta_outcome:recurrence",
        "preferred_label_en": "recurrence",
        "synonyms_en": ["relapse", "disease recurrence"],
        "mesh_terms": ["Recurrence"],
        "concept_type": "outcome",
        "pico_roles": ["outcome"],
        "meta_profiles": ["intervention_effect_meta", "prognosis_meta"],
        "standalone_search_allowed": "conditional",
        "requires_pairing_with": ["population_or_disease"],
    },
    "风险": {
        "concept_id": "meta_research_intent:risk",
        "preferred_label_en": "risk",
        "synonyms_en": ["risk factor", "risk association"],
        "mesh_terms": [],
        "concept_type": "research_intent",
        "pico_roles": ["research_intent"],
        "meta_profiles": ["exposure_disease_risk_meta"],
        "standalone_search_allowed": False,
        "requires_pairing_with": ["population_or_disease", "exposure"],
        "query_expansion_allowed": False,
    },
    "危险因素": {
        "concept_id": "meta_research_intent:risk_factor",
        "preferred_label_en": "risk factor",
        "synonyms_en": ["risk factors", "risk association"],
        "mesh_terms": ["Risk Factors"],
        "concept_type": "research_intent",
        "pico_roles": ["research_intent"],
        "meta_profiles": ["exposure_disease_risk_meta"],
        "standalone_search_allowed": False,
        "requires_pairing_with": ["population_or_disease", "exposure"],
        "query_expansion_allowed": False,
    },
    "Meta分析": {
        "concept_id": "meta_study_design:meta_analysis",
        "preferred_label_en": "meta-analysis",
        "synonyms_en": ["systematic review", "meta analysis"],
        "mesh_terms": ["Meta-Analysis as Topic"],
        "concept_type": "study_design",
        "pico_roles": ["study_design"],
        "meta_profiles": ["evidence_synthesis"],
        "standalone_search_allowed": False,
        "requires_pairing_with": ["population_or_disease"],
    },
}

NORMALIZATION_ALIASES = {"Ⅱ型糖尿病": "2型糖尿病", "II型糖尿病": "2型糖尿病", "二型糖尿病": "2型糖尿病"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_zh_candidate(term: str) -> tuple[str, list[str]]:
    actions: list[str] = []
    original = term
    normalized = unicodedata.normalize("NFKC", term).strip()
    if normalized != original:
        actions.append("fullwidth_to_halfwidth")
    replacements = {
        "（": "(",
        "）": ")",
        "，": ",",
        "％": "%",
        "Ⅱ": "2",
        "Ⅲ": "3",
        "Ⅳ": "4",
        "Ⅰ": "1",
    }
    for src, dst in replacements.items():
        if src in normalized:
            normalized = normalized.replace(src, dst)
            actions.append("punctuation_or_roman_normalization")
    for src, dst in NORMALIZATION_ALIASES.items():
        if normalized == src:
            normalized = dst
            actions.append("roman_or_chinese_type_to_arabic")
    normalized = re.sub(r"\s+", "", normalized)
    normalized = normalized.replace("II型", "2型").replace("Ⅱ型", "2型").replace("二型", "2型")
    return normalized, sorted(set(actions))


def split_parenthetical_alias(term: str) -> tuple[str, list[str]]:
    match = re.search(r"^(.+?)\(([^()]{1,20})\)$", term)
    if not match:
        return term, []
    head, alias = match.group(1).strip(), match.group(2).strip()
    return head, [alias] if alias else []


def clean_source_line(line: str, source_type: str) -> str:
    text = line.strip().strip("\ufeff")
    if not text:
        return ""
    if source_type == "anatomy_dictionary":
        text = re.sub(r"\s+n$", "", text).strip()
    if "," in text and text.split(",", 1)[0].isdigit():
        text = text.split(",", 1)[1].strip()
    if text.startswith(","):
        return ""
    return text


def classification_for_term(term: str, source_type: str, source_label: str) -> tuple[str, str]:
    if not term or term in DEFAULT_STOP_TERMS:
        return "rejected", "default_stop_term"
    if term in FUTURE_SCOPE_TERMS:
        return "future_scope", "future_tcm_or_chinese_specific_scope"
    if len(term) > 40 or re.search(r"[。；;]", term):
        return "rejected", "long_or_sentence_like_candidate"
    if source_type == "anatomy_dictionary":
        return "evidence_only", "anatomy_terms_are_evidence_for_meta_not_runtime_candidates"
    if source_label == "symptom":
        return "normalized", "symptom_or_outcome_candidate_requires_review"
    return "normalized", "candidate_requires_review"


def curated_mapping_for(term: str) -> dict[str, Any] | None:
    return CURATED_META_MAPPINGS.get(term)


def make_query_usage(concept_type: str) -> dict[str, bool]:
    return {
        "english_database_search": concept_type not in {"stop_term"},
        "chinese_database_search": False,
        "english_pdf_extraction": concept_type in {"outcome", "effect_measure", "study_design", "intervention", "risk_factor", "exposure", "disease"},
        "chinese_pdf_extraction": False,
    }


def meta_runtime_entry(term: str, mapping: dict[str, Any], source_evidence: list[dict[str, Any]]) -> dict[str, Any]:
    concept_type = str(mapping["concept_type"])
    query_expansion_allowed = bool(mapping.get("query_expansion_allowed", concept_type not in {"effect_measure", "research_intent"}))
    return {
        "concept_id": mapping["concept_id"],
        "zh_terms": sorted({term, *mapping.get("zh_terms", [])}),
        "preferred_label_en": mapping["preferred_label_en"],
        "synonyms_en": list(mapping.get("synonyms_en", [])),
        "mesh_terms": list(mapping.get("mesh_terms", [])),
        "emtree_terms": list(mapping.get("emtree_terms", [])),
        "free_text_terms_en": sorted({mapping["preferred_label_en"], *mapping.get("synonyms_en", [])}),
        "concept_type": concept_type,
        "pico_roles": list(mapping["pico_roles"]),
        "meta_profiles": list(mapping.get("meta_profiles", [])),
        "query_usage": make_query_usage(concept_type),
        "query_expansion_allowed": query_expansion_allowed,
        "standalone_search_allowed": mapping.get("standalone_search_allowed", "conditional"),
        "requires_pairing_with": list(mapping.get("requires_pairing_with", [])),
        "source_evidence": source_evidence,
        "review_status": "approved",
        "notes": "Generated from reviewed high-confidence Meta Chinese candidate rules; not promoted to shared core.",
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |" for row in rows)
    return "\n".join(lines)


def status_from_covered(covered: bool, needs_review: bool = False) -> str:
    if needs_review:
        return "needs_review"
    return "complete" if covered else "missing"


def source_evidence_from_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_file": row.get("source_file", ""),
        "source_type": row.get("source_type", ""),
        "raw_zh_term": row.get("raw_zh_term", ""),
    }


def candidate_sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("normalized_zh_term") or row.get("raw_zh_term") or ""), str(row.get("candidate_id") or ""))


def summarize_jsonl(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip()) if path.exists() else 0


def grouped_source_evidence(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        term = str(row.get("normalized_zh_term") or "")
        if not term:
            continue
        evidence = source_evidence_from_candidate(row)
        if evidence not in grouped[term]:
            grouped[term].append(evidence)
    return grouped


def duplicate_normalized_terms(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    labels: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        term = str(row.get("normalized_zh_term") or "")
        label = str(row.get("initial_source_label") or "")
        if term and label:
            labels[term].add(label)
    return {term: values for term, values in labels.items() if len(values) > 1}


def count_statuses(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key, "")) for row in rows))
