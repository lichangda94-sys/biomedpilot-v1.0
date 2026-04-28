from __future__ import annotations

import gzip
import json
import tempfile
import unittest
from pathlib import Path

from geo_processing import detect_dataset


def _write_text(path: Path, content: str, gz: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if gz:
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            handle.write(content)
        return
    path.write_text(content, encoding="utf-8")


class GeoDatasetDetectorTests(unittest.TestCase):
    def _run_case(self, accession: str, files: dict[str, tuple[str, bool]]):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            for relative_path, (content, gz) in files.items():
                _write_text(root / relative_path, content, gz=gz)
            return detect_dataset(accession=accession, root_dir=str(root))

    def test_series_matrix_normal(self):
        result = self._run_case(
            "GSE1000",
            {
                "GSE1000_series_matrix.txt.gz": (
                    "!Series_title = demo\n!Sample_title = A\nID_REF\tGSM1\tGSM2\tGSM3\nTP53\t2.1\t2.2\t2.3\nEGFR\t3.1\t3.2\t3.3\n",
                    True,
                )
            },
        )
        self.assertEqual(result.recommended_strategy, "SERIES_MATRIX_FIRST")
        self.assertEqual(result.matrix_level, "gene")

    def test_family_soft_only(self):
        result = self._run_case(
            "GSE1001",
            {
                "GSE1001_family.soft.gz": (
                    "^SERIES = GSE1001\n!Series_title = demo\n!Sample_title = GSM1\n",
                    True,
                )
            },
        )
        self.assertEqual(result.recommended_strategy, "METADATA_ONLY")
        self.assertIn("GSE1001_family.soft.gz", result.candidate_metadata_files)

    def test_supplementary_processed_matrix(self):
        result = self._run_case(
            "GSE1002",
            {
                "supp/GSE1002_counts_matrix.tsv": (
                    "gene_id\tSample1\tSample2\tSample3\nENSG000001\t10\t20\t30\nENSG000002\t5\t7\t8\n",
                    False,
                )
            },
        )
        self.assertEqual(result.recommended_strategy, "SUPPLEMENTARY_MATRIX_FIRST")
        self.assertEqual(result.value_semantic, "raw_counts")

    def test_unaccepted_series_matrix_does_not_override_supplementary_expression(self):
        result = self._run_case(
            "GSE236866",
            {
                "raw_downloads/geo_downloads/GSE236866_series_matrix.txt.gz": (
                    "!Series_title = demo\n!Series_overall_design = metadata only placeholder\n",
                    True,
                ),
                "raw_downloads/geo_downloads/GSE236866_family.soft.gz": (
                    "^SERIES = GSE236866\n^SAMPLE = GSM1\n^SAMPLE = GSM2\n",
                    True,
                ),
                "raw_downloads/supplementary/GSE236866_processed_counts.tsv": (
                    "gene_id\tGSM1\tGSM2\tGSM3\nENSG1\t10\t20\t30\nENSG2\t40\t50\t60\n",
                    False,
                ),
            },
        )
        self.assertEqual(result.recommended_strategy, "SOFT_METADATA_PLUS_SUPP_MATRIX")
        self.assertIn("raw_downloads/supplementary/GSE236866_processed_counts.tsv", result.candidate_expression_files)
        self.assertTrue(result.classification_debug["validation_detection_alignment"]["consistent"])

    def test_diff_result_table(self):
        result = self._run_case(
            "GSE1003",
            {
                "results/DEG_results.csv": (
                    "gene,logFC,adj.P.Val,P.Value,baseMean\nTP53,2.1,0.01,0.02,100\nEGFR,-1.4,0.03,0.04,80\n",
                    False,
                ),
                "GSE1003_family.soft.gz": (
                    "^SERIES = GSE1003\n!Series_title = demo\n",
                    True,
                ),
            },
        )
        self.assertEqual(result.failure_reason, "MATRIX_IS_DIFF_RESULT_NOT_EXPRESSION")
        self.assertEqual(result.recommended_strategy, "METADATA_ONLY")

    def test_raw_fastq_only(self):
        result = self._run_case(
            "GSE1004",
            {
                "raw/sample_1.fastq.gz": ("@SEQ_ID\nACGT\n+\n!!!!\n", True),
            },
        )
        self.assertEqual(result.recommended_strategy, "RAW_RNASEQ_EXTERNAL_PREPROCESS")
        self.assertEqual(result.failure_reason, "RAW_ONLY_DATASET")

    def test_raw_cel_only(self):
        result = self._run_case(
            "GSE1005",
            {
                "raw/GSM1.CEL": ("[CEL]\nVersion=3\n", False),
            },
        )
        self.assertEqual(result.recommended_strategy, "RAW_MICROARRAY_EXTERNAL_PREPROCESS")

    def test_single_cell_not_bulk(self):
        result = self._run_case(
            "GSE1006",
            {
                "matrix/single_cell_counts.tsv": (
                    "gene\tcell_barcode_1\tcell_barcode_2\tcell_barcode_3\nENSG000001\t1\t0\t2\nENSG000002\t0\t1\t3\n",
                    False,
                ),
                "README.txt": ("single cell scrna seurat umi droplet 10x", False),
            },
        )
        self.assertEqual(result.recommended_strategy, "UNSUPPORTED_SINGLE_CELL")
        self.assertEqual(result.technology_type, "single_cell")

    def test_probe_level_with_gpl_hint(self):
        result = self._run_case(
            "GSE1007",
            {
                "supp/normalized_matrix.txt": (
                    "ID_REF\tGSM1\tGSM2\tGSM3\n1007_s_at\t5.1\t5.2\t5.3\n2008_x_at\t6.1\t6.0\t6.2\n",
                    False,
                ),
                "GPL570.annot.txt": ("ID\tGene Symbol\n1007_s_at\tDDR1\n", False),
                "GSE1007_family.soft.gz": ("^SERIES = GSE1007\n!Series_title = demo\n", True),
            },
        )
        self.assertEqual(result.matrix_level, "probe")
        self.assertTrue(result.has_platform_annotation)
        self.assertIn("probe-level matrix detected; GPL annotation mapping is recommended", result.warnings)
        self.assertTrue(result.classification_debug["technology_votes"]["votes"])
        self.assertTrue(result.classification_debug["matrix_level_votes"]["votes"])
        self.assertIn("final_decision_reason", result.classification_debug)

    def test_expected_diff_and_debug_snapshot_are_exported(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "expected.json").write_text(
                json.dumps({"technology_type": "microarray", "matrix_level": "probe"}, ensure_ascii=False),
                encoding="utf-8",
            )
            _write_text(
                root / "counts.tsv",
                "gene_id\tGSM1\tGSM2\nENSG1\t10\t20\nENSG2\t30\t40\n",
            )
            result = detect_dataset(accession="GSE1010", root_dir=str(root))
            diff = result.extra["expected_vs_actual_diff"]
            self.assertIn("technology_type", [item["field"] for item in diff["mismatched_fields"]])
            self.assertTrue((root / "organized" / "reports" / "debug_snapshots" / "04_dataset_aggregation.json").exists())
            self.assertTrue((root / "organized" / "reports" / "debug_snapshots" / "dataset_detection.json").exists())


if __name__ == "__main__":
    unittest.main()
