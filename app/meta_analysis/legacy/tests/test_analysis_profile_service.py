import tempfile
import unittest
from pathlib import Path

from analysis.models import AnalysisMetric, AnalysisModelType
from analysis_profiles.models import AnalysisProfileStatus, KeywordMatchMode
from analysis_profiles.service import AnalysisProfileService
from analysis_profiles.store import AnalysisProfileStore
from extraction.models import OutcomeType


class AnalysisProfileServiceTests(unittest.TestCase):
    def test_create_analysis_profile_and_export_engine_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = AnalysisProfileService.from_root_dir(Path(temp_dir))
            parts = self._seed_profile_parts(service)

            profile = service.create_analysis_profile(
                "proj-analysis",
                "Primary OR profile",
                outcome_type=OutcomeType.BINARY,
                metric=AnalysisMetric.OR,
                model_type=AnalysisModelType.RANDOM_EFFECT,
                comparison_rule_id=parts["comparison_rule_id"],
                threshold_profile_id=parts["threshold_profile_id"],
                gene_panel_id=parts["gene_panel_id"],
                keyword_rule_set_id=parts["keyword_rule_set_id"],
            )
            ready = service.mark_ready(profile.analysis_profile_id)
            config = service.export_engine_config(profile.analysis_profile_id)

            self.assertEqual(ready.status, AnalysisProfileStatus.READY)
            self.assertEqual(config.metric, AnalysisMetric.OR)
            self.assertEqual(config.model_type, AnalysisModelType.RANDOM_EFFECT)
            self.assertEqual(config.comparison.group_a_label, "Treatment")
            self.assertEqual(config.thresholds.max_i2, 75.0)
            self.assertEqual(config.gene_panel.genes, ["EGFR", "ALK"])
            self.assertEqual(config.keyword_rule_set.keywords, ["metastatic", "advanced"])
            self.assertEqual(config.to_dict()["metric"], "OR")

    def test_validation_rejects_unsupported_metric(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = AnalysisProfileService.from_root_dir(Path(temp_dir))
            parts = self._seed_profile_parts(service)

            with self.assertRaisesRegex(ValueError, "not supported"):
                service.create_analysis_profile(
                    "proj-analysis",
                    "Bad profile",
                    outcome_type=OutcomeType.BINARY,
                    metric=AnalysisMetric.MD,
                    model_type=AnalysisModelType.FIXED_EFFECT,
                    comparison_rule_id=parts["comparison_rule_id"],
                    threshold_profile_id=parts["threshold_profile_id"],
                )

    def test_validation_detects_cross_project_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = AnalysisProfileService.from_root_dir(Path(temp_dir))
            parts = self._seed_profile_parts(service)
            other_threshold = service.create_threshold_profile("other-project", "Other threshold")

            with self.assertRaisesRegex(ValueError, "different project"):
                service.create_analysis_profile(
                    "proj-analysis",
                    "Cross project profile",
                    outcome_type=OutcomeType.BINARY,
                    metric=AnalysisMetric.OR,
                    model_type=AnalysisModelType.FIXED_EFFECT,
                    comparison_rule_id=parts["comparison_rule_id"],
                    threshold_profile_id=other_threshold.threshold_profile_id,
                )

    def test_persistence_and_listing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            service = AnalysisProfileService.from_root_dir(root_dir)
            parts = self._seed_profile_parts(service)
            profile = service.create_analysis_profile(
                "proj-analysis",
                "Persistent profile",
                outcome_type=OutcomeType.CONTINUOUS,
                metric=AnalysisMetric.MD,
                model_type=AnalysisModelType.FIXED_EFFECT,
                comparison_rule_id=parts["comparison_rule_id"],
                threshold_profile_id=parts["threshold_profile_id"],
            )

            reloaded = AnalysisProfileService(AnalysisProfileStore(root_dir))

            self.assertEqual([item.analysis_profile_id for item in reloaded.list_analysis_profiles("proj-analysis")], [profile.analysis_profile_id])
            self.assertEqual(len(reloaded.list_gene_panels("proj-analysis")), 1)
            self.assertEqual(len(reloaded.list_comparison_rules("proj-analysis")), 1)
            self.assertEqual(len(reloaded.list_keyword_rule_sets("proj-analysis")), 1)
            self.assertEqual(len(reloaded.list_threshold_profiles("proj-analysis")), 1)

    def test_threshold_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = AnalysisProfileService.from_root_dir(Path(temp_dir))

            with self.assertRaisesRegex(ValueError, "max_i2"):
                service.create_threshold_profile("proj-analysis", "Bad I2", max_i2=120)

            with self.assertRaisesRegex(ValueError, "alpha"):
                service.create_threshold_profile("proj-analysis", "Bad alpha", alpha=1.5)

    def _seed_profile_parts(self, service: AnalysisProfileService) -> dict[str, str]:
        gene_panel = service.create_gene_panel(
            "proj-analysis",
            "Lung cancer panel",
            ["EGFR", "ALK", "EGFR"],
        )
        comparison = service.create_comparison_rule(
            "proj-analysis",
            "Treatment versus control",
            "Treatment",
            "Control",
        )
        keywords = service.create_keyword_rule_set(
            "proj-analysis",
            "Advanced disease keywords",
            ["metastatic", "advanced", "metastatic"],
            match_mode=KeywordMatchMode.ANY,
        )
        threshold = service.create_threshold_profile(
            "proj-analysis",
            "Conservative thresholds",
            min_study_count=2,
            max_i2=75.0,
            alpha=0.05,
        )
        return {
            "gene_panel_id": gene_panel.gene_panel_id,
            "comparison_rule_id": comparison.comparison_rule_id,
            "keyword_rule_set_id": keywords.keyword_rule_set_id,
            "threshold_profile_id": threshold.threshold_profile_id,
        }


if __name__ == "__main__":
    unittest.main()
