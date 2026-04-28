from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from local_data.delivery_scanner import scan_delivery_folder
from local_data.models import DeliveryFileType


class LocalDeliveryScannerTests(unittest.TestCase):
    def test_mock_delivery_folder_file_types_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = {
                "Expression/raw_counts_matrix.csv": DeliveryFileType.RAW_COUNT_MATRIX,
                "Expression/sample_tpm_matrix.tsv": DeliveryFileType.TPM_MATRIX,
                "Expression/sample_fpkm_matrix.csv": DeliveryFileType.FPKM_MATRIX,
                "Expression/normalized_expression_matrix.csv": DeliveryFileType.NORMALIZED_EXPRESSION_MATRIX,
                "Metadata/sample_metadata.csv": DeliveryFileType.SAMPLE_METADATA,
                "Annotation/gene_annotation.tsv": DeliveryFileType.GENE_ANNOTATION,
                "Differential/DEG_case_vs_control.csv": DeliveryFileType.DIFFERENTIAL_EXPRESSION_RESULT,
                "QC/multiqc_report.html": DeliveryFileType.QC_REPORT,
                "RawData/S1_R1.fastq.gz": DeliveryFileType.RAW_FASTQ,
            }
            for relative_path in paths:
                self._write(root / relative_path, "fake\n")

            report = scan_delivery_folder(root)
            by_name = {candidate.file_name: candidate for candidate in report.candidates}

            for relative_path, expected_type in paths.items():
                candidate = by_name[Path(relative_path).name]
                self.assertEqual(candidate.detected_type, expected_type)
                self.assertGreater(candidate.confidence, 0)
                self.assertTrue(candidate.reasons)

            fastq = by_name["S1_R1.fastq.gz"]
            self.assertIn("raw_sequence_file_detected_but_not_parsed", fastq.warnings)

    def test_unknown_file_is_not_misclassified_as_expression_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write(root / "Report" / "notes.csv", "not,a,matrix\n")

            report = scan_delivery_folder(root)

            self.assertEqual(len(report.candidates), 1)
            self.assertEqual(report.candidates[0].detected_type, DeliveryFileType.UNKNOWN)
            self.assertIn("unclassified_file", report.candidates[0].warnings)

    def test_scanner_does_not_delete_move_or_overwrite_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expression_path = root / "Expression" / "raw_counts_matrix.csv"
            original_content = "gene_id,S1\nA,1\n"
            self._write(expression_path, original_content)

            before_files = sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())
            report = scan_delivery_folder(root)
            after_files = sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())

            self.assertEqual(before_files, after_files)
            self.assertEqual(expression_path.read_text(encoding="utf-8"), original_content)
            self.assertEqual(report.candidates[0].detected_type, DeliveryFileType.RAW_COUNT_MATRIX)

    def test_missing_root_has_stable_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "missing"

            report = scan_delivery_folder(missing)

            self.assertEqual(report.candidates, [])
            self.assertIn("root_dir_missing", report.warnings)

    def test_report_to_dict_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write(root / "Expression" / "sample_tpm_matrix.tsv", "gene_id\tS1\nA\t1\n")

            payload = scan_delivery_folder(root).to_dict()

            self.assertEqual(payload["root_dir"], str(root))
            self.assertEqual(payload["candidates"][0]["detected_type"], "tpm_matrix")
            self.assertEqual(payload["warnings"], [])

    def _write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
