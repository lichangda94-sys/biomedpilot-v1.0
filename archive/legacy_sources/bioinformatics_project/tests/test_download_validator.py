from __future__ import annotations

import gzip
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from geo_processing.download_validator import inspect_download_file, validate_downloaded_dataset


def _write_text(path: Path, content: str, gz: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if gz:
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            handle.write(content)
        return
    path.write_text(content, encoding="utf-8")


class DownloadValidatorTests(unittest.TestCase):
    def test_analysis_ready_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(
                root / "GSE1000_series_matrix.txt.gz",
                "!Series_title = demo\n!Sample_title = A\nID_REF\tGSM1\tGSM2\tGSM3\nTP53\t2.1\t2.2\t2.3\nEGFR\t3.1\t3.2\t3.3\n",
                gz=True,
            )
            _write_text(
                root / "GSE1000_family.soft.gz",
                "^SERIES = GSE1000\n^SAMPLE = GSM1\n^SAMPLE = GSM2\n!sample_table_begin\nsample\tgroup\nGSM1\tcase\nGSM2\tcontrol\n!sample_table_end\n",
                gz=True,
            )
            result = validate_downloaded_dataset("noise", str(root))
            self.assertEqual(result.gse_id, "GSE1000")
            self.assertEqual(result.status, "ANALYSIS_READY")
            self.assertTrue(result.has_expression_payload)
            self.assertTrue(result.has_sample_annotation)
            self.assertEqual(result.failure_stage, "dataset_aggregation")

    def test_expression_only_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(
                root / "counts.tsv",
                "gene_id\tGSM1\tGSM2\nENSG1\t10\t20\nENSG2\t30\t40\n",
            )
            result = validate_downloaded_dataset("GSE1001", str(root))
            self.assertEqual(result.status, "EXPRESSION_ONLY")
            self.assertEqual(result.payload_type, "expression_matrix")

    def test_metadata_only_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "sample_sheet.tsv", "sample_id\tgroup\nGSM1\tcase\nGSM2\tcontrol\n")
            result = validate_downloaded_dataset("GSE1002", str(root))
            self.assertEqual(result.status, "METADATA_ONLY")
            self.assertTrue(result.has_sample_annotation)
            self.assertFalse(result.has_expression_payload)

    def test_raw_only_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "raw" / "sample_1.fastq.gz", "@SEQ_ID\nACGT\n+\n!!!!\n", gz=True)
            result = validate_downloaded_dataset("GSE1003", str(root))
            self.assertEqual(result.status, "RAW_ONLY")
            self.assertEqual(result.payload_type, "raw_only")

    def test_no_expression_payload_annotation_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "GPL570.annot.txt", "ID\tGene Symbol\n1007_s_at\tDDR1\n")
            result = validate_downloaded_dataset("GSE1004", str(root))
            self.assertEqual(result.status, "NO_EXPRESSION_PAYLOAD")
            self.assertFalse(result.has_expression_payload)

    def test_filters_system_noise_and_generated_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "GSE6004_series_matrix.txt.gz", "!Series_title = demo\nID_REF\tGSM1\tGSM2\nTP53\t1\t2\n", gz=True)
            (root / ".DS_Store").write_text("garbage", encoding="utf-8")
            (root / "download_validation.json").write_text("{}", encoding="utf-8")
            (root / "processed_GSE6004").mkdir()
            (root / "processed_GSE6004" / "expression_probe_clean.csv").write_text("x", encoding="utf-8")
            result = validate_downloaded_dataset("bad_name", str(root))
            self.assertEqual(result.file_count, 1)
            self.assertNotIn(".DS_Store", result.ignored_files)
            self.assertEqual(result.gse_id, "GSE6004")

    def test_html_error_page_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            file_path = root / "GSE1005_family.soft.gz"
            file_path.write_text("<html><body>404 Not Found</body></html>", encoding="utf-8")
            detail = inspect_download_file(str(file_path))
            self.assertTrue(detail["excluded"])
            self.assertEqual(detail["primary_label"], "ignored")

    def test_family_soft_full_scan_supports_sample_annotation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            content = "^SERIES = GSE153659\n" + "".join(f"!Series_note = line {i}\n" for i in range(50))
            content += "^SAMPLE = GSM1\n!Sample_title = A\n^SAMPLE = GSM2\n!Sample_title = B\n"
            _write_text(root / "GSE153659_family.soft.gz", content, gz=True)
            result = validate_downloaded_dataset("wrong_name", str(root))
            self.assertEqual(result.gse_id, "GSE153659")
            self.assertTrue(result.has_family_soft)
            self.assertTrue(result.has_sample_annotation)

    def test_file_scores_are_exported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "sample_sheet.tsv", "sample_id\tgroup\nGSM1\tcase\n")
            result = validate_downloaded_dataset("GSE1006", str(root))
            json.dumps(result.to_dict(), ensure_ascii=False)
            self.assertTrue(result.extra["file_scores"])
            self.assertTrue(result.organized_paths["reports"])
            self.assertTrue((root / "organized" / "reports" / "data_asset_index.json").exists())
            self.assertTrue((root / "organized" / "reports" / "file_inventory.json").exists())
            self.assertTrue((root / "organized" / "reports" / "parser_hints.json").exists())
            self.assertTrue((root / "organized" / "reports" / "dataset_manifest_draft.json").exists())
            self.assertTrue((root / "organized" / "reports" / "module1_handoff.json").exists())

    def test_empty_download_surfaces_transaction_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            report_dir = root / "raw_downloads" / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            (report_dir / "download_transaction_log.json").write_text(
                json.dumps(
                    [
                        {
                            "file_type": "family_soft",
                            "response_status": "failed",
                            "file_exists_after_save": False,
                            "file_size_on_disk": 0,
                            "error_message": "request failed",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = validate_downloaded_dataset("GSE1999", str(root))
            self.assertEqual(result.status, "EMPTY_OR_BROKEN")
            self.assertIn("request failed", result.errors)
            self.assertEqual(result.organized_paths["reports"], [])

    def test_file_count_zero_still_reports_specific_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "raw_downloads" / "reports").mkdir(parents=True, exist_ok=True)
            result = validate_downloaded_dataset("GSE2999", str(root))
            self.assertEqual(result.status, "EMPTY_OR_BROKEN")
            self.assertTrue(result.errors)
            self.assertIn("download finished with no saved", "\n".join(result.errors).lower())

    def test_download_summary_errors_are_forwarded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            report_dir = root / "raw_downloads" / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            (report_dir / "core_download_summary.json").write_text(
                json.dumps(
                    {
                        "status": "failed",
                        "download_success": False,
                        "error": "destination path mismatch",
                        "errors": ["write failed"],
                        "path_consistency": {
                            "dataset_root": str(root),
                            "downloader_writes_to": str(root / "raw_downloads"),
                            "validation_scans": str(root),
                            "organized_reports_to": str(root / "organized" / "reports"),
                            "raw_report_dir": str(report_dir),
                            "download_targets": [str(root / "outside" / "ghost.soft.gz")],
                            "paths_consistent": False,
                            "outside_raw_download_root": [str(root / "outside" / "ghost.soft.gz")],
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            result = validate_downloaded_dataset("GSE3000", str(root))
            self.assertEqual(result.status, "EMPTY_OR_BROKEN")
            self.assertIn("destination path mismatch", "\n".join(result.errors))
            self.assertIn("inconsistent", "\n".join(result.errors).lower())

    def test_large_family_soft_exports_section_debug_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            content = "^DATABASE = GeoMiame\n" + "".join(f"!Series_note = {i}\n" for i in range(120))
            content += "^SAMPLE = GSM1\n!Sample_title = A\n^SAMPLE = GSM2\n!Sample_title = B\n!sample_table_begin\nsample\tgroup\nGSM1\tcase\nGSM2\tcontrol\n!sample_table_end\n"
            _write_text(root / "GSE2007_family.soft.gz", content, gz=True)
            detail = inspect_download_file(str(root / "GSE2007_family.soft.gz"))
            self.assertTrue(detail["head_preview"])
            self.assertTrue(detail["middle_preview"])
            self.assertTrue(detail["tail_preview"])
            self.assertIn("^SAMPLE", detail["marker_counts"])
            self.assertIn("sample_block", detail["tail_signals"])

    def test_archive_is_retained_and_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            archive_path = root / "GSE3001_RAW.tar.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("matrix/GSE3001_counts.tsv", "gene\tGSM1\tGSM2\nA\t1\t2\n")
                archive.writestr("docs/README.txt", "raw archive")
            result = validate_downloaded_dataset("GSE3001", str(root))
            self.assertIn("GSE3001_RAW.tar.zip", result.archive_files)
            self.assertIn("organized/archives", "\n".join(result.organized_paths["archives"]))

    def test_external_raw_source_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(
                root / "GSE3002_family.soft.gz",
                "^SERIES = GSE3002\n!Series_relation = SRA: https://www.ncbi.nlm.nih.gov/sra?term=SRP000001\n",
                gz=True,
            )
            result = validate_downloaded_dataset("GSE3002", str(root))
            self.assertTrue(result.external_sources)
            self.assertIn("sra", (result.external_raw_source or "").lower())

    def test_series_matrix_tail_numeric_block_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            preamble = "".join(f"!Series_note = line {i}\n" for i in range(120))
            matrix = "ID_REF\tGSM1\tGSM2\tGSM3\nTP53\t2.1\t2.2\t2.3\nEGFR\t3.1\t3.2\t3.3\n"
            _write_text(root / "GSE2008_series_matrix.txt.gz", preamble + matrix, gz=True)
            detail = inspect_download_file(str(root / "GSE2008_series_matrix.txt.gz"))
            self.assertGreater(detail["expression_score"], 0.6)
            self.assertIn("numeric_matrix_block", detail["tail_signals"] + detail["middle_signals"])

    def test_supplementary_xlsx_expression_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            xlsx_path = root / "GSE4001_counts.xlsx"
            xlsx_path.write_text("placeholder", encoding="utf-8")
            mocked_rows = [
                ["gene_id", "GSM1", "GSM2", "GSM3"],
                ["TP53", "10", "11", "12"],
                ["EGFR", "20", "21", "22"],
                ["BRCA1", "30", "31", "32"],
            ]
            with patch("geo_processing.download_validator.preview_xlsx_rows", return_value=mocked_rows):
                detail = inspect_download_file(str(xlsx_path))
            self.assertEqual(detail["primary_label"], "expression_payload")
            self.assertGreater(detail["expression_score"], 0.6)

    def test_structured_xlsx_is_not_misclassified_as_html_error_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            xlsx_path = root / "GSE4001_counts.xlsx"
            xlsx_path.write_text("placeholder", encoding="utf-8")
            mocked_rows = [
                ["gene_id", "GSM1", "GSM2"],
                ["ENSG000000404", "10", "11"],
                ["ENSG000000405", "20", "21"],
            ]
            with (
                patch("geo_processing.download_validator.preview_xlsx_rows", return_value=mocked_rows),
                patch("geo_processing.detector.matrix_classifier.preview_xlsx_rows", return_value=mocked_rows),
            ):
                detail = inspect_download_file(str(xlsx_path))
            self.assertFalse(detail["excluded"])
            self.assertNotEqual(detail["excluded_reason"], "html error/redirect page was excluded")
            self.assertEqual(detail["primary_label"], "expression_payload")

    def test_inspect_download_file_preserves_series_supplementary_source_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            xlsx_path = root / "raw_downloads" / "supplementary" / "GSE4001_counts.xlsx"
            xlsx_path.parent.mkdir(parents=True, exist_ok=True)
            xlsx_path.write_text("placeholder", encoding="utf-8")
            mocked_rows = [
                ["gene_id", "GSM1", "GSM2"],
                ["TP53", "10", "11"],
                ["EGFR", "20", "21"],
            ]
            with patch("geo_processing.download_validator.preview_xlsx_rows", return_value=mocked_rows):
                detail = inspect_download_file(str(xlsx_path))
            self.assertEqual(detail["source_level"], "series_supplementary")
            self.assertEqual(detail["source_scope"], "series_supplementary")
            self.assertEqual(detail["source_path"], str(xlsx_path.resolve()))
            self.assertEqual(detail["primary_label"], "expression_payload")

    def test_diff_result_is_excluded_from_expression_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "results.csv", "gene,logFC,adj.P.Val,P.Value\nTP53,1.2,0.01,0.02\n")
            result = validate_downloaded_dataset("GSE4002", str(root))
            self.assertNotIn("results.csv", result.candidate_matrix_files)
            self.assertIn(result.status, {"NO_EXPRESSION_PAYLOAD", "EMPTY_OR_BROKEN"})

    def test_annotated_expression_matrix_is_not_demoted_by_loose_diff_hints(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(
                root / "GSE212031_all.genes.expression.annot.txt.gz",
                "id\tCKr-1_fpkm\tCKr-2_fpkm\tCKr-3_fpkm\tSymbol\tDescription\n"
                "ENSG1\t10.1\t11.2\t12.3\tTP53\ttumor protein p53\n"
                "ENSG2\t20.1\t21.2\t22.3\tEGFR\tepidermal growth factor receptor\n",
                gz=True,
            )
            detail = inspect_download_file(str(root / "GSE212031_all.genes.expression.annot.txt.gz"))
            self.assertEqual(detail["primary_label"], "expression_payload")
            self.assertTrue(detail["accepted_as_candidate_matrix"])
            self.assertTrue(detail["accepted_as_payload"])
            self.assertNotIn("looks like differential-result table", detail["warnings"])

    def test_data_asset_index_records_multi_role_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(
                root / "GSE4003_series_matrix.txt.gz",
                "!Series_title = demo\n!Sample_title = A\nID_REF\tGSM1\tGSM2\nTP53\t1\t2\nEGFR\t3\t4\n",
                gz=True,
            )
            result = validate_downloaded_dataset("GSE4003", str(root))
            asset_index = json.loads((root / "organized" / "reports" / "data_asset_index.json").read_text(encoding="utf-8"))
            target = next(item for item in asset_index["files"] if item["relative_path"] == "GSE4003_series_matrix.txt.gz")
            self.assertEqual(target["primary_label"], "expression_payload")
            self.assertEqual(target["standardized_role"], "expression_candidate")
            self.assertIn("sample_annotation", target["secondary_labels"])
            self.assertTrue(any("/organized/expression/" in path for path in target["organized_targets"]))
            self.assertTrue(any("/organized/sample_annotation/" in path for path in target["organized_targets"]))
            self.assertIn("accepted as expression candidate", target["decision_trace"])

    def test_module1_contracts_capture_roles_and_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(
                root / "GSE5000_series_matrix.txt.gz",
                "gene_id\tGSM1\tGSM2\nTP53\t10\t20\nEGFR\t30\t40\n",
                gz=True,
            )
            _write_text(root / "sample_sheet.tsv", "sample_id\tgroup\tbatch\nGSM1\tcase\tb1\nGSM2\tcontrol\tb2\n")
            _write_text(root / "clinical.tsv", "sample_id\tstage\tsurvival\nGSM1\tII\t100\nGSM2\tIII\t90\n")
            _write_text(root / "variants.maf", "Hugo_Symbol\tTumor_Sample_Barcode\nTP53\tGSM1\n")

            result = validate_downloaded_dataset("GSE5000", str(root))

            inventory = json.loads((root / "organized" / "reports" / "file_inventory.json").read_text(encoding="utf-8"))
            roles = {item["relative_path"]: item["file_role"] for item in inventory["files"]}
            self.assertEqual(roles["GSE5000_series_matrix.txt.gz"], "expression_candidate")
            self.assertEqual(roles["sample_sheet.tsv"], "metadata_candidate")
            self.assertEqual(roles["clinical.tsv"], "clinical_candidate")
            self.assertEqual(roles["variants.maf"], "mutation_candidate")

            parser_hints = json.loads((root / "organized" / "reports" / "parser_hints.json").read_text(encoding="utf-8"))
            self.assertTrue(parser_hints["may_generate_expression_gene"])
            self.assertTrue(parser_hints["may_generate_sample_annotation"])
            self.assertTrue(parser_hints["has_clinical_info"])
            self.assertTrue(parser_hints["has_mutation_info"])
            self.assertTrue(parser_hints["has_batch_info"])

            manifest = json.loads((root / "organized" / "reports" / "dataset_manifest_draft.json").read_text(encoding="utf-8"))
            self.assertIn(manifest["recommended_strategy"], {"SERIES_MATRIX_FIRST", "SOFT_METADATA_PLUS_SUPP_MATRIX", "SUPPLEMENTARY_MATRIX_FIRST"})

            handoff = json.loads((root / "organized" / "reports" / "module1_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(handoff["dataset_info"]["dataset_id"], "GSE5000")
            self.assertTrue(handoff["may_generate_expression_gene"])
            self.assertIn("standard_assets", handoff)
            self.assertEqual(handoff["standard_assets"]["expression_gene"]["status"], "planned")
            self.assertTrue(handoff["standard_assets"]["dataset_manifest"]["expected"])
            self.assertTrue(handoff["canonical_asset_paths"]["dataset_manifest"].endswith("organized/dataset_manifest.json"))

    def test_handoff_prefers_supplementary_expression_asset_when_it_is_real_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(
                root / "GSE5100_family.soft.gz",
                "^SERIES = GSE5100\n^SAMPLE = GSM1\n^SAMPLE = GSM2\n!sample_table_begin\nsample\tgroup\nGSM1\tcase\nGSM2\tcontrol\n!sample_table_end\n",
                gz=True,
            )
            xlsx_path = root / "raw_downloads" / "supplementary" / "GSE5100_counts.xlsx"
            xlsx_path.parent.mkdir(parents=True, exist_ok=True)
            xlsx_path.write_text("placeholder", encoding="utf-8")
            mocked_rows = [
                ["gene_id", "GSM1", "GSM2"],
                ["TP53", "10", "11"],
                ["EGFR", "20", "21"],
            ]
            with (
                patch("geo_processing.download_validator.preview_xlsx_rows", return_value=mocked_rows),
                patch("geo_processing.detector.matrix_classifier.preview_xlsx_rows", return_value=mocked_rows),
            ):
                validate_downloaded_dataset("GSE5100", str(root))
            handoff = json.loads((root / "organized" / "reports" / "module1_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(handoff["preferred_expression_asset"]["file_name"], "GSE5100_counts.xlsx")
            self.assertEqual(handoff["preferred_metadata_asset"]["file_name"], "GSE5100_family.soft.gz")

    def test_handoff_surfaces_missing_expression_when_only_family_soft_metadata_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(
                root / "GSE5200_family.soft.gz",
                "^SERIES = GSE5200\n^SAMPLE = GSM1\n^SAMPLE = GSM2\n!sample_table_begin\nsample\tgroup\nGSM1\tcase\nGSM2\tcontrol\n!sample_table_end\n",
                gz=True,
            )
            validate_downloaded_dataset("GSE5200", str(root))
            handoff = json.loads((root / "organized" / "reports" / "module1_handoff.json").read_text(encoding="utf-8"))
            self.assertIsNone(handoff["preferred_expression_asset"])
            self.assertEqual(handoff["preferred_metadata_asset"]["file_name"], "GSE5200_family.soft.gz")
            self.assertIn("expression_asset", handoff["missing_required_assets"])

    def test_handoff_surfaces_archive_only_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            archive_path = root / "GSE5300_RAW.tar.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("raw/sample1.cel", "dummy")
            validate_downloaded_dataset("GSE5300", str(root))
            handoff = json.loads((root / "organized" / "reports" / "module1_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(handoff["asset_role_counts"]["archive"], 1)
            self.assertIn("archive_available", handoff["available_capabilities"])
            self.assertIn("expression_asset", handoff["missing_required_assets"])

    def test_handoff_exposes_clinical_and_mutation_preferred_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "clinical.tsv", "sample_id\tstage\tsurvival\nGSM1\tII\t100\nGSM2\tIII\t90\n")
            _write_text(root / "variants.maf", "Hugo_Symbol\tTumor_Sample_Barcode\nTP53\tGSM1\n")
            validate_downloaded_dataset("GSE5400", str(root))
            handoff = json.loads((root / "organized" / "reports" / "module1_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(handoff["preferred_clinical_asset"]["file_name"], "clinical.tsv")
            self.assertEqual(handoff["preferred_mutation_asset"]["file_name"], "variants.maf")
            self.assertIn("clinical_available", handoff["available_capabilities"])
            self.assertIn("mutation_available", handoff["available_capabilities"])

    def test_handoff_warns_when_multiple_expression_candidates_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "matrix_a.tsv", "gene_id\tGSM1\tGSM2\nTP53\t10\t11\nEGFR\t20\t21\n")
            _write_text(root / "matrix_b.tsv", "gene_id\tGSM1\tGSM2\nBRCA1\t30\t31\nBRCA2\t40\t41\n")
            validate_downloaded_dataset("GSE5500", str(root))
            handoff = json.loads((root / "organized" / "reports" / "module1_handoff.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(handoff["asset_role_counts"]["expression_candidate"], 2)
            self.assertIn("multiple_expression_candidates_detected", handoff["warnings_summary"])

    def test_partial_success_dataset_still_emits_stable_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "expr.tsv", "gene_id\tGSM1\tGSM2\nTP53\t10\t11\nEGFR\t20\t21\n")
            _write_text(root / "GPL5600.annot.txt", "ID\tGene Symbol\n1007_s_at\tDDR1\n")
            result = validate_downloaded_dataset("GSE5600", str(root))
            handoff = json.loads((root / "organized" / "reports" / "module1_handoff.json").read_text(encoding="utf-8"))
            self.assertEqual(result.status, "PARTIAL_BUT_USABLE")
            self.assertEqual(handoff["module1_state"]["current_state"], "partial_success")
            self.assertIsNotNone(handoff["preferred_expression_asset"])
            self.assertTrue(handoff["available_capabilities"])

    def test_decision_trace_and_failure_stage_surface_file_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / ".DS_Store", "garbage")
            _write_text(root / "results.csv", "gene,logFC,adj.P.Val,P.Value\nTP53,1.2,0.01,0.02\n")
            result = validate_downloaded_dataset("GSE4100", str(root))
            self.assertEqual(result.failure_stage, "semantic_classification")
            file_scores = {item["relative_path"]: item for item in result.extra["file_scores"]}
            self.assertIn("excluded from expression preference because diff-result hints were found", file_scores["results.csv"]["decision_trace"])

    def test_expected_vs_actual_diff_and_debug_snapshots_are_exported(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "sample_sheet.tsv", "sample_id\tgroup\nGSM1\tcase\nGSM2\tcontrol\n")
            (root / "expected.json").write_text(
                json.dumps({"status": "ANALYSIS_READY", "has_expression_payload": True}, ensure_ascii=False),
                encoding="utf-8",
            )
            result = validate_downloaded_dataset("GSE4200", str(root))
            diff = result.extra["expected_vs_actual_diff"]
            self.assertIn("status", [item["field"] for item in diff["mismatched_fields"]])
            self.assertTrue((root / "organized" / "reports" / "debug_snapshots" / "01_source_landing.json").exists())
            self.assertTrue((root / "organized" / "reports" / "debug_snapshots" / "04_dataset_aggregation.json").exists())
            self.assertTrue((root / "organized" / "reports" / "debug_snapshots" / "download_validation.json").exists())
            self.assertTrue((root / "organized" / "reports" / "debug_snapshots" / "expected_vs_actual_diff.json").exists())

    def test_missing_expected_json_still_emits_diff_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            _write_text(root / "sample_sheet.tsv", "sample_id\tgroup\nGSM1\tcase\n")
            result = validate_downloaded_dataset("GSE4300", str(root))
            diff = result.extra["expected_vs_actual_diff"]
            self.assertFalse(diff["enabled"])
            self.assertIn("未启用对照测试", diff["summary"])
            self.assertTrue((root / "organized" / "reports" / "expected_vs_actual_diff.json").exists())

    def test_supplementary_expression_xlsx_is_dual_archived(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            xlsx_path = root / "raw_downloads" / "supplementary" / "GSE236866_Processed_data_tau_with_inhibitors.xlsx"
            xlsx_path.parent.mkdir(parents=True, exist_ok=True)
            xlsx_path.write_text("placeholder", encoding="utf-8")
            mocked_rows = [
                ["gene_id", "Sample1", "Sample2", "Sample3"],
                ["TP53", "10", "11", "12"],
                ["EGFR", "20", "21", "22"],
                ["BRCA1", "30", "31", "32"],
            ]
            with (
                patch("geo_processing.download_validator.preview_xlsx_rows", return_value=mocked_rows),
                patch("geo_processing.detector.matrix_classifier.preview_xlsx_rows", return_value=mocked_rows),
            ):
                result = validate_downloaded_dataset("GSE236866", str(root))
            self.assertTrue(result.has_expression_payload)
            self.assertTrue(any(path.endswith("GSE236866_Processed_data_tau_with_inhibitors.xlsx") for path in result.expression_sources))
            asset_index = json.loads((root / "organized" / "reports" / "data_asset_index.json").read_text(encoding="utf-8"))
            target = next(item for item in asset_index["files"] if item["relative_path"].endswith(".xlsx"))
            self.assertEqual(target["source_level"], "series_supplementary")
            self.assertEqual(target["source_scope"], "series_supplementary")
            self.assertTrue(target["accepted_as_candidate_matrix"])
            self.assertTrue(target["accepted_as_payload"])
            self.assertEqual(target["primary_label"], "expression_payload")
            self.assertTrue(any("/organized/expression/" in path for path in target["organized_targets"]))


if __name__ == "__main__":
    unittest.main()
