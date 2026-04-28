from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tcga_gtex import (
    build_tcga_gtex_bundle,
    download_tcga_gtex_dataset,
    get_tcga_gtex_summary,
    resolve_tcga_gtex_files,
    search_tcga_gtex,
)
from tcga_gtex.adapters.gtex_adapter import resolve_files as resolve_gtex_files
from tcga_gtex.adapters.gtex_adapter import search as search_gtex
from tcga_gtex.adapters.tcga_adapter import resolve_files as resolve_tcga_files
from tcga_gtex.adapters.tcga_adapter import search as search_tcga
from tcga_gtex.models import AnalysisBundle, DownloadResult, FileRecord, QueryMapping, StudyRecord


class TcgaGtexFacadeTests(unittest.TestCase):
    def test_search_facade_returns_real_results_and_explanation(self) -> None:
        result = search_tcga_gtex("肺癌 + 基因表达 + 开放访问")
        self.assertEqual(result["status"], "success")
        self.assertIn("message", result)
        self.assertIn("warnings", result)
        self.assertIn("data", result)
        self.assertEqual(result["data"]["query"], "肺癌 + 基因表达 + 开放访问")
        self.assertTrue(result["data"]["results"])
        self.assertIn("query_mapping", result["data"])
        self.assertIn("explanation", result["data"])
        self.assertIn("matched_terms_zh", result["data"]["explanation"])
        self.assertIn("matched_concepts", result["data"]["explanation"])
        self.assertIn("selected_source_mappings", result["data"]["explanation"])
        self.assertIn("ambiguity_notes", result["data"]["explanation"])
        self.assertIn("warnings", result["data"]["explanation"])

        source_groups = result["data"]["results_by_source"]
        tcga_ids = {record["study_id"] for record in source_groups["tcga_gdc"]}
        gtex_ids = {record["study_id"] for record in source_groups["gtex"]}
        self.assertEqual(tcga_ids, {"TCGA-LUAD", "TCGA-LUSC"})
        self.assertEqual(gtex_ids, {"GTEX-LUNG"})

    def test_download_stays_unimplemented_while_bundle_and_summary_are_real(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            download_result = download_tcga_gtex_dataset("TCGA-THCA", tmpdir)
            self.assertEqual(download_result["status"], "failed")
            self.assertIn("No resolved records matched", download_result["message"])

    def test_download_runtime_copies_local_fixture_files_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = Path(tmpdir) / "fixtures"
            fixture_dir.mkdir()
            fixture_path = fixture_dir / "tcga_brca_expression.tsv.gz"
            fixture_content = "gene\tsample\nTP53\t3\n"
            fixture_path.write_text(fixture_content, encoding="utf-8")

            result = download_tcga_gtex_dataset(
                "TCGA-BRCA",
                tmpdir,
                options={
                    "resolved_records": [
                        FileRecord(
                            source="tcga_gdc",
                            study_id="TCGA-BRCA",
                            file_id="TCGA-BRCA:expression",
                            file_name="tcga_brca_expression.tsv.gz",
                            guessed_role="expression",
                            local_path=str(fixture_path),
                        )
                    ]
                },
            )

            self.assertEqual(result["status"], "success")
            manifest = result["data"]
            self.assertEqual(manifest["success_count"], 1)
            self.assertEqual(manifest["failed_count"], 0)
            record = manifest["records"][0]
            self.assertEqual(record["status"], "success")
            self.assertEqual(record["locator_type"], "local_path")
            downloaded_path = Path(tmpdir) / record["relative_path"]
            self.assertTrue(downloaded_path.exists())
            self.assertEqual(downloaded_path.read_text(encoding="utf-8"), fixture_content)
            manifest_path = Path(tmpdir) / "download_manifest.json"
            self.assertTrue(manifest_path.exists())

    def test_download_runtime_supports_mocked_http_download(self) -> None:
        class _FakeResponse:
            def __init__(self, payload: bytes) -> None:
                self.payload = payload
                self.offset = 0

            def read(self, size: int = -1) -> bytes:
                if size is None or size < 0:
                    size = len(self.payload) - self.offset
                chunk = self.payload[self.offset : self.offset + size]
                self.offset += len(chunk)
                return chunk

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "tcga_gtex.download.task_runner.request.urlopen",
                return_value=_FakeResponse(b"http fixture payload\n"),
            ) as urlopen_mock:
                result = download_tcga_gtex_dataset(
                    "GTEX-LUNG",
                    tmpdir,
                    options={
                        "resolved_records": [
                            FileRecord(
                                source="gtex",
                                study_id="GTEX-LUNG",
                                file_id="GTEX-LUNG:expression",
                                file_name="gtex_lung_expression.tsv.gz",
                                guessed_role="expression",
                                download_url="https://example.test/gtex_lung_expression.tsv.gz",
                            )
                        ]
                    },
                )

            self.assertEqual(result["status"], "success")
            urlopen_mock.assert_called_once()
            record = result["data"]["records"][0]
            self.assertEqual(record["locator_type"], "download_url")
            downloaded_path = Path(tmpdir) / record["relative_path"]
            self.assertEqual(downloaded_path.read_bytes(), b"http fixture payload\n")

    def test_download_runtime_returns_failed_without_locator(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = download_tcga_gtex_dataset(
                "TCGA-BRCA",
                tmpdir,
                options={
                    "resolved_records": [
                        FileRecord(
                            source="tcga_gdc",
                            study_id="TCGA-BRCA",
                            file_id="TCGA-BRCA:expression",
                            file_name="tcga_brca_expression.tsv.gz",
                            guessed_role="expression",
                        )
                    ]
                },
            )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["data"]["failed_count"], 1)
        self.assertIn("Missing downloadable locator", result["data"]["records"][0]["error_message"])

    def test_download_runtime_returns_failed_when_local_path_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = download_tcga_gtex_dataset(
                "TCGA-BRCA",
                tmpdir,
                options={
                    "resolved_records": [
                        FileRecord(
                            source="tcga_gdc",
                            study_id="TCGA-BRCA",
                            file_id="TCGA-BRCA:expression",
                            file_name="tcga_brca_expression.tsv.gz",
                            guessed_role="expression",
                            local_path=str(Path(tmpdir) / "missing.tsv.gz"),
                        )
                    ]
                },
            )

        self.assertEqual(result["status"], "failed")
        self.assertIn("does not exist", result["data"]["records"][0]["error_message"])

    def test_download_runtime_outputs_can_be_bundled_and_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = Path(tmpdir) / "fixtures"
            fixture_dir.mkdir()
            expression_path = fixture_dir / "tcga_brca_expression.tsv.gz"
            clinical_path = fixture_dir / "tcga_brca_clinical.json"
            expression_path.write_text("gene\tsample\nTP53\t5\n", encoding="utf-8")
            clinical_path.write_text('{"patient":"case-1"}', encoding="utf-8")

            download_result = download_tcga_gtex_dataset(
                "TCGA-BRCA",
                tmpdir,
                options={
                    "resolved_records": [
                        FileRecord(
                            source="tcga_gdc",
                            study_id="TCGA-BRCA",
                            file_id="TCGA-BRCA:expression",
                            file_name="tcga_brca_expression.tsv.gz",
                            guessed_role="expression",
                            local_path=str(expression_path),
                        ),
                        FileRecord(
                            source="tcga_gdc",
                            study_id="TCGA-BRCA",
                            file_id="TCGA-BRCA:clinical",
                            file_name="tcga_brca_clinical.json",
                            guessed_role="clinical",
                            local_path=str(clinical_path),
                        ),
                    ]
                },
            )

            bundle_result = build_tcga_gtex_bundle(tmpdir)
            summary_result = get_tcga_gtex_summary(tmpdir)

            self.assertEqual(download_result["status"], "success")
            self.assertEqual(bundle_result["status"], "success")
            self.assertEqual(summary_result["status"], "success")
            self.assertEqual(summary_result["data"]["summary"]["study_ids"], ["TCGA-BRCA"])
            self.assertIn("metadata_ready", summary_result["data"]["summary"]["analysis_compatible"])

    def test_build_bundle_and_summary_create_real_bundle_artifacts_from_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            resolved_records = resolve_tcga_files("乳腺癌")["results"][:2]
            for record in resolved_records:
                fixture_path = Path(tmpdir) / record["file_name"]
                fixture_path.write_text(f"fixture for {record['file_id']}", encoding="utf-8")

            bundle_result = build_tcga_gtex_bundle(tmpdir)
            summary_result = get_tcga_gtex_summary(tmpdir)

            resolved = str(Path(tmpdir).resolve())
            self.assertEqual(bundle_result["status"], "success")
            self.assertEqual(summary_result["status"], "success")
            self.assertEqual(bundle_result["output_dir"], resolved)
            self.assertEqual(summary_result["output_dir"], resolved)
            self.assertTrue(bundle_result["bundle_path"].endswith("analysis_bundle.json"))
            self.assertTrue(summary_result["bundle_path"].endswith("analysis_bundle.json"))

            bundle_path = Path(bundle_result["bundle_path"])
            manifest_path = Path(tmpdir) / "bundle_manifest.json"
            summary_path = Path(tmpdir) / "bundle_summary.json"

            self.assertTrue(bundle_path.exists())
            self.assertTrue(manifest_path.exists())
            self.assertTrue(summary_path.exists())

            bundle_payload = bundle_result["data"]["bundle"]
            manifest_payload = bundle_result["data"]["manifest"]
            summary_payload = summary_result["data"]["summary"]

            self.assertEqual(bundle_payload["source"], "tcga_gdc")
            self.assertEqual(bundle_payload["study_id"], "TCGA-BRCA")
            self.assertEqual(summary_payload["status"], "success")
            self.assertEqual(summary_payload["input_file_count"], 2)
            self.assertEqual(summary_payload["study_ids"], ["TCGA-BRCA"])
            self.assertIn("expression", summary_payload["guessed_roles"])
            self.assertEqual(manifest_payload["input_file_count"], 2)
            self.assertEqual(len(manifest_payload["input_files"]), 2)
            self.assertEqual(summary_result["data"]["bundle"]["metadata"]["manifest_path"], "bundle_manifest.json")

    def test_build_bundle_returns_failed_for_missing_or_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_result = build_tcga_gtex_bundle(tmpdir)
            missing_result = build_tcga_gtex_bundle(str(Path(tmpdir) / "missing"))

        self.assertEqual(empty_result["status"], "failed")
        self.assertIn("No local TCGA/GTEx input files", empty_result["message"])
        self.assertEqual(missing_result["status"], "failed")
        self.assertIn("does not exist", missing_result["message"])

    def test_get_summary_returns_failed_when_bundle_artifacts_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_tcga_gtex_summary(tmpdir)

        self.assertEqual(result["status"], "failed")
        self.assertIn("analysis bundle file does not exist", result["message"])

    def test_tcga_adapter_search_supports_major_disease_queries(self) -> None:
        expectations = {
            "乳腺癌": {"TCGA-BRCA"},
            "肺腺癌": {"TCGA-LUAD"},
            "肺鳞癌": {"TCGA-LUSC"},
            "肝细胞癌": {"TCGA-LIHC"},
            "结直肠癌": {"TCGA-COAD", "TCGA-READ"},
            "肾癌": {"TCGA-KICH", "TCGA-KIRC", "TCGA-KIRP"},
        }
        for query, expected_ids in expectations.items():
            with self.subTest(query=query):
                result = search_tcga(query)
                self.assertEqual({record["study_id"] for record in result["results"]}, expected_ids)

    def test_gtex_adapter_search_supports_tissue_and_resource_queries(self) -> None:
        lung_result = search_gtex("正常肺组织")
        self.assertEqual({record["study_id"] for record in lung_result["results"]}, {"GTEX-LUNG"})

        resource_result = search_gtex("基因表达")
        self.assertEqual({record["study_id"] for record in resource_result["results"]}, {"GTEX-GENE-EXPRESSION"})
        self.assertEqual(resource_result["results"][0]["available_data_types"], ["gene expression"])

    def test_new_disease_queries_return_expected_tcga_projects(self) -> None:
        expectations = {
            "宫颈癌": {"TCGA-CESC"},
            "子宫内膜癌": {"TCGA-UCEC"},
            "膀胱癌": {"TCGA-BLCA"},
            "肾透明细胞癌": {"TCGA-KIRC"},
            "肾乳头状癌": {"TCGA-KIRP"},
            "头颈鳞癌": {"TCGA-HNSC"},
            "食管癌": {"TCGA-ESCA"},
            "胆管癌": {"TCGA-CHOL"},
            "间皮瘤": {"TCGA-MESO"},
            "胸腺瘤": {"TCGA-THYM"},
            "睾丸生殖细胞肿瘤": {"TCGA-TGCT"},
            "肉瘤": {"TCGA-SARC"},
            "低级别胶质瘤": {"TCGA-LGG"},
            "肾上腺皮质癌": {"TCGA-ACC"},
            "嗜铬细胞瘤 / 副神经节瘤": {"TCGA-PCPG"},
        }
        for query, expected_ids in expectations.items():
            with self.subTest(query=query):
                result = search_tcga(query)
                self.assertEqual({record["study_id"] for record in result["results"]}, expected_ids)

    def test_new_tissue_queries_return_expected_gtex_tissues(self) -> None:
        expectations = {
            "肾脏": {"GTEX-KIDNEY"},
            "膀胱": {"GTEX-BLADDER"},
            "宫颈": {"GTEX-CERVIX-UTERI"},
            "子宫": {"GTEX-UTERUS"},
            "食管": {"GTEX-ESOPHAGUS"},
            "小肠": {"GTEX-SMALL-INTESTINE"},
            "唾液腺": {"GTEX-MINOR-SALIVARY-GLAND"},
            "垂体": {"GTEX-PITUITARY"},
            "肾上腺": {"GTEX-ADRENAL-GLAND"},
            "睾丸": {"GTEX-TESTIS"},
            "输卵管": {"GTEX-FALLOPIAN-TUBE"},
            "阴道": {"GTEX-VAGINA"},
            "神经": {"GTEX-NERVE"},
            "血管": {"GTEX-BLOOD-VESSEL"},
            "心脏": {"GTEX-HEART"},
            "肌肉": {"GTEX-MUSCLE"},
        }
        for query, expected_ids in expectations.items():
            with self.subTest(query=query):
                result = search_gtex(query)
                self.assertEqual({record["study_id"] for record in result["results"]}, expected_ids)

    def test_umbrella_queries_return_expected_source_groups(self) -> None:
        expectations = {
            "肺癌": {"TCGA-LUAD", "TCGA-LUSC"},
            "肾癌": {"TCGA-KICH", "TCGA-KIRC", "TCGA-KIRP"},
            "妇科肿瘤": {"TCGA-CESC", "TCGA-OV", "TCGA-UCEC", "TCGA-UCS"},
            "消化系统肿瘤": {"TCGA-CHOL", "TCGA-COAD", "TCGA-ESCA", "TCGA-LIHC", "TCGA-PAAD", "TCGA-READ", "TCGA-STAD"},
            "血液肿瘤": {"TCGA-DLBC", "TCGA-LAML"},
        }
        for query, expected_ids in expectations.items():
            with self.subTest(query=query):
                result = search_tcga(query)
                self.assertEqual({record["study_id"] for record in result["results"]}, expected_ids)

    def test_tcga_file_resolution_returns_expected_roles(self) -> None:
        result = resolve_tcga_files("乳腺癌")
        self.assertEqual(len(result["results"]), 4)
        roles = {record["guessed_role"] for record in result["results"]}
        self.assertEqual(roles, {"expression", "clinical", "biospecimen", "mutation"})
        self.assertEqual({record["study_id"] for record in result["results"]}, {"TCGA-BRCA"})

    def test_gtex_file_resolution_returns_expected_roles(self) -> None:
        result = resolve_gtex_files("正常肺组织")
        roles = {record["guessed_role"] for record in result["results"]}
        self.assertEqual(
            roles,
            {"expression", "sample_metadata", "subject_metadata", "eqtl", "sqtl", "expression_tpm", "expression_counts"},
        )
        self.assertEqual({record["study_id"] for record in result["results"]}, {"GTEX-LUNG"})

    def test_unified_file_resolution_combines_tcga_and_gtex_candidates(self) -> None:
        result = resolve_tcga_gtex_files("肺癌 + 基因表达 + 开放访问")
        self.assertEqual(result["status"], "success")
        tcga_files = result["data"]["results_by_source"]["tcga_gdc"]
        gtex_files = result["data"]["results_by_source"]["gtex"]
        self.assertTrue(tcga_files)
        self.assertTrue(gtex_files)
        self.assertEqual({record["study_id"] for record in tcga_files}, {"TCGA-LUAD", "TCGA-LUSC"})
        self.assertEqual({record["study_id"] for record in gtex_files}, {"GTEX-LUNG"})
        self.assertIn("selected_studies", result["data"]["explanation"])
        self.assertIn("resolved_file_roles", result["data"]["explanation"])


class TcgaGtexModelTests(unittest.TestCase):
    def test_models_serialize_expected_core_fields(self) -> None:
        query = QueryMapping(raw_query="甲状腺癌")
        study = StudyRecord(source="tcga", study_id="TCGA-THCA", title_en="Thyroid carcinoma")
        file_record = FileRecord(source="tcga", study_id="TCGA-THCA", file_id="file-1", file_name="counts.tsv")
        download = DownloadResult(
            source="tcga",
            study_id="TCGA-THCA",
            download_success=False,
            local_path="/tmp/tcga",
        )
        bundle = AnalysisBundle(source="gtex", study_id="GTEX-THYROID", bundle_dir="/tmp/bundle")

        self.assertEqual(query.to_dict()["raw_query"], "甲状腺癌")
        self.assertEqual(study.to_dict()["source"], "tcga")
        self.assertEqual(file_record.to_dict()["file_name"], "counts.tsv")
        self.assertIn("status", download.to_dict())
        self.assertIn("matrix_kind", bundle.to_dict())
        self.assertIn("cross_source_safe", bundle.to_dict())


if __name__ == "__main__":
    unittest.main()
