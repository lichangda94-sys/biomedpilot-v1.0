from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from geo_processing.module1_readers import (
    handoff_recommended_strategy,
    load_module1_dataset_context,
    read_download_plan,
    read_download_receipt,
    read_selected_results,
)


class Module1ReaderTests(unittest.TestCase):
    def test_read_selected_results_supports_legacy_rows(self) -> None:
        payload = [
            {
                "gse_id": "GSE1000",
                "title_en": "Demo title",
                "summary_en": "Demo summary",
                "organism": "Homo sapiens",
                "platform": "GPL570",
                "experiment_type": "Expression profiling by array",
            }
        ]
        rows = read_selected_results(payload)
        self.assertEqual(rows[0]["dataset_id"], "GSE1000")
        self.assertEqual(rows[0]["gse_id"], "GSE1000")
        self.assertEqual(rows[0]["source_db"], "geo")
        self.assertTrue(rows[0]["preview_available"])

    def test_read_selected_results_prefers_new_schema(self) -> None:
        payload = {
            "items": [
                {
                    "schema_version": "module1.search_result.v1",
                    "dataset_id": "GSE1001",
                    "source_db": "geo",
                    "title": "标准化标题",
                    "summary": "标准化摘要",
                    "organism": "Homo sapiens",
                    "platform": "GPL1111",
                    "assay_type": "bulk_rnaseq",
                    "candidate_files": [],
                    "recommended_strategy": "MANUAL_REVIEW_REQUIRED",
                    "confidence": 0.9,
                    "preview_available": True,
                }
            ]
        }
        rows = read_selected_results(payload)
        self.assertEqual(rows[0]["dataset_id"], "GSE1001")
        self.assertEqual(rows[0]["title"], "标准化标题")
        self.assertEqual(rows[0]["assay_type"], "bulk_rnaseq")

    def test_read_download_plan_supports_legacy_wrapper(self) -> None:
        payload = {"plan": [{"accession": "GSE2000", "file_name": "GSE2000_family.soft.gz"}]}
        plan = read_download_plan(payload)
        self.assertEqual(plan["schema_version"], "module1.download_plan.v1")
        self.assertEqual(plan["plan"][0]["file_name"], "GSE2000_family.soft.gz")

    def test_read_download_receipt_supports_transaction_log(self) -> None:
        payload = [
            {
                "accession": "GSE2001",
                "source_level": "series",
                "source_accession": "GSE2001",
                "guessed_role": "family_soft",
                "remote_url": "https://example.org/GSE2001_family.soft.gz",
                "response_status": "success",
                "final_saved_path": "/tmp/GSE2001_family.soft.gz",
                "file_size_on_disk": 123,
                "request_started_at": 1,
                "request_finished_at": 2,
            }
        ]
        receipt = read_download_receipt(payload, dataset_root=".")
        self.assertEqual(receipt["schema_version"], "module1.download_receipt.v1")
        self.assertEqual(receipt["files"][0]["status"], "downloaded")

    def test_load_module1_dataset_context_prefers_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            reports = root / "organized" / "reports"
            reports.mkdir(parents=True, exist_ok=True)
            handoff = {
                "schema_version": "module1.handoff.v1",
                "dataset_id": "GSE3000",
                "recommended_strategy": "SERIES_MATRIX_FIRST",
                "value_type_hint": "count",
                "dataset_info": {
                    "dataset_id": "GSE3000",
                    "source_db": "geo",
                    "legacy_status": "ANALYSIS_READY",
                    "download_dir": str(root),
                    "recommended_strategy": "SERIES_MATRIX_FIRST",
                    "value_type_hint": "count",
                },
                "file_inventory": [],
                "file_roles": {},
                "parser_hints": {"recommended_strategy": "SOFT_METADATA_PLUS_SUPP_MATRIX"},
                "dataset_manifest_draft": {"recommended_strategy": "SOFT_METADATA_PLUS_SUPP_MATRIX"},
                "standard_assets": {
                    "dataset_manifest": {
                        "asset_key": "dataset_manifest",
                        "relative_path": "organized/dataset_manifest.json",
                        "canonical_path": str(root / "organized" / "dataset_manifest.json"),
                        "exists": False,
                        "expected": True,
                        "status": "planned",
                        "source_hint": "persisted",
                        "reason": "persisted_from_handoff",
                    }
                },
                "may_generate_expression_gene": True,
                "may_generate_sample_annotation": True,
                "has_clinical_info": False,
                "has_mutation_info": False,
                "has_batch_info": False,
            }
            (reports / "module1_handoff.json").write_text(json.dumps(handoff, ensure_ascii=False), encoding="utf-8")
            context = load_module1_dataset_context(root)
            self.assertEqual(context["dataset_id"], "GSE3000")
            self.assertEqual(handoff_recommended_strategy(context), "SERIES_MATRIX_FIRST")
            self.assertEqual(context["asset_role_counts"], {})
            self.assertIn("standard_assets", context)
            self.assertEqual(context["standard_assets"]["dataset_manifest"]["status"], "planned")
            self.assertEqual(context["standard_assets"]["dataset_manifest"]["source_hint"], "persisted")
            self.assertEqual(context["standard_assets"]["dataset_manifest"]["reason_code"], "inferred_from_handoff")

    def test_load_module1_dataset_context_mirrors_dataset_info_to_top_level(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            reports = root / "organized" / "reports"
            reports.mkdir(parents=True, exist_ok=True)
            handoff = {
                "schema_version": "module1.handoff.v1",
                "dataset_info": {
                    "dataset_id": "GSE3002",
                    "source_db": "geo",
                    "download_dir": str(root),
                    "recommended_strategy": "SERIES_MATRIX_FIRST",
                    "value_type_hint": "count",
                },
                "file_inventory": [],
                "parser_hints": {
                    "dataset_id": "GSE3002",
                    "recommended_strategy": "SOFT_METADATA_PLUS_SUPP_MATRIX",
                    "default_value_type_hint": "normalized",
                },
                "dataset_manifest_draft": {
                    "dataset_id": "GSE3002",
                    "recommended_strategy": "SOFT_METADATA_PLUS_SUPP_MATRIX",
                    "value_type_hint": "normalized",
                },
                "standard_assets": {
                    "dataset_manifest": {
                        "source_hint": "persisted_only",
                    }
                },
                "module1_state": {"current_state": "partial_success"},
            }
            (reports / "module1_handoff.json").write_text(json.dumps(handoff, ensure_ascii=False), encoding="utf-8")

            context = load_module1_dataset_context(root)

            self.assertEqual(context["dataset_id"], "GSE3002")
            self.assertEqual(context["recommended_strategy"], "SERIES_MATRIX_FIRST")
            self.assertEqual(context["value_type_hint"], "count")
            self.assertEqual(context["dataset_info"]["dataset_id"], "GSE3002")
            self.assertEqual(context["standard_assets"]["dataset_manifest"]["status"], "planned")
            self.assertTrue(context["standard_assets"]["dataset_manifest"]["expected"])
            self.assertIn("dataset_manifest", context["planned_assets"])
            self.assertIn("dataset_manifest", context["canonical_asset_paths"])
            self.assertIn("module1_handoff", context["supporting_contracts"])
            self.assertEqual(context["standard_assets"]["dataset_manifest"]["reason_code"], "inferred_from_handoff")
            for field in ("expected", "exists", "status", "source_hint", "canonical_path", "reason_code"):
                self.assertIn(field, context["standard_assets"]["dataset_manifest"])

    def test_load_module1_dataset_context_falls_back_to_validation_payload(self) -> None:
        validation_payload = {
            "gse_id": "GSE3001",
            "download_dir": "/tmp/GSE3001",
            "status": "ANALYSIS_READY",
            "has_expression_payload": True,
            "has_sample_annotation": True,
            "has_clinical_annotation": False,
            "has_family_soft": True,
            "payload_type": "expression_matrix",
            "platform_annotation_files": [],
            "archive_files": [],
            "supporting_files": [],
            "external_sources": [],
            "extra": {
                "file_scores": [
                    {
                        "relative_path": "GSE3001_series_matrix.txt.gz",
                        "path": "/tmp/GSE3001/GSE3001_series_matrix.txt.gz",
                        "size_bytes": 100,
                        "primary_label": "expression_payload",
                        "secondary_labels": [],
                        "confidence": 0.9,
                        "preview_lines": ["gene_id\tGSM1\tGSM2"],
                        "organized_targets": [],
                        "source_level": "downloaded",
                        "source_path": "/tmp/GSE3001/GSE3001_series_matrix.txt.gz",
                    }
                ]
            },
        }
        context = load_module1_dataset_context("/tmp/GSE3001", validation_payload=validation_payload)
        self.assertEqual(context["dataset_info"]["dataset_id"], "GSE3001")
        self.assertEqual(handoff_recommended_strategy(context), "SOFT_METADATA_PLUS_SUPP_MATRIX")
        self.assertTrue(context["may_generate_expression_gene"])
        self.assertIn("expression_gene_possible", context["available_capabilities"])
        self.assertEqual(context["standard_assets"]["expression_gene"]["status"], "planned")
        self.assertEqual(context["standard_assets"]["expression_gene"]["reason_code"], "inferred_from_legacy")

    def test_load_module1_dataset_context_legacy_supporting_files_still_build_stable_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            reports = root / "organized" / "reports"
            reports.mkdir(parents=True, exist_ok=True)

            parser_hints = {
                "schema_version": "module1.parser_hints.v1",
                "dataset_id": "GSE3003",
                "recommended_strategy": "SERIES_MATRIX_FIRST",
                "default_value_type_hint": "count",
                "matrix_candidates": ["expr.tsv"],
                "metadata_candidates": ["sample_sheet.tsv"],
                "feature_annotation_candidates": [],
                "clinical_candidates": [],
                "mutation_candidates": [],
                "may_generate_expression_gene": True,
                "may_generate_sample_annotation": True,
                "has_clinical_info": False,
                "has_mutation_info": False,
                "has_batch_info": False,
            }
            manifest = {
                "schema_version": "module1.dataset_manifest_draft.v1",
                "dataset_id": "GSE3003",
                "recommended_strategy": "SERIES_MATRIX_FIRST",
                "value_type_hint": "count",
                "has_sample_annotation": True,
                "platform_annotation_files": [],
            }
            inventory = {
                "schema_version": "module1.file_inventory.v1",
                "dataset_id": "GSE3003",
                "source_db": "geo",
                "dataset_root": str(root),
                "files": [
                    {"relative_path": "expr.tsv", "file_role": "expression_candidate"},
                    {"relative_path": "sample_sheet.tsv", "file_role": "metadata_candidate"},
                ],
            }
            (reports / "parser_hints.json").write_text(json.dumps(parser_hints, ensure_ascii=False), encoding="utf-8")
            (reports / "dataset_manifest_draft.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
            (reports / "file_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False), encoding="utf-8")

            context = load_module1_dataset_context(root)

            self.assertEqual(context["dataset_id"], "GSE3003")
            self.assertEqual(context["recommended_strategy"], "SERIES_MATRIX_FIRST")
            self.assertEqual(context["value_type_hint"], "count")
            self.assertEqual(context["file_inventory"], inventory["files"])
            self.assertEqual(sorted(context["canonical_asset_paths"]), ["dataset_manifest", "expression_gene", "feature_annotation", "sample_annotation"])
            self.assertEqual(context["supporting_contracts"]["module1_handoff"], None)
            self.assertEqual(context["present_assets"], [])
            self.assertIn("dataset_manifest", context["planned_assets"])
            for asset_key in ("expression_gene", "sample_annotation", "feature_annotation", "dataset_manifest"):
                asset = context["standard_assets"][asset_key]
                for field in ("expected", "exists", "status", "source_hint", "canonical_path", "reason_code"):
                    self.assertIn(field, asset)
            self.assertEqual(context["standard_assets"]["expression_gene"]["reason_code"], "inferred_from_legacy")
            self.assertEqual(context["standard_assets"]["dataset_manifest"]["reason_code"], "inferred_from_legacy")

    def test_load_module1_dataset_context_marks_missing_dataset_id_reason_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            reports = root / "organized" / "reports"
            reports.mkdir(parents=True, exist_ok=True)
            handoff = {
                "schema_version": "module1.handoff.v1",
                "recommended_strategy": "SERIES_MATRIX_FIRST",
                "value_type_hint": "count",
                "dataset_info": {
                    "dataset_id": "",
                    "source_db": "geo",
                    "download_dir": str(root),
                },
                "module1_state": {"current_state": "partial_success"},
            }
            (reports / "module1_handoff.json").write_text(json.dumps(handoff, ensure_ascii=False), encoding="utf-8")

            context = load_module1_dataset_context(root)

            manifest_asset = context["standard_assets"]["dataset_manifest"]
            self.assertEqual(manifest_asset["status"], "not_applicable")
            self.assertEqual(manifest_asset["reason_code"], "missing_dataset_id")

    def test_stale_canonical_file_is_not_promoted_to_present_asset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            stale_manifest = root / "organized" / "dataset_manifest.json"
            stale_manifest.parent.mkdir(parents=True, exist_ok=True)
            stale_manifest.write_text("{}", encoding="utf-8")

            validation_payload = {
                "gse_id": "GSE3999",
                "download_dir": str(root),
                "status": "EMPTY_OR_BROKEN",
                "has_expression_payload": False,
                "has_sample_annotation": False,
                "has_clinical_annotation": False,
                "has_family_soft": False,
                "payload_type": "unknown",
                "platform_annotation_files": [],
                "archive_files": [],
                "supporting_files": [],
                "external_sources": [],
                "extra": {"file_scores": []},
            }

            context = load_module1_dataset_context(root, validation_payload=validation_payload)
            self.assertTrue(context["standard_assets"]["dataset_manifest"]["exists"])
            self.assertEqual(context["standard_assets"]["dataset_manifest"]["status"], "not_applicable")
            self.assertEqual(context["standard_assets"]["dataset_manifest"]["reason_code"], "not_expected")
            self.assertNotIn("dataset_manifest", context["present_assets"])


if __name__ == "__main__":
    unittest.main()
