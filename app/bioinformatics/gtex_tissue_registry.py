from __future__ import annotations

from dataclasses import dataclass


GTEX_VERSION = "GTEx V8"


@dataclass(frozen=True)
class GTExTissueEntry:
    tissue_id: str
    tissue_site_detail: str
    chinese_name: str
    tissue_group: str
    version: str = GTEX_VERSION
    is_primary_user_visible: bool = True
    notes: str = ""


@dataclass(frozen=True)
class GTExUsePurpose:
    purpose_id: str
    chinese_name: str
    required_internal_assets: tuple[str, ...]
    optional_internal_assets: tuple[str, ...]
    user_description: str
    readiness_profile: str


def _tid(name: str) -> str:
    return "gtex_" + "".join(char.lower() if char.isalnum() else "_" for char in name).strip("_")


GTEX_TISSUES: tuple[GTExTissueEntry, ...] = tuple(
    GTExTissueEntry(_tid(name), name, zh, group)
    for name, zh, group in (
        ("Adipose - Subcutaneous", "皮下脂肪", "脂肪组织"),
        ("Adipose - Visceral (Omentum)", "内脏脂肪/网膜脂肪", "脂肪组织"),
        ("Adrenal Gland", "肾上腺", "内分泌系统"),
        ("Artery - Aorta", "主动脉", "血管"),
        ("Artery - Coronary", "冠状动脉", "血管"),
        ("Artery - Tibial", "胫动脉", "血管"),
        ("Bladder", "膀胱", "泌尿系统"),
        ("Brain - Amygdala", "杏仁核", "脑"),
        ("Brain - Anterior cingulate cortex (BA24)", "前扣带皮层 BA24", "脑"),
        ("Brain - Caudate (basal ganglia)", "尾状核/基底节", "脑"),
        ("Brain - Cerebellar Hemisphere", "小脑半球", "脑"),
        ("Brain - Cerebellum", "小脑", "脑"),
        ("Brain - Cortex", "大脑皮层", "脑"),
        ("Brain - Frontal Cortex (BA9)", "额叶皮层 BA9", "脑"),
        ("Brain - Hippocampus", "海马", "脑"),
        ("Brain - Hypothalamus", "下丘脑", "脑"),
        ("Brain - Nucleus accumbens (basal ganglia)", "伏隔核/基底节", "脑"),
        ("Brain - Putamen (basal ganglia)", "壳核/基底节", "脑"),
        ("Brain - Spinal cord (cervical c-1)", "颈髓 C1", "脑/脊髓"),
        ("Brain - Substantia nigra", "黑质", "脑"),
        ("Breast - Mammary Tissue", "乳腺组织", "乳腺"),
        ("Cells - Cultured fibroblasts", "培养成纤维细胞", "细胞系"),
        ("Cells - EBV-transformed lymphocytes", "EBV 转化淋巴细胞", "细胞系"),
        ("Cervix - Ectocervix", "宫颈外口", "女性生殖系统"),
        ("Cervix - Endocervix", "宫颈内口", "女性生殖系统"),
        ("Colon - Sigmoid", "乙状结肠", "消化系统"),
        ("Colon - Transverse", "横结肠", "消化系统"),
        ("Esophagus - Gastroesophageal Junction", "胃食管连接部", "消化系统"),
        ("Esophagus - Mucosa", "食管黏膜", "消化系统"),
        ("Esophagus - Muscularis", "食管肌层", "消化系统"),
        ("Fallopian Tube", "输卵管", "女性生殖系统"),
        ("Heart - Atrial Appendage", "心耳", "心脏"),
        ("Heart - Left Ventricle", "左心室", "心脏"),
        ("Kidney - Cortex", "肾皮质", "泌尿系统"),
        ("Kidney - Medulla", "肾髓质", "泌尿系统"),
        ("Liver", "肝脏", "消化系统"),
        ("Lung", "肺", "呼吸系统"),
        ("Minor Salivary Gland", "小唾液腺", "头颈部/腺体"),
        ("Muscle - Skeletal", "骨骼肌", "肌肉"),
        ("Nerve - Tibial", "胫神经", "神经"),
        ("Ovary", "卵巢", "女性生殖系统"),
        ("Pancreas", "胰腺", "消化/内分泌系统"),
        ("Pituitary", "垂体", "内分泌系统"),
        ("Prostate", "前列腺", "男性生殖系统"),
        ("Skin - Not Sun Exposed (Suprapubic)", "非日晒皮肤/耻骨上", "皮肤"),
        ("Skin - Sun Exposed (Lower leg)", "日晒皮肤/小腿", "皮肤"),
        ("Small Intestine - Terminal Ileum", "小肠末端回肠", "消化系统"),
        ("Spleen", "脾脏", "免疫/血液系统"),
        ("Stomach", "胃", "消化系统"),
        ("Testis", "睾丸", "男性生殖系统"),
        ("Thyroid", "甲状腺", "内分泌系统"),
        ("Uterus", "子宫", "女性生殖系统"),
        ("Vagina", "阴道", "女性生殖系统"),
        ("Whole Blood", "全血", "血液/免疫"),
    )
)

GTEX_USE_PURPOSES: tuple[GTExUsePurpose, ...] = (
    GTExUsePurpose("normal_expression_view", "查看正常组织表达", ("gene_expression", "sample_annotation"), (), "查看独立正常组织表达资源。", "requires_expression_and_sample_annotation"),
    GTExUsePurpose("download_tissue_matrix", "下载组织表达矩阵", ("gene_level_expression", "sample_annotation"), (), "构建组织表达矩阵和样本注释。", "requires_expression_and_sample_annotation"),
    GTExUsePurpose("external_reference", "作为外部参考数据", ("gene_expression", "sample_annotation"), (), "作为外部参考资源；不自动作为 TCGA 对照。", "external_reference_not_tcga_control"),
    GTExUsePurpose("project_overview", "项目样本概况", ("tissue_metadata",), ("sample_annotation",), "只查看组织和样本概况，不下载大表达矩阵。", "metadata_only"),
)


def list_gtex_tissues(*, primary_only: bool = True) -> tuple[GTExTissueEntry, ...]:
    tissues = GTEX_TISSUES
    if primary_only:
        tissues = tuple(tissue for tissue in tissues if tissue.is_primary_user_visible)
    return tuple(sorted(tissues, key=lambda tissue: (tissue.tissue_group, tissue.tissue_site_detail)))


def grouped_gtex_tissues() -> dict[str, tuple[GTExTissueEntry, ...]]:
    grouped: dict[str, list[GTExTissueEntry]] = {}
    for tissue in list_gtex_tissues():
        grouped.setdefault(tissue.tissue_group, []).append(tissue)
    return {group: tuple(items) for group, items in sorted(grouped.items())}


def get_gtex_tissue(tissue_id: str) -> GTExTissueEntry:
    normalized = tissue_id.strip()
    for tissue in GTEX_TISSUES:
        if tissue.tissue_id == normalized or tissue.tissue_site_detail == normalized:
            return tissue
    raise KeyError(tissue_id)


def get_gtex_use_purpose(purpose_id: str) -> GTExUsePurpose:
    for purpose in GTEX_USE_PURPOSES:
        if purpose.purpose_id == purpose_id:
            return purpose
    raise KeyError(purpose_id)
