from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "audit_lexicon_coverage.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_lexicon_coverage", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load coverage audit script from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LexiconCoverageAuditTests(unittest.TestCase):
    def test_audit_report_has_expected_top_level_sections(self) -> None:
        audit = load_audit_module()
        report = audit.build_coverage_audit_report()

        self.assertIn("category_coverage", report)
        self.assertIn("disease_coverage", report)
        self.assertIn("tissue_coverage", report)
        self.assertIn("missing_items", report)
        self.assertIn("bias_flags", report)
        self.assertIn("next_recommended_expansions", report)

    def test_audit_report_files_can_be_written(self) -> None:
        audit = load_audit_module()
        report = audit.build_coverage_audit_report()

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "coverage.json"
            md_path = Path(tmpdir) / "coverage.md"
            json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            md_path.write_text(audit.build_markdown_report(report), encoding="utf-8")

            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

    def test_bias_flags_no_longer_show_thyroid_only_chinese_bridge(self) -> None:
        audit = load_audit_module()
        report = audit.build_coverage_audit_report()
        flags = {row["flag"] for row in report["bias_flags"]}

        self.assertNotIn("chinese_disease_skewed_to_thyroid", flags)
        self.assertNotIn("chinese_tissue_skewed_to_thyroid", flags)
        self.assertNotIn("chinese_disease_layer_very_sparse", flags)


if __name__ == "__main__":
    unittest.main()
