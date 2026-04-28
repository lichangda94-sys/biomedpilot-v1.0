import tempfile
import unittest
from pathlib import Path

from geo_readiness.platform_annotation_parser import (
    parse_platform_annotation_mapping_report,
)


FAKE_GPL570 = """ID\tGene Symbol
1007_s_at\tDDR1
1053_at\tRFC2
117_at\tHSPA6
121_at\tPAX8 /// PAX8-AS1
1255_g_at\t---
"""


class PlatformAnnotationParserTests(unittest.TestCase):
    def test_fake_gpl570_mapping_report_counts_mapping(self) -> None:
        report = parse_platform_annotation_mapping_report(FAKE_GPL570)

        self.assertEqual(report.platform_id, "GPL570")
        self.assertEqual(report.probe_count, 5)
        self.assertEqual(report.mapped_probe_count, 4)
        self.assertEqual(report.unmapped_probe_count, 1)
        self.assertEqual(report.mapping_success_rate, 0.8)
        self.assertTrue(report.acceptable)

    def test_multi_symbol_cells_are_collapsed_with_warning(self) -> None:
        report = parse_platform_annotation_mapping_report(FAKE_GPL570)

        self.assertIn("multi_symbol_cells_collapsed_to_first", report.warnings)

    def test_duplicate_symbols_warn(self) -> None:
        text = """Probe Set ID,Gene Symbol
probe1,TP53
probe2,TP53
probe3,EGFR
"""
        report = parse_platform_annotation_mapping_report(text)

        self.assertEqual(report.duplicated_symbol_count, 1)
        self.assertIn("duplicated_symbols_detected", report.warnings)

    def test_low_mapping_success_is_not_acceptable(self) -> None:
        text = """ID\tGene Symbol
probe1\t---
probe2\t
probe3\tTP53
"""
        report = parse_platform_annotation_mapping_report(text)

        self.assertFalse(report.acceptable)
        self.assertIn("mapping_success_rate_too_low", report.errors)

    def test_missing_columns_return_errors(self) -> None:
        report = parse_platform_annotation_mapping_report("name,value\nx,y\n")

        self.assertIn("platform_annotation_header_missing", report.errors)

    def test_local_file_parses_without_real_gpl570_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "fake_gpl570.tsv"
            path.write_text(FAKE_GPL570, encoding="utf-8")

            report = parse_platform_annotation_mapping_report(path)

        self.assertEqual(report.probe_count, 5)
        self.assertTrue(report.acceptable)

    def test_gpl570_like_comment_preamble_header_is_detected(self) -> None:
        comments = "\n".join(f"# comment {index}" for index in range(1, 17))
        text = f"""{comments}
ID\tGB_ACC\tGene Symbol
1007_s_at\tU48705\tDDR1
1053_at\tM87338\tRFC2
117_at\tX51757\t---
121_at\tX69699\tPAX8
1255_g_at\tL36861\tGUCA1A
"""
        report = parse_platform_annotation_mapping_report(text)

        self.assertEqual(report.probe_count, 5)
        self.assertEqual(report.mapped_probe_count, 4)
        self.assertEqual(report.unmapped_probe_count, 1)
        self.assertEqual(report.errors, [])
        self.assertTrue(report.acceptable)

    def test_id_and_uppercase_symbol_columns_are_detected(self) -> None:
        text = """ID,SYMBOL
probe1,TP53
probe2,EGFR
"""
        report = parse_platform_annotation_mapping_report(text)

        self.assertEqual(report.probe_count, 2)
        self.assertEqual(report.mapped_probe_count, 2)
        self.assertTrue(report.acceptable)

    def test_malformed_header_returns_stable_error(self) -> None:
        text = "# metadata\nnot,a,recognized,header\nprobe1,TP53\n"
        report = parse_platform_annotation_mapping_report(text)

        self.assertEqual(report.errors, ["platform_annotation_header_missing"])


if __name__ == "__main__":
    unittest.main()
