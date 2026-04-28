import csv
from pathlib import Path
import tempfile
import unittest

from analysis.deg_summary import (
    build_deg_summary_report,
    write_deg_summary_table,
    write_volcano_ready_descriptive_table,
)


FAKE_GENE_MATRIX = [
    {"gene_symbol": "GENE1", "case1": 10.0, "case2": 12.0, "control1": 5.0, "control2": 6.0},
    {"gene_symbol": "GENE2", "case1": 0.0, "case2": 0.0, "control1": 0.0, "control2": 1.0},
]
FAKE_GROUPS = {
    "case1": "ptc",
    "case2": "ptc",
    "control1": "normal",
    "control2": "normal",
}


class DegSummaryTests(unittest.TestCase):
    def test_fake_matrix_generates_log2fc_rows(self) -> None:
        report = build_deg_summary_report(FAKE_GENE_MATRIX, FAKE_GROUPS)

        self.assertEqual(report.gene_count, 2)
        self.assertEqual(report.computed_gene_count, 2)
        self.assertEqual(report.case_count, 2)
        self.assertEqual(report.control_count, 2)
        self.assertTrue(report.log2fc_available)
        self.assertFalse(report.pvalue_available)
        self.assertFalse(report.fdr_available)
        self.assertEqual(report.method, "mean_log2fc_summary")

    def test_write_deg_summary_table_outputs_stable_csv(self) -> None:
        report = build_deg_summary_report(FAKE_GENE_MATRIX, FAKE_GROUPS)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "deg_summary.csv"

            written_path = write_deg_summary_table(report, output_path)

            self.assertEqual(written_path, output_path)
            with output_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(
            list(rows[0].keys()),
            ["gene_symbol", "case_mean", "control_mean", "log2fc", "status"],
        )
        self.assertEqual(rows[0]["gene_symbol"], "GENE1")
        self.assertNotIn("pvalue", rows[0])
        self.assertNotIn("fdr", rows[0])
        self.assertNotIn("adjusted_pvalue", rows[0])

    def test_artifact_writer_does_not_change_report(self) -> None:
        report = build_deg_summary_report(FAKE_GENE_MATRIX, FAKE_GROUPS)
        before = report.to_dict()
        with tempfile.TemporaryDirectory() as tmpdir:
            write_deg_summary_table(report, Path(tmpdir) / "deg_summary.csv")

        self.assertEqual(report.to_dict(), before)
        self.assertEqual(report.rows[0].gene_symbol, "GENE1")
        self.assertAlmostEqual(report.rows[0].case_mean, 11.0)
        self.assertAlmostEqual(report.rows[0].control_mean, 5.5)
        self.assertAlmostEqual(report.rows[0].log2fc, 1.0)

    def test_zero_values_use_pseudocount(self) -> None:
        report = build_deg_summary_report(
            [{"gene_symbol": "ZERO", "case1": 0.0, "control1": 0.0}],
            {"case1": "ptc", "control1": "normal"},
        )

        self.assertEqual(report.computed_gene_count, 1)
        self.assertEqual(report.rows[0].log2fc, 0.0)

    def test_missing_gene_values_warn_and_skip(self) -> None:
        report = build_deg_summary_report(
            [{"gene_symbol": "GENE1", "case1": 1.0, "control1": "missing"}],
            {"case1": "ptc", "control1": "normal"},
        )

        self.assertEqual(report.computed_gene_count, 0)
        self.assertEqual(report.skipped_gene_count, 1)
        self.assertIn("gene_values_missing_or_non_numeric", report.warnings)
        self.assertIn("computed_genes_missing", report.errors)

    def test_missing_group_is_error(self) -> None:
        report = build_deg_summary_report(
            FAKE_GENE_MATRIX,
            {"case1": "ptc", "case2": "ptc"},
        )

        self.assertEqual(report.control_count, 0)
        self.assertFalse(report.log2fc_available)
        self.assertIn("control_group_has_no_samples", report.errors)

    def test_pvalue_and_fdr_are_not_available(self) -> None:
        report = build_deg_summary_report(FAKE_GENE_MATRIX, FAKE_GROUPS)

        self.assertFalse(report.pvalue_available)
        self.assertFalse(report.fdr_available)

    def test_write_volcano_ready_descriptive_table_outputs_stable_csv(self) -> None:
        report = build_deg_summary_report(FAKE_GENE_MATRIX, FAKE_GROUPS)
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "volcano_ready_descriptive_table.csv"

            written_path = write_volcano_ready_descriptive_table(report, output_path)

            self.assertEqual(written_path, output_path)
            with output_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(
            list(rows[0].keys()),
            [
                "gene_symbol",
                "case_mean",
                "control_mean",
                "log2fc",
                "abs_log2fc",
                "status",
                "pvalue",
                "padj",
                "pvalue_available",
                "fdr_available",
                "method",
            ],
        )
        self.assertEqual(rows[0]["gene_symbol"], "GENE1")
        self.assertEqual(rows[0]["status"], "descriptive_only")
        self.assertEqual(rows[0]["pvalue"], "")
        self.assertEqual(rows[0]["padj"], "")
        self.assertEqual(rows[0]["pvalue_available"], "false")
        self.assertEqual(rows[0]["fdr_available"], "false")
        self.assertEqual(rows[0]["method"], "descriptive_mean_log2fc")
        self.assertAlmostEqual(float(rows[0]["abs_log2fc"]), abs(float(rows[0]["log2fc"])))

    def test_volcano_ready_writer_does_not_change_report(self) -> None:
        report = build_deg_summary_report(FAKE_GENE_MATRIX, FAKE_GROUPS)
        before = report.to_dict()

        with tempfile.TemporaryDirectory() as tmpdir:
            write_volcano_ready_descriptive_table(
                report,
                Path(tmpdir) / "volcano_ready_descriptive_table.csv",
            )

        self.assertEqual(report.to_dict(), before)


if __name__ == "__main__":
    unittest.main()
