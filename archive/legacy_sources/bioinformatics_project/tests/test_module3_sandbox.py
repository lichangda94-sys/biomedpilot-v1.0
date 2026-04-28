from __future__ import annotations

import unittest
from pathlib import Path

from geo_processing import build_standard_asset_layout, merge_standard_asset_layout
from geo_processing.detector.models import DatasetDetectionResult
from geo_processing.download_models import DownloadValidationResult
from ui.module3_sandbox import build_sandbox_summary, workflow_result_dataset_dir
from ui.module3_sandbox_formatters import (
    build_detection_summary_text,
    build_file_detail_text,
    build_module3_asset_summary_text,
    build_module3_mainline_summary_text,
    build_validation_summary_text,
    build_workflow_result_text,
)


class Module3SandboxFormattingTests(unittest.TestCase):
    def test_validation_summary_shows_core_objects(self) -> None:
        result = DownloadValidationResult(
            gse_id="GSE7001",
            download_dir="/tmp/GSE7001",
            status="ANALYSIS_READY",
            download_success=True,
            file_count=2,
            nonempty_file_count=2,
            failure_stage="content_inspection",
            has_expression_payload=True,
            has_sample_annotation=True,
            has_clinical_annotation=False,
            payload_type="expression_matrix",
            top_problem_summary="none",
            suggested_next_fix="continue",
            expression_sources=["GSE7001_series_matrix.txt.gz"],
            sample_annotation_sources=["GSE7001_family.soft.gz"],
            archive_files=["RAW.tar"],
            platform_annotation_files=["GPL570.annot.txt"],
            supporting_files=["README.txt"],
            external_sources=["https://www.ncbi.nlm.nih.gov/sra?term=SRP1"],
        )
        text = build_validation_summary_text(result)
        self.assertIn("has_expression_payload: True", text)
        self.assertIn("failure_stage: content_inspection", text)
        self.assertIn("archive_files", text)
        self.assertIn("platform_annotation_files", text)

    def test_detection_summary_shows_candidates(self) -> None:
        result = DatasetDetectionResult(
            accession="GSE7002",
            accession_type="GSE",
            scan_root="/tmp/GSE7002",
            has_expression_payload=True,
            has_sample_annotation=True,
            payload_type="expression_matrix",
            recommended_strategy="SERIES_MATRIX_FIRST",
            failure_stage="dataset_aggregation",
            conflicts=[{"category": "matrix_level_votes", "votes": ["probe", "gene"]}],
            classification_debug={"final_decision_reason": "demo"},
            top_problem_summary="conflict exists",
            suggested_next_fix="check votes",
            candidate_expression_files=["GSE7002_series_matrix.txt.gz"],
            candidate_metadata_files=["GSE7002_family.soft.gz"],
            candidate_clinical_files=["clinical.tsv"],
            archive_files=["RAW.tar"],
            external_sources=["https://www.ncbi.nlm.nih.gov/sra?term=SRP2"],
        )
        text = build_detection_summary_text(result)
        self.assertIn("candidate_expression_files", text)
        self.assertIn("failure_stage: dataset_aggregation", text)
        self.assertIn("classification_debug", text)
        self.assertIn("candidate_clinical_files", text)
        self.assertIn("archive_files", text)

    def test_file_detail_text_shows_reasons_and_scores(self) -> None:
        detail = {
            "path": "/tmp/GSE7003_series_matrix.txt.gz",
            "relative_path": "GSE7003_series_matrix.txt.gz",
            "excluded": False,
            "excluded_reason": None,
            "container_type": "series_matrix",
            "primary_label": "expression_payload",
            "secondary_labels": ["sample_annotation"],
            "organized_targets": ["/tmp/GSE7003/organized/expression/original_candidates/GSE7003_series_matrix.txt.gz"],
            "confidence": 0.9,
            "expression_score": 0.95,
            "sample_annotation_score": 0.42,
            "clinical_score": 0.1,
            "raw_data_score": 0.0,
            "platform_annotation_score": 0.0,
            "junk_score": 0.0,
            "head_signals": ["tabular_block"],
            "middle_signals": ["numeric_matrix_block"],
            "tail_signals": ["numeric_matrix_block"],
            "global_markers_found": ["!Series_", "^SAMPLE"],
            "marker_counts": {"^SAMPLE": 3},
            "size_bytes": 1024,
            "sample_column_count": 3,
            "detected_gsm_count": 3,
            "extra": {},
            "warnings": [],
            "errors": [],
            "decision_trace": ["matrix classifier passed", "accepted as expression candidate"],
            "reasons": ["series_matrix container detected", "high numeric cell ratio"],
            "preview_lines": ["ID_REF\tGSM1\tGSM2"],
            "head_preview": ["!Series_title = demo"],
            "middle_preview": ["ID_REF\tGSM1\tGSM2"],
            "tail_preview": ["EGFR\t1\t2"],
        }
        text = build_file_detail_text(detail, ["模块3将该文件列为 candidate_expression_files"])
        self.assertIn("expression_score: 0.95", text)
        self.assertIn("decision_trace", text)
        self.assertIn("why_classified_this_way", text)
        self.assertIn("candidate_expression_files", text)

    def test_module3_asset_summary_shows_standard_asset_statuses(self) -> None:
        handoff = {
            "dataset_id": "GSE7004",
            "recommended_strategy": "SERIES_MATRIX_FIRST",
            "value_type_hint": "count",
            "may_generate_expression_gene": True,
            "may_generate_sample_annotation": True,
            "preferred_expression_asset": {"file_name": "GSE7004_series_matrix.txt.gz"},
            "preferred_metadata_asset": {"file_name": "GSE7004_family.soft.gz"},
            "preferred_feature_annotation_asset": None,
            "dataset_manifest_draft": {"has_sample_annotation": True, "platform_annotation_files": []},
            "missing_required_assets": [],
            "available_capabilities": ["expression_gene_possible", "sample_annotation_possible"],
            "module1_state": {"current_state": "partial_success"},
        }
        context = dict(handoff)
        context.update(build_standard_asset_layout("/tmp/GSE7004", handoff=handoff))
        text = build_module3_asset_summary_text(context)
        self.assertIn("module3_standard_assets:", text)
        self.assertIn("expression_gene.status: planned", text)
        self.assertIn("expression_gene.reason_code: inferred_from_handoff", text)
        self.assertIn("sample_annotation.status: planned", text)
        self.assertIn("sample_annotation.reason_code: inferred_from_handoff", text)
        self.assertIn("feature_annotation.reason_code: missing_supporting_input", text)
        self.assertIn("dataset_manifest.status: planned", text)
        self.assertIn("dataset_manifest.reason_code: inferred_from_handoff", text)
        self.assertEqual(context["standard_assets"]["expression_gene"]["reason_code"], "inferred_from_handoff")
        self.assertEqual(context["standard_assets"]["feature_annotation"]["reason_code"], "missing_supporting_input")

    def test_build_standard_asset_layout_uses_dataset_info_dataset_id_for_manifest(self) -> None:
        handoff = {
            "dataset_info": {"dataset_id": "GSE7005"},
            "recommended_strategy": "SERIES_MATRIX_FIRST",
            "value_type_hint": "count",
            "module1_state": {"current_state": "partial_success"},
        }
        layout = build_standard_asset_layout("/tmp/GSE7005", handoff=handoff)
        manifest = layout["standard_assets"]["dataset_manifest"]
        self.assertTrue(manifest["expected"])
        self.assertEqual(manifest["status"], "planned")
        self.assertEqual(manifest["source_hint"], "SERIES_MATRIX_FIRST")
        self.assertEqual(manifest["reason_code"], "inferred_from_handoff")

    def test_merge_standard_asset_layout_recomputes_dynamic_status_but_keeps_extra_fields(self) -> None:
        existing = {
            "canonical_asset_paths": {
                "dataset_manifest": "stale.json",
                "extra_asset": "/tmp/keep-me.txt",
            },
            "standard_assets": {
                "dataset_manifest": {
                    "asset_key": "dataset_manifest",
                    "canonical_path": "stale.json",
                    "exists": True,
                    "expected": True,
                    "status": "present",
                    "source_hint": "legacy_hint",
                    "legacy_note": "keep_me",
                }
            },
            "present_assets": ["dataset_manifest"],
        }
        handoff = {
            "dataset_info": {"dataset_id": "GSE7006"},
            "recommended_strategy": "SERIES_MATRIX_FIRST",
            "module1_state": {"current_state": "partial_success"},
        }

        merged = merge_standard_asset_layout(existing, build_standard_asset_layout("/tmp/GSE7006", handoff=handoff))
        manifest = merged["standard_assets"]["dataset_manifest"]

        self.assertFalse(manifest["exists"])
        self.assertTrue(manifest["expected"])
        self.assertEqual(manifest["status"], "planned")
        self.assertEqual(manifest["legacy_note"], "keep_me")
        self.assertTrue(manifest["canonical_path"].endswith("organized/dataset_manifest.json"))
        self.assertEqual(manifest["reason_code"], "status_conflict_resolved")
        self.assertEqual(merged["canonical_asset_paths"]["extra_asset"], "/tmp/keep-me.txt")
        self.assertEqual(merged["present_assets"], [])
        self.assertIn("dataset_manifest", merged["planned_assets"])

    def test_reason_code_is_consistent_with_present_and_not_applicable_statuses(self) -> None:
        handoff = {
            "dataset_id": "GSE7007",
            "recommended_strategy": "SERIES_MATRIX_FIRST",
            "may_generate_expression_gene": False,
            "may_generate_sample_annotation": False,
            "preferred_feature_annotation_asset": None,
            "dataset_manifest_draft": {"has_sample_annotation": False, "platform_annotation_files": []},
            "module1_state": {"current_state": "partial_success"},
        }

        layout = build_standard_asset_layout("/tmp/GSE7007", handoff=handoff)

        self.assertEqual(layout["standard_assets"]["dataset_manifest"]["status"], "planned")
        self.assertEqual(layout["standard_assets"]["dataset_manifest"]["reason_code"], "inferred_from_handoff")
        self.assertEqual(layout["standard_assets"]["expression_gene"]["status"], "not_applicable")
        self.assertEqual(layout["standard_assets"]["expression_gene"]["reason_code"], "not_expected")
        self.assertEqual(layout["standard_assets"]["sample_annotation"]["status"], "not_applicable")
        self.assertEqual(layout["standard_assets"]["sample_annotation"]["reason_code"], "not_expected")

    def test_module3_asset_summary_tolerates_missing_reason_code(self) -> None:
        context = {
            "recommended_strategy": "SERIES_MATRIX_FIRST",
            "value_type_hint": "count",
            "available_capabilities": [],
            "missing_required_assets": [],
            "present_assets": ["expression_gene"],
            "planned_assets": ["dataset_manifest"],
            "standard_assets": {
                "expression_gene": {
                    "status": "present",
                    "exists": True,
                    "expected": True,
                    "source_hint": "expr.tsv",
                    "canonical_path": "/tmp/GSE7008/organized/expression_gene.tsv.gz",
                },
                "sample_annotation": {
                    "status": "not_applicable",
                    "exists": False,
                    "expected": False,
                    "source_hint": None,
                    "canonical_path": "/tmp/GSE7008/organized/sample_annotation.tsv",
                },
                "feature_annotation": {
                    "status": "not_applicable",
                    "exists": False,
                    "expected": False,
                    "source_hint": None,
                    "canonical_path": "/tmp/GSE7008/organized/feature_annotation.tsv",
                },
                "dataset_manifest": {
                    "status": "planned",
                    "exists": False,
                    "expected": True,
                    "source_hint": "SERIES_MATRIX_FIRST",
                    "canonical_path": "/tmp/GSE7008/organized/dataset_manifest.json",
                },
            },
        }

        text = build_module3_asset_summary_text(context)

        self.assertIn("expression_gene.status: present", text)
        self.assertIn("expression_gene.reason_code: None", text)
        self.assertIn("sample_annotation.status: not_applicable", text)
        self.assertIn("dataset_manifest.status: planned", text)

    def test_module3_mainline_summary_is_compact_and_tracks_standard_assets(self) -> None:
        handoff = {
            "dataset_id": "GSE7009",
            "recommended_strategy": "SERIES_MATRIX_FIRST",
            "value_type_hint": "count",
            "may_generate_expression_gene": True,
            "may_generate_sample_annotation": True,
            "preferred_expression_asset": {"file_name": "GSE7009_series_matrix.txt.gz"},
            "preferred_metadata_asset": {"file_name": "GSE7009_family.soft.gz"},
            "dataset_manifest_draft": {"has_sample_annotation": True, "platform_annotation_files": []},
            "missing_required_assets": [],
            "available_capabilities": ["expression_gene_possible", "sample_annotation_possible"],
            "module1_state": {"current_state": "partial_success"},
        }
        context = dict(handoff)
        context.update(build_standard_asset_layout("/tmp/GSE7009", handoff=handoff))

        text = build_module3_mainline_summary_text(context)

        self.assertIn("模块3推荐策略: SERIES_MATRIX_FIRST", text)
        self.assertIn("模块3计划标准资产:", text)
        self.assertIn("expression_gene", text)
        self.assertIn("sample_annotation", text)
        self.assertIn("dataset_manifest", text)
        self.assertIn("expression_gene: planned / reason=inferred_from_handoff", text)
        self.assertIn("dataset_manifest: planned / reason=inferred_from_handoff", text)

    def test_workflow_result_text_includes_module3_mainline_summary(self) -> None:
        handoff = {
            "dataset_id": "GSE7100",
            "recommended_strategy": "SERIES_MATRIX_FIRST",
            "value_type_hint": "count",
            "may_generate_expression_gene": True,
            "may_generate_sample_annotation": True,
            "preferred_expression_asset": {"file_name": "GSE7100_series_matrix.txt.gz"},
            "preferred_metadata_asset": {"file_name": "GSE7100_family.soft.gz"},
            "dataset_manifest_draft": {"has_sample_annotation": True, "platform_annotation_files": []},
            "missing_required_assets": [],
            "available_capabilities": ["expression_gene_possible", "sample_annotation_possible"],
            "module1_state": {"current_state": "partial_success"},
        }
        module1_context = dict(handoff)
        module1_context.update(build_standard_asset_layout("/tmp/GSE7100", handoff=handoff))

        result = {
            "status": "success",
            "download_success_count": 1,
            "metadata_parse_success_count": 1,
            "expression_matrix_success_count": 1,
            "batch_dir": "/tmp/module3-mainline-batch",
            "metadata_json": "/tmp/module3-mainline-batch/metadata.json",
            "metadata_csv": "/tmp/module3-mainline-batch/metadata.csv",
            "workflow_results": [
                {
                    "accession": "GSE7100",
                    "download_success": True,
                    "validation_result": {"status": "ANALYSIS_READY", "next_action": "continue"},
                    "module1_handoff": module1_context,
                    "process_result": {
                        "resolved_gpl_gene_col": "Gene Symbol",
                        "gpl_gene_col_detection": "auto",
                        "manual_gpl_gene_col": None,
                        "n_samples": 8,
                        "n_probe_rows": 1200,
                        "n_probe_cols": 8,
                        "n_gene_rows": 950,
                        "n_gene_cols": 8,
                    },
                    "family_soft_path": "/tmp/GSE7100/raw_downloads/geo_downloads/GSE7100_family.soft.gz",
                    "processed_dir": "/tmp/module3-mainline-batch/processed_GSE7100",
                    "run_summary_path": "/tmp/module3-mainline-batch/processed_GSE7100/run_summary.json",
                    "metadata_parse_success": True,
                    "matrix_build_success": True,
                    "matrix_build_skipped": False,
                    "matrix_build_failed": False,
                    "expression_matrix_error": None,
                }
            ],
        }

        text = build_workflow_result_text(result)

        self.assertIn("模块3主线接入摘要:", text)
        self.assertIn("模块3推荐策略: SERIES_MATRIX_FIRST", text)
        self.assertIn("expression_gene: planned / reason=inferred_from_handoff", text)
        self.assertIn("dataset_manifest: planned / reason=inferred_from_handoff", text)
        self.assertIn("下载验收状态: ANALYSIS_READY", text)

    def test_build_sandbox_summary_includes_flat_reason_code_mapping(self) -> None:
        module1_context = {
            "recommended_strategy": "SERIES_MATRIX_FIRST",
            "available_capabilities": ["expression_gene_possible"],
            "missing_required_assets": [],
            "present_assets": ["expression_gene"],
            "planned_assets": ["sample_annotation", "dataset_manifest"],
            "standard_assets": {
                "expression_gene": {"reason_code": "present_on_disk", "status": "present"},
                "sample_annotation": {"reason_code": "inferred_from_handoff", "status": "planned"},
                "feature_annotation": {"reason_code": "missing_supporting_input", "status": "not_applicable"},
                "dataset_manifest": {"reason_code": "missing_dataset_id", "status": "planned"},
            },
        }
        validation_result = DownloadValidationResult(
            gse_id="GSE7010",
            download_dir="/tmp/GSE7010",
            status="ANALYSIS_READY",
            download_success=True,
            file_count=1,
            nonempty_file_count=1,
            top_problem_summary="none",
            suggested_next_fix="continue",
        )

        summary = build_sandbox_summary(
            gse_id="GSE7010",
            selected_dir="/tmp/GSE7010",
            validation_result=validation_result,
            module1_context=module1_context,
        )

        self.assertIn("handoff_asset_reason_codes", summary)
        self.assertEqual(
            summary["handoff_asset_reason_codes"],
            {
                "expression_gene": "present_on_disk",
                "sample_annotation": "inferred_from_handoff",
                "feature_annotation": "missing_supporting_input",
                "dataset_manifest": "missing_dataset_id",
            },
        )
        self.assertIn("handoff_standard_assets", summary)
        self.assertEqual(summary["handoff_standard_assets"], module1_context["standard_assets"])

    def test_build_sandbox_summary_tolerates_missing_reason_code_values(self) -> None:
        module1_context = {
            "standard_assets": {
                "expression_gene": {"status": "present"},
                "sample_annotation": {"reason_code": None, "status": "planned"},
            }
        }

        summary = build_sandbox_summary(
            gse_id="GSE7011",
            selected_dir="/tmp/GSE7011",
            validation_result=None,
            module1_context=module1_context,
        )

        self.assertEqual(
            summary["handoff_asset_reason_codes"],
            {
                "expression_gene": None,
                "sample_annotation": None,
                "feature_annotation": None,
                "dataset_manifest": None,
            },
        )
        self.assertEqual(summary["handoff_standard_assets"], module1_context["standard_assets"])

    def test_workflow_result_dataset_dir_prefers_dataset_root(self) -> None:
        workflow_result = {
            "accession": "GSE7200",
            "download_result": {"dataset_root": "/tmp/GSE7200"},
            "family_soft_path": "/tmp/GSE7200/raw_downloads/geo_downloads/GSE7200_family.soft.gz",
        }

        self.assertEqual(workflow_result_dataset_dir(workflow_result), str(Path("/tmp/GSE7200").resolve()))

    def test_workflow_result_dataset_dir_falls_back_to_family_soft_parent(self) -> None:
        workflow_result = {
            "accession": "GSE7201",
            "family_soft_path": "/tmp/GSE7201/raw_downloads/geo_downloads/GSE7201_family.soft.gz",
        }

        self.assertEqual(workflow_result_dataset_dir(workflow_result), str(Path("/tmp/GSE7201").resolve()))

    def test_workflow_result_dataset_dir_returns_none_without_paths(self) -> None:
        self.assertIsNone(workflow_result_dataset_dir({"accession": "GSE7202"}))


if __name__ == "__main__":
    unittest.main()
