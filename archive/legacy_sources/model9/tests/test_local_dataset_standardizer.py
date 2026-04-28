from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from local_data.delivery_scanner import scan_delivery_folder
from local_data.models import DeliveryFileType
from local_data.standardizer import (
    build_local_dataset_validation_report,
    build_selected_import_plan,
    standardize_local_dataset,
)


class LocalDatasetStandardizerTests(unittest.TestCase):
    def test_count_matrix_plan_is_valid(self) -> None:
        plan = build_selected_import_plan(
            dataset_slug="local-rna-seq",
            selected_expression_matrix="/delivery/Expression/raw_counts.csv",
            expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX,
            selected_sample_metadata="/delivery/Metadata/samples.csv",
            selected_gene_annotation="/delivery/Annotation/genes.csv",
            selected_qc_reports=["/delivery/QC/multiqc.html"],
        )

        self.assertTrue(plan.valid)
        self.assertEqual(plan.expression_data_type, "raw_count_matrix")
        self.assertEqual(plan.selected_qc_reports, ["/delivery/QC/multiqc.html"])
        self.assertEqual(plan.errors, [])

    def test_tpm_fpkm_and_normalized_types_are_supported(self) -> None:
        for expression_type in [
            DeliveryFileType.TPM_MATRIX.value,
            DeliveryFileType.FPKM_MATRIX.value,
            DeliveryFileType.NORMALIZED_EXPRESSION_MATRIX.value,
        ]:
            with self.subTest(expression_type=expression_type):
                plan = build_selected_import_plan(
                    dataset_slug="local-rna-seq",
                    selected_expression_matrix="/delivery/Expression/matrix.csv",
                    expression_data_type=expression_type,
                    selected_sample_metadata="/delivery/Metadata/samples.csv",
                )

                self.assertTrue(plan.valid)
                self.assertEqual(plan.errors, [])

    def test_missing_expression_matrix_invalidates_plan(self) -> None:
        plan = build_selected_import_plan(
            dataset_slug="local-rna-seq",
            selected_expression_matrix=None,
            expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX,
            selected_sample_metadata="/delivery/Metadata/samples.csv",
        )

        self.assertFalse(plan.valid)
        self.assertIn("expression_matrix_missing", plan.errors)

    def test_missing_metadata_is_warning_not_blocking(self) -> None:
        plan = build_selected_import_plan(
            dataset_slug="local-rna-seq",
            selected_expression_matrix="/delivery/Expression/tpm.csv",
            expression_data_type=DeliveryFileType.TPM_MATRIX,
        )

        self.assertTrue(plan.valid)
        self.assertIn("sample_metadata_missing", plan.warnings)
        self.assertIn("gene_annotation_missing", plan.warnings)

    def test_unsupported_expression_type_invalidates_plan(self) -> None:
        plan = build_selected_import_plan(
            dataset_slug="local-rna-seq",
            selected_expression_matrix="/delivery/Expression/matrix.csv",
            expression_data_type=DeliveryFileType.DIFFERENTIAL_EXPRESSION_RESULT,
            selected_sample_metadata="/delivery/Metadata/samples.csv",
        )

        self.assertFalse(plan.valid)
        self.assertIn("unsupported_expression_data_type", plan.errors)

    def test_plan_to_dict_is_stable(self) -> None:
        plan = build_selected_import_plan(
            dataset_slug="local-rna-seq",
            selected_expression_matrix="/delivery/Expression/counts.csv",
            expression_data_type="raw_count_matrix",
            selected_sample_metadata="/delivery/Metadata/samples.csv",
        )

        payload = plan.to_dict()

        self.assertEqual(payload["dataset_slug"], "local-rna-seq")
        self.assertEqual(payload["expression_data_type"], "raw_count_matrix")
        self.assertTrue(payload["valid"])

    def test_standardize_local_dataset_generates_standard_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            delivery_dir = root / "delivery"
            project_dir = root / "project"
            expression_path = delivery_dir / "Expression" / "raw_counts_matrix.csv"
            metadata_path = delivery_dir / "Metadata" / "sample_metadata.csv"
            annotation_path = delivery_dir / "Annotation" / "gene_annotation.csv"
            self._write(expression_path, "gene_id,S1,S2\nG1,1,2\nG2,3,4\n")
            self._write(metadata_path, "sample_id,group\nS1,case\nS2,control\n")
            self._write(annotation_path, "gene_id,symbol\nG1,A\nG2,B\n")
            original_expression = expression_path.read_text(encoding="utf-8")

            scan_report = scan_delivery_folder(delivery_dir)
            plan = build_selected_import_plan(
                dataset_slug="local-rna-seq",
                selected_expression_matrix=str(expression_path),
                expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX,
                selected_sample_metadata=str(metadata_path),
                selected_gene_annotation=str(annotation_path),
            )

            manifest = standardize_local_dataset(
                project_dir=project_dir,
                scan_report=scan_report,
                import_plan=plan,
            )

            dataset_dir = project_dir / "local_datasets" / "local-rna-seq"
            standardized_dir = dataset_dir / "standardized"
            self.assertTrue((dataset_dir / "delivery_scan_report.json").exists())
            self.assertTrue((dataset_dir / "selected_import_plan.json").exists())
            self.assertEqual(
                (standardized_dir / "expression_matrix.csv").read_text(encoding="utf-8"),
                original_expression,
            )
            self.assertTrue((standardized_dir / "sample_metadata.csv").exists())
            self.assertTrue((standardized_dir / "gene_annotation.csv").exists())
            self.assertTrue((standardized_dir / "local_dataset_manifest.json").exists())
            self.assertTrue((standardized_dir / "validation_report.json").exists())
            self.assertEqual(manifest.sample_count, 2)
            self.assertEqual(manifest.gene_count, 2)
            self.assertEqual(manifest.source_type, "local_delivery")
            self.assertEqual(expression_path.read_text(encoding="utf-8"), original_expression)

    def test_standardize_local_dataset_allows_optional_gene_annotation(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            delivery_dir = root / "delivery"
            project_dir = root / "project"
            expression_path = delivery_dir / "Expression" / "sample_tpm_matrix.tsv"
            metadata_path = delivery_dir / "Metadata" / "sample_metadata.csv"
            self._write(expression_path, "gene_id\tS1\nG1\t1.5\n")
            self._write(metadata_path, "sample_id,group\nS1,case\n")
            scan_report = scan_delivery_folder(delivery_dir)
            plan = build_selected_import_plan(
                dataset_slug="local-tpm",
                selected_expression_matrix=str(expression_path),
                expression_data_type=DeliveryFileType.TPM_MATRIX,
                selected_sample_metadata=str(metadata_path),
            )

            manifest = standardize_local_dataset(
                project_dir=project_dir,
                scan_report=scan_report,
                import_plan=plan,
            )

            standardized_dir = project_dir / "local_datasets" / "local-tpm" / "standardized"
            self.assertTrue((standardized_dir / "expression_matrix.csv").exists())
            self.assertTrue((standardized_dir / "sample_metadata.csv").exists())
            self.assertFalse((standardized_dir / "gene_annotation.csv").exists())
            self.assertIsNone(manifest.selected_gene_annotation)
            self.assertIn("gene_annotation_missing", manifest.warnings)

    def test_standardize_local_dataset_rejects_invalid_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            plan = build_selected_import_plan(
                dataset_slug="bad",
                selected_expression_matrix=None,
                expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX,
            )

            with self.assertRaises(ValueError):
                standardize_local_dataset(
                    project_dir=root / "project",
                    scan_report=scan_delivery_folder(root),
                    import_plan=plan,
                )

    def test_manifest_json_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            delivery_dir = root / "delivery"
            project_dir = root / "project"
            expression_path = delivery_dir / "Expression" / "raw_counts_matrix.csv"
            metadata_path = delivery_dir / "Metadata" / "sample_metadata.csv"
            self._write(expression_path, "gene_id,S1\nG1,1\n")
            self._write(metadata_path, "sample_id,group\nS1,case\n")
            scan_report = scan_delivery_folder(delivery_dir)
            plan = build_selected_import_plan(
                dataset_slug="json-check",
                selected_expression_matrix=str(expression_path),
                expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX,
                selected_sample_metadata=str(metadata_path),
            )

            standardize_local_dataset(
                project_dir=project_dir,
                scan_report=scan_report,
                import_plan=plan,
            )

            manifest_path = (
                project_dir
                / "local_datasets"
                / "json-check"
                / "standardized"
                / "local_dataset_manifest.json"
            )
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["dataset_slug"], "json-check")
            self.assertEqual(payload["sample_count"], 1)
            self.assertEqual(payload["gene_count"], 1)

    def test_validation_report_count_matrix_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expression_path = root / "expression_matrix.csv"
            metadata_path = root / "sample_metadata.csv"
            self._write(expression_path, "gene_id,S1,S2,S3\nG1,1,2,3\nG2,4,5,6\n")
            self._write(metadata_path, "sample_id,group\nS1,case\nS2,case\nS3,case\n")

            report = build_local_dataset_validation_report(
                expression_matrix_path=expression_path,
                sample_metadata_path=metadata_path,
                expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX.value,
            )

            self.assertEqual(report.sample_id_match_status, "matched")
            self.assertTrue(report.count_based_compatible)
            self.assertEqual(report.group_count, 1)
            self.assertEqual(report.group_size_summary, {"case": 3})
            self.assertEqual(report.errors, [])

    def test_validation_report_detects_sample_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expression_path = root / "expression_matrix.csv"
            metadata_path = root / "sample_metadata.csv"
            self._write(expression_path, "gene_id,S1,S2\nG1,1,2\n")
            self._write(metadata_path, "sample_id,group\nS1,case\nS3,control\n")

            report = build_local_dataset_validation_report(
                expression_matrix_path=expression_path,
                sample_metadata_path=metadata_path,
                expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX.value,
            )

            self.assertEqual(report.sample_id_match_status, "mismatch")
            self.assertIn("sample_id_mismatch", report.errors)

    def test_validation_report_detects_missing_values_and_duplicate_genes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expression_path = root / "expression_matrix.csv"
            metadata_path = root / "sample_metadata.csv"
            self._write(expression_path, "gene_id,S1,S2\nG1,1,\nG1,2,3\n")
            self._write(metadata_path, "sample_id,group\nS1,case\nS2,control\n")

            report = build_local_dataset_validation_report(
                expression_matrix_path=expression_path,
                sample_metadata_path=metadata_path,
                expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX.value,
            )

            self.assertEqual(report.missing_value_count, 1)
            self.assertEqual(report.duplicated_gene_count, 1)
            self.assertIn("missing_expression_values", report.warnings)
            self.assertIn("duplicated_gene_ids", report.warnings)

    def test_validation_report_warns_on_small_groups(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expression_path = root / "expression_matrix.csv"
            metadata_path = root / "sample_metadata.csv"
            self._write(expression_path, "gene_id,S1,S2\nG1,1,2\n")
            self._write(metadata_path, "sample_id,group\nS1,case\nS2,control\n")

            report = build_local_dataset_validation_report(
                expression_matrix_path=expression_path,
                sample_metadata_path=metadata_path,
                expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX.value,
            )

            self.assertIn("small_group_size:case", report.warnings)
            self.assertIn("small_group_size:control", report.warnings)

    def test_validation_report_marks_tpm_not_count_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expression_path = root / "expression_matrix.csv"
            metadata_path = root / "sample_metadata.csv"
            self._write(expression_path, "gene_id,S1\nG1,1.5\n")
            self._write(metadata_path, "sample_id,group\nS1,case\n")

            report = build_local_dataset_validation_report(
                expression_matrix_path=expression_path,
                sample_metadata_path=metadata_path,
                expression_data_type=DeliveryFileType.TPM_MATRIX.value,
            )

            self.assertFalse(report.count_based_compatible)
            self.assertIn("not_count_based_compatible", report.warnings)

    def test_validation_report_detects_negative_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expression_path = root / "expression_matrix.csv"
            metadata_path = root / "sample_metadata.csv"
            self._write(expression_path, "gene_id,S1\nG1,-1\n")
            self._write(metadata_path, "sample_id,group\nS1,case\n")

            report = build_local_dataset_validation_report(
                expression_matrix_path=expression_path,
                sample_metadata_path=metadata_path,
                expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX.value,
            )

            self.assertIn("negative_expression_values", report.errors)

    def test_validation_report_requires_gene_identifier_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            expression_path = root / "expression_matrix.csv"
            metadata_path = root / "sample_metadata.csv"
            self._write(expression_path, "feature,S1\nG1,1\n")
            self._write(metadata_path, "sample_id,group\nS1,case\n")

            report = build_local_dataset_validation_report(
                expression_matrix_path=expression_path,
                sample_metadata_path=metadata_path,
                expression_data_type=DeliveryFileType.RAW_COUNT_MATRIX.value,
            )

            self.assertIn("expression_gene_identifier_missing", report.errors)

    def _write(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
