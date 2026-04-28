from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tcga_gtex.adapters import gtex_adapter, tcga_adapter
from tcga_gtex.config_rules import (
    Module4RuleConfigError,
    Module4RuleService,
    inspect_rule_bundles,
    load_comparison_config,
    load_coverage_audit_rules,
    load_gene_panel,
    load_lexicon_builder_inputs,
    load_tcga_gtex_resource_rules,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILDER_SCRIPT = REPO_ROOT / "scripts" / "build_english_core_lexicon.py"
AUDIT_SCRIPT = REPO_ROOT / "scripts" / "audit_lexicon_coverage.py"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Module4RuleConfigTests(unittest.TestCase):
    def test_rule_service_loads_known_bundles_and_sections(self) -> None:
        service = Module4RuleService()

        lexicon_inputs = service.load_lexicon_builder_inputs()
        resource_rules = service.load_tcga_gtex_resource_rules()
        audit_rules = service.load_coverage_audit_rules()

        self.assertEqual(lexicon_inputs, load_lexicon_builder_inputs())
        self.assertEqual(resource_rules, load_tcga_gtex_resource_rules())
        self.assertEqual(audit_rules, load_coverage_audit_rules())
        self.assertEqual(
            service.rule_section("tcga_gtex_resources.json", "default_tcga_data_types"),
            resource_rules["default_tcga_data_types"],
        )
        self.assertEqual(service.rule_section("tcga_gtex_resources.json", "missing", default=[]), [])

    def test_rule_service_can_use_fixture_directories_without_mutating_globals(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            rules_dir = root / "rules"
            comparisons_dir = root / "comparisons"
            gene_panels_dir = root / "gene_panels"
            rules_dir.mkdir()
            comparisons_dir.mkdir()
            gene_panels_dir.mkdir()

            (rules_dir / "tcga_gtex_resources.json").write_text(
                (
                    '{"default_tcga_data_types": ["fixture expression"], '
                    '"default_gtex_resources": [], '
                    '"tcga_file_templates": {}, '
                    '"gtex_file_templates": {}}'
                ),
                encoding="utf-8",
            )
            (comparisons_dir / "GSE100.json").write_text('{"dataset_id": "GSE100"}', encoding="utf-8")
            (gene_panels_dir / "panel_a.json").write_text('{"panel_id": "panel_a"}', encoding="utf-8")

            service = Module4RuleService(
                rules_dir=rules_dir,
                comparisons_dir=comparisons_dir,
                gene_panels_dir=gene_panels_dir,
            )

            self.assertEqual(service.load_tcga_gtex_resource_rules()["default_tcga_data_types"], ["fixture expression"])
            self.assertEqual(service.load_comparison_config("GSE100")["dataset_id"], "GSE100")
            self.assertEqual(service.load_gene_panel("panel_a")["panel_id"], "panel_a")
            self.assertIsNone(service.load_comparison_config("GSE999999"))
            self.assertIsNone(service.load_gene_panel("missing_panel"))

    def test_rule_service_rejects_missing_required_rule_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir) / "rules"
            rules_dir.mkdir()
            (rules_dir / "tcga_gtex_resources.json").write_text(
                '{"default_tcga_data_types": [], "default_gtex_resources": [], "tcga_file_templates": {}}',
                encoding="utf-8",
            )
            service = Module4RuleService(rules_dir=rules_dir)

            with self.assertRaisesRegex(Module4RuleConfigError, "missing required section: gtex_file_templates"):
                service.load_tcga_gtex_resource_rules()

    def test_rule_service_rejects_wrong_rule_section_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir) / "rules"
            rules_dir.mkdir()
            (rules_dir / "coverage_audit_rules.json").write_text(
                '{"high_frequency_cancers": {}, "high_frequency_tissues": []}',
                encoding="utf-8",
            )
            service = Module4RuleService(rules_dir=rules_dir)

            with self.assertRaisesRegex(Module4RuleConfigError, "high_frequency_cancers must be list"):
                service.load_coverage_audit_rules()

    def test_rule_service_reports_loaded_missing_and_invalid_bundles(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            rules_dir = Path(tmpdir) / "rules"
            rules_dir.mkdir()
            (rules_dir / "tcga_gtex_resources.json").write_text(
                (
                    '{"default_tcga_data_types": [], '
                    '"default_gtex_resources": [], '
                    '"tcga_file_templates": {}, '
                    '"gtex_file_templates": {}}'
                ),
                encoding="utf-8",
            )
            (rules_dir / "coverage_audit_rules.json").write_text(
                '{"high_frequency_cancers": {}, "high_frequency_tissues": []}',
                encoding="utf-8",
            )
            service = Module4RuleService(rules_dir=rules_dir)

            report = service.inspect_rule_bundles()
            by_name = {item["file_name"]: item for item in report["bundles"]}

            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["status_counts"], {"missing": 1, "loaded": 1, "invalid": 1})
            self.assertEqual(by_name["tcga_gtex_resources.json"]["status"], "loaded")
            self.assertEqual(by_name["lexicon_builder_inputs.json"]["status"], "missing")
            self.assertIn("tcga_projects", by_name["lexicon_builder_inputs.json"]["missing_sections"])
            self.assertEqual(by_name["coverage_audit_rules.json"]["status"], "invalid")
            self.assertEqual(
                by_name["coverage_audit_rules.json"]["invalid_sections"]["high_frequency_cancers"],
                {"expected": "list", "actual": "dict"},
            )

    def test_default_rule_bundle_diagnostics_reports_loaded_state(self) -> None:
        report = inspect_rule_bundles()

        self.assertEqual(report["status"], "success")
        self.assertEqual(report["bundle_count"], 3)
        self.assertEqual(report["status_counts"], {"loaded": 3})
        self.assertTrue(all(item["loaded"] for item in report["bundles"]))

    def test_rule_loaders_return_expected_top_level_sections(self) -> None:
        lexicon_inputs = load_lexicon_builder_inputs()
        resource_rules = load_tcga_gtex_resource_rules()
        audit_rules = load_coverage_audit_rules()

        self.assertIn("tcga_projects", lexicon_inputs)
        self.assertIn("gtex_tissue_catalog", lexicon_inputs)
        self.assertIn("default_tcga_data_types", resource_rules)
        self.assertIn("default_gtex_resources", resource_rules)
        self.assertIn("high_frequency_cancers", audit_rules)
        self.assertIn("high_frequency_tissues", audit_rules)

    def test_builder_and_adapters_consume_externalized_rule_data(self) -> None:
        builder = _load_module(BUILDER_SCRIPT, "build_english_core_lexicon")
        resource_rules = load_tcga_gtex_resource_rules()
        lexicon_inputs = load_lexicon_builder_inputs()

        self.assertEqual(builder.TCGA_PROJECTS, lexicon_inputs["tcga_projects"])
        self.assertEqual(builder.GTEX_TISSUE_CATALOG, lexicon_inputs["gtex_tissue_catalog"])
        self.assertEqual(tcga_adapter.DEFAULT_TCGA_DATA_TYPES, resource_rules["default_tcga_data_types"])
        self.assertEqual(gtex_adapter.DEFAULT_GTEX_RESOURCES, resource_rules["default_gtex_resources"])

    def test_adapters_use_rule_service_for_resource_rules(self) -> None:
        resource_rules = load_tcga_gtex_resource_rules()

        self.assertEqual(
            tcga_adapter._RULE_SERVICE.load_tcga_gtex_resource_rules()["tcga_file_templates"],
            resource_rules["tcga_file_templates"],
        )
        self.assertEqual(
            gtex_adapter._RULE_SERVICE.load_tcga_gtex_resource_rules()["gtex_file_templates"],
            resource_rules["gtex_file_templates"],
        )

    def test_audit_script_consumes_externalized_frequency_rules(self) -> None:
        audit = _load_module(AUDIT_SCRIPT, "audit_lexicon_coverage")
        rules = load_coverage_audit_rules()

        self.assertEqual(audit.HIGH_FREQUENCY_CANCERS, rules["high_frequency_cancers"])
        self.assertEqual(audit.HIGH_FREQUENCY_TISSUES, rules["high_frequency_tissues"])

    def test_scripts_use_rule_service_for_externalized_inputs(self) -> None:
        builder = _load_module(BUILDER_SCRIPT, "build_english_core_lexicon_ruleservice")
        audit = _load_module(AUDIT_SCRIPT, "audit_lexicon_coverage_ruleservice")

        self.assertIsInstance(builder._RULE_SERVICE, Module4RuleService)
        self.assertIsInstance(audit._RULE_SERVICE, Module4RuleService)
        self.assertEqual(builder._RULE_SERVICE.load_lexicon_builder_inputs(), load_lexicon_builder_inputs())
        self.assertEqual(audit._RULE_SERVICE.load_coverage_audit_rules(), load_coverage_audit_rules())

    def test_comparison_and_gene_panel_loaders_return_none_for_missing_configs(self) -> None:
        self.assertIsNone(load_comparison_config("GSE999999"))
        self.assertIsNone(load_gene_panel("demo_panel"))

    def test_asset_contract_comparison_path_matches_loader_convention(self) -> None:
        contract_text = (REPO_ROOT / "configs" / "standards" / "asset_contract_v1.yaml").read_text(encoding="utf-8")

        self.assertIn('path_template: "configs/comparisons/{dataset_id}.json"', contract_text)
        self.assertIn("format: json", contract_text)

    def test_scripts_still_run_as_standalone_entrypoints(self) -> None:
        for script_path in (BUILDER_SCRIPT, AUDIT_SCRIPT):
            with self.subTest(script=script_path.name):
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

    def test_builder_rewrite_leaves_readable_outputs_without_temp_fragments(self) -> None:
        builder = _load_module(BUILDER_SCRIPT, "build_english_core_lexicon_atomic")
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            builder.build_english_core_lexicon(output_dir=output_dir)
            builder.build_english_core_lexicon(output_dir=output_dir)

            chinese_terms = output_dir / "chinese_concept_terms.csv"
            self.assertTrue(chinese_terms.exists())
            self.assertTrue(chinese_terms.read_text(encoding="utf-8").startswith("zh_term_id,"))
            self.assertFalse(list(output_dir.glob("*.tmp")))


if __name__ == "__main__":
    unittest.main()
