from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TCGAProjectEntry:
    project_id: str
    short_code: str
    english_name: str
    chinese_name: str
    organ_system: str
    is_primary_user_visible: bool = True
    notes: str = ""


@dataclass(frozen=True)
class TCGAAnalysisPurpose:
    purpose_id: str
    chinese_name: str
    required_internal_assets: tuple[str, ...]
    optional_internal_assets: tuple[str, ...]
    user_description: str
    readiness_profile: str


@dataclass(frozen=True)
class TCGASampleScope:
    scope_id: str
    chinese_name: str
    internal_sample_types: tuple[str, ...]
    user_description: str


TCGA_PROJECTS: tuple[TCGAProjectEntry, ...] = (
    TCGAProjectEntry("TCGA-ACC", "ACC", "Adrenocortical Carcinoma", "肾上腺皮质癌", "内分泌/神经内分泌"),
    TCGAProjectEntry("TCGA-BLCA", "BLCA", "Bladder Urothelial Carcinoma", "膀胱尿路上皮癌", "泌尿系统"),
    TCGAProjectEntry("TCGA-BRCA", "BRCA", "Breast Invasive Carcinoma", "乳腺浸润癌", "女性生殖/乳腺"),
    TCGAProjectEntry("TCGA-CESC", "CESC", "Cervical Squamous Cell Carcinoma and Endocervical Adenocarcinoma", "宫颈鳞癌和宫颈腺癌", "女性生殖系统"),
    TCGAProjectEntry("TCGA-CHOL", "CHOL", "Cholangiocarcinoma", "胆管癌", "消化系统"),
    TCGAProjectEntry("TCGA-COAD", "COAD", "Colon Adenocarcinoma", "结肠腺癌", "消化系统"),
    TCGAProjectEntry("TCGA-DLBC", "DLBC", "Diffuse Large B-cell Lymphoma", "弥漫大B细胞淋巴瘤", "血液/免疫"),
    TCGAProjectEntry("TCGA-ESCA", "ESCA", "Esophageal Carcinoma", "食管癌", "消化系统"),
    TCGAProjectEntry("TCGA-GBM", "GBM", "Glioblastoma Multiforme", "胶质母细胞瘤", "神经系统"),
    TCGAProjectEntry("TCGA-HNSC", "HNSC", "Head and Neck Squamous Cell Carcinoma", "头颈部鳞状细胞癌", "头颈部"),
    TCGAProjectEntry("TCGA-KICH", "KICH", "Kidney Chromophobe", "肾嫌色细胞癌", "泌尿系统"),
    TCGAProjectEntry("TCGA-KIRC", "KIRC", "Kidney Renal Clear Cell Carcinoma", "肾透明细胞癌", "泌尿系统"),
    TCGAProjectEntry("TCGA-KIRP", "KIRP", "Kidney Renal Papillary Cell Carcinoma", "肾乳头状细胞癌", "泌尿系统"),
    TCGAProjectEntry("TCGA-LAML", "LAML", "Acute Myeloid Leukemia", "急性髓系白血病", "血液/免疫"),
    TCGAProjectEntry("TCGA-LGG", "LGG", "Brain Lower Grade Glioma", "脑低级别胶质瘤", "神经系统"),
    TCGAProjectEntry("TCGA-LIHC", "LIHC", "Liver Hepatocellular Carcinoma", "肝细胞癌", "消化系统"),
    TCGAProjectEntry("TCGA-LUAD", "LUAD", "Lung Adenocarcinoma", "肺腺癌", "呼吸系统"),
    TCGAProjectEntry("TCGA-LUSC", "LUSC", "Lung Squamous Cell Carcinoma", "肺鳞癌", "呼吸系统"),
    TCGAProjectEntry("TCGA-MESO", "MESO", "Mesothelioma", "间皮瘤", "呼吸/胸膜"),
    TCGAProjectEntry("TCGA-OV", "OV", "Ovarian Serous Cystadenocarcinoma", "卵巢浆液性囊腺癌", "女性生殖系统"),
    TCGAProjectEntry("TCGA-PAAD", "PAAD", "Pancreatic Adenocarcinoma", "胰腺腺癌", "消化系统"),
    TCGAProjectEntry("TCGA-PCPG", "PCPG", "Pheochromocytoma and Paraganglioma", "嗜铬细胞瘤和副神经节瘤", "内分泌/神经内分泌"),
    TCGAProjectEntry("TCGA-PRAD", "PRAD", "Prostate Adenocarcinoma", "前列腺腺癌", "男性生殖/泌尿"),
    TCGAProjectEntry("TCGA-READ", "READ", "Rectum Adenocarcinoma", "直肠腺癌", "消化系统"),
    TCGAProjectEntry("TCGA-SARC", "SARC", "Sarcoma", "肉瘤", "皮肤/软组织"),
    TCGAProjectEntry("TCGA-SKCM", "SKCM", "Skin Cutaneous Melanoma", "皮肤黑色素瘤", "皮肤/软组织"),
    TCGAProjectEntry("TCGA-STAD", "STAD", "Stomach Adenocarcinoma", "胃腺癌", "消化系统"),
    TCGAProjectEntry("TCGA-TGCT", "TGCT", "Testicular Germ Cell Tumors", "睾丸生殖细胞肿瘤", "男性生殖系统"),
    TCGAProjectEntry("TCGA-THCA", "THCA", "Thyroid Carcinoma", "甲状腺癌", "内分泌/神经内分泌"),
    TCGAProjectEntry("TCGA-THYM", "THYM", "Thymoma", "胸腺瘤", "胸腺/免疫"),
    TCGAProjectEntry("TCGA-UCEC", "UCEC", "Uterine Corpus Endometrial Carcinoma", "子宫内膜癌", "女性生殖系统"),
    TCGAProjectEntry("TCGA-UCS", "UCS", "Uterine Carcinosarcoma", "子宫癌肉瘤", "女性生殖系统"),
    TCGAProjectEntry("TCGA-UVM", "UVM", "Uveal Melanoma", "葡萄膜黑色素瘤", "神经/眼部"),
)

TCGA_ANALYSIS_PURPOSES: tuple[TCGAAnalysisPurpose, ...] = (
    TCGAAnalysisPurpose("differential_expression", "表达差异分析", ("rna_seq_expression", "sample_metadata"), ("clinical_metadata",), "用于后续 DEG / PCA / heatmap / GSEA ranking。", "requires_expression_and_sample_metadata"),
    TCGAAnalysisPurpose("expression_clinical", "表达与临床联合分析", ("rna_seq_expression", "sample_metadata", "clinical_metadata"), (), "用于探索表达量与临床变量的关系。", "requires_expression_sample_and_clinical_metadata"),
    TCGAAnalysisPurpose("survival", "生存分析", ("clinical_metadata", "case_sample_mapping"), ("rna_seq_expression",), "用于生存结局预检；按基因表达分组时还需要表达数据。", "requires_clinical_survival_metadata"),
    TCGAAnalysisPurpose("project_overview", "项目样本概况", ("project_metadata",), ("sample_metadata",), "只查看项目和样本概况，不下载大表达矩阵。", "metadata_only"),
)

TCGA_SAMPLE_SCOPES: tuple[TCGASampleScope, ...] = (
    TCGASampleScope("tumor", "肿瘤样本", ("Primary Tumor",), "仅选择原发肿瘤样本。"),
    TCGASampleScope("normal", "癌旁正常样本", ("Solid Tissue Normal",), "仅选择癌旁正常样本；并非所有 TCGA 项目都有。"),
    TCGASampleScope("tumor_normal", "肿瘤 + 癌旁正常样本", ("Primary Tumor", "Solid Tissue Normal"), "用于同一项目内肿瘤与癌旁样本比较。"),
    TCGASampleScope("metastatic", "转移样本", ("Metastatic",), "仅在项目存在转移样本时可用。"),
    TCGASampleScope("recurrent", "复发样本", ("Recurrent Tumor",), "仅在项目存在复发样本时可用。"),
    TCGASampleScope("custom", "自定义样本", (), "下一阶段连接 GDC API 后开放自定义筛选。"),
)


def list_tcga_projects(*, primary_only: bool = True) -> tuple[TCGAProjectEntry, ...]:
    projects = TCGA_PROJECTS
    if primary_only:
        projects = tuple(project for project in projects if project.is_primary_user_visible)
    return tuple(sorted(projects, key=lambda project: (project.organ_system, project.short_code)))


def grouped_tcga_projects() -> dict[str, tuple[TCGAProjectEntry, ...]]:
    grouped: dict[str, list[TCGAProjectEntry]] = {}
    for project in list_tcga_projects():
        grouped.setdefault(project.organ_system, []).append(project)
    return {group: tuple(items) for group, items in sorted(grouped.items())}


def get_tcga_project(project_id: str) -> TCGAProjectEntry:
    normalized = project_id.strip().upper()
    for project in TCGA_PROJECTS:
        if project.project_id == normalized or project.short_code == normalized.replace("TCGA-", ""):
            return project
    raise KeyError(project_id)


def get_tcga_analysis_purpose(purpose_id: str) -> TCGAAnalysisPurpose:
    for purpose in TCGA_ANALYSIS_PURPOSES:
        if purpose.purpose_id == purpose_id:
            return purpose
    raise KeyError(purpose_id)


def get_tcga_sample_scope(scope_id: str) -> TCGASampleScope:
    for scope in TCGA_SAMPLE_SCOPES:
        if scope.scope_id == scope_id:
            return scope
    raise KeyError(scope_id)
