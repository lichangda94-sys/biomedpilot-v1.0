from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "build_english_core_lexicon.py"
CONCEPTS_PATH = REPO_ROOT / "tcga_gtex" / "lexicon" / "concept_catalog.csv"
CONCEPT_MAPPINGS_PATH = REPO_ROOT / "tcga_gtex" / "lexicon" / "concept_source_mappings.csv"
CHINESE_TERMS_PATH = REPO_ROOT / "tcga_gtex" / "lexicon" / "chinese_concept_terms.csv"
FULL_PATH = REPO_ROOT / "tcga_gtex" / "lexicon" / "english_core_terms_full.csv"
CURATED_PATH = REPO_ROOT / "tcga_gtex" / "lexicon" / "english_ui_terms_curated.csv"
ALIASES_PATH = REPO_ROOT / "tcga_gtex" / "lexicon" / "english_term_aliases.csv"


def load_builder_module():
    spec = importlib.util.spec_from_file_location("build_english_core_lexicon", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load lexicon builder from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EnglishCoreLexiconTests(unittest.TestCase):
    def test_builder_generates_all_csv_files(self) -> None:
        builder = load_builder_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            concepts_path, concept_mappings_path, chinese_terms_path, full_path, curated_path, aliases_path = builder.build_english_core_lexicon(output_dir=output_dir)

            self.assertTrue(concepts_path.exists())
            self.assertTrue(concept_mappings_path.exists())
            self.assertTrue(chinese_terms_path.exists())
            self.assertTrue(full_path.exists())
            self.assertTrue(curated_path.exists())
            self.assertTrue(aliases_path.exists())

    def test_csv_headers_match_expected_schema(self) -> None:
        builder = load_builder_module()

        with CONCEPTS_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            self.assertEqual(next(reader), builder.CONCEPT_HEADERS)

        with CONCEPT_MAPPINGS_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            self.assertEqual(next(reader), builder.CONCEPT_SOURCE_MAPPING_HEADERS)

        with CHINESE_TERMS_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            self.assertEqual(next(reader), builder.CHINESE_CONCEPT_TERM_HEADERS)

        with FULL_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            self.assertEqual(next(reader), builder.FULL_TERM_HEADERS)

        with CURATED_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            self.assertEqual(next(reader), builder.CURATED_TERM_HEADERS)

        with ALIASES_PATH.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            self.assertEqual(next(reader), builder.ALIAS_HEADERS)

    def test_full_terms_cover_required_core_entries(self) -> None:
        with FULL_PATH.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        term_values = {row["display_label_en"] for row in rows}
        self.assertIn("Projects", term_values)
        self.assertIn("Files", term_values)
        self.assertIn("TCGA-THCA", term_values)
        self.assertIn("Gene Expression Quantification", term_values)
        self.assertIn("Tissue", term_values)
        self.assertIn("TPM", term_values)

    def test_curated_terms_cover_required_ui_entries(self) -> None:
        with CURATED_PATH.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        titles = {row["title_en"] for row in rows}
        self.assertIn("TCGA-THCA", titles)
        self.assertIn("Thyroid", titles)
        self.assertIn("Gene Expression", titles)
        self.assertIn("Primary Tumor", titles)
        self.assertIn("TPM", titles)

    def test_curated_terms_exclude_low_value_field_path_terms(self) -> None:
        with CURATED_PATH.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        titles = {row["title_en"] for row in rows}
        self.assertNotIn("project_id", titles)
        self.assertNotIn("workflow_type", titles)
        self.assertNotIn("files.analysis.workflow_type", titles)

    def test_aliases_include_key_abbreviations_and_variants(self) -> None:
        with ALIASES_PATH.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        alias_values = {row["alias_en"] for row in rows}
        self.assertIn("THCA", alias_values)
        self.assertIn("gene expression", alias_values)

    def test_concept_layer_and_source_mappings_reserve_geo_entry(self) -> None:
        with CONCEPTS_PATH.open("r", encoding="utf-8", newline="") as handle:
            concepts = list(csv.DictReader(handle))
        with CONCEPT_MAPPINGS_PATH.open("r", encoding="utf-8", newline="") as handle:
            mappings = list(csv.DictReader(handle))

        concept_ids = {row["concept_id"] for row in concepts}
        self.assertIn("disease.thyroid_cancer", concept_ids)
        self.assertIn("disease.papillary_thyroid_carcinoma", concept_ids)
        self.assertIn("tissue.thyroid", concept_ids)

        geo_mapping_rows = [row for row in mappings if row["source"] == "geo" and row["concept_id"] == "disease.thyroid_cancer"]
        self.assertTrue(geo_mapping_rows)

    def test_source_adapter_helpers_split_structured_and_geo_rules(self) -> None:
        from tcga_gtex.search import (
            map_concept_to_geo_query_terms,
            map_concept_to_gtex_filters,
            map_concept_to_tcga_filters,
        )

        tcga_result = map_concept_to_tcga_filters("disease.thyroid_cancer")
        gtex_result = map_concept_to_gtex_filters("tissue.thyroid")
        geo_result = map_concept_to_geo_query_terms("disease.thyroid_cancer")

        self.assertIn("project.project_id", tcga_result["filters"])
        self.assertIn("TCGA-THCA", tcga_result["filters"]["project.project_id"])
        self.assertIn("tissue", gtex_result["filters"])
        self.assertIn("Thyroid", gtex_result["filters"]["tissue"])
        self.assertIn("thyroid cancer", geo_result["query_terms"])
        self.assertEqual(geo_result["status"], "reserved_for_future_geo_adapter")

    def test_chinese_concept_terms_cover_minimum_entry_points(self) -> None:
        with CHINESE_TERMS_PATH.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        terms = {row["term_zh"] for row in rows}
        self.assertIn("甲状腺癌", terms)
        self.assertIn("乳腺癌", terms)
        self.assertIn("肺腺癌", terms)
        self.assertIn("结直肠癌", terms)
        self.assertIn("宫颈癌", terms)
        self.assertIn("肾透明细胞癌", terms)
        self.assertIn("肺癌", terms)
        self.assertIn("正常甲状腺", terms)
        self.assertIn("乳腺组织", terms)
        self.assertIn("血液/骨髓", terms)
        self.assertIn("肾脏", terms)
        self.assertIn("唾液腺", terms)
        self.assertIn("基因表达", terms)
        self.assertIn("临床信息", terms)
        self.assertIn("开放访问", terms)

    def test_chinese_query_mapper_hits_expected_concepts(self) -> None:
        from tcga_gtex.search import build_query_mapping_from_chinese

        thyroid_cancer = build_query_mapping_from_chinese("甲状腺癌")
        normal_thyroid = build_query_mapping_from_chinese("正常甲状腺")
        gene_expression = build_query_mapping_from_chinese("基因表达")
        clinical = build_query_mapping_from_chinese("临床信息")
        open_access = build_query_mapping_from_chinese("开放访问")

        self.assertIn("disease.thyroid_cancer", thyroid_cancer.concept_ids)
        self.assertIn("tissue.thyroid", normal_thyroid.concept_ids)
        self.assertTrue(
            "sample_type.normal" in normal_thyroid.concept_ids
            or "sample_type.solid_tissue_normal" in normal_thyroid.concept_ids
        )
        self.assertIn("analysis_resource.gene_expression", gene_expression.concept_ids)
        self.assertIn("analysis_resource.clinical", clinical.concept_ids)
        self.assertIn("access.open", open_access.concept_ids)

    def test_multicancer_chinese_query_mapper_hits_expected_concepts(self) -> None:
        from tcga_gtex.search import build_query_mapping_from_chinese

        self.assertIn("disease.breast_cancer", build_query_mapping_from_chinese("乳腺癌").concept_ids)
        self.assertIn("disease.lung_adenocarcinoma", build_query_mapping_from_chinese("肺腺癌").concept_ids)
        self.assertIn("disease.lung_squamous_cell_carcinoma", build_query_mapping_from_chinese("肺鳞癌").concept_ids)
        self.assertIn("disease.hepatocellular_carcinoma", build_query_mapping_from_chinese("肝细胞癌").concept_ids)
        self.assertIn("disease.colorectal_cancer", build_query_mapping_from_chinese("结直肠癌").concept_ids)
        self.assertIn("disease.glioblastoma", build_query_mapping_from_chinese("胶质母细胞瘤").concept_ids)
        self.assertIn("disease.melanoma", build_query_mapping_from_chinese("黑色素瘤").concept_ids)
        self.assertIn("disease.leukemia", build_query_mapping_from_chinese("白血病").concept_ids)
        self.assertIn("disease.lymphoma", build_query_mapping_from_chinese("淋巴瘤").concept_ids)
        self.assertIn("disease.cervical_cancer", build_query_mapping_from_chinese("宫颈癌").concept_ids)
        self.assertIn("disease.endometrial_cancer", build_query_mapping_from_chinese("子宫内膜癌").concept_ids)
        self.assertIn("disease.bladder_cancer", build_query_mapping_from_chinese("膀胱癌").concept_ids)
        self.assertIn("disease.kidney_renal_clear_cell_carcinoma", build_query_mapping_from_chinese("肾透明细胞癌").concept_ids)
        self.assertIn("disease.kidney_renal_papillary_cell_carcinoma", build_query_mapping_from_chinese("肾乳头状癌").concept_ids)
        self.assertIn("disease.lower_grade_glioma", build_query_mapping_from_chinese("低级别胶质瘤").concept_ids)
        self.assertIn("disease.lung_cancer", build_query_mapping_from_chinese("肺癌").concept_ids)
        self.assertIn("disease.kidney_cancer", build_query_mapping_from_chinese("肾癌").concept_ids)
        self.assertIn("disease.gynecologic_cancer", build_query_mapping_from_chinese("妇科肿瘤").concept_ids)

    def test_chinese_query_source_previews_cover_priority_diseases_and_tissues(self) -> None:
        from tcga_gtex.search import build_source_previews_from_chinese

        breast = build_source_previews_from_chinese("乳腺癌")
        luad = build_source_previews_from_chinese("肺腺癌")
        lusc = build_source_previews_from_chinese("肺鳞癌")
        hcc = build_source_previews_from_chinese("肝细胞癌")
        crc = build_source_previews_from_chinese("结直肠癌")
        gbm = build_source_previews_from_chinese("胶质母细胞瘤")
        melanoma = build_source_previews_from_chinese("黑色素瘤")
        leukemia = build_source_previews_from_chinese("白血病")
        lymphoma = build_source_previews_from_chinese("淋巴瘤")

        self.assertIn("TCGA-BRCA", breast["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-LUAD", luad["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-LUSC", lusc["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-LIHC", hcc["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertTrue(
            "TCGA-COAD" in crc["tcga_gdc"]["filters"].get("project.project_id", [])
            or "TCGA-READ" in crc["tcga_gdc"]["filters"].get("project.project_id", [])
        )
        self.assertIn("TCGA-GBM", gbm["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-SKCM", melanoma["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-LAML", leukemia["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-DLBC", lymphoma["tcga_gdc"]["filters"].get("project.project_id", []))

        breast_tissue = build_source_previews_from_chinese("乳腺组织")
        lung_tissue = build_source_previews_from_chinese("肺组织")
        liver_tissue = build_source_previews_from_chinese("肝组织")
        brain_tissue = build_source_previews_from_chinese("脑组织")
        pancreas_tissue = build_source_previews_from_chinese("胰腺组织")
        skin_tissue = build_source_previews_from_chinese("皮肤")
        blood_tissue = build_source_previews_from_chinese("血液/骨髓")

        self.assertIn("Breast", breast_tissue["gtex"]["filters"].get("tissue", []))
        self.assertIn("Lung", lung_tissue["gtex"]["filters"].get("tissue", []))
        self.assertIn("Liver", liver_tissue["gtex"]["filters"].get("tissue", []))
        self.assertIn("Brain", brain_tissue["gtex"]["filters"].get("tissue", []))
        self.assertIn("Pancreas", pancreas_tissue["gtex"]["filters"].get("tissue", []))
        self.assertIn("Skin", skin_tissue["gtex"]["filters"].get("tissue", []))
        self.assertIn("Blood", blood_tissue["gtex"]["filters"].get("tissue", []))

    def test_second_round_disease_and_umbrella_previews(self) -> None:
        from tcga_gtex.search import build_source_previews_from_chinese

        cesc = build_source_previews_from_chinese("宫颈癌")
        ucec = build_source_previews_from_chinese("子宫内膜癌")
        blca = build_source_previews_from_chinese("膀胱癌")
        kirc = build_source_previews_from_chinese("肾透明细胞癌")
        kirp = build_source_previews_from_chinese("肾乳头状癌")
        hnsc = build_source_previews_from_chinese("头颈鳞癌")
        esca = build_source_previews_from_chinese("食管癌")
        chol = build_source_previews_from_chinese("胆管癌")
        meso = build_source_previews_from_chinese("间皮瘤")
        thym = build_source_previews_from_chinese("胸腺瘤")
        tgct = build_source_previews_from_chinese("睾丸生殖细胞肿瘤")
        sarc = build_source_previews_from_chinese("肉瘤")
        lgg = build_source_previews_from_chinese("低级别胶质瘤")
        acc = build_source_previews_from_chinese("肾上腺皮质癌")
        pcpg = build_source_previews_from_chinese("嗜铬细胞瘤 / 副神经节瘤")

        self.assertIn("TCGA-CESC", cesc["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-UCEC", ucec["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-BLCA", blca["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-KIRC", kirc["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-KIRP", kirp["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-HNSC", hnsc["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-ESCA", esca["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-CHOL", chol["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-MESO", meso["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-THYM", thym["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-TGCT", tgct["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-SARC", sarc["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-LGG", lgg["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-ACC", acc["tcga_gdc"]["filters"].get("project.project_id", []))
        self.assertIn("TCGA-PCPG", pcpg["tcga_gdc"]["filters"].get("project.project_id", []))

        lung_cancer = build_source_previews_from_chinese("肺癌")
        kidney_cancer = build_source_previews_from_chinese("肾癌")
        gyn_cancer = build_source_previews_from_chinese("妇科肿瘤")
        digestive = build_source_previews_from_chinese("消化系统肿瘤")
        heme = build_source_previews_from_chinese("血液肿瘤")

        self.assertTrue({"TCGA-LUAD", "TCGA-LUSC"}.issubset(set(lung_cancer["tcga_gdc"]["filters"].get("project.project_id", []))))
        self.assertTrue({"TCGA-KIRC", "TCGA-KIRP", "TCGA-KICH"}.issubset(set(kidney_cancer["tcga_gdc"]["filters"].get("project.project_id", []))))
        self.assertTrue({"TCGA-CESC", "TCGA-UCEC", "TCGA-OV"}.issubset(set(gyn_cancer["tcga_gdc"]["filters"].get("project.project_id", []))))
        self.assertTrue({"TCGA-LIHC", "TCGA-PAAD", "TCGA-STAD", "TCGA-COAD", "TCGA-READ", "TCGA-ESCA", "TCGA-CHOL"}.issubset(set(digestive["tcga_gdc"]["filters"].get("project.project_id", []))))
        self.assertTrue({"TCGA-LAML", "TCGA-DLBC"}.issubset(set(heme["tcga_gdc"]["filters"].get("project.project_id", []))))

    def test_second_round_tissue_previews(self) -> None:
        from tcga_gtex.search import build_source_previews_from_chinese

        expected = {
            "肾脏": "Kidney",
            "膀胱": "Bladder",
            "宫颈": "Cervix Uteri",
            "子宫": "Uterus",
            "食管": "Esophagus",
            "小肠": "Small Intestine",
            "唾液腺": "Minor Salivary Gland",
            "垂体": "Pituitary",
            "肾上腺": "Adrenal Gland",
            "睾丸": "Testis",
            "输卵管": "Fallopian Tube",
            "阴道": "Vagina",
            "神经": "Nerve",
            "血管": "Blood Vessel",
            "心脏": "Heart",
            "肌肉": "Muscle",
        }
        for query, tissue in expected.items():
            preview = build_source_previews_from_chinese(query)
            self.assertIn(tissue, preview["gtex"]["filters"].get("tissue", []))


if __name__ == "__main__":
    unittest.main()
