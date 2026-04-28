from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from geo_pipeline.process import ProcessConfig, process_from_gse_object
from geo_processing.detector.models import (
    DatasetDetectionResult,
    RecommendedStrategy,
)
from geo_tool.geo_workflow import WorkflowConfig, run_download_and_process_workflow


class GSE:
    def __init__(self, phenotype_data: pd.DataFrame, matrix_error: Exception | None = None):
        self.phenotype_data = phenotype_data
        self.gsms = {"GSM1": object(), "GSM2": object()}
        self.gpls = {}
        self.metadata = {"title": ["demo"]}
        self._matrix_error = matrix_error

    def pivot_samples(self, values: str, index: str):
        if self._matrix_error is not None:
            raise self._matrix_error
        return pd.DataFrame({"GSM1": [1.0, 2.0], "GSM2": [3.0, 4.0]}, index=["A", "B"])


class GeoWorkflowIntegrationTests(unittest.TestCase):
    def test_process_keeps_metadata_when_matrix_build_fails(self):
        gse = GSE(
            phenotype_data=pd.DataFrame(
                {
                    "title": ["sample1", "sample2"],
                    "characteristics_ch1": ["tumor", "normal"],
                },
                index=["GSM1", "GSM2"],
            ),
            matrix_error=RuntimeError("matrix unavailable"),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            result = process_from_gse_object(
                gse,
                ProcessConfig(
                    accession="GSE2000",
                    outdir=tmpdir,
                    geo_dir=tmpdir,
                ),
            )
            self.assertEqual(result["status"], "partial_success")
            self.assertTrue(result["metadata_parse_success"])
            self.assertFalse(result["expression_matrix_success"])
            self.assertTrue((Path(tmpdir) / "phenotype_table.csv").exists())
            self.assertTrue((Path(tmpdir) / "parsed" / "metadata" / "sample_metadata.tsv").exists())
            self.assertTrue((Path(tmpdir) / "organized" / "sample_annotation.tsv").exists())
            parse_report = json.loads((Path(tmpdir) / "parsed" / "reports" / "parse_report.json").read_text(encoding="utf-8"))
            manifest = json.loads((Path(tmpdir) / "organized" / "dataset_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["build_status"], "partial_success")
            self.assertEqual(manifest["asset_paths"]["sample_annotation"], "organized/sample_annotation.tsv")
            self.assertEqual(manifest["asset_paths"]["dataset_manifest"], "organized/dataset_manifest.json")
            self.assertEqual(
                parse_report["standard_assets_written"]["dataset_manifest"],
                manifest["asset_paths"]["dataset_manifest"],
            )

    def test_process_writes_phase1_assets_alongside_legacy_outputs(self):
        gse = GSE(
            phenotype_data=pd.DataFrame(
                {
                    "title": ["sample1", "sample2"],
                    "condition": ["tumor", "normal"],
                    "batch": ["b1", "b2"],
                },
                index=["GSM1", "GSM2"],
            ),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            result = process_from_gse_object(
                gse,
                ProcessConfig(
                    accession="GSE2002",
                    outdir=tmpdir,
                    geo_dir=tmpdir,
                    recommended_strategy="SERIES_MATRIX_FIRST",
                    value_type_hint="count",
                ),
            )

            self.assertEqual(result["status"], "success")
            self.assertTrue((Path(tmpdir) / "phenotype_table.csv").exists())
            self.assertTrue((Path(tmpdir) / "expression_probe_clean.csv").exists())
            self.assertTrue((Path(tmpdir) / "parsed" / "metadata" / "sample_metadata.tsv").exists())
            self.assertTrue((Path(tmpdir) / "parsed" / "expression" / "expression_matrix.tsv.gz").exists())
            self.assertTrue((Path(tmpdir) / "parsed" / "reports" / "parse_report.json").exists())
            self.assertTrue((Path(tmpdir) / "organized" / "sample_annotation.tsv").exists())
            manifest = json.loads((Path(tmpdir) / "organized" / "dataset_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["recommended_strategy"], "SERIES_MATRIX_FIRST")
            self.assertEqual(manifest["value_semantic"], "raw_counts")
            self.assertEqual(manifest["build_status"], "partial_success")
            self.assertEqual(manifest["asset_paths"]["sample_annotation"], "organized/sample_annotation.tsv")
            self.assertEqual(manifest["asset_paths"]["dataset_manifest"], "organized/dataset_manifest.json")
            self.assertEqual(manifest["sample_id_order"], ["GSM1", "GSM2"])

    def test_workflow_skips_family_soft_processing_for_raw_only_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            geo_dir = Path(tmpdir) / "geo_downloads"
            geo_dir.mkdir(parents=True, exist_ok=True)
            family_soft_path = geo_dir / "GSE2001_family.soft.gz"
            family_soft_path.write_text("placeholder", encoding="utf-8")

            detection_result = DatasetDetectionResult(
                accession="GSE2001",
                accession_type="GSE",
                scan_root=str(geo_dir),
                has_family_soft=False,
                recommended_strategy=RecommendedStrategy.RAW_RNASEQ_EXTERNAL_PREPROCESS.value,
                failure_reason="RAW_ONLY_DATASET",
                next_action="raw sequencing files detected; upstream alignment/counting pipeline is required",
            )

            with (
                patch("geo_tool.geo_workflow.download_core_geo_records") as download_mock,
                patch("geo_tool.geo_workflow.detect_dataset", return_value=detection_result),
                patch("geo_tool.geo_workflow.process_from_local_family_soft") as process_mock,
            ):
                download_mock.return_value = {
                    "status": "success",
                    "accession": "GSE2001",
                    "geo_dir": str(geo_dir),
                    "family_soft_path": str(family_soft_path),
                    "full_download_success": True,
                }
                result = run_download_and_process_workflow(
                    WorkflowConfig(accession="GSE2001", base_dir=tmpdir)
                )

            process_mock.assert_not_called()
            self.assertEqual(result["status"], "partial_success")
            self.assertEqual(
                result["detection_result"]["recommended_strategy"],
                RecommendedStrategy.RAW_RNASEQ_EXTERNAL_PREPROCESS.value,
            )
            self.assertIn("module1_handoff", result)
            self.assertEqual(
                result["module1_handoff"]["dataset_info"]["dataset_id"],
                "GSE2001",
            )
            self.assertTrue(result["matrix_build_skipped"])


if __name__ == "__main__":
    unittest.main()
