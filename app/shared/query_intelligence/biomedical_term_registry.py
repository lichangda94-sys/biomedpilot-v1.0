from __future__ import annotations

from app.shared.query_intelligence.query_intelligence_models import MedicalConcept


REGISTRY_CONCEPTS: tuple[MedicalConcept, ...] = (
    MedicalConcept(
        concept_id="obesity",
        label_zh="肥胖",
        zh_terms=("肥胖", "超重", "体重指数", "BMI"),
        en_terms=("obesity", "obese", "overweight", "body mass index", "BMI"),
        mesh_terms=("Obesity", "Body Mass Index"),
        semantic_group="exposure",
    ),
    MedicalConcept(
        concept_id="thyroid_cancer",
        label_zh="甲状腺癌",
        zh_terms=("甲状腺癌", "甲状腺肿瘤", "甲状腺癌发病"),
        en_terms=(
            "thyroid cancer",
            "thyroid carcinoma",
            "thyroid neoplasm",
            "thyroid tumor",
        ),
        mesh_terms=("Thyroid Neoplasms",),
        database_terms=("TCGA-THCA", "thyroid tissue", "tumor tissue", "normal tissue"),
        semantic_group="disease",
    ),
    MedicalConcept(
        concept_id="papillary_thyroid_cancer",
        label_zh="乳头状甲状腺癌",
        zh_terms=("乳头状甲状腺癌", "甲状腺乳头状癌"),
        en_terms=("papillary thyroid carcinoma", "PTC"),
        mesh_terms=("Thyroid Neoplasms",),
        database_terms=("TCGA-THCA",),
        semantic_group="disease",
    ),
    MedicalConcept(
        concept_id="glioma",
        label_zh="脑胶质瘤",
        zh_terms=("脑胶质瘤", "胶质瘤", "胶质母细胞瘤"),
        en_terms=("glioma", "glioblastoma", "lower grade glioma"),
        synonyms=("GBM", "LGG"),
        database_terms=("TCGA-GBM", "TCGA-LGG", "brain tissue"),
        semantic_group="disease",
    ),
    MedicalConcept(
        concept_id="lung_adenocarcinoma",
        label_zh="肺腺癌",
        zh_terms=("肺腺癌", "肺腺癌相关数据集"),
        en_terms=("lung adenocarcinoma", "LUAD"),
        database_terms=("TCGA-LUAD", "lung tissue"),
        semantic_group="disease",
    ),
    MedicalConcept(
        concept_id="hepatocellular_carcinoma",
        label_zh="肝细胞癌",
        zh_terms=("肝细胞癌", "肝癌", "肝细胞癌相关数据集"),
        en_terms=("hepatocellular carcinoma", "HCC", "liver cancer"),
        database_terms=("TCGA-LIHC", "liver tissue"),
        semantic_group="disease",
    ),
    MedicalConcept(
        concept_id="esophageal_squamous_cell_carcinoma",
        label_zh="食管鳞癌",
        zh_terms=("食管鳞癌", "食道鳞癌", "食管鳞状细胞癌"),
        en_terms=(
            "esophageal squamous cell carcinoma",
            "oesophageal squamous cell carcinoma",
            "ESCC",
            "esophageal cancer",
        ),
        semantic_group="disease",
    ),
    MedicalConcept(
        concept_id="poorly_differentiated",
        label_zh="低分化",
        zh_terms=("低分化",),
        en_terms=("poorly differentiated",),
        semantic_group="modifier",
    ),
    MedicalConcept(
        concept_id="incidence_risk",
        label_zh="发病/风险",
        zh_terms=("发病", "发生", "风险", "患病风险"),
        en_terms=("incidence", "risk", "occurrence", "disease risk"),
        semantic_group="outcome",
    ),
    MedicalConcept(
        concept_id="survival",
        label_zh="生存",
        zh_terms=("总生存", "无进展生存", "预后"),
        en_terms=("overall survival", "progression-free survival", "prognosis"),
        semantic_group="outcome",
    ),
    MedicalConcept(
        concept_id="treatment",
        label_zh="治疗",
        zh_terms=("治疗", "药物", "抑制剂", "联合化疗"),
        en_terms=("treatment", "therapy", "inhibitor", "chemotherapy"),
        semantic_group="intervention",
    ),
    MedicalConcept(
        concept_id="bio_dataset_retrieval",
        label_zh="生信数据集检索",
        zh_terms=("数据集", "表达谱", "转录组", "芯片", "测序", "RNA测序", "RNA-seq", "单细胞", "GEO", "GSE"),
        en_terms=("dataset", "GEO", "GSE", "expression profiling", "transcriptome", "RNA-seq", "microarray", "single-cell RNA-seq", "scRNA-seq"),
        database_terms=("GEO", "GSE", "TCGA", "GTEx"),
        semantic_group="dataset",
    ),
    MedicalConcept(
        concept_id="poorly_differentiated_thyroid_cancer",
        label_zh="低分化甲状腺癌",
        zh_terms=("低分化甲状腺癌", "低分化甲状腺癌相关数据集"),
        en_terms=("poorly differentiated thyroid cancer", "poorly differentiated thyroid carcinoma"),
        synonyms=("thyroid carcinoma", "thyroid neoplasm", "thyroid cancer"),
        database_terms=("tumor tissue", "cell line", "normal tissue"),
        semantic_group="disease",
    ),
    MedicalConcept(
        concept_id="lymph_node_metastasis",
        label_zh="淋巴结转移",
        zh_terms=("淋巴结转移", "转移"),
        en_terms=("lymph node metastasis", "metastasis"),
        semantic_group="phenotype",
    ),
)


def match_registry_concepts(question: str, *, target_context: str = "") -> tuple[MedicalConcept, ...]:
    text = question.lower()
    matches: list[MedicalConcept] = []
    for concept in REGISTRY_CONCEPTS:
        terms = [*concept.zh_terms, *concept.en_terms, *concept.synonyms, *concept.mesh_terms, concept.label_zh]
        if any(term and term.lower() in text for term in terms):
            _append_concept(matches, concept)
    if target_context == "bioinformatics":
        _append_concept(matches, concept_by_id("bio_dataset_retrieval"))
    if "甲状腺" in question and concept_by_id("thyroid_cancer") not in matches:
        _append_concept(matches, concept_by_id("thyroid_cancer"))
    if any(token in question for token in ("脑胶质瘤", "胶质瘤", "glioma", "glioblastoma")) and concept_by_id("glioma") not in matches:
        _append_concept(matches, concept_by_id("glioma"))
    if any(token in question for token in ("肺腺癌", "LUAD", "lung adenocarcinoma")) and concept_by_id("lung_adenocarcinoma") not in matches:
        _append_concept(matches, concept_by_id("lung_adenocarcinoma"))
    if any(token in question for token in ("肝细胞癌", "肝癌", "HCC", "hepatocellular")) and concept_by_id("hepatocellular_carcinoma") not in matches:
        _append_concept(matches, concept_by_id("hepatocellular_carcinoma"))
    if any(token in question for token in ("食管", "食道", "ESCC", "esophageal", "oesophageal")) and concept_by_id("esophageal_squamous_cell_carcinoma") not in matches:
        _append_concept(matches, concept_by_id("esophageal_squamous_cell_carcinoma"))
    if "低分化" in question and concept_by_id("poorly_differentiated") not in matches:
        _append_concept(matches, concept_by_id("poorly_differentiated"))
    if "低分化" in question and "甲状腺" in question and concept_by_id("poorly_differentiated_thyroid_cancer") not in matches:
        _append_concept(matches, concept_by_id("poorly_differentiated_thyroid_cancer"))
    if "关系" in question and concept_by_id("incidence_risk") not in matches:
        _append_concept(matches, concept_by_id("incidence_risk"))
    return tuple(matches)


def concept_by_id(concept_id: str) -> MedicalConcept:
    for concept in REGISTRY_CONCEPTS:
        if concept.concept_id == concept_id:
            return concept
    raise KeyError(concept_id)


def _append_concept(items: list[MedicalConcept], concept: MedicalConcept) -> None:
    if concept not in items:
        items.append(concept)
